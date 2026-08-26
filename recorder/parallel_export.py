"""Parallel, native-resolution video export.

The visualizer is stateful, so frames cannot be rendered independently from
one shared effect instance.  This module starts one independent renderer per
contiguous segment.  Each renderer replays the inexpensive audio/effect state
updates up to its segment and renders only its own frames.  The encoded video
segments are concatenated with ``-c:v copy``; the final video is never scaled
or re-encoded during assembly.
"""

import math
import multiprocessing
import os
import queue
import subprocess
import tempfile
import threading
import time
import traceback

import cv2
import numpy as np


_SENTINEL = object()


def _clean_environment():
    """Return an environment suitable for system FFmpeg binaries."""
    env = os.environ.copy()
    self_dir = env.get('SELF_DIR')
    ffmpeg_path = env.get('FFMPEG_PATH', 'ffmpeg')
    if self_dir and ffmpeg_path.startswith(self_dir):
        lib_path = os.path.join(self_dir, 'usr', 'lib')
        env['LD_LIBRARY_PATH'] = f"{lib_path}:{env.get('LD_LIBRARY_PATH', '')}".rstrip(':')
    else:
        env.pop('LD_LIBRARY_PATH', None)
    return env


def _run_ffmpeg(command):
    """Run an assembly FFmpeg command and expose useful diagnostics."""
    result = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        env=_clean_environment(),
    )
    if result.returncode != 0:
        error = result.stderr.decode('utf-8', errors='ignore').strip()
        failed_output = command[-1] if command else None
        if failed_output and failed_output.endswith('.part.mp4') and os.path.exists(failed_output):
            os.remove(failed_output)
        raise RuntimeError(
            f"FFmpeg error (code {result.returncode}):\n{error or 'unknown error'}"
        )


def _segment_ffmpeg_error(process, stderr_log, prefix):
    """Build a useful error for a segment that stopped before the pipe ended."""
    returncode = process.poll()
    if returncode is None:
        try:
            process.wait(timeout=1)
            returncode = process.returncode
        except subprocess.TimeoutExpired:
            pass
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


def _render_segment(config):
    """Render and encode one contiguous video segment."""
    from audio.analyzer import AudioAnalyzer, AudioFrameReader
    from effects.manager import EffectManager
    from quality_presets import build_ffmpeg_cmd
    from utils.frame_guard import FrameOwnershipGuard

    # Each process owns one encoder and one renderer.  Bound OpenCV's native
    # pool as well, otherwise N worker processes can each create N threads.
    cv_threads = max(1, int(config.get('cv_threads', 1)))
    cv2.setNumThreads(cv_threads)

    sample_rate = 44100
    analysis_chunk_size = max(64, int(math.ceil(sample_rate / config['fps'])))
    start_frame = config['start_frame']
    analyzer = AudioAnalyzer(
        config['audio_file'],
        chunk_size=analysis_chunk_size,
        sample_rate=sample_rate,
        loop=False,
        load_file=False,
    )
    reader = AudioFrameReader(
        config['audio_file'],
        sample_rate=sample_rate,
        fps=config['fps'],
        channels=1,
        analysis_chunk_size=analysis_chunk_size,
        start_frame=start_frame,
    )
    analyzer.start_stream()

    class _Renderer:
        def __init__(self, width, height):
            self.width = width
            self.height = height

    manager = EffectManager(
        analyzer=analyzer,
        renderer=_Renderer(config['render_width'], config['render_height']),
        effect_type=config['effect_type'],
        color_palette=config['color_palette'],
        background_image=config['background_image'],
        background_opacity=config['background_opacity'],
        logo_image=config['logo_image'],
        logo_position=config['logo_position'],
        logo_x=config['logo_x'],
        logo_y=config['logo_y'],
        logo_scale=config['logo_scale'],
        logo_opacity=config['logo_opacity'],
    )
    manager.init()

    ffmpeg_cmd = build_ffmpeg_cmd(
        config['width'],
        config['height'],
        config['fps'],
        None,
        config['output_file'],
        config['preset'],
        render_width=config['render_width'],
        render_height=config['render_height'],
        ffmpeg_threads=1,
        video_codec=config.get('video_codec', 'h264'),
    )
    stderr_log = tempfile.TemporaryFile(mode='w+b')
    try:
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=stderr_log,
            env=_clean_environment(),
        )
    except Exception:
        stderr_log.close()
        raise

    frame_queue = queue.Queue(maxsize=2)
    writer_error = None

    def _writer():
        nonlocal writer_error
        try:
            while True:
                item = frame_queue.get()
                try:
                    if item is _SENTINEL:
                        return
                    process.stdin.write(item)
                except (BrokenPipeError, ConnectionResetError, OSError, ValueError) as exc:
                    writer_error = f"Pipe error: {exc}"
                    return
                finally:
                    frame_queue.task_done()
        except Exception as exc:
            writer_error = str(exc)

    writer_thread = threading.Thread(target=_writer, daemon=True)
    writer_thread.start()

    start_frame = config['start_frame']
    end_frame = config['end_frame']
    progress = config.get('progress')
    progress_queue = config.get('progress_queue')
    segment_index = config.get('segment_index', 0)
    cancel_event = config.get('cancel_event')
    local_count = 0
    frame_guard = FrameOwnershipGuard()

    try:
        # Loop only over the segment's own frames.  AudioFrameReader has
        # already seeked to start_frame via FFmpeg -ss, so every read_frame()
        # call returns the next frame in this segment without wasted I/O.
        for frame_index in range(start_frame, end_frame):
            if cancel_event is not None and cancel_event.is_set():
                raise RuntimeError("Export annulé par l'utilisateur")
            chunk = reader.read_frame()
            if chunk is None:
                # Past EOF: synthesize silence to keep video duration exact.
                # This covers MP3 encoder-delay / ffprobe rounding where
                # decodable PCM is a few ms shorter than format duration.
                try:
                    import numpy as _np
                    chunk = _np.zeros(analysis_chunk_size, dtype=_np.int16)
                except Exception:
                    chunk = [0] * analysis_chunk_size
            audio_data = analyzer.analyze_chunk(chunk)
            manager.update(audio_data, 1.0 / config['fps'])
            if writer_error:
                raise RuntimeError(_segment_ffmpeg_error(process, stderr_log, writer_error))
            if process.poll() is not None:
                raise RuntimeError(
                    _segment_ffmpeg_error(process, stderr_log,
                                          "FFmpeg segment exited unexpectedly")
                )

            frame = manager.render_to_array()
            if frame.shape[2] == 3:
                frame = np.ascontiguousarray(frame)

            # Copy-on-recycle protection for this worker's writer thread.
            frame = frame_guard.ensure_owned(frame)

            queued = False
            while not queued and not writer_error:
                try:
                    frame_queue.put(memoryview(frame), timeout=1.0)
                    queued = True
                except queue.Full:
                    if process.poll() is not None:
                        raise RuntimeError(
                            _segment_ffmpeg_error(
                                process, stderr_log,
                                "FFmpeg segment exited unexpectedly"
                            )
                        )
            if not queued:
                raise RuntimeError(
                    _segment_ffmpeg_error(
                        process, stderr_log,
                        writer_error or "Unable to queue frame"
                    )
                )

            local_count += 1
            if progress:
                progress(local_count)
            elif progress_queue and (local_count % 10 == 0 or frame_index + 1 >= end_frame):
                # Progress is deliberately throttled when sent between
                # processes.  A 55-minute mix can contain 100,000 frames;
                # sending one IPC message per frame would become overhead.
                try:
                    progress_queue.put_nowait(
                        ('progress', segment_index, local_count)
                    )
                except queue.Full:
                    pass

        if writer_error:
            raise RuntimeError(_segment_ffmpeg_error(process, stderr_log, writer_error))
        frame_queue.put(_SENTINEL)
        writer_thread.join()
        if writer_error:
            raise RuntimeError(_segment_ffmpeg_error(process, stderr_log, writer_error))
        if process.stdin and not process.stdin.closed:
            process.stdin.close()

        process.wait()
        if process.returncode != 0:
            raise RuntimeError(
                _segment_ffmpeg_error(process, stderr_log, "FFmpeg segment failed")
            )
        return local_count
    finally:
        reader.close()
        analyzer.cleanup()
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        stderr_log.close()


def _segment_process_worker(config, progress_queue, result_queue, cancel_event):
    """Run one renderer in a separate process and report its result.

    Rendering Trance Scope contains Python/OpenCV calls that do not scale
    reliably inside a ThreadPoolExecutor because of the Python GIL.  A
    process per segment gives each renderer its own interpreter and also
    isolates FFmpeg failures from the parent application.
    """
    config = dict(config)
    config['progress'] = None
    config['progress_queue'] = progress_queue
    config['cancel_event'] = cancel_event
    try:
        count = _render_segment(config)
        result_queue.put(('done', config.get('segment_index', 0), count, ''))
    except BaseException:
        result_queue.put((
            'error',
            config.get('segment_index', 0),
            0,
            traceback.format_exc(),
        ))


def export_parallel(audio_file, output_file, width, height, fps, preset,
                    effect_type, color_palette, background_image=None,
                    background_opacity=0.72, logo_image=None,
                    logo_position='top-right', logo_x=0.5, logo_y=0.5,
                    logo_scale=0.18, logo_opacity=1.0, render_scale=1.0,
                    audio_duration=None, workers=2, progress_callback=None,
                    cancel_event=None, video_codec='h264'):
    """Export a native-resolution video using independent parallel segments."""
    if workers < 2:
        raise ValueError("Parallel export requires at least two workers")
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"Audio file not found: {audio_file}")

    from effects.manager import resolve_effect_type
    from quality_presets import codec_for_output

    effective_codec, output_file = codec_for_output(video_codec, output_file)
    is_webm = output_file.lower().endswith('.webm')

    if audio_duration is None:
        ffprobe = os.environ.get('FFPROBE_PATH') or 'ffprobe'
        probe = subprocess.run(
            [ffprobe, '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', audio_file],
            capture_output=True, text=True, timeout=10,
            env=_clean_environment(),
        )
        if probe.returncode != 0:
            raise RuntimeError(f"Unable to determine audio duration: {probe.stderr}")
        audio_duration = float(probe.stdout.strip())

    import math as _math
    total_frames = int(_math.ceil(audio_duration * fps - 1e-4))
    render_scale = min(1.0, max(0.1, float(render_scale)))
    render_width = max(1, int(width * render_scale))
    render_height = max(1, int(height * render_scale))
    effect_type = resolve_effect_type(effect_type)
    workers = min(max(2, int(workers)), max(2, total_frames or 2))

    print(f"Parallel export: {workers} workers, {total_frames} frames (Codec: {effective_codec.upper()})")
    if render_scale < 1.0:
        print(f"  Render scale: {render_scale}x ({render_width}x{render_height})")

    partial_suffix = '.part.webm' if is_webm else '.part.mp4'
    partial_output = f"{output_file}{partial_suffix}"
    output_dir = os.path.dirname(os.path.abspath(output_file))
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Use output_dir for temp segments to avoid filling up /tmp (tmpfs RAM disk).
    # Long 4K exports generate multi-gigabyte segment files; /tmp is limited to RAM size.
    temp_parent = output_dir if (output_dir and os.access(output_dir, os.W_OK)) else None

    completed = [0] * workers
    progress_lock = threading.Lock()
    def make_progress(segment_index, segment_start, segment_end):
        def on_progress(local_count):
            if not progress_callback:
                return
            with progress_lock:
                completed[segment_index] = local_count
                progress_callback(sum(completed), total_frames)
        return on_progress

    with tempfile.TemporaryDirectory(dir=temp_parent, prefix='.visualize-parallel-') as temp_dir:
        # Probe the encoder once before starting workers.  Without this warmup,
        # all workers can race through the hardware/libopenh264 detection.
        from quality_presets import build_ffmpeg_cmd
        # VP9/WebM concat with `-c:v copy` is fragile in the ffmpeg
        # concat demuxer (black flash at segment boundaries). Use Matroska
        # (.mkv) for VP9 intermediates – same VP9/Opus streams, but mkv
        # handles copy-concat reliably and is later muxed to final .webm.
        if is_webm:
            segment_ext = '.mkv'
        elif effective_codec == 'h264':
            segment_ext = '.ts'
        else:
            segment_ext = '.mp4'
            
        build_ffmpeg_cmd(
            width, height, fps, None,
            os.path.join(temp_dir, f'encoder_probe{segment_ext}'),
            preset,
            render_width=render_width,
            render_height=render_height,
            ffmpeg_threads=1,
            video_codec=effective_codec,
        )

        segments = []
        configs = []
        for index in range(workers):
            start = (total_frames * index) // workers
            end = (total_frames * (index + 1)) // workers
            segment_file = os.path.join(temp_dir, f'segment_{index:03d}{segment_ext}')
            segments.append(segment_file)
            configs.append({
                'audio_file': audio_file,
                'output_file': segment_file,
                'width': width,
                'height': height,
                'fps': fps,
                'preset': preset,
                'effect_type': effect_type,
                'color_palette': color_palette,
                'background_image': background_image,
                'background_opacity': background_opacity,
                'logo_image': logo_image,
                'logo_position': logo_position,
                'logo_x': logo_x,
                'logo_y': logo_y,
                'logo_scale': logo_scale,
                'logo_opacity': logo_opacity,
                'render_width': render_width,
                'render_height': render_height,
                'start_frame': start,
                'end_frame': end,
                'segment_index': index,
                'progress': make_progress(index, start, end),
                'cancel_event': cancel_event,
                'video_codec': effective_codec,
            })

        # The renderers must be separate processes.  Trance Scope spends a
        # meaningful part of each frame in Python loops and OpenCV calls; a
        # ThreadPoolExecutor leaves those loops contending for one GIL.  A
        # process also prevents one FFmpeg abort from taking down all workers.
        ctx = multiprocessing.get_context('spawn')
        progress_queue = ctx.Queue(maxsize=max(32, workers * 8))
        result_queue = ctx.Queue()
        process_cancel = ctx.Event()
        processes = []
        completed_count = [0] * workers
        finished_workers = set()
        worker_error = None
        all_dead_since = None

        # Do not pass threading callbacks/events through the process boundary.
        worker_configs = []
        for config in configs:
            worker_config = dict(config)
            worker_config['cv_threads'] = max(
                1, (os.cpu_count() or 2) // workers
            )
            worker_config.pop('progress', None)
            worker_config.pop('cancel_event', None)
            worker_configs.append(worker_config)

        try:
            for config in worker_configs:
                process = ctx.Process(
                    target=_segment_process_worker,
                    args=(config, progress_queue, result_queue, process_cancel),
                    daemon=False,
                )
                process.start()
                processes.append(process)

            while len(finished_workers) < workers:
                if cancel_event is not None and cancel_event.is_set():
                    process_cancel.set()

                # Drain all progress updates sent by worker processes
                while True:
                    try:
                        p_msg = progress_queue.get_nowait()
                        if p_msg[0] == 'progress':
                            completed_count[p_msg[1]] = p_msg[2]
                            if progress_callback:
                                with progress_lock:
                                    progress_callback(sum(completed_count), total_frames)
                    except queue.Empty:
                        break

                try:
                    message = result_queue.get(timeout=0.1)
                except queue.Empty:
                    dead = [process for process in processes if not process.is_alive()]
                    failed = next(
                        (process for process in dead if process.exitcode not in (0, None)),
                        None,
                    )
                    if failed:
                        worker_error = (
                            f"Parallel renderer process {failed.pid} exited "
                            f"with code {failed.exitcode}"
                        )
                        break
                    if len(dead) == len(processes):
                        # A multiprocessing.Queue can need a short moment to
                        # flush the final result after the child has exited
                        # cleanly.  Only declare a silent worker dead after
                        # that grace period.
                        all_dead_since = all_dead_since or time.monotonic()
                        if time.monotonic() - all_dead_since > 3.0:
                            worker_error = (
                                "Parallel renderer processes exited without "
                                "returning a result"
                            )
                            break
                    else:
                        all_dead_since = None
                    continue

                kind, index, count, detail = message
                all_dead_since = None
                if kind == 'progress':
                    completed_count[index] = count
                    if progress_callback:
                        with progress_lock:
                            progress_callback(sum(completed_count), total_frames)
                elif kind == 'done':
                    completed_count[index] = count
                    finished_workers.add(index)
                    if progress_callback:
                        with progress_lock:
                            progress_callback(sum(completed_count), total_frames)
                elif kind == 'error':
                    worker_error = detail or (
                        f"Parallel renderer {index} failed"
                    )
                    process_cancel.set()
                    break

            if worker_error:
                raise RuntimeError(worker_error)
        finally:
            if worker_error or (
                cancel_event is not None and cancel_event.is_set()
            ):
                process_cancel.set()
            for process in processes:
                if process.is_alive():
                    process.terminate()
            for process in processes:
                process.join(timeout=10)
            progress_queue.close()
            result_queue.close()
            progress_queue.join_thread()
            result_queue.join_thread()

        list_file = os.path.join(temp_dir, 'segments.txt')
        with open(list_file, 'w', encoding='utf-8') as handle:
            for segment in segments:
                escaped_segment = segment.replace("'", "'\\''")
                handle.write(f"file '{escaped_segment}'\n")

        # Single-pass concat + audio muxing directly to partial_output.
        # This avoids writing a intermediate joined.mp4 copy (~5GB for long 4K mix),
        # halving disk space usage and speeding up final assembly.
        audio_codec_args = ['-c:a', 'libopus', '-b:a', '192k'] if is_webm else ['-c:a', 'aac', '-b:a', '192k']
        movflags_args = [] if is_webm else ['-movflags', '+faststart']

        # Use +genpts to rebuild missing PTS after copy-concat (prevents
        # 1-frame black flash at segment boundaries with VP9/WebM when the
        # concat demuxer leaves a timestamp gap).
        concat_cmd = [
            os.environ.get('FFMPEG_PATH') or 'ffmpeg', '-y',
            '-fflags', '+genpts',
            '-f', 'concat', '-safe', '0', '-i', list_file,
            '-i', audio_file,
            '-map', '0:v:0', '-map', '1:a:0',
            '-c:v', 'copy',
            *audio_codec_args,
            '-af', 'apad,dynaudnorm=peak=0.95',
            '-shortest',
            '-avoid_negative_ts', 'make_zero',
            *movflags_args,
            '-loglevel', 'error', partial_output,
        ]
        _run_ffmpeg(concat_cmd)

    if not os.path.exists(partial_output) or os.path.getsize(partial_output) < 1024:
        if os.path.exists(partial_output):
            os.remove(partial_output)
        raise RuntimeError("Parallel export did not produce a valid output file")

    # Reject unusable/truncated assemblies before publishing. The per-segment
    # loops enforce their own counts; this guards concat/mux regressions.
    from quality_presets import validate_export_output
    validate_export_output(
        partial_output,
        expected_duration=(total_frames / fps) if fps else None,
        fps=fps,
    )
    try:
        os.replace(partial_output, output_file)
    except Exception:
        if os.path.exists(partial_output):
            os.remove(partial_output)
        raise
    if progress_callback:
        progress_callback(total_frames, total_frames)
        print()
    print(f"[OK] Parallel export completed: {output_file}")
