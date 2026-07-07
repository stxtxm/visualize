"""
Tests for UI components (footer labels, progress bar, etc.).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _has_display():
    """Return True if a display server is available."""
    if 'DISPLAY' not in os.environ or not os.environ['DISPLAY']:
        return False
    return True


@unittest.skipUnless(_has_display(), "No display server available")
class TestFooterLabels(unittest.TestCase):
    """Verify the copyright and social link labels in the main window footer."""

    def setUp(self):
        import tkinter as tk
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def _create_app(self):
        from ui.main_window import MainWindow
        return MainWindow(self.root)

    def test_copyright_label_exists(self):
        app = self._create_app()
        label = app._footer_copyright
        self.assertIsNotNone(label)
        self.assertIn("Timothée Grollier", label.cget("text"))
        self.assertIn("2026", label.cget("text"))
        # Should be lighter than old #4a4a5e
        self.assertEqual(label.cget("fg").lower(), "#8a8aaa")

    def test_linkedin_label_exists(self):
        app = self._create_app()
        label = app._footer_linkedin
        self.assertIsNotNone(label)
        self.assertIsNotNone(label.cget("image"), "LinkedIn should have an image")
        self.assertEqual(label.cget("bg").lower(), "#0a0a12")
        self.assertEqual(label.cget("cursor"), "hand2")

    def test_website_label_exists(self):
        app = self._create_app()
        label = app._footer_website
        self.assertIsNotNone(label)
        self.assertIsNotNone(label.cget("image"), "Website should have an image")
        self.assertEqual(label.cget("bg").lower(), "#0a0a12")
        self.assertEqual(label.cget("cursor"), "hand2")


@unittest.skipUnless(_has_display(), "No display server available")
class TestBackgroundControls(unittest.TestCase):
    """Verify opacity slider and remove background button."""

    def setUp(self):
        import tkinter as tk
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def _create_app(self):
        from ui.main_window import MainWindow
        return MainWindow(self.root)

    def test_opacity_slider_exists(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, 'opacity_slider'), "Opacity slider should exist")
        self.assertEqual(app.opacity_var.get(), 72.0, "Default opacity should be 72%")

    def test_opacity_label_displays_percentage(self):
        app = self._create_app()
        self.assertEqual(app._opacity_label.cget("text"), "72%")

    def test_remove_background_button_exists(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, 'btn_remove_bg'), "Remove background button should exist")
        self.assertIn("RETIRER", app.btn_remove_bg.cget("text").upper())


@unittest.skipUnless(_has_display(), "No display server available")
class TestProgressBar(unittest.TestCase):
    """Verify the improved export progress bar (track + fill)."""

    def setUp(self):
        import tkinter as tk
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def _create_app(self):
        from ui.main_window import MainWindow
        return MainWindow(self.root)

    def test_progress_track_exists(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_export_progress_track'), "Progress track frame should exist")
        track = app._export_progress_track
        self.assertEqual(track.cget("height"), 5, "Track height should be 5px")
        self.assertEqual(track.cget("bg").lower(), "#0a2a33")

    def test_progress_fill_exists(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_export_progress_fill'), "Progress fill frame should exist")
        fill = app._export_progress_fill
        self.assertEqual(fill.cget("height"), 5, "Fill height should be 5px")
        # Must match NEON_CYAN color
        self.assertEqual(fill.cget("bg").lower(), app.NEON_CYAN.lower())


if __name__ == '__main__':
    unittest.main()
