TAG_WEIGHTS = {
    "TAG_COGNITIVE_SYNTHESIS": 25,
    "TAG_OPERATIONAL_HUSTLE": 20,
    "TAG_SYNTACTIC_DISSOCIATION": 15,
    "TAG_AMBIGUITY_NAVIGATION": 15,
    "TAG_LOCAL_SCALABILITY": 20
}

# Zero-tolerance tag: its presence overrides all positive signals.
TAG_HONEYPOT_DETECTED = "TAG_HONEYPOT_DETECTED"

def calculate_final_score(tags: list[str]) -> int:
    """Calculates score based on deeply researched Indian contextual proxy tags.

    Zero-tolerance rule: if the adversarial engine flags a honeypot /
    chronological impossibility (TAG_HONEYPOT_DETECTED), the candidate is
    immediately floored to 0, completely overriding any positive tags.
    """
    if TAG_HONEYPOT_DETECTED in tags:
        return 0

    base_score = 50
    for tag in tags:
        base_score += TAG_WEIGHTS.get(tag, 0)
    return max(0, min(100, base_score))