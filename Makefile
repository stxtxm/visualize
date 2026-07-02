.PHONY: help build run run-cli run-menu run-no-sound run-fallback clean stop test test-audio test-effects test-quality rebuild
.PHONY: standalone-all standalone-appimage standalone-portable standalone-docker standalone-windows standalone-clean

# Nom de l'image
IMAGE_NAME := psychedelic-visualizer
IMAGE_TAG := latest
AUDIO_DIR ?= ${HOME}/Music
OUTPUT_DIR ?= ${HOME}/Videos

# Afficher l'aide
help:
	@echo "Visualisateur Psychédélique - Commandes"
	@echo "=========================================="
	@echo ""
	@echo "Construction:"
	@echo "  make build              - Construire l'image Podman"
	@echo "  make rebuild            - Reconstruire l'image"
	@echo ""
	@echo "Exécution:"
	@echo "  make run                - Lancer l'interface graphique"
	@echo "  make run-menu           - Lancer le menu CLI"
	@echo "  make run-cli            - Export vidéo (voir ci-dessous)"
	@echo ""
	@echo "Export Vidéo (CLI):"
	@echo "  make run-cli AUDIO=ma_musique.mp3 OUTPUT=ma_video.mp4"
	@echo "  make run-cli AUDIO=music.mp3 OUTPUT=video.mp4 EFFECT=tunnel"
	@echo "  make run-cli AUDIO=music.mp3 OUTPUT=video.mp4 PRESET=dev"
	@echo ""
	@echo "Presets disponibles:"
	@echo "  dev     - Très rapide (720p, 15fps) pour tests"
	@echo "  fast    - Rapide (720p, 20fps)"
	@echo "  normal  - Normale (1080p, 30fps) par défaut"
	@echo "  high    - Haute qualité (1080p, 60fps)"
	@echo "  4k      - 4K cinématique (3840x2160, 30fps)"
	@echo ""
	@echo "Options supplémentaires:"
	@echo "  EFFECT=...   - bars, circles, particles, tunnel, wave, spectrum, plasma, random"
	@echo "  COLOR=...    - psychedelic, retro, winamp_classic, dark, rainbow"
	@echo "  RESOLUTION=... - 720p, 1080p, 1440p, 4K"
	@echo "  FPS=...      - 15, 20, 24, 30, 60, 120"
	@echo ""
	@echo "Nettoyage:"
	@echo "  make clean             - Nettoyer les conteneurs"
	@echo "  make stop              - Arrêter tous les conteneurs"
	@echo ""
	@echo "Tests:"
	@echo "  make test              - Lancer tous les tests"
	@echo "  make test-quality      - Tester les présélections"
	@echo "  make test-effects      - Tester les effets"
	@echo ""
	@echo "Modes de lancement:"
	@echo "  make run-no-sound      - Lancer la GUI sans son (NO_SOUND=1)"
	@echo "  make run-fallback      - Lancer la GUI avec fallback automatique PulseAudio"
	@echo ""
	@echo "Standalone Builds:"
	@echo "  make standalone-all    - Build TOUS les formats (AppImage + Portable)"
	@echo "  make standalone-appimage - Build AppImage (recommandé pour distribution)"
	@echo "  make standalone-portable - Build bundle portable (usage perso)"
	@echo "  make standalone-docker  - Build image Docker"
	@echo "  make standalone-clean   - Nettoyer les builds standalone"

# Construire l'image
build:
	@echo "Construction de l'image Podman..."
	./podman-build.sh

# Reconstruire (forcer le rebuild)
rebuild:
	@echo "Reconstruction de l'image..."
	podman rmi $(IMAGE_NAME):$(IMAGE_TAG) 2>/dev/null || true
	make build

# Lancer l'interface graphique
run:
	@echo "Lancement de l'interface graphique..."
	@echo "Dossiers: Audio=$(AUDIO_DIR) Output=$(OUTPUT_DIR)"
	AUDIO_DIR=$(AUDIO_DIR) OUTPUT_DIR=$(OUTPUT_DIR) ./podman-run.sh

# Lancer la GUI sans son (NO_SOUND=1)
run-no-sound:
	@echo "Lancement de la GUI sans son (NO_SOUND=1)..."
	AUDIO_DIR=$(AUDIO_DIR) OUTPUT_DIR=$(OUTPUT_DIR) NO_SOUND=1 ./podman-run.sh

# Lancer la GUI avec fallback automatique (recommandé)
run-fallback:
	@echo "Lancement de la GUI avec fallback automatique..."
	AUDIO_DIR=$(AUDIO_DIR) OUTPUT_DIR=$(OUTPUT_DIR) ./run_gui_fallback.sh

# Lancer le menu CLI
run-menu:
	@echo "Lancement du menu CLI..."
	./podman-menu.sh

# Export vidéo en CLI
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
	@echo "Preset: $(PRESET)"
	@echo "Effet: $(EFFECT)"
	@echo "Couleur: $(COLOR)"
	AUDIO=$(AUDIO) OUTPUT=$(OUTPUT) EFFECT=$(EFFECT) COLOR=$(COLOR) RESOLUTION=$(RESOLUTION) FPS=$(FPS) PRESET=$(PRESET) ./podman-run-cli.sh "$(AUDIO)" "$(OUTPUT)" $(if [ -n "$(EFFECT)" ]; then echo --effect $(EFFECT); fi) $(if [ -n "$(COLOR)" ]; then echo --color $(COLOR); fi) $(if [ -n "$(RESOLUTION)" ]; then echo --resolution $(RESOLUTION); fi) $(if [ -n "$(FPS)" ]; then echo --fps $(FPS); fi) $(if [ -n "$(PRESET)" ]; then echo --preset $(PRESET); fi)

# Nettoyer les conteneurs
clean:
	@echo "Nettoyage des conteneurs..."
	podman stop psychedelic-visualizer-ui psychedelic-visualizer-cli psychedelic-menu 2>/dev/null || true
	podman rm psychedelic-visualizer-ui psychedelic-visualizer-cli psychedelic-menu 2>/dev/null || true
	@echo "Conteneurs nettoyés"

# Arrêter tous les conteneurs
stop:
	@echo "Arrêt des conteneurs..."
	podman stop psychedelic-visualizer-ui psychedelic-visualizer-cli psychedelic-menu 2>/dev/null || true
	@echo "Conteneurs arrêtés"

# Lancer les tests (dans le conteneur pour avoir les dépendances)
test:
	@echo "Lancement de tous les tests dans le conteneur..."
	@echo "(Les tests nécessitent les dépendances Python)"
	./podman-test.sh

test-quality:
	@echo "Test des présélections qualité..."
	@echo "(Nécessite les dépendances, lancez 'make test' dans le conteneur)"
	@python3 -m pytest tests/test_quality_presets.py -v 2>/dev/null || python3 -m unittest tests.test_quality_presets -v

test-effects:
	@echo "Test des effets..."
	@echo "(Nécessite les dépendances, lancez 'make test' dans le conteneur)"
	@python3 -m pytest tests/test_effects.py -v 2>/dev/null || python3 -m unittest tests.test_effects -v

test-audio:
	@echo "Test de l'analyse audio..."
	@echo "(Nécessite les dépendances, lancez 'make test' dans le conteneur)"
	@python3 -m pytest tests/test_audio.py -v 2>/dev/null || python3 -m unittest tests.test_audio -v

# Builds standalone
standalone-all: standalone-appimage standalone-portable
	@echo "✓ Tous les builds standalone terminés"

standalone-appimage:
	@echo "Build AppImage Linux..."
	chmod +x build_standalone.sh
	./build_standalone.sh appimage

standalone-portable:
	@echo "Build bundle portable Linux..."
	chmod +x build_standalone.sh
	./build_standalone.sh portable

standalone-docker:
	@echo "Build image Docker pour dev..."
	chmod +x build_standalone.sh
	./build_standalone.sh docker

standalone-windows:
	@echo "Build Windows EXE..."
	chmod +x build_standalone.sh
	./build_standalone.sh windows

standalone-clean:
	@echo "Nettoyage des builds standalone..."
	rm -rf dist_standalone/ Visualisateur.AppDir/ build_appimage/ build_venv/
	@echo "✓ Builds standalone nettoyés"
