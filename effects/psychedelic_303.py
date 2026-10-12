"""Psychedelic 303 — a bold, acid-house flyer brought to life.

The visual language is built around the classic yellow smiley, black ink,
checkerboard print, a rotating 303 record and a small set of fluorescent
registration colours. Motion follows the beat while the composition stays
clear enough to read at preview size.
"""

import math
import random

import numpy as np

from effects.base import BaseEffect

HAS_PYGAME = False
try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    pass


# Acid core in RGB (frames are RGB arrays; cv2 writes per-channel values,
# so RGB tuples render as intended).
ACID_CORE = (
    (255, 226, 0),    # acid yellow
    (196, 255, 0),    # fluorescent lime
    (57, 255, 20),    # neon green
    (255, 110, 0),    # orange
    (255, 35, 125),   # hot pink registration ink
)

SMILEY_YELLOW = (255, 232, 0)
SMILEY_DARK = (16, 8, 18)
SMILEY_YELLOW_HI = (255, 251, 165)
SMILEY_YELLOW_LO = (255, 190, 0)
SMILEY_WHITE = (255, 255, 245)
SMILEY_ORANGE = (255, 120, 20)
SMILEY_PINK = (255, 62, 132)


class Psychedelic303Effect(BaseEffect):
    """Acid-house flyer composition driven by BPM phase and spectral flux."""

    def __init__(self, width, height, color_palette='psychedelic',
                 background_image=None, background_opacity=0.68):
        super().__init__(width, height, color_palette,
                         background_image=background_image,
                         background_opacity=background_opacity)
        self.num_orbits = 72
        self.num_radial = 80
        self.num_ring = 40
        self.num_smileys = 3
        self.orbit_values = np.zeros(self.num_orbits, dtype=np.float32)
        self.target_orbits = np.zeros(self.num_orbits, dtype=np.float32)
        self.orbit_memory = np.zeros(self.num_orbits, dtype=np.float32)
        self.radial_values = np.zeros(self.num_radial, dtype=np.float32)
        self.target_radial = np.zeros(self.num_radial, dtype=np.float32)
        self.ring_values = np.zeros(self.num_ring, dtype=np.float32)
        self.target_ring = np.zeros(self.num_ring, dtype=np.float32)

        # Liquid blob drift state (module-level `random` so parallel export
        # workers replayed from a common seed stay continuous at joins).
        # Three poster-like faces: one hero and two smaller side stamps.
        # Parallel export workers replay the same seeded state at segment joins.
        self._smileys = [
            {'phase': random.random() * math.tau,
             'tilt': random.uniform(-0.16, 0.16)}
            for i in range(self.num_smileys)
        ]

        self.energy = 0.0
        self.bass = 0.0
        self.mids = 0.0
        self.treble = 0.0
        self.beat_strength = 0.0
        self.beat_phase = 0.0
        self._phase_clock = 0.0
        self.bpm = 120.0
        self.onset = 0.0
        self.rotation = 0.0
        self.flash = 0.0
        self.beat_pulse = 0.0
        self._has_beat_clock = False
        self._beat_count = -1
        self._grid_cache = None
        self._glow_buf = None
        self._glow_small_buf = None
        self._glow_blur_buf = None
        self._bloom_buf = None
        self._combined_filter = None
        self._cv2_threads_configured = False
        self._face_underlay_cache = {}

    def update(self, audio_data, delta_time):
        super().update(audio_data, delta_time)

        if not audio_data:
            dt = max(0.0, min(float(delta_time), 0.25))
            self._phase_clock = (self._phase_clock + dt * max(self.bpm, 40.0) / 60.0) % 1.0
            self.orbit_values *= 0.86
            self.orbit_memory *= 0.90
            self.radial_values *= 0.88
            self.ring_values *= 0.88
            self.flash *= math.exp(-dt * 6.5)
            self.beat_pulse *= math.exp(-dt * 7.0)
            self._has_beat_clock = False
            return

        self.energy = float(audio_data.get('energy', audio_data.get('volume', 0.0)))
        self.bass = float(audio_data.get('bass', 0.0))
        self.mids = float(audio_data.get('mids', 0.0))
        self.treble = float(audio_data.get('treble', 0.0))
        self.beat_strength = float(audio_data.get('beat_strength', 0.0))
        self.beat_phase = float(audio_data.get('beat_phase', 0.0))
        self._has_beat_clock = 'beat_phase' in audio_data
        self.bpm = float(audio_data.get('bpm', 120.0))
        self.onset = float(audio_data.get('onset_strength', audio_data.get('spectral_flux', 0.0)))

        dt = max(0.0, min(float(delta_time), 0.25))
        beat_interval = 60.0 / max(self.bpm, 40.0)
        self._phase_clock = (self._phase_clock + dt / beat_interval) % 1.0
        if audio_data.get('beat', False):
            self._phase_clock = 0.0
        elif self._has_beat_clock and 0.002 < self.beat_phase < 0.985:
            # Follow the analyzer's sample clock while it is tracking a recent
            # onset; free-run smoothly if the detector's phase has gone stale.
            self._phase_clock = self.beat_phase
        self.beat_pulse *= math.exp(-dt * (5.5 + 1.5 / beat_interval))
        self.flash *= math.exp(-dt * 6.5)
        if audio_data.get('beat', False):
            self._beat_count = (self._beat_count + 1) % 4
            self.beat_pulse = max(self.beat_pulse, min(1.0, 0.58 + self.beat_strength * 0.55))
            self.flash = max(self.flash, 1.0)
        else:
            self.beat_pulse = max(self.beat_pulse, self.onset * 0.36)
            self.flash = max(self.flash, self.onset * 0.35)

        tempo = max(self.bpm, 40.0) / 120.0
        self.rotation += dt * (0.10 + tempo * 0.12 + self.beat_strength * 0.42)
        for smiley in self._smileys:
            smiley['phase'] += dt * (1.3 + self.energy * 1.7)

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

            for i in range(self.num_ring):
                # Emphasize low-mid squelch region for the 303 ring.
                pos = (i / max(self.num_ring - 1, 1)) ** 1.15
                idx = min(int(pos * (source_len - 1)), source_len - 1)
                squelch = 0.10 * math.sin(self.time * 9.0 + i * 0.52)
                self.target_ring[i] = min(1.0, max(0.0, float(source[idx]) * 1.1 + squelch))

        attack = 0.44 if self.beat_strength > 0.4 else 0.26
        self.orbit_values = self.orbit_values * (1.0 - attack) + self.target_orbits * attack
        self.radial_values = self.radial_values * 0.70 + self.target_radial * 0.30
        self.ring_values = self.ring_values * 0.65 + self.target_ring * 0.35
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
            surface.fill((6, 10, 2))

    def render_to_array(self):
        """Render the RGB frame used by preview and MP4 export."""
        try:
            import cv2
            return self._render_cv2(cv2)
        except ImportError:
            return self._render_numpy()

    def _render_cv2(self, cv2):
        if not self._cv2_threads_configured:
            # The preview/export renders frames serially here; OpenCV's large
            # automatic worker pool costs more than it saves at these sizes
            # and can oversubscribe the parallel export workers.
            cv2.setNumThreads(1)
            self._cv2_threads_configured = True
        W, H = self.width, self.height
        s = H / 450.0
        if self.background_image is None:
            frame = self._grade_background(None)
        else:
            frame = self._grade_background(
                self._background_frame(base_color=(6, 10, 2))
            )

        if self._grid_cache is None or self._grid_cache.shape != frame.shape:
            self._grid_cache = self._make_grid(cv2, W, H)
        cv2.addWeighted(self._grid_cache, 0.58 + self.energy * 0.10, frame, 1.0, 0, dst=frame)

        cx, cy = W // 2, int(H * 0.46)
        # Leave a clear central disc for the hero face and a broad 303 groove.
        base_radius = min(W, H) * (0.295 + self.bass * 0.018)
        phase = self._tempo_phase()

        if self._glow_buf is None or self._glow_buf.shape != frame.shape:
            self._glow_buf = np.zeros_like(frame)
        self._glow_buf.fill(0)
        glow = self._glow_buf

        self._draw_303_ring(cv2, glow, cx, cy, base_radius, s, phase)
        self._draw_acid_geometry(cv2, glow, cx, cy, base_radius, s, phase)
        self._draw_303_worm(cv2, glow, cx, cy, W, H, s, phase)
        self._draw_smiley_halos(cv2, glow, cx, cy, s)

        # Bloom the neon ink at quarter resolution: this gives the poster a
        # soft printed glow without blurring the smiley artwork or paying for
        # a full-resolution convolution on every frame.
        small_size = (max(1, W // 4), max(1, H // 4))
        if self._glow_small_buf is None or self._glow_small_buf.shape[:2] != (small_size[1], small_size[0]):
            self._glow_small_buf = np.empty((small_size[1], small_size[0], 3), dtype=np.uint8)
            self._glow_blur_buf = np.empty_like(self._glow_small_buf)
        if self._bloom_buf is None or self._bloom_buf.shape != frame.shape:
            self._bloom_buf = np.empty_like(frame)
        cv2.resize(glow, small_size, dst=self._glow_small_buf, interpolation=cv2.INTER_AREA)
        cv2.GaussianBlur(self._glow_small_buf, (0, 0), sigmaX=max(0.75, 1.8 * s / 4.0),
                         dst=self._glow_blur_buf)
        cv2.resize(self._glow_blur_buf, (W, H), dst=self._bloom_buf,
                   interpolation=cv2.INTER_LINEAR)
        cv2.addWeighted(frame, 1.0, self._bloom_buf, 0.46, 0, dst=frame)
        cv2.addWeighted(glow, 0.88, frame, 1.0, 0, dst=frame)

        # Crisp foreground details on top of the glow composite.
        self._draw_smileys(cv2, frame, cx, cy, s)
        self._apply_flash(cv2, frame, cx, cy, s)

        if self._combined_filter is None or self._combined_filter.shape != (H, W, 3):
            vig = self._make_vignette(W, H)
            scan = self._make_scanlines(W, H)
            self._combined_filter = (vig * scan).astype(np.float32)
        cv2.multiply(frame, self._combined_filter, dst=frame, scale=1.0, dtype=cv2.CV_8U)
        return frame

    def _render_numpy(self):
        H, W = self.height, self.width
        frame = self._background_frame(base_color=(13, 6, 19))
        if frame is None:
            frame = np.zeros((H, W, 3), dtype=np.uint8)
            frame[:] = (13, 6, 19)

        frame[:] = self._grade_background(frame)
        cx, cy = W // 2, int(H * 0.46)

        yy, xx = np.ogrid[:H, :W]
        checker_size = max(18, int(44 * H / 450.0))
        checker = (((yy // checker_size) + (xx // checker_size)) & 1) == 0
        tiles = frame[checker].astype(np.int16)
        tiles += np.asarray((11, 1, 7), dtype=np.int16)
        frame[checker] = np.clip(tiles, 0, 255).astype(np.uint8)

        distance = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        base_radius = min(W, H) * (0.295 + self.bass * 0.018)
        for i, scale in enumerate((0.76, 0.84, 0.94, 1.04)):
            radius = base_radius * scale
            ring = np.abs(distance - radius) <= max(1.0, H * 0.002)
            frame[ring] = self._acid_color(i * 0.19)

        # Keep the spectrum sequencer visible in the OpenCV-free fallback.
        base_y = int(H * 0.98)
        margin = W * 0.07
        gap = (W - margin * 2) / 16
        active_step = (max(0, self._beat_count) * 4
                       + min(3, int(self._tempo_phase() * 4.0))) % 16
        for i in range(16):
            value = float(self.ring_values[int(i * (len(self.ring_values) - 1) / 15)])
            active = i == active_step
            pulse = self.beat_pulse * (1.0 if active else 0.10)
            bar_h = max(2, int(H * (0.070 + self.mids * 0.020 + self.bass * 0.025)
                            * (0.18 + value * 0.55 + pulse * 0.68 + self.bass * 0.10)))
            x = int(margin + (i + 0.5) * gap)
            half = max(1, int(gap * 0.10))
            color = SMILEY_YELLOW if active else self._acid_color(i / 16 * 0.56)
            frame[max(0, base_y - bar_h):base_y + 1,
                  max(0, x - half):min(W, x + half + 1)] = color

        # Keep the acid-house faces recognizable even without OpenCV.
        min_dim = min(W, H)
        for idx in range(self.num_smileys):
            self._draw_smiley_numpy(frame, *self._smiley_geom(idx, cx, cy, min_dim), idx)

        Y, X = np.ogrid[:H, :W]
        dx = (X - cx) / (W * 0.60)
        dy = (Y - cy) / (H * 0.64)
        d = np.sqrt(dx * dx + dy * dy)
        vignette = np.clip(1.08 - d * 0.52, 0.42, 1.0)
        frame = (frame.astype(np.float32) * vignette[:, :, None]).clip(0, 255).astype(np.uint8)

        frame[1::3, :, :] = (frame[1::3, :, :].astype(np.float32) * 0.955).clip(0, 255).astype(np.uint8)
        return frame

    def _grade_background(self, frame):
        W, H = self.width, self.height
        lift = 0.40 + self.energy * 0.08
        tint_a = np.asarray(self._acid_color(0.0), dtype=np.float32)
        tint_b = np.asarray(self._acid_color(0.78), dtype=np.float32)
        tint_factor = 0.045 + self.energy * 0.035

        if self.background_image is None:
            base = np.asarray((13, 6, 19), dtype=np.float32) * lift
            y = np.linspace(0, 1, H, dtype=np.float32)[:, None]
            rows = base + (
                tint_a[None, :] * (1.0 - y) + tint_b[None, :] * y
            ) * tint_factor
            # Fresh memory every call: export pipelines queue frames for an
            # async FFmpeg writer (see AGENTS.md ownership rule).
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

    def _draw_303_worm(self, cv2, layer, cx, cy, W, H, s, phase):
        """A sixteen-step 303 lane that advances on the analyzer beat clock."""
        bar_count = 16
        values = self.ring_values
        margin = W * 0.07
        gap = (W - margin * 2) / bar_count
        base_y = int(H * 0.98)
        max_h = H * (0.070 + self.mids * 0.020 + self.bass * 0.025)
        active_step = (max(0, self._beat_count) * 4 + min(3, int(phase * 4.0))) % bar_count
        lane_colors = (ACID_CORE[4], ACID_CORE[0], ACID_CORE[2], ACID_CORE[0])
        cv2.line(layer, (int(margin - gap * 0.35), base_y + max(1, int(3 * s))),
                 (int(W - margin + gap * 0.35), base_y + max(1, int(3 * s))),
                 (22, 24, 13), max(1, int(2 * s)), cv2.LINE_AA)
        for i in range(bar_count):
            value = float(values[int(i * (len(values) - 1) / (bar_count - 1))])
            active = i == active_step
            pulse = self.beat_pulse * (1.0 if active else 0.10)
            height = max(3, int(max_h * (0.18 + value * 0.55
                                         + pulse * 0.68 + self.bass * 0.10)))
            x0 = int(margin + i * gap + gap * 0.28)
            x1 = int(margin + (i + 1) * gap - gap * 0.28)
            color = lane_colors[i % len(lane_colors)]
            dim_color = tuple(int(c * (0.24 + value * 0.18)) for c in color)
            cv2.rectangle(layer, (x0, base_y - height), (x1, base_y), dim_color,
                          max(1, int(7 * s)), cv2.LINE_AA)
            cv2.rectangle(layer, (x0, base_y - height), (x1, base_y), color, -1, cv2.LINE_AA)
            cv2.line(layer, (x0, base_y - height), (x1, base_y - height),
                     SMILEY_YELLOW if active else color,
                     max(1, int((1.4 + pulse * 1.6) * s)), cv2.LINE_AA)
            if active:
                cv2.circle(layer, ((x0 + x1) // 2, base_y - height - max(2, int(4 * s))),
                           max(2, int((2 + pulse * 2) * s)), SMILEY_WHITE, -1, cv2.LINE_AA)

    def _draw_303_ring(self, cv2, layer, cx, cy, base_radius, s, phase):
        """Rotating vinyl grooves with a short, spectrum driven accent arc."""
        groove_colors = (ACID_CORE[4], ACID_CORE[2], ACID_CORE[0], ACID_CORE[2])
        for i, scale in enumerate((0.76, 0.84, 0.94, 1.04)):
            color = groove_colors[i]
            cv2.circle(layer, (cx, cy), int(base_radius * scale),
                       tuple(int(c * (0.50 + i * 0.07)) for c in color),
                       max(1, int((1.0 + (i == 3) * 1.1) * s)), cv2.LINE_AA)

        sweep = (0.14 + self.energy * 0.40 + self.beat_pulse * 0.08) * math.tau
        start = phase * math.tau + self.rotation * -0.20 - sweep * 0.5
        radius = base_radius * (1.16 + self.beat_pulse * 0.025)
        for i in range(32):
            value = float(self.ring_values[int(i * (len(self.ring_values) - 1) / 31)])
            a0 = start + sweep * i / 32
            a1 = start + sweep * (i + 0.72) / 32
            r = radius + value * 18 * s + self.beat_pulse * 5 * s
            p0 = (int(cx + math.cos(a0) * r), int(cy + math.sin(a0) * r))
            p1 = (int(cx + math.cos(a1) * r), int(cy + math.sin(a1) * r))
            color = self._acid_color(0.04 + i / 32 * 0.55)
            cv2.line(layer, p0, p1, color,
                     max(1, int((1.2 + value * 3.2) * s)), cv2.LINE_AA)

    def _draw_acid_geometry(self, cv2, layer, cx, cy, base_radius, s, phase):
        """Sparse rotating sunburst inspired by acid-house flyer printing."""
        # Fluorescent spectrum corona around the record, locked to the beat.
        tick_count = self.num_orbits
        inner_ring = base_radius * 1.09
        corona_colors = (ACID_CORE[4], ACID_CORE[0], ACID_CORE[2], ACID_CORE[1])
        for i in range(tick_count):
            angle = phase * math.tau + i * math.tau / tick_count
            value = float(self.orbit_values[i])
            inner = inner_ring + value * 4.0 * s
            outer = inner + (2.0 + value * 19.0 + self.beat_pulse * 5.0) * s
            p0 = (int(cx + math.cos(angle) * inner), int(cy + math.sin(angle) * inner))
            p1 = (int(cx + math.cos(angle) * outer), int(cy + math.sin(angle) * outer))
            cv2.line(layer, p0, p1, corona_colors[i % len(corona_colors)],
                     max(1, int((0.8 + value * 1.2 + self.beat_pulse * 0.5) * s)), cv2.LINE_AA)

        count = 36
        vals = self.radial_values
        inner = base_radius * 1.18
        for i in range(count):
            angle = self.rotation * 0.28 + i * math.tau / count
            value = float(vals[int(i * (len(vals) - 1) / (count - 1))])
            kick = self.beat_pulse * (0.12 if i % 2 == 0 else 0.035)
            outer = base_radius * (1.27 + 0.20 * value + 0.06 * self.treble + kick)
            a0, a1 = angle + 0.025, angle - 0.025
            p0 = (int(cx + math.cos(a0) * inner), int(cy + math.sin(a0) * inner))
            p1 = (int(cx + math.cos(a1) * outer), int(cy + math.sin(a1) * outer))
            color = self._acid_color((i / count) * 0.72)
            cv2.line(layer, p0, p1, tuple(int(c * 0.68) for c in color),
                     max(1, int((1.0 + value * 1.2 + self.beat_pulse) * s)), cv2.LINE_AA)

    def _smiley_geom(self, idx, cx, cy, min_dim):
        """Stable flyer layout shared by the halo and face passes."""
        sm = self._smileys[idx % len(self._smileys)]
        val = float(self.orbit_values[idx % self.num_orbits])
        phase = self._tempo_phase()
        beat_angle = phase * math.tau + idx * 1.7
        bob = (math.sin(beat_angle) * (0.008 + self.beat_pulse * 0.010)
               + math.sin(sm['phase'] * 0.65) * 0.003) * min_dim
        if idx % 3 == 0:
            x, y = cx, int(cy + bob * 0.35)
            base_size = 0.190
        else:
            side = -1 if idx % 3 == 1 else 1
            x = int(cx + side * self.width * 0.255)
            y = int(cy + bob)
            base_size = 0.125
        # Uniform scaling keeps the icon circular while the kick and bass make
        # it breathe visibly in time with the track.
        scale_pulse = 1.0 + val * 0.10 + self.beat_pulse * 0.14 + self.bass * 0.07
        r = int(min_dim * base_size * scale_pulse)
        tilt = (sm['tilt'] * 0.20 + math.sin(beat_angle) * (0.018 + self.beat_pulse * 0.025)
                + math.sin(sm['phase']) * 0.008)
        return x, y, max(4, r), tilt

    def _draw_smiley_halos(self, cv2, layer, cx, cy, s):
        """A restrained two-colour print-registration halo behind each face."""
        min_dim = min(self.width, self.height)
        for idx in range(self.num_smileys):
            x, y, r, _tilt = self._smiley_geom(idx, cx, cy, min_dim)
            if not (-r <= x <= self.width + r and -r <= y <= self.height + r):
                continue
            pulse = 1.0 + self.beat_pulse * 0.11
            pink = ACID_CORE[4]
            green = ACID_CORE[2]
            cv2.circle(layer, (x - int(2 * s), y + int(1 * s)), int(r * 1.18 * pulse),
                       tuple(int(c * 0.32) for c in pink), max(1, int(2.4 * s)), cv2.LINE_AA)
            cv2.circle(layer, (x + int(2 * s), y - int(1 * s)), int(r * 1.12 * pulse),
                       tuple(int(c * 0.48) for c in green), max(1, int(1.6 * s)), cv2.LINE_AA)
            if self.beat_pulse > 0.30:
                cv2.circle(layer, (x, y), int(r * 1.30),
                           tuple(int(c * self.beat_pulse * 0.38) for c in SMILEY_YELLOW),
                           max(1, int((1.3 + self.beat_pulse) * s)), cv2.LINE_AA)

    def _draw_smiley_numpy(self, frame, x, y, r, tilt, idx):
        """Rasterize a bold, legible smiley for the no-OpenCV fallback."""
        H, W = frame.shape[:2]
        extent = int(r * 1.35) + 1
        x0, x1 = max(0, x - extent), min(W, x + extent + 1)
        y0, y1 = max(0, y - extent), min(H, y + extent + 1)
        if x1 <= x0 or y1 <= y0:
            return

        py, px = np.mgrid[y0:y1, x0:x1]
        dx, dy = px - x, py - y
        cos_t, sin_t = math.cos(tilt), math.sin(tilt)
        local_x = cos_t * dx + sin_t * dy
        local_y = -sin_t * dx + cos_t * dy
        patch = frame[y0:y1, x0:x1]

        if idx % 3 == 0:
            drip_x = -0.30 * r
            drip_end = 1.45 * r + self.bass * 0.30 * r
            drip = ((np.abs(local_x - drip_x) <= 0.065 * r)
                    & (local_y >= 0.78 * r) & (local_y <= drip_end))
            drop = (local_x - drip_x) ** 2 + (local_y - drip_end) ** 2 <= (0.09 * r) ** 2
            patch[drip | drop] = SMILEY_DARK
            inner_drip = ((np.abs(local_x - drip_x) <= 0.032 * r)
                          & (local_y >= 0.78 * r) & (local_y <= drip_end))
            inner_drop = ((local_x - drip_x) ** 2 + (local_y - drip_end) ** 2
                          <= (0.052 * r) ** 2)
            patch[inner_drip | inner_drop] = SMILEY_YELLOW

        radius_sq = local_x ** 2 + local_y ** 2
        border = max(1.0, r * 0.12)
        patch[radius_sq <= r * r] = SMILEY_DARK
        patch[radius_sq <= (r - border) ** 2] = SMILEY_YELLOW
        # Warm rim shading adds colour depth while the very centre stays a
        # pure SMILEY_YELLOW (the rasterised tests assert on the centre).
        rim = ((radius_sq > (0.72 * r) ** 2)
               & (radius_sq <= (r - border) ** 2))
        patch[rim] = SMILEY_YELLOW_LO

        for eye_i, side in enumerate((-1, 1)):
            eye_x, eye_y = side * 0.31 * r, -0.19 * r
            spiral_ink = np.zeros_like(radius_sq, dtype=bool)
            eye_width = max(0.8, 0.025 * r)
            for k in range(56):
                q = k / 55.0
                angle = eye_i * math.pi + q * 2.05 * math.tau
                spiral_r = 0.145 * r * q
                sx = eye_x + math.cos(angle) * spiral_r
                sy = eye_y + math.sin(angle) * spiral_r
                spiral_ink |= ((local_x - sx) ** 2 + (local_y - sy) ** 2 <= eye_width ** 2)
            core = ((local_x - eye_x) ** 2 + (local_y - eye_y) ** 2
                    <= max(1.0, 0.035 * r) ** 2)
            patch[(spiral_ink | core) & (radius_sq <= (r - border) ** 2)] = SMILEY_DARK

        mouth_x = local_x / (0.53 * r)
        smile_y = 0.49 * r - 0.24 * r * mouth_x ** 2
        smile = ((np.abs(local_y - smile_y) <= max(1.0, 0.055 * r))
                 & (np.abs(mouth_x) <= 1.0)
                 & (radius_sq <= (r - border) ** 2))
        patch[smile] = SMILEY_DARK

    def _draw_smileys(self, cv2, frame, cx, cy, s):
        """Draw three legible acid-house sticker faces."""
        min_dim = min(self.width, self.height)
        for idx in range(self.num_smileys):
            x, y, r, tilt = self._smiley_geom(idx, cx, cy, min_dim)
            if not (-r <= x <= self.width + r and -r <= y <= self.height + r):
                continue
            self._draw_smiley_face(cv2, frame, x, y, r, tilt, idx, s)

    def _face_underlay(self, cv2, idx):
        """Build the static screen-print plate once; animate only its features."""
        cached = self._face_underlay_cache.get(idx)
        if cached is not None:
            return cached

        min_dim = min(self.width, self.height)
        base_ratio = 0.225 if idx == 0 else 0.112
        R = max(10, int(min_dim * base_ratio))
        pad = max(5, int(R * 0.06))
        side = 2 * (R + pad) + 1
        cx = cy = side // 2
        texture = np.zeros((side, side, 4), dtype=np.uint8)
        pink, green, dark = ACID_CORE[4], ACID_CORE[2], SMILEY_DARK
        reg = max(2, int(R * 0.035))

        cv2.circle(texture, (cx - reg, cy + reg // 2), int(R * 1.045), pink + (255,), -1, cv2.LINE_AA)
        cv2.circle(texture, (cx + reg, cy - reg // 2), int(R * 1.025), green + (255,),
                   max(1, int(R * 0.022)), cv2.LINE_AA)
        face_r = R * 0.91
        cv2.circle(texture, (cx, cy), R, dark + (255,), -1, cv2.LINE_AA)
        cv2.circle(texture, (cx, cy), int(face_r), SMILEY_YELLOW_LO + (255,),
                   -1, cv2.LINE_AA)

        x0, x1 = max(0, cx - int(face_r)), min(side, cx + int(face_r) + 1)
        y0, y1 = max(0, cy - int(face_r)), min(side, cy + int(face_r) + 1)
        py, px = np.mgrid[y0:y1, x0:x1]
        nx = (px - cx).astype(np.float32) / face_r
        ny = (py - cy).astype(np.float32) / face_r
        rr = nx * nx + ny * ny
        distance = np.sqrt(rr)
        # Keep the smiley itself perfectly round. The liquid drips are drawn
        # separately after this plate, so the iconic circle remains legible.
        coverage = np.clip((1.0 - distance) * face_r + 0.5, 0.0, 1.0)[:, :, None]
        shade = np.clip(0.54 + 0.22 * nx - 0.34 * ny + 0.12 * distance, 0.0, 1.0)
        shine = np.exp(-(((nx + 0.27) / 0.56) ** 2 + ((ny + 0.43) / 0.42) ** 2))
        face_rgb = np.empty((y1 - y0, x1 - x0, 3), dtype=np.float32)
        face_rgb[:, :, 0] = 255
        face_rgb[:, :, 1] = 250 - shade * 48 + shine * 5
        face_rgb[:, :, 2] = 4 + shade * 5 + shine * 25
        face_roi = texture[y0:y1, x0:x1, :3]
        face_roi[:] = np.clip(face_rgb * coverage + face_roi.astype(np.float32) * (1.0 - coverage),
                              0, 255).astype(np.uint8)

        spacing = max(4, int(R * 0.085))
        dot_r = max(1, int(R * 0.018))
        for oy in range(int(R * 0.32), int(R * 0.88), spacing):
            for ox in range(-int(R * 0.72), int(R * 0.73), spacing):
                if abs(ox) < R * 0.39 or ox * ox + oy * oy > (face_r * 0.85) ** 2:
                    continue
                fade = max(0.0, 1.0 - abs(ox) / max(1.0, R * 0.9))
                if fade > 0.15:
                    cv2.circle(texture, (int(cx + ox), int(cy + oy)), dot_r,
                               (int(152 + 60 * fade), int(34 + 70 * fade), 2, 255),
                               -1, cv2.LINE_AA)
        self._face_underlay_cache[idx] = texture
        return texture

    def _draw_smiley_face(self, cv2, frame, x, y, r, tilt, idx, s):
        """Render a melted, spiral-eyed acid-house screen-print face."""
        R = max(7, int(r))
        dark, pink, green = SMILEY_DARK, ACID_CORE[4], ACID_CORE[2]
        reg = max(2, int(R * 0.035))
        phase = self._tempo_phase()
        beat_angle = phase * math.tau
        ct, st = math.cos(tilt), math.sin(tilt)

        def point(u, v):
            return (int(x + (ct * u - st * v) * R),
                    int(y + (st * u + ct * v) * R))

        # Uneven liquid drips extend the silhouette. Bass makes the ink stretch
        # on kick hits and relax through the remainder of the bar.
        drip_xs = (-0.48, -0.04, 0.43)
        for drip_i, u in enumerate(drip_xs):
            if idx and drip_i == 1:
                continue
            beat_lift = max(0.0, math.cos(beat_angle - drip_i * 1.8)) * self.beat_pulse
            length = (0.20 + self.bass * 0.32 + beat_lift * 0.24 + self.onset * 0.08)
            length *= 1.0 if idx == 0 else 0.80
            start_v = math.sqrt(max(0.0, 1.0 - u * u)) * 0.88
            end_v = start_v + length
            sway = math.sin(beat_angle - drip_i * 1.4) * (0.018 + self.beat_pulse * 0.035)
            drip = np.array([point(u, start_v),
                             point(u + sway * 0.3, start_v + length * 0.34),
                             point(u + sway, start_v + length * 0.72),
                             point(u + sway * 1.15, end_v)], dtype=np.int32)
            drip_w = max(3, int(R * (0.13 if idx == 0 else 0.11)))
            cv2.polylines(frame, [drip], False, dark, drip_w + 2, cv2.LINE_AA)
            cv2.polylines(frame, [drip], False, SMILEY_YELLOW, max(2, drip_w // 2), cv2.LINE_AA)
            end = tuple(drip[-1])
            cv2.circle(frame, end, max(2, drip_w // 2 + 1), dark, -1, cv2.LINE_AA)
            cv2.circle(frame, end, max(1, drip_w // 4), SMILEY_YELLOW, -1, cv2.LINE_AA)

        # The shaded halftone plate is cached and rescaled, keeping per-frame
        # work focused on the audio-reactive eyes, grin and drips.
        source = self._face_underlay(cv2, idx)
        target_side = max(16, 2 * R + 2 * max(3, int(R * 0.06)) + 1)
        if source.shape[0] == target_side:
            underlay = source
        else:
            underlay = cv2.resize(source, (target_side, target_side), interpolation=cv2.INTER_LINEAR)
        half = target_side // 2
        sx0, sx1 = max(0, half - x), min(target_side, frame.shape[1] - x + half)
        sy0, sy1 = max(0, half - y), min(target_side, frame.shape[0] - y + half)
        if sx1 > sx0 and sy1 > sy0:
            dx0, dy0 = x - half + sx0, y - half + sy0
            src = underlay[sy0:sy1, sx0:sx1]
            dst = frame[dy0:dy0 + (sy1 - sy0), dx0:dx0 + (sx1 - sx0)]
            alpha = src[:, :, 3:4].astype(np.float32) / 255.0
            dst[:] = (src[:, :, :3].astype(np.float32) * alpha
                      + dst.astype(np.float32) * (1.0 - alpha)).clip(0, 255).astype(np.uint8)

        # Black hand-drawn spirals are the defining acid smiley mark.
        eye_y = -0.19
        for eye_i, side in enumerate((-1, 1)):
            eye_r = max(4, int(R * (0.18 + self.treble * 0.020
                                    + self.beat_pulse * 0.012)))
            ex, ey = point(side * 0.30, eye_y + 0.018 * math.sin(beat_angle + eye_i))
            spiral_ink = green if eye_i == 0 else pink
            # The thin off-register color is only a print shadow; the black
            # spiral remains the dominant shape at every preview size.
            spin = beat_angle + idx * 0.72 + eye_i * math.pi
            turns = 1.60 + self.treble * 0.50
            spiral = []
            registration = []
            for k in range(56):
                q = k / 55.0
                a = spin + q * turns * math.tau
                rad = eye_r * (0.06 + 0.82 * q)
                spiral.append((int(ex + math.cos(a) * rad), int(ey + math.sin(a) * rad)))
                offset = max(1.0, R * 0.016)
                registration.append((int(ex + math.cos(a) * rad + offset),
                                     int(ey + math.sin(a) * rad - offset)))
            spiral = np.asarray(spiral, dtype=np.int32)
            registration = np.asarray(registration, dtype=np.int32)
            cv2.polylines(frame, [registration], False, spiral_ink,
                          max(1, int(R * 0.014)), cv2.LINE_AA)
            cv2.polylines(frame, [spiral], False, dark,
                          max(2, int(R * 0.025)), cv2.LINE_AA)

        # Use the plain curved black grin of the original acid smiley. A tiny
        # magenta registration offset reacts to the kick without changing the
        # expression into a cartoon mouth.
        width = 0.49
        curve = 0.13 + self.bass * 0.09 + self.beat_pulse * 0.05
        grin = []
        echo = []
        for k in range(33):
            u = -width + k * (2.0 * width / 32)
            q = u / width
            v = 0.23 + curve * (1.0 - q * q)
            grin.append(point(u, v))
            echo.append(point(u + 0.018, v + 0.018))
        grin = np.asarray(grin, dtype=np.int32)
        echo = np.asarray(echo, dtype=np.int32)
        grin_width = max(2, int(R * (0.050 + self.beat_pulse * 0.030)))
        cv2.polylines(frame, [echo], False, pink, max(1, int(R * 0.018)), cv2.LINE_AA)
        cv2.polylines(frame, [grin], False, dark, grin_width, cv2.LINE_AA)
        cv2.circle(frame, tuple(grin[0]), max(1, grin_width // 2), dark, -1, cv2.LINE_AA)
        cv2.circle(frame, tuple(grin[-1]), max(1, grin_width // 2), dark, -1, cv2.LINE_AA)

    def _apply_flash(self, cv2, frame, cx, cy, s):
        if self.flash <= 0.03:
            return
        # A short outline pulse keeps the beat accent crisp; a filled disc here
        # used to wash almost the whole frame in yellow on every kick.
        color = self._acid_color(0.42 + self._tempo_phase() * 0.25)
        radius = int(min(frame.shape[:2]) * (0.285 + self.beat_pulse * 0.035))
        self._draw_alpha_circle(frame, cv2, (cx, cy), radius, color,
                                min(0.45, self.flash * 0.34),
                                max(1, int(3.0 * s)))

    def _make_grid(self, cv2, W, H):
        # A near-black checker print is the classic flyer texture; keep its
        # contrast low so the yellow face and fluorescent ink stay dominant.
        square = max(18, int(44 * H / 450.0))
        rows = np.arange(H, dtype=np.int32)[:, None] // square
        cols = np.arange(W, dtype=np.int32)[None, :] // square
        checker = (rows + cols) & 1
        grid = np.empty((H, W, 3), dtype=np.uint8)
        grid[:] = (6, 12, 14)
        grid[checker == 0] = (28, 7, 23)
        cx, cy = W // 2, int(H * 0.46)
        for i, scale in enumerate((0.34, 0.49, 0.66)):
            cv2.circle(grid, (cx, cy), int(min(W, H) * scale),
                       (15 + i * 2, 18 + i * 2, 8), 1, cv2.LINE_AA)
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
        lines[1::3, :, :] *= 0.988
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

    @staticmethod
    def _ramp(colors, p):
        """Smooth cyclic interpolation across a colour ramp (float RGB)."""
        n = len(colors)
        scaled = (p % 1.0) * n
        i = int(scaled) % n
        j = (i + 1) % n
        t = scaled - int(scaled)
        a, b = colors[i], colors[j]
        return (a[0] + (b[0] - a[0]) * t,
                a[1] + (b[1] - a[1]) * t,
                a[2] + (b[2] - a[2]) * t)

    def _acid_color(self, pos, mix=0.88):
        """Return a saturated flyer ink, retaining a hint of the chosen palette."""
        base = self._palette_color(pos)
        acid = self._ramp(ACID_CORE, pos)
        col = tuple(base[c] * (1 - mix) + acid[c] * mix for c in range(3))
        return tuple(int(max(0, min(255, col[c]))) for c in range(3))

    def _tempo_phase(self):
        return max(0.0, min(1.0, self._phase_clock))
