import pandas as pd

from src.predict import predict_consumption


def make_history(n_rows=400):
    dates = pd.date_range(
        start="2025-01-01 00:00:00",
        periods=n_rows,
        freq="30min",
        tz="UTC",
    )

    consumption = [
        5000 + (i % 48) * 10
        for i in range(n_rows)
    ]

    return pd.DataFrame({
        "Date - Heure": dates,
        "Consommation (MW)": consumption,
    })


def test_predict_consumption_returns_expected_keys():
    df = make_history()

    result = predict_consumption(df)

    expected_keys = {
        "prediction_mw",
        "prediction_timestamp",
        "source_timestamp",
        "model_version",
        "region",
        "forecast_horizon",
    }

    assert expected_keys.issubset(result.keys())


def test_prediction_is_numeric():
    df = make_history()

    result = predict_consumption(df)

    assert isinstance(
        result["prediction_mw"],
        float,
    )


def test_prediction_timestamp_is_24h_after_source():
    df = make_history()

    result = predict_consumption(df)

    delta = (
        result["prediction_timestamp"]
        - result["source_timestamp"]
    )

    assert delta == pd.Timedelta(hours=24)


def test_prediction_region():
    df = make_history()

    result = predict_consumption(df)

    assert (
        result["region"]
        == "Nouvelle-Aquitaine"
    )