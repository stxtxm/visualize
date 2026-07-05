#!/bin/bash
# Lance le visualiseur DIRECTEMENT depuis les sources (sans AppImage)
# Les modifications du son sont DÉJÀ appliquées dans les fichiers .py

cd "$(dirname "$0")"
echo "Lancement du visualiseur depuis les sources..."
echo "Modifications audio actives : sounddevice prioritaire + pw-play fallback"
echo ""
exec python3 main.py "$@"