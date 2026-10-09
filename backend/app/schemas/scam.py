from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TranscriptRequest(BaseModel):
    transcript: str = Field(..., min_length=1, description="The live conversation transcript to evaluate")
    caller_name: Optional[str] = None
    session_id: Optional[str] = None
    context: Optional[str] = None

    @field_validator("transcript")
    @classmethod
    def transcript_must_contain_non_whitespace(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Transcript must contain non-whitespace text.")
        return value


class RiskAssessment(BaseModel):
    risk_level: str
    confidence: float
    score: float
    is_scam: bool
    reasons: List[str]
    manipulation_signals: List[str]
    semantic_intent: str
    redacted_transcript: str
