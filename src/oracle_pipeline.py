"""Chaîne reproductible H+24 avec météo parfaite, validation 2024 et test 2025."""
import argparse
import json
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd

from src.compare_weather import make_model
from src.retrain import PROJECT_ROOT, load_metadata, prepare_training_data, regression_metrics
from src.weather import WEATHER_FEATURES, ORACLE_WEATHER_FEATURES, add_oracle_weather_features


def split_period(data, year):
    start = pd.Timestamp(f"{year}-01-01", tz="UTC")
    end = pd.Timestamp(f"{year + 1}-01-01", tz="UTC")
    target = data["Date - Heure"] + pd.Timedelta(hours=24)
    train = data[target < start - pd.Timedelta(hours=24)].copy()
    evaluation = data[(target >= start) & (target < end)].copy()
    if train.empty or len(evaluation) < 2:
        raise ValueError(f"Données insuffisantes pour {year}.")
    return train, evaluation


def run_pipeline(weather_csv, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    original = load_metadata()
    base = [f for f in original["features"] if f not in WEATHER_FEATURES + ORACLE_WEATHER_FEATURES]
    features = base + ORACLE_WEATHER_FEATURES
    weather = pd.read_csv(weather_csv)
    data = add_oracle_weather_features(prepare_training_data(), weather)
    target = "target_consumption_t_plus_24h"
    data = data[data["Date - Heure"] >= pd.Timestamp("2019-01-01", tz="UTC")]
    data = data.dropna(subset=features + [target]).copy()
    data[["Date - Heure"] + features + [target]].to_parquet(output_dir / "dataset.parquet", index=False)
    rows, periods = [], {}
    final_model = None
    for year in [2024, 2025]:
        train, evaluation = split_period(data, year)
        periods[str(year)] = {"train_rows": len(train), "evaluation_rows": len(evaluation),
                              "train_source_end": str(train["Date - Heure"].max()),
                              "evaluation_target_start": str((evaluation["Date - Heure"] + pd.Timedelta(hours=24)).min()),
                              "evaluation_target_end": str((evaluation["Date - Heure"] + pd.Timedelta(hours=24)).max())}
        predictions = pd.DataFrame({"source_timestamp": evaluation["Date - Heure"],
                                    "target_timestamp": evaluation["Date - Heure"] + pd.Timedelta(hours=24),
                                    "actual_mw": evaluation[target],
                                    "baseline": evaluation["consumption_t"]})
        rows.append({"year": year, "model": "baseline", **regression_metrics(evaluation[target], predictions["baseline"])})
        for label, columns in [("sans_meteo", base), ("meteo_parfaite", features)]:
            print(f"Entraînement {label}, évaluation {year}", flush=True)
            model = make_model(columns, original["hyperparameters"]).fit(train[columns], train[target])
            predictions[label] = model.predict(evaluation[columns])
            rows.append({"year": year, "model": label, **regression_metrics(evaluation[target], predictions[label])})
            if year == 2025 and label == "meteo_parfaite":
                final_model = model
        predictions.to_csv(output_dir / f"predictions_{year}.csv", index=False)
    metrics = pd.DataFrame(rows)
    metrics.to_csv(output_dir / "metrics.csv", index=False)
    metadata = {"model_name": "HistGradientBoostingRegressor", "version": "2.0.0-oracle",
                "region": original["region"], "forecast_horizon": "24h", "target": target,
                "features": features, "hyperparameters": original["hyperparameters"],
                "weather_alignment": "observed_target_local_day", "experimental_oracle": True,
                "limitation": "Météo future observée requise : simulation rétrospective, pas une prévision opérationnelle.",
                "weather_csv": str(Path(weather_csv).resolve()), "periods": periods,
                "selection": "Variables et hyperparamètres conservés ; aucun réglage sur le test 2025.",
                "metrics": rows}
    joblib.dump(final_model, output_dir / "model.joblib")
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    # Vérification d'une prédiction depuis l'artefact sauvegardé.
    restored = joblib.load(output_dir / "model.joblib")
    example = evaluation.iloc[[-1]]
    sample = {"source_timestamp": str(example["Date - Heure"].iloc[0]),
              "target_timestamp": str(example["Date - Heure"].iloc[0] + pd.Timedelta(hours=24)),
              "prediction_mw": float(restored.predict(example[features])[0]),
              "actual_mw": float(example[target].iloc[0]), "experimental_oracle": True}
    (output_dir / "prediction_example.json").write_text(json.dumps(sample, indent=2), encoding="utf-8")
    mlflow.set_tracking_uri(f"sqlite:///{PROJECT_ROOT / 'mlflow.db'}")
    mlflow.set_experiment("electricity_consumption_j1_oracle")
    with mlflow.start_run(run_name="complete_oracle_pipeline") as run:
        mlflow.set_tags({"experimental_oracle": "true", "weather_alignment": "observed_target_local_day"})
        mlflow.log_params(original["hyperparameters"])
        for row in rows:
            mlflow.log_metrics({f"{row['year']}_{row['model']}_{key}": row[key] for key in ["MAE", "RMSE", "R2"]})
        for name in ["metadata.json", "metrics.csv", "predictions_2024.csv", "predictions_2025.csv", "prediction_example.json"]:
            mlflow.log_artifact(str(output_dir / name))
        mlflow.sklearn.log_model(final_model, name="model", registered_model_name="electricity-consumption-j1-oracle",
                                 serialization_format="cloudpickle")
        (output_dir / "mlflow_run_id.txt").write_text(run.info.run_id, encoding="utf-8")
    print(metrics.round(3).to_string(index=False))
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weather-csv", type=Path, default=PROJECT_ROOT / "data/weather/regional_daily.csv")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "artifacts/oracle_pipeline")
    args = parser.parse_args()
    run_pipeline(args.weather_csv, args.output_dir)
