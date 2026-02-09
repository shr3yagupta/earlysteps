from fastapi import FastAPI
from pydantic import BaseModel
from logic import evaluate_screening

app = FastAPI()


class ScreeningRequest(BaseModel):
    age_months: int
    answers: list[bool]


@app.get("/")
def root():
    return {"status": "Backend running"}


@app.post("/evaluate")
def evaluate(data: ScreeningRequest):
    result, message = evaluate_screening(data.answers)
    return {
        "result": result,
        "message": message
    }
