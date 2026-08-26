#!/bin/bash
# =============================================================================
# Build AppImage - Visualize
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
rm -rf Visualize.AppDir output/ Dockerfile.appimage
mkdir -p "$DIST_DIR" output

# Créer le Dockerfile de build
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
    libportaudio2 libportaudiocpp0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# Vérifier l'installation
RUN python3 -c "import numpy, pygame, cv2, pydub, PIL, sounddevice; print('Tous les imports OK')"

# Créer la structure de sortie
RUN mkdir -p /output/usr/lib/python3.11

# Copier les dépendances Python (site-packages)
RUN cp -r /usr/local/lib/python3.11/site-packages /output/usr/lib/python3.11/

# Copier les exécutables utiles (ffmpeg/ffprobe/ffplay)
RUN mkdir -p /output/usr/bin && \
    for bin in ffmpeg ffprobe ffplay paplay pw-play aplay which; do \
        if [ -x "/usr/bin/$bin" ]; then \
            cp -nL "/usr/bin/$bin" "/output/usr/bin/$bin"; \
        fi; \
    done

# The standalone compatibility path relies on a software H.264 encoder.
RUN ffmpeg -hide_banner -encoders 2>/dev/null | grep -q 'libx264' || \
    (echo 'ERROR: bundled FFmpeg has no libx264 encoder' >&2 && exit 1)

# Copier les bibliothèques système SDL2, audio et PortAudio
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
        /usr/lib/x86_64-linux-gnu/libjack.so.* \
        /usr/lib/x86_64-linux-gnu/libdbus-1.so.* \
        /usr/lib/x86_64-linux-gnu/libdb-*.so* \
        ; do \
        cp -nL $lib /output/usr/lib/ 2>/dev/null || true; \
    done

# Copy the complete transitive runtime closure of FFmpeg. The explicit list
# above covers the common codecs, but distributions may add dependencies such
# as pocketsphinx, VAAPI, or other demuxer libraries. Missing one makes the
# bundled FFmpeg fail before the first audio frame on an otherwise valid host.
RUN set -eux; \
    for binary in /usr/bin/ffmpeg /usr/bin/ffprobe /usr/bin/ffplay; do \
        ldd "$binary" 2>/dev/null | awk '/=> \/.* \(/ {print $3} /^[[:space:]]*\/[^ ]+ \(0x/ {print $1}'; \
    done | sort -u | while read -r lib; do \
        if [ -f "$lib" ]; then cp -nL "$lib" /output/usr/lib/; fi; \
    done

RUN set -eux; \
    for pass in $(seq 1 8); do \
        deps=$(mktemp); \
        find /output/usr/lib -type f -name '*.so*' -exec ldd {} \; 2>/dev/null | \
            awk '/=> \/.* \(/ {print $3} /^[[:space:]]*\/[^ ]+ \(0x/ {print $1}' | \
            sort -u > "$deps"; \
        changed=0; \
        while read -r lib; do \
            if [ -f "$lib" ] && [ ! -e "/output/usr/lib/$(basename "$lib")" ]; then \
                cp -L "$lib" /output/usr/lib/; changed=1; \
            fi; \
        done < "$deps"; \
        rm -f "$deps"; \
        [ "$changed" -eq 0 ] && break; \
    done

# Never override the host's glibc/runtime ABI from an AppImage. These core
# libraries must be resolved from the host kernel/userspace; bundling them can
# make an otherwise valid FFmpeg binary segfault on another distribution.
RUN rm -f \
    /output/usr/lib/libc.so* \
    /output/usr/lib/libm.so* \
    /output/usr/lib/libdl.so* \
    /output/usr/lib/libpthread.so* \
    /output/usr/lib/librt.so* \
    /output/usr/lib/libresolv.so* \
    /output/usr/lib/libutil.so* \
    /output/usr/lib/libgcc_s.so* \
    /output/usr/lib/libstdc++.so* \
    /output/usr/lib/ld-linux*.so*
    
# Copier la bibliothèque FFmpeg runtime requise par ffmpeg/ffprobe
# Inclut libx264 pour l'encodage H.264 (compatible Fedora, Windows, macOS)
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
        /usr/lib/x86_64-linux-gnu/libx264* \
        /usr/lib/x86_64-linux-gnu/libx265* \
        /usr/lib/x86_64-linux-gnu/libopenh264* \
        /usr/lib/x86_64-linux-gnu/libvpx* \
        /usr/lib/x86_64-linux-gnu/libopus* \
        ; do \
        cp -nL $lib /output/usr/lib/ 2>/dev/null || true; \
    done

# Ajouter aussi les bibliothèques PulseAudio
RUN mkdir -p /output/usr/lib/pulseaudio && \
    for lib in \
        /usr/lib64/pulseaudio/libpulsecommon*.so* /usr/lib64/pulseaudio/libpulsedsp.so* \
        /usr/lib/x86_64-linux-gnu/pulseaudio/libpulsecommon*.so* /usr/lib/x86_64-linux-gnu/pulseaudio/libpulsedsp.so* \
        /usr/lib/x86_64-linux-gnu/libpulse-simple.so* /usr/lib/x86_64-linux-gnu/libpulse.so* ; do \
        cp -nL "$lib" /output/usr/lib/pulseaudio/ 2>/dev/null || true; \
    done
DOCKERFILE_EOF

# Détecter le conteneur disponible (docker ou podman)
CONTAINER_CMD="${CONTAINER_CMD:-}"
if [ -z "$CONTAINER_CMD" ]; then
    if command -v docker &>/dev/null; then
        CONTAINER_CMD=docker
    elif command -v podman &>/dev/null; then
        CONTAINER_CMD=podman
    else
        log_error "Ni docker ni podman trouvé. Installez l'un des deux."
    fi
fi
log_info "Utilisation de: $CONTAINER_CMD"

# Build conteneur
BUILD_LOG="/tmp/visualizer_build.log"
log_info "Build du conteneur $CONTAINER_CMD..."
MOUNT_FLAG=""
if [ "$CONTAINER_CMD" = "podman" ] || ($CONTAINER_CMD --version 2>/dev/null | grep -q -i "podman"); then
    MOUNT_FLAG=":Z"
fi
if ! $CONTAINER_CMD build -t visualize-appimage -f Dockerfile.appimage . > "$BUILD_LOG" 2>&1; then
    tail -10 "$BUILD_LOG"
    log_error "Build du conteneur échoué. Voir $BUILD_LOG"
fi

# Détecter si le moteur est réellement podman (même via l'alias docker)
IS_PODMAN=false
if [ "$CONTAINER_CMD" = "podman" ] || ($CONTAINER_CMD --version 2>/dev/null | grep -q -i "podman"); then
    IS_PODMAN=true
fi

# Extraction
log_info "Extraction des fichiers..."
rm -rf output/
mkdir -p output
# En rootless podman, l'uid 0 du conteneur est mappé sur l'utilisateur hôte :
# il faut donc chown en 0:0 dans le conteneur pour récupérer les droits sur l'hôte.
# Avec docker (daemon rootful), on chown directement vers l'uid/gid hôte.
if [ "$IS_PODMAN" = true ]; then
    CHOWN_TARGET="0:0"
else
    CHOWN_TARGET="$(id -u):$(id -g)"
fi
$CONTAINER_CMD run --rm -v "$SCRIPT_DIR/output:/out${MOUNT_FLAG}" visualize-appimage sh -c "cp -rL /output/* /out/ && chown -R $CHOWN_TARGET /out"
# Reprendre la propriété côté hôte au cas où les fichiers appartiendraient à root
# (docker rootful ou droits non propagés). sudo si nécessaire.
if [ ! -O "$SCRIPT_DIR/output" ]; then
    if command -v sudo &>/dev/null; then
        sudo chown -R "$(id -u):$(id -g)" "$SCRIPT_DIR/output" || true
    else
        chown -R "$(id -u):$(id -g)" "$SCRIPT_DIR/output" 2>/dev/null || true
    fi
fi


# Copier le code source dans output/usr/app sans inclure les artefacts de build
mkdir -p output/usr/app
tar --exclude='./output' --exclude='./dist_standalone' --exclude='./Visualize.AppDir' --exclude='./appimagetool-x86_64.AppImage' --exclude='./Dockerfile.appimage' --exclude='./.git' -cf - . | tar -C output/usr/app -xpf -

# Injecter la version actuelle de git dans version.py pour l'AppImage
GIT_VERSION=$(git describe --tags --always 2>/dev/null || echo "0.0.2")
echo "__version__ = \"$GIT_VERSION\"" > output/usr/app/version.py


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
rm -rf Visualize.AppDir
mkdir -p Visualize.AppDir/usr/lib
mkdir -p Visualize.AppDir/usr/share/applications
mkdir -p Visualize.AppDir/usr/share/icons/hicolor/256x256/apps

# Copier les dépendances Python (site-packages)
log_info "Copie des dépendances Python..."
mkdir -p Visualize.AppDir/usr/lib/python3.11
cp -rL output/usr/lib/python3.11/site-packages Visualize.AppDir/usr/lib/python3.11/

# Créer les symlinks manquants pour pygame.libs
if [ -d Visualize.AppDir/usr/lib/python3.11/site-packages/pygame.libs ]; then
    pushd Visualize.AppDir/usr/lib/python3.11/site-packages/pygame.libs > /dev/null
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
if [ -d Visualize.AppDir/usr/lib/pulseaudio ]; then
    pushd Visualize.AppDir/usr/lib/pulseaudio > /dev/null
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
    mkdir -p Visualize.AppDir/usr/lib
    find output/usr/lib -maxdepth 1 -type f -name '*.so*' ! -name 'libpulse*' ! -name 'libpulse-simple*' ! -name 'libpulsecommon*' -exec cp -rL {} Visualize.AppDir/usr/lib/ \; 2>/dev/null || true
fi

# Copier le code source
log_info "Copie du code source..."
mkdir -p Visualize.AppDir/usr/app
cp -r output/usr/app/* Visualize.AppDir/usr/app/
rm -rf Visualize.AppDir/usr/app/__pycache__ 2>/dev/null || true
find Visualize.AppDir/usr/app -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find Visualize.AppDir/usr/app -name "*.pyc" -delete 2>/dev/null || true

# Copier les exécutables utiles (ffmpeg/ffprobe)
if [ -d output/usr/bin ]; then
    mkdir -p Visualize.AppDir/usr/bin
    cp -rL output/usr/bin Visualize.AppDir/usr/ 2>/dev/null || true
fi

# Copier les bibliothèques PulseAudio restantes
if [ -d output/usr/lib/pulseaudio ]; then
    mkdir -p Visualize.AppDir/usr/lib
    cp -rL output/usr/lib/pulseaudio Visualize.AppDir/usr/lib/ 2>/dev/null || true
fi

# Icône
if [ -f "assets/icon.png" ]; then
    cp assets/icon.png Visualize.AppDir/usr/share/icons/hicolor/256x256/apps/visualize.png
    cp assets/icon.png Visualize.AppDir/visualize.png
fi

# Compter la taille
APPDIR_SIZE=$(du -sh Visualize.AppDir/usr/lib/python3.11 2>/dev/null | cut -f1 || echo "?")
log_info "Taille des libs Python: $APPDIR_SIZE"

# AppRun - script de lancement (compatible Python 3.11+)
cat > Visualize.AppDir/AppRun << 'APPRUN_EOF'
#!/bin/bash
SELF_DIR=$(dirname "$(readlink -f "$0")")
export SELF_DIR="$SELF_DIR"

# Python 3.11 OBLIGATOIRE : les packages embarqués (.so) sont compilés pour Python 3.11
# Tester d'abord python3.11, puis fallback vers d'autres si vraiment absent
PYTHON=""
for candidate in python3.11 python3.12 python3.10; do
    if command -v "$candidate" &> /dev/null; then
        # Vérifier que tkinter ET numpy fonctionnent (test les packages embarqués)
        if "$candidate" -c "
import sys
sys.path.insert(0, '$SELF_DIR/usr/lib/python3.11/site-packages')
import tkinter
import numpy
import PIL
" 2>/dev/null; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "Python 3.10+ requis introuvable. Installez python3 et relancez l'AppImage." >&2
    exit 1
fi

# Vérifier que tkinter est disponible
if ! "$PYTHON" -c "import tkinter" 2>/dev/null; then
    echo "tkinter n'est pas disponible pour $PYTHON. Installez python3-tkinter." >&2
    exit 1
fi

# Export PYTHONPATH (sans LD_LIBRARY_PATH problématique pour la compatibilité PipeWire)
export PYTHONPATH="$SELF_DIR/usr/lib/python3.11/site-packages:$SELF_DIR/usr/app:$PYTHONPATH"

# Always prefer the FFmpeg shipped in the AppImage. This keeps the codec set
# and runtime libraries identical on every host. Hardware H.264 is probed only
# when the host really supports it; bundled libx264 remains the universal
# software fallback and does not require a GPU driver.
if [ -x "$SELF_DIR/usr/bin/ffmpeg" ]; then
    export FFMPEG_PATH="$SELF_DIR/usr/bin/ffmpeg"
    # Keep the software fallback bounded on long 4K rawvideo exports. The
    # quality target remains CRF 18; only x264's memory-heavy lookahead preset
    # is changed when no usable hardware encoder is available.
    export VISUALIZE_4K_SAFE=1
    # Prefer the bundled x264 over OpenH264 for the software fallback. x264
    # preserves the existing CRF/profile quality settings; hardware probing
    # still has priority when a usable GPU encoder exists.
    export VISUALIZE_PREFER_X264=1
    export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:+$LD_LIBRARY_PATH:}$SELF_DIR/usr/lib"
elif command -v ffmpeg &> /dev/null; then
    export FFMPEG_PATH=$(command -v ffmpeg)
fi

if [ -x "$SELF_DIR/usr/bin/ffprobe" ]; then
    export FFPROBE_PATH="$SELF_DIR/usr/bin/ffprobe"
elif command -v ffprobe &> /dev/null; then
    export FFPROBE_PATH=$(command -v ffprobe)
fi

# Buffer audio réduit pour pygame
export SDL_AUDIO_BUFFER_SIZE=1024

# Détection améliorée du système audio pour Fedora 44/PipeWire
# Priorité : ffplay > sounddevice > pw-play > autres (ffplay est le plus fiable sur PipeWire)
HAS_PIPEWIRE=false
HAS_PULSEAUDIO=false

# Détecter PipeWire (Fedora 44 et autres distributions modernes)
if command -v pw-meta &> /dev/null 2>&1 || command -v pw-play &> /dev/null 2>&1; then
    HAS_PIPEWIRE=true
fi

# Détecter PulseAudio natif
if command -v paplay &> /dev/null 2>&1; then
    HAS_PULSEAUDIO=true
fi

# Configuration audio adaptée au système
# Priorité : pw-play (natif PipeWire) > aplay (ALSA compat) > sounddevice > autres
    if [ "$HAS_PIPEWIRE" = true ]; then
        echo "Audio: PipeWire détecté - utilisation pw-play comme backend principal"
        # Ne PAS ajouter usr/lib pour éviter les conflits de libportaudio avec PipeWire
        # (le système a ses propres libs audio compatibles)
        export LD_LIBRARY_PATH="$SELF_DIR/usr/lib/python3.11/site-packages/pygame.libs"
    # Priorité 1: pw-play (natif PipeWire, le plus fiable sur Fedora 44)
    # Priorité 2: aplay (compat ALSA de PipeWire)
    if command -v pw-play &> /dev/null 2>&1; then
        export PREFERRED_AUDIO_BACKEND=pw-play
        echo "Audio: pw-play prioritaire (natif PipeWire)"
    elif command -v aplay &> /dev/null 2>&1; then
        export PREFERRED_AUDIO_BACKEND=aplay
        echo "Audio: aplay prioritaire (ALSA compat PipeWire)"
    else
        export PREFERRED_AUDIO_BACKEND=sounddevice
        echo "Audio: sounddevice prioritaire (pw-play et aplay absents)"
    fi
    # Exporter PULSE_SERVER pour forcer la connexion au serveur Pulse native
    export PULSE_SERVER=
elif [ "$HAS_PULSEAUDIO" = true ]; then
    echo "Audio: PulseAudio détecté"
    export LD_LIBRARY_PATH="$SELF_DIR/usr/lib/python3.11/site-packages/pygame.libs:$SELF_DIR/usr/lib/pulseaudio:$SELF_DIR/usr/lib:$LD_LIBRARY_PATH"
    export SDL_AUDIODRIVER=pulseaudio
    export PREFERRED_AUDIO_BACKEND=sounddevice
else
    # Pas de serveur audio détecté, utiliser les libs embarquées
    export LD_LIBRARY_PATH="$SELF_DIR/usr/lib/python3.11/site-packages/pygame.libs:$SELF_DIR/usr/lib/pulseaudio:$SELF_DIR/usr/lib:$LD_LIBRARY_PATH"
    if [ -e "/dev/snd" ]; then
        export SDL_AUDIODRIVER=alsa
        export PREFERRED_AUDIO_BACKEND=sounddevice
    else
        export SDL_AUDIODRIVER=dummy
        export NO_SOUND=1
    fi
fi

# Forcer sounddevice à utiliser les backends natifs
export SD_ENABLE_ALSA=1
export SD_ENABLE_PULSEAUDIO=1

exec "$PYTHON" "$SELF_DIR/usr/app/main.py" "$@"
APPRUN_EOF
chmod +x Visualize.AppDir/AppRun

# Desktop file
cat > Visualize.AppDir/visualize.desktop << 'DESKTOP_EOF'
[Desktop Entry]
Name=Visualize
Comment=Audio visualizer
Exec=AppRun
Icon=visualize
Type=Application
Categories=AudioVideo;Player;Graphics;
Terminal=false
DESKTOP_EOF

# Vérifier/télécharger le runtime AppImage
RUNTIME="${RUNTIME_PATH:-/tmp/runtime-x86_64}"
if [ ! -f "$RUNTIME" ]; then
    log_info "Téléchargement du runtime AppImage..."
    curl -L --max-time 60 -o "$RUNTIME" \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/runtime-x86_64" || \
        log_error "Échec du téléchargement du runtime"
    chmod +x "$RUNTIME"
fi

# Builder l'AppImage
log_info "Création de l'AppImage..."
python3 create_appimage.py "$RUNTIME" Visualize.AppDir "$DIST_DIR/Visualize.AppImage"

if [ -f "$DIST_DIR/Visualize.AppImage" ]; then
    chmod +x "$DIST_DIR/Visualize.AppImage"
    log_success "AppImage créée : $DIST_DIR/Visualize.AppImage"
    ls -lh "$DIST_DIR/Visualize.AppImage"
else
    log_error "Échec création AppImage"
fi

echo ""
echo "========================================"
echo "Lance avec :"
echo "  ./dist_standalone/Visualize.AppImage"
echo "========================================"
