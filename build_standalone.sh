#!/bin/bash
# =============================================================================
# Build AppImage - Visualisateur Psychédélique
# =============================================================================
# Build via Podman (Docker) pour un environnement reproductible.
# Copie intégrale de Python + dépendances avec résolution des liens symboliques.
# =============================================================================

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'
DIST_DIR="$SCRIPT_DIR/dist_standalone"

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }

# Nettoyage
log_info "Nettoyage..."
rm -rf Visualisateur.AppDir output/ appimagetool-x86_64.AppImage Dockerfile.appimage
mkdir -p "$DIST_DIR" output

# Télécharger appimagetool
if [ ! -f "appimagetool-x86_64.AppImage" ]; then
    log_info "Téléchargement de appimagetool..."
    wget -q -c "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" \
        -O appimagetool-x86_64.AppImage || log_error "appimagetool téléchargement échoué"
    chmod +x appimagetool-x86_64.AppImage
fi

# Créer le Dockerfile de build - APPROCHE FINALE : site-packages + libs système (Python système requis)
cat > Dockerfile.appimage << 'DOCKERFILE_EOF'
FROM python:3.11-slim

# Installer les dépendances système pour les libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0 \
    portaudio19-dev ffmpeg \
    libpulse0 libdc1394-25 libraw1394-11 libiec61883-0 \
    pulseaudio-utils pipewire-bin alsa-utils \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
    libx11-6 libxcb-glx0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# Vérifier l'installation
RUN python3 -c "import numpy, pygame, cv2, pydub, PIL; print('Tous les imports OK')"

# Créer la structure de sortie
RUN mkdir -p /output/usr/lib/python3.11

# Copier les dépendances Python (site-packages)
RUN cp -r /usr/local/lib/python3.11/site-packages /output/usr/lib/python3.11/

# Copier les exécutables utiles (ffmpeg/ffprobe)
RUN mkdir -p /output/usr/bin && \
    for bin in ffmpeg ffprobe paplay pw-play aplay which; do \
        if [ -x "/usr/bin/$bin" ]; then \
            cp -nL "/usr/bin/$bin" "/output/usr/bin/$bin"; \
        fi; \
    done

# Copier les bibliothèques système SDL2 et audio
RUN mkdir -p /output/usr/lib && \
    for lib in \
        /usr/lib/x86_64-linux-gnu/libSDL2-2.0.so.* \
        /usr/lib/x86_64-linux-gnu/libSDL2_image-2.0.so.* \
        /usr/lib/x86_64-linux-gnu/libSDL2_mixer-2.0.so.* \
        /usr/lib/x86_64-linux-gnu/libSDL2_ttf-2.0.so.* \
        /usr/lib/x86_64-linux-gnu/libportaudio.so.* \
        /usr/lib/x86_64-linux-gnu/libasound.so.* \
        /usr/lib/x86_64-linux-gnu/libpulsedsp.so* \
        /usr/lib/x86_64-linux-gnu/libpulse.so.* \
        /usr/lib/x86_64-linux-gnu/libpulse-simple.so.* \
        /usr/lib/x86_64-linux-gnu/libX11.so.* \
        /usr/lib/x86_64-linux-gnu/libXext.so.* \
        /usr/lib/x86_64-linux-gnu/libXrender.so.* \
        /usr/lib/x86_64-linux-gnu/libGL.so.* \
        /usr/lib/x86_64-linux-gnu/libglib-2.0.so.* \
        /usr/lib/x86_64-linux-gnu/libgio-2.0.so.* \
        /usr/lib/x86_64-linux-gnu/libgobject-2.0.so.* \
        ; do \
        cp -nL $lib /output/usr/lib/ 2>/dev/null || true; \
    done

# Copier la bibliothèque FFmpeg runtime requise par ffmpeg/ffprobe
RUN mkdir -p /output/usr/lib && \
    for lib in \
        /usr/lib/x86_64-linux-gnu/libavcodec.so.* \
        /usr/lib/x86_64-linux-gnu/libavdevice.so.* \
        /usr/lib/x86_64-linux-gnu/libavfilter.so.* \
        /usr/lib/x86_64-linux-gnu/libavformat.so.* \
        /usr/lib/x86_64-linux-gnu/libavutil.so.* \
        /usr/lib/x86_64-linux-gnu/libpostproc.so.* \
        /usr/lib/x86_64-linux-gnu/libswresample.so.* \
        /usr/lib/x86_64-linux-gnu/libswscale.so.* \
        /usr/lib/x86_64-linux-gnu/libdc1394.so.* \
        /usr/lib/x86_64-linux-gnu/libraw1394.so.* \
        /usr/lib/x86_64-linux-gnu/libiec61883.so.* \
        ; do \
        cp -nL $lib /output/usr/lib/ 2>/dev/null || true; \
    done

# Ajouter aussi les bibliothèques PulseAudio depuis /usr/lib64/pulseaudio ou /usr/lib/x86_64-linux-gnu/pulseaudio
RUN mkdir -p /output/usr/lib/pulseaudio && \
    for lib in \
        /usr/lib64/pulseaudio/libpulsecommon*.so* /usr/lib64/pulseaudio/libpulsedsp.so* /usr/lib64/pulseaudio/libpulse-simple*.so* /usr/lib64/pulseaudio/libpulse.so* \
        /usr/lib/x86_64-linux-gnu/pulseaudio/libpulsecommon*.so* /usr/lib/x86_64-linux-gnu/pulseaudio/libpulsedsp.so* /usr/lib/x86_64-linux-gnu/pulseaudio/libpulse-simple*.so* /usr/lib/x86_64-linux-gnu/pulseaudio/libpulse.so* \
        /usr/lib/x86_64-linux-gnu/libpulse-simple.so* /usr/lib/x86_64-linux-gnu/libpulse.so* ; do \
        cp -nL "$lib" /output/usr/lib/pulseaudio/ 2>/dev/null || true; \
    done
DOCKERFILE_EOF

# Build conteneur
BUILD_LOG="/tmp/visualizer_build.log"
log_info "Build du conteneur Podman..."
if ! podman build -t psychedelic-appimage -f Dockerfile.appimage . > "$BUILD_LOG" 2>&1; then
    tail -10 "$BUILD_LOG"
    log_error "Build du conteneur échoué. Voir $BUILD_LOG"
fi

# Extraction
log_info "Extraction des fichiers..."
rm -rf output/
mkdir -p output
podman run --rm -v "$SCRIPT_DIR/output:/out:Z" psychedelic-appimage sh -c "cp -rL /output/* /out/"

# Copier le code source dans output/usr/app sans inclure les artefacts de build
mkdir -p output/usr/app
tar --exclude='./output' --exclude='./dist_standalone' --exclude='./Visualisateur.AppDir' --exclude='./appimagetool-x86_64.AppImage' --exclude='./Dockerfile.appimage' --exclude='./.git' -cf - . | tar -C output/usr/app -xpf -

# Vérifier que l'extraction a bien fonctionné
if [ ! -d "output/usr/lib/python3.11/site-packages" ]; then
    log_error "site-packages non trouvé dans output/usr/lib/python3.11/ ! Extraction échouée."
fi

# Copier les bibliothèques PulseAudio supplémentaires du système hôte si elles existent
if [ -d "/usr/lib64/pulseaudio" ]; then
    mkdir -p output/usr/lib/pulseaudio
    cp -nL /usr/lib64/pulseaudio/libpulsecommon*.so* output/usr/lib/pulseaudio/ 2>/dev/null || true
    cp -nL /usr/lib64/pulseaudio/libpulsedsp.so* output/usr/lib/pulseaudio/ 2>/dev/null || true
fi

log_success "site-packages trouvé dans output"

# Créer AppDir
log_info "Création de AppDir..."
rm -rf Visualisateur.AppDir
mkdir -p Visualisateur.AppDir/usr/lib
mkdir -p Visualisateur.AppDir/usr/share/applications
mkdir -p Visualisateur.AppDir/usr/share/icons/hicolor/256x256/apps

# Copier les dépendances Python (site-packages)
log_info "Copie des dépendances Python..."
mkdir -p Visualisateur.AppDir/usr/lib/python3.11
cp -rL output/usr/lib/python3.11/site-packages Visualisateur.AppDir/usr/lib/python3.11/

# Créer les symlinks manquants pour pygame.libs afin d'éviter les dépendances PulseAudio erronées
if [ -d Visualisateur.AppDir/usr/lib/python3.11/site-packages/pygame.libs ]; then
    pushd Visualisateur.AppDir/usr/lib/python3.11/site-packages/pygame.libs > /dev/null
    for source in libpulse-simple*.so*; do
        if [ -f "$source" ]; then
            ln -sf "$source" libpulse-simple.so.0
            break
        fi
    done
    for source in libpulse*.so*; do
        if [ -f "$source" ] && [[ "$source" != libpulse-simple*.so* ]] ; then
            ln -sf "$source" libpulse.so.0
            break
        fi
    done
    for source in libpulsecommon*.so*; do
        if [ -f "$source" ]; then
            ln -sf "$source" libpulsecommon.so
            ln -sf "$source" libpulsecommon.so.0
            break
        fi
    done
    popd > /dev/null
fi

# Créer les symlinks manquants dans usr/lib/pulseaudio aussi
if [ -d Visualisateur.AppDir/usr/lib/pulseaudio ]; then
    pushd Visualisateur.AppDir/usr/lib/pulseaudio > /dev/null
    for source in libpulsecommon*.so*; do
        if [ -f "$source" ]; then
            ln -sf "$source" libpulsecommon.so
            ln -sf "$source" libpulsecommon.so.0
            break
        fi
    done
    for source in libpulse-simple*.so*; do
        if [ -f "$source" ]; then
            ln -sf "$source" libpulse-simple.so.0
            break
        fi
    done
    for source in libpulse*.so*; do
        if [ -f "$source" ] && [[ "$source" != libpulse-simple*.so* ]] ; then
            ln -sf "$source" libpulse.so.0
            break
        fi
    done
    popd > /dev/null
fi

# Copier les libs système sans les bibliothèques PulseAudio conflictuelles
if [ -d output/usr/lib ]; then
    mkdir -p Visualisateur.AppDir/usr/lib
    find output/usr/lib -maxdepth 1 -type f -name '*.so*' ! -name 'libpulse*' ! -name 'libpulse-simple*' ! -name 'libpulsecommon*' -exec cp -rL {} Visualisateur.AppDir/usr/lib/ \; 2>/dev/null || true
fi

# Copier le code source
log_info "Copie du code source..."
mkdir -p Visualisateur.AppDir/usr/app
cp -r output/usr/app/* Visualisateur.AppDir/usr/app/
rm -rf Visualisateur.AppDir/usr/app/__pycache__ 2>/dev/null || true
find Visualisateur.AppDir/usr/app -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find Visualisateur.AppDir/usr/app -name "*.pyc" -delete 2>/dev/null || true

# Copier les exécutables utiles (ffmpeg/ffprobe)
if [ -d output/usr/bin ]; then
    mkdir -p Visualisateur.AppDir/usr/bin
    cp -rL output/usr/bin Visualisateur.AppDir/usr/ 2>/dev/null || true
fi

# Copier les bibliothèques PulseAudio restantes
if [ -d output/usr/lib/pulseaudio ]; then
    mkdir -p Visualisateur.AppDir/usr/lib
    cp -rL output/usr/lib/pulseaudio Visualisateur.AppDir/usr/lib/ 2>/dev/null || true
fi

# Icône
if [ -f "assets/icon.png" ]; then
    cp assets/icon.png Visualisateur.AppDir/usr/share/icons/hicolor/256x256/apps/visualisateur.png
    cp assets/icon.png Visualisateur.AppDir/visualisateur.png
fi

# Compter la taille
APPDIR_SIZE=$(du -sh Visualisateur.AppDir/usr/lib/python3.11 2>/dev/null | cut -f1 || echo "?")
log_info "Taille des libs Python: $APPDIR_SIZE"

# AppRun - script de lancement (version Python système)
cat > Visualisateur.AppDir/AppRun << 'APPRUN_EOF'
#!/bin/bash
SELF_DIR=$(dirname "$(readlink -f "$0")")

# Utiliser Python 3.11 du système hôte (nécessite Python 3.11 avec tkinter)
PYTHON="python3.11"
if command -v python3.11 &> /dev/null; then
    PYTHON="python3.11"
elif command -v python3 &> /dev/null && python3 -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 11) else 1)' &> /dev/null; then
    PYTHON="python3"
else
    echo "Python 3.11 requis introuvable. Installez python3.11 et relancez l'AppImage." >&2
    exit 1
fi
export LD_LIBRARY_PATH="$SELF_DIR/usr/lib/python3.11/site-packages/pygame.libs:$SELF_DIR/usr/lib/pulseaudio:$SELF_DIR/usr/lib:$LD_LIBRARY_PATH"
export PYTHONPATH="$SELF_DIR/usr/lib/python3.11/site-packages:$SELF_DIR/usr/app:$PYTHONPATH"
export PATH="$SELF_DIR/usr/bin:$PATH"

# Prefer embedded ffmpeg tools for pydub
export FFMPEG_PATH="$SELF_DIR/usr/bin/ffmpeg"
export FFPROBE_PATH="$SELF_DIR/usr/bin/ffprobe"

# Buffer audio réduit
export SDL_AUDIO_BUFFER_SIZE=1024

# Vérifier la disponibilité de libpulsecommon
if [ -f "$SELF_DIR/usr/lib/pulseaudio/libpulsecommon-17.0.so" ]; then
    export LD_LIBRARY_PATH="$SELF_DIR/usr/lib/pulseaudio:$LD_LIBRARY_PATH"
fi

# Détection automatique du système audio
# Préférer PulseAudio/PipeWire lorsque disponibles, sinon ALSA
if [ -d "/run/user/$(id -u 2>/dev/null || echo 1000)/pulse" ] 2>/dev/null; then
    export SDL_AUDIODRIVER=pulseaudio
elif pgrep -x "pipewire" > /dev/null 2>&1 || pgrep -x "wireplumber" > /dev/null 2>&1; then
    export SDL_AUDIODRIVER=pulseaudio
elif [ -e "/dev/snd" ]; then
    export SDL_AUDIODRIVER=alsa
else
    export SDL_AUDIODRIVER=dummy
    export NO_SOUND=1
fi

cd "$SELF_DIR/usr/app"
exec "$PYTHON" main.py "$@"
APPRUN_EOF
chmod +x Visualisateur.AppDir/AppRun

# Desktop file
cat > Visualisateur.AppDir/visualisateur.desktop << 'DESKTOP_EOF'
[Desktop Entry]
Name=Visualisateur Psychédélique
Comment=Visualisateur audio psychédélique
Exec=AppRun
Icon=visualisateur
Type=Application
Categories=AudioVideo;Player;Graphics;
Terminal=false
DESKTOP_EOF

# Builder l'AppImage
log_info "Création de l'AppImage..."
ARCH=x86_64 ./appimagetool-x86_64.AppImage Visualisateur.AppDir "$DIST_DIR/Visualisateur_Psychedelic.AppImage" 2>&1 | tail -10 || true

if [ -f "$DIST_DIR/Visualisateur_Psychedelic.AppImage" ]; then
    chmod +x "$DIST_DIR/Visualisateur_Psychedelic.AppImage"
    log_success "AppImage créée : $DIST_DIR/Visualisateur_Psychedelic.AppImage"
    ls -lh "$DIST_DIR/Visualisateur_Psychedelic.AppImage"
else
    log_error "Échec création AppImage"
fi

echo ""
echo "========================================"
echo "Lance avec :"
echo "  ./dist_standalone/Visualisateur_Psychedelic.AppImage"
echo "========================================"