# Sous-titres sur blocs blancs (ou colorés)

À lire quand la source a des sous-titres avec un **fond** (blanc, noir, coloré) : on les recouvre par nos propres blocs. Fond blanc : pas de Vmake.

## Procédure automatique (sous-titres en rectangles blancs qui reprennent la voix, 03/10/2026)

1. Après `voix.py` : `python3 scripts/blocs.py <dossier>`. Il repère le texte noir entouré de blanc image par image (marche aussi sur fond clair), regroupe les images en sous-titres d'origine stables, et place la voix française dedans : un sous-titre français par sous-titre d'origine, même moment, même rectangle (marge 3 px), une ou deux lignes comme l'original, une seule taille de police (hauteur des lettres d'origine), jamais de coupure après un petit mot. Il tient compte des remplacements de plans. Écrit `blocs.json`.
2. Lire son résumé : `ÉCART` de mots, rectangles « loin de toute voix » (carte de fin, titre non dit : à traiter à la main), mots « loin de tout rectangle » (la vidéo n'a pas de sous-titres en rectangle pour ces lignes : sous-titres classiques).
3. Fiche : `rendu.blocs: "auto"`. Réglages facultatifs `rendu.blocs_auto` : `images:[a,b]` (plage autorisée, ex. avant la carte de fin), `taille`, `max_car` (30 par ligne), `forcer:[{images, rect, lignes}]` pour un plan mal détecté.
4. `rendu.py` puis `controle.py` : il signale toute lettre d'origine visible hors de nos rectangles (image par image, plans remplacés compris) et les mots affichés contre la voix.

Testé sur EW1 (86 s, suédois, 36 sous-titres) et BM1 (42 s, allemand, police fine, sous-titre qui change de hauteur, 27 sous-titres) : aucun forçage, aucune fuite. Découpage : un nombre reste avec son unité (« 24 mois »), « % » reste avec son nombre, un texte de 3 mots ou moins tient sur une ligne même dans un rectangle de 2 lignes. Un titre en rectangle blanc **qui n'est pas dit par la voix** (hook SL5) reste un `rendu.blocs` écrit à la main.

## Sous-titres blancs sur bandeau coloré (06/10/2026, SO1 marque X, bandeau rouge 139,19,19)

`blocs.py` ne lit que du texte sombre sur blanc. **Pas de Vmake** : il efface le texte mais laisse le bandeau (et change sa teinte), ce qui crée un double bandeau au rendu. Méthode :
1. Détecter le bandeau d'origine image par image avec un filtre de couleur strict (ex. |r−139|<28, v<42, b<42, lignes de plus de 120 px), un rectangle par image.
2. Un premier rendu écrit `cues.json`. Pour chaque sous-titre (du début au début du suivant, la première plage depuis l'image 0), un `rendu.patches` à couleur pleine couvre l'union des bandeaux d'origine (+3 px), coupé quand le bandeau d'origine change de taille.
3. `rendu.sous_titres.fond: {couleur, marge_x, marge_y, rayon}` dessine notre bandeau arrondi sous le texte ; il se fond avec le patch de même couleur.
4. Retirer `zones_vmake` de la fiche, puis rendu + contrôle.

## Patchs `rayon`
`rendu.patches[].rayon` : patch de couleur pleine à coins arrondis.

## Bloc coloré arrondi, karaoké, largeur variable (09/10/2026, BL1 marque X, rose 240,173,253)

Pas de Vmake (il garde des restes du bloc). 1) Détecter le bloc d'origine image par image (filtre de couleur ±22, lignes de plus de 60 px) → `boites_src.json` ; ici toujours y 948-1047, centré, seule la largeur change. 2) `rendu.sous_titres` : texte de la couleur du texte d'origine, `trait` 0, `combler: true` (le sous-titre reste affiché pendant les pauses, comme le bloc d'origine). 3) Calculer les sous-titres avec `rendu.fabrique_cues` (sans rendu), puis un `rendu.patches` par sous-titre : couleur pleine, `rayon` (arrondi d'origine + 2), rectangle = union des blocs d'origine pendant le sous-titre + 3 px, élargi si le texte allemand est plus large (texte + 40 px de chaque côté), plages sans chevauchement. Police proche de Poppins : `DMSans.ttf`, graisse 700, taille 46. Refaire l'étape 3 après chaque changement de voix.

## Règles (valables aussi pour les blocs écrits à la main)

### Cas particulier : traces de sous-titres avec fond après Vmake

Ces règles s'appliquent seulement lorsque la source contient des sous-titres avec un fond blanc, noir ou coloré que Vmake n'a pas entièrement supprimé. Elles ne justifient pas l'ajout automatique d'un fond lorsqu'il n'y a aucune trace à masquer.

1. Analyser les zones restaurées image par image et suivre leur position verticale plan par plan.
2. Mesurer toute la silhouette visible de la trace Vmake, y compris les bords, angles, bosses et extensions ; ne pas se limiter au rectangle principal détecté.
3. Recréer le plus petit fond capable de couvrir entièrement cette silhouette et de contenir tout le texte cible. Aucun morceau de l'ancien fond, aucun mot et aucune lettre ne doivent dépasser. Marge de **3 px maximum** autour de la trace (à 720 px de large) : le bloc doit coller au bloc d'origine, jamais paraître plus épais.
   - Si le bloc d'origine est sur deux lignes, mettre le texte cible sur deux lignes équilibrées au lieu d'une seule ligne dans un grand bloc.
4. Éviter les blocs inutilement grands : raccourcir ou découper le sous-titre en segments naturels de deux lignes maximum quand cela permet de rester proche du bloc source.
5. Garder le bloc aligné verticalement : rester à la même hauteur tant que la trace ne change pas vraiment de niveau (écart de 6 px ou moins) et ne suivre que les vrais changements de niveau. Sans trace (plan sans sous-titre d'origine), garder le niveau du sous-titre en cours ou le dernier niveau utilisé ; ne jamais sauter vers la trace la plus proche.
6. **Un seul bloc pour une suite de sous-titres** : tant que le bloc d'origine reste au même niveau et à peu près à la même taille, les sous-titres consécutifs partagent exactement le même bloc, dimensionné dès le départ sur le plus grand besoin du groupe. Aucun élargissement ni rétrécissement entre deux sous-titres. Ne changer de bloc que sur un vrai changement du bloc d'origine (autre niveau vertical, passage d'une à deux lignes, largeur très différente), de préférence sur une coupe de plan.
   - **Un sous-titre = un seul bloc, de forme constante du début à la fin.** Une même phrase ne change jamais de bloc (ni taille, ni nombre de lignes). Si le bloc d'origine change pendant un sous-titre, redécouper le sous-titre au mot le plus proche du changement (0,3 à 0,5 s maximum), pour que le texte et le bloc changent ensemble. La coupure doit être naturelle : de préférence après une ponctuation, jamais après un petit mot (le, la, de, que…), au moins deux mots de chaque côté sauf fin de phrase. Un reste court rejoint le sous-titre suivant s'il tient dans le même bloc. Sans coupure naturelle possible, garder un seul bloc qui couvre les deux formes pendant tout le sous-titre.
   - Quand la voix fait une pause mais que le bloc d'origine reste affiché, prolonger le sous-titre en cours sur ce bloc ; ne jamais afficher le sous-titre suivant en avance.
   - Une variation passagère se rattache au bloc stable **qui lui ressemble** (même taille, même niveau), pas au plus proche dans le temps : un ancien bloc qui reste quelques images sur le plan suivant appartient au bloc précédent.
   - **Largeur du bloc = largeur du bloc d'origine.** Mesurer le vrai bord du bloc d'origine (ou, pour un fond semi-transparent, la marge réelle autour du texte, ~42 px sur produit test) et centrer notre bloc sur lui ; se baser sur la taille typique du plan (pas sur quelques images parasites), tout en couvrant chaque lettre d'origine. Taille de police réglée pour que le texte ait la même largeur que l'original.
   - **Aucun mot ne doit disparaître** : un calage ou un redécoupage ne doit jamais écraser un sous-titre ; chaque morceau reste au moins 0,5 s, et un sous-titre de moins de 0,4 s est fusionné avec son voisin. Contrôle : `controle.py` (mots affichés contre voix).
   - Retour à la ligne : jamais une ligne qui se termine par un petit mot (le, des, je, mon…), jamais un mot seul sur une ligne, jamais une ligne qui commence par une ponctuation.
   - Ignorer les variations passagères du bloc d'origine (moins de 8 images : coupe, transition, animation d'apparition), en largeur comme en hauteur, même séparées du bloc stable par quelques images vides : mesurer la taille sur la partie stable du plan.
   - Si le bloc d'origine change à moins de 0,4 s du changement de sous-titre (même avec une ou deux images vides entre les deux), caler le changement de sous-titre sur celui du bloc, pour que le bloc ne bouge qu'une fois. Un sous-titre qui disparaît puis réapparaît dans la même phrase (trou de moins de 0,7 s) reste affiché en continu.
   - Ne jamais reporter un gros bloc sur un plan où le bloc d'origine est plus petit : chaque plan garde la taille de son bloc d'origine.
   - Avant de livrer, lister tous les changements de taille et de position du bloc : chacun doit correspondre à un vrai changement du bloc d'origine, et aucun bloc ne doit durer moins de 0,5 s.
7. Si le même sous-titre traverse plusieurs plans, conserver une taille stable fondée sur la plus grande couverture réellement nécessaire pendant cette séquence. Ne pas agrandir ou rétrécir le bloc sans changement de texte ou de trace.
8. Maintenir sans interruption le même texte et son fond pendant les microcoupures d'une ou deux images afin d'éviter tout clignotement. Retirer le bloc uniquement quand la phrase est terminée ou lorsqu'il s'agit d'un véritable passage sans sous-titre.
9. Si un objet blanc touche la trace (ligne de terrain, semelle, bracelet), distinguer l'objet du fond à masquer afin de ne pas transformer tout l'objet en un bloc gigantesque. Un gonflement bref de la trace dû à un objet blanc s'ignore (blanc sur blanc), après vérification à l'image.
10. Utiliser par défaut **Space Grotesk 700** pour ce style validé, avec une taille lisible et un contraste fort, sauf consigne visuelle contraire du projet.
11. Contrôler la vidéo entière avec le son puis sans le son, et inspecter au ralenti les changements de plans, débuts et fins de sous-titres. Comparer côte à côte la zone des sous-titres de la source et de la version cible à une quinzaine de moments.

### blocs blancs des sous-titres (28/09/2026, produit test 4)

**Erreur :** blocs blancs trop épais (marge de 8 px autour de la trace Vmake, 88 à 140 px de haut pour une trace de 72 px). Leur position verticale suivait la trace image par image, donc ils « partaient dans tous les sens ».

**Règles :**
- Marge de 3 px maximum autour de la trace d'origine. Le bloc doit coller au bloc de la vidéo source.
- Si le bloc d'origine est sur deux lignes, mettre le texte sur deux lignes (équilibrées), au lieu d'une seule ligne dans un grand bloc.
- Garder le bloc à la même hauteur tant que la trace ne change pas vraiment de niveau (écart de 6 px ou moins). Ne suivre que les vrais changements de niveau.
- Sans trace (plan sans sous-titre d'origine), garder le niveau du sous-titre en cours ou le dernier niveau utilisé. Ne jamais sauter vers le plan le plus proche.
- Un objet blanc qui touche la trace (ligne de terrain, semelle, bracelet) fait gonfler la détection pendant quelques images : l'ignorer, blanc sur blanc. Toujours le vérifier à l'image.
- Avant de livrer, comparer côte à côte la zone des sous-titres de la source et de la version traduite.

### micro-changements de taille des blocs (28/09/2026, produit test 5)

**Erreur :** le bloc changeait de taille entre deux sous-titres alors que le bloc d'origine ne changeait pas. Deux causes : 2 ou 3 images plus larges autour d'une coupe de plan ont fait élargir le bloc, et l'ancien bloc sur deux lignes du plan précédent, resté 5 images, a imposé un gros bloc sur un plan où l'original est petit.

**Règles :**
- Les sous-titres consécutifs sur le même bloc d'origine partagent un seul bloc, dimensionné dès le départ sur le plus grand besoin du groupe.
- Ne changer de bloc que sur un vrai changement du bloc d'origine (niveau, nombre de lignes, largeur très différente).
- Ignorer les variations de quelques images (8 au maximum), en largeur comme en hauteur.
- Caler le changement de sous-titre sur le changement du bloc d'origine s'ils sont à moins de 0,4 s l'un de l'autre (0,25 s était trop court).
- Ne jamais reporter un gros bloc sur un plan où l'original est plus petit.
- Avant de livrer, lister tous les changements de bloc : aucun ne doit durer moins de 0,5 s.

### une phrase, un seul bloc (28/09/2026, produit test 5)

**Erreur :** « Parfois, ils n'ont même plus envie » passait d'un bloc d'une ligne à un bloc de deux lignes en cours de phrase, parce que le bloc d'origine changeait pendant le sous-titre.

**Règle :** un sous-titre garde un seul bloc de forme constante du début à la fin. Si le bloc d'origine change pendant la phrase, redécouper le sous-titre à un mot naturel au moment du changement (après une ponctuation, jamais après un petit mot). Sinon, un seul bloc qui couvre les deux formes. Vérification : contrôle automatique « aucun sous-titre avec plus d'un bloc ».

### pas de Vmake pour les sous-titres à fond blanc (28/09/2026, idée de l'utilisateur, testée sur produit test 5)

**Constat :** Vmake laissait de toute façon les blocs blancs vides ; nos blocs recouvrent entièrement les blocs d'origine, donc partir de la vidéo originale donne le même résultat, sans coût ni attente, avec une image non retouchée.

**Règles :**
- Fond blanc : vidéo originale + nos blocs + `controle.py` (zéro lettre de texte d'origine visible).
- Sans fond ou fond coloré : Vmake reste nécessaire.
- Une variation passagère du bloc d'origine se rattache au bloc qui lui ressemble, pas au plus proche dans le temps (sinon du texte source peut apparaître quelques images).

### largeur des blocs et mots disparus (28/09/2026, produit test 1)

**Erreur 1 :** blocs 25 à 60 px plus larges que l'original (marge fixe de 50 px au lieu des ~42 réels, plus symétrie autour du centre de l'écran, plus quelques images parasites prises en compte).
**Règle :** mesurer le vrai bord du bloc d'origine, se caler sur sa taille typique, régler la police à la même largeur que l'original.

**Erreur 2 (trouvée en contrôlant, touchait aussi produit test 2, 3 et 5) :** le calage des sous-titres sur les changements de bloc pouvait écraser un sous-titre court : des mots de la voix n'apparaissaient jamais à l'écran.
**Règle :** contrôle automatique `controle.py` (mots affichés contre voix) avant toute livraison ; chaque morceau ≥ 0,5 s, sous-titre < 0,4 s fusionné avec son voisin.

**Légendes qui se construisent ligne par ligne.** Quand la ligne 1 est dans un bloc et que la ligne 2 apparaît plus tard en texte contouré (sans bloc), mesurer l'image où la ligne 2 apparaît. Avant : bloc d'une ligne. Après : bloc de deux lignes, chaque ligne avec son propre bloc, ligne 2 comprise. Le bloc change de forme seulement à ce moment-là. Les blocs sont les rectangles des lignes d'origine (marge de 3 px), arrondis, et s'élargissent seulement si le texte français est plus long.

### ligne 2 sans rectangle, non détectée par blocs.py (04/10/2026, BR6 marque X)

**Constat :** ligne 1 dans un rectangle blanc, ligne 2 en texte blanc contouré sans rectangle (« too loose », « tighter on top »), plus une réplique en texte contouré en bas (« I like your shirt »). `blocs.py` ne voit que le texte noir sur blanc : il a mis toute la phrase dans le rectangle de la ligne 1, et un sous-titre dans la petite bulle « ooohh ». Le prix final est aussi tombé sur une étiquette de la fiche de fin.
**Règles :**
- Avant `blocs.py`, chercher le texte blanc pur hors des rectangles (pixels ≥ 242 sur les 3 canaux, par bande horizontale, image par image) pour repérer les lignes 2 et les répliques sans fond.
- Si la source construit ses légendes ligne 1 (rectangle) + ligne 2 (texte contouré) : écrire `rendu.blocs` à la main, un rectangle par ligne au moment où la ligne apparaît, en calant le texte français sur les changements de ligne de l'original. Réécrire la phrase française sur la même structure que l'original (ex. « Lui est conçu pour être / ajusté en haut / mais plus ample au ventre ») pour que la voix tombe sur ces changements.
- Une réplique non sous-titrée dans l'original (ici une onomatopée « ooohh ») reste telle quelle ; ne pas y poser de sous-titre.
- La voix qui continue sur une carte de fin sans sous-titre d'origine : pas de sous-titre (`blocs_auto.images` ou blocs à la main).

### sous-titres calés sur la voix française, pas sur l'original (04/10/2026, BR6, remarque de l'utilisateur)

**Erreur :** blocs écrits à la main avec les moments d'apparition des sous-titres anglais. La voix française démarre souvent plus tôt : on entendait « Les autres sont… » sous « Cache ton ventre », « Il sublime… » sur un écran vide (15 mots décalés).
**Règle :** un sous-titre apparaît au premier mot dit et reste jusqu'au sous-titre suivant ; seuls les rectangles suivent l'original (ils doivent couvrir son texte à chaque image). Avant le rendu, vérifier mot par mot que chaque mot dit est à l'écran au même moment (0 écart). Une phrase dite sur une carte de fin sans sous-titre d'origine reçoit quand même son sous-titre, dans une zone libre (bande noire).

### Blocs les plus fins possible, jamais de « pavé » (05/10/2026, marque X #1 / BE11, remarque de l'utilisateur)

**Erreur :** blocs blancs pleine largeur sur 2 à 3 lignes (police énorme, grandes marges), y compris sur des plans où il n'y avait aucun sous-titre d'origine à cacher (plans du présentateur que nous avions remplacés). Ça cache l'image (« on voit même plus le poil ») et fait amateur.
**Règles :**
- L'épaisseur du bloc est le défaut n° 1 à éviter : le bloc doit être **le plus fin possible** tout en cachant entièrement le sous-titre d'origine quand il a un fond.
- Reprendre le style de l'original : même taille de police, même graisse, bloc serré autour du texte (marge de 3 px autour de la trace), une ligne par bloc si l'original fait une ligne par bloc.
- Sur un plan sans sous-titre d'origine derrière (plan remplacé, plan ajouté), rien à cacher : utiliser le plus petit bloc du style de la vidéo (taille de l'original), jamais un grand bloc.
- Avant de livrer, comparer côte à côte l'image source et l'image rendue sur plusieurs plans : le bloc ne doit jamais paraître plus épais que celui de la source.
- Toujours partir de la vidéo source d'origine, jamais d'une version déjà traduite par un tiers (miroir, gros blocs, autre timing).

## Sans crédit Vmake : recouvrir des sous-titres SANS fond par des blocs blancs (08/10/2026, SIL7 marque X, décision de l'utilisateur)
Sous-titres d'origine en majuscules blanc/jaune à contour noir, sur une ligne (y ≈ 733-763 à 1280 px).
1. Détecter la boîte du texte d'origine image par image (pixels clairs ou jaunes touchant un contour sombre, plus gros groupe de colonnes) → `sub_boxes.json` ; écarter les boîtes hors de la bande habituelle.
2. Premier rendu pour obtenir `cues.json`. Pour chaque sous-titre : un `patch` blanc = union (boîtes d'origine pendant le sous-titre + 4 px) ∪ (largeur de notre texte + 12 px), hauteur fixe juste au-dessus/au-dessous du texte d'origine. Images où le texte d'origine reste affiché sans sous-titre de notre côté : même patch avec le texte du sous-titre précédent écrit dedans (`lignes`).
3. `sous_titres` : texte noir, sans ombre ni contour, sans `fond` (le patch fait le fond).
4. Grands titres non dits (« DAY 7 », garantie, « TAP BELOW ») et logo : `patches` `remplir:"interp"` + `textes` en tchèque. Vérifier la plage d'images de chaque titre en mesurant les pixels blancs dans son rectangle (un plan suivant avec un t-shirt blanc peut fausser la mesure).
**Erreurs corrigées sur SIL7 v02 → v03 (remarque de l'utilisateur, 08/10/2026) :**
- Texte anglais qui dépassait des blocs (« YOU FEEL SKEPTICAL » plus large que le bloc) : la 1re détection écartait toute image dont la boîte débordait de la bande (un t-shirt blanc faisait grimper y0), donc le bloc ne prenait que la largeur du texte tchèque. Règle : mesurer la largeur dans une **bande fixe** (y du sous-titre ± 3 px), ne jamais jeter une image, puis **vérifier par le calcul** que chaque boîte d'origine est contenue dans un bloc actif à cette image (0 fuite exigée), et relancer la détection sur la vidéo livrée.
- Grands titres oubliés (« DAY 1 », « DAY 30 ») : la planche d'analyse (1 image par plan) ne les montre pas. Règle : avant le rendu, monter une **grille de toute la vidéo, 1 image toutes les 20** (20 colonnes), la regarder en entier et lister **tous** les textes à l'écran (titres, chiffres, logos, CTA) avec leur plage d'images ; puis mesurer chaque plage (pixels blancs dans le rectangle du titre).
**Taille du bloc : priorité absolue à la stabilité (remarque de l'utilisateur, 08/10/2026, SIL7 v03 → v04).** Des blocs qui changent de largeur à chaque sous-titre ou qui se décalent à gauche/droite gênent l'œil, même si chacun est « juste ». Règle par défaut pour des sous-titres d'origine centrés : **un seul bloc centré, même largeur pour toute la vidéo**, calé sur le plus large besoin (texte d'origine + 9 px de chaque côté, texte cible + 16 px). Ne changer de taille que si la vidéo a des passages vraiment différents (autre niveau vertical, deux lignes) — jamais pour un mot court. Détection fiable des lettres d'origine (blanc > 232 ou jaune r>215 g>195 b<90, touchant un noir < 45 à 2 px, groupe de colonnes central), sinon le décor clair gonfle la largeur jusqu'au bord.
**Bloc fixe sans texte dans les pauses (08/10/2026, B8 marque X) :** avec un bloc fixe affiché en continu, les pauses de la voix laissaient des bandes blanches vides. Règle : sur toute image où le bloc est affiché sans sous-titre de notre côté, garder le texte du sous-titre précédent (patch `lignes`, même position et taille que les sous-titres). Sous-titres d'origine blancs sans contour mais à ombre portée : détecter blanc > 228 dont le pixel décalé de 2 px en bas à droite est plus sombre de 70 ; ignorer les flèches/dessins blancs (vérifier les largeurs extrêmes à l'œil).

## Karaoké sans fond, sans Vmake : blocs blancs par niveau (12/10/2026, GL3E marque X → ma marque IT)

Cas : Vmake sans crédits, sous-titres karaoké (texte blanc, mot courant surligné dans un rectangle rose ~54 px de haut) qui changent de niveau à chaque plan (haut, milieu, bas), vidéo 3D animée. Choix de l'utilisateur : blocs blancs.
1. `python3 scripts/modules/karaoke_boites.py <dossier> [--rose 186,96,124]` : repère le rectangle de surlignage par composantes connexes (hauteur 44-64 px, largeur 40-240, remplissage 0,45-0,85 à cause des trous du texte), puis étend en largeur sur le texte blanc contigu → `boites_src.json`. Mesurer d'abord la couleur du rectangle sur un zoom (ici 186,96,124 : un seuil « rose » trop large prend la peau et les muscles).
2. Fiche : pas de `rendu.sous_titres` ; `rendu.blocs: "auto"` ; réglages de découpage dans `rendu.blocs_karaoke` (`max_mots` 4, `max_car` 24).
3. `python3 scripts/modules/blocs_karaoke.py <dossier> --centre 360` : périodes de niveau stable (± 10 px, périodes < 4 images ignorées), un bloc blanc par période, largeur constante = max(largeur d'origine au 95e centile, texte le plus large + 2×22 px), texte noir 34 px ; le texte reste pendant les pauses ; écrit `blocs.json` (`blocs` + `cues`). Relancer après tout changement de voix.
4. Largeur d'origine parfois gonflée par un objet blanc contigu (produit sur fond crème) : vérifier les largeurs par période dans la sortie du script.
5. Plan remplacé (`rendu.remplacements`) : `blocs_karaoke.py` prend seul les boîtes des images donneuses. Badges et filigrane : `modules/badges.py` et `modules/filigrane.py` (voir `fiche.md`, `rendu.badges`, `rendu.filigrane: "auto"`), lancés en même temps que la voix.

### Limites vues sur le lot DE du 13/10/2026 (GL5B, GL8C, GLAA), corrigées localement dans chaque dossier, à intégrer dans les modules
- `karaoke_boites.py` : (a) le remplissage minimal 0,45 rejette les mots courts surlignés (« tap » : 0,42) → seuil 0,38 ; (b) pas de boîte tant que le premier surlignage n'est pas apparu (2 à 4 images après une coupe) ni quand l'ancien sous-titre déborde 2 images sur le plan suivant → sans surlignage, prendre l'étendue du texte blanc de la bande, et combler les trous ≤ 4 images avec la boîte voisine ; (c) fond clair (crème, draps) : le texte blanc contigu gonfle la boîte à toute la largeur → critère « pixel blanc à ≤ 3 px d'un pixel sombre (contour du texte) ou rose » (`GL5B/boites_fix.py`), avertir si une boîte dépasse 600 px ; (d) faux rectangle de la couleur du surlignage hors de la bande centrale → filtrer par position ; (e) hauteur : le surlignage dépasse de 3 à 4 px la boîte du texte → bloc à +4 px.
- `blocs_karaoke.py` : `--centre` par période (sous-titres décentrés quand un cercle occupe la droite du plan) ; option `--eviter x0,y0,x1,y1` pour qu'un bloc ne découpe pas un badge rond du même niveau (`GL5B/blocs_fix.py` : bloc arrêté à x 508) ; voix qui continue après le dernier sous-titre d'origine : prolonger la boîte à la main sur le plan fixe plutôt que de perdre des mots ; voix décalée par l'offre ajoutée : combler les pauses de la source dans `boites_src.json` pour éviter sous-titres de 0,3 s et clignotements.
- `controle.py` : angles morts : le rectangle d'un patch `rayon` est compté couvert (lettres d'origine entre bloc et cercle non signalées : vérifier à l'œil) ; le bouton « Link unten » (patch blanc + texte noir) est pris pour un sous-titre d'origine (« à vérifier » = faux positif) ; nos propres lettres signalées comme fuite quand un bloc recouvre un patch sur une image.
- `rendu.filigrane` : traits épais (> 6 px) mal estimés par la médiane 13×13 et intérieur rendu noir si le masque est plein → retirer le filigrane en amont dans `src.mp4` (`GL5B/fili_src.py` : médiane 31×31, remplissage en cascade σ 3→8→20, grain 0,4×) ; étincelle rose ni plus claire ni plus sombre que le fond : masque chroma r−(g+b)/2 > 6 (`GL8C/manuscrit.py`). `remplir: "median"` prend son échantillon à la première image du patch : pas pendant un fondu (couleur explicite).
- Textes manuscrits sur tableau blanc (`GL8C/manuscrit.py`) : un texte complet dès le début de son élément → `fixe: True`, sinon il se révèle lentement quand le plan dérive.
- zsh : ne pas mettre la commande de la file dans une variable (`$Q python3 …` ne se découpe pas), écrire un `chaine.sh` ; ne pas commencer une ligne par `=`.

### Test de vitesse (13/10/2026, TEST marque X → ma marque DE, 100 s, sans Vmake)
Chronométré de bout en bout : **16 min 40 s** (brief compris), dont machine ≈ 5 min : analyse 45 s, boîtes karaoké 67 s, clone 8 s, voix 56 s (+ 3 reprises de phrases), mixage 1 s, blocs 1 s, rendu 23 s (encodeur matériel), contrôle 85 s (dont 59 s pour « texte d'origine visible »). Le reste est du travail à la main : grille, script, mesure des badges, plans à logos, patchs.
Automatisé le 13/10/2026 (`modules/badges.py`, `modules/filigrane.py`, boîtes donneuses dans `blocs_karaoke.py`) ; la liste d'origine :
1. **Badges blancs à texte noir** (DAY 1, WEEK n) : détection par composantes blanches (min ≥ 225, 30-80 px de haut, 60-260 de large, ≥ 3 % de pixels sombres) dans la bande concernée, plages d'images par présence (blanc > 50 % du rectangle). Entrée : la traduction du texte. À ranger dans `modules/`.
2. **Badges ronds de la couleur du surlignage** (BUY 1 GET 1 FREE, MONEY BACK) : composantes de la couleur rose, 120-220 px, remplissage 0,5-0,9 → rect + rayon + plage. Le badge gauche « MONEY BACK » n'apparaît qu'en milieu de plan : ne pas se fier à une image par plan.
3. **Filigrane fixe** : zone immobile sur toute la vidéo, à repérer seul (ici [290,1125,430,1185], estimé sur un plan à fond uni).
4. **Plan à logos remplacé** : `remplacements` + copie des boîtes des images donneuses dans `boites_src.json` devraient être une seule entrée de fiche (fait à la main ici ; `boites_src_origine.json` gardé).
Pièges vus : `voix.py` sans `enchainer.py` laisse les phrases se chevaucher (mix.py pose chaque phrase à son début sans décaler) : toujours lancer `enchainer.py` puis regarder le retard max (6 s au premier essai → 14 phrases raccourcies → 0,56 s). Un deux-points ou un point au milieu d'une phrase courte allonge la voix de 1 à 2 s (S22 « Jetzt: 3 kaufen, 2 gratis. » 5,1 s → sans ponctuation forte 3,1 s). `enchainer.py` appelle `ffprobe` du PATH (ici `~/.local/bin`), pas celui de `common.py`.
Résultat de l'automatisation (13/10/2026, même dossier TEST) : `badges.py` 45 s, `filigrane.py` 10 s, rendu + contrôle inchangés ; la fiche `rendu` tient en 5 lignes de textes + `filigrane: "auto"`. Le script a corrigé une erreur de la version manuelle : WEEK 3 apparaît à l'image 1452 (fondu au milieu du plan), pas à la coupe 1494. Pièges réglés dans les modules : badge collé à une zone blanche (blouse) invisible aux composantes → seconde passe par rectangle ; doublons pendant un fondu → fusion des pistes qui se chevauchent ; texte comparé localement (fenêtre d'une hauteur de texte) pour voir un glyphe changé ; masque de texte limité à la zone blanche (cheveux autour ignorés) ; images d'estimation du filigrane choisies par finesse du masque (3-30 %), sinon remplissage noir ; `rendu.retire_filigrane` remplit en cascade (σ 4→8→20→60).
