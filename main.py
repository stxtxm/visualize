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


def run_gui():
    try:
        # Initialiser pygame DANS LE THREAD PRINCIPAL avant toute GUI
        # Ceci permet à pygame.Surface() et pygame.draw.* de fonctionner
        # depuis n'importe quel thread sans ouvrir de fenêtre
        try:
            import pygame
            pygame.display.init()
            pygame.time.init()
        except ImportError:
            pass  # pas de pygame = pas de rendu Pygame
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
    except Exception as e:
        print(f"GUI Error: {e}")
        sys.exit(1)


def run_cli():
    parser = argparse.ArgumentParser(
        description='Psychedelic Audio Visualizer',
        epilog="Examples:\n  python3 main.py audio.mp3\n  python3 main.py audio.mp3 --export video.mp4"
    )
    parser.add_argument('audio_file', nargs='?', default=None)
    parser.add_argument('--export', '-o', type=str, default=None)
    parser.add_argument('--effect', '-e', default='random',
                        choices=['bars', 'circles', 'particles', 'tunnel', 'wave', 'spectrum', 'plasma', 'random'])
    parser.add_argument('--color', '-c', default='psychedelic',
                        choices=['psychedelic', 'retro', 'dark', 'rainbow'])
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
    
    # Need audio file
    if not args.audio_file:
        run_gui()
        return
    
    if not os.path.exists(args.audio_file):
        print(f"Error: {args.audio_file} not found")
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
    
    effect_manager = EffectManager(
        analyzer=analyzer,
        effect_type=args.effect, color_palette=args.color
    )
    effect_manager.init()
    
    audio_duration = analyzer.get_duration_seconds()
    total_frames = int(audio_duration * fps)
    print(f"  Duration: {audio_duration:.0f}s, Frames: {total_frames}")
    
    ffmpeg_cmd = build_ffmpeg_cmd(width, height, fps, args.audio_file, args.export, args.preset)
    
    # Débogage : afficher la commande FFmpeg
    print(f"  FFmpeg cmd: {' '.join(ffmpeg_cmd)}")
    
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
        stderr=subprocess.PIPE,
        bufsize=0  # Désactiver le buffering pour éviter les blocages
    )
    
    frames_written = 0
    ffmpeg_error = None
    
    try:
        for frame_count in range(total_frames):
            chunk = analyzer.get_next_chunk()
            if chunk is None:
                # Fin du fichier audio, on s'arrête
                break
                
            audio_data = analyzer.analyze_chunk(chunk)
            effect_manager.current_effect.update(audio_data, 1.0/fps)
            frame = effect_manager.current_effect.render_to_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Vérifier si FFmpeg est toujours vivant avant d'écrire
            if process.poll() is not None:
                # FFmpeg a terminé prématurément (probablement à cause de -shortest)
                # C'est OK, on peut s'arrêter
                break
            
            try:
                process.stdin.write(frame.tobytes())
                frames_written += 1
            except (BrokenPipeError, ConnectionResetError, OSError) as e:
                # FFmpeg a fermé le pipe - c'est OK, il a probablement fini
                break
            
            # Vérifier périodiquement que FFmpeg est toujours vivant
            if frame_count % 100 == 0:
                if process.poll() is not None:
                    # FFmpeg a terminé, c'est probablement OK
                    break
                progress = (frame_count / total_frames) * 100
                print(f"  Progress: {progress:.0f}%")
        
        # Fermer stdin proprement pour signaler à FFmpeg que c'est fini
        try:
            process.stdin.close()
        except (BrokenPipeError, ConnectionResetError, OSError):
            # Déjà fermé, ce n'est pas grave
            pass
        
        # Attendre la fin de FFmpeg sans timeout
        try:
            stdout, stderr = process.communicate()
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            ffmpeg_error = f"FFmpeg timeout after {frames_written} frames"
        except (ValueError, OSError) as e:
            # Le pipe a été fermé, c'est OK
            stdout, stderr = b'', b''
        
        # FFmpeg peut retourner un code non-nul mais avoir créé la vidéo
        # Vérifier si la sortie existe et a une taille raisonnable
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='ignore') if stderr else ''
            if os.path.exists(args.export) and os.path.getsize(args.export) > 0:
                # FFmpeg a peut-être fini normalement malgré un code d'erreur
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
    
    # Vérifier que la sortie existe et a une taille raisonnable
    if os.path.exists(args.export):
        file_size = os.path.getsize(args.export)
        if file_size < 1024:  # Moins de 1Ko, probablement un échec
            if os.path.exists(args.export):
                os.remove(args.export)
            raise RuntimeError(f"Output file too small ({file_size} bytes), export likely failed")
        print(f"✓ Export complete: {args.export} ({file_size/1024/1024:.1f} MB)")
    else:
        raise RuntimeError(f"Output file not created: {args.export}")


def run_playback(args):
    from audio.analyzer import AudioAnalyzer
    from effects.manager import EffectManager
    from quality_presets import get_preset, RESOLUTIONS
    
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
    effect_manager = EffectManager(analyzer, renderer, args.effect, args.color)
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
