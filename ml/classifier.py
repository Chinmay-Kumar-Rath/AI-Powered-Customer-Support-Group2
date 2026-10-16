"""Production-facing category classifier for Person 3 and the backend."""

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import re

from .subcategory_rules import high_confidence_category, predict_subcategory


DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "models" / "category_model.joblib"
MIN_WORDS = 3
MIN_CONFIDENCE = 0.55


def load_artifact(model_path: str | Path = DEFAULT_MODEL_PATH) -> dict[str, Any]:
    """Load the exported vectorizer and classifier artifact."""
    return joblib.load(model_path)


def classify_category(text: str, model_path: str | Path = DEFAULT_MODEL_PATH) -> dict[str, Any]:
    """Classify one ticket and return the agreed integration contract."""
    text = str(text).strip()
    if not text or len(re.findall(r"\b\w+\b", text)) < MIN_WORDS:
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
    confidence = float(probabilities[index])
    if confidence < MIN_CONFIDENCE:
        return {
            "category": "Unknown",
            "sub_category": "Other",
            "category_confidence": round(confidence, 4),
        }
    return {
        "category": category,
        "sub_category": predict_subcategory(text, category),
        "category_confidence": round(confidence, 4),
    }


# Explicit severity words are the strongest signal.  If a requester does not
# provide one, the transparent rules below infer severity from the impact
# described in the ticket.
_EXPLICIT_SEVERITIES = ("Critical", "High", "Medium", "Low")
_SEVERITY_RULES = (
    (
        "Critical",
        re.compile(
            r"company[- ]wide|organisation[- ]wide|organization[- ]wide|"
            r"all users|everyone|entire company|major security incident|"
            r"ransomware|data breach|production (?:is )?down|complete(?:ly)? unavailable|"
            r"critical business system"
        ),
        0.92,
    ),
    (
        "High",
        re.compile(
            r"multiple users|many users|service unavailable|major disruption|"
            r"business operations|system outage|outage|cannot access important|"
            r"down for (?:the )?team"
        ),
        0.86,
    ),
    (
        "Medium",
        re.compile(
            r"individual user|significant issue|workaround|unable to access|"
            r"cannot access|can't access|blocked|intermittent"
        ),
        0.78,
    ),
    (
        "Low",
        re.compile(
            r"minor inconvenience|cosmetic|non[- ]urgent|routine request|"
            r"software installation|how do i|general question"
        ),
        0.82,
    ),
)
_PRIORITY_BY_SEVERITY = {"Critical": "P1", "High": "P2", "Medium": "P3", "Low": "P4"}


def classify_severity(text: str) -> tuple[str, float]:
    """Return severity and confidence using explicit words, then impact rules."""
    text = str(text).strip().lower()

    for severity in _EXPLICIT_SEVERITIES:
        if re.search(rf"\b{severity.lower()}\b", text):
            return severity, 0.99

    for severity, pattern, confidence in _SEVERITY_RULES:
        if pattern.search(text):
            return severity, confidence

    # With no explicit impact signal, Medium is the safest neutral default.
    return "Medium", 0.55


def classify(subject: str | None, description: str, department: str | None = None) -> dict[str, Any]:
    """Backend integration contract used by Person 3 and the API."""
    text = " ".join(part for part in (subject or "", description or "") if part).strip()
    result = classify_category(text)

    severity, severity_confidence = classify_severity(text)
    result.update(
        {
            "severity": severity,
            "severity_confidence": severity_confidence,
            "priority": _PRIORITY_BY_SEVERITY[severity],
        }
    )
    return result
