"""
OpenCV-based renderer for video export.
"""

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
    HAS_NUMPY = True
except ImportError:
    HAS_CV2 = False
    HAS_NUMPY = False


class CV2Renderer:
    """
    Renderer using OpenCV for video export.
    Generates frames as numpy arrays suitable for FFmpeg encoding.
    """

    def __init__(self, width=1920, height=1080, fps=60):
        """
        Initialize the CV2 renderer.
        
        Args:
            width: Frame width in pixels
            height: Frame height in pixels
            fps: Target frames per second
        """
        self.width = width
        self.height = height
        self.fps = fps
        self._initialized = False

    def init(self):
        """Initialize the renderer."""
        self._initialized = True

    def create_frame(self):
        """
        Create a new empty frame.
        
        Returns:
            numpy.ndarray: Black frame of dimensions (height, width, 3)
        """
        return np.zeros((self.height, self.width, 3), dtype=np.uint8)

    def cleanup(self):
        """Clean up resources."""
        self._initialized = False

    @property
    def is_initialized(self):
        """Check if renderer is initialized."""
        return self._initialized

    def get_frame_size(self):
        """Get the frame dimensions."""
        return (self.width, self.height)
