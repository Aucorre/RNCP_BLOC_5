"""Rapport visuel du test 2025 avec météo parfaite."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def main():
    folder = Path(__file__).resolve().parent.parent / "artifacts/oracle_pipeline"
    data = pd.read_csv(folder / "predictions_2025.csv")
    data["target_timestamp"] = pd.to_datetime(data["target_timestamp"], utc=True).dt.tz_convert("Europe/Paris")
    data = data.sort_values("target_timestamp").set_index("target_timestamp")
    actual, predicted = data["actual_mw"], data["meteo_parfaite"]
    mae = float((actual - predicted).abs().mean())
    mean = float(actual.mean())
    ratio = 100 * mae / mean
    summary = {"period": "test 2025", "rows": len(data), "mean_consumption_mw": mean,
               "mae_mw": mae, "mae_over_mean_percent": ratio,
               "note": "MAE / consommation moyenne ; ce ratio n'est pas la MAPE. Météo future observée."}
    (folder / "error_scale.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(2, 1, figsize=(15, 9), constrained_layout=True)
    daily = data[["actual_mw", "meteo_parfaite"]].resample("D").mean()
    # Semaine fixe, indépendante des erreurs pour éviter de choisir la meilleure.
    week = data.loc["2025-01-13":"2025-01-19"]
    for ax, frame, title in [(axes[0], daily, "Année de test — moyennes journalières"),
                              (axes[1], week, "Zoom du 13 au 19 janvier — pas de 30 minutes (semaine fixée à l'avance)")]:
        ax.plot(frame.index, frame["actual_mw"], label="Consommation réelle", color="#193b57", linewidth=1.7)
        ax.plot(frame.index, frame["meteo_parfaite"], label="Prédiction avec météo parfaite", color="#e77827", linewidth=1.4, alpha=.9)
        ax.set_title(title, loc="left")
        ax.set_ylabel("Consommation (MW)")
        ax.grid(alpha=.2)
        ax.legend(loc="upper right")
    fig.suptitle(f"Consommation réelle et prédite — Nouvelle-Aquitaine, test 2025\n"
                 f"MAE : {mae:,.1f} MW | Consommation moyenne : {mean:,.1f} MW | Ratio : {ratio:.2f} %\n"
                 "Expérience rétrospective : météo du jour cible connue, pas une prévision opérationnelle", fontsize=14)
    fig.savefig(folder / "prediction_vs_reelle.png", dpi=180)
    fig.savefig(folder / "prediction_vs_reelle.pdf")
    plt.close(fig)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
