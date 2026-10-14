"""Blocs blancs sur des sous-titres karaoké d'origine qui changent de niveau (sans Vmake, GL3E 12/10/2026).
Usage : python3 blocs_karaoke.py <dossier> [--taille 34] [--marge 3] [--marge-texte 22] [--tol-y 10] [--fin IMAGE] [--min-images 4] [--centre 360]
Entrées : boites_src.json (karaoke_boites.py), fiche.json (lignes, rendu.blocs_karaoke pour le découpage : max_mots, max_car, fusion_min), tts/*.json.
Méthode : 1) périodes = suites d'images où la boîte d'origine garde le même niveau (± tol-y) ; largeur typique = 95e centile
des largeurs, centrée sur le centre médian. 2) sous-titres italiens = rendu.fabrique_cues (mode mots). 3) un bloc blanc par
période, de largeur constante = max(largeur d'origine, plus large texte de la période + 2×marge-texte) ; le texte courant
(ou le précédent pendant les pauses) est écrit dedans ; un sous-titre qui traverse un changement de niveau suit le bloc.
Écrit blocs.json {blocs, cues} lu par rendu.py avec rendu.blocs: "auto"."""
import json,os,sys,argparse,numpy as np
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import police,fiche,analyse_json,carte_remplacements
import rendu
p=argparse.ArgumentParser();p.add_argument('d');p.add_argument('--taille',type=int,default=34);p.add_argument('--marge',type=int,default=3)
p.add_argument('--marge-texte',type=int,default=22);p.add_argument('--tol-y',type=int,default=10);p.add_argument('--fin',type=int,default=10**9);p.add_argument('--trou',type=int,default=4);p.add_argument('--min-images',type=int,default=4);p.add_argument('--centre',type=int,default=None)
A=p.parse_args();d=A.d;f=fiche(d);an=analyse_json(d);W,fps,N=an['largeur'],an['fps'],an['images']
b0={int(k):v for k,v in json.load(open(os.path.join(d,'boites_src.json'))).items()}
carte,_=carte_remplacements(f.get('rendu',{}))  # plan remplacé : la boîte de sous-titre est celle de l'image donneuse (sinon le texte d'origine de la donneuse resterait visible)
for k,src in carte.items():
    if src in b0:b0[k]=b0[src]
    else:b0.pop(k,None)
b={k:v for k,v in b0.items() if k<A.fin}
if carte:print(f"{len(carte)} image(s) de plans remplacés : boîtes prises sur les images donneuses")
per=[];cur=None
for k in sorted(b):
    v=b[k]
    if cur and k-cur['b']<=A.trou and abs(v[1]-cur['y0'])<=A.tol_y:cur['b']=k;cur['v'].append(v)
    else:cur={'a':k,'b':k,'y0':v[1],'v':[v]};per.append(cur)
per=[P for P in per if P['b']-P['a']+1>=A.min_images]  # variations passagères (transition, image parasite) ignorées
for P in per:
    vs=np.array(P['v']);P['y0']=int(np.median(vs[:,1]));P['y1']=int(np.median(vs[:,3]));ws=vs[:,2]-vs[:,0];cs=(vs[:,0]+vs[:,2])/2
    P['w']=int(np.clip(np.percentile(ws,95),60,W-60));P['cx']=A.centre if A.centre is not None else int(np.median(cs))
# réglages du découpage (max_mots, max_car, fusion_min…) dans rendu.blocs_karaoke, pas rendu.sous_titres (sinon rendu.py écrirait aussi les sous-titres classiques)
st=dict(f['rendu'].get('blocs_karaoke',{}));st.setdefault('mode','mots');cues=rendu.fabrique_cues(d,f,st,fps,N)
# sous-titre affiché moins de 0,5 s (coupé par le suivant) : fusionné avec le précédent si le texte reste court, sinon avec le suivant
cues=[list(c) for c in sorted(cues)];i=1
while i<len(cues):
    a,e,t=cues[i];aff=(cues[i+1][0] if i+1<len(cues) else e)-a
    if aff<0.5*fps and len(cues[i-1][2])+1+len(t)<=st.get('max_car',24)+6:cues[i-1][1]=e;cues[i-1][2]+=' '+t;del cues[i]
    elif aff<0.5*fps and i+1<len(cues):cues[i+1][0]=a;cues[i+1][2]=t+' '+cues[i+1][2];del cues[i]
    else:i+=1
F=police(A.taille,700);lw=lambda t:F.getlength(t)
txt={}
for a,e,t in cues:
    for k in range(a,e):txt[k]=t
# texte maintenu pendant les pauses (bloc toujours présent sur l'original)
last=None
for k in range(N):
    if k in txt:last=txt[k]
    elif last and k in b:txt[k]=last
blocs=[];out_cues=[]
for P in per:
    need=max([lw(txt[k]) for k in range(P['a'],P['b']+1) if k in txt] or [0])+2*A.marge_texte
    w=max(P['w']+2*A.marge,need);x0=int(max(2,P['cx']-w/2));x1=int(min(W-2,P['cx']+w/2));y0=P['y0']-A.marge;y1=P['y1']+A.marge
    k=P['a']
    while k<=P['b']:
        t=txt.get(k);j=k
        while j+1<=P['b'] and txt.get(j+1)==t:j+=1
        blocs.append({"images":[k,j],"lignes":[[t or '',[x0,y0,x1,y1]]],"taille":A.taille});k=j+1
# cues écrits = ce qui est affiché : un sous-titre reste jusqu'au suivant tant que la boîte d'origine est là (pauses comblées)
aff=[]
for i,(a,e,t) in enumerate(cues):
    fin=cues[i+1][0]-1 if i+1<len(cues) else e
    while e<fin and (e in b):e+=1
    aff.append([a,e,t])
json.dump({"blocs":blocs,"cues":aff},open(os.path.join(d,'blocs.json'),'w'),ensure_ascii=False)
print(f"{len(per)} périodes, {len(cues)} sous-titres, {len(blocs)} blocs")
for P in per:print(f"  {P['a']}-{P['b']} y {P['y0']}-{P['y1']} largeur orig {P['w']} centre {P['cx']}")
courts=[c for c in aff if c[1]-c[0]<0.5*fps];print('sous-titres < 0,5 s :',len(courts),courts[:5])
