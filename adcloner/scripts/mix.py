"""Mixe la musique d'origine (voix retirée) et les voix françaises posées à leur début.
Usage : python3 mix.py <dossier>   Écrit mix.wav (durée = durée de la vidéo)."""
import json,os,subprocess,sys,wave
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
SR=44100
def lire(f):
    w=wave.open(f);a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float)/32768;return a.reshape(-1,w.getnchannels())
def main():
    if len(sys.argv)<2:raise SystemExit(__doc__)
    d=sys.argv[1];f=fiche(d);an=analyse_json(d)
    N=int(an['duree']*SR);out=np.zeros((N,2));cible=0.10
    st=os.path.join(d,'dm','htdemucs','full');m=f.get('mix',{})
    if m.get('fond','musique')!='aucun' and os.path.exists(os.path.join(st,'no_vocals.wav')):
        mus=lire(os.path.join(st,'no_vocals.wav'));n=min(N,len(mus));out[:n]=mus[:n]*float(m.get('niveau_fond',1.0))
    if os.path.exists(os.path.join(st,'vocals.wav')):
        v=lire(os.path.join(st,'vocals.wav')).mean(1);fr=[v[i:i+2048] for i in range(0,len(v)-2048,2048)];r=np.array([np.sqrt((x**2).mean()) for x in fr])
        if (r>0.02).any():cible=float(np.median(r[r>0.02]))
    for l in f['lignes']:
        mp3=os.path.join(d,'tts',l['id']+'.mp3');wav=os.path.join(d,'tts',l['id']+'.wav')
        subprocess.run([FF,'-v','error','-y','-i',mp3,'-ar',str(SR),'-ac','1','-f','wav',wav],check=True)
        x=lire(wav)[:,0];mk=np.abs(x)>0.02
        if mk.any():x=np.clip(x*cible/np.sqrt((x[mk]**2).mean()),-0.98,0.98)
        fe=int(0.008*SR);x[:fe]*=np.linspace(0,1,fe);x[-fe:]*=np.linspace(1,0,fe)
        i=int(l['debut']*SR);e=min(N,i+len(x));out[i:e,0]+=x[:e-i];out[i:e,1]+=x[:e-i]
    pic=np.abs(out).max()
    if pic>0.98:out=out/pic*0.97
    o=wave.open(os.path.join(d,'mix.wav'),'wb');o.setnchannels(2);o.setsampwidth(2);o.setframerate(SR);o.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes());o.close()
    print(f"mix.wav écrit ({N/SR:.2f} s, niveau voix cible {cible:.3f}, crête {pic:.2f}{' normalisée' if pic>0.98 else ''})")
if __name__=='__main__':main()
