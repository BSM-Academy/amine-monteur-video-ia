"""Outils communs aux scripts AdCloner : ffmpeg, lecture d'images, polices, fiche vidéo, clé ElevenLabs."""
import glob,json,os,re,shutil,subprocess,sys
import numpy as np

def _binaire(p):
    """vrai exécutable (et non un petit script Python qui l'appelle, lent et bavard)"""
    try:
        with open(p,'rb') as fh:return fh.read(2)!=b'#!'
    except Exception:return False
def ffmpeg():
    for base in sys.path:
        for c in glob.glob(os.path.join(base,'static_ffmpeg','bin','*','ffmpeg')):
            if _binaire(c):return c
    p=shutil.which('ffmpeg')
    if p and _binaire(p):return p
    try:
        import imageio_ffmpeg;return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        if p:return p
        raise SystemExit("ffmpeg introuvable : installe ffmpeg, ou 'python3 -m pip install imageio-ffmpeg'")
FF=ffmpeg()

def probe(path):
    """dimensions, cadence, durée, présence d'audio (lus dans la sortie de ffmpeg -i)"""
    s=subprocess.run([FF,'-hide_banner','-i',path],capture_output=True,text=True).stderr
    d=re.search(r'Duration: (\d+):(\d+):([\d.]+)',s);dur=int(d[1])*3600+int(d[2])*60+float(d[3]) if d else 0.0
    v=re.search(r'Video:.*?(\d{2,5})x(\d{2,5})',s);f=re.search(r'(\d+(?:\.\d+)?) fps',s)
    return {'largeur':int(v[1]),'hauteur':int(v[2]),'fps':float(f[1]) if f else 30.0,'duree':dur,'audio':'Audio:' in s}

def lire_images(path,vf=None,w=None,h=None):
    """génère les images (h,w,3) uint8 d'une vidéo, éventuellement après un filtre ffmpeg"""
    if w is None:
        p=probe(path);w,h=p['largeur'],p['hauteur']
    cmd=[FF,'-v','error','-i',path]+(['-vf',vf] if vf else [])+['-f','rawvideo','-pix_fmt','rgb24','-']
    pr=subprocess.Popen(cmd,stdout=subprocess.PIPE);n=w*h*3
    try:
        while True:
            raw=pr.stdout.read(n)
            if len(raw)<n:break
            yield np.frombuffer(raw,np.uint8).reshape(h,w,3)
    finally:
        pr.stdout.close();pr.wait()

def nb_images(path):
    r=subprocess.run([FF,'-v','error','-i',path,'-map','0:v:0','-f','null','-','-progress','-'],capture_output=True,text=True)
    m=re.findall(r'^frame=(\d+)',r.stdout,re.M);return int(m[-1]) if m else 0

def fiche(dossier):
    p=os.path.join(dossier,'fiche.json')
    if not os.path.exists(p):raise SystemExit(f"fiche.json introuvable dans {dossier} (voir references/fiche.md)")
    return json.load(open(p,encoding='utf-8'))
def sauve_fiche(dossier,f):json.dump(f,open(os.path.join(dossier,'fiche.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
def analyse_json(dossier):
    p=os.path.join(dossier,'analyse.json')
    if not os.path.exists(p):raise SystemExit("analyse.json introuvable : lance d'abord analyse.py")
    return json.load(open(p,encoding='utf-8'))

def cle_groq():
    """clé Groq (Whisper dans le cloud) : variable GROQ_API_KEY, sinon ~/.config/groq/.env ou ~/.config/watch/.env ; None si absente"""
    k=os.environ.get('GROQ_API_KEY')
    if k:return k
    for f in ('~/.config/groq/.env','~/.config/watch/.env'):
        f=os.path.expanduser(f)
        if os.path.exists(f):
            for l in open(f):
                m=re.match(r'\s*(?:export\s+)?GROQ_API_KEY=["\']?([^"\'\s]+)',l)
                if m:return m.group(1)
    return None

def cle_replicate():
    """clé Replicate (demucs dans le cloud) : variable REPLICATE_API_TOKEN, sinon ~/.config/replicate/.env ; None si absente"""
    k=os.environ.get('REPLICATE_API_TOKEN')
    if k:return k
    f=os.path.expanduser('~/.config/replicate/.env')
    if os.path.exists(f):
        for l in open(f):
            m=re.match(r'\s*(?:export\s+)?REPLICATE_API_TOKEN=["\']?([^"\'\s]+)',l)
            if m:return m.group(1)
    return None

def cle_elevenlabs():
    k=os.environ.get('ELEVENLABS_API_KEY')
    if k:return k
    z=os.path.expanduser('~/.zshrc')
    if os.path.exists(z):
        for l in open(z,encoding='utf-8',errors='ignore'):
            m=re.match(r'\s*(?:export\s+)?ELEVENLABS_API_KEY=["\']?([^"\'\s]+)',l)
            if m:return m[1]
    raise SystemExit("Clé ElevenLabs absente : définis la variable d'environnement ELEVENLABS_API_KEY")

FONTS_DEPOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','fonts')  # polices livrées avec le dépôt dépôt (14/10/2026)
SERIF=['~/Library/Fonts/Georgia Bold.ttf','/System/Library/Fonts/Supplemental/Georgia Bold.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf']
def chemin_police(nom=None):
    """nom : None (Space Grotesk), "serif" (Georgia Bold), un chemin, ou un nom de fichier cherché dans les dossiers de polices"""
    if nom:
        cands=SERIF if nom=='serif' else [nom]+[os.path.join(d,nom) for d in (FONTS_DEPOT,'~/Library/Fonts','/Library/Fonts','/System/Library/Fonts','/System/Library/Fonts/Supplemental','~/.local/share/fonts')]
        for c in cands:
            p=os.path.expanduser(c)
            if os.path.exists(p):return p
        raise SystemExit(f"Police introuvable : {nom}")
    for c in [os.path.join(FONTS_DEPOT,'SpaceGrotesk.ttf'),'~/Library/Fonts/SpaceGrotesk.ttf','/Library/Fonts/SpaceGrotesk.ttf','~/.fonts/SpaceGrotesk.ttf','~/.local/share/fonts/SpaceGrotesk.ttf',
              '/System/Library/Fonts/Supplemental/Arial Bold.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']:
        p=os.path.expanduser(c)
        if os.path.exists(p):return p
    raise SystemExit("Police introuvable : installe Space Grotesk (Google Fonts)")
def police(taille,graisse=700,nom=None):
    from PIL import ImageFont
    idx=0
    if nom and '#' in nom:nom,idx=nom.rsplit('#',1);idx=int(idx)  # style d'une police .ttc, ex. "Avenir Next Condensed.ttc#9"
    f=ImageFont.truetype(chemin_police(nom),int(taille),index=idx)
    try:  # police variable : régler l'axe Weight par son nom (DM Sans a aussi un axe Optical size en premier, BL1 09/10/2026)
        ax=f.get_variation_axes();v=[]
        for x in ax:
            n=x.get('name',b'');n=n.decode() if isinstance(n,bytes) else str(n)
            v.append(min(max(graisse,x['minimum']),x['maximum']) if 'eight' in n or len(ax)==1 else (min(int(taille),x['maximum']) if 'ptical' in n else x.get('default',x['minimum'])))
        f.set_variation_by_axes(v)
    except Exception:pass
    return f

def carte_remplacements(R):
    """image de sortie -> image source, d'après rendu.remplacements ; renvoie (carte, plans trop longs pour leur matière)"""
    carte={};longs=[]
    for it in R.get('remplacements',[]):
        a,b=it['images']
        if 'image' in it:
            for i in range(a,b+1):carte[i]=it['image']
            continue
        rg=it['depuis'];mode=it.get('mode','seq')
        if mode=='seq':seq=[k for x,y in rg for k in range(x,y+1)]
        elif mode=='inverse':seq=[k for x,y in rg for k in range(y,x-1,-1)]
        else:
            x,y=rg[0];seq=list(range(y-1,x-1,-1))+list(range(x+1,y))
        for i in range(a,b+1):
            k=i-a;carte[i]=seq[k] if k<len(seq) else (seq[k%len(seq)] if mode=='aller_retour' else seq[-1])
        if b-a+1>len(seq) and mode!='aller_retour':longs.append((a,b,len(seq)))
    return carte,longs

def ratio_nom(w,h):
    r=w/h
    for nom,v in (('9x16',9/16),('4x5',4/5),('1x1',1.0),('3x4',3/4),('16x9',16/9),('4x3',4/3)):
        if abs(r-v)<0.012:return nom
    return f'{w}x{h}'

def python_demucs():
    """interpréteur qui a demucs : variable ADCLONER_PYTHON, sinon ~/adcloner-env, sinon l'interpréteur courant"""
    for c in (os.environ.get('ADCLONER_PYTHON'),os.path.expanduser('~/adcloner-env/bin/python'),sys.executable):
        if c and os.path.exists(c):
            if subprocess.run([c,'-c','import demucs'],capture_output=True).returncode==0:return c
    return None
