# Category model comparison

The same exported train/test split was used for both models. Hardware was capped at 2,500 real rows, synthetic examples were included in training only, and the test set contains real rows that were not augmented. The final classifier also applies high-confidence phrase rules before the statistical model.

| Model | Accuracy | Macro-F1 | Decision |
|---|---:|---:|---|
| TF-IDF (unigrams + bigrams) + Logistic Regression | 0.9503 | 0.8492 | Selected for integration |
| Sentence embeddings (`all-MiniLM-L6-v2`) + Logistic Regression | 0.9548 | 0.8976 | Best offline macro-F1 |

The embedding model performed better on the balanced held-out comparison, especially on macro-F1. TF-IDF remains selected for integration because it is much smaller and simpler to run in the backend, while high-confidence rules handle obvious cases. The embedding result is retained as the stronger candidate for a later model upgrade.

The comparison is based on automatically labelled data, so the metrics should be rechecked against the separate handwritten evaluation set when Person 4 supplies it.
