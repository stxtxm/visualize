"""
Effet Neon Equalizer - Inspiré de Winamp / Windows Media Player classique.
Combine des barres d'égaliseur néon, un oscilloscope circulaire déformé,
et une grille synthwave - le tout réactif au rythme en temps réel.
"""

import math
import numpy as np
from effects.base import BaseEffect

# Import pygame conditionnellement
HAS_PYGAME = False
try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    pass


class ClassicEffect(BaseEffect):
    """
    Neon Equalizer - Le grand classique revisité.
    
    Rendu pur NumPy (compatible avec et sans Pygame) :
    - Barres spectrales néon avec pics flottants (style Winamp)
    - Oscilloscope circulaire déformé par les fréquences (style WMP)
    - Rayons pulsants et grille synthwave
    - Tout réactif au beat en temps réel
    """

    def __init__(self, width, height, color_palette='psychedelic'):
        super().__init__(width, height, color_palette)

        # Barres equalizer
        self.num_bars = 64
        self.bar_heights = np.zeros(self.num_bars, dtype=np.float64)
        self.target_heights = np.zeros(self.num_bars, dtype=np.float64)
        self.peak_hold = np.zeros(self.num_bars, dtype=np.float64)
        self.peak_decay = np.zeros(self.num_bars, dtype=np.float64)

        # Paramètres visuels
        self.flash = 0.0
        self.target_flash = 0.0
        self.energy = 0.0
        self.beat_strength = 0.0
        self.pulse = 0.0
        self.sweep = 0.0
        self.rotation = 0.0

        # Données audio courantes
        self.freq_bands = []
        self.bass_level = 0.0

        # Surface de rendu réutilisable (évite les allocations)
        self._frame = None

    def update(self, audio_data, delta_time):
        super().update(audio_data, delta_time)

        if not audio_data:
            # Decay smooth quand pas de données
            self.bar_heights *= 0.90
            self.peak_hold = np.maximum(0, self.peak_hold - delta_time * 60)
            self.flash *= 0.85
            self.pulse *= 0.85
            return

        volume = audio_data.get('volume', 0)
        energy = audio_data.get('energy', volume)
        freq_bands = audio_data.get('frequency_bands', [])
        beat = audio_data.get('beat', False)
        beat_strength = audio_data.get('beat_strength', 0)
        bpm = audio_data.get('bpm', 120)

        self.energy = energy
        self.beat_strength = beat_strength
        self.freq_bands = freq_bands if freq_bands else []

        # Basses = premières bandes
        if freq_bands and len(freq_bands) > 4:
            self.bass_level = float(np.mean(freq_bands[:4]))
        else:
            self.bass_level = energy

        # Flash sur les beats
        if beat:
            self.target_flash = 1.0
        else:
            self.target_flash = beat_strength * 0.6 + energy * 0.2
        self.flash = self.flash * 0.75 + self.target_flash * 0.25
        self.pulse = beat_strength * 0.8 + energy * 0.4

        # Rotation lente (accélérée sur les beats)
        self.rotation += delta_time * (0.4 + beat_strength * 1.2)
        self.sweep += delta_time * (0.3 + bpm / 200.0)

        # Calculer les hauteurs cibles des barres
        if freq_bands:
            for i in range(self.num_bars):
                band_idx = int(i * len(freq_bands) / self.num_bars)
                band_idx = min(band_idx, len(freq_bands) - 1)
                val = float(freq_bands[band_idx])

                # Boost les graves
                bass_boost = 1.0 + (1.0 - i / self.num_bars) * 0.8
                target = val * self.height * 0.75 * bass_boost
                if beat and beat_strength > 0.4:
                    target *= 1.3

                self.target_heights[i] = target

                # Peak hold
                if target > self.peak_hold[i]:
                    self.peak_hold[i] = target
                    self.peak_decay[i] = 0.5

                if self.peak_decay[i] > 0:
                    self.peak_decay[i] = max(0, self.peak_decay[i] - delta_time)
                self.peak_hold[i] = max(0, self.peak_hold[i] - delta_time * 50)

        # Smooth interpolation des barres
        self.bar_heights = self.bar_heights * 0.72 + self.target_heights * 0.28

    def render(self, surface):
        """Rendu Pygame (si disponible)."""
        if HAS_PYGAME and surface is not None:
            self._render_pygame(surface)

    def _render_pygame(self, surface):
        """Rendu haute performance via Pygame."""
        W, H = surface.get_size()
        s = H / 450.0  # Facteur d'échelle (base = preview 450px)
        surface.fill((8, 6, 12))  # Fond sombre quasi-noir

        # Grille synthwave (lignes verticales + horizontales subtiles)
        grid_col = (18, 15, 28)
        step_x = max(20, W // 40)
        step_y = max(20, H // 22)
        for x in range(0, W, step_x):
            pygame.draw.line(surface, grid_col, (x, 0), (x, H), 1)
        for y in range(0, H, step_y):
            pygame.draw.line(surface, grid_col, (0, y), (W, y), 1)

        cx, cy = W // 2, int(H * 0.40)

        # Rayons étoilés pulsants (style WMP)
        num_beams = 12
        for i in range(num_beams):
            angle = self.rotation + i * (2 * math.pi / num_beams)
            base_len = (60 + self.pulse * 80) * s
            length = base_len + math.sin(self.sweep + i * 0.7) * 20 * s
            x1 = cx + math.cos(angle) * 25 * s
            y1 = cy + math.sin(angle) * 25 * s
            x2 = cx + math.cos(angle) * length
            y2 = cy + math.sin(angle) * length
            col = self.colors[(i + int(self.time * 2)) % len(self.colors)]
            pygame.draw.line(surface, col, (int(x1), int(y1)), (int(x2), int(y2)), max(1, int(2 * s)))

        # Oscilloscope circulaire déformé par les fréquences
        if self.freq_bands and len(self.freq_bands) >= 4:
            for ring_idx in range(3):
                base_r = (40 + ring_idx * 22 + self.pulse * 18) * s
                num_pts = 80
                pts = []
                for p in range(num_pts):
                    angle = p * (2 * math.pi / num_pts) - self.rotation * (0.8 + ring_idx * 0.15)
                    band_i = int(p * len(self.freq_bands) / num_pts)
                    band_i = min(band_i, len(self.freq_bands) - 1)
                    val = float(self.freq_bands[band_i])
                    r = base_r + val * 55 * s
                    px = cx + math.cos(angle) * r
                    py = cy + math.sin(angle) * r
                    pts.append((int(px), int(py)))

                if len(pts) >= 3:
                    col = self.colors[(ring_idx + int(self.time)) % len(self.colors)]
                    pygame.draw.polygon(surface, (*col, 30), pts)
                    pygame.draw.polygon(surface, col, pts, max(1, int(2 * s)))

        # Flash de beat (halo lumineux centré)
        if self.flash > 0.1:
            flash_surf = pygame.Surface((W, H), pygame.SRCALPHA)
            col = self.colors[int(self.time * 3) % len(self.colors)]
            alpha = int(self.flash * 60)
            r = int((80 + self.flash * 120) * s)
            pygame.draw.circle(flash_surf, (*col, alpha), (cx, cy), r)
            surface.blit(flash_surf, (0, 0))

        # Barres equalizer style Winamp (bas de l'écran)
        bar_area_height = int(H * 0.22)
        bar_baseline = H - 4
        total_bar_width = W - 20
        bar_w = max(2, total_bar_width // self.num_bars)
        bar_gap = 1
        x_start = (W - self.num_bars * bar_w) // 2

        for i in range(self.num_bars):
            bh = int(self.bar_heights[i])
            bh = min(bh, bar_area_height)
            if bh < 2:
                continue

            x = x_start + i * bar_w
            # Couleur dégradée : vert → jaune → rouge selon hauteur
            t = bh / bar_area_height
            if t < 0.6:
                # Vert → Jaune
                r = int(255 * (t / 0.6))
                g = 255
                b = 0
            else:
                # Jaune → Rouge
                ratio = (t - 0.6) / 0.4
                r = 255
                g = int(255 * (1 - ratio))
                b = 0

            bar_color = (r, g, b)
            # Barre principale
            pygame.draw.rect(surface, bar_color,
                             (x, bar_baseline - bh, bar_w - bar_gap, bh))

            # Ligne de pic flottant (cyan néon)
            ph = int(self.peak_hold[i])
            ph = min(ph, bar_area_height)
            if ph > 4:
                py = bar_baseline - ph
                pygame.draw.rect(surface, (0, 240, 255),
                                 (x, py, bar_w - bar_gap, 2))

        # Ligne de base néon
        base_col = self.colors[int(self.time * 2) % len(self.colors)]
        pygame.draw.line(surface, base_col, (10, bar_baseline), (W - 10, bar_baseline), 1)

    def render_to_array(self):
        """Rendu NumPy via OpenCV pour l'export vidéo."""
        import cv2

        W, H = self.width, self.height
        s = H / 450.0  # Facteur d'échelle (base = preview 450px)

        if self._frame is None or self._frame.shape != (H, W, 3):
            self._frame = np.zeros((H, W, 3), dtype=np.uint8)

        frame = self._frame
        frame[:] = [8, 6, 12]  # Fond sombre

        cx, cy = W // 2, int(H * 0.40)

        # Grille synthwave
        step_x = max(20, W // 40)
        step_y = max(20, H // 22)
        grid_col = (18, 15, 28)
        for x in range(0, W, step_x):
            cv2.line(frame, (x, 0), (x, H), grid_col, 1)
        for y in range(0, H, step_y):
            cv2.line(frame, (0, y), (W, y), grid_col, 1)

        # Rayons étoilés pulsants
        num_beams = 12
        for i in range(num_beams):
            angle = self.rotation + i * (2 * math.pi / num_beams)
            base_len = (60 + self.pulse * 80) * s
            length = base_len + math.sin(self.sweep + i * 0.7) * 20 * s
            x1 = int(cx + math.cos(angle) * 25 * s)
            y1 = int(cy + math.sin(angle) * 25 * s)
            x2 = int(cx + math.cos(angle) * length)
            y2 = int(cy + math.sin(angle) * length)
            col = self.colors[(i + int(self.time * 2)) % len(self.colors)]
            cv2.line(frame, (x1, y1), (x2, y2), col, max(1, int(2 * s)))

        # Oscilloscope circulaire (3 anneaux réactifs aux fréquences)
        if self.freq_bands and len(self.freq_bands) >= 4:
            num_pts = 80
            for ring_idx in range(3):
                base_r = (40 + ring_idx * 22 + self.pulse * 18) * s
                pts = []
                for p in range(num_pts):
                    angle = p * (2 * math.pi / num_pts) - self.rotation * (0.8 + ring_idx * 0.15)
                    band_i = min(int(p * len(self.freq_bands) / num_pts), len(self.freq_bands) - 1)
                    val = float(self.freq_bands[band_i])
                    r = base_r + val * 55 * s
                    px = int(cx + math.cos(angle) * r)
                    py = int(cy + math.sin(angle) * r)
                    pts.append([px, py])

                if len(pts) >= 3:
                    col = self.colors[(ring_idx + int(self.time)) % len(self.colors)]
                    pts_arr = np.array(pts, dtype=np.int32)
                    overlay = frame.copy()
                    cv2.fillPoly(overlay, [pts_arr], col)
                    frame[:] = cv2.addWeighted(overlay, 0.15, frame, 0.85, 0)
                    cv2.polylines(frame, [pts_arr], True, col, max(1, int(2 * s)))

        # Flash de beat (halo lumineux)
        if self.flash > 0.1:
            col = self.colors[int(self.time * 3) % len(self.colors)]
            alpha = min(1.0, self.flash * 0.25)
            r = int((80 + self.flash * 120) * s)
            overlay = frame.copy()
            cv2.circle(overlay, (cx, cy), r, col, -1)
            frame[:] = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

        # Barres equalizer style Winamp
        bar_area_height = int(H * 0.22)
        bar_baseline = H - 4
        bar_w = max(2, (W - 20) // self.num_bars)
        x_start = (W - self.num_bars * bar_w) // 2

        for i in range(self.num_bars):
            bh = int(self.bar_heights[i])
            bh = min(bh, bar_area_height)
            if bh < 2:
                continue

            x = x_start + i * bar_w
            t = bh / max(1, bar_area_height)
            if t < 0.6:
                rc = int(255 * (t / 0.6))
                gc = 255
                bc = 0
            else:
                ratio = (t - 0.6) / 0.4
                rc = 255
                gc = int(255 * (1 - ratio))
                bc = 0

            x_end = min(W, x + bar_w - 1)
            y_top = max(0, bar_baseline - bh)
            if x_end > x and y_top < H:
                frame[y_top:bar_baseline, x:x_end] = [rc, gc, bc]

            # Peak flottant
            ph = int(self.peak_hold[i])
            ph = min(ph, bar_area_height)
            if ph > 4:
                py = max(0, min(H - 2, bar_baseline - ph))
                frame[py:py + 2, x:x_end] = [0, 240, 255]

        # Ligne de base néon
        base_col = self.colors[int(self.time * 2) % len(self.colors)]
        cv2.line(frame, (10, bar_baseline), (W - 10, bar_baseline), base_col, 1)

        return frame
