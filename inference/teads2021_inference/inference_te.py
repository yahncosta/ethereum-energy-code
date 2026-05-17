import pandas as pd

from inference.teads2021_inference.constants_te import EC2_INSTANCE_POWER_W
from inference.pankovska2024_inference.constants_pk import (
    NODE_RAM_NON_VALIDATOR_GB,
    NODE_RAM_VALIDATOR_GB,
    NODE_VCPU_MIN,
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


def infer_teads_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["ec2_instance_type"] = None
    df["power_cloud_idle_w"] = float("nan")
    df["power_cloud_at_load_w"] = float("nan")

    aws_mask = df["cloud_provider"] == "aws"
    for idx, row in df[aws_mask].iterrows():
        is_validator = bool(row.get("is_validator_node", False))
        instance = _select_ec2_instance(is_validator)
        df.at[idx, "ec2_instance_type"] = instance
        df.at[idx, "power_cloud_idle_w"] = _avg_ec2_power(is_validator, "idle")
        df.at[idx, "power_cloud_at_load_w"] = _avg_ec2_power(is_validator, "pct100")

    return df