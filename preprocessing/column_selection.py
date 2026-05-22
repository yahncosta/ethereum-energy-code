import pandas as pd

COLUMNS_TO_KEEP = {
    "ip":              "ip",
    "AgentVersion_cl": "AgentVersion_cl",
    "attnets_num_cl":  "attnets_num",
    "syncnets_cl":     "syncnets_num",
    "AgentVersion_el": "AgentVersion_el",
    "Protocols_cl":    "Protocols_cl",
    "Protocols_el":    "Protocols_el",
}

COLUMNS_TO_DROP = ["AgentVersion_cl", "AgentVersion_el", "Protocols_el", "Protocols_cl"]


def select_and_rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in COLUMNS_TO_KEEP if c not in df.columns]
    if missing:
        print(f"  Warning - columns not found: {missing}")
    df = df[[c for c in COLUMNS_TO_KEEP if c in df.columns]]
    return df.rename(columns=COLUMNS_TO_KEEP)


def drop_raw_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=[c for c in COLUMNS_TO_DROP if c in df.columns])