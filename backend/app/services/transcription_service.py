class TranscriptionService:
    def __init__(self):
        self.provider = "demo-stt"

    def transcribe(self, audio_payload: str | None = None, text: str | None = None) -> str:
        if text:
            return text.strip()
        if audio_payload:
            return audio_payload.strip()
        return ""
