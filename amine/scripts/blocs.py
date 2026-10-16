"""Sous-titres sur rectangles blancs, automatiques : un sous-titre français par sous-titre d'origine (même moment, même rectangle).
Usage : python3 blocs.py <dossier> [--redetecter]
Entrées : src.mp4, analyse.json, fiche.json (lignes, rendu.remplacements, rendu.blocs_auto), tts/*.json.
Sorties : blocs_src.json (détection image par image, gardée en cache), blocs.json (blocs + sous-titres), lu par rendu.py quand la fiche a "blocs": "auto".
Réglages facultatifs dans la fiche, rendu.blocs_auto : {taille, max_car, forcer:[{images:[a,b], rect:[x0,y0,x1,y1], lignes:1|2}]}.
La détection repère les lettres sombres entourées de blanc (le texte du sous-titre), puis mesure le rectangle autour :
elle marche aussi quand le fond de l'image est clair et se confond avec le rectangle."""
import json,os,re,sys
import numpy as np
from scipy import ndimage
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *

VERSION_DETECTION=1

# ---------------------------------------------------------------- détection dans une image
def detecte(a,avec_lettres=False):
    """rectangles de sous-titre d'une image : [{'l':[[gx0,gy0,gx1,gy1,pg,ph,pd,pb],...] par ligne, 'g':nb de lettres}]
    g* = boîte des lettres ; p* = marge blanche mesurée à gauche, en haut, à droite, en bas (-1 = pas de bord : fond clair).
    avec_lettres : renvoie aussi chaque lettre [x0,y0,x1,y1] (pour le contrôle)"""
    H,W=a.shape[:2];white=a.min(2)>225;dark=a.max(2)<110
    trous=ndimage.binary_fill_holes(white)&~white  # ce qui est entièrement entouré de blanc : les lettres
    lab,_=ndimage.label(trous);lettres=[]
    for k,s in enumerate(ndimage.find_objects(lab),1):
        h=s[0].stop-s[0].start;w=s[1].stop-s[1].start
        if not (0.006*H<=h<=0.04*H and w<=0.35*W):continue
        m=lab[s]==k
        if m.sum()<6 or (dark[s]&m).sum()<0.3*m.sum():continue
        lettres.append([s[1].start,s[0].start,s[1].stop,s[0].stop])
    if not lettres:return ([],[]) if avec_lettres else []
    toutes_lettres=[list(map(int,r)) for r in lettres]
    # lettres -> lignes : d'abord par hauteur (chevauchement vertical), puis coupe aux grands écarts horizontaux
    lettres.sort(key=lambda r:(r[1]+r[3])/2);rangs=[]
    for r in lettres:
        R=rangs[-1] if rangs else None
        if R and min(R[1],r[3])-max(R[0],r[1])>=0.5*min(R[1]-R[0],r[3]-r[1]):R[2].append(r);R[0]=min(R[0],r[1]);R[1]=max(R[1],r[3])
        else:rangs.append([r[1],r[3],[r]])
    lignes=[]
    for _,_,rs in rangs:
        rs.sort(key=lambda r:r[0]);L=None
        for r in rs:
            if L and r[0]-L[2]<0.06*W:L[0]=min(L[0],r[0]);L[1]=min(L[1],r[1]);L[2]=max(L[2],r[2]);L[3]=max(L[3],r[3]);L[4]+=1
            else:L=[*r,1];lignes.append(L)
    lignes=[L for L in lignes if L[4]>=2 and L[2]-L[0]>=0.05*W]
    # marge blanche autour de chaque ligne
    out=[]
    for x0,y0,x1,y1,n in lignes:
        hg=y1-y0;cap_x=int(max(0.06*W,2*hg));cap_y=int(1.2*hg);bande=white[y0:y1];pl=pr=pt=pb=-1
        for p in range(1,cap_x):
            if x0-p<0 or bande[:,x0-p].mean()<0.9:pl=p-1;break
        for p in range(1,cap_x):
            if x1-1+p>=W or bande[:,x1-1+p].mean()<0.9:pr=p-1;break
        for p in range(1,cap_y):
            if y0-p<0 or white[y0-p,x0:x1].mean()<0.9:pt=p-1;break
        for p in range(1,cap_y):
            if y1-1+p>=H or white[y1-1+p,x0:x1].mean()<0.9:pb=p-1;break
        out.append([int(v) for v in (x0,y0,x1,y1,pl,pt,pr,pb,n)])
    # lignes voisines -> un même sous-titre (2 lignes empilées)
    out.sort(key=lambda L:L[1]);blocs=[]
    for L in out:
        B=blocs[-1] if blocs else None
        if B:
            P=B['l'][-1];hg=P[3]-P[1]
            if 0<=L[1]-P[3]<=1.6*hg and min(P[2],L[2])>max(P[0],L[0]):B['l'].append(L[:8]);B['g']+=L[8];continue
        blocs.append({'l':[L[:8]],'g':L[8]})
    return (blocs,toutes_lettres) if avec_lettres else blocs

# ---------------------------------------------------------------- d'une image à un rectangle de sous-titre
def rect_image(blocs,marges):
    """le sous-titre principal de l'image (le plus de lettres) -> (rect [x0,y0,x1,y1], nb de lignes, hauteur des lettres)"""
    if not blocs:return None
    B=max(blocs,key=lambda b:b['g']);rs=[]
    for x0,y0,x1,y1,*p in B['l']:
        p=[v if v>=0 else marges[k] for k,v in enumerate(p)]
        rs.append([x0-p[0],y0-p[1],x1+p[2],y1+p[3]])
    return [min(r[0] for r in rs),min(r[1] for r in rs),max(r[2] for r in rs),max(r[3] for r in rs)],len(rs),float(np.median([L[3]-L[1] for L in B['l']]))

PETITS=set("le la les un une des de du d' l' mon ma mes ton ta tes son sa ses ce cet cette ces et ou à au aux en dans sur par pour avec sans que qui ne se tu je tout toute tous toutes très".split())
def finit_ponct(m):return re.search(r"[,.:;?!…]$",m)
def petit(m):  # mot qui ne finit ni un sous-titre ni une ligne : article, préposition… ou nombre (« 24 » reste avec « mois »)
    m=m.lower();return m.strip(",.:;?!…") in PETITS or m.endswith(("d'","l'","qu'","j'")) or bool(re.fullmatch(r"\d+([.,]\d+)?",m))

def deux_lignes(txt):
    ws=txt.split();best=None
    if len(ws)<=3:return txt  # texte court : une seule ligne (jamais un mot seul sur une ligne)
    for i in range(1,len(ws)):
        a,b=' '.join(ws[:i]),' '.join(ws[i:])
        sc=abs(len(a)-len(b))+(40 if petit(ws[i-1]) else 0)+(-6 if finit_ponct(ws[i-1]) else 0)+(40 if i==1 or i==len(ws)-1 else 0)
        if best is None or sc<best[0]:best=(sc,a+'\n'+b)
    return best[1] if best else txt

def main():
    args=[a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:raise SystemExit(__doc__)
    d=args[0];f=fiche(d);an=analyse_json(d);R=f.get('rendu',{});cfg=R.get('blocs_auto',{})
    W,H,fps,N=an['largeur'],an['hauteur'],an['fps'],an['images'];ech=W/720
    # 1) détection image par image (en cache)
    cache=os.path.join(d,'blocs_src.json')
    if not os.path.exists(cache) or '--redetecter' in sys.argv or json.load(open(cache)).get('version')!=VERSION_DETECTION:
        det=[detecte(im) for im in lire_images(os.path.join(d,'src.mp4'))];json.dump({'version':VERSION_DETECTION,'images':det},open(cache,'w'))
    det=json.load(open(cache))['images']
    toutes=[L for x in det for b in x for L in b['l']]
    marges=[int(np.median([L[4+k] for L in toutes if L[4+k]>=0] or [round(10*ech)])) for k in range(4)]
    # 2) remplacements de plans : une image donneuse apporte son propre sous-titre d'origine
    carte,_=carte_remplacements(R)
    par_image=[rect_image(det[carte.get(i,i)] if carte.get(i,i)<len(det) else [],marges) for i in range(N)]
    # 3) sous-titres d'origine stables (tolérance de quelques px, variations de moins de 8 images ignorées)
    tx,ty=6*ech,8*ech;segs=[]
    for i,v in enumerate(par_image):
        if not v:continue
        r,n,hg=v;s=segs[-1] if segs else None
        if s and i-s['b']<=3 and s['n']==n and all(abs(s['r'][k]-r[k])<=(tx if k%2==0 else ty) for k in range(4)):
            s['b']=i;s['rs'].append(r);s['hg'].append(hg)
        else:segs.append({'a':i,'b':i,'n':n,'r':r,'rs':[r],'hg':[hg]})
    segs=[s for s in segs if len(s['rs'])>=8];fus=[]
    for s in segs:
        p=fus[-1] if fus else None
        if p and s['a']-p['b']<=12 and p['n']==s['n'] and all(abs(np.median([r[k] for r in p['rs']])-np.median([r[k] for r in s['rs']]))<=(tx if k%2==0 else ty) for k in range(4)):
            p['b']=s['b'];p['rs']+=s['rs'];p['hg']+=s['hg']
        else:fus.append(s)
    lim=cfg.get('images')
    if lim:segs=[dict(s,a=max(s['a'],lim[0]),b=min(s['b'],lim[1])) for s in fus if s['b']>=lim[0] and s['a']<=lim[1]]
    else:segs=fus
    m3=round(3*ech)
    for s in segs:
        rs=np.array(s['rs']);s['rect']=[max(0,int(rs[:,0].min())-m3),max(0,int(rs[:,1].min())-m3),min(W,int(rs[:,2].max())+m3),min(H,int(rs[:,3].max())+m3)];s['hg']=float(np.median(s['hg']))
    # 4) forçages de la fiche (plan où la détection échoue)
    F=[{'a':x['images'][0],'b':x['images'][1],'n':x.get('lignes',1),'rect':x['rect'],'hg':None,'force':True} for x in cfg.get('forcer',[])]
    segs=[s for s in segs if not any(x['a']<=s['b'] and s['a']<=x['b'] for x in F)]+F;segs.sort(key=lambda s:s['a'])
    for s,t in zip(segs[:-1],segs[1:]):  # trou court (transition) : chaque image va au sous-titre auquel elle ressemble
        if t['a']-s['b']<=12:
            if s.get('force') or t.get('force'):s['b']=t['a']-1;continue
            ecart=lambda r,q:abs(r[0]-q[0])+abs(r[2]-q[2])+abs(r[1]-q[1])+abs(r[3]-q[3])
            bascule=next((i for i in range(s['b']+1,t['a']) if par_image[i] and ecart(par_image[i][0],t['rect'])<ecart(par_image[i][0],s['rect'])),t['a'])
            s['b']=bascule-1;t['a']=bascule
    if not segs:raise SystemExit("aucun sous-titre sur rectangle blanc détecté : vérifier la vidéo, ou utiliser rendu.blocs à la main")
    hg_ref=float(np.median([s['hg'] for s in segs if s['hg']]))
    if not cfg.get('taille'):  # taille de police dont les lettres (avec jambages) ont la hauteur des lettres d'origine
        b=police(100).getbbox('dlpqg');taille_auto=max(14,round(hg_ref*100/(b[3]-b[1])))
    # 5) mots de la voix française, en temps absolu
    from rendu import mots_de
    mots=[]
    for l in f['lignes']:
        al=json.load(open(os.path.join(d,'tts',l['id']+'.json')))
        for w in mots_de(al):mots.append([w[0],l['debut']+w[1],l['debut']+w[2],l['id']])
    def seg_de(t):
        fr=t*fps
        for k,s in enumerate(segs):
            if s['a']<=fr<s['b']+1:return k
        k=min(range(len(segs)),key=lambda k:min(abs(fr-segs[k]['a']),abs(fr-segs[k]['b'])))
        return k if min(abs(fr-segs[k]['a']),abs(fr-segs[k]['b']))<=0.5*fps else None  # loin de tout rectangle d'origine : pas un sous-titre en rectangle
    G=[[] for _ in segs];hors=[]
    for w in mots:
        k=seg_de((w[1]+w[2])/2)
        if k is None:hors.append(w)
        else:G[k].append(w)
    ks=[k for k in range(len(segs)) if G[k]]
    for k,k2 in zip(ks[:-1],ks[1:]):  # un sous-titre ne finit pas sur un petit mot
        g,n=G[k],G[k2]
        while len(g)>1 and petit(g[-1][0]) and not finit_ponct(g[-1][0]):n.insert(0,g.pop())
    for k,k2 in zip(ks[:-1],ks[1:]):  # coupure déplacée sur une ponctuation proche (3 mots au plus), dans la même phrase
        g,n=G[k],G[k2]
        if not g or not n or finit_ponct(g[-1][0]):continue
        j=next((j for j in range(len(g)-2,max(-1,len(g)-5),-1) if finit_ponct(g[j][0])),None)
        if j is not None:n[:0]=g[j+1:];del g[j+1:];continue
        j=next((j for j in range(min(3,len(n)-1)) if finit_ponct(n[j][0])),None)
        if j is not None and n[j][3]==g[-1][3]:g.extend(n[:j+1]);del n[:j+1]
    # 6) sous-titre trop long pour son rectangle : deux sous-titres successifs sur le même rectangle
    mc=cfg.get('max_car',30);S2=[];G2=[];k=0;todo=list(zip(segs,G))
    while todo:
        s,g=todo.pop(0);txt=' '.join(w[0] for w in g)
        if g and len(txt)>mc*s['n']+4 and s['b']-s['a']>=2*fps*0.8 and len(g)>=4:
            c=[j for j in range(2,len(g)-1) if finit_ponct(g[j-1][0])] or [j for j in range(2,len(g)-1) if not petit(g[j-1][0])] or [len(g)//2]
            j=min(c,key=lambda j:abs(len(' '.join(w[0] for w in g[:j]))-len(' '.join(w[0] for w in g[j:]))))
            cut=int(max(s['a']+0.8*fps,min(s['b']-0.8*fps,round(g[j][1]*fps))))
            s1=dict(s,b=cut-1);s2=dict(s,a=cut);todo[:0]=[(s1,g[:j]),(s2,g[j:])];continue
        S2.append(s);G2.append(g)
    segs,G=S2,G2
    # 7) blocs et sous-titres
    blocs=[];cues=[];vides=[];ignores=[];taille=cfg.get('taille')
    for k,(s,g) in enumerate(zip(segs,G)):
        if g:txt=' '.join(w[0] for w in g)
        else:  # rectangle d'origine sans voix française : on prolonge le sous-titre voisin le plus proche
            voisins=[j for j in range(len(segs)) if G[j] and min(abs(segs[j]['a']-s['b']),abs(segs[j]['b']-s['a']))<=12]
            if not voisins:ignores.append((s['a'],s['b']));continue
            j=min(voisins,key=lambda j:min(abs(segs[j]['a']-s['b']),abs(segs[j]['b']-s['a'])));txt=' '.join(w[0] for w in G[j]);vides.append((s['a'],s['b']))
        txt=deux_lignes(txt) if s['n']>=2 else txt
        t=taille or taille_auto
        blocs.append({'images':[s['a'],s['b']],'lignes':[[txt,s['rect']]],'taille':t})
        if g:cues.append([s['a'],s['b']+1,txt.replace('\n',' ')])
    json.dump({'blocs':blocs,'cues':cues},open(os.path.join(d,'blocs.json'),'w'),ensure_ascii=False,indent=0)
    aff=sum(len(g) for g in G)
    print(f"{len(blocs)} sous-titres sur rectangle blanc ({len(F)} forcé(s)), mots de la voix : {len(mots)}, affichés : {aff}"+("" if aff==len(mots) else "  <-- ÉCART"))
    if hors:print(f"ATTENTION {len(hors)} mot(s) de la voix loin de tout rectangle d'origine, non affichés ici (lignes {sorted({w[3] for w in hors})}) : sous-titres classiques pour ces lignes, ou vidéo qui n'a pas de sous-titres en rectangle")
    if vides:print(f"rectangles d'origine sans voix, sous-titre voisin prolongé : {vides}")
    if ignores:print(f"ATTENTION rectangles d'origine loin de toute voix, laissés tels quels (carte de fin ? sinon rendu.blocs_auto.forcer) : {ignores}")
    for b in blocs:print(f"  {b['images'][0]:5d}-{b['images'][1]:5d} {b['images'][0]/fps:6.2f}s {b['lignes'][0][1]} t{b['taille']} {b['lignes'][0][0]!r}")
    print("Dans la fiche : rendu.blocs = \"auto\" (rendu.py lit blocs.json). Contrôle : controle.py signale tout texte d'origine visible.")
if __name__=='__main__':main()
