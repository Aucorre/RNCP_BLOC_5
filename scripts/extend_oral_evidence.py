"""Insère six slides de preuves en conservant les slides originales."""
from pathlib import Path
import zipfile
import re
import html
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
source = Path(r'C:\Users\Audren\Downloads\support_oral_bloc5_RNCP_Audren_CORRE (4).pptx')
output = ROOT / 'artifacts/support_oral_bloc5_RNCP_Audren_CORRE_preuves_champion.pptx'
with zipfile.ZipFile(source) as z:
    files = {n: z.read(n) for n in z.namelist()}
ns = {'p':'http://schemas.openxmlformats.org/presentationml/2006/main', 'a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
pres = files['ppt/presentation.xml'].decode()
size = ET.fromstring(pres).find('p:sldSz', ns)
W,H = int(size.attrib['cx']),int(size.attrib['cy'])
run = (ROOT/'artifacts/oracle_pipeline/mlflow_run_id.txt').read_text().strip()
example = json.loads((ROOT/'artifacts/oracle_pipeline/prediction_example.json').read_text())
digest = hashlib.sha256((ROOT/'artifacts/oracle_pipeline/model.joblib').read_bytes()).hexdigest()

slides = [
(19, 'C5.3.1', 'Preuve — un modèle sauvegardé et identifiable',
 [('ARTEFACTS PRODUITS', ['model.joblib : estimateur HGB entraîné', 'metadata.json : version 2.0.0-oracle', '13 variables : 10 historiques + 3 météo', 'Dossier : artifacts/oracle_pipeline/']),
  ('CONTRAT DE RÉUTILISATION', ['Horizon : t + 24 h ; région : Nouvelle-Aquitaine', 'Ordre des variables fourni par le JSON', 'experimental_oracle : true', 'Météo observée du jour cible obligatoire'])],
 'Empreinte SHA-256 du modèle : ' + digest[:32] + '…'),
(19, 'C5.3.1', 'Preuve — prédire après rechargement Joblib',
 [('SÉQUENCE EXÉCUTÉE', ['1. Sauvegarder avec joblib.dump', '2. Recharger avec joblib.load', '3. Reconstruire les 13 variables', '4. Exécuter model.predict hors notebook']),
  ('EXEMPLE EXPORTÉ — TEST 2025', ['Source : 30/12/2025 à 22:30 UTC', 'Cible : 31/12/2025 à 22:30 UTC', f"Prédiction : {example['prediction_mw']:.2f} MW", f"Réel : {example['actual_mw']:.2f} MW ; écart : {abs(example['actual_mw']-example['prediction_mw']):.2f} MW"] )],
 'Source : prediction_example.json. Exemple de fonctionnement ; la MAE globale reste 161,79 MW.'),
(21, 'C5.3.2', 'Preuve — relier le run à la version du modèle',
 [('MLFLOW VÉRIFIÉ', ['Expérience : electricity_consumption_j1_oracle', 'Run : complete_oracle_pipeline', 'Registry : electricity-consumption-j1-oracle', 'Version enregistrée : 1']),
  ('ÉLÉMENTS TRAÇABLES', ['Hyperparamètres et métriques 2024 / 2025', 'Modèle + métadonnées JSON', 'Prédictions, valeurs réelles et exemple exportés', 'Aucun alias champion défini à ce jour'])],
 'Run ID : ' + run),
(21, 'C5.3.2', 'Sélection — meilleur modèle expérimental',
 [('VALIDATION 2024 — COMPARAISON', ['Même jeu de lignes et mêmes hyperparamètres', 'Baseline : MAE 277,44 MW', 'HGB sans météo : MAE 205,64 MW', 'HGB météo parfaite : MAE 159,94 MW']),
  ('CONFIRMATION SUR LE TEST 2025', ['HGB sans météo : MAE 207,45 MW', 'HGB météo parfaite : MAE 161,79 MW', 'Gain : 22 % de MAE ; R² : 0,957', 'Choix expérimental : HGB météo parfaite'])],
 'Sélection sur validation ; test 2025 de confirmation. Ce choix ne constitue pas une promotion en production.'),
(22, 'C5.3.3', 'Preuve — mesurer les erreurs et fixer une alerte',
 [('RÉSULTATS SUR 17 511 OBSERVATIONS', ['Consommation moyenne : 4 717,35 MW', 'MAE : 161,79 MW ; RMSE : 217,48 MW', 'MAE / moyenne : 3,43 % (pas la MAPE)', 'Source : predictions_2025.csv et error_scale.json']),
  ('RÈGLE DU PROTOTYPE DE MONITORING', ['Comparer la MAE récente à la référence', 'Fenêtre par défaut : 500 prédictions évaluées', 'Seuil proposé : référence × 1,20', 'Avec 161,79 MW : alerte au-delà de 194,15 MW'])],
 'monitoring.py implémente la règle ; son application continue au modèle oracle n’est pas automatisée.'),
(23, 'C5.3.4', 'Champion / challenger — décision de promotion',
 [('CRITÈRES À SATISFAIRE', ['Comparer candidat et référence sur les mêmes dates', 'Réduire la MAE et contrôler RMSE / pics', 'Vérifier schéma, tests et rechargement', 'Vérifier la disponibilité des entrées à l’instant t']),
  ('DÉCISION ET TRAÇABILITÉ', ['Oracle : meilleur résultat expérimental', 'Météo future observée : non disponible à t', 'Pas de promotion comme champion opérationnel', 'Après validation : alias champion + retour arrière'])],
 'Processus proposé : conserver la version précédente et tracer le motif de promotion. Aucun alias n’a été modifié.')]

def shape(i,x,y,w,h,lines,font=22,color='12202F',fill=None,bold=False):
    geom = f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else '<a:noFill/>'
    paragraphs = ''.join(f'<a:p><a:pPr><a:spcAft><a:spcPts val="1600"/></a:spcAft></a:pPr><a:r><a:rPr lang="fr-FR" sz="{font*100}" b="{int(bold)}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="Calibri"/></a:rPr><a:t>{html.escape(line)}</a:t></a:r></a:p>' for line in lines)
    return f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="Evidence {i}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{int(x)}" y="{int(y)}"/><a:ext cx="{int(w)}" cy="{int(h)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>{geom}<a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr wrap="square" lIns="150000" rIns="150000" tIns="100000" bIns="100000"><a:normAutofit/></a:bodyPr><a:lstStyle/>{paragraphs}</p:txBody></p:sp>'

rels = files['ppt/_rels/presentation.xml.rels'].decode()
ct = files['[Content_Types].xml'].decode()
ids = list(ET.fromstring(pres).find('p:sldIdLst', ns))
insertions = {}
for idx,(after,competency,title,cards,foot) in enumerate(slides,25):
    shapes = shape(2,.05*W,.05*H,.70*W,.12*H,[title],30,bold=True)
    shapes += shape(3,.78*W,.04*H,.19*W,.06*H,['Bloc 5 — '+competency],12,'2F61B8','F5F8FC',True)
    for k,(heading,body) in enumerate(cards):
        x = (.055+k*.46)*W
        shapes += shape(10+k*2,x,.24*H,.43*W,.09*H,[heading],18,'2F61B8',bold=True)
        shapes += shape(11+k*2,x,.34*H,.43*W,.43*H,body,21,fill='F5F8FC')
    shapes += shape(20,.055*W,.80*H,.90*W,.10*H,[foot],15,'2F61B8')
    shapes += shape(21,.055*W,.94*H,.9*W,.04*H,['RNCP39586 — Bloc 5 — Apprentissage automatique'],10,'666666')
    xml = f'<p:sld xmlns:p="{ns["p"]}" xmlns:a="{ns["a"]}"><p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill></p:bgPr></p:bg><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/>{shapes}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'
    files[f'ppt/slides/slide{idx}.xml'] = xml.encode()
    files[f'ppt/slides/_rels/slide{idx}.xml.rels'] = b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout2.xml"/></Relationships>'
    rid = f'rIdEvidence{idx}'
    rels = rels.replace('</Relationships>',f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{idx}.xml"/></Relationships>')
    ct = ct.replace('</Types>',f'<Override PartName="/ppt/slides/slide{idx}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/></Types>')
    insertions.setdefault(after,[]).append(f'<p:sldId id="{1000+idx}" r:id="{rid}"/>')
matches = re.findall(r'<p:sldId\b[^>]*/>',pres)
assert len(matches)==24
for after, additions in insertions.items():
    pres = pres.replace(matches[after-1],matches[after-1]+''.join(additions))
files['ppt/presentation.xml']=pres.encode()
files['ppt/_rels/presentation.xml.rels']=rels.encode()
files['[Content_Types].xml']=ct.encode()
if 'docProps/app.xml' in files:
    files['docProps/app.xml']=re.sub(rb'<Slides>\d+</Slides>',b'<Slides>30</Slides>',files['docProps/app.xml'])
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
    for name,data in files.items():
        if name.endswith(('.xml','.rels')): ET.fromstring(data)
        z.writestr(name,data)
with zipfile.ZipFile(output) as z:
    assert z.testzip() is None
    assert len(ET.fromstring(z.read('ppt/presentation.xml')).find('p:sldIdLst',ns))==30
print(output)
