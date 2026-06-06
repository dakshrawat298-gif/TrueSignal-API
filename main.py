import csv
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
import uvicorn

from sanitization import process_and_sanitize_payload
from scoring_engine import calculate_final_score
from gemini_agent import run_truesignal_evaluation, OutboundValidationSchema

LEADERBOARD_CSV = "team_submission.csv"
STATIC_DIR = "static"


app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "success", "message": "TrueSignal engine is live."}


@app.get("/api/leaderboard")
async def leaderboard():
    """Return the candidate leaderboard from the CSV, highest score first.

    Returns an empty list gracefully when the file is missing or empty."""
    if not os.path.exists(LEADERBOARD_CSV):
        return JSONResponse({"count": 0, "candidates": []})

    candidates = []
    try:
        with open(LEADERBOARD_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_score = (row.get("score") or "").strip()
                try:
                    score = int(raw_score)
                except (TypeError, ValueError):
                    try:
                        score = int(float(raw_score))
                    except (TypeError, ValueError):
                        score = 0
                candidates.append(
                    {
                        "candidate_id": (row.get("candidate_id") or "").strip(),
                        "score": score,
                        "reasoning": (row.get("reasoning") or "").strip(),
                    }
                )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read leaderboard: {e}")

    candidates.sort(key=lambda c: c["score"], reverse=True)
    for i, c in enumerate(candidates, start=1):
        c["rank"] = i

    return JSONResponse({"count": len(candidates), "candidates": candidates})


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
        "decision_ledger": validated_outbound.ledger,
    }


@app.get("/")
async def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
