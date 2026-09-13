# Premier essai avec météo prévue

Source : https://open-meteo.com/en/docs/previous-runs-api ; modèle ICON Global.
Les réponses brutes 2024 et 2025 et paramètres de requête sont conservés dans
`data/weather/icon_previous_day2/`.

Trois variables horaires : température à 2 m, température ressentie et code WMO.
Les cinq villes doivent être présentes ; températures moyennées à poids égaux,
code WMO modal (plus petit code en cas d'égalité).

L'expérience prédit la consommation à H+24 avec les champs `previous_day2`
(échéance météo nominale de 48 h). Cette marge nominale de 24 h avant l'instant
source vise à couvrir la latence de publication. L'API ne fournit pas les heures
réelles de publication : il s'agit d'une hypothèse explicite, pas d'un audit de
disponibilité run par run. Pour une preuve plus stricte, utiliser une archive
avec initialisation et publication identifiables.

Jointure en UTC sur l'heure inférieure de t+24h ; à la demi-heure, la dernière
heure est utilisée sans interpolation. Aucune moyenne sur la journée future.
Les lignes manquantes sont exclues de tous les modèles. L'entraînement utilise
la couverture disponible de 2024, le test 2025, avec purge de 24 h. Aucun tuning
sur le test. Le contrôle oracle conserve ses variables quotidiennes : sa
comparaison avec la météo prévue change aussi la granularité des variables.

```powershell
$env:OMP_NUM_THREADS = "4"
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\python.exe -m src.forecast_trial --download
.\.venv\Scripts\python.exe -m src.forecast_trial
```

Résultats, modèles et périodes exactes : `artifacts/forecast_trial/`.
Ce premier essai ne modifie pas les alias MLflow ni le modèle actif.
