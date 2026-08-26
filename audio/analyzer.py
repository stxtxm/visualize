"""
Module d'analyse audio utilisant FFT pour extraire les caractéristiques du son.
"""

import math
from collections import deque
import os
import sys
import subprocess
import tempfile

# Importer numpy conditionnellement - vérifier NO_SOUND AVANT l'import
no_sound = os.environ.get('NO_SOUND', '').lower() in ('1', 'true', 'yes')

HAS_NUMPY = False
if not no_sound:
    try:
        import numpy as np
        HAS_NUMPY = True
    except ImportError:
        HAS_NUMPY = False
        import warnings
        warnings.warn("numpy non disponible, utilisation de données audio simulées")
else:
    # En mode NO_SOUND, on n'a pas besoin de numpy
    HAS_NUMPY = False


class AudioStreamReader:
    """Streams mono/stereo audio chunks from any file using ffmpeg."""
    def __init__(self, filename, sample_rate=44100, chunk_size=1024, channels=1,
                 seek_seconds=0.0):
        self.filename = filename
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.process = None
        self._seek_seconds = seek_seconds
        self._open_stream()
        
    def _open_stream(self):
        from shutil import which
        ffmpeg_path = os.environ.get('FFMPEG_PATH') or which('ffmpeg')
        if not ffmpeg_path:
            raise FileNotFoundError("ffmpeg non trouvé")

        cmd = [ffmpeg_path, '-v', 'error']
        # Input seeking: jump to the requested position before decoding.
        # This avoids reading through all preceding audio data sequentially,
        # which is critical for parallel export workers on long files.
        if self._seek_seconds > 0:
            cmd += ['-ss', f'{self._seek_seconds:.6f}']
        cmd += [
            '-i', self.filename,
            '-f', 's16le',
            '-acodec', 'pcm_s16le',
            '-ac', str(self.channels),
            '-ar', str(self.sample_rate),
            '-'
        ]
        
        # Use the AppImage's bundled libraries when its FFmpeg is selected;
        # otherwise strip embedded paths to avoid conflicts with system FFmpeg.
        env = os.environ.copy()
        self_dir = env.get('SELF_DIR')
        try:
            bundled = self_dir and os.path.realpath(ffmpeg_path).startswith(
                os.path.realpath(self_dir) + os.sep
            )
        except OSError:
            bundled = False
        if bundled:
            env['LD_LIBRARY_PATH'] = os.path.join(self_dir, 'usr', 'lib')
        else:
            env.pop('LD_LIBRARY_PATH', None)
        
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=env
        )
        
    def read_chunk(self):
        if not self.process:
            return None
        # 16-bit samples = 2 bytes per sample
        bytes_to_read = self.chunk_size * self.channels * 2
        try:
            data = self.process.stdout.read(bytes_to_read)
        except Exception:
            return None
        if not data:
            return None

        # Keep a final partial block.  Frame-level consumers can combine it
        # with their sample buffer instead of silently losing the tail.
        sample_bytes = self.channels * 2
        usable_bytes = len(data) - (len(data) % sample_bytes)
        data = data[:usable_bytes]
        if not data:
            return None
            
        # Unpack bytes to numpy array
        if HAS_NUMPY:
            if self.channels == 1:
                samples = np.frombuffer(data, dtype=np.int16)
            else:
                samples = np.frombuffer(data, dtype=np.int16).reshape(-1, self.channels)
            return samples

        else:
            # Fallback structure unpacking without numpy
            import struct
            count = len(data) // 2
            samples = list(struct.unpack(f"<{count}h", data))
            if self.channels > 1:
                # Reshape to list of lists
                samples = [samples[i:i+self.channels] for i in range(0, len(samples), self.channels)]
            return samples
        
    def close(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=1)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None


class AudioFrameReader:
    """Read audio blocks whose boundaries follow a video FPS clock.

    ``sample_rate / fps`` is often fractional (for example 1837.5 samples at
    24 FPS).  This reader distributes the extra sample across frames instead
    of accumulating drift over a long export.
    """

    def __init__(self, filename, sample_rate=44100, fps=30, channels=1,
                 analysis_chunk_size=None, start_frame=0):
        self.sample_rate = sample_rate
        self.fps = fps
        self.channels = channels
        self.analysis_chunk_size = (
            analysis_chunk_size
            if analysis_chunk_size is not None
            else max(64, int(math.ceil(sample_rate / fps)))
        )
        # When start_frame > 0, use FFmpeg -ss input seeking to jump directly
        # to the segment start instead of reading through all preceding audio.
        seek_seconds = start_frame / fps if start_frame > 0 else 0.0
        self._reader = AudioStreamReader(
            filename,
            sample_rate=sample_rate,
            chunk_size=self.analysis_chunk_size,
            channels=channels,
            seek_seconds=seek_seconds,
        )
        self._frame_index = start_frame
        if HAS_NUMPY:
            self._buffer = (
                np.empty((0, channels), dtype=np.int16)
                if channels > 1 else np.empty(0, dtype=np.int16)
            )
        else:
            self._buffer = []

    def read_frame(self):
        """Return the next FPS-sized mono/stereo block, or ``None`` at EOF."""
        start = int(round(self._frame_index * self.sample_rate / self.fps))
        end = int(round((self._frame_index + 1) * self.sample_rate / self.fps))
        required = max(1, end - start)

        while len(self._buffer) < required:
            chunk = self._reader.read_chunk()
            if chunk is None:
                if len(self._buffer) == 0:
                    return None
                # EOF with a partial buffer: pad with silence to complete
                # the last video frame instead of dropping it. This prevents
                # "Audio stream ended before segment frame" on files where
                # ffprobe's duration is a few ms longer than the decodable
                # PCM stream (common for MP3 gapless).
                missing = required - len(self._buffer)
                if HAS_NUMPY:
                    if self.channels == 1:
                        pad = np.zeros(missing, dtype=np.int16)
                        self._buffer = np.concatenate((self._buffer, pad))
                    else:
                        pad = np.zeros((missing, self.channels), dtype=np.int16)
                        self._buffer = np.concatenate((self._buffer, pad))
                else:
                    pad_val = [0] * self.channels if self.channels > 1 else 0
                    self._buffer.extend([pad_val] * missing)
                break
            if HAS_NUMPY:
                self._buffer = np.concatenate((self._buffer, chunk))
            else:
                self._buffer.extend(chunk)

        frame = self._buffer[:required]
        self._buffer = self._buffer[required:]
        self._frame_index += 1

        # AudioAnalyzer uses one fixed FFT window.  Pad the occasional
        # shorter FPS block without changing the video-clock boundaries.
        if required < self.analysis_chunk_size:
            padding = self.analysis_chunk_size - required
            if HAS_NUMPY:
                pad_width = ((0, padding), (0, 0)) if frame.ndim > 1 else (0, padding)
                frame = np.pad(frame, pad_width, mode='constant')
            else:
                padding_value = [0] * self.channels if self.channels > 1 else 0
                frame = frame + [padding_value] * padding
        return frame

    def close(self):
        self._reader.close()


class AudioAnalyzer:
    """
    Analyse les données audio en temps réel pour en extraire des caractéristiques.
    """
    freq_bands = [
        (20, 250),
        (250, 500),
        (500, 2000),
        (2000, 4000),
        (4000, 20000)
    ]
    analysis_bands = [
        (20, 150),     # Sub-bass
        (150, 500),    # Bass/Low-mids
        (500, 2000),   # Mids
        (2000, 8000),  # High-mids
        (8000, 20000)  # Highs
    ]

    def __init__(self, audio_file, chunk_size=1024, sample_rate=44100, loop=False, load_file=True):
        self.audio_file = audio_file
        self.chunk_size = chunk_size
        self.sample_rate = sample_rate
        self.loop = loop
        self.audio = None
        self.audio_data = None
        self.current_chunk = 0
        self.total_chunks = 0
        self.use_simulated = False
        self.freq_bands = list(self.__class__.freq_bands)
        self.analysis_bands = list(self.__class__.analysis_bands)
        self.beat_phase = 0.0
        self.last_beat_time = 0.0
        
        # Vérifier si NO_SOUND est activé ou si numpy n'est pas disponible
        import os
        no_sound = os.environ.get('NO_SOUND', '').lower() in ('1', 'true', 'yes')
        
        # Si numpy n'est pas disponible, forcer le mode simulé
        if not HAS_NUMPY:
            no_sound = True
        
        # Charger le fichier audio avec pydub
        if no_sound:
            # Mode sans son: générer des données simulées
            import warnings
            warnings.warn("NO_SOUND activé ou numpy non disponible. Utilisation de données audio simulées.")
            self._init_simulated_data(sample_rate, chunk_size)
        elif not load_file:
            # Mode streaming offline ou en temps réel (pas de chargement initial du fichier)
            self.audio_data = None
            self.total_chunks = 0
        else:
            try:
                from pydub import AudioSegment
                from shutil import which

                ffmpeg_path = os.environ.get('FFMPEG_PATH') or which('ffmpeg')
                ffprobe_path = os.environ.get('FFPROBE_PATH') or which('ffprobe')

                if ffmpeg_path:
                    AudioSegment.converter = ffmpeg_path
                if ffprobe_path:
                    AudioSegment.ffprobe = ffprobe_path

                # Vider temporairement LD_LIBRARY_PATH pour que les binaires système
                # (ffprobe, ffmpeg) puissent charger leurs libs système correctement.
                # L'AppImage injecte des libs embarquées (ex: libdb-5.3.so absent)
                # qui causent un crash exit=127 de ffprobe/ffmpeg système.
                _saved_ldpath = os.environ.pop('LD_LIBRARY_PATH', None)
                try:
                    self.audio = AudioSegment.from_file(audio_file)
                finally:
                    if _saved_ldpath is not None:
                        os.environ['LD_LIBRARY_PATH'] = _saved_ldpath

                self.audio = self.audio.set_frame_rate(sample_rate)
                self.audio = self.audio.set_channels(1)  # Mono pour simplification
                self.audio_data = np.array(self.audio.get_array_of_samples())
                self.total_chunks = len(self.audio_data) // chunk_size
            except Exception as e:
                load_error = e
                self.audio_data = None
                self.audio = None
                from shutil import which
                ffmpeg_path = os.environ.get('FFMPEG_PATH') or which('ffmpeg')

                # Fallback: conversion directe ffmpeg → WAV (sans pydub)
                # On vide aussi LD_LIBRARY_PATH pour ffmpeg système
                if ffmpeg_path:
                    try:
                        import wave
                        import struct
                        tmp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                        tmp_file.close()
                        ffmpeg_cmd = [
                            ffmpeg_path,
                            '-y',
                            '-i', audio_file,
                            '-ar', str(sample_rate),
                            '-ac', '1',
                            '-f', 'wav',
                            tmp_file.name,
                        ]
                        _saved_ldpath2 = os.environ.pop('LD_LIBRARY_PATH', None)
                        try:
                            proc = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=30)
                        finally:
                            if _saved_ldpath2 is not None:
                                os.environ['LD_LIBRARY_PATH'] = _saved_ldpath2
                        if proc.returncode == 0 and os.path.exists(tmp_file.name):
                            with wave.open(tmp_file.name, 'rb') as wav_file:
                                frames = wav_file.readframes(wav_file.getnframes())
                                self.audio_data = np.array([
                                    struct.unpack('<h', frames[i:i + 2])[0]
                                    for i in range(0, len(frames) - (len(frames) % 2), 2)
                                ], dtype=np.int16)
                                self.total_chunks = len(self.audio_data) // chunk_size
                        if os.path.exists(tmp_file.name):
                            os.unlink(tmp_file.name)
                    except Exception:
                        self.audio_data = None

                if self.audio_data is None and str(audio_file).lower().endswith('.wav'):
                    try:
                        import wave
                        import struct
                        with wave.open(audio_file, 'rb') as wav_file:
                            frames = wav_file.readframes(wav_file.getnframes())
                            self.audio_data = np.array([
                                struct.unpack('<h', frames[i:i + 2])[0]
                                for i in range(0, len(frames) - (len(frames) % 2), 2)
                            ], dtype=np.int16)
                            self.total_chunks = len(self.audio_data) // chunk_size
                    except Exception:
                        self.audio_data = None

                if self.audio_data is None:
                    import warnings
                    warnings.warn(
                        f"Erreur pydub: {load_error}. Fallback vers données audio simulées."
                    )
                    self._init_simulated_data(sample_rate, chunk_size)
        
        # Configuration de l'analyse
        if HAS_NUMPY:
            self.fft_window = np.hanning(chunk_size)
            self._freqs = np.fft.rfftfreq(chunk_size, 1.0 / sample_rate)
            
            # Pré-calcul des masques de bandes visuelles (32 bandes logarithmiques)
            low_hz = 30.0
            high_hz = min(18000.0, sample_rate / 2.0)
            edges = np.geomspace(low_hz, high_hz, 32 + 1)
            self._visual_band_masks = []
            self._visual_band_weights = []
            for i, (low, high) in enumerate(zip(edges[:-1], edges[1:])):
                mask = (self._freqs >= low) & (self._freqs < high)
                self._visual_band_masks.append(mask)
                weight = 1.0 + (1.0 - i / max(31, 1)) * 0.45
                self._visual_band_weights.append(weight)

            # Pré-calcul des tranches d'indices pour les 5 bandes de sortie
            self._freq_band_slices = []
            fft_len = chunk_size // 2 + 1
            for low, high in self.freq_bands:
                low_idx = int(low * chunk_size / sample_rate)
                high_idx = min(int(high * chunk_size / sample_rate), fft_len)
                self._freq_band_slices.append((low_idx, high_idx))
        else:
            # Alternative sans numpy pour la fenêtre de Hann
            self.fft_window = [0.5 * (1 - math.cos(2 * math.pi * i / (chunk_size - 1))) for i in range(chunk_size)]
            self._freqs = None
            self._visual_band_masks = None
            self._visual_band_weights = None
            self._freq_band_slices = None
        
        # Indices des bandes pour bass, mids, treble
        self.bass_band_indices = [0, 1]  # 20-500 Hz
        self.mid_band_indices = [2, 3]   # 500-5000 Hz
        self.treble_band_indices = [4]  # 5000-20000 Hz
        
        # Historique pour le lissage
        self.volume_history = deque(maxlen=10)
        self.freq_history = deque(maxlen=10)
        self.visual_band_history = deque(maxlen=5)
        self.bass_history = deque(maxlen=10)
        self.mid_history = deque(maxlen=10)
        self.treble_history = deque(maxlen=10)
        self._previous_fft_magnitude = None
        
        # Détecteur de BPM
        from audio.bpm_detector import BPMDetector
        self.bpm_detector = BPMDetector(
            sample_rate=sample_rate,
            bpm_range=(40, 200),
            window_size=chunk_size
        )
        
        # État
        self.is_playing = False
    
    def _init_simulated_data(self, sample_rate, chunk_size):
        """Initialise des données audio simulées."""
        self.use_simulated = True
        # Générer des données audio simulées (sinusoïdale)
        duration = 10.0  # 10 secondes par défaut
        num_samples = int(sample_rate * duration)
        
        if HAS_NUMPY:
            # Version avec numpy
            t = np.linspace(0, duration, num_samples)
            # Mélange de plusieurs fréquences
            self.audio_data = np.sin(2 * np.pi * 440 * t) * 0.3  # 440 Hz
            self.audio_data += np.sin(2 * np.pi * 220 * t) * 0.2  # 220 Hz
            self.audio_data += np.sin(2 * np.pi * 880 * t) * 0.1  # 880 Hz
            self.audio_data = (self.audio_data * 32767).astype(np.int16)
        else:
            # Version sans numpy
            import math
            self.audio_data = []
            for i in range(num_samples):
                t = i / sample_rate
                sample = (math.sin(2 * math.pi * 440 * t) * 0.3 + 
                         math.sin(2 * math.pi * 220 * t) * 0.2 + 
                         math.sin(2 * math.pi * 880 * t) * 0.1)
                # Convertir en int16
                self.audio_data.append(int(sample * 32767))
            # Convertir en liste d'entiers
            self.audio_data = [int(x) for x in self.audio_data]
        
        self.total_chunks = len(self.audio_data) // chunk_size
        self.audio = None

    def start_stream(self):
        """Démarre le flux audio."""
        self.current_chunk = 0
        self.is_playing = True
        # Log pour le debug
        try:
            from ui.log_display import log_message
            log_message(f"AudioAnalyzer: Stream démarré (simulated={self.use_simulated})")
        except:
            pass
    
    def set_current_stream_chunk(self, chunk):
        """Met à jour le chunk de flux courant (appelé par le thread de lecture)."""
        self._current_stream_chunk = chunk
        self.current_chunk += 1

    def get_next_chunk(self):
        """Récupère le prochain chunk audio."""
        if not self.is_playing:
            try:
                from ui.log_display import log_message
                log_message("AudioAnalyzer: get_next_chunk appelé mais is_playing=False")
            except:
                pass
            return None
        
        # Mode streaming direct sans fichier chargé en RAM
        if self.audio_data is None:
            chunk = getattr(self, '_current_stream_chunk', None)
            if chunk is None:
                if HAS_NUMPY:
                    return np.zeros(self.chunk_size, dtype=np.int16)
                else:
                    return [0] * self.chunk_size
            return chunk
        
        start = self.current_chunk * self.chunk_size
        end = start + self.chunk_size
        
        if start >= len(self.audio_data):
            # Fin du fichier
            if self.loop:
                # Boucler
                self.current_chunk = 0
                start = 0
                end = self.chunk_size
            else:
                # Ne pas boucler, retourner None
                return None
        
        chunk = self.audio_data[start:end]
        self.current_chunk += 1
        
        # Si on utilise des listes (mode sans numpy), convertir en tableau compatible
        if not HAS_NUMPY and isinstance(chunk, list):
            # Retourner tel quel, le code appelant devra gérer
            pass
        
        return chunk
    
    def analyze_chunk(self, chunk):
        """
        Analyse un chunk audio et retourne les caractéristiques.
        
        Returns:
            dict: {
                'volume': float,         # Niveau de volume normalisé [0, 1]
                'volume_smooth': float,  # Volume lissé
                'frequency_bands': list, # Niveaux par bande de fréquence [0, 1] (16 bandes)
                'spectrum': list,        # Spectre FFT complet
                'beat': bool,            # Détection de beat
                'beat_strength': float,  # Force du beat [0, 1]
                'bpm': float,            # BPM actuel (lissé)
                'bpm_confidence': float, # Confiance dans la détection BPM [0, 1]
                'bass': float,           # Niveau des basses [0, 1] (0-500 Hz)
                'mids': float,           # Niveau des médiums [0, 1] (500-3000 Hz)
                'treble': float          # Niveau des aigus [0, 1] (3000-20000 Hz)
            }
        """
        # Si numpy n'est pas disponible, utiliser l'analyse simulée
        if not HAS_NUMPY:
            return self._analyze_chunk_simulated(chunk)
        
        if chunk is None or len(chunk) < self.chunk_size:
            return self._get_default_result()
        
        # Normaliser le chunk (pydub retourne des int16)
        chunk = chunk.astype(np.float32) / 32768.0
        
        # Appliquer la fenêtre de Hann
        windowed = chunk * self.fft_window[:len(chunk)]
        
        # Calculer le volume (RMS) plus propre et plus dynamique
        rms = np.sqrt(np.mean(windowed ** 2))
        energy = float(min(rms * 2.4, 1.0))
        volume = float(min(rms * 3.2, 1.0))
        
        # Lissage du volume
        self.volume_history.append(volume)
        smoothed_volume = np.mean(self.volume_history) if self.volume_history else volume
        
        fft_result = np.fft.rfft(windowed)
        fft_magnitude = np.abs(fft_result)
        freqs = self._freqs if self._freqs is not None else np.fft.rfftfreq(len(windowed), 1.0 / self.sample_rate)
        
        # Normaliser le spectre
        if len(fft_magnitude) > 0:
            fft_magnitude = fft_magnitude / (np.max(fft_magnitude) + 1e-10)
        
        # Calculer le centroid spectral et une énergie spectrale plus expressive
        spectral_energy = float(np.mean(fft_magnitude[1:]))
        if np.sum(fft_magnitude) > 0:
            spectral_centroid = float(np.sum(freqs * fft_magnitude) / (np.sum(fft_magnitude) + 1e-10))
            spectral_centroid = min(max(spectral_centroid / (self.sample_rate / 2.0), 0.0), 1.0)
        else:
            spectral_centroid = 0.0
        
        # Calculer les bandes de fréquence (5 bandes de sortie)
        frequency_bands = []
        slices = self._freq_band_slices or [
            (int(low * self.chunk_size / self.sample_rate), min(int(high * self.chunk_size / self.sample_rate), len(fft_magnitude)))
            for low, high in self.freq_bands
        ]
        for low_idx, high_idx in slices:
            if low_idx >= high_idx:
                frequency_bands.append(0.0)
                continue
            
            band_magnitude = np.mean(fft_magnitude[low_idx:high_idx])
            frequency_bands.append(min(band_magnitude * 8.0 + spectral_energy * 0.3, 1.0))

        # Bandes visuelles logarithmiques plus fines pour les nouveaux rendus.
        visual_bands = self._calculate_visual_bands(fft_magnitude, freqs, band_count=32)

        # Flux spectral / onset: énergie positive gagnée depuis la frame précédente.
        if self._previous_fft_magnitude is None or len(self._previous_fft_magnitude) != len(fft_magnitude):
            spectral_flux = 0.0
        else:
            diff = fft_magnitude - self._previous_fft_magnitude
            spectral_flux = float(np.sqrt(np.mean(np.maximum(diff, 0.0) ** 2)) * 8.0)
            spectral_flux = min(max(spectral_flux, 0.0), 1.0)
        self._previous_fft_magnitude = fft_magnitude.copy()
        
        # Calculer les niveaux bass, mids, treble
        bass_level = np.mean([frequency_bands[i] for i in self.bass_band_indices]) if self.bass_band_indices else 0.0
        mid_level = np.mean([frequency_bands[i] for i in self.mid_band_indices]) if self.mid_band_indices else 0.0
        treble_level = np.mean([frequency_bands[i] for i in self.treble_band_indices]) if self.treble_band_indices else 0.0
        
        # Stocker dans l'historique pour le lissage
        self.bass_history.append(bass_level)
        self.mid_history.append(mid_level)
        self.treble_history.append(treble_level)
        
        # Lisser les niveaux
        smoothed_bass = np.mean(self.bass_history) if self.bass_history else bass_level
        smoothed_mid = np.mean(self.mid_history) if self.mid_history else mid_level
        smoothed_treble = np.mean(self.treble_history) if self.treble_history else treble_level
        
        # Détection de BPM et beats avec le détecteur dédié
        bpm_result = self.bpm_detector.detect(chunk)
        current_time = self.current_chunk * (self.chunk_size / self.sample_rate)
        if bpm_result['is_beat']:
            self.last_beat_time = current_time
            self.beat_phase = 0.0
        else:
            beat_interval = 60.0 / max(bpm_result['bpm'], 40.0)
            if beat_interval > 0:
                time_since_last = max(0.0, current_time - self.last_beat_time)
                self.beat_phase = min(1.0, time_since_last / beat_interval)
            else:
                self.beat_phase = 0.0
        
        # Stocker l'historique des fréquences pour le lissage
        self.freq_history.append(frequency_bands)
        smoothed_bands = np.mean(self.freq_history, axis=0) if self.freq_history else frequency_bands
        self.visual_band_history.append(visual_bands)
        smoothed_visual_bands = np.mean(self.visual_band_history, axis=0) if self.visual_band_history else visual_bands
        
        return {
            'volume': float(volume),
            'volume_smooth': float(smoothed_volume),
            'frequency_bands': [float(x) for x in smoothed_bands],
            'visual_bands': [float(x) for x in smoothed_visual_bands],
            'spectrum': fft_magnitude.tolist(),
            'beat': bpm_result['is_beat'],
            'beat_strength': bpm_result['beat_strength'],
            'beat_phase': float(self.beat_phase),
            'energy': float(energy),
            'spectral_flux': float(spectral_flux),
            'onset_strength': float(max(spectral_flux, bpm_result['beat_strength'] * 0.65 if bpm_result['is_beat'] else spectral_flux * 0.5)),
            'spectral_centroid': float(spectral_centroid),
            'bpm': bpm_result['bpm'],
            'bpm_confidence': bpm_result['bpm_confidence'],
            'bass': float(smoothed_bass),
            'mids': float(smoothed_mid),
            'treble': float(smoothed_treble)
        }

    def _calculate_visual_bands(self, fft_magnitude, freqs, band_count=32):
        """Return log-spaced normalized bands for visualizers."""
        if not HAS_NUMPY or len(fft_magnitude) == 0:
            return [0.0] * band_count

        if self._visual_band_masks is not None and len(self._visual_band_masks) == band_count:
            bands = []
            for mask, weight in zip(self._visual_band_masks, self._visual_band_weights):
                if not np.any(mask):
                    bands.append(0.0)
                    continue
                magnitude = np.mean(fft_magnitude[mask])
                bands.append(float(min(1.0, magnitude * 9.5 * weight)))
            return bands

        low_hz = 30.0
        high_hz = min(18000.0, self.sample_rate / 2.0)
        edges = np.geomspace(low_hz, high_hz, band_count + 1)
        bands = []
        for low, high in zip(edges[:-1], edges[1:]):
            mask = (freqs >= low) & (freqs < high)
            if not np.any(mask):
                bands.append(0.0)
                continue
            magnitude = np.mean(fft_magnitude[mask])
            weight = 1.0 + (1.0 - len(bands) / max(band_count - 1, 1)) * 0.45
            bands.append(float(min(1.0, magnitude * 9.5 * weight)))
        return bands
    
    def _analyze_chunk_simulated(self, chunk):
        """Analyse simulée sans numpy."""
        import math
        import random
        
        if chunk is None or len(chunk) < self.chunk_size:
            return self._get_default_result()
        
        # Calculer un volume simulé à partir des données
        if isinstance(chunk, list):
            # Calculer RMS manuellement
            sum_sq = sum(x * x for x in chunk)
            rms = math.sqrt(sum_sq / len(chunk)) if len(chunk) > 0 else 0
            # Normaliser (supposer que les valeurs sont dans la plage int16)
            volume = min((rms / 32768.0) * 3, 1.0)
        else:
            # Si c'est un tableau numpy mais qu'on est en mode simulé, utiliser une valeur par défaut
            volume = 0.5 + 0.3 * math.sin(self.current_chunk * 0.5)
        
        # Lissage du volume
        self.volume_history.append(volume)
        smoothed_volume = sum(self.volume_history) / len(self.volume_history) if self.volume_history else volume
        
        # Générer des bandes de fréquence simulées plus expressives
        import time
        iteration = self.current_chunk + (int(time.time() * 1000) % 1000)
        frequency_bands = []
        for i, (low, high) in enumerate(self.freq_bands):
            variation = 0.35 + 0.4 * math.sin(iteration * 0.12 + i * 0.45)
            variation += 0.2 * math.sin(iteration * 0.04 + i * 0.18)
            frequency_bands.append(min(max(variation, 0.0), 1.0))
        visual_bands = []
        for i in range(32):
            variation = 0.30 + 0.34 * math.sin(iteration * 0.10 + i * 0.31)
            variation += 0.22 * math.sin(iteration * 0.035 + i * 0.11)
            visual_bands.append(min(max(variation, 0.0), 1.0))
        
        # Calculer les niveaux bass, mids, treble
        bass_level = sum(frequency_bands[i] for i in self.bass_band_indices) / len(self.bass_band_indices) if self.bass_band_indices else 0.0
        mid_level = sum(frequency_bands[i] for i in self.mid_band_indices) / len(self.mid_band_indices) if self.mid_band_indices else 0.0
        treble_level = sum(frequency_bands[i] for i in self.treble_band_indices) / len(self.treble_band_indices) if self.treble_band_indices else 0.0
        
        # Stocker dans l'historique pour le lissage
        self.bass_history.append(bass_level)
        self.mid_history.append(mid_level)
        self.treble_history.append(treble_level)
        
        # Lisser les niveaux
        smoothed_bass = sum(self.bass_history) / len(self.bass_history) if self.bass_history else bass_level
        smoothed_mid = sum(self.mid_history) / len(self.mid_history) if self.mid_history else mid_level
        smoothed_treble = sum(self.treble_history) / len(self.treble_history) if self.treble_history else treble_level
        
        # Détection de BPM et beats (le bpm_detector gère déjà le mode simulé)
        bpm_result = self.bpm_detector.detect(chunk)
        
        # Stocker l'historique des fréquences pour le lissage
        self.freq_history.append(frequency_bands)
        smoothed_bands = []
        if self.freq_history:
            # Moyenne simple des bandes
            num_history = len(self.freq_history)
            for i in range(len(frequency_bands)):
                avg = sum(freq[i] for freq in self.freq_history) / num_history
                smoothed_bands.append(avg)
        else:
            smoothed_bands = frequency_bands
        
        # Générer un spectre simulé plus riche
        spectrum = [0.0] * (self.chunk_size // 2)
        for i in range(len(spectrum)):
            spectrum[i] = random.uniform(0.1, 0.8) * math.exp(-i / (self.chunk_size / 4))
        
        beat_phase = 0.0
        if bpm_result['is_beat']:
            self.last_beat_time = self.current_chunk * (self.chunk_size / self.sample_rate)
            self.beat_phase = 0.0
        else:
            beat_interval = 60.0 / max(bpm_result['bpm'], 40.0)
            if beat_interval > 0:
                time_since_last = max(0.0, self.current_chunk * (self.chunk_size / self.sample_rate) - self.last_beat_time)
                self.beat_phase = min(1.0, time_since_last / beat_interval)
            else:
                self.beat_phase = 0.0
        
        return {
            'volume': float(volume),
            'volume_smooth': float(smoothed_volume),
            'frequency_bands': [float(x) for x in smoothed_bands],
            'visual_bands': [float(x) for x in visual_bands],
            'spectrum': spectrum,
            'beat': bpm_result['is_beat'],
            'beat_strength': bpm_result['beat_strength'],
            'beat_phase': float(self.beat_phase),
            'energy': float(volume),
            'spectral_flux': float(abs(math.sin(iteration * 0.18)) * 0.55),
            'onset_strength': float(bpm_result['beat_strength'] if bpm_result['is_beat'] else abs(math.sin(iteration * 0.18)) * 0.25),
            'spectral_centroid': float(0.45 + 0.1 * math.sin(self.current_chunk * 0.25)),
            'bpm': bpm_result['bpm'],
            'bpm_confidence': bpm_result['bpm_confidence'],
            'bass': float(smoothed_bass),
            'mids': float(smoothed_mid),
            'treble': float(smoothed_treble)
        }
    
    def _get_default_result(self):
        """Retourne un résultat par défaut."""
        return {
            'volume': 0.0,
            'volume_smooth': 0.0,
            'frequency_bands': [0.0] * len(self.freq_bands),
            'visual_bands': [0.0] * 32,
            'spectrum': [],
            'beat': False,
            'beat_strength': 0.0,
            'beat_phase': 0.0,
            'energy': 0.0,
            'spectral_flux': 0.0,
            'onset_strength': 0.0,
            'spectral_centroid': 0.0,
            'bpm': 120.0,
            'bpm_confidence': 0.0,
            'bass': 0.0,
            'mids': 0.0,
            'treble': 0.0,
        }
    
    def cleanup(self):
        """Nettoie les ressources."""
        self.is_playing = False
        self.current_chunk = 0
    
    def get_duration_seconds(self):
        """Retourne la durée du fichier audio en secondes."""
        if self.audio is not None:
            return len(self.audio) / 1000.0
        elif self.audio_data is not None:
            return len(self.audio_data) / self.sample_rate
        elif self.audio_file and os.path.exists(self.audio_file):
            import subprocess
            ffprobe_path = os.environ.get('FFPROBE_PATH') or 'ffprobe'
            try:
                cmd = [ffprobe_path, '-v', 'error', '-show_entries', 'format=duration',
                       '-of', 'default=noprint_wrappers=1:nokey=1', self.audio_file]
                env = os.environ.copy()
                env.pop('LD_LIBRARY_PATH', None)
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, env=env)
                if result.returncode == 0 and result.stdout.strip():
                    return float(result.stdout.strip())
            except Exception:
                pass
            return 10.0
        else:
            return 10.0
