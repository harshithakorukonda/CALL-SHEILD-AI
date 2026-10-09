# CallShield AI

CallShield AI is a transcript-based scam-risk prototype. It analyzes text entered manually or captured using the browser speech-recognition feature. It does not intercept cellular calls, and the microphone feature does not automatically send transcripts for analysis.

## Backend classifier

The backend uses a scikit-learn text classifier with word and character TF-IDF features and balanced Logistic Regression. It predicts from the loaded model artifact; it does not contain hardcoded sentence-to-label responses. The local signal analyzer adds explanatory signal names but does not decide the classifier's prediction or call an external semantic-AI service.

The included `backend/data/CALLSHIELD_90_Dataset.json` has 90 synthetic examples (60 SCAM, 30 LEGITIMATE). They are used for reproducible stratified five-fold out-of-fold evaluation and for fitting the persisted model after evaluation. Every example is held out from the fold-specific model that generates its evaluation prediction. The report is an estimate from this small dataset, not a final independent test set, and the model is retrained on all 90 examples for application inference.

These synthetic examples are too few to establish production reliability or generalization to all scam styles, languages, and real call transcripts. Collect independently sourced and reviewed data, with a separate held-out test set, before making production claims. The binary SCAM threshold is fixed at 0.50; risk is HIGH at 0.70 or above, LOW at 0.35 or below, and MEDIUM otherwise. These thresholds are declared in code rather than tuned and reported on the same evaluation records. MEDIUM indicates an uncertain model score.

## Install

Run these commands from the repository root in PowerShell:

```powershell
cd backend
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If your virtual environment is not at the repository root, replace the Python executable path with your environment's Python. From a fresh clone without a virtual environment, create one first:

```powershell
cd ..
py -m venv .venv
cd backend
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Train or retrain

From `backend`:

```powershell
..\.venv\Scripts\python.exe -m app.ml.train
```

This validates the dataset, prints the stratified out-of-fold metrics, fits the final classifier on all 90 records, and saves `backend/models/callshield_text_classifier.joblib`. An alternate dataset or artifact path can be supplied with `--dataset` and `--output`.

## Evaluate

From `backend`:

```powershell
..\.venv\Scripts\python.exe -m app.ml.evaluate
```

Optionally save all fold predictions, class-specific metrics, false positives, and false negatives:

```powershell
..\.venv\Scripts\python.exe -m app.ml.evaluate --output reports/callshield-evaluation.json
```

Evaluation reruns stratified out-of-fold validation and does not evaluate on training predictions. Do not use these 90 examples to claim independent test performance.

## Tests

Train the artifact first, then from `backend` run:

```powershell
..\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Regression scenarios exercise the saved-model inference path and validate the response/risk contract. They do not hardcode the expected model result for each individual synthetic transcript.

## Start the backend

From `backend`:

```powershell
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

The manual analysis API is `POST http://127.0.0.1:8001/api/analyze`. If the model artifact is missing or cannot be loaded, the API returns HTTP 503 with an explicit error instead of fabricating a prediction.

## Start the frontend

In another PowerShell terminal:

```powershell
cd frontend
npm install
npm run dev
```

The default frontend API base URL is `http://localhost:8001`; set `VITE_API_URL` if your backend is running at another address.
