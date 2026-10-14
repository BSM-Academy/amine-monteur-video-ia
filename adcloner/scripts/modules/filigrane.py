"""Repère le filigrane fixe d'une vidéo (logo ou texte semi-transparent toujours au même endroit, ex. « marque-x » en bas).
Usage : python3 filigrane.py <dossier> [--pas 6] [--seuil-presence 0.6] [--zone y0,y1]
Méthode : contours (gradient) de chaque image échantillonnée ; un pixel de filigrane a un contour présent sur presque toutes les images,
le reste de l'image change de plan en plan. Composante la plus persistante -> rectangle (+ 8 px). Images d'estimation : les 5 images
échantillonnées où le fond autour du rectangle est le plus uni. « sombre » : filigrane plus foncé que son fond sur ces images.
Écrit filigrane.json {rect, images, estimer_sur, sombre, seuil, presence} lu par rendu.py avec rendu.filigrane: "auto". (TEST marque X, 13/10/2026)"""
import json,os,sys,argparse,numpy as np
from scipy import ndimage
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import lire_images,analyse_json
p=argparse.ArgumentParser();p.add_argument('d');p.add_argument('--pas',type=int,default=6);p.add_argument('--seuil-presence',type=float,default=0.6);p.add_argument('--zone',default=None)
A=p.parse_args();d=A.d;an=analyse_json(d);W,H,N=an['largeur'],an['hauteur'],an['images']
acc=None;frames=[];ims=[]
for i,im in enumerate(lire_images(os.path.join(d,'src.mp4'))):
    if i%A.pas:continue
    g=im.astype(np.float32).mean(2);e=np.hypot(ndimage.sobel(g,0),ndimage.sobel(g,1))>40
    acc=e.astype(np.int32) if acc is None else acc+e;frames.append(i);ims.append(im)
pres=acc/len(frames)
if A.zone:
    y0,y1=map(int,A.zone.split(','));mz=np.zeros_like(pres,bool);mz[y0:y1]=True;pres=np.where(mz,pres,0)
m=pres>=A.seuil_presence;m=ndimage.binary_dilation(m,iterations=3);lab,k=ndimage.label(m)
if k==0:raise SystemExit("aucun filigrane fixe trouvé (aucun contour présent sur plus de %d %% des images)"%int(A.seuil_presence*100))
best=None
for j,s in enumerate(ndimage.find_objects(lab)):
    comp=(lab[s]==j+1);sc=(pres[s]*comp).sum()
    h=s[0].stop-s[0].start;w=s[1].stop-s[1].start
    if h>0.25*H or w>0.6*W:continue  # un décor fixe entier (cadre, bord) n'est pas un filigrane
    if best is None or sc>best[0]:best=(sc,s,comp)
if best is None:raise SystemExit("rien de la taille d'un filigrane")
sc,s,comp=best;x0,y0,x1,y1=max(0,s[1].start-8),max(0,s[0].start-8),min(W,s[1].stop+8),min(H,s[0].stop+8)
mask=np.zeros((H,W),bool);mask[s]=comp;mask=ndimage.binary_dilation(mask,iterations=2)
# images d'estimation : fond le plus uni autour du rectangle (anneau de 12 px), et contraste du filigrane sur ces images
ring=np.zeros((H,W),bool);ring[max(0,y0-12):min(H,y1+12),max(0,x0-12):min(W,x1+12)]=True;ring[y0:y1,x0:x1]=False
def alpha_une(im,sombre):
    """estimation de l'alpha du filigrane sur une image (même calcul que rendu.estime_alpha) -> part du rectangle au-dessus du seuil"""
    reg=im[y0:y1,x0:x1].astype(np.float32);bg=np.stack([ndimage.median_filter(reg[...,c],size=(13,13)) for c in range(3)],-1)
    den=np.clip(255-bg,20,None);w=255-bg;clair=(((reg-bg)/den)*w).sum(-1)/w.sum(-1)
    if sombre:clair=np.maximum(clair,((bg-reg)/np.clip(bg,20,None)).mean(-1))
    a=np.clip(clair,0,0.9);return float((a>=0.08).mean())
cands=[]
for i,im in zip(frames,ims):
    g=im.astype(np.float32).mean(2);cands.append((g[ring].std(),i,g[mask].mean()-g[ring].mean(),im))
sombre=bool(np.mean([c for _,_,c,_ in sorted(cands)[:10]])<0)
# fond uni (écart-type de l'anneau faible) ET masque fin : 3 à 30 % du rectangle (un masque plein noircit le remplissage)
notes=[]
for sd,i,c,im in cands:
    fr=alpha_une(im,sombre);notes.append((0 if 0.03<=fr<=0.30 else 1,sd,i,fr))
notes.sort();choisis=[]
for _,sd,i,fr in notes:
    if all(abs(i-j)>=A.pas for j in choisis):choisis.append(i)
    if len(choisis)==5:break
out={'rect':[int(x0),int(y0),int(x1),int(y1)],'images':[0,N-1],'estimer_sur':sorted(choisis),'sombre':sombre,'seuil':0.08,'presence':round(float(pres[mask].mean()),2)}
json.dump(out,open(os.path.join(d,'filigrane.json'),'w'))
print(f"filigrane : rect {out['rect']} ({x1-x0}x{y1-y0} px), présent sur {int(out['presence']*100)} % des images, {'sombre' if sombre else 'clair'} sur son fond, estimé sur {out['estimer_sur']} -> filigrane.json")
