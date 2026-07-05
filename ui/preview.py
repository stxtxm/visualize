"""
Preview component for Tkinter UI.
"""

import tkinter as tk
from PIL import Image, ImageTk


class PreviewFrame(tk.Canvas):
    """
    Frame for displaying real-time video preview.
    """

    def __init__(self, master, width=800, height=450, **kwargs):
        """
        Initialize the preview frame.
        
        Args:
            master: Parent widget
            width: Preview width in pixels
            height: Preview height in pixels
            **kwargs: Additional Canvas arguments
        """
        super().__init__(master, width=width, height=height, **kwargs)
        self.width = width
        self.height = height
        self.current_image = None
        self.bg_color = "#000000"
        self.configure(bg=self.bg_color, highlightthickness=0)

    def update_image(self, image):
        """
        Update the displayed image.
        
        Args:
            image: PIL ImageTk.PhotoImage to display
        """
        # Garder une référence pour éviter que le garbage collector ne supprime l'image
        self._image_ref = image
        
        if self.current_image is None:
            self.current_image = self.create_image(
                self.width // 2,
                self.height // 2,
                anchor=tk.CENTER,
                image=image
            )
        else:
            self.itemconfig(self.current_image, image=image)

    def clear(self):
        """Clear the preview."""
        if self.current_image:
            self.delete(self.current_image)
            self.current_image = None
        self.configure(bg=self.bg_color)
