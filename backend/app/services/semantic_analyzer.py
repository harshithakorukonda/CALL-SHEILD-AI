import re
from collections import Counter


URGENT_WORDS = {
    "urgent", "immediately", "right now", "today", "asap", "quickly", "now", "tonight"
}
AUTHORITY_WORDS = {
    "police", "government", "official", "bank", "kyc", "reserve", "inspector", "authority"
}
THREAT_WORDS = {
    "suspended", "blocked", "frozen", "arrest", "legal", "investigation", "penalty", "fraud"
}
SECRECY_WORDS = {
    "secret", "confidential", "do not tell", "keep it private", "don't share", "silent"
}
FINANCIAL_REQUEST_WORDS = {
    "otp", "pin", "cvv", "upi", "paytm", "bank transfer", "send money", "verify code", "transaction"
}
DISTRESS_WORDS = {
    "grandchild", "hospital", "emergency", "family", "trouble", "injured", "critical"
}


def analyze_transcript(transcript: str) -> dict:
    text = (transcript or "").lower()
    words = re.findall(r"[a-zA-Z]+", text)
    counts = Counter(words)

    signals = []
    weights = {"urgency": 0.0, "authority": 0.0, "fear": 0.0, "secrecy": 0.0, "financial_request": 0.0, "distress": 0.0}

    urgency_matches = [w for w in URGENT_WORDS if w in text]
    if urgency_matches:
        signals.append("urgency")
        weights["urgency"] = 0.22 + min(len(urgency_matches) * 0.1, 0.35)

    authority_matches = [w for w in AUTHORITY_WORDS if w in text]
    if authority_matches:
        signals.append("authority")
        weights["authority"] = 0.18 + min(len(authority_matches) * 0.08, 0.28)

    fear_matches = [w for w in THREAT_WORDS if w in text]
    if fear_matches:
        signals.append("fear")
        weights["fear"] = 0.2 + min(len(fear_matches) * 0.09, 0.35)

    secrecy_matches = [w for w in SECRECY_WORDS if w in text]
    if secrecy_matches:
        signals.append("secrecy")
        weights["secrecy"] = 0.18 + min(len(secrecy_matches) * 0.12, 0.32)

    financial_matches = [w for w in FINANCIAL_REQUEST_WORDS if w in text]
    if financial_matches:
        signals.append("financial_request")
        weights["financial_request"] = 0.28 + min(len(financial_matches) * 0.1, 0.4)

    distress_matches = [w for w in DISTRESS_WORDS if w in text]
    if distress_matches:
        signals.append("distress")
        weights["distress"] = 0.15 + min(len(distress_matches) * 0.12, 0.3)

    total_matches = len(set(signals))
    semantic_intent = "benign" if total_matches == 0 else "manipulation"

    if financial_matches and (urgency_matches or fear_matches):
        semantic_intent = "financial_pressure"
    elif authority_matches and fear_matches:
        semantic_intent = "authority_threat"
    elif distress_matches and urgency_matches:
        semantic_intent = "family_emergency"

    return {
        "text": text,
        "signal_counts": counts,
        "manipulation_signals": signals,
        "signal_weights": weights,
        "semantic_intent": semantic_intent,
        "dominant_signals": sorted(signals, key=lambda s: weights[s], reverse=True)[:3],
    }
