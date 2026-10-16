# Amine : cœur de la procédure

Adapter une publicité vidéo dans une autre langue en gardant son impact commercial, son montage, son rythme, avec une voix naturelle, des sous-titres exacts et **un seul export au format d'origine**. Fonctionne pour toute paire de langues.

## Règles qui ne changent jamais

1. **Durée** : durée finale ÷ durée source entre 0,98 et 1,02. Sinon, reprendre le script, pas le montage.
2. **Montage** : mêmes plans, même ordre, mêmes moments. Ce qui change : voix, sous-titres, textes à l'écran, marque, et offre/CTA seulement si le marché l'exige.
3. **Se calquer sur la source** : vérifier l'offre dans la voix **et** dans les textes affichés, jusqu'à la dernière image (la transcription peut manquer la fin). Reprendre l'offre, la garantie et les preuves telles quelles. Ne rien ajouter (pas de remise, d'urgence, de garantie absentes de la source). Le site cible remplace le site ou le CTA de la source.
4. **Adapter, pas traduire** : phrases courtes, langage naturel du marché, même hook, problème, mécanisme, preuves, bénéfices, offre, CTA, ton.
5. **Retirer toute trace de la marque d'origine** : logo, produit, emballage, URL, prix, offre, voix, sous-titres, y compris sur les micro-plans. Une trace restante bloque la livraison.
6. **Format d'origine** : même ratio et mêmes dimensions, H.264 MP4, même cadence. Pas de recadrage ni de version 9:16 ou 4:5 sans demande.
7. **Nommage** : `REFERENCE_LANGUE_FORMAT_v01.mp4` (le script le fait).
8. **Sources** : ne jamais modifier une source, travailler sur des copies. Choisir une source dans la bonne langue (pas déjà dans la langue cible, pas sans voix).
9. **Vidéo déjà adaptée dans une autre langue** (ex. on donne la version CZ pour faire la DE) : repartir de la **source d'origine** (`src_origine.mp4` du dossier de travail précédent) et réutiliser `analyse.json`, `dm/`, `clean_vmake.mp4`, `vmake_zones.json`, la section `rendu` et `echantillon_voix.mp3` (pour recloner) : zéro Vmake. Ne refaire que le script, les textes affichés et la carte de fin (SIL6 DE, 09/10/2026).

## Étape 0 : diagnostic du type de vidéo (avant tout, demandé par l'utilisateur le 08/10/2026)

Monter une **grille de toute la vidéo** (1 image toutes les 15 à 20, 16-20 colonnes) et la regarder en entier. Noter dans `fiche.json` (`notes`) : le type de sous-titres, la liste des titres/logos/prix/écran de fin avec leurs plages d'images, la méthode, le coût Vmake annoncé (2 crédits par seconde de vidéo).

| Type de sous-titres d'origine | Méthode | Vmake |
|---|---|---|
| 1. Fixes, 1 ligne, avec fond (blanc/couleur) | nos blocs sur les blocs d'origine (`blocs.py`, `sous-titres-blocs.md`) | non |
| 2. Fixes, 1 ligne, sans fond | Vmake puis nos sous-titres ; sans crédit : bloc blanc fixe centré (`scripts/modules/blocs_fixes.py`) | oui / non |
| 3. Mobiles ou karaoké, sans fond | Vmake obligatoire, puis nos sous-titres au même endroit | oui |
| 4. Mobiles, avec fond (boîte qui suit) | boîte de même couleur image par image (méthode SB1/SO1) ; pas de Vmake (il laisse la boîte) | non |
| 5. Aucun sous-titre | nos sous-titres, sans fond (choix de l'utilisateur) | non |
| + Grands titres, logos, prix, écran de fin | patch `interp` + `textes`, ou Vmake ; toujours relevés sur la grille | selon |

## Chaîne de travail (une vidéo, une conversation)

1. **Fiche et analyse.** Créer un dossier de travail, copier `templates/fiche-exemple.json` en `fiche.json`, puis `python3 scripts/analyse.py <video> <dossier>`. Demander à l'utilisateur ce qui manque : produit et marque cibles, site (si la source en montre ou en dit un), offre, voix. Regarder la planche `planche.jpg` **une fois** pour repérer logos, emballages, textes à l'écran et plans à remplacer.
2. **Nettoyer le texte d'origine.**
   - Sous-titres sur fond blanc : on les recouvre par nos blocs, placés automatiquement par `blocs.py` après la voix (`sous-titres-blocs.md`). Texte sur un rectangle blanc (ou d'une couleur unie) = **pas de Vmake** : le vérifier sur la planche avant de lancer `vmake.py`.
   - Texte sans fond, karaoké, légendes : `python3 scripts/vmake.py <dossier>` (`vmake.md`), puis le refaire (`texte-libre.md`).
3. **Script français.** À partir des phrases de `analyse.json` (le budget en caractères est indiqué par phrase), écrire une version courte par phrase, avec les noms de la fiche. Compter 20 à 30 % de mots en moins. Remplir `lignes` dans la fiche (texte, début, fin de fenêtre).
4. **Voix.** `scripts/voix.py --cloner`, puis `scripts/voix.py`, puis **toujours** `scripts/modules/enchainer.py` (retard max à garder < 0,6 s, sinon raccourcir le script : les phrases se chevauchent dans le mixage sinon), puis `scripts/mix.py` (`voix.md`). Pendant la voix, lancer en parallèle `scripts/modules/badges.py` et `scripts/modules/filigrane.py` (section `rendu`, `fiche.md`). Corriger les phrases signalées « TROP LONG » (ratio > 1,10) ; écouter celles marquées « à écouter ». `voix.py` réécoute chaque phrase (mots sautés, mots déformés, accent) et reprend seul les mauvaises (`voix.md`).
5. **Plans à traiter.** Badges et filigrane : regarder `badges_planche.jpg` une fois, écrire les textes dans `rendu.badges`, mettre `rendu.filigrane: "auto"`. Logo, flacon, fiche de fin : `plans-produit.md`. Les décisions vont dans la section `rendu` de la fiche.
6. **Rendu.** `python3 scripts/rendu.py <dossier>` produit la vidéo livrable (section `rendu` décrite dans `fiche.md`).
7. **Contrôle.** `python3 scripts/controle.py <dossier> --planche` : rapport texte court, plus une planche à regarder une fois (`controle-qualite.md`). Corriger la fiche et relancer le rendu si une alerte apparaît.
8. **Livrer** le fichier du dossier de travail dans le dossier de sortie demandé, et signaler ce qui n'a pas pu être validé (fidélité de la voix, plans remplacés, micro-défauts).

## Sous-titres, textes à l'écran, lip sync (rappel)

- Sous-titres générés depuis la **voix finale**, jamais depuis la source ; mêmes mots que la voix (sauf graphie visuelle, ex. `exemple.com` dit « exemple point com »). Deux lignes courtes au plus, police lisible à fort contraste, à l'emplacement des sous-titres d'origine, sans masquer visage, produit, démonstration ni CTA. Relire marques, nombres et unités.
- Caler début et fin phrase par phrase (surtout les premières secondes). La voix va jusqu'à la fin utile de la vidéo, sans longue plage silencieuse après le CTA, sans être coupée par la dernière image.
- Textes à l'écran : les lister tous, les traduire ou les recréer, remplacer logos, prix, garanties, comparatifs et CTA, sans débordement.
- Lip sync : seulement quand la bouche est bien visible et que ça apporte un gain ; sinon plan de coupe. Produit, B-roll, animation, visage trop petit : pas de lip sync.
- Les noms de produit, marque, site, offre et CTA sont ceux du brief courant, jamais ceux d'un projet précédent.

## Économie de tokens (sans toucher à la qualité)

- Une conversation par vidéo. L'état de la vidéo est dans `fiche.json` et le dossier de travail : une conversation neuve peut reprendre sans tout relire.
- Charger seulement les fiches utiles à la vidéo (tableau du `SKILL.md`). Ne pas relire ce cœur à chaque étape.
- Les contrôles passent par les scripts. Images à regarder : `planche.jpg` (étape 1) et `controle_planche.jpg` (étape 7), pas plus de deux planches par vidéo, sauf défaut précis à examiner.
- Ne jamais réécrire un script déjà fourni : adapter la fiche. Écrire un script nouveau seulement pour un cas rare (fiche produit de fin, étiquette) et le ranger ensuite dans `scripts/modules/` s'il est réutilisable.
- Vmake : une seule demande d'accord par lot (si l'utilisateur ne l'a pas déjà donnée dans le skill).

## Brief à demander avant de commencer

Langue cible et marché, marque et produit cibles (si la source en parle), site cible (si la source en montre ou en dit un), offre/prix/garantie (par défaut, ceux de la source), voix souhaitée (par défaut, clonage de la voix d'origine), dossier de sortie.

## Texte d'adaptation (prompt)

```text
Tu es un copywriter natif en [LANGUE CIBLE], spécialisé en publicité Meta, UGC et direct response pour le marché [PAYS].
Adapte le script ci-dessous. Ce n'est pas une traduction littérale. Conserve promesse, émotion, mécanisme et ordre des arguments ;
langage naturel du marché ; respecte chaque durée ; phrases courtes plutôt que voix accélérée ; remplace [MARQUE SOURCE] par [MARQUE CIBLE] ;
applique exactement l'offre, la garantie et le CTA fournis ; ne rien inventer hors de la source. Pour chaque ligne : version courte
prioritaire, version un peu plus longue, traduction française de contrôle, nombre de mots et alerte de dépassement.
```
