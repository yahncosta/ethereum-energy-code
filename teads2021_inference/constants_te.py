EC2_INSTANCE_POWER_W: dict[str, dict[str, float]] = {
    "m5.large":    {"vcpu": 2, "ram_gb": 8,  "idle": 9.3,  "pct10": 14.5, "pct50": 24.5, "pct100": 39.7},
    "m5.xlarge":   {"vcpu": 4, "ram_gb": 16, "idle": 16.1, "pct10": 25.4, "pct50": 44.6, "pct100": 72.9},
    "m5.2xlarge":  {"vcpu": 8, "ram_gb": 32, "idle": 29.7, "pct10": 47.5, "pct50": 85.8, "pct100": 141.3},
    "m5a.large":   {"vcpu": 2, "ram_gb": 8,  "idle": 7.8,  "pct10": 12.0, "pct50": 21.0, "pct100": 35.0},
    "m5a.xlarge":  {"vcpu": 4, "ram_gb": 16, "idle": 13.5, "pct10": 21.0, "pct50": 37.8, "pct100": 63.0},
    "m5a.2xlarge": {"vcpu": 8, "ram_gb": 32, "idle": 25.0, "pct10": 39.0, "pct50": 70.0, "pct100": 118.0},
    "t3.medium":   {"vcpu": 2, "ram_gb": 4,  "idle": 4.3,  "pct10": 7.0,  "pct50": 13.5, "pct100": 24.0},
    "t3.large":    {"vcpu": 2, "ram_gb": 8,  "idle": 6.8,  "pct10": 11.0, "pct50": 20.5, "pct100": 36.0},
    "t3.xlarge":   {"vcpu": 4, "ram_gb": 16, "idle": 11.4, "pct10": 18.5, "pct50": 35.0, "pct100": 62.0},
}