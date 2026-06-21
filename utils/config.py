"""
Configuration module for psychedelic visualizer.
"""

import os
import json
from pathlib import Path


class Config:
    """
    Configuration manager for the visualizer.
    Handles default settings and user preferences.
    """
    
    # Default configuration
    DEFAULTS = {
        'audio_dir': os.path.expanduser('~/Music'),
        'output_dir': os.path.expanduser('~/Videos'),
        'effect': 'random',
        'color_palette': 'psychedelic',
        'resolution': '1080p',
        'fps': 60,
        'fullscreen': False,
        'volume': 1.0,
        'smoothing': 0.2,
        'num_bars': 64,
        'num_circles': 10,
        'max_particles': 200,
        'tunnel_depth': 30,
        'num_waves': 8,
    }
    
    # Resolution mappings
    RESOLUTIONS = {
        '1080p': (1920, 1080),
        '1440p': (2560, 1440),
        '4K': (3840, 2160),
    }
    
    # Available effects
    EFFECTS = ['random', 'bars', 'circles', 'particles', 'tunnel', 'wave']
    
    # Available color palettes
    PALETTES = ['psychedelic', 'retro', 'dark', 'rainbow']
    
    def __init__(self, config_file=None):
        """
        Initialize the configuration.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_file = config_file
        self._config = self.DEFAULTS.copy()
        
        # Load user configuration if available
        if config_file and os.path.exists(config_file):
            self.load()
        else:
            # Try default config file location
            default_config = os.path.join(
                os.path.expanduser('~'),
                '.psychedelic-visualizer',
                'config.json'
            )
            if os.path.exists(default_config):
                self.config_file = default_config
                self.load()

    def load(self):
        """Load configuration from file."""
        if not self.config_file:
            return
        
        try:
            with open(self.config_file, 'r') as f:
                loaded_config = json.load(f)
                # Update defaults with loaded values
                for key, value in loaded_config.items():
                    if key in self._config:
                        self._config[key] = value
        except Exception:
            pass  # Ignore errors and use defaults

    def save(self):
        """Save configuration to file."""
        if not self.config_file:
            return
        
        try:
            # Ensure directory exists
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception:
            pass

    def get(self, key, default=None):
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)
    
    def set(self, key, value):
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        if key in self._config or key in self.DEFAULTS:
            self._config[key] = value

    def get_resolution(self, resolution_name):
        """
        Get resolution dimensions.
        
        Args:
            resolution_name: Name of resolution (e.g., '1080p')
            
        Returns:
            Tuple of (width, height)
        """
        return self.RESOLUTIONS.get(resolution_name, (1920, 1080))
    
    @property
    def audio_dir(self):
        """Get audio directory."""
        return self.get('audio_dir', self.DEFAULTS['audio_dir'])
    
    @audio_dir.setter
    def audio_dir(self, value):
        """Set audio directory."""
        self.set('audio_dir', value)
    
    @property
    def output_dir(self):
        """Get output directory."""
        return self.get('output_dir', self.DEFAULTS['output_dir'])
    
    @output_dir.setter
    def output_dir(self, value):
        """Set output directory."""
        self.set('output_dir', value)


# Global configuration instance
config = Config()
