import collections
import ipaddress
import json
import time
from pathlib import Path

import pandas as pd

from preprocessing.download_ip_ranges import PROVIDERS

IP_RANGES_DIR = Path(__file__).parent / "ip_ranges"


def load_ip_indices() -> list[tuple[str, dict[int, list[ipaddress.IPv4Network]]]]:
    indices = []
    for provider in PROVIDERS:
        path = IP_RANGES_DIR / f"{provider}.json"
        if not path.exists():
            print(f"  {provider}: missing file {path}, skipping")
            continue

        data = json.loads(path.read_text())
        nets = [ipaddress.ip_network(p, strict=False) for p in data["prefixes"]]

        idx: dict[int, list[ipaddress.IPv4Network]] = collections.defaultdict(list)
        for net in nets:
            idx[int(net.network_address) >> 24].append(net)

        indices.append((provider, dict(idx)))
        print(f"  {provider}: {len(nets)} prefixes loaded")

    return indices


def classify_ip(ip_str: str, indices) -> str | None:
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return None
    for provider, idx in indices:
        if any(addr in net for net in idx.get(int(addr) >> 24, [])):
            return provider
    return None


def assign_cloud_provider(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    indices = load_ip_indices()

    t0 = time.time()
    df["cloud_provider"] = df["ip"].apply(lambda ip: classify_ip(ip, indices))
    print(f"  Done in {time.time() - t0:.2f}s")

    cloud_count = int(df["cloud_provider"].notna().sum())
    print(f"  Cloud-hosted : {cloud_count}/{len(df)} ({100 * cloud_count / len(df):.1f}%)")
    print(df["cloud_provider"].value_counts(dropna=False).to_string())

    return df