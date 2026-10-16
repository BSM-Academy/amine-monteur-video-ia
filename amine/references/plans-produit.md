# Plans avec logo ou emballage, filigrane, fiche produit de fin

À lire quand un plan montre la marque d'origine (logo, flacon, étiquette, filigrane de site) ou quand la vidéo se termine par une fiche produit à localiser. Remplacement de plans : `rendu.remplacements` (voir `fiche.md`). Fiche de fin et étiquettes : scripts à écrire pour la vidéo, d'après les méthodes ci-dessous.

### logos concurrents (28/09/2026, produit test 4)

**Erreur trouvée dans une version précédente :** le logo concurrent restait visible sur des plans d'une seule seconde et sur des flashes de 2 à 10 images.

**Règle :** détecter toutes les coupes de plan, y compris les micro-plans, et inspecter chaque plan où apparaît le produit en gros plan (zoom), pas seulement une planche d'images à 1 image par seconde.

**Emballage concurrent lisible (ex. « MARQUE X » sur un flacon tenu en main).**
- Je n'ai pas réussi à remplacer l'étiquette image par image : le masque de couleur mélange la main, les murs clairs et le dessin de l'étiquette. Sur un plan fixe et net (image générée) ça marche, pas sur un flacon tenu à la main.
- Appliquer la règle du SOP : remplacer le plan par une image du plan voisin, sans le flacon. Prolonger le plan précédent en le jouant à l'envers (du dernier bon point jusqu'à 1 s en arrière), ou en va-et-vient sur les 25 dernières images d'un plan calme. Ne jamais rejouer un plan entier : on voit le saut.
- Commencer le remplacement à la première image de la transition (flash blanc, fondu) : sinon une image éclaircie reste visible.
- Ne remplacer que les images où l'emballage est lisible.

**Plans avec flacon lisible, plusieurs passages (marque X).**
- Remplacer chaque plan par des images de la même vidéo : femme qui parle sans flacon pour les plans parlés, gros plans de gélules ou schémas pour les plans d'ingrédients.
- Éviter les 5 premières images d'un plan donneur (fondu, flou).
- Un plan donneur peut être réutilisé s'il est loin dans la vidéo.
- Vérifier que le plan donneur ne montre pas lui-même le logo ou l'emballage (03/10/2026, EW1 : homme penché, logo sur la ceinture). Une zone Vmake manuelle doit aussi couvrir les images de sortie qui reprennent ce plan comme donneur.
- Aux images de transition floues qui montrent encore le flacon, tenir la première image nette du plan suivant.
- Un flacon trop petit pour être lu (moins de 8 px de hauteur de texte) peut rester, mais le signaler.
- Les post-it écrits à la main sont du texte à l'écran : les traduire, ou remplacer le plan.

**Filigrane de site fixe (ex. concurrent.com).** Estimer la transparence du filigrane sur un plan à fond uni, puis le retirer en remplissant la zone depuis ses bords (flou normalisé) et en réinjectant le grain local. Remplacer ensuite par le site cible (ex. ma-boutique.com) au même endroit, avec la même transparence. Il est absent des premiers plans : trouver l'image où il apparaît.

**Grand filigrane semi-transparent gris sur toute la vidéo (06/10/2026, SO2 marque X).** Il éclaircit les fonds sombres et assombrit les clairs. Échecs : inversion du mélange alpha (alpha et couleur introuvables sur des plans très variés), remplissage flou (fantôme et bruit sur les motifs), Vmake « Smart Removal » SKM0003 (filigrane intact, image abîmée). Règle : regarder la planche d'analyse en zoom au centre de l'image ; si un filigrane de marque couvre la vidéo, chercher tout de suite une autre version de la même pub (même script, autre rendu) sur Trendtrack. SO1 (version squelette, sans filigrane) a remplacé SO2.

**Fiche produit de fin.** Elle se refait image par image sur la vidéo d'origine, sans la reconstruire :
- repérer les couleurs et les rectangles des éléments (prix, étiquettes, bouton, marque) ;
- suivre l'opacité de l'apparition en fondu et la position du bouton qui glisse ou pulse ;
- redessiner chaque texte avec la même opacité, en gardant les images du produit.

**Fiche produit de fin avec zoom lent.** L'étiquette change de taille à chaque image.
- Se caler sur le bouchon noir du flacon (seuil de luminosité à 80) : sa largeur donne toute la géométrie de l'étiquette. Mesurer les proportions sur deux images, puis les appliquer à chaque image.
- Remplir la zone avec la teinte de l'étiquette prise colonne par colonne, pour garder l'ombrage du cylindre.
- Redessiner le contenu en français (emblème, titre, encadré, puces, mention), chaque texte réduit pour tenir dans son cadre.
- Le bouton rose se refait en copiant son dégradé vertical, pris juste avant le début du texte.
- Les images de début d'animation (flou, apparition) peuvent garder un petit défaut : le signaler.

### logo imprimé sur le produit (03/10/2026, EV179 V-Shape)

**Constat :** la planche d'analyse ne montrait pas le petit « LOGO » imprimé sur la poitrine des débardeurs (plan 418-461, produits posés à plat) ; trouvé seulement en zoomant. Vmake n'efface pas non plus un titre stylisé (« BUY TWO GET ONE FREE ») : il a fallu `remplir: "interp"` + texte recréé, découpé par paliers de 3 images pour suivre le zoom.
**Règle :** pour un vêtement ou un objet de marque, faire une planche recadrée sur le produit dans chaque plan où il apparaît en gros plan, avant le rendu. Plan lisible : remplacer par un plan de la même vidéo sur le même thème (ici le collage avant/après).

### plans de remplacement fournis par l'utilisateur (06/10/2026, N7 marque X → ma marque IT)

**Cas :** L'utilisateur donne un dossier Drive de plans déjà refaits avec son flacon (souvent 1080x1920 à 24 i/s, avec leurs propres sous-titres anglais et parfois « MARQUE X » dans le texte).
**Méthode :**
- Télécharger sans passer le fichier par le contexte : `curl -L "https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t"` (lister les ID avec l'outil Drive `search_files`, `parentId = '<dossier>'`, deux pages). Éliminer les doublons (même taille).
- Choisir le plan le plus proche du plan d'origine (même personne, même geste). Éviter les fins de clip qui finissent sur une fiche « Buy 2 get 1 » ou une offre absente de la source.
- Insérer les plans **avant Vmake** dans une copie de la source (`src_origine.mp4` gardé, nouveau `src.mp4` = montage), mis à l'échelle et à la cadence de la source : Vmake efface alors aussi les sous-titres des plans insérés.
- Repérer flash de début et coupe de fin du clip (`select='gt(scene,0.1)',showinfo` sans `-v error`, plus `signalstats` pour un flash blanc) et couper **avant** la conversion de cadence, sinon une image flashée ou une image d'un autre plan passe.
- Plan donneur trop court : ralentir légèrement (0,9) puis aller-retour, jamais au-delà.

### Plans avec flacon concurrent régénérés par IA (12/10/2026, BE13 marque X → ma marque IT)

**Cas :** 5 plans 3D (fraise/banane) montrent le flacon « MARQUE X » lisible ; la bibliothèque de rushs ma marque ne couvre que la scène du comptoir. Décision de l'utilisateur : régénérer les plans manquants, le moins de secondes possible.
**Méthode validée :**
- Image de départ = **une image nette du plan** (jamais la 1re image : flash ou fondu de transition, le défaut passe dans la génération), éditée par GPT Image (« recrée à l'identique, remplace le flacon par celui de la 2e référence, retire le sous-titre ») : 10 crédits.
- Animation : **Kling 3.0 pro** (`kling_video`, `mode: pro`) = **18 crédits/s** (1080p), 3,5 fois moins cher que Seedance 2.5 (~63 crédits/s). L'outil Kie exige `multi_shots: true` + `multi_prompt: [{prompt, duration}]` même pour un seul plan (sinon erreur « multi_shots cannot be empty »). Générer 0,5 à 1 s de plus que le plan, couper ensuite. Le coût est à la seconde : regrouper des plans dans une seule génération ne fait pas d'économie, réutiliser un rush oui.
- Contrôler chaque clip à 8 i/s : Kling peut faire un geste parasite (tour sur soi flou) ; garder les parties propres.
- Insertion : `montage_src.py` dans le dossier de travail reconstruit `src.mp4` (même nombre d'images, 25 i/s, 720x1280) à partir de `src_origine.mp4`. **Lancer `blocs.py` avant de remplacer `src.mp4`** : `blocs_src.json` (cache) garde la détection des bandeaux d'origine, donc nos bandeaux restent au bon endroit sur les plans insérés.
- Titres rouges sur boîte blanche (« ONE. », « No flinching ») : mesurer la boîte blanche image par image autour du texte rouge, `patches` blancs `rayon: 10` + texte rouge (Montserrat ExtraBold, taille 38 à 42 pour remplir la boîte comme l'original).
- Carte de fin : refaite en PIL sur le rush flouté (packshot détouré généré par GPT Image `background: transparent`, bandeau d'offre, badge garantie, bouton qui pulse), mêmes moments d'apparition que l'original.
- **Reproduire l'ACTION du plan, pas une image fixe (remarque de l'utilisateur, 12/10/2026).** Erreur sur BE13 : prompt écrit d'après l'image 0 (avant le geste), action inventée (« montre le flacon ») alors que la fraise applique la crème sur la banane. Règle : grille du plan d'origine 1 image sur 8, décrire le geste réel et son moment, donner à Kling une image de début ET une image de fin d'action éditées (`image_urls` : 2 images), puis comparer original / nouveau plan côte à côte sur la même grille (geste, moment), pas seulement le flacon et le style.

### Filigrane sombre et badges ronds (12/10/2026, GL3E marque X)

- **Filigrane gris semi-transparent** (« marque-x » en bas, sur toute la vidéo) : `rendu.filigrane` avec `sombre: true` (l'estimation prend aussi ce qui assombrit le fond), `estimer_sur` = images sur fond uni clair, `seuil` 0,08. Vérifier le masque une fois (image alpha) avant le rendu.
- **Badge rond** (offre, garantie) : pas de Vmake. Mesurer le cercle intérieur (composante de sa couleur) et l'anneau blanc ; `rendu.patches` avec `rect` = cadre du cercle, `rayon` = rayon, `remplir` = couleur médiane du cercle, puis `lignes` en blanc ; largeur de chaque ligne vérifiée contre la corde du cercle à sa hauteur (`police(taille).getlength`). Repérer les images d'apparition (anneau partiel) : elles restent non patchées si elles durent 2-3 images, à signaler.
- **Bouton qui se balance** (« Link below 👇 ») : position par image (lignes blanches ≥ 240 dans la zone), un patch blanc par position avec le texte ; les patchs acceptent maintenant les émojis en couleur.
