_TIER_WEIGHTS: dict[int, float] = {4: 0.25, 5: 0.50, 6: 0.25}

_IDLE: dict[int, float] = {4: 3.66, 5: 25.04, 6: 78.17}

ARM_IDLE_W: float = 3.04

WEIGHTED_IDLE_W: float = sum(_TIER_WEIGHTS[t] * v for t, v in _IDLE.items())

COMBINED_ADJUSTMENT_FACTOR: float = 0.91

CCRI_CL_MARGINAL_W: dict[str, float] = {
    "lighthouse": 6.89,
    "prysm":      8.41,
    "teku":       9.49,
    "nimbus":     5.99,
    "lodestar":   11.01,
}

CCRI_EL_MARGINAL_W: dict[str, float] = {
    "geth":   19.58,
    "erigon": 24.60,
    "besu":   41.84,
}

PROXY_CL_MARGINAL_W: dict[str, float] = {
    "grandine": CCRI_CL_MARGINAL_W["nimbus"],
    "caplin":   0.0,
}

PROXY_EL_MARGINAL_W: dict[str, float] = {
    "nethermind": CCRI_EL_MARGINAL_W["geth"],
    "reth":       CCRI_EL_MARGINAL_W["erigon"],
}