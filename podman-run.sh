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
    --volume /run/user/"${UID}"/pulse:/run/user/"${UID}"/pulse:ro \
    --env PULSE_SERVER=unix:/run/user/"${UID}"/pulse/pulseaudio.socket \
    --env PULSE_COOKIE=/run/user/"${UID}"/pulse/cookie \
    --volume /run/user/"${UID}"/pulse/cookie:/run/user/"${UID}"/pulse/cookie:ro \
    --volume "$AUDIO_DIR":/audio:ro \
    --volume "$OUTPUT_DIR":/output \
    --volume "$(pwd)":/app:ro,Z \
    --device /dev/snd \
    "${IMAGE_NAME}:${IMAGE_TAG}" \
    python3 /app/main.py

# Révoquer l'accès X11 après l'arrêt
xhost -local: 2>/dev/null
