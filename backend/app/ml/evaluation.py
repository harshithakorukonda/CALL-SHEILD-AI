from collections import Counter
from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    precision_recall_fscore_support,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from app.ml.pipeline import (
    HIGH_RISK_THRESHOLD,
    LOW_RISK_THRESHOLD,
    RANDOM_STATE,
    SCAM_THRESHOLD,
    build_classifier,
)


LABELS = ("LEGITIMATE", "SCAM")


def evaluate_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    texts = [record["text"] for record in records]
    expected_labels = np.asarray([record["label"] for record in records])
    label_counts = Counter(expected_labels)
    smallest_class = min(label_counts.values())
    folds = min(5, smallest_class)
    if folds < 2:
        raise ValueError("Stratified cross-validation requires at least two examples per label.")

    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=RANDOM_STATE)
    out_of_fold_probabilities = cross_val_predict(
        build_classifier(),
        texts,
        expected_labels,
        cv=splitter,
        method="predict_proba",
    )
    classes = np.asarray(sorted(label_counts))
    scam_column = int(np.where(classes == "SCAM")[0][0])
    scam_probabilities = out_of_fold_probabilities[:, scam_column]
    predicted_labels = np.where(scam_probabilities >= SCAM_THRESHOLD, "SCAM", "LEGITIMATE")

    matrix = confusion_matrix(expected_labels, predicted_labels, labels=LABELS)
    true_negative, false_positive, false_negative, true_positive = matrix.ravel()
    class_precision, class_recall, class_f1, class_support = precision_recall_fscore_support(
        expected_labels,
        predicted_labels,
        labels=LABELS,
        zero_division=0,
    )
    class_metrics = {
        label: {
            "precision": float(class_precision[index]),
            "recall": float(class_recall[index]),
            "f1": float(class_f1[index]),
            "support": int(class_support[index]),
        }
        for index, label in enumerate(LABELS)
    }
    predictions = []
    for record, expected, predicted, probability in zip(
        records, expected_labels, predicted_labels, scam_probabilities, strict=True
    ):
        predicted_risk = (
            "HIGH"
            if probability >= HIGH_RISK_THRESHOLD
            else "LOW"
            if probability <= LOW_RISK_THRESHOLD
            else "MEDIUM"
        )
        predictions.append(
            {
                "id": record["id"],
                "category": record["category"],
                "text": record["text"],
                "expected_label": str(expected),
                "predicted_label": str(predicted),
                "expected_risk_level": record["risk_level"],
                "predicted_risk_level": predicted_risk,
                "scam_probability": float(probability),
                "correct": bool(expected == predicted),
            }
        )

    return {
        "method": f"{folds}-fold stratified out-of-fold cross-validation",
        "random_state": RANDOM_STATE,
        "scam_probability_threshold": SCAM_THRESHOLD,
        "risk_thresholds": {
            "low_max": LOW_RISK_THRESHOLD,
            "high_min": HIGH_RISK_THRESHOLD,
        },
        "record_count": len(records),
        "class_distribution": {
            label: {"count": int(label_counts.get(label, 0)), "fraction": label_counts.get(label, 0) / len(records)}
            for label in LABELS
        },
        "confusion_matrix": {
            "labels": list(LABELS),
            "rows_expected_columns_predicted": matrix.tolist(),
            "true_positives": int(true_positive),
            "false_positives": int(false_positive),
            "false_negatives": int(false_negative),
            "true_negatives": int(true_negative),
        },
        "metrics": {
            "accuracy": float(accuracy_score(expected_labels, predicted_labels)),
            "precision": float(precision_score(expected_labels, predicted_labels, pos_label="SCAM", zero_division=0)),
            "recall": float(recall_score(expected_labels, predicted_labels, pos_label="SCAM", zero_division=0)),
            "f1": float(f1_score(expected_labels, predicted_labels, pos_label="SCAM", zero_division=0)),
        },
        "class_metrics": class_metrics,
        "false_positives": [item for item in predictions if item["expected_label"] == "LEGITIMATE" and item["predicted_label"] == "SCAM"],
        "false_negatives": [item for item in predictions if item["expected_label"] == "SCAM" and item["predicted_label"] == "LEGITIMATE"],
        "risk_level_mismatches": [item for item in predictions if item["expected_risk_level"] != item["predicted_risk_level"]],
        "predictions": predictions,
    }
