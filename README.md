# Visualize 🎨🎵

> Generate high-quality Winamp/Media Player-style visualizations synced to your music.

![CI](https://github.com/stxtxm/visualize/actions/workflows/release.yml/badge.svg)

---

## ✨ Features

- **Trance Scope visualizer** with a BPM-synced spectral bloom, interference threads, orbital glyphs, glow, and beat strobe
- **Optional image background** visible instantly in the preview and embedded in MP4 exports
- **Logo overlay** with nine anchor presets or fully custom X/Y placement, size, and opacity
- **Additional effects**: Neon Equalizer, Psychedelic Plasma, 3D Cyber Tunnel, Particles, Wave, Spectrum
- **5 color palettes**: Psychedelic, Retro, Winamp Classic, Dark, Rainbow
- **Tkinter GUI** with real-time preview, effect/palette controls, background image selection, and export settings
- **Modern responsive controls** with a two-row navigation grid, clear empty-preview call-to-action, live state indicators, and theme-aware widgets
- **Tabbed sidebar interface** : File, Effects, Background, Logo, Export, and Logs tabs for an organized, ergonomic workflow
- **4 selectable themes** : Cyberpunk, Synthwave, Matrix, Tokyo Night (persisted between sessions)
- **Live preview HUD** : FPS counter, playback timecode, and animated neon border
- **Toast notifications** for playback, export, and theme changes
- **Click-to-select** : click the empty preview to open the file picker
- **Keyboard shortcuts** : Space/Ctrl+P play, Ctrl+S/Esc stop, Ctrl+E export
- **MP4 video export** (H.264 + AAC) : 720p, 1080p, 1440p, 4K
- **Reliable parallel 4K and VP9/WebM export**: workers preserve temporal effect state at segment joins; VP9 uses constant-quality encoding and Matroska intermediates to avoid black flashes
- **Faithful audio export**: source loudness is left untouched; AAC is encoded at 256 kbps and Opus at 224 kbps
- **Standalone AppImage** : zero system dependencies, works on any Linux distro
- **Pygame fullscreen mode** with drag-and-drop (fallback when tkinter is unavailable)

---

## 🚀 Usage (AppImage)

Download the latest `Visualize.AppImage` from the [Releases](https://github.com/stxtxm/visualize/releases) page.

```bash
chmod +x Visualize.AppImage
./Visualize.AppImage                  # GUI (default)
./Visualize.AppImage audio.mp3 -o video.mp4  # CLI export
```

### GUI Mode (default)

The GUI offers a streamlined interface :
1. Select an audio file
2. Choose an effect, palette, optional background image, logo placement, export resolution, quality preset, and internal render scale
3. Press play to preview the visualizer in real time
4. Export the same visual stack to MP4

> The visualizer defaults to **Trance Scope** with the **Psychedelic** palette for a modern, BPM-reactive look. The classic Winamp-inspired visualizer remains available as **Neon Equalizer**.

### CLI Export

```bash
./Visualize.AppImage audio.mp3 -o video.mp4 --preset normal
./Visualize.AppImage audio.mp3 -o video.mp4 --effect spectrum --color rainbow --preset 4k
./Visualize.AppImage audio.mp3 -o video.mp4 --effect trance_scope --background cover.png
./Visualize.AppImage audio.mp3 -o video.mp4 --logo logo.png --logo-position custom --logo-x 50 --logo-y 8 --logo-scale 18
# Faster 4K export: safe worker count is selected automatically; no GPU is required
./Visualize.AppImage audio.mp3 -o video.mp4 --preset 4k --render-workers 0
```

| Option | Values |
|--------|--------|
| `--effect` / `-e` | `trance_scope`, `pro_trance`, `neon_equalizer`, `classic`, `psychedelic_plasma`, `3d_cyber_tunnel`, `bars`, `circles`, `particles`, `wave`, `spectrum`, `random` |
| `--color` / `-c` | `psychedelic`, `retro`, `winamp_classic`, `dark`, `rainbow` |
| `--background` / `-b` | Optional image path (`.png`, `.jpg`, `.webp`, `.bmp`, etc.) |
| `--logo` | Optional foreground logo image |
| `--logo-position` | `top-left`, `top-center`, `top-right`, `center-left`, `center`, `center-right`, `bottom-left`, `bottom-center`, `bottom-right`, or `custom` |
| `--logo-x`, `--logo-y` | Custom logo position as percentages of the available frame area |
| `--logo-scale` | Logo width as a percentage of video width (default `18`) |
| `--logo-opacity` | Logo opacity percentage (default `100`) |
| `--preset` / `-p` | `dev`, `fast`, `normal`, `high`, `4k` |
| `--resolution` / `-r` | `720p`, `1080p`, `1440p`, `4K` |
| `--fps` | `15`, `20`, `24`, `30`, `60`, `120` |
| `--render-scale` | Internal render scale from `0.1` to `1.0`; lower values speed up long exports but reduce detail (50% renders 1080p before 4K upscaling) |
| `--render-workers` | Parallel process workers; `0` auto-selects a CPU/RAM-safe count for 4K, `1` disables segmentation. Workers replay effect state without rasterizing it, so joins remain seamless. |

---

## 📦 Quality Presets

| Preset | Resolution | FPS | Nominal rate / CRF | Usage |
|--------|------------|-----|---------|-------|
| `dev` | 720p | 15 | 8M / CRF 28 | Quick tests |
| `fast` | 720p | 20 | 8M / CRF 23 | Fast iteration |
| `normal` | 1080p | 30 | 15M | Standard quality |
| `high` | 1080p | 60 | 20M | High quality |
| `4k` | 4K | 30 | CRF 18 (H.264), CRF 24 (VP9); 20M only where an encoder requires a cap | Maximum quality |

### Export quality and reliability

- VP9 uses pure CRF mode (`-b:v 0`) rather than a bitrate ceiling, preventing quality pumping on high-energy frames.
- Parallel VP9 exports use Matroska segment files and regenerated timestamps before the final WebM mux, avoiding decoder glitches at joins.
- Dynamic loudness normalization is intentionally disabled: the exported mix retains the source's level and dynamics. Audio is encoded as AAC 256 kbps in MP4 or Opus 224 kbps in WebM.

---

## 📥 Development Setup

```bash
git clone https://github.com/stxtxm/visualize.git
cd visualize
pip install -r requirements.txt
sudo apt install ffmpeg libsdl2-2.0-0  # Ubuntu/Debian or equivalent

# GUI
python3 main.py

# Export
python3 main.py audio.mp3 -o video.mp4 --preset normal
```

### Build AppImage

```bash
# Requires docker or podman
bash build_standalone.sh
# Generates dist_standalone/Visualize.AppImage
```

---

## 🔧 Development

### Project Structure

```
visualize/
├── main.py                      # Entry point (CLI + GUI)
├── quality_presets.py           # Export quality presets
├── build_standalone.sh          # AppImage build script (Docker/Podman)
├── Dockerfile.appimage          # Build image for AppImage
├── create_appimage.py           # Type 2 AppImage assembler
├── AGENTS.md                    # Project context for AI agents
├── version.py                   # Dynamic version manager
├── audio/
│   ├── analyzer.py              # FFT analysis, volume, beats, BPM
│   ├── player.py                # Real-time audio playback
│   └── loader.py                # Audio file loading
├── effects/
│   ├── base.py                  # Abstract base class + palettes
│   ├── manager.py               # Effect selection/instantiation
│   ├── trance_scope.py          # Modern BPM-synced trance visualizer
│   ├── classic.py               # Circular oscilloscope (Winamp-style)
│   ├── plasma.py                # Algorithmic plasma
│   ├── tunnel.py                # 3D cyber tunnel
│   ├── bars.py                  # Equalizer bars
│   ├── circles.py               # Concentric circles
│   ├── particles.py             # Beat-reactive particles
│   ├── wave.py                  # Sinusoidal waves
│   └── spectrum.py              # Frequency spectrum
├── renderer/
│   ├── headless_renderer.py     # Headless rendering (export + preview)
│   ├── pygame_renderer.py       # Pygame rendering (fullscreen)
│   ├── array_renderer.py        # NumPy array conversion
│   └── cv2_renderer.py          # OpenCV rendering
├── recorder/
│   └── video_recorder.py        # FFmpeg wrapper
├── ui/
│   ├── main_window.py           # Main Tkinter window
│   ├── preview.py               # Real-time video preview
│   └── log_display.py           # In-app log display
├── utils/
│   └── paths.py                 # Path manager (host/container)
├── scripts/
│   ├── gen_test_audio.py        # Generate test wave file
│   └── render_preview.py        # Generate rendering previews
├── tests/
│   ├── test_audio.py            # Audio analysis tests
│   ├── test_effects.py          # Visual effects tests
│   ├── test_paths.py            # PathManager tests
│   ├── test_quality_presets.py  # Preset tests
│   ├── test_export.py           # CI export test (generates video)
│   ├── test_e2e_simple.py       # Simplified end-to-end tests
│   └── ...
└── .github/workflows/
    └── release.yml              # CI/CD : test → build → release
```

### Testing

```bash
python3 -m pytest tests/ -v
python3 tests/test_export.py            # Full export test (generates video)
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `libopenh264` not found | Falls back to `libx264` automatically |
| `tkinter` not found | `sudo apt install python3-tk` ; or use `--no-gui` |
| AppImage won't run | `./Visualize.AppImage --help` |
| Slow 4K export or a long mix | Use `--preset 4k --render-workers 0`; this keeps native 4K output, uses isolated renderer processes, replays state without pre-rendering frames, bounds FFmpeg memory, and assembles segments without a final video re-encode |

---

## 🤝 Contributing

1. Read [AGENTS.md](AGENTS.md) to understand the project context
2. `git checkout -b feature/your-feature`
3. Commit + push
4. Open a Pull Request

---

## 📜 License

MIT
