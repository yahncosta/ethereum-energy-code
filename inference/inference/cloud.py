import numpy as np
import pandas as pd

from inference.constants.cloud import (
    CLOUD_PUE_PANKOVSKA,
    NODE_VCPU_MIN_NON_VALIDATOR,
    NODE_VCPU_MIN_VALIDATOR,
    NODE_RAM_NON_VALIDATOR_GB,
    NODE_RAM_VALIDATOR_GB,
    SSD_OVERHEAD_W_PANKOVSKA,
    EC2_INSTANCE_POWER_W,
    _ALL_VCPU_MAX_W,
)
from inference.constants.gossip_phase_sync_member import GOSSIP_PHASE_NO_VALIDATORS

def infer_cloud_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["is_validator"] = (
        (df["gossip_phase"] != GOSSIP_PHASE_NO_VALIDATORS) | df["is_sync_committee_member"]
    )

    df["required_ram_gb"] = np.where(df["is_validator"], NODE_RAM_VALIDATOR_GB, NODE_RAM_NON_VALIDATOR_GB)
    df["required_vcpu"] = np.where(df["is_validator"], NODE_VCPU_MIN_VALIDATOR, NODE_VCPU_MIN_NON_VALIDATOR)

    aws_mask = df["cloud_provider"] == "aws"
    for idx, row in df[aws_mask].iterrows():
        node_arch = row["hw_arch"]
        candidates = {
            k: v for k, v in EC2_INSTANCE_POWER_W.items()
            if v["vcpu"] >= row["required_vcpu"]
            and v["ram_gb"] >= row["required_ram_gb"]
            and v["arch"] == node_arch
        }

        if not candidates:
            raise ValueError(f"No EC2 candidates found.")

        pct100_vals = [v["pct100"] for v in candidates.values()]
        df.at[idx, "power_cloud_at_load_w"] = sum(pct100_vals) / len(pct100_vals)

    non_aws_cloud_mask = df["cloud_provider"].notna() & (df["cloud_provider"] != "aws")
    for idx, row in df[non_aws_cloud_mask].iterrows():
        vcpu_min = row["required_vcpu"]
        max_w = _ALL_VCPU_MAX_W[row["cloud_provider"]] * vcpu_min
        df.at[idx, "power_cloud_at_load_w"] = max_w

    cloud_mask = df["cloud_provider"].notna() & df["power_cloud_at_load_w"].notna()
    df.loc[cloud_mask, "power_node_w"] = (
        (df.loc[cloud_mask, "power_cloud_at_load_w"] + SSD_OVERHEAD_W_PANKOVSKA) * CLOUD_PUE_PANKOVSKA
    )

    df = df.drop(columns=["is_validator", "required_ram_gb", "required_vcpu"])

    return df