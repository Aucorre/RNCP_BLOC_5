"""Sonde la couverture réelle des prévisions archivées Open-Meteo."""
import json
from pathlib import Path
import requests

OUT = Path(__file__).resolve().parents[1] / 'data/weather/forecast_probe'
OUT.mkdir(parents=True, exist_ok=True)
variables = ['temperature_2m_previous_day1', 'apparent_temperature_previous_day1', 'weather_code_previous_day1']
results = []
for model in ['meteofrance_arpege_europe', 'icon_global', 'gfs_global']:
    for date in ['2024-01-15', '2025-01-15', '2025-12-15']:
        params = {'latitude': '44.84,45.83,46.16,43.49,43.30',
                  'longitude': '-0.58,1.26,-1.15,-1.47,-0.37',
                  'start_date': date, 'end_date': date, 'hourly': ','.join(variables),
                  'models': model, 'timezone': 'UTC'}
        response = requests.get('https://previous-runs-api.open-meteo.com/v1/forecast', params=params, timeout=45)
        payload = response.json()
        (OUT / f'{model}_{date}.json').write_text(json.dumps(payload), encoding='utf-8')
        row = {'model': model, 'date': date, 'status': response.status_code, 'url': response.url}
        if response.ok:
            items = payload if isinstance(payload, list) else [payload]
            row['non_null_by_city'] = [{v: sum(x is not None for x in item['hourly'][v]) for v in variables} for item in items]
        else:
            row['error'] = payload
        results.append(row)
        print(json.dumps(row), flush=True)
(OUT / 'summary.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
