from functools import lru_cache
from pathlib import Path

import joblib

from app.ml.pipeline import HIGH_RISK_THRESHOLD, LOW_RISK_THRESHOLD, SCAM_THRESHOLD

from .redaction_service import redact_sensitive
from .risk_engine import assess_risk
from .semantic_analyzer import analyze_transcript


MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "callshield_text_classifier.joblib"
SCAM_LABEL = "SCAM"


class ModelUnavailableError(RuntimeError):
    pass


class ModelInferenceError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _load_model_artifact() -> dict:
    if not MODEL_PATH.is_file():
        raise ModelUnavailableError(
            f"Trained classifier artifact not found at {MODEL_PATH}. "
            "Train it with `python -m app.ml.train` from the backend directory."
        )
    try:
        artifact = joblib.load(MODEL_PATH)
    except Exception as error:
        raise ModelUnavailableError(
            f"Could not load classifier artifact at {MODEL_PATH}: {error}"
        ) from error
    if not isinstance(artifact, dict) or not {"model", "classes", "metadata"} <= artifact.keys():
        raise ModelUnavailableError(
            f"Classifier artifact at {MODEL_PATH} has an invalid structure. Retrain the model."
        )
    if not hasattr(artifact["model"], "predict_proba"):
        raise ModelUnavailableError(
            f"Classifier artifact at {MODEL_PATH} cannot provide class probabilities. Retrain the model."
        )
    if SCAM_LABEL not in artifact["classes"] or "LEGITIMATE" not in artifact["classes"]:
        raise ModelUnavailableError(
            f"Classifier artifact at {MODEL_PATH} does not include both required labels. Retrain the model."
        )
    return artifact


def detect_scam(transcript: str) -> dict:
    if not isinstance(transcript, str) or not transcript.strip():
        raise ValueError("Transcript must contain non-whitespace text.")

    safe_text = redact_sensitive(transcript)
    artifact = _load_model_artifact()
    model = artifact["model"]
    try:
        probabilities = model.predict_proba([safe_text])[0]
        class_probabilities = dict(zip(artifact["classes"], probabilities, strict=True))
        scam_probability = float(class_probabilities[SCAM_LABEL])
    except Exception as error:
        raise ModelInferenceError(f"Classifier inference failed: {error}") from error

    predicted_label = SCAM_LABEL if scam_probability >= SCAM_THRESHOLD else "LEGITIMATE"
    if scam_probability >= HIGH_RISK_THRESHOLD:
        risk_level = "HIGH"
    elif scam_probability <= LOW_RISK_THRESHOLD:
        risk_level = "LOW"
    else:
        risk_level = "MEDIUM"

    analysis = analyze_transcript(safe_text)
    confidence = max(scam_probability, 1.0 - scam_probability)
    
    rule_assessment = assess_risk(analysis)
    
    # Combine ML prediction with dynamic semantic reasons
    reasons = list(rule_assessment.get("reasons", []))
    ml_summary = f"ML model scam probability: {scam_probability * 100:.1f}% ({predicted_label})"
    if ml_summary not in reasons:
        reasons.insert(0, ml_summary)

    intent = analysis.get("semantic_intent", "benign")
    if risk_level == "HIGH" and intent == "benign":
        intent = "scam_likely"

    return {
        "risk_level": risk_level,
        "confidence": round(confidence, 4),
        "score": round(scam_probability, 4),
        "is_scam": predicted_label == SCAM_LABEL,
        "reasons": reasons,
        "manipulation_signals": analysis.get("manipulation_signals", analysis.get("dominant_signals", [])),
        "semantic_intent": intent,
        "redacted_transcript": safe_text,
    }
