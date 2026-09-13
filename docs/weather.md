# Ajout de météo quotidienne

## Chaîne complète météo parfaite

```powershell
$env:OMP_NUM_THREADS = "4"
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\python.exe -m src.oracle_pipeline
```

Cette commande reprend le CSV météo régional existant, prépare et sauvegarde
le dataset, évalue sur 2024 puis réentraîne pour le test 2025 avec purge de 24 h.
Les variables et hyperparamètres HGB sont conservés, sans nouvelle recherche ni
sélection sur 2025. Baseline de persistance, HGB sans météo et HGB météo parfaite
sont évalués sur les mêmes lignes. Le modèle final est celui évalué sur 2025,
entraîné uniquement avant cette période ; il n'est pas réentraîné sur le test.

Sorties dans `artifacts/oracle_pipeline/` : dataset Parquet, métriques CSV,
prédictions 2024/2025 (utilisables pour analyser les erreurs), modèle Joblib,
métadonnées, exemple de prédiction après rechargement et identifiant MLflow.
Expérience MLflow : `electricity_consumption_j1_oracle` ; modèle enregistré :
`electricity-consumption-j1-oracle`. Les anciennes expériences restent consultables.

Pour rejouer une prédiction historique avec l'artefact obtenu :

```powershell
.\.venv\Scripts\python.exe -m src.predict_oracle --history-csv data/raw/eco2mix-regional-cons-def.csv --weather-csv data/weather/regional_daily.csv --source-time 2025-06-01T12:00:00Z
```

L'historique est coupé à l'instant demandé ; la météo observée du jour cible
reste nécessaire. Ces simulations sont explicitement marquées `experimental_oracle`.

## Expérience météo parfaite du jour cible

```powershell
$env:OMP_NUM_THREADS = "4"
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\python.exe -m src.compare_weather --weather-csv data/weather/regional_daily.csv --oracle --output-dir artifacts/weather_oracle_comparison
```

Compare trois HGB : sans météo, météo de la veille, météo observée du jour
contenant l'instant cible t+24h en Europe/Paris. Les trois modèles utilisent
les mêmes lignes complètes et hyperparamètres, avec validation sur 2024.
Les variables de l'expérience portent le préfixe `weather_target_day_observed_`
et remplacent celles de la veille pour ce troisième modèle. Les températures
restent des moyennes quotidiennes sur les cinq villes et le code WMO une catégorie.
Le calcul ajoute 24 heures en UTC avant de déterminer la date locale, pour
respecter l'horizon même aux changements d'heure.

Cette expérience utilise volontairement de l'information future : elle mesure
l'intérêt potentiel de la météo du jour cible, pas une performance exploitable
en production. Les résultats et le modèle expérimental sont enregistrés dans
le dossier indiqué, avec cette limite dans `comparison.json`. L'entraînement
et la prédiction opérationnels restent sur la météo de la veille. Une amélioration
devra être confirmée avec des prévisions archivées disponibles à l'instant source.

## Météo de la veille

Les trois variables sont la température moyenne à 2 m (°C), la température
ressentie moyenne (°C) et le code WMO quotidien (catégorie : ciel clair,
nuages, brouillard, pluie, neige, orage…). Source et définitions :
[Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api).

Depuis la racine du projet :

```powershell
.\.venv\Scripts\python.exe -m src.weather --regional --start 2018-12-31 --end 2025-12-31 --output data/weather/regional_daily.csv
$env:OMP_NUM_THREADS = "4"
.\.venv\Scripts\python.exe -m src.compare_weather --weather-csv data/weather/regional_daily.csv
```

Avec `--regional`, le téléchargement couvre Bordeaux, Limoges, La Rochelle,
Bayonne et Pau. Les températures sont moyennées à poids égaux. Le code WMO
retenu est le plus fréquent ; en cas d'égalité, le plus petit code est retenu
par convention, sans interprétation de gravité. Une journée est exclue si une
ville manque ou présente une valeur manquante. Les CSV par ville sont conservés
à côté du CSV régional. Il s'agit d'une approximation par cinq points, sans
pondération par population ou consommation. Aucun gain n'est garanti.
Sans `--regional`, Bordeaux reste le point par défaut ; `--latitude` et
`--longitude` permettent de le changer.

La comparaison réentraîne les modèles avec et sans météo sur les mêmes lignes
complètes à partir de 2019, avec les mêmes hyperparamètres. La validation porte
sur les cibles de 2024, avec une purge de 24 h avant son début. Les métriques
MAE, RMSE et R² s'affichent dans le terminal, ainsi que la réduction relative
des erreurs (positive = amélioration). Résultats, périodes, variables et deux
modèles sont sauvegardés dans `artifacts/weather_comparison/`. L'artefact actif
n'est pas remplacé. Cette commande ne crée pas de run MLflow.

Après avoir figé les choix sur 2024, évaluer séparément sur 2025 :

```powershell
.\.venv\Scripts\python.exe -m src.compare_weather --weather-csv data/weather/regional_daily.csv --validation-start 2025-01-01 --validation-end 2026-01-01 --output-dir artifacts/weather_test_2025
```

Pour le réentraînement opérationnel existant (validation sur les 30 derniers
jours disponibles, enregistrement du candidat dans MLflow) :

```powershell
.\.venv\Scripts\python.exe -m src.retrain --weather-csv data/weather/regional_daily.csv
```

Pour mesurer séparément l'effet de la standardisation :

```powershell
$env:OMP_NUM_THREADS = "4"
.\.venv\Scripts\python.exe -m src.compare_weather --weather-csv data/weather/regional_daily.csv --compare-scaling --output-dir artifacts/weather_scaling_comparison
```

Cette option entraîne quatre variantes : avec/sans météo, chacune avec/sans
standardisation. `StandardScaler` centre et réduit les variables numériques
avec la moyenne et l'écart-type appris uniquement sur l'entraînement. Le code
WMO reste catégoriel. Le scaler est sauvegardé avec le modèle dans une Pipeline
et réutilisé automatiquement en prédiction. Les quatre variantes utilisent les
mêmes lignes et périodes. Le réentraînement MLflow existant reste inchangé.
Les arbres HGB étant presque insensibles à l'échelle des variables, un gain
faible ou nul est attendu ; cette expérience permet de le mesurer.

`build_features(history, weather=daily_weather)` et
`predict_consumption(history, weather=daily_weather)` acceptent le même tableau
quotidien. Colonnes CSV : `date`, `temperature_2m_mean`,
`apparent_temperature_mean`, `weather_code`.

Chaque instant de consommation reçoit la météo de la veille civile en
Europe/Paris. Une journée complète ne doit pas être utilisée avant sa fin.
Les dates absentes ne sont ni interpolées ni propagées. À l'entraînement,
les lignes incomplètes sont exclues ; pour un modèle météo, la prédiction
échoue explicitement si la météo nécessaire au dernier instant manque.

Les archives sont des réanalyses reconstruites après les événements : leur
disponibilité réelle peut être retardée. Cette intégration sert à expérimenter
sur l'historique ; elle ne garantit pas la disponibilité des données de la veille
en exploitation. Pour utiliser la météo du jour cible à H+24, il faut des
prévisions archivées avec leur date d'émission, disponibles à l'instant source,
puis la même source de prévisions en exploitation. Utiliser la météo réellement
observée du lendemain donnerait une évaluation trop optimiste.

Le réentraînement crée un candidat MLflow avec ses métadonnées, sans remplacer
l'artefact actif. Il ajoute les trois variables aux variables existantes et
réserve les 30 derniers jours à la validation, avec une purge de 24 h.
Les anciennes métriques de test présentes dans les métadonnées restent celles
du modèle initial ; les métriques du candidat sont enregistrées séparément.
Avant promotion, comparer avec et sans météo sur les mêmes lignes et périodes,
puis réévaluer sur un test indépendant. Le modèle actif reste utilisable sans
météo tant qu'il n'a pas été remplacé par un modèle entraîné avec ces variables.
