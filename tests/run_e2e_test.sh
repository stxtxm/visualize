#!/bin/bash

# Script pour exécuter les tests E2E dans le conteneur avec Xvfb
# Xvfb permet d'exécuter des applications graphiques sans affichage physique

echo "=========================================="
echo "Test E2E: Affichage vidéo dans la GUI"
echo "=========================================="
echo ""

# Nettoyer d'abord
podman stop -t 1 e2e-test 2>/dev/null
podman rm -f e2e-test 2>/dev/null

# Démarrer Xvfb sur l'affichage 99
echo "Démarrage de Xvfb..."
Xvfb :99 -screen 0 1024x768x24 &
XVFB_PID=$!
sleep 1

# Exporter l'affichage pour Xvfb
export DISPLAY=:99

# Lancer le test dans le conteneur avec Xvfb
echo "Lancement du test dans le conteneur..."
podman run --rm --name e2e-test \
    --volume "$(pwd)/..":/app:ro,Z \
    --env NO_SOUND=1 \
    --env SDL_VIDEODRIVER=x11 \
    --env SDL_RENDER_DRIVER=software \
    --env SDL_AUDIODRIVER=dummy \
    --env DISPLAY=:99 \
    psychedelic-visualizer:latest \
    python3 /app/tests/test_e2e_gui.py

TEST_RESULT=$?

# Arrêter Xvfb
kill $XVFB_PID 2>/dev/null

if [ $TEST_RESULT -eq 0 ]; then
    echo ""
    echo "✓ Tous les tests E2E ont réussi !"
else
    echo ""
    echo "✗ Certains tests E2E ont échoué"
fi

exit $TEST_RESULT
