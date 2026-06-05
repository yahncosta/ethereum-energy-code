import numpy as np
import pandas as pd

from inference.constants.cloud import (
    CLOUD_PUE,
    NODE_VCPU_MIN_NON_VALIDATOR,
    NODE_VCPU_MIN_VALIDATOR,
    NODE_RAM_NON_VALIDATOR_GB,
    NODE_RAM_VALIDATOR_GB,
    SSD_OVERHEAD_W,
    EC2_INSTANCE_POWER_W,
    CCF_VCPU_MIN_W,
    CCF_VCPU_MAX_W,
)
from inference.constants.gossip_phase_sync_member import GOSSIP_PHASE_NO_VALIDATORS

def _avg_pct100(candidates: dict) -> float:
    vals = [v["pct100"] for v in candidates.values()]
    return sum(vals) / len(vals) if vals else 0.0


def _avg_idle(candidates: dict) -> float:
    vals = [v["idle"] for v in candidates.values()]
    return sum(vals) / len(vals) if vals else 0.0


def infer_cloud_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["is_validator"] = (
        (df["gossip_phase"] != GOSSIP_PHASE_NO_VALIDATORS) | df["is_sync_committee_member"]
    )

    df["required_ram_gb"] = np.where(df["is_validator"], NODE_RAM_VALIDATOR_GB, NODE_RAM_NON_VALIDATOR_GB)
    df["required_vcpu"] = np.where(df["is_validator"], NODE_VCPU_MIN_VALIDATOR, NODE_VCPU_MIN_NON_VALIDATOR)

    aws_mask = df["cloud_provider"] == "aws"
    for idx, row in df[aws_mask].iterrows():
        candidates = {
            k: v for k, v in EC2_INSTANCE_POWER_W.items()
            if v["vcpu"] >= row["required_vcpu"]
            and v["ram_gb"] >= row["required_ram_gb"]
        }

        if not candidates:
            raise ValueError("No EC2 candidates found.")

        df.at[idx, "power_cloud_idle_w"] = _avg_idle(candidates)
        df.at[idx, "power_cloud_at_load_w"] = _avg_pct100(candidates)

    non_aws_cloud_mask = df["cloud_provider"].notna() & (df["cloud_provider"] != "aws")
    for idx, row in df[non_aws_cloud_mask].iterrows():
        vcpu_min = row["required_vcpu"]
        min_w = CCF_VCPU_MIN_W.get(row["cloud_provider"], 0.74) * vcpu_min
        max_w = CCF_VCPU_MAX_W.get(row["cloud_provider"], 3.50) * vcpu_min
        df.at[idx, "power_cloud_idle_w"] = min_w + SSD_OVERHEAD_W
        df.at[idx, "power_cloud_at_load_w"] = min_w + 0.5 * (max_w - min_w) + SSD_OVERHEAD_W

    cloud_mask = df["cloud_provider"].notna() & df["power_cloud_at_load_w"].notna()
    df.loc[cloud_mask, "power_node_w"] = (
        (df.loc[cloud_mask, "power_cloud_at_load_w"] + SSD_OVERHEAD_W) * CLOUD_PUE
    )

    df = df.drop(columns=["is_validator", "required_ram_gb", "required_vcpu"])

    return df