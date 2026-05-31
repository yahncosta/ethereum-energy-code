import numpy as np
import pandas as pd

from inference.constants.pankovska2024 import (
    CLOUD_PUE,
    NODE_VCPU_MIN,
    NODE_RAM_NON_VALIDATOR_GB,
    NODE_RAM_VALIDATOR_GB,
    SSD_OVERHEAD_W,
    EC2_INSTANCE_POWER_W,
    CCF_VCPU_MIN_W,
    CCF_VCPU_MAX_W,
)
from inference.constants.p2p_spec2020 import GOSSIP_PHASE_NO_VALIDATORS


def infer_pankovska_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["is_validator"] = (
        (df["gossip_phase"] != GOSSIP_PHASE_NO_VALIDATORS) | df["is_sync_committee_member"]
    )

    df["required_ram_gb"] = np.where(df["is_validator"], NODE_RAM_VALIDATOR_GB, NODE_RAM_NON_VALIDATOR_GB)

    ec2_candidates = {
        k: v for k, v in EC2_INSTANCE_POWER_W.items()
        if v["vcpu"] >= NODE_VCPU_MIN
    }

    aws_mask = df["cloud_provider"] == "aws"
    for idx, row in df[aws_mask].iterrows():
        eligible = {
            k: v for k, v in ec2_candidates.items()
            if v["ram_gb"] >= row["required_ram_gb"]
        }
        if not eligible:
            eligible = {"m5.xlarge": EC2_INSTANCE_POWER_W["m5.xlarge"]}

        avg_idle = sum(
            v["idle"] for k, v in eligible.items()
            if any(k.startswith(p) for p in ("m5.", "m5a.", "t3."))
        ) / max(sum(1 for k in eligible if any(k.startswith(p) for p in ("m5.", "m5a.", "t3."))), 1)

        avg_load = sum(
            v["pct100"] for k, v in eligible.items()
            if any(k.startswith(p) for p in ("m5.", "m5a.", "t3."))
        ) / max(sum(1 for k in eligible if any(k.startswith(p) for p in ("m5.", "m5a.", "t3."))), 1)

        df.at[idx, "power_cloud_idle_w"] = avg_idle
        df.at[idx, "power_cloud_at_load_w"] = avg_load

    non_aws_cloud_mask = df["cloud_provider"].notna() & (df["cloud_provider"] != "aws")
    for idx, row in df[non_aws_cloud_mask].iterrows():
        min_w = CCF_VCPU_MIN_W.get(row["cloud_provider"], 0.74) * NODE_VCPU_MIN
        max_w = CCF_VCPU_MAX_W.get(row["cloud_provider"], 3.50) * NODE_VCPU_MIN
        df.at[idx, "power_cloud_idle_w"] = min_w + 0.0 * (max_w - min_w) + SSD_OVERHEAD_W
        df.at[idx, "power_cloud_at_load_w"] = min_w + 0.5 * (max_w - min_w) + SSD_OVERHEAD_W

    cloud_mask = df["cloud_provider"].notna() & df["power_cloud_at_load_w"].notna()
    df.loc[cloud_mask, "power_node_w"] = (
        (df.loc[cloud_mask, "power_cloud_at_load_w"] + SSD_OVERHEAD_W) * CLOUD_PUE
    )

    df = df.drop(columns=["is_validator", "required_ram_gb"])

    return df