"""
Renderer module for psychedelic visualizer.
Contains base renderer and specific implementations.
"""

from renderer.cv2_renderer import CV2Renderer
from renderer.pygame_renderer import PygameRenderer

__all__ = ['CV2Renderer', 'PygameRenderer']
