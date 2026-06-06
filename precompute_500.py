# precompute_500.py
import asyncio
import json
from gemini_agent import run_truesignal_evaluation
from scoring_engine import calculate_final_score

async def main():
    input_file = "top_500_candidates.jsonl"
    output_file = "scored_500.json"
    
    candidates = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                candidates.append(json.loads(line))
                
    total = len(candidates)
    results = []
    
    for i, candidate in enumerate(candidates, start=1):
        candidate_id = candidate.get("candidate_id")
        
        ai_result = await run_truesignal_evaluation(candidate)
        score = calculate_final_score(ai_result.get("tags", []))
        reasoning = ai_result.get("ledger", "System error: No reasoning provided.")
        
        results.append({
            "candidate_id": candidate_id,
            "score": score,
            "reasoning": reasoning
        })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4)
            
        print(f"Processed {i}/{total}... Sleeping for rate limit")
        
        if i < total:
            await asyncio.sleep(4.1)

if __name__ == "__main__":
    asyncio.run(main())