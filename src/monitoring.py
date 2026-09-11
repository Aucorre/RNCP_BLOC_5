from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

MONITORING_DIR = PROJECT_ROOT / "data" / "monitoring"
MONITORING_DIR.mkdir(parents=True, exist_ok=True)

PREDICTIONS_PATH = (
    MONITORING_DIR
    / "predictions_history.csv"
)


def log_prediction(
    source_timestamp,
    prediction_timestamp,
    prediction_mw,
    model_version,
    region,
):
    """
    Enregistre une prédiction dans l'historique.
    """

    row = pd.DataFrame([{
        "logged_at": datetime.now(timezone.utc),
        "source_timestamp": source_timestamp,
        "prediction_timestamp": prediction_timestamp,
        "prediction_mw": prediction_mw,
        "actual_mw": None,
        "model_version": model_version,
        "region": region,
    }])

    if PREDICTIONS_PATH.exists():
        row.to_csv(
            PREDICTIONS_PATH,
            mode="a",
            header=False,
            index=False,
        )
    else:
        row.to_csv(
            PREDICTIONS_PATH,
            index=False,
        )
        
        
def update_actual_value(
    prediction_timestamp,
    actual_mw,
):
    """
    Ajoute la consommation réelle lorsqu'elle devient disponible.
    """

    if not PREDICTIONS_PATH.exists():
        raise FileNotFoundError(
            "Aucun historique de prédictions disponible."
        )

    df = pd.read_csv(
        PREDICTIONS_PATH,
        parse_dates=[
            "logged_at",
            "source_timestamp",
            "prediction_timestamp",
        ],
    )

    prediction_timestamp = pd.to_datetime(
        prediction_timestamp,
        utc=True,
    )

    mask = (
        df["prediction_timestamp"]
        == prediction_timestamp
    )

    if not mask.any():
        raise ValueError(
            "Aucune prédiction trouvée pour ce timestamp."
        )

    df.loc[
        mask,
        "actual_mw"
    ] = actual_mw

    df.to_csv(
        PREDICTIONS_PATH,
        index=False,
    )
    
def compute_monitoring_metrics(
    last_n=500,
):
    """
    Calcule les performances sur les dernières prédictions
    dont la valeur réelle est connue.
    """

    if not PREDICTIONS_PATH.exists():
        raise FileNotFoundError(
            "Aucun historique de prédictions disponible."
        )

    df = pd.read_csv(
        PREDICTIONS_PATH,
        parse_dates=[
            "logged_at",
            "source_timestamp",
            "prediction_timestamp",
        ],
    )

    evaluated = (
        df
        .dropna(
            subset=[
                "prediction_mw",
                "actual_mw",
            ]
        )
        .tail(last_n)
    )

    if len(evaluated) < 2:
        raise ValueError(
            "Pas assez de prédictions évaluées."
        )

    y_true = evaluated["actual_mw"]
    y_pred = evaluated["prediction_mw"]

    metrics = {
        "n_predictions": len(evaluated),
        "MAE": mean_absolute_error(
            y_true,
            y_pred,
        ),
        "RMSE": mean_squared_error(
            y_true,
            y_pred,
        ) ** 0.5,
        "R2": r2_score(
            y_true,
            y_pred,
        ),
    }

    return metrics


def check_performance_alert(
    reference_mae,
    tolerance_pct=20,
    last_n=500,
):
    """
    Compare la MAE récente à la MAE de référence.
    """

    metrics = compute_monitoring_metrics(
        last_n=last_n
    )

    threshold = (
        reference_mae
        * (1 + tolerance_pct / 100)
    )

    alert = (
        metrics["MAE"] > threshold
    )

    return {
        "alert": alert,
        "current_mae": metrics["MAE"],
        "reference_mae": reference_mae,
        "threshold_mae": threshold,
        "n_predictions": metrics[
            "n_predictions"
        ],
    }