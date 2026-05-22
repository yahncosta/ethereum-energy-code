import pandas as pd

from inference.constants.p2p_spec2020 import (
    ATTNETS_SATURATION_THRESHOLD,
    GOSSIP_PHASE_NO_VALIDATORS,
    GOSSIP_PHASE_SATURATED,
    GOSSIP_PHASE_RAMPING,
)


def _gossip_phase(attnets_num: float) -> str:
    n = int(attnets_num) if not pd.isna(attnets_num) else 0
    if n == 0:
        return GOSSIP_PHASE_NO_VALIDATORS
    if n < ATTNETS_SATURATION_THRESHOLD:
        return GOSSIP_PHASE_RAMPING
    return GOSSIP_PHASE_SATURATED


def infer_p2p_metadata_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["gossip_phase"] = df["attnets_num"].apply(_gossip_phase)
    df["is_sync_committee_member"] = df["syncnets_num"] > 0

    return df