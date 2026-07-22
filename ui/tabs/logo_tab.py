"""Logo overlay controls for the preview and video export."""

import os
import tkinter as tk
from tkinter import ttk

from ui.file_dialog import FileDialog


class LogoTab(tk.Frame):
    """Select a logo and place it anywhere in the rendered frame."""

    BG_PANEL = "#12121d"
    BG_CARD = "#1b1b2a"
    FG_LIGHT = "#e2e2ee"
    FG_MUTED = "#85859e"
    NEON_CYAN = "#00e5ff"

    POSITION_COORDINATES = {
        "top-left": (0, 0),
        "top-center": (50, 0),
        "top-right": (100, 0),
        "center-left": (0, 50),
        "center": (50, 50),
        "center-right": (100, 50),
        "bottom-left": (0, 100),
        "bottom-center": (50, 100),
        "bottom-right": (100, 100),
    }

    def __init__(self, master, logo_image_var, position_var, x_var, y_var,
                 scale_var, opacity_var, change_callback=None,
                 status_callback=None):
        super().__init__(master)
        self.configure(bg=self.BG_PANEL)
        self._logo_var = logo_image_var
        self._position_var = position_var
        self._x_var = x_var
        self._y_var = y_var
        self._scale_var = scale_var
        self._opacity_var = opacity_var
        self._change_callback = change_callback
        self._status_callback = status_callback
        self._build_ui()

    def _build_ui(self):
        title = tk.Label(self, text="LOGO SUPERPOSÉ", font=('Helvetica', 9, 'bold'),
                         fg=self.NEON_CYAN, bg=self.BG_PANEL)
        title.pack(anchor=tk.W, pady=(10, 12), padx=12)

        logo_row = tk.Frame(self, bg=self.BG_PANEL)
        logo_row.pack(fill=tk.X, padx=12, pady=(0, 6))
        self.entry_logo = tk.Entry(
            logo_row, textvariable=self._logo_var,
            bg=self.BG_CARD, fg=self.FG_LIGHT,
            insertbackground=self.FG_LIGHT, bd=0, font=('Helvetica', 9),
            highlightthickness=1, highlightbackground="#2a2a3e",
            highlightcolor=self.NEON_CYAN,
        )
        self.entry_logo.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(0, 6))

        btn_logo = tk.Button(
            logo_row, text="CHOISIR", command=self._open_logo,
            bg="#252538", fg=self.FG_LIGHT, activebackground="#35354e",
            activeforeground=self.FG_LIGHT, bd=0, padx=8,
            font=('Helvetica', 7, 'bold'), cursor="hand2"
        )
        btn_logo.pack(side=tk.RIGHT)
        self._add_hover(btn_logo, "#35354e", "#252538")

        self.btn_remove = tk.Button(
            self, text="✕ RETIRER LE LOGO", command=self._remove_logo,
            bg="#1a1a2e", fg="#ff3b3b", activebackground="#2a0a0a",
            activeforeground="#ff5b5b", bd=0, padx=6, pady=4,
            font=('Helvetica', 8, 'bold'), cursor="hand2"
        )
        self.btn_remove.pack(fill=tk.X, padx=12, pady=(6, 12))
        self._add_hover(self.btn_remove, "#2a0a0a", "#1a1a2e")

        self._create_dropdown(
            "POSITION", self._position_var,
            ["top-left", "top-center", "top-right", "center-left", "center",
             "center-right", "bottom-left", "bottom-center", "bottom-right", "custom"],
            self._on_position_change,
        )

        self.x_slider = self._create_slider("X (CUSTOM)", self._x_var, self._on_x_change)
        self.y_slider = self._create_slider("Y (CUSTOM)", self._y_var, self._on_y_change)
        self.scale_slider = self._create_slider(
            "TAILLE", self._scale_var, self._on_scale_change, suffix="%"
        )
        self.opacity_slider = self._create_slider(
            "OPACITÉ", self._opacity_var, self._on_opacity_change, suffix="%"
        )

        info = tk.Label(
            self,
            text="Les coordonnées X/Y vont de 0 à 100 %\n\nLe logo est conservé dans la preview et l'export.",
            font=('Helvetica', 7), fg=self.FG_MUTED, bg=self.BG_PANEL,
            justify=tk.LEFT,
        )
        info.pack(anchor=tk.W, padx=16, pady=(12, 0))

    def _create_dropdown(self, label_text, variable, values, callback):
        label = tk.Label(self, text=label_text, font=('Helvetica', 8, 'bold'),
                         fg=self.FG_MUTED, bg=self.BG_PANEL)
        label.pack(anchor=tk.W, padx=12, pady=(0, 5))
        combo = ttk.Combobox(self, textvariable=variable, values=values,
                             state='readonly')
        combo.pack(fill=tk.X, padx=12, pady=(0, 8))
        combo.bind('<<ComboboxSelected>>', callback)
        self.position_combo = combo

    def _create_slider(self, label_text, variable, callback, suffix="%"):
        title = tk.Label(self, text=label_text, font=('Helvetica', 8, 'bold'),
                         fg=self.FG_MUTED, bg=self.BG_PANEL)
        title.pack(anchor=tk.W, padx=12, pady=(2, 4))
        row = tk.Frame(self, bg=self.BG_PANEL)
        row.pack(fill=tk.X, padx=12, pady=(0, 5))
        slider = tk.Scale(
            row, from_=0, to=100, orient=tk.HORIZONTAL,
            variable=variable, command=callback, showvalue=False,
            bg=self.BG_PANEL, fg=self.FG_LIGHT, highlightthickness=0,
            bd=0, troughcolor="#1a1a2e", activebackground=self.NEON_CYAN,
            sliderlength=16, length=180,
        )
        slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        label = tk.Label(row, text=f"{int(variable.get())}{suffix}",
                         font=('Courier', 9, 'bold'), fg=self.NEON_CYAN,
                         bg=self.BG_PANEL, width=5, anchor=tk.E)
        label.pack(side=tk.RIGHT, padx=(8, 0))
        slider._value_label = label
        slider._value_suffix = suffix
        return slider

    def _notify(self, status=None):
        if status and self._status_callback:
            self._status_callback(status)
        if self._change_callback:
            self._change_callback()

    def _open_logo(self):
        filetypes = [
            ('Images', '*.png *.jpg *.jpeg *.webp *.bmp'),
            ('Tous les fichiers', '*.*'),
        ]
        filename = FileDialog.show(
            self.master, mode="open", title="Sélectionner un logo",
            initial_dir=os.path.expanduser("~"), filetypes=filetypes,
        )
        if filename:
            self._logo_var.set(filename)
            self._notify(f"Logo: {os.path.basename(filename)}")

    def _remove_logo(self):
        self._logo_var.set("")
        self._notify("Logo retiré")

    def _on_position_change(self, event=None):
        position = self._position_var.get()
        if position in self.POSITION_COORDINATES:
            x, y = self.POSITION_COORDINATES[position]
            self._x_var.set(x)
            self._y_var.set(y)
        self._notify(f"Position du logo: {position}")

    def _on_custom_change(self, variable, slider, value):
        slider._value_label.configure(text=f"{int(float(value))}{slider._value_suffix}")
        self._position_var.set("custom")
        self._notify()

    def _on_x_change(self, value):
        self._on_custom_change(self._x_var, self.x_slider, value)

    def _on_y_change(self, value):
        self._on_custom_change(self._y_var, self.y_slider, value)

    def _on_scale_change(self, value):
        self.scale_slider._value_label.configure(text=f"{int(float(value))}%")
        self._notify()

    def _on_opacity_change(self, value):
        self.opacity_slider._value_label.configure(text=f"{int(float(value))}%")
        self._notify()

    def _add_hover(self, widget, hover_bg, normal_bg):
        widget.bind("<Enter>", lambda e: widget.configure(bg=hover_bg))
        widget.bind("<Leave>", lambda e: widget.configure(bg=normal_bg))
