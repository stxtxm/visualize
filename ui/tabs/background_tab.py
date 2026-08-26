"""
Background image tab for Visualize.
"""

import tkinter as tk
from tkinter import messagebox
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.file_dialog import FileDialog


class BackgroundTab(tk.Frame):
    """Tab for background image selection and opacity control."""

    BG_PANEL = "#12121d"
    BG_CARD = "#1b1b2a"
    FG_LIGHT = "#e2e2ee"
    FG_MUTED = "#85859e"
    NEON_CYAN = "#00e5ff"
    NEON_PINK = "#ff007f"

    def __init__(self, master, background_image_var, opacity_var,
                 opacity_label=None, status_callback=None):
        super().__init__(master)
        self.configure(bg=self.BG_PANEL)
        self._bg_var = background_image_var
        self._opacity_var = opacity_var
        self._status_callback = status_callback
        self._build_ui()

    def _build_ui(self):
        title = tk.Label(self, text="IMAGE DE FOND", font=('Helvetica', 9, 'bold'),
                         fg=self.NEON_CYAN, bg=self.BG_PANEL)
        title.pack(anchor=tk.W, pady=(10, 12), padx=12)

        # File row
        bg_row = tk.Frame(self, bg=self.BG_PANEL)
        bg_row.pack(fill=tk.X, padx=12, pady=(0, 6))

        self.entry_bg = tk.Entry(
            bg_row, textvariable=self._bg_var,
            bg=self.BG_CARD, fg=self.FG_LIGHT,
            insertbackground=self.FG_LIGHT, bd=0,
            font=('Helvetica', 9),
            highlightthickness=1, highlightbackground="#2a2a3e",
            highlightcolor=self.NEON_CYAN,
        )
        self.entry_bg.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(0, 6))

        btn_bg = tk.Button(
            bg_row, text="CHOISIR", command=self._open_background,
            bg="#252538", fg=self.FG_LIGHT, activebackground="#35354e",
            activeforeground=self.FG_LIGHT, bd=0, padx=8,
            font=('Helvetica', 7, 'bold'), cursor="hand2"
        )
        btn_bg.pack(side=tk.RIGHT)
        self._add_hover(btn_bg, "#35354e", "#252538")

        # Remove button
        self.btn_remove = tk.Button(
            self, text="✕ RETIRER LE FOND",
            command=self._remove_background,
            bg="#1a1a2e", fg="#ff3b3b",
            activebackground="#2a0a0a", activeforeground="#ff5b5b",
            bd=0, padx=6, pady=4, font=('Helvetica', 8, 'bold'),
            cursor="hand2"
        )
        self.btn_remove.pack(fill=tk.X, padx=12, pady=(6, 16))
        self._add_hover(self.btn_remove, "#2a0a0a", "#1a1a2e")

        # Separator
        sep = tk.Frame(self, bg="#2a2a3e", height=1)
        sep.pack(fill=tk.X, padx=12, pady=(0, 12))

        # Opacity section
        opacity_title = tk.Label(self, text="OPACITÉ DU FOND",
                                 font=('Helvetica', 8, 'bold'), fg=self.FG_MUTED,
                                 bg=self.BG_PANEL)
        opacity_title.pack(anchor=tk.W, padx=12, pady=(0, 8))

        slider_row = tk.Frame(self, bg=self.BG_PANEL)
        slider_row.pack(fill=tk.X, padx=12, pady=(0, 4))

        self.opacity_slider = tk.Scale(
            slider_row, from_=0, to=100, orient=tk.HORIZONTAL,
            variable=self._opacity_var, command=self._on_opacity_change,
            showvalue=False, bg=self.BG_PANEL, fg=self.FG_LIGHT,
            highlightthickness=0, bd=0, troughcolor="#1a1a2e",
            activebackground=self.NEON_CYAN, sliderlength=16, length=180,
        )
        self.opacity_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._opacity_label = tk.Label(
            slider_row, text=f"{int(self._opacity_var.get())}%",
            font=('Courier', 9, 'bold'), fg=self.NEON_CYAN,
            bg=self.BG_PANEL, width=4, anchor=tk.E,
        )
        self._opacity_label.pack(side=tk.RIGHT, padx=(8, 0))

        # Info text
        info = tk.Label(
            self, text="L'image de fond est utilisée comme matière\ngraphique beat-synced par l'effet Trance Scope.",
            font=('Helvetica', 7), fg=self.FG_MUTED, bg=self.BG_PANEL,
            justify=tk.LEFT,
        )
        info.pack(anchor=tk.W, padx=16, pady=(12, 0))

    def _open_background(self):
        filetypes = [
            ('Images', '*.png *.jpg *.jpeg *.webp *.bmp'),
            ('Tous les fichiers', '*.*')
        ]
        filename = FileDialog.show(
            self.master, mode="open", title="Sélectionner une image de fond",
            initial_dir=os.path.expanduser("~"), filetypes=filetypes
        )
        if filename:
            self._bg_var.set(filename)
            if self._status_callback:
                self._status_callback(f"Fond: {os.path.basename(filename)}")

    def _remove_background(self):
        self._bg_var.set("")
        if self._status_callback:
            self._status_callback("Fond retiré")

    def _on_opacity_change(self, val):
        pct = int(float(val))
        self._opacity_label.configure(text=f"{pct}%")

    def _add_hover(self, widget, hover_bg, normal_bg):
        widget.bind("<Enter>", lambda e: widget.configure(bg=hover_bg))
        widget.bind("<Leave>", lambda e: widget.configure(bg=normal_bg))
