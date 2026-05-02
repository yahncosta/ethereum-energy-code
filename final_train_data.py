from datasets import load_dataset, DatasetDict
import pandas as pd

REPO_ID = "yhackspacher/ethereum-crawl"

COLUMNS_TO_KEEP = {
    "ip": "ip",
    "AgentVersion_cl": "AgentVersion_cl",
    "attnets_num_cl": "attnets_num",
    "syncnets_cl": "syncnets",
    "AgentVersion_el": "AgentVersion_el",
    "Protocols_cl": "Protocols_cl",
    "Protocols_el": "Protocols_el"
}

print("Loading final_visits_merged...")
ds = load_dataset(REPO_ID, name="final_visits_merged", split="train")
print(f"  Rows: {len(ds)}")
print(f"  Columns: {ds.column_names}")

df = ds.to_pandas()

missing = [c for c in COLUMNS_TO_KEEP if c not in df.columns]
if missing:
    print(f"  Warning - columns not found: {missing}")

df = df[[c for c in COLUMNS_TO_KEEP if c in df.columns]]
df = df.rename(columns=COLUMNS_TO_KEEP)

print(f"\nFinal columns: {list(df.columns)}")

print("Pushing to train_data...")
DatasetDict({"train": __import__('datasets').Dataset.from_pandas(df, preserve_index=False)}).push_to_hub(
    REPO_ID,
    config_name="train_data",
    commit_message="Overwrite train_data: select and rename columns from final_visits_merged",
)

print(f"Done. train_data: {len(df)} rows x {len(df.columns)} columns.")