import pandas as pd
from src.forecast_trial import join_forecast, FEATURES


def test_hourly_alignment_uses_target_floor_and_keeps_gaps():
    history = pd.DataFrame({'Date - Heure':pd.to_datetime(['2025-03-29T23:30Z','2025-03-30T00:00Z'])})
    weather = pd.DataFrame({FEATURES[0]:[12],FEATURES[1]:[10],FEATURES[2]:[3]},
                           index=pd.to_datetime(['2025-03-30T23:00Z']))
    result = join_forecast(history, weather)
    assert result.loc[0,FEATURES[0]] == 12
    assert result.loc[1,FEATURES].isna().all()
    assert str(result[FEATURES[-1]].dtype) == 'category'
