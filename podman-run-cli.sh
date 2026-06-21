#!/bin/bash

# Script pour lancer le conteneur en mode CLI (sans interface graphique)
# Idéal pour l'export vidéo
# Corrigé et optimisé pour Podman sur Fedora

IMAGE_NAME="psychedelic-visualizer"
IMAGE_TAG="latest"
CONTAINER_NAME="psychedelic-visualizer-cli"

# Vérifications
if [ $# -lt 2 ]; then
    echo "Usage: $0 <fichier_audio> <fichier_sortie> [options]"
    echo ""
    echo "Exemple:"
    echo "  $0 /chemin/vers/musique.mp3 /chemin/vers/video.mp4"
    echo "  $0 musique.mp3 video.mp4 --effect tunnel --resolution 4K"
    echo "  $0 musique.mp3 video.mp4 --preset dev"
    echo ""
    echo "Presets disponibles: dev, fast, normal, high, 4k"
    echo "Effets: bars, circles, particles, tunnel, wave, random"
    echo "Couleurs: psychedelic, retro, dark, rainbow"
    exit 1
fi

AUDIO_FILE="$1"
OUTPUT_FILE="$2"
shift 2  # Retirer les 2 premiers arguments

# Récupérer le chemin absolu du fichier audio
if [[ "$AUDIO_FILE" != /* ]]; then
    AUDIO_FILE="$(pwd)/$AUDIO_FILE"
fi

# Récupérer le chemin absolu du fichier de sortie
if [[ "$OUTPUT_FILE" != /* ]]; then
    OUTPUT_FILE="$(pwd)/$OUTPUT_FILE"
fi

# Extraire le dossier de sortie
OUTPUT_DIR="$(dirname "$OUTPUT_FILE")"
AUDIO_DIR="$(dirname "$AUDIO_FILE")"

# Convertir les chemins relatifs en absolus
if [[ "$OUTPUT_DIR" == "." ]]; then
    OUTPUT_DIR="$(pwd)"
fi
if [[ "$AUDIO_DIR" == "." ]]; then
    AUDIO_DIR="$(pwd)"
fi

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

# Vérifier que le fichier audio existe
if [ ! -f "$AUDIO_FILE" ]; then
    echo "Erreur: Le fichier audio '$AUDIO_FILE' n'existe pas."
    exit 1
fi

# Lancer le conteneur en mode headless
echo "=========================================="
echo "Export Vidéo en cours..."
echo "=========================================="
echo ""
echo "Entrée:  $AUDIO_FILE"
echo "Sortie:  $OUTPUT_FILE"
echo ""
echo "⚠️  La vidéo sera sauvegardée dans: ./output/"
echo ""

# Utilisation du répertoire courant comme /data
# Monter ./output comme /app/output dans le conteneur
DATA_DIR="$(pwd)"
PROJECT_DIR="$(pwd)"
mkdir -p "$DATA_DIR/output"

podman run --rm \
    --name "$CONTAINER_NAME" \
    --volume "$PROJECT_DIR":/app:Z \
    --volume "$DATA_DIR":/data:Z \
    "${IMAGE_NAME}:${IMAGE_TAG}" \
    python3 /app/main.py /data/$(basename "$AUDIO_FILE") \
    --export /app/output/$(basename "$OUTPUT_FILE") \
    --no-gui \
    "$@"

# Vérifier le résultat
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ Export terminé!"
    echo "Vidéo disponible: $OUTPUT_FILE"
else
    echo ""
    echo "❌ Export échoué (code: $EXIT_CODE)"
fi
