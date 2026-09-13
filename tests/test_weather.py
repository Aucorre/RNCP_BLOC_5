import pandas as pd
import pytest

from src.weather import add_weather_features, fetch_daily_weather, WEATHER_FEATURES
from src.weather import aggregate_daily_weather
from src.weather import add_oracle_weather_features, ORACLE_WEATHER_FEATURES


def test_oracle_uses_exact_h24_local_date_across_dst():
    history = pd.DataFrame({"Date - Heure": ["2025-03-29T22:30Z", "2025-03-29T21:30Z"]})
    weather = pd.DataFrame({"date": ["2025-03-30", "2025-03-31"],
                            "temperature_2m_mean": [10, 20],
                            "apparent_temperature_mean": [8, 18], "weather_code": [3, 61]})
    result = add_oracle_weather_features(history, weather)
    assert result[ORACLE_WEATHER_FEATURES[0]].tolist() == [20, 10]
    assert str(result[ORACLE_WEATHER_FEATURES[-1]].dtype) == "category"


def test_oracle_missing_target_day_stays_missing():
    history = pd.DataFrame({"Date - Heure": ["2025-04-01T12:00Z"]})
    assert add_oracle_weather_features(history, daily())[ORACLE_WEATHER_FEATURES].isna().all().all()


def test_regional_mean_and_modal_code():
    frames = {str(i): daily() for i in range(5)}
    for i, frame in enumerate(frames.values()):
        frame["temperature_2m_mean"] = 10 + i
        frame["weather_code"] = [61 if i < 3 else 3] * 2
    result = aggregate_daily_weather(frames)
    assert result["temperature_2m_mean"].tolist() == [12, 12]
    assert result["weather_code"].tolist() == [61, 61]


def test_regional_incomplete_day_excluded():
    result = aggregate_daily_weather({"a": daily(), "b": daily().iloc[:1]})
    assert len(result) == 1


def test_regional_tie_is_deterministic():
    a, b = daily(), daily()
    a["weather_code"], b["weather_code"] = 61, 3
    assert aggregate_daily_weather({"a": a, "b": b})["weather_code"].tolist() == [3, 3]


def daily():
    return pd.DataFrame({"date": ["2025-03-29", "2025-03-30"],
                         "temperature_2m_mean": [10, 20],
                         "apparent_temperature_mean": [8, 18],
                         "weather_code": [3, 61]})


def test_previous_local_day_across_dst():
    history = pd.DataFrame({"Date - Heure": pd.to_datetime([
        "2025-03-30T00:00Z", "2025-03-30T21:30Z", "2025-03-30T22:00Z"])})
    result = add_weather_features(history, daily())
    assert result[WEATHER_FEATURES[0]].tolist() == [10, 10, 20]
    assert str(result[WEATHER_FEATURES[-1]].dtype) == "category"


def test_missing_day_is_not_filled_from_another_day():
    history = pd.DataFrame({"Date - Heure": ["2025-04-02T12:00Z"]})
    assert add_weather_features(history, daily())[WEATHER_FEATURES].isna().all().all()


def test_duplicates_rejected():
    with pytest.raises(ValueError, match="uniques"):
        add_weather_features(pd.DataFrame(), pd.concat([daily(), daily()]))


def test_download_parameters_and_response(monkeypatch):
    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"daily": daily().rename(columns={"date": "time"}).to_dict("list")}

    def get(url, params, timeout):
        assert params["timezone"] == "Europe/Paris"
        assert params["temperature_unit"] == "celsius"
        assert timeout > 0
        return Response()

    monkeypatch.setattr("src.weather.requests.get", get)
    assert len(fetch_daily_weather("2025-03-29", "2025-03-30")) == 2
