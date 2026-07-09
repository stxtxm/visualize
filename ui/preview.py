"""
Optimised preview component for Tkinter UI.
- PhotoImage reference kept to avoid GC
- Click on empty preview opens file selection dialog
- Clean resize handling
"""

import tkinter as tk
from PIL import Image, ImageTk


class PreviewFrame(tk.Canvas):
    """
    Canvas for displaying real-time video preview.
    Clicking on the empty preview triggers a callback to open a file dialog.
    """

    def __init__(self, master, on_click_empty=None, **kwargs):
        super().__init__(master, **kwargs)
        self._image_ref = None
        self._current_img_id = None
        self._has_image = False
        self._on_click_empty = on_click_empty
        self.bg_color = "#05050a"
        self.configure(bg=self.bg_color, highlightthickness=0)

        self.bind("<Configure>", self._on_resize)
        self.bind("<Button-1>", self._on_click)

    def _on_resize(self, event):
        """Recenter image when canvas is resized."""
        if self._current_img_id is not None:
            self.coords(
                self._current_img_id,
                self.winfo_width() // 2,
                self.winfo_height() // 2,
            )

    def _on_click(self, event):
        """Handle click: if empty, trigger the callback to open file dialog."""
        if not self._has_image and self._on_click_empty:
            self._on_click_empty()

    def update_image(self, image):
        """
        Update the displayed image.
        Args:
            image: PIL ImageTk.PhotoImage to display
        """
        self._has_image = True
        self._image_ref = image
        if self._current_img_id is None:
            self._current_img_id = self.create_image(
                self.winfo_width() // 2,
                self.winfo_height() // 2,
                anchor=tk.CENTER,
                image=image,
            )
        else:
            self.itemconfig(self._current_img_id, image=image)

    def clear(self):
        """Clear the preview."""
        if self._current_img_id:
            self.delete(self._current_img_id)
            self._current_img_id = None
        self._image_ref = None
        self._has_image = False
        self.configure(bg=self.bg_color)

    def get_display_size(self):
        """Return the current display size in pixels."""
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10:
            w = max(w, 320)
            h = max(h, 240)
        return (w, h)

    def has_image(self):
        """Return True if an image is currently displayed."""
        return self._has_image