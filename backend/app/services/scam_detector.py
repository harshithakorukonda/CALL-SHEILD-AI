from .redaction_service import redact_sensitive
from .semantic_analyzer import analyze_transcript
from .risk_engine import assess_risk


def detect_scam(transcript: str) -> dict:
    safe_text = redact_sensitive(transcript)
    analysis = analyze_transcript(safe_text)
    assessment = assess_risk(analysis)

    return {
        "risk_level": assessment["risk_level"],
        "confidence": assessment["confidence"],
        "score": assessment["score"],
        "is_scam": assessment["is_scam"],
        "reasons": assessment["reasons"],
        "manipulation_signals": analysis["dominant_signals"],
        "semantic_intent": analysis["semantic_intent"],
        "redacted_transcript": safe_text,
    }
