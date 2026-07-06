# Visualisateur Psychédélique 🎨🎵

> Générateur d'animations psychédéliques synchronisées avec votre musique, inspiré de Winamp et Windows Media Player.

![CI](https://github.com/stxtxm/visualize/actions/workflows/release.yml/badge.svg)

---

## ✨ Fonctionnalités

- **8 effets visuels** : Neon Equalizer, Psychedelic Plasma, 3D Cyber Tunnel, Barres, Cercles, Particules, Vagues, Spectre
- **5 palettes de couleurs** : Psychédélique, Rétro, Winamp Classic, Sombre, Arc-en-ciel
- **Interface graphique Tkinter** avec aperçu en temps réel
- **Export vidéo MP4** (H.264 + AAC) : 720p, 1080p, 1440p, 4K
- **AppImage autonome** : zéro dépendance système, fonctionne sur toute distro Linux
- **Mode Pygame plein écran** (fallback si tkinter indisponible)

---

## 🚀 Utilisation (AppImage)

Téléchargez la dernière `Visualisateur_Psychedelic.AppImage` depuis les [Releases](https://github.com/stxtxm/visualize/releases).

```bash
chmod +x Visualisateur_Psychedelic.AppImage
./Visualisateur_Psychedelic.AppImage          # GUI
./Visualisateur_Psychedelic.AppImage audio.mp3 --export video.mp4  # Export CLI
```

### Options CLI

```bash
./Visualisateur_Psychedelic.AppImage \
    audio.mp3 \
    --export video.mp4 \
    --effect neon_equalizer \
    --color psychedelic \
    --preset normal \
    --resolution 1080p \
    --fps 30
```

| Option | Valeurs |
|--------|---------|
| `--effect` / `-e` | `neon_equalizer`, `psychedelic_plasma`, `3d_cyber_tunnel`, `bars`, `circles`, `particles`, `tunnel`, `wave`, `spectrum`, `plasma`, `classic`, `random` |
| `--color` / `-c` | `psychedelic`, `retro`, `winamp_classic`, `dark`, `rainbow` |
| `--preset` / `-p` | `dev`, `fast`, `normal`, `high`, `4k` |
| `--resolution` / `-r` | `720p`, `1080p`, `1440p`, `4K` |
| `--fps` | `15`, `20`, `24`, `30`, `60`, `120` |

---

## 📦 Présélections qualité/vitesse

| Présélection | Résolution | FPS | Bitrate | Usage |
|-------------|------------|-----|---------|-------|
| `dev` | 720p | 15 | 10M | Tests rapides |
| `fast` | 720p | 20 | 10M | Itérations fréquentes |
| `normal` | 1080p | 30 | 15M | Usage standard |
| `high` | 1080p | 60 | 20M | Haute qualité |
| `4k` | 4K | 30 | 50M | Qualité maximale |

---

## 📥 Installation (développement)

```bash
git clone https://github.com/stxtxm/visualize.git
cd visualize
pip install -r requirements.txt
sudo apt install ffmpeg libsdl2-2.0-0  # Ubuntu/Debian ; ou l'équivalent sur votre distro

# GUI
python3 main.py

# Export
python3 main.py audio.mp3 -o video.mp4 --preset normal
```

### Build AppImage

```bash
# Nécessite docker ou podman
bash build_standalone.sh
# Génère dist_standalone/Visualisateur_Psychedelic.AppImage
```

---

## 🔧 Développement

### Structure du projet

```
visualize/
├── main.py                      # Point d'entrée (CLI + GUI)
├── quality_presets.py           # Présélections qualité export
├── build_standalone.sh          # Build AppImage (Docker/Podman)
├── Dockerfile.appimage          # Image de build pour l'AppImage
├── create_appimage.py           # Assembleur AppImage Type 2
├── AGENTS.md                    # Contexte projet pour IA
├── scripts/
│   └── gen_test_audio.py        # Génère un WAV de test pour CI
├── audio/
│   ├── analyzer.py              # Analyse FFT, volume, beats, BPM
│   ├── player.py                # Lecture audio temps réel
│   └── loader.py                # Chargement fichiers audio
├── effects/
│   ├── base.py                  # Classe abstraite + palettes
│   ├── manager.py               # Sélection/instantiation effets
│   ├── bars.py                  # Barres equalizer
│   ├── circles.py               # Cercles concentriques
│   ├── classic.py               # Oscilloscope circulaire
│   ├── particles.py             # Particules réactives
│   ├── plasma.py                # Plasma algorithmique
│   ├── spectrum.py              # Spectre fréquences
│   ├── tunnel.py                # Tunnel 3D
│   └── wave.py                  # Vagues sinusoïdales
├── renderer/
│   ├── pygame_renderer.py       # Rendu Pygame (GUI)
│   ├── headless_renderer.py     # Rendu sans fenêtre (export)
│   ├── array_renderer.py        # Conversion numpy array
│   └── cv2_renderer.py          # Rendu OpenCV
├── recorder/
│   └── video_recorder.py        # Encapsuleur FFmpeg
├── ui/
│   ├── main_window.py           # Fenêtre principale Tkinter
│   ├── preview.py               # Aperçu vidéo temps réel
│   └── log_display.py           # Logs dans l'interface
├── utils/
│   └── paths.py                 # Gestionnaire de chemins (PathManager, hôte/conteneur)
├── tests/
│   ├── test_audio.py            # Tests analyse audio
│   ├── test_effects.py          # Tests effets visuels
│   ├── test_paths.py            # Tests PathManager
│   ├── test_quality_presets.py  # Tests présélections
│   ├── test_export.py           # Test export CI (génère vidéo)
│   ├── test_e2e_simple.py       # Tests end-to-end simplifiés
│   └── ...
└── .github/workflows/
    └── release.yml              # CI/CD : test → build → release
```

### Tests

```bash
python3 -m pytest tests/ -v
python3 tests/test_export.py            # Test export complet (génère une vidéo)
```

### Ajouter un effet

1. Créer `effects/mon_effet.py` avec une classe héritant de `BaseEffect`
2. Implémenter `render(surface)` (pygame) et `render_to_array() -> np.ndarray`
3. Enregistrer dans `EFFECT_MAP` dans `effects/manager.py`
4. Ajouter l'option dans le `choices` du argparse dans `main.py`

---

## 🐛 Dépannage

| Problème | Solution |
|----------|----------|
| `libopenh264` non trouvé | `sudo apt install ffmpeg` ou le build utilise `libx264` automatiquement |
| `tkinter` non trouvé | `sudo apt install python3-tk` ; ou utilisez `--no-gui` |
| AppImage ne se lance pas | `./Visualisateur_Psychedelic.AppImage --help` ; vérifiez `ldd` |
| Export lent | Utilisez `--preset dev` pour les tests, `--preset fast` pour production rapide |

---

## 🤝 Contribution

1. Lire [AGENTS.md](AGENTS.md) pour comprendre le contexte du projet
2. `git checkout -b feature/ma-fonctionnalité`
3. Commiter + push
4. Ouvrir une Pull Request

---

## 📜 Licence

MIT
