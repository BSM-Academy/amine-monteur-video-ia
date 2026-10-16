"""Recale les phrases à la suite quand la voix cible déborde un peu de ses fenêtres (voix d'origine rapide).
Usage : python3 enchainer.py <dossier> [--ecart 0.06]   (après voix.py, avant mix.py)
Début de chaque phrase = max(début d'origine dans analyse.json, fin de la précédente + écart). Affiche le retard maximal (garder < 0,6-0,8 s) et la fin de la voix."""
import json,sys,os,subprocess
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import FF
FP=os.path.join(os.path.dirname(FF),'ffprobe');FP=FP if os.path.exists(FP) else 'ffprobe'
d=sys.argv[1];ec=float(sys.argv[sys.argv.index('--ecart')+1]) if '--ecart' in sys.argv else 0.06
f=json.load(open(os.path.join(d,'fiche.json')));a=json.load(open(os.path.join(d,'analyse.json')))
orig={p['id']:p['debut'] for p in a['phrases']}
dur=lambda i:float(subprocess.run([FP,'-v','error','-show_entries','format=duration','-of','csv=p=0',os.path.join(d,'tts',i+'.mp3')],capture_output=True,text=True).stdout)
prev=0;mx=0;pire=None
for l in f['lignes']:
    o=orig.get(l['id'],l['debut']);s=max(o,prev+ec);l['debut']=round(s,2);prev=s+dur(l['id'])
    if s-o>mx:mx=s-o;pire=l['id']
json.dump(f,open(os.path.join(d,'fiche.json'),'w'),ensure_ascii=False,indent=1)
print(f"retard max {mx:.2f} s ({pire}), fin de la voix {prev:.2f} s / vidéo {a['duree']:.2f} s")
