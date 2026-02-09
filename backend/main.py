from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Answers(BaseModel):
    answers: list[str]

@app.get("/")
def root():
    return {"message": "EarlySteps backend running"}

@app.post("/check")
def check_answers(data: Answers):
    if data.answers.count("no") >= 2:
        return {"result": "Screening recommended"}
    return {"result": "Development looks okay"}
