TAG_WEIGHTS = {
    "TAG_COGNITIVE_SYNTHESIS": 25,
    "TAG_OPERATIONAL_HUSTLE": 20,
    "TAG_SYNTACTIC_DISSOCIATION": 15,
    "TAG_AMBIGUITY_NAVIGATION": 15,
    "TAG_LOCAL_SCALABILITY": 20
}

def calculate_final_score(tags: list[str]) -> int:
    """Calculates score based on deeply researched Indian contextual proxy tags."""
    base_score = 50
    for tag in tags:
        base_score += TAG_WEIGHTS.get(tag, 0)
    return max(0, min(100, base_score))