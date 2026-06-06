import json
import csv

def generate_final_csv():
    input_file = "scored_500.json"
    output_file = "team_submission.csv"

    with open(input_file, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
    top_100 = candidates[:100]

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        
        for rank, candidate in enumerate(top_100, start=1):
            writer.writerow([
                candidate.get("candidate_id", ""),
                rank,
                candidate.get("score", 0),
                candidate.get("reasoning", "")
            ])

if __name__ == "__main__":
    generate_final_csv()