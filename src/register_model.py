from __future__ import annotations

import json
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn


PROJECT_ROOT = Path(__file__).resolve().parent.parent

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

MODEL_PATH = (
    ARTIFACTS_DIR
    / "electricity_consumption_hgb_j1.joblib"
)

METADATA_PATH = (
    ARTIFACTS_DIR
    / "electricity_consumption_hgb_j1_metadata.json"
)


def register_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Modèle introuvable : {MODEL_PATH}"
        )

    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"Métadonnées introuvables : {METADATA_PATH}"
        )

    model = joblib.load(MODEL_PATH)

    with open(
        METADATA_PATH,
        "r",
        encoding="utf-8",
    ) as f:
        metadata = json.load(f)

    # Base SQLite locale pour conserver les runs MLflow
    mlflow.set_tracking_uri(
        f"sqlite:///{PROJECT_ROOT / 'mlflow.db'}"
    )

    mlflow.set_experiment(
        "electricity_consumption_j1"
    )

    with mlflow.start_run(
        run_name="hgb_j1_final"
    ):

        # Informations générales
        mlflow.set_tags({
            "region": metadata["region"],
            "forecast_horizon": metadata["forecast_horizon"],
            "model_version": metadata["version"],
            "model_type": metadata["model_name"],
        })

        # Hyperparamètres
        mlflow.log_params(
            metadata["hyperparameters"]
        )

        # Métriques finales
        mlflow.log_metrics({
            "test_mae": metadata["test_metrics"]["MAE"],
            "test_rmse": metadata["test_metrics"]["RMSE"],
            "test_r2": metadata["test_metrics"]["R2"],

            "baseline_mae":
                metadata["baseline_test_metrics"]["MAE"],

            "baseline_rmse":
                metadata["baseline_test_metrics"]["RMSE"],

            "baseline_r2":
                metadata["baseline_test_metrics"]["R2"],
        })

        # Variables utilisées
        mlflow.log_dict(
            {
                "features": metadata["features"]
            },
            "features.json",
        )

        # Métadonnées complètes
        mlflow.log_dict(
            metadata,
            "metadata.json",
        )

        # Modèle sklearn
        logged_model = mlflow.sklearn.log_model(
            sk_model=model,
            name="model",
            registered_model_name="electricity-consumption-j1",
        )

        print(
            "Modèle et métadonnées enregistrés dans MLflow."
        )


if __name__ == "__main__":
    register_model()