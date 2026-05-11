import numpy as np
import pandas as pd

from teads2021_inference.constants_te import (
    CCF_VCPU_MAX_W,
    CCF_VCPU_MIN_W,
    CLOUD_PUE,
    EC2_INSTANCE_POWER_W,
    HOME_PUE,
    NODE_RAM_NON_VALIDATOR_GB,
    NODE_RAM_VALIDATOR_GB,
    NODE_VCPU_MIN,
    SSD_OVERHEAD_W,
)


def _select_ec2_instance(is_validator: bool) -> str:
    min_ram = NODE_RAM_VALIDATOR_GB if is_validator else NODE_RAM_NON_VALIDATOR_GB
    candidates = {
        k: v for k, v in EC2_INSTANCE_POWER_W.items()
        if v["ram_gb"] >= min_ram and v["vcpu"] >= NODE_VCPU_MIN
    }
    if not candidates:
        return "m5.xlarge"
    return min(candidates, key=lambda k: (candidates[k]["ram_gb"], candidates[k]["vcpu"]))


def _ec2_power(instance: str, load_key: str) -> float:
    row = EC2_INSTANCE_POWER_W.get(instance, EC2_INSTANCE_POWER_W["m5.xlarge"])
    return row[load_key] + SSD_OVERHEAD_W


def _ccf_power(provider: str, utilization: float) -> float:
    vcpus = NODE_VCPU_MIN
    min_w = CCF_VCPU_MIN_W.get(provider, 0.74) * vcpus
    max_w = CCF_VCPU_MAX_W.get(provider, 3.50) * vcpus
    return min_w + utilization * (max_w - min_w) + SSD_OVERHEAD_W


def infer_teads_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["pue_factor"] = np.where(df["cloud_provider"].notna(), CLOUD_PUE, HOME_PUE)

    df["ec2_instance_type"] = None
    df["power_cloud_idle_w"] = np.nan
    df["power_cloud_at_load_w"] = np.nan

    for idx, row in df[df["cloud_provider"].notna()].iterrows():
        provider = row["cloud_provider"]
        is_validator = bool(row.get("is_validator_node", False))

        if provider == "aws":
            instance = _select_ec2_instance(is_validator)
            df.at[idx, "ec2_instance_type"] = instance
            df.at[idx, "power_cloud_idle_w"] = _ec2_power(instance, "idle")
            df.at[idx, "power_cloud_at_load_w"] = _ec2_power(instance, "pct50")
        else:
            df.at[idx, "power_cloud_idle_w"] = _ccf_power(provider, utilization=0.0)
            df.at[idx, "power_cloud_at_load_w"] = _ccf_power(provider, utilization=0.5)

    return df