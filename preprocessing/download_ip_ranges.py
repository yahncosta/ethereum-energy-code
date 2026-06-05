import collections
import ipaddress
import json
import re
import time
from pathlib import Path

import requests

OUTPUT_DIR = Path(__file__).parent / "ip_ranges"

OFFICIAL_PROVIDER_URLS: dict[str, str] = {
    "aws":    "https://ip-ranges.amazonaws.com/ip-ranges.json",
    "gcp":    "https://www.gstatic.com/ipranges/cloud.json",
    "oracle": "https://docs.oracle.com/en-us/iaas/tools/public_ip_ranges.json",
}

RIPE_ASN_MAP: dict[str, list[int]] = {
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

PROVIDERS = list(OFFICIAL_PROVIDER_URLS.keys()) + ["azure"] + list(RIPE_ASN_MAP.keys())


def _get_azure_url() -> str:
    r = requests.get(
        "https://www.microsoft.com/en-us/download/confirmation.aspx?id=56519",
        timeout=20,
    )
    r.raise_for_status()
    match = re.search(
        r'https://download\.microsoft\.com/download/[^"\']+ServiceTags_Public_\d+\.json',
        r.text,
    )
    if not match:
        raise ValueError("Could not find Azure IP ranges URL")
    return match.group(0)


def _fetch_ripe_prefixes(asn: int, retries: int = 3, timeout: int = 40) -> list[str]:
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(
                f"https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS{asn}",
                timeout=timeout,
            )
            r.raise_for_status()
            return [
                p["prefix"]
                for p in r.json()["data"]["prefixes"]
                if ":" not in p["prefix"]
            ]
        except requests.exceptions.Timeout:
            print(f"    AS{asn}: timeout (attempt {attempt}/{retries})")
            if attempt < retries:
                time.sleep(2 ** attempt)
        except Exception as exc:
            print(f"    AS{asn}: failed — {exc}")
            return []
    print(f"    AS{asn}: all {retries} attempts timed out, skipping")
    return []


def download_all():
    OUTPUT_DIR.mkdir(exist_ok=True)

    try:
        azure_url = _get_azure_url()
        print(f"azure: resolved -> {azure_url}")
        OFFICIAL_PROVIDER_URLS["azure"] = azure_url
    except Exception as exc:
        print(f"azure: FAILED to resolve URL — {exc}")

    print("\nFetching official IP ranges...")
    for provider, url in OFFICIAL_PROVIDER_URLS.items():
        try:
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            data = r.json()

            if provider == "aws":
                prefixes = [p["ip_prefix"] for p in data["prefixes"]]
            elif provider == "gcp":
                prefixes = [p["ipv4Prefix"] for p in data["prefixes"] if "ipv4Prefix" in p]
            elif provider == "azure":
                prefixes = [
                    cidr
                    for v in data["values"]
                    for cidr in v["properties"].get("addressPrefixes", [])
                    if ":" not in cidr
                ]
            elif provider == "oracle":
                prefixes = [
                    c["cidr"]
                    for region in data.get("regions", [])
                    for c in region.get("cidrs", [])
                    if ":" not in c["cidr"]
                ]

            out = OUTPUT_DIR / f"{provider}.json"
            out.write_text(json.dumps({"prefixes": prefixes}, indent=2))
            print(f"  {provider}: {len(prefixes)} prefixes -> {out.name}")
        except Exception as exc:
            print(f"  {provider}: FAILED — {exc}")

    print("\nFetching ASN prefix lists from RIPE stat...")
    for provider, asns in RIPE_ASN_MAP.items():
        prefixes = []
        for asn in asns:
            fetched = _fetch_ripe_prefixes(asn)
            print(f"  AS{asn} ({provider}): {len(fetched)} prefixes")
            prefixes.extend(fetched)
            time.sleep(0.15)

        out = OUTPUT_DIR / f"{provider}.json"
        out.write_text(json.dumps({"prefixes": prefixes}, indent=2))
        print(f"  {provider}: {len(prefixes)} total -> {out.name}\n")

    print("Done.")


if __name__ == "__main__":
    download_all()