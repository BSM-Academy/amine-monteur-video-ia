# Voix : clonage, synthèse, durées

Commandes : `python3 scripts/voix.py <dossier> --cloner` (clone + test de synthèse, repli automatique), puis `python3 scripts/voix.py <dossier>` (génère les lignes de la fiche et affiche le tableau des durées), puis `python3 scripts/mix.py <dossier>`.

## Étape 4 : Générer et caler la voix cible

1. Utiliser autant que possible la **même voix que dans la vidéo originale**, grâce au clonage multilingue.
2. Si cette voix ne peut pas être reproduite correctement dans la langue cible, choisir une voix qui lui ressemble fortement : même genre, tranche d'âge, timbre, accent, énergie, débit et intention publicitaire.
3. Face caméra : privilégier le clonage de la voix originale afin de préserver l'identité du personnage.
4. Générer phrase par phrase.
5. Poser chaque phrase sur son timecode.
6. Retirer toute la voix source, en conservant musique et bruitages utiles.

### Contrôle par phrase

```text
durée audio cible ÷ durée disponible
```

| Ratio | Verdict | Action |
|---|---|---|
| 0,90–1,02 | Bon | Conserver ou ajuster légèrement les silences |
| 1,02–1,10 | Tolérable | Écouter ; raccourcir si le débit semble forcé |
| > 1,10 | Trop long | Raccourcir et régénérer |
| < 0,90 | Trop court | Utiliser la version longue ou des pauses naturelles |

Ne jamais masquer un texte trop long par une forte accélération.

### Réécoute automatique de chaque phrase (03/10/2026, remarque de l'utilisateur : mots sautés, mots mal prononcés)

**Constat (diagnostic de 6 vidéos) :** sons parasites entendus comme des mots en plus (BM1 : « Depuis **la semaine**, … jouent **de ce** dehors »), mots déformés (SL5 : « ce ventre » → « se vendre »), accent de la voix d'origine qui ressort (BD3 « carrure », SL5 « OK mec » reconnus comme de l'anglais).
**Ce que fait `voix.py` :**
- réglage `style` à 0 (le style exagéré rend la voix instable), phrases voisines envoyées à ElevenLabs (`previous_text`, `next_text`) pour une intonation qui s'enchaîne ;
- chaque phrase générée est réécoutée par Whisper : langue entendue + mots, en ignorant homophones, pluriels et chiffres écrits en lettres. Colonne « écoute » : `ok`, `à écouter [écarts]` (1 mot différent : écouter), `MAUVAISE` (2 mots ou plus sautés, ajoutés ou déformés) ou `ACCENT xx` (langue entendue autre que la cible) ;
- une phrase MAUVAISE ou avec ACCENT est régénérée automatiquement (`voix.reprises`, 2 par défaut ; caractères facturés à chaque essai) et la meilleure prise est gardée. `--reprendre` le fait aussi pour des phrases déjà générées.
**Si ça reste MAUVAIS après les reprises :** reformuler la phrase (mot plus courant, phrase plus simple, pas de mot étranger), ou baisser l'instabilité (`voix.stabilite` 0,6 à 0,7). Accent persistant sur plusieurs phrases : voix française de la bibliothèque proche (genre, âge, énergie).
Écouter quand même chaque phrase marquée « à écouter » : Whisper peut se tromper (« d'où ces » / « douces et »).

**Voix.**
- Isoler la voix et la musique avec demucs, installé dans un environnement Python isolé. L'installation demande l'accord de l'utilisateur.
- Cloner la voix depuis la voix isolée (20 s environ). Pour une réplique secondaire très courte (1 s), prendre une voix de la bibliothèque de même genre et âge.
- Vitesse ElevenLabs de 1,07 au maximum, et seulement pour rentrer dans une fenêtre.
- Poser chaque phrase au début de la fenêtre de son sous-titre. Une phrase peut empiéter sur la pause suivante, jamais sur le sous-titre suivant.
- Normaliser chaque phrase sur le niveau de la voix d'origine.
- Quand la source n'a pas de musique (fond quasi muet), ne mettre que la voix.

**Clone bloqué par ElevenLabs.** ElevenLabs peut bloquer un clone avec une vérification par CAPTCHA (erreur 403 « voice_access_denied », statut `detected_captcha_voice`). Seule la personne clonée peut la passer, donc ne pas réessayer et ne pas chercher à contourner. Passer directement à une voix de la bibliothèque proche (même genre, âge, énergie), par exemple « Léo – Energetic & Engaging » pour un jeune homme dynamique. Vérifier le premier appel de synthèse juste après la création du clone, avant de générer toutes les phrases.

**Clones jetables (décision de l'utilisateur, 09/10/2026, remplace celle du 03/10).** Un clone ne sert qu'à sa vidéo. Le nommer `<REF> <marque> clone`, et le **supprimer dès que toutes les phrases de la vidéo sont générées** (`DELETE /v1/voices/<id>`), sans attendre la validation. Le dire dans la réponse. Une correction après coup : les phrases déjà faites restent dans `tts/` (cache), et pour une phrase nouvelle on reclone depuis `echantillon_voix.mp3` (gratuit, quelques secondes), on génère **seulement les phrases changées** avec `voix.py <dossier> L4 L7` (le cache dépend de l'id de voix : `voix.py <dossier>` sans liste régénère TOUTES les phrases, 944 caractères perdus sur BL1 le 09/10/2026), puis on resupprime. Seules les voix de catégorie « cloned » comptent dans la limite (10). Les voix de la bibliothèque (Lea, Léo…) ne se suppriment jamais.

**Emplacements pleins (10 sur 10).** Ne devrait plus arriver (clones jetables). Sinon, supprimer tous les clones (catégorie « cloned ») : ils sont tous jetables (accord de l'utilisateur, 09/10/2026), puis relancer `--cloner`.

**Durée du texte français.** Le français est plus long : prévoir 20 à 30 % de mots en moins, quitte à raccourcir. Mesurer la durée réelle de chaque phrase (alignement ElevenLabs) avant de la poser, et ne régénérer que les phrases qui dépassent leur fenêtre.

**Clé ElevenLabs invalide (03/10/2026, Peel shot).** Erreur 401 `invalid_api_key` au clonage : ce n'est pas un refus de clone, le repli sur une voix de bibliothèque échouera aussi. Arrêter l'étape voix et demander à l'utilisateur de renouveler la clé ; ne jamais lire ni afficher la clé.

**demucs introuvable.** Les scripts cherchent `ADCLONER_PYTHON`, puis `~/adcloner-env`. Un environnement créé dans un dossier temporaire de conversation disparaît : l'installer dans `~/adcloner-env` (avec l'accord de l'utilisateur).

**Deuxième voix courte (04/10/2026, BR6).** Une réplique dite par une autre personne (femme, ~230 Hz contre ~150 Hz pour l'homme : mesurer la hauteur de voix de chaque phrase sur la voix isolée) prend une voix de bibliothèque de même genre (ex. Lea). `voix.py` n'a qu'une voix par fiche : générer les autres lignes, mettre l'id de la voix secondaire dans `voix.id`, lancer `voix.py <dossier> L2`, puis remettre l'id du clone. La clé de cache contient l'id de la voix, donc les autres lignes ne sont pas régénérées.

**Toujours refaire le mixage après une phrase régénérée (05/10/2026, BR6).** J'ai régénéré L5 après `mix.py` sans relancer le mixage : la vidéo livrée disait l'ancienne phrase alors que les sous-titres (calés sur `tts/*.json`) affichaient la nouvelle. L'utilisateur l'a entendu. Règle : après tout `voix.py`, relancer `mix.py` puis `rendu.py` ; avant de livrer, transcrire la vidéo finale (Whisper) et comparer phrase par phrase avec la fiche.

**Langue cible lue dans la fiche (05/10/2026, IS1 suédois → allemand).** `voix.py` avait le français codé en dur (`language_code` ElevenLabs et réécoute Whisper) : une voix allemande sortait avec un réglage français et chaque phrase était marquée « ACCENT de MAUVAISE », avec 2 reprises facturées pour rien. Corrigé : la langue vient de `langue_cible` de la fiche. Toujours renseigner `langue_cible`.

**Supprimer le clone (05/10/2026, durci le 09/10/2026).** Les 10 emplacements étaient pleins de clones oubliés. Règle actuelle : suppression juste après la génération des phrases (voir « Clones jetables »).

**Source déjà dans la langue cible (06/10/2026, SO1 marque X DE → ma marque DE).** Rebrand complet : revoicer toute la vidéo avec le clone (marque, prix, offre, tailles changent). La voix d'origine était très rapide : le clone dépassait de 10 % au total. Raccourcir le script d'environ 25 %, puis caler les phrases à la suite (début = max(début source, fin précédente + 0,08 s)) en vérifiant que le retard maximal reste sous 0,6 s et que la voix finit avant la fin de la vidéo.

**Voix de bibliothèque partagée (06/10/2026, N7 italien).** Après un clone bloqué (403 captcha), supprimer ce clone inutilisable tout de suite, puis chercher une voix proche avec `GET /v1/shared-voices?language=it&gender=male&use_cases=advertisement` et l'ajouter au compte (`POST /v1/voices/add/<public_owner_id>/<voice_id>`) avant de la mettre dans `voix.id`. Italien homme jeune, posé : « Romario - Credible, Calm and Balanced » (`YpCv81OHYUqjcik0cjn5`), repli « Gian - Clear, Upbeat » (`wytO3xyllSDjJKHNkchr`).

**Versions dans une 2e langue à partir d'une vidéo déjà adaptée (08/10/2026, lot DE après CZ).** Réutiliser le dossier de travail (src, analyse, dm, boîtes d'origine, patches `interp`, `textes`) et `echantillon_voix.mp3` pour recloner la voix d'origine (le clone de la 1re langue a été supprimé). Remettre les débuts d'origine si `enchainer.py` a été utilisé (il relit `analyse.json`). Allemand plus long que le tchèque : mots composés à écrire sans tirets quand c'est possible (« Bauch Kompression » au lieu de « 360-Grad-Bauch-Kompression ») pour que le découpage des sous-titres puisse couper, `max_car` 17 en majuscules, 21 en minuscules ; voix rapide : `scripts/modules/enchainer.py` (retard max ≈ 0,6-0,9 s). À améliorer : la liste des petits mots de fin de morceau n'a pas l'allemand (« ein, », « da. », « deinem ») ni le tchèque.

**Mot clé dit en même temps qu'un titre à l'écran (08/10/2026, SIL7 DE).** Quand la source dit un mot qui s'affiche aussi en gros titre (« Day one » + titre DAY 1, « Day 7 », prix, « garantie »…), ce mot doit tomber au même moment que dans la source. Si la traduction le met en fin d'une longue phrase, la voix l'avance de plusieurs secondes (SIL7 DE : « Tag 1 » dit 2 s avant le titre TAG 1). Correction : sortir ce mot dans sa propre ligne (`S1b`, `debut` = l'instant où la source le dit, lu dans `analyse.json` → `mots`), puis remettre ce début à la main après `enchainer.py`. Contrôle : pour chaque titre de `rendu.textes`, comparer ses images avec celles du sous-titre du même mot dans `cues.json` ; un écart de plus de 0,5 s se justifie seulement si la source a le même écart (vérifier sur une planche source / adaptation côte à côte).

**Règle prioritaire : pas de trou de voix que la source n'a pas (08/10/2026, SIL7 DE, remarque de l'utilisateur).** Quand la source parle sans s'arrêter, l'adaptation parle aussi sans s'arrêter, et les sous-titres défilent sans blanc. Un silence de plus d'1 s (voix figée, aucun nouveau sous-titre) là où la source parle est une faute de voix, pas un détail. Erreur faite : après avoir sorti « Tag 1 » de la phrase, la phrase restante était trop courte (8,5 s pour 11 s) et laissait 2,5 s de vide avant « Tag 1 ». Correction : **rallonger le texte** en traduisant plus complètement ce que dit la source (« like this » → « so », « 30 days straight » → « 30 Tage am Stück », « all four of those » → « alle vier »), jamais ralentir la voix au-delà de ~0,9 ni ajouter d'idée absente de la source. `controle.py` le vérifie seul (« trous de voix absents de la source »).

**Réécoute Whisper en une seule demande par vidéo (13/10/2026, test Groq 3 vidéos en parallèle).** Le palier gratuit de Groq autorise 20 demandes par minute ; la réécoute phrase par phrase (25 à 30 demandes par vidéo) saturait dès deux vidéos en parallèle, avec repli silencieux sur Whisper local (2,4 Go). `voix.py` colle maintenant toutes les phrases à vérifier dans un seul wav (1 s de silence entre deux), fait une demande Whisper, et rend les mots horodatés à leur phrase (`ecoute_lot`) ; les reprises sont regénérées puis réécoutées ensemble (une demande par tour). Résultat : 1 à 3 demandes par vidéo ; testé sur GL3E (31 phrases) : mêmes verdicts qu'en phrase par phrase, 30 s au lieu d'une minute ; 3 vidéos en parallèle (GLAF, GLD9, GLF8) : 0 erreur 429, étape voix (clone + synthèse + réécoute) en 61 à 72 s par vidéo. Limite : la langue entendue vaut pour tout le lot (plus de détection d'accent phrase par phrase). `analyse.transcrire()` réessaie après un 429/5xx (en-tête `retry-after`, sinon 15 s, 30 s, 45 s, 60 s) avant de retomber en local ; `ADCLONER_WHISPER=groq` interdit le repli local (utile pour mesurer). `NOMBRES` contient l'allemand et l'italien : « drei » lu « 3 » n'est plus un écart (GL5B S19 était marquée MAUVAISE à tort).

**Whisper dans le cloud (Groq), 13/10/2026.** `analyse.transcrire()` passe d'abord par l'API Groq (`whisper-large-v3`, mots et segments horodatés, langue détectée renvoyée en code « de »/« en ») quand une clé existe (`GROQ_API_KEY` dans l'environnement, `~/.config/groq/.env` ou `~/.config/watch/.env`), sinon mlx_whisper local. Mesuré sur GL3E : 113 s d'audio transcrits en 9 s, zéro mémoire sur le Mac (le local prenait 1,5 à 2 Go et 1 à 2 min). Forcer le local : `ADCLONER_WHISPER=local`. Pièges : Groq répond 403 sans en-tête User-Agent ; demander les deux granularités (`word` et `segment`) sinon `segments` est vide ; audio envoyé en mp3 mono 16 kHz (limite 25 Mo). Reste lourd en local : demucs (2,5 à 4 Go), à remplacer par une API (ElevenLabs Audio Isolation ou Replicate) pour pouvoir traiter plusieurs vidéos en parallèle.

**Voix de bibliothèque allemande, femme jeune, pub (13/10/2026, GL5B et GLAA, clone bloqué 403).** « Clara – German Authentic & Commercial » (`eHUtR7GEpF8oQODRxCTo`), repli « Ina Incredible » (`Gt7OshJCH7MuzX96wFHi`) ; aussi Sophia (`QT6va3HQK8j63EC2r9cw`), Darinka (`IPgFCimtGutbaeC6sKnf`). `POST /v1/voices/add/<owner>/<id>` exige un corps JSON `{"new_name": …}` (422 sinon). Un clone bloqué par captcha sur une vidéo le reste pour toutes les langues : ne pas recloner, passer directement à la bibliothèque.
**Débit d'une voix de bibliothèque** : Clara est rapide (17 à 22 caractères par seconde de fenêtre, contre 13 à 16 pour une voix italienne comme Giulia). Avec un script « 25 % plus court », 13 phrases sur 17 sortaient trop courtes et des trous de voix > 1 s apparaissaient. Règle : générer d'abord 2 ou 3 phrases test pour mesurer le débit, puis dimensionner le script (≈ 17 car/s pour Clara, traduire presque complètement). Une phrase longue avec un trou se corrige mieux en la scindant (S15 + S15b) qu'en l'allongeant. Durées très variables d'une prise à l'autre avec les virgules et deux-points : une seule virgule par phrase longue.
**Groq 429 (Too Many Requests)** quand 3 vidéos ou plus réécoutent leurs phrases en même temps (limite 7 200 s d'audio par heure) : `transcrire()` retombe sur le Whisper local, hors file lourde, et la mémoire du Mac repart. Réessai avec attente ajouté dans `analyse.py` (session du 13/10) ; limiter à 2 ou 3 vidéos en parallèle.
