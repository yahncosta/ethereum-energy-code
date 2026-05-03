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
df_el_filtered = df_el[el_ips.apply(len) == 1].copy()
df_el_filtered["ip"] = el_ips[df_el_filtered.index].apply(lambda ips: ips[0])
print(f"  EL rows before filter: {len(df_el)}")
print(f"  EL rows after filter: {len(df_el_filtered)}")

print("Keeping only IPs that appear exactly once in each layer...")
cl_ip_counts = df_cl["ip"].value_counts()
el_ip_counts = df_el_filtered["ip"].value_counts()

clean_ips = set(cl_ip_counts[cl_ip_counts == 1].index) & set(el_ip_counts[el_ip_counts == 1].index)
print(f"  IPs with exactly one CL and one EL peer: {len(clean_ips)}")

df_cl_clean = df_cl[df_cl["ip"].isin(clean_ips)]
df_el_clean = df_el_filtered[df_el_filtered["ip"].isin(clean_ips)]

print("Renaming columns to avoid collisions...")
df_cl_clean = df_cl_clean.rename(columns=lambda c: c + "_cl" if c != "ip" else c)
df_el_clean = df_el_clean.rename(columns=lambda c: c + "_el" if c != "ip" else c)

print("Joining on IP...")
df_merged = df_cl_clean.merge(df_el_clean, on="ip", how="inner")
print(f"  Rows after inner join: {len(df_merged)}")

print("Uploading final_visits_merged...")
DatasetDict({"train": Dataset.from_pandas(df_merged, preserve_index=False)}).push_to_hub(
    REPO_ID,
    config_name="final_visits_merged",
    commit_message="Add final_visits_merged: only unambiguous 1-to-1 IP matches between layers",
)

print("Done.")