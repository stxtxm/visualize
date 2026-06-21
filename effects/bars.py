"""
Effet de barres de fréquence style égaliseur.
"""

import numpy as np
from effects.base import BaseEffect


class BarEffect(BaseEffect):
    """
    Effet de barres de fréquence qui réagissent au son.
    """
    
    def __init__(self, width, height, color_palette='psychedelic'):
        super().__init__(width, height, color_palette)
        self.num_bars = 64
        self.bar_width = max(1, width // self.num_bars)
        self.bar_heights = [0.0] * self.num_bars
        self.target_heights = [0.0] * self.num_bars
        self.smoothing = 0.2
    
    def update(self, audio_data, delta_time):
        super().update(audio_data, delta_time)
        
        if not audio_data or not audio_data['spectrum']:
            # Si pas de données, réduire progressivement les barres
            for i in range(self.num_bars):
                self.target_heights[i] = 0
        else:
            # Mapper le spectre FFT aux barres
            spectrum = audio_data['spectrum']
            spectrum_len = len(spectrum)
            
            for i in range(self.num_bars):
                # Calculer l'index dans le spectre
                spec_idx = int(i * spectrum_len / self.num_bars)
                if spec_idx < spectrum_len:
                    # Amplifier et normaliser la hauteur
                    self.target_heights[i] = spectrum[spec_idx] * self.height * 1.5
                else:
                    self.target_heights[i] = 0
        
        # Lissage des hauteurs
        for i in range(self.num_bars):
            self.bar_heights[i] = (
                self.bar_heights[i] * (1 - self.smoothing) +
                self.target_heights[i] * self.smoothing
            )
    
    def render(self, surface):
        """Rendu des barres sur la surface Pygame."""
        import pygame
        surface.fill((0, 0, 0))
        
        for i in range(self.num_bars):
            # Calculer la hauteur avec un minimum pour la visibilité
            bar_height = max(int(self.bar_heights[i]), 2)
            
            # Calculer la couleur (dépend de la position et du temps)
            color_idx = (i + int(self.time * 10)) % len(self.colors)
            color = self.colors[color_idx]
            
            # Dessiner la barre avec effet de dégradé
            x = i * self.bar_width
            y_start = self.height - bar_height
            
            # Dessiner chaque ligne de la barre avec un dégradé
            for h in range(0, bar_height, max(1, bar_height // 10)):
                # Calculer la couleur avec transparence
                alpha_factor = 1.0 - (h / bar_height) * 0.7
                bar_color = (
                    min(int(color[0] * alpha_factor), 255),
                    min(int(color[1] * alpha_factor), 255),
                    min(int(color[2] * alpha_factor), 255)
                )
                yy = self.height - 1 - h
                pygame.draw.line(
                    surface,
                    bar_color,
                    (x + self.bar_width // 2, self.height - 1),
                    (x + self.bar_width // 2, yy),
                    max(1, self.bar_width // 2)
                )
    
    def render_to_array(self):
        """Rendu vers un tableau numpy pour l'export vidéo."""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        for i in range(self.num_bars):
            bar_height = max(int(self.bar_heights[i]), 2)
            color_idx = (i + int(self.time * 10)) % len(self.colors)
            color = self.colors[color_idx]
            
            x = i * self.bar_width
            
            # Dessiner la barre avec dégradé
            for h in range(bar_height):
                alpha_factor = 1.0 - (h / bar_height) * 0.7
                bar_color = (
                    min(int(color[0] * alpha_factor), 255),
                    min(int(color[1] * alpha_factor), 255),
                    min(int(color[2] * alpha_factor), 255)
                )
                yy = self.height - 1 - h
                if 0 <= yy < self.height:
                    # Dessiner une ligne horizontale pour la barre
                    start_x = max(0, x)
                    end_x = min(self.width, x + self.bar_width)
                    if start_x < end_x:
                        frame[yy, start_x:end_x] = bar_color
        
        return frame
