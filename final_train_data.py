from datasets import load_dataset, DatasetDict

REPO_ID = "yhackspacher/ethereum-crawl"

COLUMNS_TO_DROP = [
    "PeerID_cl",
    "Maddrs_cl",
    "Protocols_cl",
    "ConnectDuration_cl",
    "CrawlDuration_cl",
    "VisitStartedAt_cl",
    "VisitEndedAt_cl",
    "ConnectErrorStr_cl",
    "CrawlErrorStr_cl",
    "attnets_cl",
    "fork_digest_cl",
    "next_fork_epoch_cl",
    "next_fork_version_cl",
    "seq_cl",
    "signature_cl",
    "tcp_cl",
    "udp_cl",
    "opstack_chain_id_cl",
    "opstack_version_cl",
    "direct_close_cl",
    "gen_tcp_addr_cl",
    "connect_error_cl",
    "PeerID_el",
    "Maddrs_el",
    "Protocols_el",
    "ConnectDuration_el",
    "CrawlDuration_el",
    "VisitStartedAt_el",
    "VisitEndedAt_el",
    "ConnectErrorStr_el",
    "CrawlErrorStr_el",
    "connect_error_el",
]


print("Loading final_visits_merged...")
ds = load_dataset(REPO_ID, name="final_visits_merged", split="train")
print(f"  Rows: {len(ds)}")
print(f"  Columns: {ds.column_names}")

to_drop = [c for c in COLUMNS_TO_DROP if c in ds.column_names]
to_keep = [c for c in ds.column_names if c not in to_drop]

print(f"\nDropping: {to_drop}")
print(f"Keeping:  {to_keep}")

ds_train = ds.remove_columns(to_drop)

print(f"\nPushing to train_data (overwriting)...")
DatasetDict({"train": ds_train}).push_to_hub(
    REPO_ID,
    config_name="train_data",
    commit_message="Overwrite train_data: drop non-energy-relevant columns from final_visits_merged",
)

print(f"Done. train_data: {len(ds_train)} rows x {len(to_keep)} columns.")
print(f"Final columns: {ds_train.column_names}")