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

    def __init__(self, width, height, color_palette='psychedelic', background_image=None, background_opacity=0.68):
        super().__init__(width, height, color_palette, background_image=background_image, background_opacity=background_opacity)
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
        # A solid background does not need the temporary base frame created
        # by BaseEffect.  Reusing one uint8 buffer removes a full-frame
        # allocation and copy on every 4K frame without changing any pixel.
        if self.background_image is None:
            frame = self._grade_background(None)
        else:
            frame = self._grade_background(
                self._background_frame(base_color=(3, 4, 10))
            )

        if self._grid_cache is None or self._grid_cache.shape != frame.shape:
            self._grid_cache = self._make_grid(cv2, W, H)
        cv2.addWeighted(self._grid_cache, 0.30 + self.energy * 0.15, frame, 1.0, 0, dst=frame)

        cx, cy = W // 2, int(H * 0.46)
        base_radius = min(W, H) * (0.155 + self.bass * 0.045)
        phase = self._tempo_phase()

        if not hasattr(self, '_glow_buf') or self._glow_buf.shape != frame.shape:
            self._glow_buf = np.zeros_like(frame)
        self._glow_buf.fill(0)
        glow = self._glow_buf

        self._draw_interference_threads(cv2, glow, cx, cy, base_radius, s, phase)
        self._draw_spectral_bloom(cv2, glow, cx, cy, base_radius, s, phase)
        self._draw_orbital_glyphs(cv2, glow, cx, cy, base_radius, s, phase)
        cv2.addWeighted(glow, 0.88, frame, 1.0, 0, dst=frame)

        self._draw_center_lens(cv2, frame, cx, cy, base_radius, s, phase)
        self._apply_flash(cv2, frame, cx, cy, s)

        if not hasattr(self, '_combined_filter') or self._combined_filter.shape != (H, W, 3):
            vig = self._make_vignette(W, H)
            scan = self._make_scanlines(W, H)
            self._combined_filter = (vig * scan).astype(np.float32)
        cv2.multiply(frame, self._combined_filter, dst=frame, scale=1.0, dtype=cv2.CV_8U)
        return frame

    def _render_numpy(self):
        H, W = self.height, self.width
        frame = self._background_frame(base_color=(3, 4, 10))
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
        lift = 0.28 + self.energy * 0.12
        tint_a = np.asarray(self._palette_color(self.beat_phase), dtype=np.float32)
        tint_b = np.asarray(self._palette_color(0.35 + self.time * 0.03), dtype=np.float32)
        tint_factor = 0.10 + self.energy * 0.10

        # With a solid background, every pixel in a row has the same value.
        # Build the Hx1 gradient once and broadcast it into the output instead
        # of performing several full-frame float32 operations at 4K.  This is
        # algebraically equivalent to the general path below and does not
        # change the rendered colors.
        if self.background_image is None:
            base = np.asarray((3, 4, 10), dtype=np.float32) * lift * 0.70
            y = np.linspace(0, 1, H, dtype=np.float32)[:, None]
            rows = base + (
                tint_a[None, :] * (1.0 - y) + tint_b[None, :] * y
            ) * tint_factor
            # Every call must return freshly-owned memory: export
            # pipelines queue frames for an asynchronous FFmpeg writer
            # while rendering continues; handing back a cached buffer
            # produces torn/black flashes (see AGENTS.md ownership rule).
            graded_rows = np.clip(rows, 0, 255).astype(np.uint8)[:, None, :]
            frame_out = np.empty((H, W, 3), dtype=np.uint8)
            frame_out[:] = graded_rows
            return frame_out

        graded = frame.astype(np.float32)
        graded *= lift
        y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        tint = tint_a * (1 - y) + tint_b * y
        graded = graded * 0.70 + tint * tint_factor

        if self.background_image is not None:
            shift = int(math.sin(self.time * 0.9) * (2 + self.beat_strength * 8))
            graded[:, :, 0] = np.roll(graded[:, :, 0], shift, axis=1)
            graded[:, :, 2] = np.roll(graded[:, :, 2], -shift, axis=0)
        return np.clip(graded, 0, 255).astype(np.uint8)

    def _draw_interference_threads(self, cv2, layer, cx, cy, base_radius, s, phase):
        count = self.num_radial
        i_arr = np.arange(count, dtype=np.float32)
        t_arr = i_arr / count
        angles = self.rotation * 0.9 + t_arr * (2.0 * np.pi)
        phase_wave = phase * (2.0 * np.pi)

        vals = self.radial_values.astype(np.float32)
        amps = (42.0 + vals * 150.0 + self.onset * 65.0) * s
        lobes = np.sin(angles * 3.0 + phase_wave) * amps
        twists = np.cos(angles * 5.0 - self.rotation * 1.8) * amps * 0.45

        r_a = base_radius * (1.00 + self.bass * 0.35) + lobes
        xa = (cx + np.cos(angles) * r_a + np.cos(angles * 2.0) * twists).astype(np.int32)
        ya = (cy + np.sin(angles * 1.36) * r_a * 0.78 + np.sin(angles * 2.7) * twists).astype(np.int32)
        pts_a = np.column_stack((xa, ya))

        r_b = base_radius * (1.48 + self.mids * 0.28) + np.cos(angles * 4.0 + phase_wave) * amps * 0.72
        xb = (cx + np.cos(-angles * 1.12) * r_b).astype(np.int32)
        yb = (cy + np.sin(-angles * 0.92) * r_b * 0.82).astype(np.int32)
        pts_b = np.column_stack((xb, yb))

        r_c = base_radius * (0.56 + self.treble * 0.24) + vals * (52.0 * s)
        xc = (cx + np.cos(angles * 2.4 + self.rotation) * r_c).astype(np.int32)
        yc = (cy + np.sin(angles * 1.8 - self.rotation) * r_c).astype(np.int32)
        pts_c = np.column_stack((xc, yc))

        for idx, pts in enumerate((pts_a, pts_b, pts_c)):
            color = self._palette_color(0.18 + idx * 0.22 + self.time * 0.025)
            cv2.polylines(layer, [pts], True, tuple(int(c * 0.30) for c in color), max(1, int((7 - idx * 1.6) * s)), cv2.LINE_AA)
            cv2.polylines(layer, [pts], True, color, max(1, int((1.4 + idx * 0.3) * s)), cv2.LINE_AA)

    def _draw_spectral_bloom(self, cv2, layer, cx, cy, base_radius, s, phase):
        lobes = 9
        steps = np.linspace(0.0, 1.0, 42, dtype=np.float32)
        spreads = (steps - 0.5) * 0.72
        env = np.sin(steps * np.pi)

        for petal in range(lobes):
            color = self._palette_color(petal / lobes + self.time * 0.028)
            angles = self.rotation * -0.82 + (petal * (2.0 * np.pi) / lobes) + spreads
            band_idx = min(int((petal / lobes) * len(self.radial_values)), len(self.radial_values) - 1)
            val = float(self.radial_values[band_idx])

            r = base_radius * (0.52 + env * (1.45 + self.bass * 0.35))
            r += (val * 82.0 + math.sin(phase * 2.0 * math.pi + petal) * 18.0) * s * env

            xs = (cx + np.cos(angles + np.sin(steps * np.pi) * 0.28) * r).astype(np.int32)
            ys = (cy + np.sin(angles * 1.18) * r * (0.72 + self.mids * 0.10)).astype(np.int32)
            arr = np.column_stack((xs, ys))

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
        color = self._palette_color(0.60 + self.beat_phase * 0.4)
        radius = int(base_radius * (0.34 + self.beat_strength * 0.10))
        self._draw_alpha_circle(frame, cv2, (cx, cy), max(2, radius), color, 0.10 + self.energy * 0.10)
        cv2.circle(frame, (cx, cy), max(2, radius), (245, 255, 255), max(1, int(1.4 * s)), cv2.LINE_AA)
        needle_angle = self.rotation * 1.7 + phase * 2 * math.pi
        x = int(cx + math.cos(needle_angle) * base_radius * 1.65)
        y = int(cy + math.sin(needle_angle) * base_radius * 1.65)
        cv2.line(frame, (cx, cy), (x, y), (245, 255, 255), max(1, int(1.2 * s)), cv2.LINE_AA)

    def _apply_flash(self, cv2, frame, cx, cy, s):
        if self.flash <= 0.03:
            return
        color = self._palette_color(self.time * 0.1)
        radius = int((120 + self.flash * 260) * s)
        self._draw_additive_circle(frame, cv2, (cx, cy), radius, color, min(0.18, self.flash * 0.16))

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
