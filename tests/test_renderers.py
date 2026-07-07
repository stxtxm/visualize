"""
Tests for renderer modules: ArrayRenderer, HeadlessRenderer, PygameRenderer.
"""
import unittest
import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')


class TestArrayRenderer(unittest.TestCase):
    def test_init_creates_frame(self):
        from renderer.array_renderer import ArrayRenderer
        r = ArrayRenderer(width=320, height=240, fps=30)
        r.init()
        self.assertTrue(r.is_initialized)
        self.assertEqual(r.get_frame_size(), (320, 240))

    def test_get_surface_returns_array(self):
        from renderer.array_renderer import ArrayRenderer
        r = ArrayRenderer(width=320, height=240, fps=30)
        r.init()
        surf = r.get_surface()
        self.assertEqual(surf.shape, (240, 320, 3))

    def test_frame_as_bytes(self):
        from renderer.array_renderer import ArrayRenderer
        r = ArrayRenderer(width=320, height=240, fps=30)
        r.init()
        b = r.get_frame_as_bytes()
        self.assertEqual(len(b), 320 * 240 * 3)

    def test_handle_events_and_present(self):
        from renderer.array_renderer import ArrayRenderer
        r = ArrayRenderer(width=320, height=240, fps=30)
        r.init()
        self.assertTrue(r.handle_events())
        r.present()  # no-op
        r.cleanup()
        self.assertFalse(r.is_initialized)


class TestHeadlessRenderer(unittest.TestCase):
    def test_init(self):
        from renderer.headless_renderer import HeadlessRenderer
        r = HeadlessRenderer(width=1920, height=1080, fps=60)
        r.init()
        self.assertTrue(r.is_initialized)

    def test_get_surface(self):
        from renderer.headless_renderer import HeadlessRenderer
        r = HeadlessRenderer(width=1920, height=1080, fps=60)
        r.init()
        surf = r.get_surface()
        self.assertIsNotNone(surf)

    def test_frame_as_bytes(self):
        from renderer.headless_renderer import HeadlessRenderer
        r = HeadlessRenderer(width=1920, height=1080, fps=60)
        r.init()
        # may be None if pygame unavailable, but should not raise
        r.get_frame_as_bytes()

    def test_handle_events_present_cleanup(self):
        from renderer.headless_renderer import HeadlessRenderer
        r = HeadlessRenderer(width=1920, height=1080, fps=60)
        r.init()
        self.assertTrue(r.handle_events())
        r.present()
        r.cleanup()
        self.assertFalse(r.is_initialized)


class TestPygameRenderer(unittest.TestCase):
    def test_init_no_window(self):
        try:
            import pygame
        except ImportError:
            self.skipTest("pygame not available")
        from renderer.pygame_renderer import PygameRenderer
        r = PygameRenderer(width=400, height=300, no_window=True, fps=30)
        r.init()
        self.assertTrue(r.is_initialized)
        self.assertIsNotNone(r.get_surface())
        self.assertTrue(r.handle_events())
        r.present()
        r.cleanup()
        self.assertFalse(r.is_initialized)

    def test_get_frame_as_bytes(self):
        try:
            import pygame
        except ImportError:
            self.skipTest("pygame not available")
        from renderer.pygame_renderer import PygameRenderer
        r = PygameRenderer(width=400, height=300, no_window=True, fps=30)
        r.init()
        b = r.get_frame_as_bytes()
        # bytes or None (headless dummy still returns bytes)
        if b is not None:
            self.assertEqual(len(b), 400 * 300 * 3)
        r.cleanup()


if __name__ == '__main__':
    unittest.main()