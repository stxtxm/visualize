"""
Effet de cercles concentriques pulsants.
"""

import numpy as np
import math
from effects.base import BaseEffect


class CircleEffect(BaseEffect):
    """
    Effet de cercles concentriques qui pulsent au rythme de la musique.
    """
    
    def __init__(self, width, height, color_palette='psychedelic'):
        super().__init__(width, height, color_palette)
        self.center_x = width // 2
        self.center_y = height // 2
        self.num_circles = 10
        self.radii = [0.0] * self.num_circles
        self.target_radii = [0.0] * self.num_circles
        self.angles = [0.0] * self.num_circles
        
        # Initialiser les cercles
        max_radius = min(width, height) // 2 - 20
        for i in range(self.num_circles):
            base_radius = max_radius * (i + 1) / self.num_circles
            self.radii[i] = base_radius
            self.target_radii[i] = base_radius
            self.angles[i] = i * 0.2
    
    def update(self, audio_data, delta_time):
        super().update(audio_data, delta_time)
        
        if audio_data:
            volume = audio_data.get('volume', 0)
            freq_bands = audio_data.get('frequency_bands', [])
            
            # Calculer un facteur de pulsation
            pulse_factor = 1.0 + volume * 0.5
            
            # Ajouter un effet de beat
            if audio_data.get('beat', False):
                pulse_factor += 0.5
            
            for i in range(self.num_circles):
                # Chaque cercle réagit à une bande de fréquence différente
                band_idx = i % len(freq_bands) if freq_bands else 0
                band_factor = freq_bands[band_idx] if freq_bands else 1.0
                
                # Calculer le rayon cible
                base_radius = min(self.width, self.height) // 2 * (i + 1) / self.num_circles
                self.target_radii[i] = base_radius * pulse_factor * (0.8 + band_factor * 0.4)
                
                # Faire tourner les cercles
                self.angles[i] += delta_time * (0.5 + band_factor * 2)
        
        # Lissage des rayons
        for i in range(self.num_circles):
            self.radii[i] = (
                self.radii[i] * 0.9 +
                self.target_radii[i] * 0.1
            )
    
    def render(self, surface):
        """Rendu des cercles concentriques avec Pygame."""
        import pygame
        surface.fill((0, 0, 0))
        
        for i in range(self.num_circles):
            radius = int(self.radii[i])
            if radius < 1:
                continue
            
            # Calculer la couleur avec rotation
            color_idx = (i + int(self.time * 5 + self.angles[i] * 2)) % len(self.colors)
            color = self.colors[color_idx]
            
            # Dessiner le cercle
            pygame.draw.circle(
                surface,
                color,
                (self.center_x, self.center_y),
                radius,
                2  # Épaisseur de la ligne
            )
            
            # Ajouter un effet de traits radiaux
            num_lines = 36
            for j in range(num_lines):
                angle = self.angles[i] + j * (2 * math.pi / num_lines)
                inner_radius = radius * 0.8
                outer_radius = radius
                
                x1 = self.center_x + math.cos(angle) * inner_radius
                y1 = self.center_y + math.sin(angle) * inner_radius
                x2 = self.center_x + math.cos(angle) * outer_radius
                y2 = self.center_y + math.sin(angle) * outer_radius
                
                # Couleur avec transparence
                line_color = (
                    color[0] // 2,
                    color[1] // 2,
                    color[2] // 2
                )
                
                pygame.draw.line(surface, line_color, (int(x1), int(y1)), (int(x2), int(y2)), 1)
    
    def render_to_array(self):
        """Rendu vers un tableau numpy pour l'export vidéo."""
        import cv2
        
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        for i in range(self.num_circles):
            radius = int(self.radii[i])
            if radius < 1:
                continue
            
            color_idx = (i + int(self.time * 5 + self.angles[i] * 2)) % len(self.colors)
            color = self.colors[color_idx]
            
            # Dessiner le cercle
            cv2.circle(frame, (self.center_x, self.center_y), radius, color, 2)
            
            # Ajouter un effet de traits radiaux
            num_lines = 36
            for j in range(num_lines):
                angle = self.angles[i] + j * (2 * math.pi / num_lines)
                inner_radius = int(radius * 0.8)
                outer_radius = radius
                
                x1 = int(self.center_x + math.cos(angle) * inner_radius)
                y1 = int(self.center_y + math.sin(angle) * inner_radius)
                x2 = int(self.center_x + math.cos(angle) * outer_radius)
                y2 = int(self.center_y + math.sin(angle) * outer_radius)
                
                line_color = (
                    color[0] // 2,
                    color[1] // 2,
                    color[2] // 2
                )
                
                cv2.line(frame, (x1, y1), (x2, y2), line_color, 1)
        
        return frame
