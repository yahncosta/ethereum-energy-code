import numpy as np
import pandas as pd
from datasets import load_dataset, Dataset, DatasetDict


REPO_ID       = "yhackspacher/ethereum-crawl"
SOURCE_CONFIG = "train_data"
TARGET_CONFIG = "train_data"
SOURCE_SPLIT  = "train"

CCRI_CL_MARGINAL_W: dict[str, float | None] = {
    "lighthouse":  6.0,
    "prysm":      12.0,
    "teku":       18.0,
    "nimbus":      4.0,
    "lodestar":    8.0,
    "caplin":     None,
    "grandine":   None,
}

CCRI_EL_MARGINAL_W: dict[str, float | None] = {
    "geth":        6.0,
    "erigon":      4.0,
    "besu":       11.0,
    "nethermind": None,
    "reth":       None,
}

COMBINED_ADJUSTMENT_FACTOR: float = 0.91

CCRI_HW_TIERS: dict[int, dict] = {
    1: {
        "description":         "Raspberry Pi 4 Model B",
        "cpu":                 "ARM Cortex-A72",
        "ram_gb":              8,
        "storage":             "128 GB SD card",
        "arch":                "ARM",
        "meets_validator_req": False,
        "power_idle_w":        5.0,
        "power_idle_min_w":    3.5,
        "power_idle_max_w":    6.5,
    },
    2: {
        "description":         "Intel NUC (low-power variant A)",
        "cpu":                 "Intel Core i3 (low-power)",
        "ram_gb":              16,
        "storage":             "512 GB SSD",
        "arch":                "x86",
        "meets_validator_req": True,
        "power_idle_w":        7.0,
        "power_idle_min_w":    5.0,
        "power_idle_max_w":    9.0,
    },
    3: {
        "description":         "Intel NUC (low-power variant B)",
        "cpu":                 "Intel Core i5 (low-power)",
        "ram_gb":              16,
        "storage":             "1 TB SSD",
        "arch":                "x86",
        "meets_validator_req": True,
        "power_idle_w":       10.0,
        "power_idle_min_w":    7.0,
        "power_idle_max_w":   13.0,
    },
    4: {
        "description":         "Pre-built desktop (mid-range)",
        "cpu":                 "Intel Core i5-1135G7",
        "ram_gb":              16,
        "storage":             "2 TB SSD",
        "arch":                "x86",
        "meets_validator_req": True,
        "power_idle_w":       20.0,
        "power_idle_min_w":   15.0,
        "power_idle_max_w":   25.0,
    },
    5: {
        "description":         "Mid-range desktop",
        "cpu":                 "Intel Core i7 / AMD Ryzen 7",
        "ram_gb":              64,
        "storage":             "2 TB NVMe",
        "arch":                "x86",
        "meets_validator_req": True,
        "power_idle_w":       50.0,
        "power_idle_min_w":   35.0,
        "power_idle_max_w":   70.0,
    },
    6: {
        "description":         "High-end workstation",
        "cpu":                 "AMD Threadripper",
        "ram_gb":              256,
        "storage":             "4 TB NVMe",
        "arch":                "x86",
        "meets_validator_req": True,
        "power_idle_w":      150.0,
        "power_idle_min_w":  100.0,
        "power_idle_max_w":  200.0,
    },
}

TIER_WEIGHTS: dict[int, float] = {4: 0.25, 5: 0.50, 6: 0.25}


def infer_ccri_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "cloud_provider" not in df.columns:
        df["cloud_provider"] = None

    df["power_cl_marginal_w"] = df["consensus_client"].map(CCRI_CL_MARGINAL_W).astype(float)
    df["power_el_marginal_w"] = df["execution_client"].map(CCRI_EL_MARGINAL_W).astype(float)

    df["ccri_measured"] = (
        df["power_cl_marginal_w"].notna() & df["power_el_marginal_w"].notna()
    )

    df["power_combined_adj_factor"] = COMBINED_ADJUSTMENT_FACTOR

    df["hw_config_tier"] = df.apply(
        lambda row: None if pd.notna(row["cloud_provider"])
        else (1 if row["hw_arch"] == "ARM" else 4),
        axis=1,
    ).astype("Int64")

    def resolve_idle(tier):
        if pd.isna(tier):
            return None, None, None
        t = int(tier)
        if t == 1:
            cfg = CCRI_HW_TIERS[1]
            return cfg["power_idle_w"], cfg["power_idle_min_w"], cfg["power_idle_max_w"]
        return (
            sum(w * CCRI_HW_TIERS[t]["power_idle_w"]     for t, w in TIER_WEIGHTS.items()),
            sum(w * CCRI_HW_TIERS[t]["power_idle_min_w"] for t, w in TIER_WEIGHTS.items()),
            sum(w * CCRI_HW_TIERS[t]["power_idle_max_w"] for t, w in TIER_WEIGHTS.items()),
        )

    idle_values = df["hw_config_tier"].map(resolve_idle)
    df["power_idle_w"]     = idle_values.map(lambda x: x[0]).astype(float)
    df["power_idle_min_w"] = idle_values.map(lambda x: x[1]).astype(float)
    df["power_idle_max_w"] = idle_values.map(lambda x: x[2]).astype(float)

    df["power_node_w"] = np.where(
        df["ccri_measured"] & df["power_idle_w"].notna(),
        (df["power_el_marginal_w"] + df["power_cl_marginal_w"])
        * df["power_combined_adj_factor"]
        + df["power_idle_w"],
        np.nan,
    )

    return df


if __name__ == "__main__":
    print("=" * 60)
    print(f"Loading '{SOURCE_CONFIG}' from {REPO_ID}")
    print("=" * 60)

    df = load_dataset(REPO_ID, name=SOURCE_CONFIG, split=SOURCE_SPLIT).to_pandas()
    print(f"Loaded: {len(df)} rows x {len(df.columns)} columns\n")

    df = infer_ccri_features(df)

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

    print(f"\nColumns ({len(df.columns)}):")
    for col in df.columns:
        n_null = int(df[col].isna().sum())
        print(f"  {col:<40} nulls: {n_null}/{total}")

    print(f"\n{'=' * 60}")
    print(f"Pushing to '{TARGET_CONFIG}'...")
    print("=" * 60)

    DatasetDict({SOURCE_SPLIT: Dataset.from_pandas(df, preserve_index=False)}).push_to_hub(
        REPO_ID,
        config_name=TARGET_CONFIG,
        commit_message="ccri_inference: add hw_config_tier, power_idle_w, power_node_w and related columns",
    )
    print(f"Done. https://huggingface.co/datasets/{REPO_ID}")