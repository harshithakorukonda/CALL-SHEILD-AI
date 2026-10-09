from typing import List, Optional

from pydantic import BaseModel, Field


class TranscriptRequest(BaseModel):
    transcript: str = Field(..., min_length=1, description="The live conversation transcript to evaluate")
    caller_name: Optional[str] = None
    session_id: Optional[str] = None
    context: Optional[str] = None


class RiskAssessment(BaseModel):
    risk_level: str
    confidence: float
    score: float
    is_scam: bool
    reasons: List[str]
    manipulation_signals: List[str]
    semantic_intent: str
    redacted_transcript: str
