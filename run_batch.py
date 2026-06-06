import asyncio
import aiohttp
import json
import csv

async def evaluate_candidate(session, candidate_data, semaphore):
    url = "http://127.0.0.1:8000/evaluate"
    max_retries = 3
    async with semaphore:
        for attempt in range(max_retries):
            try:
                async with session.post(url, json=candidate_data, timeout=30.0) as response:
                    if response.status == 200:
                        return await response.json()
                    if response.status in (429, 500, 422):
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
            
            if attempt == max_retries - 1:
                return {
                    "candidate_name": candidate_data.get("candidate_name", "Unknown"),
                    "target_role": candidate_data.get("target_role", "Unknown"),
                    "final_score": 0,
                    "tags": [],
                    "global_equivalency_translation": "PIPELINE_ERROR",
                    "decision_ledger": f"Fatal API Failure after 3 retries."
                }

async def main():
    with open("redrob_dataset.json", "r", encoding="utf-8") as f:
        dataset = json.load(f)

    semaphore = asyncio.Semaphore(5)

    async with aiohttp.ClientSession() as session:
        tasks = [evaluate_candidate(session, candidate, semaphore) for candidate in dataset]
        results = await asyncio.gather(*tasks)

    results.sort(key=lambda x: x.get("final_score", 0), reverse=True)

    with open("final_submission.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(['Rank', 'Candidate Name', 'Target Role', 'Final Score', 'Tags', 'Global Translation', 'Decision Ledger'])
        
        for rank, result in enumerate(results, start=1):
            writer.writerow([
                rank,
                result.get("candidate_name"),
                result.get("target_role"),
                result.get("final_score"),
                json.dumps(result.get("tags", [])),
                result.get("global_equivalency_translation"),
                result.get("decision_ledger")
            ])

if __name__ == "__main__":
    asyncio.run(main())