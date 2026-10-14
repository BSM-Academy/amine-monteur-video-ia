#!/usr/bin/env bash
# Livre des fichiers finis sur la branche « livraisons » du dépôt et affiche leurs liens de téléchargement.
# Usage : bash livrer.sh <video.mp4> [autres fichiers]
set -e
[ $# -ge 1 ] || { echo "usage : bash livrer.sh <video.mp4> [autres fichiers]"; exit 1; }
racine="$(cd "$(dirname "$0")" && pwd)"
fichiers=(); for f in "$@"; do fichiers+=("$(cd "$(dirname "$f")" && pwd)/$(basename "$f")"); done
jour=$(date +%Y-%m-%d); w=$(mktemp -d)/livraisons
cd "$racine"
if git fetch -q origin livraisons 2>/dev/null; then
  git worktree add -q --detach "$w" FETCH_HEAD
else  # première livraison : branche vide, sans le code
  git worktree add -q --detach "$w"
  (cd "$w" && git checkout -q --orphan livraisons-neuve && git rm -rqf .)
fi
mkdir -p "$w/livraisons/$jour"
cp "${fichiers[@]}" "$w/livraisons/$jour/"
(cd "$w" && git add livraisons && git commit -qm "Livraison $jour : $(basename "${fichiers[0]}")" && git push -q origin HEAD:livraisons)
slug=$(git remote get-url origin | sed -E 's#\.git$##; s#/+$##' | awk -F/ '{print $(NF-1)"/"$NF}')
git worktree remove --force "$w"
echo "Livré. Liens de téléchargement :"
for f in "${fichiers[@]}"; do echo "https://github.com/$slug/blob/livraisons/livraisons/$jour/$(basename "$f")"; done
