CCRI_CL_MARGINAL_W: dict[str, float | None] = {
    "lighthouse": 6.0,
    "prysm":      12.0,
    "teku":       18.0,
    "nimbus":     4.0,
    "lodestar":   8.0,
    "caplin":     None,
    "grandine":   None,
}

CCRI_EL_MARGINAL_W: dict[str, float | None] = {
    "geth":       6.0,
    "erigon":     4.0,
    "besu":       11.0,
    "nethermind": None,
    "reth":       None,
}

COMBINED_ADJUSTMENT_FACTOR: float = 0.91

CCRI_HW_TIERS: dict[int, dict] = {
    1: {
        "description": "Raspberry Pi 4 Model B",
        "cpu": "ARM Cortex-A72",
        "ram_gb": 8,
        "storage": "128 GB SD card",
        "arch": "ARM",
        "meets_validator_req": False,
        "power_idle_w": 5.0,
        "power_idle_min_w": 3.5,
        "power_idle_max_w": 6.5,
    },
    2: {
        "description": "Intel NUC (low-power variant A)",
        "cpu": "Intel Core i3 (low-power)",
        "ram_gb": 16,
        "storage": "512 GB SSD",
        "arch": "x86",
        "meets_validator_req": True,
        "power_idle_w": 7.0,
        "power_idle_min_w": 5.0,
        "power_idle_max_w": 9.0,
    },
    3: {
        "description": "Intel NUC (low-power variant B)",
        "cpu": "Intel Core i5 (low-power)",
        "ram_gb": 16,
        "storage": "1 TB SSD",
        "arch": "x86",
        "meets_validator_req": True,
        "power_idle_w": 10.0,
        "power_idle_min_w": 7.0,
        "power_idle_max_w": 13.0,
    },
    4: {
        "description": "Pre-built desktop (mid-range)",
        "cpu": "Intel Core i5-1135G7",
        "ram_gb": 16,
        "storage": "2 TB SSD",
        "arch": "x86",
        "meets_validator_req": True,
        "power_idle_w": 20.0,
        "power_idle_min_w": 15.0,
        "power_idle_max_w": 25.0,
    },
    5: {
        "description": "Mid-range desktop",
        "cpu": "Intel Core i7 / AMD Ryzen 7",
        "ram_gb": 64,
        "storage": "2 TB NVMe",
        "arch": "x86",
        "meets_validator_req": True,
        "power_idle_w": 50.0,
        "power_idle_min_w": 35.0,
        "power_idle_max_w": 70.0,
    },
    6: {
        "description": "High-end workstation",
        "cpu": "AMD Threadripper",
        "ram_gb": 256,
        "storage": "4 TB NVMe",
        "arch": "x86",
        "meets_validator_req": True,
        "power_idle_w": 150.0,
        "power_idle_min_w": 100.0,
        "power_idle_max_w": 200.0,
    },
}

CCRI_BEST_GUESS_TIER_WEIGHTS: dict[int, float] = {
    4: 0.25,
    5: 0.50,
    6: 0.25,
}