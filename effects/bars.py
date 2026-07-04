"""
Effet de barres de fréquence style égaliseur.
"""

import sys
import os

# Importer numpy conditionnellement
HAS_NUMPY = False
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# Importer pygame conditionnellement
HAS_PYGAME = False
try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

from effects.base import BaseEffect


class BarEffect(BaseEffect):
    """
    Effet de barres de fréquence qui réagissent au son.
    Style Winamp classique avec des barres qui réagissent aux fréquences.
    """
    
    def __init__(self, width, height, color_palette='psychedelic'):
        super().__init__(width, height, color_palette)
        self.num_bars = 64
        self.bar_width = max(1, width // self.num_bars)
        self.bar_heights = [0.0] * self.num_bars
        self.target_heights = [0.0] * self.num_bars
        self.smoothing = 0.2
        # Pour l'effet peak hold (les pics restent brièvement)
        self.peak_values = [0.0] * self.num_bars
        self.peak_decay = [0.0] * self.num_bars
        self.peak_hold_time = 1.0  # Temps de rétention des pics en secondes
        # Pour l'effet de bordure
        self.border_thickness = 1
        # Pour l'effet de dégradé vertical
        self.gradient_intensity = 0.7
        # Pour l'effet de mouvement des barres
        self.pulse = 0.0
        self.target_pulse = 0.0
    
    def update(self, audio_data, delta_time):
        super().update(audio_data, delta_time)
        
        if not audio_data or not audio_data['spectrum']:
            # Si pas de données, réduire progressivement les barres
            for i in range(self.num_bars):
                self.target_heights[i] = 0
            self.target_pulse = 0.0
        else:
            # Mapper le spectre FFT aux barres
            spectrum = audio_data['spectrum']
            spectrum_len = len(spectrum)
            volume = audio_data.get('volume', 0)
            energy = audio_data.get('energy', volume)
            beat = audio_data.get('beat', False)
            beat_strength = audio_data.get('beat_strength', 0)
            beat_phase = audio_data.get('beat_phase', 0.0)
            spectral_centroid = audio_data.get('spectral_centroid', 0.5)
            
            # Calculer la pulsation globale plus marquée
            self.target_pulse = max(volume * 0.35, energy * 0.45)
            if beat:
                self.target_pulse = min(self.target_pulse + beat_strength * 0.6, 1.0)
            self.target_pulse = min(self.target_pulse + beat_phase * 0.2 + spectral_centroid * 0.1, 1.0)
            
            for i in range(self.num_bars):
                # Calculer l'index dans le spectre
                spec_idx = int(i * spectrum_len / self.num_bars)
                if spec_idx < spectrum_len:
                    # Amplifier et normaliser la hauteur
                    # Les basses (premières barres) ont plus d'amplitude
                    bass_boost = 1.0 + (1.0 - i / self.num_bars) * 0.9
                    self.target_heights[i] = spectrum[spec_idx] * self.height * 2.0 * bass_boost * (1.0 + energy * 0.35)
                else:
                    self.target_heights[i] = 0
                
                # Mettre à jour les pics
                if self.target_heights[i] > self.peak_values[i]:
                    self.peak_values[i] = self.target_heights[i]
                    self.peak_decay[i] = self.peak_hold_time
        
        # Lissage des hauteurs
        for i in range(self.num_bars):
            self.bar_heights[i] = (
                self.bar_heights[i] * (1 - self.smoothing) +
                self.target_heights[i] * self.smoothing
            )
            
            # Mettre à jour le decay des pics
            if self.peak_decay[i] > 0:
                self.peak_decay[i] -= delta_time
        
        # Lissage de la pulsation
        self.pulse = (
            self.pulse * (1 - self.smoothing * 2) +
            self.target_pulse * self.smoothing * 2
        )
    
    def render(self, surface):
        """Rendu des barres sur la surface Pygame."""
        # Si pygame n'est pas disponible, ne rien faire
        if not HAS_PYGAME:
            return
        
        import pygame
        surface.fill((0, 0, 0))
        
        for i in range(self.num_bars):
            # Calculer la hauteur avec un minimum pour la visibilité
            bar_height = max(int(self.bar_heights[i] * (1 + self.pulse * 0.2)), 2)
            
            # Calculer la couleur (dépend de la position et du temps)
            color_idx = (i + int(self.time * 10)) % len(self.colors)
            color = self.colors[color_idx]
            
            # Dessiner la barre avec effet de dégradé
            x = i * self.bar_width
            y_start = self.height - bar_height
            
            # Dessiner la barre principale avec dégradé
            for h in range(0, bar_height, max(1, bar_height // 10)):
                # Calculer la couleur avec transparence
                alpha_factor = 1.0 - (h / bar_height) * self.gradient_intensity
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
            
            # Dessiner les pics (peak hold)
            if self.peak_decay[i] > 0:
                peak_height = min(int(self.peak_values[i] * (self.peak_decay[i] / self.peak_hold_time)), self.height)
                peak_y = self.height - peak_height
                peak_color = (
                    min(int(color[0] * 1.8), 255),
                    min(int(color[1] * 1.8), 255),
                    min(int(color[2] * 1.8), 255)
                )
                # Dessiner une ligne fine pour le pic
                pygame.draw.line(
                    surface,
                    peak_color,
                    (x + self.bar_width // 2, peak_y),
                    (x + self.bar_width // 2, peak_y - 5),
                    max(1, self.bar_width // 3)
                )
            
            # Dessiner une bordure lumineuse
            if bar_height > 2:
                border_color = (
                    min(int(color[0] * 1.5), 255),
                    min(int(color[1] * 1.5), 255),
                    min(int(color[2] * 1.5), 255)
                )
                pygame.draw.line(
                    surface,
                    border_color,
                    (x, y_start),
                    (x, y_start + bar_height - 1),
                    self.border_thickness
                )
                pygame.draw.line(
                    surface,
                    border_color,
                    (x + self.bar_width, y_start),
                    (x + self.bar_width, y_start + bar_height - 1),
                    self.border_thickness
                )
    
    def render_to_array(self):
        """Rendu vers un tableau numpy pour l'export vidéo."""
        if not HAS_NUMPY:
            # Si numpy n'est pas disponible, retourner None ou une liste
            return None
        
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        for i in range(self.num_bars):
            bar_height = max(int(self.bar_heights[i] * (1 + self.pulse * 0.2)), 2)
            color_idx = (i + int(self.time * 10)) % len(self.colors)
            color = self.colors[color_idx]
            
            x = i * self.bar_width
            
            # Dessiner la barre avec dégradé
            for h in range(bar_height):
                alpha_factor = 1.0 - (h / bar_height) * self.gradient_intensity
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
            
            # Dessiner les pics (peak hold)
            if self.peak_decay[i] > 0:
                peak_height = min(int(self.peak_values[i] * (self.peak_decay[i] / self.peak_hold_time)), self.height)
                peak_y = self.height - peak_height
                peak_color = (
                    min(int(color[0] * 1.8), 255),
                    min(int(color[1] * 1.8), 255),
                    min(int(color[2] * 1.8), 255)
                )
                # Dessiner une ligne fine pour le pic
                for h in range(5):
                    yy = peak_y - h
                    if 0 <= yy < self.height:
                        start_x = max(0, x + self.bar_width // 2 - self.bar_width // 6)
                        end_x = min(self.width, x + self.bar_width // 2 + self.bar_width // 6)
                        if start_x < end_x:
                            frame[yy, start_x:end_x] = peak_color
            
            # Dessiner une bordure lumineuse
            if bar_height > 2:
                border_color = (
                    min(int(color[0] * 1.5), 255),
                    min(int(color[1] * 1.5), 255),
                    min(int(color[2] * 1.5), 255)
                )
                # Bordure gauche
                yy_start = self.height - bar_height
                for h in range(bar_height):
                    yy = yy_start + h
                    if 0 <= yy < self.height and x >= 0 and x < self.width:
                        frame[yy, x] = border_color
                # Bordure droite
                for h in range(bar_height):
                    yy = yy_start + h
                    if 0 <= yy < self.height and x + self.bar_width - 1 >= 0 and x + self.bar_width - 1 < self.width:
                        frame[yy, x + self.bar_width - 1] = border_color
        
        return frame
    
    def cleanup(self):
        """Nettoyer les ressources."""
        pass  # Rien à nettoyer pour l'instant
