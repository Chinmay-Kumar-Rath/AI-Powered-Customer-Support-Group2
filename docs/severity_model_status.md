# Severity Model Status

## Current implementation

- Severity classification rules are implemented in `ml/classifier.py`.
- Priority mapping is implemented: Critical -> P1, High -> P2, Medium -> P3, Low -> P4.
- IT and Finance department escalation has been checked.
- Severity tests: 11 passed.
- Backend tests: 8 passed.
- Severity labeling guidance is available in `docs/severity_labeling_guide.md`.

## Machine-learning evaluation status

The severity ML training script expects `data/severity_gold_labels.csv`.
That verified dataset is not currently available, so the ML model has not been validly trained and evaluated using the required gold labels.

An older evaluation report recorded 35% accuracy on 20 test rows. Its label source was `data/severity_review_independent_v2_completed.csv`. Those labels were not reliable independent ground truth, so the result must not be used as a valid estimate of model performance.

The existing `ml/severity_model.joblib` and `data/severity_model_evaluation.json` may be artifacts from that earlier experiment. Do not represent them as a validated production severity model or a verified evaluation.

## Review data

`data/severity_review_batch20_terminal.csv` contains provisional severity suggestions and notes for a 20-ticket review exercise. These entries are not independent reviewer-confirmed labels and must not be used as gold labels for model training or final evaluation.

## Remaining work

1. Obtain independently reviewed severity labels using the labeling guide.
2. Resolve uncertain and conflicting labels with a human reviewer.
3. Build `data/severity_gold_labels.csv` from verified labels only.
4. Train and evaluate the severity model using a documented, reproducible split.
5. Report accuracy, confusion matrix, per-class precision and recall.
6. Confirm that the model meets the 85% accuracy target before claiming that it does.
