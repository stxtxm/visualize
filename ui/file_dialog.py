"""
Custom file selection / save dialog for the psychedelic visualizer GUI.

Replaces tkinter.filedialog which, on Linux, renders with Tk's themed widgets
(the old 'default' Motif theme) producing unreadable text and an awkward filename
entry. This dialog uses the application's dark/neon theme, large readable fonts,
clear navigation and a comfortable text entry, and behaves identically everywhere
(Fedora, AppImage sandbox, ...).
"""

import os
import tkinter as tk
from tkinter import messagebox


class FileDialog(tk.Toplevel):
    """A reusable, themeable open/save file dialog.

    Use the classmethod ``show`` which is modal and returns the chosen path
    (str) or an empty string if cancelled.
    """

    BG_DARK = "#09090d"
    BG_PANEL = "#12121d"
    BG_CARD = "#1b1b2a"
    FG_LIGHT = "#e2e2ee"
    FG_MUTED = "#85859e"
    NEON_CYAN = "#00e5ff"
    BORDER = "#3a3a55"

    @classmethod
    def show(cls, parent, mode="open", title="Sélectionner un fichier",
             initial_dir=None, filetypes=None, defaultextension=""):
        """Show the dialog modally.

        Args:
            parent: parent Tk window.
            mode: "open" or "save".
            title: window title.
            initial_dir: starting directory (str) or None for user home.
            filetypes: list of (label, pattern) tuples, e.g.
                [("Fichiers audio", "*.mp3 *.wav"), ("Tous les fichiers", "*.*")].
            defaultextension: extension appended in save mode when missing (".mp4").

        Returns:
            The absolute chosen path (str) or "" if cancelled.
        """
        if filetypes is None:
            filetypes = [("Tous les fichiers", "*.*")]
        if initial_dir is None or not os.path.isdir(initial_dir):
            initial_dir = os.path.expanduser("~")

        dlg = cls(parent, mode=mode, title=title, initial_dir=initial_dir,
                  filetypes=filetypes, defaultextension=defaultextension)
        dlg.grab_set()
        dlg.wait_window()
        return dlg._result

    def __init__(self, parent, mode="open", title="Sélectionner un fichier",
                 initial_dir=None, filetypes=None, defaultextension=""):
        super().__init__(parent)
        self.transient(parent)
        self.title(title)
        self.mode = mode
        self.filetypes = filetypes or [("Tous les fichiers", "*.*")]
        self.defaultextension = defaultextension
        self._result = ""
        self._current_dir = os.path.abspath(initial_dir or os.path.expanduser("~"))
        self._active_filter = tk.StringVar(value=self.filetypes[0][0])

        self.configure(bg=self.BG_DARK)
        self.minsize(640, 480)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        self._build_ui()
        self._path_var = tk.StringVar(value=self._current_dir)
        self.entry_path.configure(textvariable=self._path_var)
        self._populate()
        self._center(parent)

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        # Navigation bar
        nav = tk.Frame(self, bg=self.BG_PANEL, padx=10, pady=8)
        nav.pack(fill=tk.X)

        btn_home = tk.Button(nav, text="🏠", command=self._go_home,
                             bg="#252538", fg=self.FG_LIGHT, activebackground="#35354e",
                             activeforeground=self.FG_LIGHT, bd=0, padx=8, pady=3,
                             font=('Helvetica', 11), cursor="hand2")
        btn_home.pack(side=tk.LEFT, padx=(0, 4))

        btn_up = tk.Button(nav, text="⬆", command=self._go_up,
                           bg="#252538", fg=self.FG_LIGHT, activebackground="#35354e",
                           activeforeground=self.FG_LIGHT, bd=0, padx=8, pady=3,
                           font=('Helvetica', 11), cursor="hand2")
        btn_up.pack(side=tk.LEFT, padx=(0, 6))

        self.entry_path = tk.Entry(nav, bg=self.BG_CARD, fg=self.FG_LIGHT,
                                   insertbackground=self.FG_LIGHT, bd=0,
                                   font=('Helvetica', 11),
                                   highlightthickness=1, highlightbackground=self.BORDER,
                                   highlightcolor=self.NEON_CYAN)
        self.entry_path.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry_path.bind("<Return>", lambda e: self._navigate_to(self.entry_path.get()))

        # File list
        list_frame = tk.Frame(self, bg=self.BG_DARK, padx=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 8))

        list_inner = tk.Frame(list_frame, bg=self.BG_PANEL, relief="solid", bd=1)
        list_inner.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(
            list_inner, bg=self.BG_CARD, fg=self.FG_LIGHT,
            selectbackground=self.NEON_CYAN, selectforeground="#000000",
            font=('Helvetica', 11), bd=0, highlightthickness=0,
            activestyle="none"
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind("<Double-1>", self._on_item_activate)
        self.listbox.bind("<Return>", self._on_item_activate)

        scroll = tk.Scrollbar(list_frame, command=self.listbox.yview,
                              bg=self.BORDER, troughcolor=self.BG_PANEL,
                              activebackground=self.NEON_CYAN)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scroll.set)

        hint = tk.Label(self,
                        text="Double-cliquez sur un dossier pour l'ouvrir · Entrée pour valider",
                        font=('Helvetica', 8), fg=self.FG_MUTED, bg=self.BG_DARK)
        hint.pack(fill=tk.X, padx=10)

        # Filter + filename row
        bottom = tk.Frame(self, bg=self.BG_DARK, padx=10, pady=8)
        bottom.pack(fill=tk.X)

        tk.Label(bottom, text="Filtre :", font=('Helvetica', 9, 'bold'),
                 fg=self.FG_MUTED, bg=self.BG_DARK).pack(side=tk.LEFT, padx=(0, 4))

        filter_names = [ft[0] for ft in self.filetypes]
        filter_menu = tk.OptionMenu(bottom, self._active_filter, *filter_names,
                                    command=lambda _=None: self._populate())
        filter_menu.configure(bg="#252538", fg=self.FG_LIGHT, activebackground="#35354e",
                              activeforeground=self.FG_LIGHT, bd=0,
                              font=('Helvetica', 9), highlightthickness=0)
        filter_menu.pack(side=tk.LEFT, padx=(0, 10))

        if self.mode == "save":
            tk.Label(bottom, text="Nom :", font=('Helvetica', 9, 'bold'),
                     fg=self.FG_MUTED, bg=self.BG_DARK).pack(side=tk.LEFT, padx=(0, 4))
            self.entry_name = tk.Entry(bottom, bg=self.BG_CARD, fg=self.FG_LIGHT,
                                       insertbackground=self.FG_LIGHT, bd=0,
                                       font=('Helvetica', 11),
                                       highlightthickness=1, highlightbackground=self.BORDER,
                                       highlightcolor=self.NEON_CYAN)
            self.entry_name.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.entry_name.bind("<Return>", lambda e: self._on_confirm())

        # Buttons
        btn_row = tk.Frame(self, bg=self.BG_DARK, padx=10)
        btn_row.pack(fill=tk.X, pady=(0, 10))

        cancel_text = "Annuler"
        ok_text = "Ouvrir" if self.mode == "open" else "Enregistrer"

        btn_cancel = tk.Button(btn_row, text=cancel_text, command=self._on_cancel,
                               bg="#33334d", fg=self.FG_LIGHT, activebackground="#3a3a55",
                               activeforeground=self.FG_LIGHT, bd=0, padx=16, pady=6,
                               font=('Helvetica', 10, 'bold'), cursor="hand2")
        btn_cancel.pack(side=tk.RIGHT)

        btn_ok = tk.Button(btn_row, text=ok_text, command=self._on_confirm,
                           bg=self.NEON_CYAN, fg="#000000", activebackground="#7af0ff",
                           activeforeground="#000000", bd=0, padx=16, pady=6,
                           font=('Helvetica', 10, 'bold'), cursor="hand2")
        btn_ok.pack(side=tk.RIGHT, padx=(0, 8))

        self.bind("<Escape>", lambda e: self._on_cancel())
        if self.mode == "save":
            self.entry_name.focus_set()
        else:
            self.listbox.focus_set()

    # --------------------------------------------------------------- Logic
    def _center(self, parent):
        self.update_idletasks()
        w, h = 760, 520
        self.geometry(f"{w}x{h}")
        px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry(f"+{max(0, px)}+{max(0, py)}")

    def _patterns(self):
        label = self._active_filter.get()
        for name, pat in self.filetypes:
            if name == label:
                return [p.strip().lower() for p in pat.split() if p.strip()]
        return ["*.*"]

    def _populate(self):
        self.listbox.delete(0, tk.END)
        try:
            entries = os.listdir(self._current_dir)
        except (PermissionError, OSError) as e:
            messagebox.showerror("Erreur", f"Impossible d'accéder au dossier :\n{e}")
            self._current_dir = os.path.expanduser("~")
            self._path_var.set(self._current_dir)
            return

        dirs = []
        files = []
        patterns = self._patterns()
        for name in entries:
            full = os.path.join(self._current_dir, name)
            if os.path.isdir(full):
                dirs.append(name)
            else:
                low = name.lower()
                if any(low.endswith(pat.lstrip("*")) or pat == "*.*" for pat in patterns):
                    files.append(name)

        for d in sorted(dirs):
            self.listbox.insert(tk.END, f"📁  {d}")
        for f in sorted(files):
            self.listbox.insert(tk.END, f"🎵  {f}")

        self._path_var.set(self._current_dir)

    def _go_home(self):
        self._current_dir = os.path.expanduser("~")
        self._populate()

    def _go_up(self):
        parent = os.path.dirname(self._current_dir)
        if parent and parent != self._current_dir:
            self._current_dir = parent
            self._populate()

    def _navigate_to(self, path):
        path = os.path.expanduser(path.strip())
        if not path:
            return
        if os.path.isdir(path):
            self._current_dir = os.path.abspath(path)
            self._populate()
        elif os.path.isfile(path):
            if self.mode == "open":
                self._result = os.path.abspath(path)
                self.destroy()
            else:
                self._current_dir = os.path.dirname(os.path.abspath(path))
                self._populate()
                if hasattr(self, "entry_name"):
                    self.entry_name.delete(0, tk.END)
                    self.entry_name.insert(0, os.path.basename(path))
        else:
            messagebox.showerror("Dossier introuvable", f"Chemin invalide :\n{path}")

    def _on_item_activate(self, event=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        label = self.listbox.get(sel[0])
        name = label.split("  ", 1)[1] if "  " in label else label
        full = os.path.join(self._current_dir, name)
        if os.path.isdir(full):
            self._current_dir = full
            self._populate()
        else:
            if self.mode == "open":
                self._result = os.path.abspath(full)
                self.destroy()
            else:
                if hasattr(self, "entry_name"):
                    self.entry_name.delete(0, tk.END)
                    self.entry_name.insert(0, name)
                self._on_confirm()

    def _on_confirm(self):
        if self.mode == "open":
            sel = self.listbox.curselection()
            if not sel:
                return
            label = self.listbox.get(sel[0])
            name = label.split("  ", 1)[1] if "  " in label else label
            full = os.path.join(self._current_dir, name)
            if os.path.isfile(full):
                self._result = os.path.abspath(full)
                self.destroy()
            else:
                self._current_dir = full
                self._populate()
            return

        # save mode
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showerror("Nom manquant", "Veuillez saisir un nom de fichier.")
            return
        if self.defaultextension and not name.lower().endswith(self.defaultextension.lower()):
            name += self.defaultextension
        full = os.path.join(self._current_dir, name)
        if os.path.exists(full):
            ok = messagebox.askyesno("Écraser ?",
                                     f"Le fichier existe déjà :\n{os.path.basename(full)}\n\nVoulez-vous le remplacer ?")
            if not ok:
                return
        self._result = os.path.abspath(full)
        self.destroy()

    def _on_cancel(self):
        self._result = ""
        self.destroy()
