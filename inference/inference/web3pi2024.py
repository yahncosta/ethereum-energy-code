import pandas as pd

from inference.constants.p2p_spec2020 import GOSSIP_PHASE_SATURATED
from inference.constants.web3pi2024 import (
    WEB3PI_CONSENSUS_CLIENT,
    WEB3PI_HW_ARCH,
    WEB3PI_POWER_W,
)


def infer_web3pi_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    web3pi_mask = (
        (df["hw_arch"] == WEB3PI_HW_ARCH)
        & (df["consensus_client"] == WEB3PI_CONSENSUS_CLIENT)
        & (df["cloud_provider"].isna())
        & (df["gossip_phase"] == GOSSIP_PHASE_SATURATED)
    )

    df.loc[web3pi_mask, "power_node_w"] = WEB3PI_POWER_W

    return df