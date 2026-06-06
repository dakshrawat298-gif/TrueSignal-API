import json
import csv
import os
import time

import requests

API_URL = "http://127.0.0.1:5000/evaluate"
INPUT_FILE = "top_500_candidates.jsonl"
OUTPUT_CSV = "team_submission.csv"
PROGRESS_FILE = "batch_progress.jsonl"
DELAY_SECONDS = 1.5
REQUEST_TIMEOUT = 90
MAX_RETRIES = 3
CHECKPOINT_EVERY = 25
# Set BATCH_LIMIT to a positive number to only process the first N candidates (smoke test).
LIMIT = int(os.environ.get("BATCH_LIMIT", "0"))


def build_payload(record: dict) -> dict:
    """Map a rich candidate profile into the /evaluate API's expected input shape."""
    profile = record.get("profile", {}) or {}

    candidate_name = profile.get("anonymized_name") or "Unknown Candidate"
    target_role = profile.get("headline") or profile.get("current_title") or "Unknown Role"

    parts = []

    summary = profile.get("summary")
    if summary:
        parts.append(f"SUMMARY: {summary}")

    yoe = profile.get("years_of_experience")
    cur_title = profile.get("current_title")
    cur_company = profile.get("current_company")
    if yoe or cur_company or cur_title:
        parts.append(
            f"EXPERIENCE: {yoe} years total; currently {cur_title or 'N/A'} at {cur_company or 'N/A'}."
        )

    history = record.get("career_history", []) or []
    if history:
        parts.append("CAREER HISTORY:")
        for job in history:
            parts.append(
                f"- {job.get('title', '')} at {job.get('company', '')} "
                f"({job.get('duration_months', '?')} months): {job.get('description', '')}"
            )

    education = record.get("education", []) or []
    if education:
        edu = "; ".join(
            f"{e.get('degree', '')} {e.get('field_of_study', '')} @ {e.get('institution', '')}"
            for e in education
        )
        parts.append(f"EDUCATION: {edu}")

    skills = record.get("skills", []) or []
    if skills:
        skill_names = ", ".join(
            f"{s.get('name')} ({s.get('proficiency')})" for s in skills[:15]
        )
        parts.append(f"SKILLS: {skill_names}")

    unstructured_activity = "\n".join(parts).strip() or "No activity provided."

    return {
        "candidate_name": candidate_name,
        "target_role": target_role,
        "unstructured_activity": unstructured_activity,
    }


def evaluate_one(payload: dict) -> dict:
    """POST a single candidate to the local evaluation server using a fresh
    connection each time (Connection: close) with light retries."""
    headers = {"Content-Type": "application/json", "Connection": "close"}
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(
                API_URL, json=payload, headers=headers, timeout=REQUEST_TIMEOUT
            )
            if resp.status_code == 200:
                return resp.json()
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
                continue
            return {
                "final_score": 0,
                "decision_ledger": f"PIPELINE_ERROR: HTTP {resp.status_code} after {MAX_RETRIES} retries.",
            }
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
                continue
            return {
                "final_score": 0,
                "decision_ledger": f"PIPELINE_ERROR: request failed after {MAX_RETRIES} retries ({e}).",
            }


def load_records() -> list:
    records = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def load_progress() -> dict:
    """Return already-processed rows keyed by candidate_id so the run is resumable."""
    done = {}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    row = json.loads(line)
                    done[row["candidate_id"]] = row
    return done


def write_csv(results: list) -> None:
    rows = sorted(results, key=lambda r: r.get("score", 0), reverse=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "score", "reasoning"])
        for r in rows:
            writer.writerow([r["candidate_id"], r["score"], r["reasoning"]])


def main() -> None:
    records = load_records()
    if LIMIT > 0:
        records = records[:LIMIT]
    total = len(records)

    done = load_progress()
    results = list(done.values())
    print(f"Loaded {total} candidates; {len(done)} already processed.", flush=True)

    progress_f = open(PROGRESS_FILE, "a", encoding="utf-8")
    try:
        for i, record in enumerate(records, start=1):
            cid = record.get("candidate_id", f"ROW_{i}")
            if cid in done:
                continue

            payload = build_payload(record)
            start = time.time()
            result = evaluate_one(payload)
            elapsed = time.time() - start

            score = result.get("final_score", 0)
            reasoning = (
                result.get("decision_ledger")
                or result.get("global_equivalency_translation")
                or "No reasoning produced."
            )
            row = {"candidate_id": cid, "score": score, "reasoning": reasoning}
            results.append(row)
            done[cid] = row

            progress_f.write(json.dumps(row) + "\n")
            progress_f.flush()
            print(f"[{i}/{total}] {cid} -> score {score} ({elapsed:.1f}s)", flush=True)

            if i % CHECKPOINT_EVERY == 0:
                write_csv(results)

            time.sleep(DELAY_SECONDS)
    finally:
        progress_f.close()

    write_csv(results)
    print(f"DONE. Wrote {len(results)} rows to {OUTPUT_CSV}.", flush=True)


if __name__ == "__main__":
    main()
