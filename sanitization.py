import re
from pydantic import BaseModel

class RawCandidateData(BaseModel):
    candidate_name: str
    target_role: str
    unstructured_activity: str

# FIX: Removed (?i) from the strings
malicious_patterns = [
    r"ignore previous instructions",
    r"system prompt",
    r"bypass",
    r"jailbreak"
]

# FIX: Passed re.IGNORECASE directly to the compiler
pattern = re.compile(r'(?:' + '|'.join(malicious_patterns) + r')', re.IGNORECASE)

def sanitize_against_prompt_injection(text: str) -> str:
    if not text:
        text = ""

    text = text.replace("<", "&lt;").replace(">", "&gt;")
    text = pattern.sub("[REDACTED_MALICIOUS_INTENT]", text)

    return f"<untrusted_activity>\n{text}\n</untrusted_activity>"

def process_and_sanitize_payload(payload: dict) -> dict:
    validated_data = RawCandidateData(**payload)

    sanitized_activity = sanitize_against_prompt_injection(validated_data.unstructured_activity)

    return {
        "candidate_name": validated_data.candidate_name,
        "target_role": validated_data.target_role,
        "unstructured_activity": sanitized_activity
    }