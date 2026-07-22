"""Reusable logo overlay for array and Pygame rendering paths."""

from __future__ import annotations

import os

try:
    import numpy as np
except ImportError:  # pragma: no cover - the application already requires numpy
    np = None


LOGO_POSITIONS = (
    "top-left",
    "top-center",
    "top-right",
    "center-left",
    "center",
    "center-right",
    "bottom-left",
    "bottom-center",
    "bottom-right",
    "custom",
)

_POSITION_COORDINATES = {
    "top-left": (0.0, 0.0),
    "top-center": (0.5, 0.0),
    "top-right": (1.0, 0.0),
    "center-left": (0.0, 0.5),
    "center": (0.5, 0.5),
    "center-right": (1.0, 0.5),
    "bottom-left": (0.0, 1.0),
    "bottom-center": (0.5, 1.0),
    "bottom-right": (1.0, 1.0),
}


class LogoOverlay:
    """Load a logo once and composite it on RGB frames or Pygame surfaces.

    ``x`` and ``y`` are normalized coordinates in the available space after
    subtracting the logo dimensions: 0.0 is the left/top edge and 1.0 is the
    right/bottom edge. This makes custom placement independent of resolution.
    """

    def __init__(self, width, height, image_path=None, position="top-right",
                 x=0.5, y=0.5, scale=0.18, opacity=1.0):
        self.width = max(1, int(width))
        self.height = max(1, int(height))
        self.image_path = None
        self.image = None
        self.position = position if position in LOGO_POSITIONS else "top-right"
        self.x = self._clamp(x)
        self.y = self._clamp(y)
        self.scale = self._clamp(scale, 0.01, 1.0)
        self.opacity = self._clamp(opacity, 0.0, 1.0)
        self._scaled_cache = None
        if image_path:
            self.set_image(image_path)

    @staticmethod
    def _clamp(value, low=0.0, high=1.0):
        try:
            return max(low, min(high, float(value)))
        except (TypeError, ValueError):
            return low

    def set_frame_size(self, width, height):
        """Update the target dimensions used by subsequent overlays."""
        self.width = max(1, int(width))
        self.height = max(1, int(height))
        self._scaled_cache = None

    def set_image(self, image_path):
        """Load an image as RGBA; invalid paths disable the overlay."""
        self.image_path = image_path or None
        self.image = None
        self._scaled_cache = None
        if not self.image_path or np is None or not os.path.exists(self.image_path):
            return

        try:
            from PIL import Image
            with Image.open(self.image_path) as image:
                self.image = np.asarray(image.convert("RGBA"), dtype=np.uint8).copy()
        except Exception:
            self.image = None

    def set_position(self, position):
        if position in LOGO_POSITIONS:
            self.position = position

    def set_coordinates(self, x=None, y=None):
        if x is not None:
            self.x = self._clamp(x)
        if y is not None:
            self.y = self._clamp(y)

    def set_scale(self, scale):
        self.scale = self._clamp(scale, 0.01, 1.0)
        self._scaled_cache = None

    def set_opacity(self, opacity):
        self.opacity = self._clamp(opacity, 0.0, 1.0)

    def _scaled_image(self):
        if self.image is None:
            return None

        target_width = max(1, int(self.width * self.scale))
        source_height, source_width = self.image.shape[:2]
        target_height = max(1, int(target_width * source_height / max(source_width, 1)))

        # Keep a very tall logo from covering nearly the complete visualizer.
        max_height = max(1, int(self.height * 0.8))
        if target_height > max_height:
            target_height = max_height
            target_width = max(1, int(target_height * source_width / max(source_height, 1)))

        cache_key = (target_width, target_height, self.image.shape)
        if self._scaled_cache is None or self._scaled_cache[0] != cache_key:
            from PIL import Image
            pil_image = Image.fromarray(self.image, mode="RGBA")
            resampling = getattr(Image, "Resampling", Image).LANCZOS
            scaled = pil_image.resize((target_width, target_height), resampling)
            self._scaled_cache = (cache_key, np.asarray(scaled, dtype=np.uint8).copy())
        return self._scaled_cache[1]

    def _geometry(self):
        image = self._scaled_image()
        if image is None:
            return None

        logo_height, logo_width = image.shape[:2]
        if self.position == "custom":
            x_ratio, y_ratio = self.x, self.y
        else:
            x_ratio, y_ratio = _POSITION_COORDINATES[self.position]

        max_x = max(0, self.width - logo_width)
        max_y = max(0, self.height - logo_height)
        x = int(round(max_x * x_ratio))
        y = int(round(max_y * y_ratio))
        return image, x, y

    def apply(self, frame):
        """Composite the logo on an RGB numpy frame and return that frame."""
        geometry = self._geometry()
        if geometry is None or frame is None or np is None:
            return frame

        image, x, y = geometry
        logo_height, logo_width = image.shape[:2]
        frame_height, frame_width = frame.shape[:2]
        x2 = min(frame_width, x + logo_width)
        y2 = min(frame_height, y + logo_height)
        if x2 <= x or y2 <= y:
            return frame

        crop = image[:y2 - y, :x2 - x]
        alpha = (crop[:, :, 3].astype(np.float32) / 255.0) * self.opacity
        if not np.any(alpha):
            return frame

        roi = frame[y:y2, x:x2]
        blended = (
            crop[:, :, :3].astype(np.float32) * alpha[:, :, None]
            + roi.astype(np.float32) * (1.0 - alpha[:, :, None])
        )
        frame[y:y2, x:x2] = np.clip(blended, 0, 255).astype(np.uint8)
        return frame

    def render_pygame(self, surface):
        """Composite the same logo on a Pygame surface."""
        geometry = self._geometry()
        if geometry is None or surface is None:
            return

        try:
            import pygame
            image, x, y = geometry
            logo_surface = pygame.image.fromstring(
                image.tobytes(), (image.shape[1], image.shape[0]), "RGBA"
            )
            if self.opacity < 1.0:
                logo_surface.set_alpha(int(round(self.opacity * 255)))
            surface.blit(logo_surface, (x, y))
        except Exception:
            # A logo must never break playback when a renderer lacks Pygame.
            pass

