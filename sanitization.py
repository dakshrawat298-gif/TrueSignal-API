from pydantic import BaseModel

class RawCandidateData(BaseModel):
    candidate_name: str
    target_role: str
    unstructured_activity: str

def sanitize_against_prompt_injection(text: str) -> str:
    """Securely sandbox untrusted candidate input via XML containment.

    We do NOT censor or rewrite the candidate's actual content (a primitive
    word-blocking regex destroyed legitimate technical resumes). Instead we:
      1. Strip control/non-printable characters (keeping tabs and newlines).
      2. Neutralize angle brackets so the input cannot break out of its tag.
      3. Wrap the result inside <untrusted_activity> tags, which the agent is
         instructed to treat strictly as inert data.
    """
    if not text:
        text = ""

    # Clean up weird/non-printable characters while preserving real formatting.
    text = "".join(ch for ch in text if ch in ("\n", "\t") or ord(ch) >= 32)

    # XML sandboxing: escape angle brackets so the payload stays inside the tag.
    text = text.replace("<", "&lt;").replace(">", "&gt;")

    return f"<untrusted_activity>\n{text}\n</untrusted_activity>"

def process_and_sanitize_payload(payload: dict) -> dict:
    validated_data = RawCandidateData(**payload)

    sanitized_activity = sanitize_against_prompt_injection(validated_data.unstructured_activity)

    return {
        "candidate_name": validated_data.candidate_name,
        "target_role": validated_data.target_role,
        "unstructured_activity": sanitized_activity
    }