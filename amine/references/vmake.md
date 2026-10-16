# Vmake : effacer le texte à l'écran

Vmake (tâche « Subtitle », `SKM0002`) efface le texte sans fond ou sur fond coloré. Commande : `python3 scripts/vmake.py <dossier>` (écrit `clean_vmake.mp4` et `vmake_zones.json`). Dans la fiche, `rendu.zones_vmake: "auto"` reprend le résultat Vmake seulement là où il y avait du texte. La « zone » d'une période est l'union de toutes ses images : une période qui couvre toute la vidéo avec une zone géante signale le plus souvent des sous-titres continus, pas une erreur (03/10/2026, EW1 : zone [8,50,712,1142] sur 85 s, mais 4 % de l'image par image). Lire la zone « typique par image ». Si `vmake.py` affiche « zones auto non fiables » (une zone de plus de 50 % d'une image), passer en zones manuelles.

### texte sans fond : Vmake sans demander (02/10/2026, Peel shot)

**Erreur :** j'ai demandé à l'utilisateur l'autorisation d'envoyer la vidéo à Vmake alors que le SOP dit déjà d'y passer le texte sans fond. Un essai de nettoyage local (floutage de la zone) laissait des taches sur la moquette et des restes de la petite ligne : inutilisable.

**Règles :**
- Texte à l'écran sans fond (contour noir sur image, sous-titres karaoké, légendes) : lancer directement Vmake (tâche « Subtitle », `SKM0002`), sans poser la question. L'envoi de la vidéo et l'usage du quota sont déjà autorisés par le skill.
- Ne pas perdre de temps à tester un nettoyage local de ce type de texte : seul Vmake donne un résultat propre.
- Vmake renvoie le fichier en gros débit (~25 Mo pour 30 s) : toujours réencoder à l'export final.

**Vmake : ne remplacer que la zone nettoyée.** Vmake réencode toute la vidéo et baisse un peu la qualité (écart moyen d'environ 3 niveaux de gris, fichier de 25 Mo pour 30 s). Garder la vidéo d'origine partout, et ne reprendre le résultat Vmake que dans le rectangle du texte effacé (marge de 20 px, bord adouci de 12 px), uniquement sur les images où le texte apparaît.

**Vérifier le nombre d'images de Vmake.** Vmake peut rendre quelques images de moins (gourde : 2277 contre 2281). Comparer les deux fichiers : si le décalage est de 0 partout, c'est simplement la fin qui manque. Garder alors la vidéo d'origine pour ces dernières images.

**Surlignage karaoké coloré (05/10/2026, BL1 marque X).** Vmake efface le texte mais laisse des restes des rectangles violets qui surlignent un mot. Les effacer avant le rendu : `python3 scripts/modules/violet.py clean_vmake_original.mp4 clean_vmake.mp4` (garder une copie de la sortie Vmake d'origine). Le script repère le violet dans la bande des sous-titres et le remplace par interpolation verticale. Seuils à élargir si de fines traces restent sur les bords ; adapter les seuils de couleur pour un autre coloris. Garder aussi les étiquettes d'origine utiles au-dessus des sous-titres avec `zones_vmake.limite`.
**Passer aussi `violet.py` sur la source** (06/10/2026, BL1) : le rendu ne prend la vidéo Vmake que dans les rectangles de texte ; une barre de surlignage posée juste au-dessus du texte vient donc de `src.mp4`. Faire `violet.py source_<x>.mp4 src.mp4` (src.mp4 n'est qu'une copie de la source), puis le rendu. `violet.py` garde maintenant la cadence de la source (avant : forcée à 30 i/s, la vidéo raccourcissait de 1 s sur BL1 et l'image se décalait de la voix).

**Vmake inutilisable sur les vidéos 3D/animées (09/10/2026, BL1 marque X).** Étiquettes fines grises sur mannequin 3D : une partie laissée (SEAMLESS) ; badge doré « UP TO 50% OFF » non effacé ; ligne de garantie dorée qui s'écrit lettre par lettre : abîmée. Pour ces textes, préférer `patches` `interp` (fond sombre ou dégradé) + `textes` ; pour les petites étiquettes techniques en anglais, les garder. Regarder `clean_vmake.mp4` sur les plans à textes avant de construire la fiche dessus.
