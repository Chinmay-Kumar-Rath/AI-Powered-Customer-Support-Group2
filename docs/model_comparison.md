# Category model comparison

The same exported train/test split was used for both models. Synthetic examples were included in training only. The test set contains 4,059 real rows and was not augmented.

| Model | Accuracy | Macro-F1 | Decision |
|---|---:|---:|---|
| TF-IDF (unigrams + bigrams) + Logistic Regression | 0.9638 | 0.8538 | Selected |
| Sentence embeddings (`all-MiniLM-L6-v2`) + Logistic Regression | 0.9542 | 0.8457 | Not selected |

TF-IDF is selected because it performed better on both accuracy and macro-F1 and is substantially simpler to run and integrate for this project.

The comparison is based on automatically labelled data, so the metrics should be rechecked against the separate handwritten evaluation set when Person 4 supplies it.
