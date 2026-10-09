def assess_risk(analysis: dict) -> dict:
    weights = analysis["signal_weights"]
    score = sum(weights.values())
    threshold = 0.7

    if not analysis["manipulation_signals"]:
        score = 0.08
        return {
            "risk_level": "LOW",
            "confidence": 0.72,
            "score": round(score, 3),
            "is_scam": False,
            "reasons": ["Conversation appears routine and non-coercive."],
        }

    score = min(score, 1.0)
    if score >= threshold:
        risk_level = "HIGH"
        is_scam = True
    elif score >= 0.45:
        risk_level = "MEDIUM"
        is_scam = True
    else:
        risk_level = "LOW"
        is_scam = False

    reasons = []
    if "financial_request" in analysis["manipulation_signals"]:
        reasons.append("The caller is trying to obtain a payment or verification detail.")
    if "urgency" in analysis["manipulation_signals"]:
        reasons.append("The caller is creating time pressure to reduce hesitation.")
    if "fear" in analysis["manipulation_signals"]:
        reasons.append("The caller is using fear or threats to control the victim's response.")
    if "authority" in analysis["manipulation_signals"]:
        reasons.append("The caller is impersonating an official or trusted authority.")
    if "secrecy" in analysis["manipulation_signals"]:
        reasons.append("The caller is instructing the user to keep information private or hidden.")
    if not reasons:
        reasons.append("The conversation contains manipulative social-engineering cues.")

    confidence = round(min(0.55 + score * 0.45, 0.99), 3)

    return {
        "risk_level": risk_level,
        "confidence": confidence,
        "score": round(score, 3),
        "is_scam": is_scam,
        "reasons": reasons,
    }
