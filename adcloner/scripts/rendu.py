"""Rendu final piloté par la fiche : zones nettoyées par Vmake, remplacement de plans, filigrane, patchs, textes, blocs, sous-titres.
Usage : python3 rendu.py <dossier>
Entrées : src.mp4, fiche.json (section "rendu"), analyse.json, tts/, mix.wav, et si utilisé clean_vmake.mp4 + vmake_zones.json.
Sorties : <rendu.sortie> (vidéo sans son), cues.json, et le livrable <REF>_<LANGUE>_<RATIO>_v01.mp4 (vidéo + mix.wav).
Le format de la section "rendu" est décrit dans references/fiche.md."""
import json,os,re,subprocess,sys
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw,ImageFilter
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *

# ---------------------------------------------------------------- calques (petits tableaux RGBA + position)
class Calque:
    def __init__(self,im):
        a=np.array(im).astype(np.float32);ys,xs=np.where(a[...,3]>0)
        if len(ys)==0:self.arr=None;return
        self.y0,self.y1,self.x0,self.x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1;self.arr=a[self.y0:self.y1,self.x0:self.x1]
    def pose(self,a):
        if self.arr is None:return
        al=self.arr[...,3:4]/255;reg=a[self.y0:self.y1,self.x0:self.x1];reg[:]=reg*(1-al)+self.arr[...,:3]*al

# ---------------------------------------------------------------- émojis en couleur (police Apple Color Emoji)
EMOJI=re.compile('[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF][\uFE0F\u200D\U0001F3FB-\U0001F3FF\U0001F000-\U0001FAFF\u2600-\u27BF]*')
POLICE_EMOJI=['/System/Library/Fonts/Apple Color Emoji.ttc','/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf']
_emo={}
def morceaux(l):
    """découpe une ligne en [(est_emoji, texte)]"""
    r=[];i=0
    for m in EMOJI.finditer(l):
        if m.start()>i:r.append((False,l[i:m.start()]))
        r.append((True,m.group()));i=m.end()
    if i<len(l):r.append((False,l[i:]))
    return r
def image_emoji(s,h):
    s=re.sub('[\U0001F3FB-\U0001F3FF]','',s)  # couleur de peau retirée : sans libraqm, Pillow la dessine en carré à part
    if (s,h) not in _emo:
        from PIL import ImageFont
        p=next((c for c in POLICE_EMOJI if os.path.exists(c)),None)
        if not p:raise SystemExit("Police d'émojis introuvable")
        f=ImageFont.truetype(p,160 if 'Apple' in p else 109);bb=f.getbbox(s)
        im=Image.new('RGBA',(bb[2]+8,bb[3]+8),(0,0,0,0));ImageDraw.Draw(im).text((4,4),s,font=f,embedded_color=True)
        im=im.crop(im.getbbox());_emo[(s,h)]=im.resize((max(1,round(im.width*h/im.height)),h),Image.LANCZOS)
    return _emo[(s,h)]
def largeur_ligne(l,f,taille):
    return sum(image_emoji(t,int(taille*0.9)).width+taille*0.12 if e else f.getlength(t) for e,t in morceaux(l))

def ajuste(texte,largeur_max,taille,graisse,mini=18,nom=None):
    f=police(taille,graisse,nom)
    while largeur_ligne(texte,f,taille)>largeur_max and taille>mini:taille-=1;f=police(taille,graisse,nom)
    return f,taille

def texte_ombre(W,H,lignes,y,taille,graisse=700,couleur=(255,255,255),ombre=(0,0,0),decal=(1,2),flou=2.0,trait=3,x=None,interligne=1.08,largeur=590,police_nom=None,fond=None):
    x=W/2 if x is None else x
    f,taille=ajuste(max(lignes,key=len),largeur,taille,graisse,nom=police_nom)
    base=Image.new('RGBA',(W,H),(0,0,0,0));sh=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(base);ds=ImageDraw.Draw(sh)
    lh=int(taille*interligne);y0=y-lh*(len(lignes)-1)/2;emojis=[]
    bandeau=None
    if fond:  # bandeau coloré arrondi derrière le texte (sous-titres sur fond rouge, SO1 06/10/2026) : {couleur, marge_x, marge_y, rayon}
        lw=max(largeur_ligne(l,f,taille) for l in lignes);mx,my=fond.get('marge_x',14),fond.get('marge_y',8)
        hh=lh*len(lignes)-(lh-taille)+2*my;bandeau=Image.new('RGBA',(W,H),(0,0,0,0))
        ImageDraw.Draw(bandeau).rounded_rectangle([x-lw/2-mx,y-hh/2,x+lw/2+mx,y+hh/2],radius=fond.get('rayon',8),fill=(*fond.get('couleur',[139,19,19]),255))
    for n,l in enumerate(lignes):
        yy=y0+n*lh
        if not EMOJI.search(l):
            ds.text((x+decal[0],yy+decal[1]),l,font=f,fill=(*ombre,215),anchor='mm',stroke_width=trait,stroke_fill=(*ombre,215))
            d.text((x,yy),l,font=f,fill=(*couleur,255),anchor='mm');continue
        cx=x-largeur_ligne(l,f,taille)/2
        for e,t in morceaux(l):
            if e:
                im=image_emoji(t,int(taille*0.9));cx+=taille*0.06;emojis.append((im,(round(cx),round(yy-im.height/2))));cx+=im.width+taille*0.06
            else:
                ds.text((cx+decal[0],yy+decal[1]),t,font=f,fill=(*ombre,215),anchor='lm',stroke_width=trait,stroke_fill=(*ombre,215))
                d.text((cx,yy),t,font=f,fill=(*couleur,255),anchor='lm');cx+=f.getlength(t)
    for im,pos in emojis:base.alpha_composite(im,pos)
    sh=sh.filter(ImageFilter.GaussianBlur(flou))
    out=Image.alpha_composite(sh,base)
    if bandeau is not None:out=Image.alpha_composite(bandeau,out)
    return Calque(out)

def calque_blocs(W,H,lignes,taille=46):
    """un rectangle blanc arrondi par entrée ; le texte peut tenir sur plusieurs lignes ('\n') dans le même rectangle.
    Les rectangles réellement dessinés (élargis si le texte dépasse) sont gardés dans .rects pour le contrôle."""
    im=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(im);rects=[]
    for texte,r in lignes:
        ls=texte.split('\n');f,tl=ajuste(max(ls,key=lambda l:largeur_ligne(l,police(taille),taille)),W-24,taille,700,min(30,taille))
        tw=max(largeur_ligne(l,f,tl) for l in ls);x0,y0,x1,y1=r;cx=(x0+x1)/2
        if x1-x0<tw+36:x0=int(cx-(tw+36)/2);x1=int(cx+(tw+36)/2)
        x0=max(2,x0);x1=min(W-2,x1);rects.append([x0,y0,x1,y1])
        d.rounded_rectangle([x0,y0,x1,y1],radius=12,fill=(255,255,255,255));lh=(y1-y0)/len(ls)
        for k,l in enumerate(ls):
            yy=y0+lh*(k+0.5)+1
            if not EMOJI.search(l):d.text(((x0+x1)/2,yy),l,font=f,fill=(17,17,17,255),anchor='mm');continue
            px=(x0+x1)/2-largeur_ligne(l,f,tl)/2  # émojis en couleur, comme texte_ombre
            for e,t in morceaux(l):
                if e:em=image_emoji(t,int(tl*0.9));px+=tl*0.06;im.alpha_composite(em,(round(px),round(yy-em.height/2)));px+=em.width+tl*0.06
                else:d.text((px,yy),t,font=f,fill=(17,17,17,255),anchor='lm');px+=f.getlength(t)
    c=Calque(im);c.rects=rects;return c

def coupe(txt,max_car):
    if len(txt)<=max_car:return [txt]
    ws=txt.split();best=None
    if len(ws)<2:return [txt]  # un seul mot plus long que la ligne (« 360-Grad-Kreuzbandstruktur. », SO1) : la police est réduite par ajuste()
    for i in range(1,len(ws)):
        a,b=' '.join(ws[:i]),' '.join(ws[i:]);sc=abs(len(a)-len(b))+(6 if len(a)>max_car+4 or len(b)>max_car+4 else 0)
        if best is None or sc<best[0]:best=(sc,[a,b])
    return best[1]

# ---------------------------------------------------------------- sous-titres calés sur l'alignement de la voix
def mots_de(al):
    ch=al['characters'];st=al['character_start_times_seconds'];en=al['character_end_times_seconds'];out=[];cur='';s0=e0=None
    for c,a,b in zip(ch,st,en):
        if c==' ':
            if cur:out.append([cur,s0,e0]);cur='';s0=None
        else:
            if s0 is None:s0=a
            cur+=c;e0=b
    if cur:out.append([cur,s0,e0])
    r=[]  # ponctuation française isolée (« toile : », « 1950 ? », « 100 % ») rattachée au mot précédent
    for w in out:
        if r and re.fullmatch(r"[:;?!»…%€$]+",w[0]):r[-1][0]+=' '+w[0];r[-1][2]=w[2]
        else:r.append(w)
    return r

MOTS_OUTILS=set("le la les un une des de du mon ma mes ton ta tes son sa ses ce cet cette ces et ou à au aux en dans sur par pour avec sans the a an of to and".split())
def fabrique_cues(d,f,st,fps,N):
    ex=set(st.get('ids_exclus',[]));cues=[];mode=st.get('mode','phrase')
    if mode=='phrase':
        for l in f['lignes']:
            if l['id'] in ex:continue
            al=json.load(open(os.path.join(d,'tts',l['id']+'.json')));full=''.join(al['characters']);parts=st.get('scinder',{}).get(l['id']) or [full.strip()];pos=0
            for p in parts:
                j=full.index(p,pos);pos=j+len(p)
                cues.append([l['debut']+al['character_start_times_seconds'][j],l['debut']+al['character_end_times_seconds'][pos-1]+st.get('tenue',0.12),p])
    else:
        mots=[]
        for l in f['lignes']:
            if l['id'] in ex:continue
            al=json.load(open(os.path.join(d,'tts',l['id']+'.json')))
            for w in mots_de(al):mots.append([w[0],l['debut']+w[1],l['debut']+w[2]])
        chunks=[];cur=[]
        for w in mots:
            if cur and st.get('max_car_dur') and len(' '.join(x[0] for x in cur+[w]))>st['max_car_dur']:chunks.append(cur);cur=[]  # plafond dur : le mot passe au sous-titre suivant (mots composés allemands, SO1 11/10/2026)
            cur.append(w);txt=' '.join(x[0] for x in cur)
            if re.search(r"[,.:?!]$",w[0]):chunks.append(cur);cur=[]
            elif len(cur)>=st.get('max_mots',3) or len(txt)>=st.get('max_car',18):
                if len(cur)>1 and cur[-1][0].lower() in MOTS_OUTILS:chunks.append(cur[:-1]);cur=[cur[-1]]  # petit mot (article, préposition…) : passe au morceau suivant
                else:chunks.append(cur);cur=[]
        if cur:chunks.append(cur)
        cs=[[c[0][1],c[-1][2]+0.22,' '.join(x[0] for x in c)] for c in chunks];fusion=st.get('fusion_min',0.38)
        for c in cs:
            if cues and (c[1]-c[0]<fusion) and len(cues[-1][2])+len(c[2])<26:cues[-1][1]=c[1];cues[-1][2]+=' '+c[2]
            else:cues.append(c)
    cues.sort(key=lambda c:c[0])
    for a,b in zip(cues[:-1],cues[1:]):
        if a[1]>b[0]-0.03 or st.get('combler'):a[1]=b[0]-0.03  # combler : le sous-titre reste affiché pendant les pauses (bloc d'origine toujours visible, BL1 09/10/2026)
    if cues and st.get('combler'):cues[0][0]=0;cues[-1][1]=N/fps
    if cues:cues[-1][1]=min(cues[-1][1],N/fps-0.02)
    lim=st.get('images')
    out=[]
    for a,b,t in cues:
        a=round(a*fps);b=max(a+max(8,int(0.27*fps)),round(b*fps))
        if lim and not (lim[0]<=a<=lim[1]):continue
        if lim:b=min(b,lim[1])  # le dernier sous-titre s'arrête aussi à la fin de la plage (ex. avant une carte de fin)
        out.append([a,b,t])
    return out

# ---------------------------------------------------------------- filigrane
def estime_alpha(src,rect,indices,seuil,sombre=False):
    x0,y0,x1,y1=rect;ests=[];want=set(indices)
    for i,im in enumerate(lire_images(src)):
        if i in want:
            reg=im[y0:y1,x0:x1].astype(np.float32);bg=np.stack([ndimage.median_filter(reg[...,c],size=(13,13)) for c in range(3)],-1)
            den=np.clip(255-bg,20,None);w=255-bg;clair=(((reg-bg)/den)*w).sum(-1)/w.sum(-1)
            if sombre:clair=np.maximum(clair,((bg-reg)/np.clip(bg,20,None)).mean(-1))  # filigrane sombre (texte gris « marque-x », GL3E 12/10/2026) : on repère aussi ce qui assombrit le fond
            ests.append(clair)
        if i>max(want):break
    a=np.clip(np.mean(ests,0),0,0.9);a[a<seuil]=0;return a
def retire_filigrane(a,rect,alpha,rng,seuil):
    x0,y0,x1,y1=rect;reg=a[y0:y1,x0:x1].copy();m=ndimage.binary_dilation(alpha>seuil,iterations=2);w=(~m).astype(np.float32);out=reg.copy()
    for c in range(3):  # remplissage en cascade : là où aucun voisin propre n'est à portée (masque dense), on élargit (sinon intérieur noir, GL5B 13/10/2026)
        fill=reg[...,c].copy();done=~m
        for sg in (4,8,20,60):
            num=ndimage.gaussian_filter(reg[...,c]*w,sg);den=ndimage.gaussian_filter(w,sg);ok=(~done)&(den>0.05);fill[ok]=(num/np.clip(den,1e-3,None))[ok];done|=ok
        fill[~done]=np.median(reg[...,c][~m]) if (~m).any() else reg[...,c][~done]
        out[...,c]=np.where(m,fill,reg[...,c])
    hp=reg-np.stack([ndimage.uniform_filter(reg[...,c],5) for c in range(3)],-1);sd=hp[~m].std()
    out[m]+=rng.normal(0,sd,(m.sum(),3)).astype(np.float32);a[y0:y1,x0:x1]=np.clip(out,0,255)

# ---------------------------------------------------------------- zones nettoyées par Vmake
_FE={}
def masque(W,H,rects,e):
    cle=(tuple(map(tuple,rects)),e)
    if cle not in _FE:
        if len(_FE)>200:_FE.clear()
        m=np.zeros((H,W),np.float32)
        for x0,y0,x1,y1 in rects:m[max(0,y0):max(0,y1),max(0,x0):max(0,x1)]=1
        _FE[cle]=ndimage.gaussian_filter(m,e)[...,None]
    return _FE[cle]

def main():
    if len(sys.argv)<2:raise SystemExit(__doc__)
    d=sys.argv[1];f=fiche(d);R=f.get('rendu',{});an=analyse_json(d)
    W,H,fps,N=an['largeur'],an['hauteur'],an['fps'],an['images'];src=os.path.join(d,'src.mp4');vm=os.path.join(d,'clean_vmake.mp4')
    # --- remplacements de plans
    carte,longs=carte_remplacements(R)
    for a,b,n in longs:print(f"attention : plan {a}-{b} plus long que la matière ({n} images), dernière image tenue")
    donneurs={s for i,s in carte.items() if s!=i}
    # --- Vmake
    zv=R.get('zones_vmake');auto=None;manuel=[]
    if zv=='auto' or (isinstance(zv,dict) and zv.get('mode')=='auto'):
        zj=json.load(open(os.path.join(d,'vmake_zones.json')));auto=zj['zones'];conf=zv if isinstance(zv,dict) else {}
    elif zv:manuel=zv
    avec_vmake=bool(zv) and os.path.exists(vm)
    # --- filigrane
    fg=R.get('filigrane');alpha=None
    if fg=='auto' or (isinstance(fg,dict) and fg.get('mode')=='auto'):  # modules/filigrane.py
        pj=os.path.join(d,'filigrane.json')
        if not os.path.exists(pj):raise SystemExit("filigrane.json absent : lance d'abord modules/filigrane.py")
        fj=json.load(open(pj));fj.update({k:v for k,v in fg.items() if k!='mode'} if isinstance(fg,dict) else {});fg=fj
    if fg:alpha=estime_alpha(src,fg['rect'],fg['estimer_sur'],fg.get('seuil',0.06),fg.get('sombre',False))
    # --- calques
    sty=R.get('sous_titres');cues=fabrique_cues(d,f,sty,fps,N) if sty else []
    lb=R.get('blocs',[])
    if lb=='auto':  # sous-titres sur rectangles blancs préparés par blocs.py
        p=os.path.join(d,'blocs.json')
        if not os.path.exists(p):raise SystemExit("blocs.json absent : lance d'abord blocs.py")
        bj=json.load(open(p,encoding='utf-8'));lb=bj['blocs']
    json.dump(sorted(cues+(bj['cues'] if R.get('blocs')=='auto' else [])),open(os.path.join(d,'cues.json'),'w'),ensure_ascii=False)  # tous les sous-titres, pour controle.py
    cache={}
    def cal(cle,fabrique):
        if cle not in cache:
            if len(cache)>400:cache.clear()
            cache[cle]=fabrique()
        return cache[cle]
    def sub_calque(t):
        s=sty;lignes=coupe(t.upper() if s.get('majuscules') else t,s.get('max_car_ligne',30))
        return texte_ombre(W,H,lignes,s.get('y',int(H*0.8)),s.get('taille',36),s.get('graisse',700),tuple(s.get('couleur',[255,255,255])),tuple(s.get('couleur_ombre',[0,0,0])),tuple(s.get('decalage',[1,2])),s.get('flou',2.0),s.get('trait',3),interligne=s.get('interligne',1.28),largeur=s.get('largeur',600),police_nom=s.get('police'),fond=s.get('fond'))
    textes=[(t['images'][0],t['images'][1],t) for t in R.get('textes',[])]
    blocs=[(b['images'][0],b['images'][1],b) for b in lb];geom=[[] for _ in range(N)]
    patches=R.get('patches',[])+patches_badges(d,R)
    # --- première passe : mémoriser les images donneuses
    DS={};DV={}
    if donneurs:
        for i,(a,b) in enumerate(zip(lire_images(src),lire_images(vm) if avec_vmake else iter(lambda:None,1))):
            if i in donneurs:DS[i]=a.copy();DV[i]=None if b is None else b.copy()
            if i>max(donneurs):break
    # --- rendu
    sortie=os.path.join(d,R.get('sortie','rendu_video.mp4'))
    # encodeur : puce vidéo du Mac par défaut (h264_videotoolbox, 4 fois moins d'énergie, 30 % plus rapide, SSIM 0,989 à q 75, mesuré 13/10/2026) ; "x264" dans la fiche pour l'ancien libx264 preset slow
    # hors Mac (cloud Linux, 14/10/2026) : videotoolbox n'existe pas, libx264 automatiquement
    x264=R.get('encodeur')=='x264' or sys.platform!='darwin'
    enc=['-c:v','libx264','-crf',str(R.get('crf',17)),'-preset','slow'] if x264 else ['-c:v','h264_videotoolbox','-q:v',str(R.get('qualite',75))]
    wr=subprocess.Popen([FF,'-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(fps),'-i','-',*enc,'-pix_fmt','yuv420p',sortie],stdin=subprocess.PIPE)
    ia=lire_images(src);ib=lire_images(vm) if avec_vmake else None;rng=np.random.default_rng(7);fond_patch={}
    for o in range(N):
        try:ra=next(ia)
        except StopIteration:break
        rb=next(ib,None) if ib is not None else None
        s=carte.get(o,o)
        if s!=o:ra=DS[s];rb=DV.get(s)
        a=ra.astype(np.float32);b=rb.astype(np.float32) if rb is not None else None
        # zones Vmake
        if b is not None:
            if auto is not None:
                bx=auto.get(str(s),[])
                lim=conf.get('images')
                if lim and not (lim[0]<=o<=lim[1]):bx=[]
                if bx:
                    mg=conf.get('marge',14);rc=[[x0-mg,y0-mg,x1+mg,y1+mg] for x0,y0,x1,y1 in bx]
                    if conf.get('limite'):
                        L=conf['limite'];rc=[[max(x0,L[0]),max(y0,L[1]),min(x1,L[2]),min(y1,L[3])] for x0,y0,x1,y1 in rc if x1>L[0] and x0<L[2] and y1>L[1] and y0<L[3]]
                    if rc:
                        m=masque(W,H,rc,conf.get('adoucir',4)/2.5+2)
                        if conf.get('exclure'):m=m*(1-masque(W,H,conf['exclure'],1.5))  # zones où l'on garde la source (ex. émojis d'origine)
                        a=a*(1-m)+b*m
            for z in manuel:
                if z['images'][0]<=o<=z['images'][1]:
                    m=masque(W,H,[z['rect']],z.get('adoucir',12)/2.5);a=a*(1-m)+b*m
        # filigrane
        if fg and fg['images'][0]<=o<=fg['images'][1]:
            retire_filigrane(a,fg['rect'],alpha,rng,fg.get('seuil',0.06))
            if fg.get('remplacer_par'):cal(('fil',fg['remplacer_par']),lambda:fil_calque(W,H,fg)).pose(a)
        # patchs
        for k,p in enumerate(patches):
            if p['images'][0]<=o<=p['images'][1]:
                x0,y0,x1,y1=p['rect'];rem=p.get('remplir','median')
                if rem=='median':
                    if k not in fond_patch:fond_patch[k]=tuple(float(v) for v in np.median(a[p.get('echantillon',[y0,y0+10,x0,x1])[0]:p.get('echantillon',[y0,y0+10,x0,x1])[1],p.get('echantillon',[y0,y0+10,x0,x1])[2]:p.get('echantillon',[y0,y0+10,x0,x1])[3]].reshape(-1,3),axis=0))
                    rem=fond_patch[k]
                if rem=='interp':  # fond flou ou dégradé : interpolation verticale entre la ligne au-dessus et celle en dessous
                    t=np.linspace(0,1,y1-y0,dtype=np.float32)[:,None,None]
                    a[y0:y1,x0:x1]=ndimage.gaussian_filter(a[y0-4:y0,x0:x1].mean(0)*(1-t)+a[y1:y1+4,x0:x1].mean(0)*t,(0,8,0))
                elif p.get('rayon'):  # patch à coins arrondis (recouvre un bloc arrondi d'origine, BL1 09/10/2026)
                    if ('arr',k) not in fond_patch:
                        mk=Image.new('L',(x1-x0,y1-y0),0);ImageDraw.Draw(mk).rounded_rectangle([0,0,x1-x0-1,y1-y0-1],radius=p['rayon'],fill=255)
                        fond_patch[('arr',k)]=(np.asarray(mk,np.float32)/255)[...,None]
                    m=fond_patch[('arr',k)];a[y0:y1,x0:x1]=a[y0:y1,x0:x1]*(1-m)+np.array(rem,np.float32)*m
                else:a[y0:y1,x0:x1]=np.array(rem,np.float32)
                c=cal(('patch',k),lambda p=p:patch_calque(W,H,p));c.pose(a)
        # textes
        for a0,b0,t in textes:
            if a0<=o<=b0:
                c=cal(('txt',a0,tuple(t['lignes'])),lambda t=t:texte_ombre(W,H,t['lignes'],t['y'],t.get('taille',46),t.get('graisse',700),tuple(t.get('couleur',[255,255,255])),tuple(t.get('couleur_ombre',[0,0,0])),tuple(t.get('decalage',[1,2])),t.get('flou',2.0),t.get('trait',3),t.get('x'),t.get('interligne',1.08),t.get('largeur',590),t.get('police')));c.pose(a)
        for a0,b0,bl in blocs:
            if a0<=o<=b0:c=cal(('blocs',a0,json.dumps(bl['lignes'])),lambda bl=bl:calque_blocs(W,H,[(l[0],l[1]) for l in bl['lignes']],bl.get('taille',46)));c.pose(a);geom[o]+=c.rects
        for ca,cb,t in cues:
            if ca<=o<cb:cal(('sub',t),lambda t=t:sub_calque(t)).pose(a);break
        wr.stdin.write(np.clip(a,0,255).astype(np.uint8).tobytes())
    wr.stdin.close();wr.wait()
    lay=os.path.join(d,'layout.json')  # rectangles dessinés par image, pour le contrôle du texte d'origine visible
    if blocs:json.dump({'rects':geom},open(lay,'w'))
    elif os.path.exists(lay):os.remove(lay)  # reste d'un ancien rendu avec rectangles
    ratio=ratio_nom(W,H);nom=f"{f.get('ref','VIDEO')}_{f.get('langue_cible','fr').upper()}_{ratio}_v01.mp4"
    livrable=os.path.join(d,nom)
    if os.path.exists(os.path.join(d,'mix.wav')):
        subprocess.run([FF,'-v','error','-y','-i',sortie,'-i',os.path.join(d,'mix.wav'),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart','-shortest',livrable],check=True)
        print('livrable :',livrable)
    else:print("mix.wav absent : vidéo sans son écrite dans",sortie)

def patches_badges(d,R):
    """rendu.badges {id: [lignes] | {lignes, taille|tailles, couleur, couleur_fond, police}} + badges.json (modules/badges.py) -> patchs"""
    B=R.get('badges')
    if not B:return []
    pj=os.path.join(d,'badges.json')
    if not os.path.exists(pj):raise SystemExit("badges.json absent : lance d'abord modules/badges.py")
    bj={b['id']:b for b in json.load(open(pj))};out=[]
    for bid,v in B.items():
        if bid not in bj:raise SystemExit(f"badge {bid} inconnu dans badges.json ({', '.join(bj)})")
        b=bj[bid];v=v if isinstance(v,dict) else {'lignes':v};L=v.get('lignes',[]);x0,y0,x1,y1=b['rect'];cx,cy=(x0+x1)/2,(y0+y1)/2
        if not L or v.get('ignorer'):continue
        if b['type']=='blanc':
            t=v.get('taille',int((y1-y0)*0.42));ts=v.get('tailles',[t]*len(L));lh=t*1.15;p={'images':v.get('images',b['images']),'rect':b['rect'],'remplir':v.get('couleur_fond',[255,255,255]),'lignes':[]}
            for k,l in enumerate(L):p['lignes'].append({'texte':l,'x':cx,'y':cy+(k-(len(L)-1)/2)*lh,'taille':ts[k],'graisse':v.get('graisse',700),'couleur':v.get('couleur',[20,20,20]),'ancre':'mm','largeur':x1-x0-16,'police':v.get('police')})
        else:
            r=b['rayon'];t=v.get('taille',int(r*0.31));ts=v.get('tailles',[t]*len(L));lh=t*1.45;p={'images':v.get('images',b['images']),'rect':b['rect'],'rayon':r,'remplir':v.get('couleur_fond',b.get('couleur',[178,83,125])),'lignes':[]}
            for k,l in enumerate(L):p['lignes'].append({'texte':l,'x':cx,'y':cy+(k-(len(L)-1)/2)*lh,'taille':ts[k],'graisse':v.get('graisse',700),'couleur':v.get('couleur',[255,255,255]),'ancre':'mm','largeur':int(1.6*r),'police':v.get('police')})
        out.append(p)
    return out
def fil_calque(W,H,fg):
    c=texte_ombre(W,H,[fg['remplacer_par']],fg.get('y',(fg['rect'][1]+fg['rect'][3])//2),fg.get('taille',31),400,(255,255,255),(255,255,255),(0,0),0.01,0)
    if c.arr is not None:c.arr[...,3]*=fg.get('opacite',0.62)
    return c
def patch_calque(W,H,p):
    im=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(im)
    for l in p.get('lignes',[]):
        f,_=ajuste(l['texte'],l.get('largeur',10**6),l.get('taille',24),l.get('graisse',700),8,nom=l.get('police'))  # police : comme rendu.textes (ex. "DIN Condensed Bold.ttf")
        col=tuple(l.get('couleur',[20,20,20]))+(255,)
        if not EMOJI.search(l['texte']):d.text((l['x'],l['y']),l['texte'],font=f,fill=col,anchor=l.get('ancre','mm'));continue
        tl=f.size;parts=morceaux(l['texte']);tw=sum((image_emoji(t,int(tl*0.9)).width+tl*0.12) if e else f.getlength(t) for e,t in parts)  # émojis en couleur dans un patch (bouton « Link qui sotto 👇 », GL3E 12/10/2026), ancre mm
        px=l['x']-tw/2
        for e,t in parts:
            if e:em=image_emoji(t,int(tl*0.9));px+=tl*0.06;im.alpha_composite(em,(round(px),round(l['y']-em.height/2)));px+=em.width+tl*0.06
            else:d.text((px,l['y']),t,font=f,fill=col,anchor='lm');px+=f.getlength(t)
    return Calque(im)
if __name__=='__main__':main()
