import numpy as np
import pandas as pd

from inference.ccf_coefficients.constants_ccf import CCF_VCPU_MIN_W, CCF_VCPU_MAX_W
from inference.pankovska2024_inference.constants_pk import (
    CLOUD_PUE,
    HOME_PUE,
    NODE_VCPU_MIN,
    SSD_OVERHEAD_W,
)


def _ccf_power(provider: str, utilization: float) -> float:
    vcpus = NODE_VCPU_MIN
    min_w = CCF_VCPU_MIN_W.get(provider, 0.74) * vcpus
    max_w = CCF_VCPU_MAX_W.get(provider, 3.50) * vcpus
    return min_w + utilization * (max_w - min_w) + SSD_OVERHEAD_W


def infer_pankovska_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["pue_factor"] = np.where(df["cloud_provider"].notna(), CLOUD_PUE, HOME_PUE)

    non_aws_cloud_mask = df["cloud_provider"].notna() & (df["cloud_provider"] != "aws")
    for idx, row in df[non_aws_cloud_mask].iterrows():
        provider = row["cloud_provider"]
        df.at[idx, "power_cloud_idle_w"]    = _ccf_power(provider, utilization=0.0)
        df.at[idx, "power_cloud_at_load_w"] = _ccf_power(provider, utilization=0.5)

    cloud_mask = df["cloud_provider"].notna() & df["power_cloud_at_load_w"].notna()
    df.loc[cloud_mask, "power_node_w"] = (
        df.loc[cloud_mask, "power_cloud_at_load_w"] + SSD_OVERHEAD_W
    )

    df["power_node_pue_adjusted_w"] = df["power_node_w"] * df["pue_factor"]

    return df