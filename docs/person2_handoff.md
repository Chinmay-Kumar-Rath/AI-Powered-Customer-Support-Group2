# Person 2 handoff

## Rebuild commands

From the repository root:

```powershell
.\venv\Scripts\python.exe ml\generate_synthetic_tickets.py
.\venv\Scripts\python.exe ml\build_category_dataset.py
.\venv\Scripts\python.exe ml\train_category_model.py
```

The optional embedding comparison is:

```powershell
.\venv\Scripts\python.exe ml\compare_embedding_model.py
```

## Integration contract

```python
from ml.classifier import classify_category

result = classify_category(subject + " " + description)
```

The result contains `category`, `sub_category`, and `category_confidence`. Empty text returns `Unknown` with confidence `0.0`.

## Data boundary

The test set is created before synthetic augmentation. Synthetic rows are present only in `train.csv`; `test.csv` contains only the held-out real rows.

## Human review still required

Review `data/manual_audit_sample.csv`. Fill `reviewed_category`, change `review_status` to `reviewed`, and record disagreements in `review_notes`. This is the remaining human quality-control step.
