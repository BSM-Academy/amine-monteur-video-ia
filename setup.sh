#!/usr/bin/env bash
# Script de démarrage de l'environnement cloud « Atelier » (claude.ai/code) : à déclarer comme setup script.
set -e
cd "$(dirname "$0")"
python3 -m pip install --quiet -r requirements.txt
mkdir -p ~/.local/share/fonts && cp -n fonts/*.ttf ~/.local/share/fonts/ 2>/dev/null || true
which ffmpeg >/dev/null || { echo "ffmpeg absent" ; exit 1 ; }
python3 -c "import numpy, scipy, PIL; print('deps ok')"
echo "setup ok"
