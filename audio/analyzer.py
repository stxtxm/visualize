"""
Module d'analyse audio utilisant FFT pour extraire les caractéristiques du son.
"""

import numpy as np
import math
from collections import deque


class AudioAnalyzer:
    """
    Analyse un flux audio et extrait les caractéristiques pour la visualisation.
    """
    
    def __init__(self, audio_file, chunk_size=1024, sample_rate=44100, loop=True):
        self.audio_file = audio_file
        self.chunk_size = chunk_size
        self.sample_rate = sample_rate
        self.loop = loop
        
        # Charger le fichier audio avec pydub
        try:
            from pydub import AudioSegment
            self.audio = AudioSegment.from_file(audio_file)
            self.audio = self.audio.set_frame_rate(sample_rate)
            self.audio = self.audio.set_channels(1)  # Mono pour simplification
        except Exception as e:
            raise RuntimeError(f"Erreur lors du chargement du fichier audio: {e}")
        
        # Configuration de l'analyse
        self.fft_window = np.hanning(chunk_size)
        self.freq_bands = [
            (20, 150),    # Basses
            (150, 500),   # Basses-médiums
            (500, 2000),  # Médiums
            (2000, 5000), # Médiums-aigus
            (5000, 20000) # Aigus
        ]
        
        # Historique pour le lissage
        self.volume_history = deque(maxlen=10)
        self.freq_history = deque(maxlen=10)
        
        # État
        self.current_chunk = 0
        self.audio_data = np.array(self.audio.get_array_of_samples())
        self.total_chunks = len(self.audio_data) // chunk_size
        self.is_playing = False
    
    def start_stream(self):
        """Démarre le flux audio."""
        self.current_chunk = 0
        self.is_playing = True
    
    def get_next_chunk(self):
        """Récupère le prochain chunk audio."""
        if not self.is_playing:
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
        
        return chunk
    
    def analyze_chunk(self, chunk):
        """
        Analyse un chunk audio et retourne les caractéristiques.
        
        Returns:
            dict: {
                'volume': float,        # Niveau de volume normalisé [0, 1]
                'frequency_bands': list, # Niveaux par bande de fréquence [0, 1]
                'spectrum': list,       # Spectre FFT complet
                'beat': bool            # Détection de beat
            }
        """
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
        
        # Calculer les bandes de fréquence
        frequency_bands = []
        for low, high in self.freq_bands:
            # Convertir les fréquences en indices
            low_idx = int(low * self.chunk_size / self.sample_rate)
            high_idx = min(int(high * self.chunk_size / self.sample_rate), len(fft_magnitude))
            
            if low_idx >= high_idx:
                frequency_bands.append(0)
                continue
            
            band_magnitude = np.mean(fft_magnitude[low_idx:high_idx])
            frequency_bands.append(min(band_magnitude * 5, 1.0))  # Amplifier
        
        # Détection de beat (simplifiée)
        beat = False
        if len(self.volume_history) >= 2:
            prev_volumes = list(self.volume_history)[:-1]
            if len(prev_volumes) > 0:
                prev_volume = np.mean(prev_volumes)
                if smoothed_volume > prev_volume * 1.5 and smoothed_volume > 0.3:
                    beat = True
        
        # Stocker l'historique des fréquences pour le lissage
        self.freq_history.append(frequency_bands)
        smoothed_bands = np.mean(self.freq_history, axis=0) if self.freq_history else frequency_bands
        
        return {
            'volume': float(smoothed_volume),
            'frequency_bands': [float(x) for x in smoothed_bands],
            'spectrum': [float(x) for x in fft_magnitude],
            'beat': beat
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
        return len(self.audio) / 1000.0
    
    def get_total_frames(self, fps):
        """Retourne le nombre total de frames pour un FPS donné."""
        return int(self.get_duration_seconds() * fps)
