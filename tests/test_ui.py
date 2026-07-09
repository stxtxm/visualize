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
        self.assertEqual(label.cget("fg").lower(), "#9a9acb")

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
        self.assertEqual(app._footer.cget("height"), 46)


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

    def test_popover_canvas_exists(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_export_canvas'),
                        "Export popover progress canvas should exist")
        self.assertEqual(int(app._export_canvas.cget("height")), 14,
                         "Canvas height should be 14px")

    def test_popover_draw_method_exists(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_draw_export_progress'),
                        "Export popover should have a draw method")
        # Should not raise even before the widget is laid out
        app._draw_export_progress(50)
        app._draw_export_progress(100, success_color=True)
        app._draw_export_progress(100, error_color=True)

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

    def test_popover_hide_button_exists(self):
        """Export popover should have a hide toggle button."""
        app = self._create_app()
        self.assertTrue(hasattr(app, '_export_popover_hide'),
                        "Export popover hide button should exist")
        self.assertEqual(app._export_popover_hide.cget("cursor"), "hand2")

    def test_persistent_toggle_button_exists(self):
        """A persistent status-bar button must always allow re-showing the popover."""
        app = self._create_app()
        self.assertTrue(hasattr(app, 'btn_toggle_popover'),
                        "Persistent popover toggle button should exist")
        self.assertEqual(app.btn_toggle_popover.cget("cursor"), "hand2")
        # It must be able to re-show the popover even after it was hidden.
        app._set_popover_visible(False)
        self.assertEqual(app._export_popover.place_info(), {},
                         "Popover should be unmanaged (hidden) after hide")
        app._toggle_export_popover()
        # After toggling from hidden, the popover is managed again (re-shown).
        self.assertNotEqual(app._export_popover.place_info(), {},
                            "Popover should be re-shown by the persistent toggle")

    def test_popover_toggle_method_exists(self):
        """Toggle method for export popover should exist."""
        app = self._create_app()
        self.assertTrue(hasattr(app, '_toggle_export_popover'),
                        "Toggle export popover method should exist")
        self.assertTrue(hasattr(app, 'export_popover_hidden'),
                        "Export popover hidden state should exist")

    def test_popover_hidden_state_default(self):
        """Export popover should be visible by default."""
        # Reset preferences to ensure clean state
        import os
        config_path = os.path.expanduser("~/.visualize_config.json")
        if os.path.exists(config_path):
            os.remove(config_path)
        app = self._create_app()
        self.assertFalse(app.export_popover_hidden,
                         "Export popover should be visible by default")

    def test_icon_loading_fallback(self):
        """Icons should have fallback if assets are missing."""
        app = self._create_app()
        # Even with missing files, icons should exist due to fallback
        self.assertIsNotNone(app._icon_linkedin)
        self.assertIsNotNone(app._icon_website)


@unittest.skipUnless(_has_display(), "No display server available")
class TestSocialIconVisibility(unittest.TestCase):
    """Verify the footer social icons are legible (high contrast on dark bg)."""

    FOOTER_BG = (10, 10, 18)  # #0a0a12

    def setUp(self):
        import tkinter as tk
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def _assets_dir(self):
        import os
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, "assets")

    def _icon_stats(self, name):
        from PIL import Image
        import os
        path = os.path.join(self._assets_dir(), name)
        self.assertTrue(os.path.exists(path), f"Missing icon asset: {name}")
        im = Image.open(path).convert("RGBA")
        px = [p for p in im.getdata() if p[3] > 200]
        self.assertGreater(len(px), 500, f"{name} looks empty")
        avg = tuple(sum(c[i] for c in px) // len(px) for i in range(3))
        dist = sum((avg[i] - self.FOOTER_BG[i]) ** 2 for i in range(3)) ** 0.5
        return avg, dist

    def test_linkedin_icon_visible(self):
        avg, dist = self._icon_stats("linkedin.png")
        self.assertGreater(dist, 60, "LinkedIn icon too close to footer bg (unreadable)")

    def test_website_icon_visible(self):
        avg, dist = self._icon_stats("website.png")
        self.assertGreater(dist, 60, "Website icon too close to footer bg (unreadable)")

    def test_hover_icons_visible(self):
        for name in ("linkedin_hover.png", "website_hover.png"):
            avg, dist = self._icon_stats(name)
            self.assertGreater(dist, 60, f"{name} too close to footer bg (unreadable)")


if __name__ == '__main__':
    unittest.main()