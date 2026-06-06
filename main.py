import csv
import json
import os

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
import uvicorn

from sanitization import process_and_sanitize_payload
from scoring_engine import calculate_final_score
from gemini_agent import run_truesignal_evaluation, OutboundValidationSchema
from run_batch import build_payload

LEADERBOARD_CSV = "team_submission.csv"
STATIC_DIR = "static"

# Cap sandbox uploads so judges get a fast demo without hitting rate limits.
SANDBOX_MAX_CANDIDATES = 8

# Hard ceiling on sandbox upload size (2MB) to protect server memory.
SANDBOX_MAX_UPLOAD_BYTES = 2 * 1024 * 1024
SANDBOX_TOO_LARGE_MESSAGE = "File too large. Please upload a sample file under 2MB."


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


def _record_to_payload(record: dict) -> dict:
    """Map an uploaded record to the evaluation input shape.

    Accepts both the rich dataset format (profile/career_history/education/
    skills) via build_payload, and a flat format that already carries
    candidate_name / target_role / unstructured_activity."""
    if "unstructured_activity" in record:
        return {
            "candidate_name": record.get("candidate_name") or "Unknown Candidate",
            "target_role": record.get("target_role") or "Unknown Role",
            "unstructured_activity": record.get("unstructured_activity") or "",
        }
    return build_payload(record)


async def _score_record(record: dict, index: int) -> dict:
    """Run a single uploaded record through the live Gemini scoring pipeline."""
    cid = record.get("candidate_id") or f"SANDBOX_{index:03d}"
    payload = _record_to_payload(record)
    clean_data = process_and_sanitize_payload(payload)
    ai_result = await run_truesignal_evaluation(clean_data)

    try:
        validated = OutboundValidationSchema(**ai_result)
    except ValidationError:
        return {
            "candidate_id": cid,
            "score": 0,
            "reasoning": "Evaluation failed output validation.",
        }

    score = calculate_final_score(validated.tags)
    reasoning = (
        validated.ledger
        or validated.global_equivalency_translation
        or "No reasoning produced."
    )
    return {"candidate_id": cid, "score": score, "reasoning": reasoning}


@app.post("/api/sandbox_upload")
async def sandbox_upload(file: UploadFile = File(...)):
    """Accept a .jsonl of candidates, score the first few through the live
    Gemini pipeline, and return them ranked highest-first.

    This is independent of /api/leaderboard — the CSV fallback is untouched."""
    # Read incrementally and abort the moment we exceed the cap, so a massive
    # upload can never balloon server memory before the candidate cap applies.
    chunks = []
    total = 0
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > SANDBOX_MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail=SANDBOX_TOO_LARGE_MESSAGE)
        chunks.append(chunk)
    raw = b"".join(chunks)

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")

    records = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue  # skip malformed lines, keep the sandbox forgiving
        if not isinstance(obj, dict):
            continue  # skip valid-JSON-but-not-a-record lines (lists, scalars)
        records.append(obj)

    if not records:
        raise HTTPException(
            status_code=400,
            detail="No valid JSONL candidate records found in the uploaded file.",
        )

    records = records[:SANDBOX_MAX_CANDIDATES]

    candidates = []
    for i, record in enumerate(records, start=1):
        candidates.append(await _score_record(record, i))

    candidates.sort(key=lambda c: c["score"], reverse=True)
    for i, c in enumerate(candidates, start=1):
        c["rank"] = i

    return JSONResponse(
        {"count": len(candidates), "candidates": candidates, "source": "sandbox"}
    )


@app.get("/")
async def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
