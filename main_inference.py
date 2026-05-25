from datasets import Dataset, DatasetDict, load_dataset

from inference.inference.p2p_spec2020 import infer_p2p_metadata_features
from inference.inference.ccri import infer_ccri_features
from inference.inference.web3pi2024 import infer_web3pi_features
from inference.inference.pankovska2024 import infer_pankovska_features

REPO_ID = "yhackspacher/ethereum-crawl"
SOURCE_CONFIG = "pre_train_data"
TARGET_CONFIG = "train_data"
SOURCE_SPLIT = "train"


def main():
    df = load_dataset(REPO_ID, name=SOURCE_CONFIG, split=SOURCE_SPLIT).to_pandas()
    df = infer_p2p_metadata_features(df)
    df = infer_ccri_features(df)
    df = infer_web3pi_features(df)
    df = infer_pankovska_features(df)

    DatasetDict({SOURCE_SPLIT: Dataset.from_pandas(df, preserve_index=False)}).push_to_hub(
        REPO_ID,
        config_name=TARGET_CONFIG,
        commit_message="Refactor: merge proxy into ccri, fix constants from CCRI 2022 report",
    )


if __name__ == "__main__":
    main()