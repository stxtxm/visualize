"""
Effet de spectre circulaire inspiré de Winamp.
Crée un spectre audio circulaire avec des bandes de fréquence qui pulsent.
"""

import numpy as np
import math
from effects.base import BaseEffect


class SpectrumEffect(BaseEffect):
    """
    Effet de spectre circulaire style Winamp.
    Les bandes de fréquence sont disposées en cercle et pulsent au rythme de la musique.
    """
    
    def __init__(self, width, height, color_palette='psychedelic'):
        super().__init__(width, height, color_palette)
        self.center_x = width // 2
        self.center_y = height // 2
        self.num_bands = 32  # Nombre de bandes de fréquence
        self.band_heights = [0.0] * self.num_bands
        self.target_heights = [0.0] * self.num_bands
        self.band_angles = [0.0] * self.num_bands
        self.smoothing = 0.15
        self.rotation = 0.0
        self.rotation_speed = 0.0
        self.pulse = 0.0
        self.target_pulse = 0.0
        self.peak_values = [0.0] * self.num_bands
        self.peak_decay = [0.0] * self.num_bands
        
        # Initialiser les angles des bandes
        for i in range(self.num_bands):
            self.band_angles[i] = i * (2 * math.pi / self.num_bands)
    
    def update(self, audio_data, delta_time):
        super().update(audio_data, delta_time)
        
        # Rotation de base
        self.rotation += self.rotation_speed * delta_time
        
        if audio_data:
            volume = audio_data.get('volume', 0)
            energy = audio_data.get('energy', volume)
            freq_bands = audio_data.get('frequency_bands', [])
            beat = audio_data.get('beat', False)
            beat_strength = audio_data.get('beat_strength', 0)
            beat_phase = audio_data.get('beat_phase', 0.0)
            bpm = audio_data.get('bpm', 120)
            spectral_centroid = audio_data.get('spectral_centroid', 0.5)
            
            # Calculer la rotation en fonction du BPM et du centroid spectral
            bpm_normalized = (bpm - 60) / (180 - 60)
            self.rotation_speed = bpm_normalized * 0.35 + volume * 0.15 + spectral_centroid * 0.1
            
            # Calculer la pulsation en fonction du volume, de l’énergie et du beat
            self.target_pulse = max(volume, energy * 0.8)
            if beat:
                self.target_pulse = min(self.target_pulse + beat_strength * 0.9, 1.0)
            self.target_pulse = min(self.target_pulse + beat_phase * 0.15, 1.0)
            
            # Mettre à jour les hauteurs des bandes
            for i in range(self.num_bands):
                # Mapper les bandes de fréquence
                band_idx = int(i * len(freq_bands) / self.num_bands) if freq_bands else 0
                band_value = freq_bands[band_idx] if band_idx < len(freq_bands) else 0.0
                
                # Calculer la hauteur cible avec amplification
                self.target_heights[i] = band_value * 180 * (1 + energy * 0.65 + spectral_centroid * 0.2)
                
                # Lissage
                self.band_heights[i] = (
                    self.band_heights[i] * (1 - self.smoothing) +
                    self.target_heights[i] * self.smoothing
                )
                
                # Mettre à jour les pics
                if band_value > self.peak_values[i]:
                    self.peak_values[i] = band_value
                    self.peak_decay[i] = 1.0
                else:
                    self.peak_decay[i] = max(0.0, self.peak_decay[i] - delta_time * 2)
        else:
            self.target_pulse = 0.0
            self.rotation_speed *= 0.95
        
        # Lissage de la pulsation
        self.pulse = (
            self.pulse * (1 - self.smoothing * 2) +
            self.target_pulse * self.smoothing * 2
        )
    
    def _get_color_for_band(self, band_idx, intensity=1.0):
        """Retourne une couleur pour une bande donnée."""
        # Utiliser la palette, mais avec une intensité variable
        color = self.colors[band_idx % len(self.colors)]
        
        # Ajuster la luminosité en fonction de l'intensité
        r, g, b = color
        r = min(255, int(r * intensity))
        g = min(255, int(g * intensity))
        b = min(255, int(b * intensity))
        
        return (r, g, b)
    
    def render(self, surface):
        """Rendu du spectre circulaire avec Pygame."""
        import pygame
        surface.fill((0, 0, 0))
        
        # Rayon de base
        base_radius = min(self.width, self.height) // 3
        
        # Dessiner les bandes de fréquence
        for i in range(self.num_bands):
            # Calculer la hauteur avec pulsation
            band_height = int(self.band_heights[i] * (1 + self.pulse * 0.3))
            
            # Calculer la couleur avec rotation
            color_idx = (i + int(self.time * 8)) % len(self.colors)
            color = self.colors[color_idx]
            
            # Position angulaire avec rotation
            angle = self.band_angles[i] + self.rotation
            
            # Calculer les positions
            inner_radius = base_radius - 20
            outer_radius = inner_radius + band_height
            
            # Coordonnées des points
            x1 = self.center_x + math.cos(angle) * inner_radius
            y1 = self.center_y + math.sin(angle) * inner_radius
            x2 = self.center_x + math.cos(angle) * outer_radius
            y2 = self.center_y + math.sin(angle) * outer_radius
            
            # Dessiner la bande
            pygame.draw.line(
                surface,
                color,
                (int(x1), int(y1)),
                (int(x2), int(y2)),
                max(2, int(5 * (1 + volume * 0.5))) if 'volume' in locals() else 2
            )
            
            # Dessiner les pics
            if self.peak_decay[i] > 0:
                peak_radius = outer_radius + 15 * self.peak_decay[i]
                peak_x = self.center_x + math.cos(angle) * peak_radius
                peak_y = self.center_y + math.sin(angle) * peak_radius
                
                # Couleur plus claire pour les pics
                peak_color = (
                    min(255, int(color[0] * 1.5)),
                    min(255, int(color[1] * 1.5)),
                    min(255, int(color[2] * 1.5))
                )
                
                pygame.draw.circle(surface, peak_color, (int(peak_x), int(peak_y)), 3)
        
        # Dessiner un cercle central qui pulse
        center_size = int(15 + self.pulse * 25)
        center_color = self.colors[int(self.time * 4) % len(self.colors)]
        pygame.draw.circle(surface, center_color, (self.center_x, self.center_y), center_size, 2)
        
        # Ajouter un effet de fond avec des cercles concentriques
        for i in range(3):
            radius = base_radius + i * 30
            alpha = 50 * (1 - i / 3)
            circle_color = (*center_color, alpha)
            
            # Créer une surface temporaire pour la transparence
            s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.circle(s, circle_color, (self.center_x, self.center_y), radius, 1)
            surface.blit(s, (0, 0))
    
    def render_to_array(self):
        """Rendu vers un tableau numpy pour l'export vidéo."""
        import cv2
        
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Rayon de base
        base_radius = min(self.width, self.height) // 3
        
        # Dessiner les bandes de fréquence
        for i in range(self.num_bands):
            band_height = int(self.band_heights[i] * (1 + self.pulse * 0.3))
            color_idx = (i + int(self.time * 8)) % len(self.colors)
            color = self.colors[color_idx]
            
            angle = self.band_angles[i] + self.rotation
            inner_radius = base_radius - 20
            outer_radius = inner_radius + band_height
            
            x1 = int(self.center_x + math.cos(angle) * inner_radius)
            y1 = int(self.center_y + math.sin(angle) * inner_radius)
            x2 = int(self.center_x + math.cos(angle) * outer_radius)
            y2 = int(self.center_y + math.sin(angle) * outer_radius)
            
            cv2.line(frame, (x1, y1), (x2, y2), color, max(2, int(5 * (1 + self.pulse * 0.5))))
            
            # Dessiner les pics
            if self.peak_decay[i] > 0:
                peak_radius = outer_radius + 15 * int(self.peak_decay[i])
                peak_x = int(self.center_x + math.cos(angle) * peak_radius)
                peak_y = int(self.center_y + math.sin(angle) * peak_radius)
                cv2.circle(frame, (peak_x, peak_y), 3, (
                    min(255, int(color[0] * 1.5)),
                    min(255, int(color[1] * 1.5)),
                    min(255, int(color[2] * 1.5))
                ), -1)
        
        # Dessiner le cercle central
        center_size = int(15 + self.pulse * 25)
        center_color = self.colors[int(self.time * 4) % len(self.colors)]
        cv2.circle(frame, (self.center_x, self.center_y), center_size, center_color, 2)
        
        # Ajouter les cercles concentriques
        for i in range(3):
            radius = base_radius + i * 30
            alpha = 0.2 * (1 - i / 3)
            circle_color = center_color
            
            overlay = frame.copy()
            cv2.circle(overlay, (self.center_x, self.center_y), radius, circle_color, 1)
            frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        
        return frame
