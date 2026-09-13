import pandas as pd
import pytest

from src.oracle_pipeline import split_period


def test_split_purges_horizon_and_excludes_next_year():
    data = pd.DataFrame({"Date - Heure": pd.to_datetime([
        "2023-12-29T23:30Z", "2023-12-30T00:00Z", "2023-12-31T00:00Z",
        "2024-12-30T23:30Z", "2024-12-31T00:00Z"])})
    train, test = split_period(data, 2024)
    assert train.index.tolist() == [0]
    assert test.index.tolist() == [2, 3]


def test_empty_period_rejected():
    with pytest.raises(ValueError):
        split_period(pd.DataFrame({"Date - Heure": pd.to_datetime(["2020-01-01"], utc=True)}), 2025)
