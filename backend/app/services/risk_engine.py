def assess_risk(analysis: dict) -> dict:
    context = analysis.get("risk_context", {})
    signals = set(analysis.get("manipulation_signals", ()))

    credential_request = context.get("credential_request", "credential_request" in signals)
    payment_request = context.get("payment_request", "payment_request" in signals)
    impersonation = context.get("impersonation", "impersonation" in signals)
    deception = context.get("deception", "deception" in signals)
    coercion = context.get("coercion", bool(signals & {"fear", "secrecy"}))
    coercive_pressure = context.get(
        "coercive_pressure",
        coercion or (
            context.get("urgency", "urgency" in signals)
            and (
                credential_request
                or (payment_request and (deception or impersonation))
            )
        ),
    )
    distress_and_urgency = context.get("distress", "distress" in signals) and context.get(
        "urgency", "urgency" in signals
    )

    credential_scam = credential_request and (coercive_pressure or impersonation)
    payment_scam = payment_request and (
        coercive_pressure or deception or impersonation or credential_request or distress_and_urgency
    )
    coordinated_impersonation = impersonation and coercion

    if credential_scam or payment_scam:
        risk_level = "HIGH"
        score = 0.9
        reasons = []
        if credential_request:
            reasons.append("The caller is requesting a private credential or verification code.")
        if payment_request:
            reasons.append("The caller is requesting a payment or approval of a financial transaction.")
        if impersonation:
            reasons.append("The request is paired with a claim of trusted authority.")
        if coercive_pressure:
            reasons.append("The request is paired with a threat, secrecy, or coercive time pressure.")
        if deception:
            reasons.append("The request is paired with a deceptive promise, refund, or account-protection claim.")
        if distress_and_urgency:
            reasons.append("An urgent personal-emergency story is being used alongside a payment request.")
    elif credential_request or payment_request or coordinated_impersonation:
        risk_level = "MEDIUM"
        score = 0.55
        reasons = ["The conversation contains a sensitive credential or payment request without enough context to confirm a scam."]
    else:
        risk_level = "LOW"
        score = min(
            0.08 + sum(
                analysis.get("signal_weights", {}).get(signal, 0.0)
                for signal in ("urgency", "authority", "fear", "secrecy", "distress")
            ),
            0.44,
        )
        reasons = ["No coercive credential request or suspicious payment combination was detected."]

    return {
        "risk_level": risk_level,
        "confidence": 0.9 if risk_level == "HIGH" else 0.65 if risk_level == "MEDIUM" else 0.72,
        "score": round(score, 3),
        "is_scam": risk_level in {"HIGH", "MEDIUM"},
        "reasons": reasons,
    }
