"""Production-facing category classifier for Person 3 and the backend."""

from pathlib import Path
from typing import Any

import joblib
import numpy as np

from .subcategory_rules import high_confidence_category, predict_subcategory


DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "models" / "category_model.joblib"


def load_artifact(model_path: str | Path = DEFAULT_MODEL_PATH) -> dict[str, Any]:
    """Load the exported vectorizer and classifier artifact."""
    return joblib.load(model_path)


def classify_category(text: str, model_path: str | Path = DEFAULT_MODEL_PATH) -> dict[str, Any]:
    """Classify one ticket and return the agreed integration contract."""
    text = str(text).strip()
    if not text or len(text.split()) < 2:
        return {
            "category": "Unknown",
            "sub_category": "Other",
            "category_confidence": 0.0,
        }

    rule_category = high_confidence_category(text)
    if rule_category is not None:
        return {
            "category": rule_category,
            "sub_category": predict_subcategory(text, rule_category),
            "category_confidence": 0.99,
        }

    artifact = load_artifact(model_path)
    vectorizer = artifact["vectorizer"]
    model = artifact["model"]
    features = vectorizer.transform([text])
    probabilities = model.predict_proba(features)[0]
    index = int(np.argmax(probabilities))
    category = str(model.classes_[index])
    return {
        "category": category,
        "sub_category": predict_subcategory(text, category),
        "category_confidence": round(float(probabilities[index]), 4),
    }
