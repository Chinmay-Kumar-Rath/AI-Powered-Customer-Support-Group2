"""Train the final Person 2 category model from exported train/test CSVs."""

from pathlib import Path
import json

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from subcategory_rules import SUBCATEGORY_RULES


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "ml" / "models"
SEED = 42
CATEGORIES = ["Network", "VPN", "Software", "Hardware", "Password Reset", "Email", "Security"]


def main() -> None:
    train = pd.read_csv(DATA_DIR / "train.csv")
    test = pd.read_csv(DATA_DIR / "test.csv")
    vectorizer = TfidfVectorizer(lowercase=True, strip_accents="unicode", ngram_range=(1, 2), min_df=2, max_features=100_000, sublinear_tf=True)
    x_train = vectorizer.fit_transform(train["text"])
    x_test = vectorizer.transform(test["text"])
    model = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=SEED)
    model.fit(x_train, train["category"])
    predictions = model.predict(x_test)
    report = classification_report(test["category"], predictions, labels=CATEGORIES, output_dict=True, zero_division=0)
    accuracy = accuracy_score(test["category"], predictions)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"vectorizer": vectorizer, "model": model, "categories": CATEGORIES, "subcategory_rules": SUBCATEGORY_RULES, "seed": SEED}, MODEL_DIR / "category_model.joblib")
    pd.DataFrame(report).transpose().to_csv(DATA_DIR / "category_evaluation_report.csv")
    with (DATA_DIR / "category_metrics.json").open("w", encoding="utf-8") as file:
        json.dump({"accuracy": accuracy, "macro_f1": report["macro avg"]["f1-score"], "train_rows": len(train), "test_rows": len(test)}, file, indent=2)

    cm = confusion_matrix(test["category"], predictions, labels=CATEGORIES)
    plt.figure(figsize=(10, 7))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=CATEGORIES, yticklabels=CATEGORIES)
    plt.xlabel("Predicted category")
    plt.ylabel("True category")
    plt.title("Category confusion matrix")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(DATA_DIR / "category_confusion_matrix.png", dpi=160)
    plt.close()

    print(f"accuracy={accuracy:.4f}")
    print(f"macro_f1={report['macro avg']['f1-score']:.4f}")
    print(f"saved={MODEL_DIR / 'category_model.joblib'}")


if __name__ == "__main__":
    main()
