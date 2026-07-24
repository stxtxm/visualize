"""
Effet de vague psychédélique.
"""

import numpy as np
import math
from effects.base import BaseEffect


class WaveEffect(BaseEffect):
    """
    Effet de vague qui réagit au son.
    """
    
    def __init__(self, width, height, color_palette='psychedelic'):
        super().__init__(width, height, color_palette)
        self.num_waves = 8
        self.amplitudes = [50.0] * self.num_waves
        self.frequencies = [0.01 * (i + 1) for i in range(self.num_waves)]
        self.phases = [0.0] * self.num_waves
        self.speed = 0.5
        self.center_x = width // 2
        self.center_y = height // 2
    
    def update(self, audio_data, delta_time):
        super().update(audio_data, delta_time)
        
        if audio_data:
            volume = audio_data.get('volume', 0)
            freq_bands = audio_data.get('frequency_bands', [])
            
            # Mettre à jour les amplitudes en fonction des bandes de fréquence
            for i in range(self.num_waves):
                band_idx = i % len(freq_bands) if freq_bands else 0
                self.amplitudes[i] = 50 + freq_bands[band_idx] * 200
            
            # Ajouter un effet de beat
            if audio_data.get('beat', False):
                for i in range(self.num_waves):
                    self.phases[i] += 0.5
        
        # Mettre à jour les phases
        for i in range(self.num_waves):
            self.phases[i] += delta_time * self.speed * (i + 1) * 0.5
    
    def render(self, surface):
        """Rendu de l'effet vague avec Pygame."""
        import pygame
        surface.fill((0, 0, 0))
        
        # Dessiner des vagues concentriques
        for i in range(self.num_waves):
            amplitude = self.amplitudes[i]
            frequency = self.frequencies[i]
            phase = self.phases[i]
            
            # Calculer la couleur avec rotation
            color_idx = (i + int(self.time * 3)) % len(self.colors)
            color = self.colors[color_idx]
            
            # Dessiner la vague
            num_points = 200
            points = []
            for j in range(num_points):
                angle = j * (2 * math.pi / num_points)
                radius = self.center_x * 0.8  # Rayon de base
                
                # Calculer le déplacement de la vague
                wave_displacement = amplitude * math.sin(
                    angle * frequency * 10 + phase * math.pi
                )
                
                r = radius + wave_displacement
                x = self.center_x + math.cos(angle) * r
                y = self.center_y + math.sin(angle) * r
                points.append((x, y))
            
            # Fermer le polygone
            if points:
                points.append(points[0])
            
            # Dessiner le polygone avec transparence
            if len(points) > 2:
                # Créer une surface temporaire pour la transparence
                s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                # Utiliser un alpha pour la couleur
                alpha_color = (*color, 60)
                pygame.draw.polygon(s, alpha_color, points)
                surface.blit(s, (0, 0))
    
    def render_to_array(self):
        """Rendu vers un tableau numpy pour l'export vidéo."""
        import cv2
        
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        num_points = 200
        angles = np.linspace(0, 2 * np.pi, num_points, endpoint=False, dtype=np.float32)
        cos_angles = np.cos(angles)
        sin_angles = np.sin(angles)
        radius = self.center_x * 0.8

        # Dessiner des vagues concentriques
        for i in range(self.num_waves):
            amplitude = self.amplitudes[i]
            frequency = self.frequencies[i]
            phase = self.phases[i]
            
            color_idx = (i + int(self.time * 3)) % len(self.colors)
            color = self.colors[color_idx]
            
            wave_displacement = amplitude * np.sin(angles * (frequency * 10.0) + phase * np.pi)
            r = radius + wave_displacement
            
            xs = (self.center_x + cos_angles * r).astype(np.int32)
            ys = (self.center_y + sin_angles * r).astype(np.int32)
            polygon = np.column_stack((xs, ys))
            polygon = np.vstack((polygon, polygon[0]))
            
            self._draw_alpha_poly(frame, cv2, polygon, color, 0.25)
        
        return frame
