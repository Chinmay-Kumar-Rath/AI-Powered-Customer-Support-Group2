"""Create the 50-per-source manual audit sample required by Person 2."""

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SEED = 42


def main() -> None:
    kaggle = pd.read_csv(DATA_DIR / "all_tickets_processed_improved_v3.csv")
    kaggle = kaggle.rename(columns={"Document": "text", "Topic_group": "source_label"})
    kaggle_sample = kaggle.sample(50, random_state=SEED).assign(source="kaggle")

    hf = pd.read_csv(DATA_DIR / "aa_dataset-tickets-multi-lang-5-2-50-version.csv", low_memory=False)
    hf = hf[hf["language"].astype(str).str.lower().eq("en")].copy()
    hf["text"] = (hf["subject"].fillna("").astype(str) + " " + hf["body"].fillna("")).str.replace(r"\s+", " ", regex=True).str.strip()
    hf_sample = hf.sample(50, random_state=SEED).assign(source="huggingface", source_label="")

    sample = pd.concat([
        kaggle_sample[["source", "text", "source_label"]],
        hf_sample[["source", "text", "source_label"]],
    ], ignore_index=True)
    sample["reviewed_category"] = ""
    sample["review_status"] = "pending"
    sample["review_notes"] = ""
    sample.to_csv(DATA_DIR / "manual_audit_sample.csv", index=False)
    print(f"Wrote {len(sample)} rows to {DATA_DIR / 'manual_audit_sample.csv'}")


if __name__ == "__main__":
    main()
