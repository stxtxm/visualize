# Psychedelic Visualizer 🎨🎵

> Generate high-quality Winamp/Media Player-style visualizations synced to your music.

![CI](https://github.com/stxtxm/visualize/actions/workflows/release.yml/badge.svg)

---

## ✨ Features

- **Winamp/Media Player-style visualizer** with circular oscilloscope, equalizer bars, star rays, and grid
- **Additional effects** via CLI : Psychedelic Plasma, 3D Cyber Tunnel, Particles, Wave, Spectrum
- **5 color palettes** via CLI : Psychedelic, Retro, Winamp Classic, Dark, Rainbow
- **Tkinter GUI** with real-time preview (simplified controls : file + export quality only)
- **MP4 video export** (H.264 + AAC) : 720p, 1080p, 1440p, 4K
- **Standalone AppImage** : zero system dependencies, works on any Linux distro
- **Pygame fullscreen mode** with drag-and-drop (fallback when tkinter is unavailable)

---

## 🚀 Usage (AppImage)

Download the latest `Visualisateur_Psychedelic.AppImage` from the [Releases](https://github.com/stxtxm/visualize/releases) page.

```bash
chmod +x Visualisateur_Psychedelic.AppImage
./Visualisateur_Psychedelic.AppImage                  # GUI (default)
./Visualisateur_Psychedelic.AppImage audio.mp3 -o video.mp4  # CLI export
```

### GUI Mode (default)

The GUI offers a streamlined interface :
1. Select an audio file
2. Choose export resolution (1080p, 1440p, 4K) and quality preset
3. Press play to preview the visualizer in real-time
4. Export to MP4

> The visualizer defaults to the **Neon Equalizer** effect with the **Winamp Classic** color palette for an authentic retro feel. For advanced options (different effects, color palettes), use the CLI.

### CLI Export

```bash
./Visualisateur_Psychedelic.AppImage audio.mp3 -o video.mp4 --preset normal
./Visualisateur_Psychedelic.AppImage audio.mp3 -o video.mp4 --effect spectrum --color rainbow --preset 4k
```

| Option | Values |
|--------|--------|
| `--effect` / `-e` | `neon_equalizer`, `psychedelic_plasma`, `3d_cyber_tunnel`, `bars`, `circles`, `particles`, `wave`, `spectrum`, `random` |
| `--color` / `-c` | `psychedelic`, `retro`, `winamp_classic`, `dark`, `rainbow` |
| `--preset` / `-p` | `dev`, `fast`, `normal`, `high`, `4k` |
| `--resolution` / `-r` | `720p`, `1080p`, `1440p`, `4K` |
| `--fps` | `15`, `20`, `24`, `30`, `60`, `120` |

---

## 📦 Quality Presets

| Preset | Resolution | FPS | Bitrate | Usage |
|--------|------------|-----|---------|-------|
| `dev` | 720p | 15 | 10M | Quick tests |
| `fast` | 720p | 20 | 10M | Fast iteration |
| `normal` | 1080p | 30 | 15M | Standard quality |
| `high` | 1080p | 60 | 20M | High quality |
| `4k` | 4K | 30 | 50M | Maximum quality |

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
# Generates dist_standalone/Visualisateur_Psychedelic.AppImage
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
├── audio/
│   ├── analyzer.py              # FFT analysis, volume, beats, BPM
│   ├── player.py                # Real-time audio playback
│   └── loader.py                # Audio file loading
├── effects/
│   ├── base.py                  # Abstract base class + palettes
│   ├── manager.py               # Effect selection/instantiation
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
| AppImage won't run | `./Visualisateur_Psychedelic.AppImage --help` |
| Slow export | Use `--preset dev` for tests, `--preset fast` for quick production |

---

## 🤝 Contributing

1. Read [AGENTS.md](AGENTS.md) to understand the project context
2. `git checkout -b feature/your-feature`
3. Commit + push
4. Open a Pull Request

---

## 📜 License

MIT
