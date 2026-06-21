#!/bin/bash

# Script pour lancer le menu interactif dans le conteneur
# Corrigé et optimisé pour Podman sur Fedora

IMAGE_NAME="psychedelic-visualizer"
IMAGE_TAG="latest"
CONTAINER_NAME="psychedelic-menu"

# Chemins par défaut
AUDIO_DIR="${HOME}/Music"
OUTPUT_DIR="${HOME}/Videos"
XAUTHORITY_FILE="${HOME}/.Xauthority"

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

# Autoriser X11
xhost +local: 2>/dev/null

echo "=========================================="
echo "  Visualisateur Psychédélique - Menu"
echo "=========================================="
echo ""
echo "Lancement du menu interactif..."
echo ""

# Créer les dossiers si nécessaire
mkdir -p "$AUDIO_DIR" "$OUTPUT_DIR"

# Lancer le conteneur
podman run --rm \
    --name "$CONTAINER_NAME" \
    --interactive \
    --tty \
    --volume /tmp/.X11-unix:/tmp/.X11-unix:ro \
    --env DISPLAY \
    --env XAUTHORITY="$XAUTHORITY_FILE" \
    --volume "$XAUTHORITY_FILE":"$XAUTHORITY_FILE":ro \
    --volume "$AUDIO_DIR":/audio:ro \
    --volume "$OUTPUT_DIR":/output \
    --volume "$(pwd)":/app:ro,Z \
    "${IMAGE_NAME}:${IMAGE_TAG}" \
    python3 /app/export_menu.py

echo ""
echo "Menu terminé."
