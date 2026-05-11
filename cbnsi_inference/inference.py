import numpy as np
import pandas as pd

from cbnsi_inference.constants import (
    CBNSI_BEST_GUESS_TIER_WEIGHTS,
    CBNSI_HW_TIERS,
    COMBINED_ADJUSTMENT_FACTOR,
)


def infer_cbnsi_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "cloud_provider" not in df.columns:
        df["cloud_provider"] = None

    df["power_combined_adj_factor"] = COMBINED_ADJUSTMENT_FACTOR

    df["hw_config_tier"] = df.apply(
        lambda row: None if pd.notna(row["cloud_provider"]) else (1 if row["hw_arch"] == "ARM" else 4),
        axis=1,
    ).astype("Int64")

    idle_values = df["hw_config_tier"].map(resolve_idle_power)

    df["power_idle_w"] = idle_values.map(lambda x: x[0]).astype(float)
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


def resolve_idle_power(tier) -> tuple[float | None, float | None, float | None]:
    if pd.isna(tier):
        return None, None, None

    tier = int(tier)

    if tier == 1:
        config = CBNSI_HW_TIERS[1]
        return config["power_idle_w"], config["power_idle_min_w"], config["power_idle_max_w"]

    return (
        weighted_idle("power_idle_w"),
        weighted_idle("power_idle_min_w"),
        weighted_idle("power_idle_max_w"),
    )


def weighted_idle(key: str) -> float:
    return sum(
        weight * CBNSI_HW_TIERS[tier][key]
        for tier, weight in CBNSI_BEST_GUESS_TIER_WEIGHTS.items()
    )