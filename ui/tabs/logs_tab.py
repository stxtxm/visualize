"""
Logs tab for Visualize.
Integrated log viewer (no separate window needed).
"""

import tkinter as tk
from tkinter import scrolledtext
import os
import sys
import queue

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class LogsTab(tk.Frame):
    """Tab displaying captured log messages with color-coded levels."""

    BG_PANEL = "#12121d"
    BG_CARD = "#1b1b2a"
    FG_LIGHT = "#e2e2ee"
    FG_MUTED = "#85859e"
    NEON_CYAN = "#00e5ff"
    NEON_GREEN = "#39ff14"
    NEON_PINK = "#ff007f"
    NEON_AMBER = "#ffaa00"

    COLORS = {
        "INFO": "#00e5ff",
        "STDOUT": "#e2e2ee",
        "STDERR": "#ffaa00",
        "ERROR": "#ff3b3b",
        "WARNING": "#ffaa00",
        "DEBUG": "#85859e",
    }

    def __init__(self, master, log_capture=None):
        super().__init__(master)
        self.configure(bg=self.BG_PANEL)
        self._log_capture = log_capture
        self._log_queue = queue.Queue()
        self._build_ui()
        self._poll_logs()

    def _build_ui(self):
        title = tk.Label(self, text="LOGS", font=('Helvetica', 9, 'bold'),
                         fg=self.NEON_CYAN, bg=self.BG_PANEL)
        title.pack(anchor=tk.W, pady=(10, 8), padx=12)

        # Text area with scroll
        text_frame = tk.Frame(self, bg=self.BG_PANEL, relief="solid", bd=1,
                              highlightbackground="#2a2a3e", highlightthickness=1)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))

        self._log_text = scrolledtext.ScrolledText(
            text_frame, wrap=tk.WORD, width=40, height=12,
            state=tk.DISABLED,
            font=('Courier', 8),
            bg="#0a0a12", fg=self.FG_LIGHT,
            insertbackground=self.FG_LIGHT,
            bd=0, highlightthickness=0,
        )
        self._log_text.pack(fill=tk.BOTH, expand=True)

        # Configure tags for colors
        for level, color in self.COLORS.items():
            self._log_text.tag_configure(level, foreground=color)
        self._log_text.tag_configure("BOLD", font=('Courier', 8, 'bold'))

        # Button row
        btn_frame = tk.Frame(self, bg=self.BG_PANEL)
        btn_frame.pack(fill=tk.X, padx=12, pady=(0, 10))

        self.btn_clear = tk.Button(
            btn_frame, text="🗑 EFFACER",
            command=self._clear_logs,
            bg="#252538", fg=self.FG_LIGHT,
            activebackground="#35354e", activeforeground=self.FG_LIGHT,
            bd=0, padx=8, pady=3, font=('Helvetica', 8, 'bold'),
            cursor="hand2",
        )
        self.btn_clear.pack(side=tk.LEFT, padx=(0, 6))
        self._add_hover(self.btn_clear, "#35354e", "#252538")

        self.btn_copy = tk.Button(
            btn_frame, text="📋 COPIER",
            command=self._copy_logs,
            bg="#252538", fg=self.FG_LIGHT,
            activebackground="#35354e", activeforeground=self.FG_LIGHT,
            bd=0, padx=8, pady=3, font=('Helvetica', 8, 'bold'),
            cursor="hand2",
        )
        self.btn_copy.pack(side=tk.LEFT, padx=(0, 6))
        self._add_hover(self.btn_copy, "#35354e", "#252538")

    def add_message(self, message, level="INFO"):
        """Add a message to the log queue from external threads."""
        self._log_queue.put((level, message))

    def _clear_logs(self):
        self._log_text.config(state=tk.NORMAL)
        self._log_text.delete(1.0, tk.END)
        self._log_text.config(state=tk.DISABLED)

    def _copy_logs(self):
        try:
            logs = self._log_text.get(1.0, tk.END)
            self.clipboard_clear()
            self.clipboard_append(logs)
            self.add_message("Logs copiés dans le presse-papiers", "INFO")
        except Exception as e:
            print(f"Copy error: {e}")

    def _poll_logs(self):
        """Poll for new log messages."""
        # Check external log capture
        if self._log_capture:
            try:
                logs = self._log_capture.get_logs()
                if logs:
                    for line in logs.split('\n'):
                        if line.strip():
                            self._insert_log(line)
            except Exception:
                pass

        # Check internal queue
        try:
            while True:
                level, msg = self._log_queue.get_nowait()
                tag = level if level in self.COLORS else "INFO"
                self._insert_log(f"[{level}] {msg}", tag)
        except queue.Empty:
            pass

        self.after(200, self._poll_logs)

    def _insert_log(self, text, tag="INFO"):
        """Insert a log line with color tagging."""
        try:
            self._log_text.config(state=tk.NORMAL)
            self._log_text.insert(tk.END, text + '\n', tag)
            self._log_text.see(tk.END)
            # Limit log size to prevent memory issues
            if int(self._log_text.index('end-1c').split('.')[0]) > 500:
                self._log_text.delete(1.0, '100.0')
            self._log_text.config(state=tk.DISABLED)
        except Exception:
            pass

    def _add_hover(self, widget, hover_bg, normal_bg):
        widget.bind("<Enter>", lambda e: widget.configure(bg=hover_bg))
        widget.bind("<Leave>", lambda e: widget.configure(bg=normal_bg))


def get_global_logs_tab():
    """Global reference for easy access."""
    return getattr(get_global_logs_tab, '_instance', None)


def set_global_logs_tab(tab):
    """Set the global logs tab reference."""
    get_global_logs_tab._instance = tab
