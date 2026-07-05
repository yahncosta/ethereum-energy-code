from pathlib import Path

IP_RANGES_DIR = Path("./ip_ranges")

HF_REPO_ID = "yhackspacher/ethereum-energy-data"
HF_REPO_TYPE = "dataset"
CONSENSUS_DATA_FILENAME = "out_consensus.json"
EXECUTION_DATA_FILENAME = "out_execution.json"

OFFICIAL_PROVIDER_URLS: dict[str, str] = {
    "aws":    "https://ip-ranges.amazonaws.com/ip-ranges.json",
    "gcp":    "https://www.gstatic.com/ipranges/cloud.json",
    "oracle": "https://docs.oracle.com/en-us/iaas/tools/public_ip_ranges.json",
}

RIPE_PROVIDERS: dict[str, dict] = {
    "hetzner":      {"seed_asns": [24940],  "search_terms": ["hetzner"],                "name_filter": "hetzner"},
    "ovh":          {"seed_asns": [16276],  "search_terms": ["ovh"],                    "name_filter": "ovh"},
    "contabo":      {"seed_asns": [51167],  "search_terms": ["contabo"],                "name_filter": "contabo"},
    "netcup":       {"seed_asns": [197540], "search_terms": ["netcup"],                 "name_filter": "netcup"},
    "latitude":     {"seed_asns": [396356], "search_terms": ["latitude"],               "name_filter": "latitude"},
    "digitalocean": {"seed_asns": [14061],  "search_terms": ["digitalocean"],           "name_filter": "digitalocean"},
    "vultr":        {"seed_asns": [20473],  "search_terms": ["choopa"],                 "name_filter": "constant company"},
    "linode":       {"seed_asns": [63949],  "search_terms": ["linode", "akamai-linode"],"name_filter": "linode"},
    "leaseweb":     {"seed_asns": [60781],  "search_terms": ["leaseweb"],               "name_filter": "leaseweb"},
    "clouvider":    {"seed_asns": [62240],  "search_terms": ["clouvider"],              "name_filter": "clouvider"},
}

PROVIDERS: list[str] = list(OFFICIAL_PROVIDER_URLS.keys()) + ["azure"] + list(RIPE_PROVIDERS.keys())