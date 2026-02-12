from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import random

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
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------- STORAGE (Demo) ----------------
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

class PasswordAuth(BaseModel):
    identifier: str
    password: str

class Profile(BaseModel):
    name: str
    age: int

class Answers(BaseModel):
    child: str
    answers: list[str]

# ---------------- UTILS ----------------

def create_token(identifier: str):
    return jwt.encode(
        {
            "sub": identifier,
            "exp": datetime.utcnow() + timedelta(hours=2)
        },
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

# ---------------- ROUTES ----------------

@app.get("/")
def root():
    return {"message": "EarlySteps backend running"}

# Signup
@app.post("/auth/signup")
def signup(data: PasswordAuth):
    if data.identifier in users_db:
        raise HTTPException(status_code=400, detail="User exists")

    users_db[data.identifier] = pwd_context.hash(data.password)
    return {"message": "User created"}

# Password Login
@app.post("/auth/login")
def login(data: PasswordAuth):
    if data.identifier not in users_db:
        raise HTTPException(status_code=400, detail="User not found")

    if not pwd_context.verify(data.password, users_db[data.identifier]):
        raise HTTPException(status_code=400, detail="Wrong password")

    token = create_token(data.identifier)
    return {"token": token}

# OTP (Demo Mode)
@app.post("/auth/request-otp")
def request_otp(data: LoginRequest):
    otp = str(random.randint(100000, 999999))
    otp_db[data.identifier] = otp
    print("OTP for", data.identifier, "is:", otp)
    return {"message": "OTP generated (check server logs)"}

@app.post("/auth/verify-otp")
def verify_otp(data: OTPVerify):
    if otp_db.get(data.identifier) != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    token = create_token(data.identifier)
    return {"token": token}

# Create Profile
@app.post("/profiles")
def create_profile(profile: Profile, user=Depends(verify_token)):
    if user not in profiles_db:
        profiles_db[user] = []

    profiles_db[user].append(profile.dict())
    return {"message": "Profile created"}

# Get Profiles
@app.get("/profiles")
def get_profiles(user=Depends(verify_token)):
    return profiles_db.get(user, [])

# Questionnaire
@app.post("/questionnaire")
def questionnaire(data: Answers, user=Depends(verify_token)):

    score = data.answers.count("no")

    if score >= 3:
        result = "Screening recommended"
    else:
        result = "Development looks okay"

    if user not in results_db:
        results_db[user] = {}

    results_db[user][data.child] = result

    return {"result": result}
