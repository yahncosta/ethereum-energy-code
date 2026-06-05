SSD_OVERHEAD_W_PANKOVSKA: float = 5.0

CLOUD_PUE_PANKOVSKA: float = 1.2

NODE_VCPU_MIN_NON_VALIDATOR: int = 4
NODE_VCPU_MIN_VALIDATOR: int = 8
NODE_RAM_NON_VALIDATOR_GB: int = 32
NODE_RAM_VALIDATOR_GB: int = 64

EC2_INSTANCE_POWER_W: dict[str, dict[str, float]] = {
    "m5.2xlarge":   {"vcpu": 8,  "ram_gb": 32,  "idle": 17.64,  "pct10": 27.92,  "pct50": 56.48,  "pct100": 79.82},
    "m5.4xlarge":   {"vcpu": 16, "ram_gb": 64,  "idle": 35.28,  "pct10": 55.84,  "pct50": 112.97, "pct100": 159.63},
    "m5.8xlarge":   {"vcpu": 32, "ram_gb": 128, "idle": 70.56,  "pct10": 111.67, "pct50": 225.93, "pct100": 319.26},
    "m5a.2xlarge":  {"vcpu": 8,  "ram_gb": 32,  "idle": 16.94,  "pct10": 26.88,  "pct50": 44.54,  "pct100": 59.82},
    "m5a.4xlarge":  {"vcpu": 16, "ram_gb": 64,  "idle": 33.88,  "pct10": 53.75,  "pct50": 89.08,  "pct100": 119.64},
    "m5a.8xlarge":  {"vcpu": 32, "ram_gb": 128, "idle": 67.75,  "pct10": 107.50, "pct50": 178.17, "pct100": 239.27},
    "m6i.2xlarge":  {"vcpu": 8,  "ram_gb": 32,  "idle": 18.25,  "pct10": 29.03,  "pct50": 48.51,  "pct100": 64.90},
    "m6i.4xlarge":  {"vcpu": 16, "ram_gb": 64,  "idle": 36.51,  "pct10": 58.07,  "pct50": 97.02,  "pct100": 129.79},
    "m6i.8xlarge":  {"vcpu": 32, "ram_gb": 128, "idle": 73.02,  "pct10": 116.14, "pct50": 194.04, "pct100": 259.58},
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
}

NON_HYPERSCALE_VCPU_MAX_W: dict[str, float] = {
    provider: round(
        sum(_CCF_MICROARCH_MAX_W[arch] for arch in archs) / len(archs),
        4,
    )
    for provider, archs in _PROVIDER_MICROARCHS.items()
}