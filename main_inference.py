import pandas as pd
from datasets import load_dataset, Dataset, DatasetDict

from cloud_inference import infer_cloud_features
from ccri_inference import infer_ccri_features

REPO_ID       = "yhackspacher/ethereum-crawl"
SOURCE_CONFIG = "pre_train_data"
TARGET_CONFIG = "train_data"
SOURCE_SPLIT  = "train"

print("=" * 60)
print("STEP 1 — Loading base crawl dataset")
print("=" * 60)

dataset = load_dataset(REPO_ID, name=SOURCE_CONFIG, split=SOURCE_SPLIT)
df = dataset.to_pandas()

print(f"Loaded: {len(df)} rows x {len(df.columns)} columns")
print(f"Columns: {df.columns.tolist()}\n")

print("=" * 60)
print("STEP 2 — Cloud hosting inference")
print("=" * 60)

df = infer_cloud_features(df)

cloud_count = int(df["is_cloud_hosted"].sum())
total = len(df)
print(f"Cloud-hosted: {cloud_count}/{total} ({100 * cloud_count / total:.1f}%)")
print(df["cloud_provider"].value_counts().to_string())
print()

print("=" * 60)
print("STEP 3 — CCRI hardware & power inference")
print("=" * 60)

df = infer_ccri_features(df)

measured = int(df["ccri_measured"].sum())
print(f"CCRI coverage: {measured}/{total} rows ({100 * measured / total:.1f}%)")

unmeasured_pairs = (
    df[~df["ccri_measured"]]
    .groupby(["consensus_client", "execution_client"])
    .size()
    .sort_values(ascending=False)
)
print("Unmeasured client pairs:")
print(unmeasured_pairs.to_string())
print()

print("=" * 60)
print("FINAL DATASET SUMMARY")
print("=" * 60)
print(f"Shape: {df.shape}")
print(f"\nColumns ({len(df.columns)}):")
for col in df.columns:
    n_null = int(df[col].isna().sum())
    print(f"  {col:<40} nulls: {n_null}/{total}")
print()

print("=" * 60)
print(f"PUSHING to {REPO_ID}  [config: {TARGET_CONFIG}]")
print("=" * 60)

DatasetDict({SOURCE_SPLIT: Dataset.from_pandas(df, preserve_index=False)}).push_to_hub(
    REPO_ID,
    config_name=TARGET_CONFIG,
    commit_message=f"Update {TARGET_CONFIG} with cloud and CCRI inferred features",
)

print(f"Done. Dataset pushed to: https://huggingface.co/datasets/{REPO_ID}")