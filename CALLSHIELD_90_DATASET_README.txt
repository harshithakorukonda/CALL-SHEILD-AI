CALLSHIELD AI — 90 synthetic transcript examples

Exactly 90 examples:
- 60 SCAM / HIGH examples across 12 scam categories.
- 30 LEGITIMATE / LOW examples to measure false positives.

Formats:
- JSON: structured dataset
- JSONL: one JSON object per line
- CSV: spreadsheet-friendly
- README: usage notes

Important limitations:
- These are synthetic examples, not real call recordings or a validated production dataset.
- Adding examples does not automatically train a model.
- Use them for evaluation, rule tuning, or a training pipeline that you explicitly implement.
- Keep separate train/validation/test splits and add unseen paraphrases.
- Never use real OTPs, passwords, PINs, card details, or private recordings.
- Labels are expected labels, not guarantees of current detector predictions.
- Do not classify urgency, bank mentions, or OTP references alone as high risk.

Evaluation and training:
- From the backend directory, run `python -m app.ml.evaluate` for stratified out-of-fold metrics, including class-specific results, false positives, false negatives, and risk-level mismatches.
- Run `python -m app.ml.train` to evaluate and fit the TF-IDF/Logistic Regression classifier, then save the fitted artifact under `backend/models/`.
- Run `python -m unittest discover -s tests -v` after training to validate data, evaluation reporting, and the trained-model inference/API path.
- The evaluation predictions are out-of-fold estimates; the final artifact is trained on all 90 records. This small synthetic dataset is not an independent final test set and is not adequate to establish production reliability.
