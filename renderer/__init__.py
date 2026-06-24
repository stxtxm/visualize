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

# Importer CV2Renderer conditionnellement (nécessite cv2)
try:
    from renderer.cv2_renderer import CV2Renderer
    _has_cv2 = True
except ImportError:
    CV2Renderer = None
    _has_cv2 = False

__all__ = []
if _has_pygame:
    __all__.append('PygameRenderer')
if _has_cv2:
    __all__.append('CV2Renderer')
