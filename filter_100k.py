import json
import heapq

def process_candidates(input_file, output_file, top_n=500):
    top_candidates = []
    counter = 0
    
    core_skills = [
        "pinecone", "weaviate", "qdrant", "milvus", "faiss", 
        "opensearch", "elasticsearch", "sentence-transformers", 
        "embeddings", "ranking", "retrieval", "ndcg"
    ]

    print(f"Starting processing of {input_file}...")

    with open(input_file, 'r', encoding='utf-8') as infile:
        for line_num, line in enumerate(infile, 1):
            if line_num % 10000 == 0:
                print(f"Processed {line_num} lines...")
                
            try:
                candidate = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            profile = candidate.get("profile", {})
            if not isinstance(profile, dict):
                profile = {}
                
            signals = candidate.get("redrob_signals", {})
            if not isinstance(signals, dict):
                signals = {}
            
            # Extract and sanitize fields
            yoe = profile.get("years_of_experience")
            yoe = float(yoe) if yoe is not None else 0.0
            
            response_rate = signals.get("recruiter_response_rate")
            response_rate = float(response_rate) if response_rate is not None else 0.0
            
            notice_period = signals.get("notice_period_days")
            notice_period = int(notice_period) if notice_period is not None else 999
            
            country = candidate.get("Country", candidate.get("country", profile.get("Country", profile.get("country", ""))))
            country = str(country).strip().lower() if country else ""
            
            willing_to_relocate = bool(signals.get("willing_to_relocate", False))
            
            # Hard Rejections
            if yoe < 3:
                continue
                
            if response_rate < 0.10:
                continue
                
            if notice_period > 60:
                continue
                
            if country != "india" and not willing_to_relocate:
                continue
                
            # Scoring
            score = 0
            
            if 4 <= yoe <= 9:
                score += 10
                
            github_score = signals.get("github_activity_score")
            github_score = float(github_score) if github_score is not None else 0.0
            if github_score > 20:
                score += 10
                
            if response_rate > 0.50:
                score += 10
                
            # ߚ FIX: Correctly parsing skills and career history based on Redrob schema
            skills = candidate.get("skills", [])
            skill_names = [s.get("name", "").lower() for s in skills if isinstance(s, dict)]
            
            career_history = candidate.get("career_history", [])
            history_text = " ".join([h.get("description", "").lower() for h in career_history if isinstance(h, dict)])
            
            for core_skill in core_skills:
                # Check if skill exists in exact skill names OR career history text
                if any(core_skill in s for s in skill_names) or (core_skill in history_text):
                    score += 20
                        
            # Push to heap
            heapq.heappush(top_candidates, (score, counter, candidate))
            counter += 1
            
            if len(top_candidates) > top_n:
                heapq.heappop(top_candidates)
                
    # Sort descending by score for the final output
    top_candidates.sort(key=lambda x: x[0], reverse=True)
    
    print(f"Writing top {len(top_candidates)} candidates to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for score, _, candidate in top_candidates:
            outfile.write(json.dumps(candidate) + '\n')
            
    print("Done. Phase 1 Complete!")

if __name__ == "__main__":
    process_candidates("candidates.jsonl", "top_500_candidates.jsonl")