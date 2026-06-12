import numpy as np
import pandas as pd

from inference.constants.cloud import (
    CLOUD_PUE_PANKOVSKA,
    NODE_VCPU_MIN_NON_VALIDATOR,
    NODE_VCPU_MIN_VALIDATOR,
    NODE_RAM_NON_VALIDATOR_GB,
    NODE_RAM_VALIDATOR_GB,
    NODE_SSD_NON_VALIDATOR_TB,
    NODE_SSD_VALIDATOR_TB,
    SSD_OVERHEAD_W_PANKOVSKA,
    CCF_MEMORY_W_PER_GB,
    CCF_SSD_W_PER_TB,
    AWS_EC2_INSTANCE_POWER_W,
    _ALL_VCPU_MAX_W,
)


def infer_cloud_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["required_ram_gb"] = np.where(df["is_validator"], NODE_RAM_VALIDATOR_GB, NODE_RAM_NON_VALIDATOR_GB)
    df["required_vcpu"] = np.where(df["is_validator"], NODE_VCPU_MIN_VALIDATOR, NODE_VCPU_MIN_NON_VALIDATOR)
    df["required_ssd_tb"] = np.where(df["is_validator"], NODE_SSD_VALIDATOR_TB, NODE_SSD_NON_VALIDATOR_TB)

    aws_mask = df["cloud_provider"] == "aws"
    for idx, row in df[aws_mask].iterrows():
        node_arch = row["hw_arch"]
        candidates = {
            k: v for k, v in AWS_EC2_INSTANCE_POWER_W.items()
            if v["vcpu"] >= row["required_vcpu"]
            and v["ram_gb"] >= row["required_ram_gb"]
            and v["arch"] == node_arch
        }

        if not candidates:
            raise ValueError(f"No EC2 candidates found.")

        pct100_vals = [v["pct100"] for v in candidates.values()]
        p_cloud_load = sum(pct100_vals) / len(pct100_vals)
        df.at[idx, "power_node_w"] = (p_cloud_load + SSD_OVERHEAD_W_PANKOVSKA) * CLOUD_PUE_PANKOVSKA

    non_aws_cloud_mask = df["cloud_provider"].notna() & (df["cloud_provider"] != "aws")
    for idx, row in df[non_aws_cloud_mask].iterrows():
        vcpu_min = row["required_vcpu"]
        p_cpu_w = _ALL_VCPU_MAX_W[row["cloud_provider"]] * vcpu_min
        p_ram_w = CCF_MEMORY_W_PER_GB * row["required_ram_gb"]
        p_ssd_w = CCF_SSD_W_PER_TB * row["required_ssd_tb"]
        df.at[idx, "power_node_w"] = p_cpu_w + p_ram_w + p_ssd_w

    return df