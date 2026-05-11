import collections
import ipaddress
import re
import time

import numpy as np
import pandas as pd
import requests
from datasets import load_dataset, DatasetDict, Dataset

REPO_ID = "yhackspacher/ethereum-crawl"

COLUMNS_TO_KEEP = {
    "ip":              "ip",
    "AgentVersion_cl": "AgentVersion_cl",
    "attnets_num_cl":  "attnets_num",
    "syncnets_cl":     "syncnets",
    "AgentVersion_el": "AgentVersion_el",
    "Protocols_cl":    "Protocols_cl",
    "Protocols_el":    "Protocols_el",
}

_ARM_TOKENS = {"aarch64", "aarch_64", "arm64"}
_X86_TOKENS = {"x86_64", "amd64", "linux-x64", "windows-x64", "linux-386", "x86_64-unknown-linux-gnu"}

_CL_PATTERNS = [
    ("lighthouse", re.compile(r"lighthouse", re.IGNORECASE)),
    ("prysm",      re.compile(r"prysm",      re.IGNORECASE)),
    ("teku",       re.compile(r"teku",        re.IGNORECASE)),
    ("nimbus",     re.compile(r"nimbus",      re.IGNORECASE)),
    ("lodestar",   re.compile(r"lodestar",    re.IGNORECASE)),
    ("grandine",   re.compile(r"grandine",    re.IGNORECASE)),
    ("caplin",     re.compile(r"caplin",      re.IGNORECASE)),
]

_EL_PATTERNS = [
    ("geth",       re.compile(r"^geth",      re.IGNORECASE)),
    ("nethermind", re.compile(r"nethermind", re.IGNORECASE)),
    ("besu",       re.compile(r"^besu",      re.IGNORECASE)),
    ("erigon",     re.compile(r"erigon",     re.IGNORECASE)),
    ("reth",       re.compile(r"^reth",      re.IGNORECASE)),
]

OFFICIAL_PROVIDER_URLS: dict[str, str] = {
    "aws":    "https://ip-ranges.amazonaws.com/ip-ranges.json",
    "gcp":    "https://www.gstatic.com/ipranges/cloud.json",
    "azure":  "https://download.microsoft.com/download/7/1/d/71d86715-5596-4529-9b13-da13a5de5b63/ServiceTags_Public_20260427.json",
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


def _detect_arch(agent: str) -> str | None:
    if not agent or (isinstance(agent, float) and np.isnan(agent)):
        return None
    low = agent.lower()
    is_arm = any(tok in low for tok in _ARM_TOKENS)
    is_x86 = any(tok in low for tok in _X86_TOKENS)
    if is_arm and is_x86:
        return None
    if is_arm:
        return "ARM"
    if is_x86:
        return "x86"
    return None


def _match_client(agent: str, patterns) -> str | None:
    for name, pat in patterns:
        if pat.search(agent):
            return name
    return None


def _parse_agent(agent, patterns) -> tuple:
    if not agent or (isinstance(agent, float) and np.isnan(agent)):
        return None, None
    return _match_client(agent, patterns), _detect_arch(agent)


def _resolve_hw_arch(cl_arch, el_arch) -> str | None:
    archs = {a for a in (cl_arch, el_arch) if a is not None}
    if len(archs) > 1:
        return None
    if len(archs) == 1:
        return archs.pop()
    return None


def _build_ip_indices() -> list[tuple[str, dict[int, list[ipaddress.IPv4Network]]]]:
    indices = []

    print("Fetching official IP ranges (AWS, GCP, Azure, Oracle)...")
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
            print(f"  {provider}: ok")
        except Exception as exc:
            print(f"  {provider}: FAILED — {exc}")

    print("Fetching ASN prefix lists from RIPE stat...")
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
                print(f"  warning: AS{asn} ({provider}) failed: {exc}")

        idx = collections.defaultdict(list)
        for net in nets:
            idx[int(net.network_address) >> 24].append(net)
        indices.append((provider, dict(idx)))
        print(f"  {provider}: ok")

    return indices


def _classify_ip(ip_str: str, indices) -> str | None:
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return None
    for provider, idx in indices:
        if any(addr in net for net in idx.get(int(addr) >> 24, [])):
            return provider
    return None


print("Loading final_visits_merged...")
ds = load_dataset(REPO_ID, name="final_visits_merged", split="train")
print(f"  Rows: {len(ds)}")
print(f"  Columns: {ds.column_names}")

df = ds.to_pandas()

missing = [c for c in COLUMNS_TO_KEEP if c not in df.columns]
if missing:
    print(f"  Warning - columns not found: {missing}")

df = df[[c for c in COLUMNS_TO_KEEP if c in df.columns]]
df = df.rename(columns=COLUMNS_TO_KEEP)

print(f"\nSelected columns: {list(df.columns)}")

cl_parsed = df["AgentVersion_cl"].apply(lambda v: _parse_agent(v, _CL_PATTERNS))
el_parsed = df["AgentVersion_el"].apply(lambda v: _parse_agent(v, _EL_PATTERNS))

df["consensus_client"], cl_arch = zip(*cl_parsed)
df["execution_client"], el_arch = zip(*el_parsed)

df["hw_arch"] = [_resolve_hw_arch(c, e) for c, e in zip(cl_arch, el_arch)]

before = len(df)

null_arch = df["hw_arch"].isna()
null_cl   = df["consensus_client"].isna()
null_el   = df["execution_client"].isna()

df = df[~null_arch & ~null_cl & ~null_el].reset_index(drop=True)

print(f"  dropped (null hw_arch)          : {null_arch.sum()}")
print(f"  dropped (null consensus_client) : {null_cl.sum()}")
print(f"  dropped (null execution_client) : {null_el.sum()}")
print(f"  dropped total (unique rows)     : {before - len(df)}")
print(f"  remaining rows                  : {len(df)}")
print(f"  hw_arch ARM                     : {(df['hw_arch'] == 'ARM').sum()}")
print(f"  hw_arch x86                     : {(df['hw_arch'] == 'x86').sum()}")

COLUMNS_TO_DROP = ["AgentVersion_cl", "AgentVersion_el", "Protocols_el", "Protocols_cl"]
df = df.drop(columns=[c for c in COLUMNS_TO_DROP if c in df.columns])

print("\nClassifying IPs by cloud provider...")
indices = _build_ip_indices()
t0 = time.time()
df["cloud_provider"] = df["ip"].apply(lambda ip: _classify_ip(ip, indices))
print(f"  Done in {time.time() - t0:.2f}s")

cloud_count = int(df["cloud_provider"].notna().sum())
print(f"  Cloud-hosted : {cloud_count}/{len(df)} ({100 * cloud_count / len(df):.1f}%)")
print(df["cloud_provider"].value_counts(dropna=False).to_string())

print("\nPushing to pre_train_data...")
DatasetDict({"train": Dataset.from_pandas(df, preserve_index=False)}).push_to_hub(
    REPO_ID,
    config_name="pre_train_data",
    commit_message="Overwrite pre_train_data: client parsing, hw_arch, cloud_provider",
)

print(f"Done. pre_train_data: {len(df)} rows x {len(df.columns)} columns.")