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
        """Rendu des barres style égaliseur classique Winamp."""
        if not HAS_PYGAME:
            return
        
        import pygame
        surface.fill((10, 10, 15)) # Fond sombre rétro
        
        # Grille d'arrière-plan rétro
        grid_color = (25, 25, 35)
        for gy in range(0, self.height, 20):
            pygame.draw.line(surface, grid_color, (0, gy), (self.width, gy), 1)
            
        block_h = 4
        block_gap = 2
        block_total = block_h + block_gap
        max_blocks = self.height // block_total
        
        for i in range(self.num_bars):
            # Hauteur normalisée
            norm_height = self.bar_heights[i] / self.height
            norm_height = max(0.0, min(1.0, norm_height * (1.0 + self.pulse * 0.2)))
            num_blocks = int(norm_height * max_blocks)
            
            x = i * self.bar_width
            w = self.bar_width - 2
            if w < 1:
                w = 1
                
            # Blocs empilés de bas en haut
            for b in range(num_blocks):
                by = self.height - (b + 1) * block_total
                
                height_ratio = b / max_blocks
                if height_ratio < 0.6:
                    color = (0, 235, 100) # Vert
                elif height_ratio < 0.85:
                    color = (235, 235, 0) # Jaune
                else:
                    color = (255, 0, 50) # Rouge
                    
                pygame.draw.rect(surface, color, (x, by, w, block_h))
                
            # Pic flottant (peak hold)
            peak_ratio = self.peak_values[i] / self.height
            if peak_ratio > 0.02:
                peak_block = int(peak_ratio * max_blocks)
                peak_by = self.height - (peak_block + 1) * block_total
                peak_by = max(0, min(self.height - block_total, peak_by))
                
                peak_color = (0, 240, 255) # Cyan néon
                pygame.draw.rect(surface, peak_color, (x, peak_by, w, 2))
    
    def render_to_array(self):
        """Rendu vers un tableau numpy pour l'export vidéo (style Winamp) hautement optimisé."""
        import cv2
        
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:, :] = [15, 10, 10] # Fond BGR sombre
        
        # Grille
        grid_color = (35, 25, 25)
        for gy in range(0, self.height, 20):
            cv2.line(frame, (0, gy), (self.width, gy), grid_color, 1)
            
        block_h = 4
        block_gap = 2
        block_total = block_h + block_gap
        max_blocks = self.height // block_total
        
        b_yellow_thresh = int(max_blocks * 0.6)
        b_red_thresh = int(max_blocks * 0.85)

        green_color = np.array([100, 235, 0], dtype=np.uint8)
        yellow_color = np.array([0, 235, 235], dtype=np.uint8)
        red_color = np.array([50, 0, 255], dtype=np.uint8)
        peak_color = np.array([255, 240, 0], dtype=np.uint8)
        bg_color = np.array([15, 10, 10], dtype=np.uint8)

        for i in range(self.num_bars):
            norm_height = self.bar_heights[i] / self.height
            norm_height = max(0.0, min(1.0, norm_height * (1.0 + self.pulse * 0.2)))
            num_blocks = int(norm_height * max_blocks)
            
            x = i * self.bar_width
            w = max(1, self.bar_width - 2)
            x_end = x + w
            
            if num_blocks > 0:
                # 1. Vert (b = 0 .. b_yellow_thresh)
                n_green = min(num_blocks, b_yellow_thresh)
                if n_green > 0:
                    y_top = self.height - n_green * block_total
                    frame[y_top:self.height, x:x_end] = green_color

                # 2. Jaune (b = b_yellow_thresh .. b_red_thresh)
                if num_blocks > b_yellow_thresh:
                    n_yellow = min(num_blocks, b_red_thresh)
                    y_top_y = self.height - n_yellow * block_total
                    y_bot_y = self.height - b_yellow_thresh * block_total
                    frame[y_top_y:y_bot_y, x:x_end] = yellow_color

                # 3. Rouge (b = b_red_thresh .. num_blocks)
                if num_blocks > b_red_thresh:
                    y_top_r = self.height - num_blocks * block_total
                    y_bot_r = self.height - b_red_thresh * block_total
                    frame[y_top_r:y_bot_r, x:x_end] = red_color

                # Carve out block gaps for all filled blocks
                y_filled_top = self.height - num_blocks * block_total
                # Block gap coordinates
                gap_offsets = np.arange(self.height - block_gap, y_filled_top - 1, -block_total)
                for go in gap_offsets:
                    frame[go:go + block_gap, x:x_end] = bg_color

            # Pic flottant (peak hold)
            peak_ratio = self.peak_values[i] / self.height
            if peak_ratio > 0.02:
                peak_block = int(peak_ratio * max_blocks)
                peak_by = self.height - (peak_block + 1) * block_total
                peak_by = max(0, min(self.height - block_total, peak_by))
                frame[peak_by:peak_by + 2, x:x_end] = peak_color
                
        return frame
    
    def cleanup(self):
        """Nettoyer les ressources."""
        pass  # Rien à nettoyer pour l'instant
