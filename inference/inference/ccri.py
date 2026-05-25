import pandas as pd

from inference.constants.ccri import (
    ARM_IDLE_W,
    CCRI_CL_MARGINAL_W,
    CCRI_EL_MARGINAL_W,
    COMBINED_ADJUSTMENT_FACTOR,
    ERIGON_CAPLIN_COMBINED_MARGINAL_W,
    PROXY_CL_MARGINAL_W,
    PROXY_EL_MARGINAL_W,
    WEIGHTED_IDLE_W,
)

_ALL_CL_MARGINAL_W = {**CCRI_CL_MARGINAL_W, **PROXY_CL_MARGINAL_W}
_ALL_EL_MARGINAL_W = {**CCRI_EL_MARGINAL_W, **PROXY_EL_MARGINAL_W}


def infer_ccri_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["power_cl_marginal_w"] = df["consensus_client"].map(_ALL_CL_MARGINAL_W)
    df["power_el_marginal_w"] = df["execution_client"].map(_ALL_EL_MARGINAL_W)

    df["power_idle_w"] = df["hw_arch"].apply(
        lambda arch: ARM_IDLE_W if arch == "ARM" else WEIGHTED_IDLE_W
    )

    bare_metal_mask = (
        df["cloud_provider"].isna()
        & df["power_cl_marginal_w"].notna()
        & df["power_el_marginal_w"].notna()
        & df["power_idle_w"].notna()
    )

    df["power_node_w"] = float("nan")
    df.loc[bare_metal_mask, "power_node_w"] = (
        (df.loc[bare_metal_mask, "power_cl_marginal_w"] + df.loc[bare_metal_mask, "power_el_marginal_w"])
        * COMBINED_ADJUSTMENT_FACTOR
        + df.loc[bare_metal_mask, "power_idle_w"]
    )

    return df