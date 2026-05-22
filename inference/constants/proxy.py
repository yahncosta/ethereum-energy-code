PROXY_CL_MARGINAL_W: dict[str, float] = {
    "grandine": 4.0,
}

PROXY_EL_MARGINAL_W: dict[str, float] = {
    "nethermind": 6.0,
    "reth":       4.0,
}

ERIGON_CAPLIN_COMBINED_MARGINAL_W: float = 4.0

PROXY_CL_SOURCE: dict[str, str] = {
    "grandine": "nimbus",
}

PROXY_EL_SOURCE: dict[str, str] = {
    "nethermind": "geth",
    "reth":       "erigon",
}