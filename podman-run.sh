#!/bin/bash

# Script pour lancer le conteneur avec interface graphique
# Corrigé et optimisé pour Podman sur Fedora

IMAGE_NAME="psychedelic-visualizer"
IMAGE_TAG="latest"
CONTAINER_NAME="psychedelic-visualizer-ui"

# Chemins par défaut (peuvent être écrasés par des variables d'environnement)
AUDIO_DIR="${AUDIO_DIR:-${HOME}/Music}"
OUTPUT_DIR="${OUTPUT_DIR:-${HOME}/Videos}"
XAUTHORITY_FILE="${XAUTHORITY_FILE:-${HOME}/.Xauthority}"

# Créer les dossiers si ils n'existent pas
mkdir -p "$AUDIO_DIR" "$OUTPUT_DIR"

# Vérifier que Podman est installé
if ! command -v podman &> /dev/null; then
    echo "Erreur: Podman n'est pas installé."
    echo "Installez-le avec: sudo dnf install podman"
    exit 1
fi

# Vérifier que l'image existe
if ! podman image exists "${IMAGE_NAME}:${IMAGE_TAG}" &> /dev/null; then
    echo "L'image ${IMAGE_NAME}:${IMAGE_TAG} n'existe pas."
    echo "Construisez-la d'abord avec: make build"
    exit 1
fi

# Tuer le conteneur existant s'il y en a un
if podman ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}"; then
    echo "Arrêt du conteneur existant..."
    podman stop "$CONTAINER_NAME" > /dev/null 2>&1
    podman rm "$CONTAINER_NAME" > /dev/null 2>&1
fi

# Autoriser l'accès X11
xhost +local: 2>/dev/null

echo "=========================================="
echo "Lancement du Visualisateur Psychédélique"
echo "=========================================="
echo ""
echo "Dossiers montés:"
echo "  Audio:  ${AUDIO_DIR}"
echo "  Output: ${OUTPUT_DIR}"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter"
echo ""

# Vérifier si NO_SOUND est activé
if [ "${NO_SOUND}" = "1" ] || [ "${NO_SOUND}" = "true" ]; then
    # Mode sans son - désactiver PulseAudio et ALSA
    echo "Mode: SANS SON (NO_SOUND=1)"
    PULSE_VOLUMES=""
    DEV_SND=""
    PULSE_ENV=""
    PULSE_COOKIE_ENV=""
    PULSE_COOKIE_VOL=""
    SDL_AUDIO="--env SDL_AUDIODRIVER=dummy"
    SDL_VIDEO="--env SDL_VIDEODRIVER=x11 --env SDL_RENDER_DRIVER=software"
else
    # Mode avec son - activer PulseAudio
    PULSE_VOLUMES="--volume /run/user/\"${UID}\"/pulse:/run/user/\"${UID}\"/pulse:ro"
    DEV_SND="--device /dev/snd"
    PULSE_ENV="--env PULSE_SERVER=unix:/run/user/\"${UID}\"/pulse/pulseaudio.socket --env PULSE_COOKIE=/run/user/\"${UID}\"/pulse/cookie"
    PULSE_COOKIE_ENV="--env PULSE_COOKIE=/run/user/\"${UID}\"/pulse/cookie"
    PULSE_COOKIE_VOL="--volume /run/user/\"${UID}\"/pulse/cookie:/run/user/\"${UID}\"/pulse/cookie:ro"
    SDL_AUDIO=""
    SDL_VIDEO=""
fi

# Lancer le conteneur avec toutes les options nécessaires
podman run --rm \
    --name "$CONTAINER_NAME" \
    --interactive \
    --tty \
    --net=host \
    --ipc=host \
    --security-opt label=disable \
    --volume /tmp/.X11-unix:/tmp/.X11-unix:ro \
    --env DISPLAY \
    --env XAUTHORITY="$XAUTHORITY_FILE" \
    --volume "$XAUTHORITY_FILE":"$XAUTHORITY_FILE":ro \
    $PULSE_VOLUMES \
    $PULSE_ENV \
    $PULSE_COOKIE_ENV \
    $PULSE_COOKIE_VOL \
    $SDL_AUDIO \
    $SDL_VIDEO \
    --volume "$(pwd)/input":/app/input:ro,Z \
    --volume "$(pwd)/output":/app/output:Z \
    --volume "$(pwd)":/app:ro,Z \
    $DEV_SND \
    "${IMAGE_NAME}:${IMAGE_TAG}" \
    python3 /app/main.py

# Révoquer l'accès X11 après l'arrêt
xhost -local: 2>/dev/null
