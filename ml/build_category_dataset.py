"""Build Person 2's processed, train, and held-out test CSV files."""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SEED = 42
CATEGORIES = ["Network", "VPN", "Software", "Hardware", "Password Reset", "Email", "Security"]
TAG_COLUMNS = [f"tag_{i}" for i in range(1, 9)]


def build_huggingface_labels(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, low_memory=False)
    df = raw[raw["language"].astype(str).str.lower().eq("en")].copy()
    df["text"] = (df["subject"].fillna("").astype(str) + " " + df["body"].fillna("")).str.replace(r"\s+", " ", regex=True).str.strip()
    df = df[df["text"].ne("")].drop_duplicates(subset=["text"]).copy()
    df["all_tags"] = df[TAG_COLUMNS].fillna("").astype(str).agg(" | ".join, axis=1)

    trusted = ["Security", "Network", "Hardware", "Software"]
    for tag in trusted:
        df[f"has_{tag.lower()}_tag"] = df[TAG_COLUMNS].eq(tag).any(axis=1)
    flags = [f"has_{tag.lower()}_tag" for tag in trusted]
    df["target_tag_count"] = df[flags].sum(axis=1)

    labeled = df[["text", "all_tags"]].copy()
    labeled["category"] = pd.NA
    labeled["label_method"] = pd.NA

    vpn = df["text"].str.contains(r"\bvpn\b", case=False, regex=True, na=False)
    labeled.loc[vpn, ["category", "label_method"]] = ["VPN", "explicit_keyword"]

    for category in trusted:
        mask = labeled["category"].isna() & df[f"has_{category.lower()}_tag"] & df["target_tag_count"].eq(1)
        labeled.loc[mask, ["category", "label_method"]] = [category, "unique_tag"]

    remaining = labeled["category"].isna()
    password = remaining & df["text"].str.contains(
        r"\bforgot (my )?password\b|\bpassword reset\b|\breset (my )?password\b|\baccount locked\b|\bcredentials expired\b",
        case=False, regex=True, na=False,
    )
    email = remaining & df["text"].str.contains(
        r"\boutlook\b|\bmailbox\b|\bcannot send\b|\bcannot receive\b|\bsend and receive\b",
        case=False, regex=True, na=False,
    )
    labeled.loc[password, ["category", "label_method"]] = ["Password Reset", "explicit_keyword"]
    labeled.loc[email, ["category", "label_method"]] = ["Email", "explicit_keyword"]
    labeled["source"] = "huggingface"
    return labeled.dropna(subset=["category"])


def build_kaggle_labels(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    df = raw.rename(columns={"Document": "text", "Topic_group": "source_label"}).copy()
    df["text"] = df["text"].fillna("").astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    df = df[df["text"].ne("")].drop_duplicates(subset=["text"])
    hardware = df["source_label"].eq("Hardware")
    access = df["source_label"].eq("Access") & df["text"].str.contains(
        r"\bpassword\b|\blogin\b|\bcredential\b|\blocked\b",
        case=False, regex=True, na=False,
    )
    return pd.concat([
        pd.DataFrame({"text": df.loc[hardware, "text"], "all_tags": "", "category": "Hardware", "label_method": "kaggle_hardware", "source": "kaggle"}),
        pd.DataFrame({"text": df.loc[access, "text"], "all_tags": "", "category": "Password Reset", "label_method": "kaggle_access_keyword", "source": "kaggle"}),
    ], ignore_index=True)


def main() -> None:
    real = pd.concat([
        build_huggingface_labels(DATA_DIR / "aa_dataset-tickets-multi-lang-5-2-50-version.csv"),
        build_kaggle_labels(DATA_DIR / "all_tickets_processed_improved_v3.csv"),
    ], ignore_index=True)
    real = real[real["category"].isin(CATEGORIES)].drop_duplicates(subset=["text"]).reset_index(drop=True)
    real.insert(0, "ticket_id", np.arange(1, len(real) + 1))

    train_real, test = train_test_split(real, test_size=0.20, random_state=SEED, stratify=real["category"])
    train_real = train_real.reset_index(drop=True)
    test = test.reset_index(drop=True)

    synthetic_path = DATA_DIR / "synthetic_tickets.csv"
    if synthetic_path.exists():
        synthetic = pd.read_csv(synthetic_path)
        synthetic["all_tags"] = ""
        synthetic["source"] = "synthetic"
        synthetic["label_method"] = "reviewed_template"
        synthetic = synthetic[["text", "all_tags", "category", "label_method", "source"]]
        train = pd.concat([train_real, synthetic], ignore_index=True).drop_duplicates(subset=["text"])
    else:
        train = train_real

    real.to_csv(DATA_DIR / "processed_tickets.csv", index=False)
    train.to_csv(DATA_DIR / "train.csv", index=False)
    test.to_csv(DATA_DIR / "test.csv", index=False)
    print("processed:", real.shape)
    print("train:", train.shape)
    print("test:", test.shape)
    print("train distribution:\n", train["category"].value_counts().reindex(CATEGORIES, fill_value=0))
    print("test distribution:\n", test["category"].value_counts().reindex(CATEGORIES, fill_value=0))


if __name__ == "__main__":
    main()
