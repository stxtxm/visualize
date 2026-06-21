"""
Module pour afficher les logs dans la GUI Tkinter.
Capture les logs de stdout/stderr et les affiche dans une fenêtre.
"""

import sys
import os
import threading
import queue
import tkinter as tk
from tkinter import scrolledtext
import io


class LogCapture:
    """Capture les logs et les stocke dans une queue pour affichage dans Tkinter"""
    
    def __init__(self):
        self.log_queue = queue.Queue()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.capturing = False
    
    def start_capture(self):
        """Commence à capturer stdout et stderr"""
        if self.capturing:
            return
        self.capturing = True
        
        # Rediriger stdout
        sys.stdout = io.TextIOWrapper(
            io.BytesIO(), 
            encoding='utf-8',
            errors='ignore'
        )
        # Rediriger stderr
        sys.stderr = io.TextIOWrapper(
            io.BytesIO(), 
            encoding='utf-8',
            errors='ignore'
        )
        
        # Lancer le thread de capture
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
    
    def _capture_loop(self):
        """Boucle de capture des logs"""
        import time
        while self.capturing:
            try:
                # Lire depuis stdout
                if hasattr(sys.stdout, 'buffer'):
                    stdout_data = sys.stdout.buffer.getvalue()
                    if stdout_data:
                        self.log_queue.put(("STDOUT", stdout_data.decode('utf-8', errors='ignore')))
                        sys.stdout.buffer.truncate(0)
                        sys.stdout.buffer.seek(0)
                
                # Lire depuis stderr
                if hasattr(sys.stderr, 'buffer'):
                    stderr_data = sys.stderr.buffer.getvalue()
                    if stderr_data:
                        self.log_queue.put(("STDERR", stderr_data.decode('utf-8', errors='ignore')))
                        sys.stderr.buffer.truncate(0)
                        sys.stderr.buffer.seek(0)
                
                time.sleep(0.1)
            except Exception as e:
                self.log_queue.put(("ERROR", f"Erreur de capture: {e}"))
                break
    
    def stop_capture(self):
        """Arrête la capture et restaure stdout/stderr"""
        self.capturing = False
        if hasattr(self, 'capture_thread'):
            self.capture_thread.join(timeout=1)
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
    
    def get_logs(self):
        """Récupère tous les logs de la queue"""
        logs = []
        while not self.log_queue.empty():
            source, message = self.log_queue.get()
            logs.append(f"[{source}] {message}")
        return '\n'.join(logs)
    
    def get_all_logs_blocking(self):
        """Récupère tous les logs, bloque jusqu'à ce qu'il y en ait"""
        logs = self.get_logs()
        if logs:
            return logs
        # Attendre un peu qu'un log arrive
        import time
        time.sleep(0.5)
        return self.get_logs()


class LogWindow:
    """Fenêtre Tkinter pour afficher les logs"""
    
    def __init__(self, root, log_capture=None):
        self.root = root
        self.log_capture = log_capture or LogCapture()
        self.log_text = None
        self.setup_ui()
    
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
            state=tk.DISABLED
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
        
        # Démarrer la mise à jour périodique
        self.update_logs()
    
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
            self.log_text.insert(tk.END, "\n[Logs copiés dans le presse-papiers]\n")
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
            self.log_text.insert(tk.END, f"\n[Logs sauvegardés dans {filename}]\n")
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
