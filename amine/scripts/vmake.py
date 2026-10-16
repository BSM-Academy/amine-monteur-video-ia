"""Efface le texte à l'écran avec Vmake (tâche Subtitle SKM0002), aligne les images et repère où se trouvait le texte.
Usage : python3 vmake.py <dossier_de_travail> [--existant]
Entrée : <dossier>/src.mp4. Sorties : clean_vmake.mp4, vmake_zones.json (rectangles de texte par image), résumé court.
Variables : VMAKE_DIR (dossier du skill Vmake ; défaut : la copie du dépôt `vmake-skill/` si MT_AK est défini, sinon ~/.codex/skills/vmake-skill). Les clés MT_AK / MT_SK sont lues par le skill Vmake (variables d'environnement, ou scripts/.env sur le Mac)."""
import json,os,subprocess,sys,urllib.request
import numpy as np
from scipy import ndimage
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *

def lancer(src,out):
    depot=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','vmake-skill')  # copie du skill Vmake dans le dépôt dépôt (14/10/2026)
    mac=os.path.expanduser('~/.codex/skills/vmake-skill')
    # ordre : VMAKE_DIR ; sinon la copie du dépôt si les clés MT_AK/MT_SK sont dans l'environnement (cloud) ; sinon l'installation Mac (qui a son .env) ; sinon le dépôt
    vd=os.environ.get('VMAKE_DIR') or (depot if os.environ.get('MT_AK') else (mac if os.path.exists(mac) else depot));script=os.path.join(vd,'scripts','vmake_ai.py')
    if not os.path.exists(script):raise SystemExit(f"skill Vmake introuvable ({script}) : installe-le ou définis VMAKE_DIR")
    r=subprocess.run([sys.executable,script,'run-task','--task','SKM0002','--input',src,'--agent-name','AdCloner'],capture_output=True,text=True)
    txt=r.stdout[r.stdout.find('{'):] if '{' in r.stdout else ''
    try:url=json.loads(txt)['data']['result']['urls'][0]
    except Exception:raise SystemExit("Vmake n'a pas renvoyé de résultat :\n"+(r.stderr[-600:] or r.stdout[-600:]))
    urllib.request.urlretrieve(url,out)

def main():
    args=[a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:raise SystemExit(__doc__)
    d=args[0];src=os.path.join(d,'src.mp4');out=os.path.join(d,'clean_vmake.mp4')
    if '--existant' not in sys.argv or not os.path.exists(out):lancer(src,out)
    P=probe(src);W,H=P['largeur'],P['hauteur'];ns=nb_images(src);nv=nb_images(out)
    zones={};runs=[];cur=None;i=0;geants=0
    for a,b in zip(lire_images(src),lire_images(out)):
        dm=np.abs(a.astype(np.int16)-b.astype(np.int16)).sum(2)>130
        dm=ndimage.binary_closing(dm,np.ones((7,17)));lab,k=ndimage.label(dm);bx=[]
        for s in ndimage.find_objects(lab):
            h=s[0].stop-s[0].start;w=s[1].stop-s[1].start
            if h>14 and w>40:
                if h*w>0.5*W*H:geants+=1;continue  # zone de plus de la moitié de l'image : Vmake a réencodé toute l'image, pas du texte
                bx.append([int(s[1].start),int(s[0].start),int(s[1].stop),int(s[0].stop)])
        if bx:
            zones[i]=bx
            r=[min(c[0] for c in bx),min(c[1] for c in bx),max(c[2] for c in bx),max(c[3] for c in bx)]
            if cur and i-cur['b']<=6:cur['b']=i;cur['r']=[min(cur['r'][0],r[0]),min(cur['r'][1],r[1]),max(cur['r'][2],r[2]),max(cur['r'][3],r[3])];cur['t'].append(r)
            else:cur={'a':i,'b':i,'r':r,'t':[r]};runs.append(cur)
        i+=1
    json.dump({'images_source':ns,'images_vmake':nv,'zones':zones},open(os.path.join(d,'vmake_zones.json'),'w'))
    print(f"images : source {ns}, Vmake {nv}"+("  <-- Vmake a rendu moins d'images : la fin est reprise de la source" if nv<ns else ''))
    print(f"texte détecté sur {len(zones)} images, {len(runs)} périodes :")
    for r in runs:print(f"  images {r['a']}-{r['b']} ({r['a']/P['fps']:.1f}-{(r['b']+1)/P['fps']:.1f} s) zone {r['r']}, typique par image {[int(v) for v in np.median(r['t'],0)]}")  # union de la période / zone médiane
    if geants:print(f"ATTENTION : {geants} zone(s) couvrant plus de 50 % de l'image, écartées. Zones auto non fiables sur cette vidéo : passer en zones manuelles (zones_vmake: [{{images, rect}}]).")
if __name__=='__main__':main()
