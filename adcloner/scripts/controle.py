"""Contrôle qualité automatique de la vidéo livrée, en un rapport texte court (le but : ne pas ouvrir d'images pour ça).
Usage : python3 controle.py <dossier> [--planche]
Vérifie : durée, format, cadence, son ; mots affichés contre voix finale (retranscription) ; durée des sous-titres ; lignes trop longues ; trous de voix absents de la source.
--planche écrit une seule planche légère (controle_planche.jpg) d'images prises aux sous-titres, à regarder une fois."""
import difflib,glob,json,os,re,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
from analyse import transcrire
from voix import _pareil
from PIL import Image,ImageDraw

def norm(t):return re.sub(r"[^a-zà-ÿ0-9]+"," ",t.lower().replace("'"," ").replace("’"," ")).split()

def main():
    if len(sys.argv)<2:raise SystemExit(__doc__)
    d=sys.argv[1];f=fiche(d);an=analyse_json(d);alertes=[];ok=[]
    liv=[p for p in glob.glob(os.path.join(d,f"{f.get('ref','*')}_*_v*.mp4"))];liv=sorted(liv)[-1] if liv else None
    if not liv:raise SystemExit("livrable introuvable : lance rendu.py")
    S=probe(os.path.join(d,'src.mp4'));L=probe(liv);n_out=nb_images(liv)
    # --- technique
    if (L['largeur'],L['hauteur'])!=(S['largeur'],S['hauteur']):alertes.append(f"dimensions {L['largeur']}x{L['hauteur']} ≠ source {S['largeur']}x{S['hauteur']}")
    else:ok.append(f"format {L['largeur']}x{L['hauteur']} identique à la source")
    if abs(L['fps']-S['fps'])>0.5:alertes.append(f"cadence {L['fps']} ≠ {S['fps']}")
    if not L['audio']:alertes.append("pas de piste audio")
    dv=n_out/L['fps'];ds=an['images']/S['fps'];r=dv/ds
    (ok if 0.98<=r<=1.02 else alertes).append(f"durée vidéo {dv:.2f} s / source {ds:.2f} s = {r*100:.1f} %")
    # --- voix finale contre sous-titres
    cues=json.load(open(os.path.join(d,'cues.json'))) if os.path.exists(os.path.join(d,'cues.json')) else []
    if cues and os.path.exists(os.path.join(d,'mix.wav')):
        tr=transcrire(os.path.join(d,'mix.wav'),f.get('langue_cible','fr'));entendu=norm(' '.join(s['text'] for s in tr['segments']))
        affiche=norm(' '.join(c[2] for c in cues));ex=set(norm(' '.join(f.get('controle',{}).get('sans_voix',[]))))
        manque=[];
        for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,affiche,entendu,autojunk=False).get_opcodes():
            if t!='equal' and not _pareil(affiche[i1:i2],entendu[j1:j2]):manque.append((' '.join(affiche[i1:i2]),' '.join(entendu[j1:j2])))  # homophones, pluriels, « 6 » / « six » ignorés
        manque=[m for m in manque if not all(w in ex for w in norm(m[0]))]
        # une graphie différente de la même parole (ex. « 100 % » / « 100% ») n'est pas une erreur : on garde les écarts de plus de 2 mots
        gros=[m for m in manque if len(m[0].split())>2 or len(m[1].split())>2]
        (ok if not gros else alertes).append(f"mots affichés contre voix : {len(gros)} écart(s) notable(s)"+(" "+str(gros[:4]) if gros else ""))
        if manque and not gros:ok.append(f"  ({len(manque)} petit(s) écart(s) de graphie ou de transcription)")
        mini=f.get('controle',{}).get('duree_min_sous_titre',0.3 if f.get('rendu',{}).get('sous_titres',{}).get('mode')=='mots' else 0.4)
        courts=[(c[2],round((c[1]-c[0])/an['fps'],2)) for c in cues if (c[1]-c[0])/an['fps']<mini-0.005]
        (alertes if courts else ok).append(f"sous-titres de moins de {str(mini).replace('.',',')} s : "+(str(courts[:4]) if courts else "aucun"))
    # --- lignes trop longues (relevé depuis la voix)
    trop=[];ls=sorted(f['lignes'],key=lambda l:l['debut'])
    for k,l in enumerate(ls):
        p=os.path.join(d,'tts',l['id']+'.json')
        if os.path.exists(p):
            dur=json.load(open(p))['character_end_times_seconds'][-1]
            fen=(ls[k+1]['debut'] if k+1<len(ls) else l['fin_fenetre'])-l['debut']  # une phrase peut aller jusqu'au début de la suivante
            if dur>fen+0.05:trop.append(f"{l['id']} ({dur:.2f} s pour {fen:.2f} s)")
    (alertes if trop else ok).append("phrases plus longues que leur fenêtre : "+(', '.join(trop) if trop else "aucune"))
    # --- trous de voix : silence d'au moins 1 s alors que la source parle (texte trop court ou mal calé)
    trous=[];fins=[]
    for l in ls:
        p=os.path.join(d,'tts',l['id']+'.json')
        if os.path.exists(p):fins.append((l['id'],l['debut'],l['debut']+json.load(open(p))['character_end_times_seconds'][-1]))
    for (i0,_,e0),(i1,s1,_) in zip(fins,fins[1:]):
        parle=sum(max(0,min(s1,m['b'])-max(e0,m['a'])) for m in an.get('mots',[]))
        if s1-e0>=1.0 and parle>=0.7:trous.append(f"{i0}→{i1} {e0:.1f}-{s1:.1f} s (source parle {parle:.1f} s)")
    (alertes if trous else ok).append("trous de voix absents de la source : "+(', '.join(trous) if trous else "aucun"))
    # --- sous-titres sur rectangles blancs : texte d'origine qui dépasse
    from controle_texte_visible import rapport
    rv=rapport(d,liv)
    if rv:
        (alertes if rv[1] else ok).append(rv[0])
        if rv[2]:alertes.append("à vérifier : "+rv[2])
    print("OK     :");[print("  -",x) for x in ok]
    print("ALERTE :" if alertes else "Aucune alerte automatique.");[print("  -",x) for x in alertes]
    print("À vérifier à la main (non automatisable) : fidélité de la voix à l'écoute, logo ou texte d'origine sur les micro-plans, qualité des plans remplacés.")
    if '--planche' in sys.argv and cues:
        W,H=L['largeur'],L['hauteur'];tw=160;th=int(round(tw*H/W/2)*2);ids=sorted({(c[0]+c[1])//2 for c in cues})
        pas=max(1,len(ids)//12);ids=ids[::pas][:12];want={i:k for k,i in enumerate(ids)};tiles={}
        for i,im in enumerate(lire_images(liv,f'scale={tw}:{th}',tw,th)):
            if i in want:tiles[want[i]]=Image.fromarray(im.copy())
        sh=Image.new('RGB',(6*tw,((len(tiles)+5)//6)*th))
        for k,t in sorted(tiles.items()):sh.paste(t,((k%6)*tw,(k//6)*th))
        sh.save(os.path.join(d,'controle_planche.jpg'),quality=70);print('planche :',os.path.join(d,'controle_planche.jpg'))
if __name__=='__main__':main()
