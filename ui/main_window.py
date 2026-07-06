"""
Main window for the psychedelic visualizer GUI.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import time

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
        self.selected_effect = tk.StringVar(value="Neon Equalizer")
        self.selected_color = tk.StringVar(value="winamp_classic")
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
        
        self._setup_ui()

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
        self.root.geometry("1150x680")
        self.root.minsize(950, 600)
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
            
        create_dropdown(left_panel, "RÉSOLUTION EXPORT", self.resolution, ['1080p', '1440p', '4K'])
        create_dropdown(left_panel, "PRESET DE QUALITÉ", self.selected_preset, ['dev', 'fast', 'normal', 'high', '4k'], self._preset_changed)
        
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
        
        btn_export = tk.Button(secondary_btn_frame, text="🎥 EXPORTER", command=self._export_video, bg="#2a2a3e", fg=self.FG_LIGHT, activebackground="#3a3a55", activeforeground=self.FG_LIGHT, bd=0, pady=5, font=('Helvetica', 8, 'bold'), cursor="hand2")
        btn_export.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        add_hover(btn_export, "#3a3a55", "#2a2a3e")
        
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
        
        # Status Bar
        self.status_var = tk.StringVar(value="PRÊT")
        status_frame = tk.Frame(right_panel, bg="#111116", height=24, bd=0)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        led_status = tk.Label(status_frame, text="●", font=('Helvetica', 10), fg=self.NEON_CYAN, bg="#111116", padx=5)
        led_status.pack(side=tk.LEFT)
        
        # Update led status dynamically when playback state changes
        def update_led(*args):
            if self.is_playing.get():
                led_status.configure(fg=self.NEON_GREEN)
            else:
                led_status.configure(fg=self.NEON_CYAN)
        self.is_playing.trace_add("write", update_led)
        
        status_label = tk.Label(status_frame, textvariable=self.status_var, font=('Courier', 9, 'bold'), fg=self.NEON_CYAN, bg="#111116", anchor=tk.W)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    def _preset_changed(self, event=None):
        """Update resolution and FPS when preset changes."""
        from quality_presets import get_preset
        preset = get_preset(self.selected_preset.get())
        self.resolution.set(preset['resolution'])
        self.fps.set(preset['fps'])
        self.status_var.set(f"Préglage: {preset['name']}")
    
    def _open_file(self):
        """Open file dialog to select audio file from input directory."""
        filetypes = [
            ('Fichiers audio', '*.mp3 *.wav *.flac *.ogg *.aac'),
            ('Tous les fichiers', '*.*')
        ]
        
        initial_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'input')
        if not os.path.exists(initial_dir):
            initial_dir = os.path.expanduser('~')
        
        filename = filedialog.askopenfilename(
            title="Sélectionner un fichier audio",
            initialdir=initial_dir,
            filetypes=filetypes
        )
        
        if filename:
            self.audio_file.set(filename)
            self.status_var.set(f"Fichier chargé: {os.path.basename(filename)}")

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
            effect_name_map = {
                "Neon Equalizer": "neon_equalizer",
                "Psychedelic Plasma": "psychedelic_plasma",
                "3D Cyber Tunnel": "3d_cyber_tunnel"
            }
            effect_key = effect_name_map.get(self.selected_effect.get(), "neon_equalizer")
            
            self.effect_manager = EffectManager(
                analyzer=self.analyzer,
                renderer=self.preview_renderer,
                effect_type=effect_key,
                color_palette=self.selected_color.get()
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
                        effect_name_map = {"Neon Equalizer": "neon_equalizer", "Psychedelic Plasma": "psychedelic_plasma", "3D Cyber Tunnel": "3d_cyber_tunnel"}
                        effect_key = effect_name_map.get(self.selected_effect.get(), "neon_equalizer")
                        self.preview_renderer.width = pw
                        self.preview_renderer.height = ph
                        self.effect_manager = EffectManager(
                            analyzer=self.analyzer,
                            renderer=self.preview_renderer,
                            effect_type=effect_key,
                            color_palette=self.selected_color.get()
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

    def _export_video(self):
        """Export video."""
        if not self.audio_file.get():
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier audio d'abord.")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Enregistrer la vidéo",
            defaultextension=".mp4",
            initialdir=os.path.expanduser("~"),
            filetypes=[('Fichiers MP4', '*.mp4'), ('Tous les fichiers', '*.*')]
        )
        
        if not filename:
            return
        
        width, height = self._get_resolution()
        
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
                effect_type=self.selected_effect.get(),
                color_palette=self.selected_color.get()
            )
            self.recorder._ffmpeg_cmd = build_ffmpeg_cmd(
                width, height, self.fps.get(), 
                self.audio_file.get(), filename, self.selected_preset.get()
            )
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de la création du recorder: {str(e)}")
            return
        
        export_thread = threading.Thread(
            target=self._export_loop,
            args=(filename,),
            daemon=True
        )
        export_thread.start()
        
        self.status_var.set(f"Export en cours vers {os.path.basename(filename)}...")

    def _export_loop(self, filename):
        """Export loop."""
        try:
            self.recorder.record()
            basename = os.path.basename(filename)
            self.root.after(0, lambda bn=basename: self.status_var.set(f"Export terminé: {bn}"))
            self.root.after(0, lambda f=filename: messagebox.showinfo("Succès", f"Vidéo exportée vers\n{f}"))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda em=error_msg: self.status_var.set(f"Erreur d'export: {em}"))
            self.root.after(0, lambda em=error_msg: messagebox.showerror("Erreur", f"Échec de l'export:\n{em}"))

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