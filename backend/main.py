from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import random
import os
import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = "earlysteps-secret"
ALGORITHM = "HS256"
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Temporary storage (hackathon)
users_db = {}
otp_db = {}

# ------------------ MODELS ------------------

class LoginRequest(BaseModel):
    identifier: str

class OTPVerify(BaseModel):
    identifier: str
    otp: str

class PasswordAuth(BaseModel):
    identifier: str
    password: str

class Answers(BaseModel):
    answers: list[str]

# ------------------ UTILITIES ------------------

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

    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def is_email(identifier: str):
    return "@" in identifier

# ------------------ EMAIL OTP ------------------
def send_email_otp(to_email, otp):
    msg = MIMEText(f"Your EarlySteps OTP is: {otp}")
    msg["Subject"] = "EarlySteps OTP"
    msg["From"] = os.getenv("EMAIL_ADDRESS")
    msg["To"] = to_email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_PASSWORD"))
    server.send_message(msg)
    server.quit()

# ------------------ SMS OTP ------------------

def send_sms_otp(phone, otp):
    client = Client(
        os.getenv("TWILIO_SID"),
        os.getenv("TWILIO_AUTH")
    )

    client.messages.create(
        body=f"Your EarlySteps OTP is {otp}",
        from_=os.getenv("TWILIO_PHONE"),
        to=phone
    )

# ------------------ ROUTES ------------------

@app.get("/")
def root():
    return {"message": "EarlySteps backend running"}

# Signup with password
@app.post("/auth/signup")
def signup(data: PasswordAuth):
    if data.identifier in users_db:
        raise HTTPException(status_code=400, detail="User exists")

    users_db[data.identifier] = pwd_context.hash(data.password)
    return {"message": "User created successfully"}

# Password login
@app.post("/auth/login")
def login(data: PasswordAuth):
    if data.identifier not in users_db:
        raise HTTPException(status_code=400, detail="User not found")

    if not pwd_context.verify(data.password, users_db[data.identifier]):
        raise HTTPException(status_code=400, detail="Wrong password")

    token = create_token(data.identifier)
    return {"token": token}

# Request OTP
@app.post("/auth/request-otp")
def request_otp(data: LoginRequest):
    otp = str(random.randint(100000, 999999))
    otp_db[data.identifier] = otp

    if is_email(data.identifier):
        send_email_otp(data.identifier, otp)
    else:
        send_sms_otp(data.identifier, otp)

    return {"message": "OTP sent"}

# Verify OTP
@app.post("/auth/verify-otp")
def verify_otp(data: OTPVerify):
    if otp_db.get(data.identifier) != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    token = create_token(data.identifier)
    return {"token": token}

# Protected check
@app.post("/check")
def check_answers(data: Answers, user=Depends(verify_token)):
    if data.answers.count("no") >= 2:
        return {"result": "Screening recommended"}
    return {"result": "Development looks okay"}
