import pandas as pd
import numpy as np

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


def assign_hw_tier(row: pd.Series) -> int | None:
    if row.get("is_cloud_hosted", False):
        return None
    if row["hw_arch"] == "ARM":
        return 1
    return 4


def _weighted_idle(key: str) -> float:
    return sum(w * CCRI_HW_TIERS[t][key] for t, w in TIER_WEIGHTS.items())


def resolve_idle_power(tier: int | None) -> tuple[float | None, float | None, float | None]:
    if tier is None:
        return None, None, None
    if tier == 1:
        t = CCRI_HW_TIERS[1]
        return t["power_idle_w"], t["power_idle_min_w"], t["power_idle_max_w"]
    return (
        _weighted_idle("power_idle_w"),
        _weighted_idle("power_idle_min_w"),
        _weighted_idle("power_idle_max_w"),
    )


def infer_ccri_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "is_cloud_hosted" not in df.columns:
        df["is_cloud_hosted"] = False

    df["power_cl_marginal_w"] = df["consensus_client"].map(CCRI_CL_MARGINAL_W).astype(float)
    df["power_el_marginal_w"] = df["execution_client"].map(CCRI_EL_MARGINAL_W).astype(float)

    df["ccri_measured"] = (
        df["power_cl_marginal_w"].notna() & df["power_el_marginal_w"].notna()
    )

    df["power_combined_adj_factor"] = COMBINED_ADJUSTMENT_FACTOR

    df["hw_config_tier"] = df.apply(assign_hw_tier, axis=1).astype("Int64")

    idle_values = df["hw_config_tier"].map(
        lambda t: resolve_idle_power(None if pd.isna(t) else int(t))
    )
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