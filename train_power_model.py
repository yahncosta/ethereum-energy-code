import json

import joblib
import pandas as pd
from datasets import Dataset, DatasetDict, load_dataset
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

REPO_ID = "yhackspacher/ethereum-crawl"
SOURCE_CONFIG = "train_data"
SOURCE_SPLIT = "train"

CATEGORICAL_FEATURES = [
    "consensus_client",
    "execution_client",
    "hw_arch",
    "os_token",
    "cloud_provider",
]
NUMERICAL_FEATURES = ["attnets_num", "syncnets_num"]
TARGET = "power_node_w"

MODEL_PATH = "rf_power_model.joblib"
METRICS_PATH = "model_results.json"

N_ESTIMATORS = 500
TEST_SIZE = 0.2
RANDOM_STATE = 42


def load_training_frame() -> pd.DataFrame:
    df = load_dataset(REPO_ID, name=SOURCE_CONFIG, split=SOURCE_SPLIT).to_pandas()
    df[CATEGORICAL_FEATURES] = df[CATEGORICAL_FEATURES].fillna("unknown")
    df["attnets_num"] = df["attnets_num"].fillna(0)
    return df


def build_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES)],
        remainder="passthrough",
    )
    model = RandomForestRegressor(
        n_estimators=N_ESTIMATORS,
        oob_score=True,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    return Pipeline([("preprocess", preprocessor), ("model", model)])


def grouped_importances(pipeline: Pipeline) -> dict:
    feature_names = pipeline.named_steps["preprocess"].get_feature_names_out()
    importances = pipeline.named_steps["model"].feature_importances_
    grouped = {}
    for name, importance in zip(feature_names, importances):
        matched = next(
            (feat for feat in CATEGORICAL_FEATURES if name.split("__")[-1].startswith(f"{feat}_")),
            None,
        )
        key = matched or name.split("__")[-1]
        grouped[key] = grouped.get(key, 0.0) + float(importance)
    return dict(sorted(grouped.items(), key=lambda item: -item[1]))


def main():
    df = load_training_frame()
    features = df[CATEGORICAL_FEATURES + NUMERICAL_FEATURES]
    target = df[TARGET]

    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )

    pipeline = build_pipeline()
    pipeline.fit(x_train, y_train)

    predictions = pipeline.predict(x_test)
    metrics = {
        "n_train": len(x_train),
        "n_test": len(x_test),
        "rmse": mean_squared_error(y_test, predictions) ** 0.5,
        "mae": mean_absolute_error(y_test, predictions),
        "r2": r2_score(y_test, predictions),
        "oob_r2": pipeline.named_steps["model"].oob_score_,
        "y_test_mean": float(y_test.mean()),
        "y_test_std": float(y_test.std()),
        "feature_importances": grouped_importances(pipeline),
    }

    print(json.dumps(metrics, indent=2))

    joblib.dump(pipeline, MODEL_PATH)
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    importance_rows = [
        {"feature": feature, "importance": importance}
        for feature, importance in metrics["feature_importances"].items()
    ]
    DatasetDict({"train": Dataset.from_pandas(pd.DataFrame(importance_rows), preserve_index=False)}).push_to_hub(
        REPO_ID,
        config_name="power_model_feature_importances",
        commit_message="Add Random Forest power model feature importances",
    )


if __name__ == "__main__":
    main()