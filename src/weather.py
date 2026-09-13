"""Météo quotidienne Open-Meteo, en °C et jours civils Europe/Paris."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import requests

DAILY_COLUMNS = ["temperature_2m_mean", "apparent_temperature_mean", "weather_code"]
WEATHER_FEATURES = [f"weather_previous_day_{name}" for name in DAILY_COLUMNS]
ORACLE_WEATHER_FEATURES = [f"weather_target_day_observed_{name}" for name in DAILY_COLUMNS]
CITIES = {"bordeaux": (44.84, -0.58), "limoges": (45.83, 1.26),
          "la_rochelle": (46.16, -1.15), "bayonne": (43.49, -1.47),
          "pau": (43.30, -0.37)}
WMO_CODES = {0, 1, 2, 3, 45, 48, 51, 53, 55, 56, 57, 61, 63, 65,
             66, 67, 71, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99}


def validate_daily_weather(weather: pd.DataFrame) -> pd.DataFrame:
    required = {"date", *DAILY_COLUMNS}
    if required - set(weather.columns):
        raise ValueError(f"Colonnes météo manquantes : {sorted(required - set(weather.columns))}")
    data = weather[["date", *DAILY_COLUMNS]].copy()
    data["date"] = pd.to_datetime(data["date"], format="%Y-%m-%d", errors="raise")
    if data["date"].isna().any() or data["date"].duplicated().any():
        raise ValueError("Les dates météo doivent être renseignées et uniques.")
    for column in DAILY_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="raise")
    if not data["weather_code"].dropna().isin(WMO_CODES).all():
        raise ValueError("Code météo WMO invalide.")
    return data.sort_values("date")


def fetch_daily_weather(start: str, end: str, latitude=44.84, longitude=-0.58) -> pd.DataFrame:
    """Télécharge des réanalyses historiques (pas des prévisions disponibles à t)."""
    if pd.Timestamp(start) > pd.Timestamp(end):
        raise ValueError("La date de début doit précéder la date de fin.")
    response = requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params={"latitude": latitude, "longitude": longitude,
                "start_date": start, "end_date": end,
                "daily": ",".join(DAILY_COLUMNS), "timezone": "Europe/Paris",
                "temperature_unit": "celsius"},
        timeout=60,
    )
    response.raise_for_status()
    data = pd.DataFrame(response.json()["daily"]).rename(columns={"time": "date"})
    return validate_daily_weather(data)


def aggregate_daily_weather(city_weather: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Poids égaux ; journée incomplète exclue ; mode WMO, plus petit code si égalité."""
    if not city_weather:
        raise ValueError("Au moins une ville est nécessaire.")
    frames = [validate_daily_weather(frame).assign(city=city)
              for city, frame in city_weather.items()]
    combined = pd.concat(frames, ignore_index=True).dropna(subset=DAILY_COLUMNS)
    complete = combined.groupby("date")["city"].transform("nunique") == len(frames)
    return combined[complete].groupby("date", as_index=False).agg(
        temperature_2m_mean=("temperature_2m_mean", "mean"),
        apparent_temperature_mean=("apparent_temperature_mean", "mean"),
        weather_code=("weather_code", lambda codes: codes.mode().iloc[0]),
    )


def add_oracle_weather_features(data: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    """Expérience uniquement : météo observée du jour local contenant t + 24 h."""
    daily = validate_daily_weather(weather).set_index("date")
    result = data.copy()
    target = pd.to_datetime(result["Date - Heure"], utc=True) + pd.Timedelta(hours=24)
    day = target.dt.tz_convert("Europe/Paris").dt.tz_localize(None).dt.normalize()
    for column, feature in zip(DAILY_COLUMNS, ORACLE_WEATHER_FEATURES):
        result[feature] = day.map(daily[column])
    result[ORACLE_WEATHER_FEATURES[-1]] = pd.Categorical(
        result[ORACLE_WEATHER_FEATURES[-1]], categories=sorted(WMO_CODES))
    return result


def add_weather_features(data: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    """Joint exactement la veille locale ; aucune propagation des jours manquants."""
    daily = validate_daily_weather(weather).set_index("date")
    result = data.copy()
    local = pd.to_datetime(result["Date - Heure"], utc=True).dt.tz_convert("Europe/Paris")
    previous_day = local.dt.tz_localize(None).dt.normalize() - pd.Timedelta(days=1)
    for column, feature in zip(DAILY_COLUMNS, WEATHER_FEATURES):
        result[feature] = previous_day.map(daily[column])
    # Le code WMO est une catégorie, pas une grandeur continue.
    result[WEATHER_FEATURES[-1]] = pd.Categorical(
        result[WEATHER_FEATURES[-1]], categories=sorted(WMO_CODES)
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--latitude", type=float, default=44.84)
    parser.add_argument("--longitude", type=float, default=-0.58)
    parser.add_argument("--regional", action="store_true", help="Moyenne des cinq villes")
    parser.add_argument("--output", type=Path, default=Path("data/weather/bordeaux_daily.csv"))
    args = parser.parse_args()
    if args.regional:
        city_weather = {}
        for city, (latitude, longitude) in CITIES.items():
            print(f"Téléchargement : {city}", flush=True)
            city_weather[city] = fetch_daily_weather(args.start, args.end, latitude, longitude)
        weather = aggregate_daily_weather(city_weather)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        for city, frame in city_weather.items():
            frame.to_csv(args.output.with_name(f"{args.output.stem}_{city}.csv"), index=False)
    else:
        weather = fetch_daily_weather(args.start, args.end, args.latitude, args.longitude)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    weather.to_csv(args.output, index=False)
    print(f"{len(weather)} journées enregistrées dans {args.output}")
