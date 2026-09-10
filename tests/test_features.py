import pandas as pd

from src.features import build_features


def make_history(n_rows=400):
    dates = pd.date_range(
        start="2025-01-01 00:00:00",
        periods=n_rows,
        freq="30min",
        tz="UTC",
    )

    return pd.DataFrame({
        "Date - Heure": dates,
        "Consommation (MW)": range(1000, 1000 + n_rows),
    })


def test_build_features_creates_expected_columns():
    df = make_history()

    result = build_features(df)

    expected_columns = [
        "consumption_t",
        "consumption_lag_30min",
        "consumption_lag_1h",
        "consumption_lag_24h",
        "consumption_lag_7d",
        "consumption_roll_mean_48",
        "consumption_roll_mean_336",
        "hour",
        "day_of_week",
        "month",
        "hour_sin",
        "hour_cos",
    ]

    for col in expected_columns:
        assert col in result.columns


def test_build_features_keeps_chronological_order():
    df = make_history()

    df = df.sample(
        frac=1,
        random_state=42
    ).reset_index(drop=True)

    result = build_features(df)

    assert result["Date - Heure"].is_monotonic_increasing


def test_lag_30min_is_correct():
    df = make_history()

    result = build_features(df)

    row = result.iloc[1]

    assert (
        row["consumption_lag_30min"]
        == result.iloc[0]["consumption_t"]
    )


def test_lag_24h_is_correct():
    df = make_history()

    result = build_features(df)

    row = result.iloc[48]

    assert (
        row["consumption_lag_24h"]
        == result.iloc[0]["consumption_t"]
    )


def test_missing_required_column_raises_error():
    df = pd.DataFrame({
        "Date - Heure": pd.date_range(
            "2025-01-01",
            periods=10,
            freq="30min",
            tz="UTC",
        )
    })

    try:
        build_features(df)
        assert False, "Une ValueError était attendue"

    except ValueError:
        assert True