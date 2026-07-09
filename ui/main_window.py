"""
Main window for the psychedelic visualizer GUI.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from ui.file_dialog import FileDialog
import threading
import os
import sys
import time
import webbrowser
from PIL import Image, ImageDraw, ImageFont, ImageTk

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from version import __version__
except ImportError:
    __version__ = "0.0.0"

class MainWindow:
    """
    Main application window for the psychedelic visualizer.
    """

    def __init__(self, root):
        """
        Initialize the main window.
        
        Args:
            root: Tk root window
        """
        self.root = root
        self.is_playing = tk.BooleanVar(value=False)
        self._is_playing_event = threading.Event()
        self.audio_file = tk.StringVar(value="")
        self.selected_effect = tk.StringVar(value="Trance Scope")
        self.selected_color = tk.StringVar(value="psychedelic")
        self.background_image = tk.StringVar(value="")
        self.resolution = tk.StringVar(value="1080p")
        self.fps = tk.IntVar(value=60)
        self.selected_preset = tk.StringVar(value="normal")
        
        self.playback_thread = None
        self.analyzer = None
        self.preview_renderer = None
        self.effect_manager = None
        self.recorder = None
        
        # Frame skipping: skip frames if rendering is too slow
        self._frame_skip_counter = 0
        self._frame_skip_threshold = 0
        self._last_frame_time = 0.0
        self._frame_times = []
        
        # Pre-allocated PhotoImage for thread-safe updates
        self._pending_frame = None
        self._frame_lock = threading.Lock()

        # Export popover visibility state (persists between exports)
        self.export_popover_hidden = False
        self._export_in_progress = False
        self._load_ui_preferences()

        self._setup_ui()

    def _load_ui_preferences(self):
        """Load UI preferences from config file (export popover visibility)."""
        import json
        config_path = os.path.join(self._user_home_dir(), ".visualize_config.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    self.export_popover_hidden = config.get("export_popover_hidden", False)
        except Exception as e:
            print(f"[WARNING] Failed to load UI preferences: {e}")
            self.export_popover_hidden = False

    def _save_ui_preferences(self):
        """Save UI preferences to config file."""
        import json
        config_path = os.path.join(self._user_home_dir(), ".visualize_config.json")
        try:
            config = {
                "export_popover_hidden": self.export_popover_hidden
            }
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"[WARNING] Failed to save UI preferences: {e}")

    def _load_icon(self, path, size=28):
        """Load an icon from file, with fallback to a simple colored circle if file not found."""
        try:
            img = Image.open(path)
            img = img.resize((size, size), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except (FileNotFoundError, OSError, IOError) as e:
            # Fallback: create a simple colored circle as placeholder
            img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            cx, cy = size // 2, size // 2
            r = size // 2 - 2
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=self.NEON_CYAN)
            return ImageTk.PhotoImage(img)

    def _setup_ui(self):
        """Set up a modernized cyberpunk side-by-side UI."""
        # Couleurs du thème cyberpunk / Winamp modernisé
        self.BG_DARK = "#09090d"     # Fond principal ultra-sombre
        self.BG_PANEL = "#12121d"    # Fond du panneau latéral (sidebar)
        self.BG_CARD = "#1b1b2a"     # Fond des cartes/champs de saisie
        self.FG_LIGHT = "#e2e2ee"    # Texte principal clair
        self.FG_MUTED = "#85859e"    # Texte secondaire grisé
        
        self.NEON_CYAN = "#00e5ff"   # Cyan fluo
        self.NEON_PINK = "#ff007f"   # Rose fluo
        self.NEON_GREEN = "#39ff14"  # Vert fluo
        self.NEON_AMBER = "#ffaa00"  # Orange fluo
        
        self.root.title(f"Visualisateur Psychédélique {__version__}")
        self.root.geometry("1180x720")
        self.root.minsize(980, 640)
        self.root.configure(bg=self.BG_DARK)
        
        # Appliquer le style global TTK
        style = ttk.Style()
        style.theme_use('default')
        style.configure('.', background=self.BG_DARK, foreground=self.FG_LIGHT)
        style.configure('TFrame', background=self.BG_DARK)
        
        # Style pour les ComboBox de façon propre
        style.map('TCombobox', fieldbackground=[('readonly', self.BG_CARD)],
                              selectbackground=[('readonly', self.NEON_CYAN)],
                              selectforeground=[('readonly', '#000000')],
                              background=[('readonly', self.BG_CARD)])
        style.configure('TCombobox', foreground=self.FG_LIGHT, fieldbackground=self.BG_CARD,
                        bordercolor=self.BG_PANEL, arrowcolor=self.NEON_CYAN,
                        font=('Helvetica', 9))
        
        # Main container
        main_frame = tk.Frame(self.root, bg=self.BG_DARK, padx=12, pady=12)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # LEFT PANEL (SIDEBAR CONTROLS)
        left_panel = tk.Frame(main_frame, bg=self.BG_PANEL, width=280, padx=15, pady=15, bd=1, relief="solid", highlightbackground=self.NEON_CYAN, highlightcolor=self.NEON_CYAN)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        left_panel.pack_propagate(False) # Garder sa taille fixe
        
        # Branding
        title_label = tk.Label(left_panel, text="PSYCHEDELIC", font=('Helvetica', 16, 'bold'), fg=self.NEON_CYAN, bg=self.BG_PANEL)
        title_label.pack(anchor=tk.W, pady=(0, 2))
        sub_label = tk.Label(left_panel, text=f"VISUALIZER v{__version__}", font=('Helvetica', 9, 'bold'), fg=self.NEON_PINK, bg=self.BG_PANEL)
        sub_label.pack(anchor=tk.W, pady=(0, 20))
        
        # --- SECTION FILE ---
        lbl_file = tk.Label(left_panel, text="FICHIER AUDIO", font=('Helvetica', 8, 'bold'), fg=self.FG_MUTED, bg=self.BG_PANEL)
        lbl_file.pack(anchor=tk.W, pady=(0, 4))
        
        file_container = tk.Frame(left_panel, bg=self.BG_PANEL)
        file_container.pack(fill=tk.X, pady=(0, 15))
        
        self.entry_file = tk.Entry(file_container, textvariable=self.audio_file, bg=self.BG_CARD, fg=self.FG_LIGHT, insertbackground=self.FG_LIGHT, bd=0, font=('Helvetica', 9), highlightthickness=1, highlightbackground="#2a2a3e", highlightcolor=self.NEON_CYAN)
        self.entry_file.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(0, 6))
        
        btn_browse = tk.Button(file_container, text="...", command=self._open_file, bg="#252538", fg=self.FG_LIGHT, activebackground="#35354e", activeforeground=self.FG_LIGHT, bd=0, padx=8, font=('Helvetica', 9, 'bold'), cursor="hand2")
        btn_browse.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Hover effect helper
        def add_hover(widget, hover_bg, normal_bg):
            widget.bind("<Enter>", lambda e: widget.configure(bg=hover_bg))
            widget.bind("<Leave>", lambda e: widget.configure(bg=normal_bg))
            
        add_hover(btn_browse, "#35354e", "#252538")
        
        # --- SECTION CONTROLS ---
        def create_dropdown(parent, label_text, variable, values, cmd=None):
            lbl = tk.Label(parent, text=label_text, font=('Helvetica', 8, 'bold'), fg=self.FG_MUTED, bg=self.BG_PANEL)
            lbl.pack(anchor=tk.W, pady=(8, 4))
            combo = ttk.Combobox(parent, textvariable=variable, values=values, state='readonly')
            combo.pack(fill=tk.X, pady=(0, 10))
            if cmd:
                combo.bind('<<ComboboxSelected>>', cmd)
            return combo
            
        create_dropdown(left_panel, "EFFET", self.selected_effect,
                        ['Trance Scope', 'Neon Equalizer', 'Psychedelic Plasma', '3D Cyber Tunnel'],
                        self._effect_changed)
        create_dropdown(left_panel, "PALETTE", self.selected_color,
                        ['psychedelic', 'winamp_classic', 'retro', 'dark', 'rainbow'],
                        self._palette_changed)
        create_dropdown(left_panel, "RÉSOLUTION EXPORT", self.resolution, ['1080p', '1440p', '4K'])
        create_dropdown(left_panel, "PRESET DE QUALITÉ", self.selected_preset, ['dev', 'fast', 'normal', 'high', '4k'], self._preset_changed)

        lbl_bg = tk.Label(left_panel, text="IMAGE DE FOND", font=('Helvetica', 8, 'bold'), fg=self.FG_MUTED, bg=self.BG_PANEL)
        lbl_bg.pack(anchor=tk.W, pady=(8, 4))
        bg_container = tk.Frame(left_panel, bg=self.BG_PANEL)
        bg_container.pack(fill=tk.X, pady=(0, 10))
        self.entry_background = tk.Entry(bg_container, textvariable=self.background_image, bg=self.BG_CARD,
                                         fg=self.FG_LIGHT, insertbackground=self.FG_LIGHT, bd=0,
                                         font=('Helvetica', 9), highlightthickness=1,
                                         highlightbackground="#2a2a3e", highlightcolor=self.NEON_CYAN)
        self.entry_background.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(0, 6))
        btn_bg = tk.Button(bg_container, text="+", command=self._open_background_file, bg="#252538",
                           fg=self.FG_LIGHT, activebackground="#35354e", activeforeground=self.FG_LIGHT,
                           bd=0, padx=9, font=('Helvetica', 10, 'bold'), cursor="hand2")
        btn_bg.pack(side=tk.RIGHT, fill=tk.Y)
        add_hover(btn_bg, "#35354e", "#252538")

        # ── Opacity slider for background ──
        self.opacity_var = tk.DoubleVar(value=72)
        opacity_frame = tk.Frame(left_panel, bg=self.BG_PANEL)
        opacity_frame.pack(fill=tk.X, pady=(0, 4))
        lbl_opacity = tk.Label(opacity_frame, text="OPACITÉ FOND", font=('Helvetica', 8, 'bold'), fg=self.FG_MUTED, bg=self.BG_PANEL)
        lbl_opacity.pack(anchor=tk.W)
        slider_row = tk.Frame(opacity_frame, bg=self.BG_PANEL)
        slider_row.pack(fill=tk.X, pady=(4, 0))
        self.opacity_slider = tk.Scale(slider_row, from_=0, to=100, orient=tk.HORIZONTAL,
                                       variable=self.opacity_var, command=self._on_opacity_change,
                                       showvalue=False, bg=self.BG_PANEL, fg=self.FG_LIGHT,
                                       highlightthickness=0, bd=0, troughcolor="#1a1a2e",
                                       activebackground=self.NEON_CYAN, sliderlength=16, length=180)
        self.opacity_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._opacity_label = tk.Label(slider_row, text="72%", font=('Courier', 9, 'bold'),
                                       fg=self.NEON_CYAN, bg=self.BG_PANEL, width=4, anchor=tk.E)
        self._opacity_label.pack(side=tk.RIGHT, padx=(8, 0))

        # ── Remove background button ──
        self.btn_remove_bg = tk.Button(left_panel, text="✕ RETIRER LE FOND",
                                       command=self._remove_background,
                                       bg="#1a1a2e", fg="#ff3b3b",
                                       activebackground="#2a0a0a", activeforeground="#ff5b5b",
                                       bd=0, padx=6, pady=3, font=('Helvetica', 8, 'bold'),
                                       cursor="hand2")
        self.btn_remove_bg.pack(fill=tk.X, pady=(0, 10))
        add_hover(self.btn_remove_bg, "#2a0a0a", "#1a1a2e")

        # Spacer
        left_panel.grid_rowconfigure(9, weight=1)
        
        # --- ACTION BUTTONS (PLAY/STOP) ---
        btn_container = tk.Frame(left_panel, bg=self.BG_PANEL)
        btn_container.pack(side=tk.BOTTOM, fill=tk.X, pady=(15, 0))
        
        # Lecture
        self.btn_play = tk.Button(btn_container, text="▶  LECTURE", command=self._toggle_playback, bg=self.NEON_GREEN, fg="#05050a", activebackground="#a2ff8e", activeforeground="#05050a", bd=0, pady=6, font=('Helvetica', 10, 'bold'), cursor="hand2")
        self.btn_play.pack(fill=tk.X, pady=(0, 8))
        add_hover(self.btn_play, "#a2ff8e", self.NEON_GREEN)
        
        # Arrêter
        self.btn_stop = tk.Button(btn_container, text="⏹  ARRÊTER", command=self._stop_playback, bg=self.NEON_PINK, fg="#ffffff", activebackground="#ff52a2", activeforeground="#ffffff", bd=0, pady=6, font=('Helvetica', 10, 'bold'), cursor="hand2")
        self.btn_stop.pack(fill=tk.X, pady=(0, 15))
        add_hover(self.btn_stop, "#ff52a2", self.NEON_PINK)
        
        # Export & Logs row
        secondary_btn_frame = tk.Frame(btn_container, bg=self.BG_PANEL)
        secondary_btn_frame.pack(fill=tk.X)
        
        self.btn_export = tk.Button(secondary_btn_frame, text="🎥 EXPORTER", command=self._export_video, bg="#2a2a3e", fg=self.FG_LIGHT, activebackground="#3a3a55", activeforeground=self.FG_LIGHT, bd=0, pady=5, font=('Helvetica', 8, 'bold'), cursor="hand2")
        self.btn_export.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        add_hover(self.btn_export, "#3a3a55", "#2a2a3e")
        
        btn_logs = tk.Button(secondary_btn_frame, text="📝 LOGS", command=self._show_logs, bg="#2a2a3e", fg=self.FG_LIGHT, activebackground="#3a3a55", activeforeground=self.FG_LIGHT, bd=0, pady=5, font=('Helvetica', 8, 'bold'), cursor="hand2")
        btn_logs.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(4, 0))
        add_hover(btn_logs, "#3a3a55", "#2a2a3e")
        
        # RIGHT PANEL (PREVIEW + STATUS)
        right_panel = tk.Frame(main_frame, bg=self.BG_DARK)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Title of Aperçu
        preview_title = tk.Label(right_panel, text="ÉCRAN DE PREVIEW", font=('Helvetica', 9, 'bold'), fg=self.NEON_CYAN, bg=self.BG_DARK)
        preview_title.pack(anchor=tk.W, pady=(0, 8))
        
        # Preview screen container with glowing border
        preview_border = tk.Frame(right_panel, bg=self.NEON_CYAN, bd=1)
        preview_border.pack(fill=tk.BOTH, expand=True)
        
        self.preview = PreviewFrame(preview_border, bd=0, highlightthickness=0)
        self.preview.pack(fill=tk.BOTH, expand=True)
        
        # ── Export progress popover (overlaid on preview, bottom-right) ──
        self._export_popover = tk.Frame(
            self.preview, bg="#0a0a12", bd=0,
            highlightthickness=1, highlightbackground=self.NEON_CYAN
        )
        # Inner container with padding
        self._export_popover_inner = tk.Frame(self._export_popover, bg="#0a0a12")
        self._export_popover_inner.pack(fill=tk.BOTH, padx=10, pady=6)
        # Header row: icon + label
        popover_header = tk.Frame(self._export_popover_inner, bg="#0a0a12")
        popover_header.pack(fill=tk.X, pady=(0, 4))
        self._export_popover_icon = tk.Label(popover_header, text="🎥", font=('Helvetica', 8),
                                             bg="#0a0a12", fg=self.FG_LIGHT)
        self._export_popover_icon.pack(side=tk.LEFT, padx=(0, 6))
        self._export_popover_label = tk.Label(popover_header, text="EXPORT",
                                              font=('Helvetica', 8, 'bold'),
                                              bg="#0a0a12", fg=self.NEON_CYAN)
        self._export_popover_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Hide toggle button (eye icon)
        self._export_popover_hide = tk.Label(popover_header, text="👁",
                                              font=('Helvetica', 8, 'bold'),
                                              bg="#0a0a12", fg=self.FG_MUTED,
                                              cursor="hand2")
        self._export_popover_hide.pack(side=tk.RIGHT, padx=(0, 6))
        self._export_popover_hide.bind("<Button-1>", lambda e: self._toggle_export_popover())
        self._export_popover_hide.bind("<Enter>", lambda e: self._export_popover_hide.configure(fg=self.NEON_CYAN))
        self._export_popover_hide.bind("<Leave>", lambda e: self._export_popover_hide.configure(fg=self.FG_MUTED))
        
        # Close button
        self._export_popover_close = tk.Label(popover_header, text="✕",
                                               font=('Helvetica', 8, 'bold'),
                                               bg="#0a0a12", fg="#555",
                                               cursor="hand2")
        self._export_popover_close.pack(side=tk.RIGHT, padx=(6, 0))
        self._export_popover_close.bind("<Button-1>", lambda e: self._hide_export_popover())
        self._export_popover_close.bind("<Enter>", lambda e: self._export_popover_close.configure(fg="#ff3b3b"))
        self._export_popover_close.bind("<Leave>", lambda e: self._export_popover_close.configure(fg="#555"))
        # Progress bar row
        progress_row = tk.Frame(self._export_popover_inner, bg="#0a0a12")
        progress_row.pack(fill=tk.X)
        self._export_popover_track = tk.Frame(progress_row, bg="#1a1a2e", height=4, bd=0)
        self._export_popover_track.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self._export_popover_fill = tk.Frame(self._export_popover_track, bg=self.NEON_CYAN, height=4, bd=0)
        self._export_popover_fill.place(x=0, y=0, width=0, relheight=1.0)
        self._export_popover_pct = tk.Label(progress_row, text="0%",
                                            font=('Courier', 8, 'bold'),
                                            bg="#0a0a12", fg=self.NEON_CYAN, width=4, anchor=tk.E)
        self._export_popover_pct.pack(side=tk.RIGHT)

        # Status Bar
        self.status_var = tk.StringVar(value="PRÊT")
        status_frame = tk.Frame(right_panel, bg="#111116", height=24, bd=0)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self._led_status = tk.Label(status_frame, text="●", font=('Helvetica', 10), fg=self.NEON_CYAN, bg="#111116", padx=5)
        self._led_status.pack(side=tk.LEFT)
        
        # Update led status dynamically when playback state changes
        def update_led(*args):
            if self.is_playing.get():
                self._led_status.configure(fg=self.NEON_GREEN)
            else:
                self._led_status.configure(fg=self.NEON_CYAN)
        self.is_playing.trace_add("write", update_led)
        
        status_label = tk.Label(status_frame, textvariable=self.status_var, font=('Courier', 9, 'bold'), fg=self.NEON_CYAN, bg="#111116", anchor=tk.W)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # ── Footer: copyright + social links ──
        self._footer = tk.Frame(self.root, bg="#0a0a12", height=24)
        self._footer.pack(side=tk.BOTTOM, fill=tk.X)
        self._footer.pack_propagate(False)

        self._footer_copyright = tk.Label(self._footer, text="© 2026 Timothée Grollier",
                 font=('Helvetica', 7), fg="#8a8aaa", bg="#0a0a12",
                 anchor=tk.W)
        self._footer_copyright.pack(side=tk.LEFT, padx=10)

        # Social icons – loaded from professional assets
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
        self._icon_linkedin = self._load_icon(os.path.join(assets_dir, "linkedin.png"), 28)
        self._icon_linkedin_hover = self._load_icon(os.path.join(assets_dir, "linkedin_hover.png"), 28)
        self._icon_website = self._load_icon(os.path.join(assets_dir, "website.png"), 28)
        self._icon_website_hover = self._load_icon(os.path.join(assets_dir, "website_hover.png"), 28)

        social = tk.Frame(self._footer, bg="#0a0a12")
        social.pack(side=tk.RIGHT, padx=(10, 15))

        self._footer_linkedin = tk.Label(social, image=self._icon_linkedin,
                        bg="#0a0a12", cursor="hand2")
        self._footer_linkedin.pack(side=tk.LEFT, padx=(0, 8))
        self._footer_linkedin.bind("<Button-1>", lambda e: webbrowser.open(
            "https://fr.linkedin.com/in/timoth%C3%A9e-grollier-dev"))
        self._footer_linkedin.bind("<Enter>", lambda e: self._footer_linkedin.configure(image=self._icon_linkedin_hover))
        self._footer_linkedin.bind("<Leave>", lambda e: self._footer_linkedin.configure(image=self._icon_linkedin))

        self._footer_website = tk.Label(social, image=self._icon_website,
                        bg="#0a0a12", cursor="hand2")
        self._footer_website.pack(side=tk.LEFT)
        self._footer_website.bind("<Button-1>", lambda e: webbrowser.open(
            "https://timotheegrollier.github.io/"))
        self._footer_website.bind("<Enter>", lambda e: self._footer_website.configure(image=self._icon_website_hover))
        self._footer_website.bind("<Leave>", lambda e: self._footer_website.configure(image=self._icon_website))

        # Keyboard shortcuts
        self.root.bind("<Control-h>", self._toggle_export_popover)
        self.root.bind("<Control-H>", self._toggle_export_popover)

    def _preset_changed(self, event=None):
        """Update resolution and FPS when preset changes."""
        from quality_presets import get_preset
        preset = get_preset(self.selected_preset.get())
        self.resolution.set(preset['resolution'])
        self.fps.set(preset['fps'])
        self.status_var.set(f"Préglage: {preset['name']}")

    def _palette_changed(self, event=None):
        """Apply palette changes to the live effect when playback is running."""
        if self.effect_manager:
            self.effect_manager.change_palette(self.selected_color.get())
            self.status_var.set(f"Palette: {self.selected_color.get()}")

    def _effect_changed(self, event=None):
        """Apply effect changes to the live preview."""
        if self.effect_manager:
            self.effect_manager.change_effect(self._get_effect_key())
            self.effect_manager.set_background_image(self.background_image.get() or None)
            self.status_var.set(f"Effet: {self.selected_effect.get()}")
    
    def _open_file(self):
        """Open file dialog to select audio file from input directory."""
        filetypes = [
            ('Fichiers audio', '*.mp3 *.wav *.flac *.ogg *.aac'),
            ('Tous les fichiers', '*.*')
        ]
        
        initial_dir = self._default_browse_dir()
        
        filename = FileDialog.show(
            self.root,
            mode="open",
            title="Sélectionner un fichier audio",
            initial_dir=initial_dir,
            filetypes=filetypes
        )
        
        if filename:
            self.audio_file.set(filename)
            self.status_var.set(f"Fichier chargé: {os.path.basename(filename)}")

    def _open_background_file(self):
        """Open file dialog to select an image background for preview and export."""
        filetypes = [
            ('Images', '*.png *.jpg *.jpeg *.webp *.bmp'),
            ('Tous les fichiers', '*.*')
        ]
        filename = FileDialog.show(
            self.root,
            mode="open",
            title="Sélectionner une image de fond",
            initial_dir=self._user_home_dir(),
            filetypes=filetypes
        )
        if filename:
            self.background_image.set(filename)
            if self.effect_manager:
                self.effect_manager.set_background_image(filename)
            self.status_var.set(f"Fond: {os.path.basename(filename)}")

    def _on_opacity_change(self, val):
        """Update background opacity in real-time from slider."""
        opacity = float(val) / 100.0
        self._opacity_label.configure(text=f"{int(float(val)):.0f}%")
        if self.effect_manager:
            self.effect_manager.set_background_opacity(opacity)

    def _remove_background(self):
        """Clear the background image from preview and export."""
        self.background_image.set("")
        if self.effect_manager:
            self.effect_manager.set_background_image(None)
        self.status_var.set("Fond retiré")

    def _get_effect_key(self):
        """Map GUI labels to internal effect identifiers."""
        effect_name_map = {
            "Trance Scope": "trance_scope",
            "Neon Equalizer": "neon_equalizer",
            "Psychedelic Plasma": "psychedelic_plasma",
            "3D Cyber Tunnel": "3d_cyber_tunnel"
        }
        return effect_name_map.get(self.selected_effect.get(), "trance_scope")

    def _toggle_playback(self):
        """Toggle playback."""
        if not self.audio_file.get():
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier audio d'abord.")
            return
        
        if self.is_playing.get():
            self._stop_playback()
        else:
            self._start_playback()

    def _start_playback(self):
        """Start playback and preview."""
        self.is_playing.set(True)
        self._is_playing_event.set()
        
        # Stop existing thread if any
        if self.playback_thread and self.playback_thread.is_alive():
            self._stop_playback()
        
        # Initialize analyzer (RAM-efficient streaming mode)
        try:
            from audio.analyzer import AudioAnalyzer
            self.analyzer = AudioAnalyzer(self.audio_file.get(), load_file=False)
        except Exception as e:
            self.status_var.set(f"Erreur: {str(e)}")
            self.is_playing.set(False)
            self._is_playing_event.clear()
            return
        
        # Initialize audio player
        try:
            from audio.player import AudioPlayer
            self.audio_player = AudioPlayer(
                sample_rate=self.analyzer.sample_rate,
                chunk_size=self.analyzer.chunk_size,
                channels=2
            )
            # Démarrer la lecture en flux direct depuis le fichier
            self.audio_player.start_from_file(self.audio_file.get(), loop=self.analyzer.loop, analyzer=self.analyzer)
        except Exception as e:
            import traceback
            print(f"[MAIN] AudioPlayer init FAILED: {e}", file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
            self.status_var.set(f"Erreur audio: {str(e)}")
            self.audio_player = None
        
        # Détecter le renderer à utiliser
        self._has_pygame = False
        try:
            import os as _os
            _os.environ['SDL_VIDEODRIVER'] = 'dummy'
            _os.environ['SDL_AUDIODRIVER'] = 'dummy'
            import pygame as _pg
            if not _pg.get_init():
                _pg.init()
            self._has_pygame = True
        except ImportError:
            self._has_pygame = False
        except Exception:
            self._has_pygame = False
        
        # Créer le renderer à la taille exacte du canvas preview (pas de resize)
        try:
            pw = max(self.preview.winfo_width(), 200)
            ph = max(self.preview.winfo_height(), 100)
            self._preview_render_size = (pw, ph)

            if self._has_pygame:
                from renderer.headless_renderer import HeadlessRenderer
                self.preview_renderer = HeadlessRenderer(
                    width=pw,
                    height=ph,
                    fps=self.fps.get()
                )
                self.preview_renderer.init()
            else:
                from renderer.array_renderer import ArrayRenderer
                self.preview_renderer = ArrayRenderer(
                    width=pw,
                    height=ph,
                    fps=self.fps.get()
                )
        except Exception as e:
            self.status_var.set(f"Erreur: {str(e)}")
            self.is_playing.set(False)
            self._is_playing_event.clear()
            return
        
        # Create effect manager with reduced resolution
        try:
            from effects.manager import EffectManager
            effect_key = self._get_effect_key()
            
            self.effect_manager = EffectManager(
                analyzer=self.analyzer,
                renderer=self.preview_renderer,
                effect_type=effect_key,
                color_palette=self.selected_color.get(),
                background_image=self.background_image.get() or None
            )
            self.effect_manager.init()
        except Exception as e:
            self.status_var.set(f"Erreur: {str(e)}")
            self.is_playing.set(False)
            self._is_playing_event.clear()
            return
        
        # Reset frame skipping
        self._frame_skip_counter = 0
        self._frame_skip_threshold = 0
        self._frame_times = []
        
        # Start playback in a separate thread
        self.playback_thread = threading.Thread(
            target=self._playback_loop,
            daemon=True
        )
        self.playback_thread.start()
        
        self.status_var.set("Lecture en cours...")

    def _playback_loop(self):
        """Playback loop for preview."""
        try:
            self.analyzer.start_stream()
            self.preview_renderer.init()

            iteration = 0
            try:
                from ui.log_display import log_message
                log_message("Playback: Boucle de lecture démarrée")
            except:
                pass

            while self._is_playing_event.is_set():
                iteration += 1

                if not self.preview_renderer.handle_events():
                    self._is_playing_event.clear()
                    break

                delta_time = self.preview_renderer.clock.tick(self.fps.get()) / 1000.0

                # Vérifier si le canvas a changé de taille → recréer l'effet
                pw = max(self.preview.winfo_width(), 200)
                ph = max(self.preview.winfo_height(), 100)
                if (pw, ph) != getattr(self, '_preview_render_size', (0, 0)):
                    try:
                        from effects.manager import EffectManager
                        effect_key = self._get_effect_key()
                        self.preview_renderer.width = pw
                        self.preview_renderer.height = ph
                        self.effect_manager = EffectManager(
                            analyzer=self.analyzer,
                            renderer=self.preview_renderer,
                            effect_type=effect_key,
                            color_palette=self.selected_color.get(),
                background_image=self.background_image.get() or None,
                background_opacity=self.opacity_var.get() / 100.0
            )
                        self.effect_manager.init()
                        self._preview_render_size = (pw, ph)
                    except Exception:
                        pass

                if not hasattr(self, 'audio_player') or self.audio_player is None or not self.audio_player.is_playing:
                    break

                chunk = self.analyzer.get_next_chunk()
                if chunk is None:
                    break

                audio_data = self.analyzer.analyze_chunk(chunk)

                # Saut de frame adaptatif si le rendu est trop lent
                target_frame_time = 1.0 / max(self.fps.get(), 1)
                if delta_time > target_frame_time * 1.5:
                    self._frame_skip_threshold = min(3, self._frame_skip_threshold + 1)
                elif delta_time < target_frame_time * 0.8:
                    self._frame_skip_threshold = max(0, self._frame_skip_threshold - 1)

                self._frame_skip_counter += 1
                if self._frame_skip_counter <= self._frame_skip_threshold:
                    self.effect_manager.current_effect.update(audio_data, delta_time)
                    continue
                self._frame_skip_counter = 0

                self.effect_manager.current_effect.update(audio_data, delta_time)

                # Rendu via render_to_array() (identique à l'export)
                arr = self.effect_manager.current_effect.render_to_array()
                frame = self._capture_frame(arr)

                if frame is not None:
                    with self._frame_lock:
                        self._pending_frame = frame
                    self.root.after(0, self._update_preview_from_pending)

                self.preview_renderer.present()

            try:
                from ui.log_display import log_message
                log_message(f"Playback: Boucle terminée après {iteration} itérations")
            except:
                pass

        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda em=error_msg: self.status_var.set(f"Erreur: {em}"))
        finally:
            if hasattr(self, 'audio_player') and self.audio_player:
                try:
                    self.audio_player.cleanup()
                except Exception:
                    pass
            if hasattr(self, 'analyzer') and self.analyzer:
                self.analyzer.cleanup()
            if hasattr(self, 'preview_renderer') and self.preview_renderer:
                self.preview_renderer.cleanup()
            self.is_playing.set(False)
            self._is_playing_event.clear()
            self.root.after(0, lambda: self.status_var.set("Lecture arrêtée"))

    def _update_preview_from_pending(self):
        """Affiche l'image dans le canvas (thread principal). Resize LANCZOS si besoin."""
        from PIL import Image, ImageTk

        with self._frame_lock:
            pil_img = self._pending_frame
            self._pending_frame = None

        if pil_img is None:
            return

        pw, ph = self.preview.winfo_width(), self.preview.winfo_height()
        if pw > 10 and ph > 10 and (pw, ph) != pil_img.size:
            pil_img = pil_img.resize((pw, ph), Image.LANCZOS)
        self.preview.update_image(ImageTk.PhotoImage(pil_img))

    def _capture_frame(self, arr):
        """
        Convertit un frame numpy en PIL Image (appelé depuis le thread de rendu).
        Le redimensionnement est fait dans _update_preview_from_pending (thread principal).
        """
        from PIL import Image

        if arr is not None and len(arr.shape) == 3 and arr.shape[0] > 0 and arr.shape[1] > 0:
            return Image.fromarray(arr)
        return None

    def _stop_playback(self):
        """Stop playback."""
        self.is_playing.set(False)
        self._is_playing_event.clear()
        
        # Arrêter le lecteur audio en premier pour libérer les tubes/pipes bloqués
        if hasattr(self, 'audio_player') and self.audio_player:
            try:
                self.audio_player.cleanup()
            except Exception:
                pass
        
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=0.2)
            if self.playback_thread.is_alive():
                import ctypes
                try:
                    thread_id = self.playback_thread.ident
                    if thread_id:
                        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), ctypes.py_object(SystemExit))
                        if res == 0:
                            pass
                        elif res != 1:
                            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), ctypes.c_long(0))
                except Exception as e:
                    print(f"Warning: Impossible d'arrêter le thread proprement: {e}")
        
        if hasattr(self, 'analyzer') and self.analyzer:
            self.analyzer.cleanup()
        if hasattr(self, 'preview_renderer') and self.preview_renderer:
            self.preview_renderer.cleanup()
        
        self.preview.clear()
        self.status_var.set("Lecture arrêtée")

    def _show_export_popover(self):
        """Place the export popover at bottom-right of the preview canvas."""
        if self.export_popover_hidden:
            return
        self._export_popover.pack(side=tk.BOTTOM, anchor=tk.SE, padx=6, pady=6)

    def _hide_export_popover(self):
        """Hide the export popover."""
        self._export_popover.pack_forget()

    def _toggle_export_popover(self, event=None):
        """Toggle export popover visibility and save preference."""
        self.export_popover_hidden = not self.export_popover_hidden
        self._save_ui_preferences()
        if self.export_popover_hidden:
            self._hide_export_popover()
        else:
            if self._export_in_progress:
                self._show_export_popover()

    def _export_video(self):
        """Export video."""
        if not self.audio_file.get():
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier audio d'abord.")
            return
        
        initial_dir = self._default_browse_dir()

        filename = FileDialog.show(
            self.root,
            mode="save",
            title="Enregistrer la vidéo",
            initial_dir=initial_dir,
            defaultextension=".mp4",
            filetypes=[('Fichiers MP4', '*.mp4'), ('Tous les fichiers', '*.*')]
        )
        
        if not filename:
            return
        
        width, height = self._get_resolution()
        
        # Set export in progress flag
        self._export_in_progress = True
        
        try:
            from recorder.video_recorder import VideoRecorder
            from quality_presets import get_preset, build_ffmpeg_cmd
            
            preset = get_preset(self.selected_preset.get())
            
            self.recorder = VideoRecorder(
                audio_file=self.audio_file.get(),
                output_file=filename,
                width=width,
                height=height,
                fps=self.fps.get(),
                effect_type=self._get_effect_key(),
                color_palette=self.selected_color.get(),
                background_image=self.background_image.get() or None
            )
            self.recorder._ffmpeg_cmd = build_ffmpeg_cmd(
                width, height, self.fps.get(), 
                self.audio_file.get(), filename, self.selected_preset.get()
            )
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de la création du recorder: {str(e)}")
            return
        
        # Show export popover
        self._export_popover_label.configure(text="EXPORT EN COURS")
        self._export_popover_pct.configure(text="0%")
        self._export_popover_fill.place(x=0, y=0, width=0, relheight=1.0)
        self._export_popover_close.configure(fg="#555")
        self._show_export_popover()

        self.btn_export.config(state=tk.DISABLED, text="⏳ EXPORT...")
        self.status_var.set(f"Export: {os.path.basename(filename)}")
        self._led_status.configure(fg="#ffaa00")

        try:
            export_thread = threading.Thread(
                target=self._export_loop,
                args=(filename,),
                daemon=True
            )
            export_thread.start()
        except Exception as e:
            self._export_in_progress = False
            raise

    def _show_export_progress(self, current, total):
        pct = (current / total) * 100 if total > 0 else 0
        self.status_var.set(f"EXPORT {current}/{total} ({pct:.0f}%)")
        self._export_popover_label.configure(text=f"EXPORT {current}/{total}")
        w = self._export_popover_track.winfo_width()
        if w > 0:
            self._export_popover_fill.place(x=0, y=0, width=max(1, int(w * pct / 100)), relheight=1.0)
        self._export_popover_pct.configure(text=f"{pct:.0f}%")

    def _export_finished(self, basename=None, error=None):
        self._export_in_progress = False
        self.btn_export.config(state=tk.NORMAL, text="🎥 EXPORTER")
        if error:
            self._led_status.configure(fg="#ff3b3b")
            self.status_var.set(f"ÉCHEC: {error[:60]}")
            self._export_popover_label.configure(text="EXPORT ÉCHOUÉ")
            self._export_popover_pct.configure(text="ERR")
            self._export_popover_close.configure(fg="#ff3b3b")
            self.root.after(5000, lambda: (
                self._hide_export_popover(),
                self._led_status.configure(fg=self.NEON_CYAN)
            ))
        else:
            self._led_status.configure(fg=self.NEON_GREEN)
            self.status_var.set(f"✓ EXPORT TERMINÉ: {basename}")
            w = self._export_popover_track.winfo_width()
            if w > 0:
                self._export_popover_fill.place(x=0, y=0, width=w, relheight=1.0)
            self._export_popover_label.configure(text="✓ EXPORT TERMINÉ")
            self._export_popover_pct.configure(text="100%")
            self.root.after(3000, lambda: (
                self._hide_export_popover(),
                self._led_status.configure(fg=self.NEON_CYAN),
                self.status_var.set("PRÊT")
            ))

    def _export_loop(self, filename):
        """Export loop."""
        try:
            self.recorder.record(
                progress_callback=lambda c, t: self.root.after(0, lambda: self._show_export_progress(c, t))
            )
            basename = os.path.basename(filename)
            self.root.after(0, lambda bn=basename: self._export_finished(bn))
            self.root.after(0, lambda f=filename: messagebox.showinfo("Succès", f"Vidéo exportée vers\n{f}"))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda em=error_msg: self._export_finished(error=em))
            self.root.after(0, lambda em=error_msg: messagebox.showerror("Erreur", f"Échec de l'export:\n{em}"))

    @staticmethod
    def _user_home_dir():
        """Return a reliable user home directory, even inside an AppImage sandbox."""
        for candidate in (os.path.expanduser("~"), os.environ.get("HOME"), os.environ.get("USERPROFILE")):
            if candidate and os.path.isdir(candidate):
                return candidate
        return os.path.dirname(os.path.abspath(__file__))

    def _default_browse_dir(self):
        """Return the default directory for file dialogs.

        When running inside an AppImage (APPDIR set), force user home.
        Otherwise, prefer the project ``input`` folder when it exists,
        falling back to user home.
        """
        if os.environ.get("APPDIR"):
            return self._user_home_dir()
        candidate = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'input')
        return candidate if os.path.isdir(candidate) else self._user_home_dir()

    def _get_resolution(self):
        """Get selected resolution."""
        resolution = self.resolution.get()
        resolutions = {
            '1080p': (1920, 1080),
            '1440p': (2560, 1440),
            '4K': (3840, 2160)
        }
        return resolutions.get(resolution, (1920, 1080))

    def _show_logs(self):
        """Affiche la fenêtre des logs."""
        try:
            from ui.log_display import show_log_window
            log_root = tk.Toplevel(self.root)
            log_root.title("Logs - Visualisateur Psychédélique")
            show_log_window(log_root)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'afficher les logs: {e}")
    
    def run(self):
        """Run the main loop."""
        self.root.mainloop()


# Import PreviewFrame
from ui.preview import PreviewFrame