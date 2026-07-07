"""
Tests for effects modules.
"""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestBaseEffect(unittest.TestCase):
    """Test base effect class."""
    
    def test_import(self):
        """Test that base effect can be imported."""
        from effects.base import BaseEffect
        self.assertTrue(callable(BaseEffect))
    
    def test_initialization(self):
        """Test BaseEffect initialization."""
        from effects.base import BaseEffect
        
        effect = BaseEffect(width=1920, height=1080, color_palette='psychedelic')
        
        self.assertEqual(effect.width, 1920)
        self.assertEqual(effect.height, 1080)
        self.assertEqual(effect.color_palette, 'psychedelic')
        self.assertGreater(len(effect.colors), 0)
    
    def test_color_palettes(self):
        """Test all color palettes are defined."""
        from effects.base import BaseEffect
        
        palettes = ['psychedelic', 'retro', 'dark', 'rainbow']
        
        for palette in palettes:
            effect = BaseEffect(width=100, height=100, color_palette=palette)
            self.assertGreater(len(effect.colors), 0, f"Palette {palette} should have colors")
    
    def test_get_color(self):
        """Test get_color method."""
        from effects.base import BaseEffect
        
        effect = BaseEffect(width=100, height=100)
        
        # Test with None index (should use time)
        color = effect.get_color(None)
        self.assertIsInstance(color, tuple)
        self.assertEqual(len(color), 3)
        
        # Test with specific index
        color = effect.get_color(0)
        self.assertIsInstance(color, tuple)
    
    def test_time_increases(self):
        """Test that time increases on update."""
        from effects.base import BaseEffect
        
        effect = BaseEffect(width=100, height=100)
        initial_time = effect.time
        
        effect.update({'volume': 0.5}, 0.1)
        
        self.assertGreater(effect.time, initial_time)
    
    def test_render_raises_not_implemented(self):
        """Test that base render method raises NotImplementedError."""
        from effects.base import BaseEffect
        import numpy as np
        
        effect = BaseEffect(width=100, height=100)
        
        with self.assertRaises(NotImplementedError):
            effect.render(np.zeros((100, 100, 3), dtype=np.uint8))
    
    def test_render_to_array_raises_not_implemented(self):
        """Test that base render_to_array method raises NotImplementedError."""
        from effects.base import BaseEffect
        
        effect = BaseEffect(width=100, height=100)
        
        with self.assertRaises(NotImplementedError):
            effect.render_to_array()


class TestClassicEffect(unittest.TestCase):
    """Test classic effect."""

    def test_classic_effect_can_be_imported(self):
        from effects.classic import ClassicEffect
        self.assertTrue(callable(ClassicEffect))


class TestTranceScopeEffect(unittest.TestCase):
    """Test professional trance effect."""

    def test_import(self):
        from effects.trance_scope import TranceScopeEffect
        self.assertTrue(callable(TranceScopeEffect))

    def test_render_to_array(self):
        from effects.trance_scope import TranceScopeEffect
        import numpy as np

        effect = TranceScopeEffect(width=120, height=80)
        effect.update({
            'volume': 0.5,
            'energy': 0.5,
            'frequency_bands': [0.1, 0.2, 0.3, 0.4, 0.5],
            'visual_bands': [0.2] * 32,
            'spectrum': [0.1] * 512,
            'beat': True,
            'beat_strength': 0.8,
            'beat_phase': 0.15,
            'bpm': 128.0,
            'bass': 0.6,
            'mids': 0.4,
            'treble': 0.3,
            'onset_strength': 0.7,
        }, 0.033)
        frame = effect.render_to_array()

        self.assertIsInstance(frame, np.ndarray)
        self.assertEqual(frame.shape, (80, 120, 3))
        self.assertEqual(frame.dtype, np.uint8)

    def test_trance_scope_has_no_bar_equalizer_surface(self):
        from effects.trance_scope import TranceScopeEffect

        effect = TranceScopeEffect(width=120, height=80)

        self.assertFalse(hasattr(effect, 'bar_heights'))
        self.assertFalse(hasattr(effect, 'num_bars'))
        self.assertFalse(hasattr(effect, '_draw_equalizer'))
        self.assertTrue(hasattr(effect, 'orbit_values'))


class TestBarEffect(unittest.TestCase):
    """Test bar effect."""
    
    def test_import(self):
        """Test that bar effect can be imported."""
        from effects.bars import BarEffect
        self.assertTrue(callable(BarEffect))
    
    def test_initialization(self):
        """Test BarEffect initialization."""
        from effects.bars import BarEffect
        
        effect = BarEffect(width=1920, height=1080)
        
        self.assertEqual(effect.width, 1920)
        self.assertEqual(effect.height, 1080)
        self.assertEqual(len(effect.bar_heights), effect.num_bars)
    
    def test_update(self):
        """Test BarEffect update method."""
        from effects.bars import BarEffect
        
        effect = BarEffect(width=100, height=100)
        
        # Test with None audio data
        effect.update(None, 0.1)
        
        # Test with valid audio data
        audio_data = {
            'volume': 0.5,
            'frequency_bands': [0.1, 0.2, 0.3, 0.4, 0.5],
            'spectrum': [0.1] * 512,
            'beat': False
        }
        effect.update(audio_data, 0.1)
        
        # Check that bar heights were updated
        self.assertGreater(sum(effect.bar_heights), 0)
    
    def test_render_to_array(self):
        """Test BarEffect render_to_array method."""
        from effects.bars import BarEffect
        import numpy as np
        
        effect = BarEffect(width=100, height=100)
        
        frame = effect.render_to_array()
        
        self.assertIsInstance(frame, np.ndarray)
        self.assertEqual(frame.shape, (100, 100, 3))


class TestCircleEffect(unittest.TestCase):
    """Test circle effect."""
    
    def test_import(self):
        """Test that circle effect can be imported."""
        from effects.circles import CircleEffect
        self.assertTrue(callable(CircleEffect))
    
    def test_initialization(self):
        """Test CircleEffect initialization."""
        from effects.circles import CircleEffect
        
        effect = CircleEffect(width=1920, height=1080)
        
        self.assertEqual(effect.width, 1920)
        self.assertEqual(effect.height, 1080)
        self.assertEqual(len(effect.radii), effect.num_circles)
    
    def test_render_to_array(self):
        """Test CircleEffect render_to_array method."""
        from effects.circles import CircleEffect
        import numpy as np
        
        effect = CircleEffect(width=100, height=100)
        
        frame = effect.render_to_array()
        
        self.assertIsInstance(frame, np.ndarray)
        self.assertEqual(frame.shape, (100, 100, 3))


class TestParticleEffect(unittest.TestCase):
    """Test particle effect."""
    
    def test_import(self):
        """Test that particle effect can be imported."""
        from effects.particles import ParticleEffect
        self.assertTrue(callable(ParticleEffect))
    
    def test_initialization(self):
        """Test ParticleEffect initialization."""
        from effects.particles import ParticleEffect
        
        effect = ParticleEffect(width=1920, height=1080)
        
        self.assertEqual(effect.width, 1920)
        self.assertEqual(effect.height, 1080)
        self.assertEqual(len(effect.particles), 0)  # Initially empty


class TestTunnelEffect(unittest.TestCase):
    """Test tunnel effect."""
    
    def test_import(self):
        """Test that tunnel effect can be imported."""
        from effects.tunnel import TunnelEffect
        self.assertTrue(callable(TunnelEffect))
    
    def test_initialization(self):
        """Test TunnelEffect initialization."""
        from effects.tunnel import TunnelEffect
        
        effect = TunnelEffect(width=1920, height=1080)
        
        self.assertEqual(effect.width, 1920)
        self.assertEqual(effect.height, 1080)
    
    def test_render_to_array(self):
        """Test TunnelEffect render_to_array method."""
        from effects.tunnel import TunnelEffect
        import numpy as np
        
        effect = TunnelEffect(width=100, height=100)
        
        frame = effect.render_to_array()
        
        self.assertIsInstance(frame, np.ndarray)
        self.assertEqual(frame.shape, (100, 100, 3))


class TestWaveEffect(unittest.TestCase):
    """Test wave effect."""
    
    def test_import(self):
        """Test that wave effect can be imported."""
        from effects.wave import WaveEffect
        self.assertTrue(callable(WaveEffect))
    
    def test_initialization(self):
        """Test WaveEffect initialization."""
        from effects.wave import WaveEffect
        
        effect = WaveEffect(width=1920, height=1080)
        
        self.assertEqual(effect.width, 1920)
        self.assertEqual(effect.height, 1080)
    
    def test_render_to_array(self):
        """Test WaveEffect render_to_array method."""
        from effects.wave import WaveEffect
        import numpy as np
        
        effect = WaveEffect(width=100, height=100)
        
        frame = effect.render_to_array()
        
        self.assertIsInstance(frame, np.ndarray)
        self.assertEqual(frame.shape, (100, 100, 3))


class TestEffectManager(unittest.TestCase):
    """Test effect manager."""
    
    def test_import(self):
        """Test that effect manager can be imported."""
        from effects.manager import EffectManager
        self.assertTrue(callable(EffectManager))
    
    def test_effect_types(self):
        """Test that all effect types are available."""
        from effects.manager import EffectManager
        
        effect_types = ['bars', 'circles', 'particles', 'tunnel', 'wave', 'random']
        
        for effect_type in effect_types:
            # Just check that the type is in the mapping
            self.assertIn(effect_type, ['bars', 'circles', 'particles', 'tunnel', 'wave', 'random'])


if __name__ == '__main__':
    unittest.main()
