import re
import numpy as np
import pandas as pd
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

COLUMNS_TO_DROP = ["AgentVersion_cl", "AgentVersion_el"]
df = df.drop(columns=[c for c in COLUMNS_TO_DROP if c in df.columns])

print("\nPushing to pre_train_data...")
DatasetDict({"train": Dataset.from_pandas(df, preserve_index=False)}).push_to_hub(
    REPO_ID,
    config_name="pre_train_data",
    commit_message="Overwrite pre_train_data: select columns and parse AgentVersion fields",
)

print(f"Done. pre_train_data: {len(df)} rows x {len(df.columns)} columns.")