import json
import re
import time

import requests

from shared_variables import IP_RANGES_DIR, OFFICIAL_PROVIDER_URLS, RIPE_PROVIDERS

OUTPUT_DIR = IP_RANGES_DIR

OFFICIAL_PROVIDER_PARSERS = {
    "aws":    lambda data: [p["ip_prefix"] for p in data["prefixes"]],
    "gcp":    lambda data: [p["ipv4Prefix"] for p in data["prefixes"] if "ipv4Prefix" in p],
    "azure":  lambda data: [
        cidr
        for v in data["values"]
        for cidr in v["properties"].get("addressPrefixes", [])
        if ":" not in cidr
    ],
    "oracle": lambda data: [
        c["cidr"]
        for region in data.get("regions", [])
        for c in region.get("cidrs", [])
        if ":" not in c["cidr"]
    ],
}


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


def _get(url: str, params: dict | None = None, retries: int = 3, timeout: int = 40):
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.Timeout:
            print(f"    timeout (attempt {attempt}/{retries}) — {url}")
            if attempt < retries:
                time.sleep(2 ** attempt)
        except Exception as exc:
            print(f"    failed — {exc}")
            return None
    return None


def _discover_asns(config: dict) -> list[int]:
    asns = set(config["seed_asns"])
    for term in config["search_terms"]:
        data = _get("https://stat.ripe.net/data/searchcomplete/data.json", params={"resource": term})
        if not data:
            continue
        for category in data["data"]["categories"]:
            if category["category"] != "ASNs":
                continue
            for suggestion in category["suggestions"]:
                if config["name_filter"] in suggestion["description"].lower():
                    asns.add(int(suggestion["value"].lstrip("AS")))
        time.sleep(0.15)
    return sorted(asns)


def _fetch_ripe_prefixes(asn: int) -> list[str]:
    data = _get("https://stat.ripe.net/data/announced-prefixes/data.json", params={"resource": f"AS{asn}"})
    if not data:
        return []
    return [p["prefix"] for p in data["data"]["prefixes"] if ":" not in p["prefix"]]


def download_all():
    OUTPUT_DIR.mkdir(exist_ok=True)

    try:
        OFFICIAL_PROVIDER_URLS["azure"] = _get_azure_url()
        print(f"azure: resolved -> {OFFICIAL_PROVIDER_URLS['azure']}")
    except Exception as exc:
        print(f"azure: FAILED to resolve URL — {exc}")

    print("\nFetching official IP ranges...")
    for provider, url in OFFICIAL_PROVIDER_URLS.items():
        data = _get(url)
        if data is None:
            print(f"  {provider}: FAILED")
            continue
        prefixes = OFFICIAL_PROVIDER_PARSERS[provider](data)
        out = OUTPUT_DIR / f"{provider}.json"
        out.write_text(json.dumps({"prefixes": prefixes}, indent=2))
        print(f"  {provider}: {len(prefixes)} prefixes -> {out.name}")

    print("\nDiscovering and fetching RIPE-registered provider ASNs...")
    for provider, config in RIPE_PROVIDERS.items():
        asns = _discover_asns(config)
        print(f"  {provider}: {len(asns)} ASN(s) discovered -> {asns}")

        prefixes: list[str] = []
        for asn in asns:
            fetched = _fetch_ripe_prefixes(asn)
            print(f"    AS{asn}: {len(fetched)} prefixes")
            prefixes.extend(fetched)
            time.sleep(0.15)

        prefixes = sorted(set(prefixes))
        out = OUTPUT_DIR / f"{provider}.json"
        out.write_text(json.dumps({"prefixes": prefixes}, indent=2))
        print(f"  {provider}: {len(prefixes)} unique prefixes total -> {out.name}\n")

    print("Done.")


if __name__ == "__main__":
    download_all()