"""
Tests for effects/manager.py (EffectManager): instantiation of every effect,
change_effect, change_palette, random selection, delegation, cleanup.
"""
import unittest
import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')


class MockRenderer:
    def __init__(self, w=800, h=600):
        self.width = w
        self.height = h


class TestEffectManagerFull(unittest.TestCase):
    """Exercise EffectManager thoroughly."""

    def _make_manager(self, effect_type='bars', palette='psychedelic'):
        from effects.manager import EffectManager
        mgr = EffectManager(analyzer=None, renderer=MockRenderer(),
                            effect_type=effect_type, color_palette=palette)
        mgr.init()
        return mgr

    def test_instantiate_every_effect(self):
        from effects.manager import EFFECT_MAP
        for effect_type in EFFECT_MAP:
            with self.subTest(effect=effect_type):
                mgr = self._make_manager(effect_type=effect_type)
                self.assertIsNotNone(mgr.current_effect)
                mgr.cleanup()

    def test_change_effect(self):
        mgr = self._make_manager(effect_type='bars')
        mgr.change_effect('plasma')
        self.assertIsNotNone(mgr.current_effect)
        self.assertIn(mgr.get_current_effect_name(), ('psychedelic_plasma', 'plasma'))
        mgr.cleanup()

    def test_change_palette(self):
        mgr = self._make_manager(effect_type='bars', palette='psychedelic')
        mgr.change_palette('winamp_classic')
        self.assertEqual(mgr.current_effect.color_palette, 'winamp_classic')
        self.assertGreater(len(mgr.current_effect.colors), 0)
        mgr.cleanup()

    def test_random_effect(self):
        mgr = self._make_manager(effect_type='random')
        self.assertIsNotNone(mgr.current_effect)
        mgr.cleanup()

    def test_update_delegates(self):
        mgr = self._make_manager(effect_type='bars')
        audio = {'volume': 0.5, 'frequency_bands': [0.1] * 5, 'spectrum': [0.1] * 512,
                 'beat': True, 'bass': 0.3, 'mids': 0.2, 'treble': 0.1}
        t0 = mgr.current_effect.time
        mgr.update(audio, 0.033)
        self.assertGreater(mgr.current_effect.time, t0)
        mgr.cleanup()

    def test_render_to_array_delegates(self):
        mgr = self._make_manager(effect_type='bars')
        frame = mgr.render_to_array()
        self.assertIsInstance(frame, np.ndarray)
        self.assertEqual(frame.shape, (600, 800, 3))
        mgr.cleanup()

    def test_render_delegates_to_surface(self):
        try:
            import pygame
        except ImportError:
            self.skipTest("pygame not available")
        pygame.init()
        mgr = self._make_manager(effect_type='bars')
        surf = pygame.Surface((800, 600))
        mgr.render(surf)
        pygame.quit()
        mgr.cleanup()

    def test_cleanup_nulls_effect(self):
        mgr = self._make_manager(effect_type='bars')
        mgr.cleanup()
        self.assertIsNone(mgr.current_effect)
        self.assertFalse(mgr.is_initialized)

    def test_get_current_effect_name_fallback(self):
        mgr = self._make_manager(effect_type='bars')
        name = mgr.get_current_effect_name()
        self.assertTrue(isinstance(name, str))
        mgr.cleanup()


if __name__ == '__main__':
    unittest.main()