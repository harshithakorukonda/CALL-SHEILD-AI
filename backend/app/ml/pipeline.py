from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline


RANDOM_STATE = 42
SCAM_THRESHOLD = 0.5
HIGH_RISK_THRESHOLD = 0.7
LOW_RISK_THRESHOLD = 0.35


def build_classifier() -> Pipeline:
    features = FeatureUnion(
        [
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
                ),
            ),
        ]
    )
