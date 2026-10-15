# Person 2 data card

## Sources

1. `all_tickets_processed_improved_v3.csv`: 47,837 rows with `Document` and `Topic_group`. Text is short and stopword-reduced. Only Hardware and carefully verified Access rows are reused.
2. `aa_dataset-tickets-multi-lang-5-2-50-version.csv`: 28,587 rows with subject, body, priority, language, queue, and tags. Only English rows are used for category training. The answer column is excluded to avoid leakage.

## Preparation

English Hugging Face rows are combined from subject and body, normalized for whitespace, and deduplicated by text. Hugging Face rows with exactly one trusted category tag are retained. Explicit VPN, password-reset, and email wording supplies the weaker categories. Ambiguous multi-tag rows are excluded. Kaggle Hardware rows are retained; Access rows are retained only when they explicitly indicate password or login trouble.

The original real data is split 80/20 with a fixed random seed of 42 before any synthetic augmentation. Synthetic rows, when present, are added to training only.

## Known limitations

- Hardware is much larger than Email and VPN.
- Some source tags are broad or overlapping.
- Keyword labeling for weak categories requires manual review.
- Synthetic tickets may improve coverage but can introduce repetitive phrasing.
- Logistic Regression probabilities are useful confidence estimates but are not calibrated probabilities.
- The held-out test set is derived from the automatically labelled data; a separate handwritten evaluation set is needed for final external validation.
