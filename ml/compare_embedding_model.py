"""Compare the TF-IDF baseline with a sentence-embedding classifier."""

from pathlib import Path
import json

import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CATEGORIES = ["Network", "VPN", "Software", "Hardware", "Password Reset", "Email", "Security"]


def main() -> None:
    train = pd.read_csv(DATA_DIR / "train.csv")
    test = pd.read_csv(DATA_DIR / "test.csv")
    encoder = SentenceTransformer("all-MiniLM-L6-v2")
    x_train = encoder.encode(train["text"].tolist(), batch_size=32, show_progress_bar=True, normalize_embeddings=True)
    x_test = encoder.encode(test["text"].tolist(), batch_size=32, show_progress_bar=True, normalize_embeddings=True)
    model = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)
    model.fit(x_train, train["category"])
    predictions = model.predict(x_test)
    report = classification_report(test["category"], predictions, labels=CATEGORIES, output_dict=True, zero_division=0)
    result = {
        "model": "sentence-transformers/all-MiniLM-L6-v2 + LogisticRegression",
        "accuracy": accuracy_score(test["category"], predictions),
        "macro_f1": report["macro avg"]["f1-score"],
        "train_rows": len(train),
        "test_rows": len(test),
    }
    (DATA_DIR / "embedding_metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
