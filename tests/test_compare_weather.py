import numpy as np
import pandas as pd

from src import compare_weather as module
from src.weather import WEATHER_FEATURES


def test_scaler_fits_only_training_and_preserves_weather_category(tmp_path):
    import joblib
    category = WEATHER_FEATURES[-1]
    train = pd.DataFrame({"temperature": [0., 10., 20., 30.],
                          category: pd.Categorical([3, 61, 3, 61])})
    model = module.make_model(list(train.columns), {"max_iter": 2, "min_samples_leaf": 1}, True)
    model.fit(train, [1., 2., 3., 4.])
    transformer = model.named_steps["standardize"]
    scaler = transformer.named_transformers_["numeric"]
    assert scaler.mean_[0] == 15.
    future = train.iloc[:1].copy()
    future["temperature"] = 1000.
    transformed = transformer.transform(future)
    assert transformed[category].iloc[0] == 3
    assert str(transformed[category].dtype) == "category"
    assert scaler.mean_[0] == 15.
    path = tmp_path / "pipeline.joblib"
    joblib.dump(model, path)
    np.testing.assert_allclose(model.predict(future), joblib.load(path).predict(future))


def test_comparison_uses_same_rows_and_purges_future_targets(monkeypatch):
    times = pd.date_range("2023-12-27", "2024-01-04", freq="6h", tz="UTC")
    data = pd.DataFrame({"Date - Heure": times, "base": np.arange(len(times)),
                         "target_consumption_t_plus_24h": np.arange(len(times)) + 10})
    for feature in WEATHER_FEATURES:
        data[feature] = 3.0
    data.loc[2, WEATHER_FEATURES[0]] = np.nan
    monkeypatch.setattr(module, "prepare_training_data", lambda weather: data)
    monkeypatch.setattr(module, "load_metadata", lambda: {"features": ["base"], "hyperparameters": {}})
    fitted, predicted = [], []

    class Model:
        def __init__(self, **kwargs):
            pass

        def fit(self, x, y):
            fitted.append(x.index.tolist())
            return self

        def predict(self, x):
            predicted.append(x.index.tolist())
            return np.zeros(len(x))

    monkeypatch.setattr(module, "HistGradientBoostingRegressor", Model)
    _, report, _ = module.compare_weather(pd.DataFrame(), "2024-01-01", "2024-01-04")
    assert fitted[0] == fitted[1]
    assert predicted[0] == predicted[1]
    assert 2 not in fitted[0]
    assert (data.loc[fitted[0], "Date - Heure"] + pd.Timedelta(hours=24)).max() < pd.Timestamp("2023-12-31", tz="UTC")
    assert set(report.index) == {"sans_meteo", "avec_meteo"}
