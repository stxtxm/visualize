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

    def test_linkedin_hover_images_exist(self):
        """LinkedIn should have a hover variant (brighter background)."""
        app = self._create_app()
        self.assertTrue(hasattr(app, '_icon_linkedin_hover'),
                        "LinkedIn should have a hover icon")

    def test_website_label_exists(self):
        app = self._create_app()
        label = app._footer_website
        self.assertIsNotNone(label)
        self.assertIsNotNone(label.cget("image"), "Website should have an image")
        self.assertEqual(label.cget("bg").lower(), "#0a0a12")
        self.assertEqual(label.cget("cursor"), "hand2")

    def test_website_hover_images_exist(self):
        """Website should have a hover variant (brighter background)."""
        app = self._create_app()
        self.assertTrue(hasattr(app, '_icon_website_hover'),
                        "Website should have a hover icon")

    def test_footer_self_reference(self):
        """Footer frame should be stored as self._footer."""
        app = self._create_app()
        self.assertTrue(hasattr(app, '_footer'), "Footer frame should exist")
        # Footer should have height 22
        self.assertEqual(app._footer.cget("height"), 22)


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
    """Verify the improved export progress bar (dedicated row between status and footer)."""

    def setUp(self):
        import tkinter as tk
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def _create_app(self):
        from ui.main_window import MainWindow
        return MainWindow(self.root)

    def test_progress_container_exists(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_export_progress_container'),
                        "Progress container frame should exist")
        self.assertEqual(app._export_progress_container.cget("bg").lower(), "#0a0a12")

    def test_progress_bar_widget(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_export_progress_bar'),
                        "Progress bar frame should exist")
        self.assertEqual(app._export_progress_bar.cget("height"), 10,
                         "Bar height should be 10px")
        self.assertEqual(app._export_progress_bar.cget("bg").lower(), "#1a1a2e")

    def test_progress_fill_widget(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_export_progress_fill'),
                        "Progress fill frame should exist")
        self.assertEqual(app._export_progress_fill.cget("height"), 10,
                         "Fill height should be 10px")
        self.assertEqual(app._export_progress_fill.cget("bg").lower(), app.NEON_CYAN.lower())

    def test_progress_percentage_label(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_export_progress_pct'),
                        "Progress percentage label should exist")
        self.assertEqual(app._export_progress_pct.cget("fg").lower(), app.NEON_CYAN.lower())
        self.assertEqual(app._export_progress_pct.cget("bg").lower(), "#0a0a12")


if __name__ == '__main__':
    unittest.main()