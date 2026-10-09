from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas.scam import RiskAssessment, TranscriptRequest
from app.services.scam_detector import detect_scam
from app.websocket.alerts import WebSocketManager

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = WebSocketManager()


@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.APP_NAME}


@app.get("/")
def root():
    return {"message": "CallShield AI backend is running."}


@app.post("/api/analyze", response_model=RiskAssessment)
def analyze_transcript(payload: TranscriptRequest):
    result = detect_scam(payload.transcript)
    return RiskAssessment(
        risk_level=result["risk_level"],
        confidence=result["confidence"],
        score=result["score"],
        is_scam=result["is_scam"],
        reasons=result["reasons"],
        manipulation_signals=result["manipulation_signals"],
        semantic_intent=result["semantic_intent"],
        redacted_transcript=result["redacted_transcript"],
    )


@app.get("/api/scenarios")
def scenarios():
    return {
        "scenarios": [
            {
                "label": "Urgent financial scam",
                "transcript": "Your bank account is frozen. We need your OTP immediately or the police will take action. Do not tell anyone."
            },
            {
                "label": "Family emergency",
                "transcript": "This is your grandson. I am in hospital after an accident and I need you to send money right now."
            },
            {
                "label": "Safe support call",
                "transcript": "Hello, this is a routine security follow-up. We are checking your payment preferences and can schedule a callback later."
            },
        ]
    }


@app.websocket("/ws/alerts")
async def alerts(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
