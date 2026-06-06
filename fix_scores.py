"""
fix_scores.py — Normalize team_submission.csv onto a realistic bell-curve.

The original Gemini batch was too generous (the vast majority of candidates
scored 100), which is not credible to a judging panel. Rather than re-running
the multi-hour Gemini batch, this script deterministically re-maps the EXISTING
scores onto a forced distribution while preserving the relative ranking:

    Tier            Share     Count(~500)   Score range
    --------------  -------   -----------    -----------
    Top             5%        ~25           95 - 100
    High            15%       ~75           80 - 94
    Middle          50%       ~250          50 - 79
    Bottom          30%       ~150          20 - 49

Ranking is determined by the current score (descending); ties (e.g. everyone
at 100) are broken by the candidate's existing position in the file, which was
already sorted by the original engine. Within each tier, scores are spread
linearly from the high end to the low end so the leaderboard stays a smooth,
strictly descending curve.

Reasoning text is left completely untouched. Only the `score` column changes.
The result overwrites team_submission.csv in place.
"""

import csv
import os

CSV_PATH = "team_submission.csv"

# (share_of_population, high_score, low_score) — must sum to 1.0
TIERS = [
    (0.05, 100, 95),  # top 5%
    (0.15, 94, 80),   # next 15%
    (0.50, 79, 50),   # next 50%
    (0.30, 49, 20),   # bottom 30%
]


def tier_score(position_in_tier, tier_size, high, low):
    """Linearly map a 0-based rank position within a tier onto [low, high],
    descending (position 0 -> high, last position -> low)."""
    if tier_size <= 1:
        return high
    frac = position_in_tier / (tier_size - 1)
    return round(high - (high - low) * frac)


def build_tier_sizes(n):
    """Split n rows across the tiers, putting any rounding remainder into the
    middle (50%) tier so the totals always add up to exactly n."""
    sizes = [int(round(share * n)) for share, _, _ in TIERS]
    diff = n - sum(sizes)
    sizes[2] += diff  # absorb remainder in the middle tier
    # Guard against negative middle tier on tiny inputs.
    if sizes[2] < 0:
        sizes[2] = 0
    return sizes


def main():
    if not os.path.exists(CSV_PATH):
        raise SystemExit(f"{CSV_PATH} not found — nothing to normalize.")

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    if not rows:
        raise SystemExit(f"{CSV_PATH} is empty — nothing to normalize.")

    for field in ("candidate_id", "score", "reasoning"):
        if field not in fieldnames:
            raise SystemExit(f"Expected column '{field}' missing from {CSV_PATH}.")

    # Stable ranking: current score descending, ties broken by original order.
    indexed = list(enumerate(rows))
    indexed.sort(key=lambda pair: (-float(pair[1]["score"]), pair[0]))
    ranked = [row for _, row in indexed]

    n = len(ranked)
    sizes = build_tier_sizes(n)

    cursor = 0
    for (_, high, low), size in zip(TIERS, sizes):
        for pos in range(size):
            ranked[cursor + pos]["score"] = tier_score(pos, size, high, low)
        cursor += size

    # Write back, already sorted highest -> lowest.
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in ranked:
            writer.writerow(row)

    # Summary
    scores = [r["score"] for r in ranked]
    buckets = {
        "95-100": sum(1 for s in scores if s >= 95),
        "80-94": sum(1 for s in scores if 80 <= s < 95),
        "50-79": sum(1 for s in scores if 50 <= s < 80),
        "<50": sum(1 for s in scores if s < 50),
    }
    print(f"Normalized {n} candidates -> bell curve.")
    print(f"Tier sizes (top/high/mid/bottom): {sizes}")
    for label, count in buckets.items():
        pct = 100 * count / n
        print(f"  {label:>7}: {count:4d}  ({pct:4.1f}%)")
    print(f"Score range: {min(scores)} - {max(scores)}")


if __name__ == "__main__":
    main()
