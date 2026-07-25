"""
Main window for the psychedelic visualizer GUI.
Refactored with tabbed sidebar, theme switching, toast notifications,
pulsing LED, recent files, timecode, volume, and keyboard shortcuts.
"""

import tkinter as tk
from tkinter import messagebox, ttk
import threading
import os
import sys
import time
import json
import webbrowser
from PIL import Image, ImageDraw, ImageTk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from version import __version__
except ImportError:
    __version__ = "0.0.0"

from ui.tab_panel import TabPanel
from ui.tabs.file_tab import FileTab
from ui.tabs.effects_tab import EffectsTab
from ui.tabs.background_tab import BackgroundTab
from ui.tabs.logo_tab import LogoTab
from ui.tabs.export_tab import ExportTab
from ui.tabs.logs_tab import LogsTab, set_global_logs_tab
from ui.preview import PreviewFrame
from ui.toast import ToastManager
from ui.theme import get_theme, THEME_NAMES

try:
    import cv2
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False


class MainWindow:
    """
    Main application window with tabbed sidebar controls.
    Supports dynamic theme switching, toast notifications, and more.
    """

    def __init__(self, root):
        self.root = root
        self._theme_name = tk.StringVar(value="cyberpunk")
        self._theme = get_theme("cyberpunk")

        self.is_playing = tk.BooleanVar(value=False)
        self._is_playing_event = threading.Event()
        self.audio_file = tk.StringVar(value="")
        self.audio_file.trace_add("write", self._audio_file_changed)
        self.selected_effect = tk.StringVar(value="Trance Scope")
        self.selected_color = tk.StringVar(value="psychedelic")
        self.background_image = tk.StringVar(value="")
        self.logo_image = tk.StringVar(value="")
        self.logo_position = tk.StringVar(value="top-right")
        self.logo_x = tk.DoubleVar(value=100)
        self.logo_y = tk.DoubleVar(value=0)
        self.logo_scale = tk.DoubleVar(value=18)
        self.logo_opacity = tk.DoubleVar(value=100)
        self.resolution = tk.StringVar(value="1080p")
        self.fps = tk.IntVar(value=60)
        self.selected_preset = tk.StringVar(value="normal")
        self.opacity_var = tk.DoubleVar(value=72)
        self.volume_var = tk.DoubleVar(value=80)

        # Recent files
        self._recent_files = []
        self._load_recent_files()

        # Audio device — load from config
        saved_device = self._load_audio_device_pref()
        self.audio_device = tk.StringVar(value=saved_device)
        self.audio_device.trace_add("write", self._audio_device_changed)

        self._cleanup_lock = threading.Lock()
        self._cleaned_up = False

        # Playback / export state
        self.playback_thread = None
        self.analyzer = None
        self.preview_renderer = None
        self.effect_manager = None
        self.recorder = None
        self.audio_player = None
        self._export_in_progress = False

        # Frame timing
        self._frame_times = []
        self._preview_render_size = (0, 0)
        self._pending_frame = None
        self._frame_lock = threading.Lock()
        self._ui_frame_interval = 33
        self._fps_counter = 0
        self._fps_last_time = 0.0
        self._fps_display = 0
        self._playback_start_time = 0.0
        self._timecode_str = tk.StringVar(value="00:00.000")

        # Preview border glow animation
        self._glow_direction = 1
        self._glow_intensity = 0.5

        # LED pulse animation
        self._led_pulse = 0.0
        self._led_pulse_dir = 1

        self._setup_ui()
        self._bind_shortcuts()

        # Toast manager
        self.toast = ToastManager(self.root)

    # ── Recent files ───────────────────────────────────────────────────
    def _recent_files_path(self):
        return os.path.join(os.path.expanduser("~"), ".visualize_recent.json")

    def _load_recent_files(self):
        try:
            path = self._recent_files_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._recent_files = data.get("recent", [])[:10]
        except Exception:
            self._recent_files = []

    def _save_recent_file(self, path):
        if path in self._recent_files:
            self._recent_files.remove(path)
        self._recent_files.insert(0, path)
        self._recent_files = self._recent_files[:10]
        try:
            with open(self._recent_files_path(), "w", encoding="utf-8") as f:
                json.dump({"recent": self._recent_files}, f)
        except Exception:
            pass

    # ── Theme application ──────────────────────────────────────────────
    def _apply_theme(self, theme_name="cyberpunk"):
        """Apply a theme consistently to the whole interface."""
        previous_theme = getattr(self, "_theme", None)
        theme = get_theme(theme_name)
        self._theme = theme
        self._theme_name.set(theme_name)

        self.root.configure(bg=theme.bg_dark)
        self._configure_ttk_styles(theme)
        if hasattr(self, "_main_frame"):
            self._recolor_widgets(self._main_frame, theme, previous_theme)

        if hasattr(self, '_footer'):
            self._footer.configure(bg=theme.footer_bg)
        if hasattr(self, '_footer_copyright'):
            self._footer_copyright.configure(bg=theme.footer_bg, fg=theme.footer_fg)

        # Status bar surface
        if hasattr(self, '_led_status'):
            self._led_status.configure(bg=theme.status_bg)

        # Preview border
        if hasattr(self, '_preview_border'):
            self._preview_border.configure(bg=theme.border)
        if hasattr(self, 'preview'):
            self.preview.apply_theme(theme)
        if hasattr(self, '_preview_effect_label'):
            self._preview_effect_label.configure(fg=theme.fg_light)
        if hasattr(self, '_preview_palette_label'):
            self._preview_palette_label.configure(fg=theme.fg_muted)
        if hasattr(self, 'btn_play') and hasattr(self, 'btn_stop'):
            if self.is_playing.get():
                self.btn_play.configure(bg=theme.button_bg, fg=theme.fg_muted)
                self.btn_stop.configure(bg=theme.neon_secondary,
                                        activebackground=theme.button_hover)
            else:
                self.btn_play.configure(bg=theme.neon_accent, fg="#05050a",
                                        activebackground=theme.button_hover)
                self.btn_stop.configure(bg=theme.button_bg,
                                        activebackground=theme.button_hover)

        # Save preference
        self._save_theme_pref(theme_name)

        # Toast notification
        if hasattr(self, 'toast'):
            self.toast.show(f"Theme: {theme.name}", 1.5, "info")

    def _configure_ttk_styles(self, theme):
        """Give native ttk controls the same visual language as Tk widgets."""
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "TCombobox", fieldbackground=theme.input_bg,
            background=theme.input_bg, foreground=theme.fg_light,
            bordercolor=theme.border, lightcolor=theme.border,
            darkcolor=theme.border, arrowcolor=theme.neon_primary,
            padding=(8, 5), relief="flat",
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", theme.input_bg)],
            foreground=[("readonly", theme.fg_light)],
            selectbackground=[("readonly", theme.button_hover)],
            selectforeground=[("readonly", theme.fg_light)],
        )

    def _recolor_widgets(self, widget, theme, previous_theme=None):
        """Recolor legacy Tk widgets while preserving semantic accents."""
        old_to_new_bg = {
            "#09090d": theme.bg_dark, "#12121d": theme.bg_panel,
            "#1b1b2a": theme.bg_card, "#1a1a2e": theme.button_bg,
            "#252538": theme.button_bg, "#252540": theme.button_hover,
            "#35354e": theme.button_hover, "#2a1a2e": theme.button_bg,
            "#3a2a3e": theme.button_hover, "#1a3a1a": theme.button_bg,
            "#05050a": theme.preview_bg, "#0a0a12": theme.footer_bg,
            "#0d0d18": theme.status_bg, "#1c1c30": theme.border,
            "#2a2a3e": theme.border, "#3a1a2a": theme.danger_bg,
            "#14233b": theme.progress_track,
        }
        old_to_new_fg = {
            "#e2e2ee": theme.fg_light, "#85859e": theme.fg_muted,
            "#00e5ff": theme.neon_primary, "#ff007f": theme.neon_secondary,
            "#ff52a2": theme.neon_secondary, "#a2ff8e": theme.neon_accent,
            "#39ff14": theme.neon_accent, "#ffaa00": theme.neon_warn,
            "#ff3b3b": theme.danger_fg, "#ff5b5b": theme.danger_fg,
        }
        if previous_theme:
            old_to_new_bg.update({
                previous_theme.bg_dark: theme.bg_dark,
                previous_theme.bg_panel: theme.bg_panel,
                previous_theme.bg_card: theme.bg_card,
                previous_theme.input_bg: theme.input_bg,
                previous_theme.button_bg: theme.button_bg,
                previous_theme.button_hover: theme.button_hover,
                previous_theme.preview_bg: theme.preview_bg,
                previous_theme.status_bg: theme.status_bg,
                previous_theme.border: theme.border,
                previous_theme.footer_bg: theme.footer_bg,
                previous_theme.danger_bg: theme.danger_bg,
            })
            old_to_new_fg.update({
                previous_theme.fg_light: theme.fg_light,
                previous_theme.fg_muted: theme.fg_muted,
                previous_theme.neon_primary: theme.neon_primary,
                previous_theme.neon_secondary: theme.neon_secondary,
                previous_theme.neon_accent: theme.neon_accent,
                previous_theme.neon_warn: theme.neon_warn,
                previous_theme.danger_fg: theme.danger_fg,
            })

        try:
            for option in ("bg", "background", "highlightbackground", "troughcolor"):
                value = widget.cget(option)
                if value in old_to_new_bg:
                    widget.configure(**{option: old_to_new_bg[value]})
            for option in ("fg", "foreground", "activeforeground", "insertbackground"):
                value = widget.cget(option)
                if value in old_to_new_fg:
                    widget.configure(**{option: old_to_new_fg[value]})
            for option in ("activebackground",):
                value = widget.cget(option)
                if value in old_to_new_bg:
                    widget.configure(**{option: old_to_new_bg[value]})
        except (tk.TclError, TypeError):
            pass

        for child in widget.winfo_children():
            self._recolor_widgets(child, theme, previous_theme)

    def _find_status_frame(self):
        """Find the status bar frame."""
        for child in self.root.winfo_children():
            for sub in child.winfo_children() if hasattr(child, 'winfo_children') else []:
                for s in sub.winfo_children() if hasattr(sub, 'winfo_children') else []:
                    try:
                        if s.cget("bg") in ("#0d0d18", "#111116"):
                            return s
                    except Exception:
                        pass
        return None

    def _save_theme_pref(self, theme_name):
        try:
            path = os.path.join(os.path.expanduser("~"), ".visualize_config.json")
            config = {}
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            config["theme"] = theme_name
            with open(path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass

    def _load_theme_pref(self):
        try:
            path = os.path.join(os.path.expanduser("~"), ".visualize_config.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    return config.get("theme", "cyberpunk")
        except Exception:
            pass
        return "cyberpunk"

    # ── UI Setup ───────────────────────────────────────────────────────
    def _setup_ui(self):
        saved_theme = self._load_theme_pref()
        theme = get_theme(saved_theme)
        self._theme = theme
        self._theme_name.set(saved_theme)

        T = theme  # shorthand

        self.root.title(f"Visualisateur Psychédélique {__version__}")
        self.root.geometry("1360x820")
        self.root.minsize(1120, 720)
        self.root.configure(bg=T.bg_dark)

        # ── Main container ──
        self._main_frame = tk.Frame(self.root, bg=T.bg_dark, padx=18, pady=16)
        main_frame = self._main_frame
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ── LEFT: Tabbed sidebar ──
        left_panel = tk.Frame(main_frame, bg=T.bg_panel, width=320,
                              padx=0, pady=0, bd=1, relief="solid",
                              highlightbackground=T.border,
                              highlightcolor=T.border)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        left_panel.pack_propagate(False)

        # Branding header
        header = tk.Frame(left_panel, bg=T.bg_panel)
        header.pack(fill=tk.X, padx=14, pady=(14, 4))

        title_label = tk.Label(header, text="PSYCHEDELIC",
                               font=('Helvetica', 18, 'bold'),
                               fg=T.neon_primary, bg=T.bg_panel)
        title_label.pack(anchor=tk.W)

        sub_label = tk.Label(header, text=f"AUDIO VISUALIZER  •  v{__version__}",
                             font=('Helvetica', 8, 'bold'),
                             fg=T.neon_secondary, bg=T.bg_panel)
        sub_label.pack(anchor=tk.W, pady=(0, 0))

        # Theme selector
        theme_frame = tk.Frame(header, bg=T.bg_panel)
        theme_frame.pack(fill=tk.X, pady=(6, 0))

        theme_lbl = tk.Label(theme_frame, text="APPARENCE",
                             font=('Helvetica', 7, 'bold'),
                             fg=T.fg_muted, bg=T.bg_panel)
        theme_lbl.pack(side=tk.LEFT, padx=(0, 4))

        theme_combo = ttk.Combobox(theme_frame, textvariable=self._theme_name,
                                   values=THEME_NAMES, state='readonly',
                                   width=14, font=('Helvetica', 8))
        theme_combo.pack(side=tk.RIGHT)
        theme_combo.bind('<<ComboboxSelected>>',
                         lambda e: self._apply_theme(self._theme_name.get()))

        # Separator
        sep = tk.Frame(left_panel, bg=T.border, height=1)
        sep.pack(fill=tk.X, padx=10, pady=(4, 4))

        # Tab panel
        self.tab_panel = TabPanel(left_panel)
        self.tab_panel.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Create tabs
        self._file_tab = self.tab_panel.add_tab(
            "🎵 FICHIER",
            FileTab(self.tab_panel, self.audio_file,
                    status_callback=self._set_status,
                    audio_device_var=self.audio_device)
        )
        self._effects_tab = self.tab_panel.add_tab(
            "✨ EFFETS",
            EffectsTab(self.tab_panel, self.selected_effect, self.selected_color,
                       effect_changed_cb=self._effect_changed,
                       palette_changed_cb=self._palette_changed)
        )
        self._bg_tab = self.tab_panel.add_tab(
            "🖼 FOND",
            BackgroundTab(self.tab_panel, self.background_image, self.opacity_var,
                          status_callback=self._set_status)
        )
        self._logo_tab = self.tab_panel.add_tab(
            "◇ LOGO",
            LogoTab(
                self.tab_panel, self.logo_image, self.logo_position,
                self.logo_x, self.logo_y, self.logo_scale, self.logo_opacity,
                change_callback=self._logo_changed,
                status_callback=self._set_status,
            )
        )
        self._export_tab = self.tab_panel.add_tab(
            "📤 EXPORT",
            ExportTab(self.tab_panel, self.audio_file, self.resolution, self.fps,
                      self.selected_preset, self.selected_effect, self.selected_color,
                      self.background_image,
                      export_callback=self._on_export_request,
                      cancel_callback=self._on_export_cancel,
                      status_callback=self._set_status)
        )
        self._logs_tab = self.tab_panel.add_tab(
            "📋 LOGS",
            LogsTab(self.tab_panel)
        )
        set_global_logs_tab(self._logs_tab)

        # ── Transport controls ──
        btn_container = tk.Frame(left_panel, bg=T.bg_panel)
        btn_container.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(4, 12))

        transport_row = tk.Frame(btn_container, bg=T.bg_panel)
        transport_row.pack(fill=tk.X, pady=(0, 6))

        self.btn_play = tk.Button(
            transport_row, text="▶  LECTURE",
            command=self._toggle_playback,
            bg=T.neon_accent, fg="#05050a",
            activebackground="#a2ff8e", activeforeground="#05050a",
            bd=0, pady=8, font=('Helvetica', 9, 'bold'), cursor="hand2",
            relief="flat",
        )
        self.btn_play.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self._add_hover(self.btn_play, "#a2ff8e", T.neon_accent)

        self.btn_stop = tk.Button(
            transport_row, text="■  ARRÊTER",
            command=self._stop_playback,
            bg="#2a1a2e", fg=T.fg_muted,
            activebackground="#3a2a3e", activeforeground=T.fg_light,
            bd=0, pady=8, font=('Helvetica', 9, 'bold'), cursor="hand2",
            relief="flat",
        )
        self.btn_stop.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        self._add_hover(self.btn_stop, "#3a2a3e", "#2a1a2e")

        # Volume slider
        vol_frame = tk.Frame(btn_container, bg=T.bg_panel)
        vol_frame.pack(fill=tk.X, pady=(8, 0))

        vol_icon = tk.Label(vol_frame, text="🔊", font=('Helvetica', 8),
                            bg=T.bg_panel, fg=T.fg_muted)
        vol_icon.pack(side=tk.LEFT, padx=(0, 6))

        self.volume_slider = tk.Scale(
            vol_frame, from_=0, to=100, orient=tk.HORIZONTAL,
            variable=self.volume_var, command=self._on_volume_change,
            showvalue=False, bg=T.bg_panel, fg=T.fg_light,
            highlightthickness=0, bd=0, troughcolor="#1a1a2e",
            activebackground=T.neon_primary, sliderlength=12, length=160,
        )
        self.volume_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._volume_label = tk.Label(vol_frame, text="80%",
                                      font=('Courier', 7, 'bold'),
                                      fg=T.fg_muted, bg=T.bg_panel,
                                      width=3, anchor=tk.E)
        self._volume_label.pack(side=tk.RIGHT, padx=(4, 0))

        shortcut_hint = tk.Label(
            btn_container, text="Espace lecture  •  Ctrl+E export  •  Échap arrêt",
            font=('Helvetica', 7), fg=T.fg_muted, bg=T.bg_panel,
        )
        shortcut_hint.pack(anchor=tk.W, pady=(6, 0))

        # ── RIGHT: Preview + Status ──
        right_panel = tk.Frame(main_frame, bg=T.bg_dark)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Preview header
        preview_header = tk.Frame(right_panel, bg=T.bg_dark)
        preview_header.pack(fill=tk.X, pady=(0, 8))

        preview_title = tk.Label(preview_header, text="APERÇU EN DIRECT",
                                 font=('Helvetica', 10, 'bold'),
                                 fg=T.neon_primary, bg=T.bg_dark)
        preview_title.pack(side=tk.LEFT)

        self._preview_state_label = tk.Label(
            preview_header, text="● PRÊT", font=('Helvetica', 7, 'bold'),
            fg=T.fg_muted, bg=T.bg_dark, padx=10,
        )
        self._preview_state_label.pack(side=tk.LEFT, padx=(12, 0))

        preview_meta = tk.Frame(preview_header, bg=T.bg_dark)
        preview_meta.pack(side=tk.RIGHT)
        self._preview_effect_label = tk.Label(
            preview_meta, textvariable=self.selected_effect,
            font=('Helvetica', 8, 'bold'), fg=T.fg_light, bg=T.bg_dark,
        )
        self._preview_effect_label.pack(side=tk.LEFT, padx=(0, 10))
        self._preview_palette_label = tk.Label(
            preview_meta, textvariable=self.selected_color,
            font=('Helvetica', 8), fg=T.fg_muted, bg=T.bg_dark,
        )
        self._preview_palette_label.pack(side=tk.LEFT, padx=(0, 10))

        timecode_label = tk.Label(preview_header, textvariable=self._timecode_str,
                                  font=('Courier', 9, 'bold'),
                                  fg=T.fg_muted, bg=T.bg_dark, padx=8)
        timecode_label.pack(side=tk.RIGHT)

        self._fps_display_label = tk.Label(
            preview_header, text="-- FPS",
            font=('Courier', 8, 'bold'), fg=T.fg_muted,
            bg=T.bg_dark, padx=8,
        )
        self._fps_display_label.pack(side=tk.RIGHT)

        # Preview with animated neon border
        self._preview_border = tk.Frame(right_panel, bg=T.border, bd=1,
                                        highlightthickness=0)
        self._preview_border.pack(fill=tk.BOTH, expand=True)

        self.preview = PreviewFrame(self._preview_border, bd=0,
                                    highlightthickness=0,
                                    on_click_empty=self._on_preview_click)
        self.preview.pack(fill=tk.BOTH, expand=True)

        self._animate_border()

        # ── Status bar ──
        self.status_var = tk.StringVar(value="PRÊT")
        status_frame = tk.Frame(right_panel, bg=T.status_bg, height=30, bd=0,
                                highlightthickness=1,
                                highlightbackground=T.border)
        self._status_frame = status_frame
        status_frame.pack(fill=tk.X, pady=(10, 0))

        self._led_status = tk.Label(status_frame, text="●",
                                    font=('Helvetica', 9),
                                    fg=T.neon_primary, bg=T.status_bg, padx=6)
        self._led_status.pack(side=tk.LEFT)

        def update_led(*args):
            theme = self._theme
            if self.is_playing.get():
                self._led_status.configure(fg=theme.neon_accent)
                if hasattr(self, '_preview_state_label'):
                    self._preview_state_label.configure(
                        text="● EN LECTURE", fg=theme.neon_accent
                    )
                self.btn_play.configure(bg=theme.button_bg, fg=theme.fg_muted,
                                        text="▶  EN COURS")
                self.btn_stop.configure(bg=theme.neon_secondary, fg="#ffffff",
                                        activebackground=theme.button_hover)
            else:
                self._led_status.configure(fg=theme.neon_primary)
                if hasattr(self, '_preview_state_label'):
                    self._preview_state_label.configure(
                        text="● PRÊT", fg=theme.fg_muted
                    )
                self.btn_play.configure(bg=theme.neon_accent, fg="#05050a",
                                        text="▶  LECTURE")
                self.btn_stop.configure(bg=theme.button_bg, fg=theme.fg_muted,
                                        activebackground=theme.button_hover)
            self._update_action_states()
        self.is_playing.trace_add("write", update_led)

        status_label = tk.Label(status_frame, textvariable=self.status_var,
                                font=('Helvetica', 8, 'bold'),
                                fg=T.neon_primary, bg=T.status_bg,
                                anchor=tk.W)
        self._status_label = status_label
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        # ── Footer ──
        self._footer = tk.Frame(self.root, bg=T.footer_bg, height=42)
        self._footer.pack(side=tk.BOTTOM, fill=tk.X)
        self._footer.pack_propagate(False)

        footer_divider = tk.Frame(self._footer, bg=T.border, height=1, bd=0)
        footer_divider.pack(side=tk.TOP, fill=tk.X)

        self._footer_copyright = tk.Label(
            self._footer, text="© 2026 Timothée Grollier",
            font=('Helvetica', 7, 'bold'), fg=T.footer_fg, bg=T.footer_bg,
            anchor=tk.W, padx=16,
        )
        self._footer_copyright.pack(side=tk.LEFT, fill=tk.Y)

        # Social icons
        assets_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets"
        )
        icon_size = 34
        self._icon_linkedin = self._load_icon(
            os.path.join(assets_dir, "linkedin.png"), icon_size
        )
        self._icon_linkedin_hover = self._load_icon(
            os.path.join(assets_dir, "linkedin_hover.png"), icon_size
        )
        self._icon_website = self._load_icon(
            os.path.join(assets_dir, "website.png"), icon_size
        )
        self._icon_website_hover = self._load_icon(
            os.path.join(assets_dir, "website_hover.png"), icon_size
        )

        social = tk.Frame(self._footer, bg=T.footer_bg)
        social.pack(side=tk.RIGHT, padx=10, pady=0, fill=tk.Y)

        def _make_social(parent, icon, icon_hover, url, tooltip):
            lbl = tk.Label(parent, image=icon, bg=T.footer_bg,
                           cursor="hand2", padx=4)
            lbl.pack(side=tk.LEFT)
            lbl.bind("<Button-1>", lambda e: webbrowser.open(url))
            lbl.bind("<Enter>", lambda e: (
                lbl.configure(image=icon_hover),
                lbl.configure(bg=self._theme.button_hover)
            ))
            lbl.bind("<Leave>", lambda e: (
                lbl.configure(image=icon), lbl.configure(bg=self._theme.footer_bg)
            ))
            return lbl

        self._footer_linkedin = _make_social(
            social, self._icon_linkedin, self._icon_linkedin_hover,
            "https://fr.linkedin.com/in/timoth%C3%A9e-grollier-dev", "LinkedIn"
        )
        self._footer_website = _make_social(
            social, self._icon_website, self._icon_website_hover,
            "https://timotheegrollier.github.io/", "Site web"
        )

        # Apply saved theme
        self._apply_theme(saved_theme)
        self._update_action_states()

    # ── Keyboard shortcuts ─────────────────────────────────────────────
    def _bind_shortcuts(self):
        self.root.bind("<space>", lambda e: self._toggle_playback())
        self.root.bind("<Control-p>", lambda e: self._toggle_playback())
        self.root.bind("<Control-s>", lambda e: self._stop_playback())
        self.root.bind("<Control-e>", lambda e: self._export_tab.btn_export.invoke())
        self.root.bind("<Escape>", lambda e: self._stop_playback())

    # ── Volume control ─────────────────────────────────────────────────
    def _on_volume_change(self, val):
        pct = int(float(val))
        self._volume_label.configure(text=f"{pct}%")
        if hasattr(self, 'audio_player') and self.audio_player:
            try:
                self.audio_player.set_volume(pct / 100.0)
            except Exception:
                pass

    def _audio_file_changed(self, *args):
        """Keep primary actions honest: no audio means nothing to play/export."""
        self._update_action_states()

    def _update_action_states(self):
        """Enable only actions that are meaningful in the current state."""
        has_audio = bool(
            self.audio_file.get() and os.path.isfile(self.audio_file.get())
        )
        is_playing = bool(self.is_playing.get())
        if hasattr(self, 'btn_play'):
            self.btn_play.configure(
                state=tk.NORMAL if has_audio or is_playing else tk.DISABLED
            )
        if hasattr(self, 'btn_stop'):
            self.btn_stop.configure(state=tk.NORMAL if is_playing else tk.DISABLED)
        if hasattr(self, '_export_tab') and not self._export_in_progress:
            self._export_tab.set_export_button_state(has_audio)

    # ── Preview border glow animation ──────────────────────────────────
    def _animate_border(self):
        if self.is_playing.get():
            self._glow_intensity += 0.03 * self._glow_direction
            if self._glow_intensity >= 1.0:
                self._glow_direction = -1
            elif self._glow_intensity <= 0.3:
                self._glow_direction = 1

            c0 = self._theme.neon_primary
            c1 = self._theme.neon_accent
            r0, g0, b0 = int(c0[1:3], 16), int(c0[3:5], 16), int(c0[5:7], 16)
            r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
            i = self._glow_intensity
            r = int(r0 + (r1 - r0) * i)
            g = int(g0 + (g1 - g0) * i)
            b = int(b0 + (b1 - b0) * i)
            colour = f"#{r:02x}{g:02x}{b:02x}"
            self._preview_border.configure(bg=colour)
        else:
            self._preview_border.configure(bg=self._theme.border)

        self.root.after(50, self._animate_border)

    # ── Pulsing LED ────────────────────────────────────────────────────
    def _animate_led(self):
        """Pulse the status LED when playing."""
        if self.is_playing.get():
            self._led_pulse += 0.05 * self._led_pulse_dir
            if self._led_pulse >= 1.0:
                self._led_pulse_dir = -1
            elif self._led_pulse <= 0.3:
                self._led_pulse_dir = 1

            c = self._theme.neon_accent
            r, g, b = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
            r = int(r * self._led_pulse)
            g = int(g * self._led_pulse)
            b = int(b * self._led_pulse)
            colour = f"#{r:02x}{g:02x}{b:02x}"
            self._led_status.configure(fg=colour)

        self.root.after(80, self._animate_led)

    # ── Helpers ────────────────────────────────────────────────────────
    def _load_icon(self, path, size=28):
        try:
            img = Image.open(path)
            img = img.resize((size, size), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except (FileNotFoundError, OSError, IOError):
            img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            cx = cy = size // 2
            r = size // 2 - 2
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=self._theme.neon_primary)
            return ImageTk.PhotoImage(img)

    def _add_hover(self, widget, hover_bg, normal_bg):
        widget.bind("<Enter>", lambda e: widget.configure(bg=hover_bg))
        widget.bind("<Leave>", lambda e: widget.configure(bg=normal_bg))

    def _set_status(self, message):
        self.status_var.set(message)

    def _get_effect_key(self):
        effect_name_map = {
            "Trance Scope": "trance_scope",
            "Neon Equalizer": "neon_equalizer",
            "Psychedelic Plasma": "psychedelic_plasma",
            "3D Cyber Tunnel": "3d_cyber_tunnel",
            "Bars": "bars",
            "Circles": "circles",
            "Particles": "particles",
            "Wave": "wave",
            "Spectrum": "spectrum",
        }
        return effect_name_map.get(self.selected_effect.get(), "trance_scope")

    def _get_resolution(self):
        resolutions = {
            '1080p': (1920, 1080),
            '1440p': (2560, 1440),
            '4K': (3840, 2160),
        }
        return resolutions.get(self.resolution.get(), (1920, 1080))

    # ── Audio device persistence ──────────────────────────────────────
    def _config_path(self):
        return os.path.join(os.path.expanduser("~"), ".visualize_config.json")

    def _load_audio_device_pref(self):
        try:
            path = self._config_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    return config.get("audio_device", "")
        except Exception:
            pass
        return ""

    def _save_audio_device_pref(self, device_str):
        try:
            path = self._config_path()
            config = {}
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            config["audio_device"] = device_str
            with open(path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass

    def _audio_device_changed(self, *args):
        device_str = self.audio_device.get()
        self._save_audio_device_pref(device_str)

    def _resolve_device_id(self):
        """Convert audio_device string (format: 'index: name (api)') to integer device index.
        Returns None if the saved device is no longer available (fallback to system default)."""
        device_str = self.audio_device.get().strip()
        if not device_str:
            return None
        
        # Parse "index: name (api)" format
        saved_index = None
        if ':' in device_str:
            try:
                saved_index = int(device_str.split(':')[0].strip())
            except (ValueError, IndexError):
                pass
        elif device_str.isdigit():
            saved_index = int(device_str)
        
        # If we have an index, verify it still exists
        if saved_index is not None:
            from audio.player import AudioPlayer
            devices = AudioPlayer.list_devices()
            available_indices = [d['index'] for d in devices]
            
            if saved_index in available_indices:
                return saved_index
            
            # Device no longer available - fallback to system default
            self._set_status("Périphérique audio indisponible, utilisation du défaut système")
            self.toast.show("Périphérique audio débranché, retour au défaut", 2.0, "warning")
            
            # Clear the saved preference
            self.audio_device.set("")
            self._save_audio_device_pref("")
            
            return None
        
        # Otherwise try to match device name
        from audio.player import AudioPlayer
        for dev in AudioPlayer.list_devices():
            if device_str in dev['name']:
                return dev['index']
        return None

    # ── Effect / Palette callbacks ─────────────────────────────────────
    def _effect_changed(self, event=None):
        if self.effect_manager:
            self.effect_manager.change_effect(self._get_effect_key())
            self.effect_manager.set_background_image(
                self.background_image.get() or None
            )
            self._set_status(f"Effet: {self.selected_effect.get()}")

    def _palette_changed(self, event=None):
        if self.effect_manager:
            self.effect_manager.change_palette(self.selected_color.get())
            self._set_status(f"Palette: {self.selected_color.get()}")

    def _logo_changed(self):
        """Apply logo controls immediately when playback is running."""
        if not self.effect_manager:
            return
        self.effect_manager.set_logo_image(self.logo_image.get() or None)
        self.effect_manager.set_logo_position(self.logo_position.get())
        self.effect_manager.set_logo_coordinates(
            self.logo_x.get() / 100.0,
            self.logo_y.get() / 100.0,
        )
        self.effect_manager.set_logo_scale(self.logo_scale.get() / 100.0)
        self.effect_manager.set_logo_opacity(self.logo_opacity.get() / 100.0)

    # ── Preview interaction ────────────────────────────────────────────
    def _on_preview_click(self):
        """Open the file selection dialog when preview is clicked while empty."""
        self._file_tab._open_file()

    # ── Playback ───────────────────────────────────────────────────────
    def _toggle_playback(self):
        if not self.audio_file.get():
            messagebox.showerror("Erreur",
                                 "Veuillez sélectionner un fichier audio d'abord.")
            return
        if self.is_playing.get():
            self._stop_playback()
        else:
            self._start_playback()

    def _start_playback(self):
        self.is_playing.set(True)
        self._is_playing_event.set()

        if self.playback_thread and self.playback_thread.is_alive():
            self._stop_playback()

        # Save to recent files
        self._save_recent_file(self.audio_file.get())

        # Init analyzer
        try:
            from audio.analyzer import AudioAnalyzer
            self.analyzer = AudioAnalyzer(self.audio_file.get(), load_file=False)
        except Exception as e:
            self._set_status(f"Erreur: {str(e)}")
            self.is_playing.set(False)
            self._is_playing_event.clear()
            return

        # Init audio player
        try:
            from audio.player import AudioPlayer
            device_id = self._resolve_device_id()
            self.audio_player = AudioPlayer(
                sample_rate=self.analyzer.sample_rate,
                chunk_size=self.analyzer.chunk_size,
                channels=2,
                device_id=device_id,
            )
            self.audio_player.start_from_file(
                self.audio_file.get(), loop=self.analyzer.loop,
                analyzer=self.analyzer
            )
            try:
                self.audio_player.set_volume(self.volume_var.get() / 100.0)
            except AttributeError:
                pass  # AudioPlayer may not support set_volume
        except Exception as e:
            import traceback
            print(f"[MAIN] AudioPlayer init FAILED: {e}", file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
            self._set_status(f"Erreur audio: {str(e)}")
            self.audio_player = None

        # Detect renderer
        self._has_pygame = False
        try:
            import os as _os
            _os.environ['SDL_VIDEODRIVER'] = 'dummy'
            _os.environ['SDL_AUDIODRIVER'] = 'dummy'
            import pygame as _pg
            if not _pg.get_init():
                _pg.init()
            self._has_pygame = True
        except (ImportError, Exception):
            self._has_pygame = False

        # Create renderer
        try:
            pw, ph = self.preview.get_display_size()
            self._preview_render_size = (pw, ph)

            if self._has_pygame:
                from renderer.headless_renderer import HeadlessRenderer
                self.preview_renderer = HeadlessRenderer(
                    width=pw, height=ph, fps=self.fps.get()
                )
                self.preview_renderer.init()
            else:
                from renderer.array_renderer import ArrayRenderer
                self.preview_renderer = ArrayRenderer(
                    width=pw, height=ph, fps=self.fps.get()
                )
        except Exception as e:
            self._set_status(f"Erreur: {str(e)}")
            self.is_playing.set(False)
            self._is_playing_event.clear()
            return

        # Create effect manager
        try:
            from effects.manager import EffectManager
            self.effect_manager = EffectManager(
                analyzer=self.analyzer,
                renderer=self.preview_renderer,
                effect_type=self._get_effect_key(),
                color_palette=self.selected_color.get(),
                background_image=self.background_image.get() or None,
                background_opacity=self.opacity_var.get() / 100.0,
                logo_image=self.logo_image.get() or None,
                logo_position=self.logo_position.get(),
                logo_x=self.logo_x.get() / 100.0,
                logo_y=self.logo_y.get() / 100.0,
                logo_scale=self.logo_scale.get() / 100.0,
                logo_opacity=self.logo_opacity.get() / 100.0,
            )
            self.effect_manager.init()
        except Exception as e:
            self._set_status(f"Erreur: {str(e)}")
            self.is_playing.set(False)
            self._is_playing_event.clear()
            return

        self._frame_times = []
        self._fps_counter = 0
        self._fps_last_time = time.time()
        self._playback_start_time = time.time()
        self._cleaned_up = False

        self.playback_thread = threading.Thread(
            target=self._playback_loop, daemon=True
        )
        self.playback_thread.start()
        self._set_status("Lecture en cours...")
        self.toast.show(f"▶ {os.path.basename(self.audio_file.get())}", 1.5, "success")

    def _playback_loop(self):
        try:
            self.analyzer.start_stream()
            self.preview_renderer.init()

            iteration = 0
            last_ui_update = 0.0
            last_timecode_update = 0.0

            while self._is_playing_event.is_set():
                iteration += 1

                if not self.preview_renderer.handle_events():
                    self._is_playing_event.clear()
                    break

                delta_time = self.preview_renderer.clock.tick(
                    self.fps.get()
                ) / 1000.0

                pw, ph = self.preview.get_display_size()
                # Plafonner la résolution de rendu interne pour les performances de l'aperçu GUI (max 960x540)
                max_w = 960
                max_h = 540
                scale = min(1.0, max_w / pw, max_h / ph)
                rw = int(pw * scale)
                rh = int(ph * scale)

                if (rw, rh) != self._preview_render_size:
                    self._resize_effect(rw, rh)

                if (not hasattr(self, 'audio_player')
                        or self.audio_player is None
                        or not self.audio_player.is_playing):
                    break

                chunk = self.analyzer.get_next_chunk()
                if chunk is None:
                    break

                audio_data = self.analyzer.analyze_chunk(chunk)
                self.effect_manager.update(audio_data, delta_time)

                arr = self.effect_manager.render_to_array()
                if arr is not None and (pw, ph) != (rw, rh) and _HAS_CV2:
                    arr = cv2.resize(arr, (pw, ph), interpolation=cv2.INTER_LINEAR)
                frame = self._capture_frame(arr)

                if frame is not None:
                    with self._frame_lock:
                        self._pending_frame = frame

                now = time.time()
                if now - last_ui_update > (self._ui_frame_interval / 1000.0):
                    last_ui_update = now
                    self.root.after(0, self._update_preview_from_pending)

                if now - last_timecode_update > 0.1:
                    last_timecode_update = now
                    elapsed = now - self._playback_start_time
                    mins = int(elapsed // 60)
                    secs = int(elapsed % 60)
                    millis = int((elapsed * 1000) % 1000)
                    self.root.after(
                        0,
                        lambda m=mins, s=secs, ms=millis:
                            self._timecode_str.set(f"{m:02d}:{s:02d}.{ms:03d}")
                    )

                self._fps_counter += 1
                elapsed = now - self._fps_last_time
                if elapsed >= 1.0:
                    self._fps_display = int(self._fps_counter / elapsed)
                    self._fps_counter = 0
                    self._fps_last_time = now
                    self.root.after(0, self._update_fps_display)

                self.preview_renderer.present()

            self._logs_tab.add_message(
                f"Playback: terminé après {iteration} itérations", "INFO"
            )

        except Exception as e:
            error_msg = str(e)
            self.root.after(
                0, lambda em=error_msg: self._set_status(f"Erreur: {em}")
            )
        finally:
            self._cleanup_playback()

    def _update_fps_display(self):
        colour = self._theme.neon_accent if self._fps_display >= 30 else self._theme.neon_warn
        if self._fps_display < 15:
            colour = "#ff3b3b"
        self._fps_display_label.configure(text=f"{self._fps_display} FPS", fg=colour)

    def _resize_effect(self, new_w, new_h):
        try:
            self.preview_renderer.width = new_w
            self.preview_renderer.height = new_h
            if hasattr(self.effect_manager, 'current_effect'):
                self.effect_manager.current_effect.width = new_w
                self.effect_manager.current_effect.height = new_h
            if hasattr(self.effect_manager, 'resize'):
                self.effect_manager.resize(new_w, new_h)
            self._preview_render_size = (new_w, new_h)
        except Exception:
            pass

    def _update_preview_from_pending(self):
        with self._frame_lock:
            pil_img = self._pending_frame
            self._pending_frame = None
        if pil_img is None:
            return
        pw, ph = self.preview.winfo_width(), self.preview.winfo_height()
        if pw > 10 and ph > 10 and (pw, ph) != pil_img.size:
            pil_img = pil_img.resize((pw, ph), Image.BILINEAR)
        self.preview.update_image(ImageTk.PhotoImage(pil_img))

    def _capture_frame(self, arr):
        if (arr is not None and len(arr.shape) == 3
                and arr.shape[0] > 0 and arr.shape[1] > 0):
            return Image.fromarray(arr)
        return None

    def _stop_playback(self):
        self.is_playing.set(False)
        self._is_playing_event.clear()

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
                        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                            ctypes.c_long(thread_id), ctypes.py_object(SystemExit)
                        )
                        if res == 0:
                            pass
                        elif res != 1:
                            ctypes.pythonapi.PyThreadState_SetAsyncExc(
                                ctypes.c_long(thread_id), ctypes.c_long(0)
                            )
                except Exception as e:
                    print(f"Warning: thread stop failed: {e}")

        self._cleanup_playback()
        self.preview.clear()
        self._fps_display_label.configure(text="-- FPS", fg=self._theme.fg_muted)
        self._timecode_str.set("00:00.000")
        self._set_status("Lecture arrêtée")

    def _cleanup_playback(self):
        with self._cleanup_lock:
            if self._cleaned_up:
                return
            self._cleaned_up = True
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

    # ── Export ─────────────────────────────────────────────────────────
    def _on_export_request(self, filename):
        if self._export_in_progress:
            return

        width, height = self._get_resolution()
        self._export_in_progress = True

        try:
            from recorder.video_recorder import VideoRecorder
            from quality_presets import get_preset, build_ffmpeg_cmd

            preset = get_preset(self.selected_preset.get())

            self.recorder = VideoRecorder(
                audio_file=self.audio_file.get(),
                output_file=filename,
                width=width, height=height,
                fps=self.fps.get(),
                effect_type=self._get_effect_key(),
                color_palette=self.selected_color.get(),
                background_image=self.background_image.get() or None,
                background_opacity=self.opacity_var.get() / 100.0,
                logo_image=self.logo_image.get() or None,
                logo_position=self.logo_position.get(),
                logo_x=self.logo_x.get() / 100.0,
                logo_y=self.logo_y.get() / 100.0,
                logo_scale=self.logo_scale.get() / 100.0,
                logo_opacity=self.logo_opacity.get() / 100.0,
            )
            self.recorder._ffmpeg_cmd = build_ffmpeg_cmd(
                width, height, self.fps.get(),
                self.audio_file.get(), filename, self.selected_preset.get()
            )
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de la création du recorder: {str(e)}")
            self._export_in_progress = False
            return

        self._export_tab.set_export_button_state(False, export_in_progress=True)
        self._export_tab.show_progress(0, 1)
        self._export_tab.show_cancel_button()
        self._set_status(f"Export: {os.path.basename(filename)}")
        self._led_status.configure(fg=self._theme.neon_warn)

        export_thread = threading.Thread(
            target=self._export_loop, args=(filename,), daemon=True
        )
        export_thread.start()

    def _export_loop(self, filename):
        try:
            self.recorder.record(
                progress_callback=lambda c, t: self.root.after(
                    0, lambda: self._export_tab.show_progress(c, t)
                )
            )
            basename = os.path.basename(filename)
            self.root.after(0, lambda bn=basename: self._export_finished(bn))
            self.root.after(0, lambda f=filename: messagebox.showinfo(
                "Succès", f"Vidéo exportée vers\n{f}"
            ))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda em=error_msg: self._export_finished(error=em))
            self.root.after(0, lambda em=error_msg: messagebox.showerror(
                "Erreur", f"Échec de l'export:\n{em}"
            ))

    def _on_export_cancel(self):
        """Called when the user clicks the cancel button during export."""
        if self.recorder:
            self.recorder.cancel()

    def _export_finished(self, basename=None, error=None):
        self._export_in_progress = False
        self._export_tab.set_export_button_state(True)
        self._export_tab.hide_cancel_button()

        if error:
            is_cancel = "annulé" in error.lower()
            if is_cancel:
                self._led_status.configure(fg=self._theme.neon_warn)
                self._set_status("EXPORT ANNULÉ")
                self._export_tab._progress_label.configure(
                    text="EXPORT ANNULÉ", fg=self._theme.neon_warn
                )
                self._export_tab._progress_pct.configure(
                    text="--", fg=self._theme.neon_warn
                )
                self._export_tab._draw_progress(0)
                self._export_tab._progress_frame.pack(fill=tk.X, padx=12, pady=(0, 4))
                self._export_tab._progress_frame.update_idletasks()
                self.toast.show("Export annulé", 2.0, "warning")
            else:
                self._led_status.configure(fg="#ff3b3b")
                self._set_status(f"ÉCHEC: {error[:60]}")
                self._export_tab.show_progress_error(error)
                self.toast.show(f"Export échoué: {error[:40]}", 3.0, "error")
            self.root.after(5000, lambda: (
                self._export_tab.hide_progress(),
                self._led_status.configure(fg=self._theme.neon_primary),
                self._set_status("PRÊT"),
            ))
        else:
            self._led_status.configure(fg=self._theme.neon_accent)
            self._set_status(f"✓ EXPORT TERMINÉ: {basename}")
            self._export_tab.show_progress_success(basename)
            self.toast.show(f"✓ Export terminé: {basename}", 3.0, "success")
            self.root.after(3000, lambda: (
                self._export_tab.hide_progress(),
                self._led_status.configure(fg=self._theme.neon_primary),
                self._set_status("PRÊT"),
            ))

    # ── Run ────────────────────────────────────────────────────────────
    def run(self):
        self._animate_led()
        self.root.mainloop()
