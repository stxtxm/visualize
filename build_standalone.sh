#!/bin/bash
# =============================================================================
# Build Standalone - Visualisateur Psychédélique
# Crée des applications standalone pour Linux (AppImage et Bundle Portable)
# =============================================================================
#
# Auteur: TimO
# Version: 2.0 - Optimisé pour la fluidité et la portabilité
#
# Usage:
#   ./build_standalone.sh appimage      # Build AppImage
#   ./build_standalone.sh portable      # Build bundle portable
#   ./build_standalone.sh docker        # Build image Docker
#   ./build_standalone.sh all           # Build tout
#
# =============================================================================

set -e

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Chemins
DIST_DIR="$SCRIPT_DIR/dist_standalone"
BUILD_DIR="$SCRIPT_DIR/build_standalone"

# Version de Python
PYTHON_VERSION="3.11"

# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

cleanup() {
    log_info "Nettoyage..."
    rm -rf "$BUILD_DIR" Visualisateur.AppDir/ linuxdeploy*.AppImage Dockerfile.standalone 2>/dev/null || true
}

# Vérifier si une commande existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# =============================================================================
# BUILD APPIMAGE (Recommandé pour distribution)
# =============================================================================

build_appimage() {
    log_section "Build AppImage"
    
    log_info "Préparation de l'environnement..."
    mkdir -p "$BUILD_DIR" "$DIST_DIR"
    
    # Vérifier que linuxdeploy est disponible ou le télécharger
    if [ ! -f "linuxdeploy-x86_64.AppImage" ]; then
        log_info "Téléchargement de linuxdeploy..."
        wget -q -c "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage" \
            -O linuxdeploy-x86_64.AppImage || {
            log_error "Impossible de télécharger linuxdeploy"
            return 1
        }
        chmod +x linuxdeploy-x86_64.AppImage
    fi
    
    # Vérifier que le plugin python est disponible ou le télécharger
    if [ ! -f "linuxdeploy-plugin-python-x86_64.AppImage" ]; then
        log_info "Téléchargement de linuxdeploy-plugin-python..."
        wget -q -c "https://github.com/linuxdeploy/linuxdeploy-plugin-python/releases/download/continuous/linuxdeploy-plugin-python-x86_64.AppImage" \
            -O linuxdeploy-plugin-python-x86_64.AppImage || {
            log_error "Impossible de télécharger linuxdeploy-plugin-python"
            return 1
        }
        chmod +x linuxdeploy-plugin-python-x86_64.AppImage
    fi
    
    log_info "Création de la structure AppDir..."
    rm -rf Visualisateur.AppDir
    mkdir -p Visualisateur.AppDir/usr/bin
    mkdir -p Visualisateur.AppDir/usr/lib
    mkdir -p Visualisateur.AppDir/usr/share/applications
    mkdir -p Visualisateur.AppDir/usr/share/icons/hicolor/256x256/apps
    mkdir -p Visualisateur.AppDir/usr/lib/x86_64-linux-gnu
    
    # Copier l'application
    log_info "Copie de l'application..."
    cp -r audio effects renderer ui utils recorder assets main.py export_menu.py quality_presets.py requirements.txt Visualisateur.AppDir/usr/bin/
    
    # Créer un conteneur temporaire pour builder les dépendances
    log_info "Création d'un conteneur de build temporaire..."
    
    cat > Dockerfile.standalone << 'DOCKERFILE_EOF'
FROM python:3.11-slim

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    portaudio19-dev \
    gcc \
    python3-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libsdl2-2.0-0 \
    libsdl2-image-2.0-0 \
    libsdl2-mixer-2.0-0 \
    libsdl2-ttf-2.0-0 \
    ffmpeg \
    libx264-dev \
    libmp3lame-dev \
    libx11-6 \
    libxcb-glx0 \
    tk-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
COPY . /app
RUN mkdir -p /output/lib /output/bin /output/app && \
    cp -r /root/.local/lib/python3.11/site-packages /output/lib/python3.11/ 2>/dev/null || \
    cp -r /usr/local/lib/python3.11/site-packages /output/lib/python3.11/ && \
    cp /usr/local/bin/python3 /output/bin/python3 2>/dev/null || \
    cp /usr/bin/python3.11 /output/bin/python3 && \
    cp -r /app/* /output/app/
DOCKERFILE_EOF
    
    # Builder le conteneur de build
    log_info "Build du conteneur de dépendances..."
    if command_exists podman; then
        CONTAINER_TOOL="podman"
    elif command_exists docker; then
        CONTAINER_TOOL="docker"
    else
        log_error "Podman ou Docker requis pour le build"
        return 1
    fi
    
    $CONTAINER_TOOL build -t psychedelic-standalone-builder -f Dockerfile.standalone . 2>&1 | tail -5 || true
    
    # Extraire les fichiers depuis le conteneur
    log_info "Extraction des fichiers depuis le conteneur..."
    CONTAINER_ID=$($CONTAINER_TOOL create psychedelic-standalone-builder)
    
    $CONTAINER_TOOL cp $CONTAINER_ID:/output/lib Visualisateur.AppDir/usr/ 2>/dev/null || true
    $CONTAINER_TOOL cp $CONTAINER_ID:/output/bin Visualisateur.AppDir/usr/ 2>/dev/null || true
    $CONTAINER_TOOL cp $CONTAINER_ID:/output/app/* Visualisateur.AppDir/usr/bin/ 2>/dev/null || true
    
    $CONTAINER_TOOL rm $CONTAINER_ID >/dev/null 2>&1
    $CONTAINER_TOOL rmi psychedelic-standalone-builder >/dev/null 2>&1
    
    rm -f Dockerfile.standalone
    
    # Créer le script AppRun avec gestion intelligente du son
    log_info "Création du script AppRun..."
    cat > Visualisateur.AppDir/AppRun << 'APPRUN_EOF'
#!/bin/bash
SELF_DIR=$(dirname "$(readlink -f "$0")")
cd "$SELF_DIR/usr/bin"

export LD_LIBRARY_PATH="$SELF_DIR/usr/lib:$SELF_DIR/usr/lib/x86_64-linux-gnu:$SELF_DIR/usr/local/lib:${LD_LIBRARY_PATH}"
export PYTHONPATH="$SELF_DIR/usr/lib/python3.11/site-packages:$SELF_DIR/usr/bin:${PYTHONPATH}"
export PATH="$SELF_DIR/usr/bin:$PATH"
export HOME="$HOME"

# Optimisation pour la fluidité
export SDL_AUDIO_BUFFER_SIZE=1024
export SDL_AUDIODRIVER=pulse

# Vérifier PulseAudio
PULSE_AVAILABLE=false
if [ -d "/run/user/$(id -u 2>/dev/null || echo 1000)/pulse" ] 2>/dev/null; then
    PULSE_AVAILABLE=true
fi

if [ "$PULSE_AVAILABLE" = false ]; then
    if [ -e "/dev/snd" ]; then
        export SDL_AUDIODRIVER=alsa
    else
        export SDL_AUDIODRIVER=dummy
        export NO_SOUND=1
    fi
fi

# Lancer l'application
exec python3 main.py "$@" || exit 1
APPRUN_EOF
    
    chmod +x Visualisateur.AppDir/AppRun
    
    # Créer le fichier .desktop
    log_info "Création du fichier .desktop..."
    cat > Visualisateur.AppDir/usr/share/applications/visualisateur.desktop << 'DESKTOP_EOF'
[Desktop Entry]
Name=Visualisateur Psychédélique
Comment=Visualisateur audio psychédélique synchronisé avec votre musique
Exec=AppRun
Icon=visualisateur
Type=Application
Categories=AudioVideo;Player;Graphics;Multimedia;
Terminal=false
StartupWMClass=Visualisateur-Psychedelique
DESKTOP_EOF
    
    # Copier l'icône
    if [ -f "assets/icon.png" ]; then
        cp assets/icon.png Visualisateur.AppDir/usr/share/icons/hicolor/256x256/apps/visualisateur.png
        cp assets/icon.png Visualisateur.AppDir/visualisateur.png
    fi
    
    # Builder l'AppImage
    log_info "Build de l'AppImage avec linuxdeploy..."
    
    ./linuxdeploy-x86_64.AppImage \
        --appdir Visualisateur.AppDir \
        --plugin python \
        --output appimage 2>&1 | tail -10 || true
    
    # Déplacer le résultat
    if ls Visualisateur*.AppImage 1>/dev/null 2>&1; then
        mv Visualisateur*.AppImage "$DIST_DIR/Visualisateur_Psychedelic.AppImage"
        chmod +x "$DIST_DIR/Visualisateur_Psychedelic.AppImage"
        log_info "AppImage creé: $DIST_DIR/Visualisateur_Psychedelic.AppImage"
        ls -lh "$DIST_DIR/Visualisateur_Psychedelic.AppImage"
    else
        log_error "Echec de la creation de l'AppImage"
        return 1
    fi
    
    cleanup
}

# =============================================================================
# BUILD BUNDLE PORTABLE
# =============================================================================

build_portable() {
    log_section "Build Bundle Portable"
    
    log_info "Creation de l'environnement portable..."
    mkdir -p "$BUILD_DIR" "$DIST_DIR"
    
    # Creer un virtual environment portable
    log_info "Creation du virtual environment..."
    
    if [ ! -d "build_venv" ]; then
        python3 -m venv build_venv || {
            log_error "Impossible de créer le virtual environment"
            log_info "Installez: sudo apt install python3-venv (Debian/Ubuntu) ou sudo dnf install python3-virtualenv (Fedora)"
            return 1
        }
    fi
    
    # Activer la venv et installer les dependances
    log_info "Installation des dependances Python..."
    source build_venv/bin/activate
    
    pip install --upgrade pip >/dev/null 2>&1
    pip install --no-cache-dir -r requirements.txt >/dev/null 2>&1 || {
        log_error "Echec de l'installation des dependances"
        deactivate
        return 1
    }
    
    deactivate
    
    # Copier l'application
    log_info "Copie de l'application..."
    rm -rf build_venv/app
    mkdir -p build_venv/app
    cp -r audio effects renderer ui utils recorder assets main.py export_menu.py quality_presets.py requirements.txt build_venv/app/
    
    # Creer le script de lancement intelligent
    log_info "Creation du script de lancement..."
    cat > build_venv/run_visualisateur.sh << 'PORTABLE_EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export PYTHONPATH="$SCRIPT_DIR/app:$PYTHONPATH"
export PATH="$SCRIPT_DIR/bin:$PATH"
export SDL_AUDIO_BUFFER_SIZE=1024

# Verifier PulseAudio
PULSE_AVAILABLE=false
if [ -d "/run/user/$(id -u 2>/dev/null || echo 1000)/pulse" ] 2>/dev/null; then
    PULSE_AVAILABLE=true
fi

if [ "$PULSE_AVAILABLE" = false ]; then
    if [ -e "/dev/snd" ]; then
        export SDL_AUDIODRIVER=alsa
    else
        export SDL_AUDIODRIVER=dummy
        export NO_SOUND=1
    fi
fi

cd "$SCRIPT_DIR/app"
exec "$SCRIPT_DIR/bin/python3" main.py "$@"
PORTABLE_EOF
    
    chmod +x build_venv/run_visualisateur.sh
    
    # Packager
    log_info "Packaging du bundle portable..."
    cd build_venv
    
    tar czf "$DIST_DIR/Visualisateur_Psychedelic_Linux.tar.gz" \
        --exclude='*.pyc' --exclude='__pycache__' --exclude='*.pyo' .
    
    cd "$SCRIPT_DIR"
    
    log_info "Bundle portable creé: $DIST_DIR/Visualisateur_Psychedelic_Linux.tar.gz"
    ls -lh "$DIST_DIR/Visualisateur_Psychedelic_Linux.tar.gz"
    
    cleanup
}

# =============================================================================
# BUILD DOCKER IMAGE
# =============================================================================

build_docker() {
    log_section "Build Docker Image"
    
    log_info "Build de l'image Docker..."
    
    if command_exists podman; then
        CONTAINER_TOOL="podman"
    elif command_exists docker; then
        CONTAINER_TOOL="docker"
    else
        log_error "Podman ou Docker requis"
        return 1
    fi
    
    $CONTAINER_TOOL build -t psychedelic-visualizer:latest -f Dockerfile . || {
        log_error "Echec du build Docker"
        return 1
    }
    
    log_info "Image Docker creee: psychedelic-visualizer:latest"
    cleanup
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    TARGET="${1:-help}"
    
    case "$TARGET" in
        appimage|linux)
            build_appimage
            ;;
        portable)
            build_portable
            ;;
        docker)
            build_docker
            ;;
        all)
            build_appimage
            build_portable
            build_docker
            ;;
        help|"")
            echo ""
            echo "Build Standalone - Visualisateur Psychedelique v2.0"
            echo "======================================================"
            echo ""
            echo "Usage: $0 [appimage|portable|docker|all]"
            echo ""
            echo "Commandes:"
            echo "  appimage    - Build AppImage (pour distribution)"
            echo "  portable    - Build bundle portable (usage perso)"
            echo "  docker      - Build image Docker"
            echo "  all        - Build tout"
            echo ""
            ;;
        *)
            log_error "Commande inconnue: $TARGET"
            exit 1
            ;;
    esac
    
    echo ""
    log_info "Build termine! Fichiers dans: $DIST_DIR/"
    ls -lh "$DIST_DIR/" 2>/dev/null || true
}

main "$@"
