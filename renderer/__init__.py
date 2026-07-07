"""
Renderer module for psychedelic visualizer.
Contains base renderer and specific implementations.
"""

# Importer PygameRenderer conditionnellement
try:
    from renderer.pygame_renderer import PygameRenderer
    _has_pygame = True
except ImportError:
    PygameRenderer = None
    _has_pygame = False

__all__ = []
if _has_pygame:
    __all__.append('PygameRenderer')
