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

print("Filtering out EL peers with multiple distinct IPs in Maddrs...")
el_ips = df_el["Maddrs"].apply(extract_ips_from_maddrs)
df_el_filtered = df_el[el_ips.apply(len) <= 1].copy()
print(f"  EL rows before filter: {len(df_el)}")
print(f"  EL rows after filter: {len(df_el_filtered)}")

print("Extracting single IP from EL Maddrs...")
df_el_filtered["ip"] = el_ips[df_el_filtered.index].apply(lambda ips: ips[0] if ips else None)
df_el_filtered = df_el_filtered[df_el_filtered["ip"].notna()]
print(f"  EL rows with valid IP: {len(df_el_filtered)}")

print("Renaming columns to avoid collisions...")
df_cl_renamed = df_cl.rename(columns=lambda c: c + "_cl" if c != "ip" else c)
df_el_renamed = df_el_filtered.rename(columns=lambda c: c + "_el" if c != "ip" else c)

print("Joining EL ip on CL ip...")
df_merged = df_cl_renamed.merge(df_el_renamed, on="ip", how="inner")
print(f"  Rows after inner join: {len(df_merged)}")

print("Identifying EL peers that matched more than one CL peer...")
el_match_counts = df_merged.groupby("PeerID_el")["PeerID_cl"].nunique()
ambiguous_el = set(el_match_counts[el_match_counts > 1].index)
print(f"  EL peers matched to more than one CL peer: {len(ambiguous_el)}")
print(f"  Rows that will be removed: {df_merged['PeerID_el'].isin(ambiguous_el).sum()}")

df_merged = df_merged[~df_merged["PeerID_el"].isin(ambiguous_el)]
print(f"  Rows after removing ambiguous EL peers: {len(df_merged)}")

print("Uploading final_visits_merged...")
DatasetDict({"train": Dataset.from_pandas(df_merged, preserve_index=False)}).push_to_hub(
    REPO_ID,
    config_name="final_visits_merged",
    commit_message="Add final_visits_merged: EL peers matching multiple CL peers excluded entirely",
)

print("Done.")