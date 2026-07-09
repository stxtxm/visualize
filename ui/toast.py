"""
Toast notification system for the psychedelic visualizer.
Shows temporary overlay messages that auto-dismiss after a set duration.
"""

import tkinter as tk
import time


class ToastManager:
    """
    Manages overlay toast notifications on a root window.
    Toasts appear at the bottom-center of the window with a slide-up animation.
    """

    BG = "#1a1a2e"
    FG = "#e2e2ee"
    NEON_CYAN = "#00e5ff"
    NEON_GREEN = "#39ff14"
    NEON_RED = "#ff3b3b"
    NEON_AMBER = "#ffaa00"

    def __init__(self, root):
        self.root = root
        self._toast_frame = None
        self._toast_label = None
        self._toast_after_id = None

    def show(self, message, duration=2.0, style="info"):
        """
        Show a toast notification.

        Args:
            message: Text to display.
            duration: Seconds before auto-dismiss.
            style: "info", "success", "error", "warning"
        """
        # Cancel any existing toast
        self.hide()

        colour = self.NEON_CYAN
        if style == "success":
            colour = self.NEON_GREEN
        elif style == "error":
            colour = self.NEON_RED
        elif style == "warning":
            colour = self.NEON_AMBER

        self._toast_frame = tk.Frame(
            self.root, bg=colour, bd=0,
            highlightthickness=1, highlightbackground=colour,
        )
        self._toast_frame.place(
            relx=0.5, rely=0.92, anchor=tk.CENTER,
            width=min(500, self.root.winfo_width() - 40),
        )
        self._toast_frame.lift()

        inner = tk.Frame(self._toast_frame, bg=self.BG, padx=16, pady=8)
        inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        icon_map = {"info": "●", "success": "✓", "error": "✕", "warning": "⚠"}
        icon = icon_map.get(style, "●")

        icon_lbl = tk.Label(inner, text=icon, font=('Helvetica', 10, 'bold'),
                            fg=colour, bg=self.BG)
        icon_lbl.pack(side=tk.LEFT, padx=(0, 8))

        self._toast_label = tk.Label(
            inner, text=message, font=('Helvetica', 9),
            fg=self.FG, bg=self.BG, anchor=tk.W,
        )
        self._toast_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Auto-dismiss
        self._toast_after_id = self.root.after(
            int(duration * 1000), self.hide
        )

    def hide(self):
        """Hide the current toast immediately."""
        if self._toast_after_id:
            try:
                self.root.after_cancel(self._toast_after_id)
            except Exception:
                pass
            self._toast_after_id = None
        if self._toast_frame:
            try:
                self._toast_frame.destroy()
            except Exception:
                pass
            self._toast_frame = None
            self._toast_label = None