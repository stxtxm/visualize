# Visualisateur Psychédélique 🎨🎵

> Un outil **100% conteneurisé** pour générer des animations psychédéliques synchronisées avec votre musique, inspiré de Winamp et Windows Media Player.

**Aucune installation sur votre système** - Tout fonctionne dans un conteneur Podman/Docker !

---

## ✨ Fonctionnalités

- **5 effets visuels psychédéliques** : Barres, Cercles, Particules, Tunnel, Vagues
- **4 palettes de couleurs** : Psychédélique, Rétro, Sombre, Arc-en-ciel
- **5 présélections qualité/vitesse** : Dev (ultra-rapide), Rapide, Normale, Haute, 4K
- **Interface graphique** simple et intuitive (dans le conteneur)
- **Export vidéo MP4** en haute qualité : 720p, 1080p, 1440p, 4K
- **Aperçu en temps réel** avant export
- **Zéro dépendance** sur l'hôte (sauf Podman/Docker)

---

## 📊 Présélections de Qualité/Vitesse

| Présélection | Résolution | FPS | FFmpeg Preset | Temps Export | Description |
|--------------|------------|-----|---------------|-------------|-------------|
| `dev` | 720p | 15 | ultrafast | **~0.25x temps réel** | Tests rapides, faible qualité |
| `fast` | 720p | 20 | superfast | **~0.5x temps réel** | Bon compromis |
| `normal` | 1080p | 30 | fast | **~1x temps réel** | Qualité standard |
| `high` | 1080p | 60 | medium | **~1.5x temps réel** | Meilleure qualité |
| `4k` | 4K | 30 | slow | **~2x temps réel** | Qualité maximale |

✅ **Pour des tests ultra-rapides, utilisez `--preset dev` ou `PRESET=dev` !**

---

## 🐳 Prérequis

### Sur Fedora (recommandé)
```bash
# Podman est déjà installé par défaut sur Fedora
# Vérifier qu'il est à jour
sudo dnf update podman

# Installer les outils optionnels pour le son dans l'UI
sudo dnf install pulseaudio xorg-x11-server-Xorg
```

### Sur d'autres distributions Linux
```bash
# Ubuntu/Debian
sudo apt install podman

# Arch Linux
sudo pacman -S podman
```

---

## 📥 Installation

### 1. Cloner le projet
```bash
git clone /home/timo/dev/visualize
cd visualize
```

Ou si vous lisez ceci depuis le répertoire existant, vous êtes déjà au bon endroit !

### 2. Construire l'image Podman
```bash
# Dans le répertoire du projet
make build
```

C'est tout ! 🎉

> **Note** : La construction peut prendre quelques minutes (téléchargement des dépendances Python et système).

---

## 🚀 Utilisation

### 🎨 Avec Interface Graphique (recommandé)
```bash
# Lancer l'interface
make run
```

**Dans l'interface, vous pouvez :**
- Sélectionner un fichier audio depuis `~/Music`
- Choisir un **présélection** (dev, fast, normal, high, 4k)
- Choisir un **effet** (barres, cercles, particules, tunnel, vagues, aléatoire)
- Sélectionner une **palette de couleurs**
- Lancer la lecture/aperçu en temps réel
- Exporter en vidéo MP4 (sauvegardé dans `~/Videos`)

### 🎬 En Ligne de Commande (Export Direct)

#### Export basique
```bash
# Export avec présélection par défaut (normal = 1080p, 30fps)
make run-cli AUDIO=ma_musique.mp3 OUTPUT=ma_video.mp4

# Export ULTRA-RAPIDE pour tests (0.25x temps réel !)
make run-cli AUDIO=music.mp3 OUTPUT=video.mp4 PRESET=dev

# Export en 4K haute qualité
make run-cli AUDIO=music.mp3 OUTPUT=video.mp4 PRESET=4k
```

#### Toutes les options disponibles
```bash
# Syntaxe complète
make run-cli \
    AUDIO=chemin/vers/audio.mp3 \
    OUTPUT=chemin/vers/video.mp4 \
    PRESET=dev \
    EFFECT=tunnel \
    COLOR=rainbow \
    RESOLUTION=1080p \
    FPS=60
```

#### Options disponibles
- **PRESET** : dev, fast, normal, high, 4k
- **EFFECT** : bars, circles, particles, tunnel, wave, random
- **COLOR** : psychedelic, retro, dark, rainbow
- **RESOLUTION** : 720p, 1080p, 1440p, 4K
- **FPS** : 15, 20, 24, 30, 60, 120

### 🐳 Commandes Podman Directes

Si vous préférez utiliser Podman directement :

```bash
# Construire l'image
./podman-build.sh

# Lancer l'interface graphique
./podman-run.sh

# Lancer le menu CLI interactif
./podman-menu.sh

# Export vidéo direct
./podman-run-cli.sh /chemin/audio.mp3 /chemin/video.mp4 --preset dev
```

---

## 🎯 Workflows Typiques

### 1. Test rapide avec un fichier
```bash
# Copier un fichier dans ~/Music
cp ~/Téléchargements/ma_musique.mp3 ~/Music/

# Export ultra-rapide (quelques secondes)
make run-cli AUDIO=ma_musique.mp3 OUTPUT=test.mp4 PRESET=dev

# Regarder le résultat
xdg-open ~/Videos/test.mp4
```

### 2. Export haute qualité pour YouTube
```bash
make run-cli \
    AUDIO=mon_son.mp3 \
    OUTPUT=youtube_video.mp4 \
    PRESET=high \
    EFFECT=tunnel \
    COLOR=psychedelic
```

### 3. Batch processing (plusieurs fichiers)
```bash
# Pour tous les MP3 dans ~/Music
for audio in ~/Music/*.mp3; do
    output="~/Videos/$(basename "$audio" .mp3).mp4"
    make run-cli AUDIO="$audio" OUTPUT="$output" PRESET=fast
done
```

### 4. Prévisualisation avant export
```bash
# Lancer l'interface
make run
# Sélectionner fichier, effet, palette, présélection
# Cliquer sur "▶ Lecture" pour prévisualiser
# Cliquer sur "🎥 Exporter Vidéo" pour exporter
```

---

## 📂 Organisation des Fichiers

Par défaut, le conteneur monte :
- `~/Music` → `/audio` (fichiers audio, lecture seule)
- `~/Videos` → `/output` (vidéos exportées, écriture)
- `$(pwd)` → `/app` (code source, lecture seule)

Vous pouvez modifier ces chemins via des variables d'environnement :
```bash
AUDIO_DIR=/mon/dossier/musique OUTPUT_DIR=/mon/dossier/videos make run
```

---

## 🐛 Dépannage

### ❌ "Error: Podman not installed"
```bash
# Installer Podman
sudo dnf install podman  # Fedora
sudo apt install podman  # Ubuntu/Debian
```

### ❌ "Image psychedelic-visualizer:latest not found"
```bash
# Construire l'image
make build
```

### ❌ "Cannot connect to X server" / "X11 forwarding error"
```bash
# Autoriser X11
xhost +local:

# Vérifier que X11 est en cours d'exécution
echo $DISPLAY  # Doit retourner :0 ou :1

# Si ça ne marche toujours pas
xhost +  # Moins sécurisé mais fonctionne
```

### ❌ "Permission denied" pour le son
```bash
# Ajouter votre utilisateur au groupe audio
sudo usermod -aG audio $USER

# Redémarrer la session (déconnexion/reconnexion)

# Ou lancer en root (moins sécurisé)
sudo ./podman-run.sh
```

### ❌ "No such file or directory" pour /dev/snd
```bash
# Vérifier que le périphérique audio existe
ls -la /dev/snd/

# Si vous n'avez pas besoin du son dans l'aperçu, utilisez uniquement le mode CLI
# pour l'export
```

### ❌ "FFmpeg not found" dans le conteneur
```bash
# Reconstruire l'image (FFmpeg est installé dans le Dockerfile)
make rebuild
```

### ❌ L'export est très lent
```bash
# Utiliser un présélection plus rapide
make run-cli AUDIO=music.mp3 OUTPUT=video.mp4 PRESET=dev

# Ou réduire la résolution
make run-cli AUDIO=music.mp3 OUTPUT=video.mp4 PRESET=fast
```

---

## 🔧 Développement

### Structure du Projet
```
visualize/
├── Dockerfile                    # Définition du conteneur
├── docker-entrypoint.sh          # Point d'entrée du conteneur
├── podman-build.sh               # Script de build
├── podman-run.sh                 # Lancement avec GUI
├── podman-run-cli.sh             # Lancement en CLI
├── podman-menu.sh                # Menu CLI interactif
├── Makefile                     # Commandes simplifiées
├── main.py                      # Application principale
├── export_menu.py               # Menu CLI pour export
├── quality_presets.py           # Présélections qualité/vitesse
├── audio/
│   ├── __init__.py
│   ├── analyzer.py              # Analyse audio (FFT, volume, beats)
│   └── loader.py                # Chargement fichiers audio
├── effects/
│   ├── __init__.py
│   ├── base.py                  # Classe de base
│   ├── bars.py                  # Effet barres
│   ├── circles.py               # Effet cercles
│   ├── particles.py             # Effet particules
│   ├── tunnel.py                # Effet tunnel
│   ├── wave.py                  # Effet vagues
│   └── manager.py               # Gestionnaire d'effets
├── renderer/
│   ├── __init__.py
│   ├── pygame_renderer.py        # Rendu Pygame (temps réel)
│   └── cv2_renderer.py          # Rendu OpenCV (export)
├── recorder/
│   ├── __init__.py
│   └── video_recorder.py         # Export vidéo FFmpeg
├── ui/
│   ├── __init__.py
│   ├── main_window.py           # Fenêtre principale Tkinter
│   └── preview.py               # Composant d'aperçu
├── utils/
│   ├── __init__.py
│   ├── config.py                # Configuration
│   └── helpers.py               # Fonctions utilitaires
├── tests/                       # Tests automatiques
│   ├── __init__.py
│   ├── test_quality_presets.py
│   ├── test_audio.py
│   └── test_effects.py
└── README.md                    # Documentation
```

### Lancer les Tests
```bash
# Tous les tests
make test

# Tests spécifiques
make test-audio
make test-effects
```

### Ajouter un nouvel effet
1. Créer un nouveau fichier dans `effects/` (ex: `effects/mon_effet.py`)
2. Hériter de `BaseEffect`
3. Implémenter `render()` et `render_to_array()`
4. Ajouter l'effet dans `effects/manager.py`

Exemple minimal :
```python
# effects/mon_effet.py
from effects.base import BaseEffect

class MonEffet(BaseEffect):
    def render(self, surface):
        # Dessiner sur la surface Pygame
        pass
    
    def render_to_array(self):
        # Retourner un tableau numpy (H, W, 3)
        pass
```

---

## 📜 Licence

MIT - Libre d'utiliser, modifier et distribuer.

---

## 🤝 Contribution

Les contributions sont les bienvenues !

1. Forker le projet
2. Créer une branche (`git checkout -b feature/ma-fonctionnalité`)
3. Commiter vos changements (`git commit -m 'Ajout de ma fonctionnalité'`)
4. Pousser vers la branche (`git push origin feature/ma-fonctionnalité`)
5. Ouvrir une Pull Request

---

## 📞 Support

Pour les problèmes ou questions :
- Vérifiez d'abord la section [Dépannage](#-dépannage)
- Lancez `make test` pour vérifier que tout fonctionne
- Consultez les logs des conteneurs avec `podman logs <conteneur>`

---

## 🏷️ Tags

`visualisateur` `audio` `psychédélique` `winamp` `pygame` `opencv` `ffmpeg` `podman` `docker` `fedora` `python` `tkinter`
