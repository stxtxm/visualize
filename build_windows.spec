# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Visualisateur Psychédélique Windows build.

Usage:
    python -m PyInstaller build_windows.spec

This bundles the app + ffmpeg into a single portable EXE directory
or a one-file EXE.
"""

import os
import sys

BLOCK_CIPHER_KEY = None

# ── Paths ──────────────────────────────────────────────────────────
# SPECPATH is defined by PyInstaller when loading the spec file
ROOT = os.path.abspath(SPECPATH) if 'SPECPATH' in dir() else os.getcwd()
FFMPEG_DIR = os.path.join(ROOT, "ffmpeg_bin")

# ── Collect all effect plugins ─────────────────────────────────────
HIDDEN_IMPORTS = [
    "audio",
    "audio.analyzer",
    "audio.player",
    "audio.bpm_detector",
    "effects",
    "effects.base",
    "effects.manager",
    "effects.classic",
    "effects.trance_scope",
    "effects.plasma",
    "effects.tunnel",
    "effects.bars",
    "effects.circles",
    "effects.particles",
    "effects.wave",
    "effects.spectrum",
    "effects.logo_overlay",
    "recorder",
    "recorder.video_recorder",
    "quality_presets",
    "renderer",
    "renderer.headless_renderer",
    "renderer.array_renderer",
    "renderer.pygame_renderer",
    "ui",
    "ui.main_window",
    "ui.theme",
    "ui.toast",
    "ui.preview",
    "ui.tab_panel",
    "ui.tabs",
    "ui.tabs.file_tab",
    "ui.tabs.effects_tab",
    "ui.tabs.background_tab",
    "ui.tabs.logo_tab",
    "ui.tabs.export_tab",
    "ui.tabs.logs_tab",
    "ui.log_display",
    "utils.paths",
    "version",
]

# Detect ffmpeg binaries for bundling
ffmpeg_binaries = []
if os.path.isdir(FFMPEG_DIR):
    for exe in ("ffmpeg.exe", "ffprobe.exe", "ffplay.exe"):
        p = os.path.join(FFMPEG_DIR, exe)
        if os.path.exists(p):
            ffmpeg_binaries.append((p, "."))
else:
    print("WARNING: ffmpeg_bin directory not found. Build --onedir cannot bundle ffmpeg.", file=sys.stderr)

a = Analysis(
    ["main.py"],
    pathex=[str(ROOT)],
    binaries=ffmpeg_binaries,
    datas=[
        # Include input directory if it exists
        *([(os.path.join(ROOT, "input"), "input")] if os.path.exists(os.path.join(ROOT, "input")) else []),
    ],
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter.test",
        "unittest",
        "pytest",
        "test",
    ],
    noarchive=False,
    module_collection_mode={
        "numpy": "pyz",
        "cv2": "pyz",
        "PIL": "pyz",
        "pygame": "pyz",
        "sounddevice": "pyz",
        "scipy": "pyz",
    },
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Visualisateur_Psychedelique",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

# Also create the one-folder variant with all files
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Visualisateur_Psychedelique_portable",
)
