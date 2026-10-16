# Texte sans bloc : sous-titres, textes du haut, autocollants

À lire quand le texte d'origine est écrit **directement sur l'image** (blanc avec ombre ou contour, karaoké, légendes, autocollant de commentaire). On le fait effacer par Vmake (`vmake.md`), puis on le refait en français avec `rendu.textes`, `rendu.sous_titres` et `rendu.patches` (voir `fiche.md`).

**Sous-titres sans bloc (texte blanc sur l'image).**
- Mon style : texte blanc Space Grotesk 700 d'environ 36 px, avec une ombre noire douce, à la position des sous-titres d'origine.
- Nettoyer avec Vmake toute la zone des sous-titres d'origine quand ils sont présents en continu.
- Découper chaque phrase de la voix à ses ponctuations (« : » ou « , »), avec deux lignes de 30 caractères au maximum, et caler chaque morceau sur l'alignement ElevenLabs.
- Garder au moins 0,5 s par morceau, et ne jamais empiéter sur le suivant.

**Sous-titres mot par mot (karaoké).** Relever la taille et la position d'origine (ici centre vers 69 % de la hauteur, texte blanc, ombre violette décalée vers le bas-droite). Découper la voix en morceaux de 1 à 3 mots (18 caractères au plus), cassés à la ponctuation, calés sur l'alignement ElevenLabs, avec les morceaux de moins de 0,38 s fusionnés.

**Textes du haut avec ombre (sans bloc).** Repérer leurs fenêtres en comparant la vidéo d'origine et la version Vmake : le recouvrement entre images consécutives tombe quand le texte change. Refaire chaque texte en Space Grotesk 700 blanc avec une ombre noire douce, à la même position, sur deux lignes au plus.

**Autocollant de commentaire (carte blanche avec avatar, style TikTok).** Vmake laisse des traces de texte dans la carte. Garder la carte et l'avatar d'origine, repeindre en blanc seulement la zone des textes, puis réécrire les lignes en français dans la taille qui tient dans la carte (réduire la police au besoin, raccourcir le texte). Repérer sa position une fois : elle ne bouge pas.

**Étiquette à fond uni (ex. « OTHER BRANDS » blanc sur noir, 03/10/2026, BD3).** Pas de Vmake : `rendu.patches` à couleur pleine (`remplir:[r,v,b]` de l'étiquette) sur l'intérieur de l'étiquette, puis texte recréé dans `lignes`.

**Barre ou boîte sombre semi-transparente (03/10/2026, TC1).** Vmake garde la boîte et efface le texte : réécrire le texte blanc dans la boîte, avec un français qui tient dans la largeur de la boîte d'origine.

**Texte à l'écran sans voix.** Un texte affiché que la voix ne dit pas (ex. « Hides your belly ») se traduit et reste affiché sans voix. Ne pas lui en inventer une.

**Sous-titres sur les textes recréés (03/10/2026, Peel shot).** Avec `sous_titres.y` à 892, les sous-titres mot par mot passaient sur « Regarde la peau sèche… » (y 815 à 925) et « 1 acheté = 1 offert ! » (y 855). Règle : placer `sous_titres.y` en dehors de la hauteur de tous les `rendu.textes` (ici 1040), et le vérifier sur la planche de contrôle.

**Émojis et police du titre (03/10/2026, couverture FB3).** Vmake a effacé les émojis 🌸☕🎀 du titre, et le titre est ressorti en Space Grotesk alors que l'original avait une police à empattements. Règle : relever les émojis et la famille de police de chaque texte sur la planche d'analyse, puis les reprendre dans la fiche (`police`, émojis dans `lignes`, voir `fiche.md`).

**Émojis d'origine à garder (03/10/2026, FB3 couverture).** Vmake efface mal les émojis : il laisse des restes qui varient d'une image à l'autre. Ne pas les redessiner : garder ceux de la source avec `rendu.zones_vmake: {"mode":"auto","exclure":[[x0,y0,x1,y1]]}` sur leur rectangle (marge d'environ 10 px). Repérer le rectangle sur une image recadrée de la source, puis vérifier sur 3 ou 4 moments de la vidéo.
