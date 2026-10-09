import re
from collections import Counter


SIGNAL_PATTERNS = {
    "urgency": (
        "urgent",
        "immediately",
        "right now",
        "today",
        "asap",
        "quickly",
        "now",
        "tonight",
        "within one hour",
        "within ten minutes",
        "in ten minutes",
        "before midnight",
    ),
    "authority": (
        "police",
        "government",
        "official",
        "bank",
        "kyc",
        "reserve",
        "inspector",
        "authority",
        "account verification",
        "mobile provider",
    ),
    "fear": (
        "suspended",
        "blocked",
        "frozen",
        "arrest",
        "legal action",
        "investigation",
        "penalty",
        "fraud",
        "deactivated",
        "disconnected",
        "detained",
        "will be ruined",
        "will expose",
        "will send",
        "unless you",
        "or your account",
    ),
    "secrecy": (
        "secret",
        "confidential",
        "do not tell",
        "keep it private",
        "don't share",
        "silent",
        "do not discuss",
        "don't call",
    ),
    "distress": (
        "grandchild",
        "hospital",
        "emergency",
        "family",
        "trouble",
        "injured",
        "critical",
        "accident",
        "detained",
    ),
}

CREDENTIAL_PATTERNS = (
    r"\b(?:tell|share|read|provide|send|give|reveal|disclose|confirm|text|forward|"
    r"enter|type|key\s+in|submit)\b.{0,60}\b(?:otp|one[- ]time\s+(?:password|code)|"
    r"security\s+code|verification\s+code|six[- ]digit\s+code|code\s+from\s+"
    r"(?:your\s+)?(?:sms|text|phone)|code\s+you\s+received|pin|password|cvv|"
    r"recovery\s+phrase|code\s+on\s+screen)\b",
)
PAYMENT_REQUEST_PATTERNS = (
    r"\b(?:pay|send|transfer|deposit|wire|remit|purchase|buy|approve|scan)\b.{0,70}\b"
    r"(?:money|funds|payment|fee|charge|upi|collect\s+request|wallet|account|"
    r"gift\s+cards?|cryptocurrency|crypto|bitcoin|registration|processing|bail|"
    r"deposit|release|recharge|transfer)\b",
    r"\b(?:upfront|advance|registration|processing|release|delivery|redelivery|"
    r"activation|security)\s+(?:registration\s+)?(?:fee|charge|payment|deposit)\b",
    r"\b(?:larger\s+)?collect\s+request\b",
)
THREAT_PATTERNS = (
    r"\b(?:will|may|could|unless|or)\b.{0,45}\b(?:block(?:ed)?|suspend(?:ed)?|"
    r"freeze|frozen|deactivat(?:e|ed)|disconnect(?:ed)?|arrest|detain(?:ed)?|"
    r"penalty|legal action|expose|ruin(?:ed)?|delete)\b",
    r"\b(?:blocked|suspended|frozen|deactivated|disconnected|detained|arrested)\b",
    r"\b(?:unless you|or your account)\b",
)
IMPERSONATION_PATTERNS = (
    r"\b(?:i am|this is|calling from|speaking from)\b.{0,45}\b(?:your\s+)?"
    r"(?:bank|government|police|tax|account verification|kyc|computer support|"
    r"mobile provider|official|inspector)\b",
    r"\b(?:bank|government|police|tax|account verification|kyc|computer support|"
    r"mobile provider)\s+(?:staff|agent|officer|department|team)\b",
)
DECEPTION_PATTERNS = (
    r"\b(?:account|kyc)\s+(?:verification|protection|security)\b",
    r"\b(?:refund|reverse(?:d|sal)?|release|unlock|recover)\b",
    r"\b(?:guarantee(?:d)?|double your money|won a|you won|prize|lottery)\b",
    r"\b(?:hired|job offer|work[- ]from[- ]home|recruit(?:ment)?)\b",
    r"\b(?:remote access|gift cards?|private wallet|recovery phrase)\b",
    r"\b(?:i am your|this is your)\s+(?:grandson|granddaughter|son|daughter|relative)\b",
)

RISK_WEIGHTS = {
    "urgency": 0.15,
    "authority": 0.1,
    "fear": 0.2,
    "secrecy": 0.2,
    "distress": 0.1,
    "financial_request": 0.3,
    "credential_request": 0.3,
    "payment_request": 0.3,
    "impersonation": 0.25,
    "deception": 0.25,
}


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL) for pattern in patterns)


def _matches_phrases(text: str, phrases: tuple[str, ...]) -> bool:
    for phrase in phrases:
        pattern = r"(?<!\w)" + r"\s+".join(re.escape(part) for part in phrase.split()) + r"(?!\w)"
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False


def _requests_credentials(text: str) -> bool:
    safe_advice_patterns = (
        r"\b(?:never|don't|do not|should not|must not)\b.{0,45}\b"
        r"(?:tell|share|read|provide|send|give|reveal|disclose|enter|type|"
        r"submit)\b.{0,50}\b(?:otp|one[- ]time\s+(?:password|code)|security\s+"
        r"code|verification\s+code|six[- ]digit\s+code|pin|password|cvv)\b",
        r"\b(?:enter|type|use|submit)\b.{0,45}\b(?:otp|one[- ]time\s+(?:password|code)|"
        r"security\s+code|verification\s+code|pin)\b.{0,40}\bonly\b.{0,35}\b"
        r"(?:official|banking)\s+app\b",
    )
    for pattern in CREDENTIAL_PATTERNS:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE | re.DOTALL):
            prefix = text[max(0, match.start() - 55):match.start()]
            matched_request = text[match.start():match.end()]
            if _matches_any(prefix + matched_request, safe_advice_patterns):
                continue
            if re.search(r"\b(?:never|don't|do not|not)\b.{0,30}$", prefix):
                continue
            if re.search(
                r"\b(?:only|inside|within|through)\b.{0,35}\b(?:official|banking)\s+app\b",
                text[match.start():match.end() + 55],
            ):
                continue
            return True
    return False


def analyze_transcript(transcript: str) -> dict:
    text = (transcript or "").lower()
    words = re.findall(r"[a-zA-Z]+", text)
    counts = Counter(words)

    legacy_signals = {
        signal: _matches_phrases(text, phrases)
        for signal, phrases in SIGNAL_PATTERNS.items()
    }
    credential_request = _requests_credentials(text)
    payment_request = _matches_any(text, PAYMENT_REQUEST_PATTERNS)
    impersonation = _matches_any(text, IMPERSONATION_PATTERNS)
    deception = _matches_any(text, DECEPTION_PATTERNS)
    threat = _matches_any(text, THREAT_PATTERNS)
    urgency = legacy_signals["urgency"]
    secrecy = legacy_signals["secrecy"]
    distress = legacy_signals["distress"]

    signals = [signal for signal, matched in legacy_signals.items() if matched]
    if credential_request:
        signals.extend(("financial_request", "credential_request"))
    if payment_request:
        signals.append("payment_request")
    if impersonation:
        signals.append("impersonation")
    if deception:
        signals.append("deception")
    signals = list(dict.fromkeys(signals))

    coercion = threat or secrecy
    coercive_pressure = coercion or (
        urgency
        and (
            credential_request
            or (payment_request and (deception or impersonation))
        )
    )
    weights = {
        signal: RISK_WEIGHTS.get(signal, 0.0) if matched else 0.0
        for signal, matched in (
            *legacy_signals.items(),
            ("financial_request", credential_request),
            ("credential_request", credential_request),
            ("payment_request", payment_request),
            ("impersonation", impersonation),
            ("deception", deception),
        )
    }

    if credential_request and (coercive_pressure or impersonation):
        semantic_intent = "credential_coercion"
    elif payment_request and (
        coercive_pressure or deception or impersonation or (distress and urgency)
    ):
        semantic_intent = "coercive_payment_request"
    elif signals:
        semantic_intent = "manipulation"
    else:
        semantic_intent = "benign"

    risk_context = {
        "credential_request": credential_request,
        "payment_request": payment_request,
        "impersonation": impersonation,
        "deception": deception,
        "coercion": coercion,
        "coercive_pressure": coercive_pressure,
        "urgency": urgency,
        "distress": distress,
    }

    return {
        "text": text,
        "signal_counts": counts,
        "manipulation_signals": signals,
        "signal_weights": weights,
        "risk_context": risk_context,
        "semantic_intent": semantic_intent,
        "dominant_signals": sorted(
            signals,
            key=lambda signal: (
                weights.get(signal, 0.0),
                signal in {"credential_request", "payment_request", "impersonation", "deception"},
            ),
            reverse=True,
        )[:3],
    }
