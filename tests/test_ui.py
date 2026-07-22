"""
Comprehensive tests for UI components after tabbed refactor.

Tests cover:
- TabPanel navigation and visibility
- Footer labels and social icons
- FileTab, EffectsTab, BackgroundTab, ExportTab, LogsTab
- MainWindow integration
- Export progress (integrated in ExportTab, no more popover)
"""

import os
import sys
import unittest
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _has_display():
    """Return True if a display server is available."""
    if 'DISPLAY' not in os.environ or not os.environ['DISPLAY']:
        return False
    return True


# ══════════════════════════════════════════════════════════════════════
# TabPanel tests
# ══════════════════════════════════════════════════════════════════════

@unittest.skipUnless(_has_display(), "No display server available")
class TestTabPanel(unittest.TestCase):
    """TabPanel widget: creation, adding tabs, selection, visibility."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def _create_panel(self):
        from ui.tab_panel import TabPanel
        panel = TabPanel(self.root)
        panel.pack()
        return panel

    def test_creation(self):
        panel = self._create_panel()
        self.assertIsNotNone(panel)
        self.assertEqual(len(panel._tabs), 0)
        self.assertEqual(len(panel._tab_buttons), 0)

    def test_add_tab(self):
        panel = self._create_panel()
        content = panel.add_tab("TEST")
        self.assertIsNotNone(content)
        self.assertEqual(len(panel._tabs), 1)
        self.assertEqual(len(panel._tab_buttons), 1)
        self.assertEqual(panel._tabs[0][0], "TEST")

    def test_add_tab_with_frame(self):
        panel = self._create_panel()
        custom = tk.Frame(panel)
        returned = panel.add_tab("CUSTOM", custom)
        self.assertIs(returned, custom)

    def test_multiple_tabs(self):
        panel = self._create_panel()
        panel.add_tab("A")
        panel.add_tab("B")
        panel.add_tab("C")
        self.assertEqual(len(panel._tabs), 3)
        self.assertEqual(len(panel._tab_buttons), 3)

    def test_select_tab_by_index(self):
        panel = self._create_panel()
        self.root.geometry("200x300")
        self.root.update_idletasks()

        t0 = panel.add_tab("A")
        t1 = panel.add_tab("B")
        t2 = panel.add_tab("C")
        self.root.update_idletasks()

        # Initially first tab is active
        self.assertEqual(panel._active_index.get(), 0)

        # Select middle tab — verify index changed and no crash
        panel.select(1)
        self.root.update_idletasks()
        self.assertEqual(panel._active_index.get(), 1)

        # Select last tab
        panel.select(2)
        self.root.update_idletasks()
        self.assertEqual(panel._active_index.get(), 2)

        # Verify button styles updated on each selection
        panel.select(0)
        self.root.update_idletasks()
        self.assertEqual(panel._active_index.get(), 0)

    def test_select_out_of_range(self):
        panel = self._create_panel()
        panel.add_tab("A")
        panel.select(5)  # should not raise
        self.assertEqual(panel._active_index.get(), 0)
        panel.select(-1)
        self.assertEqual(panel._active_index.get(), 0)

    def test_button_styles_on_select(self):
        panel = self._create_panel()
        panel.add_tab("A")
        panel.add_tab("B")
        btn0, btn1 = panel._tab_buttons
        # First tab active (cyan)
        self.assertEqual(btn0.cget("fg").lower(), panel.NEON_CYAN.lower())
        self.assertEqual(btn1.cget("fg").lower(), panel.FG_MUTED.lower())
        # Switch
        panel.select(1)
        self.assertEqual(btn0.cget("fg").lower(), panel.FG_MUTED.lower())
        self.assertEqual(btn1.cget("fg").lower(), panel.NEON_CYAN.lower())


# ══════════════════════════════════════════════════════════════════════
# Footer tests
# ══════════════════════════════════════════════════════════════════════

@unittest.skipUnless(_has_display(), "No display server available")
class TestFooterLabels(unittest.TestCase):
    """Verify the copyright and social link labels in the main window footer."""

    def setUp(self):
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
        # Colour is theme-dependent; just verify it's a valid hex
        fg = label.cget("fg").lower()
        self.assertTrue(fg.startswith("#"), f"Expected hex colour, got {fg}")

    def test_linkedin_label_exists(self):
        app = self._create_app()
        label = app._footer_linkedin
        self.assertIsNotNone(label)
        self.assertIsNotNone(label.cget("image"), "LinkedIn should have an image")
        # Background is theme-dependent; just verify it's a valid hex
        bg = label.cget("bg").lower()
        self.assertTrue(bg.startswith("#"), f"Expected hex colour, got {bg}")
        self.assertEqual(label.cget("cursor"), "hand2")

    def test_website_label_exists(self):
        app = self._create_app()
        label = app._footer_website
        self.assertIsNotNone(label)
        self.assertIsNotNone(label.cget("image"), "Website should have an image")
        bg = label.cget("bg").lower()
        self.assertTrue(bg.startswith("#"), f"Expected hex colour, got {bg}")
        self.assertEqual(label.cget("cursor"), "hand2")

    def test_footer_self_reference(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_footer'), "Footer frame should exist")
        self.assertEqual(app._footer.cget("height"), 42)


# ══════════════════════════════════════════════════════════════════════
# Background controls tests
# ══════════════════════════════════════════════════════════════════════

@unittest.skipUnless(_has_display(), "No display server available")
class TestBackgroundControls(unittest.TestCase):
    """Verify opacity slider and remove background button in BackgroundTab."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def _create_app(self):
        from ui.main_window import MainWindow
        return MainWindow(self.root)

    def test_opacity_var_default(self):
        app = self._create_app()
        self.assertEqual(app.opacity_var.get(), 72.0, "Default opacity should be 72%")

    def test_remove_background_button_exists(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_bg_tab'),
                        "Background tab should exist")
        self.assertTrue(hasattr(app._bg_tab, 'btn_remove'),
                        "Remove background button should exist in tab")

    def test_background_file_var(self):
        app = self._create_app()
        self.assertEqual(app.background_image.get(), "")

    def test_background_tab_opacity_slider(self):
        app = self._create_app()
        tab = app._bg_tab
        self.assertTrue(hasattr(tab, 'opacity_slider'),
                        "Opacity slider should exist in BackgroundTab")
        self.assertEqual(int(tab.opacity_slider.cget("from")), 0)
        self.assertEqual(int(tab.opacity_slider.cget("to")), 100)

    def test_background_tab_opacity_label(self):
        app = self._create_app()
        tab = app._bg_tab
        self.assertIsNotNone(tab._opacity_label)
        self.assertIn("72", tab._opacity_label.cget("text"))


# ══════════════════════════════════════════════════════════════════════
# Effects tab tests
# ══════════════════════════════════════════════════════════════════════

@unittest.skipUnless(_has_display(), "No display server available")
class TestEffectsTab(unittest.TestCase):
    """Verify EffectsTab dropdowns and description."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def _create_app(self):
        from ui.main_window import MainWindow
        return MainWindow(self.root)

    def test_effects_tab_exists(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_effects_tab'))

    def test_effect_var_default(self):
        app = self._create_app()
        self.assertEqual(app.selected_effect.get(), "Trance Scope")

    def test_palette_var_default(self):
        app = self._create_app()
        self.assertEqual(app.selected_color.get(), "psychedelic")

    def test_description_updates(self):
        app = self._create_app()
        tab = app._effects_tab
        # Default description should be for Trance Scope
        desc = tab._desc_text.get()
        self.assertIn("Visualizer premium", desc)
        self.assertIn("bloom spectral", desc)


# ══════════════════════════════════════════════════════════════════════
# File tab tests
# ══════════════════════════════════════════════════════════════════════

@unittest.skipUnless(_has_display(), "No display server available")
class TestFileTab(unittest.TestCase):
    """Verify FileTab presence and file info display."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def _create_app(self):
        from ui.main_window import MainWindow
        return MainWindow(self.root)

    def test_file_tab_exists(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_file_tab'))

    def test_initial_file_info(self):
        app = self._create_app()
        self.assertEqual(app._file_tab._file_info_text.get(),
                         "Aucun fichier sélectionné")

    def test_file_var_default(self):
        app = self._create_app()
        self.assertEqual(app.audio_file.get(), "")

    def test_format_size(self):
        tab = self._create_app()._file_tab
        self.assertIn("o", tab._format_size(500))
        self.assertIn("Ko", tab._format_size(2048))
        self.assertIn("Mo", tab._format_size(1048576 * 5))
        self.assertIn("Go", tab._format_size(1073741824 * 3))


# ══════════════════════════════════════════════════════════════════════
# Export tab tests
# ══════════════════════════════════════════════════════════════════════

@unittest.skipUnless(_has_display(), "No display server available")
class TestExportTab(unittest.TestCase):
    """Verify ExportTab controls and progress bar."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def _create_app(self):
        from ui.main_window import MainWindow
        return MainWindow(self.root)

    def test_export_tab_exists(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_export_tab'))

    def test_export_button_exists(self):
        app = self._create_app()
        tab = app._export_tab
        self.assertTrue(hasattr(tab, 'btn_export'))
        self.assertEqual(tab.btn_export.cget("text"), "🎥 EXPORTER LA VIDÉO")

    def test_default_resolution(self):
        app = self._create_app()
        self.assertEqual(app.resolution.get(), "1080p")

    def test_default_fps(self):
        app = self._create_app()
        self.assertEqual(app.fps.get(), 60)

    def test_show_progress(self):
        app = self._create_app()
        tab = app._export_tab
        tab.show_progress(50, 100)
        self.assertIn("50", tab._progress_pct.cget("text"))

    def test_show_progress_success(self):
        app = self._create_app()
        tab = app._export_tab
        tab.show_progress_success("test.mp4")
        self.assertIn("100%", tab._progress_pct.cget("text"))
        self.assertIn("test.mp4", tab._progress_label.cget("text"))

    def test_show_progress_error(self):
        app = self._create_app()
        tab = app._export_tab
        tab.show_progress_error("Something went wrong")
        self.assertIn("ERR", tab._progress_pct.cget("text"))
        self.assertIn("ÉCHEC", tab._progress_label.cget("text"))

    def test_hide_progress(self):
        app = self._create_app()
        tab = app._export_tab
        tab.show_progress(10, 100)
        # Check that the label text was set (verifies show_progress ran)
        self.assertIn("10", tab._progress_pct.cget("text"))
        # hide_progress should not raise
        try:
            tab.hide_progress()
        except Exception as e:
            self.fail(f"hide_progress raised: {e}")

    def test_set_export_button_disabled(self):
        app = self._create_app()
        tab = app._export_tab
        tab.set_export_button_state(False)
        self.assertEqual(str(tab.btn_export.cget("state")),
                         str(tk.DISABLED))

    def test_set_export_button_enabled(self):
        app = self._create_app()
        tab = app._export_tab
        tab.set_export_button_state(True)
        self.assertEqual(str(tab.btn_export.cget("state")),
                         str(tk.NORMAL))

    def test_draw_progress(self):
        app = self._create_app()
        tab = app._export_tab
        # Should not raise
        tab._draw_progress(50)
        tab._draw_progress(100, success_color=True)
        tab._draw_progress(100, error_color=True)

    def test_draw_progress_on_empty_canvas(self):
        app = self._create_app()
        tab = app._export_tab
        try:
            tab._draw_progress(0)
        except Exception as e:
            self.fail(f"_draw_progress(0) raised: {e}")


# ══════════════════════════════════════════════════════════════════════
# Logs tab tests
# ══════════════════════════════════════════════════════════════════════

@unittest.skipUnless(_has_display(), "No display server available")
class TestLogsTab(unittest.TestCase):
    """Verify LogsTab exists and accepts messages."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def _create_app(self):
        from ui.main_window import MainWindow
        return MainWindow(self.root)

    def test_logs_tab_exists(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, '_logs_tab'))

    def test_add_message(self):
        app = self._create_app()
        tab = app._logs_tab
        tab.add_message("Test message", "INFO")
        # Not checking display directly as it's async (polling)
        # Just verify it doesn't crash
        self.root.update_idletasks()


# ══════════════════════════════════════════════════════════════════════
# MainWindow integration tests
# ══════════════════════════════════════════════════════════════════════

@unittest.skipUnless(_has_display(), "No display server available")
class TestMainWindowIntegration(unittest.TestCase):
    """MainWindow: tabs, preview, status bar, led."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def _create_app(self):
        from ui.main_window import MainWindow
        return MainWindow(self.root)

    def test_tab_panel_exists(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, 'tab_panel'))
        self.assertEqual(len(app.tab_panel._tabs), 6)

    def test_tab_labels(self):
        app = self._create_app()
        labels = [t[0] for t in app.tab_panel._tabs]
        self.assertIn("FICHIER", labels[0])
        self.assertIn("EFFETS", labels[1])
        self.assertIn("FOND", labels[2])
        self.assertIn("LOGO", labels[3])
        self.assertIn("EXPORT", labels[4])
        self.assertIn("LOGS", labels[5])

    def test_preview_exists(self):
        app = self._create_app()
        self.assertTrue(hasattr(app, 'preview'))

    def test_status_bar(self):
        app = self._create_app()
        self.assertEqual(app.status_var.get(), "PRÊT")
        self.assertTrue(hasattr(app, '_led_status'))

    def test_effect_key_map(self):
        """Verify all UI labels map to valid effect keys."""
        app = self._create_app()
        labels = [
            "Trance Scope", "Neon Equalizer", "Psychedelic Plasma",
            "3D Cyber Tunnel", "Bars", "Circles", "Particles",
            "Wave", "Spectrum",
        ]
        for label in labels:
            app.selected_effect.set(label)
            key = app._get_effect_key()
            self.assertIsNotNone(key)
            self.assertIsInstance(key, str)

    def test_get_resolution(self):
        app = self._create_app()
        app.resolution.set("1080p")
        self.assertEqual(app._get_resolution(), (1920, 1080))
        app.resolution.set("1440p")
        self.assertEqual(app._get_resolution(), (2560, 1440))
        app.resolution.set("4K")
        self.assertEqual(app._get_resolution(), (3840, 2160))


# ══════════════════════════════════════════════════════════════════════
# Social icon visibility tests (unchanged)
# ══════════════════════════════════════════════════════════════════════

@unittest.skipUnless(_has_display(), "No display server available")
class TestSocialIconVisibility(unittest.TestCase):
    """Verify the footer social icons are legible (high contrast on dark bg)."""

    FOOTER_BG = (10, 10, 18)  # #0a0a12

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def _assets_dir(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, "assets")

    def _icon_stats(self, name):
        from PIL import Image
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
        self.assertGreater(dist, 60,
                           "LinkedIn icon too close to footer bg (unreadable)")

    def test_website_icon_visible(self):
        avg, dist = self._icon_stats("website.png")
        self.assertGreater(dist, 60,
                           "Website icon too close to footer bg (unreadable)")

    def test_hover_icons_visible(self):
        for name in ("linkedin_hover.png", "website_hover.png"):
            avg, dist = self._icon_stats(name)
            self.assertGreater(dist, 60,
                               f"{name} too close to footer bg (unreadable)")


# ══════════════════════════════════════════════════════════════════════
# Old export popover must NOT exist (was replaced by integrated progress)
# ══════════════════════════════════════════════════════════════════════

@unittest.skipUnless(_has_display(), "No display server available")
class TestOldExportPopoverRemoved(unittest.TestCase):
    """Verify old popover widgets are gone; replaced by ExportTab progress."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def _create_app(self):
        from ui.main_window import MainWindow
        return MainWindow(self.root)

    def test_old_export_popover_not_in_mainwindow(self):
        app = self._create_app()
        self.assertFalse(hasattr(app, '_export_popover'),
                         "Old _export_popover should not exist")
        self.assertFalse(hasattr(app, '_export_popover_inner'),
                         "Old _export_popover_inner should not exist")
        self.assertFalse(hasattr(app, '_export_popover_label'),
                         "Old _export_popover_label should not exist")
        self.assertFalse(hasattr(app, '_export_canvas'),
                         "Old _export_canvas should not exist")
        self.assertFalse(hasattr(app, '_export_popover_pct'),
                         "Old _export_popover_pct should not exist")

    def test_old_btn_toggle_popover_not_in_mainwindow(self):
        app = self._create_app()
        self.assertFalse(hasattr(app, 'btn_toggle_popover'),
                         "Old btn_toggle_popover should not exist")

    def test_old_export_progress_bar_not_in_mainwindow(self):
        app = self._create_app()
        self.assertFalse(hasattr(app, '_export_progress_container'),
                         "Old _export_progress_container should not exist")
        self.assertFalse(hasattr(app, '_export_progress_bar'),
                         "Old _export_progress_bar should not exist")


if __name__ == '__main__':
    unittest.main()
