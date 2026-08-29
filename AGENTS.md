# AGENTS.md — Mémoire Projet

**CE FICHIER DOIT ÊTRE LU PAR TOUT AGENT TRAVAILLANT SUR CE PROJET.**
*À mettre à jour après chaque modification significative de l'architecture, des dépendances ou des processus.*

---

## Vue d'ensemble

**Visualize** — Application Python de visualisation audio psychédélique. Prend un fichier audio en entrée, l'analyse en temps réel (FFT, BPM, beats) et génère des animations synchronisées. Dispose d'une interface graphique Tkinter, d'un mode export vidéo, et peut être distribuée sous forme d'AppImage autonome.

> **Rebrand (v0.3.1+)** : ancien nom « Visualisateur Psychédélique » / « Psychedelic Visualizer ». Artefacts renommés : `Visualize.AppImage`, `Visualize.AppDir`, `visualize.desktop`, `Visualize.exe` / `Visualize_portable` (Windows), image Docker `visualize-appimage`. La palette `psychedelic` et l'effet `psychedelic_plasma` conservent leurs IDs d'origine.

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
| `trance_scope` / `pro_trance` | `TranceScopeEffect` | Visualizer premium : fond image optionnel, bloom spectral, interférences, glyphes orbitaux et strobe BPM |
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

### Image de fond

- `BaseEffect` fournit `set_background_image()` et `_background_frame()` pour charger une image via Pillow, la recadrer à la résolution active et la rendre disponible en RGB numpy.
- `background_opacity` (0.0–1.0, défaut 0.72) contrôle le mélange image / couleur unie. Accessible via `set_background_opacity()`.
- `_background_frame()` utilise `self.background_opacity` si `opacity` n'est pas explicitement passé.
- Le chemin `background_image` est propagé par `EffectManager`, le CLI (`--background`) et `VideoRecorder`.
- `TranceScopeEffect` utilise l'image comme matière graphique beat-synced (gradation, dérive chromatique, glow) et elle est donc visible dans la preview comme dans l'export MP4.

### Logo superposé

- `effects/logo_overlay.py` fournit une couche RGBA commune aux tableaux numpy et aux surfaces Pygame.
- `EffectManager` applique le logo après le rendu de l'effet dans `render_to_array()` et `render()`, afin de garantir sa présence dans la preview et le mode plein écran.
- Le logo est propagé par le CLI (`--logo`, `--logo-position`, `--logo-x`, `--logo-y`, `--logo-scale`, `--logo-opacity`) et par `VideoRecorder`.
- Les positions nommées utilisent les neuf ancres écran; `custom` utilise X/Y en pourcentage de l'espace disponible après prise en compte de la taille du logo.
- L'onglet **Logo** de l'interface permet de choisir le fichier, l'ancre, les coordonnées, la taille et l'opacité. Les coordonnées sont normalisées dans le manager pour rester indépendantes de la résolution.

### Icône de l'application (branding)

- Source de vérité : `assets/icon.svg` — tuile sombre arrondie, bordure néon dégradée (cyan `#00f0ff` → violet `#7c4dff` → magenta `#ff3ddb`), 5 barres d'égaliseur formant un « V » (Visualize).
- `assets/icon.png` (256×256) : `magick -background none assets/icon.svg -resize 256x256 -depth 8 -strip assets/icon.png`. `assets/icon-48/64/128.png` : mêmes commandes avec `-resize 48/64/128`. `icon.svg` copié en `hicolor/scalable`.
- `assets/icon.ico` (16→256 px) : `magick -background none assets/icon.svg -define icon:auto-resize=256,128,64,48,32,24,16 assets/icon.ico`. Utilisé par PyInstaller (`build_windows.spec` → `icon=`) et NSIS (`installer.nsi` → `Icon`/`UninstallIcon`).
- AppImage : `build_standalone.sh` installe `hicolor/{48,64,128,256}/apps/visualize.png` + `scalable/apps/visualize.svg`, copie `visualize.png` à la racine AppDir **et** `.DirIcon` (requis `AppImageSpec`), `visualize.desktop` avec `StartupWMClass=Visualize`, `Version=1.0`, `X-AppImage-Version`.
- Intégrations runtime : `MainWindow._set_window_icon()` (`iconphoto`, candidats `_MEIPASS/assets` puis `<repo>/assets`) ; `pygame.display.set_icon()` dans `main.py` (fallback plein écran, `className='Visualize'`) et `renderer/pygame_renderer.py`.
- Après toute modification de `icon.svg`, régénérer `icon.png`, `icon-48/64/128.png` ET `icon.ico`.

---

## Analyse audio

### AudioAnalyzer (`audio/analyzer.py`)

- Utilise **numpy** pour la FFT (via `scipy.fft` ou `numpy.fft`)
- Bandes de fréquences : Sub-bass (20-250Hz), Bass (250-500Hz), Low-mids (500-2000Hz), High-mids (2000-4000Hz), Highs (4000-20000Hz)
- Détection de beat, calcul BPM, spectre complet
- Bandes visuelles logarithmiques `visual_bands` (32 bandes), `spectral_flux` et `onset_strength` pour les rendus modernes synchronisés aux transitoires
- Mode `NO_SOUND=1` pour tests sans audio réelle
- Utilise `AudioStreamReader` pour décoder l'audio via ffmpeg

### AudioStreamReader

- Lit l'audio via un pipe ffmpeg → `pcm_s16le`
- Nettrie `LD_LIBRARY_PATH` avant de lancer ffmpeg (évite les conflits avec les libs embarquées)
- Retourne des chunks numpy (ou listes en fallback sans numpy)

---

## Export vidéo

### quality_presets.py

- **Codecs vidéo configurables (`video_codec`)** :
  - **`h264`** (par défaut) : H.264 (NVENC > VAAPI > VideoToolbox > libopenh264 > libx264). Standard universel.
  - **`vp9`** : WebM / VP9 (`libvpx-vp9`) + Opus (`libopus`). **Royalty-free**, lisible immédiatement sur Fedora/Linux sans aucun codec propriétaire ou dépôt RPM Fusion.
  - **`h265`** : HEVC (`libx265`) pour une compression optimale.
- Présélections : `dev` (720p15), `fast` (720p20), `normal` (1080p30), `high` (1080p60), `4k` (4K30)
- `build_ffmpeg_cmd()` et `codec_for_output()` construisent les paramètres FFmpeg et ajustent automatiquement l'extension (`.webm` pour VP9, `.mp4` pour H.264/H.265).
- Supporte `render_width`/`render_height` : quand différent de la sortie, ajoute `-vf scale=W:H:flags=lanczos`

### Pipelines de rendu pour l'export

```
main.py → AudioAnalyzer → EffectManager → render_to_array() → RGB bytes (`rgb24`)
  → [queue.Queue maxsize=2] → writer thread → ffmpeg (rawvideo pipe) → output.mp4
```

- Le CLI et `VideoRecorder` utilisent `AudioFrameReader` en mode export : le fichier audio n'est plus entièrement décodé en mémoire.
- La taille du bloc d'analyse est calculée avec `ceil(44100 / fps)` et `AudioFrameReader` distribue précisément les échantillons fractionnaires afin qu'une image corresponde à la bonne durée audio et que les mixes longs restent synchronisés.
- `AudioFrameReader` lit l'audio en blocs d'une seconde dans un buffer interne, puis découpe exactement les fenêtres par frame; cela réduit fortement les appels pipe/FFmpeg sans modifier les échantillons analysés.
- Les WAV PCM 16-bit dont le taux d'échantillonnage correspond sont lus directement avec le module `wave`, y compris avec seek par segment; cela évite un décodeur FFmpeg par worker lors des exports 4K parallèles.
- Les exports appellent `AudioAnalyzer.set_stream_position(frame_index, frame_index / fps)` avant chaque analyse afin que `beat_phase` utilise l'horloge vidéo exacte, y compris pour les FPS à nombre d'échantillons fractionnaire.
- La durée d'export provient de `ffprobe` sur le fichier source, y compris lorsque `NO_SOUND=1` active l'analyse simulée.
- FFmpeg écrit d'abord dans `<output>.part.mp4`; le fichier final n'est remplacé qu'après une terminaison réussie et une validation minimale.
- **Padding de fin de piste** — Le générateur du `VideoRecorder` pade maintenant en silence jusqu'à `total_frames` (comme `run_export()` et `parallel_export`), y compris quand ffprobe surestime la durée PCM décodable (MP3 gapless/VBR) : plus aucun « audio ended N frame(s) early », la vidéo atteint toujours sa durée cible.
- **Validation avant publication** — `quality_presets.validate_export_output()` (ffprobe JSON) est appelée sur chaque `.part.*` juste avant `os.replace()` dans les trois chemins d'export : flux vidéo (+audio) requis, > 0 paquets vidéo, durée à ±max(0,35 s ; 6 frames). Un export invalide échoue au lieu d'être publié ; sans ffprobe, la validation se dégrade en simple notice.
- **Validation en environnement embarqué** — Le validateur passe systématiquement par `_ffmpeg_environment(ffprobe_path)` : un FFprobe embarqué reçoit son propre `usr/lib`, un FFprobe système est isolé d'un `LD_LIBRARY_PATH` résiduel (cas réel : modules nettoyant la variable pour PipeWire au sein de l'AppImage faisaient échouer le chargement de `libavdevice.so.61`, interprété à tort comme « fichier illisible »). Deux tentatives (stricte puis tolérante `-err_detect ignore_err`) sont essayées avant échec définitif.
- **Artefacts d'échec préservés** — Un export refusé par la validation ne détruit plus la pièce à conviction : `preserve_failed_partial()` renomme le `.part.*` en `<sortie>.rejected.<ext>` (remplace l'éventuel précédent) ; ceci s'applique aux trois chemins d'export.
- **VP9 stable** — Les flags explicites `-tile-columns/-tile-rows` ont été retirés des deux branches VP9 (`build_ffmpeg_cmd` et fallback sans H.264 logiciel) : ils déclenchaient des corruptions visuelles sur certaines builds libvpx ; le tiling automatique derrière `-row-mt 1` suffit.
- **VP9 en CRF pur (anti-flash)** — La branche VP9 utilise `-crf (24 en 4K) -b:v 0` (constant-quality) et le bloc générique `-b:v/-maxrate/-bufsize` n'est appliqué qu'aux encodeurs pilotés par débit (matériel, libopenh264). L'ancien mode contraint (`-b:v 20M -maxrate -bufsize`) étranglait la qualité sur les contenus riches en beats → « flashes » visibles en 4K. libx264/libx265 (CRF) sont également exempts de cap.
- **Fidélité audio** — Aucun filtre de loudness dynamique (`dynaudnorm` supprimé des trois chemins d'export) : seul `apad` (alignement durée) reste appliqué. Bitrates audio transparents : AAC 256k (MP4), Opus 224k (WebM).
- La GUI expose une échelle de rendu interne de 100 %, 75 % ou 50 % (100 % par défaut); FFmpeg upscale ensuite vers la résolution finale si une échelle réduite est choisie.
- `--render-workers` lance des segments 4K indépendants dans des processus séparés; chaque worker rejoue l'analyse et l'état de l'effet depuis le début sans rasteriser le préambule, puis encode uniquement sa plage. Cette continuité (et une graine aléatoire commune) évite les sauts de phase/particules aux jonctions. Les segments sont concaténés avec `-c:v copy`, sans remise à l'échelle ni ré-encodage vidéo final. Chaque FFmpeg de segment est limité à un thread d'encodage et de filtre pour éviter la multiplication des threads et des buffers internes du codec; VP9 utilise jusqu'à quatre threads par segment.
- Les capacités d'encodeur sont sondées une seule fois par export puis transmises aux workers `spawn`; VP9 et H.265 ne déclenchent aucun sondage H.264 inutile.
- L'AppImage utilise en priorité son FFmpeg embarqué, teste un encodeur matériel réellement utilisable puis retombe sur `libx264` logiciel (OpenH264 est réservé aux installations non-standalone). `VISUALIZE_4K_SAFE=1` active automatiquement le preset x264 `superfast` en 4K si aucun encodeur matériel n'est disponible, avec CRF 18 et une mémoire bornée. `recommended_render_workers()` limite le parallélisme selon les CPU et la RAM disponible.

### Progress de l'export

- **GUI** : barre 2px `#00f0ff` (`NEON_CYAN`) dans `status_frame` (`self._export_progress_bar`), visible via `_show_export_progress()` / cachée via `_export_finished()`.
- **CLI** : `print(f"\r  Export: {frame_count}/{total_frames} ({pct:.0f}%)", end="", flush=True)` dans `main.py` (tous les 10 frames).
- **Programmatique** : `VideoRecorder.record(progress_callback=callable(frame_count, total_frames))` — appelé à chaque frame.

---

## Interface graphique

### MainWindow (`ui/main_window.py`)

- Fenêtre Tkinter avec architecture à onglets (`TabPanel` + `ui/tabs/`) :
  - **Onglet Fichier** (`FileTab`) : sélection fichier audio (parcours), infos fichier (taille, durée)
  - **Onglet Effets** (`EffectsTab`) : effet + palette avec description dynamique
  - **Onglet Fond** (`BackgroundTab`) : image de fond + curseur opacité temps réel
  - **Onglet Logo** (`LogoTab`) : image superposée + position, coordonnées, taille et opacité
  - **Onglet Export** (`ExportTab`) : résolution, FPS, présélection, échelle de rendu, bouton export + barre progression intégrée
  - **Onglet Logs** (`LogsTab`) : logs colorés intégrés
- Boutons Lecture/Stop + curseur volume sous les onglets
- **4 thèmes** (`ui/theme.py`) : Cyberpunk, Synthwave, Matrix, Tokyo Night — sélecteur dans le header, persisté dans `~/.visualize_config.json`
- **Toasts** (`ui/toast.py`) : notifications overlay pour lecture/export/thème
- **HUD preview** : compteur FPS, timecode `00:00.000`, bordure néon animée
- **LED pulsante** dans la status bar pendant la lecture
- **Raccourcis** : Space/Ctrl+P (play), Ctrl+S/Esc (stop), Ctrl+E (export)
- **Navigation onglets** : `TabPanel` affiche les six onglets en grille 3×2 dans la sidebar pour éviter la compression horizontale.
- **États d'action** : Lecture et Export sont désactivés tant qu'aucun fichier audio valide n'est sélectionné; Stop est désactivé hors lecture.
- **Clic sur preview vide** → ouvre le dialog de sélection de fichier
- **Preview vide** : affiche une invitation explicite à sélectionner un fichier et utilise un curseur d'action.
- **Thèmes** : `MainWindow._apply_theme()` met à jour les widgets Tk, les contrôles ttk, le preview et les couleurs des boutons; les couleurs complémentaires sont définies dans `ui/theme.py`.
- Footer : `self._footer_copyright`, `self._footer_linkedin`, `self._footer_website`
- La boucle de lecture utilise `render_to_array()` via `HeadlessRenderer` (ou `ArrayRenderer` fallback)
- L'aperçu est redimensionné avec `LANCZOS` quand la fenêtre change de taille
- Effet recréé dynamiquement si la taille de fenêtre change

### PreviewFrame (`ui/preview.py`)

- `tk.Canvas` avec `update_image()` (PhotoImage) et `clear()`
- Bind `<Configure>` pour recentrer l'image
- Bind `<Button-1>` : si vide, déclenche `on_click_empty` callback (ouvre le dialog fichier)
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
 | `test_effects.py` | Base, palettes, render_to_array, render |
 | `test_effects_full.py` | Parametric tests: all effects × all palettes × sizes |
 | `test_player.py` | AudioPlayer backend detection, play_chunk, cleanup |
 | `test_bpm_detector.py` | BPM detection, beat on periodic signal, history |
 | `test_manager_full.py` | EffectManager instantiation, delegation, change |
 | `test_renderers.py` | ArrayRenderer, HeadlessRenderer, PygameRenderer |
 | `test_cli.py` | Argparse validation, CLI export invocation, progress output |
 | `test_error_handling.py` | NO_SOUND mode, corrupt audio, ffmpeg fallback |
 | `test_paths.py` | PathManager : conteneur/hôte, chemins, fichiers |
 | `test_quality_presets.py` | Présélections, build_ffmpeg_cmd, résolutions |
 | `test_ui.py` | Footer labels existence, copyright text, social link badges |
 | `test_logo.py` | Logo RGBA, position personnalisée et application par le manager |
 
 ### Tests intégration
 
 | Fichier | Description |
 |---------|-------------|
 | `test_export.py` | Lance `main.py --export`, vérifie la vidéo avec ffprobe, progress output, progress_callback ; fiabilisation export : buffers frais par effet (12 rendus), padding jusqu'à total_frames (sources tronquées), rejet/acceptation `validate_export_output` |
 | `test_e2e_simple.py` | Test bout-en-bout sans GUI (6 scénarios) |
 | `test_e2e_gui.py` | Tests d'intégration GUI (pygame renderer) |
 | `test_e2e_short_mp3_play_simple.py` | Tests simplifiés playback MP3 |
 
 ### Contraintes de test
 
 - `input/test.wav` généré par `scripts/gen_test_audio.py` (10s sine wave 220+440+880Hz)
 - Tests Pygame : les effets sont testés avec une surface factice (pas de display)
 - Tests analyse : utilisent `AudioAnalyzer` en mode `NO_SOUND` (données simulées)

---

## Contraintes et décisions architecturales

### 🔴 Critiques

1. **`render_to_array()` et `render()` sont DUPLIQUÉS** dans chaque effet. Les deux méthodes doivent produire le même rendu. Ne JAMAIS modifier l'une sans l'autre. **Propriété du buffer** : chaque appel à `render_to_array()` doit retourner de la mémoire fraîchement allouée pour la frame — les exports mettent les frames en file pour un thread FFmpeg asynchrone pendant que le rendu continue ; un buffer d'instance réutilisé produit des frames déchirées et des flashs noirs. Un garde-fou `FrameOwnershipGuard` (`utils/frame_guard.py`) copie défensivement toute adresse recyclée trop tôt dans les trois boucles d'export (`main.py`, `VideoRecorder.record()`, `parallel_export._render_segment()`).
2. **OpenH264 ne supporte PAS `-preset`**. Le code détecte le codec disponible (`_check_openh264()`) et n'ajoute `-preset` que pour `libx264`.
3. **ALSA underrun protégé** : `_start_sounddevice()` pré-remplit la queue avec 8 chunks silencieux AVANT de démarrer le stream, et le callback rejoue `_last_chunk_f32` sur underrun au lieu du silence. `blocksize = chunk_size * 8`, `queue.maxsize = 256`, `latency='high'`.
3. **Pygame doit être initialisé APRÈS Tkinter** dans le thread principal pour la GUI. L'order est : `pygame.display.init()` → `pygame.font.init()` → Tkinter → boucle d'aperçu. Note: `pygame.time.init()` n'existe plus dans pygame 2.x.
4. **`pygame.time.init()` n'existe plus dans pygame 2.x**. Utiliser `pygame.display.init()` + `pygame.font.init()` pour l'initialisation partielle, ou `pygame.init()` pour l'initialisation complète.
5. **`LD_LIBRARY_PATH` est nettoyé** avant de lancer ffmpeg dans `AudioStreamReader` pour éviter les conflits avec les libs de l'AppImage.
6. **Gestion de la version (`version.py`)** : La version de l'application est centralisée dans `version.py`. En dev, elle est lue dynamiquement via `git describe --tags --always`. Au build de l'AppImage (`build_standalone.sh`), le script écrit la version Git statique dans `output/usr/app/version.py` pour éviter d'avoir à modifier manuellement les fichiers.
7. **Images de fond** : toujours passer par `EffectManager.set_background_image()` ou le paramètre `background_image`; ne pas charger l'image directement dans la GUI ou l'export.

### 🟡 Importantes

8. **Le scaling** utilise `s = height / 450.0`. Tous les dessins doivent être multipliés par `s`. La hauteur de référence 450px vient de la résolution historique 800×450.
9. **`HeadlessRenderer` n'a plus de cap** de résolution. L'effet est créé à la taille exacte de la fenêtre ou de l'export.
10. **L'aperçu GUI utilise `render_to_array()`** (comme l'export), pas `render()`. Changé pour garantir la correspondance visuelle.
11. **Le logo est une couche finale** — l'aperçu et les exports directs passent par `EffectManager`; `VideoRecorder` applique également la couche aux générateurs de frames personnalisés.

### 🟡 Importantes

12. **Les tags GitHub déclenchent la CI** via `on: push: tags: ['v*']`. Re-tagger avec `git tag -d vX.Y.Z && git push --delete origin vX.Y.Z && git tag vX.Y.Z && git push origin vX.Y.Z`.
13. **Permissions de build Docker (CI)** : Docker sur la CI tourne en root, rendant les fichiers de `output/` inaccessibles au user runner. `build_standalone.sh` applique donc un `chown -R $(id -u):$(id -g)` sur le dossier de sortie si Docker est détecté.
14. **Références GUI stockées en instance** — Tout widget Tkinter qui doit être testé ou modifié depuis l'extérieur doit être stocké comme `self._nom_du_widget`. Actuellement : `self._footer_copyright`, `self._footer_linkedin`, `self._footer_website`, `self._export_progress_bar`, `self._status_bar_inner`.

### 🔵 Optimisations export (ajoutées v0.X)

19. **Encodage matériel auto-détecté** — `quality_presets._check_hardware_encoder()` vérifie chaque encodeur par un test réel (2x2 frame). Priorité : NVENC > VAAPI > VideoToolbox > libx264 > libopenh264. Le test réel évite les faux positifs (encodeur listé mais libcuda.so.1 manquant).
20. **Thread writer asynchrone** — `VideoRecorder.record()` utilise un thread + `queue.Queue(maxsize=2)` pour superposer le rendu des frames et l'écriture du pipe ffmpeg. Le thread principal pousse les bytes dans la queue, le writer thread écrit sur stdin. Le sentinel `_SENTINEL` signale l'arrêt. Deux frames limitent la mémoire occupée en 4K.
21. **Échelle de rendu** (CLI et GUI) — Rendu à résolution réduite, ffmpeg upscale avec lanczos. Ex: `--render-scale 0.5` sur export 4K → rendu 1080p, upscale 4K. Gain ~4x sur le rendu. Aucun impact quality pour du contenu abstrait.
22. **RGB direct vers FFmpeg** — Les pipes rawvideo sont déclarés `rgb24`; ne jamais convertir les arrays RGB des effets vers BGR (ni via OpenCV ni par vue), sinon les canaux rouge/bleu sont inversés et une copie inutile est créée.
23. **Exports longs bornés en mémoire** — Ne pas réintroduire `AudioAnalyzer(..., load_file=True)` dans un pipeline d'export; conserver le décodage audio par flux et fermer le lecteur dans le `finally`.
24. **Fichiers temporaires d'export** — Les sorties intermédiaires doivent conserver le suffixe du conteneur (`<output>.part.mp4` ou `<output>.part.webm`) pour permettre à FFmpeg de détecter le muxer; utiliser `os.replace()` après succès.
25. **Parallélisme 4K** — `recorder/parallel_export.py` rend des segments natifs dans des processus séparés et assemble la vidéo avec `-c:v copy`; l'audio est muxé ensuite avec les mêmes paramètres AAC que l'export séquentiel. Cette isolation contourne le GIL Python et protège le processus principal contre un arrêt d'encodeur.
26. **Mémoire FFmpeg 4K** — Les workers limitent `-threads`, `-filter_threads` et `-filter_complex_threads`; le mode standalone choisit `superfast` avec CRF 18 pour éviter l'accumulation de buffers x264 qui peut dépasser 1 Go par encodeur sur les longs flux rawvideo.
27. **Compatibilité AppImage** — `build_standalone.sh` sélectionne le FFmpeg embarqué, teste les encodeurs matériels disponibles et conserve `libx264` comme fallback universel; aucun GPU ni pilote propriétaire n'est requis. Le nombre de workers 1440p/4K est limité à quatre, puis ajusté selon `MemAvailable`; les résolutions 720p/1080p restent sur le pipeline séquentiel plus rapide afin d'éviter le coût de rejeu d'état.
28. **Gradation Trance Scope** — Sans image de fond, `_grade_background()` applique une version vectorisée équivalente par lignes en allouant le frame de sortie à chaque appel ; le chemin reste pixel-identique au calcul float32 général et n'a jamais réutilisé un buffer partagé entre frames.
29. **VP9 parallèle via Matroska** — Les exports VP9 passent désormais (comme H.264/H.265) par des segments parallèles : les segments intermédiaires sont encodés en `.mkv` (fiable pour le copy-concat, contrairement aux `.webm`) puis assemblés avec `-fflags +genpts` et muxés vers le `.webm` final. Les workers rejouent le préambule d'état sans produire de frames et partagent une graine aléatoire stable : les effets temporels et aléatoires restent continus aux frontières. Chaque segment VP9 reçoit un petit pool de threads d'encodage (`min(4, cpus // workers)`) car un libvpx mono-thread est extrêmement lent en haute résolution ; les segments x264/x265 restent à 1 thread d'encodage pour borner la mémoire. Un test d'intégration scanne chaque frame décodée pour détecter une régression de flash de frontière (`test_parallel_vp9_export_no_boundary_flash`).

### 🔴 CI + Release — English release message obligatoire

29. **`generate_release_notes: true`** dans `.github/workflows/release.yml` — La CI utilise `softprops/action-gh-release` avec l'option `generate_release_notes: true`. NE JAMAIS mettre de `body:` en dur dans la workflow : cela écrase le message de release à chaque push de tag.
30. **Éditer la release après la CI** — Dès que la CI a créé la release (auto-generated notes), vous devez immédiatement la modifier avec un message de release en anglais décrivant les changements. Utilisez `gh release edit vX.Y.Z --notes "..."` ou éditez-la sur GitHub directement.
31. **README et messages de release en anglais** — Le README.md et les `body` des GitHub Releases doivent être rédigés en anglais uniquement. Tout agent travaillant sur ce projet doit produire et maintenir ces contenus en anglais.
32. **AGENTS.md et fichiers internes** — Ce fichier (`AGENTS.md`) ainsi que `MARCHE_A_SUIVRE.md`, `NOUVEAUTES.md` et autres documents internes peuvent rester en français si nécessaire, car ils sont destinés aux développeurs du projet.
33. **Commits et PRs** — Les messages de commit et les titres/descriptions de Pull Requests doivent être en anglais.

### 🟢 Recommandations

34. **Toujours lancer les tests** (`python3 -m pytest tests/ -v`) avant de commit.
35. **Mettre à jour AGENTS.md** après tout changement architectural, nouvelle dépendance, ou nouveau processus.
36. **Ajouter tout nouvel effet dans EFFECT_MAP** (`effects/manager.py`) ET dans les `choices` du argparse (`main.py`).

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
python3 main.py audio.mp3 -o video.mp4 --background cover.png --effect trance_scope

# Ajouter un logo et le placer précisément (pourcentages)
python3 main.py audio.mp4 -o video.mp4 --logo logo.png --logo-position custom --logo-x 50 --logo-y 8

# Tests
python3 -m pytest tests/ -v
python3 tests/test_export.py

# Build AppImage
bash build_standalone.sh

# CI/CD (après commit)
git tag v0.X.Y && git push origin v0.X.Y

# Exporter avec --render-scale (0.25-1.0, défaut 1.0) pour rendu accéléré
# ex: rendu à 1080p → upscale 4K avec lanczos
python3 main.py audio.mp3 -o video.mp4 --render-scale 0.5

# 4K standalone-safe export: hardware probe + software fallback + CPU/RAM-aware workers
python3 main.py audio.mp3 -o video.mp4 --preset 4k --render-workers 0

# Ajouter les release notes en anglais après la CI
gh release edit v0.X.Y --notes "## What's new in v0.X.Y ..."

# Recréer un tag (si pipeline échoue)
git tag -d v0.X.Y && git push --delete origin v0.X.Y
git tag v0.X.Y && git push origin v0.X.Y
```
