import numpy as np
import pandas as pd
from datasets import Dataset, DatasetDict, load_dataset
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import KFold, RandomizedSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor
import shap

REPO_ID = "yhackspacher/ethereum-crawl"
SOURCE_CONFIG = "train_data"
SOURCE_SPLIT = "train"

CATEGORICAL_FEATURES: list[str] = [
    "consensus_client",
    "execution_client",
    "hw_arch",
    "os_token",
    "cloud_provider",
]

NUMERIC_FEATURES: list[str] = [
    "attnets_num",
    "syncnets_num",
]

FEATURE_COLUMNS: list[str] = CATEGORICAL_FEATURES + NUMERIC_FEATURES

TARGET_COLUMN: str = "power_node_w"

TEST_SIZE: float = 0.2
RANDOM_STATE: int = 42
CV_FOLDS: int = 10
N_ITER_SEARCH: int = 50

XGB_PARAM_DISTRIBUTIONS: dict = {
    "max_depth": list(range(2, 7)),
    "learning_rate": [0.01, 0.02, 0.03, 0.05, 0.07, 0.1, 0.15, 0.2, 0.25, 0.3],
    "n_estimators": list(range(50, 501, 25)),
    "min_child_weight": list(range(1, 21)),
}

RF_N_ESTIMATORS: int = 500


def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for column in CATEGORICAL_FEATURES:
        df[column] = df[column].astype("category")
    return df


def split_by_combination(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    combinations = df[FEATURE_COLUMNS].drop_duplicates().reset_index(drop=True)

    train_combinations, test_combinations = train_test_split(
        combinations,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )

    merged = df.merge(
        test_combinations.assign(_is_test=True),
        on=FEATURE_COLUMNS,
        how="left",
    )
    is_test = merged["_is_test"].fillna(False).astype(bool).to_numpy()

    df_train = df.loc[~is_test].reset_index(drop=True)
    df_test = df.loc[is_test].reset_index(drop=True)

    return df_train, df_test


def tune_xgboost(df_train: pd.DataFrame) -> tuple[XGBRegressor, dict]:
    X_train = df_train[FEATURE_COLUMNS]
    y_train = df_train[TARGET_COLUMN]

    cv = KFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    search = RandomizedSearchCV(
        estimator=XGBRegressor(
            random_state=RANDOM_STATE,
            enable_categorical=True,
            tree_method="hist",
            verbosity=0,
        ),
        param_distributions=XGB_PARAM_DISTRIBUTIONS,
        n_iter=N_ITER_SEARCH,
        scoring="neg_root_mean_squared_error",
        cv=cv,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    search.fit(X_train, y_train)

    return search.best_estimator_, search.best_params_


def fit_random_forest_baseline(df_train: pd.DataFrame) -> Pipeline:
    X_train = df_train[FEATURE_COLUMNS]
    y_train = df_train[TARGET_COLUMN]

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("numeric", SimpleImputer(strategy="median"), NUMERIC_FEATURES),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=RF_N_ESTIMATORS,
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    model.fit(X_train, y_train)
    return model


def evaluate(model, df_test: pd.DataFrame) -> dict:
    X_test = df_test[FEATURE_COLUMNS]
    y_test = df_test[TARGET_COLUMN]
    y_pred = model.predict(X_test)

    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae = float(mean_absolute_error(y_test, y_pred))

    return {"rmse": rmse, "mae": mae, "predictions": y_pred}


def compute_shap_importance(model, df_test: pd.DataFrame) -> pd.DataFrame:
    X_test = df_test[FEATURE_COLUMNS]

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)

    mean_abs_shap = np.abs(shap_values).mean(axis=0)

    return (
        pd.DataFrame({"feature": FEATURE_COLUMNS, "mean_abs_shap": mean_abs_shap})
        .sort_values("mean_abs_shap", ascending=False)
        .reset_index(drop=True)
    )


def preview_config(name: str, df: pd.DataFrame):
    print(f"config: {name}")
    print(f"rows: {len(df)}")
    print(f"columns: {list(df.columns)}")
    print(df.dtypes.to_string())
    print(df.head(10).to_string(index=False))
    print()


def main():
    df = load_dataset(REPO_ID, name=SOURCE_CONFIG, split=SOURCE_SPLIT).to_pandas()
    df = encode_categoricals(df)

    df_train, df_test = split_by_combination(df)

    xgb_model, best_params = tune_xgboost(df_train)

    rf_model = fit_random_forest_baseline(df_train)

    xgb_metrics = evaluate(xgb_model, df_test)
    rf_metrics = evaluate(rf_model, df_test)

    shap_importance = compute_shap_importance(xgb_model, df_test)

    predictions_df = df_test[FEATURE_COLUMNS + [TARGET_COLUMN]].copy()
    predictions_df["predicted_power_node_w_xgb"] = xgb_metrics["predictions"]
    predictions_df["predicted_power_node_w_rf"] = rf_metrics["predictions"]

    # DatasetDict({"train": Dataset.from_pandas(predictions_df, preserve_index=False)}).push_to_hub(
    #     REPO_ID,
    #     config_name="model_test_predictions",
    #     commit_message="Add held-out test predictions for XGBoost and Random Forest baseline",
    # )

    # DatasetDict({"train": Dataset.from_pandas(shap_importance, preserve_index=False)}).push_to_hub(
    #     REPO_ID,
    #     config_name="shap_feature_importance",
    #     commit_message="Add global SHAP feature importance ranking for the tuned XGBoost model",
    # )

    preview_config("model_test_predictions", predictions_df)
    preview_config("shap_feature_importance", shap_importance)


if __name__ == "__main__":
    main()