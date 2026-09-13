"""Mise à jour ciblée du PPTX, sans réécriture des styles ni des positions."""
from pathlib import Path
import zipfile
import re
import html
import json
import io
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r"C:\Users\Audren\Downloads\support_oral_bloc5_RNCP_Audren_CORRE (3).pptx")
OUTPUT = ROOT / "artifacts/support_oral_bloc5_RNCP_Audren_CORRE_meteo_actualise.pptx"
changes = {
3: {"Données de l’application éCO2mix en open data": "éCO2mix + météo quotidienne Open-Meteo (5 villes)", "Source : 2012–2026  |  Modélisation : 2019–2025": "éCO2mix : 2012–2026 | Météo et modèle : 2019–2025"},
7: {"130 924 lignes":"122 637 lignes", "27":"15", "colonnes finales":"13 variables + date + cible", "2019-01-08":"2019-01-01", "2026-06-29":"2025-12-30", "dataset final":"dataset météo parfaite", "fin features":"dernier instant source", "Suppression de la colonne entièrement vide.":"Jointure météo observée sur le jour local de t + 24 h.", "Consommation moyenne":"Moyenne sur le test 2025"},
8: {"Variables calendaires et cycliques":"Calendrier + 3 variables météo du jour cible", "Cosinus de l’heure et du jour de la semaine pour une meilleure continuité":"Températures réelle / ressentie et code WMO", "Pas d’information future dans les features":"Oracle : météo future connue, hors production"},
10: {"Sélectionner les variables utiles":"Sélection initiale — avant météo", "Filtrage métier : exclure les variables non disponibles au moment de la prédiction":"Étude initiale sans météo : variables disponibles à t", "RÉSULTAT":"ÉTUDE INITIALE", "variables retenues":"variables étudiées (historique)", "HGB top 7":"HGB sans météo (test 2025)", "HGB toutes variables":"HGB initial (validation 2024)", "IMPACT SUR LA PERFORMANCE":"REPÈRES HISTORIQUES — PÉRIODES DISTINCTES"},
11: {"Sélectionner les variables utiles":"Importance des variables — étude initiale", "Sélection du top 10 en importance pour le moment":"10 variables historiques conservées dans la chaîne météo", "Performances du modèle à 10 variable : ":"Validation initiale sans météo (avant enrichissement) :"},
12: {"Supprimer la redondance":"Redondance — étude initiale et choix final", "Passage à 7 variables":"Modèle météo final : 10 + 3 = 13 variables", "Suppression de la consommation de la dernière demie-heure, de la consommation de l’avant-dernier jour et du slot de demie heure (de 0 à 47)":"La réduction à 7 variables appartient à l’étude initiale. La chaîne météo conserve les 10 variables historiques et ajoute 3 variables du jour cible.", "RÉSULTATS FINAUX":"COMPARAISONS INITIALES SANS MÉTÉO", "CHECK DE CORRELATION":"ANALYSE INITIALE DE CORRÉLATION"},
13: {"Entraîner et comparer les modèles":"Comparaison initiale des modèles", "MODÈLES COMPARÉS":"ÉTUDE INITIALE SANS MÉTÉO", "VALIDATION":"CHAÎNE MÉTÉO : HGB CONSERVÉ"},
14: {"Optimiser les performances du modèle":"Optimisation initiale — paramètres conservés", "Le gain d’optimisation est limité : le modèle par défaut était déjà bien adapté.":"Chaîne météo : mêmes hyperparamètres, sans nouveau tuning.", "La vraie amélioration vient surtout du feature engineering et du choix du modèle.":"Le gain météo est évalué séparément sur 2024 puis 2025."},
15: {"Météo de la veille : 100 % disponible":"Veille : disponibilité réelle à vérifier", "Météo du jour cible : test oracle":"Jour cible observé : météo parfaite", "Périmètre régional approximé par 5 villes":"Bordeaux, Limoges, La Rochelle, Bayonne, Pau"},
16: {"La température apporte une information physique absente des seuls historiques.":"Les 3 variables météo cible améliorent la MAE de 22 %.", "Elle aide surtout à expliquer les écarts liés au chaud/froid et certains pics.":"Effet mesuré sur les mêmes lignes du test 2025.", "L'amélioration montre que le modèle initial était limité par l'information disponible, pas seulement par l'algorithme.":"Ce gain porte sur la météo observée ; il reste à confirmer avec des prévisions archivées."},
17: {"Résultats finaux sur le test 2025":"Test 2025 — modèle avec météo parfaite", "Modèle MAE":"MAE météo parfaite", "gain MAE":"gain vs baseline", "MAE vs conso moyenne":"MAE / moyenne (pas MAPE)"},
18: {"Résultats finaux sur le test 2025":"Test 2025 — réel vs météo parfaite"},
19: {"electricity_consumption_hgb_j1.joblib":"artifacts/oracle_pipeline/model.joblib", "electricity_consumption_hgb_j1_metadata.json":"artifacts/oracle_pipeline/metadata.json", "version":"version : 2.0.0-oracle", "features sélectionnées":"13 variables (10 + 3 météo)", "métriques test":"metrics : validation 2024 / test 2025", "baseline":"experimental_oracle : true", "src/features.py reconstruit les variables":"features.py + weather.py : variables oracle", "src/predict.py charge le modèle et prédit à J+1":"predict_oracle.py : simulation à H+24", "Test hors notebook validé":"Artefact rechargé et prédiction vérifiée"},
20: {"Pytest : contrôle de features.py et predict.py":"Pytest : 22 tests locaux réussis", "Validation à chaque push / pull request":"Météo, H+24, splits et standardisation testés", "Assurer que la production ne contienne pas de bug":"Détecter les régressions du code"},
21: {"Runs d’expérimentation":"Expérience : electricity_consumption_j1_oracle", "Paramètres et métriques":"Métriques 2024 / 2025 + paramètres", "Artefacts modèle":"Modèle, JSON et prédictions CSV", "Model Registry : candidat / champion":"Registry : modèle oracle, version 1"},
22: {"Suivre la performance en production":"Suivi des erreurs — prototype et oracle", "HISTORISATION":"PROTOTYPE DE MONITORING", "Le monitoring réalisé sur MLFlow compare la performance récente à la MAE de référence du modèle.":"monitoring.py compare la MAE récente à la référence ; MLflow conserve les runs.", "Une alerte indique une possible dégradation nécessitant analyse ou réentraînement.":"Oracle : erreurs exportées dans predictions_2025.csv ; pas de suivi en production."},
23: {"Collecter, historiser et réentraîner":"Réentraîner — chaîne oracle reproductible", "Les prédictions et valeurs réelles alimentent l’historique.":"oracle_pipeline.py : dataset, validation, test et exports.", "Un modèle candidat est réentraîné sur données récentes.":"Modèle évalué sur 2025, entraîné avant le test.", "La promotion n’est envisagée qu’après comparaison avec le champion.":"Modèle oracle enregistré séparément dans MLflow.", "Données rafraîchies quotidiennement et check hebdomadaire pour vérifier si un drift est en train de se créer.":"Rafraîchissement et contrôle du drift : automatisations envisagées, non planifiées dans cette chaîne."},
24: {"Modèle complet de prévision J+1":"Chaîne H+24 avec météo parfaite", "Gain de ≈19 % vs baseline":"MAE : −37,5 % vs baseline ; −22 % vs HGB", "Chaîne ML traçable : modèle, métriques, tests, monitoring":"MAE 161,8 MW ; 3,43 % de la conso moyenne", "Industrialisation volontairement légère":"Oracle rétrospectif ; production à adapter"}
}

with zipfile.ZipFile(SOURCE) as z:
    content = {n: z.read(n) for n in z.namelist()}
    infos = z.infolist()
counts = {}
for slide, replacements in changes.items():
    name = f"ppt/slides/slide{slide}.xml"
    xml = content[name].decode('utf-8')
    for old, new in replacements.items():
        old_encoded = html.escape(old, quote=False)
        # Only text nodes change; every run's original styling remains intact.
        needle = '>' + old_encoded + '</a:t>'
        if needle not in xml:
            raise ValueError(f"Slide {slide}: texte absent : {old}")
        xml = xml.replace(needle, '>' + html.escape(new, quote=False) + '</a:t>')
    content[name] = xml.encode('utf-8')
    counts[slide] = len(replacements)

def text_image(name, text):
    old = Image.open(io.BytesIO(content[name]))
    # Same aspect ratio as the existing screenshot, rendered at higher resolution.
    w = max(1200, old.width)
    h = round(w * old.height / old.width)
    im = Image.new('RGB', (w, h), '#151719')
    draw = ImageDraw.Draw(im)
    lines = text.splitlines()
    size = max(8, min(int((h - 40) / max(len(lines), 1) / 1.25), 38))
    fontpath = 'C:/Windows/Fonts/consola.ttf'
    while True:
        font = ImageFont.truetype(fontpath, size)
        if max(draw.textlength(line, font=font) for line in lines) <= w-40 or size <= 8:
            break
        size -= 1
    draw.multiline_text((20, 20), text, fill='#d9e7ee', font=font, spacing=max(2, size//4))
    out = io.BytesIO(); im.save(out, format='PNG'); content[name] = out.getvalue()

meta = json.loads((ROOT/'artifacts/oracle_pipeline/metadata.json').read_text(encoding='utf-8'))
compact = {k: meta[k] for k in ['version','region','forecast_horizon','features','hyperparameters','weather_alignment','experimental_oracle']}
compact['test_2025'] = {"MAE":161.7893,"RMSE":217.4787,"R2":0.956539}
text_image('ppt/media/image25.png', json.dumps(compact, indent=2, ensure_ascii=False))
text_image('ppt/media/image4.png', 'VARIABLES FINALES : 13\n\n10 historiques / calendaires\n+ température moyenne cible\n+ température ressentie cible\n+ code WMO cible (catégorie)\n\nMétéo parfaite : jour de t + 24 h')
text_image('ppt/media/image19.png', 'tests/\n  test_features.py\n  test_predict.py\n  test_weather.py\n  test_compare_weather.py\n  test_oracle_pipeline.py')
text_image('ppt/media/image13.png', 'pytest tests -q\n22 passed\n8 warnings : ancien artefact sklearn 1.9.0 / 1.9.1')
text_image('ppt/media/image22.png', 'MLflow — expérience oracle\n\nelectricity_consumption_j1_oracle\nRegistry : electricity-consumption-j1-oracle\nVersion enregistrée : 1\n\nTest 2025\nMAE  : 161,789 MW\nRMSE : 217,479 MW\nR²   : 0,956539\n\nexperimental_oracle = true\nModèle + metadata.json + prédictions CSV')
with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as out:
    for info in infos:
        out.writestr(info, content[info.filename])
with zipfile.ZipFile(OUTPUT) as check:
    assert check.testzip() is None
    for name in check.namelist():
        if name.endswith('.xml') or name.endswith('.rels'):
            ET.fromstring(check.read(name))
print(OUTPUT)
print(f'{len(counts)} slides mises à jour ; 5 visuels actualisés ; 24 slides conservées.')
