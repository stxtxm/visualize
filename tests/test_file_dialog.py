#!/usr/bin/env python3
"""
Tests for the custom FileDialog (open/save).

These tests require a Tk display. They are skipped automatically on headless
CI runners (no DISPLAY / Tk unavailable) so the suite stays green there, but
they run on a real desktop (e.g. the user's Fedora machine).
"""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    tk = __import__("tkinter", fromlist=["Tk"])
except Exception as e:  # pragma: no cover - depends on environment
    pytest.skip(f"tkinter indisponible : {e}", allow_module_level=True)


def _make_root():
    try:
        root = tk.Tk()
        root.withdraw()
        return root
    except Exception as e:  # pragma: no cover - depends on environment
        pytest.skip(f"Tk non disponible (pas de display) : {e}")


def _temp_files():
    d = tempfile.mkdtemp()
    for name in ("song.mp3", "track.wav", "note.txt", "image.png"):
        with open(os.path.join(d, name), "w") as f:
            f.write("x")
    sub = os.path.join(d, "subdir")
    os.makedirs(sub)
    return d


def test_save_appends_default_extension():
    root = _make_root()
    dlg = __import__("ui.file_dialog", fromlist=["FileDialog"]).FileDialog(
        root, mode="save", title="t", initial_dir=tempfile.gettempdir(),
        filetypes=[("Fichiers MP4", "*.mp4")], defaultextension=".mp4"
    )
    dlg.entry_name.insert(0, "ma_video")
    dlg._on_confirm()
    assert dlg._result.endswith(".mp4")
    assert os.path.basename(dlg._result) == "ma_video.mp4"
    dlg.destroy()
    root.destroy()


def test_open_filters_by_filetype():
    root = _make_root()
    d = _temp_files()
    dlg = __import__("ui.file_dialog", fromlist=["FileDialog"]).FileDialog(
        root, mode="open", title="t", initial_dir=d,
        filetypes=[("Fichiers audio", "*.mp3 *.wav"), ("Tous les fichiers", "*.*")]
    )
    labels = list(dlg.listbox.get(0, tk.END))
    # subdir first, then audio files only (txt/png excluded by active filter)
    assert any("subdir" in l for l in labels)
    assert any("song.mp3" in l for l in labels)
    assert not any("note.txt" in l for l in labels)
    assert not any("image.png" in l for l in labels)
    dlg.destroy()
    root.destroy()


def test_navigation_up_and_home():
    root = _make_root()
    home = os.path.expanduser("~")
    child = tempfile.mkdtemp(dir=home) if os.access(home, os.W_OK) else tempfile.mkdtemp()
    dlg = __import__("ui.file_dialog", fromlist=["FileDialog"]).FileDialog(
        root, mode="open", title="t", initial_dir=child,
        filetypes=[("Tous les fichiers", "*.*")]
    )
    dlg._go_up()
    assert dlg._current_dir == os.path.dirname(child) or dlg._current_dir == child
    dlg._go_home()
    assert dlg._current_dir == home
    dlg.destroy()
    root.destroy()


def test_cancel_returns_empty():
    root = _make_root()
    dlg = __import__("ui.file_dialog", fromlist=["FileDialog"]).FileDialog(
        root, mode="open", title="t", initial_dir=tempfile.gettempdir(),
        filetypes=[("Tous les fichiers", "*.*")]
    )
    dlg._on_cancel()
    assert dlg._result == ""
    root.destroy()


def test_show_falls_back_to_home_on_invalid_dir():
    root = _make_root()
    fake_dir = "/this_path_should_not_exist_12345"
    fd = __import__("ui.file_dialog", fromlist=["FileDialog"])
    captured = {}

    def inspect_and_close():
        for w in root.winfo_children():
            if isinstance(w, fd.FileDialog):
                captured['dir'] = w._current_dir
                w.destroy()
                break

    root.after(50, inspect_and_close)
    result = fd.FileDialog.show(
        root, mode="open", title="t", initial_dir=fake_dir,
        filetypes=[("Tous les fichiers", "*.*")]
    )
    assert captured.get('dir') == os.path.expanduser("~")
    assert result == ""
    root.destroy()
