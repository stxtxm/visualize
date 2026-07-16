"""
Détection de BPM (Beats Per Minute) précise basée sur autocorrélation.

Ce module implémente un algorithme de détection de BPM qui :
1. Calcule l'enveloppe du signal audio
2. Applique un filtre passe-haut pour enlever les basses fréquences
3. Utilise l'autocorrélation pour détecter les périodicités
4. Détecte les pics dans l'autocorrélation
5. Convertit les périodes en BPM
6. Applique un lissage temporel pour stabiliser la détection

Inspiré par :
- https://en.wikipedia.org/wiki/Autocorrelation
- https://www.mikrocontroller.net/articles/Beat_Detection
- https://github.com/librosa/librosa (pour l'analyse audio)
"""

from collections import deque
import math
import os

# Vérifier si NO_SOUND est activé avant d'importer numpy
no_sound = os.environ.get('NO_SOUND', '').lower() in ('1', 'true', 'yes')

# Importer numpy conditionnellement
HAS_NUMPY = False
if not no_sound:
    try:
        import numpy as np
        HAS_NUMPY = True
    except ImportError:
        HAS_NUMPY = False


class BPMDetector:
    """
    Détecte le BPM (Beats Per Minute) d'un signal audio en temps réel.
    
    L'algorithme est conçu pour fonctionner avec des chunks audio de petite taille
    (1024-4096 samples) et fournit une estimation de BPM mise à jour régulièrement.
    
    Attributs:
        sample_rate: Taux d'échantillonnage (default: 44100)
        bpm_range: Plage de BPM à détecter (default: 40-200)
        window_size: Taille de la fenêtre d'analyse (default: 4096)
        history_size: Nombre de détections à garder pour le lissage (default: 20)
    """
    
    def __init__(self, sample_rate=44100, bpm_range=(40, 200), window_size=4096, history_size=20):
        self.sample_rate = sample_rate
        self.bpm_range = bpm_range
        self.window_size = window_size
        self.history_size = history_size
        self.use_simulated = not HAS_NUMPY
        
        # Historique des détections
        self.bpm_history = deque(maxlen=history_size)
        self.beat_history = deque(maxlen=10)
        self.volume_history = deque(maxlen=10)
        
        # État
        self.current_time = 0.0
        self.last_beat_time = -10.0  # Initialisé dans le passé
        self.chunk_duration = window_size / sample_rate
        
        # Paramètres de détection
        self.volume_threshold = 0.1
        self.beat_min_interval = 60.0 / bpm_range[1]  # Intervalle min en secondes
        self.beat_max_interval = 60.0 / bpm_range[0]  # Intervalle max en secondes
        
        # Si numpy n'est pas disponible, pré-remplir avec des valeurs par défaut
        if self.use_simulated:
            # Pré-remplir l'historique avec des valeurs simulées
            for _ in range(history_size):
                self.bpm_history.append(120.0)
                self.beat_history.append(0.5)
                self.volume_history.append(0.3)
    
    def detect(self, chunk):
        """
        Détecte le BPM et les beats à partir d'un chunk audio.
        
        Cette méthode doit être appelée séquentiellement avec chaque chunk audio.
        Elle retourne une estimation mise à jour du BPM et si un beat a été détecté.
        
        Args:
            chunk: Tableau numpy de samples audio (mono, float32 ou int16)
                   Si None ou trop court, retourne les dernières valeurs
        
        Returns:
            dict: {
                'bpm': float,           # BPM actuel (lissé)
                'raw_bpm': float,      # BPM brut (dernière détection)
                'bpm_confidence': float, # Confiance (0.0 - 1.0)
                'is_beat': bool,        # True si un beat a été détecté
                'beat_strength': float, # Force du beat (0.0 - 1.0)
                'volume': float         # Volume actuel (0.0 - 1.0)
            }
        """
        # Si numpy n'est pas disponible, retourner des valeurs simulées
        if self.use_simulated:
            return self._get_simulated_result()
        
        if chunk is None or len(chunk) < 100:
            return self._get_last_result()
        
        # Convertir en float32 si nécessaire
        if chunk.dtype != np.float32:
            if chunk.dtype == np.int16:
                chunk = chunk.astype(np.float32) / 32768.0
            else:
                chunk = chunk.astype(np.float32)
        
        # Calculer le volume (RMS)
        volume = self._calculate_volume(chunk)
        self.volume_history.append(volume)
        
        # Calculer le BPM
        bpm_result = self._detect_bpm(chunk)
        
        # Détecter les beats
        beat_result = self._detect_beat(volume, bpm_result['raw_bpm'])
        
        # Mettre à jour le temps
        self.current_time += self.chunk_duration
        
        # Mettre à jour l'historique BPM
        if bpm_result['raw_bpm'] > 0:
            self.bpm_history.append(bpm_result['raw_bpm'])
        
        # Calculer le BPM lissé
        smoothed_bpm = float(np.mean(self.bpm_history)) if self.bpm_history else bpm_result['raw_bpm']
        
        return {
            'bpm': smoothed_bpm,
            'raw_bpm': bpm_result['raw_bpm'],
            'bpm_confidence': bpm_result['confidence'],
            'is_beat': beat_result['is_beat'],
            'beat_strength': beat_result['strength'],
            'volume': volume
        }
    
    def _get_simulated_result(self):
        """Retourne des résultats simulés quand numpy n'est pas disponible."""
        import math
        # Générer des beats simulés basés sur le temps
        self.current_time += self.chunk_duration
        
        # Simuler un BPM constant avec des variations
        base_bpm = 120.0
        variation = 5.0 * math.sin(self.current_time * 2)
        simulated_bpm = base_bpm + variation
        
        # Simuler des beats (tous les 0.5 secondes environ)
        beat_interval = 60.0 / base_bpm
        time_since_last = self.current_time - self.last_beat_time
        is_beat = time_since_last >= beat_interval * 0.9
        
        if is_beat:
            self.last_beat_time = self.current_time
        
        # Simuler un volume qui varie
        simulated_volume = 0.5 + 0.3 * math.sin(self.current_time * 10)
        simulated_volume = max(0, min(1, simulated_volume))
        
        # Mettre à jour les historiques (simulés)
        self.bpm_history.append(simulated_bpm)
        self.volume_history.append(simulated_volume)
        self.beat_history.append(simulated_volume)
        
        return {
            'bpm': float(simulated_bpm),
            'raw_bpm': float(simulated_bpm),
            'bpm_confidence': 0.8,
            'is_beat': is_beat,
            'beat_strength': 0.7 if is_beat else 0.1,
            'volume': float(simulated_volume)
        }
    
    def _calculate_volume(self, chunk):
        """Calcule le volume RMS du chunk."""
        return float(np.sqrt(np.mean(chunk ** 2)))
    
    def _detect_bpm(self, chunk):
        """
        Détecte le BPM à partir d'un chunk audio.
        
        Utilise l'autocorrélation de l'enveloppe du signal pour détecter
        les périodicités correspondantes aux BPM.
        
        Args:
            chunk: Tableau numpy de samples audio
            
        Returns:
            dict: {'raw_bpm': float, 'confidence': float}
        """
        # Calculer l'enveloppe du signal
        envelope = self._get_envelope(chunk)
        
        # Appliquer un filtre passe-haut pour enlever les basses fréquences
        # (on ne veut pas détecter les notes continues, seulement les beats)
        filtered_envelope = self._high_pass_filter(envelope)
        
        # Normaliser
        filtered_envelope -= np.mean(filtered_envelope)
        filtered_envelope /= (np.std(filtered_envelope) + 1e-10)
        
        # Calculer l'autocorrélation
        corr = self._autocorrelation(filtered_envelope)
        
        # Trouver les pics dans l'autocorrélation
        peaks = self._find_peaks(corr)
        
        # Convertir les positions des pics en BPM
        bpm_candidates = []
        for peak_idx in peaks:
            # Éviter le pic à 0 (corrélation avec soi-même)
            if peak_idx == 0:
                continue
            
            # Convertir l'index en secondes, puis en BPM
            lag_seconds = peak_idx / self.sample_rate
            bpm = 60.0 / lag_seconds
            
            # Filtrer par plage de BPM
            if self.bpm_range[0] <= bpm <= self.bpm_range[1]:
                bpm_candidates.append(bpm)
        
        if not bpm_candidates:
            # Pas de candidat trouvé, retourner le dernier BPM connu
            last_bpm = float(np.mean(self.bpm_history)) if self.bpm_history else 120.0
            return {'raw_bpm': last_bpm, 'confidence': 0.0}
        
        # Trouver le BPM le plus probable (le pic le plus haut)
        # Utiliser les valeurs de corrélation pour pondérer
        best_bpm = 120.0
        best_confidence = 0.0
        
        for peak_idx in peaks:
            if peak_idx == 0:
                continue
            lag_seconds = peak_idx / self.sample_rate
            bpm = 60.0 / lag_seconds
            
            if self.bpm_range[0] <= bpm <= self.bpm_range[1]:
                # La confiance est proportionnelle à la hauteur du pic
                confidence = corr[peak_idx] / (np.max(corr) + 1e-10)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_bpm = bpm
        
        return {'raw_bpm': best_bpm, 'confidence': float(best_confidence)}
    
    def _get_envelope(self, chunk):
        """
        Calcule l'enveloppe du signal audio.
        
        L'enveloppe représente l'amplitude instantanée du signal,
        utile pour détecter les transitoires (beats).
        """
        # Utiliser la valeur absolue du signal
        envelope = np.abs(chunk)
        
        # Appliquer un filtre de lissage pour réduire le bruit
        # Fenêtre de lissage de 5 samples
        if len(envelope) > 5:
            kernel = np.ones(5) / 5
            envelope = np.convolve(envelope, kernel, mode='same')
        
        return envelope
    
    def _high_pass_filter(self, signal, cutoff_hz=10):
        """
        Applique un filtre passe-haut simple.
        
        Cela permet d'enlever les composantes basses fréquences (basses continues)
        et de ne garder que les variations rapides (beats, attaques).
        """
        # Filtre très simple : soustraire une moyenne mobile
        window_size = max(1, int(self.sample_rate / cutoff_hz / 2))
        
        if len(signal) <= window_size:
            return signal
        
        # Somme cumulative pour calculer la moyenne mobile en O(N)
        cumsum = np.cumsum(np.insert(signal, 0, 0))
        moving_avg = (cumsum[window_size:-1] - cumsum[:-window_size-1]) / window_size
        
        filtered = signal.copy()
        filtered[window_size:] -= moving_avg
        
        # Pour les premiers window_size éléments, on soustrait la moyenne progressive
        first_avg = np.mean(signal[:window_size])
        filtered[:window_size] -= first_avg
        
        return filtered
    
    def _autocorrelation(self, signal):
        """
        Calcule l'autocorrélation du signal.
        
        L'autocorrélation mesure la similarité du signal avec lui-même
        à différents décalages temporels. Les pics indiquent des périodicités.
        """
        n = len(signal)
        
        # Calculer l'autocorrélation
        corr = np.correlate(signal, signal, mode='full')
        
        # Ne garder que la moitié positive (décalages >= 0)
        corr = corr[n-1:]
        
        return corr
    
    def _find_peaks(self, data, min_distance=10):
        """
        Trouve les pics locaux dans un signal.
        
        Args:
            data: Tableau numpy de valeurs
            min_distance: Distance minimale entre deux pics (en indices)
        
        Returns:
            list: Liste des indices des pics
        """
        peaks = []
        
        for i in range(1, len(data) - 1):
            if data[i] > data[i-1] and data[i] > data[i+1]:
                # Vérifier qu'on n'est pas trop proche d'un autre pic
                if not peaks or i - peaks[-1] > min_distance:
                    peaks.append(i)
        
        return peaks
    
    def _detect_beat(self, volume, current_bpm):
        """
        Détecte si un beat se produit à l'instant courant.
        
        Utilise une combinaison de :
        1. Seuil adaptatif basé sur le volume moyen
        2. Intervalle minimum entre les beats (basé sur le BPM)
        
        Args:
            volume: Volume RMS du chunk actuel
            current_bpm: BPM actuel (pour calculer l'intervalle minimum)
        
        Returns:
            dict: {'is_beat': bool, 'strength': float}
        """
        # Calculer le seuil adaptatif
        if self.volume_history:
            avg_volume = float(np.mean(self.volume_history))
            threshold = avg_volume * 1.5 if avg_volume > 0.01 else 0.1
        else:
            threshold = 0.1
            avg_volume = 0.0
        
        # Temps depuis le dernier beat
        time_since_last_beat = self.current_time - self.last_beat_time
        
        # Calculer l'intervalle minimum entre les beats basé sur le BPM
        if current_bpm > 0:
            min_interval = 60.0 / current_bpm * 0.8  # 80% de l'intervalle théorique
        else:
            min_interval = self.beat_min_interval
        
        # Détecter le beat
        is_beat = False
        strength = 0.0
        
        if volume > threshold and volume > 0.05:
            # Vérifier que suffisamment de temps s'est écoulé depuis le dernier beat
            if time_since_last_beat >= min_interval:
                is_beat = True
                self.last_beat_time = self.current_time
                
                # Calculer la force du beat
                if avg_volume > 0:
                    strength = min(1.0, volume / avg_volume - 1.0)
                else:
                    strength = min(1.0, volume * 10)
            else:
                # Trop tôt pour un beat, mais le volume est élevé
                # Cela pourrait être un beat manqué
                strength = min(1.0, volume / (avg_volume + 0.01) - 0.5) if avg_volume > 0 else 0.0
        
        # Ajouter à l'historique
        self.beat_history.append(volume)
        
        return {'is_beat': is_beat, 'strength': float(max(0, strength))}
    
    def _get_last_result(self):
        """Retourne le dernier résultat connu."""
        last_bpm = float(sum(self.bpm_history) / len(self.bpm_history)) if self.bpm_history else 120.0
        last_volume = float(sum(self.volume_history) / len(self.volume_history)) if self.volume_history else 0.0
        
        return {
            'bpm': last_bpm,
            'raw_bpm': last_bpm,
            'bpm_confidence': 0.0,
            'is_beat': False,
            'beat_strength': 0.0,
            'volume': last_volume
        }
    
    def reset(self):
        """Réinitialise le détecteur."""
        self.bpm_history.clear()
        self.beat_history.clear()
        self.volume_history.clear()
        self.current_time = 0.0
        self.last_beat_time = -10.0
    
    def get_bpm_history(self):
        """Retourne l'historique des détections de BPM."""
        return list(self.bpm_history)
