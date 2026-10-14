"""Analyse d'une vidéo source en une passe : audio, voix/musique, transcription mot à mot, coupes de plan, une planche légère.
Usage : python3 analyse.py <video> <dossier_de_travail> [--langue en]
Écrit dans le dossier : src.mp4 (copie), full.wav, dm/ (voix et musique séparées), analyse.json, planche.jpg"""
import json,os,shutil,subprocess,sys,wave
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
from PIL import Image,ImageDraw

def transcrire_groq(path,langue=None,cle=None):
    """Whisper large-v3 via l'API Groq (13/10/2026, option cloud) : audio converti en mp3 mono 16 kHz, mots et segments horodatés.
    Renvoie le même format que mlx_whisper : {'language','text','segments':[{'start','end','text','words':[{'word','start','end'}]}]}"""
    import tempfile,urllib.request,uuid
    tmp=os.path.join(tempfile.gettempdir(),f'groq_{uuid.uuid4().hex}.mp3')
    subprocess.run([FF,'-v','error','-y','-i',path,'-ac','1','-ar','16000','-b:a','64k',tmp],check=True)
    try:
        b='----adcloner'+uuid.uuid4().hex;parts=[('model','whisper-large-v3'),('response_format','verbose_json'),('timestamp_granularities[]','word'),('timestamp_granularities[]','segment')]
        if langue:parts.append(('language',langue))
        body=b''
        for k,v in parts:body+=f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
        body+=f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="a.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n'.encode()+open(tmp,'rb').read()+f'\r\n--{b}--\r\n'.encode()
        r=urllib.request.Request('https://api.groq.com/openai/v1/audio/transcriptions',data=body,headers={'Authorization':'Bearer '+cle,'Content-Type':'multipart/form-data; boundary='+b,'User-Agent':'adcloner/1.0'})  # sans User-Agent, Groq répond 403
        d=json.load(urllib.request.urlopen(r,timeout=300))
    finally:
        if os.path.exists(tmp):os.remove(tmp)
    words=[{'word':' '+w['word'].strip(),'start':float(w['start']),'end':float(w['end'])} for w in d.get('words') or []]
    segs=[]
    for sg in d.get('segments') or []:
        ws=[w for w in words if sg['start']-0.05<=w['start']<sg['end']+0.05 and not any(w is x for s2 in segs for x in s2['words'])]
        segs.append({'start':float(sg['start']),'end':float(sg['end']),'text':sg['text'],'words':ws})
    if not segs and words:segs=[{'start':words[0]['start'],'end':words[-1]['end'],'text':d.get('text',''),'words':words}]
    LANG={'english':'en','french':'fr','german':'de','italian':'it','spanish':'es','czech':'cs','dutch':'nl','portuguese':'pt','polish':'pl','swedish':'sv','danish':'da','norwegian':'no','finnish':'fi','turkish':'tr','romanian':'ro','hungarian':'hu','greek':'el','arabic':'ar','japanese':'ja','chinese':'zh','korean':'ko','russian':'ru','ukrainian':'uk'}
    lg=(d.get('language') or '').lower();lg=LANG.get(lg,lg[:2] if len(lg)>2 else lg)  # Groq renvoie « German », les scripts attendent « de »
    return {'language':lg,'text':d.get('text',''),'segments':segs}

DEMUCS_REPLICATE='ryan5453/demucs:ff5ad47d2685b27c0f820ee134c4394140804f08fa755cb20c846459faa4b337'  # htdemucs sur Replicate (version du 04/10/2026)
def separer_replicate(wav,dossier,cle):
    """demucs (htdemucs, deux pistes) via l'API Replicate (13/10/2026) : envoie full.wav, écrit dm/htdemucs/full/{vocals,no_vocals}.wav
    comme le demucs local. ~1 à 2 min, 0 Go sur le Mac, ~0,04 $ par vidéo. Lève une exception si Replicate échoue."""
    import urllib.request,uuid,time
    H={'Authorization':'Bearer '+cle}
    b='----adcloner'+uuid.uuid4().hex
    body=(f'--{b}\r\nContent-Disposition: form-data; name="content"; filename="full.wav"\r\nContent-Type: audio/wav\r\n\r\n').encode()+open(wav,'rb').read()+f'\r\n--{b}--\r\n'.encode()
    r=urllib.request.Request('https://api.replicate.com/v1/files',data=body,headers={**H,'Content-Type':'multipart/form-data; boundary='+b})
    url=json.load(urllib.request.urlopen(r,timeout=300))['urls']['get']
    corps=json.dumps({'version':DEMUCS_REPLICATE.split(':')[1],'input':{'audio':url,'model':'htdemucs','isolate_stem':'vocals','format':'wav','shifts':1}}).encode()
    r=urllib.request.Request('https://api.replicate.com/v1/predictions',data=corps,headers={**H,'Content-Type':'application/json','Prefer':'wait=60'})
    p=json.load(urllib.request.urlopen(r,timeout=120));t0=time.time()
    while p['status'] in ('starting','processing'):
        if time.time()-t0>900:raise RuntimeError('Replicate : plus de 15 min sans résultat')
        time.sleep(5);p=json.load(urllib.request.urlopen(urllib.request.Request(p['urls']['get'],headers=H),timeout=60))
    if p['status']!='succeeded':raise RuntimeError(f"Replicate {p['status']} : {p.get('error')}")
    d=os.path.join(dossier,'dm','htdemucs','full');os.makedirs(d,exist_ok=True)
    for k in ('vocals','no_vocals'):
        with urllib.request.urlopen(urllib.request.Request(p['output'][k],headers=H),timeout=300) as src,open(os.path.join(d,k+'.wav'),'wb') as dst:shutil.copyfileobj(src,dst)
    print(f"demucs via Replicate : {time.time()-t0:.0f} s",file=sys.stderr)
    return d

def separer(wav,dossier):
    """Voix et musique séparées -> dossier des pistes (dm/htdemucs/full) ou None.
    ADCLONER_DEMUCS=local : demucs local seul ; =replicate : Replicate seul (erreur si échec) ; sinon Replicate si une clé existe, puis local."""
    mode=os.environ.get('ADCLONER_DEMUCS','');d=os.path.join(dossier,'dm','htdemucs','full')
    if os.path.exists(os.path.join(d,'vocals.wav')) and os.path.exists(os.path.join(d,'no_vocals.wav')):return d  # déjà fait (2e langue)
    cle=None if mode=='local' else cle_replicate()
    if cle:
        try:return separer_replicate(wav,dossier,cle)
        except Exception as e:
            if mode=='replicate':raise SystemExit(f"Replicate indisponible ({str(e)[:160]}) et ADCLONER_DEMUCS=replicate : pas de repli local")
            print(f"Replicate indisponible ({str(e)[:100]}) : demucs local",file=sys.stderr)
    elif mode=='replicate':raise SystemExit("ADCLONER_DEMUCS=replicate mais aucune clé : REPLICATE_API_TOKEN ou ~/.config/replicate/.env")
    py=python_demucs()
    if not py:return None
    env=dict(os.environ);env['PATH']=os.path.dirname(FF)+os.pathsep+env.get('PATH','')
    subprocess.run([py,'-m','demucs','--two-stems=vocals','-n','htdemucs','-d','cpu','-o',os.path.join(dossier,'dm'),wav],env=env,capture_output=True)
    return d if os.path.exists(os.path.join(d,'vocals.wav')) else None

def transcrire(path,langue=None):
    """Whisper : Groq si une clé existe (quelques secondes, rien en mémoire), sinon mlx_whisper local, sinon faster_whisper.
    ADCLONER_WHISPER=local : local seul ; =groq : Groq seul (erreur au lieu du repli local).
    Groq 429/5xx : attente (en-tête retry-after, sinon 15 s, 30 s, 45 s, 60 s) et nouvel essai, 5 essais au plus (13/10/2026)."""
    mode=os.environ.get('ADCLONER_WHISPER','');cle=None if mode=='local' else cle_groq()
    if cle:
        import time;err=None
        for essai in range(5):
            try:return transcrire_groq(path,langue,cle)
            except Exception as e:
                err=e;code=getattr(e,'code',None)
                if code not in (429,500,502,503) or essai==4:break
                ra=getattr(e,'headers',None);ra=ra.get('retry-after') if ra else None
                try:att=float(ra)
                except (TypeError,ValueError):att=15.0*(essai+1)
                print(f"Groq {code} : nouvel essai dans {att:.0f} s",file=sys.stderr);time.sleep(min(att,90))
        if mode=='groq':raise SystemExit(f"Groq indisponible ({str(err)[:120]}) et ADCLONER_WHISPER=groq : pas de repli local")
        print(f"Groq indisponible ({str(err)[:80]}) : Whisper local",file=sys.stderr)
    try:
        import mlx_whisper
        return mlx_whisper.transcribe(path,path_or_hf_repo="mlx-community/whisper-large-v3-turbo",word_timestamps=True,**({'language':langue} if langue else {}))
    except ImportError:
        from faster_whisper import WhisperModel
        m=WhisperModel('large-v3',compute_type='int8');segs,info=m.transcribe(path,word_timestamps=True,language=langue)
        out=[]
        for s in segs:out.append({'start':s.start,'end':s.end,'text':s.text,'words':[{'word':w.word,'start':w.start,'end':w.end} for w in s.words]})
        return {'language':info.language,'segments':out}

def rms_db(wav):
    w=wave.open(wav);a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float)/32768
    return round(20*np.log10(np.sqrt((a**2).mean())+1e-9),1)

def main():
    av=sys.argv[1:];langue=None
    if '--langue' in av:
        i=av.index('--langue')
        if i+1>=len(av):raise SystemExit("--langue sans valeur (ex. --langue en)")
        langue=av[i+1];del av[i:i+2]
    args=[a for a in av if not a.startswith('--')]
    if len(args)!=2:raise SystemExit(__doc__)
    video,dossier=args;os.makedirs(dossier,exist_ok=True)
    src=os.path.join(dossier,'src.mp4')
    if os.path.abspath(video)!=os.path.abspath(src):shutil.copy(video,src)
    P=probe(src);W,H=P['largeur'],P['hauteur']
    wav=os.path.join(dossier,'full.wav')
    subprocess.run([FF,'-v','error','-y','-i',src,'-vn','-ar','44100','-ac','2',wav],check=True)
    # voix / musique
    stems=separer(wav,dossier)
    cible=stems and os.path.join(stems,'vocals.wav') or wav
    tr=transcrire(cible,langue)
    # coupes de plan + nombre d'images en une seule lecture réduite
    n=0;prev=None;cuts=[]
    for im in lire_images(src,'scale=96:96',96,96):
        a=im.astype(np.int16)
        if prev is not None and np.abs(a-prev).mean()>16:cuts.append(n)
        prev=a;n+=1
    shots=[0]
    for c in cuts:
        if c-shots[-1]>8:shots.append(c)
    shots.append(n)
    # une seule planche légère : l'image du milieu de chaque plan
    tw=150;th=int(round(tw*H/W/2)*2);want={}
    for i,(a,b) in enumerate(zip(shots[:-1],shots[1:])):want[min(n-1,a+min(10,(b-a)//2))]=i
    tiles={}
    for i,im in enumerate(lire_images(src,f'scale={tw}:{th}',tw,th)):
        if i in want:tiles[want[i]]=Image.fromarray(im.copy())
    cols=12;rows=(len(tiles)+cols-1)//cols;sheet=Image.new('RGB',(cols*tw,rows*th))
    for k,(i,t) in enumerate(sorted(tiles.items())):
        d=ImageDraw.Draw(t);d.rectangle([0,0,44,11],fill=(0,0,0));d.text((2,0),f"{shots[i]}",fill=(255,255,0));sheet.paste(t,((k%cols)*tw,(k//cols)*th))
    sheet.save(os.path.join(dossier,'planche.jpg'),quality=70)
    # phrases avec fenêtres et budget de caractères
    mots=[w for s in tr['segments'] for w in s.get('words',[])];phrases=[];cur=[]
    for w in mots:
        cur.append(w)
        if re.search(r'[.?!]$',w['word'].strip()):phrases.append(cur);cur=[]
    if cur:phrases.append(cur)
    liste=[{'id':f'S{i}','debut':round(p[0]['start'],2),'fin':round(p[-1]['end'],2),'texte':''.join(w['word'] for w in p).strip(),
            'budget_car':int((p[-1]['end']-p[0]['start'])*17)} for i,p in enumerate(phrases,1)]
    res={'largeur':W,'hauteur':H,'fps':P['fps'],'duree':P['duree'],'images':n,'langue_source':tr.get('language'),'phrases':liste,'plans':shots,
         'mots':[{'m':w['word'].strip(),'a':round(w['start'],2),'b':round(w['end'],2)} for w in mots],
         'stems':bool(stems),'niveau_fond_db':rms_db(os.path.join(stems,'no_vocals.wav')) if stems else None}
    json.dump(res,open(os.path.join(dossier,'analyse.json'),'w',encoding='utf-8'),ensure_ascii=False)
    if os.path.exists(os.path.join(dossier,'fiche.json')) and res['langue_source']:  # langue détectée reportée dans la fiche
        f=fiche(dossier)
        if f.get('langue_source')!=res['langue_source']:print(f"fiche : langue_source {f.get('langue_source')} -> {res['langue_source']}");f['langue_source']=res['langue_source'];sauve_fiche(dossier,f)
    print(f"{W}x{H} {P['fps']:.0f} fps, {n} images, {P['duree']:.1f} s | langue {res['langue_source']} | {len(shots)-1} plans | voix/musique séparées : {'oui' if stems else 'NON (demucs absent)'} | fond {res['niveau_fond_db']} dB")
    for p in liste:print(f"{p['id']}: {p['debut']:.2f}-{p['fin']:.2f} (~{p['budget_car']} car) {p['texte']}")
    print('planche :',os.path.join(dossier,'planche.jpg'))
if __name__=='__main__':main()
