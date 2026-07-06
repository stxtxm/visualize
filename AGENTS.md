# AGENTS.md — Mémoire Projet

**CE FICHIER DOIT ÊTRE LU PAR TOUT AGENT TRAVAILLANT SUR CE PROJET.**
*À mettre à jour après chaque modification significative de l'architecture, des dépendances ou des processus.*

---

## Vue d'ensemble

Application Python de visualisation audio psychédélique. Prend un fichier audio en entrée, l'analyse en temps réel (FFT, BPM, beats) et génère des animations synchronisées. Dispose d'une interface graphique Tkinter, d'un mode export vidéo, et peut être distribuée sous forme d'AppImage autonome.

---

## Architecture

### Flux principal

```
Fichier audio → AudioStreamReader (ffmpeg) → AudioAnalyzer (FFT/numpy)
  → EffectManager → BaseEffect.render() / render_to_array()
    → Pygame (GUI en temps réel) ou FFmpeg (export MP4)
```

### Points d'entrée

- `main.py` — CLI + GUI. Détecte automatiquement Tkinter ou Pygame fallback.
- `build_standalone.sh` — Build AppImage via conteneur Docker/Podman.

### Modes de fonctionnement

1. **GUI Tkinter** (par défaut) — Fenêtre avec sélection fichier, effets, palettes, aperçu temps réel, export.
2. **CLI Export** — `main.py audio.mp3 --export video.mp4` — Mode headless avec barre de progression.
3. **Pygame plein écran** — Fallback si Tkinter indisponible. Drag & drop de fichiers audio.
4. **AppImage** — Distribution autonome avec Python et toutes les dépendances embarquées.

---

## Effets visuels

Tous les effets héritent de `BaseEffect` (`effects/base.py`) et doivent implémenter :

| Méthode | Usage |
|---------|-------|
| `render(surface)` | Dessin Pygame (mode GUI temps réel) |
| `render_to_array() -> np.ndarray` | Retourne un tableau numpy (H, W, 3) pour l'export |

### Effets disponibles

| ID | Classe | Description |
|----|--------|-------------|
| `neon_equalizer` / `classic` | `ClassicEffect` | Oscilloscope circulaire + barres + rayons + grille |
| `psychedelic_plasma` / `plasma` | `PlasmaEffect` | Plasma algorithmique avec couleurs dynamiques |
| `3d_cyber_tunnel` / `tunnel` | `TunnelEffect` | Effet de tunnel 3D style cyberpunk |
| `bars` | `BarEffect` | Barres verticales type equalizer |
| `circles` | `CircleEffect` | Cercles concentriques réactifs |
| `particles` | `ParticleEffect` | Particules réagissant au beat |
| `wave` | `WaveEffect` | Vagues sinusoïdales |
| `spectrum` | `SpectrumEffect` | Spectre fréquences détaillé |
| `random` | — | Sélection aléatoire par `EffectManager` |

### Contraintes d'implémentation

- **`render_to_array()`** doit être implémentée SÉPARÉMENT de `render()`. L'export utilise `render_to_array()` via OpenCV (`cv2`). L'aperçu GUI utilise `render_to_array()` via `HeadlessRenderer`.
- Les tailles d'image sont dynamiques (définies par la résolution d'export ou la taille de la fenêtre). Utilisez `self.width` et `self.height`.
- Le scaling proportionnel : les effets doivent utiliser un facteur d'échelle `s = self.height / 450.0` pour s'adapter à n'importe quelle résolution.

### Palettes de couleurs

Définies dans `BaseEffect._get_color_palette()` :
- **`psychedelic`** — Magenta, Cyan, Jaune, Rouge, Vert, Bleu, Orange, Violet
- **`retro`** — Vert Winamp, Jaune, Bleu clair, Magenta, Cyan
- **`winamp_classic`** — 4 nuances de vert + 3 de jaune
- **`dark`** — Gris foncé, Bleu, Rouge, Vert, Jaune
- **`rainbow`** — Rouge → Orange → Jaune → Vert → Bleu → Indigo → Violet

---

## Analyse audio

### AudioAnalyzer (`audio/analyzer.py`)

- Utilise **numpy** pour la FFT (via `scipy.fft` ou `numpy.fft`)
- Bandes de fréquences : Sub-bass (20-250Hz), Bass (250-500Hz), Low-mids (500-2000Hz), High-mids (2000-4000Hz), Highs (4000-20000Hz)
- Détection de beat, calcul BPM, spectre complet
- Mode `NO_SOUND=1` pour tests sans audio réelle
- Utilise `AudioStreamReader` pour décoder l'audio via ffmpeg

### AudioStreamReader

- Lit l'audio via un pipe ffmpeg → `pcm_s16le`
- Nettrie `LD_LIBRARY_PATH` avant de lancer ffmpeg (évite les conflits avec les libs embarquées)
- Retourne des chunks numpy (ou listes en fallback sans numpy)

---

## Export vidéo

### quality_presets.py

- **Codecs H.264 détectés automatiquement** : `libopenh264` si disponible, sinon `libx264` avec `-preset`
- Présélections : `dev` (720p15), `fast` (720p20), `normal` (1080p30), `high` (1080p60), `4k` (4K30)
- `build_ffmpeg_cmd()` construit la commande ffmpeg complète
- Le flag `-preset` n'est ajouté QUE pour `libx264` (pas supporté par `libopenh264`)

### Pipelines de rendu pour l'export

```
main.py → AudioAnalyzer → EffectManager → render_to_array() → cv2.cvtColor(RGB2BGR)
  → process.stdin.write() → ffmpeg (rawvideo pipe) → output.mp4
```

---

## Interface graphique

### MainWindow (`ui/main_window.py`)

- Fenêtre Tkinter avec :
  - Sélection fichier audio (parcours ou glisser-déposer)
  - Menu déroulant résolution + présélection qualité
  - **Effet et palette ne sont PAS exposés dans la GUI** — valeur par défaut : `Neon Equalizer` + `winamp_classic`
  - Effet et palette sont configurables UNIQUEMENT via CLI (`--effect`, `--color`)
  - Boutons Lecture, Stop, Exporter
  - Aperçu vidéo temps réel (Label Tkinter avec PhotoImage)
  - Logs en bas (redirige stderr via `LogDisplay`)
- La boucle de lecture utilise `render_to_array()` via `HeadlessRenderer`
- L'aperçu est redimensionné avec `LANCZOS` quand la fenêtre change de taille
- Effet recréé dynamiquement si la taille de fenêtre change

### PreviewFrame (`ui/preview.py`)

- Bind `<Configure>` pour resize dynamique
- Plus de dimensions fixes — utilise `winfo_width()` / `winfo_height()`

---

## CI/CD Pipeline (`.github/workflows/release.yml`)

Déclenché sur push de tag `v*`.

1. **test** (ubuntu-24.04) : Install deps → génère test audio → pytest → test export
2. **build** (ubuntu-24.04) : squashfs-tools → `CONTAINER_CMD=docker bash build_standalone.sh` → upload artifact
3. **release** (ubuntu-24.04) : download artifact → création GitHub Release avec AppImage

### Contraintes CI

- `libopenh264` N'EST PAS disponible dans ffmpeg sur ubuntu-24.04 → fallback `libx264` automatique
- `pytest-timeout` n'est pas installé → ne pas utiliser `--timeout`
- Python 3.11 dans le cache GitHub (`actions/setup-python@v5`)

---

## Build AppImage

### `build_standalone.sh`

- Script bash qui construit l'AppImage complète
- Utilise `$CONTAINER_CMD` (docker ou podman, auto-détecté)
- Étapes :
  1. Build image Docker (`Dockerfile.appimage` — Debian slim + Python 3.11 + dépendances)
  2. Extraction des fichiers build (Python, libs, dépendances)
  3. Assemblage avec `create_appimage.py` (runtime ELF + squashfs)

### `Dockerfile.appimage`

- Base : `python:3.11-slim`
- Installe : SDL2, OpenGL, portaudio, ffmpeg avec libx264/libx265/libopenh264
- Les libs sont extraites de l'image et packagées dans l'AppDir

### `create_appimage.py`

- Assembleur AppImage Type 2 (format standard)
- Utilise `mksquashfs` pour créer le système de fichiers compressé
- Lit un runtime ELF et y attache le squashfs avec un offset aligné

---

## Tests

### Tests unitaires (pytest)

| Fichier | Description |
|---------|-------------|
| `test_audio.py` | Analyse audio : FFT, bandes, beats, initialisation |
| `test_effects.py` | 25 tests : rendu Pygame, rendu array, palettes, scaling |
| `test_paths.py` | PathManager : conteneur/hôte, chemins, fichiers |
| `test_quality_presets.py` | Présélections, build_ffmpeg_cmd, résolutions |

### Tests intégration

| Fichier | Description |
|---------|-------------|
| `test_export.py` | Lance `main.py --export`, vérifie la vidéo avec ffprobe |
| `test_e2e_simple.py` | Test bout-en-bout sans GUI (6 scénarios) |

### Contraintes de test

- `input/test.wav` généré par `scripts/gen_test_audio.py` (10s sine wave 220+440+880Hz)
- Tests Pygame : les effets sont testés avec une surface factice (pas de display)
- Tests analyse : utilisent `AudioAnalyzer` en mode `NO_SOUND` (données simulées)

---

## Contraintes et décisions architecturales

### 🔴 Critiques

1. **`render_to_array()` et `render()` sont DUPLIQUÉS** dans chaque effet. Les deux méthodes doivent produire le même rendu. Ne JAMAIS modifier l'une sans l'autre.
2. **OpenH264 ne supporte PAS `-preset`**. Le code détecte le codec disponible (`_check_openh264()`) et n'ajoute `-preset` que pour `libx264`.
3. **Pygame doit être initialisé APRÈS Tkinter** dans le thread principal pour la GUI. L'order est : `pygame.display.init()` → `pygame.time.init()` → Tkinter → boucle d'aperçu.
4. **`LD_LIBRARY_PATH` est nettoyé** avant de lancer ffmpeg dans `AudioStreamReader` pour éviter les conflits avec les libs de l'AppImage.
5. **Gestion de la version (`version.py`)** : La version de l'application est centralisée dans `version.py`. En dev, elle est lue dynamiquement via `git describe --tags --always`. Au build de l'AppImage (`build_standalone.sh`), le script écrit la version Git statique dans `output/usr/app/version.py` pour éviter d'avoir à modifier manuellement les fichiers.

### 🟡 Importantes

6. **Le scaling** utilise `s = height / 450.0`. Tous les dessins doivent être multipliés par `s`. La hauteur de référence 450px vient de la résolution historique 800×450.
7. **`HeadlessRenderer` n'a plus de cap** de résolution. L'effet est créé à la taille exacte de la fenêtre ou de l'export.
8. **L'aperçu GUI utilise `render_to_array()`** (comme l'export), pas `render()`. Changé pour garantir la correspondance visuelle.
9. **Les tags GitHub déclenchent la CI** via `on: push: tags: ['v*']`. Re-tagger avec `git tag -d vX.Y.Z && git push --delete origin vX.Y.Z && git tag vX.Y.Z && git push origin vX.Y.Z`.
10. **Permissions de build Docker (CI)** : Docker sur la CI tourne en root, rendant les fichiers de `output/` inaccessibles au user runner. `build_standalone.sh` applique donc un `chown -R $(id -u):$(id -g)` sur le dossier de sortie si Docker est détecté.

### 🟢 Recommandations

11. **Toujours lancer les tests** (`python3 -m pytest tests/ -v`) avant de commit.
12. **Mettre à jour AGENTS.md** après tout changement architectural, nouvelle dépendance, ou nouveau processus.
13. **Ajouter tout nouvel effet dans EFFECT_MAP** (`effects/manager.py`) ET dans les `choices` du argparse (`main.py`).

---

## Dépendances

### Python (requirements.txt)

| Package | Usage |
|---------|-------|
| `pydub` | Décodage audio (fallback) |
| `sounddevice` | Lecture audio temps réel |
| `pygame` | Rendu GUI et fallback plein écran |
| `opencv-python` | Rendu export (headless, conversion RGB→BGR) |
| `Pillow` | Conversion numpy → PhotoImage pour l'aperçu Tkinter |
| `numpy` | Analyse audio FFT, manipulation matrices |
| `scipy` | FFT (alternative numpy) |
| `pytest` | Tests |

### Système

| Dépendance | Usage |
|------------|-------|
| `ffmpeg` | Décodage audio + encodage vidéo export |
| `libsdl2-2.0-0` + libs | Pygame (rendu) |
| `portaudio19-dev` | Sounddevice (audio temps réel) |
| `python3-tk` | Interface graphique Tkinter |
| `docker` ou `podman` | Build AppImage |

---

## Quick Reference

```bash
# Lancer
python3 main.py                          # GUI
python3 main.py audio.mp3 -o video.mp4   # Export

# Tests
python3 -m pytest tests/ -v
python3 tests/test_export.py

# Build AppImage
bash build_standalone.sh

# CI/CD (après commit)
git tag v0.0.2 && git push origin v0.0.2

# Recréer un tag (si pipeline échoue)
git tag -d v0.0.2 && git push --delete origin v0.0.2
git tag v0.0.2 && git push origin v0.0.2
```
