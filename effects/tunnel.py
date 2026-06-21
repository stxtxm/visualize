"""
Effet de tunnel psychédélique.
"""

import numpy as np
import math
from effects.base import BaseEffect


class TunnelEffect(BaseEffect):
    """
    Effet de tunnel avec distorsion.
    """
    
    def __init__(self, width, height, color_palette='psychedelic'):
        super().__init__(width, height, color_palette)
        self.center_x = width // 2
        self.center_y = height // 2
        self.rotation = 0
        self.tunnel_depth = 30
        self.distortion = 0.0
        self.target_distortion = 0.0
    
    def update(self, audio_data, delta_time):
        super().update(audio_data, delta_time)
        
        self.rotation += delta_time * 0.5
        
        if audio_data:
            volume = audio_data.get('volume', 0)
            freq_bands = audio_data.get('frequency_bands', [])
            
            # La distorsion dépend du volume
            self.target_distortion = volume * 0.5
            
            # Ajouter un effet de beat
            if audio_data.get('beat', False):
                self.target_distortion += 0.3
        
        # Lissage de la distorsion
        self.distortion = (
            self.distortion * 0.8 +
            self.target_distortion * 0.2
        )
    
    def render(self, surface):
        """Rendu de l'effet tunnel avec Pygame."""
        import pygame
        surface.fill((0, 0, 0))
        
        # Dessiner des cercles concentriques avec distorsion
        max_radius = min(self.width, self.height) // 2
        
        for i in range(self.tunnel_depth):
            radius = int(max_radius * (i + 1) / self.tunnel_depth)
            if radius < 1:
                continue
            
            # Calculer la couleur
            color_idx = (i + int(self.time * 10)) % len(self.colors)
            color = self.colors[color_idx]
            
            # Appliquer la distorsion
            distortion_factor = self.distortion * (1 - i / self.tunnel_depth)
            
            # Dessiner le cercle avec distorsion
            num_points = 36
            points = []
            for j in range(num_points):
                angle = self.rotation + j * (2 * math.pi / num_points)
                
                # Appliquer la distorsion sinusoïdale
                distortion = math.sin(angle * 3 + self.time * 2) * distortion_factor * radius * 0.3
                
                r = radius + distortion
                x = self.center_x + math.cos(angle) * r
                y = self.center_y + math.sin(angle) * r
                points.append((int(x), int(y)))
            
            # Dessiner le polygone
            if len(points) > 2:
                pygame.draw.polygon(surface, color, points, 2)
    
    def render_to_array(self):
        """Rendu vers un tableau numpy pour l'export vidéo."""
        import cv2
        
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Dessiner des cercles concentriques avec distorsion
        max_radius = min(self.width, self.height) // 2
        
        for i in range(self.tunnel_depth):
            radius = int(max_radius * (i + 1) / self.tunnel_depth)
            if radius < 1:
                continue
            
            # Calculer la couleur
            color_idx = (i + int(self.time * 10)) % len(self.colors)
            color = self.colors[color_idx]
            
            # Appliquer la distorsion
            distortion_factor = self.distortion * (1 - i / self.tunnel_depth)
            
            # Dessiner le cercle avec distorsion
            num_points = 36
            points = []
            for j in range(num_points):
                angle = self.rotation + j * (2 * math.pi / num_points)
                
                # Appliquer la distorsion sinusoïdale
                distortion = math.sin(angle * 3 + self.time * 2) * distortion_factor * radius * 0.3
                
                r = radius + distortion
                x = self.center_x + math.cos(angle) * r
                y = self.center_y + math.sin(angle) * r
                points.append([int(x), int(y)])
            
            # Dessiner le polygone rempli
            if len(points) > 2:
                polygon = np.array(points, dtype=np.int32)
                cv2.fillPoly(frame, [polygon], color)
        
        return frame
