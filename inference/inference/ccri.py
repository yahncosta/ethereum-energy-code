import pandas as pd

from inference.constants.ccri import (
    CCRI_BEST_GUESS_TIER_WEIGHTS,
    CCRI_CL_MARGINAL_W,
    CCRI_EL_MARGINAL_W,
    CCRI_HW_TIERS,
    COMBINED_ADJUSTMENT_FACTOR,
)


def infer_ccri_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["power_cl_marginal_w"] = df["consensus_client"].map(CCRI_CL_MARGINAL_W).astype(float)
    df["power_el_marginal_w"] = df["execution_client"].map(CCRI_EL_MARGINAL_W).astype(float)

    df["ccri_measured"] = df["power_cl_marginal_w"].notna() & df["power_el_marginal_w"].notna()

    df["power_combined_adj_factor"] = COMBINED_ADJUSTMENT_FACTOR

    df["hw_config_tier"] = df.apply(
        lambda row: None if pd.notna(row["cloud_provider"]) else (1 if row["hw_arch"] == "ARM" else 4),
        axis=1,
    ).astype("Int64")

    idle_values = df["hw_config_tier"].map(_resolve_idle_power)
    df["power_idle_w"]     = idle_values.map(lambda x: x[0]).astype(float)
    df["power_idle_min_w"] = idle_values.map(lambda x: x[1]).astype(float)
    df["power_idle_max_w"] = idle_values.map(lambda x: x[2]).astype(float)

    bare_metal_mask = df["cloud_provider"].isna() & df["ccri_measured"] & df["power_idle_w"].notna()

    df["power_node_w"] = float("nan")
    df.loc[bare_metal_mask, "power_node_w"] = (
        (df.loc[bare_metal_mask, "power_el_marginal_w"] + df.loc[bare_metal_mask, "power_cl_marginal_w"])
        * df.loc[bare_metal_mask, "power_combined_adj_factor"]
        + df.loc[bare_metal_mask, "power_idle_w"]
    )

    return df


def _resolve_idle_power(tier) -> tuple[float | None, float | None, float | None]:
    if pd.isna(tier):
        return None, None, None
    tier = int(tier)
    if tier == 1:
        config = CCRI_HW_TIERS[1]
        return config["power_idle_w"], config["power_idle_min_w"], config["power_idle_max_w"]
    return (
        _weighted_idle("power_idle_w"),
        _weighted_idle("power_idle_min_w"),
        _weighted_idle("power_idle_max_w"),
    )


def _weighted_idle(key: str) -> float:
    return sum(
        weight * CCRI_HW_TIERS[tier][key]
        for tier, weight in CCRI_BEST_GUESS_TIER_WEIGHTS.items()
    )