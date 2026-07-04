"""
Audio player module for real-time sound playback.
Supports multiple backends: sounddevice, pyaudio, pygame.mixer, ffplay, aplay.
"""

import os
import sys
import threading
import time
import struct
import subprocess
import tempfile
import warnings


class AudioPlayer:
    """
    Plays audio chunks in real-time through the system's sound card.
    Automatically selects the best available backend.
    """

    def __init__(self, sample_rate=44100, chunk_size=1024, channels=1):
        """
        Initialize the audio player.

        Args:
            sample_rate: Sample rate in Hz
            chunk_size: Number of samples per chunk
            channels: Number of audio channels (1=mono, 2=stereo)
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.is_playing = False
        self._thread = None
        self._buffer = []
        self._buffer_lock = threading.Lock()
        self._backend = None
        self._backend_name = None
        self._stream = None
        self._pyaudio_instance = None
        self._ffplay_process = None
        self._aplay_process = None
        self._temp_wav = None
        # If running inside AppImage, ensure embedded SDL/Pulse libs are available
        self._ensure_appimage_audio_paths()
        # Detect available backends
        self._detect_backend()

    def _ensure_appimage_audio_paths(self):
        """Ensure AppImage embedded audio libraries are available to the runtime."""
        appdir = os.environ.get('APPDIR') or os.environ.get('SNAP') or None
        if appdir is None:
            # Determine if we are running from the local AppImage AppRun layout
            here = os.path.dirname(os.path.abspath(__file__))
            candidate = os.path.abspath(os.path.join(here, '..', '..', '..'))
            if os.path.exists(os.path.join(candidate, 'AppRun')):
                appdir = candidate
        if appdir:
            pygame_libs = os.path.join(appdir, 'usr', 'lib', 'python3.11', 'site-packages', 'pygame.libs')
            pulseaudio_libs = os.path.join(appdir, 'usr', 'lib', 'pulseaudio')
            path_parts = []
            if os.path.isdir(pygame_libs):
                path_parts.append(pygame_libs)
            if os.path.isdir(pulseaudio_libs):
                path_parts.append(pulseaudio_libs)
            if path_parts:
                existing = os.environ.get('LD_LIBRARY_PATH', '')
                new_path = ':'.join(path_parts + [existing]) if existing else ':'.join(path_parts)
                os.environ['LD_LIBRARY_PATH'] = new_path

    def _detect_backend(self):
        """Detect the best available audio playback backend."""
        backends = []

        # 1. sounddevice (best on Linux)
        try:
            import sounddevice as sd
            backends.append(('sounddevice', sd))
        except ImportError:
            pass

        # 2. pyaudio (cross-platform)
        try:
            import pyaudio as pa
            backends.append(('pyaudio', pa))
        except ImportError:
            pass

        # 3. pygame.mixer (already a dependency) - with timeout protection
        try:
            import pygame
            mixer_ok = False
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init(self.sample_rate, -16, self.channels)
                mixer_ok = pygame.mixer.get_init()
            except Exception as exc:
                mixer_ok = False
                warnings.warn(f"Pygame mixer unavailable: {exc}")

            if mixer_ok:
                backends.append(('pygame', pygame))
        except ImportError:
            pass

        # 4. paplay (PulseAudio)
        try:
            result = subprocess.run(
                ['which', 'paplay'],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                backends.append(('paplay', None))
        except Exception:
            pass

        # 5. pw-play (PipeWire)
        try:
            result = subprocess.run(
                ['which', 'pw-play'],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                backends.append(('pw-play', None))
        except Exception:
            pass

        # 6. aplay (via subprocess, ALSA)
        try:
            result = subprocess.run(
                ['which', 'aplay'],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                backends.append(('aplay', None))
        except Exception:
            pass

        # 7. ffplay (via subprocess)
        try:
            result = subprocess.run(
                ['which', 'ffplay'],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                backends.append(('ffplay', None))
        except Exception:
            pass

        if backends:
            self._backend_name, self._backend = backends[0]
            try:
                from ui.log_display import log_message
                log_message(f"AudioPlayer: detected backends {[name for name, _ in backends]}")
                log_message(f"AudioPlayer: Using backend '{self._backend_name}'")
            except Exception:
                pass
        else:
            self._backend_name = None
            self._backend = None
            warnings.warn("Aucun backend audio disponible pour la lecture sonore")

    def start(self):
        """Start the audio player."""
        if self._backend_name is None:
            warnings.warn("AudioPlayer: No backend available, cannot play audio")
            return

        self.is_playing = True

        if self._backend_name == 'sounddevice':
            self._start_sounddevice()
        elif self._backend_name == 'pyaudio':
            self._start_pyaudio()
        elif self._backend_name == 'pygame':
            self._start_pygame()
        elif self._backend_name in ('ffplay', 'aplay', 'paplay', 'pw-play'):
            self._start_subprocess()

    def _start_sounddevice(self):
        """Start sounddevice backend."""
        import sounddevice as sd
        import numpy as np

        def callback(outdata, frames, time_info, status):
            if status:
                print(f"sounddevice status: {status}", file=sys.stderr)
            chunk = self._get_next_chunk()
            if chunk is not None and len(chunk) > 0:
                if isinstance(chunk, list):
                    chunk = np.array(chunk, dtype=np.float32) / 32768.0
                elif hasattr(chunk, 'dtype') and chunk.dtype == np.int16:
                    chunk = chunk.astype(np.float32) / 32768.0
                # Ensure correct length
                if len(chunk) > frames:
                    chunk = chunk[:frames]
                elif len(chunk) < frames:
                    chunk = np.pad(chunk, (0, frames - len(chunk)))
                # Convert mono to stereo if needed
                if self.channels == 2 and chunk.ndim == 1:
                    outdata[:] = np.column_stack((chunk, chunk))
                else:
                    outdata[:] = chunk.reshape(-1, 1) if chunk.ndim == 1 else chunk
            else:
                outdata.fill(0)

        try:
            self._stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=callback,
                blocksize=self.chunk_size
            )
            self._stream.start()
        except Exception as e:
            try:
                from ui.log_display import log_message
                log_message(f"AudioPlayer: sounddevice error: {e}")
            except Exception:
                pass
            self._backend_name = None
            self.is_playing = False

    def _start_pyaudio(self):
        """Start pyaudio backend."""
        import pyaudio as pa

        self._pyaudio_instance = pa.PyAudio()

        def callback(in_data, frame_count, time_info, status):
            chunk = self._get_next_chunk()
            if chunk is not None and len(chunk) > 0:
                if isinstance(chunk, list):
                    data = struct.pack('<' + 'h' * len(chunk), *chunk)
                elif hasattr(chunk, 'tobytes'):
                    data = chunk.tobytes()
                else:
                    data = b'\x00' * frame_count * 2
                return (data, pa.paContinue)
            else:
                return (b'\x00' * frame_count * 2, pa.paContinue)

        try:
            self._stream = self._pyaudio_instance.open(
                format=pa.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=callback
            )
            self._stream.start_stream()
        except Exception as e:
            try:
                from ui.log_display import log_message
                log_message(f"AudioPlayer: pyaudio error: {e}")
            except Exception:
                pass
            self._backend_name = None
            self.is_playing = False

    def _start_pygame(self):
        """Start pygame.mixer backend."""
        import pygame
        # pygame.mixer.init already called in _detect_backend
        self._thread = threading.Thread(target=self._pygame_play_loop, daemon=True)
        self._thread.start()

    def _pygame_play_loop(self):
        """Playback loop for pygame.mixer backend."""
        import pygame
        import numpy as np

        # Create a Sound object buffer
        buffer_size = self.sample_rate * 2  # 1 second buffer
        audio_buffer = np.zeros(buffer_size, dtype=np.int16)

        while self.is_playing:
            chunk = self._get_next_chunk()
            if chunk is not None and len(chunk) > 0:
                if isinstance(chunk, list):
                    chunk_arr = np.array(chunk, dtype=np.int16)
                else:
                    chunk_arr = np.array(chunk, dtype=np.int16)

                # Create sound and play it
                try:
                    sound = pygame.sndarray.make_sound(chunk_arr)
                    sound.play()
                    # Wait approximately for the chunk duration
                    time.sleep(self.chunk_size / self.sample_rate * 0.9)
                except Exception:
                    time.sleep(0.01)
            else:
                time.sleep(0.01)

    def _start_subprocess(self):
        """Start subprocess-based backend (ffplay, aplay, paplay, pw-play)."""
        # For subprocess backends, we write chunks to a pipe
        # This is a simpler approach: write to a temporary WAV file and play it
        self._thread = threading.Thread(target=self._subprocess_play_loop, daemon=True)
        self._thread.start()

    def _subprocess_play_loop(self):
        """Playback loop for subprocess backends."""
        import numpy as np

        # Accumulate chunks into a buffer, then play via subprocess
        buffer_duration = 0.5  # 500ms buffer
        buffer_size = int(self.sample_rate * buffer_duration)
        accumulated = []

        while self.is_playing:
            chunk = self._get_next_chunk()
            if chunk is not None and len(chunk) > 0:
                accumulated.append(chunk)

                # Check total accumulated samples
                total = sum(len(c) if hasattr(c, '__len__') else 1 for c in accumulated)
                if total >= buffer_size:
                    self._play_accumulated(accumulated)
                    accumulated = []
            else:
                if accumulated:
                    self._play_accumulated(accumulated)
                    accumulated = []
                time.sleep(0.01)

        # Play remaining
        if accumulated:
            self._play_accumulated(accumulated)

    def _play_accumulated(self, chunks):
        """Play accumulated audio chunks via subprocess."""
        import numpy as np

        try:
            # Concatenate all chunks
            all_data = []
            for c in chunks:
                if isinstance(c, list):
                    all_data.extend(c)
                elif hasattr(c, 'tolist'):
                    all_data.extend(c.tolist())
                else:
                    all_data.append(c)

            if not all_data:
                return

            # Convert to numpy array
            audio_array = np.array(all_data, dtype=np.int16)

            # Write to a temporary WAV file
            import wave
            fd, path = tempfile.mkstemp(suffix='.wav')
            os.close(fd)

            with wave.open(path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_array.tobytes())

            # Play with the selected backend
            try:
                if self._backend_name == 'ffplay':
                    subprocess.run(
                        ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', path],
                        capture_output=True, timeout=5
                    )
                elif self._backend_name == 'aplay':
                    subprocess.run(
                        ['aplay', '-q', '-f', 'S16_LE', '-r', str(self.sample_rate),
                         '-c', str(self.channels), path],
                        capture_output=True, timeout=5
                    )
                elif self._backend_name == 'paplay':
                    subprocess.run(
                        ['paplay', path],
                        capture_output=True, timeout=5
                    )
                elif self._backend_name == 'pw-play':
                    subprocess.run(
                        ['pw-play', path],
                        capture_output=True, timeout=5
                    )
            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass
            finally:
                try:
                    os.unlink(path)
                except Exception:
                    pass
        except Exception as e:
            try:
                from ui.log_display import log_message
                log_message(f"AudioPlayer: subprocess play error: {e}")
            except Exception:
                pass

    def _get_next_chunk(self):
        """Get the next audio chunk from the buffer."""
        with self._buffer_lock:
            if self._buffer:
                return self._buffer.pop(0)
            return None

    def play_chunk(self, chunk):
        """
        Queue an audio chunk for playback.

        Args:
            chunk: Audio data (list of int16 samples or numpy array)
        """
        if not self.is_playing:
            return
        with self._buffer_lock:
            self._buffer.append(chunk)
            # Limit buffer size to prevent memory issues
            if len(self._buffer) > 100:
                self._buffer = self._buffer[-50:]

    def stop(self):
        """Stop the audio player."""
        self.is_playing = False

        # Clean up backend-specific resources
        if self._stream is not None:
            try:
                if self._backend_name == 'sounddevice':
                    self._stream.stop()
                    self._stream.close()
                elif self._backend_name == 'pyaudio':
                    if self._stream.is_active():
                        self._stream.stop_stream()
                    self._stream.close()
                    if self._pyaudio_instance:
                        self._pyaudio_instance.terminate()
            except Exception:
                pass
            self._stream = None

        if self._ffplay_process:
            try:
                self._ffplay_process.terminate()
            except Exception:
                pass
            self._ffplay_process = None

        if self._aplay_process:
            try:
                self._aplay_process.terminate()
            except Exception:
                pass
            self._aplay_process = None

        # Clear buffer
        with self._buffer_lock:
            self._buffer.clear()

    def cleanup(self):
        """Clean up all resources."""
        self.stop()