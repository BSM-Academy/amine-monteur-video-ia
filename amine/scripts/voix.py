"""Voix ElevenLabs : clonage (facultatif) et synthèse phrase par phrase avec alignement, tableau des durées.
Usage :
  python3 voix.py <dossier> --cloner [--secondaire]   crée un clone depuis la voix isolée, teste une synthèse, enregistre l'id dans la fiche
  python3 voix.py <dossier> [--force] [--reprendre] [S1 S2 ...]   génère les lignes de la fiche (celles déjà générées avec le même texte sont gardées)
Chaque phrase est réécoutée par Whisper (langue entendue + mots, sans tenir compte des homophones) : une phrase avec un accent
étranger ou des mots sautés/ajoutés est régénérée automatiquement (voix.reprises, 2 par défaut) et la meilleure prise est gardée.
--reprendre applique aussi la reprise aux phrases déjà générées.
Lit fiche.json : voix{id,repli_id,vitesse_max}, lignes[{id,texte,debut,fin_fenetre,vitesse?}]. Écrit tts/<id>.mp3 et tts/<id>.json."""
import base64,difflib,hashlib,json,os,re,sys,unicodedata,urllib.error,urllib.request
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
API='https://api.elevenlabs.io/v1'

def appel(url,corps=None,methode='POST',entetes=None):
    k=cle_elevenlabs();h={} if k=='cloud' else {'xi-api-key':k};h.update(entetes or {})  # 'cloud' = secret réseau : le proxy ajoute l'en-tête (14/10/2026)
    req=urllib.request.Request(url,corps,h,method=methode)
    try:return urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        return e

LANGUE='fr'  # langue cible : lue dans la fiche (langue_cible) par main() ; avant le 05/10/2026 le français était codé en dur

def synthese(voix,texte,vitesse=1.0,avant=None,apres=None,stabilite=0.5):
    # style 0 : le style exagéré rend la voix instable (mots avalés, sons parasites) ; phrases voisines envoyées pour une intonation qui s'enchaîne
    c={"text":texte,"model_id":"eleven_multilingual_v2","language_code":LANGUE,"voice_settings":{"speed":vitesse,"stability":stabilite,"similarity_boost":0.85,"style":0,"use_speaker_boost":True}}
    if avant:c["previous_text"]=avant
    if apres:c["next_text"]=apres
    corps=json.dumps(c).encode()
    r=appel(f"{API}/text-to-speech/{voix}/with-timestamps?output_format=mp3_44100_128",corps,entetes={'Content-Type':'application/json'})
    code=getattr(r,'status',None) or getattr(r,'code',None)
    if code!=200:return code,r.read().decode('utf-8','ignore')[:300]
    return 200,json.load(r)

# ---------------------------------------------------------------- réécoute d'une phrase générée
NOMBRES=set("zéro un une deux trois quatre cinq six sept huit neuf dix onze douze treize quatorze quinze seize vingt trente quarante cinquante soixante cent cents mille et pour "
  "null eins eine einer einem einen zwei drei vier fünf sechs sieben acht neun zehn elf zwölf zwanzig dreißig vierzig fünfzig hundert tausend und prozent "  # allemand (13/10/2026 : « drei » lu « 3 » comptait comme un écart)
  "zero uno una due tre quattro cinque sei sette otto nove dieci undici dodici venti trenta quaranta cinquanta cento mila e per cento".split())  # italien
def _mots(t):return re.sub(r"[^a-zà-ÿß0-9%]+"," ",t.lower().replace("'"," ").replace("’"," ").replace("-"," ")).split()
def _son(t):
    """forme sonore approximative : homophones et pluriels confondus (aux sprays = au spray, carrure = carure, ajusté = ajustez)"""
    t=''.join(c for c in unicodedata.normalize('NFD',t) if unicodedata.category(c)!='Mn')
    def fin(t):  # terminaisons muettes
        while len(t)>2 and re.search(r'(ent|er|s|x|z|t|d|p|e)$',t):t=re.sub(r'(ent|er|s|x|z|t|d|p|e)$','',t)
        return t
    t=fin(re.sub(r'(.)\1+',r'\1',t))
    for a,b in (('eau','o'),('au','o'),('ai','e'),('ph','f'),('qu','k'),('ce','se'),('ci','si'),('en','an')):t=t.replace(a,b)
    return re.sub(r'(.)\1+',r'\1',fin(t)).replace('c','k')
def _pareil(a,b):
    if all(re.fullmatch(r'[0-9%]+',w) or w in NOMBRES for w in a+b) and any(re.fullmatch(r'[0-9%]+',w) for w in a+b):return True  # « 6 » = « six »
    if len(a)==len(b) and all(_son(x)==_son(y) for x,y in zip(a,b)):return True
    return _son(''.join(a))==_son(''.join(b))  # « micro lésions » = « microlésions »
def _compare(texte,entendu,lg):
    """-> {langue, ecarts:[(attendu, entendu)], score (mots vraiment différents), grave}"""
    a=_mots(texte);b=_mots(entendu);ecarts=[];score=0
    for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
        if t=='equal' or _pareil(a[i1:i2],b[j1:j2]):continue
        ecarts.append((' '.join(a[i1:i2]),' '.join(b[j1:j2])))
        score+=sum(_son(x)!=_son(y) for x,y in zip(a[i1:i2],b[j1:j2])) if i2-i1==j2-j1 else max(i2-i1,j2-j1)
    etranger=lg not in (None,LANGUE) and len(a)>=4
    return {'langue':lg,'ecarts':ecarts,'score':score+(5 if etranger else 0),'grave':etranger or score>=2}
def ecoute(mp3,texte):
    """réécoute d'une seule phrase (une demande Whisper)"""
    from analyse import transcrire
    tr=transcrire(mp3);return _compare(texte,' '.join(x['text'] for x in tr['segments']),tr.get('language'))
def ecoute_lot(items):
    """Réécoute groupée (13/10/2026) : items=[(id, mp3, texte)] -> {id: résultat de _compare}.
    Toutes les phrases sont collées dans un seul wav (1 s de silence entre deux), une seule demande Whisper (Groq : 20 demandes/min
    au palier gratuit, une par phrase saturait dès deux vidéos en parallèle), puis les mots horodatés sont rendus à leur phrase.
    La langue entendue vaut pour tout le lot (plus de détection d'accent phrase par phrase)."""
    if not items:return {}
    import subprocess,tempfile,wave,numpy as np
    from analyse import transcrire
    SR=16000;GAP=1.0;sil=np.zeros(int(SR*GAP),dtype=np.int16);parts=[sil];pos=GAP;plages=[]
    for i,mp3,t in items:
        raw=subprocess.run([FF,'-v','error','-i',mp3,'-ac','1','-ar',str(SR),'-f','s16le','-'],capture_output=True,check=True).stdout
        a=np.frombuffer(raw,dtype=np.int16);plages.append((i,t,pos,pos+len(a)/SR));parts+=[a,sil];pos+=len(a)/SR+GAP
    tmp=os.path.join(tempfile.gettempdir(),f'ecoute_{os.getpid()}_{abs(hash(tuple(i for i,_,_ in items)))}.wav')
    with wave.open(tmp,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes(np.concatenate(parts).tobytes())
    try:tr=transcrire(tmp)
    finally:
        if os.path.exists(tmp):os.remove(tmp)
    mots=[w for s in tr['segments'] for w in (s.get('words') or [])];lg=tr.get('language')
    if not mots:  # pas d'horodatage mot à mot : on retombe sur une demande par phrase
        return {i:ecoute(mp3,t) for i,mp3,t in items}
    return {i:_compare(t,' '.join(w['word'] for w in mots if d0-0.3<=(w['start']+w['end'])/2<d1+0.3),lg) for i,t,d0,d1 in plages}

def cloner(dossier,f):
    stems=os.path.join(dossier,'dm','htdemucs','full','vocals.wav')
    if not os.path.exists(stems):raise SystemExit("voix isolée absente (lance analyse.py avec demucs)")
    ech=os.path.join(dossier,'echantillon_voix.mp3')
    subprocess.run([FF,'-v','error','-y','-ss','0','-t','25','-i',stems,'-ac','1','-b:a','128k',ech],check=True)
    nom=f"{f.get('ref','video')} {f.get('marque','')}".strip()+" clone"  # règle de voix.md : <REF> <marque> clone
    r0=appel(f"{API}/voices",methode='GET');c0=getattr(r0,'status',None) or getattr(r0,'code',None)
    if c0==200:
        vs=json.load(r0).get('voices',[])
        for x in vs:
            if x.get('name')==nom:print('clone déjà existant, réutilisé :',x['voice_id']);return x['voice_id']
        n=sum(1 for x in vs if x.get('category')=='cloned');print(f"clones existants : {n}/10, places restantes : {max(0,10-n)}")
    # corps multipart minimal
    b='----adcloner';data=open(ech,'rb').read()
    corps=b''.join([f'--{b}\r\nContent-Disposition: form-data; name="name"\r\n\r\n{nom}\r\n'.encode(),
                    f'--{b}\r\nContent-Disposition: form-data; name="files"; filename="echantillon.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n'.encode(),data,f'\r\n--{b}--\r\n'.encode()])
    r=appel(f"{API}/voices/add",corps,entetes={'Content-Type':f'multipart/form-data; boundary={b}'})
    code=getattr(r,'status',None) or getattr(r,'code',None);rep=r.read().decode('utf-8','ignore')
    if code!=200:
        print("CLONAGE REFUSÉ :",rep[:250])
        if 'voice_limit_reached' in rep:print("-> emplacements de voix pleins : supprimer les clones des vidéos déjà livrées (clones temporaires, voir voix.md), puis relancer --cloner.")
        return None
    vid=json.loads(rep)['voice_id']
    c,t=synthese(vid,'Test.')
    if c!=200:
        print(f"CLONE BLOQUÉ à la synthèse (HTTP {c}) :",str(t)[:200]);print("-> voix de repli (pas de contournement : la personne clonée doit vérifier sa voix elle-même).");return None
    print('clone OK :',vid);return vid

def main():
    args=[a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:raise SystemExit(__doc__)
    d=args[0];f=fiche(d);v=f.get('voix',{})
    global LANGUE;LANGUE=f.get('langue_cible','fr')
    if '--cloner' in sys.argv:
        vid=cloner(d,f)
        v['id']=vid or v.get('repli_id');f['voix']=v;sauve_fiche(d,f)
        if not v['id']:raise SystemExit("aucune voix : renseigne voix.repli_id dans la fiche")
        print('voix retenue :',v['id']);return
    if not v.get('id'):raise SystemExit("voix.id absent de la fiche (lance --cloner ou renseigne une voix)")
    os.makedirs(os.path.join(d,'tts'),exist_ok=True);vmax=float(v.get('vitesse_max',1.07))
    ids=[a for a in args[1:]] or [l['id'] for l in f['lignes']];force='--force' in sys.argv
    tot=0;trop=[];reprendre='--reprendre' in sys.argv;stab=float(v.get('stabilite',0.5));essais=int(v.get('reprises',2));a_ecouter=[]
    print(f"{'id':5s} {'car':>4s} {'durée':>6s} {'fenêtre':>8s} {'ratio':>6s}  écoute")
    L=f['lignes'];etat=[]
    def prise(k,l,sp):
        avant=L[k-1]['texte'] if k>0 else None;apres=L[k+1]['texte'] if k+1<len(L) else None
        c,r=synthese(v['id'],l['texte'],sp,avant,apres,stab)
        if c!=200:raise SystemExit(f"{l['id']} : ElevenLabs HTTP {c} {r}")
        return base64.b64decode(r['audio_base64']),r['alignment']
    # 1. synthèse (une demande ElevenLabs par phrase à générer)
    for k,l in enumerate(L):
        if l['id'] not in ids:continue
        sp=min(float(l.get('vitesse',1.0)),vmax);cle=hashlib.md5((f"{v['id']}|{sp}|{l['texte']}"+('' if LANGUE=='fr' else '|'+LANGUE)).encode()).hexdigest()
        mp3=os.path.join(d,'tts',l['id']+'.mp3');js=os.path.join(d,'tts',l['id']+'.json');ct=os.path.join(d,'tts',l['id']+'.cle');ec=os.path.join(d,'tts',l['id']+'.ecoute.json')
        neuf=''
        if not force and os.path.exists(mp3) and os.path.exists(js) and os.path.exists(ct) and open(ct).read()==cle:al=json.load(open(js))
        else:
            au,al=prise(k,l,sp);open(mp3,'wb').write(au);json.dump(al,open(js,'w'));open(ct,'w').write(cle);tot+=len(l['texte']);neuf='*'
        e=json.load(open(ec)) if os.path.exists(ec) else None
        if not e or e.get('cle')!=cle or neuf:e=None
        etat.append(dict(k=k,l=l,sp=sp,cle=cle,mp3=mp3,js=js,ec=ec,neuf=neuf,al=al,e=e,n=0))
    # 2. réécoute groupée : une seule demande Whisper pour toutes les phrases à vérifier
    a_verifier=[s for s in etat if s['e'] is None]
    res=ecoute_lot([(s['l']['id'],s['mp3'],s['l']['texte']) for s in a_verifier])
    for s in a_verifier:
        e=res[s['l']['id']];e['cle']=s['cle'];s['e']=e;json.dump(e,open(s['ec'],'w'),ensure_ascii=False)
    # 3. reprises : les phrases MAUVAISES sont regénérées puis réécoutées ensemble (une demande Whisper par tour, 2 tours au plus)
    for tour in range(essais):
        cand=[s for s in etat if s['e']['grave'] and (s['neuf'] or reprendre)]
        if not cand:break
        for s in cand:
            au,al2=prise(s['k'],s['l'],s['sp']);tot+=len(s['l']['texte']);s['n']+=1;s['tmp']=s['mp3']+'.essai.mp3';s['al2']=al2;open(s['tmp'],'wb').write(au)
        res=ecoute_lot([(s['l']['id'],s['tmp'],s['l']['texte']) for s in cand])
        for s in cand:  # on garde la meilleure prise
            e2=res[s['l']['id']];e2['cle']=s['cle']
            if e2['score']<s['e']['score']:os.replace(s['tmp'],s['mp3']);json.dump(s['al2'],open(s['js'],'w'));s['al']=s['al2'];s['e']=e2;json.dump(e2,open(s['ec'],'w'),ensure_ascii=False)
            else:os.remove(s['tmp'])
    # 4. tableau
    for s in etat:
        l,e,al,n,neuf=s['l'],s['e'],s['al'],s['n'],s['neuf']
        dur=al['character_end_times_seconds'][-1];fen=l['fin_fenetre']-l['debut'];ratio=dur/fen
        flag='  TROP LONG' if ratio>1.10 else ('  à écouter' if ratio>1.02 else ('  court' if ratio<0.7 else ''))  # seuils de voix.md
        if ratio>1.10:trop.append(l['id'])
        ver='ok' if not e['ecarts'] and e['langue']==LANGUE else ((('ACCENT '+str(e['langue'])+' ') if e['langue']!=LANGUE else '')+('MAUVAISE ' if e['grave'] else 'à écouter ')+str(e['ecarts'][:3]))
        if e['ecarts'] or e['langue']!=LANGUE:a_ecouter.append(l['id'])
        print(f"{l['id']:5s} {len(l['texte']):4d} {dur:5.2f}s {fen:7.2f}s {ratio:6.2f}{neuf}{flag}  {ver}"+(f"  ({n} reprise(s))" if n else ""))
    print(f"caractères facturés : {tot}  (* = généré maintenant)  trop longs : {trop or 'aucun'}  à écouter : {a_ecouter or 'aucune'}")
    if any(json.load(open(os.path.join(d,'tts',i+'.ecoute.json')))['grave'] for i in a_ecouter):
        print("Phrase(s) MAUVAISE(S) : reformuler (mot plus courant, phrase plus simple), ou --reprendre. Accent persistant : voix de la bibliothèque (voix.md).")
if __name__=='__main__':main()
