.PHONY: help run-cli standalone-appimage standalone-clean

# Nom de l'image (hérité, conservé pour compatibilité)
IMAGE_NAME := visualize-appimage
IMAGE_TAG := latest
AUDIO_DIR ?= ${HOME}/Music
OUTPUT_DIR ?= ${HOME}/Videos

help:
	@echo "Visualize - Commandes"
	@echo "=========================================="
	@echo ""
	@echo "Exécution:"
	@echo "  python3 main.py             - Lancer la GUI"
	@echo "  python3 main.py -h          - Afficher l'aide"
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
	@echo "Tests:"
	@echo "  python3 -m pytest tests/ -v"

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
	python3 main.py "$(AUDIO)" --export "$(OUTPUT)" \
		--effect $(or $(EFFECT),random) \
		--color $(or $(COLOR),psychedelic) \
		--resolution $(or $(RESOLUTION),) \
		--fps $(or $(FPS),) \
		--preset $(or $(PRESET),normal)

standalone-appimage:
	@echo "Build AppImage Linux..."
	chmod +x build_standalone.sh
	./build_standalone.sh

standalone-clean:
	@echo "Nettoyage des builds standalone..."
	rm -rf dist_standalone/ Visualize.AppDir/ output/ appimagetool-x86_64.AppImage Dockerfile.appimage
	@echo "✓ Builds standalone nettoyés"
