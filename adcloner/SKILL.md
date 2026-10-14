---
name: adcloner
description: Adapter et localiser des publicités vidéo dans une autre langue en préservant la voix, le montage, le rythme et l'efficacité commerciale. Utiliser pour traduire, doubler, sous-titrer, nettoyer, recadrer ou contrôler des vidéos publicitaires, livrées dans le format d'origine de la source.
---

# AdCloner : traduction de vidéos publicitaires

Produire une adaptation qui ressemble à la création originale, pas une traduction mot à mot. Qualité d'abord, et le moins de tokens possible : le travail répétitif est fait par des scripts, l'état d'une vidéo est dans `fiche.json`.

**Avant de commencer, lire seulement** [references/00-coeur.md](references/00-coeur.md) (règles et chaîne de travail). Charger les fiches ci-dessous **uniquement quand le cas se présente**, pas toutes.

| Cas dans la vidéo | Fiche à lire |
|---|---|
| Écrire la fiche vidéo, comprendre la section `rendu` | [fiche.md](references/fiche.md) |
| Sous-titres d'origine sur fond blanc ou coloré | [sous-titres-blocs.md](references/sous-titres-blocs.md) |
| Texte écrit sur l'image (ombre, contour, karaoké, légendes, autocollant) | [texte-libre.md](references/texte-libre.md) |
| Vmake (effacer du texte) | [vmake.md](references/vmake.md) |
| Voix, clonage, durées, mixage | [voix.md](references/voix.md) |
| Logo, emballage, filigrane, fiche produit de fin | [plans-produit.md](references/plans-produit.md) |
| Contrôle final | [controle-qualite.md](references/controle-qualite.md) |

Scripts (dans `scripts/`) : `analyse.py`, `vmake.py`, `voix.py`, `mix.py`, `rendu.py`, `controle.py`, plus `blocs.py` (sous-titres sur rectangles blancs, automatiques), `controle_texte_visible.py` (appelé par `controle.py`), et dans `modules/` : `badges.py` (badges blancs et ronds à recouvrir), `filigrane.py` (filigrane fixe), `enchainer.py` (calage des phrases), `karaoke_boites.py` + `blocs_karaoke.py` (karaoké sans Vmake). Chacun affiche son mode d'emploi sans argument. Modèle de fiche : `templates/fiche-exemple.json`. L'ancien SOP complet est dans `references/archive/` (à ne lire qu'en cas de doute).

## Principes essentiels

- Demander avant de commencer : produit et marque cibles quand la source les mentionne ou les montre, site quand la source en montre ou en dit un. Ne jamais réutiliser les informations d'une adaptation précédente.
- Préserver hook, structure commerciale, montage, ordre des plans et rythme. Durée finale entre 98 % et 102 % de la source.
- Se calquer sur la source : aucune offre, remise, prix ou garantie absente de la source.
- Retirer toute trace de la marque d'origine, y compris sur les micro-plans ; un plan montrant un logo se remplace par un plan de la même vidéo.
- Voix : clonage de la voix d'origine ; si refusé ou peu naturel, voix de remplacement très ressemblante (genre, âge, timbre, énergie, débit). Pas de contournement d'un blocage de vérification.
- Sous-titres générés depuis la voix finale, mêmes mots que la voix. Livrer une seule vidéo, au format d'origine.
- Ne jamais modifier les sources originales ; travailler sur des copies.

## Autorisations et coûts

- **Vmake** : lancer directement pour le texte sans fond ou sur fond coloré (envoi de la vidéo et usage du quota déjà autorisés par l'utilisateur, 02/10/2026). Ne reprendre le résultat Vmake que dans la zone nettoyée.
- **ElevenLabs** : annoncer les caractères consommés ; les clones sont jetables : supprimer celui d'une vidéo dès que ses phrases sont générées, sans attendre la validation (voir `voix.md`) ; ne jamais supprimer une voix de bibliothèque.
- Toute autre opération payante, tout autre envoi externe et toute publication : demander l'autorisation au moment de l'action.
- **Amélioration trouvée en cours de travail** : l'ajouter à la fiche concernée (ou à `00-coeur.md`) sans attendre qu'on la demande.

## Validation

Lancer `scripts/controle.py`, puis signaler clairement ce qui ne peut pas être validé : fidélité vocale, textes non nettoyés, logos restants, écarts de durée, plans remplacés.
