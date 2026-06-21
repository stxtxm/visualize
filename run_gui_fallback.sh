#!/bin/bash

# Script de lancement de la GUI avec fallback automatique
# Si PulseAudio n'est pas disponible, lance en mode NO_SOUND

echo "=========================================="
echo "Lancement du Visualisateur Psychédélique (avec fallback)"
echo "=========================================="
echo ""

# Chemins par défaut
AUDIO_DIR="${AUDIO_DIR:-${HOME}/Music}"
OUTPUT_DIR="${OUTPUT_DIR:-${HOME}/Videos}"

# Créer les dossiers si ils n'existent pas
mkdir -p "$AUDIO_DIR" "$OUTPUT_DIR"

echo "Dossiers montés:"
echo "  Audio:  ${AUDIO_DIR}"
echo "  Output: ${OUTPUT_DIR}"
echo ""

# Vérifier si PulseAudio est disponible
PULSE_AVAILABLE=false
if [ -d "/run/user/${UID}/pulse" ] && [ -S "/run/user/${UID}/pulse/pulseaudio.socket" ]; then
    PULSE_AVAILABLE=true
    echo "✓ PulseAudio détecté sur l'hôte"
else
    echo "⚠ PulseAudio non détecté - mode NO_SOUND activé"
fi

# Autoriser X11 (non bloquant, timeout 2s)
timeout 2 xhost +local: 2>/dev/null || true

echo ""
echo "Démarrage du conteneur..."
echo ""

if [ "$PULSE_AVAILABLE" = true ]; then
    # Lancer avec PulseAudio
    echo "Mode: AVEC SON"
    podman run --rm \
        --name "psychedelic-visualizer-gui" \
        --interactive \
        --tty \
        --net=host \
        --ipc=host \
        --security-opt label=disable \
        --volume /tmp/.X11-unix:/tmp/.X11-unix:ro \
        --env DISPLAY \
        --env XAUTHORITY="${HOME}/.Xauthority" \
        --volume "${HOME}/.Xauthority":"${HOME}/.Xauthority":ro \
        --volume /run/user/"${UID}"/pulse:/run/user/"${UID}"/pulse:ro \
        --env PULSE_SERVER=unix:/run/user/"${UID}"/pulse/pulseaudio.socket \
        --env PULSE_COOKIE=/run/user/"${UID}"/pulse/cookie \
        --volume /run/user/"${UID}"/pulse/cookie:/run/user/"${UID}"/pulse/cookie:ro \
        --volume "$(pwd)/input":/app/input:ro,Z \
        --volume "$(pwd)/output":/app/output:Z \
        --volume "$(pwd)":/app:ro,Z \
        --device /dev/snd \
        psychedelic-visualizer:latest \
        python3 /app/main.py
else
    # Lancer sans PulseAudio (mode NO_SOUND)
    # Note: On retire --tty et --interactive pour éviter les problèmes
    # quand Tkinter s'exécute dans un conteneur
    echo "Mode: SANS SON (NO_SOUND=1)"
    podman run --rm \
        --name "psychedelic-visualizer-gui" \
        --net=host \
        --ipc=host \
        --security-opt label=disable \
        --volume /tmp/.X11-unix:/tmp/.X11-unix:ro \
        --env DISPLAY \
        --env XAUTHORITY="${HOME}/.Xauthority" \
        --volume "${HOME}/.Xauthority":"${HOME}/.Xauthority":ro \
        --volume "$(pwd)/input":/app/input:ro,Z \
        --volume "$(pwd)/output":/app/output:Z \
        --volume "$(pwd)":/app:ro,Z \
        --env NO_SOUND=1 \
        --env SDL_VIDEODRIVER=x11 \
        --env SDL_RENDER_DRIVER=software \
        --env SDL_AUDIODRIVER=dummy \
        psychedelic-visualizer:latest \
        python3 /app/main.py
fi

# Révoquer X11
xhost -local: 2>/dev/null
