from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import random

app = FastAPI()

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- SECURITY ----------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "earlysteps-secret"
ALGORITHM = "HS256"

# ---------- DATABASE (TEMP) ----------
users_db = {}
otp_db = {}

# ---------- MODELS ----------
class Answers(BaseModel):
    answers: list[str]

class LoginRequest(BaseModel):
    identifier: str  # email or phone

class PasswordSignup(BaseModel):
    identifier: str
    password: str

class OTPVerify(BaseModel):
    identifier: str
    otp: str

# ---------- AUTH ----------
@app.post("/auth/request-otp")
def request_otp(data: LoginRequest):
    otp = str(random.randint(100000, 999999))
    otp_db[data.identifier] = otp
    print("OTP:", otp)  # demo
    return {"message": "OTP sent"}

@app.post("/auth/verify-otp")
def verify_otp(data: OTPVerify):
    if otp_db.get(data.identifier) != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    token = jwt.encode(
        {"sub": data.identifier, "exp": datetime.utcnow() + timedelta(hours=2)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return {"token": token}

@app.post("/auth/signup")
def signup(data: PasswordSignup):
    if data.identifier in users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    users_db[data.identifier] = pwd_context.hash(data.password)
    return {"message": "User created"}

@app.post("/auth/login")
def login(data: PasswordSignup):
    if data.identifier not in users_db:
        raise HTTPException(status_code=400, detail="User not found")
    if not pwd_context.verify(data.password, users_db[data.identifier]):
        raise HTTPException(status_code=400, detail="Wrong password")

    token = jwt.encode(
        {"sub": data.identifier, "exp": datetime.utcnow() + timedelta(hours=2)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return {"token": token}

# ---------- CORE ----------
@app.get("/")
def root():
    return {"message": "EarlySteps backend running"}

@app.post("/check")
def check_answers(data: Answers):
    if data.answers.count("no") >= 2:
        return {"result": "Screening recommended"}
    return {"result": "Development looks okay"}
