"""
Effect manager module for psychedelic visualizer.
Manages the selection and instantiation of visual effects.
"""

import random
import importlib

from effects.logo_overlay import LogoOverlay


# Map effect type names to module names
EFFECT_MAP = {
    'trance_scope': ('trance_scope', 'TranceScopeEffect'),
    'pro_trance': ('trance_scope', 'TranceScopeEffect'),
    'neon_equalizer': ('classic', 'ClassicEffect'),
    'psychedelic_plasma': ('plasma', 'PlasmaEffect'),
    '3d_cyber_tunnel': ('tunnel', 'TunnelEffect'),
    'bars': ('bars', 'BarEffect'),
    'circles': ('circles', 'CircleEffect'),
    'particles': ('particles', 'ParticleEffect'),
    'tunnel': ('tunnel', 'TunnelEffect'),
    'wave': ('wave', 'WaveEffect'),
    'spectrum': ('spectrum', 'SpectrumEffect'),
    'plasma': ('plasma', 'PlasmaEffect'),
    'classic': ('classic', 'ClassicEffect'),
}

RANDOM_EFFECTS = [
    'trance_scope',
    'neon_equalizer',
    'psychedelic_plasma',
    '3d_cyber_tunnel',
]


def resolve_effect_type(effect_type):
    """Resolve ``random`` once so parallel segments share one effect."""
    if effect_type == 'random':
        return random.choice(RANDOM_EFFECTS)
    return effect_type


class EffectManager:
    """
    Manages visual effects for the audio visualizer.
    Handles effect selection, initialization, and updates.
    """

    def __init__(self, analyzer=None, renderer=None, effect_type='random',
                 color_palette='psychedelic', background_image=None,
                 background_opacity=0.72, logo_image=None,
                 logo_position='top-right', logo_x=0.5, logo_y=0.5,
                 logo_scale=0.18, logo_opacity=1.0):
        """
        Initialize the effect manager.
        
        Args:
            analyzer: Audio analyzer instance
            renderer: Renderer instance
            effect_type: Type of effect to use ('bars', 'circles', etc.)
            color_palette: Color palette to use
            background_image: Path to optional background image
            background_opacity: Blend opacity for background image (0.0-1.0)
            logo_image: Path to an optional foreground logo image
            logo_position: Preset placement or ``custom``
            logo_x/logo_y: Custom placement in normalized coordinates
            logo_scale: Logo width as a fraction of the frame width
            logo_opacity: Logo opacity (0.0-1.0)
        """
        self.analyzer = analyzer
        self.renderer = renderer
        self.effect_type = effect_type
        self.color_palette = color_palette
        self.background_image = background_image
        self.background_opacity = max(0.0, min(1.0, background_opacity))
        self.logo_image = logo_image
        self.logo_position = logo_position
        self.logo_x = max(0.0, min(1.0, float(logo_x)))
        self.logo_y = max(0.0, min(1.0, float(logo_y)))
        self.logo_scale = max(0.01, min(1.0, float(logo_scale)))
        self.logo_opacity = max(0.0, min(1.0, float(logo_opacity)))
        self.current_effect = None
        self._initialized = False
        
        # Store width and height from renderer
        self.width = renderer.width if renderer else 1920
        self.height = renderer.height if renderer else 1080
        self.logo_overlay = LogoOverlay(
            self.width, self.height,
            image_path=self.logo_image,
            position=self.logo_position,
            x=self.logo_x,
            y=self.logo_y,
            scale=self.logo_scale,
            opacity=self.logo_opacity,
        )

    def init(self):
        """Initialize the effect manager."""
        self._create_effect()
        self._initialized = True

    def _create_effect(self):
        """Create the effect instance based on current settings."""
        # Determine which effect to use
        effect_name = resolve_effect_type(self.effect_type)
        
        # Get module file and class name
        module_file, class_name = EFFECT_MAP.get(effect_name, ('classic', 'ClassicEffect'))
        
        # Import the module dynamically
        try:
            module = importlib.import_module(f'effects.{module_file}')
            effect_class = getattr(module, class_name)
        except (ImportError, AttributeError):
            from effects.classic import ClassicEffect
            effect_class = ClassicEffect
        
        # Create the effect instance
        try:
            self.current_effect = effect_class(
                width=self.width,
                height=self.height,
                color_palette=self.color_palette,
                background_image=self.background_image
            )
        except TypeError:
            self.current_effect = effect_class(
                width=self.width,
                height=self.height,
                color_palette=self.color_palette
            )
            if self.background_image and hasattr(self.current_effect, 'set_background_image'):
                self.current_effect.set_background_image(self.background_image)
        
        if hasattr(self.current_effect, 'set_background_opacity'):
            self.current_effect.set_background_opacity(self.background_opacity)
        
        self._current_effect_name = effect_name

    def change_effect(self, effect_type):
        """Change the current effect."""
        self.effect_type = effect_type
        self._create_effect()

    def change_palette(self, color_palette):
        """Change the color palette."""
        self.color_palette = color_palette
        if self.current_effect:
            self.current_effect.color_palette = color_palette
            self.current_effect.colors = self.current_effect._get_color_palette()

    def set_background_image(self, image_path):
        """Apply a background image to the active effect and future recreations."""
        self.background_image = image_path or None
        if self.current_effect and hasattr(self.current_effect, 'set_background_image'):
            self.current_effect.set_background_image(self.background_image)

    def set_background_opacity(self, opacity):
        """Set background image opacity on the active effect and future recreations."""
        opacity = max(0.0, min(1.0, opacity))
        self.background_opacity = opacity
        if self.current_effect and hasattr(self.current_effect, 'set_background_opacity'):
            self.current_effect.set_background_opacity(opacity)

    def set_logo_image(self, image_path):
        """Apply a foreground logo to preview, playback and future renders."""
        self.logo_image = image_path or None
        self.logo_overlay.set_image(self.logo_image)

    def set_logo_position(self, position):
        """Set a named logo position or ``custom``."""
        self.logo_position = position
        self.logo_overlay.set_position(position)

    def set_logo_coordinates(self, x=None, y=None):
        """Set custom logo coordinates in normalized 0.0-1.0 units."""
        if x is not None:
            self.logo_x = max(0.0, min(1.0, float(x)))
        if y is not None:
            self.logo_y = max(0.0, min(1.0, float(y)))
        self.logo_overlay.set_coordinates(x, y)

    def set_logo_scale(self, scale):
        self.logo_scale = max(0.01, min(1.0, float(scale)))
        self.logo_overlay.set_scale(self.logo_scale)

    def set_logo_opacity(self, opacity):
        self.logo_opacity = max(0.0, min(1.0, float(opacity)))
        self.logo_overlay.set_opacity(self.logo_opacity)

    def resize(self, width, height):
        """Update manager and logo dimensions when the preview is resized."""
        self.width = max(1, int(width))
        self.height = max(1, int(height))
        self.logo_overlay.set_frame_size(self.width, self.height)

    def update(self, audio_data, delta_time):
        """
        Update the current effect with audio data.
        
        Args:
            audio_data: Dictionary with audio analysis data
            delta_time: Time since last frame in seconds
        """
        if self.current_effect and audio_data:
            self.current_effect.update(audio_data, delta_time)

    def render(self, surface):
        """
        Render the current effect to a surface.
        
        Args:
            surface: Pygame surface to render to
        """
        if self.current_effect and surface:
            self.current_effect.render(surface)
            self.logo_overlay.render_pygame(surface)

    def render_to_array(self):
        """
        Render the current effect to a numpy array.
        
        Returns:
            numpy.ndarray: Rendered frame as RGB array
        """
        if self.current_effect:
            frame = self.current_effect.render_to_array()
            return self.logo_overlay.apply(frame)
        else:
            # Return a black frame
            import numpy as np
            return np.zeros((self.height, self.width, 3), dtype=np.uint8)

    def get_current_effect_name(self):
        """Get the name of the current effect."""
        return self._current_effect_name if hasattr(self, '_current_effect_name') else self.effect_type

    def cleanup(self):
        """Clean up resources."""
        self.current_effect = None
        self._initialized = False

    @property
    def is_initialized(self):
        """Check if effect manager is initialized."""
        return self._initialized
