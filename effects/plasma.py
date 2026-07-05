"""
Effet plasma psychédélique.
Crée un effet de plasma fluide qui réagit à la musique avec des distorsions colorées.
Inspiré des visualisations plasma des années 90.
"""

import numpy as np
import math
from effects.base import BaseEffect


class PlasmaEffect(BaseEffect):
    """
    Effet de plasma avec distorsions sinusoïdales complexes.
    Créé un rendu fluide et hypnotique qui réagit aux fréquences audio.
    """
    
    def __init__(self, width, height, color_palette='psychedelic'):
        super().__init__(width, height, color_palette)
        self.center_x = width // 2
        self.center_y = height // 2
        
        # Paramètres de distorsion
        self.time_scale = 0.001
        self.num_waves = 8
        self.wave_frequencies = [0.01 * (i + 1) for i in range(self.num_waves)]
        self.wave_amplitudes = [50.0 + i * 20 for i in range(self.num_waves)]
        self.wave_phases = [0.0] * self.num_waves
        self.wave_directions = [(math.cos(i * math.pi / 4), math.sin(i * math.pi / 4)) for i in range(self.num_waves)]
        
        # Pour la synchro audio
        self.bass_factor = 0.0
        self.treble_factor = 0.0
        self.volume_factor = 0.0
        self.beat_factor = 0.0
        
        # Couleurs interpolées
        self.color_phase = 0.0
        self.color_speed = 0.002
        
        # Pour les points de plasma
        self.plasma_points = []
        self.num_points = 20
        self.distortion = 0.0
        self.target_distortion = 0.0
        self.pulse = 0.0
        self.target_pulse = 0.0
        self.smoothing = 0.1
        
        # Initialiser les points de plasma
        self._init_plasma_points()
    
    def _init_plasma_points(self):
        """Initialiser les points de distorsion pour l'effet plasma."""
        import random
        for _ in range(self.num_points):
            angle = random.random() * 2 * np.pi
            distance = random.random() * min(self.width, self.height) * 0.4
            x = self.center_x + distance * np.cos(angle)
            y = self.center_y + distance * np.sin(angle)
            self.plasma_points.append({
                'x': float(x),
                'y': float(y),
                'vx': random.uniform(-0.5, 0.5),
                'vy': random.uniform(-0.5, 0.5),
                'phase': random.random() * 2 * np.pi,
                'size': random.randint(10, 50),
                'color': random.random() * 2 * np.pi
            })
    
    def update(self, audio_data, delta_time):
        super().update(audio_data, delta_time)
        
        # Mettre à jour les phases des ondes
        for i in range(self.num_waves):
            self.wave_phases[i] += delta_time * 0.5 * (i + 1) * 0.1
        
        # Mettre à jour la phase des couleurs
        self.color_phase += delta_time * self.color_speed * 10
        
        if audio_data:
            volume = audio_data.get('volume', 0)
            bass = audio_data.get('bass', 0)
            mids = audio_data.get('mids', 0)
            treble = audio_data.get('treble', 0)
            beat = audio_data.get('beat', False)
            beat_strength = audio_data.get('beat_strength', 0)
            bpm = audio_data.get('bpm', 120)
            
            # Stocker les facteurs pour le rendu
            self.volume_factor = volume
            self.bass_factor = bass
            self.treble_factor = treble
            self.beat_factor = beat_strength if beat else 0.0
            
            # Calculer la distorsion en fonction du volume et des basses
            self.target_distortion = (bass * 0.7 + volume * 0.3) * 1.2
            
            # Calculer la pulsation
            self.target_pulse = volume * 0.5
            if beat:
                self.target_pulse = min(self.target_pulse + beat_strength * 0.8, 1.0)
            
            # Déplacer les points de plasma
            for point in self.plasma_points:
                # Déplacement de base
                point['x'] += point['vx'] * delta_time * 50
                point['y'] += point['vy'] * delta_time * 50
                
                # Rebondir sur les bords
                if point['x'] < 0 or point['x'] > self.width:
                    point['vx'] = -point['vx']
                if point['y'] < 0 or point['y'] > self.height:
                    point['vy'] = -point['vy']
                
                # Mettre à jour la phase
                point['phase'] += delta_time * (1 + volume * 2)
                
                # Réagir aux beats
                if beat and beat_strength > 0.3:
                    point['vx'] += random.uniform(-2, 2) * beat_strength
                    point['vy'] += random.uniform(-2, 2) * beat_strength
                    point['size'] = min(200, point['size'] * (1 + beat_strength))
            
            # Modifier les amplitudes des ondes en fonction de la musique
            freq_bands = audio_data.get('frequency_bands', [])
            if freq_bands:
                for i in range(min(self.num_waves, len(freq_bands))):
                    # Les bandes de basse affectent les grandes ondes
                    # Les bandes de treble affectent les petites ondes
                    band_idx = i % len(freq_bands)
                    frequency_mult = 1.0 + freq_bands[band_idx] * 2
                    self.wave_amplitudes[i] = 50.0 + i * 20 * frequency_mult
            
            # Sur un beat, ajouter une distorsion temporaire
            if beat:
                for i in range(self.num_waves):
                    self.wave_phases[i] += beat_strength * 0.5
        else:
            self.volume_factor = 0.0
            self.bass_factor = 0.0
            self.treble_factor = 0.0
            self.beat_factor = 0.0
            self.target_distortion = 0.0
            self.target_pulse = 0.0
        
        # Lissage
        self.distortion = (
            self.distortion * (1 - self.smoothing) +
            self.target_distortion * self.smoothing
        )
        self.pulse = (
            self.pulse * (1 - self.smoothing * 2) +
            self.target_pulse * self.smoothing * 2
        )
    
    def _generate_plasma_frame(self, target_w, target_h):
        """Calcule le frame de plasma sous forme de tableau NumPy RGB (H, W, 3)."""
        # Résolution de calcul interne pour la rapidité
        calc_w = 200
        calc_h = int(calc_w * target_h / target_w)
        
        # Grid de coordonnées
        x = np.linspace(0, target_w, calc_w)
        y = np.linspace(0, target_h, calc_h)
        X, Y = np.meshgrid(x, y)
        
        total = np.zeros_like(X)
        
        # Combiner plusieurs ondes sinusoïdales
        for i in range(self.num_waves):
            dx, dy = self.wave_directions[i]
            freq = self.wave_frequencies[i]
            amp = self.wave_amplitudes[i] * (1.0 + self.volume_factor * 0.5)
            phase = self.wave_phases[i]
            
            dist_from_center = np.sqrt((X - self.center_x) ** 2 + (Y - self.center_y) ** 2)
            dist_factor = dist_from_center / (target_w / 2.0)
            
            # Moduler la fréquence et l'amplitude en fonction de la distance
            mod_freq = freq * (0.5 + dist_factor * 0.5)
            mod_amp = amp * (0.8 + dist_factor * 0.2)
            
            # Calculer la valeur de l'onde
            val = np.sin(
                X * dx * mod_freq * 2.0 * np.pi + 
                Y * dy * mod_freq * 2.0 * np.pi + 
                phase * np.pi + 
                self.time * self.time_scale * 10.0
            ) * mod_amp
            
            total += val
            
        # Ajouter une distorsion radiale basée sur les basses
        dist_from_center = np.sqrt((X - self.center_x) ** 2 + (Y - self.center_y) ** 2)
        radial_distortion = np.sin(dist_from_center * 0.01 + self.time * 2.0) * self.bass_factor * 100.0
        total += radial_distortion
        
        # Ajouter une distorsion spiralée basée sur le treble
        angle = np.arctan2(Y - self.center_y, X - self.center_x)
        spiral_distortion = np.sin(angle * 8.0 + self.time * 3.0 + self.treble_factor * np.pi) * self.treble_factor * 50.0
        total += spiral_distortion
        
        # Ajouter un effet de beat
        if self.beat_factor > 0:
            total += np.sin(self.time * 10.0 + self.beat_factor * 5.0) * self.beat_factor * 200.0
            
        # Normaliser la valeur
        val_norm = (total % 360) / 360.0
        
        # Utiliser la phase des couleurs pour animer
        hue_shift = (self.color_phase + val_norm * 0.5) % 1.0
        
        # Convertir HSV en RGB (vectorisé)
        h = hue_shift * 6.0
        i = h.astype(np.int32)
        f = h - i
        
        r = np.zeros_like(h)
        g = np.zeros_like(h)
        b = np.zeros_like(h)
        
        r[i == 0] = 1.0; g[i == 0] = f[i == 0]
        r[i == 1] = 1.0 - f[i == 1]; g[i == 1] = 1.0
        g[i == 2] = 1.0; b[i == 2] = f[i == 2]
        g[i == 3] = 1.0 - f[i == 3]; b[i == 3] = 1.0
        r[i == 4] = f[i == 4]; b[i == 4] = 1.0
        r[i == 5] = 1.0; b[i == 5] = 1.0 - f[i == 5]
        
        R = (r * 255.0).astype(np.uint8)
        G = (g * 255.0).astype(np.uint8)
        B = (b * 255.0).astype(np.uint8)
        
        # Appliquer la palette de couleurs
        if self.color_palette != 'rainbow':
            num_colors = len(self.colors)
            color_indices = (val_norm * num_colors).astype(np.int32) % num_colors
            
            palette_colors = np.array(self.colors, dtype=np.uint8)
            pixel_colors = palette_colors[color_indices]
            
            mix_factor = 0.5
            R = (R * mix_factor + pixel_colors[:, :, 0] * (1.0 - mix_factor)).astype(np.uint8)
            G = (G * mix_factor + pixel_colors[:, :, 1] * (1.0 - mix_factor)).astype(np.uint8)
            B = (B * mix_factor + pixel_colors[:, :, 2] * (1.0 - mix_factor)).astype(np.uint8)
            
        return np.stack((R, G, B), axis=-1)
    
    def render(self, surface):
        """Rendu avec Pygame."""
        import pygame
        
        width, height = self.width, self.height
        rgb_array = self._generate_plasma_frame(width, height)
        
        # Transposer pour le format attendu par pygame.surfarray (W, H, 3)
        rgb_transposed = rgb_array.transpose(1, 0, 2)
        temp_surface = pygame.surfarray.make_surface(rgb_transposed)
        
        # Upscaler de façon lisse
        upscaled = pygame.transform.smoothscale(temp_surface, (width, height))
        surface.blit(upscaled, (0, 0))
        
        # Vignette optimisée sans double boucle
        if not hasattr(self, '_vignette') or self._vignette.get_size() != (width, height):
            self._vignette = pygame.Surface((width, height), pygame.SRCALPHA)
            cx, cy = width // 2, height // 2
            max_dist = math.sqrt(cx**2 + cy**2)
            for r_step in range(20, 0, -1):
                radius = int(max_dist * (r_step / 20.0))
                alpha = int(120 * (1.0 - (r_step / 20.0)))
                pygame.draw.circle(self._vignette, (0, 0, 0, alpha), (cx, cy), radius)
                
        surface.blit(self._vignette, (0, 0))
        
        # Dessiner les patterns
        self._draw_additional_patterns(surface)
    
    def _draw_additional_patterns(self, surface):
        """Ajouter des motifs supplémentaires pour enrichir le plasma."""
        import pygame
        
        center_x, center_y = self.width // 2, self.height // 2
        for i in range(3):
            radius = int(50 + i * 80 + self.pulse * 50)
            alpha = 100 * (1 - i / 3)
            color = self.colors[int(self.time * 2 + i) % len(self.colors)]
            
            # Dessiner directement avec un petit décalage pour la fluidité
            s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, alpha), (center_x, center_y), radius, 2)
            surface.blit(s, (0, 0))
        
        # Lignes radiales
        num_lines = 16
        for i in range(num_lines):
            angle = i * (2 * math.pi / num_lines) + self.time * 0.5
            length = 200 + self.pulse * 100
            
            x1 = center_x + math.cos(angle) * 50
            y1 = center_y + math.sin(angle) * 50
            x2 = center_x + math.cos(angle) * length
            y2 = center_y + math.sin(angle) * length
            
            color_idx = int(self.time * 4 + i) % len(self.colors)
            color = self.colors[color_idx]
            
            pygame.draw.line(surface, color, (int(x1), int(y1)), (int(x2), int(y2)), 2)
    
    def render_to_array(self):
        """Rendu vers un tableau numpy pour l'export vidéo."""
        import cv2
        width, height = self.width, self.height
        rgb_array = self._generate_plasma_frame(width, height)
        
        # Interpolation bilinéaire rapide OpenCV
        frame = cv2.resize(rgb_array, (width, height), interpolation=cv2.INTER_LINEAR)
        
        # Vignette vectorisée NumPy
        cx, cy = width // 2, height // 2
        Y_indices, X_indices = np.indices((height, width))
        dists = np.sqrt((X_indices - cx)**2 + (Y_indices - cy)**2)
        max_dist = math.sqrt(cx**2 + cy**2)
        vignette_factors = 1.0 - (dists / max_dist) * 0.4
        vignette_factors = np.clip(vignette_factors, 0.0, 1.0)[:, :, np.newaxis]
        
        frame = (frame * vignette_factors).astype(np.uint8)
        
        self._draw_additional_patterns_cv2(frame)
        return frame
    
    def _draw_additional_patterns_cv2(self, frame):
        """Ajouter des motifs supplémentaires avec OpenCV."""
        import cv2
        
        center_x, center_y = self.width // 2, self.height // 2
        
        # Dessiner des cercles
        for i in range(3):
            radius = int(50 + i * 80 + self.pulse * 50)
            alpha = 0.3 * (1 - i / 3)
            color = self.colors[int(self.time * 2 + i) % len(self.colors)]
            
            overlay = frame.copy()
            cv2.circle(overlay, (center_x, center_y), radius, color, 2)
            frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        
        # Dessiner des lignes radiales
        num_lines = 16
        for i in range(num_lines):
            angle = i * (2 * math.pi / num_lines) + self.time * 0.5
            length = 200 + self.pulse * 100
            
            x1 = int(center_x + math.cos(angle) * 50)
            y1 = int(center_y + math.sin(angle) * 50)
            x2 = int(center_x + math.cos(angle) * length)
            y2 = int(center_y + math.sin(angle) * length)
            
            color_idx = int(self.time * 4 + i) % len(self.colors)
            color = self.colors[color_idx]
            
            cv2.line(frame, (x1, y1), (x2, y2), color, 2)
