# Build AppImage - Visualize

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
└── Visualize.AppImage    # Fichier exécutable unique
```

**Utilisation :**
```bash
chmod +x dist_standalone/Visualize.AppImage
./dist_standalone/Visualize.AppImage
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
SDL_AUDIODRIVER=alsa ./Visualize.AppImage

# Forcer mode sans son
NO_SOUND=1 ./Visualize.AppImage
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
chmod +x dist_standalone/Visualize.AppImage
./dist_standalone/Visualize.AppImage
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
chmod +x Visualize.AppImage

# Vérifier que Python 3.11 est installé
python3.11 --version

# Lancer avec debug
./Visualize.AppImage --appimage-extract-and-run
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
SDL_AUDIODRIVER=alsa ./Visualize.AppImage

# Mode sans son
NO_SOUND=1 ./Visualize.AppImage
```

### 🔧 Fedora 44 / PipeWire (dépannage spécifique)

Sur Fedora 44 qui utilise **PipeWire** par défaut au lieu de PulseAudio, l'AppImage utilise ffplay comme backend audio pour éviter les conflits de bibliothèques.

```bash
# Vérifier que ffplay est installé
which ffplay || sudo dnf install ffmpeg

# Vérifier PipeWire
pgrep -x "pipewire" && echo "PipeWire détecté" || echo "PulseAudio ou autre"

# Relancer l'AppImage (ffplay sera utilisé automatiquement)
./Visualize.AppImage
```

### 🎨 Fedora 44 / GNOME — Icônes & lanceur

GNOME n'intègre pas automatiquement les AppImages : tant qu'aucun fichier
`.desktop` utilisateur n'est enregistré, le dock et la vue Activités affichent
une icône générique. Le dépôt fournit un script d'intégration par utilisateur,
idempotent et sans droit root :

```bash
chmod +x Visualize.AppImage
./scripts/integrate_appimage.sh dist_standalone/Visualize.AppImage
```

Le script installe les icônes dans `~/.local/share/icons/hicolor/`, crée
`~/.local/share/applications/visualize.desktop` (avec
`StartupWMClass=Visualize`) et rafraîchit le cache GTK. Lancez ensuite
l'application depuis Activités puis épinglez-la au dock. Si l'icône du dock
reste générique, déconnectez/reconnectez-vous (ou `Alt+F2 r` sous X11).
Options : `--dry-run` (prévisualisation), `--force` (écrase un `.desktop`
personnalisé), et accepte aussi un dossier `Visualize.AppDir`.

**Icône du fichier `.AppImage` dans Files (Nautilus)** : contrairement à
d'autres gestionnaires, GNOME Files n'extrait pas les icônes embarquées ;
il faut un thumbnailer système (non fourni par Fedora) :
- recommandé : **AppImageLauncher** (RPM depuis ses releases GitHub ou un COPR),
  qui propose « Integrate » au premier lancement ;
- sinon : `appimage-thumbnailer` (script upstream ou paquet COPR).
Sans l'un de ces outils, le fichier garde une icône générique — c'est normal.

**Diagnostic** : vérifiez la classe de fenêtre avec `xprop | grep WM_CLASS`
(X11) ou le Looking Glass (`Alt+F2` → `lg` → onglet *Windows*) ; elle doit
valoir `"Visualize"`. Le script conserve précisément cette valeur via
`StartupWMClass=Visualize`.

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