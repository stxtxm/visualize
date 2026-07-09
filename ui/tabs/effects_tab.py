"""
Effects selection tab for the psychedelic visualizer.
"""

import tkinter as tk
from tkinter import ttk
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _create_dropdown(parent, label_text, variable, values, cmd=None, bg=None):
    """Helper to create a labeled dropdown with neon styling."""
    if bg is None:
        bg = parent.cget("bg")
    lbl = tk.Label(parent, text=label_text, font=('Helvetica', 8, 'bold'),
                   fg="#85859e", bg=bg)
    lbl.pack(anchor=tk.W, pady=(8, 4))
    combo = ttk.Combobox(parent, textvariable=variable, values=values, state='readonly')
    combo.pack(fill=tk.X, pady=(0, 10))
    if cmd:
        combo.bind('<<ComboboxSelected>>', cmd)
    return combo


class EffectsTab(tk.Frame):
    """Tab for selecting visual effect and color palette."""

    BG_PANEL = "#12121d"
    NEON_CYAN = "#00e5ff"

    def __init__(self, master, effect_var, palette_var,
                 effect_changed_cb=None, palette_changed_cb=None):
        super().__init__(master)
        self.configure(bg=self.BG_PANEL)
        self._effect_var = effect_var
        self._palette_var = palette_var
        self._effect_cb = effect_changed_cb
        self._palette_cb = palette_changed_cb
        self._build_ui()

    def _build_ui(self):
        title = tk.Label(self, text="EFFET VISUEL", font=('Helvetica', 9, 'bold'),
                         fg=self.NEON_CYAN, bg=self.BG_PANEL)
        title.pack(anchor=tk.W, pady=(10, 12), padx=12)

        _create_dropdown(
            self, "EFFET", self._effect_var,
            ['Trance Scope', 'Neon Equalizer', 'Psychedelic Plasma',
             '3D Cyber Tunnel', 'Bars', 'Circles', 'Particles',
             'Wave', 'Spectrum'],
            self._effect_cb,
        )

        _create_dropdown(
            self, "PALETTE DE COULEURS", self._palette_var,
            ['psychedelic', 'winamp_classic', 'retro', 'dark', 'rainbow'],
            self._palette_cb,
        )

        # Description area (will be updated on effect change)
        sep = tk.Frame(self, bg="#2a2a3e", height=1)
        sep.pack(fill=tk.X, padx=12, pady=(10, 10))

        desc_title = tk.Label(self, text="DESCRIPTION",
                              font=('Helvetica', 8, 'bold'), fg="#85859e",
                              bg=self.BG_PANEL)
        desc_title.pack(anchor=tk.W, padx=12, pady=(0, 6))

        self._desc_text = tk.StringVar(
            value="Sélectionnez un effet pour voir sa description"
        )
        desc_label = tk.Label(
            self, textvariable=self._desc_text,
            font=('Helvetica', 8), fg="#e2e2ee", bg=self.BG_PANEL,
            justify=tk.LEFT, anchor=tk.W, wraplength=240,
        )
        desc_label.pack(fill=tk.X, padx=12, pady=(0, 10))

        # Initialize description for default effect
        self._update_desc()

    def _update_desc(self, *args):
        descriptions = {
            "Trance Scope": "Visualizer premium : fond image optionnel, bloom spectral, interférences, glyphes orbitaux et strobe BPM.",
            "Neon Equalizer": "Oscilloscope circulaire + barres + rayons + grille. Style classique moderne.",
            "Psychedelic Plasma": "Plasma algorithmique avec couleurs dynamiques et fluides.",
            "3D Cyber Tunnel": "Effet de tunnel 3D style cyberpunk avec perspective.",
            "Bars": "Barres verticales type equalizer classique.",
            "Circles": "Cercles concentriques réactifs au rythme.",
            "Particles": "Particules réagissant au beat et aux fréquences.",
            "Wave": "Vagues sinusoïdales synchronisées sur l'audio.",
            "Spectrum": "Spectre fréquences détaillé avec analyse FFT.",
        }
        effect = self._effect_var.get()
        self._desc_text.set(descriptions.get(effect, "Aucune description disponible."))