"""
Professional trance visualizer.

Layer stack:
- optional background image with beat-synced exposure and chromatic drift
- refracted tempo lattice and rotating spectral bloom
- orbital glyph field and interference threads
- additive glow, beat strobe, vignette and subtle scanlines
"""

import math

import numpy as np

from effects.base import BaseEffect

HAS_PYGAME = False
try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    pass


class TranceScopeEffect(BaseEffect):
    """Modern psychedelic trance field built around BPM phase and spectral flux."""

    def __init__(self, width, height, color_palette='psychedelic', background_image=None):
        super().__init__(width, height, color_palette, background_image=background_image)
        self.num_orbits = 144
        self.num_radial = 160
        self.orbit_values = np.zeros(self.num_orbits, dtype=np.float32)
        self.target_orbits = np.zeros(self.num_orbits, dtype=np.float32)
        self.orbit_memory = np.zeros(self.num_orbits, dtype=np.float32)
        self.radial_values = np.zeros(self.num_radial, dtype=np.float32)
        self.target_radial = np.zeros(self.num_radial, dtype=np.float32)

        self.energy = 0.0
        self.bass = 0.0
        self.mids = 0.0
        self.treble = 0.0
        self.beat_strength = 0.0
        self.beat_phase = 0.0
        self.bpm = 120.0
        self.onset = 0.0
        self.rotation = 0.0
        self.flash = 0.0
        self._frame = None
        self._vignette = None
        self._scanlines = None
        self._grid_cache = None

    def update(self, audio_data, delta_time):
        super().update(audio_data, delta_time)

        if not audio_data:
            self.orbit_values *= 0.86
            self.orbit_memory *= 0.90
            self.radial_values *= 0.88
            self.flash *= 0.78
            return

        self.energy = float(audio_data.get('energy', audio_data.get('volume', 0.0)))
        self.bass = float(audio_data.get('bass', 0.0))
        self.mids = float(audio_data.get('mids', 0.0))
        self.treble = float(audio_data.get('treble', 0.0))
        self.beat_strength = float(audio_data.get('beat_strength', 0.0))
        self.beat_phase = float(audio_data.get('beat_phase', 0.0))
        self.bpm = float(audio_data.get('bpm', 120.0))
        self.onset = float(audio_data.get('onset_strength', audio_data.get('spectral_flux', 0.0)))

        if audio_data.get('beat', False):
            self.flash = max(self.flash, 1.0)
        else:
            self.flash = max(self.flash * 0.84, self.onset * 0.35)

        tempo = max(self.bpm, 40.0) / 120.0
        self.rotation += delta_time * (0.18 + tempo * 0.24 + self.beat_strength * 0.9)

        bands = audio_data.get('visual_bands') or audio_data.get('frequency_bands') or []
        spectrum = audio_data.get('spectrum') or []
        source = bands if bands else spectrum
        source_len = len(source)

        if source_len:
            for i in range(self.num_orbits):
                pos = (i / max(self.num_orbits - 1, 1)) ** 1.35
                idx = min(int(pos * (source_len - 1)), source_len - 1)
                val = float(source[idx])
                low_bias = 1.0 + (1.0 - i / self.num_orbits) * 0.45
                interference = 0.07 * math.sin(self.time * 5.0 + i * 0.37)
                self.target_orbits[i] = min(1.0, max(0.0, val * low_bias + self.onset * 0.16 + interference))

            for i in range(self.num_radial):
                pos = abs(math.sin(i / self.num_radial * math.pi))
                idx = min(int((pos ** 1.7) * (source_len - 1)), source_len - 1)
                shimmer = 0.08 * math.sin(self.time * 7.0 + i * 0.23)
                self.target_radial[i] = min(1.0, max(0.0, float(source[idx]) + shimmer))

        attack = 0.44 if self.beat_strength > 0.4 else 0.26
        self.orbit_values = self.orbit_values * (1.0 - attack) + self.target_orbits * attack
        self.radial_values = self.radial_values * 0.70 + self.target_radial * 0.30
        self.orbit_memory = np.maximum(self.orbit_memory * (1.0 - delta_time * 1.10), self.orbit_values)

    def render(self, surface):
        """Render to a pygame surface for the fullscreen fallback."""
        if not HAS_PYGAME or surface is None:
            return
        frame = self.render_to_array()
        try:
            surf = pygame.surfarray.make_surface(np.swapaxes(frame, 0, 1))
            surface.blit(surf, (0, 0))
        except Exception:
            surface.fill((4, 3, 8))

    def render_to_array(self):
        """Render the RGB frame used by preview and MP4 export."""
        try:
            import cv2
            return self._render_cv2(cv2)
        except ImportError:
            return self._render_numpy()

    def _render_cv2(self, cv2):
        W, H = self.width, self.height
        s = H / 450.0
        frame = self._background_frame(base_color=(3, 4, 10), opacity=0.68)
        if frame is None:
            frame = np.zeros((H, W, 3), dtype=np.uint8)
            frame[:] = (3, 4, 10)

        frame[:] = self._grade_background(frame)

        if self._grid_cache is None or self._grid_cache.shape != frame.shape:
            self._grid_cache = self._make_grid(cv2, W, H)
        cv2.addWeighted(self._grid_cache, 0.30 + self.energy * 0.15, frame, 1.0, 0, dst=frame)

        cx, cy = W // 2, int(H * 0.46)
        base_radius = min(W, H) * (0.155 + self.bass * 0.045)
        phase = self._tempo_phase()

        glow = np.zeros_like(frame)
        self._draw_interference_threads(cv2, glow, cx, cy, base_radius, s, phase)
        self._draw_spectral_bloom(cv2, glow, cx, cy, base_radius, s, phase)
        self._draw_orbital_glyphs(cv2, glow, cx, cy, base_radius, s, phase)
        cv2.addWeighted(glow, 0.88, frame, 1.0, 0, dst=frame)

        self._draw_center_lens(cv2, frame, cx, cy, base_radius, s, phase)
        self._apply_flash(cv2, frame, cx, cy, s)

        if self._vignette is None or self._vignette.shape != (H, W, 3):
            self._vignette = self._make_vignette(W, H)
        frame[:] = np.clip(frame.astype(np.float32) * self._vignette, 0, 255).astype(np.uint8)

        if self._scanlines is None or self._scanlines.shape != (H, W, 3):
            self._scanlines = self._make_scanlines(W, H)
        frame[:] = np.clip(frame.astype(np.float32) * self._scanlines, 0, 255).astype(np.uint8)
        return frame

    def _render_numpy(self):
        H, W = self.height, self.width
        frame = self._background_frame(base_color=(3, 4, 10), opacity=0.68)
        if frame is None:
            frame = np.zeros((H, W, 3), dtype=np.uint8)
            frame[:] = (3, 4, 10)

        frame[:] = self._grade_background(frame)
        frame = self._draw_grid_numpy(frame)
        cx, cy = W // 2, int(H * 0.46)
        max_r = min(W, H) * 0.42

        for i, value in enumerate(self.orbit_values):
            angle = self.rotation + i * 0.19
            radius = max_r * (0.18 + 0.78 * i / max(self.num_orbits - 1, 1)) + value * 20
            x = int(cx + math.cos(angle) * radius)
            y = int(cy + math.sin(angle * 1.7) * radius * 0.72)
            if 0 <= x < W and 0 <= y < H:
                color = self._palette_color(i / self.num_orbits)
                frame[max(0, y - 1):min(H, y + 2), max(0, x - 1):min(W, x + 2)] = color

        # Vignette
        Y, X = np.ogrid[:H, :W]
        dx = (X - cx) / (W * 0.60)
        dy = (Y - cy) / (H * 0.64)
        d = np.sqrt(dx * dx + dy * dy)
        vignette = np.clip(1.08 - d * 0.52, 0.42, 1.0)
        frame = (frame.astype(np.float32) * vignette[:, :, None]).clip(0, 255).astype(np.uint8)

        # Scanlines
        frame[1::3, :, :] = (frame[1::3, :, :].astype(np.float32) * 0.955).clip(0, 255).astype(np.uint8)
        return frame

    def _draw_grid_numpy(self, frame):
        H, W = frame.shape[:2]
        cx, cy = W // 2, int(H * 0.46)
        color = np.array([16, 24, 36], dtype=np.uint8)
        for r in np.linspace(min(W, H) * 0.12, max(W, H) * 0.74, 8):
            rr = int(r)
            Y, X = np.ogrid[:H, :W]
            mask = np.abs(np.sqrt((X - cx) ** 2 + (Y - cy) ** 2) - rr) < 1.5
            frame[mask] = color
        for i in range(24):
            a = i * 2 * math.pi / 24
            dx = math.cos(a)
            dy = math.sin(a)
            steps = max(H, W)
            for t in np.linspace(0, steps, steps):
                x = int(cx + dx * t)
                y = int(cy + dy * t)
                if 0 <= x < W and 0 <= y < H:
                    frame[y, x] = color
        return frame

    def _grade_background(self, frame):
        W, H = self.width, self.height
        graded = frame.astype(np.float32)
        lift = 0.28 + self.energy * 0.12
        graded *= lift
        tint_a = np.array(self._palette_color(self.beat_phase), dtype=np.float32)
        tint_b = np.array(self._palette_color(0.35 + self.time * 0.03), dtype=np.float32)
        y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        tint = tint_a * (1 - y) + tint_b * y
        graded = graded * 0.70 + tint * (0.10 + self.energy * 0.10)

        if self.background_image is not None:
            shift = int(math.sin(self.time * 0.9) * (2 + self.beat_strength * 8))
            graded[:, :, 0] = np.roll(graded[:, :, 0], shift, axis=1)
            graded[:, :, 2] = np.roll(graded[:, :, 2], -shift, axis=0)
        return np.clip(graded, 0, 255).astype(np.uint8)

    def _draw_interference_threads(self, cv2, layer, cx, cy, base_radius, s, phase):
        ribbon_a = []
        ribbon_b = []
        ribbon_c = []
        count = self.num_radial
        for i in range(count):
            value = float(self.radial_values[i])
            t = i / count
            angle = self.rotation * 0.9 + t * math.tau
            phase_wave = phase * math.tau
            amp = (42 + value * 150 + self.onset * 65) * s
            lobe = math.sin(angle * 3.0 + phase_wave) * amp
            twist = math.cos(angle * 5.0 - self.rotation * 1.8) * amp * 0.45
            radius = base_radius * (1.00 + self.bass * 0.35) + lobe
            x = cx + math.cos(angle) * radius + math.cos(angle * 2.0) * twist
            y = cy + math.sin(angle * 1.36) * radius * 0.78 + math.sin(angle * 2.7) * twist
            ribbon_a.append((int(x), int(y)))

            radius_b = base_radius * (1.48 + self.mids * 0.28) + math.cos(angle * 4.0 + phase_wave) * amp * 0.72
            ribbon_b.append((
                int(cx + math.cos(-angle * 1.12) * radius_b),
                int(cy + math.sin(-angle * 0.92) * radius_b * 0.82)
            ))

            radius_c = base_radius * (0.56 + self.treble * 0.24) + value * 52 * s
            ribbon_c.append((
                int(cx + math.cos(angle * 2.4 + self.rotation) * radius_c),
                int(cy + math.sin(angle * 1.8 - self.rotation) * radius_c)
            ))

        for idx, ribbon in enumerate((ribbon_a, ribbon_b, ribbon_c)):
            color = self._palette_color(0.18 + idx * 0.22 + self.time * 0.025)
            pts = np.array(ribbon, dtype=np.int32)
            cv2.polylines(layer, [pts], True, tuple(int(c * 0.30) for c in color), max(1, int((7 - idx * 1.6) * s)), cv2.LINE_AA)
            cv2.polylines(layer, [pts], True, color, max(1, int((1.4 + idx * 0.3) * s)), cv2.LINE_AA)

    def _draw_spectral_bloom(self, cv2, layer, cx, cy, base_radius, s, phase):
        lobes = 9
        for petal in range(lobes):
            color = self._palette_color(petal / lobes + self.time * 0.028)
            pts = []
            for step in range(42):
                t = step / 41.0
                spread = (t - 0.5) * 0.72
                angle = self.rotation * -0.82 + petal * math.tau / lobes + spread
                band_idx = min(int((petal / lobes) * len(self.radial_values)), len(self.radial_values) - 1)
                value = float(self.radial_values[band_idx])
                envelope = math.sin(t * math.pi)
                radius = base_radius * (0.52 + envelope * (1.45 + self.bass * 0.35))
                radius += (value * 82 + math.sin(phase * math.tau + petal) * 18) * s * envelope
                x = int(cx + math.cos(angle + math.sin(t * math.pi) * 0.28) * radius)
                y = int(cy + math.sin(angle * 1.18) * radius * (0.72 + self.mids * 0.10))
                pts.append((x, y))
            arr = np.array(pts, dtype=np.int32)
            cv2.polylines(layer, [arr], False, tuple(int(c * 0.42) for c in color), max(1, int(8 * s)), cv2.LINE_AA)
            cv2.polylines(layer, [arr], False, color, max(1, int(1.5 * s)), cv2.LINE_AA)

    def _draw_orbital_glyphs(self, cv2, layer, cx, cy, base_radius, s, phase):
        for i, value in enumerate(self.orbit_values):
            if i % 2 and value < 0.08:
                continue
            t = i / max(self.num_orbits - 1, 1)
            memory = float(self.orbit_memory[i])
            angle = self.rotation * (1.35 + t * 0.5) + t * math.tau * 4.0
            radius = base_radius * (1.10 + t * 2.15) + math.sin(phase * math.tau + i * 0.21) * 18 * s
            radius += value * 68 * s
            x = int(cx + math.cos(angle) * radius)
            y = int(cy + math.sin(angle * 0.84 + math.sin(t * math.tau)) * radius * 0.62)
            if not (-20 * s <= x <= self.width + 20 * s and -20 * s <= y <= self.height + 20 * s):
                continue
            color = self._palette_color(t + self.time * 0.035)
            size = max(1, int((1.5 + value * 7.0 + memory * 3.5 + self.beat_strength * 1.8) * s))
            angle2 = angle + math.pi * 0.5
            x2 = int(x + math.cos(angle2) * size * 2.2)
            y2 = int(y + math.sin(angle2) * size * 2.2)
            cv2.line(layer, (x, y), (x2, y2), tuple(int(c * 0.52) for c in color), max(1, int(size * 0.45)), cv2.LINE_AA)
            cv2.circle(layer, (x, y), size, color, -1, cv2.LINE_AA)

    def _draw_center_lens(self, cv2, frame, cx, cy, base_radius, s, phase):
        overlay = frame.copy()
        color = self._palette_color(0.60 + self.beat_phase * 0.4)
        radius = int(base_radius * (0.34 + self.beat_strength * 0.10))
        cv2.circle(overlay, (cx, cy), max(2, radius), color, -1, cv2.LINE_AA)
        cv2.addWeighted(overlay, 0.10 + self.energy * 0.10, frame, 0.90, 0, dst=frame)
        cv2.circle(frame, (cx, cy), max(2, radius), (245, 255, 255), max(1, int(1.4 * s)), cv2.LINE_AA)
        needle_angle = self.rotation * 1.7 + phase * 2 * math.pi
        x = int(cx + math.cos(needle_angle) * base_radius * 1.65)
        y = int(cy + math.sin(needle_angle) * base_radius * 1.65)
        cv2.line(frame, (cx, cy), (x, y), (245, 255, 255), max(1, int(1.2 * s)), cv2.LINE_AA)

    def _apply_flash(self, cv2, frame, cx, cy, s):
        if self.flash <= 0.03:
            return
        overlay = frame.copy()
        color = self._palette_color(self.time * 0.1)
        radius = int((120 + self.flash * 260) * s)
        cv2.circle(overlay, (cx, cy), radius, color, -1, cv2.LINE_AA)
        cv2.addWeighted(overlay, min(0.18, self.flash * 0.16), frame, 1.0, 0, dst=frame)

    def _make_grid(self, cv2, W, H):
        grid = np.zeros((H, W, 3), dtype=np.uint8)
        cx, cy = W // 2, int(H * 0.46)
        color = (16, 24, 36)
        for r in np.linspace(min(W, H) * 0.12, max(W, H) * 0.74, 8):
            cv2.circle(grid, (cx, cy), int(r), color, 1, cv2.LINE_AA)
        for i in range(24):
            a = i * 2 * math.pi / 24
            x = int(cx + math.cos(a) * max(W, H))
            y = int(cy + math.sin(a) * max(W, H))
            cv2.line(grid, (cx, cy), (x, y), color, 1, cv2.LINE_AA)
        return grid

    @staticmethod
    def _make_vignette(W, H):
        Y, X = np.ogrid[:H, :W]
        cx, cy = W / 2.0, H * 0.46
        dx = (X - cx) / (W * 0.60)
        dy = (Y - cy) / (H * 0.64)
        d = np.sqrt(dx * dx + dy * dy)
        v = np.clip(1.08 - d * 0.52, 0.42, 1.0)
        return np.stack([v, v, v], axis=-1).astype(np.float32)

    @staticmethod
    def _make_scanlines(W, H):
        lines = np.ones((H, W, 3), dtype=np.float32)
        lines[1::3, :, :] *= 0.955
        return lines

    def _palette_color(self, pos):
        pos = pos % 1.0
        scaled = pos * len(self.colors)
        i = int(scaled) % len(self.colors)
        j = (i + 1) % len(self.colors)
        t = scaled - int(scaled)
        a = self.colors[i]
        b = self.colors[j]
        return tuple(int(a[c] * (1 - t) + b[c] * t) for c in range(3))

    def _tempo_phase(self):
        if self.beat_phase > 0:
            return self.beat_phase
        beat_interval = 60.0 / max(self.bpm, 40.0)
        return (self.time % beat_interval) / beat_interval
