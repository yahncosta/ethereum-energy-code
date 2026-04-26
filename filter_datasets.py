from datasets import load_dataset, DatasetDict

REPO_ID = "yhackspacher/ethereum-crawl"


def apply_shared_filters(dataset):
    return dataset.filter(
        lambda row:
            row["ConnectErrorStr"] == "" and
            row.get("AgentVersion") not in (None, "")
    )


def apply_consensus_filters(dataset):
    return dataset.filter(
        lambda row:
            row.get("fork_digest") not in (None, "") and
            row.get("opstack_chain_id") is None
    )


for source_config, target_config, is_consensus in [
    ("consensus_visits", "final_visits_consensus", True),
    ("execution_visits",  "final_visits_execution", False),
]:
    print(f"Loading {source_config}...")
    ds = load_dataset(REPO_ID, name=source_config, split="train")
    print(f"  Rows before filtering: {len(ds)}")

    ds = apply_shared_filters(ds)
    print(f"  Rows after shared filters: {len(ds)}")

    if is_consensus:
        ds = apply_consensus_filters(ds)
        print(f"  Rows after consensus-only filters: {len(ds)}")

    DatasetDict({"train": ds}).push_to_hub(
        REPO_ID,
        config_name=target_config,
        commit_message=f"Add {target_config}: filtering applied",
    )
    print(f"  Uploaded as {target_config}.\n")

print("Done.")