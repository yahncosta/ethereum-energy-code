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


def _arch(agent: str) -> str:
    low = agent.lower()
    for tok in _ARM_TOKENS:
        if tok in low:
            return "ARM"
    return "x86"


def _match_client(agent: str, patterns) -> str | None:
    for name, pat in patterns:
        if pat.search(agent):
            return name
    return None


def _parse_agent(agent, patterns) -> tuple:
    if not agent or (isinstance(agent, float) and np.isnan(agent)):
        return None, None
    return _match_client(agent, patterns), _arch(agent)


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

df["consensus_client"], df["cl_arch"] = zip(*cl_parsed)
df["execution_client"], df["el_arch"] = zip(*el_parsed)

df["hw_arch"] = (
    (df["cl_arch"] == "ARM") | (df["el_arch"] == "ARM")
).map({True: "ARM", False: "x86"})

print(f"  consensus_client nulls : {df['consensus_client'].isna().sum()}")
print(f"  execution_client nulls : {df['execution_client'].isna().sum()}")
print(f"  ARM nodes              : {(df['hw_arch'] == 'ARM').sum()}")

print("\nPushing to pre_train_data...")
DatasetDict({"train": Dataset.from_pandas(df, preserve_index=False)}).push_to_hub(
    REPO_ID,
    config_name="pre_train_data",
    commit_message="Overwrite pre_train_data: select columns and parse AgentVersion fields",
)

print(f"Done. pre_train_data: {len(df)} rows x {len(df.columns)} columns.")