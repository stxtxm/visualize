# Builds Standalone - Visualisateur Psychédélique

> **Application standalone optimisée pour la fluidité et la portabilité**
> Fonctionne sur Fedora, Debian, Ubuntu, Linux Mint et autres distributions Linux

---

## 📦 Formats Disponibles

| Format | Taille Estimée | Portabilité | Usage Recommandé | Dépendances Hôte |
|--------|---------------|-------------|------------------|------------------|
| **AppImage** | ~150-200 MB | ⭐⭐⭐⭐⭐ | Distribution publique | Aucune |
| **Bundle Portable** | ~80-100 MB | ⭐⭐⭐⭐ | Usage personnel | Python 3.x, libs système |

---

## 🚀 Commandes de Build

### Depuis le répertoire du projet :

```bash
# Build TOUT (AppImage + Bundle Portable)
make standalone-all

# Build AppImage SEULEMENT (recommandé pour distribution)
make standalone-appimage

# Build Bundle Portable SEULEMENT (pour usage perso)
make standalone-portable

# Nettoyer les builds
make standalone-clean
```

### Ou via le script directement :

```bash
# Build AppImage
./build_standalone.sh appimage

# Build Bundle Portable
./build_standalone.sh portable

# Build Docker (pour dev)
./build_standalone.sh docker

# Tout build
./build_standalone.sh all

# Aide
./build_standalone.sh help
```

---

## 📂 Structure des Fichiers Générés

### AppImage
```
dist_standalone/
└── Visualisateur_Psychedelic.AppImage    # Fichier exécutable unique
```

**Utilisation :**
```bash
chmod +x dist_standalone/Visualisateur_Psychedelic.AppImage
./dist_standalone/Visualisateur_Psychedelic.AppImage
```

### Bundle Portable
```
dist_standalone/
└── Visualisateur_Psychedelic_Linux.tar.gz    # Archive complète
    (ou .zip si zip est installé)
```

**Contenu de l'archive :**
```
Visualisateur_Psychedelic_Linux/
├── app/                          # Code source
│   ├── main.py
│   ├── audio/
│   ├── effects/
│   ├── renderer/
│   ├── ui/
│   ├── utils/
│   ├── recorder/
│   └── assets/
├── bin/                         # Python virtualenv
│   ├── python3
│   ├── pip
│   └── ...
├── lib/                         # Dépendances Python
│   └── python3.11/site-packages/
│       ├── numpy/
│       ├── opencv_python/
│       ├── pygame/
│       └── ...
└── run_visualisateur.sh          # Script de lancement intelligent
```

**Utilisation :**
```bash
# Extraire l'archive
tar xzf dist_standalone/Visualisateur_Psychedelic_Linux.tar.gz

# Lancer
cd Visualisateur_Psychedelic_Linux
./run_visualisateur.sh
```

---

## ⚙️ Optimisations pour la Fluidité

### Problème résolu : Son Saccadé

Les builds standalone incluent des **optimisations spécifiques** pour éviter les saccades :

1. **`SDL_AUDIO_BUFFER_SIZE=1024`** - Buffer audio réduit pour minimiser la latence
2. **Détection automatique du système audio** :
   - Essaye PulseAudio d'abord (recommandé)
   - Fallback vers ALSA si PulseAudio non disponible
   - Mode `NO_SOUND=1` avec driver `dummy` si aucun système audio
3. **Gestion intelligente des dépendances** dans les scripts de lancement

### Performances

| Configuration | FPS Attendus | Latence Audio | Taille |
|--------------|-------------|---------------|-------|
| Preset `dev` | 15 FPS | ~15ms | 720p |
| Preset `fast` | 20 FPS | ~20ms | 720p |
| Preset `normal` | 30 FPS | ~30ms | 1080p |
| Preset `high` | 60 FPS | ~50ms | 1080p |

---

## 🔧 Prérequis pour le Build

### Sur Fedora (recommandé)

```bash
# Podman (déjà installé par défaut)
sudo dnf update podman

# Outils de build
sudo dnf install wget tar gzip python3-venv python3-pip

# Pour les dépendances système (si build en local)
sudo dnf install python3-devel gcc portaudio-devel \
    SDL2-devel SDL2_image-devel SDL2_mixer-devel SDL2_ttf-devel \
    ffmpeg-devel libX11-devel tk-devel
```

### Sur Debian/Ubuntu

```bash
# Podman
sudo apt install podman

# Outils de build
sudo apt install wget tar gzip python3-venv python3-pip

# Pour les dépendances système
sudo apt install python3-dev g++ libportaudio2 libportaudio-dev \
    libsdl2-2.0-0 libsdl2-dev libsdl2-image-2.0-0 libsdl2-image-dev \
    libsdl2-mixer-2.0-0 libsdl2-mixer-dev libsdl2-ttf-2.0-0 libsdl2-ttf-dev \
    ffmpeg libavcodec-dev libtk-dev python3-tk
```

### Sur Arch Linux

```bash
sudo pacman -S podman wget tar gzip python python-pip
sudo pacman -S portaudio sdl2 ffmpeg tk
```

---

## 🎯 Workflows Typiques

### 1. Développement Normal (dans conteneur)

```bash
# Builder l'image de dev
make build

# Lancer la GUI
make run

# ou avec fallback audio
make run-fallback
```

### 2. Build pour Distribution (AppImage)

```bash
# Builder l'AppImage
make standalone-appimage

# Le résultat est dans dist_standalone/
ls -lh dist_standalone/

# Tester l'AppImage
chmod +x dist_standalone/Visualisateur_Psychedelic.AppImage
./dist_standalone/Visualisateur_Psychedelic.AppImage
```

### 3. Build pour Usage Personnel (Bundle Portable)

```bash
# Builder le bundle portable
make standalone-portable

# Extraire et tester
cd /tmp
tar xzf /chemin/vers/visualize/dist_standalone/Visualisateur_Psychedelic_Linux.tar.gz
cd Visualisateur_Psychedelic_Linux
./run_visualisateur.sh
```

### 4. Build Tout

```bash
# Build AppImage + Bundle Portable + Docker
make standalone-all

# Nettoyer
make standalone-clean
```

---

## 🐛 Dépannage

### ❌ "linuxdeploy non trouvé"

**Solution :** Le script le télécharge automatiquement depuis GitHub. Vérifie ta connexion internet.

```bash
# Téléchargement manuel
wget https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
chmod +x linuxdeploy-x86_64.AppImage
```

### ❌ "python3-venv non trouvé"

**Solution :** Installe le package pour créer des virtual environments.

```bash
# Fedora
sudo dnf install python3-virtualenv

# Debian/Ubuntu
sudo apt install python3-venv

# Arch
sudo pacman -S python-pip python-wheel
```

### ❌ "Dépendances Python manquantes"

**Solution :** Le script installe automatiquement les dépendances depuis `requirements.txt`. Si échec :

```bash
# Installer manuellement
pip install -r requirements.txt
```

### ❌ "AppImage ne se lance pas"

**Solution :** Vérifie les permissions et les dépendances.

```bash
# Donner les permissions
chmod +x Visualisateur_Psychedelic.AppImage

# Vérifier les dépendances avec ldd
ldd Visualisateur_Psychedelic.AppImage

# Lancer avec debug
./Visualisateur_Psychedelic.AppImage --appimage-extract-and-run
```

### ❌ "Pas de son dans l'AppImage"

**Solution :** L'AppImage inclut un fallback automatique :

1. **PulseAudio** (priorité) - Vérifie que PulseAudio est actif :
   ```bash
   pulseaudio --check && echo "PulseAudio OK" || echo "PulseAudio non démarré"
   ```

2. **ALSA** (fallback) - Si `/dev/snd` existe

3. **Mode sans son** - Si aucun système audio n'est disponible

Pour forcer un mode :
```bash
# Forcer ALSA
SDL_AUDIODRIVER=alsa ./Visualisateur_Psychedelic.AppImage

# Forcer mode sans son
NO_SOUND=1 ./Visualisateur_Psychedelic.AppImage
```

### ❌ "L'AppImage est lente"

**Solutions :**

1. **Réduire la résolution** : Utilise le preset `dev` ou `fast`
2. **Fermer d'autres applications** : Le rendu vidéo consomme des ressources
3. **Vérifier les pilotes graphiques** :
   ```bash
   glxinfo | grep "OpenGL renderer"
   ```

---

## 📊 Comparaison des Formats

### AppImage

**✅ Avantages :**
- Zéro installation sur la machine cible
- Fonctionne sur toutes les distributions Linux
- Intégration avec le menu des applications
- Un seul fichier à distribuer
- Pas de conflits de dépendances

**⚠️ Inconvénients :**
- Taille plus importante (~150-200 MB)
- Build plus long (nécessite téléchargement de linuxdeploy)
- Peut ne pas fonctionner sur des systèmes très anciens

**📦 Contenu :**
- Python 3.11 complet
- Toutes les dépendances Python (numpy, opencv, pygame, etc.)
- Bibliothèques système nécessaires
- Application complète

---

### Bundle Portable

**✅ Avantages :**
- Plus léger (~80-100 MB)
- Facile à mettre à jour (juste remplacer les fichiers)
- Dépendances Python isolées
- Peut utiliser les bibliothèques système de l'hôte

**⚠️ Inconvénients :**
- Nécessite Python 3.x sur la machine hôte
- Nécessite les bibliothèques système (SDL2, PortAudio, etc.)
- Moins portable (dépend de l'architecture et des libs système)

**📦 Contenu :**
- Python virtual environment
- Dépendances Python
- Code source de l'application
- Script de lancement intelligent

---

## 🎨 Personnalisation

### Changer l'icône

Place une image `icon.png` (256x256) dans le dossier `assets/` avant de builder.

### Changer le nom de l'application

Modifie les variables dans `build_standalone.sh` :
- `APPIMAGE_NAME`
- Nom dans le fichier `.desktop`

### Optimiser la taille

Pour réduire la taille de l'AppImage :

1. **Utiliser UPX** (compression des exécutables) :
   ```bash
   # Installer UPX
   sudo apt install upx-ucl  # Debian/Ubuntu
   sudo dnf install upx      # Fedora
   
   # Builder avec compression
   ./linuxdeploy-x86_64.AppImage --appdir AppDir --output appimage --compression=upx
   ```

2. **Exclure les fichiers inutiles** :
   - Tests (`tests/`)
   - Documentation (`README.md`, etc.)
   - Fichiers temporaires

---

## 📚 Références

- [linuxdeploy](https://github.com/linuxdeploy/linuxdeploy) - Outil de création d'AppImage
- [linuxdeploy-plugin-python](https://github.com/linuxdeploy/linuxdeploy-plugin-python) - Plugin Python pour linuxdeploy
- [AppImage](https://appimage.org/) - Format d'application portable pour Linux
- [Python Virtual Environments](https://docs.python.org/3/library/venv.html) - Documentation officielle

---

## 💬 Support

Pour les problèmes :

1. **Vérifie les logs** : Les scripts affichent des informations détaillées
2. **Vérifie les dépendances** : `ldd` pour les bibliothèques, `pip list` pour Python
3. **Essaie en mode debug** : Ajoute `set -x` au début des scripts pour voir chaque commande

---

## 🎉 Conclusion

Tu as maintenant deux options professionnelles pour distribuer ton application :

- **AppImage** → Pour une distribution large (zéro dépendance)
- **Bundle Portable** → Pour un usage personnel ou des tests

Les deux sont **optimisés pour la fluidité** avec :
- Buffer audio réduit
- Détection automatique du système audio
- Fallback intelligent si problème

**Recommandation :** Utilise **AppImage** pour la distribution publique et **Bundle Portable** pour toi ou des amis qui ont déjà Python installé.
