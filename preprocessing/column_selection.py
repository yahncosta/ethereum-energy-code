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


def drop_and_clean_rows(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    null_arch = df["hw_arch"].isna()
    null_cl   = df["consensus_client"].isna()
    null_el   = df["execution_client"].isna()
    arm_no_os = (df["hw_arch"] == "ARM") & df["os_token"].isna()

    df = df[~null_arch & ~null_cl & ~null_el & ~arm_no_os].reset_index(drop=True)

    print(f"  dropped (null hw_arch)          : {null_arch.sum()}")
    print(f"  dropped (null consensus_client) : {null_cl.sum()}")
    print(f"  dropped (null execution_client) : {null_el.sum()}")
    print(f"  dropped (arm without os_token)  : {arm_no_os.sum()}")
    print(f"  dropped total (unique rows)     : {before - len(df)}")
    print(f"  remaining rows                  : {len(df)}")
    print(f"  hw_arch ARM                     : {(df['hw_arch'] == 'ARM').sum()}")
    print(f"  hw_arch x86                     : {(df['hw_arch'] == 'x86').sum()}")

    caplin_invalid = (df["consensus_client"] == "caplin") & (df["execution_client"] != "erigon")
    print(f"  dropped (caplin without erigon) : {caplin_invalid.sum()}")
    df = df[~caplin_invalid].reset_index(drop=True)

    return df.drop(columns=[c for c in COLUMNS_TO_DROP if c in df.columns])