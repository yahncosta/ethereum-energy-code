OFFICIAL_PROVIDER_URLS: dict[str, str] = {
    "aws": "https://ip-ranges.amazonaws.com/ip-ranges.json",
    "gcp": "https://www.gstatic.com/ipranges/cloud.json",
    "azure": "https://download.microsoft.com/download/7/1/d/71d86715-5596-4529-9b13-da13a5de5b63/ServiceTags_Public_20260427.json",
    "oracle": "https://docs.oracle.com/en-us/iaas/tools/public_ip_ranges.json",
}

RIPE_ASN_MAP: dict[str, list[int]] = {
    "hetzner": [24940, 213230],
    "ovh": [16276, 35540],
    "contabo": [51167],
    "netcup": [197540],
    "latitude": [396356],
    "digitalocean": [14061],
    "vultr": [20473],
    "linode": [63949],
    "leaseweb": [60781],
    "clouvider": [62240],
}