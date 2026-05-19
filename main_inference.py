from datasets import Dataset, DatasetDict, load_dataset

from inference.sutton2022_inference.inference_su import infer_sutton_features
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
    print("=" * 60)
    print("STEP 1 — Loading base crawl dataset")
    print("=" * 60)
    df = load_dataset(REPO_ID, name=SOURCE_CONFIG, split=SOURCE_SPLIT).to_pandas()
    print(f"Loaded: {len(df)} rows x {len(df.columns)} columns")
    print(f"Columns: {df.columns.tolist()}\n")

    print("=" * 60)
    print("STEP 2 — Sutton (2022): validator and subnet activity features")
    print("=" * 60)
    df = infer_sutton_features(df)

    print("=" * 60)
    print("STEP 3 — Teads (2021): AWS EC2 instance selection and power lookup")
    print("=" * 60)
    df = infer_teads_features(df)

    print("=" * 60)
    print("STEP 4 — CCRI (2022): client marginal power, hw tier, idle power, bare-metal node power")
    print("=" * 60)
    df = infer_ccri_features(df)

    print("=" * 60)
    print("STEP 5 — Proxy inference: marginal power estimates for unmeasured client combinations")
    print("=" * 60)
    df = infer_proxy_features(df)

    print("=" * 60)
    print("STEP 6 — Pankovska (2024): PUE factors, CCF fallback for non-AWS cloud, SSD overhead, cloud node power")
    print("=" * 60)
    df = infer_pankovska_features(df)

    print("=" * 60)
    print("STEP 7 — Web3 Pi (2024): ARM Nimbus empirical power override")
    print("=" * 60)
    df = infer_web3pi_features(df)


    print("=" * 60)
    print(f"PUSHING to {REPO_ID}  [config: {TARGET_CONFIG}]")
    print("=" * 60)
    DatasetDict({SOURCE_SPLIT: Dataset.from_pandas(df, preserve_index=False)}).push_to_hub(
        REPO_ID,
        config_name=TARGET_CONFIG,
        commit_message="Move inference modules into inference/ namespace package",
    )
    print(f"Done. Dataset pushed to: https://huggingface.co/datasets/{REPO_ID}")


if __name__ == "__main__":
    main()