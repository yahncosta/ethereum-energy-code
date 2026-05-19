import pandas as pd

from inference.ccri2022_inference.constants_cc import (
    COMBINED_ADJUSTMENT_FACTOR,
)
from inference.proxy_inference.constants_proxy import (
    ERIGON_CAPLIN_COMBINED_MARGINAL_W,
    PROXY_CL_MARGINAL_W,
    PROXY_CL_SOURCE,
    PROXY_EL_MARGINAL_W,
    PROXY_EL_SOURCE,
)


def infer_proxy_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    caplin_mask = (
        (df["consensus_client"] == "caplin")
        & (df["execution_client"] == "erigon")
        & df["cloud_provider"].isna()
        & df["power_idle_w"].notna()
        & df["power_node_w"].isna()
    )

    df.loc[caplin_mask, "power_el_marginal_w"]    = ERIGON_CAPLIN_COMBINED_MARGINAL_W
    df.loc[caplin_mask, "power_cl_marginal_w"]    = 0.0
    df.loc[caplin_mask, "proxy_el_source"]        = "erigon_caplin_combined"
    df.loc[caplin_mask, "proxy_cl_source"]        = "erigon_caplin_combined"
    df.loc[caplin_mask, "proxy_inferred"]         = True
    df.loc[caplin_mask, "power_node_w"] = (
        ERIGON_CAPLIN_COMBINED_MARGINAL_W
        + df.loc[caplin_mask, "power_idle_w"]
    )

    for el_client, el_w in PROXY_EL_MARGINAL_W.items():
        for cl_client, cl_w in PROXY_CL_MARGINAL_W.items():
            mask = (
                (df["execution_client"] == el_client)
                & (df["consensus_client"] == cl_client)
                & df["cloud_provider"].isna()
                & df["power_idle_w"].notna()
                & df["power_node_w"].isna()
                & ~caplin_mask
            )
            df.loc[mask, "power_el_marginal_w"] = el_w
            df.loc[mask, "power_cl_marginal_w"] = cl_w
            df.loc[mask, "proxy_el_source"]     = PROXY_EL_SOURCE[el_client]
            df.loc[mask, "proxy_cl_source"]     = PROXY_CL_SOURCE[cl_client]
            df.loc[mask, "proxy_inferred"]      = True
            df.loc[mask, "power_node_w"] = (
                (el_w + cl_w) * COMBINED_ADJUSTMENT_FACTOR
                + df.loc[mask, "power_idle_w"]
            )

    for el_client, el_w in PROXY_EL_MARGINAL_W.items():
        mask = (
            (df["execution_client"] == el_client)
            & (~df["consensus_client"].isin(PROXY_CL_MARGINAL_W))
            & df["power_cl_marginal_w"].notna()
            & df["cloud_provider"].isna()
            & df["power_idle_w"].notna()
            & df["power_node_w"].isna()
            & ~caplin_mask
        )
        df.loc[mask, "power_el_marginal_w"] = el_w
        df.loc[mask, "proxy_el_source"]     = PROXY_EL_SOURCE[el_client]
        df.loc[mask, "proxy_cl_source"]     = "ccri_measured"
        df.loc[mask, "proxy_inferred"]      = True
        df.loc[mask, "power_node_w"] = (
            (el_w + df.loc[mask, "power_cl_marginal_w"]) * COMBINED_ADJUSTMENT_FACTOR
            + df.loc[mask, "power_idle_w"]
        )

    for cl_client, cl_w in PROXY_CL_MARGINAL_W.items():
        mask = (
            (df["consensus_client"] == cl_client)
            & (~df["execution_client"].isin(PROXY_EL_MARGINAL_W))
            & (~df["execution_client"].isin(["erigon"]))
            & df["power_el_marginal_w"].notna()
            & df["cloud_provider"].isna()
            & df["power_idle_w"].notna()
            & df["power_node_w"].isna()
            & ~caplin_mask
        )
        df.loc[mask, "power_cl_marginal_w"] = cl_w
        df.loc[mask, "proxy_cl_source"]     = PROXY_CL_SOURCE[cl_client]
        df.loc[mask, "proxy_el_source"]     = "ccri_measured"
        df.loc[mask, "proxy_inferred"]      = True
        df.loc[mask, "power_node_w"] = (
            (df.loc[mask, "power_el_marginal_w"] + cl_w) * COMBINED_ADJUSTMENT_FACTOR
            + df.loc[mask, "power_idle_w"]
        )

    if "proxy_inferred" not in df.columns:
        df["proxy_inferred"] = False
    if "proxy_el_source" not in df.columns:
        df["proxy_el_source"] = None
    if "proxy_cl_source" not in df.columns:
        df["proxy_cl_source"] = None

    df["proxy_inferred"] = df["proxy_inferred"].fillna(False)

    return df