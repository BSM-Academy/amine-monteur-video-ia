"""Détecte les badges d'origine à recouvrir : étiquettes blanches à texte noir (DAY 1, WEEK 3…) et badges ronds de couleur (BUY 1 GET 1 FREE, MONEY BACK).
Usage : python3 badges.py <dossier> [--couleur 178,83,125] [--tol 30] [--sans-ronds] [--sans-blancs]
Lit <dossier>/src.mp4. Écrit badges.json (liste {id, type, images:[a,b], rect, rayon?, couleur?}) et badges_planche.jpg (une vignette par badge,
à regarder une fois pour écrire les textes). Dans la fiche : rendu.badges = {"B1": ["TAG 1"], "B3": ["3 KAUFEN", "2 GRATIS"], ...} (voir fiche.md) ;
rendu.py fabrique les patchs.
Blancs : composantes de pixels blancs (min RVB ≥ 225), 30-80 px de haut, 60-260 de large, remplissage ≥ 0,6, 2 à 40 % de pixels sombres (le texte).
Ronds : composantes de la couleur donnée (± tol), 100-240 px, à peu près carrées, remplissage 0,5-0,9 (le texte blanc fait des trous).
Un badge = même rectangle (± 6 px) et même texte sur des images consécutives (trous ≤ 3 images), au moins 6 images. Un texte qui change
(WEEK 1 -> WEEK 3 au même endroit) fait un nouveau badge. Seconde passe pour les blancs : un badge collé à une zone blanche (blouse, mur)
échappe aux composantes, on l'étend image par image par un test sur son rectangle. (TEST marque X, 13/10/2026)"""
import json,os,sys,argparse,numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import lire_images,analyse_json
p=argparse.ArgumentParser();p.add_argument('d');p.add_argument('--couleur',default='178,83,125');p.add_argument('--tol',type=int,default=30)
p.add_argument('--sans-ronds',action='store_true');p.add_argument('--sans-blancs',action='store_true');p.add_argument('--min-images',type=int,default=6)
A=p.parse_args();d=A.d;C=np.array([int(v) for v in A.couleur.split(',')]);an=analyse_json(d);W,H=an['largeur'],an['hauteur'];sc=W/720
SRC=os.path.join(d,'src.mp4')

def blancs(im):
    m=(im.min(2)>=225);lab,k=ndimage.label(m);out=[]
    for j,s in enumerate(ndimage.find_objects(lab)):
        h=s[0].stop-s[0].start;w=s[1].stop-s[1].start
        if not(30*sc<=h<=80*sc and 60*sc<=w<=260*sc):continue
        if (lab[s]==j+1).mean()<0.6:continue
        dark=(im[s].max(2)<80).mean()
        if dark<0.02 or dark>0.4:continue
        out.append([s[1].start,s[0].start,s[1].stop,s[0].stop])
    return out
def ronds(im):
    m=(np.abs(im.astype(int)-C).max(2)<=A.tol);m=ndimage.binary_closing(m,np.ones((5,5)));lab,k=ndimage.label(m);out=[]
    for j,s in enumerate(ndimage.find_objects(lab)):
        h=s[0].stop-s[0].start;w=s[1].stop-s[1].start
        if not(100*sc<=h<=240*sc and 100*sc<=w<=240*sc and 0.8<=w/h<=1.25):continue
        if not(0.5<=(lab[s]==j+1).mean()<=0.9):continue
        out.append([s[1].start,s[0].start,s[1].stop,s[0].stop])
    return out
def masque_texte(im,r):
    """pixels sombres à l'intérieur de la zone blanche du badge (cheveux ou décor sombres autour du badge ignorés)"""
    x0,y0,x1,y1=[int(v) for v in r];reg=im[y0:y1,x0:x1];aire=ndimage.binary_fill_holes(ndimage.binary_closing(reg.min(2)>=225,np.ones((5,5))))
    return (reg.max(2)<80)&aire
def cadre(m):
    ys,xs=np.where(m)
    return m[ys.min():ys.max()+1,xs.min():xs.max()+1] if len(ys) else m[:0,:0]
def meme_texte(m1,m2,tol=1):
    """même texte : masques recadrés sur leur texte (insensible au décalage du badge) ; un glyphe changé (WEEK 1 -> WEEK 3) se voit
    localement : sur une fenêtre de colonnes large comme la hauteur du texte, plus de 35 % des pixels diffèrent (à tol px près)"""
    m1=cadre(m1);m2=cadre(m2)
    if m1.size==0 or m2.size==0:return m1.size==m2.size
    if abs(m1.shape[0]-m2.shape[0])>3 or abs(m1.shape[1]-m2.shape[1])>max(4,0.06*max(m1.shape[1],m2.shape[1])):return False
    h=min(m1.shape[0],m2.shape[0]);w=min(m1.shape[1],m2.shape[1]);m1=m1[:h,:w];m2=m2[:h,:w];u=(m1|m2)
    if u.sum()==0:return True
    d1=ndimage.binary_dilation(m1,iterations=tol);d2=ndimage.binary_dilation(m2,iterations=tol);diff=(m1&~d2)|(m2&~d1)
    cd=np.convolve(diff.sum(0),np.ones(h),'same');cu=np.convolve(u.sum(0),np.ones(h),'same')
    return (cd/np.maximum(cu,1)).max()<0.35 and diff.sum()/u.sum()<0.12

class Piste:
    def __init__(s,typ,i,r,im):s.typ=typ;s.a=i;s.b=i;s.rs=[r];s.m=masque_texte(im,r);s.ex=None;s.pres=None
    def rect(s):return np.median(np.array(s.rs[-8:]),0)
    def rect_all(s):return np.median(np.array(s.rs),0).astype(int).tolist()
pistes=[]
def suivre(typ,i,rects,im):
    for r in rects:
        for P in pistes:
            if P.typ==typ and i-P.b<=3 and np.abs(np.array(r)-P.rect()).max()<=6*sc and (typ=='rond' or meme_texte(P.m,masque_texte(im,r))):
                P.b=i;P.rs.append(r);break
        else:pistes.append(Piste(typ,i,r,im))
for i,im in enumerate(lire_images(SRC)):
    if not A.sans_blancs:suivre('blanc',i,blancs(im),im)
    if not A.sans_ronds:suivre('rond',i,ronds(im),im)
    for P in pistes:
        if P.b==i and P.ex is None and len(P.rs)>=A.min_images//2:P.ex=im.copy()
pistes=[P for P in pistes if P.b-P.a+1>=A.min_images]
# doublons (deux composantes du même badge) : même type, rectangles à 8 px, plages qui se touchent, même texte
fusion=True
while fusion:
    fusion=False
    for P in pistes:
        for Q in pistes:
            if P is Q or P.typ!=Q.typ or np.abs(np.array(P.rect_all())-np.array(Q.rect_all())).max()>8*sc:continue
            chev=min(P.b,Q.b)-max(P.a,Q.a)+1  # deux badges ne peuvent pas occuper la même place en même temps : chevauchement = doublon
            if Q.a>P.b+3 or P.a>Q.b+3 or (chev<3 and P.typ=='blanc' and not meme_texte(P.m,Q.m)):continue
            if (Q.b-Q.a)>(P.b-P.a):P.m=Q.m
            P.a=min(P.a,Q.a);P.b=max(P.b,Q.b);P.rs+=Q.rs;P.ex=P.ex if P.ex is not None else Q.ex;pistes.remove(Q);fusion=True;break
        if fusion:break
# seconde passe (badges blancs) : extension image par image par un test sur le rectangle (blanc > 50 %, texte sombre 2-40 %, même texte)
if any(P.typ=='blanc' for P in pistes):
    for P in pistes:P.pres=set(range(P.a,P.b+1));P.fondu=set();P.r0=P.rect_all()
    for i,im in enumerate(lire_images(SRC)):
        for P in pistes:
            if P.typ!='blanc' or not (P.a-150<=i<P.a or P.b<i<=P.b+150):continue
            x0,y0,x1,y1=P.r0;reg=im[y0:y1,x0:x1];w=(reg.min(2)>=225).mean();dk=(reg.max(2)<80).mean()
            if w>0.5 and 0.02<=dk<=0.4 and meme_texte(P.m,masque_texte(im,P.r0)):P.pres.add(i)
            elif w>0.25 and dk>=0.005:P.fondu.add(i)  # badge en fondu (apparition ou disparition) : à couvrir aussi
    for P in pistes:
        if P.pres is None:continue
        a=P.a
        while any(a-k in P.pres for k in (1,2,3)):a-=1
        b=P.b
        while any(b+k in P.pres for k in (1,2,3)):b+=1
        autres=set().union(*[Q.pres for Q in pistes if Q is not P and Q.pres and np.abs(np.array(Q.r0)-np.array(P.r0)).max()<=12*sc]) if len(pistes)>1 else set()
        for _ in range(12):  # fondu : pas au-delà du badge voisin au même endroit (WEEK 1 -> WEEK 3)
            if a-1 in P.fondu and a-1 not in autres:a-=1
        for _ in range(12):
            if b+1 in P.fondu and b+1 not in autres:b+=1
        P.a,P.b=a,b
out=[]
for n,P in enumerate(sorted(pistes,key=lambda P:(P.a,P.rect_all()[1])),1):
    r=P.rect_all();e={'id':f'B{n}','type':P.typ,'images':[P.a,P.b],'rect':r}
    if P.typ=='rond':
        e['rayon']=int(round(max(r[2]-r[0],r[3]-r[1])/2));e['centre']=[(r[0]+r[2])//2,(r[1]+r[3])//2]
        if P.ex is not None:  # couleur réelle du badge (médiane des pixels de la couleur cherchée)
            reg=P.ex[r[1]:r[3],r[0]:r[2]].reshape(-1,3);sel=reg[np.abs(reg.astype(int)-C).max(1)<=A.tol];e['couleur']=np.median(sel,0).astype(int).tolist() if len(sel) else C.tolist()
    e['_ex']=P.ex;out.append(e)
# planche : une vignette par badge (zone du badge + marge)
tiles=[]
for e in out:
    ex=e.pop('_ex')
    if ex is None:continue
    x0,y0,x1,y1=e['rect'];mg=int(20*sc);th=160
    c=Image.fromarray(ex).crop((max(0,x0-mg),max(0,y0-mg),min(W,x1+mg),min(H,y1+mg)));tiles.append((e['id'],c.resize((int(c.width*th/c.height),th))))
if tiles:
    th=160;tw=max(t.width for _,t in tiles)+10;cols=min(8,len(tiles));rows=(len(tiles)+cols-1)//cols
    sh=Image.new('RGB',(cols*tw,rows*(th+22)),(40,40,40));dr=ImageDraw.Draw(sh)
    for k,(i,t) in enumerate(tiles):
        x=(k%cols)*tw;y=(k//cols)*(th+22);sh.paste(t,(x+5,y+20));dr.text((x+6,y+3),i,fill=(255,255,0))
    sh.save(os.path.join(d,'badges_planche.jpg'),quality=80)
json.dump(out,open(os.path.join(d,'badges.json'),'w'))
print(f"{len(out)} badge(s) -> badges.json"+(" + badges_planche.jpg (à regarder une fois)" if tiles else ""))
for e in out:print(f"  {e['id']} {e['type']:5s} images {e['images'][0]}-{e['images'][1]} rect {e['rect']}"+(f" rayon {e['rayon']} couleur {e.get('couleur')}" if e['type']=='rond' else ''))
