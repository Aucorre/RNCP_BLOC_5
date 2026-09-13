"""Compare deux modèles réentraînés sur les mêmes lignes et les mêmes périodes."""
import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.retrain import load_metadata, prepare_training_data, regression_metrics
from src.weather import WEATHER_FEATURES, ORACLE_WEATHER_FEATURES, add_oracle_weather_features


def make_model(features, hyperparameters, standardize=False):
    categorical = [name for name in features if name in (WEATHER_FEATURES[-1], ORACLE_WEATHER_FEATURES[-1])]
    params = dict(hyperparameters)
    params.update(random_state=42, categorical_features=categorical)
    model = HistGradientBoostingRegressor(**params)
    if standardize:
        numeric = [name for name in features if name not in categorical]
        preprocessing = ColumnTransformer(
            [("numeric", StandardScaler(), numeric)],
            remainder="passthrough", verbose_feature_names_out=False,
        ).set_output(transform="pandas")
        model = Pipeline([("standardize", preprocessing), ("model", model)])
    return model


def compare_weather(weather, validation_start="2024-01-01", validation_end="2025-01-01", compare_scaling=False, oracle=False):
    metadata = load_metadata()
    base = [name for name in metadata["features"] if name not in WEATHER_FEATURES + ORACLE_WEATHER_FEATURES]
    enriched = base + WEATHER_FEATURES
    target = "target_consumption_t_plus_24h"
    data = prepare_training_data(weather=weather)
    required = enriched + [target]
    if oracle:
        data = add_oracle_weather_features(data, weather)
        required += ORACLE_WEATHER_FEATURES
    data = data.dropna(subset=required)
    start, end = pd.Timestamp(validation_start, tz="UTC"), pd.Timestamp(validation_end, tz="UTC")
    if start >= end:
        raise ValueError("La fin de validation doit suivre son début.")
    # Les dates de découpage portent sur la cible H+24.
    target_time = data["Date - Heure"] + pd.Timedelta(hours=24)
    train = data[(data["Date - Heure"] >= pd.Timestamp("2019-01-01", tz="UTC"))
                 & (target_time < start - pd.Timedelta(hours=24))]
    validation = data[(target_time >= start) & (target_time < end)]
    if train.empty or len(validation) < 2:
        raise ValueError("Données insuffisantes sur les périodes demandées.")
    models, rows = {}, []
    configurations = [("sans_meteo", base, False), ("avec_meteo", enriched, False)]
    if compare_scaling:
        configurations += [("sans_meteo_standardise", base, True), ("avec_meteo_standardise", enriched, True)]
    if oracle:
        configurations.append(("meteo_parfaite_jour_cible", base + ORACLE_WEATHER_FEATURES, False))
    for label, features, standardize in configurations:
        print(f"Entraînement {label} : {len(train)} lignes ; validation : {len(validation)}", flush=True)
        model = make_model(features, metadata["hyperparameters"], standardize).fit(train[features], train[target])
        rows.append({"modele": label, **regression_metrics(validation[target], model.predict(validation[features]))})
        models[label] = model
    report = pd.DataFrame(rows).set_index("modele")
    details = {"train_rows": len(train), "validation_rows": len(validation),
               "validation_target_start": str((validation["Date - Heure"] + pd.Timedelta(hours=24)).min()),
               "validation_target_end": str((validation["Date - Heure"] + pd.Timedelta(hours=24)).max()),
               "features": {label: features for label, features, _ in configurations},
               "standardized": {label: scaled for label, _, scaled in configurations},
               "hyperparameters": metadata["hyperparameters"],
               "weather_alignment": "previous_local_day"}
    details["oracle_experiment"] = oracle
    if oracle:
        details["oracle_limitation"] = "Observed weather on local date of t+24h; future information, not a deployable forecast."
    return models, report, details


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weather-csv", required=True, type=Path)
    parser.add_argument("--compare-scaling", action="store_true", help="Compare aussi les deux modèles standardisés")
    parser.add_argument("--oracle", action="store_true", help="Expérience météo observée du jour cible (information future)")
    parser.add_argument("--validation-start", default="2024-01-01")
    parser.add_argument("--validation-end", default="2025-01-01")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/weather_comparison"))
    args = parser.parse_args()
    models, report, details = compare_weather(pd.read_csv(args.weather_csv), args.validation_start, args.validation_end, args.compare_scaling, args.oracle)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report.to_csv(args.output_dir / "metrics.csv")
    details["weather_csv"] = str(args.weather_csv.resolve())
    (args.output_dir / "comparison.json").write_text(json.dumps(details, indent=2), encoding="utf-8")
    for label, model in models.items():
        joblib.dump(model, args.output_dir / f"{label}.joblib")
    print(report.round(3).to_string())
    if args.oracle:
        print("EXPÉRIENCE MÉTÉO PARFAITE : observations futures, résultat non exploitable tel quel en production.")
        for metric in ["MAE", "RMSE"]:
            baseline = report.loc["sans_meteo", metric]
            if baseline:
                gain = 100 * (baseline - report.loc["meteo_parfaite_jour_cible", metric]) / baseline
                print(f"Gain météo parfaite {metric} : {gain:+.2f} %")
    for metric in ["MAE", "RMSE"]:
        baseline = report.loc["sans_meteo", metric]
        if baseline:
            gain = 100 * (baseline - report.loc["avec_meteo", metric]) / baseline
            print(f"Gain {metric} : {gain:+.2f} % (positif = amélioration)")
    print(f"Résultats et modèles : {args.output_dir}")
    if args.compare_scaling:
        for label in ["sans_meteo", "avec_meteo"]:
            for metric in ["MAE", "RMSE"]:
                baseline = report.loc[label, metric]
                if baseline:
                    gain = 100 * (baseline - report.loc[f"{label}_standardise", metric]) / baseline
                    print(f"Gain standardisation {label}, {metric} : {gain:+.4f} %")
