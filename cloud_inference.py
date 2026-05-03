import time
import ipaddress
import collections
import requests
import pandas as pd


_OFFICIAL_PROVIDER_URLS: dict[str, str] = {
    "aws":    "https://ip-ranges.amazonaws.com/ip-ranges.json",
    "gcp":    "https://www.gstatic.com/ipranges/cloud.json",
    "azure":  "https://download.microsoft.com/download/7/1/d/71d86715-5596-4529-9b13-da13a5de5b63/ServiceTags_Public_20260427.json",
    "oracle": "https://docs.oracle.com/en-us/iaas/tools/public_ip_ranges.json",
}

_RIPE_ASN_MAP: dict[str, list[int]] = {
    "hetzner":      [24940, 213230],
    "ovh":          [16276, 35540],
    "contabo":      [51167],
    "netcup":       [197540],
    "latitude":     [396356],
    "digitalocean": [14061],
    "vultr":        [20473],
    "linode":       [63949],
    "leaseweb":     [60781],
    "clouvider":    [62240],
}

_CLOUD_PROVIDERS: frozenset[str] = frozenset(
    list(_OFFICIAL_PROVIDER_URLS.keys()) + list(_RIPE_ASN_MAP.keys())
)


def infer_cloud_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    indices: list[tuple[str, dict[int, list[ipaddress.IPv4Network]]]] = []

    print("  [cloud_inference] fetching official IP ranges (AWS, GCP, Azure, Oracle)...")
    for provider, url in _OFFICIAL_PROVIDER_URLS.items():
        try:
            data = requests.get(url, timeout=20).raise_for_status() or requests.get(url, timeout=20).json()
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            data = r.json()

            if provider == "aws":
                nets = [ipaddress.ip_network(p["ip_prefix"]) for p in data["prefixes"]]
            elif provider == "gcp":
                nets = [ipaddress.ip_network(p["ipv4Prefix"]) for p in data["prefixes"] if "ipv4Prefix" in p]
            elif provider == "azure":
                nets = [
                    ipaddress.ip_network(cidr, strict=False)
                    for v in data["values"]
                    for cidr in v["properties"].get("addressPrefixes", [])
                    if ":" not in cidr
                ]
            elif provider == "oracle":
                nets = [
                    ipaddress.ip_network(c["cidr"], strict=False)
                    for region in data.get("regions", [])
                    for c in region.get("cidrs", [])
                    if ":" not in c["cidr"]
                ]

            idx: dict[int, list[ipaddress.IPv4Network]] = collections.defaultdict(list)
            for net in nets:
                idx[int(net.network_address) >> 24].append(net)
            indices.append((provider, dict(idx)))
            print(f"    {provider}: ok")
        except Exception as exc:
            print(f"    {provider}: FAILED — {exc}")

    print("  [cloud_inference] fetching ASN prefix lists from RIPE stat...")
    for provider, asns in _RIPE_ASN_MAP.items():
        nets = []
        for asn in asns:
            try:
                r = requests.get(
                    f"https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS{asn}",
                    timeout=20,
                )
                r.raise_for_status()
                for p in r.json()["data"]["prefixes"]:
                    if ":" not in p["prefix"]:
                        nets.append(ipaddress.ip_network(p["prefix"], strict=False))
                time.sleep(0.15)
            except Exception as exc:
                print(f"    [cloud_inference] warning: AS{asn} ({provider}) failed: {exc}")
        idx = collections.defaultdict(list)
        for net in nets:
            idx[int(net.network_address) >> 24].append(net)
        indices.append((provider, dict(idx)))
        print(f"    {provider}: ok")

    print(f"  [cloud_inference] classifying {len(df)} IPs...")
    t0 = time.time()

    def classify(ip_str: str) -> str:
        try:
            addr = ipaddress.ip_address(ip_str)
        except ValueError:
            return "other"
        for provider, idx in indices:
            if any(addr in net for net in idx.get(int(addr) >> 24, [])):
                return provider
        return "other"

    df["cloud_provider"] = df["ip"].apply(classify)
    df["is_cloud_hosted"] = df["cloud_provider"].isin(_CLOUD_PROVIDERS)
    print(f"  [cloud_inference] done in {time.time() - t0:.2f}s")

    return df