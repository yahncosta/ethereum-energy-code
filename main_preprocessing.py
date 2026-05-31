from datasets import Dataset, DatasetDict, load_dataset

from preprocessing.column_selection import select_and_rename_columns, drop_and_clean_rows
from preprocessing.client_parsing import parse_clients_and_arch
from preprocessing.cloud_classification import assign_cloud_provider
from preprocessing.syncnets_parsing import parse_syncnets

REPO_ID = "yhackspacher/ethereum-crawl"
SOURCE_CONFIG = "final_visits_merged"
TARGET_CONFIG = "pre_train_data"
SOURCE_SPLIT = "train"


def main():
    df = load_dataset(REPO_ID, name=SOURCE_CONFIG, split=SOURCE_SPLIT).to_pandas()
    df = select_and_rename_columns(df)
    df = parse_syncnets(df)
    df = parse_clients_and_arch(df)
    df = drop_and_clean_rows(df)
    df = assign_cloud_provider(df)

    DatasetDict({SOURCE_SPLIT: Dataset.from_pandas(df, preserve_index=False)}).push_to_hub(
        REPO_ID,
        config_name=TARGET_CONFIG,
        commit_message="Overwrite pre_train_data: client parsing, hw_arch, cloud_provider",
    )


if __name__ == "__main__":
    main()