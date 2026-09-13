"""Prédiction rétrospective avec météo observée à H+24."""
import argparse
import json
from pathlib import Path

import joblib
import pandas as pd

from src.features import build_features
from src.weather import add_oracle_weather_features


def predict_oracle(history, weather, artifact_dir):
    artifact_dir = Path(artifact_dir)
    metadata = json.loads((artifact_dir / "metadata.json").read_text(encoding="utf-8"))
    if not metadata.get("experimental_oracle"):
        raise ValueError("Un artefact météo parfaite est requis.")
    data = add_oracle_weather_features(build_features(history), weather)
    features = metadata["features"]
    if data.empty or data.iloc[[-1]][features].isna().any().any():
        raise ValueError("Historique ou météo du jour cible manquant au dernier instant.")
    current = data.iloc[[-1]]
    model = joblib.load(artifact_dir / "model.joblib")
    return {"source_timestamp": str(current["Date - Heure"].iloc[0]),
            "target_timestamp": str(current["Date - Heure"].iloc[0] + pd.Timedelta(hours=24)),
            "prediction_mw": float(model.predict(current[features])[0]),
            "model_version": metadata["version"], "experimental_oracle": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history-csv", required=True, type=Path, help="CSV séparé par ;, Date - Heure et Consommation (MW)")
    parser.add_argument("--weather-csv", required=True, type=Path)
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts/oracle_pipeline"))
    parser.add_argument("--source-time", required=True, help="Instant source ISO avec fuseau, dans la période de test")
    args = parser.parse_args()
    history = pd.read_csv(args.history_csv, sep=";", low_memory=False, na_values=["ND", "N/A", ""])
    if "Région" in history:
        history = history[history["Région"] == "Nouvelle-Aquitaine"].copy()
    timestamps = pd.to_datetime(history["Date - Heure"], utc=True, errors="coerce")
    history = history[timestamps <= pd.to_datetime(args.source_time, utc=True)]
    print(json.dumps(predict_oracle(history, pd.read_csv(args.weather_csv), args.artifact_dir), indent=2))
