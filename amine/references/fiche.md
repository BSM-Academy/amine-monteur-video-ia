# La fiche vidéo (`fiche.json`)

Un fichier par vidéo, dans le dossier de travail. Il pilote les scripts et sert de mémoire. Exemple complet : `templates/fiche-exemple.json`.

| Clé | Rôle |
|---|---|
| `ref`, `langue_source`, `langue_cible` | nommage du livrable et langue de la voix |
| `marque`, `produit`, `site`, `offre` | brief (pour mémoire) |
| `voix` | `{id, repli_id, vitesse_max}` : voix ElevenLabs, voix de remplacement, vitesse maximale (1,07) |
| `lignes` | liste `{id, texte, debut, fin_fenetre, vitesse?}` : chaque phrase française, son début (secondes) et la fin de sa fenêtre |
| `mix` | `{fond: "musique"\|"aucun", niveau_fond}` |
| `controle` | `{sans_voix: ["texte affiché sans voix", ...], duree_min_sous_titre: 0.4}` : textes sans voix à ne pas signaler, et durée minimale d'un sous-titre (0,3 par défaut en karaoké, 0,4 sinon) |
| `rendu` | tout ce que le rendu doit faire (ci-dessous) |

## Section `rendu`

Toutes les entrées sont facultatives. Les images se donnent en numéros d'image `[début, fin]` (inclus), pas en secondes.

- `sortie` : nom du fichier sans son (défaut `rendu_video.mp4`). `encodeur` : puce vidéo du Mac par défaut (`qualite` 75, de 1 à 100) ; `"x264"` pour libx264 preset slow avec `crf` (17), plus lent et 4 fois plus gourmand, à réserver à un besoin précis.
- `zones_vmake` : `"auto"` (ou `{mode:"auto", marge:14, images:[a,b], limite:[x0,y0,x1,y1]}`) reprend le résultat Vmake seulement là où du texte a été détecté ; `exclure:[[x0,y0,x1,y1],...]` garde la source dans ces rectangles (émojis ou éléments d'origine à conserver). Sinon une liste manuelle de `{images, rect:[x0,y0,x1,y1], adoucir}`.
- `remplacements` : `{images, depuis:[[a,b],...], mode: "seq"|"inverse"|"aller_retour"}` remplace un plan par d'autres images de la vidéo ; `{images, image:N}` tient une image. Avec `blocs: "auto"`, `blocs_karaoke.py` prend seul les boîtes de sous-titres des images donneuses (sinon le texte d'origine de la donneuse resterait visible).
- `filigrane` : `"auto"` lit `filigrane.json` écrit par `modules/filigrane.py` (rectangle, images d'estimation, sombre/clair trouvés seuls) ; `{mode:"auto", remplacer_par:"site.com"}` pour y ajouter des réglages. À la main : `{images, rect, estimer_sur:[images de fond uni], sombre, seuil, remplacer_par:"site.com", y, taille, opacite}`.
- `badges` : `{"B1": ["TAG 1"], "B4": ["3 KAUFEN", "2 GRATIS"], "B5": {"lignes": [...], "tailles": [21,21,15], "couleur": [...], "couleur_fond": [...], "police": "...", "images": [a,b], "ignorer": true}}` : textes à écrire sur les badges détectés par `modules/badges.py` (`badges.json` + `badges_planche.jpg` à regarder une fois pour lire les textes d'origine). Badge blanc : fond blanc, texte noir ajusté à la largeur ; badge rond : fond de la couleur mesurée, texte blanc, lignes centrées. `rendu.py` en fait des `patches`.
- `patches` : `{images, rect, remplir:[r,v,b]|"median"|"interp", lignes:[{texte,x,y,taille,graisse,couleur,ancre}]}` repeint un rectangle et y écrit du texte (autocollant, prix, étiquette). Chaque ligne accepte aussi `police` (même valeurs que `textes`, ex. `"DIN Condensed Bold.ttf"` pour un prix en police condensée, BR6 04/10/2026). `"interp"` : fond flou ou en dégradé, interpolation verticale entre les lignes au-dessus et en dessous (titre stylisé que Vmake n'efface pas).
- `textes` : `{images, lignes:[...], y, taille, graisse, couleur, couleur_ombre, decalage, flou, trait}` texte blanc avec ombre, `police`.
  - `police` (aussi dans `sous_titres`) : absent = Space Grotesk ; `"serif"` = Georgia Bold, pour un original à empattements ; ou un nom de fichier de police (`"Didot.ttc"`, `"Baskerville.ttc"`…). Style précis d'un `.ttc` : `"Avenir Next Condensed.ttc#9"` (Heavy Italic). Reprendre la famille de l'original.
  - Émojis : les écrire tels quels dans `lignes` (ex. `"POUR LES ACCROS AUX PLAIDS 🌸☕🎀"`), ils sortent en couleur, aussi dans `blocs`. Sans couleur de peau (💪 et non 💪🏼) : le script la retire. Vmake efface les émojis de l'original : toujours les remettre.
- `blocs` : `"auto"` = sous-titres préparés par `blocs.py` (réglages dans `blocs_auto`, voir `sous-titres-blocs.md`). Sinon à la main : `{images, lignes:[[texte, [x0,y0,x1,y1]], ...], taille}` blocs blancs arrondis qui recouvrent les blocs d'origine ; `taille` = police (46 par défaut), à régler pour que le texte ait la largeur de l'original ; `\n` dans le texte = plusieurs lignes dans un même rectangle.
- `sous_titres` : `{mode:"phrase"|"mots", y, taille, graisse, couleur, couleur_ombre, decalage, flou, trait, max_car_ligne, scinder:{id:[morceaux]}, ids_exclus, images, tenue}`. `images:[a,b]` = plage où les sous-titres peuvent apparaître (début **et** fin, ex. s'arrêter avant la carte de fin). Mode `mots` : `max_mots`, `max_car`, `fusion_min` ; un morceau ne finit jamais sur un petit mot (article, préposition), et la ponctuation isolée (« : », « ? ») reste avec le mot précédent. `majuscules: true` écrit les sous-titres en capitales (original tout en majuscules). `max_car_dur` (ex. 24) : plafond strict, un mot qui ferait dépasser passe au sous-titre suivant (mots composés allemands qui élargissaient le bloc fixe à 720 px, SO1 11/10/2026). `combler: true` : le sous-titre reste affiché pendant les pauses (bloc d'origine toujours visible). Calcul sans rendu : `rendu.fabrique_cues(dossier, fiche, sous_titres, fps, nb_images)` (à écrire dans `cues.json` avant `modules/blocs_fixes.py`). Calés sur l'alignement de la voix.

## Étapes et fichiers produits

| Script | Écrit |
|---|---|
| `analyse.py` | `src.mp4`, `full.wav`, `dm/…`, `analyse.json`, `planche.jpg` |
| `vmake.py` | `clean_vmake.mp4`, `vmake_zones.json` |
| `voix.py` | `tts/<id>.mp3`, `tts/<id>.json` (alignement) |
| `mix.py` | `mix.wav` |
| `blocs.py` | `blocs_src.json` (détection, en cache), `blocs.json` |
| `modules/badges.py` | `badges.json`, `badges_planche.jpg` |
| `modules/filigrane.py` | `filigrane.json` |
| `rendu.py` | `rendu_video.mp4`, `cues.json`, `layout.json` (si rectangles), `<REF>_<LANGUE>_<RATIO>_v01.mp4` |
| `controle.py` | rapport texte, `controle_planche.jpg` |
