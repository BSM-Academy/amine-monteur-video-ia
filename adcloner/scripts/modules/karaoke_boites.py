"""Boîtes des sous-titres karaoké d'origine (texte blanc, mot courant surligné dans un rectangle de couleur), image par image, sans Vmake.
Usage : python3 karaoke_boites.py <dossier> [--rose r,g,b] [--tol 24] [--haut 44,64] [--large 40,240] [--sortie boites_src.json]
Lit <dossier>/src.mp4. Pour chaque image : composantes connexes de la couleur du surlignage (±tol), garde celle qui a la forme du
rectangle (hauteur et largeur dans les bornes, remplissage 0,45-0,85 : le texte blanc fait des trous), prend ses lignes comme bande
du sous-titre, puis étend la bande en largeur sur les pixels blancs (min ≥ 225) contigus (trous ≤ 22 px).
Sans surlignage : garde la boîte précédente si la bande contient encore du texte blanc. Écrit {image:[x0,y0,x1,y1]} (GL3E, 12/10/2026)."""
import json,os,sys,argparse,numpy as np
from scipy import ndimage
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import lire_images
p=argparse.ArgumentParser();p.add_argument('d');p.add_argument('--rose',default='186,96,124');p.add_argument('--tol',type=int,default=24)
p.add_argument('--haut',default='44,64');p.add_argument('--large',default='40,240');p.add_argument('--sortie',default='boites_src.json')
A=p.parse_args();R=np.array([int(v) for v in A.rose.split(',')]);h0,h1=map(int,A.haut.split(','));w0,w1=map(int,A.large.split(','))
out={};prev=None;n=0;K=np.ones((3,3))
for im in lire_images(os.path.join(A.d,'src.mp4')):
    a=im.astype(int);m=ndimage.binary_closing(np.abs(a-R).max(2)<=A.tol,K);H,W=m.shape;lab,k=ndimage.label(m);best=None;box=None
    for i,s in enumerate(ndimage.find_objects(lab)):
        h=s[0].stop-s[0].start;w=s[1].stop-s[1].start
        if not(h0<=h<=h1 and w0<=w<=w1):continue
        area=int((lab[s]==i+1).sum());fill=area/(h*w)
        if not(0.45<=fill<=0.85):continue
        if best is None or area>best[0]:best=(area,s)
    if best:
        s=best[1];y0,y1=s[0].start,s[0].stop-1;px0,px1=s[1].start,s[1].stop-1
        w=(a[y0:y1+1].min(2)>=225)|m[y0:y1+1];col=w.sum(0)>=2
        x0=px0;gap=0
        for x in range(px0-1,-1,-1):
            if col[x]:x0=x;gap=0
            else:
                gap+=1
                if gap>22:break
        x1=px1;gap=0
        for x in range(px1+1,W):
            if col[x]:x1=x;gap=0
            else:
                gap+=1
                if gap>22:break
        box=[int(x0),int(y0),int(x1),int(y1)]
    elif prev is not None:
        x0,y0,x1,y1=prev
        if (a[y0:y1+1,x0:x1+1].min(2)>=225).sum()>=60:box=prev
    if box:out[n]=box;prev=box
    else:prev=None
    n+=1
json.dump(out,open(os.path.join(A.d,A.sortie),'w'))
print(f"{len(out)} images avec sous-titre sur {n}")
