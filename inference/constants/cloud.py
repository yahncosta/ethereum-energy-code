SSD_OVERHEAD_W_PANKOVSKA: float = 5.0

CLOUD_PUE_PANKOVSKA: float = 1.2

NODE_VCPU_MIN_NON_VALIDATOR: int = 4
NODE_VCPU_MIN_VALIDATOR: int = 8
NODE_RAM_NON_VALIDATOR_GB: int = 32
NODE_RAM_VALIDATOR_GB: int = 64

_M6I_CPU_NAME: str = "Xeon Platinum 8375C"
_R6I_CPU_NAME: str = "Xeon Platinum 8375C"

_M6I_RAM_GB: dict[str, int] = {
    "m6i.2xlarge": 32,
    "m6i.4xlarge": 64,
    "m6i.8xlarge": 128,
}

_R6I_RAM_GB: dict[str, int] = {
    "r6i.2xlarge": 64,
    "r6i.4xlarge": 128,
}

_M6I_PKG_W_100: dict[str, float] = {
    "m6i.2xlarge": 38.20,
    "m6i.4xlarge": 76.39,
    "m6i.8xlarge": 152.78,
}

_M6I_RAM_W_100: dict[str, float] = {
    "m6i.2xlarge": 19.20,
    "m6i.4xlarge": 38.40,
    "m6i.8xlarge": 76.80,
}

_M6I_DELTA: dict[str, float] = {
    "m6i.2xlarge": 7.5,
    "m6i.4xlarge": 15.0,
    "m6i.8xlarge": 30.0,
}

EC2_INSTANCE_POWER_W: dict[str, dict] = {
    "m6i.2xlarge": {
        "vcpu":   8,
        "ram_gb": _M6I_RAM_GB["m6i.2xlarge"],
        "arch":   "x86",
        "pct100": _M6I_PKG_W_100["m6i.2xlarge"] + _M6I_RAM_W_100["m6i.2xlarge"] + _M6I_DELTA["m6i.2xlarge"],
    },
    "m6i.4xlarge": {
        "vcpu":   16,
        "ram_gb": _M6I_RAM_GB["m6i.4xlarge"],
        "arch":   "x86",
        "pct100": _M6I_PKG_W_100["m6i.4xlarge"] + _M6I_RAM_W_100["m6i.4xlarge"] + _M6I_DELTA["m6i.4xlarge"],
    },
    "m6i.8xlarge": {
        "vcpu":   32,
        "ram_gb": _M6I_RAM_GB["m6i.8xlarge"],
        "arch":   "x86",
        "pct100": _M6I_PKG_W_100["m6i.8xlarge"] + _M6I_RAM_W_100["m6i.8xlarge"] + _M6I_DELTA["m6i.8xlarge"],
    },
    "r6i.2xlarge": {
        "vcpu":   8,
        "ram_gb": _R6I_RAM_GB["r6i.2xlarge"],
        "arch":   "x86",
        "pct100": _M6I_PKG_W_100["m6i.2xlarge"] + 2 * _M6I_RAM_W_100["m6i.2xlarge"] + _M6I_DELTA["m6i.2xlarge"],
    },
    "r6i.4xlarge": {
        "vcpu":   16,
        "ram_gb": _R6I_RAM_GB["r6i.4xlarge"],
        "arch":   "x86",
        "pct100": _M6I_PKG_W_100["m6i.4xlarge"] + 2 * _M6I_RAM_W_100["m6i.4xlarge"] + _M6I_DELTA["m6i.4xlarge"],
    },
    "r6g.2xlarge": {
        "vcpu":   8,
        "ram_gb": 64,
        "arch":   "ARM",
        "pct100": 61.20,
    },
    "r6g.4xlarge": {
        "vcpu":   16,
        "ram_gb": 128,
        "arch":   "ARM",
        "pct100": 122.50,
    },
}

CCF_VCPU_MAX_W: dict[str, float] = {
    "aws":   3.50,
    "gcp":   4.26,
    "azure": 3.76,
}

_CCF_MICROARCH_MAX_W: dict[str, float] = {
    "EPYC 1st Gen":    2.6042,
    "EPYC 2nd Gen":    1.6930,
    "EPYC 3rd Gen":    1.9573,
    "EPYC 4th Gen":    2.2822,
    "EPYC 5th Gen":    8.9614,
    "Cascade Lake":    4.0632,
    "Ice Lake":        3.7582,
    "Sapphire Rapids": 4.1605,
    "Skylake":         4.1042,
}

_PROVIDER_MICROARCHS: dict[str, list[str]] = {
    "hetzner":      ["EPYC 2nd Gen", "EPYC 3rd Gen", "EPYC 4th Gen"],
    "ovh":          ["EPYC 3rd Gen", "EPYC 4th Gen", "Cascade Lake", "Sapphire Rapids"],
    "contabo":      ["EPYC 2nd Gen", "EPYC 5th Gen"],
    "netcup":       ["EPYC 2nd Gen", "EPYC 4th Gen", "EPYC 5th Gen"],
    "digitalocean": ["Skylake", "Ice Lake", "Sapphire Rapids", "EPYC 3rd Gen"],
    "vultr":        ["Cascade Lake", "EPYC 2nd Gen", "EPYC 4th Gen"],
    "linode":       ["EPYC 1st Gen", "EPYC 2nd Gen", "EPYC 3rd Gen"],
    "leaseweb":     ["Cascade Lake", "Sapphire Rapids", "EPYC 2nd Gen", "EPYC 3rd Gen"],
    "clouvider":    ["Ice Lake", "EPYC 3rd Gen", "EPYC 4th Gen"],
    "latitude":     ["EPYC 3rd Gen", "EPYC 4th Gen", "EPYC 5th Gen"],
    "oracle":       ["EPYC 3rd Gen", "EPYC 4th Gen", "EPYC 5th Gen"],
}

NON_HYPERSCALE_VCPU_MAX_W: dict[str, float] = {
    provider: round(
        sum(_CCF_MICROARCH_MAX_W[arch] for arch in archs) / len(archs),
        4,
    )
    for provider, archs in _PROVIDER_MICROARCHS.items()
}

_ALL_VCPU_MAX_W: dict[str, float] = {**CCF_VCPU_MAX_W, **NON_HYPERSCALE_VCPU_MAX_W}