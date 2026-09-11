from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

from src.features import build_features
from src.monitoring import log_prediction
from src.monitoring import update_actual_value



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


def load_model():
    """
    Charge le modèle de prévision sauvegardé.
    """
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Modèle introuvable : {MODEL_PATH}"
        )

    return joblib.load(MODEL_PATH)


def load_metadata() -> dict:
    """
    Charge les métadonnées associées au modèle.
    """
    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"Métadonnées introuvables : {METADATA_PATH}"
        )

    with open(
        METADATA_PATH,
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def predict_consumption(
    history: pd.DataFrame,
) -> dict:
    """
    Prédit la consommation électrique à J+1 à partir
    d'un historique de consommation.

    La dernière ligne exploitable est utilisée comme instant t.
    """

    model = load_model()
    metadata = load_metadata()

    feature_names = metadata["features"]

    enriched = build_features(history)

    available_rows = enriched.dropna(
        subset=feature_names
    )

    if available_rows.empty:
        raise ValueError(
            "Historique insuffisant pour construire "
            "toutes les variables nécessaires au modèle."
        )

    current_row = available_rows.iloc[[-1]]

    X = current_row[feature_names]

    prediction = float(
        model.predict(X)[0]
    )

    timestamp_t = (
        current_row["Date - Heure"]
        .iloc[0]
    )

    target_timestamp = (
        timestamp_t
        + pd.Timedelta(hours=24)
    )

    log_prediction(
        source_timestamp=timestamp_t,
        prediction_timestamp=target_timestamp,
        prediction_mw=prediction,
        model_version=metadata.get(
            "version",
            "unknown",
        ),
        region=metadata.get(
            "region",
            "unknown",
        ),
    )

    return {
        "prediction_mw": prediction,
        "prediction_timestamp": target_timestamp,
        "source_timestamp": timestamp_t,
        "model_version": metadata.get(
            "version",
            "unknown",
        ),
        "region": metadata.get(
            "region",
            "unknown",
        ),
        "forecast_horizon": metadata.get(
            "forecast_horizon",
            "24h",
        ),
    }


if __name__ == "__main__":

    data_path = (
        PROJECT_ROOT
        / "data"
        / "raw"
        / "eco2mix-regional-cons-def.csv"
    )

    df = pd.read_csv(
        data_path,
        sep=";",
        na_values=["ND", "N/A", ""],
        low_memory=False,
    )

    df = df[
        df["Région"] == "Nouvelle-Aquitaine"
    ].copy()

    result = predict_consumption(df)

    print(
        f"Prévision J+1 : "
        f"{result['prediction_mw']:.0f} MW"
    )

    print(
        f"Instant prédit : "
        f"{result['prediction_timestamp']}"
    )