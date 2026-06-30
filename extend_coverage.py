import joblib
import pandas as pd
from datasets import Dataset, DatasetDict, load_dataset

from preprocessing.client_parsing import parse_clients_and_arch
from preprocessing.cloud_classification import assign_cloud_provider
from preprocessing.column_selection import COLUMNS_TO_KEEP
from preprocessing.syncnets_parsing import parse_syncnets

REPO_ID = "yhackspacher/ethereum-crawl"
MERGED_CONFIG = "final_visits_merged"
LABELLED_CONFIG = "train_data"
SOURCE_SPLIT = "train"

CATEGORICAL_FEATURES = [
    "consensus_client",
    "execution_client",
    "hw_arch",
    "os_token",
    "cloud_provider",
]
NUMERICAL_FEATURES = ["attnets_num", "syncnets_num"]

MODEL_PATH = "rf_power_model.joblib"


def build_unfiltered_frame() -> pd.DataFrame:
    df = load_dataset(REPO_ID, name=MERGED_CONFIG, split=SOURCE_SPLIT).to_pandas()
    df = df[[c for c in COLUMNS_TO_KEEP if c in df.columns]].rename(columns=COLUMNS_TO_KEEP)
    df = parse_syncnets(df)
    df = parse_clients_and_arch(df)
    df = assign_cloud_provider(df)
    return df


def split_recoverable_and_invalid(df: pd.DataFrame):
    missing_required = (
        df["hw_arch"].isna()
        | df["consensus_client"].isna()
        | df["execution_client"].isna()
        | df["os_token"].isna()
    )
    caplin_invalid = (df["consensus_client"] == "caplin") & (df["execution_client"] != "erigon")

    recoverable = df[missing_required & ~caplin_invalid].copy()
    invalid = df[caplin_invalid & ~missing_required].copy()
    return recoverable, invalid


def main():
    pipeline = joblib.load(MODEL_PATH)

    df_unfiltered = build_unfiltered_frame()
    recoverable, invalid = split_recoverable_and_invalid(df_unfiltered)

    recoverable[CATEGORICAL_FEATURES] = recoverable[CATEGORICAL_FEATURES].fillna("unknown")
    recoverable["attnets_num"] = recoverable["attnets_num"].fillna(0)

    recoverable["power_node_w"] = pipeline.predict(recoverable[CATEGORICAL_FEATURES + NUMERICAL_FEATURES])
    recoverable["power_source"] = "model_estimate"

    labelled = load_dataset(REPO_ID, name=LABELLED_CONFIG, split=SOURCE_SPLIT).to_pandas()
    labelled["power_source"] = "rule_based"

    output_columns = CATEGORICAL_FEATURES + NUMERICAL_FEATURES + ["power_node_w", "power_source"]
    extended = pd.concat(
        [labelled[output_columns], recoverable[output_columns]],
        ignore_index=True,
    )

    print(f"rule_based rows        : {len(labelled)}")
    print(f"model_estimate rows     : {len(recoverable)}")
    print(f"unrecoverable rows      : {len(invalid)}")
    print(f"total matched peers     : {len(df_unfiltered)}")
    print(f"coverage after extension: {len(extended)} / {len(df_unfiltered)}")

    DatasetDict({"train": Dataset.from_pandas(extended, preserve_index=False)}).push_to_hub(
        REPO_ID,
        config_name="power_estimates_extended",
        commit_message="Add power_estimates_extended: rule-based labels plus model coverage for incomplete-feature peers",
    )


if __name__ == "__main__":
    main()