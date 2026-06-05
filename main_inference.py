from datasets import Dataset, DatasetDict, load_dataset

from inference.inference.gossip_phase_sync_member import infer_gossip_sync_features
from inference.inference.bare_metal import infer_bare_metal_features
from inference.inference.cloud import infer_cloud_features

REPO_ID = "yhackspacher/ethereum-crawl"
SOURCE_CONFIG = "pre_train_data"
TARGET_CONFIG = "train_data"
SOURCE_SPLIT = "train"


def main():
    df = load_dataset(REPO_ID, name=SOURCE_CONFIG, split=SOURCE_SPLIT).to_pandas()
    df = infer_gossip_sync_features(df)
    df = infer_bare_metal_features(df)
    df = infer_cloud_features(df)

    DatasetDict({SOURCE_SPLIT: Dataset.from_pandas(df, preserve_index=False)}).push_to_hub(
        REPO_ID,
        config_name=TARGET_CONFIG,
        commit_message="Refactor: merge proxy into ccri, fix constants from CCRI 2022 report",
    )


if __name__ == "__main__":
    main()