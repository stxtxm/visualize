"""
Video recorder module for exporting psychedelic visualizations to MP4.
"""

import subprocess
import numpy as np
import sys
import os
import threading
import queue


class VideoRecorder:
    """
    Exports audio visualization as MP4 video using FFmpeg.
    """

    def __init__(self, audio_file, output_file, width=1920, height=1080,
                 fps=60, effect_type='random', color_palette='psychedelic',
                 background_image=None, background_opacity=0.72,
                 render_scale=1.0):
        """
        Initialize the video recorder.

        Args:
            audio_file: Path to input audio file
            output_file: Path to output video file
            width: Video width in pixels
            height: Video height in pixels
            fps: Frames per second
            effect_type: Type of visual effect to use
            color_palette: Color palette to use
            background_image: Path to optional background image
            background_opacity: Blend opacity for background image (0.0-1.0)
            render_scale: Scale factor for rendering (0.25-1.0).
                          Lower values render at reduced resolution for
                          faster export; ffmpeg upscales to target resolution.
                          1.0 = full resolution (default).
        """
        self.audio_file = audio_file
        self.output_file = output_file
        self.width = width
        self.height = height
        self.fps = fps
        self.effect_type = effect_type
        self.color_palette = color_palette
        self.background_image = background_image
        self.background_opacity = background_opacity
        self.render_scale = min(1.0, max(0.1, render_scale))
        self._render_width = max(1, int(width * self.render_scale))
        self._render_height = max(1, int(height * self.render_scale))
        self._ffmpeg_cmd = self._build_ffmpeg_command()
        self._process = None
        self._cancelled = False

    def _build_ffmpeg_command(self):
        """Build the FFmpeg command for encoding."""
        from quality_presets import build_ffmpeg_cmd
        return build_ffmpeg_cmd(
            self.width,
            self.height,
            self.fps,
            self.audio_file,
            self.output_file,
            'normal',
            render_width=self._render_width,
            render_height=self._render_height,
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

    def _default_effect_generator(self):
        """Generates visualizer frames sequentially from the audio file with 0 RAM overhead."""
        from audio.analyzer import AudioAnalyzer, AudioStreamReader
        from effects.manager import EffectManager

        analyzer = AudioAnalyzer(self.audio_file, sample_rate=44100, chunk_size=1024, load_file=False)
        analyzer.start_stream()
        reader = AudioStreamReader(self.audio_file, sample_rate=44100, chunk_size=1024, channels=1)

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
            while True:
                chunk = reader.read_chunk()
                if chunk is None:
                    break
                audio_data = analyzer.analyze_chunk(chunk)
                manager.update(audio_data, delta_time)
                frame = manager.render_to_array()
                yield frame
        finally:
            reader.close()

    def cancel(self):
        """Cancel an ongoing export."""
        self._cancelled = True
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
        if effect_generator is None:
            effect_generator = self._default_effect_generator()

        # Validate audio file
        if not os.path.exists(self.audio_file):
            raise FileNotFoundError(f"Audio file not found: {self.audio_file}")

        # Get audio duration
        audio_duration = self._get_audio_duration(self.audio_file)
        total_frames = int(audio_duration * self.fps)

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

        self._process = subprocess.Popen(
            self._ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )

        # Thread-safe queue + sentinel for the async pipe writer
        frame_queue = queue.Queue(maxsize=8)
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
                    if self._process.poll() is not None:
                        writer_error = f"FFmpeg exited early"
                        frame_queue.task_done()
                        break
                    try:
                        self._process.stdin.write(item)
                    except (BrokenPipeError, ConnectionResetError, ValueError, IOError, OSError) as e:
                        writer_error = f"Pipe error: {e}"
                        frame_queue.task_done()
                        break
                    frame_queue.task_done()
            except Exception as e:
                writer_exception = e

        writer_thread = threading.Thread(target=_pipe_writer, daemon=True)
        writer_thread.start()

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

                    # Convert RGB to BGR (FFmpeg expects bgr24 pixel format)
                    if frame.shape[2] == 3:
                        frame = frame[:, :, ::-1]

                # Queue the frame bytes for the writer thread, blocking with a short timeout to check for errors/cancellation
                queued = False
                while not queued and not self._cancelled and not writer_error:
                    try:
                        frame_queue.put(frame.tobytes(), timeout=1.0)
                        queued = True
                    except queue.Full:
                        if self._process.poll() is not None:
                            writer_error = "FFmpeg process exited unexpectedly"
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
            try:
                frame_queue.put(_SENTINEL, timeout=5)
            except queue.Full:
                pass
            writer_thread.join(timeout=10)

            # Close stdin to signal FFmpeg that we're done
            try:
                if self._process.stdin and not self._process.stdin.closed:
                    self._process.stdin.close()
            except Exception as e:
                print(f"Warning when closing stdin: {e}")

            # Wait for FFmpeg to finish
            try:
                stdout, stderr = self._process.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                self._process.kill()
                stdout, stderr = self._process.communicate()
                raise RuntimeError("FFmpeg timeout - export took too long")
            except (ValueError, OSError):
                # stdin pipe already broken — FFmpeg already exited
                if self._process.returncode is None:
                    self._process.wait(timeout=5)
                stdout, stderr = (b'', b'')

            if self._process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else 'Unknown error'
                print(f"FFmpeg stderr output:\n{error_msg}")
                raise RuntimeError(f"FFmpeg error (code {self._process.returncode}):\n{error_msg}")

            print(f"\nVideo exported successfully: {self.output_file}")

        except Exception as e:
            print(f"Export failed with error: {type(e).__name__}: {e}")
            # Try to get FFmpeg's output in case of crash
            if self._process:
                try:
                    stdout, stderr = self._process.communicate(timeout=5)
                    if stderr:
                        print(f"FFmpeg stderr:\n{stderr.decode('utf-8', errors='ignore')}")
                except:
                    pass
            raise
        finally:
            if self._process and self._process.poll() is None:
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except:
                    self._process.kill()
            self._process = None

    def cleanup(self):
        """Clean up resources."""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except:
                self._process.kill()
        self._process = None
