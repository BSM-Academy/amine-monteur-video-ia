# Contrôle qualité final

Commande : `python3 scripts/controle.py <dossier> [--planche]`. Le script vérifie seul la durée, le format, la cadence, le son, les mots affichés contre la voix finale, les sous-titres trop courts et les phrases trop longues. Reste à faire à la main : fidélité de la voix (écoute), micro-plans avec logo, qualité des plans remplacés.

## Étape 9 : Contrôle qualité final

Regarder la vidéo en entier avec le son, puis sans le son.

### Contenu

- [ ] Hook et promesse préservés
- [ ] Sens validé via la traduction française de contrôle
- [ ] Marque, produit, offre, prix, garantie et CTA corrects
- [ ] Aucune trace visuelle ou audio de la source
- [ ] Aucun argument inventé

### Audio

- [ ] Plus aucune voix source audible
- [ ] Même voix que l'originale, ou voix de remplacement fortement ressemblante
- [ ] Voix naturelle dans la langue cible, avec un timbre, une énergie et un débit cohérents
- [ ] Aucun passage artificiellement accéléré ou coupé
- [ ] La dernière phrase se termine avec la fin utile de la vidéo, sans silence final injustifié
- [ ] Musique et bruitages conservés
- [ ] Lip sync acceptable si nécessaire

### Sous-titres et textes

- [ ] Sous-titres générés depuis la voix finale
- [ ] Chaque titre à l'écran (jour, prix, garantie) tombe au moment où la voix dit le mot, avec le même écart que la source (voir `voix.md`)
- [ ] Aucun silence de plus d'1 s dans la voix ni blanc dans les sous-titres là où la source parle (`controle.py` : trous de voix)
- [ ] Orthographe relue mot par mot
- [ ] Maximum deux lignes, lisibles et synchronisées
- [ ] Les mots affichés correspondent à la voix finale et les premières secondes sont précisément calées
- [ ] Aucun texte ni aucune lettre ne dépasse de son fond
- [ ] Aucune trace d'ancien fond ne dépasse derrière le nouveau bloc
- [ ] Aucun double bloc, changement de taille injustifié ou clignotement du même sous-titre
- [ ] Blocs aussi fins que le bloc d'origine (marge de 3 px max) et alignés verticalement, sauf vrai changement de niveau de la trace
- [ ] Chaque sous-titre garde un seul bloc du début à la fin (aucune phrase qui change de forme de bloc)
- [ ] Aucun micro-changement de taille entre sous-titres consécutifs ; aucun bloc de moins de 0,5 s ; aucun gros bloc reporté sur un plan où l'original est petit
- [ ] Tous les textes incrustés localisés
- [ ] Rien d'important masqué ou hors cadre
- [ ] `controle.py` : tous les mots affichés, aucun sous-titre de moins de 0,4 s
- [ ] Blocs de la même largeur que les blocs d'origine
- [ ] Fond blanc traité sans Vmake : `controle.py` ne signale aucune lettre de texte d'origine hors de nos rectangles
- [ ] Aucun logo concurrent visible, y compris sur les micro-plans et flashes de quelques images ; les plans remplacés proviennent de la même vidéo ou d'une autre vidéo du même produit

### Technique

- [ ] Durée finale entre 98 % et 102 % de la source
- [ ] Export dans le format d'origine contrôlé (même ratio et mêmes dimensions que la source)
- [ ] Dimensions et orientation vérifiées
- [ ] Référence et version correctement nommées
- [ ] Lecture intégrale effectuée, même pour les vidéos longues
