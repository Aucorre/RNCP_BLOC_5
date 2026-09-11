from __future__ import annotations

import json
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd

from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

from src.features import build_features


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "eco2mix-regional-cons-def.csv"
)

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

METADATA_PATH = (
    ARTIFACTS_DIR
    / "electricity_consumption_hgb_j1_metadata.json"
)

MODEL_NAME = "electricity-consumption-j1"


def regression_metrics(y_true, y_pred):
    return {
        "MAE": mean_absolute_error(y_true, y_pred),
        "RMSE": mean_squared_error(y_true, y_pred) ** 0.5,
        "R2": r2_score(y_true, y_pred),
    }


def load_metadata():
    with open(
        METADATA_PATH,
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def prepare_training_data():
    df = pd.read_csv(
        RAW_PATH,
        sep=";",
        na_values=["ND", "N/A", ""],
        low_memory=False,
    )

    df = df[
        df["Région"] == "Nouvelle-Aquitaine"
    ].copy()

    df["Date - Heure"] = pd.to_datetime(
        df["Date - Heure"],
        utc=True,
        errors="coerce",
    )

    df = (
        df
        .dropna(
            subset=[
                "Date - Heure",
                "Consommation (MW)",
            ]
        )
        .sort_values("Date - Heure")
        .drop_duplicates(
            subset=["Date - Heure"],
            keep="last",
        )
    )

    # Features disponibles à t
    df = build_features(df)

    # Construction cible t + 24 h
    target_lookup = (
        df[
            [
                "Date - Heure",
                "Consommation (MW)",
            ]
        ]
        .copy()
    )

    target_lookup["Date - Heure"] = (
        target_lookup["Date - Heure"]
        - pd.Timedelta(hours=24)
    )

    target_lookup = target_lookup.rename(
        columns={
            "Consommation (MW)":
            "target_consumption_t_plus_24h"
        }
    )

    df = df.merge(
        target_lookup,
        on="Date - Heure",
        how="left",
    )

    return df


def retrain_model():
    metadata = load_metadata()

    features = metadata["features"]
    params = metadata["hyperparameters"]

    df = prepare_training_data()

    dataset = df[
        ["Date - Heure"]
        + features
        + ["target_consumption_t_plus_24h"]
    ].dropna().copy()

    # Exemple : les dernières 30 journées servent
    # d'évaluation du candidat
    cutoff = (
        dataset["Date - Heure"].max()
        - pd.Timedelta(days=30)
    )

    train = dataset[
        dataset["Date - Heure"] < cutoff
    ].copy()

    validation = dataset[
        dataset["Date - Heure"] >= cutoff
    ].copy()

    X_train = train[features]
    y_train = train[
        "target_consumption_t_plus_24h"
    ]

    X_val = validation[features]
    y_val = validation[
        "target_consumption_t_plus_24h"
    ]

    candidate = HistGradientBoostingRegressor(
        **params,
        random_state=42,
    )

    candidate.fit(
        X_train,
        y_train,
    )

    predictions = candidate.predict(
        X_val
    )

    metrics = regression_metrics(
        y_val,
        predictions,
    )

    return candidate, metrics, metadata


def log_candidate_to_mlflow(
    model,
    metrics,
    metadata,
):
    mlflow.set_tracking_uri(
        f"sqlite:///{PROJECT_ROOT / 'mlflow.db'}"
    )

    mlflow.set_experiment(
        "electricity_consumption_j1"
    )

    with mlflow.start_run(
        run_name="hgb_j1_retraining_candidate"
    ):

        mlflow.set_tags({
            "status": "candidate",
            "region": metadata["region"],
            "forecast_horizon":
                metadata["forecast_horizon"],
        })

        mlflow.log_params(
            metadata["hyperparameters"]
        )

        mlflow.log_metrics({
            "candidate_mae": metrics["MAE"],
            "candidate_rmse": metrics["RMSE"],
            "candidate_r2": metrics["R2"],
        })

        mlflow.sklearn.log_model(
            sk_model=model,
            name="model",
            registered_model_name=MODEL_NAME,
        )

        print("Candidat enregistré dans MLflow.")
        print(metrics)
        
        
    
if __name__ == "__main__":
    model, metrics, metadata = retrain_model()

    log_candidate_to_mlflow(
        model,
        metrics,
        metadata,
    )