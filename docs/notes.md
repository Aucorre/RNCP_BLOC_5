### Colonne entièrement vide

La colonne `Column 30` ne contient aucune valeur renseignée sur l'ensemble du jeu de données.

Elle n'apporte donc aucune information exploitable pour l'analyse ou la modélisation et sera supprimée lors de la phase de préparation.


### Analyse des doublons temporels

Les doublons détectés sur la clé `Région + Date - Heure` se concentrent autour des changements d’heure légale, fin mars et fin octobre.

Ce comportement s’explique par le passage entre heure d’hiver et heure d’été, qui modifie la correspondance entre heure locale et heure UTC. Certaines heures peuvent alors être répétées ou absentes selon la période.

Ces lignes ne sont donc pas considérées comme des doublons purs car la colonne Heure diffère mais il s'agit bel et bien du même relevé à deux heures différentes.

La reconstruction d’un index temporel cohérent avec le fuseau `Europe/Paris` sera réalisée lors de la phase de préparation des données.