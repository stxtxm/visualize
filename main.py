#!/usr/bin/env python3
"""Visualize - Point d'entrée principal"""

import os
import sys
import math

# Linux-specific: suppress ALSA/SDL noise without affecting Windows audio
if sys.platform == 'linux':
    os.environ['ALSA_NO_ERROR_REPORT'] = '1'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'

import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def has_gui():
    try:
        import tkinter as tk
        return True
    except ImportError:
        return False


def has_pygame():
    try:
        import pygame
        return True
    except ImportError:
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
    
    try:
        _icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.png")
        if os.path.isfile(_icon_path):
            pygame.display.set_icon(pygame.image.load(_icon_path))
    except Exception:
        pass
    screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN | pygame.DOUBLEBUF)
    pygame.display.set_caption("Visualize")
    
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
                effect_manager.render(screen)
        
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
        description='Visualize - Audio Visualizer',
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
    parser.add_argument('--logo', default=None,
                        help='Optional logo image drawn above the visualizer')
    parser.add_argument('--logo-position', default='top-right',
                        choices=['top-left', 'top-center', 'top-right',
                                 'center-left', 'center', 'center-right',
                                 'bottom-left', 'bottom-center', 'bottom-right',
                                 'custom'],
                        help='Logo placement preset, or custom with --logo-x/--logo-y')
    parser.add_argument('--logo-x', type=float, default=50.0,
                        help='Custom logo horizontal position in percent (0-100)')
    parser.add_argument('--logo-y', type=float, default=50.0,
                        help='Custom logo vertical position in percent (0-100)')
    parser.add_argument('--logo-scale', type=float, default=18.0,
                        help='Logo width as a percentage of the video width (1-100)')
    parser.add_argument('--logo-opacity', type=float, default=100.0,
                        help='Logo opacity in percent (0-100)')
    parser.add_argument('--audio-device', '-d', type=str, default=None,
                        help='Audio output device index or name substring (use "list" to show available devices)')
    parser.add_argument('--resolution', '-r', default=None,
                        choices=['720p', '1080p', '1440p', '4K'])
    parser.add_argument('--fps', type=int, default=None)
    parser.add_argument('--preset', '-p', default='normal',
                        choices=['dev', 'fast', 'normal', 'high', '4k'])
    parser.add_argument('--render-scale', type=float, default=1.0,
                        help='Render scale factor (0.25-1.0). Lower = faster export, '
                             'ffmpeg upscales to target resolution. Default 1.0')
    parser.add_argument('--render-workers', type=int, default=0,
                        help='Parallel native-resolution workers; 0=auto (4K uses available CPU cores)')
    parser.add_argument('--codec', default='h264',
                        choices=['h264', 'h265', 'vp9'],
                        help='Video codec: h264 (default, most universal), '
                             'vp9 (royalty-free, plays on Linux without extra codecs), '
                             'h265 (better compression, needs codec support)')
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

    if args.logo and not os.path.exists(args.logo):
        print(f"Error: {args.logo} not found")
        sys.exit(1)
    
    if args.export:
        run_export(args)
    else:
        run_playback(args)


def run_export(args):
    from audio.analyzer import AudioAnalyzer
    from audio.analyzer import AudioFrameReader
    from effects.manager import EffectManager
    from quality_presets import (
        get_preset, RESOLUTIONS, build_ffmpeg_cmd,
        recommended_render_workers,
    )
    import subprocess, tempfile
    
    preset = get_preset(args.preset)
    res = args.resolution or preset['resolution']
    fps = args.fps or preset['fps']
    width, height = RESOLUTIONS.get(res, (1920, 1080))

    render_workers = args.render_workers
    if render_workers == 0:
        render_workers = recommended_render_workers(width, height)
    elif width >= 3840:
        requested_workers = max(1, render_workers)
        safe_workers = recommended_render_workers(width, height)
        render_workers = min(requested_workers, safe_workers)
        if render_workers != requested_workers:
            print(
                f"  Limiting 4K parallel export to {render_workers} worker(s) "
                f"for available hardware resources"
            )

    # Concatenating independently encoded VP9 segments can produce decoder
    # glitches at segment boundaries. Use the sequential path for VP9.
    if render_workers > 1 and args.codec != 'vp9':
        from recorder.parallel_export import export_parallel

        def _parallel_progress(current, total):
            if current % 10 == 0 or current == total:
                pct = (current / total) * 100 if total else 0
                print(f"\r  Export: {current}/{total} ({pct:.0f}%)", end="", flush=True)

        export_parallel(
            audio_file=args.audio_file,
            output_file=args.export,
            width=width,
            height=height,
            fps=fps,
            preset=args.preset,
            effect_type=args.effect,
            color_palette=args.color,
            background_image=args.background,
            background_opacity=args.background_opacity,
            logo_image=args.logo,
            logo_position=args.logo_position,
            logo_x=args.logo_x / 100.0,
            logo_y=args.logo_y / 100.0,
            logo_scale=args.logo_scale / 100.0,
            logo_opacity=args.logo_opacity / 100.0,
            render_scale=args.render_scale,
            workers=render_workers,
            progress_callback=_parallel_progress,
            video_codec=args.codec,
        )
        print()
        return
    
    print(f"Exporting {args.audio_file} -> {args.export}")
    print(f"  Preset: {preset['name']} ({width}x{height}, {fps}fps)")
    
    # Keep the export bounded in memory.  Loading an hour of decoded audio
    # through pydub costs hundreds of megabytes before the first frame exists.
    sample_rate = 44100
    analysis_chunk_size = max(64, int(math.ceil(sample_rate / fps)))
    analyzer = AudioAnalyzer(
        args.audio_file,
        chunk_size=analysis_chunk_size,
        sample_rate=sample_rate,
        loop=False,
        load_file=False,
    )
    reader = AudioFrameReader(
        args.audio_file,
        sample_rate=sample_rate,
        fps=fps,
        channels=1,
        analysis_chunk_size=analysis_chunk_size,
    )
    analyzer.start_stream()

    render_scale = min(1.0, max(0.1, args.render_scale))
    render_width = max(1, int(width * render_scale))
    render_height = max(1, int(height * render_scale))

    class ExportRenderer:
        def __init__(self, w, h):
            self.width = w
            self.height = h

    effect_manager = EffectManager(
        analyzer=analyzer,
        renderer=ExportRenderer(render_width, render_height),
        effect_type=args.effect,
        color_palette=args.color,
        background_image=args.background,
        background_opacity=args.background_opacity,
        logo_image=args.logo,
        logo_position=args.logo_position,
        logo_x=args.logo_x / 100.0,
        logo_y=args.logo_y / 100.0,
        logo_scale=args.logo_scale / 100.0,
        logo_opacity=args.logo_opacity / 100.0,
    )
    effect_manager.init()
    
    # The analyzer can intentionally use synthetic data under NO_SOUND=1;
    # export duration must always describe the real source file.
    try:
        ffprobe_path = os.environ.get('FFPROBE_PATH') or 'ffprobe'
        duration_cmd = [
            ffprobe_path, '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            args.audio_file,
        ]
        duration_env = os.environ.copy()
        self_dir = duration_env.get('SELF_DIR')
        try:
            bundled_ffprobe = self_dir and os.path.realpath(ffprobe_path).startswith(
                os.path.realpath(self_dir) + os.sep
            )
        except OSError:
            bundled_ffprobe = False
        if bundled_ffprobe:
            duration_env['LD_LIBRARY_PATH'] = os.path.join(self_dir, 'usr', 'lib')
        else:
            duration_env.pop('LD_LIBRARY_PATH', None)
        duration_result = subprocess.run(
            duration_cmd, capture_output=True, text=True,
            timeout=10, env=duration_env,
        )
        audio_duration = float(duration_result.stdout.strip())
        if duration_result.returncode != 0 or audio_duration <= 0:
            raise ValueError("invalid duration")
    except (OSError, ValueError, subprocess.SubprocessError):
        audio_duration = analyzer.get_duration_seconds()
    import math as _math
    total_frames = int(_math.ceil(audio_duration * fps - 1e-4))
    print(f"  Duration: {audio_duration:.0f}s, Frames: {total_frames}")
    if render_scale < 1.0:
        print(f"  Render scale: {render_scale}x ({render_width}x{render_height})")
    
    import threading, queue, cv2

    from quality_presets import codec_for_output
    effective_codec, target_export = codec_for_output(args.codec, args.export)
    is_webm = target_export.lower().endswith('.webm')
    partial_output = f"{target_export}.part.webm" if is_webm else f"{target_export}.part.mp4"
    ffmpeg_cmd = build_ffmpeg_cmd(width, height, fps, args.audio_file,
                                  partial_output, args.preset,
                                  render_width=render_width,
                                  render_height=render_height,
                                  video_codec=effective_codec)

    # Vérifier que le fichier audio existe
    if not os.path.exists(args.audio_file):
        raise FileNotFoundError(f"Audio file not found: {args.audio_file}")

    # Vérifier que le dossier de sortie existe
    output_dir = os.path.dirname(args.export)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    stderr_log = tempfile.TemporaryFile(mode="w+b")
    ffmpeg_env = os.environ.copy()
    self_dir = ffmpeg_env.get('SELF_DIR')
    try:
        bundled_ffmpeg = self_dir and os.path.realpath(
            os.environ.get('FFMPEG_PATH') or 'ffmpeg'
        ).startswith(os.path.realpath(self_dir) + os.sep)
    except OSError:
        bundled_ffmpeg = False
    if bundled_ffmpeg:
        bundled_libs = os.path.join(self_dir, 'usr', 'lib')
        ffmpeg_env['LD_LIBRARY_PATH'] = (
            f"{bundled_libs}:{ffmpeg_env.get('LD_LIBRARY_PATH', '')}"
        ).rstrip(':')
    else:
        ffmpeg_env.pop('LD_LIBRARY_PATH', None)
    try:
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=stderr_log,
            env=ffmpeg_env,
        )
    except Exception:
        stderr_log.close()
        raise

    def _ffmpeg_diagnostic(prefix):
        returncode = process.poll()
        try:
            stderr_log.seek(0)
            detail = stderr_log.read().decode('utf-8', errors='ignore').strip()
        except Exception:
            detail = ''
        if returncode == -9:
            hint = ' (process killed by the OS, usually because of memory pressure)'
        elif returncode is None:
            hint = ''
        else:
            hint = f' (exit code {returncode})'
        return f"{prefix}{hint}:\n{detail or 'no FFmpeg diagnostic was produced'}"
    
    frames_written = 0
    # Two frames are enough to overlap rendering and encoding while avoiding
    # hundreds of megabytes of queued 4K RGB/BGR buffers.
    frame_queue = queue.Queue(maxsize=2)
    _SENTINEL = object()
    writer_error = None

    def _pipe_writer():
        nonlocal writer_error, frames_written
        try:
            while True:
                item = frame_queue.get()
                if item is _SENTINEL:
                    frame_queue.task_done()
                    break
                if process.poll() is not None:
                    writer_error = _ffmpeg_diagnostic("FFmpeg process exited early")
                    frame_queue.task_done()
                    break
                try:
                    process.stdin.write(item)
                    frames_written += 1
                except (BrokenPipeError, ConnectionResetError, ValueError, OSError) as e:
                    writer_error = f"Pipe error: {e}"
                    frame_queue.task_done()
                    break
                frame_queue.task_done()
        except Exception as e:
            writer_error = str(e)

    writer_thread = threading.Thread(target=_pipe_writer, daemon=True)
    writer_thread.start()
    
    export_succeeded = False
    frame_count = 0
    try:
        for _ in range(total_frames):
            if writer_error or process.poll() is not None:
                break

            # One analysis block corresponds to one output frame.  The old
            # implementation used the analyzer's default 1024 samples here,
            # which made the visual timeline run faster than the video FPS.
            chunk = reader.read_frame()
            if chunk is None:
                # EOF reached before total_frames (MP3 gapless / VBR rounding):
                # pad with silence to honour exact video duration instead of aborting.
                try:
                    import numpy as _np
                    chunk = _np.zeros(analysis_chunk_size, dtype=_np.int16)
                except Exception:
                    chunk = [0] * analysis_chunk_size

            audio_data = analyzer.analyze_chunk(chunk)
            effect_manager.update(audio_data, 1.0/fps)
            frame = effect_manager.render_to_array()

            if frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR, dst=frame)

            buf = memoryview(frame)
            queued = False
            while not queued and not writer_error:
                try:
                    frame_queue.put(buf, timeout=1.0)
                    queued = True
                except queue.Full:
                    if process.poll() is not None:
                        writer_error = _ffmpeg_diagnostic(
                            "FFmpeg process exited unexpectedly"
                        )
                        break

            if not queued:
                break

            frame_count += 1

            if frame_count % 10 == 0 or frame_count == total_frames:
                pct = (frame_count / total_frames) * 100 if total_frames > 0 else 0
                print(f"\r  Export: {frame_count}/{total_frames} ({pct:.0f}%)", end="", flush=True)

        if writer_error:
            raise RuntimeError(_ffmpeg_diagnostic(writer_error))
        if frame_count < total_frames:
            if process.poll() is not None:
                raise RuntimeError(
                    _ffmpeg_diagnostic(
                        f"FFmpeg stopped after {frame_count}/{total_frames} frames"
                    )
                )
            missing = total_frames - frame_count
            print(f"  Warning: export short by {missing} frame(s) "
                  f"({frame_count}/{total_frames}), continuing")

            # Do not abort – finalize with available frames.

        frame_queue.put(_SENTINEL)
        writer_thread.join()
        if writer_error:
            raise RuntimeError(_ffmpeg_diagnostic(writer_error))

        try:
            if process.stdin and not process.stdin.closed:
                process.stdin.close()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        
        # stdin is already closed above, so wait directly instead of calling
        # communicate() on a closed pipe.  This avoids a late ValueError on
        # long encodes and does not impose an arbitrary 30-second finalization
        # limit on large MP4 files.
        process.wait()
        stderr_log.seek(0)
        stderr = stderr_log.read()
        
        print()
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='ignore') if stderr else ''
            raise RuntimeError(f"FFmpeg error (code {process.returncode}):\n{error_msg}")

        if not os.path.exists(partial_output) or os.path.getsize(partial_output) < 1024:
            raise RuntimeError("FFmpeg completed without producing a valid output file")
        os.replace(partial_output, target_export)
        export_succeeded = True
        print(f"[OK] Export completed: {target_export}")
                
    except KeyboardInterrupt:
        print("\n[CANCELLED] Export cancelled by user")
        raise
    finally:
        reader.close()
        analyzer.cleanup()
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except:
                process.kill()
        stderr_log.close()
        if not export_succeeded and os.path.exists(partial_output):
            try:
                os.remove(partial_output)
            except OSError:
                pass
    
    if export_succeeded and os.path.exists(target_export):
        file_size = os.path.getsize(target_export)
        if file_size < 1024:
            raise RuntimeError(f"Output file too small ({file_size} bytes), export likely failed")
        print(f"[OK] Export complete: {target_export} ({file_size/1024/1024:.1f} MB)")
    else:
        raise RuntimeError(f"Output file not created: {target_export}")


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
            # Verify the device index still exists
            devices = AudioPlayer.list_devices()
            available_indices = [d['index'] for d in devices]
            if device_id not in available_indices:
                print(f"Warning: device {device_id} no longer available, using default")
                device_id = None
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
    effect_manager = EffectManager(
        analyzer, renderer, args.effect, args.color,
        background_image=args.background,
        background_opacity=args.background_opacity,
        logo_image=args.logo,
        logo_position=args.logo_position,
        logo_x=args.logo_x / 100.0,
        logo_y=args.logo_y / 100.0,
        logo_scale=args.logo_scale / 100.0,
        logo_opacity=args.logo_opacity / 100.0,
    )
    effect_manager.init()
    
    # Create audio player with resolved device
    audio_player = AudioPlayer(
        sample_rate=analyzer.sample_rate,
        chunk_size=analyzer.chunk_size,
        channels=2,
        device_id=device_id,
    )
    audio_player.start()
    
    try:
        while renderer.handle_events():
            chunk = analyzer.get_next_chunk()
            if chunk is not None:
                audio_player.play_chunk(chunk)
            audio_data = analyzer.analyze_chunk(chunk)
            effect_manager.update(audio_data, 1.0/fps)
            if _has_pygame:
                effect_manager.render(renderer.get_surface())
            else:
                arr = effect_manager.render_to_array()
                if arr is not None:
                    frame = renderer.get_surface()
                    h, w = min(arr.shape[0], frame.shape[0]), min(arr.shape[1], frame.shape[1])
                    frame[:h, :w] = arr[:h, :w]
            renderer.present()
    finally:
        analyzer.cleanup()
        renderer.cleanup()
        if audio_player:
            audio_player.cleanup()


if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()

    if len(sys.argv) == 1 and has_gui():
        run_gui()
    else:
        run_cli()
