"""
Export tab for the psychedelic visualizer.
Integrates resolution, quality preset, FPS, and progress bar.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.file_dialog import FileDialog


class ExportTab(tk.Frame):
    """Tab for video export controls with integrated progress bar."""

    BG_PANEL = "#12121d"
    BG_CARD = "#1b1b2a"
    FG_LIGHT = "#e2e2ee"
    FG_MUTED = "#85859e"
    NEON_CYAN = "#00e5ff"
    NEON_GREEN = "#39ff14"
    NEON_PINK = "#ff007f"
    NEON_AMBER = "#ffaa00"

    def __init__(self, master, audio_file_var, resolution_var, fps_var,
                 preset_var, effect_var, palette_var, bg_image_var,
                 export_callback=None, cancel_callback=None,
                 status_callback=None):
        super().__init__(master)
        self.configure(bg=self.BG_PANEL)
        self._audio_file = audio_file_var
        self._resolution = resolution_var
        self._fps = fps_var
        self._preset = preset_var
        self._effect = effect_var
        self._palette = palette_var
        self._bg_image = bg_image_var
        self._export_callback = export_callback
        self._cancel_callback = cancel_callback
        self._status_callback = status_callback
        self._build_ui()

    def _build_ui(self):
        title = tk.Label(self, text="EXPORT VIDÉO", font=('Helvetica', 9, 'bold'),
                         fg=self.NEON_CYAN, bg=self.BG_PANEL)
        title.pack(anchor=tk.W, pady=(10, 12), padx=12)

        intro = tk.Label(
            self,
            text="La vidéo reprend exactement l'effet, le fond et le logo visibles dans la preview.",
            font=('Helvetica', 7), fg=self.FG_MUTED, bg=self.BG_PANEL,
            justify=tk.LEFT, wraplength=250,
        )
        intro.pack(anchor=tk.W, padx=12, pady=(0, 8))

        # Resolution
        self._create_dropdown("RÉSOLUTION", self._resolution,
                              ['1080p', '1440p', '4K'])

        # Quality preset
        self._create_dropdown("PRESET QUALITÉ", self._preset,
                              ['dev', 'fast', 'normal', 'high', '4k'],
                              self._on_preset_change)

        # FPS display
        fps_frame = tk.Frame(self, bg=self.BG_PANEL)
        fps_frame.pack(fill=tk.X, padx=12, pady=(4, 10))
        lbl = tk.Label(fps_frame, text="FPS", font=('Helvetica', 8, 'bold'),
                       fg=self.FG_MUTED, bg=self.BG_PANEL)
        lbl.pack(side=tk.LEFT)
        self._fps_label = tk.Label(fps_frame, textvariable=self._fps,
                                   font=('Courier', 9, 'bold'),
                                   fg=self.NEON_CYAN, bg=self.BG_PANEL)
        self._fps_label.pack(side=tk.RIGHT)

        # Separator
        sep = tk.Frame(self, bg="#2a2a3e", height=1)
        sep.pack(fill=tk.X, padx=12, pady=(10, 12))

        # Export button
        self.btn_export = tk.Button(
            self, text="🎥 EXPORTER LA VIDÉO",
            command=self._on_export_click,
            bg=self.NEON_PINK, fg="#ffffff",
            activebackground="#ff52a2", activeforeground="#ffffff",
            bd=0, pady=8, font=('Helvetica', 10, 'bold'), cursor="hand2",
        )
        self.btn_export.pack(fill=tk.X, padx=12, pady=(0, 12))
        self._add_hover(self.btn_export, "#ff52a2", self.NEON_PINK)

        # Progress section (integrated, no popover)
        self._progress_frame = tk.Frame(self, bg=self.BG_PANEL)
        self._progress_frame.pack(fill=tk.X, padx=12, pady=(0, 4))

        self._progress_label = tk.Label(
            self._progress_frame, text="",
            font=('Helvetica', 8, 'bold'), fg=self.NEON_CYAN,
            bg=self.BG_PANEL, anchor=tk.W,
        )
        self._progress_label.pack(fill=tk.X, pady=(0, 4))

        # Progress bar (canvas)
        self._progress_canvas = tk.Canvas(
            self._progress_frame, height=8,
            bg=self.BG_PANEL, bd=0, highlightthickness=0,
        )
        self._progress_canvas.pack(fill=tk.X)

        self._progress_pct = tk.Label(
            self._progress_frame, text="",
            font=('Courier', 9, 'bold'), fg=self.NEON_CYAN,
            bg=self.BG_PANEL, anchor=tk.E,
        )
        self._progress_pct.pack(fill=tk.X, pady=(2, 0))

        # Cancel button (hidden by default)
        self.btn_cancel = tk.Button(
            self._progress_frame, text="✕ ANNULER",
            command=self._on_cancel_click,
            bg="#3a1a2a", fg="#ff6b6b",
            activebackground="#5a2a3a", activeforeground="#ff6b6b",
            bd=0, pady=6, font=('Helvetica', 9, 'bold'), cursor="hand2",
        )
        self.btn_cancel.pack(fill=tk.X, pady=(6, 0))
        self._add_hover(self.btn_cancel, "#5a2a3a", "#3a1a2a")
        self.btn_cancel.pack_forget()  # hidden initially

        # Hide progress initially
        self._progress_frame.pack_forget()

    def _create_dropdown(self, label_text, variable, values, cmd=None):
        lbl = tk.Label(self, text=label_text, font=('Helvetica', 8, 'bold'),
                       fg=self.FG_MUTED, bg=self.BG_PANEL)
        lbl.pack(anchor=tk.W, padx=12, pady=(8, 4))
        combo = ttk.Combobox(self, textvariable=variable, values=values,
                             state='readonly')
        combo.pack(fill=tk.X, padx=12, pady=(0, 6))
        if cmd:
            combo.bind('<<ComboboxSelected>>', cmd)

    def _on_preset_change(self, event=None):
        from quality_presets import get_preset
        preset = get_preset(self._preset.get())
        self._resolution.set(preset['resolution'])
        self._fps.set(preset['fps'])
        if self._status_callback:
            self._status_callback(f"Préglage: {preset['name']}")

    def _on_export_click(self):
        if not self._audio_file.get():
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier audio d'abord.")
            return

        initial_dir = os.path.expanduser("~")
        filename = FileDialog.show(
            self.master, mode="save", title="Enregistrer la vidéo",
            initial_dir=initial_dir, defaultextension=".mp4",
            filetypes=[('Fichiers MP4', '*.mp4'), ('Tous les fichiers', '*.*')]
        )
        if not filename:
            return

        if self._export_callback:
            self._export_callback(filename)

    def show_progress(self, current, total):
        """Show or update the progress bar."""
        pct = (current / total) * 100 if total > 0 else 0
        self._progress_label.configure(text=f"EXPORT {current}/{total}")
        self._progress_pct.configure(text=f"{pct:.0f}%")
        self._draw_progress(pct)
        self._progress_frame.pack(fill=tk.X, padx=12, pady=(0, 4))
        self._progress_frame.update_idletasks()

    def show_progress_error(self, message):
        """Show error state on progress bar."""
        self._progress_label.configure(text=f"ÉCHEC: {message[:50]}", fg="#ff3b3b")
        self._progress_pct.configure(text="ERR", fg="#ff3b3b")
        self._draw_progress(100, error_color=True)
        self._progress_frame.pack(fill=tk.X, padx=12, pady=(0, 4))
        self._progress_frame.update_idletasks()

    def show_progress_success(self, basename):
        """Show success state on progress bar."""
        self._progress_label.configure(text=f"✓ EXPORT TERMINÉ: {basename}", fg=self.NEON_GREEN)
        self._progress_pct.configure(text="100%", fg=self.NEON_GREEN)
        self._draw_progress(100, success_color=True)
        self._progress_frame.pack(fill=tk.X, padx=12, pady=(0, 4))
        self._progress_frame.update_idletasks()

    def hide_progress(self):
        """Hide the progress bar and cancel button."""
        self.btn_cancel.pack_forget()
        self._progress_frame.pack_forget()

    def show_cancel_button(self):
        """Show the cancel button."""
        self.btn_cancel.pack(fill=tk.X, pady=(6, 0))

    def hide_cancel_button(self):
        """Hide the cancel button."""
        self.btn_cancel.pack_forget()

    def _on_cancel_click(self):
        """Called when the user clicks the cancel button."""
        if self._cancel_callback:
            self._cancel_callback()

    def set_export_button_state(self, enabled=True):
        """Enable or disable the export button."""
        state = tk.NORMAL if enabled else tk.DISABLED
        text = "🎥 EXPORTER LA VIDÉO" if enabled else "⏳ EXPORT EN COURS..."
        self.btn_export.config(state=state, text=text)

    def _draw_progress(self, pct, success_color=False, error_color=False):
        """Draw the progress bar on the canvas."""
        c = self._progress_canvas
        try:
            c.update_idletasks()
        except Exception:
            return
        w = c.winfo_width()
        h = c.winfo_height()
        if w <= 2 or h <= 2:
            return

        c.delete("all")
        r = h / 2.0
        pct = max(0.0, min(100.0, pct))

        # Track
        c.create_rectangle(1.5, 1.5, w - 1.5, h - 1.5,
                           fill="#14233b", outline="#24405e", width=1)

        fw = (w - 3) * pct / 100.0
        if fw > 1:
            if error_color:
                fill = "#ff3b3b"
            elif success_color:
                fill = self.NEON_GREEN
            else:
                fill = self.NEON_CYAN
            c.create_rectangle(1.5, 1.5, 1.5 + fw, h - 1.5,
                               fill=fill, outline="", width=0)

    def _add_hover(self, widget, hover_bg, normal_bg):
        widget.bind("<Enter>", lambda e: widget.configure(bg=hover_bg))
        widget.bind("<Leave>", lambda e: widget.configure(bg=normal_bg))
