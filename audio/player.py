"""
Audio player module for real-time sound playback.
Supports multiple backends: sounddevice, pyaudio, pygame.mixer (buffer-based).
Uses sounddevice as primary backend for low-latency streaming.
"""

import os
import sys
import threading
import time
import struct
import subprocess
import tempfile
import warnings
import queue
try:
    import numpy as np
    _HAS_NUMPY = True
except Exception:
    _HAS_NUMPY = False
from shutil import which

print("[AudioPlayer] module chargé, numpy=", _HAS_NUMPY, file=sys.stderr, flush=True)


def _log(msg):
    """Log a message safely."""
    print(f"[AudioPlayer] {msg}", file=sys.stderr, flush=True)
    try:
        from ui.log_display import log_message
        log_message(f"AudioPlayer: {msg}")
    except Exception:
        pass


class AudioPlayer:
    """
    Plays audio chunks in real-time through the system's sound card.
    Uses sounddevice as primary backend for low-latency streaming.
    Falls back to pygame.mixer buffers or subprocess if unavailable.
    """

    def __init__(self, sample_rate=44100, chunk_size=1024, channels=2):
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
        self._subproc = None  # persistent subprocess for pw-play/ffplay streaming
        self._is_from_data = False
        
        # Audio queue for streaming backends
        self._audio_queue = queue.Queue(maxsize=64)
        
        # Timestamp tracking for audio/video sync
        self._current_chunk_index = 0
        self._playback_start_time = 0.0
        
        # If running inside AppImage, ensure embedded SDL/Pulse libs are available
        self._ensure_appimage_audio_paths()
        # Detect available backends
        self._detect_backend()

    def _ensure_appimage_audio_paths(self):
        """Ensure AppImage embedded audio libraries are available to the runtime."""
        appdir = os.environ.get('APPDIR') or os.environ.get('SNAP') or None
        if appdir is None:
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
        """
        Detect the best available audio playback backend.
        Uses shutil.which() instead of subprocess.run(['which', ...])
        to avoid hanging on systems with broken subprocess.
        """
        backends = []

        # Check for preferred backend from environment
        preferred = os.environ.get('PREFERRED_AUDIO_BACKEND', '')

        # 1. sounddevice (best on Linux - low latency streaming via PortAudio)
        # sounddevice works with PipeWire via PortAudio's ALSA/Pulse backends
        try:
            import sounddevice as sd
            # Don't test check_output_settings - it can hang on some systems
            backends.append(('sounddevice', sd))
        except ImportError:
            pass

        # 2. pw-play (PipeWire native - best for Fedora 44+ with PipeWire)
        if which('pw-play') is not None:
            backends.append(('pw-play', None))

        # 3. ffplay (compatible - works with PipeWire/Fedora 44)
        if which('ffplay') is not None:
            backends.append(('ffplay', None))

        # 4. pyaudio (cross-platform fallback)
        try:
            import pyaudio as pa
            backends.append(('pyaudio', pa))
        except ImportError:
            pass

        # 5. pygame.mixer buffer-based playback (already a dependency)
        try:
            import pygame
            mixer_ok = False
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init(self.sample_rate, -16, self.channels)
                mixer_ok = pygame.mixer.get_init()
            except Exception:
                mixer_ok = False
            if mixer_ok:
                backends.append(('pygame', pygame))
        except ImportError:
            pass

        # 6. paplay (PulseAudio) - fallback
        if which('paplay') is not None:
            backends.append(('paplay', None))

        # 7. aplay (via subprocess, ALSA)
        if which('aplay') is not None:
            backends.append(('aplay', None))

        # Prioritize preferred backend if set
        if preferred and preferred in [name for name, _ in backends]:
            for i, (name, backend) in enumerate(backends):
                if name == preferred:
                    backends.insert(0, backends.pop(i))
                    break

        if backends:
            self._backend_name, self._backend = backends[0]
            _log(f"detected backends: {[name for name, _ in backends]}")
            _log(f"using backend: '{self._backend_name}'")
        else:
            self._backend_name = None
            self._backend = None
            warnings.warn("Aucun backend audio disponible pour la lecture sonore")

    def get_elapsed_seconds(self):
        """Return elapsed playback time in seconds (for A/V sync)."""
        if self._playback_start_time == 0.0:
            return 0.0
        return time.time() - self._playback_start_time

    def get_current_chunk_index(self):
        """Return the current chunk being played (for A/V sync)."""
        return self._current_chunk_index

    def start(self):
        """Start the audio player."""
        if self._backend_name is None:
            warnings.warn("AudioPlayer: No backend available, cannot play audio")
            return

        self.is_playing = True
        self._is_from_data = False
        self._playback_start_time = time.time()
        self._current_chunk_index = 0

        if self._backend_name == 'sounddevice':
            self._start_sounddevice()
        elif self._backend_name == 'pyaudio':
            self._start_pyaudio()
        elif self._backend_name == 'pygame':
            self._start_pygame()
        elif self._backend_name in ('pw-play', 'ffplay', 'aplay'):
            self._start_stdin_stream()
        elif self._backend_name == 'paplay':
            self._start_subprocess()
        else:
            try:
                self._start_stdin_stream()
            except Exception:
                try:
                    self._start_subprocess()
                except Exception:
                    self.is_playing = False

    def start_from_data(self, audio_data, loop=True):
        """
        Stream audio_data (numpy int16 array) at the correct sample rate,
        completely independent of the visual frame rate.

        This starts a dedicated feeder thread that paces chunk delivery
        to exactly match the sample_rate, preventing the underruns and
        slow-motion audio caused by the 30 FPS visual loop.
        """
        if self._backend_name is None:
            warnings.warn("AudioPlayer: No backend, cannot play")
            return
        if audio_data is None or len(audio_data) == 0:
            warnings.warn("AudioPlayer: No audio data provided")
            return

        self.is_playing = True
        self._is_from_data = True
        self._playback_start_time = time.time()
        self._current_chunk_index = 0

        # Start the appropriate backend infrastructure
        if self._backend_name == 'sounddevice':
            self._start_sounddevice()
        elif self._backend_name == 'pyaudio':
            self._start_pyaudio()
        elif self._backend_name == 'pygame':
            self._start_pygame()
        elif self._backend_name in ('pw-play', 'ffplay', 'aplay'):
            self._start_stdin_stream()
        elif self._backend_name == 'paplay':
            self._start_subprocess()

        # Start the dedicated audio feeder thread
        feeder = threading.Thread(
            target=self._data_feeder_loop,
            args=(audio_data, loop),
            daemon=True
        )
        feeder.start()
        _log(f"start_from_data: backend={self._backend_name}, "
             f"samples={len(audio_data)}, loop={loop}")

    def _data_feeder_loop(self, audio_data, loop=True):
        """
        Feed audio chunks to the backend, naturally paced by blocking I/O (backpressure).
        This eliminates manual sleeps and timing drift on PipeWire.
        """
        total = len(audio_data)
        idx = 0
        
        while self.is_playing:
            end = min(idx + self.chunk_size, total)
            chunk = audio_data[idx:end]
            
            if len(chunk) == 0:
                if loop:
                    idx = 0
                    self._current_chunk_index = 0
                    continue
                else:
                    self.is_playing = False
                    break
                    
            self._current_chunk_index = idx // self.chunk_size
            
            # Envoyer au backend approprié
            if self._backend_name in ('sounddevice', 'pyaudio'):
                # Bloque si la queue est pleine (pression arrière naturelle)
                self._audio_queue.put(chunk)
            elif self._backend_name in ('pw-play', 'ffplay', 'aplay'):
                if self._subproc and self._subproc.stdin:
                    try:
                        if hasattr(chunk, 'tobytes'):
                            data = chunk.tobytes()
                        elif isinstance(chunk, list):
                            data = struct.pack('<' + 'h' * len(chunk), *chunk)
                        else:
                            data = bytes(chunk)
                        # Bloque naturellement si le buffer du pipe est plein
                        self._subproc.stdin.write(data)
                        self._subproc.stdin.flush()
                    except (BrokenPipeError, ValueError, OSError):
                        self.is_playing = False
                        break
            else:
                # Pacing manuel uniquement pour pygame.mixer (qui n'a pas de stdin/queue bloquante)
                chunk_duration = self.chunk_size / self.sample_rate
                time.sleep(chunk_duration)
                with self._buffer_lock:
                    self._buffer.append(chunk)
                    if len(self._buffer) > 48:
                        self._buffer = self._buffer[-24:]
                        
            idx = end

        if not loop:
            self.is_playing = False
            self._current_chunk_index = 0

    def start_from_file(self, audio_file, loop=False, analyzer=None):
        """
        Start playback directly from an audio file using streaming.
        Avoids loading the file into RAM.
        """
        if self._backend_name is None:
            warnings.warn("AudioPlayer: No backend, cannot play")
            return
            
        self.is_playing = True
        self._is_from_data = False
        self._playback_start_time = time.time()
        self._current_chunk_index = 0
        
        # Start the appropriate backend infrastructure
        if self._backend_name == 'sounddevice':
            self._start_sounddevice()
        elif self._backend_name == 'pyaudio':
            self._start_pyaudio()
        elif self._backend_name == 'pygame':
            self._start_pygame()
        elif self._backend_name in ('pw-play', 'ffplay', 'aplay'):
            self._start_stdin_stream()
        elif self._backend_name == 'paplay':
            self._start_subprocess()
            
        # Start file feeder thread
        feeder = threading.Thread(
            target=self._file_feeder_loop,
            args=(audio_file, loop, analyzer),
            daemon=True
        )
        feeder.start()
        _log(f"start_from_file: backend={self._backend_name}, file={audio_file}, loop={loop}")

    def _file_feeder_loop(self, audio_file, loop=False, analyzer=None):
        """Reads audio chunks from file, outputs to backend, and feeds analyzer."""
        from audio.analyzer import AudioStreamReader
        
        # We need stereo chunks (2 channels) for playback
        reader = None
        try:
            reader = AudioStreamReader(audio_file, sample_rate=self.sample_rate, chunk_size=self.chunk_size, channels=2)
        except Exception as e:
            _log(f"Error opening AudioStreamReader: {e}")
            self.is_playing = False
            return
            
        idx = 0
        while self.is_playing:
            samples = reader.read_chunk()
            if samples is None:
                if loop:
                    reader.close()
                    try:
                        reader = AudioStreamReader(audio_file, sample_rate=self.sample_rate, chunk_size=self.chunk_size, channels=2)
                        idx = 0
                        self._current_chunk_index = 0
                        continue
                    except Exception as e:
                        _log(f"Error reopening AudioStreamReader on loop: {e}")
                        self.is_playing = False
                        break
                else:
                    self.is_playing = False
                    break
                    
            self._current_chunk_index = idx
            idx += 1
            
            # 1. Feed backend
            if self._backend_name in ('sounddevice', 'pyaudio'):
                # Send stereo samples to queue
                self._audio_queue.put(samples)
            elif self._backend_name in ('pw-play', 'ffplay', 'aplay'):
                if self._subproc and self._subproc.stdin:
                    try:
                        data = samples.tobytes()
                        self._subproc.stdin.write(data)
                        self._subproc.stdin.flush()
                    except (BrokenPipeError, ValueError, OSError):
                        self.is_playing = False
                        break
            else:
                # Manual pacing (pygame, etc.)
                chunk_duration = self.chunk_size / self.sample_rate
                time.sleep(chunk_duration)
                
            # 2. Feed mono samples to the analyzer
            if analyzer is not None:
                if _HAS_NUMPY:
                    # Convert to mono by averaging channels
                    mono_chunk = samples.mean(axis=1).astype(np.int16)
                else:
                    # Average left and right for each frame
                    mono_chunk = [int((frame[0] + frame[1]) / 2) for frame in samples]
                analyzer.set_current_stream_chunk(mono_chunk)
                
        if reader:
            reader.close()

    def _start_sounddevice(self):
        """Start sounddevice streaming backend."""
        import sounddevice as sd

        def callback(outdata, frames, time_info, status):
            if status:
                print(f"sounddevice status: {status}", file=sys.stderr)
            try:
                chunk = self._audio_queue.get_nowait()
            except queue.Empty:
                outdata.fill(0)
                return

            if chunk is not None and len(chunk) > 0:
                if hasattr(chunk, 'dtype') and chunk.dtype == np.int16:
                    chunk_f32 = chunk.astype(np.float32) / 32768.0
                elif isinstance(chunk, (list, tuple)):
                    chunk_f32 = np.array(chunk, dtype=np.float32) / 32768.0
                else:
                    chunk_f32 = np.asarray(chunk, dtype=np.float32)
                    if np.max(np.abs(chunk_f32)) > 1.0:
                        chunk_f32 = chunk_f32 / 32768.0
                if len(chunk_f32) > frames:
                    chunk_f32 = chunk_f32[:frames]
                elif len(chunk_f32) < frames:
                    chunk_f32 = np.pad(chunk_f32, (0, frames - len(chunk_f32)))
                if self.channels == 2 and chunk_f32.ndim == 1:
                    outdata[:] = np.column_stack((chunk_f32, chunk_f32))
                elif chunk_f32.ndim == 1:
                    outdata[:] = chunk_f32.reshape(-1, 1)
                else:
                    outdata[:] = chunk_f32
            else:
                outdata.fill(0)

        try:
            blocksize = max(self.chunk_size, 512)
            self._stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=callback,
                blocksize=blocksize,
                dtype='float32',
                latency='low'
            )
            self._stream.start()
            _log("sounddevice stream started successfully")
        except Exception as e:
            _log(f"sounddevice error: {e}")
            self._try_fallback()

    def _start_stdin_stream(self):
        """Start a persistent subprocess streaming raw PCM data to stdin."""
        cmd = []
        if self._backend_name == 'pw-play':
            cmd = [
                'pw-play',
                '--raw',
                '--rate=' + str(self.sample_rate),
                '--channels=' + str(self.channels),
                '--format=s16',
                '-'
            ]
        elif self._backend_name == 'ffplay':
            # Map channel count to ffplay layout name
            ch_layout = 'mono' if self.channels == 1 else 'stereo'
            cmd = [
                'ffplay',
                '-nodisp',
                '-autoexit',
                '-loglevel', 'quiet',
                '-f', 's16le',
                '-ar', str(self.sample_rate),
                '-ch_layout', ch_layout,
                '-'
            ]
        elif self._backend_name == 'aplay':
            cmd = [
                'aplay',
                '-q',
                '-f', 'S16_LE',
                '-r', str(self.sample_rate),
                '-c', str(self.channels),
                '-'
            ]
        else:
            raise ValueError(f"Unsupported stdin stream backend: {self._backend_name}")

        try:
            # Lancer le subprocess SANS le LD_LIBRARY_PATH de l'AppImage
            # pour éviter les conflits de libs système (ex: libdb-5.3.so)
            env = os.environ.copy()
            env.pop('LD_LIBRARY_PATH', None)
            self._subproc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                env=env
            )

            if not self._is_from_data:
                self._thread = threading.Thread(target=self._stdin_stream_loop, daemon=True)
                self._thread.start()
                _log(f"{self._backend_name} stdin stream loop thread started (pid={self._subproc.pid})")
            else:
                _log(f"{self._backend_name} stdin stream started in raw direct mode (pid={self._subproc.pid})")

            # Thread pour lire stderr du subprocess et l'afficher
            def _read_stderr(proc, name):
                for line in proc.stderr:
                    print(f"[{name} stderr] {line.decode(errors='ignore').rstrip()}", file=sys.stderr, flush=True)
            stderr_thread = threading.Thread(
                target=_read_stderr, args=(self._subproc, self._backend_name), daemon=True
            )
            stderr_thread.start()
        except Exception as e:
            _log(f"{self._backend_name} stream error: {e}")
            self._try_fallback()

    def _stdin_stream_loop(self):
        """Stream audio chunks directly to subprocess stdin."""
        chunks_written = 0
        while self.is_playing:
            chunk = self._get_next_chunk()
            if chunk is not None and len(chunk) > 0:
                try:
                    if hasattr(chunk, 'tobytes'):
                        data = chunk.tobytes()
                    elif isinstance(chunk, list):
                        data = struct.pack('<' + 'h' * len(chunk), *chunk)
                    else:
                        data = bytes(chunk)
                    if self._subproc and self._subproc.stdin:
                        self._subproc.stdin.write(data)
                        self._subproc.stdin.flush()
                        chunks_written += 1
                        if chunks_written in (1, 10, 50, 100):
                            rc = self._subproc.poll()
                            _log(f"{self._backend_name} chunks_written={chunks_written} proc_alive={rc is None}")
                except (BrokenPipeError, OSError) as e:
                    _log(f"{self._backend_name} pipe broken after {chunks_written} chunks: {e}")
                    self.is_playing = False
                    break
            else:
                time.sleep(0.001)

    def _start_pyaudio(self):
        """Start pyaudio streaming backend."""
        import pyaudio as pa

        self._pyaudio_instance = pa.PyAudio()

        def callback(in_data, frame_count, time_info, status):
            try:
                chunk = self._audio_queue.get_nowait()
            except queue.Empty:
                return (b'\x00' * frame_count * 2, pa.paContinue)

            if chunk is not None and len(chunk) > 0:
                if hasattr(chunk, 'tobytes'):
                    data = chunk.tobytes()
                elif isinstance(chunk, (list, tuple)):
                    data = struct.pack('<' + 'h' * len(chunk), *chunk)
                else:
                    data = b'\x00' * frame_count * 2
                expected_bytes = frame_count * 2
                if len(data) < expected_bytes:
                    data += b'\x00' * (expected_bytes - len(data))
                elif len(data) > expected_bytes:
                    data = data[:expected_bytes]
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
            _log(f"pyaudio error: {e}")
            self._backend_name = None
            self.is_playing = False

    def _start_pygame(self):
        """Start pygame.mixer buffer-based playback with pre-allocated channels."""
        import pygame
        try:
            pygame.mixer.set_num_channels(4)
        except Exception:
            pass
        self._thread = threading.Thread(target=self._pygame_play_loop, daemon=True)
        self._thread.start()

    def _pygame_play_loop(self):
        """Playback loop for pygame.mixer backend."""
        import pygame
        import numpy as np

        num_buffers = 3
        buffers = []
        for _ in range(num_buffers):
            buf = np.zeros(self.chunk_size, dtype=np.int16)
            try:
                sound = pygame.sndarray.make_sound(buf)
                buffers.append(sound)
            except Exception:
                pass

        buffer_idx = 0
        chunk_duration = self.chunk_size / self.sample_rate

        while self.is_playing:
            chunk = self._get_next_chunk()
            if chunk is not None and len(chunk) > 0:
                if isinstance(chunk, list):
                    chunk_arr = np.array(chunk, dtype=np.int16)
                else:
                    chunk_arr = np.array(chunk, dtype=np.int16)
                try:
                    if buffer_idx < len(buffers):
                        try:
                            sound = pygame.sndarray.make_sound(chunk_arr)
                            channel = sound.play()
                            if channel:
                                wait_start = time.time()
                                while channel.get_busy() and time.time() - wait_start < chunk_duration * 1.5:
                                    time.sleep(0.001)
                        except Exception:
                            time.sleep(chunk_duration * 0.5)
                    else:
                        sound = pygame.sndarray.make_sound(chunk_arr)
                        sound.play()
                        time.sleep(chunk_duration * 0.8)
                    buffer_idx += 1
                    self._current_chunk_index += 1
                except Exception:
                    time.sleep(0.001)
            else:
                time.sleep(0.001)

    def _start_subprocess(self):
        """Start subprocess-based backend with temp files (ffplay, aplay, paplay)."""
        self._thread = threading.Thread(target=self._subprocess_play_loop, daemon=True)
        self._thread.start()

    def _subprocess_play_loop(self):
        """Playback loop for subprocess backends."""
        import numpy as np

        buffer_duration = 0.1
        buffer_size = int(self.sample_rate * buffer_duration)
        accumulated = []

        while self.is_playing:
            chunk = self._get_next_chunk()
            if chunk is not None and len(chunk) > 0:
                accumulated.append(chunk)
                self._current_chunk_index += 1
                total = sum(len(c) if hasattr(c, '__len__') else 1 for c in accumulated)
                if total >= buffer_size:
                    self._play_accumulated(accumulated)
                    accumulated = []
            else:
                if accumulated:
                    self._play_accumulated(accumulated)
                    accumulated = []
                time.sleep(0.001)

        if accumulated:
            self._play_accumulated(accumulated)

    def _try_fallback(self):
        """Fallback to pw-play or ffplay when sounddevice fails."""
        if which('pw-play') is not None:
            _log("falling back to pw-play stream")
            self._backend_name = 'pw-play'
            self._start_stdin_stream()
        elif which('ffplay') is not None:
            _log("falling back to ffplay stream")
            self._backend_name = 'ffplay'
            self._start_stdin_stream()
        else:
            _log("no fallback available, audio disabled")
            self._backend_name = None
            self.is_playing = False

    def _play_accumulated(self, chunks):
        """Play accumulated audio chunks via subprocess with temp file."""
        import numpy as np

        try:
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

            audio_array = np.array(all_data, dtype=np.int16)

            import wave
            fd, path = tempfile.mkstemp(suffix='.wav')
            os.close(fd)

            with wave.open(path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_array.tobytes())

            try:
                timeout = max(2.0, len(all_data) / self.sample_rate + 2.0)
                if self._backend_name == 'ffplay':
                    result = subprocess.run(
                        ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', path],
                        capture_output=True, timeout=timeout
                    )
                    if result.returncode != 0:
                        stderr = result.stderr.decode('utf-8', errors='ignore')[:200]
                        if stderr:
                            _log(f"ffplay error (rc={result.returncode}): {stderr}")
                elif self._backend_name == 'aplay':
                    subprocess.run(
                        ['aplay', '-q', '-f', 'S16_LE', '-r', str(self.sample_rate),
                         '-c', str(self.channels), path],
                        capture_output=True, timeout=timeout
                    )
                elif self._backend_name == 'paplay':
                    subprocess.run(
                        ['paplay', path],
                        capture_output=True, timeout=timeout
                    )
            except subprocess.TimeoutExpired:
                _log(f"{self._backend_name} timeout")
            except Exception as e:
                _log(f"{self._backend_name} error: {e}")
            finally:
                try:
                    os.unlink(path)
                except Exception:
                    pass
        except Exception as e:
            _log(f"subprocess play error: {e}")

    def _get_next_chunk(self):
        """Get the next audio chunk from the buffer."""
        with self._buffer_lock:
            if self._buffer:
                return self._buffer.pop(0)
            return None

    def play_chunk(self, chunk):
        """
        Queue an audio chunk for playback.
        For sounddevice/pyaudio backends, uses a queue for streaming.
        For other backends, uses a buffer list.

        Args:
            chunk: Audio data (list of int16 samples or numpy array)
        """
        if not self.is_playing:
            return
        if self._is_from_data:
            return
        
        self._current_chunk_index += 1
        
        # For streaming backends (sounddevice, pyaudio), use the queue
        if self._backend_name in ('sounddevice', 'pyaudio'):
            try:
                self._audio_queue.put_nowait(chunk)
            except queue.Full:
                pass
        else:
            # For pygame/subprocess backends, use buffer list
            with self._buffer_lock:
                self._buffer.append(chunk)
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

        # Close persistent subprocess (pw-play stream)
        if self._subproc is not None:
            try:
                if self._subproc.stdin:
                    self._subproc.stdin.close()
            except Exception:
                pass
            try:
                self._subproc.terminate()
                self._subproc.wait(timeout=1)
            except Exception:
                try:
                    self._subproc.kill()
                except Exception:
                    pass
            self._subproc = None

        # Clear queues
        with self._buffer_lock:
            self._buffer.clear()
        try:
            while True:
                self._audio_queue.get_nowait()
        except queue.Empty:
            pass

    def cleanup(self):
        """Clean up all resources."""
        self.stop()