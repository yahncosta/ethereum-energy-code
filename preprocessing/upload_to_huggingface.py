import json
import pandas as pd
from pathlib import Path
from datasets import Dataset, DatasetDict
from huggingface_hub import HfApi, create_repo

HF_USERNAME = "yhackspacher"
REPO_NAME   = "ethereum-crawl"
REPO_ID     = f"{HF_USERNAME}/{REPO_NAME}"
DATA_DIR    = Path("./crawl_data")

CONSENSUS_VISITS_FILE     = DATA_DIR / "consensus_fullCrawl_visits.json"
EXECUTION_VISITS_FILE     = DATA_DIR / "execution_fullCrawl_visits.json"
CONSENSUS_CRAWL_FILE      = DATA_DIR / "consensus_fullCrawl_crawl.json"
EXECUTION_CRAWL_FILE      = DATA_DIR / "execution_fullCrawl_crawl.json"
CONSENSUS_PROPERTIES_FILE = DATA_DIR / "consensus_fullCrawl_crawl_properties.json"
EXECUTION_PROPERTIES_FILE = DATA_DIR / "execution_fullCrawl_crawl_properties.json"


def read_visits(path: Path) -> pd.DataFrame:
    print(f"  Reading {path.name} ...")
    records = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    df = pd.DataFrame(records)

    props = pd.json_normalize(
        df["Properties"].apply(lambda x: x if isinstance(x, dict) else {})
    )
    df = pd.concat([df.drop(columns=["Properties"]), props], axis=1)

    for col in ["Maddrs", "Protocols"]:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: json.dumps(x) if isinstance(x, list) else "[]"
            )

    for col in ["VisitStartedAt", "VisitEndedAt"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True).astype(str)

    return df


def build_crawl_session_df() -> pd.DataFrame:
    with open(CONSENSUS_CRAWL_FILE) as f:
        cl = json.load(f)
    with open(EXECUTION_CRAWL_FILE) as f:
        el = json.load(f)

    return pd.DataFrame([
        {"layer": "consensus", **cl},
        {"layer": "execution", **el},
    ])


def parse_properties_to_df(path: Path, source: str) -> pd.DataFrame:
    with open(path) as f:
        props = json.load(f)

    rows = []
    for category, entries in props.items():
        if isinstance(entries, dict):
            for key, value in entries.items():
                rows.append({
                    "category": category,
                    "key":      key,
                    "count":    int(value),
                    "source":   source,
                })
        else:
            rows.append({
                "category": category,
                "key":      "__value__",
                "count":    int(entries),
                "source":   source,
            })

    return pd.DataFrame(rows)


def upload(df: pd.DataFrame, config_name: str, commit_message: str):
    ds = Dataset.from_pandas(df, preserve_index=False)
    DatasetDict({"train": ds}).push_to_hub(
        REPO_ID,
        config_name=config_name,
        commit_message=commit_message,
    )
    print(f"  Uploaded '{config_name}' ({len(df):,} rows).")


def main():
    print("=" * 60)
    print(f"Repository: {REPO_ID}")
    print("=" * 60)

    create_repo(repo_id=REPO_ID, repo_type="dataset", private=False, exist_ok=True)
    print("Repository ready.\n")

    print("[1/4] consensus_visits")
    upload(
        read_visits(CONSENSUS_VISITS_FILE),
        config_name="consensus_visits",
        commit_message="Add consensus layer visit records (118,537 peers)",
    )

    print("\n[2/4] execution_visits")
    upload(
        read_visits(EXECUTION_VISITS_FILE),
        config_name="execution_visits",
        commit_message="Add execution layer visit records (77,453 peers)",
    )

    print("\n[3/4] crawl_session")
    upload(
        build_crawl_session_df(),
        config_name="crawl_session",
        commit_message="Add crawl session metadata (one row per layer)",
    )

    print("\n[4/4] crawl_properties")
    cl_props = parse_properties_to_df(CONSENSUS_PROPERTIES_FILE, source="consensus")
    el_props = parse_properties_to_df(EXECUTION_PROPERTIES_FILE, source="execution")
    upload(
        pd.concat([cl_props, el_props], ignore_index=True),
        config_name="crawl_properties",
        commit_message="Add consensus + execution crawl properties with source column (category, key, count, source)",
    )

    print("\n" + "=" * 60)
    print(f"Done. Dataset: https://huggingface.co/datasets/{REPO_ID}")
    print("=" * 60)


if __name__ == "__main__":
    main()