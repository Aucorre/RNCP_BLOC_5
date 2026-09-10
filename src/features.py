from __future__ import annotations

import numpy as np
import pandas as pd


TIMESTAMP_COL = "Date - Heure"
CONSUMPTION_COL = "Consommation (MW)"


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construit les variables utilisées par le modèle de prévision J+1.

    Le DataFrame doit contenir au minimum :
    - Date - Heure
    - Consommation (MW)

    La fonction suppose que les données sont disponibles jusqu'à l'instant t
    et ne construit aucune variable à partir du futur.
    """

    required_columns = {
        TIMESTAMP_COL,
        CONSUMPTION_COL,
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Colonnes manquantes : {sorted(missing_columns)}"
        )

    data = df.copy()

    data[TIMESTAMP_COL] = pd.to_datetime(
        data[TIMESTAMP_COL],
        utc=True,
        errors="coerce",
    )

    data = (
        data
        .dropna(subset=[TIMESTAMP_COL, CONSUMPTION_COL])
        .sort_values(TIMESTAMP_COL)
        .drop_duplicates(
            subset=[TIMESTAMP_COL],
            keep="last",
        )
        .reset_index(drop=True)
    )

    consumption_by_time = (
        data
        .set_index(TIMESTAMP_COL)[CONSUMPTION_COL]
    )

    lags = {
        "30min": pd.Timedelta(minutes=30),
        "1h": pd.Timedelta(hours=1),
        "3h": pd.Timedelta(hours=3),
        "6h": pd.Timedelta(hours=6),
        "24h": pd.Timedelta(hours=24),
        "48h": pd.Timedelta(hours=48),
        "7d": pd.Timedelta(days=7),
    }

    for name, delta in lags.items():
        data[f"consumption_lag_{name}"] = (
            consumption_by_time
            .reindex(data[TIMESTAMP_COL] - delta)
            .to_numpy()
        )

    data["consumption_t"] = data[CONSUMPTION_COL]

    data["consumption_roll_mean_48"] = (
        data[CONSUMPTION_COL]
        .shift(1)
        .rolling(window=48)
        .mean()
    )

    data["consumption_roll_mean_336"] = (
        data[CONSUMPTION_COL]
        .shift(1)
        .rolling(window=336)
        .mean()
    )

    data["consumption_roll_std_48"] = (
        data[CONSUMPTION_COL]
        .shift(1)
        .rolling(window=48)
        .std()
    )

    data["consumption_roll_std_336"] = (
        data[CONSUMPTION_COL]
        .shift(1)
        .rolling(window=336)
        .std()
    )

    data["consumption_diff_1"] = (
        data["consumption_t"]
        - data["consumption_lag_30min"]
    )

    data["consumption_diff_24h"] = (
        data["consumption_t"]
        - data["consumption_lag_24h"]
    )

    local_dt = (
        data[TIMESTAMP_COL]
        .dt.tz_convert("Europe/Paris")
    )

    data["hour"] = local_dt.dt.hour
    data["minute"] = local_dt.dt.minute
    data["day_of_week"] = local_dt.dt.dayofweek
    data["month"] = local_dt.dt.month
    data["day_of_year"] = local_dt.dt.dayofyear
    data["is_weekend"] = (
        local_dt.dt.dayofweek >= 5
    ).astype(int)

    data["half_hour_slot"] = (
        data["hour"] * 2
        + data["minute"] // 30
    )

    data["hour_sin"] = np.sin(
        2 * np.pi * data["half_hour_slot"] / 48
    )

    data["hour_cos"] = np.cos(
        2 * np.pi * data["half_hour_slot"] / 48
    )

    data["dow_sin"] = np.sin(
        2 * np.pi * data["day_of_week"] / 7
    )

    data["dow_cos"] = np.cos(
        2 * np.pi * data["day_of_week"] / 7
    )

    data["month_sin"] = np.sin(
        2 * np.pi * data["month"] / 12
    )

    data["month_cos"] = np.cos(
        2 * np.pi * data["month"] / 12
    )

    return data