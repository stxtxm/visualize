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
        self.assertEqual(label.cget("fg").lower(), "#8a8aaa")

    def test_linkedin_label_exists(self):
        app = self._create_app()
        label = app._footer_linkedin
        self.assertIsNotNone(label)
        self.assertIsNotNone(label.cget("image"), "LinkedIn should have an image")
        self.assertEqual(label.cget("bg").lower(), "#0a0a12")
        self.assertEqual(label.cget("cursor"), "hand2")

    def test_linkedin_hover_images_exist(self):
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
        app = self._create_app()
        self.assertTrue(hasattr(app, '_icon_website_hover'),
                        "Website should have a hover icon")

    def test_footer_self_reference(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_footer'), "Footer frame should exist")
        self.assertEqual(app._footer.cget("height"), 24)


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
class TestExportPopover(unittest.TestCase):
    """Verify the export progress popover (overlaid on preview, bottom-right)."""

    def setUp(self):
        import tkinter as tk
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def _create_app(self):
        from ui.main_window import MainWindow
        return MainWindow(self.root)

    def test_popover_exists(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_export_popover'),
                        "Export popover frame should exist")

    def test_popover_inner_exists(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_export_popover_inner'),
                        "Export popover inner frame should exist")

    def test_popover_label_exists(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_export_popover_label'),
                        "Export popover label should exist")
        self.assertEqual(app._export_popover_label.cget("fg").lower(), app.NEON_CYAN.lower())

    def test_popover_close_button(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_export_popover_close'),
                        "Export popover close button should exist")
        self.assertEqual(app._export_popover_close.cget("cursor"), "hand2")

    def test_popover_track_exists(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_export_popover_track'),
                        "Export popover progress track should exist")
        self.assertEqual(app._export_popover_track.cget("height"), 4,
                         "Track height should be 4px")

    def test_popover_fill_exists(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_export_popover_fill'),
                        "Export popover progress fill should exist")
        self.assertEqual(app._export_popover_fill.cget("height"), 4,
                         "Fill height should be 4px")
        self.assertEqual(app._export_popover_fill.cget("bg").lower(), app.NEON_CYAN.lower())

    def test_popover_pct_label(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_export_popover_pct'),
                        "Export popover percentage label should exist")
        self.assertEqual(app._export_popover_pct.cget("fg").lower(), app.NEON_CYAN.lower())

    def test_popover_hide_show(self):
        """Test show/hide methods work without error."""
        app = self._create_app()
        app._show_export_popover()
        app._hide_export_popover()

    def test_old_progress_bar_removed(self):
        """Old export progress bar widgets should no longer exist."""
        app = self._create_app()
        self.assertFalse(hasattr(app, '_export_progress_container'),
                         "Old _export_progress_container should not exist")
        self.assertFalse(hasattr(app, '_export_progress_bar'),
                         "Old _export_progress_bar should not exist")
        self.assertFalse(hasattr(app, '_export_progress_track'),
                         "Old _export_progress_track should not exist")


if __name__ == '__main__':
    unittest.main()