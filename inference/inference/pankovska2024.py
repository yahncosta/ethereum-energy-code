import numpy as np
import pandas as pd

from inference.constants.ccf import CCF_VCPU_MIN_W, CCF_VCPU_MAX_W
from inference.constants.teads import EC2_INSTANCE_POWER_W
from inference.constants.pankovska2024 import (
    CLOUD_PUE,
    HOME_PUE,
    NODE_VCPU_MIN,
    NODE_RAM_NON_VALIDATOR_GB,
    NODE_RAM_VALIDATOR_GB,
    SSD_OVERHEAD_W,
)
from inference.constants.p2p_spec2020 import GOSSIP_PHASE_NO_VALIDATORS


def _select_ec2_instance(is_validator: bool) -> str:
    min_ram = NODE_RAM_VALIDATOR_GB if is_validator else NODE_RAM_NON_VALIDATOR_GB
    candidates = {
        k: v for k, v in EC2_INSTANCE_POWER_W.items()
        if v["ram_gb"] >= min_ram and v["vcpu"] >= NODE_VCPU_MIN
    }
    if not candidates:
        return "m5.xlarge"
    return min(candidates, key=lambda k: (candidates[k]["ram_gb"], candidates[k]["vcpu"]))


def _avg_ec2_power(is_validator: bool, load_key: str) -> float:
    min_ram = NODE_RAM_VALIDATOR_GB if is_validator else NODE_RAM_NON_VALIDATOR_GB
    families = [
        next(
            (k for k, v in EC2_INSTANCE_POWER_W.items()
             if k.startswith(prefix) and v["ram_gb"] >= min_ram and v["vcpu"] >= NODE_VCPU_MIN),
            None
        )
        for prefix in ("m5.", "m5a.", "t3.")
    ]
    matched = [EC2_INSTANCE_POWER_W[i][load_key] for i in families if i is not None]
    return sum(matched) / len(matched) if matched else EC2_INSTANCE_POWER_W["m5.xlarge"][load_key]


def _ccf_power(provider: str, utilization: float) -> float:
    vcpus = NODE_VCPU_MIN
    min_w = CCF_VCPU_MIN_W.get(provider, 0.74) * vcpus
    max_w = CCF_VCPU_MAX_W.get(provider, 3.50) * vcpus
    return min_w + utilization * (max_w - min_w) + SSD_OVERHEAD_W


def infer_pankovska_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["pue_factor"] = np.where(df["cloud_provider"].notna(), CLOUD_PUE, HOME_PUE)

    aws_mask = df["cloud_provider"] == "aws"
    for idx, row in df[aws_mask].iterrows():
        is_validator = row["gossip_phase"] != GOSSIP_PHASE_NO_VALIDATORS or row["is_sync_committee_member"]
        df.at[idx, "ec2_instance_type"]     = _select_ec2_instance(is_validator)
        df.at[idx, "power_cloud_idle_w"]    = _avg_ec2_power(is_validator, "idle")
        df.at[idx, "power_cloud_at_load_w"] = _avg_ec2_power(is_validator, "pct100")

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