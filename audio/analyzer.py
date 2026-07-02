"""
Module d'analyse audio utilisant FFT pour extraire les caractéristiques du son.
"""

import math
from collections import deque
import os
import sys

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


class AudioAnalyzer:
    """
    Analyse un flux audio et extrait les caractéristiques pour la visualisation.
    
    Retourne des données enrichies avec :
    - volume: Niveau de volume [0, 1]
    - frequency_bands: Niveaux par bande de fréquence [0, 1]
    - spectrum: Spectre FFT complet
    - beat: Détection de beat (bool)
    - bpm: BPM actuel (float)
    - beat_strength: Force du beat [0, 1]
    - bass: Niveau des basses [0, 1]
    - mids: Niveau des médiums [0, 1]
    - treble: Niveau des aigus [0, 1]
    """
    
    def __init__(self, audio_file, chunk_size=1024, sample_rate=44100, loop=True):
        self.audio_file = audio_file
        self.chunk_size = chunk_size
        self.sample_rate = sample_rate
        self.loop = loop
        self.audio = None
        self.audio_data = None
        self.current_chunk = 0
        self.total_chunks = 0
        self.use_simulated = False
        
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
        else:
            try:
                from pydub import AudioSegment
                self.audio = AudioSegment.from_file(audio_file)
                self.audio = self.audio.set_frame_rate(sample_rate)
                self.audio = self.audio.set_channels(1)  # Mono pour simplification
                self.audio_data = np.array(self.audio.get_array_of_samples())
                self.total_chunks = len(self.audio_data) // chunk_size
            except Exception as e:
                # Si pydub échoue, on génère des données simulées
                import warnings
                warnings.warn(f"Erreur pydub: {e}. Utilisation de données audio simulées.")
                self._init_simulated_data(sample_rate, chunk_size)
        
        # Configuration de l'analyse
        if HAS_NUMPY:
            self.fft_window = np.hanning(chunk_size)
        else:
            # Alternative sans numpy pour la fenêtre de Hann
            self.fft_window = [0.5 * (1 - math.cos(2 * math.pi * i / (chunk_size - 1))) for i in range(chunk_size)]
        
        # 16 bandes de fréquence pour une analyse plus fine
        self.freq_bands = [
            (20, 60),     # Sub-bass
            (60, 120),    # Bass
            (120, 200),   # Low bass
            (200, 350),   # Mid bass
            (350, 500),   # Upper bass
            (500, 1000),  # Lower mids
            (1000, 2000), # Mids
            (2000, 3000), # Upper mids
            (3000, 4000), # Lower treble
            (4000, 5000), # Treble
            (5000, 6000), # Upper treble
            (6000, 7000), # High treble
            (7000, 8000), # Very high treble
            (8000, 10000),# Ultra treble
            (10000, 12000),
            (12000, 20000)
        ]
        
        # Indices des bandes pour bass, mids, treble
        self.bass_band_indices = [0, 1, 2, 3, 4]  # 20-500 Hz
        self.mid_band_indices = [5, 6, 7]       # 500-3000 Hz
        self.treble_band_indices = [8, 9, 10, 11, 12, 13, 14, 15]  # 3000-20000 Hz
        
        # Historique pour le lissage
        self.volume_history = deque(maxlen=10)
        self.freq_history = deque(maxlen=10)
        self.bass_history = deque(maxlen=10)
        self.mid_history = deque(maxlen=10)
        self.treble_history = deque(maxlen=10)
        
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
    
    def get_next_chunk(self):
        """Récupère le prochain chunk audio."""
        if not self.is_playing:
            try:
                from ui.log_display import log_message
                log_message("AudioAnalyzer: get_next_chunk appelé mais is_playing=False")
            except:
                pass
            return None
        
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
        
        # Calculer le volume (RMS)
        rms = np.sqrt(np.mean(windowed ** 2))
        volume = min(rms * 3, 1.0)  # Amplifier et limiter à 1
        
        # Lissage du volume
        self.volume_history.append(volume)
        smoothed_volume = np.mean(self.volume_history) if self.volume_history else volume
        
        # Calculer le spectre FFT
        fft_result = np.fft.rfft(windowed * self.fft_window[:len(windowed)])
        fft_magnitude = np.abs(fft_result)
        
        # Normaliser le spectre
        if len(fft_magnitude) > 0:
            fft_magnitude = fft_magnitude / (np.max(fft_magnitude) + 1e-10)
        
        # Calculer les bandes de fréquence (16 bandes)
        frequency_bands = []
        for low, high in self.freq_bands:
            # Convertir les fréquences en indices
            low_idx = int(low * self.chunk_size / self.sample_rate)
            high_idx = min(int(high * self.chunk_size / self.sample_rate), len(fft_magnitude))
            
            if low_idx >= high_idx:
                frequency_bands.append(0.0)
                continue
            
            band_magnitude = np.mean(fft_magnitude[low_idx:high_idx])
            # Amplifier pour une meilleure dynamique
            frequency_bands.append(min(band_magnitude * 8, 1.0))
        
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
        
        # Stocker l'historique des fréquences pour le lissage
        self.freq_history.append(frequency_bands)
        smoothed_bands = np.mean(self.freq_history, axis=0) if self.freq_history else frequency_bands
        
        return {
            'volume': float(volume),
            'volume_smooth': float(smoothed_volume),
            'frequency_bands': [float(x) for x in smoothed_bands],
            'spectrum': [float(x) for x in fft_magnitude],
            'beat': bpm_result['is_beat'],
            'beat_strength': bpm_result['beat_strength'],
            'bpm': bpm_result['bpm'],
            'bpm_confidence': bpm_result['bpm_confidence'],
            'bass': float(smoothed_bass),
            'mids': float(smoothed_mid),
            'treble': float(smoothed_treble)
        }
    
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
        
        # Générer des bandes de fréquence simulées
        import time
        iteration = self.current_chunk + (int(time.time() * 1000) % 1000)
        frequency_bands = []
        for i, (low, high) in enumerate(self.freq_bands):
            # Simuler des variations basées sur l'itération et la bande
            variation = 0.5 + 0.3 * math.sin(iteration * 0.1 + i * 0.5)
            frequency_bands.append(min(max(variation, 0.0), 1.0))
        
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
        
        # Générer un spectre simulé
        spectrum = [0.0] * (self.chunk_size // 2)
        for i in range(len(spectrum)):
            spectrum[i] = random.uniform(0.1, 0.8) * math.exp(-i / (self.chunk_size / 4))
        
        return {
            'volume': float(volume),
            'volume_smooth': float(smoothed_volume),
            'frequency_bands': [float(x) for x in smoothed_bands],
            'spectrum': spectrum,
            'beat': bpm_result['is_beat'],
            'beat_strength': bpm_result['beat_strength'],
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
            'frequency_bands': [0.0] * len(self.freq_bands),
            'spectrum': [],
            'beat': False
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
        else:
            return 10.0  # Durée par défaut
