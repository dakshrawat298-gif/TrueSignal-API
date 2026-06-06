from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ValidationError
import uvicorn
from sanitization import process_and_sanitize_payload
from scoring_engine import calculate_final_score
from agent_engine import run_truesignal_evaluation

class OutboundValidationSchema(BaseModel):
    tags: list[str]
    global_equivalency_translation: str
    ledger: str

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "success", "message": "TrueSignal engine is live."}

@app.post("/evaluate")
async def evaluate(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    clean_data = process_and_sanitize_payload(payload)
    ai_result = await run_truesignal_evaluation(clean_data)

    try:
        validated_outbound = OutboundValidationSchema(**ai_result)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    final_score = calculate_final_score(validated_outbound.tags)

    return {
        "candidate_name": clean_data.get("candidate_name"),
        "target_role": clean_data.get("target_role"),
        "final_score": final_score,
        "tags": validated_outbound.tags,
        "global_equivalency_translation": validated_outbound.global_equivalency_translation,
        "decision_ledger": validated_outbound.ledger
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)