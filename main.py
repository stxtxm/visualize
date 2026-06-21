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
        from ui.main_window import MainWindow
        import tkinter as tk
        root = tk.Tk()
        app = MainWindow(root)
        root.protocol("WM_DELETE_WINDOW", lambda: [app._stop_playback(), root.quit()])
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
                        choices=['bars', 'circles', 'particles', 'tunnel', 'wave', 'random'])
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
    from renderer.cv2_renderer import CV2Renderer
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
    
    renderer = CV2Renderer(width=width, height=height, fps=fps)
    renderer.init()
    
    effect_manager = EffectManager(
        analyzer=analyzer, renderer=renderer,
        effect_type=args.effect, color_palette=args.color
    )
    effect_manager.init()
    
    audio_duration = analyzer.get_duration_seconds()
    total_frames = int(audio_duration * fps)
    print(f"  Duration: {audio_duration:.0f}s, Frames: {total_frames}")
    
    ffmpeg_cmd = build_ffmpeg_cmd(width, height, fps, args.audio_file, args.export, args.preset)
    process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        for frame_count in range(total_frames):
            chunk = analyzer.get_next_chunk()
            audio_data = analyzer.analyze_chunk(chunk) if chunk is not None else analyzer._get_default_result()
            effect_manager.current_effect.update(audio_data, 1.0/fps)
            frame = effect_manager.current_effect.render_to_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            process.stdin.write(frame.tobytes())
            if frame_count % 100 == 0:
                print(f"  Progress: {(frame_count/total_frames)*100:.0f}%")
        # Ne PAS fermer stdin manuellement - communicate() le fera automatiquement
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise RuntimeError(stderr.decode('utf-8', errors='ignore'))
    finally:
        analyzer.cleanup()
        renderer.cleanup()
        if process.poll() is None:
            process.terminate()
    print(f"✓ Export complete: {args.export}")


def run_playback(args):
    from audio.analyzer import AudioAnalyzer
    from renderer.pygame_renderer import PygameRenderer
    from effects.manager import EffectManager
    from quality_presets import get_preset, RESOLUTIONS
    
    preset = get_preset(args.preset)
    res = args.resolution or preset['resolution']
    fps = args.fps or preset['fps']
    width, height = RESOLUTIONS.get(res, (1920, 1080))
    
    analyzer = AudioAnalyzer(args.audio_file, loop=True)
    analyzer.start_stream()
    renderer = PygameRenderer(width, height, args.fullscreen, fps)
    renderer.init()
    effect_manager = EffectManager(analyzer, renderer, args.effect, args.color)
    effect_manager.init()
    
    try:
        while renderer.handle_events():
            chunk = analyzer.get_next_chunk()
            audio_data = analyzer.analyze_chunk(chunk)
            effect_manager.current_effect.update(audio_data, 1.0/fps)
            effect_manager.current_effect.render(renderer.get_surface())
            renderer.present()
    finally:
        analyzer.cleanup()
        renderer.cleanup()


if __name__ == '__main__':
    if len(sys.argv) == 1 and has_gui():
        run_gui()
    else:
        run_cli()
