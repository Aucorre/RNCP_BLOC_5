# Prévision de la consommation électrique régionale

## Contexte

L'équilibre entre production et consommation d'électricité doit être assuré en permanence. La consommation varie fortement selon l'heure, le jour de la semaine, la saison, les périodes de vacances et les conditions météorologiques.

Pouvoir anticiper ces variations permet aux gestionnaires du réseau de mieux adapter les moyens de production à la demande, de limiter les déséquilibres et de faciliter l'intégration de productions renouvelables variables.

Ce projet vise à développer un modèle de Machine Learning capable de prévoir à court terme la consommation électrique d'une région française à partir de données historiques de consommation, de variables calendaires et, dans un second temps, de données météorologiques.

Le projet est réalisé dans le cadre du bloc 5 de la certification RNCP39586 :

> Concevoir et déployer des modèles d'apprentissage automatique.

---

## Problématique

L'objectif du projet est de répondre à la question suivante :

> Peut-on prévoir la consommation électrique future d'une région française à partir de son historique récent de consommation, du contexte calendaire et de variables explicatives externes ?

La tâche principale est une **régression sur série temporelle**.

L'horizon de prévision définitif sera fixé après l'analyse exploratoire des données. Plusieurs horizons pourront être évalués, par exemple :

- H+1 ;
- H+24 ;
- même pas de temps le lendemain.

Le projet commencera sur une région afin de valider la méthodologie avant d'envisager une généralisation à plusieurs régions.

---

## Intérêt métier

Une prévision fiable de la demande électrique peut contribuer à :

- mieux anticiper les périodes de forte consommation ;
- améliorer l'équilibrage entre production et consommation ;
- réduire le recours à des moyens de production coûteux lors des pics ;
- mieux planifier les échanges et les besoins de flexibilité ;
- faciliter l'intégration des énergies renouvelables.

L'objectif du projet n'est pas de reproduire les outils opérationnels de RTE, mais de construire et d'évaluer une chaîne de Machine Learning cohérente sur des données ouvertes réelles.

---

## Source de données principale

### Données éCO2mix régionales consolidées et définitives

Source : **RTE / ODRE / data.gouv.fr**

Jeu de données utilisé comme source principale pour la consommation électrique régionale.

[Données eco2mix regionales consolidées et définitives](https://www.data.gouv.fr/datasets/donnees-eco2mix-regionales-consolidees-et-definitives/reuses_and_dataservices)

Le fichier téléchargé contient environ **3 millions de lignes** pour un volume d'environ **400 Mo**.

L'extrait inspecté comporte notamment les variables suivantes :

- `Code INSEE région`
- `Région`
- `Nature`
- `Date`
- `Heure`
- `Date - Heure`
- `Consommation (MW)`
- `Thermique (MW)`
- `Nucléaire (MW)`
- `Eolien (MW)`
- `Solaire (MW)`
- `Hydraulique (MW)`
- `Pompage (MW)`
- `Bioénergies (MW)`
- `Ech. physiques (MW)`
- `Stockage batterie`
- `Déstockage batterie`
- `Eolien terrestre`
- `Eolien offshore`
- différents taux de couverture et de charge par filière.

Les premières années du jeu présentent davantage de valeurs absentes sur certaines variables de production, tandis que les années récentes sont plus complètes. Ce point devra être quantifié précisément pendant l'exploration avant de fixer la période d'étude.

---

## Sources complémentaires envisagées

### Données météorologiques

Une source météorologique ouverte sera ajoutée afin d'étudier l'effet de variables telles que :

- température ;
- température minimale et maximale ;
- éventuellement humidité, vent ou nébulosité si leur intérêt est démontré.

La source et la granularité seront choisies après définition de la région et de l'horizon de prévision.

### Données calendaires

Des variables calendaires pourront être construites ou enrichies à partir de sources publiques :

- heure ;
- jour de la semaine ;
- week-end ;
- mois ;
- saison ;
- jours fériés ;
- vacances scolaires.

---

## Unité d'observation

L'unité d'observation est un **pas de temps pour une région donnée**.

Chaque ligne du futur jeu de données Machine Learning représentera les informations disponibles jusqu'à un instant `t`, associées à la consommation observée à un instant futur `t+h`.

Exemple conceptuel :

| Date - Heure | Région | Conso t | Conso t-1 | Conso t-24 | Calendrier | Météo | Cible conso t+h |
|---|---|---:|---:|---:|---|---|---:|
| 2026-01-10 14:00 | Région A | ... | ... | ... | ... | ... | ... |

---

## Variable cible

La variable cible sera dérivée de :

`Consommation (MW)`

Pour un horizon `h`, la cible prendra la forme :

`Consommation_t_plus_h`

Il s'agit d'une variable quantitative continue exprimée en MW.

La valeur de `h` sera fixée après l'analyse de la fréquence réelle des observations et des besoins métier retenus.

---

## Variables explicatives envisagées

La liste définitive sera déterminée à partir de l'analyse exploratoire et d'une méthode de sélection de variables.

### Historique de consommation

Des variables retardées pourront notamment être construites :

- consommation au pas précédent ;
- consommation à la même heure la veille ;
- consommation à la même heure la semaine précédente ;
- variations récentes de consommation.

### Statistiques glissantes

- moyenne glissante sur plusieurs pas de temps ;
- moyenne glissante journalière ;
- moyenne glissante hebdomadaire ;
- minimum et maximum récents ;
- volatilité ou écart-type récent.

### Variables calendaires

- heure ;
- jour de la semaine ;
- week-end ;
- mois ;
- saison ;
- jour férié ;
- vacances scolaires.

### Variables météorologiques

Sous réserve de disponibilité et de pertinence :

- température ;
- température ressentie ou indicateur équivalent ;
- autres variables météorologiques retenues après analyse.

### Variables issues du système électrique

Le dataset contient également des informations de production et d'échanges.

Ces variables ne seront utilisées qu'après vérification de leur disponibilité réelle au moment de la prédiction. Pour éviter toute fuite d'information, les valeurs contemporaines ou futures inconnues au moment de l'inférence ne devront pas être utilisées comme variables explicatives.

Des valeurs historiques retardées de certaines filières pourront en revanche être étudiées si elles apportent une information pertinente.

---

## Méthodologie envisagée

Le projet suivra les étapes suivantes :

1. Compréhension et exploration des données
2. Analyse de la complétude selon les années et les régions
3. Choix de la période et de la région d'étude
4. Nettoyage et préparation
5. Construction de la variable cible
6. Feature engineering temporel et calendaire
7. Intégration éventuelle des données météorologiques
8. Sélection des variables
9. Construction de plusieurs baselines
10. Entraînement de plusieurs modèles de régression
11. Validation temporelle
12. Évaluation et comparaison
13. Optimisation des hyperparamètres
14. Analyse détaillée des erreurs
15. Sauvegarde du modèle
16. Préparation du déploiement
17. Mise en place du CI/CD
18. Monitoring des performances
19. Collecte et historisation des nouvelles données

---

## Baselines

Avant tout modèle de Machine Learning, plusieurs méthodes naïves seront évaluées.

Exemples :

- dernière valeur connue ;
- consommation observée au même horaire la veille ;
- consommation observée au même horaire la semaine précédente ;
- moyenne historique pour un créneau comparable.

Ces baselines permettront de vérifier que le modèle apporte une amélioration réelle par rapport à des règles simples adaptées aux séries temporelles électriques.

---

## Stratégie d'évaluation

Les données étant temporelles, aucune séparation aléatoire classique ne sera utilisée.

L'entraînement, la validation et le test respecteront l'ordre chronologique afin de reproduire une situation réelle :

> apprendre sur le passé et prédire une période future.

Une validation de type `TimeSeriesSplit` ou une validation chronologique équivalente pourra être utilisée lors de l'optimisation.

Les métriques envisagées sont notamment :

- MAE ;
- RMSE ;
- R² ;
- éventuellement MAPE ou sMAPE après vérification de leur pertinence.

L'évaluation ne se limitera pas à une métrique globale. Une attention particulière sera portée :

- aux pics de consommation ;
- aux différentes saisons ;
- aux heures de pointe et heures creuses ;
- aux jours ouvrés, week-ends et jours fériés.

---

## Vigilances méthodologiques

Plusieurs risques devront être contrôlés :

- fuite de données entre l'instant de prédiction et la cible ;
- utilisation de variables qui ne seraient pas disponibles au moment réel de l'inférence ;
- incohérences ou ruptures temporelles ;
- valeurs manquantes sur les années les plus anciennes ;
- évolution du schéma et de la complétude au fil du temps ;
- changement éventuel de pas temporel ;
- effets calendaires et saisonniers ;
- différences entre régions ;
- surapprentissage sur une période particulière ;
- reproductibilité des traitements.

---

## Modèles envisagés

La sélection définitive sera réalisée après exploration des données.

Une première comparaison pourra inclure :

- régression linéaire régularisée ;
- Random Forest ;
- HistGradientBoosting ;
- XGBoost ou LightGBM si leur utilisation apporte un bénéfice mesurable.

Les modèles seront comparés aux baselines temporelles avant toute optimisation poussée.

---

## Organisation du projet

```text
electricity-consumption-ml/
│
├── README.md
├── requirements.txt
│
├── data/
│   ├── raw/
│   └── processed/
│
├── notebooks/
├── src/
├── artifacts/
├── tests/
└── docs/
```

---

## Lien avec le bloc 5 RNCP

Le projet doit permettre de produire des preuves concrètes pour les différentes compétences du bloc 5 :

- analyse du besoin ;
- définition et justification de la stratégie de résolution ;
- choix des technologies et outils ;
- construction d'un jeu de données exploitable ;
- construction des variables ;
- sélection des variables ;
- entraînement de modèles d'apprentissage automatique ;
- optimisation des performances ;
- sauvegarde du modèle ;
- mise en place d'un processus CI/CD ;
- monitoring des performances ;
- collecte des nouvelles données et historisation des prédictions.

Une attention particulière sera portée aux compétences éliminatoires relatives à la construction des variables, à leur sélection, à l'entraînement et à l'optimisation des modèles.

---

## État du projet

Le sujet et la source de données principale sont définis.

Le dataset brut a été téléchargé et une première inspection montre :

- un volume d'environ 400 Mo ;
- près de 3 millions de lignes ;
- une couverture multi-régionale ;
- de nombreuses variables liées à la consommation, la production et les échanges ;
- une complétude plus faible sur les premières années que sur les années récentes.

### Prochaine étape

> Réaliser une exploration complète du dataset afin de mesurer précisément la couverture temporelle, le pas de temps, la complétude par année et par région, puis sélectionner la période et la région retenues pour le premier modèle.



Les nouvelles prédictions et observations réelles sont historisées afin de suivre l’évolution des performances du modèle dans le temps. Une dégradation persistante des indicateurs peut déclencher un réentraînement. Le nouveau modèle est alors enregistré comme candidat dans MLflow et comparé au modèle de référence avant toute promotion.