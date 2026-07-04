"""
Effet visuel classique inspiré de Winamp / Media Player.
Combine des barres verticales, un halo central, une profondeur et des éclats de beat.
"""

import math
import numpy as np
from effects.base import BaseEffect


class ClassicEffect(BaseEffect):
    """Rendu rétro moderne, très réactif au rythme."""

    def __init__(self, width, height, color_palette='winamp_classic'):
        super().__init__(width, height, color_palette)
        self.num_bars = 52
        self.bar_heights = [0.0] * self.num_bars
        self.target_heights = [0.0] * self.num_bars
        self.bar_width = max(3, width // (self.num_bars + 2))
        self.baseline = height * 0.78
        self.depth = 0.0
        self.target_depth = 0.0
        self.orbit = 0.0
        self.target_orbit = 0.0
        self.rotation = 0.0
        self.target_rotation = 0.0
        self.background_shift = 0.0
        self.glow = 0.0
        self.target_glow = 0.0
        self.center_x = width // 2
        self.center_y = height // 2
        self.flash = 0.0
        self.target_flash = 0.0
        self.sweep = 0.0
        self.peak_hold = [0.0] * self.num_bars
        self.peak_decay = [0.0] * self.num_bars

    def update(self, audio_data, delta_time):
        super().update(audio_data, delta_time)

        if audio_data:
            volume = audio_data.get('volume', 0)
            energy = audio_data.get('energy', volume)
            freq_bands = audio_data.get('frequency_bands', [])
            beat = audio_data.get('beat', False)
            beat_strength = audio_data.get('beat_strength', 0)
            beat_phase = audio_data.get('beat_phase', 0.0)
            bpm = audio_data.get('bpm', 120)

            self.target_flash = max(0.0, min(1.0, beat_strength * 0.9 + energy * 0.3 + beat_phase * 0.15))
            if beat:
                self.target_flash = 1.0
            self.target_depth = max(0.0, min(1.0, volume * 0.9 + energy * 0.45 + beat_strength * 0.18))
            self.target_orbit = max(0.0, min(1.0, beat_strength * 0.8 + energy * 0.35 + beat_phase * 0.12))
            self.target_rotation = (energy * 0.3 + beat_strength * 0.5) * 1.2
            self.target_glow = max(0.0, min(1.0, volume * 0.35 + beat_strength * 0.5 + energy * 0.25))

            self.sweep += delta_time * (0.35 + (bpm / 220.0) * 1.2)
            self.background_shift += delta_time * (0.16 + beat_strength * 0.45)

            for i in range(self.num_bars):
                band_idx = min(len(freq_bands) - 1, int(i * len(freq_bands) / self.num_bars)) if freq_bands else 0
                band_value = freq_bands[band_idx] if freq_bands else 0.0
                bass_boost = 1.0 + (1.0 - i / self.num_bars) * 1.0
                target = band_value * self.height * 0.9 * bass_boost * (0.9 + energy * 0.9)
                if beat and beat_strength > 0.45:
                    target *= 1.25
                self.target_heights[i] = target

                if target > self.peak_hold[i]:
                    self.peak_hold[i] = target
                    self.peak_decay[i] = 0.45
                elif self.peak_decay[i] > 0:
                    self.peak_decay[i] = max(0.0, self.peak_decay[i] - delta_time * 1.2)

                self.peak_hold[i] = max(0.0, self.peak_hold[i] - delta_time * 55.0)
        else:
            self.target_flash *= 0.88
            self.target_glow *= 0.92
            for i in range(self.num_bars):
                self.target_heights[i] *= 0.9

        for i in range(self.num_bars):
            self.bar_heights[i] = self.bar_heights[i] * 0.78 + self.target_heights[i] * 0.22

        self.flash = self.flash * 0.78 + self.target_flash * 0.22
        self.depth = self.depth * 0.78 + self.target_depth * 0.22
        self.orbit = self.orbit * 0.78 + self.target_orbit * 0.22
        self.rotation = self.rotation * 0.78 + self.target_rotation * 0.22
        self.glow = self.glow * 0.78 + self.target_glow * 0.22

    def render(self, surface):
        import pygame

        # Background dynamique
        for row in range(self.height):
            blend = row / max(1, self.height)
            shift = math.sin(self.background_shift + row * 0.02) * 18
            base_color = (
                int(max(0, min(255, 8 + 24 * (1 - blend) + self.depth * 12 + shift * 0.2))),
                int(max(0, min(255, 8 + 18 * (1 - blend) + self.depth * 10 + shift * 0.1))),
                int(max(0, min(255, 12 + 28 * (1 - blend) + self.depth * 14 + shift * 0.3))),
            )
            pygame.draw.line(surface, base_color, (0, row), (self.width, row))

        # Reticule de fond
        grid = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        grid_color = (35, 35, 55, min(80, int(40 + self.glow * 60)))
        step = max(48, self.width // 20)
        for gx in range(0, self.width, step):
            pygame.draw.line(grid, grid_color, (gx, 0), (gx, self.height), 1)
        for gy in range(0, self.height, step):
            pygame.draw.line(grid, grid_color, (0, gy), (self.width, gy), 1)
        surface.blit(grid, (0, 0))

        # Bass horizon glow
        horizon_color = (
            min(255, int(100 + self.depth * 80)),
            min(255, int(40 + self.depth * 50)),
            min(255, int(120 + self.depth * 70)),
        )
        horizon_alpha = int(40 + self.flash * 120)
        horizon_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(horizon_surface, (*horizon_color, horizon_alpha), (0, int(self.baseline - 20), self.width, int(self.height - self.baseline + 20)))
        surface.blit(horizon_surface, (0, 0))

        # Bars et pic hold
        for i in range(self.num_bars):
            bar_height = max(3, int(self.bar_heights[i]))
            x = i * self.bar_width + int((self.width - self.bar_width * self.num_bars) / 2)
            y = int(self.baseline - bar_height)
            color_idx = (i + int(self.time * 8)) % len(self.colors)
            color = self.colors[color_idx]
            glow_color = tuple(min(255, int(c * (0.6 + self.flash * 0.4 + self.glow * 0.5))) for c in color)
            pygame.draw.rect(surface, glow_color, (x - 1, y - 1, max(2, self.bar_width), bar_height + 2), 1)
            for h in range(min(bar_height, self.height)):
                alpha_factor = 1.0 - (h / bar_height) * 0.5
                line_color = tuple(min(255, int(c * (0.35 + alpha_factor * 0.7))) for c in color)
                pygame.draw.line(surface, line_color, (x + self.bar_width // 2, self.height - 1 - h), (x + self.bar_width // 2, self.height - 1 - h), max(1, self.bar_width - 2))
            pygame.draw.rect(surface, color, (x, y, max(2, self.bar_width - 2), bar_height))
            top_cap = pygame.Rect(x, y, max(2, self.bar_width - 2), 4)
            pygame.draw.rect(surface, (255, 255, 255), top_cap)

            if self.peak_decay[i] > 0:
                peak_y = int(self.baseline - min(int(self.peak_hold[i]), self.height))
                peak_color = tuple(min(255, int(c * 1.6)) for c in color)
                pygame.draw.line(surface, peak_color, (x, peak_y), (x + max(2, self.bar_width - 2), peak_y), 2)

        # Bass ring
        for ring in range(6):
            radius = int(40 + ring * 26 + self.flash * 40 + self.orbit * 30 + math.sin(self.sweep + ring * 0.5) * 12)
            ring_color = self.colors[(int(self.time * 2) + ring) % len(self.colors)]
            pygame.draw.circle(surface, ring_color, (self.center_x, self.center_y), radius, 2)

        # Inner pulse burst
        inner = int(50 + self.flash * 70 + self.orbit * 50)
        center_color = self.colors[int(self.time * 3) % len(self.colors)]
        pygame.draw.circle(surface, center_color, (self.center_x, self.center_y), inner, 3)

        # Star beams
        for i in range(18):
            angle = self.rotation + i * (2 * math.pi / 18)
            length = 140 + self.flash * 90 + self.orbit * 40
            x1 = self.center_x + math.cos(angle) * 30
            y1 = self.center_y + math.sin(angle) * 30
            x2 = self.center_x + math.cos(angle) * length
            y2 = self.center_y + math.sin(angle) * length
            beam_color = tuple(min(255, int(c * (0.8 + self.flash * 0.5))) for c in center_color)
            pygame.draw.line(surface, beam_color, (int(x1), int(y1)), (int(x2), int(y2)), 1)

        if self.flash > 0.2:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            alpha = int(80 * self.flash)
            pygame.draw.circle(overlay, (*center_color, alpha), (self.center_x, self.center_y), int(260 + self.flash * 90), 0)
            surface.blit(overlay, (0, 0))

    def render_to_array(self):
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        for row in range(self.height):
            blend = row / max(1, self.height)
            shift = math.sin(self.background_shift + row * 0.02) * 18
            base_color = (
                int(max(0, min(255, 8 + 24 * (1 - blend) + self.depth * 12 + shift * 0.2))),
                int(max(0, min(255, 8 + 18 * (1 - blend) + self.depth * 10 + shift * 0.1))),
                int(max(0, min(255, 12 + 28 * (1 - blend) + self.depth * 14 + shift * 0.3))),
            )
            frame[row, :] = base_color

        for i in range(self.num_bars):
            bar_height = max(3, int(self.bar_heights[i]))
            x = i * self.bar_width + int((self.width - self.bar_width * self.num_bars) / 2)
            y = int(self.baseline - bar_height)
            color_idx = (i + int(self.time * 8)) % len(self.colors)
            color = self.colors[color_idx]
            for h in range(bar_height):
                alpha_factor = 1.0 - (h / bar_height) * 0.5
                line_color = tuple(min(255, int(c * (0.35 + alpha_factor * 0.7))) for c in color)
                yy = self.height - 1 - h
                if 0 <= yy < self.height:
                    frame[yy, x:x + max(2, self.bar_width - 2)] = line_color
            if 0 <= y < self.height:
                frame[y:self.height, x:x + max(2, self.bar_width - 2)] = color
            if self.peak_decay[i] > 0:
                peak_y = int(self.baseline - min(int(self.peak_hold[i]), self.height))
                if 0 <= peak_y < self.height:
                    frame[peak_y:peak_y + 2, x:x + max(2, self.bar_width - 2)] = tuple(min(255, int(c * 1.6)) for c in color)

        cv2 = __import__('cv2')
        for ring in range(6):
            radius = int(40 + ring * 26 + self.flash * 40 + self.orbit * 30 + math.sin(self.sweep + ring * 0.5) * 12)
            color = self.colors[(int(self.time * 2) + ring) % len(self.colors)]
            cv2.circle(frame, (self.center_x, self.center_y), radius, color, 2)

        inner = int(50 + self.flash * 70 + self.orbit * 50)
        center_color = self.colors[int(self.time * 3) % len(self.colors)]
        cv2.circle(frame, (self.center_x, self.center_y), inner, center_color, 3)

        for i in range(18):
            angle = self.rotation + i * (2 * math.pi / 18)
            length = 140 + self.flash * 90 + self.orbit * 40
            x1 = int(self.center_x + math.cos(angle) * 30)
            y1 = int(self.center_y + math.sin(angle) * 30)
            x2 = int(self.center_x + math.cos(angle) * length)
            y2 = int(self.center_y + math.sin(angle) * length)
            cv2.line(frame, (x1, y1), (x2, y2), tuple(min(255, int(c * (0.8 + self.flash * 0.5))) for c in center_color), 1)

        if self.flash > 0.2:
            cv2.circle(frame, (self.center_x, self.center_y), int(260 + self.flash * 90), center_color, -1)

        return frame
