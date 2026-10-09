import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from app.services.semantic_analyzer import analyze_transcript

RANDOM_STATE = 42
SCAM_THRESHOLD = 0.5
HIGH_RISK_THRESHOLD = 0.6
LOW_RISK_THRESHOLD = 0.4


class DomainFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extracts high-level domain semantic features to assist ML classification."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        features = []
        for text in X:
            analysis = analyze_transcript(str(text))
            ctx = analysis.get("risk_context", {})
            safe_text = str(text).lower()
            
            # Check for safe advice or routine non-scam phrases
            safe_otp_advice = any(phrase in safe_text for phrase in ["never tell", "don't share", "enter the otp only inside", "only inside your official"])
            safe_no_payment = "no payment is needed" in safe_text or "no payment required" in safe_text
            safe_routine = any(phrase in safe_text for phrase in ["dispatched and should arrive", "reached home safely", "community meeting", "received your insurance claim"])

            safe_score = 1.0 if (safe_otp_advice or safe_no_payment or safe_routine) else 0.0

            has_ask_or_threat = bool(
                ctx.get("credential_request")
                or ctx.get("payment_request")
                or ctx.get("coercion")
                or ctx.get("impersonation")
                or ctx.get("deception")
            )

            row = [
                1.0 if ctx.get("credential_request") else 0.0,
                1.0 if ctx.get("payment_request") else 0.0,
                1.0 if ctx.get("impersonation") else 0.0,
                1.0 if ctx.get("deception") else 0.0,
                1.0 if ctx.get("coercion") else 0.0,
                1.0 if ctx.get("coercive_pressure") else 0.0,
                1.0 if (ctx.get("urgency") and has_ask_or_threat) else 0.0,
                1.0 if ctx.get("distress") else 0.0,
                safe_score,
                len(analysis.get("manipulation_signals", [])) / 5.0,
            ]
            features.append(row)
        return np.array(features, dtype=np.float64)


def build_classifier() -> Pipeline:
    features = FeatureUnion(
        [
            (
                "domain_features",
                DomainFeatureExtractor(),
            ),
            (
                "word_tfidf",
                TfidfVectorizer(
                    analyzer="word",
                    ngram_range=(1, 2),
                    min_df=1,
                    sublinear_tf=True,
                    strip_accents="unicode",
                ),
            ),
            (
                "character_tfidf",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    min_df=1,
                    sublinear_tf=True,
                    strip_accents="unicode",
                ),
            ),
        ]
    )
    return Pipeline(
        [
            ("features", features),
            (
                "classifier",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=2000,
                    random_state=RANDOM_STATE,
                    solver="liblinear",
                    C=2.0,
                ),
            ),
        ]
    )

