"""
Module pour afficher les logs dans la GUI Tkinter.
Capture les logs de stdout/stderr et les affiche dans une fenêtre.
"""

import sys
import os
import threading
import queue
import tkinter as tk
from tkinter import scrolledtext, messagebox
import io


class TeeStream:
    """File-like object qui écrit vers deux streams"""
    
    def __init__(self, stream1, stream2):
        self.stream1 = stream1
        self.stream2 = stream2
    
    def write(self, data):
        self.stream1.write(data)
        self.stream2.write(data)
        self.flush()
        return len(data)
    
    def flush(self):
        self.stream1.flush()
        if hasattr(self.stream2, 'flush'):
            self.stream2.flush()
    
    def __getattr__(self, attr):
        return getattr(self.stream1, attr)


class LogCapture:
    """
    Capture les logs et les stocke dans une queue pour affichage dans Tkinter.
    Utilise un file-like wrapper qui écrit à la fois vers le vrai stdout et vers notre buffer.
    """
    
    def __init__(self):
        self.log_queue = queue.Queue()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.capturing = False
        self.stdout_buffer = None
        self.stderr_buffer = None
    
    def start_capture(self):
        """Commence à capturer stdout et stderr"""
        if self.capturing:
            return
        self.capturing = True
        
        # Créer des buffers pour capturer
        self.stdout_buffer = io.StringIO()
        self.stderr_buffer = io.StringIO()
        
        # Créer des wrappers qui écrivent à la fois vers le vrai stdout et vers notre buffer
        sys.stdout = TeeStream(self.original_stdout, self.stdout_buffer)
        sys.stderr = TeeStream(self.original_stderr, self.stderr_buffer)
        
        # Lancer le thread de capture
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
        # Log initial
        self.log_queue.put(("INFO", "=== Début de la capture des logs ==="))
    
    def _capture_loop(self):
        """Boucle de capture des logs"""
        import time
        while self.capturing:
            try:
                # Lire depuis stdout buffer
                if self.stdout_buffer:
                    self.stdout_buffer.seek(0)
                    stdout_data = self.stdout_buffer.read()
                    if stdout_data:
                        # Mettre chaque ligne séparément
                        for line in stdout_data.split('\n'):
                            if line.strip():
                                self.log_queue.put(("STDOUT", line))
                        self.stdout_buffer.seek(0)
                        self.stdout_buffer.truncate()
                
                # Lire depuis stderr buffer
                if self.stderr_buffer:
                    self.stderr_buffer.seek(0)
                    stderr_data = self.stderr_buffer.read()
                    if stderr_data:
                        for line in stderr_data.split('\n'):
                            if line.strip():
                                self.log_queue.put(("STDERR", line))
                        self.stderr_buffer.seek(0)
                        self.stderr_buffer.truncate()
                
                time.sleep(0.05)
            except Exception as e:
                self.log_queue.put(("ERROR", f"Erreur de capture: {e}"))
                import traceback
                self.log_queue.put(("ERROR", traceback.format_exc()))
                break
    
    def stop_capture(self):
        """Arrête la capture et restaure stdout/stderr"""
        self.capturing = False
        if hasattr(self, 'capture_thread'):
            self.capture_thread.join(timeout=1)
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        self.log_queue.put(("INFO", "=== Fin de la capture des logs ==="))
    
    def get_logs(self):
        """Récupère tous les logs de la queue"""
        logs = []
        while not self.log_queue.empty():
            try:
                source, message = self.log_queue.get_nowait()
                logs.append(f"[{source}] {message}")
            except queue.Empty:
                break
        return '\n'.join(logs)


class LogWindow:
    """Fenêtre Tkinter pour afficher les logs"""
    
    def __init__(self, root, log_capture=None):
        self.root = root
        self.log_capture = log_capture or get_log_capture()
        self.log_text = None
        self.setup_ui()
        self.update_logs()
    
    def setup_ui(self):
        """Configure l'interface"""
        # Créer un frame pour les logs
        log_frame = tk.LabelFrame(self.root, text="Logs", padx=5, pady=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Zone de texte avec scroll
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            wrap=tk.WORD, 
            width=80, 
            height=20,
            state=tk.DISABLED,
            font=('Monospace', 10)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Boutons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        btn_clear = tk.Button(btn_frame, text="Effacer", command=self.clear_logs)
        btn_clear.pack(side=tk.LEFT, padx=5)
        
        btn_copy = tk.Button(btn_frame, text="Copier", command=self.copy_logs)
        btn_copy.pack(side=tk.LEFT, padx=5)
        
        btn_save = tk.Button(btn_frame, text="Sauvegarder", command=self.save_logs)
        btn_save.pack(side=tk.LEFT, padx=5)
        
        # Ajouter un message initial
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, "Attente des logs...\n")
        self.log_text.config(state=tk.DISABLED)
    
    def update_logs(self):
        """Met à jour l'affichage des logs"""
        try:
            logs = self.log_capture.get_logs()
            if logs:
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, logs + '\n')
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)
        except Exception as e:
            print(f"Erreur update logs: {e}")
        
        # Réplanifier la mise à jour
        self.root.after(200, self.update_logs)
    
    def clear_logs(self):
        """Efface les logs"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def copy_logs(self):
        """Copie les logs dans le presse-papiers"""
        try:
            logs = self.log_text.get(1.0, tk.END)
            self.root.clipboard_clear()
            self.root.clipboard_append(logs)
            # Afficher un message
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, "\n[✓ Logs copiés dans le presse-papiers]\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        except Exception as e:
            print(f"Erreur copy: {e}")
    
    def save_logs(self):
        """Sauvegarde les logs dans un fichier"""
        try:
            logs = self.log_text.get(1.0, tk.END)
            filename = f"/tmp/visualize_logs_{os.getpid()}.log"
            with open(filename, 'w') as f:
                f.write(logs)
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"\n[✓ Logs sauvegardés dans {filename}]\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        except Exception as e:
            print(f"Erreur save: {e}")


# Singleton pour la capture de logs
_log_capture = None


def get_log_capture():
    """Récupère ou crée l'instance de LogCapture"""
    global _log_capture
    if _log_capture is None:
        _log_capture = LogCapture()
    return _log_capture


def start_log_capture():
    """Démarre la capture des logs"""
    capture = get_log_capture()
    capture.start_capture()
    return capture


def stop_log_capture():
    """Arrête la capture des logs"""
    capture = get_log_capture()
    if capture:
        capture.stop_capture()


def show_log_window(root=None):
    """Affiche la fenêtre des logs"""
    if root is None:
        root = tk.Tk()
        root.title("Logs - Visualisateur Psychédélique")
        root.geometry("800x600")
    
    log_window = LogWindow(root, get_log_capture())
    return root


def log_message(message, level="INFO"):
    """Ajoute un message manuellement aux logs"""
    capture = get_log_capture()
    if capture:
        capture.log_queue.put((level, message))
