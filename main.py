#!/usr/bin/env python3
"""Visualisateur Audio Psychédélique - Point d'entrée principal"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def has_gui():
    try:
        import tkinter as tk
        return True
    except:
        return False


def has_pygame():
    try:
        import pygame
        return True
    except:
        return False


def run_gui():
    try:
        # Initialiser pygame DANS LE THREAD PRINCIPAL avant toute GUI
        try:
            import pygame
            pygame.display.init()
            pygame.font.init()
        except ImportError:
            pass
        except Exception:
            pass
        
        from ui.main_window import MainWindow
        from ui.log_display import start_log_capture
        import tkinter as tk
        
        # Démarrer la capture des logs
        start_log_capture()
        
        root = tk.Tk()
        app = MainWindow(root)
        root.protocol("WM_DELETE_WINDOW", lambda: app._stop_playback() or root.quit())
        root.mainloop()
    except ImportError as e:
        if 'tkinter' in str(e) and has_pygame():
            _run_pygame_fallback()
        else:
            print(f"GUI Error: {e}")
            print("Installez python3-tkinter ou utilisez --no-gui avec un fichier audio.")
            sys.exit(1)
    except Exception as e:
        print(f"GUI Error: {e}")
        sys.exit(1)


def _run_pygame_fallback():
    """
    Fallback quand tkinter n'est pas disponible.
    Ouvre une fenêtre Pygame plein écran avec lecture immédiate.
    L'utilisateur peut glisser-déposer un fichier audio ou utiliser le CLI.
    """
    import pygame
    from audio.analyzer import AudioAnalyzer
    from effects.manager import EffectManager
    from quality_presets import get_preset, RESOLUTIONS
    
    pygame.display.init()
    pygame.font.init()
    
    # Plein écran
    info = pygame.display.Info()
    width, height = info.current_w, info.current_h
    
    # Résolution réduite pour les performances si l'écran est trop grand
    if width > 1920:
        width = 1920
        height = 1080
    
    screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN | pygame.DOUBLEBUF)
    pygame.display.set_caption("Visualisateur Psychédélique")
    
    preset = get_preset('normal')
    fps = 60
    clock = pygame.time.Clock()
    
    # Police pour les messages
    try:
        font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 24)
    except Exception:
        font = None
        small_font = None
    
    analyzer = None
    audio_player = None
    effect_manager = None
    audio_file = None
    is_playing = False
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    if is_playing:
                        if analyzer:
                            analyzer.cleanup()
                        if audio_player:
                            audio_player.cleanup()
                        if effect_manager:
                            effect_manager.cleanup()
                        is_playing = False
                    else:
                        pass
            elif event.type == pygame.DROPFILE:
                # Glisser-déposer un fichier audio
                try:
                    if analyzer:
                        analyzer.cleanup()
                    if audio_player:
                        audio_player.cleanup()
                    
                    analyzer = AudioAnalyzer(event.file)
                    analyzer.start_stream()
                    
                    from audio.player import AudioPlayer
                    audio_player = AudioPlayer(
                        sample_rate=analyzer.sample_rate,
                        chunk_size=analyzer.chunk_size
                    )
                    audio_player.start()
                    
                    effect_manager = EffectManager(
                        analyzer=analyzer,
                        renderer=None,
                        effect_type='random',
                        color_palette='psychedelic'
                    )
                    effect_manager.init()
                    is_playing = True
                    audio_file = event.file
                except Exception as e:
                    print(f"Erreur chargement {event.file}: {e}")
        
        # Rendu
        screen.fill((0, 0, 0))
        
        if is_playing and analyzer and effect_manager and audio_player:
            chunk = analyzer.get_next_chunk()
            if chunk is not None:
                audio_data = analyzer.analyze_chunk(chunk)
                audio_player.play_chunk(chunk)
                effect_manager.current_effect.update(audio_data, clock.get_time() / 1000.0)
                effect_manager.current_effect.render(screen)
        
        # Infos à l'écran
        if font and small_font:
            if not is_playing:
                text = font.render("Glissez un fichier audio ici", True, (255, 255, 255))
                text_rect = text.get_rect(center=(width // 2, height // 2))
                screen.blit(text, text_rect)
                
                hint = small_font.render("ou lancez: python3 main.py chemin/vers/audio.mp3", True, (200, 200, 200))
                hint_rect = hint.get_rect(center=(width // 2, height // 2 + 40))
                screen.blit(hint, hint_rect)
            else:
                # Afficher le nom du fichier
                name = small_font.render(os.path.basename(audio_file or ""), True, (200, 200, 200))
                screen.blit(name, (10, 10))
        
        pygame.display.flip()
        clock.tick(fps)
    
    if analyzer:
        analyzer.cleanup()
    if effect_manager:
        effect_manager.cleanup()
    pygame.quit()


def run_cli():
    parser = argparse.ArgumentParser(
        description='Psychedelic Audio Visualizer',
        epilog="Examples:\n  python3 main.py audio.mp3\n  python3 main.py audio.mp3 --export video.mp4"
    )
    parser.add_argument('audio_file', nargs='?', default=None)
    parser.add_argument('--export', '-o', type=str, default=None)
    parser.add_argument('--effect', '-e', default='trance_scope',
                        choices=['trance_scope', 'pro_trance', 'neon_equalizer', 'classic',
                                 'bars', 'circles', 'particles', 'tunnel', 'wave',
                                 'spectrum', 'plasma', 'psychedelic_plasma',
                                 '3d_cyber_tunnel', 'random'])
    parser.add_argument('--color', '-c', default='psychedelic',
                        choices=['psychedelic', 'retro', 'winamp_classic', 'dark', 'rainbow'])
    parser.add_argument('--background', '-b', default=None,
                        help='Optional image file used as the visualizer background')
    parser.add_argument('--background-opacity', type=float, default=0.72,
                        help='Background image opacity (0.0-1.0), default 0.72')
    parser.add_argument('--audio-device', '-d', type=str, default=None,
                        help='Audio output device index or name substring (use "list" to show available devices)')
    parser.add_argument('--resolution', '-r', default=None,
                        choices=['720p', '1080p', '1440p', '4K'])
    parser.add_argument('--fps', type=int, default=None)
    parser.add_argument('--preset', '-p', default='normal',
                        choices=['dev', 'fast', 'normal', 'high', '4k'])
    parser.add_argument('--fullscreen', '-f', action='store_true')
    parser.add_argument('--no-gui', action='store_true')
    args = parser.parse_args()
    
    # Launch GUI if no args and GUI available
    if len(sys.argv) == 1 and has_gui() and not args.no_gui:
        run_gui()
        return
    
    # Fallback: pas de tkinter mais pygame dispo → lancer le mode plein écran
    if len(sys.argv) == 1 and not has_gui() and has_pygame():
        print("tkinter non disponible - lancement en mode Pygame plein écran")
        print("Glissez un fichier audio dans la fenêtre ou utilisez: python3 main.py <fichier>")
        _run_pygame_fallback()
        return
    
    # Handle --audio-device list before requiring audio file
    if args.audio_device and args.audio_device.lower() == 'list':
        from audio.player import AudioPlayer
        devices = AudioPlayer.list_devices()
        print("\nAvailable audio output devices:")
        print("-" * 60)
        for d in devices:
            print(f"  {d['index']}: {d['name']} ({d['api']}) - {d['channels']} ch")
        print()
        sys.exit(0)

    # Need audio file
    if not args.audio_file:
        print("Utilisation: python3 main.py <fichier_audio>")
        print("  ou installez python3-tkinter pour la GUI")
        sys.exit(1)
    
    if not os.path.exists(args.audio_file):
        print(f"Error: {args.audio_file} not found")
        sys.exit(1)

    if args.background and not os.path.exists(args.background):
        print(f"Error: {args.background} not found")
        sys.exit(1)
    
    if args.export:
        run_export(args)
    else:
        run_playback(args)


def run_export(args):
    from audio.analyzer import AudioAnalyzer
    from effects.manager import EffectManager
    from quality_presets import get_preset, RESOLUTIONS, build_ffmpeg_cmd
    import cv2, subprocess, numpy as np
    
    preset = get_preset(args.preset)
    res = args.resolution or preset['resolution']
    fps = args.fps or preset['fps']
    width, height = RESOLUTIONS.get(res, (1920, 1080))
    
    print(f"Exporting {args.audio_file} -> {args.export}")
    print(f"  Preset: {preset['name']} ({width}x{height}, {fps}fps)")
    
    analyzer = AudioAnalyzer(args.audio_file, loop=False)
    analyzer.start_stream()
    
    class ExportRenderer:
        def __init__(self, w, h):
            self.width = w
            self.height = h

    effect_manager = EffectManager(
        analyzer=analyzer,
        renderer=ExportRenderer(width, height),
        effect_type=args.effect,
        color_palette=args.color,
        background_image=args.background,
        background_opacity=args.background_opacity
    )
    effect_manager.init()
    
    audio_duration = analyzer.get_duration_seconds()
    total_frames = int(audio_duration * fps)
    print(f"  Duration: {audio_duration:.0f}s, Frames: {total_frames}")
    
    ffmpeg_cmd = build_ffmpeg_cmd(width, height, fps, args.audio_file, args.export, args.preset)
    
    # Vérifier que le fichier audio existe
    if not os.path.exists(args.audio_file):
        raise FileNotFoundError(f"Audio file not found: {args.audio_file}")
    
    # Vérifier que le dossier de sortie existe
    output_dir = os.path.dirname(args.export)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    process = subprocess.Popen(
        ffmpeg_cmd, 
        stdin=subprocess.PIPE, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )
    
    frames_written = 0
    ffmpeg_error = None
    
    try:
        for frame_count in range(total_frames):
            chunk = analyzer.get_next_chunk()
            if chunk is None:
                break
                
            audio_data = analyzer.analyze_chunk(chunk)
            effect_manager.current_effect.update(audio_data, 1.0/fps)
            frame = effect_manager.current_effect.render_to_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            if process.poll() is not None:
                break
            
            try:
                process.stdin.write(frame.tobytes())
                frames_written += 1
            except (BrokenPipeError, ConnectionResetError, ValueError, OSError):
                break
            
            if frame_count % 10 == 0:
                if process.poll() is not None:
                    break
                pct = (frame_count / total_frames) * 100 if total_frames > 0 else 0
                print(f"\r  Export: {frame_count}/{total_frames} ({pct:.0f}%)", end="", flush=True)
        
        try:
            process.stdin.close()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        
        try:
            stdout, stderr = process.communicate()
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            ffmpeg_error = f"FFmpeg timeout after {frames_written} frames"
        except (ValueError, OSError):
            stdout, stderr = b'', b''
        
        if process.returncode is None:
            process.wait()
        
        print()
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='ignore') if stderr else ''
            if os.path.exists(args.export) and os.path.getsize(args.export) > 0:
                print(f"✓ Export completed: {args.export}")
                return
            else:
                raise RuntimeError(f"FFmpeg error (code {process.returncode}):\n{error_msg}")
        
        if ffmpeg_error:
            error_msg = stderr.decode('utf-8', errors='ignore') if stderr else ffmpeg_error
            raise RuntimeError(f"Export failed:\n{error_msg}")
                
    except KeyboardInterrupt:
        print("\n❌ Export cancelled by user")
        raise
    finally:
        analyzer.cleanup()
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except:
                process.kill()
    
    if os.path.exists(args.export):
        file_size = os.path.getsize(args.export)
        if file_size < 1024:
            if os.path.exists(args.export):
                os.remove(args.export)
            raise RuntimeError(f"Output file too small ({file_size} bytes), export likely failed")
        print(f"✓ Export complete: {args.export} ({file_size/1024/1024:.1f} MB)")
    else:
        raise RuntimeError(f"Output file not created: {args.export}")


def run_playback(args):
    from audio.analyzer import AudioAnalyzer
    from audio.player import AudioPlayer
    from effects.manager import EffectManager
    from quality_presets import get_preset, RESOLUTIONS
    
    # Resolve audio device
    device_id = None
    if args.audio_device:
        if args.audio_device.isdigit():
            device_id = int(args.audio_device)
        else:
            # Try to match by name substring
            devices = AudioPlayer.list_devices()
            for d in devices:
                if args.audio_device.lower() in d['name'].lower():
                    device_id = d['index']
                    break
            if device_id is None:
                print(f"Warning: no device found matching '{args.audio_device}', using default")
    
    try:
        import pygame
        _has_pygame = True
    except ImportError:
        _has_pygame = False
    
    preset = get_preset(args.preset)
    res = args.resolution or preset['resolution']
    fps = args.fps or preset['fps']
    width, height = RESOLUTIONS.get(res, (1920, 1080))
    
    analyzer = AudioAnalyzer(args.audio_file, loop=True)
    analyzer.start_stream()
    
    if _has_pygame:
        from renderer.pygame_renderer import PygameRenderer
        renderer = PygameRenderer(width, height, args.fullscreen, fps)
    else:
        from renderer.array_renderer import ArrayRenderer
        renderer = ArrayRenderer(width, height, fps)
    
    renderer.init()
    effect_manager = EffectManager(analyzer, renderer, args.effect, args.color, background_image=args.background, background_opacity=args.background_opacity)
    effect_manager.init()
    
    try:
        while renderer.handle_events():
            chunk = analyzer.get_next_chunk()
            audio_data = analyzer.analyze_chunk(chunk)
            effect_manager.current_effect.update(audio_data, 1.0/fps)
            if _has_pygame:
                effect_manager.current_effect.render(renderer.get_surface())
            else:
                arr = effect_manager.current_effect.render_to_array()
                if arr is not None:
                    frame = renderer.get_surface()
                    h, w = min(arr.shape[0], frame.shape[0]), min(arr.shape[1], frame.shape[1])
                    frame[:h, :w] = arr[:h, :w]
            renderer.present()
    finally:
        analyzer.cleanup()
        renderer.cleanup()


if __name__ == '__main__':
    if len(sys.argv) == 1 and has_gui():
        run_gui()
    else:
        run_cli()
