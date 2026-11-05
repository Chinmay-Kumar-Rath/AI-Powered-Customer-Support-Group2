from pathlib import Path
import json

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

DATA_FILE = Path("data/severity_gold_labels.csv")
MODEL_FILE = Path("ml/severity_model.joblib")
REPORT_FILE = Path("data/severity_model_evaluation.json")
LABELS = ["Low", "Medium", "High", "Critical"]
MIN_PER_CLASS = 10

def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Reviewed dataset not found: {DATA_FILE}")

    data = pd.read_csv(DATA_FILE)
    required = {"text", "reviewer_2_severity"}
    if not required.issubset(data.columns):
        raise ValueError(f"Expected columns: {sorted(required)}")

    data = data.dropna(subset=["text", "reviewer_2_severity"]).copy()
    data["text"] = data["text"].astype(str).str.strip()
    data["severity"] = data["reviewer_2_severity"].astype(str).str.strip()
    data = data[
        data["text"].str.len().ge(5)
        & data["severity"].isin(LABELS)
    ].drop_duplicates(subset=["ticket_id"])

    print("Valid reviewed tickets:", len(data))
    print("Severity counts:")
    print(data["severity"].value_counts().reindex(LABELS, fill_value=0).to_string())

    counts = data["severity"].value_counts()
    if len(data) < 80 or any(counts.get(label, 0) < MIN_PER_CLASS for label in LABELS):
        print(
            "\nNOT TRAINED: need at least 80 valid reviewed tickets "
            "and at least 10 examples per severity class."
        )
        print("Continue collecting and validating independent labels first.")
        return

    X_train, X_test, y_train, y_test = train_test_split(
        data["text"],
        data["severity"],
        test_size=0.20,
        random_state=42,
        stratify=data["severity"],
    )

    model = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=50000,
            strip_accents="unicode",
            sublinear_tf=True,
        )),
        ("classifier", LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=42,
        )),
    ])

    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)

    print(f"\nAccuracy: {accuracy:.3%}")
    print("\nConfusion matrix (rows=true, columns=predicted):")
    print(confusion_matrix(y_test, predictions, labels=LABELS))
    print("\nClassification report:")
    print(classification_report(
        y_test, predictions, labels=LABELS, zero_division=0
    ))

    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_FILE)

    report = {
        "accuracy": float(accuracy),
        "test_size": int(len(y_test)),
        "train_size": int(len(y_train)),
        "labels": LABELS,
        "confusion_matrix": confusion_matrix(
            y_test, predictions, labels=LABELS
        ).tolist(),
        "classification_report": classification_report(
            y_test, predictions, labels=LABELS,
            output_dict=True, zero_division=0
        ),
        "label_source": str(DATA_FILE),
        "random_state": 42,
        "note": "Results are only as reliable as the reviewed labels."
    }
    REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\nSaved model:", MODEL_FILE)
    print("Saved evaluation:", REPORT_FILE)
    if accuracy >= 0.85:
        print("Accuracy meets the 85% target on this held-out split.")
    else:
        print("Accuracy is below the 85% target on this held-out split.")

if __name__ == "__main__":
    main()
