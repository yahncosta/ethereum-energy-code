from datasets import Dataset, DatasetDict, load_dataset

from inference.p2pspec2020_inference.inference_p2p import infer_p2p_metadata_features
from inference.teads2021_inference.inference_te import infer_teads_features
from inference.ccri2022_inference.inference_cc import infer_ccri_features
from inference.pankovska2024_inference.inference_pk import infer_pankovska_features
from inference.web3pi2024_inference.inference_wp import infer_web3pi_features
from inference.proxy_inference.inference_proxy import infer_proxy_features

REPO_ID = "yhackspacher/ethereum-crawl"
SOURCE_CONFIG = "pre_train_data"
TARGET_CONFIG = "train_data"
SOURCE_SPLIT = "train"


def main():
    df = load_dataset(REPO_ID, name=SOURCE_CONFIG, split=SOURCE_SPLIT).to_pandas()
    df = infer_p2p_metadata_features(df)
    df = infer_teads_features(df)
    df = infer_ccri_features(df)
    df = infer_proxy_features(df)
    df = infer_web3pi_features(df)
    df = infer_pankovska_features(df)

    DatasetDict({SOURCE_SPLIT: Dataset.from_pandas(df, preserve_index=False)}).push_to_hub(
        REPO_ID,
        config_name=TARGET_CONFIG,
        commit_message="Move inference modules into inference/ namespace package",
    )


if __name__ == "__main__":
    main()