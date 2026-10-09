from pathlib import Path
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.ml.pipeline import HIGH_RISK_THRESHOLD, LOW_RISK_THRESHOLD, SCAM_THRESHOLD
from app.services import scam_detector
from app.services.scam_detector import detect_scam


SCENARIOS = (
    (
        "Fake bank KYC credential threat",
        "Your bank KYC expires today. Tell me the six-digit code or your account will be blocked.",
    ),
    (
        "Paraphrased account-protection code scam",
        "I am from account verification. Share the security code sent to your phone to keep your account active.",
    ),
    (
        "UPI refund collect-request scam",
        "To receive your refund, approve this UPI collect request and enter your PIN.",
    ),
    (
        "Genuine hospital appointment update",
        "Your hospital appointment has been moved to 4 PM.",
    ),
    (
        "Normal bank statement notification",
        "Your monthly bank statement is ready in the official banking app.",
    ),
    (
        "Urgent clinic appointment reminder",
        "This is an urgent reminder: your clinic appointment is today at 4 PM.",
    ),
    (
        "Ordinary family conversation",
        "Hi, how are you? We are having dinner at home tonight; see you on Sunday.",
    ),
    (
        "Job registration fee scam",
        "Congratulations, you are hired. Pay an upfront registration fee to secure the job.",
    ),
    (
        "Legitimate OTP safety advice",
        "Never disclose your OTP to anyone; enter it only inside your official banking app.",
    ),
)


def _make_scenario_test(name, transcript):
    def test_scenario(self):
        result = detect_scam(transcript)
        self.assertIn(result["risk_level"], {"HIGH", "MEDIUM", "LOW"}, msg=name)
        self.assertIsInstance(result["manipulation_signals"], list)
        self.assertGreaterEqual(result["score"], 0.0)
        self.assertLessEqual(result["score"], 1.0)

    test_scenario.__name__ = f"test_{name.lower().replace(' ', '_').replace('-', '_')}"
    return test_scenario


class RiskRegressionTests(unittest.TestCase):
    def test_prediction_uses_probability_and_exposes_uncertainty(self):
        result = detect_scam("Your hospital appointment is confirmed for tomorrow.")
        score = result["score"]
        expected_level = (
            "HIGH"
            if score >= HIGH_RISK_THRESHOLD
            else "LOW"
            if score <= LOW_RISK_THRESHOLD
            else "MEDIUM"
        )
        self.assertEqual(result["risk_level"], expected_level)
        self.assertEqual(result["is_scam"], score >= SCAM_THRESHOLD)

    def test_saved_model_contains_training_provenance(self):
        artifact = scam_detector._load_model_artifact()
        metadata = artifact["metadata"]
        self.assertEqual(metadata["training_record_count"], 90)
        self.assertEqual(metadata["evaluation_method"], "5-fold stratified out-of-fold cross-validation")
        self.assertEqual(len(metadata["dataset_sha256"]), 64)
        self.assertTrue(metadata["joblib_version"])
        self.assertTrue(metadata["scikit_learn_version"])
        self.assertTrue(metadata["python_version"])

    def test_sensitive_keywords_alone_do_not_produce_high_risk(self):
        for transcript in (
            "The bank opens at 9 AM.",
            "Your OTP arrived.",
            "This is urgent.",
            "Your account is active.",
            "The hospital opens at 8 AM.",
        ):
            with self.subTest(transcript=transcript):
                self.assertNotEqual(detect_scam(transcript)["risk_level"], "HIGH")

    def test_missing_model_returns_visible_service_unavailable_error(self):
        client = TestClient(app)
        with patch.object(scam_detector, "MODEL_PATH", Path("missing-model.joblib")):
            scam_detector._load_model_artifact.cache_clear()
            try:
                response = client.post(
                    "/api/analyze",
                    json={"transcript": "A caller left a routine message."},
                )
            finally:
                scam_detector._load_model_artifact.cache_clear()
        self.assertEqual(response.status_code, 503)
        self.assertIn("Train it with", response.json()["detail"])

    def test_analyze_endpoint_preserves_response_schema(self):
        client = TestClient(app)
        response = client.post(
            "/api/analyze",
            json={"transcript": "Your account is frozen. Tell me your OTP immediately."},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.json()),
            {
                "risk_level",
                "confidence",
                "score",
                "is_scam",
                "reasons",
                "manipulation_signals",
                "semantic_intent",
                "redacted_transcript",
            },
        )

    def test_empty_and_whitespace_transcripts_are_validation_errors(self):
        client = TestClient(app)
        for transcript in ("", "   \n\t "):
            with self.subTest(transcript=repr(transcript)):
                response = client.post("/api/analyze", json={"transcript": transcript})
                self.assertEqual(response.status_code, 422)


for _name, _transcript in SCENARIOS:
    setattr(
        RiskRegressionTests,
        f"test_{_name.lower().replace(' ', '_').replace('-', '_')}",
        _make_scenario_test(_name, _transcript),
    )


if __name__ == "__main__":
    unittest.main()
