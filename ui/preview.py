"""
Preview component for Tkinter UI.
"""

import tkinter as tk
from PIL import Image, ImageTk


class PreviewFrame(tk.Canvas):
    """
    Frame for displaying real-time video preview.
    Se redimensionne automatiquement avec la fenêtre.
    """

    def __init__(self, master, **kwargs):
        """Initialize the preview frame."""
        super().__init__(master, **kwargs)
        self.current_image = None
        self.bg_color = "#000000"
        self.configure(bg=self.bg_color, highlightthickness=0)
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        """Recentrer l'image quand le canvas est redimensionné."""
        if self.current_image is not None:
            self.coords(
                self.current_image,
                self.winfo_width() // 2,
                self.winfo_height() // 2
            )

    def update_image(self, image):
        """
        Update the displayed image.
        
        Args:
            image: PIL ImageTk.PhotoImage to display
        """
        self._image_ref = image

        if self.current_image is None:
            self.current_image = self.create_image(
                self.winfo_width() // 2,
                self.winfo_height() // 2,
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
