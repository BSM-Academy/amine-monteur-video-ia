"""Bloc blanc fixe et centré qui cache les sous-titres d'origine (sans Vmake). Méthode validée par l'utilisateur le 08/10/2026 (SIL7, B8).
Usage : python3 blocs_fixes.py <dossier> --boites sub_boxes.json --rect y0,y1 --texte-y Y --taille T [--fin IMAGE] [--ignore a-b,c-d] [--majuscules] [--marge-orig 9] [--marge-texte 16] [--fusion 15]
Prérequis : un premier rendu (cues.json à jour) et le fichier des boîtes d'origine {image:[x0,y0,x1,y1]}.
Écrit dans fiche.json : un bloc blanc (même largeur partout) sur les plages où il faut cacher l'original ou afficher le texte, + le texte précédent maintenu dans les pauses. Garde les patches « interp » existants. Affiche les fuites (lettres d'origine hors du bloc)."""
import json,sys,os,argparse
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import police
p=argparse.ArgumentParser();p.add_argument('d');p.add_argument('--boites',required=True);p.add_argument('--rect',required=True);p.add_argument('--texte-y',type=int,required=True)
p.add_argument('--taille',type=int,required=True);p.add_argument('--fin',type=int,default=10**9);p.add_argument('--ignore',default='');p.add_argument('--majuscules',action='store_true')
p.add_argument('--marge-orig',type=int,default=9);p.add_argument('--marge-texte',type=int,default=16);p.add_argument('--fusion',type=int,default=15)
A=p.parse_args();d=A.d
f=json.load(open(os.path.join(d,'fiche.json')));R=f['rendu'];cues=json.load(open(os.path.join(d,'cues.json')))
W=json.load(open(os.path.join(d,'analyse.json')))['largeur'];C=W//2;y0,y1=map(int,A.rect.split(','))
ign=[tuple(map(int,r.split('-'))) for r in A.ignore.split(',') if r]
b={int(k):v for k,v in json.load(open(os.path.join(d,A.boites))).items() if int(k)<A.fin and not any(a<=int(k)<=e for a,e in ign)}
F=police(A.taille,700);U=(lambda t:t.upper()) if A.majuscules else (lambda t:t)
ho=max([max(C-v[0],v[2]-C)+A.marge_orig for v in b.values()] or [0]);ht=max(F.getlength(U(t))/2+A.marge_texte for a,e,t in cues)
hw=int(min(C,((max(ho,ht)+9)//10)*10))
txt={k:t for a,e,t in cues for k in range(a,e)}
show=sorted(k for k in set(b)|set(txt) if k<A.fin)
seg=[];cur=[show[0],show[0]]
for k in show[1:]:
    if k-cur[1]<=A.fusion:cur[1]=k
    else:seg.append(cur);cur=[k,k]
seg.append(cur)
P=[{"images":[s,e],"rect":[C-hw,y0,C+hw,y1],"remplir":[255,255,255],"lignes":[]} for s,e in seg]
for s,e in seg:
    miss=[k for k in range(s,e+1) if k not in txt];gs=[];c=[]
    for k in miss:
        if c and k-c[-1]>1:gs.append(c);c=[]
        c.append(k)
    if c:gs.append(c)
    for g in gs:
        pv=[q for q in cues if q[1]<=g[0]];nx=[q for q in cues if q[0]>g[-1]];t=pv[-1][2] if pv else nx[0][2]
        P.append({"images":[g[0],g[-1]],"rect":[0,0,1,1],"remplir":[255,255,255],"lignes":[{"texte":U(t),"x":C,"y":A.texte_y,"taille":A.taille,"graisse":700,"couleur":[0,0,0],"ancre":"mm"}]})
fuite=[k for k,v in b.items() if not any(q['images'][0]<=k<=q['images'][1] and q['rect'][0]<=v[0] and q['rect'][2]>=v[2] for q in P if q['rect'][2]>1)]
R['patches']=P+[q for q in R.get('patches',[]) if q.get('remplir')=='interp']
st=R['sous_titres'];st.update({"y":A.texte_y,"taille":A.taille,"couleur":[0,0,0],"couleur_ombre":[255,255,255],"flou":0,"trait":0,"decalage":[0,0]});st.pop('fond',None)
json.dump(f,open(os.path.join(d,'fiche.json'),'w'),ensure_ascii=False,indent=1)
print(f"bloc {2*hw} px (original {2*ho:.0f}, texte {2*ht:.0f}), {len(seg)} plage(s) {seg}, fuites en largeur : {len(fuite)} {fuite[:10]}")
