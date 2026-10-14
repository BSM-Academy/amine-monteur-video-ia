"""File d'attente pour les étapes lourdes quand plusieurs vidéos tournent en parallèle sur un Mac à 8 Go (réglage de l'utilisateur 13/10/2026).
Usage : python3 file_lourde.py [--file demucs|rendu] [--slots N] -- <commande...>
Files : « demucs » = 1 jeton (analyse.py : séparation voix/musique, 2,5 à 4 Go) ; « rendu » = 2 jetons (rendu.py, controle.py, blocs, détections : ~1 Go chacun).
Whisper passe par Groq (plus rien en mémoire). Attend un jeton libre (verrous fcntl dans ~/.adcloner-slots/<file>/), lance la commande, libère le jeton."""
import fcntl,os,sys,subprocess,time
av=sys.argv[1:];file='rendu';slots=None
while av and av[0] in ('--slots','--file'):
    if av[0]=='--slots':slots=int(av[1])
    else:file=av[1]
    av=av[2:]
if slots is None:slots=1 if file=='demucs' else 2
if av and av[0]=='--':av=av[1:]
if not av:raise SystemExit(__doc__)
d=os.path.expanduser('~/.adcloner-slots/'+file);os.makedirs(d,exist_ok=True)
while True:
    for i in range(slots):
        f=open(os.path.join(d,f'slot{i}'),'w')
        try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:f.close();continue
        print(f"[file {file}] jeton {i} pris : {' '.join(os.path.basename(a) for a in av[:2])}",file=sys.stderr,flush=True)
        r=subprocess.run(av);f.close();sys.exit(r.returncode)
    time.sleep(5)
