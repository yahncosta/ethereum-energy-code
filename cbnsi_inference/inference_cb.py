import pandas as pd


def infer_cbnsi_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["power_node_w_source"] = None

    bare_metal_measured = df["cloud_provider"].isna() & df["ccri_measured"]
    df.loc[bare_metal_measured, "power_node_w_source"] = "ccri_formula"

    cloud_estimated = df["cloud_provider"].notna() & df["power_node_w"].notna()
    df.loc[cloud_estimated, "power_node_w_source"] = "pankovska_ccf"

    if "power_node_pue_adjusted_w" not in df.columns:
        df["power_node_pue_adjusted_w"] = df["power_node_w"] * df["pue_factor"]

    return df