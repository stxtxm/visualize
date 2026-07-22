"""Tests for the shared logo overlay used by preview and export."""

import os
import sys
import tempfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _logo_file(color=(255, 0, 0, 255), size=(10, 10)):
    handle = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    handle.close()
    Image.new("RGBA", size, color).save(handle.name)
    return handle.name


def test_logo_overlay_custom_position_and_scale():
    from effects.logo_overlay import LogoOverlay

    path = _logo_file()
    try:
        overlay = LogoOverlay(
            100, 60, image_path=path, position="custom",
            x=1.0, y=1.0, scale=0.2,
        )
        frame = np.zeros((60, 100, 3), dtype=np.uint8)
        overlay.apply(frame)

        # The 20x20 logo is anchored to the bottom-right corner.
        assert tuple(frame[59, 99]) == (255, 0, 0)
        assert tuple(frame[40, 80]) == (255, 0, 0)
        assert tuple(frame[39, 79]) == (0, 0, 0)
    finally:
        os.unlink(path)


def test_effect_manager_applies_logo_to_rendered_frame():
    from effects.manager import EffectManager

    path = _logo_file(color=(0, 255, 0, 255), size=(8, 8))

    class Renderer:
        width = 80
        height = 50

    try:
        manager = EffectManager(
            renderer=Renderer(), effect_type="bars", logo_image=path,
            logo_position="top-left", logo_scale=0.2,
        )
        manager.init()
        frame = manager.render_to_array()
        assert tuple(frame[0, 0]) == (0, 255, 0)
        assert tuple(frame[7, 12]) == (0, 255, 0)
        manager.cleanup()
    finally:
        os.unlink(path)
