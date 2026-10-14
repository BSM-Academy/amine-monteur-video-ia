"""Contrôle des sous-titres sur rectangles blancs : aucune lettre du sous-titre d'origine ne doit rester visible.
Usage : python3 controle_texte_visible.py <dossier>   (appelé aussi par controle.py quand layout.json existe)
Lit le livrable et layout.json (rectangles dessinés par rendu.py, image par image).
Signale : lettres sombres sur fond blanc hors de nos rectangles, près d'eux (texte d'origine qui dépasse) ;
et sous-titres d'origine entiers sur des images sans rectangle (à vérifier : carte de fin, texte voulu, ou oubli)."""
import glob,json,os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
from blocs import detecte

def plages(ims):
    r=[]
    for i in ims:
        if r and i-r[-1][1]<=2:r[-1][1]=i
        else:r.append([i,i])
    return ', '.join(f"{a}-{b}" if a!=b else f"{a}" for a,b in r)

def verifie(video,rects,W,H):
    """-> (images avec lettres d'origine qui dépassent, images avec un sous-titre d'origine sans rectangle)"""
    tol=max(2,round(2*W/720));fuite=[];sans=[]
    for i,im in enumerate(lire_images(video)):
        B,L=detecte(im,True);R=rects[i] if i<len(rects) else []
        if R:
            m=0.02*H;dedans=lambda l:any(r[0]-tol<=l[0] and l[2]<=r[2]+tol and r[1]-tol<=l[1] and l[3]<=r[3]+tol for r in R)
            hors=[l for l in L if any(l[3]>=r[1]-m and l[1]<=r[3]+m for r in R) and not dedans(l)]
            # sur la hauteur de nos rectangles : toute lettre compte ; juste au-dessus ou au-dessous : seulement un mot (2 lettres voisines), pas une tache isolée
            rang=lambda l:any(l[3]>r[1] and l[1]<r[3] for r in R)
            hors=[l for l in hors if rang(l) or any(q is not l and min(l[3],q[3])-max(l[1],q[1])>=0.5*min(l[3]-l[1],q[3]-q[1]) and max(q[0]-l[2],l[0]-q[2])<0.06*W for q in hors)]
            if hors:fuite.append(i)
        elif any(min(l[4],l[6])<0 or min(l[4],l[6])>=4*W/720 for b in B for l in b['l']):sans.append(i)  # vrai rectangle : marge blanche à gauche et à droite (pas le creux d'une lettre blanche contourée)
    return fuite,sans

def rapport(d,liv):
    p=os.path.join(d,'layout.json')
    if not os.path.exists(p):return None
    rects=json.load(open(p))['rects'];P=probe(liv);fuite,sans=verifie(liv,rects,P['largeur'],P['hauteur'])
    return (f"texte d'origine visible hors de nos rectangles : {len(fuite)} image(s)"+(f" ({plages(fuite)})" if fuite else ""),bool(fuite),
            f"sous-titre d'origine sur des images sans rectangle : {plages(sans)}" if sans else None)

if __name__=='__main__':
    if len(sys.argv)<2:raise SystemExit(__doc__)
    d=sys.argv[1];f=fiche(d);liv=sorted(glob.glob(os.path.join(d,f"{f.get('ref','*')}_*_v*.mp4")))
    if not liv:raise SystemExit("livrable introuvable : lance rendu.py")
    r=rapport(d,liv[-1])
    if r is None:raise SystemExit("layout.json absent : relance rendu.py (il l'écrit quand la fiche a des blocs)")
    print(('ALERTE : ' if r[1] else 'OK : ')+r[0]);r[2] and print('À VÉRIFIER : '+r[2])
