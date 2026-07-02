.PHONY: help build run run-cli clean stop standalone-appimage standalone-clean

# Nom de l'image
IMAGE_NAME := psychedelic-visualizer
IMAGE_TAG := latest
AUDIO_DIR ?= ${HOME}/Music
OUTPUT_DIR ?= ${HOME}/Videos

help:
	@echo "Visualisateur Psychédélique - Commandes"
	@echo "=========================================="
	@echo ""
	@echo "Construction:"
	@echo "  make build              - Construire l'image Podman"
	@echo ""
	@echo "Exécution:"
	@echo "  make run                - Lancer l'interface graphique"
	@echo "  make run-cli            - Export vidéo (voir ci-dessous)"
	@echo ""
	@echo "Export Vidéo (CLI):"
	@echo "  make run-cli AUDIO=ma_musique.mp3 OUTPUT=ma_video.mp4"
	@echo "  make run-cli AUDIO=music.mp3 OUTPUT=video.mp4 EFFECT=tunnel"
	@echo ""
	@echo "Presets disponibles: dev, fast, normal, high, 4k"
	@echo ""
	@echo "AppImage:"
	@echo "  make standalone-appimage - Build AppImage (recommandé)"
	@echo "  make standalone-clean    - Nettoyer les builds standalone"
	@echo ""
	@echo "Nettoyage:"
	@echo "  make clean               - Nettoyer les conteneurs"
	@echo "  make stop                - Arrêter tous les conteneurs"

build:
	@echo "Construction de l'image Podman..."
	./podman-build.sh

run:
	@echo "Lancement de l'interface graphique..."
	@echo "Dossiers: Audio=$(AUDIO_DIR) Output=$(OUTPUT_DIR)"
	AUDIO_DIR=$(AUDIO_DIR) OUTPUT_DIR=$(OUTPUT_DIR) ./podman-run.sh

run-cli:
	@if [ -z "$(AUDIO)" ]; then \
		echo "Erreur: AUDIO non spécifié"; \
		echo "Exemple: make run-cli AUDIO=ma_musique.mp3 OUTPUT=ma_video.mp4"; \
		exit 1; \
	fi
	@if [ -z "$(OUTPUT)" ]; then \
		echo "Erreur: OUTPUT non spécifié"; \
		exit 1; \
	fi
	@echo "Export vidéo: $(AUDIO) -> $(OUTPUT)"
	AUDIO=$(AUDIO) OUTPUT=$(OUTPUT) EFFECT=$(EFFECT) COLOR=$(COLOR) RESOLUTION=$(RESOLUTION) FPS=$(FPS) PRESET=$(PRESET) ./podman-run-cli.sh "$(AUDIO)" "$(OUTPUT)"

clean:
	@echo "Nettoyage des conteneurs..."
	podman stop psychedelic-visualizer-ui psychedelic-visualizer-cli 2>/dev/null || true
	podman rm psychedelic-visualizer-ui psychedelic-visualizer-cli 2>/dev/null || true
	@echo "Conteneurs nettoyés"

stop:
	@echo "Arrêt des conteneurs..."
	podman stop psychedelic-visualizer-ui psychedelic-visualizer-cli 2>/dev/null || true
	@echo "Conteneurs arrêtés"

standalone-appimage:
	@echo "Build AppImage Linux..."
	chmod +x build_standalone.sh
	./build_standalone.sh

standalone-clean:
	@echo "Nettoyage des builds standalone..."
	rm -rf dist_standalone/ Visualisateur.AppDir/ output/ appimagetool-x86_64.AppImage Dockerfile.appimage
	@echo "✓ Builds standalone nettoyés"