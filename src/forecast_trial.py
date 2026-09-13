"""Essai ICON : météo prévue à 48 h, consommation à H+24."""
import argparse
import json
from pathlib import Path
import joblib
import pandas as pd
import requests
from sklearn.ensemble import HistGradientBoostingRegressor
from src.retrain import load_metadata, regression_metrics
from src.weather import ORACLE_WEATHER_FEATURES, WMO_CODES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/forecast_trial'
CACHE = ROOT / 'data/weather/icon_previous_day2'
VARIABLES = ['temperature_2m', 'apparent_temperature', 'weather_code']
FEATURES = ['forecast_' + v for v in VARIABLES]


def download():
    CACHE.mkdir(parents=True, exist_ok=True)
    for year in [2024, 2025]:
        path = CACHE / f'{year}.json'
        if path.exists():
            continue
        params = {'latitude':'44.84,45.83,46.16,43.49,43.30',
                  'longitude':'-0.58,1.26,-1.15,-1.47,-0.37',
                  'start_date':f'{year}-01-01', 'end_date':f'{year}-12-31',
                  'hourly':','.join(v+'_previous_day2' for v in VARIABLES),
                  'models':'icon_global', 'timezone':'UTC'}
        print(f'Téléchargement ICON {year}', flush=True)
        r = requests.get('https://previous-runs-api.open-meteo.com/v1/forecast', params=params, timeout=60)
        r.raise_for_status()
        payload = r.json()
        if not isinstance(payload, list) or len(payload) != 5:
            raise ValueError('Cinq réponses météo attendues.')
        path.write_text(json.dumps(payload), encoding='utf-8')
        (CACHE / f'{year}_request.json').write_text(json.dumps(params, indent=2), encoding='utf-8')


def regional():
    frames = []
    for year in [2024, 2025]:
        for city, item in enumerate(json.loads((CACHE/f'{year}.json').read_text())):
            frame = pd.DataFrame(item['hourly']).rename(columns={'time':'valid_time', **{
                v+'_previous_day2': f for v,f in zip(VARIABLES,FEATURES)}})
            frame['city'] = city
            frames.append(frame)
    data = pd.concat(frames, ignore_index=True)
    data['valid_time'] = pd.to_datetime(data['valid_time'], utc=True)
    data = data.dropna(subset=FEATURES)
    complete = data.groupby('valid_time').city.transform('nunique') == 5
    return data[complete].groupby('valid_time').agg({FEATURES[0]:'mean', FEATURES[1]:'mean',
                                                   FEATURES[2]:lambda s:s.mode().iloc[0]})


def join_forecast(data, weather):
    data = data.copy()
    # À :30, utiliser l'heure inférieure ; aucune interpolation depuis un run plus récent.
    valid = (data['Date - Heure'] + pd.Timedelta(hours=24)).dt.floor('h')
    for feature in FEATURES:
        data[feature] = valid.map(weather[feature])
    data[FEATURES[-1]] = pd.Categorical(data[FEATURES[-1]], categories=sorted(WMO_CODES))
    return data


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    weather = regional()
    weather.to_csv(OUT/'weather_coverage.csv')
    original = load_metadata()
    base = original['features']
    data = pd.read_parquet(ROOT/'artifacts/oracle_pipeline/dataset.parquet')
    data = join_forecast(data, weather).dropna(subset=base+FEATURES+ORACLE_WEATHER_FEATURES)
    target = 'target_consumption_t_plus_24h'
    target_time = data['Date - Heure'] + pd.Timedelta(hours=24)
    # Choix fixé avant mesure : entraînement 2024, test 2025, purge 24 h.
    train = data[target_time < pd.Timestamp('2024-12-31', tz='UTC')]
    test = data[(target_time >= pd.Timestamp('2025-01-01', tz='UTC')) & (target_time < pd.Timestamp('2026-01-01', tz='UTC'))]
    if len(train)<1000 or len(test)<1000:
        raise ValueError('Couverture insuffisante pour cette comparaison.')
    predictions = test[['Date - Heure',target]].copy()
    rows=[]
    for label, features in [('sans_meteo',base),('meteo_prevue',base+FEATURES),('oracle',base+ORACLE_WEATHER_FEATURES)]:
        print(f'{label}: train={len(train)}, test={len(test)}',flush=True)
        params=dict(original['hyperparameters'])
        params.update(random_state=42,categorical_features=[f for f in features if f in [FEATURES[-1],ORACLE_WEATHER_FEATURES[-1]]])
        model=HistGradientBoostingRegressor(**params).fit(train[features],train[target])
        predictions[label]=model.predict(test[features])
        rows.append({'model':label,**regression_metrics(test[target],predictions[label])})
        joblib.dump(model, OUT/f'{label}.joblib')
    pd.DataFrame(rows).to_csv(OUT/'metrics.csv',index=False)
    predictions.to_csv(OUT/'predictions.csv',index=False)
    metadata={'weather_model':'icon_global','offset':'previous_day2',
              'availability_assumption':'48h nominal lead; 24h margin before source time. Actual publication timestamps not supplied by this API.',
              'alignment':'floor(target H+24 to UTC hour); no daily averaging',
              'coverage_first':str(weather.index.min()),'coverage_last':str(weather.index.max()),
              'train_rows':len(train),'test_rows':len(test),
              'train_first':str(train['Date - Heure'].min()),'train_last':str(train['Date - Heure'].max()),
              'test_first':str(test['Date - Heure'].min()),'test_last':str(test['Date - Heure'].max()),
              'features':base+FEATURES,'hyperparameters':original['hyperparameters'],
              'note':'Fixed model; no tuning on 2025. Oracle daily vs forecast hourly: comparison also changes granularity.',
              'metrics':rows}
    (OUT/'metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    print(pd.DataFrame(rows).to_string(index=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--download',action='store_true')
    args=parser.parse_args()
    if args.download: download()
    else: run()
