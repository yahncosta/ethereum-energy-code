from datasets import load_dataset
import json

REPO_ID = "yhackspacher/ethereum-crawl"

df_cl = load_dataset(REPO_ID, name="final_visits_consensus", split="train").to_pandas()
df_el = load_dataset(REPO_ID, name="final_visits_execution", split="train").to_pandas()

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

cl_multi = df_cl[df_cl["Maddrs"].apply(extract_ips_from_maddrs).apply(len) > 1]
el_multi = df_el[df_el["Maddrs"].apply(extract_ips_from_maddrs).apply(len) > 1]

print(f"CL peers with multiple distinct IPs: {len(cl_multi)}")
print(f"EL peers with multiple distinct IPs: {len(el_multi)}")