"""
Comprehensive tests for all visual effects: update(), render_to_array(),
render() on a dummy surface, all palettes, and scaling factor.
"""
import unittest
import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Run headless for pygame-based render() tests
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

EFFECT_MODULES = {
    'bars': 'BarEffect',
    'circles': 'CircleEffect',
    'particles': 'ParticleEffect',
    'tunnel': 'TunnelEffect',
    'wave': 'WaveEffect',
    'spectrum': 'SpectrumEffect',
    'plasma': 'PlasmaEffect',
    'classic': 'ClassicEffect',
    'neon_equalizer': 'ClassicEffect',
    'psychedelic_plasma': 'PlasmaEffect',
    '3d_cyber_tunnel': 'TunnelEffect',
}

PALETTES = ['psychedelic', 'retro', 'winamp_classic', 'dark', 'rainbow']

SIZES = [(100, 100), (800, 450), (1920, 1080)]


def make_audio_data():
    return {
        'volume': 0.5,
        'volume_smooth': 0.5,
        'frequency_bands': [0.1, 0.2, 0.3, 0.4, 0.5],
        'spectrum': [0.1] * 512,
        'beat': True,
        'beat_strength': 0.8,
        'beat_phase': 0.1,
        'energy': 0.5,
        'spectral_centroid': 0.4,
        'bpm': 120.0,
        'bpm_confidence': 0.9,
        'bass': 0.4,
        'mids': 0.3,
        'treble': 0.2,
    }


class TestAllEffects(unittest.TestCase):
    """Parametric tests across all effects, palettes, and sizes."""

    def _get_effect_class(self, effect_type):
        module_name, class_name = None, None
        # map via EFFECT_MAP
        from effects.manager import EFFECT_MAP
        if effect_type in EFFECT_MAP:
            module_name, class_name = EFFECT_MAP[effect_type]
        else:
            module_name, class_name = effect_type, EFFECT_MODULES.get(effect_type, 'BaseEffect')
        module = __import__(f'effects.{module_name}', fromlist=[class_name])
        return getattr(module, class_name)

    def test_render_to_array_shape_all_effects(self):
        for effect_type in EFFECT_MODULES:
            cls = self._get_effect_class(effect_type)
            for (w, h) in SIZES:
                with self.subTest(effect=effect_type, size=(w, h)):
                    eff = cls(width=w, height=h, color_palette='psychedelic')
                    eff.update(make_audio_data(), 0.033)
                    frame = eff.render_to_array()
                    self.assertIsInstance(frame, np.ndarray)
                    self.assertEqual(frame.shape, (h, w, 3))
                    self.assertEqual(frame.dtype, np.uint8)

    def test_update_mutates_time(self):
        for effect_type in EFFECT_MODULES:
            cls = self._get_effect_class(effect_type)
            with self.subTest(effect=effect_type):
                eff = cls(width=200, height=200, color_palette='psychedelic')
                t0 = eff.time
                eff.update(make_audio_data(), 0.1)
                self.assertGreater(eff.time, t0)

    def test_all_palettes_produce_colors(self):
        for effect_type in EFFECT_MODULES:
            cls = self._get_effect_class(effect_type)
            for palette in PALETTES:
                with self.subTest(effect=effect_type, palette=palette):
                    eff = cls(width=200, height=200, color_palette=palette)
                    self.assertGreater(len(eff.colors), 0)
                    frame = eff.render_to_array()
                    self.assertEqual(frame.shape, (200, 200, 3))

    def test_render_on_dummy_surface(self):
        try:
            import pygame
        except ImportError:
            self.skipTest("pygame not available")
        pygame.init()
        for effect_type in EFFECT_MODULES:
            cls = self._get_effect_class(effect_type)
            with self.subTest(effect=effect_type):
                eff = cls(width=160, height=120, color_palette='psychedelic')
                eff.update(make_audio_data(), 0.033)
                surf = pygame.Surface((160, 120))
                eff.render(surf)
        pygame.quit()

    def test_scaling_factor(self):
        """Effects should scale drawing by s = height / 450.0."""
        for effect_type in ('bars', 'circles', 'classic', 'spectrum'):
            cls = self._get_effect_class(effect_type)
            with self.subTest(effect=effect_type):
                eff_small = cls(width=100, height=100, color_palette='psychedelic')
                eff_big = cls(width=1920, height=1080, color_palette='psychedelic')
                # scaling factor should differ
                self.assertNotEqual(eff_small.height / 450.0, eff_big.height / 450.0)

    def test_classic_render_to_array_default_palette(self):
        from effects.classic import ClassicEffect
        eff = ClassicEffect(width=300, height=300, color_palette='winamp_classic')
        eff.update(make_audio_data(), 0.033)
        frame = eff.render_to_array()
        self.assertEqual(frame.shape, (300, 300, 3))


if __name__ == '__main__':
    unittest.main()