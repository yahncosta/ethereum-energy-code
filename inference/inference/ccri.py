import pandas as pd

from inference.constants.ccri import (
    ARM_LINUX_NODE_W,
    ARM_MACOS_IDLE_W,
    CCRI_CL_MARGINAL_W,
    CCRI_EL_MARGINAL_W,
    COMBINED_ADJUSTMENT_FACTOR,
    PROXY_CL_MARGINAL_W,
    PROXY_EL_MARGINAL_W,
    WEIGHTED_IDLE_W,
)

_ALL_CL_MARGINAL_W = {**CCRI_CL_MARGINAL_W, **PROXY_CL_MARGINAL_W}
_ALL_EL_MARGINAL_W = {**CCRI_EL_MARGINAL_W, **PROXY_EL_MARGINAL_W}

_MACOS_OS_TOKENS = {"darwin", "macos", "osx"}


def _is_macos(os_token: str | None) -> bool:
    return os_token in _MACOS_OS_TOKENS


def infer_ccri_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["power_cl_marginal_w"] = df["consensus_client"].map(_ALL_CL_MARGINAL_W)
    df["power_el_marginal_w"] = df["execution_client"].map(_ALL_EL_MARGINAL_W)

    arm_non_cloud = (df["hw_arch"] == "ARM") & df["cloud_provider"].isna()
    x86_non_cloud = (df["hw_arch"] == "x86") & df["cloud_provider"].isna()

    linux_arm_mask = arm_non_cloud & ~df["os_token"].apply(_is_macos)
    macos_arm_mask = arm_non_cloud & df["os_token"].apply(_is_macos)

    bare_metal_x86_mask = (
        x86_non_cloud
        & df["power_cl_marginal_w"].notna()
        & df["power_el_marginal_w"].notna()
    )

    bare_metal_macos_mask = (
        macos_arm_mask
        & df["power_cl_marginal_w"].notna()
        & df["power_el_marginal_w"].notna()
    )

    df["power_node_w"] = float("nan")

    df.loc[linux_arm_mask, "power_node_w"] = ARM_LINUX_NODE_W

    df.loc[bare_metal_x86_mask, "power_node_w"] = (
        (df.loc[bare_metal_x86_mask, "power_cl_marginal_w"] + df.loc[bare_metal_x86_mask, "power_el_marginal_w"])
        * COMBINED_ADJUSTMENT_FACTOR
        + WEIGHTED_IDLE_W
    )

    df.loc[bare_metal_macos_mask, "power_node_w"] = (
        (df.loc[bare_metal_macos_mask, "power_cl_marginal_w"] + df.loc[bare_metal_macos_mask, "power_el_marginal_w"])
        * COMBINED_ADJUSTMENT_FACTOR
        + ARM_MACOS_IDLE_W
    )

    return df