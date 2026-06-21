#!/bin/bash

# Script pour lancer les tests dans le conteneur

IMAGE_NAME="psychedelic-visualizer"
IMAGE_TAG="latest"
CONTAINER_NAME="psychedelic-tests"

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

# Lancer les tests dans le conteneur
echo "=========================================="
echo "Lancement des tests..."
echo "=========================================="
echo ""

# Passer les arguments au script Python
TEST_ARGS="$@"

podman run --rm \
    --name "$CONTAINER_NAME" \
    --volume "$(pwd)":/app:ro,Z \
    "${IMAGE_NAME}:${IMAGE_TAG}" \
    python3 -m unittest discover tests/ -v

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Tous les tests ont réussi !"
else
    echo "❌ Certains tests ont échoué (code: $EXIT_CODE)"
fi

exit $EXIT_CODE
