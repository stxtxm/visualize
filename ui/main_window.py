"""
Main window for the psychedelic visualizer GUI.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


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
        self.audio_file = tk.StringVar(value="")
        self.selected_effect = tk.StringVar(value="random")
        self.selected_color = tk.StringVar(value="psychedelic")
        self.resolution = tk.StringVar(value="1080p")
        self.fps = tk.IntVar(value=60)
        self.selected_preset = tk.StringVar(value="normal")
        
        self.playback_thread = None
        self.analyzer = None
        self.preview_renderer = None
        self.effect_manager = None
        self.recorder = None
        
        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        self.root.title("Visualisateur Psychédélique")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            header_frame,
            text="Visualisateur Psychédélique",
            font=('Helvetica', 16, 'bold')
        ).pack(side=tk.LEFT)
        
        # Controls
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # File selection
        ttk.Label(control_frame, text="Fichier audio:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(
            control_frame,
            textvariable=self.audio_file,
            width=50
        ).grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Button(
            control_frame,
            text="Parcourir...",
            command=self._open_file
        ).grid(row=0, column=2, sticky=tk.W, padx=5)
        
        # Preset selection (quality/speed)
        ttk.Label(control_frame, text="Préglage:").grid(row=0, column=3, sticky=tk.W, padx=(10, 0))
        self.preset_combo = ttk.Combobox(
            control_frame,
            textvariable=self.selected_preset,
            values=['dev', 'fast', 'normal', 'high', '4k'],
            state='readonly',
            width=8
        )
        self.preset_combo.grid(row=0, column=4, sticky=tk.W, padx=5)
        self.preset_combo.bind('<<ComboboxSelected>>', self._preset_changed)
        
        # Effect selection
        ttk.Label(control_frame, text="Effet:").grid(row=0, column=5, sticky=tk.W, padx=(10, 0))
        self.effect_combo = ttk.Combobox(
            control_frame,
            textvariable=self.selected_effect,
            values=['random', 'bars', 'circles', 'particles', 'tunnel', 'wave', 'spectrum', 'plasma'],
            state='readonly',
            width=12
        )
        self.effect_combo.grid(row=0, column=6, sticky=tk.W, padx=5)
        
        # Color palette selection
        ttk.Label(control_frame, text="Couleurs:").grid(row=1, column=3, sticky=tk.W, padx=(10, 0), pady=(5, 0))
        self.color_combo = ttk.Combobox(
            control_frame,
            textvariable=self.selected_color,
            values=['psychedelic', 'retro', 'winamp_classic', 'dark', 'rainbow'],
            state='readonly',
            width=12
        )
        self.color_combo.grid(row=1, column=4, sticky=tk.W, padx=5, pady=(5, 0))
        
        # Second row of controls
        ttk.Label(control_frame, text="Résolution:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.resolution_combo = ttk.Combobox(
            control_frame,
            textvariable=self.resolution,
            values=['1080p', '1440p', '4K'],
            state='readonly',
            width=8
        )
        self.resolution_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=(5, 0))
        
        ttk.Label(control_frame, text="FPS:").grid(row=1, column=2, sticky=tk.W, pady=(5, 0))
        self.fps_spin = ttk.Spinbox(
            control_frame,
            from_=30, to=120,
            textvariable=self.fps,
            width=5
        )
        self.fps_spin.grid(row=1, column=3, sticky=tk.W, padx=5, pady=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            button_frame,
            text="▶ Lecture",
            command=self._toggle_playback
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="⏹ Arrêter",
            command=self._stop_playback
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="🎥 Exporter Vidéo",
            command=self._export_video
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="📝 Logs",
            command=self._show_logs
        ).pack(side=tk.LEFT, padx=5)
        
        # Preview frame
        preview_frame = ttk.LabelFrame(main_frame, text="Aperçu", padding="5")
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        self.preview = PreviewFrame(preview_frame, width=800, height=450)
        self.preview.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar(value="Prêt")
        ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        ).pack(fill=tk.X, pady=(5, 0))

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
        
        # Commencer dans le dossier input du projet
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
        
        # Stop existing thread if any
        if self.playback_thread and self.playback_thread.is_alive():
            self._stop_playback()
        
        # Initialize analyzer
        try:
            from audio.analyzer import AudioAnalyzer
            self.analyzer = AudioAnalyzer(self.audio_file.get())
        except Exception as e:
            self.status_var.set(f"Erreur: {str(e)}")
            self.is_playing.set(False)
            return
        
        # Get resolution
        width, height = self._get_resolution()
        
        # Create renderer for preview
        try:
            from renderer.pygame_renderer import PygameRenderer
            self.preview_renderer = PygameRenderer(
                width=width,
                height=height,
                fullscreen=False,
                fps=self.fps.get()
            )
        except Exception as e:
            self.status_var.set(f"Erreur: {str(e)}")
            self.is_playing.set(False)
            return
        
        # Create effect manager
        try:
            from effects.manager import EffectManager
            self.effect_manager = EffectManager(
                analyzer=self.analyzer,
                renderer=self.preview_renderer,
                effect_type=self.selected_effect.get(),
                color_palette=self.selected_color.get()
            )
            self.effect_manager.init()
        except Exception as e:
            self.status_var.set(f"Erreur: {str(e)}")
            self.is_playing.set(False)
            return
        
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
            
            # Main loop
            iteration = 0
            try:
                from ui.log_display import log_message
                log_message("Playback: Boucle de lecture démarrée")
            except:
                pass
            
            while self.is_playing.get():
                iteration += 1
                
                # Handle events
                if not self.preview_renderer.handle_events():
                    try:
                        from ui.log_display import log_message
                        log_message(f"Playback: Événement QUIT à itération {iteration}")
                    except:
                        pass
                    self.is_playing.set(False)
                    break
                
                # Get delta time
                delta_time = self.preview_renderer.clock.tick(self.fps.get()) / 1000.0
                
                # Get audio data
                chunk = self.analyzer.get_next_chunk()
                if chunk is None:
                    try:
                        from ui.log_display import log_message
                        log_message(f"Playback: Chunk None à itération {iteration} - ARRET")
                    except:
                        pass
                    break
                    
                audio_data = self.analyzer.analyze_chunk(chunk)
                
                # Log tous les 20 itérations
                if iteration % 20 == 0:
                    try:
                        from ui.log_display import log_message
                        log_message(f"Playback: Itération {iteration} - Volume={audio_data.get('volume', 0):.4f}")
                    except:
                        pass
                
                # Update and render
                self.effect_manager.current_effect.update(audio_data, delta_time)
                surface = self.preview_renderer.get_surface()
                self.effect_manager.current_effect.render(surface)
                
                # Capture frame for Tkinter preview (AVANT present pour éviter deadlock)
                # On crée une copie de la surface pour éviter les problèmes de verrouillage
                frame = self._capture_frame_copy(surface)
                if frame is not None:
                    self.root.after(0, self._update_preview, frame)
                
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
            if hasattr(self, 'analyzer') and self.analyzer:
                self.analyzer.cleanup()
            if hasattr(self, 'preview_renderer') and self.preview_renderer:
                self.preview_renderer.cleanup()
            self.is_playing.set(False)
            self.root.after(0, lambda: self.status_var.set("Lecture arrêtée"))

    def _capture_frame_copy(self, surface):
        """Capture a copy of the surface for preview (thread-safe)."""
        try:
            import pygame
            import numpy as np
            from PIL import Image, ImageTk
            
            # Créer une COPIE de la surface pour éviter les deadlocks
            # pygame.surfarray.array3d verrouille la surface, donc on fait une copie d'abord
            surface_copy = surface.copy()
            data = pygame.surfarray.array3d(surface_copy)
            
            # Convert to PIL Image
            img = Image.fromarray(data)
            img = img.resize((self.preview.width, self.preview.height), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            # En mode debug, on affiche l'erreur
            import warnings
            warnings.warn(f"Erreur capture frame: {e}")
            return None
    
    def _capture_frame(self):
        """Capture current frame for preview (déprécié, garde pour compatibilité)."""
        try:
            surface = self.preview_renderer.get_surface()
            return self._capture_frame_copy(surface)
        except Exception:
            return None

    def _update_preview(self, frame):
        """Update preview with new frame."""
        self.preview.update_image(frame)

    def _stop_playback(self):
        """Stop playback."""
        self.is_playing.set(False)
        if self.playback_thread and self.playback_thread.is_alive():
            # Attendre 1 seconde, puis forcer si nécessaire
            self.playback_thread.join(timeout=1)
            if self.playback_thread.is_alive():
                # Thread toujours vivant, essayer de le marquer comme daemon pour éviter le blocage
                import ctypes
                try:
                    # Méthode avancée pour tuer un thread Python
                    thread_id = self.playback_thread.ident
                    if thread_id:
                        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), ctypes.py_object(SystemExit))
                        if res == 0:
                            pass  # Thread déjà terminé
                        elif res != 1:
                            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), ctypes.c_long(0))
                            raise RuntimeError("Échec de l'arrêt forcé du thread")
                except Exception as e:
                    print(f"Warning: Impossible d'arrêter le thread proprement: {e}")
                    # Créer un nouveau thread qui forera l'arrêt après un délai
                    pass
        
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
        
        # Ask for output file
        filename = filedialog.asksaveasfilename(
            title="Enregistrer la vidéo",
            defaultextension=".mp4",
            filetypes=[('Fichiers MP4', '*.mp4'), ('Tous les fichiers', '*.*')]
        )
        
        if not filename:
            return
        
        # Get resolution
        width, height = self._get_resolution()
        
        # Create recorder with preset
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
            # Override FFmpeg command with preset
            self.recorder._ffmpeg_cmd = build_ffmpeg_cmd(
                width, height, self.fps.get(), 
                self.audio_file.get(), filename, self.selected_preset.get()
            )
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de la création du recorder: {str(e)}")
            return
        
        # Start export in a thread
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
            # Créer une nouvelle fenêtre pour les logs
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
