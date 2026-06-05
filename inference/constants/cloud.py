SSD_OVERHEAD_W_PANKOVSKA: float = 5.0

CLOUD_PUE_PANKOVSKA: float = 1.2

NODE_VCPU_MIN_NON_VALIDATOR: int = 4
NODE_VCPU_MIN_VALIDATOR: int = 8
NODE_RAM_NON_VALIDATOR_GB: int = 32
NODE_RAM_VALIDATOR_GB: int = 64

EC2_INSTANCE_POWER_W: dict[str, dict] = {
    "m6i.2xlarge":  {"vcpu": 8,  "ram_gb": 32,  "arch": "x86", "pct100": 64.90},
    "m6i.4xlarge":  {"vcpu": 16, "ram_gb": 64,  "arch": "x86", "pct100": 129.79},
    "m6i.8xlarge":  {"vcpu": 32, "ram_gb": 128, "arch": "x86", "pct100": 259.58},
    "m7g.2xlarge":  {"vcpu": 8,  "ram_gb": 32,  "arch": "ARM", "pct100": 47.60},
    "m7g.4xlarge":  {"vcpu": 16, "ram_gb": 64,  "arch": "ARM", "pct100": 95.20},
    "m7g.8xlarge":  {"vcpu": 32, "ram_gb": 128, "arch": "ARM", "pct100": 190.40},
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