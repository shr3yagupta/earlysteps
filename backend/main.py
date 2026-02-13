from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError
from datetime import datetime, timedelta
import random
import os
import requests
import google.generativeai as genai

app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- SECURITY ----------------
SECRET_KEY = "earlysteps-secret"
ALGORITHM = "HS256"
security = HTTPBearer(auto_error=False)

# ---------------- GEMINI CONFIG ----------------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# ---------------- DEMO STORAGE ----------------
users_db = {}
otp_db = {}
profiles_db = {}
results_db = {}

# ---------------- MODELS ----------------

class LoginRequest(BaseModel):
    identifier: str

class OTPVerify(BaseModel):
    identifier: str
    otp: str

class Profile(BaseModel):
    name: str
    age: int

class Answers(BaseModel):
    child: str
    answers: list[str]

# ---------------- AUTH UTILS ----------------

def create_token(identifier: str):
    return jwt.encode(
        {"sub": identifier, "exp": datetime.utcnow() + timedelta(hours=2)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ---------------- AUTH ROUTES ----------------

@app.post("/auth/request-otp")
def request_otp(data: LoginRequest):
    otp = str(random.randint(100000, 999999))
    otp_db[data.identifier] = otp
    print("OTP for", data.identifier, "is:", otp)
    return {"message": "OTP generated (check logs)"}

@app.post("/auth/verify-otp")
def verify_otp(data: OTPVerify):
    if otp_db.get(data.identifier) != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    token = create_token(data.identifier)
    return {"token": token}

# ---------------- PROFILE ----------------

@app.post("/profiles")
def create_profile(profile: Profile, user=Depends(verify_token)):
    if user not in profiles_db:
        profiles_db[user] = []
    profiles_db[user].append(profile.dict())
    return {"message": "Profile created"}

@app.get("/profiles")
def get_profiles(user=Depends(verify_token)):
    return profiles_db.get(user, [])

# ---------------- QUESTIONNAIRE ----------------

@app.post("/questionnaire")
def questionnaire(data: Answers, user=Depends(verify_token)):

    formatted_answers = "\n".join(
        [f"Q{i+1}: {ans}" for i, ans in enumerate(data.answers)]
    )

    try:
        prompt = f"""
        You are a responsible developmental screening AI.

        Questionnaire responses:
        {formatted_answers}

        Analyze overall behavioral pattern.
        Focus on absence of age-appropriate behaviors.

        Categorize strictly as:
        - On Track
        - Needs Monitoring
        - Extra Support Recommended

        Provide:
        1. status
        2. summary (parent friendly)
        3. reassurance (clear: not diagnosis)
        4. next_steps (short list)
        5. follow_up recommendation
        """

        response = model.generate_content(prompt)
        summary = response.text
        status = "Needs Monitoring"

    except Exception as e:
        print("Gemini ERROR:", e)

        score = data.answers.count("no")

        if score <= 1:
            status = "On Track"
        elif score <= 3:
            status = "Needs Monitoring"
        else:
            status = "Extra Support Recommended"

        summary = "Based on response patterns, some age‑appropriate behaviors may require monitoring."

    result = {
        "status": status,
        "summary": summary,
        "reassurance": "This is not a medical diagnosis. This tool is for early screening only.",
        "next_steps": [
            "Observe behaviors over next 4–6 weeks.",
            "Consult pediatrician if concerns persist."
        ],
        "follow_up": "Repeat screening in 30 days.",
        "timestamp": datetime.utcnow().isoformat()
    }

    if user not in results_db:
        results_db[user] = {}

    if data.child not in results_db[user]:
        results_db[user][data.child] = []

    results_db[user][data.child].append(result)

    return result

# ---------------- HISTORY ----------------

@app.get("/history/{child}")
def get_history(child: str, user=Depends(verify_token)):
    return results_db.get(user, {}).get(child, [])

# ---------------- NEARBY SUPPORT ----------------

@app.get("/nearby-support")
def nearby_support(lat: float, lng: float):

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

    params = {
        "location": f"{lat},{lng}",
        "radius": 5000,
        "type": "hospital",
        "keyword": "pediatric developmental clinic",
        "key": GOOGLE_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    results = []

    for place in data.get("results", [])[:5]:
        results.append({
            "name": place["name"],
            "address": place.get("vicinity")
        })

    return results
