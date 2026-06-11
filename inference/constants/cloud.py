SSD_OVERHEAD_W_PANKOVSKA: float = 5.0

CLOUD_PUE_PANKOVSKA: float = 1.2

NODE_VCPU_MIN_NON_VALIDATOR: int = 4
NODE_VCPU_MIN_VALIDATOR: int = 8
NODE_RAM_NON_VALIDATOR_GB: int = 32
NODE_RAM_VALIDATOR_GB: int = 64

_M6I_INSTANCES: dict[str, dict] = {
    "m6i.2xlarge": {"vcpu": 8,  "ram_gb": 32,  "arch": "x86", "cpu": "Xeon Platinum 8375C", "pkg_w_100": 38.20, "ram_w_100": 19.20, "delta": 7.5,  "pct100": 64.90},
    "m6i.4xlarge": {"vcpu": 16, "ram_gb": 64,  "arch": "x86", "cpu": "Xeon Platinum 8375C", "pkg_w_100": 76.39, "ram_w_100": 38.40, "delta": 15.0, "pct100": 129.79},
}

_R6I_INSTANCES: dict[str, dict] = {
    "r6i.2xlarge": {"vcpu": 8,  "ram_gb": 64,  "arch": "x86", "cpu": "Xeon Platinum 8375C", "pkg_w_100": _M6I_INSTANCES["m6i.2xlarge"]["pkg_w_100"], "ram_w_100": 2 * _M6I_INSTANCES["m6i.2xlarge"]["ram_w_100"], "delta": _M6I_INSTANCES["m6i.2xlarge"]["delta"], "pct100": _M6I_INSTANCES["m6i.2xlarge"]["pkg_w_100"] + 2 * _M6I_INSTANCES["m6i.2xlarge"]["ram_w_100"] + _M6I_INSTANCES["m6i.2xlarge"]["delta"]},
    "r6i.4xlarge": {"vcpu": 16, "ram_gb": 128, "arch": "x86", "cpu": "Xeon Platinum 8375C", "pkg_w_100": _M6I_INSTANCES["m6i.4xlarge"]["pkg_w_100"], "ram_w_100": 2 * _M6I_INSTANCES["m6i.4xlarge"]["ram_w_100"], "delta": _M6I_INSTANCES["m6i.4xlarge"]["delta"], "pct100": _M6I_INSTANCES["m6i.4xlarge"]["pkg_w_100"] + 2 * _M6I_INSTANCES["m6i.4xlarge"]["ram_w_100"] + _M6I_INSTANCES["m6i.4xlarge"]["delta"]},
}

_R6G_INSTANCES: dict[str, dict] = {
    "r6g.2xlarge": {"vcpu": 8,  "ram_gb": 64,  "arch": "ARM", "pct100": 61.20},
    "r6g.4xlarge": {"vcpu": 16, "ram_gb": 128, "arch": "ARM", "pct100": 122.50},
}

_GRAVITON3_CHIP_W_100: float = 100.0
_GRAVITON3_TOTAL_VCPUS: int = 64

_M6G_INSTANCES: dict[str, dict] = {
    "m6g.2xlarge": {"vcpu": 8,  "ram_gb": 32, "arch": "ARM", "pkg_w_100": 19.10, "ram_w_100": 19.20, "delta": 3.8},
    "m6g.4xlarge": {"vcpu": 16, "ram_gb": 64, "arch": "ARM", "pkg_w_100": 38.20, "ram_w_100": 38.40, "delta": 7.5},
}

_M7G_INSTANCES_BASE: dict[str, dict] = {
    "m7g.2xlarge": _M6G_INSTANCES["m6g.2xlarge"],
    "m7g.4xlarge": _M6G_INSTANCES["m6g.4xlarge"],
}

_M7G_INSTANCES_PKG: dict[str, dict] = {
    name: {
        **v,
        "pkg_w_100": round(_GRAVITON3_CHIP_W_100 * (v["vcpu"] / _GRAVITON3_TOTAL_VCPUS), 2),
    }
    for name, v in _M7G_INSTANCES_BASE.items()
}

_M7G_INSTANCES: dict[str, dict] = {
    name: {
        "vcpu":      v["vcpu"],
        "ram_gb":    v["ram_gb"],
        "arch":      v["arch"],
        "pkg_w_100": v["pkg_w_100"],
        "ram_w_100": v["ram_w_100"],
        "delta":     v["delta"],
        "pct100":    v["pkg_w_100"] + v["ram_w_100"] + v["delta"],
    }
    for name, v in _M7G_INSTANCES_PKG.items()
}

EC2_INSTANCE_POWER_W: dict[str, dict] = {
    name: {"vcpu": v["vcpu"], "ram_gb": v["ram_gb"], "arch": v["arch"], "pct100": v["pct100"]}
    for name, v in {**_M6I_INSTANCES, **_R6I_INSTANCES, **_R6G_INSTANCES, **_M7G_INSTANCES}.items()
}

CCF_VCPU_MAX_W: dict[str, float] = {
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