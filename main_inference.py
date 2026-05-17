from datasets import Dataset, DatasetDict, load_dataset

from sutton2022_inference import infer_sutton_features
from teads2021_inference import infer_teads_features
from ccri2022_inference import infer_ccri_features
from pankovska2024_inference import infer_pankovska_features
from cbnsi_inference import infer_cbnsi_features
from web3pi2024_inference import infer_web3pi_features

REPO_ID = "yhackspacher/ethereum-crawl"
SOURCE_CONFIG = "pre_train_data"
TARGET_CONFIG = "train_data"
SOURCE_SPLIT = "train"


def print_sutton_summary(df):
    total = len(df)
    print(f"Validator nodes: {int(df['is_validator_node'].sum())}/{total}")
    print("Gossip phase distribution:")
    print(df["gossip_phase"].value_counts().to_string())
    print(f"Subnet-saturated (attnets=64): {int(df['is_subnet_saturated'].sum())}")
    print(f"Sync committee members (syncnets>0): {int(df['is_sync_committee_member'].sum())}")
    print()


def print_teads_summary(df):
    total = len(df)
    aws_count = int((df["cloud_provider"] == "aws").sum())
    print(f"AWS nodes with EC2 instance assigned: {aws_count}/{total}")
    if aws_count > 0:
        print("\nEC2 instance type distribution (AWS nodes):")
        print(df.loc[df["cloud_provider"] == "aws", "ec2_instance_type"].value_counts().to_string())
    print()


def print_ccri_summary(df):
    total = len(df)
    measured = int(df["ccri_measured"].sum())
    print(f"CCRI coverage: {measured}/{total} ({100 * measured / total:.1f}%)")
    unmeasured = (
        df[~df["ccri_measured"]]
        .groupby(["consensus_client", "execution_client"])
        .size()
        .sort_values(ascending=False)
    )
    print("Unmeasured client pairs:")
    print(unmeasured.to_string())
    print()


def print_pankovska_summary(df):
    total = len(df)
    cloud_count = int(df["cloud_provider"].notna().sum())
    print(f"Cloud-hosted: {cloud_count}/{total} ({100 * cloud_count / total:.1f}%)")
    print(df["cloud_provider"].value_counts(dropna=False).to_string())
    print(f"\nPUE factor distribution:")
    print(df["pue_factor"].value_counts().to_string())
    print()


def print_web3pi_summary(df):
    total = len(df)
    override_count = int((df["power_node_w_source"] == "web3pi_empirical").sum())
    print(f"Web3 Pi override applied: {override_count}/{total} ({100 * override_count / total:.1f}%)")
    print()


def print_dataset_summary(df):
    total = len(df)
    print("=" * 60)
    print("FINAL DATASET SUMMARY")
    print("=" * 60)
    print(f"Shape: {df.shape}")
    print(f"\nColumns ({len(df.columns)}):")
    for col in df.columns:
        n_null = int(df[col].isna().sum())
        print(f"  {col:<45} nulls: {n_null}/{total}")
    print()
    print("power_node_w statistics:")
    print(df["power_node_w"].describe().to_string())
    print()
    print("power_node_pue_adjusted_w statistics:")
    print(df["power_node_pue_adjusted_w"].describe().to_string())
    print()
    print("power_node_w_source distribution:")
    print(df["power_node_w_source"].value_counts(dropna=False).to_string())
    print()


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
    print_sutton_summary(df)

    print("=" * 60)
    print("STEP 3 — Teads (2021): AWS EC2 instance selection and power lookup")
    print("=" * 60)
    df = infer_teads_features(df)
    print_teads_summary(df)

    print("=" * 60)
    print("STEP 4 — CCRI (2022): client marginal power, hw tier, idle power, bare-metal node power")
    print("=" * 60)
    df = infer_ccri_features(df)
    print_ccri_summary(df)

    print("=" * 60)
    print("STEP 5 — Pankovska (2024): PUE factors, CCF fallback for non-AWS cloud, SSD overhead, cloud node power")
    print("=" * 60)
    df = infer_pankovska_features(df)
    print_pankovska_summary(df)

    print("=" * 60)
    print("STEP 6 — CBNSI: route power_node_w_source label, finalise pue-adjusted power")
    print("=" * 60)
    df = infer_cbnsi_features(df)

    print("=" * 60)
    print("STEP 7 — Web3 Pi (2024): ARM Nimbus empirical power override")
    print("=" * 60)
    df = infer_web3pi_features(df)
    print_web3pi_summary(df)

    print_dataset_summary(df)

    print("=" * 60)
    print(f"PUSHING to {REPO_ID}  [config: {TARGET_CONFIG}]")
    print("=" * 60)
    DatasetDict({SOURCE_SPLIT: Dataset.from_pandas(df, preserve_index=False)}).push_to_hub(
        REPO_ID,
        config_name=TARGET_CONFIG,
        commit_message="Refactor: split inference responsibilities across ccri2022, teads2021, pankovska2024, cbnsi, web3pi2024",
    )
    print(f"Done. Dataset pushed to: https://huggingface.co/datasets/{REPO_ID}")


if __name__ == "__main__":
    main()