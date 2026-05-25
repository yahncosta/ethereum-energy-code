_TIER_WEIGHTS: dict[int, float] = {4: 0.25, 5: 0.50, 6: 0.25}

_IDLE: dict[int, float] = {4: 3.66, 5: 25.04, 6: 78.17}

_CL_MARGINAL: dict[str, dict[int, float]] = {
    "lighthouse": {4: 2.75,  5: 3.14,  6: 18.84},
    "prysm":      {4: 3.51,  5: 2.87,  6: 24.33},
    "teku":       {4: 3.71,  5: 3.32,  6: 27.46},
    "nimbus":     {4: 1.67,  5: 2.08,  6: 17.11},
    "lodestar":   {4: 3.14,  5: 3.89,  6: 33.55},
}

_EL_MARGINAL: dict[str, dict[int, float]] = {
    "geth":   {4: 11.23, 5: 9.70,  6: 47.70},
    "erigon": {4: 18.60, 5: 17.59, 6: 44.62},
    "besu":   {4: 30.25, 5: 31.02, 6: 75.04},
}


def _weighted(per_tier: dict[int, float]) -> float:
    return sum(_TIER_WEIGHTS[t] * v for t, v in per_tier.items())


ARM_IDLE_W: float = 3.04

WEIGHTED_IDLE_W: float = _weighted(_IDLE)

COMBINED_ADJUSTMENT_FACTOR: float = 0.91

CCRI_CL_MARGINAL_W: dict[str, float] = {k: _weighted(v) for k, v in _CL_MARGINAL.items()}

CCRI_EL_MARGINAL_W: dict[str, float] = {k: _weighted(v) for k, v in _EL_MARGINAL.items()}

PROXY_CL_MARGINAL_W: dict[str, float] = {
    "grandine": CCRI_CL_MARGINAL_W["nimbus"],
    "caplin":   0.0,
}

PROXY_EL_MARGINAL_W: dict[str, float] = {
    "nethermind": CCRI_EL_MARGINAL_W["geth"],
    "reth":       CCRI_EL_MARGINAL_W["erigon"],
}