"""
Effect manager module for psychedelic visualizer.
Manages the selection and instantiation of visual effects.
"""

import random
import importlib


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


class EffectManager:
    """
    Manages visual effects for the audio visualizer.
    Handles effect selection, initialization, and updates.
    """

    def __init__(self, analyzer=None, renderer=None, effect_type='random',
                 color_palette='psychedelic', background_image=None):
        """
        Initialize the effect manager.
        
        Args:
            analyzer: Audio analyzer instance
            renderer: Renderer instance
            effect_type: Type of effect to use ('bars', 'circles', etc.)
            color_palette: Color palette to use
        """
        self.analyzer = analyzer
        self.renderer = renderer
        self.effect_type = effect_type
        self.color_palette = color_palette
        self.background_image = background_image
        self.current_effect = None
        self._initialized = False
        
        # Store width and height from renderer
        self.width = renderer.width if renderer else 1920
        self.height = renderer.height if renderer else 1080

    def init(self):
        """Initialize the effect manager."""
        self._create_effect()
        self._initialized = True

    def _create_effect(self):
        """Create the effect instance based on current settings."""
        # Determine which effect to use
        if self.effect_type == 'random':
            effect_name = random.choice(['trance_scope', 'neon_equalizer', 'psychedelic_plasma', '3d_cyber_tunnel'])
        else:
            effect_name = self.effect_type
        
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

    def render_to_array(self):
        """
        Render the current effect to a numpy array.
        
        Returns:
            numpy.ndarray: Rendered frame as RGB array
        """
        if self.current_effect:
            return self.current_effect.render_to_array()
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
