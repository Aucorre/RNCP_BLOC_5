"""Actualise le support (3) avec le candidat météo prévue, sans changer les dispositions."""
from pathlib import Path
import runpy
import re
import html
import json
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
code=(ROOT/'scripts/update_oral_slides.py').read_text(encoding='utf-8')
state={'__file__':str(ROOT/'scripts/update_oral_slides.py')}
exec(code.split('with zipfile.ZipFile(SOURCE)')[0],state)
with zipfile.ZipFile(state['SOURCE']) as z: files={n:z.read(n) for n in z.namelist()}
state['content']=files
exec(code[code.index('def text_image('):code.index('\nmeta = json.loads')],state)
image=state['text_image']
meta = json.loads((ROOT/'artifacts/forecast_trial/metadata.json').read_text())
data = pd.read_csv(ROOT/'artifacts/forecast_trial/predictions.csv')
target = 'target_consumption_t_plus_24h'
mean = data[target].mean()
mae = (data[target]-data.meteo_prevue).abs().mean()
ratio=100*mae/mean

def replace_paragraphs(slide, replacements, exact=False):
    name=f'ppt/slides/slide{slide}.xml'
    xml=files[name].decode()
    found=set()
    def change(match):
        p=match.group()
        texts=re.findall(r'<a:t>(.*?)</a:t>',p,re.S)
        text=''.join(html.unescape(t) for t in texts)
        new=text
        for old,value in replacements.items():
            if (new == old if exact or len(old)<10 else old in new):
                new=new.replace(old,value); found.add(old)
        if new==text: return p
        count=0
        def sub(m):
            nonlocal count
            count+=1
            return '<a:t>'+ (html.escape(new,quote=False) if count==1 else '')+'</a:t>'
        return re.sub(r'<a:t>.*?</a:t>',sub,p,flags=re.S)
    xml=re.sub(r'<a:p>.*?</a:p>',change,xml,flags=re.S)
    missing=set(replacements)-found
    files[name]=xml.encode()

updates={
3:{'éCO2mix + météo quotidienne Open-Meteo (5 villes)':'éCO2mix + prévisions horaires ICON via Open-Meteo', 'éCO2mix : 2012–2026 | Météo et modèle : 2019–2025':'Candidat météo prévue : entraînement 2024 | test 2025'},
5:{'2019–2023':'2024 (candidat)', '2024':'Étude initiale', 'Validation chronologique':'Découpage chronologique, purge de 24 h', 'Comparaison de modèles simples et non linéaires':'Paramètres conservés ; aucun tuning sur 2025'},
7:{'122 637 lignes':'34 088 lignes', 'dataset météo parfaite':'16 577 train + 17 511 test', '2019-01-01':'2024-01-19', 'Jointure météo observée sur le jour local de t + 24 h.':'Jointure sur l’heure UTC de la cible H+24.'},
8:{'Calendrier + 3 variables météo du jour cible':'Calendrier + 3 prévisions météo horaires', 'Températures réelle / ressentie et code WMO':'Température prévue, ressentie prévue, code WMO', 'Oracle : météo future connue, hors production':'Prévision à 48 h : marge nominale de 24 h'},
10:{'HGB sans météo (test 2025)':'Ancien HGB sans météo (2025)'},
13:{'CHAÎNE MÉTÉO : HGB CONSERVÉ':'CANDIDAT : HGB + MÉTÉO PRÉVUE'},
15:{'Open-Meteo Historical Weather API':'Open-Meteo Previous Model Runs API', 'Données quotidiennes, sans clé API':'ICON Global : prévisions horaires archivées', 'Température moyenne':'Température prévue à 2 m', 'Température ressentie moyenne':'Température ressentie prévue', 'Code météo WMO':'Code météo prévu (catégorie WMO)', 'Veille : disponibilité réelle à vérifier':'Échéance météo : 48 h ; cible conso : H+24', 'Jour cible observé : météo parfaite':'Marge nominale avant t : 24 h', 'En production : utiliser la prévision J+1':'Publication réelle non horodatée par cette API'},
16:{'Comparer le modèle historique/calendaire avec le modèle enrichi par météo':'Même entraînement 2024 et mêmes 17 511 observations de test 2025', '207,5 MW':'226,7 MW', '161,8 MW':'177,4 MW', 'HGB + météo cible':'HGB + météo prévue', '~22%':'21,7 %', 'Les 3 variables météo cible améliorent la MAE de 22 %.':'Les prévisions ICON réduisent la MAE de 21,7 %.', 'Effet mesuré sur les mêmes lignes du test 2025.':'RMSE : 247,51 MW ; R² : 0,944 sur le test 2025.', 'Ce gain porte sur la météo observée ; il reste à confirmer avec des prévisions archivées.':'Oracle réentraîné sur les mêmes dates : MAE 178,30 MW (météo quotidienne).', "Si la météo du jour cible est observée, elle n'est pas disponible au moment t.":'Prévisions à 48 h utilisées pour une consommation à H+24.', 'Elle doit être présentée comme une expérience oracle hors production.':'Marge de publication supposée : 24 h ; à auditer par run.', "En production, on utiliserait la prévision météo J+1 disponible au moment de l'inférence.":'Test rétrospectif : aucune performance en production réelle mesurée.'},
17:{'Test 2025 — modèle avec météo parfaite':'Test 2025 — candidat avec météo prévue', '161,8 MW':'177,4 MW', 'MAE météo parfaite':'MAE météo prévue', '≈38%':'≈31,5 %', '0,957':'0,944', '3,43 %':f'{ratio:.2f} %'.replace('.',',')},
18:{'Test 2025 — réel vs météo parfaite':'Test 2025 — réel vs météo prévue'},
19:{'artifacts/oracle_pipeline/model.joblib':'artifacts/forecast_trial/meteo_prevue.joblib', 'artifacts/oracle_pipeline/metadata.json':'artifacts/forecast_trial/metadata.json', 'version : 2.0.0-oracle':'weather_model : icon_global', 'metrics : validation 2024 / test 2025':'metrics : test 2025 (3 configurations)', 'experimental_oracle : true':'offset : previous_day2', 'features.py + weather.py : variables oracle':'forecast_trial.py : jointure des prévisions', 'predict_oracle.py : simulation à H+24':'Modèle candidat sauvegardé avec joblib', 'Artefact rechargé et prédiction vérifiée':'Prédictions exportées dans predictions.csv'},
20:{'Pytest : 22 tests locaux réussis':'Test de jointure météo prévue : réussi', 'Météo, H+24, splits et standardisation testés':'H+24 en UTC, demi-heures et données manquantes'},
21:{'Expérience : electricity_consumption_j1_oracle':'Oracle : expérience MLflow existante', 'Métriques 2024 / 2025 + paramètres':'Candidat prévu : métriques et JSON locaux', 'Modèle, JSON et prédictions CSV':'Artefacts dans artifacts/forecast_trial/', 'Registry : modèle oracle, version 1':'Candidat prévu : non enregistré au Registry'},
22:{'Suivi des erreurs — prototype et oracle':'Suivi des erreurs — candidat météo prévue', 'Oracle : erreurs exportées dans predictions_2025.csv ; pas de suivi en production.':'Candidat : predictions.csv ; monitoring continu non activé.'},
23:{'Réentraîner — chaîne oracle reproductible':'Réentraîner — candidat météo prévue', 'oracle_pipeline.py : dataset, validation, test et exports.':'forecast_trial.py : archives, jointure, entraînement, test.', 'Modèle évalué sur 2025, entraîné avant le test.':'Entraînement sur 2024 ; test sur 2025, purge de 24 h.', 'Modèle oracle enregistré séparément dans MLflow.':'Candidat prévu sauvegardé ; promotion non effectuée.'},
24:{'Chaîne H+24 avec météo parfaite':'Candidat H+24 avec météo prévue ICON', 'MAE : −37,5 % vs baseline ; −22 % vs HGB':'MAE : −31,5 % vs baseline ; −21,7 % vs HGB', 'MAE 161,8 MW ; 3,43 % de la conso moyenne':f'MAE 177,4 MW ; {ratio:.2f} % de la conso moyenne'.replace('.',','), 'Météo intégrée en expérimentation ; jours fériés non intégrés':'Test rétrospectif ; disponibilité à auditer par run', 'Oracle rétrospectif ; production à adapter':'Entraînement météo limité à 2024', "Remplacer l'oracle météo par des prévisions J+1":'Valider les heures de publication des prévisions'}
}
slide_numbers=sorted(int(re.search(r'slide(\d+)\.xml',n).group(1)) for n in files if re.fullmatch(r'ppt/slides/slide\d+\.xml',n))
for slide in slide_numbers:
    # Existing corrections apply to matching text even if intermediate slides shifted numbering.
    for mapping in state['changes'].values():
        mapping={k:v for k,v in mapping.items() if k!='Chaîne ML traçable : modèle, métriques, tests, monitoring'}
        replace_paragraphs(slide,mapping,exact=True)
    for original_slide,mapping in updates.items():
        if original_slide==5 and slide!=5: continue
        replace_paragraphs(slide,mapping)
extra={
'model.joblib : estimateur HGB entraîné':'meteo_prevue.joblib : candidat entraîné',
'metadata.json : version 2.0.0-oracle':'metadata.json : ICON, périodes et paramètres',
'Dossier : artifacts/oracle_pipeline/':'Dossier : artifacts/forecast_trial/',
'Météo observée du jour cible obligatoire':'Trois prévisions horaires ICON requises',
'Empreinte SHA-256 du modèle : 4e3841dfa1e7086ced50fb3222d99ea6…':'Artefact : meteo_prevue.joblib (candidat météo prévue)',
'Prédire après rechargement Joblib':'Prédictions exportées du candidat',
'SÉQUENCE EXÉCUTÉE':'CHAÎNE EXÉCUTÉE',
'2. Recharger avec joblib.load':'2. Conserver les variables dans metadata.json',
'3. Reconstruire les 13 variables':'3. Joindre les prévisions ICON à H+24',
'4. Exécuter model.predict hors notebook':'4. Exporter les prédictions et valeurs réelles',
'Source : prediction_example.json. Exemple de fonctionnement ; la MAE globale reste 161,79 MW.':'Source : forecast_trial/predictions.csv ; MAE globale : 177,41 MW.',
'Relier le run à la version du modèle':'Traçabilité — oracle enregistré, candidat local',
'MLFLOW VÉRIFIÉ':'MLFLOW : ORACLE HISTORIQUE',
'Hyperparamètres et métriques 2024 / 2025':'Candidat prévu : paramètres et métriques 2025 locaux',
'VALIDATION 2024 — COMPARAISON':'PROTOCOLE DU NOUVEAU CANDIDAT',
'Baseline : MAE 277,44 MW':'Train : 16 577 observations de 2024',
'HGB sans météo : MAE 205,64 MW':'Test : 17 511 observations de 2025',
'HGB météo parfaite : MAE 159,94 MW':'Paramètres conservés ; pas de tuning sur 2025',
'HGB sans météo : MAE 207,45 MW':'HGB sans météo : MAE 226,67 MW',
'HGB météo parfaite : MAE 161,79 MW':'HGB météo prévue : MAE 177,41 MW',
'Gain : 22 % de MAE ; R² : 0,957':'Gain : 21,7 % de MAE ; R² : 0,944',
'Choix expérimental : HGB météo parfaite':'Candidat principal : HGB météo prévue',
'Sélection sur validation ; test 2025 de confirmation. Ce choix ne constitue pas une promotion en production.':'Comparaison exploratoire sur 2025 ; confirmation sur une période future nécessaire avant promotion.',
'Erreurs exportées dans predictions_2025.csv':'Erreurs exportées dans forecast_trial/predictions.csv',
'MAE : 161,79 MW ; RMSE : 217,48 MW':'MAE : 177,41 MW ; RMSE : 247,51 MW',
'MAE / moyenne : 3,43 % (pas la MAPE)':'MAE / moyenne : 3,76 % (pas la MAPE)',
'Source : predictions_2025.csv et error_scale.json':'Source : forecast_trial/predictions.csv et metrics.csv',
'Avec 161,79 MW : alerte au-delà de 194,15 MW':'Avec 177,41 MW : seuil proposé de 212,89 MW',
'monitoring.py implémente la règle ; son application continue au modèle oracle n’est pas automatisée.':'monitoring.py implémente la règle ; le candidat prévu n’est pas surveillé en continu.',
'Oracle : meilleur résultat expérimental':'Météo prévue : candidat principal',
'Météo future observée : non disponible à t':'Délai de publication : hypothèse à auditer',
'MAE : −38 % vs baseline ; −22 % vs HGB':'MAE : −31,5 % vs baseline ; −21,7 % vs HGB',
"Remplacer l'oracle météo par des prévisions archivées à J+1":'Valider les publications et tester une période future'
}
last=data.iloc[-1]
extra['Prédiction : 7190.88 MW']=f'Prédiction : {last.meteo_prevue:.2f} MW'
extra['Réel : 7196.00 MW ; écart : 5.12 MW']=f'Réel : {last[target]:.2f} MW ; écart : {abs(last[target]-last.meteo_prevue):.2f} MW'
for slide in slide_numbers: replace_paragraphs(slide,extra)
compact={k:meta[k] for k in ['weather_model','offset','train_rows','test_rows','features','hyperparameters']}
compact['metrics']=meta['metrics'][1]
image('ppt/media/image25.png',json.dumps(compact,indent=2,ensure_ascii=False))
image('ppt/media/image4.png','VARIABLES FINALES : 13\n\n10 historiques / calendaires\n+ forecast_temperature_2m\n+ forecast_apparent_temperature\n+ forecast_weather_code\n\nICON : previous_day2')
image('ppt/media/image9.png','ICON Global — prévisions archivées\n\ntemperature_2m_previous_day2\napparent_temperature_previous_day2\nweather_code_previous_day2\n\nCible consommation : t + 24 h\nJointure : heure UTC inférieure de la cible\nMarge nominale de disponibilité : 24 h')
image('ppt/media/image22.png','TRAÇABILITÉ DU CANDIDAT\n\nartifacts/forecast_trial/\n  meteo_prevue.joblib\n  metadata.json\n  metrics.csv\n  predictions.csv\n\nICON Global ; échéance météo 48 h\nTest 2025 : MAE 177,41 MW\n\nNon enregistré dans MLflow\nAucun alias champion attribué')
data.index=pd.to_datetime(data['Date - Heure'],utc=True)+pd.Timedelta(hours=24)
fig,axes=plt.subplots(2,1,figsize=(15,9),constrained_layout=True)
for ax,frame,title in [(axes[0],data[[target,'meteo_prevue']].resample('D').mean(),'Test 2025 — moyennes journalières'),(axes[1],data.loc['2025-01-13':'2025-01-19'],'13–19 janvier — pas de 30 minutes')]:
    ax.plot(frame.index,frame[target],label='Consommation réelle',color='#193b57')
    ax.plot(frame.index,frame.meteo_prevue,label='Météo prévue ICON',color='#e77827')
    ax.set_title(title,loc='left'); ax.set_ylabel('MW'); ax.grid(alpha=.2); ax.legend()
fig.suptitle(f'Candidat météo prévue — MAE 177,41 MW | RMSE 247,51 MW | R² 0,944\nMAE / moyenne : {ratio:.2f} % — test rétrospectif, pas de mesure en production')
chart=ROOT/'artifacts/forecast_trial/prediction_vs_reelle.png'
fig.savefig(chart,dpi=160); plt.close(fig)
files['ppt/media/image8.png']=chart.read_bytes()
out=ROOT/'artifacts/support_oral_bloc5_RNCP_Audren_CORRE_meteo_prevue.pptx'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for name,payload in files.items():
        if name.endswith(('.xml','.rels')): ET.fromstring(payload)
        z.writestr(name,payload)
with zipfile.ZipFile(out) as z: assert z.testzip() is None
print(out)
