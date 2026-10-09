import json
from pathlib import Path
from typing import Any


DATASET_PATH = Path(__file__).resolve().parents[2] / "data" / "CALLSHIELD_90_Dataset.json"
EXPECTED_RECORD_COUNT = 90
LABEL_TO_RISK = {"SCAM": "HIGH", "LEGITIMATE": "LOW"}
REQUIRED_FIELDS = {"id", "text", "label", "risk_level", "category", "signals", "source"}


def validate_dataset(records: Any) -> list[dict[str, Any]]:
    if not isinstance(records, list):
        raise ValueError("Dataset must be a JSON array of records.")
    if len(records) != EXPECTED_RECORD_COUNT:
        raise ValueError(f"Expected {EXPECTED_RECORD_COUNT} records, found {len(records)}.")

    seen_ids: set[str] = set()
    validated: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Record {index + 1} must be a JSON object.")
        missing_fields = REQUIRED_FIELDS - record.keys()
        if missing_fields:
            raise ValueError(f"Record {index + 1} is missing fields: {', '.join(sorted(missing_fields))}.")

        record_id = record["id"]
        if not isinstance(record_id, str) or not record_id.strip():
            raise ValueError(f"Record {index + 1} must have a non-empty string id.")
        if record_id in seen_ids:
            raise ValueError(f"Duplicate dataset record id: {record_id}.")
        seen_ids.add(record_id)

        if not isinstance(record["text"], str) or not record["text"].strip():
            raise ValueError(f"Record {record_id} must have non-empty transcript text.")
        if not isinstance(record["label"], str) or record["label"] not in LABEL_TO_RISK:
            raise ValueError(f"Record {record_id} has unsupported label: {record['label']!r}.")
        expected_risk = LABEL_TO_RISK[record["label"]]
        if record["risk_level"] != expected_risk:
            raise ValueError(
                f"Record {record_id} has risk_level {record['risk_level']!r}; "
                f"expected {expected_risk!r} for {record['label']}."
            )
        for field in ("category", "source"):
            if not isinstance(record[field], str) or not record[field].strip():
                raise ValueError(f"Record {record_id} must have a non-empty {field}.")
        if not isinstance(record["signals"], list) or not all(
            isinstance(signal, str) for signal in record["signals"]
        ):
            raise ValueError(f"Record {record_id} signals must be an array of strings.")

        validated.append(record)

    label_counts = {label: sum(record["label"] == label for record in validated) for label in LABEL_TO_RISK}
    if any(count < 2 for count in label_counts.values()):
        raise ValueError(
            "Dataset must contain at least two examples for each label to run stratified validation."
        )

    return validated


def load_dataset(path: Path = DATASET_PATH) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as dataset_file:
        records = json.load(dataset_file)
    return validate_dataset(records)


def evaluate_dataset(records: list[dict[str, Any]]) -> dict[str, Any]:
    from app.ml.evaluation import evaluate_records

    return evaluate_records(validate_dataset(records))
