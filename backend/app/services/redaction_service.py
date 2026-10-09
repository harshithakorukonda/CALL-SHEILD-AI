import re


def redact_sensitive(text: str) -> str:
    if not text:
        return ""

    sanitized = text
    patterns = [
        (r"\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b", "[CARD]"),
        (r"\b\d{6}\b", "[OTP]"),
        (r"\b(?:\d{10}|\+?\d{10,15})\b", "[PHONE]"),
        (r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", "[EMAIL]"),
        (r"\b[A-Z]{4}0[A-Z0-9]{6}\b", "[IFSC]"),
    ]

    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

    return sanitized
