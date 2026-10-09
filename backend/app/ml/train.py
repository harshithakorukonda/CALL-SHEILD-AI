import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import sklearn

from app.ml.evaluation import evaluate_records
from app.ml.pipeline import build_classifier
from app.services.dataset_evaluator import DATASET_PATH, load_dataset


MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "callshield_text_classifier.joblib"


def train_model(dataset_path: Path = DATASET_PATH, model_path: Path = MODEL_PATH) -> dict:
    records = load_dataset(dataset_path)
    evaluation = evaluate_records(records)
    texts = [record["text"] for record in records]
    labels = [record["label"] for record in records]

    model = build_classifier()
    model.fit(texts, labels)
    dataset_hash = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    artifact = {
        "model": model,
        "classes": list(model.named_steps["classifier"].classes_),
        "metadata": {
            "model_type": "word-and-character TF-IDF with balanced Logistic Regression",
            "joblib_version": joblib.__version__,
            "scikit_learn_version": sklearn.__version__,
            "python_version": sys.version.split()[0],
            "trained_at_utc": datetime.now(timezone.utc).isoformat(),
            "training_record_count": len(records),
            "class_distribution": evaluation["class_distribution"],
            "dataset_sha256": dataset_hash,
            "evaluation_method": evaluation["method"],
            "cross_validation_metrics": evaluation["metrics"],
            "risk_thresholds": evaluation["risk_thresholds"],
            "scam_probability_threshold": evaluation["scam_probability_threshold"],
        },
    }

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, model_path)
    return {"model_path": str(model_path), "metadata": artifact["metadata"], "evaluation": evaluation}


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and save the CallShield text classifier.")
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--output", type=Path, default=MODEL_PATH)
    args = parser.parse_args()
    result = train_model(args.dataset, args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
