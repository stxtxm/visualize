# Build AppImage - Visualisateur Psychédélique

> **Application portable semi-standalone** — fonctionne sur Fedora, Debian, Ubuntu, Linux Mint et toute distribution Linux.
> Build via Podman (Docker) pour un environnement reproductible.

---

## 📦 Format : AppImage

| Format | Taille | Portabilité | Usage |
|--------|--------|-------------|-------|
| **AppImage** | ~180-200 MB | ⭐⭐⭐⭐ | Distribution publique — nécessite Python 3.11 sur la machine cible |

---

## 🔧 Prérequis pour l'utilisation

L'AppImage utilise **Python 3.11 du système hôte** pour éviter les problèmes de compatibilité des bibliothèques système.

### Sur Fedora
```bash
sudo dnf install python3.11 python3.11-pip python3.11-tkinter
```

### Sur Debian/Ubuntu
```bash
sudo apt install python3.11 python3.11-pip python3.11-tk
```

### Autres dépendances recommandées (pour audio/vidéo)
```bash
# Fedora
sudo dnf install SDL2 SDL2_mixer SDL2_image SDL2_ttf portaudio pulseaudio ffmpeg

# Debian/Ubuntu
sudo apt install libsdl2-2.0-0 libsdl2-mixer-2.0-0 libsdl2-image-2.0-0 libsdl2-ttf-2.0-0 portaudio19-dev pulseaudio ffmpeg
```

### Vérification des prérequis
```bash
# Vérifier Python 3.11
python3.11 --version

# Vérifier tkinter
python3.11 -c "import tkinter; print('tkinter OK')"
```

---

## 🚀 Build de l'AppImage

### Depuis le répertoire du projet :

```bash
# Build AppImage (recommandé pour distribution)
make standalone-appimage

# Nettoyer les builds
make standalone-clean
```

### Ou via le script directement :

```bash
./build_standalone.sh
```

Le résultat se trouve dans `dist_standalone/` :

```
dist_standalone/
└── Visualisateur_Psychedelic.AppImage    # Fichier exécutable unique
```

**Utilisation :**
```bash
chmod +x dist_standalone/Visualisateur_Psychedelic.AppImage
./dist_standalone/Visualisateur_Psychedelic.AppImage
```

---

## ✅ Ce qui est inclus dans l'AppImage

- **Dépendances Python** (numpy, pygame, opencv, pydub, Pillow, scipy)
- **Code source complet** de l'application

**Ce qui n'est PAS inclus (utilisé depuis le système hôte) :**
- Python 3.11 (exécutable)
- Bibliothèques système (SDL2, PortAudio, PulseAudio, ALSA, OpenGL, X11, Tcl/Tk)
- FFmpeg

---

## 🔊 Son dans l'AppImage

L'AppImage détecte automatiquement le système audio au lancement :

 | Système audio | Comportement |
 |---------------|-------------|
 | **PipeWire** | Utilise ffplay comme fallback (compatible avec Fedora 44) |
 | **PulseAudio** | Utilisé par défaut (meilleure latence) |
 | **ALSA** | Fallback automatique si /dev/snd existe |
 | **Aucun** | Mode dummy silencieux (NO_SOUND=1 activé) |

Pour forcer un mode :
```bash
# Forcer ALSA
SDL_AUDIODRIVER=alsa ./Visualisateur_Psychedelic.AppImage

# Forcer mode sans son
NO_SOUND=1 ./Visualisateur_Psychedelic.AppImage
```

---

## 🔧 Prérequis pour le Build

Le build utilise `build_standalone.sh`, qui détecte automatiquement **Docker** ou **Podman** (`$CONTAINER_CMD`).

### Sur Fedora
```bash
sudo dnf install docker wget tar gzip python3-venv python3-pip
```

### Sur Debian/Ubuntu
```bash
sudo apt install docker.io wget tar gzip python3-venv python3-pip
```

Le build se fait **dans un conteneur** (Docker par défaut, Podman si détecté) — pas besoin d'installer les dépendances Python en local.

---

## 📋 Workflows

### 1. Build AppImage
```bash
make standalone-appimage
ls -lh dist_standalone/
```

### 2. Tester l'AppImage
```bash
chmod +x dist_standalone/Visualisateur_Psychedelic.AppImage
./dist_standalone/Visualisateur_Psychedelic.AppImage
```

### 3. Nettoyer
```bash
make standalone-clean
```

---

## 🐛 Dépannage

### ❌ AppImage ne se lance pas
```bash
# Vérifier les permissions
chmod +x Visualisateur_Psychedelic.AppImage

# Vérifier que Python 3.11 est installé
python3.11 --version

# Lancer avec debug
./Visualisateur_Psychedelic.AppImage --appimage-extract-and-run
```

### ❌ Erreur "module not found"
```bash
# L'AppImage inclut toutes les dépendances Python nécessaires
# Si erreur, vérifier que Python 3.11 est bien utilisé
python3.11 --version
```

### ❌ Pas de son
```bash
# Vérifier PulseAudio
pulseaudio --check && echo "OK" || echo "PulseAudio non démarré"

# Fedora 44 (PipeWire) - installer ffplay si absent
sudo dnf install ffmpeg

# Forcer ALSA
SDL_AUDIODRIVER=alsa ./Visualisateur_Psychedelic.AppImage

# Mode sans son
NO_SOUND=1 ./Visualisateur_Psychedelic.AppImage
```

### 🔧 Fedora 44 / PipeWire (dépannage spécifique)

Sur Fedora 44 qui utilise **PipeWire** par défaut au lieu de PulseAudio, l'AppImage utilise ffplay comme backend audio pour éviter les conflits de bibliothèques.

```bash
# Vérifier que ffplay est installé
which ffplay || sudo dnf install ffmpeg

# Vérifier PipeWire
pgrep -x "pipewire" && echo "PipeWire détecté" || echo "PulseAudio ou autre"

# Relancer l'AppImage (ffplay sera utilisé automatiquement)
./Visualisateur_Psychedelic.AppImage
```

Pour vérifier les logs d'erreur audio, cliquez sur le bouton "📝 Logs" dans l'interface.

### ❌ Pas de rendu graphique
```bash
# Vérifier qu'un serveur X11 est accessible
echo $DISPLAY
```

---

## 📚 Références

- [linuxdeploy](https://github.com/linuxdeploy/linuxdeploy)
- [AppImage](https://appimage.org/)