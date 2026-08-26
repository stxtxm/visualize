"""
Effet Neon Equalizer — Inspiré de Winamp AVS / Windows Media Player Geiss.

Oscilloscope circulaire géant + equalizer LED subtil fusionnés
via blending additif, dégradé de fondu et glow radial unifié.
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
    Neon Equalizer — rendu premium unifié.

    L'oscilloscope circulaire est l'élément principal, dominant et lumineux.
    L'equalizer LED se fond dans la partie basse de l'image avec un dégradé
    de transparence vertical (fondu vers le haut) et un blending additif
    qui le fusionne avec le glow de l'oscilloscope.
    """

    def __init__(self, width, height, color_palette='psychedelic'):
        super().__init__(width, height, color_palette)

        # Barres equalizer
        self.num_bars = 40
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

        # Données audio
        self.freq_bands = []
        self.bass_level = 0.0

        # Caches de vignettes/masques ; jamais le frame de sortie
        self._vignette = None
        self._fade_mask = None

    def update(self, audio_data, delta_time):
        super().update(audio_data, delta_time)

        if not audio_data:
            self.bar_heights *= 0.88
            self.peak_hold = np.maximum(0, self.peak_hold - delta_time * 55)
            self.flash *= 0.82
            self.pulse *= 0.82
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

        if freq_bands and len(freq_bands) > 2:
            self.bass_level = float(np.mean(freq_bands[:2]))
        else:
            self.bass_level = energy

        # Flash sur beats
        if beat:
            self.target_flash = 1.0
        else:
            self.target_flash = beat_strength * 0.6 + energy * 0.2
        self.flash = self.flash * 0.70 + self.target_flash * 0.30
        self.pulse = max(0, min(1, beat_strength * 0.85 + energy * 0.35))

        # Rotation
        self.rotation += delta_time * (0.35 + beat_strength * 1.5)
        self.sweep += delta_time * (0.25 + bpm / 240.0)

        # Hauteurs cibles des barres
        if freq_bands:
            n_bands = len(freq_bands)
            for i in range(self.num_bars):
                band_idx = min(int(i * n_bands / self.num_bars), n_bands - 1)
                val = float(freq_bands[band_idx])
                boost = 1.0 + (1.0 - i / self.num_bars) * 0.5
                target = val * boost
                if beat and beat_strength > 0.35:
                    target *= 1.35
                self.target_heights[i] = max(0, min(1.0, target))

                if self.target_heights[i] > self.peak_hold[i]:
                    self.peak_hold[i] = self.target_heights[i]
                    self.peak_decay[i] = 0.6
                if self.peak_decay[i] > 0:
                    self.peak_decay[i] = max(0, self.peak_decay[i] - delta_time)
                self.peak_hold[i] = max(0, self.peak_hold[i] - delta_time * 0.8)

        self.bar_heights = self.bar_heights * 0.68 + self.target_heights * 0.32

    # ─── Couleur néon (Violet -> Rose -> Cyan) ───────────
    @staticmethod
    def _led_color_neon(ratio):
        """ratio = 0..1 (bas..haut). Violet -> Rose -> Cyan."""
        if ratio < 0.5:
            t = ratio / 0.5
            r = int(130 + 125 * t)
            g = 0
            b = int(250 - 70 * t)
            return (r, g, b)
        else:
            t = (ratio - 0.5) / 0.5
            r = int(255 - 255 * t)
            g = int(240 * t)
            b = int(180 + 75 * t)
            return (r, g, b)

    # ─── RENDU PYGAME (preview GUI) ─────────────────────────────────
    def render(self, surface):
        if HAS_PYGAME and surface is not None:
            self._render_pygame(surface)

    def _render_pygame(self, surface):
        W, H = surface.get_size()
        s = H / 450.0
        surface.fill((4, 3, 8))

        # Dimensions equalizer
        bar_baseline = H - int(2 * s)
        bar_max_h = int(H * 0.22)

        # ── Grille synthwave sur tout l'écran ──
        grid_col = (10, 8, 16)
        step_x = max(24, W // 32)
        step_y = max(24, H // 18)
        for gx in range(0, W, step_x):
            pygame.draw.line(surface, grid_col, (gx, 0), (gx, H), 1)
        for gy in range(0, H, step_y):
            pygame.draw.line(surface, grid_col, (0, gy), (W, gy), 1)

        # ── Oscilloscope circulaire (centre de l'écran, dominant) ──
        cx = W // 2
        cy = int(H * 0.42)

        # Rayons étoilés géants
        num_beams = 16
        for i in range(num_beams):
            angle = self.rotation + i * (2 * math.pi / num_beams)
            length = (70 + self.pulse * 130 + math.sin(self.sweep + i * 0.6) * 20) * s
            x1 = int(cx + math.cos(angle) * 22 * s)
            y1 = int(cy + math.sin(angle) * 22 * s)
            x2 = int(cx + math.cos(angle) * length)
            y2 = int(cy + math.sin(angle) * length)
            col = self.colors[(i + int(self.time * 2.5)) % len(self.colors)]
            dim = tuple(max(0, c // 3) for c in col)
            pygame.draw.line(surface, dim, (int(cx + math.cos(angle) * length * 0.5),
                                            int(cy + math.sin(angle) * length * 0.5)),
                             (x2, y2), max(1, int(4 * s)))
            pygame.draw.line(surface, col, (x1, y1),
                             (int(cx + math.cos(angle) * length * 0.6),
                              int(cy + math.sin(angle) * length * 0.6)),
                             max(1, int(2 * s)))

        # 3 anneaux
        if self.freq_bands and len(self.freq_bands) >= 3:
            for ring_idx in range(3):
                base_r = (45 + ring_idx * 32 + self.pulse * 25) * s
                num_pts = 100
                pts = []
                for p in range(num_pts):
                    angle = p * (2 * math.pi / num_pts) - self.rotation * (0.6 + ring_idx * 0.2)
                    band_i = min(int(p * len(self.freq_bands) / num_pts), len(self.freq_bands) - 1)
                    val = float(self.freq_bands[band_i])
                    r = base_r + val * 60 * s
                    pts.append((int(cx + math.cos(angle) * r),
                                int(cy + math.sin(angle) * r)))

                if len(pts) >= 3:
                    col = self.colors[(ring_idx + int(self.time * 1.5)) % len(self.colors)]
                    dim = tuple(max(0, c // 4) for c in col)
                    try:
                        alpha_surf = pygame.Surface((W, H), pygame.SRCALPHA)
                        pygame.draw.polygon(alpha_surf, (*col, 22 + ring_idx * 8), pts)
                        surface.blit(alpha_surf, (0, 0))
                    except Exception:
                        pass
                    pygame.draw.polygon(surface, dim, pts, max(1, int(6 * s)))
                    pygame.draw.polygon(surface, col, pts, max(1, int(2.5 * s)))

        # Flash de beat (halo géant couvrant tout l'écran, fusionnant les deux zones)
        if self.flash > 0.05:
            try:
                flash_surf = pygame.Surface((W, H), pygame.SRCALPHA)
                col = self.colors[int(self.time * 3) % len(self.colors)]
                alpha = int(min(100, self.flash * 100))
                radius = int((100 + self.flash * 180) * s)
                pygame.draw.circle(flash_surf, (*col, alpha), (cx, cy), radius)
                surface.blit(flash_surf, (0, 0))
            except Exception:
                pass

        # ── Equalizer LED fusionné via blending additif ──
        # On dessine les barres sur une surface séparée avec un dégradé de fondu
        # vertical (opaque en bas, transparent en haut) pour une intégration douce.
        eq_surf = pygame.Surface((W, H), pygame.SRCALPHA)

        bar_w = W / self.num_bars
        bar_gap = max(1, int(bar_w * 0.20))
        bar_draw_w = max(2, int(bar_w - bar_gap))

        block_h = max(2, int(3 * s))
        block_gap = max(1, int(1.5 * s))
        block_total = block_h + block_gap
        max_blocks = max(1, bar_max_h // block_total)

        for i in range(self.num_bars):
            bh = float(self.bar_heights[i])
            num_blocks = int(min(1.0, bh) * max_blocks)
            if num_blocks < 1:
                continue

            x = int(i * bar_w + bar_gap * 0.5)

            for b in range(num_blocks):
                by = bar_baseline - (b + 1) * block_total
                ratio = b / max_blocks
                col = self._led_color_neon(ratio)

                # Fondu vertical : les blocs du bas sont opaques, ceux du haut s'estompent
                # ratio=0 (bas) -> opacité max, ratio=1 (haut) -> opacité faible
                fade = 1.0 - ratio * 0.7  # 1.0 en bas → 0.3 en haut
                core_alpha = int(160 * fade)
                glow_alpha = int(50 * fade)

                # Glow diffus
                pygame.draw.rect(eq_surf, (*col, glow_alpha),
                                 (x - 2, by - 1, bar_draw_w + 4, block_h + 2))
                # Noyau LED
                pygame.draw.rect(eq_surf, (*col, core_alpha),
                                 (x, by, bar_draw_w, block_h))

            # Peak flottant (très subtil)
            ph = float(self.peak_hold[i])
            peak_blocks = int(min(1.0, ph) * max_blocks)
            if peak_blocks > 1:
                peak_y = bar_baseline - (peak_blocks + 1) * block_total
                fade_p = 1.0 - (peak_blocks / max_blocks) * 0.7
                pygame.draw.rect(eq_surf, (0, 255, 255, int(35 * fade_p)),
                                 (x - 2, peak_y - 1, bar_draw_w + 4, block_h + 2))
                pygame.draw.rect(eq_surf, (0, 255, 255, int(120 * fade_p)),
                                 (x, peak_y, bar_draw_w, block_h))

        # Blit de l'equalizer fusionné
        surface.blit(eq_surf, (0, 0))

        # ── Vignette radiale sombre pour unifier la composition ──
        try:
            vig_surf = pygame.Surface((W, H), pygame.SRCALPHA)
            # Coins assombris pour donner de la profondeur
            for corner_x, corner_y in [(0, 0), (W, 0), (0, H), (W, H)]:
                pygame.draw.circle(vig_surf, (0, 0, 0, 35), (corner_x, corner_y), int(max(W, H) * 0.6))
            surface.blit(vig_surf, (0, 0))
        except Exception:
            pass

    # ─── RENDU NUMPY (export vidéo via cv2) ─────────────────────────
    def render_to_array(self):
        """Rendu NumPy + OpenCV pour l'export haute qualité."""
        try:
            import cv2
            return self._render_cv2(cv2)
        except ImportError:
            return self._render_numpy_fallback()

    def _render_cv2(self, cv2):
        W, H = self.width, self.height
        s = H / 450.0

        # Every render must own fresh memory: cached buffers corrupt
        # asynchronous exports (torn/black flashes). See AGENTS.md.
        frame = np.zeros((H, W, 3), dtype=np.uint8)
        frame[:] = [4, 3, 8]

        # Dimensions equalizer
        bar_baseline = H - int(2 * s)
        bar_max_h = int(H * 0.22)

        cx, cy = W // 2, int(H * 0.42)

        # Grille
        grid_col = (10, 8, 16)
        step_x = max(24, W // 32)
        step_y = max(24, H // 18)
        for gx in range(0, W, step_x):
            cv2.line(frame, (gx, 0), (gx, H), grid_col, 1)
        for gy in range(0, H, step_y):
            cv2.line(frame, (0, gy), (W, gy), grid_col, 1)

        # Rayons étoilés géants
        num_beams = 16
        for i in range(num_beams):
            angle = self.rotation + i * (2 * math.pi / num_beams)
            length = (70 + self.pulse * 130 + math.sin(self.sweep + i * 0.6) * 20) * s
            x1 = int(cx + math.cos(angle) * 22 * s)
            y1 = int(cy + math.sin(angle) * 22 * s)
            x2 = int(cx + math.cos(angle) * length)
            y2 = int(cy + math.sin(angle) * length)
            col = self.colors[(i + int(self.time * 2.5)) % len(self.colors)]
            # Glow dim (épaisse)
            dim = tuple(max(0, c // 3) for c in col)
            cv2.line(frame,
                     (int(cx + math.cos(angle) * length * 0.5), int(cy + math.sin(angle) * length * 0.5)),
                     (x2, y2), dim, max(1, int(4 * s)), cv2.LINE_AA)
            # Core (fine)
            cv2.line(frame, (x1, y1), (x2, y2), col, max(1, int(2 * s)), cv2.LINE_AA)

        # Oscilloscope circulaire (3 anneaux géants)
        if self.freq_bands and len(self.freq_bands) >= 3:
            p_indices = np.linspace(0, 2 * np.pi, 100, endpoint=False, dtype=np.float32)
            band_indices = np.clip((np.linspace(0, len(self.freq_bands) - 1, 100)).astype(int), 0, len(self.freq_bands) - 1)
            freq_arr = np.array(self.freq_bands, dtype=np.float32)
            vals = freq_arr[band_indices]

            for ring_idx in range(3):
                base_r = (45 + ring_idx * 32 + self.pulse * 25) * s
                angles = p_indices - self.rotation * (0.6 + ring_idx * 0.2)
                r = base_r + vals * (60.0 * s)
                xs = (cx + np.cos(angles) * r).astype(np.int32)
                ys = (cy + np.sin(angles) * r).astype(np.int32)
                pts_arr = np.column_stack((xs, ys))

                col = self.colors[(ring_idx + int(self.time * 1.5)) % len(self.colors)]
                alpha = 0.08 + ring_idx * 0.04
                self._draw_alpha_poly(frame, cv2, pts_arr, col, alpha)
                # Glow externe épais
                dim = tuple(max(0, c // 3) for c in col)
                cv2.polylines(frame, [pts_arr], True, dim, max(1, int(6 * s)), cv2.LINE_AA)
                # Core mince lumineux
                cv2.polylines(frame, [pts_arr], True, col, max(1, int(2 * s)), cv2.LINE_AA)

        # Flash de beat (halo géant couvrant tout)
        if self.flash > 0.05:
            col = self.colors[int(self.time * 3) % len(self.colors)]
            alpha = min(0.25, self.flash * 0.25)
            radius = int((100 + self.flash * 180) * s)
            self._draw_alpha_circle(frame, cv2, (cx, cy), radius, col, alpha)

        # ── Equalizer LED fusionné via blending additif avec fondu vertical ──
        eq_layer = np.zeros_like(frame)

        bar_w = W / self.num_bars
        bar_gap = max(1, int(bar_w * 0.20))
        bar_draw_w = max(2, int(bar_w - bar_gap))

        block_h = max(2, int(3 * s))
        block_gap = max(1, int(1.5 * s))
        block_total = block_h + block_gap
        max_blocks = max(1, bar_max_h // block_total)

        for i in range(self.num_bars):
            bh = float(self.bar_heights[i])
            num_blocks = int(min(1.0, bh) * max_blocks)
            if num_blocks < 1:
                continue

            x = int(i * bar_w + bar_gap * 0.5)
            x_end = min(W, x + bar_draw_w)

            for b in range(num_blocks):
                by = bar_baseline - (b + 1) * block_total
                ratio = b / max_blocks
                col = self._led_color_neon(ratio)

                # Fondu vertical : opaque en bas, transparent en haut
                fade = 1.0 - ratio * 0.7

                by_end = min(H, by + block_h)
                if by >= 0 and by_end > by and x_end > x:
                    # Intensité du LED selon le fondu
                    led = tuple(int(c * fade) for c in col)
                    eq_layer[by:by_end, x:x_end] = led

                    # Glow étendu (plus large, plus faible)
                    gx1 = max(0, x - 2)
                    gx2 = min(W, x_end + 2)
                    gy1 = max(0, by - 1)
                    gy2 = min(H, by_end + 1)
                    glow_col = tuple(int(c * fade * 0.4) for c in col)
                    # Additive : on prend le max entre l'existant et le glow
                    eq_layer[gy1:gy2, gx1:gx2] = np.maximum(
                        eq_layer[gy1:gy2, gx1:gx2], glow_col)

            # Peak flottant subtil
            ph = float(self.peak_hold[i])
            peak_blocks = int(min(1.0, ph) * max_blocks)
            if peak_blocks > 1:
                peak_y = bar_baseline - (peak_blocks + 1) * block_total
                fade_p = 1.0 - (peak_blocks / max_blocks) * 0.7
                by_end = min(H, peak_y + block_h)
                if peak_y >= 0 and by_end > peak_y and x_end > x:
                    peak_intensity = int(200 * fade_p)
                    eq_layer[peak_y:by_end, x:x_end] = (0, peak_intensity, peak_intensity)

        # Blending additif de l'equalizer (les barres s'ajoutent à la lumière existante)
        # Utiliser addWeighted avec 0.5 pour que les barres ne masquent pas le fond
        cv2.addWeighted(eq_layer, 0.55, frame, 1.0, 0, dst=frame)

        # ── Vignette radiale douce pour unifier ──
        if self._vignette is None or self._vignette.shape[:2] != (H, W):
            self._vignette = self._make_vignette(W, H)
        # Appliquer la vignette (assombrit les bords)
        cv2.multiply(frame, self._vignette, dst=frame, scale=1.0, dtype=cv2.CV_8U)

        return frame

    @staticmethod
    def _make_vignette(W, H):
        """Crée un masque de vignette radiale (1.0 au centre, ~0.7 aux bords)."""
        Y, X = np.ogrid[:H, :W]
        cx, cy = W / 2, H * 0.42
        # Distance normalisée
        dx = (X - cx) / (W * 0.6)
        dy = (Y - cy) / (H * 0.6)
        d = np.sqrt(dx * dx + dy * dy)
        # Vignette douce : 1.0 au centre → 0.65 aux extrêmes
        v = np.clip(1.0 - d * 0.35, 0.65, 1.0)
        return np.stack([v, v, v], axis=-1).astype(np.float32)

    def _render_numpy_fallback(self):
        """Fallback pur NumPy si cv2 non disponible."""
        W, H = self.width, self.height
        # Every render must own fresh memory: cached buffers corrupt
        # asynchronous exports (torn/black flashes). See AGENTS.md.
        frame = np.zeros((H, W, 3), dtype=np.uint8)
        frame[:] = [4, 3, 8]

        bar_baseline = H - 6
        bar_max_h = int(H * 0.22)
        bar_w = W / self.num_bars
        bar_gap = max(1, int(bar_w * 0.20))
        bar_draw_w = max(2, int(bar_w - bar_gap))

        block_h = 3
        block_gap_v = 2
        block_total = block_h + block_gap_v
        max_blocks = max(1, bar_max_h // block_total)

        for i in range(self.num_bars):
            bh = float(self.bar_heights[i])
            num_blocks = int(min(1.0, bh) * max_blocks)
            if num_blocks < 1:
                continue
            x = int(i * bar_w + bar_gap * 0.5)
            x_end = min(W, x + bar_draw_w)
            for b in range(num_blocks):
                by = bar_baseline - (b + 1) * block_total
                by_end = min(H, by + block_h)
                if by >= 0 and by_end > by and x_end > x:
                    ratio = b / max_blocks
                    fade = 1.0 - ratio * 0.7
                    col = self._led_color_neon(ratio)
                    led = tuple(int(c * fade) for c in col)
                    frame[by:by_end, x:x_end] = led

            ph = float(self.peak_hold[i])
            peak_blocks = int(min(1.0, ph) * max_blocks)
            if peak_blocks > 1:
                peak_y = max(0, bar_baseline - (peak_blocks + 1) * block_total)
                by_end = min(H, peak_y + block_h)
                fade_p = 1.0 - (peak_blocks / max_blocks) * 0.7
                if peak_y >= 0 and x_end > x:
                    frame[peak_y:by_end, x:x_end] = (0, int(200 * fade_p), int(200 * fade_p))

        return frame
