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
    
    def _plasma_value(self, x, y):
        """Calcule la valeur du plasma à une position donnée."""
        total = 0.0
        
        # Combiner plusieurs ondes sinusoïdales
        for i in range(self.num_waves):
            dx, dy = self.wave_directions[i]
            freq = self.wave_frequencies[i]
            amp = self.wave_amplitudes[i] * (1 + self.volume_factor * 0.5)
            phase = self.wave_phases[i]
            
            # Ajouter des variations basées sur la position
            dist_from_center = math.sqrt((x - self.center_x) ** 2 + (y - self.center_y) ** 2)
            dist_factor = dist_from_center / (self.width // 2)
            
            # Moduler la fréquence et l'amplitude en fonction de la distance
            mod_freq = freq * (0.5 + dist_factor * 0.5)
            mod_amp = amp * (0.8 + dist_factor * 0.2)
            
            # Calculer la valeur de l'onde
            value = math.sin(
                x * dx * mod_freq * 2 * math.pi + 
                y * dy * mod_freq * 2 * math.pi + 
                phase * math.pi + 
                self.time * self.time_scale * 10
            ) * mod_amp
            
            total += value
        
        # Ajouter une distorsion radiale basée sur les basses
        dist_from_center = math.sqrt((x - self.center_x) ** 2 + (y - self.center_y) ** 2)
        radial_distortion = math.sin(dist_from_center * 0.01 + self.time * 2) * self.bass_factor * 100
        total += radial_distortion
        
        # Ajouter une distorsion spiralée basée sur le treble
        angle = math.atan2(y - self.center_y, x - self.center_x)
        spiral_distortion = math.sin(angle * 8 + self.time * 3 + self.treble_factor * math.pi) * self.treble_factor * 50
        total += spiral_distortion
        
        # Ajouter un effet de beat
        if self.beat_factor > 0:
            total += math.sin(self.time * 10 + self.beat_factor * 5) * self.beat_factor * 200
        
        return total
    
    def _get_color_from_value(self, value):
        """Convertit une valeur de plasma en couleur."""
        # Normaliser la valeur
        value = (value % 360) / 360.0
        
        # Utiliser la phase des couleurs pour animer
        hue_shift = self.color_phase + value * 0.5
        hue_shift = hue_shift % 1.0
        
        # Convertir HSV en RGB (approximation rapide)
        # H: 0-1, S: 1, V: 1
        h = hue_shift * 6
        i = int(h)
        f = h - i
        
        if i == 0:
            r, g, b = 1, f, 0
        elif i == 1:
            r, g, b = 1 - f, 1, 0
        elif i == 2:
            r, g, b = 0, 1, f
        elif i == 3:
            r, g, b = 0, 1 - f, 1
        elif i == 4:
            r, g, b = f, 0, 1
        else:  # i == 5
            r, g, b = 1, 0, 1 - f
        
        # Convertir en RGB 0-255
        r = min(255, int(r * 255))
        g = min(255, int(g * 255))
        b = min(255, int(b * 255))
        
        # Appliquer la palette si spécifiée (mélanger avec les couleurs de la palette)
        if self.color_palette != 'rainbow':
            palette_color = self.colors[int(value * len(self.colors)) % len(self.colors)]
            # Mélanger avec la couleur HSV
            mix_factor = 0.5
            r = int(r * mix_factor + palette_color[0] * (1 - mix_factor))
            g = int(g * mix_factor + palette_color[1] * (1 - mix_factor))
            b = int(b * mix_factor + palette_color[2] * (1 - mix_factor))
        
        return (r, g, b)
    
    def render(self, surface):
        """Rendu avec Pygame."""
        import pygame
        
        # Créer un tableau numpy pour calculer le plasma
        # Pour éviter de tout recalculer pixel par pixel
        width, height = self.width, self.height
        
        # Pour des performances raisonnables, on sample avec un pas
        sample_step = max(1, width // 200)
        
        # Créer une surface temporaire
        temp_surface = pygame.Surface((width, height))
        
        # Dessiner le plasma
        for x in range(0, width, sample_step):
            for y in range(0, height, sample_step):
                value = self._plasma_value(x, y)
                color = self._get_color_from_value(value)
                
                # Dessiner un rectangle de la taille du sample
                rect = pygame.Rect(x, y, sample_step, sample_step)
                pygame.draw.rect(temp_surface, color, rect)
        
        # Copier sur la surface de sortie
        surface.blit(temp_surface, (0, 0))
        
        # Ajouter un effet de vignette (bords sombres)
        vignette = pygame.Surface((width, height), pygame.SRCALPHA)
        for x in range(0, width, max(1, width // 50)):
            for y in range(0, height, max(1, height // 50)):
                dist = math.sqrt((x - self.center_x) ** 2 + (y - self.center_y) ** 2)
                max_dist = math.sqrt(self.center_x ** 2 + self.center_y ** 2)
                alpha = int(100 * (1 - dist / max_dist))
                if alpha > 0:
                    pygame.draw.circle(vignette, (0, 0, 0, alpha), (x, y), max(1, width // 100))
        
        surface.blit(vignette, (0, 0))
        
        # Ajouter des motifs supplémentaires
        self._draw_additional_patterns(surface)
    
    def _draw_additional_patterns(self, surface):
        """Ajouter des motifs supplémentaires pour enrichir le plasma."""
        import pygame
        
        # Dessiner des cercles qui pulsent
        center_x, center_y = self.width // 2, self.height // 2
        for i in range(3):
            radius = int(50 + i * 80 + self.pulse * 50)
            alpha = 100 * (1 - i / 3)
            color = self.colors[int(self.time * 2 + i) % len(self.colors)]
            
            # Créer une surface temporaire pour la transparence
            s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, alpha), (center_x, center_y), radius, 2)
            surface.blit(s, (0, 0))
        
        # Dessiner des lignes radiales
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
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Pour l'export vidéo, on utilise un pas plus petit
        sample_step = max(1, width // 200)
        
        for x in range(0, width, sample_step):
            for y in range(0, height, sample_step):
                value = self._plasma_value(x, y)
                color = self._get_color_from_value(value)
                
                # Remplir le bloc
                frame[y:y+sample_step, x:x+sample_step] = list(color)
        
        # Ajouter un effet de vignette
        for x in range(width):
            for y in range(height):
                dist = math.sqrt((x - self.center_x) ** 2 + (y - self.center_y) ** 2)
                max_dist = math.sqrt(self.center_x ** 2 + self.center_y ** 2)
                vignette_factor = 1.0 - dist / max_dist
                if vignette_factor < 0.3:
                    # Assombrir les bords
                    frame[y, x] = [int(c * vignette_factor * 3) for c in frame[y, x]]
        
        # Ajouter des motifs supplémentaires
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
