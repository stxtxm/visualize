#!/bin/bash

# Script pour construire l'image Podman

IMAGE_NAME="psychedelic-visualizer"
IMAGE_TAG="latest"

echo "=========================================="
echo "Construction de l'image Podman..."
echo "=========================================="
echo ""

# Construire l'image avec Podman
podman build \
    --tag "${IMAGE_NAME}:${IMAGE_TAG}" \
    --file Dockerfile \
    .

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Image construite avec succès: ${IMAGE_NAME}:${IMAGE_TAG}"
    echo ""
    echo "Pour lancer le conteneur:"
    echo "  ./podman-run.sh"
    echo ""
    echo "Pour lancer en mode CLI (export vidéo):"
    echo "  ./podman-run-cli.sh /chemin/vers/audio.mp3 /chemin/vers/sortie.mp4"
else
    echo ""
    echo "✗ Erreur lors de la construction de l'image"
    exit 1
fi
