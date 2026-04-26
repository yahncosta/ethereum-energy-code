from datasets import load_dataset, DatasetDict, Dataset
import pandas as pd
import json

REPO_ID = "yhackspacher/ethereum-crawl"

print("Loading final_visits_consensus...")
df_cl = load_dataset(REPO_ID, name="final_visits_consensus", split="train").to_pandas()
print(f"  Rows: {len(df_cl)}")

print("Loading final_visits_execution...")
df_el = load_dataset(REPO_ID, name="final_visits_execution", split="train").to_pandas()
print(f"  Rows: {len(df_el)}")

print("Extracting all IPs from Maddrs for execution layer...")

def extract_ips_from_maddrs(maddrs_json):
    try:
        maddrs = json.loads(maddrs_json) if isinstance(maddrs_json, str) else maddrs_json
        seen = []
        for m in (maddrs or []):
            parts = m.split("/")
            if len(parts) >= 3 and parts[1] == "ip4":
                ip = parts[2]
                if ip not in seen:
                    seen.append(ip)
        return seen
    except Exception:
        return []

el_records = []
for _, row in df_el.iterrows():
    ips = extract_ips_from_maddrs(row["Maddrs"])
    for ip in ips:
        el_records.append({**row.to_dict(), "ip": ip})

df_el_expanded = pd.DataFrame(el_records)
df_el_expanded = df_el_expanded[df_el_expanded["ip"].notna()]
print(f"  EL rows after IP expansion: {len(df_el_expanded)}")

print("Renaming columns to avoid collisions...")
df_cl = df_cl.rename(columns=lambda c: c + "_cl" if c != "ip" else c)
df_el_expanded = df_el_expanded.rename(columns=lambda c: c + "_el" if c != "ip" else c)

print("Joining on IP...")
df_merged = df_cl.merge(df_el_expanded, on="ip", how="inner")
print(f"  Rows after inner join: {len(df_merged)}")

df_merged = df_merged.drop_duplicates(subset=["PeerID_el"])
print(f"  Rows after deduplication on PeerID_el: {len(df_merged)}")

print("Uploading train_data...")
DatasetDict({"train": Dataset.from_pandas(df_merged, preserve_index=False)}).push_to_hub(
    REPO_ID,
    config_name="train_data",
    commit_message="Add train_data: inner join of consensus and execution visits on IP, all Maddrs IPs considered",
)

print("Done.")