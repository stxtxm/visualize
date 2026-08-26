"""
File selection tab for Visualize.
"""

import tkinter as tk
from tkinter import messagebox, ttk
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.file_dialog import FileDialog


class FileTab(tk.Frame):
    """Tab for audio file selection and info display."""

    BG_PANEL = "#12121d"
    BG_CARD = "#1b1b2a"
    FG_LIGHT = "#e2e2ee"
    FG_MUTED = "#85859e"
    NEON_CYAN = "#00e5ff"
    NEON_GREEN = "#39ff14"

    def __init__(self, master, audio_file_var, status_callback=None, audio_device_var=None):
        super().__init__(master)
        self.configure(bg=self.BG_PANEL)
        self.audio_file = audio_file_var
        self.status_callback = status_callback
        self.audio_device_var = audio_device_var
        self._file_info_text = None
        self._build_ui()

    def _build_ui(self):
        # Title
        title = tk.Label(self, text="FICHIER AUDIO", font=('Helvetica', 9, 'bold'),
                         fg=self.NEON_CYAN, bg=self.BG_PANEL)
        title.pack(anchor=tk.W, pady=(10, 12), padx=12)

        # File row
        file_row = tk.Frame(self, bg=self.BG_PANEL)
        file_row.pack(fill=tk.X, padx=12, pady=(0, 6))

        self.entry_file = tk.Entry(
            file_row, textvariable=self.audio_file,
            bg=self.BG_CARD, fg=self.FG_LIGHT,
            insertbackground=self.FG_LIGHT, bd=0,
            font=('Helvetica', 9),
            highlightthickness=1, highlightbackground="#2a2a3e",
            highlightcolor=self.NEON_CYAN,
        )
        self.entry_file.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(0, 6))

        btn_browse = tk.Button(
            file_row, text="PARCOURIR", command=self._open_file,
            bg="#252538", fg=self.FG_LIGHT, activebackground="#35354e",
            activeforeground=self.FG_LIGHT, bd=0, padx=8,
            font=('Helvetica', 7, 'bold'), cursor="hand2"
        )
        btn_browse.pack(side=tk.RIGHT)
        self._add_hover(btn_browse, "#35354e", "#252538")

        # Clear action hint (native Tk drag-and-drop is not available everywhere).
        hint = tk.Label(self, text="Formats : MP3, WAV, FLAC, OGG, AAC",
                        font=('Helvetica', 7), fg=self.FG_MUTED, bg=self.BG_PANEL)
        hint.pack(anchor=tk.W, padx=16, pady=(0, 14))

        # Separator
        sep = tk.Frame(self, bg="#2a2a3e", height=1)
        sep.pack(fill=tk.X, padx=12, pady=(0, 12))

        # File info section
        info_title = tk.Label(self, text="INFORMATIONS FICHIER",
                              font=('Helvetica', 8, 'bold'), fg=self.FG_MUTED,
                              bg=self.BG_PANEL)
        info_title.pack(anchor=tk.W, padx=12, pady=(0, 6))

        self._file_info_text = tk.StringVar(value="Aucun fichier sélectionné")
        info_label = tk.Label(
            self, textvariable=self._file_info_text,
            font=('Helvetica', 8), fg=self.FG_LIGHT, bg=self.BG_PANEL,
            justify=tk.LEFT, anchor=tk.W, wraplength=240,
        )
        info_label.pack(fill=tk.X, padx=12, pady=(0, 10))

        # ── Audio device selector ──
        if self.audio_device_var is not None:
            dev_sep = tk.Frame(self, bg="#2a2a3e", height=1)
            dev_sep.pack(fill=tk.X, padx=12, pady=(0, 12))

            dev_title = tk.Label(self, text="SORTIE AUDIO",
                                 font=('Helvetica', 8, 'bold'), fg=self.FG_MUTED,
                                 bg=self.BG_PANEL)
            dev_title.pack(anchor=tk.W, padx=12, pady=(0, 6))

            dev_row = tk.Frame(self, bg=self.BG_PANEL)
            dev_row.pack(fill=tk.X, padx=12, pady=(0, 6))

            self._device_combo = ttk.Combobox(
                dev_row, textvariable=self.audio_device_var,
                state='readonly', width=28, font=('Helvetica', 8),
            )
            self._device_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

            btn_refresh = tk.Button(
                dev_row, text="🔄", command=self._refresh_devices,
                bg="#252538", fg=self.FG_LIGHT, activebackground="#35354e",
                activeforeground=self.FG_LIGHT, bd=0, padx=6,
                font=('Helvetica', 9), cursor="hand2"
            )
            btn_refresh.pack(side=tk.RIGHT, padx=(4, 0))
            self._add_hover(btn_refresh, "#35354e", "#252538")

            self._refresh_devices()

        # Track the file variable for info updates
        self.audio_file.trace_add("write", self._on_file_changed)

    def _refresh_devices(self):
        """Refresh the audio device list from sounddevice."""
        try:
            from audio.player import AudioPlayer
            devices = AudioPlayer.list_devices()
            # Build display names: "index: name (api)"
            display_names = []
            for d in devices:
                label = f"{d['index']}: {d['name']} ({d['api']})"
                display_names.append(label)
            self._device_combo['values'] = display_names
            
            # If current value is not in list, try to match by name
            current = self.audio_device_var.get()
            if current and current not in display_names:
                # Try to find by device name substring
                for d in devices:
                    if current in d['name'] or current == str(d['index']):
                        match = f"{d['index']}: {d['name']} ({d['api']})"
                        self.audio_device_var.set(match)
                        break
            
            # If no valid device selected, pick a default
            if not self.audio_device_var.get() and display_names:
                # Default: select "default" or first device
                for label in display_names:
                    if 'default' in label.lower():
                        self.audio_device_var.set(label)
                        break
                if not self.audio_device_var.get() and display_names:
                    self.audio_device_var.set(display_names[0])
        except Exception as e:
            print(f"[FileTab] refresh_devices error: {e}", file=sys.stderr, flush=True)

    def _open_file(self):
        filetypes = [
            ('Fichiers audio', '*.mp3 *.wav *.flac *.ogg *.aac'),
            ('Tous les fichiers', '*.*')
        ]
        initial_dir = self._default_browse_dir()
        filename = FileDialog.show(
            self.master, mode="open", title="Sélectionner un fichier audio",
            initial_dir=initial_dir, filetypes=filetypes
        )
        if filename:
            self.audio_file.set(filename)

    def _on_file_changed(self, *args):
        path = self.audio_file.get()
        if path and os.path.isfile(path):
            basename = os.path.basename(path)
            size = os.path.getsize(path)
            ext = os.path.splitext(path)[1].upper()
            size_str = self._format_size(size)
            self._file_info_text.set(
                f"📄 {basename}\n"
                f"📦 {size_str}\n"
                f"🏷 {ext}"
            )
            if self.status_callback:
                self.status_callback(f"Fichier chargé: {basename}")
        else:
            self._file_info_text.set("Aucun fichier sélectionné")

    def _default_browse_dir(self):
        for candidate in (os.path.expanduser("~"), os.environ.get("HOME")):
            if candidate and os.path.isdir(candidate):
                return candidate
        return os.path.dirname(os.path.abspath(__file__))

    def _format_size(self, bytes_val):
        for unit in ['o', 'Ko', 'Mo', 'Go']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} To"

    def _add_hover(self, widget, hover_bg, normal_bg):
        widget.bind("<Enter>", lambda e: widget.configure(bg=hover_bg))
        widget.bind("<Leave>", lambda e: widget.configure(bg=normal_bg))
