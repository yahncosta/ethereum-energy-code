from datasets import Dataset, DatasetDict, load_dataset

from preprocessing.column_selection import drop_raw_columns, select_and_rename_columns
from preprocessing.client_parsing import drop_unresolvable_rows, parse_clients_and_arch
from preprocessing.cloud_classification import assign_cloud_provider

REPO_ID = "yhackspacher/ethereum-crawl"
SOURCE_CONFIG = "final_visits_merged"
TARGET_CONFIG = "pre_train_data"
SOURCE_SPLIT = "train"


def main():
    print("=" * 60)
    print("STEP 1 — Loading merged crawl dataset")
    print("=" * 60)
    df = load_dataset(REPO_ID, name=SOURCE_CONFIG, split=SOURCE_SPLIT).to_pandas()
    print(f"  Loaded: {len(df)} rows x {len(df.columns)} columns")

    print("\n" + "=" * 60)
    print("STEP 2 — Selecting and renaming columns")
    print("=" * 60)
    df = select_and_rename_columns(df)
    print(f"  Selected columns: {list(df.columns)}")

    print("\n" + "=" * 60)
    print("STEP 3 — Parsing clients and architecture from AgentVersion")
    print("=" * 60)
    df = parse_clients_and_arch(df)

    print("\n" + "=" * 60)
    print("STEP 4 — Dropping rows with unresolvable clients or architecture")
    print("=" * 60)
    df = drop_unresolvable_rows(df)

    print("\n" + "=" * 60)
    print("STEP 5 — Dropping raw AgentVersion and Protocols columns")
    print("=" * 60)
    df = drop_raw_columns(df)
    print(f"  Remaining columns: {list(df.columns)}")

    print("\n" + "=" * 60)
    print("STEP 6 — Classifying IPs by cloud provider")
    print("=" * 60)
    df = assign_cloud_provider(df)

    print("\n" + "=" * 60)
    print(f"STEP 7 — Pushing to {REPO_ID}  [config: {TARGET_CONFIG}]")
    print("=" * 60)
    DatasetDict({SOURCE_SPLIT: Dataset.from_pandas(df, preserve_index=False)}).push_to_hub(
        REPO_ID,
        config_name=TARGET_CONFIG,
        commit_message="Overwrite pre_train_data: client parsing, hw_arch, cloud_provider",
    )
    print(f"  Done. pre_train_data: {len(df)} rows x {len(df.columns)} columns.")


if __name__ == "__main__":
    main()