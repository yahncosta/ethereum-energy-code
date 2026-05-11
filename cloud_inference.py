import time
import ipaddress
import collections
import requests
import pandas as pd
from datasets import load_dataset, Dataset, DatasetDict


REPO_ID       = "yhackspacher/ethereum-crawl"
SOURCE_CONFIG = "pre_train_data"
TARGET_CONFIG = "train_data"
SOURCE_SPLIT  = "train"

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


def infer_cloud_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    indices: list[tuple[str, dict[int, list[ipaddress.IPv4Network]]]] = []

    print("  [cloud_inference] fetching official IP ranges (AWS, GCP, Azure, Oracle)...")
    for provider, url in _OFFICIAL_PROVIDER_URLS.items():
        try:
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

    def classify(ip_str: str) -> str | None:
        try:
            addr = ipaddress.ip_address(ip_str)
        except ValueError:
            return None
        for provider, idx in indices:
            if any(addr in net for net in idx.get(int(addr) >> 24, [])):
                return provider
        return None

    df["cloud_provider"] = df["ip"].apply(classify)
    print(f"  [cloud_inference] done in {time.time() - t0:.2f}s")

    return df


if __name__ == "__main__":
    print("=" * 60)
    print(f"Loading '{SOURCE_CONFIG}' from {REPO_ID}")
    print("=" * 60)

    df = load_dataset(REPO_ID, name=SOURCE_CONFIG, split=SOURCE_SPLIT).to_pandas()
    print(f"Loaded: {len(df)} rows x {len(df.columns)} columns\n")

    df = infer_cloud_features(df)

    total = len(df)
    cloud_count = int(df["cloud_provider"].notna().sum())
    print(f"\nCloud-hosted: {cloud_count}/{total} ({100 * cloud_count / total:.1f}%)")
    print(df["cloud_provider"].value_counts().to_string())

    print(f"\n{'=' * 60}")
    print(f"Pushing to '{TARGET_CONFIG}'...")
    print("=" * 60)

    DatasetDict({SOURCE_SPLIT: Dataset.from_pandas(df, preserve_index=False)}).push_to_hub(
        REPO_ID,
        config_name=TARGET_CONFIG,
        commit_message="cloud_inference: add cloud_provider (None when no cloud ASN matched)",
    )
    print(f"Done. https://huggingface.co/datasets/{REPO_ID}")