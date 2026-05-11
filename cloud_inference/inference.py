import collections
import ipaddress
import time

import pandas as pd
import requests

from cloud_inference.constants import OFFICIAL_PROVIDER_URLS, RIPE_ASN_MAP


def infer_cloud_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    indices: list[tuple[str, dict[int, list[ipaddress.IPv4Network]]]] = []

    print("  [cloud_inference] fetching official IP ranges (AWS, GCP, Azure, Oracle)...")
    for provider, url in OFFICIAL_PROVIDER_URLS.items():
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
            else:
                nets = []

            idx: dict[int, list[ipaddress.IPv4Network]] = collections.defaultdict(list)
            for net in nets:
                idx[int(net.network_address) >> 24].append(net)

            indices.append((provider, dict(idx)))
            print(f"    {provider}: ok")
        except Exception as exc:
            print(f"    {provider}: FAILED — {exc}")

    print("  [cloud_inference] fetching ASN prefix lists from RIPE stat...")
    for provider, asns in RIPE_ASN_MAP.items():
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