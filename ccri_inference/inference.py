import numpy as np
import pandas as pd

from ccri_inference.constants import (
    CCRI_CL_MARGINAL_W,
    CCRI_EL_MARGINAL_W,
    CCRI_HW_TIERS,
    COMBINED_ADJUSTMENT_FACTOR,
    TIER_WEIGHTS,
)


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
        lambda row: None if pd.notna(row["cloud_provider"]) else (1 if row["hw_arch"] == "ARM" else 4),
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
            sum(w * CCRI_HW_TIERS[t]["power_idle_w"] for t, w in TIER_WEIGHTS.items()),
            sum(w * CCRI_HW_TIERS[t]["power_idle_min_w"] for t, w in TIER_WEIGHTS.items()),
            sum(w * CCRI_HW_TIERS[t]["power_idle_max_w"] for t, w in TIER_WEIGHTS.items()),
        )

    idle_values = df["hw_config_tier"].map(resolve_idle)

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