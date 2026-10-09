import argparse
import json
from pathlib import Path
from typing import Any

from app.ml.evaluation import evaluate_records
from app.services.dataset_evaluator import DATASET_PATH, load_dataset


def _report_summary(report: dict[str, Any]) -> str:
    metrics = report["metrics"]
    matrix = report["confusion_matrix"]
    distribution = report["class_distribution"]
    lines = [
        "CallShield text classifier — stratified out-of-fold evaluation",
        f"Method: {report['method']} (random_state={report['random_state']})",
        f"Dataset: {report['record_count']} records; SCAM={distribution['SCAM']['count']}, LEGITIMATE={distribution['LEGITIMATE']['count']}",
        (
            f"Binary SCAM threshold={report['scam_probability_threshold']:.2f}; "
            f"risk thresholds={report['risk_thresholds']}"
        ),
        f"Accuracy={metrics['accuracy']:.4f} Precision={metrics['precision']:.4f} Recall={metrics['recall']:.4f} F1={metrics['f1']:.4f}",
        "Per-class metrics (precision / recall / F1 / support):",
        *[
            f"  {label}: {values['precision']:.4f} / {values['recall']:.4f} / {values['f1']:.4f} / {values['support']}"
            for label, values in report["class_metrics"].items()
        ],
        (
            "Confusion matrix (rows expected LEGITIMATE,SCAM; columns predicted LEGITIMATE,SCAM): "
            f"{matrix['rows_expected_columns_predicted']}"
        ),
        f"False positives ({matrix['false_positives']}):",
    ]
    lines.extend(
        f"  {item['id']} [{item['category']}] p_scam={item['scam_probability']:.3f}: {item['text']}"
        for item in report["false_positives"]
    )
    if not report["false_positives"]:
        lines.append("  none")
    lines.append(f"False negatives ({matrix['false_negatives']}):")
    lines.extend(
        f"  {item['id']} [{item['category']}] p_scam={item['scam_probability']:.3f}: {item['text']}"
        for item in report["false_negatives"]
    )
    if not report["false_negatives"]:
        lines.append("  none")
    lines.append(f"Risk-level mismatches with expected HIGH/LOW: {len(report['risk_level_mismatches'])}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate CallShield using stratified out-of-fold predictions.")
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--output", type=Path, help="Optional path to save the full JSON report.")
    args = parser.parse_args()

    report = evaluate_records(load_dataset(args.dataset))
    report["dataset"] = str(args.dataset)
    print(_report_summary(report))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Full report saved to {args.output}")


if __name__ == "__main__":
    main()
