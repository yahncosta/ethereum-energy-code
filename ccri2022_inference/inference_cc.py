import pandas as pd

from ccri2022_inference.constants_cc import CCRI_CL_MARGINAL_W, CCRI_EL_MARGINAL_W


def infer_ccri_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["power_cl_marginal_w"] = df["consensus_client"].map(CCRI_CL_MARGINAL_W).astype(float)
    df["power_el_marginal_w"] = df["execution_client"].map(CCRI_EL_MARGINAL_W).astype(float)

    df["ccri_measured"] = df["power_cl_marginal_w"].notna() & df["power_el_marginal_w"].notna()

    return df