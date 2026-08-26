"""
Video recorder module for exporting psychedelic visualizations to MP4.
"""

import subprocess
import numpy as np
import sys
import os
import threading
import queue
import tempfile
import math

from utils.frame_guard import FrameOwnershipGuard


class VideoRecorder:
    """
    Exports audio visualization as MP4 video using FFmpeg.
    """

    def __init__(self, audio_file, output_file, width=1920, height=1080,
                 fps=60, effect_type='random', color_palette='psychedelic',
                 background_image=None, background_opacity=0.72,
                 render_scale=1.0, logo_image=None,
                 logo_position='top-right', logo_x=0.5, logo_y=0.5,
                 logo_scale=0.18, logo_opacity=1.0, render_workers=1,
                 preset='normal', video_codec='h264'):
        """
        Initialize the video recorder.
        """
        from quality_presets import codec_for_output
        self.audio_file = audio_file
        self.video_codec, self.output_file = codec_for_output(video_codec, output_file)
        self.width = width
        self.height = height
        self.fps = fps
        self.effect_type = effect_type
        self.color_palette = color_palette
        self.background_image = background_image
        self.background_opacity = background_opacity
        self.logo_image = logo_image
        self.logo_position = logo_position
        self.logo_x = max(0.0, min(1.0, float(logo_x)))
        self.logo_y = max(0.0, min(1.0, float(logo_y)))
        self.logo_scale = max(0.01, min(1.0, float(logo_scale)))
        self.logo_opacity = max(0.0, min(1.0, float(logo_opacity)))
        self.render_scale = min(1.0, max(0.1, render_scale))
        self.render_workers = max(1, int(render_workers))
        self.preset = preset
        self._render_width = max(1, int(width * self.render_scale))
        self._render_height = max(1, int(height * self.render_scale))
        is_webm = self.output_file.lower().endswith('.webm')
        partial_suffix = '.part.webm' if is_webm else '.part.mp4'
        self._partial_output_file = f"{self.output_file}{partial_suffix}"
        self._ffmpeg_cmd = self._build_ffmpeg_command()
        self._process = None
        self._cancelled = False
        self._parallel_cancel_event = threading.Event()
        from effects.logo_overlay import LogoOverlay
        self._logo_overlay = LogoOverlay(
            self._render_width, self._render_height,
            image_path=self.logo_image,
            position=self.logo_position,
            x=self.logo_x,
            y=self.logo_y,
            scale=self.logo_scale,
            opacity=self.logo_opacity,
        )

    def _build_ffmpeg_command(self):
        """Build the FFmpeg command for encoding."""
        from quality_presets import build_ffmpeg_cmd
        return build_ffmpeg_cmd(
            self.width,
            self.height,
            self.fps,
            self.audio_file,
            self._partial_output_file,
            self.preset,
            render_width=self._render_width,
            render_height=self._render_height,
            video_codec=self.video_codec,
        )

    def _get_audio_duration(self, audio_file):
        """Get duration of audio file in seconds."""
        import os
        try:
            # Use ffprobe to get duration
            import subprocess
            ffprobe_path = os.environ.get('FFPROBE_PATH') or 'ffprobe'
            cmd = [
                ffprobe_path,
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                audio_file
            ]

            # Prepare environment
            env = os.environ.copy()
            self_dir = os.environ.get('SELF_DIR')
            ffmpeg_path = os.environ.get('FFMPEG_PATH', 'ffmpeg')
            if self_dir and ffmpeg_path.startswith(self_dir):
                # If using bundled FFmpeg/ffprobe, add SELF_DIR/usr/lib to LD_LIBRARY_PATH
                lib_path = os.path.join(self_dir, 'usr', 'lib')
                if 'LD_LIBRARY_PATH' in env:
                    env['LD_LIBRARY_PATH'] = f"{lib_path}:{env['LD_LIBRARY_PATH']}"
                else:
                    env['LD_LIBRARY_PATH'] = lib_path
            else:
                # For system FFmpeg/ffprobe, remove LD_LIBRARY_PATH to avoid conflicts
                env.pop('LD_LIBRARY_PATH', None)

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                env=env
            )
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                return duration
        except Exception:
            pass

        # Fallback: estimate from file size
        # Assume MP3 at 128 kbps
        file_size = os.path.getsize(audio_file)
        bitrate = 128000  # 128 kbps
        duration = (file_size * 8) / bitrate
        return duration

    def _default_effect_generator(self, total_frames=None):
        """Generates visualizer frames sequentially from the audio file with 0 RAM overhead.

        When *total_frames* is provided and the decodable PCM stream ends early
        (MP3 gapless / VBR estimation gap), silent chunks keep feeding the
        analyzer so exactly *total_frames* frames are produced. The encoded
        video therefore always reaches its intended duration instead of
        stopping a few frames short.
        """
        from audio.analyzer import AudioAnalyzer, AudioFrameReader
        from effects.manager import EffectManager

        sample_rate = 44100
        # Match the decoded audio window to the video clock: one frame gets
        # one FPS-sized block of samples.  A fixed 1024-sample block made a
        # 30 FPS export consume audio at roughly 43 FPS.
        chunk_size = max(64, int(math.ceil(sample_rate / self.fps)))
        analyzer = AudioAnalyzer(
            self.audio_file,
            sample_rate=sample_rate,
            chunk_size=chunk_size,
            load_file=False,
        )
        analyzer.start_stream()
        reader = AudioFrameReader(
            self.audio_file,
            sample_rate=sample_rate,
            fps=self.fps,
            channels=1,
            analysis_chunk_size=chunk_size,
        )

        class _Renderer:
            def __init__(self, w, h):
                self.width = w
                self.height = h

        manager = EffectManager(
            analyzer=analyzer,
            renderer=_Renderer(self._render_width, self._render_height),
            effect_type=self.effect_type,
            color_palette=self.color_palette,
            background_image=self.background_image,
            background_opacity=self.background_opacity
        )
        manager.init()

        delta_time = 1.0 / self.fps

        try:
            produced = 0
            while True:
                chunk = reader.read_frame()
                if chunk is None:
                    # MP3 gapless / VBR: decodable PCM can stop before the
                    # ffprobe-reported duration that defined total_frames.
                    # Pad silence so the export reaches its exact target;
                    # mirrors what run_export() already does.
                    if total_frames is None or produced >= total_frames:
                        break
                    try:
                        import numpy as _np
                        chunk = _np.zeros(chunk_size, dtype=_np.int16)
                    except Exception:
                        chunk = [0] * chunk_size
                audio_data = analyzer.analyze_chunk(chunk)
                manager.update(audio_data, delta_time)
                yield manager.render_to_array()
                produced += 1
        finally:
            reader.close()
            analyzer.cleanup()

    def cancel(self):
        """Cancel an ongoing export."""
        self._cancelled = True
        self._parallel_cancel_event.set()
        self.cleanup()

    def record(self, effect_generator=None, progress_callback=None):
        """
        Record the visualization to a video file.

        Uses a threaded pipe writer to overlap frame rendering with
        ffmpeg encoding for maximum throughput.

        Args:
            effect_generator: A callable or iterator that yields frames
                           as numpy arrays (height, width, 3) in RGB format.
                           If None, an internal generator is automatically created
                           to stream and render the visual effect.
            progress_callback: Optional callable(frame_count, total_frames)
                           called periodically during export for UI progress updates.
        """
        import os
        generated_from_audio = effect_generator is None
        self._parallel_cancel_event.clear()

        # Validate audio file
        if not os.path.exists(self.audio_file):
            raise FileNotFoundError(f"Audio file not found: {self.audio_file}")

        # Get audio duration
        audio_duration = self._get_audio_duration(self.audio_file)

        # Compute the frame budget before building the generator so the
        # internal renderer can pad truncated sources up to total_frames.
        # ceil preserves tail up to one frame (<33 ms). Subtract a tiny
        # epsilon to avoid floating-point ceil overshoot on exact multiples
        # (e.g. 3289.766667*30 = 98693.00001).
        import math
        total_frames = int(math.ceil(audio_duration * self.fps - 1e-4))

        if effect_generator is None:
            effect_generator = self._default_effect_generator(total_frames)
        elif callable(effect_generator):
            effect_generator = effect_generator()

        # Defence-in-depth against recycled effect buffers: a single cached
        # array returned twice lets the async writer read bytes the next
        # render overwrote (torn/black flashes). See AGENTS.md ownership rule.
        frame_guard = FrameOwnershipGuard()

        # VP9 segment concatenation is not reliable across all decoders;
        # encode it as one continuous stream to avoid boundary flashes.
        if (
            generated_from_audio
            and self.render_workers > 1
            and self.video_codec != 'vp9'
        ):
            from recorder.parallel_export import export_parallel
            from quality_presets import recommended_render_workers
            safe_workers = self.render_workers
            if self.width >= 3840:
                safe_workers = min(safe_workers, recommended_render_workers(
                    self.width, self.height
                ))
            if safe_workers > 1:
                export_parallel(
                    audio_file=self.audio_file,
                    output_file=self.output_file,
                    width=self.width,
                    height=self.height,
                    fps=self.fps,
                    preset=self.preset,
                    effect_type=self.effect_type,
                    color_palette=self.color_palette,
                    background_image=self.background_image,
                    background_opacity=self.background_opacity,
                    logo_image=self.logo_image,
                    logo_position=self.logo_position,
                    logo_x=self.logo_x,
                    logo_y=self.logo_y,
                    logo_scale=self.logo_scale,
                    logo_opacity=self.logo_opacity,
                    render_scale=self.render_scale,
                    audio_duration=audio_duration,
                    workers=safe_workers,
                    progress_callback=progress_callback,
                    cancel_event=self._parallel_cancel_event,
                    video_codec=self.video_codec,
                )
                return

        print(f"Exporting {self.audio_file} to {self.output_file}")
        print(f"  Resolution: {self.width}x{self.height}")
        if self.render_scale < 1.0:
            print(f"  Render scale: {self.render_scale}x ({self._render_width}x{self._render_height})")
        print(f"  FPS: {self.fps}")
        print(f"  Duration: {audio_duration:.1f}s")
        print(f"  Total frames: {total_frames}")
        print(f"  Effect: {self.effect_type}")
        print(f"  Colors: {self.color_palette}")
        if self.background_image:
            print(f"  Background: {self.background_image}")
        if self.logo_image:
            print(f"  Logo: {self.logo_image} ({self.logo_position})")
        print()

        # Start FFmpeg process
        # Prepare environment correctly
        env = os.environ.copy()
        self_dir = os.environ.get('SELF_DIR')
        ffmpeg_path = os.environ.get('FFMPEG_PATH', 'ffmpeg')
        if self_dir and ffmpeg_path.startswith(self_dir):
            # If using bundled FFmpeg, add SELF_DIR/usr/lib to LD_LIBRARY_PATH
            lib_path = os.path.join(self_dir, 'usr', 'lib')
            if 'LD_LIBRARY_PATH' in env:
                env['LD_LIBRARY_PATH'] = f"{lib_path}:{env['LD_LIBRARY_PATH']}"
            else:
                env['LD_LIBRARY_PATH'] = lib_path
        else:
            # For system FFmpeg, remove LD_LIBRARY_PATH to avoid conflicts
            env.pop('LD_LIBRARY_PATH', None)

        stderr_log = tempfile.TemporaryFile(mode='w+b')
        try:
            self._process = subprocess.Popen(
                self._ffmpeg_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=stderr_log,
                env=env
            )
        except Exception:
            stderr_log.close()
            raise

        process = self._process

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

        # Thread-safe queue + sentinel for the async pipe writer
        # Keep only a small in-flight window: each 4K BGR frame is ~24 MiB.
        frame_queue = queue.Queue(maxsize=2)
        _SENTINEL = object()
        writer_error = None
        writer_exception = None

        def _pipe_writer():
            nonlocal writer_error, writer_exception
            try:
                while True:
                    item = frame_queue.get()
                    if item is _SENTINEL:
                        frame_queue.task_done()
                        break
                    if process.poll() is not None:
                        writer_error = _ffmpeg_diagnostic("FFmpeg exited early")
                        frame_queue.task_done()
                        break
                    try:
                        process.stdin.write(item)
                    except (BrokenPipeError, ConnectionResetError, ValueError, IOError, OSError) as e:
                        writer_error = f"Pipe error: {e}"
                        frame_queue.task_done()
                        break
                    frame_queue.task_done()
            except Exception as e:
                writer_exception = e

        writer_thread = threading.Thread(target=_pipe_writer, daemon=True)
        writer_thread.start()

        export_succeeded = False
        try:
            frame_count = 0

            for frame in effect_generator:
                if self._cancelled:
                    raise RuntimeError("Export annulé par l'utilisateur")

                # Check for writer thread errors
                # Check for writer thread errors
                if writer_error:
                    print(f"  {writer_error} at frame {frame_count}")
                    break
                if writer_exception:
                    raise RuntimeError(f"Writer thread error: {writer_exception}")

                # Ensure frame is in correct format (height, width, 3)
                if isinstance(frame, np.ndarray):
                    if frame.dtype != np.uint8:
                        frame = frame.astype(np.uint8)

                    # Custom generators are supported too: the recorder owns
                    # the final logo layer for every exported frame.
                    if self.logo_image:
                        self._logo_overlay.set_frame_size(frame.shape[1], frame.shape[0])
                        frame = self._logo_overlay.apply(frame)

                    # Ensure the frame array is contiguous in memory before sending to FFmpeg
                    if frame.shape[2] == 3:
                        frame = np.ascontiguousarray(frame)

                # Copy-on-recycle protection for the async writer thread.
                frame = frame_guard.ensure_owned(frame)

                # Queue the frame bytes for the writer thread, blocking with a short timeout to check for errors/cancellation
                queued = False
                buf = memoryview(frame)
                while not queued and not self._cancelled and not writer_error:
                    try:
                        frame_queue.put(buf, timeout=1.0)
                        queued = True
                    except queue.Full:
                        if process.poll() is not None:
                            writer_error = _ffmpeg_diagnostic(
                                "FFmpeg process exited unexpectedly"
                            )
                            break

                if self._cancelled:
                    raise RuntimeError("Export annulé par l'utilisateur")
                if not queued:
                    break

                frame_count += 1

                if progress_callback:
                    progress_callback(frame_count, total_frames)
                elif frame_count % 100 == 0:
                    progress = (frame_count / total_frames) * 100
                    print(f"Export: {progress:.1f}% ({frame_count}/{total_frames} frames)")

                if total_frames > 0 and frame_count >= total_frames:
                    break

            # Signal writer thread to stop
            if not writer_error:
                frame_queue.put(_SENTINEL)
            writer_thread.join()

            if writer_error:
                raise RuntimeError(_ffmpeg_diagnostic(writer_error))
            if writer_exception:
                raise RuntimeError(f"Writer thread error: {writer_exception}")
            if generated_from_audio and frame_count < total_frames:
                # Audio ended slightly before video duration (MP3 gapless /
                # ffprobe rounding). Pad was already applied in
                # AudioFrameReader; if we are still short, warn and let
                # ffmpeg -shortest trim audio instead of aborting. This is
                # <1 frame (33 ms) for floor rounding, at most a few frames
                # for VBR drift – inaudible vs. aborting export.
                missing = total_frames - frame_count
                print(f"  Warning: audio ended {missing} frame(s) early "
                      f"({frame_count}/{total_frames}), final video will be "
                      f"{frame_count/self.fps:.2f}s (short by {missing/self.fps:.3f}s)")

                # Do not abort – finalize with what we have.

            # Close stdin to signal FFmpeg that we're done
            try:
                if process.stdin and not process.stdin.closed:
                    process.stdin.close()
            except Exception as e:
                print(f"Warning when closing stdin: {e}")

            # stdin is closed explicitly; wait without an arbitrary 30-second
            # timeout, which is too short for finalizing a large MP4.
            process.wait()
            stderr_log.seek(0)
            stderr = stderr_log.read()

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else 'Unknown error'
                print(f"FFmpeg stderr output:\n{error_msg}")
                raise RuntimeError(f"FFmpeg error (code {process.returncode}):\n{error_msg}")

            if not os.path.exists(self._partial_output_file) or os.path.getsize(self._partial_output_file) < 1024:
                raise RuntimeError("FFmpeg completed without producing a valid output file")

            # Fail loudly on unusable/truncated output BEFORE replacing the
            # final artifact; missing ffprobe degrades to a printed notice.
            from quality_presets import validate_export_output

            # Strict duration checking applies to the internal audio-driven
            # generator, which now guarantees exactly total_frames frames.
            # Custom generators define their own frame budget (documented
            # programmatic API), so only structural checks apply to them.
            validate_export_output(
                self._partial_output_file,
                expected_duration=(
                    (total_frames / self.fps)
                    if generated_from_audio and total_frames > 0
                    else None
                ),
                fps=self.fps,
            )
            os.replace(self._partial_output_file, self.output_file)
            export_succeeded = True

            print(f"\nVideo exported successfully: {self.output_file}")

        except Exception as e:
            print(f"Export failed with error: {type(e).__name__}: {e}")
            # Preserve FFmpeg's diagnostic even when the writer fails before
            # the normal wait path is reached.
            if process:
                try:
                    if process.poll() is None:
                        process.terminate()
                        process.wait(timeout=5)
                except:
                    pass
            try:
                stderr_log.seek(0)
                error_output = stderr_log.read()
                if error_output:
                    print(f"FFmpeg stderr:\n{error_output.decode('utf-8', errors='ignore')}")
            except Exception:
                pass
            raise
        finally:
            stderr_log.close()
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except:
                    process.kill()
            if not export_succeeded and os.path.exists(self._partial_output_file):
                try:
                    os.remove(self._partial_output_file)
                except OSError:
                    pass
            self._process = None

    def cleanup(self):
        """Clean up resources."""
        process = self._process
        if process and process.poll() is None:
            try:
                if process.stdin and not process.stdin.closed:
                    process.stdin.close()
            except Exception:
                pass
            process.terminate()
            try:
                process.wait(timeout=5)
            except:
                process.kill()
        self._process = None
