import unittest

from app.services.dataset_evaluator import evaluate_dataset, load_dataset, validate_dataset


class DatasetEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = load_dataset()
        cls.report = evaluate_dataset(cls.records)

    def test_dataset_contains_90_records_with_unique_ids(self):
        self.assertEqual(len(self.records), 90)
        self.assertEqual(len({record["id"] for record in self.records}), 90)

    def test_dataset_contains_expected_class_balance(self):
        labels = [record["label"] for record in self.records]
        self.assertEqual(labels.count("SCAM"), 60)
        self.assertEqual(labels.count("LEGITIMATE"), 30)

    def test_all_records_are_included_in_evaluation(self):
        self.assertEqual(
            {item["id"] for item in self.report["predictions"]},
            {record["id"] for record in self.records},
        )

    def test_out_of_fold_metrics_match_confusion_matrix(self):
        matrix = self.report["confusion_matrix"]
        metrics = self.report["metrics"]
        true_negative = matrix["true_negatives"]
        false_positive = matrix["false_positives"]
        false_negative = matrix["false_negatives"]
        true_positive = matrix["true_positives"]
        total = true_negative + false_positive + false_negative + true_positive
        expected_precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0
        expected_recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0
        expected_f1 = 2 * expected_precision * expected_recall / (expected_precision + expected_recall) if expected_precision + expected_recall else 0

        self.assertEqual(total, len(self.records))
        self.assertEqual(self.report["method"], "5-fold stratified out-of-fold cross-validation")
        self.assertAlmostEqual(
            metrics["accuracy"],
            (true_positive + true_negative) / total,
        )
        self.assertAlmostEqual(metrics["precision"], expected_precision)
        self.assertAlmostEqual(metrics["recall"], expected_recall)
        self.assertAlmostEqual(metrics["f1"], expected_f1)

    def test_report_includes_metrics_for_both_labels(self):
        class_metrics = self.report["class_metrics"]
        self.assertEqual(set(class_metrics), {"SCAM", "LEGITIMATE"})
        self.assertEqual(class_metrics["SCAM"]["support"], 60)
        self.assertEqual(class_metrics["LEGITIMATE"]["support"], 30)
        for values in class_metrics.values():
            for metric in ("precision", "recall", "f1"):
                self.assertGreaterEqual(values[metric], 0.0)
                self.assertLessEqual(values[metric], 1.0)

    def test_invalid_dataset_record_is_rejected(self):
        malformed = [dict(record) for record in self.records]
        malformed[0]["risk_level"] = "LOW"
        with self.assertRaisesRegex(ValueError, "risk_level"):
            validate_dataset(malformed)

if __name__ == "__main__":
    unittest.main()
