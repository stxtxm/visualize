"""
Custom lightweight tab panel widget for Tkinter.
No external dependencies, minimal overhead.
Refined with active tab indicator, smooth hover, and better spacing.
"""

import tkinter as tk


class TabPanel(tk.Frame):
    """
    A lightweight tabbed panel with neon-styled tabs.

    Usage::

        panel = TabPanel(parent)
        panel.add_tab("FICHIER", file_frame)
        panel.add_tab("EFFETS", effects_frame)
        panel.pack(fill=tk.BOTH, expand=True)
        panel.select(0)
    """

    BG_DARK = "#09090d"
    BG_PANEL = "#12121d"
    BG_CARD = "#1b1b2a"
    FG_LIGHT = "#e2e2ee"
    FG_MUTED = "#85859e"
    NEON_CYAN = "#00e5ff"
    NEON_PINK = "#ff007f"
    TAB_INACTIVE_BG = "#1a1a2e"
    TAB_ACTIVE_BG = "#12121d"
    TAB_HOVER_BG = "#252540"
    TAB_ACTIVE_GLOW = "#00e5ff"
    BORDER = "#2a2a3e"

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg=self.BG_PANEL)

        self._tabs = []          # list of (label_text, content_frame)
        self._tab_buttons = []   # list of tk.Button widgets
        self._active_index = tk.IntVar(value=-1)
        self._glow_lines = []    # list of Frame widgets (active tab indicators)

        # Tab bar at the top
        self._tab_bar = tk.Frame(self, bg=self.BG_PANEL, height=34)
        self._tab_bar.pack(fill=tk.X, side=tk.TOP)
        self._tab_bar.pack_propagate(False)

        # Thin neon divider below tab bar
        self._divider = tk.Frame(self, bg="#1c1c30", height=1)
        self._divider.pack(fill=tk.X, side=tk.TOP)

        # Content area
        self._content_area = tk.Frame(self, bg=self.BG_PANEL)
        self._content_area.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

    def add_tab(self, label, content_frame=None):
        """Add a tab with the given label and optional pre-created content frame.

        If content_frame is None, one will be created automatically.
        Returns the content frame.
        """
        if content_frame is None:
            content_frame = tk.Frame(self._content_area, bg=self.BG_PANEL)

        index = len(self._tabs)
        self._tabs.append((label, content_frame))
        content_frame.configure(bg=self.BG_PANEL)

        # Create tab button
        btn = tk.Button(
            self._tab_bar,
            text=label.upper(),
            command=lambda i=index: self.select(i),
            bg=self.TAB_INACTIVE_BG,
            fg=self.FG_MUTED,
            activebackground=self.TAB_HOVER_BG,
            activeforeground=self.FG_LIGHT,
            bd=0,
            padx=12,
            pady=5,
            font=('Helvetica', 7, 'bold'),
            cursor="hand2",
            relief="flat",
        )
        btn.pack(side=tk.LEFT, padx=(0, 1), pady=4)
        self._tab_buttons.append(btn)

        # Glow line (active indicator) — hidden by default
        glow = tk.Frame(self._tab_bar, bg=self.TAB_ACTIVE_GLOW, height=2)
        self._glow_lines.append(glow)

        # Hover effects
        self._add_hover(btn)

        # If this is the first tab, select it
        if index == 0:
            self.select(0)
        else:
            content_frame.place_forget()

        return content_frame

    def select(self, index):
        """Programmatically select a tab by index."""
        if index < 0 or index >= len(self._tabs):
            return
        self._active_index.set(index)
        self._update_visibility()
        self.update_idletasks()

    def _update_visibility(self):
        active = self._active_index.get()
        for i, (_, frame) in enumerate(self._tabs):
            if i == active:
                frame.place(in_=self._content_area, relx=0, rely=0,
                            relwidth=1, relheight=1)
                frame.lift()
            else:
                frame.place_forget()

        # Update button styles and glow lines
        for i, btn in enumerate(self._tab_buttons):
            glow = self._glow_lines[i]
            if i == active:
                btn.configure(
                    bg=self.TAB_ACTIVE_BG,
                    fg=self.NEON_CYAN,
                )
                # Position glow line below the button
                glow.place(in_=self._tab_bar, relx=0, rely=1.0,
                           width=btn.winfo_width(), height=2)
                glow.lift()
            else:
                btn.configure(
                    bg=self.TAB_INACTIVE_BG,
                    fg=self.FG_MUTED,
                )
                glow.place_forget()

    def _add_hover(self, widget):
        widget.bind("<Enter>", lambda e: self._on_tab_enter(widget))
        widget.bind("<Leave>", lambda e: self._on_tab_leave(widget))

    def _on_tab_enter(self, widget):
        if widget.cget('fg') != self.NEON_CYAN:
            widget.configure(bg=self.TAB_HOVER_BG)

    def _on_tab_leave(self, widget):
        if widget.cget('fg') != self.NEON_CYAN:
            widget.configure(bg=self.TAB_INACTIVE_BG)