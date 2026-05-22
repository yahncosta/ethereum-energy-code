import pandas as pd


def _syncnets_count(s: str) -> int:
    if not s or s in ("0x00", "0x0000000000000000"):
        return 0
    try:
        return bin(int(s, 16)).count("1")
    except Exception:
        return 0


def parse_syncnets(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["syncnets_num"] = df["syncnets_num"].apply(lambda s: _syncnets_count(str(s)))
    return df