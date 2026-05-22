import pandas as pd

from inference.p2pspec2020_inference.constants_p2p import (
    ATTNETS_SATURATION_THRESHOLD,
    GOSSIP_PHASE_NO_VALIDATORS,
    GOSSIP_PHASE_RAMPING,
    GOSSIP_PHASE_SATURATED,
)




def _gossip_phase(attnets_num: float) -> str:
    n = int(attnets_num) if not pd.isna(attnets_num) else 0
    if n == 0:
        return GOSSIP_PHASE_NO_VALIDATORS
    if n < ATTNETS_SATURATION_THRESHOLD:
        return GOSSIP_PHASE_RAMPING
    return GOSSIP_PHASE_SATURATED


def infer_p2p_metadata_features(df):
    df = df.copy()

    df["is_validator_node"] = (df["attnets_num"].fillna(0) > 0) | (df["syncnets_num"] > 0)

    df["is_subnet_saturated"] = df["attnets_num"].fillna(0).apply(
        lambda n: int(n) == ATTNETS_SATURATION_THRESHOLD
    )

    df["gossip_phase"] = df["attnets_num"].apply(_gossip_phase)

    df["is_sync_committee_member"] = df["syncnets_num"] > 0

    return df