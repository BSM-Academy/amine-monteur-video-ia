#!/usr/bin/env bash
# Livre des fichiers finis sur la branche « livraisons » du dépôt et affiche le lien de téléchargement de la vidéo.
# Usage : bash livrer.sh <video.mp4> [fiche.json controle.txt …]  → livraisons/<AAAA-MM-JJ>/<nom de la vidéo>/
set -e
[ $# -ge 1 ] || { echo "usage : bash livrer.sh <video.mp4> [autres fichiers]"; exit 1; }
for f in "$@"; do [ -f "$f" ] || { echo "fichier introuvable : $f"; exit 1; }; done
racine="$(cd "$(dirname "$0")" && pwd)"
fichiers=(); for f in "$@"; do fichiers+=("$(cd "$(dirname "$f")" && pwd)/$(basename "$f")"); done
jour=$(date +%Y-%m-%d); nom=$(basename "${fichiers[0]%.*}"); dest="livraisons/$jour/$nom"
w=$(mktemp -d)/livraisons; tmp="livraisons-tmp-$$"
cd "$racine"
trap 'git -C "$racine" worktree remove --force "$w" >/dev/null 2>&1; git -C "$racine" worktree prune; git -C "$racine" branch -D "$tmp" >/dev/null 2>&1; true' EXIT
if git fetch -q origin livraisons 2>/dev/null; then
  git worktree add -q --detach "$w" FETCH_HEAD
else  # première livraison : branche vide, sans le code
  git worktree add -q --detach "$w"
  (cd "$w" && git checkout -q --orphan "$tmp" && git rm -rqf .)
fi
mkdir -p "$w/$dest"
cp "${fichiers[@]}" "$w/$dest/"
(cd "$w" && git add livraisons && git commit -qm "Livraison $jour : $nom" && git push -q origin HEAD:livraisons)
slug=$(git remote get-url origin | sed -E 's#\.git$##; s#/+$##' | awk -F/ '{print $(NF-1)"/"$NF}')
echo "Livré. Lien de téléchargement de la vidéo :"
echo "https://github.com/$slug/blob/livraisons/$dest/$(basename "${fichiers[0]}")"
