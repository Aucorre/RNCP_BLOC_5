# Prévision de la consommation électrique régionale à J+1

## Présentation du projet

Ce projet a été réalisé dans le cadre du bloc 5 du titre RNCP39586  
**« Ingénieur en science des données spécialisé en infrastructure data ou en apprentissage automatique »**.

L’objectif est de construire un système de prévision de la consommation électrique à court terme pour la région **Nouvelle-Aquitaine**.

Le modèle cherche à prédire la consommation électrique **24 heures à l’avance**, à partir de données historiques de consommation et de variables temporelles construites à partir de la série.

Le projet couvre l’ensemble du cycle de vie d’un modèle de Machine Learning :

- analyse du besoin ;
- préparation des données ;
- construction et sélection des variables ;
- entraînement et comparaison de modèles ;
- optimisation des hyperparamètres ;
- évaluation sur une période future ;
- sauvegarde et réutilisation du modèle ;
- suivi des performances ;
- automatisation des tests ;
- gestion du cycle de vie et du réentraînement.

---

## Contexte

La consommation d’électricité varie fortement selon :

- l’heure de la journée ;
- le jour de la semaine ;
- la saison ;
- les habitudes de consommation ;
- les conditions extérieures ;
- les périodes de forte demande.

Pouvoir anticiper ces variations permet aux gestionnaires du réseau de mieux adapter la production à la demande.

Une prévision plus précise peut notamment contribuer à :

- limiter les déséquilibres entre production et consommation ;
- mieux anticiper les pics de demande ;
- réduire le recours à des moyens de production coûteux ;
- faciliter l’intégration de sources de production variables.

Le problème constitue également un cas d’usage intéressant de Machine Learning, car il s’agit d’une **série temporelle**, pour laquelle l’ordre chronologique des observations doit être respecté.

---

## Objectif

L’objectif retenu est de prédire :

> **la consommation électrique en Nouvelle-Aquitaine 24 heures après l’instant courant.**

Le problème est donc formulé comme une **régression sur série temporelle**.

### Périmètre retenu

- Région : **Nouvelle-Aquitaine**
- Granularité : **30 minutes**
- Horizon principal : **J+1 / H+24**
- Variable cible : consommation électrique en MW
- Période de travail : données récentes à partir de 2019
- Jeu de test final : année 2025

Une expérience complémentaire de prévision à **J+7** a également été réalisée afin d’étudier l’impact de l’allongement de l’horizon de prévision.

---

## Données

Les données utilisées proviennent du jeu de données public **éCO2mix régional**, publié par RTE / ODRÉ.

Le fichier source contient plusieurs millions d’observations de consommation et de production électrique à une granularité de 30 minutes.

Parmi les principales informations disponibles :

- région ;
- date et heure ;
- consommation électrique ;
- production thermique ;
- production nucléaire ;
- production éolienne ;
- production solaire ;
- production hydraulique ;
- bioénergies ;
- échanges physiques ;
- autres indicateurs liés au système électrique.

Pour ce projet, le modèle principal utilise principalement l’historique de consommation ainsi que des variables temporelles dérivées.

---

## Analyse exploratoire

Le premier notebook est consacré à l’analyse du jeu de données.

Les principaux points étudiés sont :

- volume des données ;
- période couverte ;
- nombre de régions ;
- fréquence temporelle ;
- types de variables ;
- taux de valeurs manquantes ;
- présence de doublons ;
- continuité temporelle ;
- évolution de la consommation ;
- saisonnalité journalière ;
- saisonnalité hebdomadaire ;
- saisonnalité annuelle.

L’analyse met notamment en évidence :

- une forte dépendance de la consommation à l’heure de la journée ;
- des profils différents entre jours ouvrés et week-ends ;
- une saisonnalité annuelle ;
- une fréquence principale de 30 minutes ;
- quelques anomalies liées notamment aux changements d’heure.

---

## Construction des variables

La préparation du dataset Machine Learning repose sur plusieurs familles de variables.

### Variables historiques

Des lags de consommation sont construits à différents horizons :

- 30 minutes ;
- 1 heure ;
- 3 heures ;
- 6 heures ;
- 24 heures ;
- 48 heures ;
- 7 jours.

### Statistiques glissantes

Des statistiques glissantes sont calculées sur différentes fenêtres :

- moyenne sur 24 heures ;
- moyenne sur 7 jours ;
- écart-type sur 24 heures ;
- écart-type sur plusieurs jours.

### Variables de tendance

Des différences entre la consommation actuelle et certaines consommations passées sont également construites.

### Variables calendaires

Les variables temporelles incluent notamment :

- heure ;
- minute ;
- jour de la semaine ;
- mois ;
- jour de l’année ;
- week-end ;
- créneau de demi-heure.

Des transformations cycliques sinus / cosinus sont utilisées afin de représenter correctement les variables périodiques.

---

## Baseline

Avant d’entraîner les modèles de Machine Learning, une baseline temporelle est définie.

Pour la prévision à J+1 :

> la consommation de demain au même créneau est supposée égale à la consommation observée aujourd’hui.

Cette baseline sert de référence afin de mesurer la valeur ajoutée réelle des modèles.

---

## Séparation temporelle

Les données ne sont pas mélangées aléatoirement.

La séparation respecte la chronologie :

- entraînement : données historiques ;
- validation : année 2024 ;
- test final : année 2025.

Le jeu de test n’est pas utilisé pour sélectionner le modèle ou ses hyperparamètres.

Lors de l’optimisation, une validation croisée temporelle est utilisée avec `TimeSeriesSplit`.

Un intervalle de sécurité est ajouté entre les périodes d’entraînement et de validation afin d’éviter que la cible future des dernières observations d’entraînement ne chevauche la période de validation.

---

## Modèles comparés

Plusieurs approches ont été comparées.

### Ridge Regression

Un modèle linéaire régularisé est utilisé comme premier modèle Machine Learning.

Il sert notamment à comparer une approche linéaire à des modèles capables de capturer des relations plus complexes.

### HistGradientBoostingRegressor

Le modèle principal retenu est un :

`HistGradientBoostingRegressor`

Ce modèle est adapté aux datasets relativement volumineux et permet de modéliser des relations non linéaires entre les variables.

---

## Sélection des variables

La sélection des variables repose sur plusieurs approches :

- analyse de corrélation ;
- analyse métier ;
- permutation importance.

La permutation importance permet d’identifier les variables dont la perturbation dégrade le plus les performances du modèle.

Le modèle initial utilise environ 27 variables.

Après sélection, seules les **10 variables les plus importantes** sont conservées.

Cette réduction permet de supprimer plus de 60 % des variables tout en conservant des performances quasiment identiques.

### Comparaison

| Configuration | MAE | RMSE | R² |
|---|---:|---:|---:|
| HGB toutes variables | ~206 MW | ~294 MW | ~0.912 |
| HGB top 10 variables | ~207 MW | ~295 MW | ~0.912 |

La perte de performance est très faible malgré une réduction importante du nombre de variables.

---

## Optimisation des hyperparamètres

Le modèle retenu est optimisé avec `RandomizedSearchCV`.

Les principaux hyperparamètres explorés sont :

- `learning_rate` ;
- `max_iter` ;
- `max_leaf_nodes` ;
- `min_samples_leaf` ;
- `l2_regularization`.

La validation utilise `TimeSeriesSplit` afin de respecter la chronologie des observations.

L’optimisation apporte un gain limité par rapport au modèle par défaut.

Ce résultat indique que les paramètres standards du HistGradientBoosting étaient déjà bien adaptés au problème.

---

## Résultats finaux

Le modèle final est évalué sur l’année **2025**, conservée comme jeu de test indépendant.

### Baseline J+1

- MAE : environ **258 MW**
- RMSE : environ **356 MW**
- R² : environ **0,885**

### HistGradientBoosting optimisé

- MAE : environ **209 MW**
- RMSE : environ **288 MW**
- R² : environ **0,925**

Le modèle réduit donc la MAE et la RMSE d’environ **19 %** par rapport à la baseline.

L’amélioration principale provient du choix du modèle et du feature engineering, davantage que de l’optimisation des hyperparamètres.

---

## Analyse des erreurs

Une analyse complémentaire est réalisée sur les périodes de forte consommation.

Les performances se dégradent sur les 10 % d’observations présentant les consommations les plus élevées.

Cela montre que le modèle reproduit correctement la dynamique générale de la série, mais reste moins précis pendant certains pics de consommation.

Cette limite constitue un axe d’amélioration possible.

Des variables météorologiques ou calendaires supplémentaires pourraient notamment améliorer la capacité du modèle à anticiper ces situations.

---

## Prévision à J+7

Une expérience complémentaire étudie un horizon de prévision à **7 jours**.

L’objectif est de comparer les performances avec le modèle principal à J+1 et d’observer l’impact de l’allongement de l’horizon.

Cette expérience n’est pas utilisée comme modèle principal du projet.

Elle permet principalement d’étudier les limites de prédictibilité à partir des seules données historiques disponibles.

---

## Sauvegarde et réutilisation du modèle

Le modèle final est sauvegardé sous forme d’artefact avec `joblib`.

Les métadonnées associées sont stockées dans un fichier JSON.

Elles contiennent notamment :

- nom du modèle ;
- version ;
- région ;
- horizon de prévision ;
- variable cible ;
- variables utilisées ;
- hyperparamètres ;
- performances finales ;
- performances de la baseline.

Structure :

```text
artifacts/
├── electricity_consumption_hgb_j1.joblib
└── electricity_consumption_hgb_j1_metadata.json