# Psychedelic Visualizer 🎨🎵

> Generate psychedelic animations synced to your music, inspired by Winamp and Windows Media Player.

![CI](https://github.com/stxtxm/visualize/actions/workflows/release.yml/badge.svg)

---

## ✨ Features

- **8 visual effects** : Neon Equalizer, Psychedelic Plasma, 3D Cyber Tunnel, Bars, Circles, Particles, Wave, Spectrum
- **5 color palettes** : Psychedelic, Retro, Winamp Classic, Dark, Rainbow
- **Tkinter GUI** with real-time preview
- **MP4 video export** (H.264 + AAC) : 720p, 1080p, 1440p, 4K
- **Standalone AppImage** : zero system dependencies, works on any Linux distro
- **Pygame fullscreen mode** (fallback when tkinter is unavailable)

---

## 🚀 Usage (AppImage)

Download the latest `Visualisateur_Psychedelic.AppImage` from the [Releases](https://github.com/stxtxm/visualize/releases) page.

```bash
chmod +x Visualisateur_Psychedelic.AppImage
./Visualisateur_Psychedelic.AppImage          # GUI
./Visualisateur_Psychedelic.AppImage audio.mp3 --export video.mp4  # CLI export
```

### CLI Options

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

| Option | Values |
|--------|--------|
| `--effect` / `-e` | `neon_equalizer`, `psychedelic_plasma`, `3d_cyber_tunnel`, `bars`, `circles`, `particles`, `tunnel`, `wave`, `spectrum`, `plasma`, `classic`, `random` |
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
sudo apt install ffmpeg libsdl2-2.0-0  # Ubuntu/Debian or equivalent on your distro

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
├── scripts/
│   └── gen_test_audio.py        # Generate test WAV for CI
├── audio/
│   ├── analyzer.py              # FFT analysis, volume, beats, BPM
│   ├── player.py                # Real-time audio playback
│   └── loader.py                # Audio file loading
├── effects/
│   ├── base.py                  # Abstract base class + palettes
│   ├── manager.py               # Effect selection/instantiation
│   ├── bars.py                  # Equalizer bars
│   ├── circles.py               # Concentric circles
│   ├── classic.py               # Circular oscilloscope
│   ├── particles.py             # Beat-reactive particles
│   ├── plasma.py                # Algorithmic plasma
│   ├── spectrum.py              # Frequency spectrum
│   ├── tunnel.py                # 3D cyber tunnel
│   └── wave.py                  # Sinusoidal waves
├── renderer/
│   ├── pygame_renderer.py       # Pygame rendering (GUI)
│   ├── headless_renderer.py     # Headless rendering (export)
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

### Adding an Effect

1. Create `effects/my_effect.py` with a class inheriting from `BaseEffect`
2. Implement `render(surface)` (pygame) and `render_to_array() -> np.ndarray`
3. Register in `EFFECT_MAP` in `effects/manager.py`
4. Add to `choices` in the argparse in `main.py`

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `libopenh264` not found | `sudo apt install ffmpeg` or the build falls back to `libx264` automatically |
| `tkinter` not found | `sudo apt install python3-tk` ; or use `--no-gui` |
| AppImage won't run | `./Visualisateur_Psychedelic.AppImage --help` ; check `ldd` |
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
