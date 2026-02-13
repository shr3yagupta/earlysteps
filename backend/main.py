from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
import random
import requests

app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- AUTH ----------------
SECRET_KEY = "earlysteps-secret"
ALGORITHM = "HS256"
security = HTTPBearer(auto_error=False)

otp_db = {}
profiles_db = {}
results_db = {}

GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

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

# ---------------- TOKEN ----------------
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

# ---------------- OTP ----------------
@app.post("/auth/request-otp")
def request_otp(data: LoginRequest):
    otp = str(random.randint(100000, 999999))
    otp_db[data.identifier] = otp
    print("OTP:", otp)
    return {"message": "OTP sent (check logs)"}

@app.post("/auth/verify-otp")
def verify_otp(data: OTPVerify):
    if otp_db.get(data.identifier) != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    return {"token": create_token(data.identifier)}

# ---------------- PROFILE ----------------
@app.post("/profiles")
def create_profile(profile: Profile, user=Depends(verify_token)):
    profiles_db.setdefault(user, []).append(profile.dict())
    return {"message": "Profile created"}

@app.get("/profiles")
def get_profiles(user=Depends(verify_token)):
    return profiles_db.get(user, [])

# ---------------- QUESTIONNAIRE ----------------
@app.post("/questionnaire")
def questionnaire(data: Answers, user=Depends(verify_token)):

    # Simple scoring logic (stable demo version)
    score = data.answers.count("no")

    if score <= 1:
        status = "On Track"
    elif score <= 3:
        status = "Needs Monitoring"
    else:
        status = "Extra Support Recommended"

    summary = "Assessment based on overall response patterns focusing on absence of age‑appropriate behaviors."

    result = {
        "status": status,
        "summary": summary,
        "reassurance": "This is not a medical diagnosis. This is an early screening tool.",
        "next_steps": [
            "Observe behaviors over next 4–6 weeks.",
            "Consult pediatrician if concerns persist."
        ],
        "follow_up": "Repeat screening in 30 days.",
        "timestamp": datetime.utcnow().isoformat()
    }

    results_db.setdefault(user, {})
    results_db[user].setdefault(data.child, [])
    results_db[user][data.child].append(result)

    return result

# ---------------- HISTORY ----------------
@app.get("/history/{child}")
def get_history(child: str, user=Depends(verify_token)):
    return results_db.get(user, {}).get(child, [])

# ---------------- NEARBY SUPPORT ----------------
@app.get("/nearby-support")
def nearby_support(lat: float, lng: float):

    base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    details_url = "https://maps.googleapis.com/maps/api/place/details/json"
    distance_url = "https://maps.googleapis.com/maps/api/distancematrix/json"

    categories = {
        "government": "government hospital pediatric",
        "private": "private hospital pediatric",
        "specialists": "developmental pediatrician child psychologist therapy"
    }

    final_results = {}

    for key, keyword in categories.items():

        params = {
            "location": f"{lat},{lng}",
            "radius": 7000,
            "keyword": keyword,
            "key": GOOGLE_API_KEY
        }

        response = requests.get(base_url, params=params)
        data = response.json()

        results = []

        for place in data.get("results", [])[:5]:

            place_id = place["place_id"]

            details_res = requests.get(details_url, params={
                "place_id": place_id,
                "fields": "formatted_phone_number",
                "key": GOOGLE_API_KEY
            })
            phone = details_res.json().get("result", {}).get("formatted_phone_number", "Not Available")

            distance_res = requests.get(distance_url, params={
                "origins": f"{lat},{lng}",
                "destinations": f"{place['geometry']['location']['lat']},{place['geometry']['location']['lng']}",
                "key": GOOGLE_API_KEY
            })

            distance_data = distance_res.json()
            distance_text = distance_data["rows"][0]["elements"][0].get("distance", {}).get("text", "N/A")

            results.append({
                "name": place["name"],
                "address": place.get("vicinity"),
                "rating": place.get("rating", "N/A"),
                "phone": phone,
                "distance": distance_text,
                "lat": place["geometry"]["location"]["lat"],
                "lng": place["geometry"]["location"]["lng"]
            })

        final_results[key] = results

    return final_results
