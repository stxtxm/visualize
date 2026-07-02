"""
Gestion centralisée des paths pour le projet conteneurisé.
Resout le mapping entre hôte et conteneur automatiquement.

Ce module permet de gérer les paths de manière transparente, que le code
s'exécute dans le conteneur Podman/Docker ou sur l'hôte.
"""

import os
import sys


class PathManager:
    """
    Gère les paths entre l'hôte et le conteneur.
    
    Dans le conteneur:
        - input_dir = /app/input
        - output_dir = /app/output
        - project_dir = /app
    
    Sur l'hôte:
        - input_dir = <project_root>/input
        - output_dir = <project_root>/output
        - project_dir = <project_root>
    
    Utilisation:
        path_manager = PathManager()
        audio_file = path_manager.get_input_path('ma_musique.mp3')
        output_file = path_manager.get_output_path('ma_video.mp4')
    """
    
    def __init__(self):
        """Initialise le PathManager en détectant l'environnement."""
        self._detect_environment()
        self._setup_directories()
    
    def _detect_environment(self):
        """Détecte si on est dans le conteneur ou sur l'hôte."""
        # Vérifier si /app/main.py existe (conteneur)
        in_container = os.path.exists('/app/main.py')
        
        if in_container:
            # Dans le conteneur
            self.in_container = True
            self.project_dir = '/app'
            self.input_dir = '/app/input'
            self.output_dir = '/app/output'
        else:
            # Sur l'hôte - essayer de trouver la racine du projet
            self.in_container = False
            
            # Trouver la racine du projet (là où se trouve main.py)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_dir = current_dir
            
            # Monter jusqu'à trouver main.py
            while True:
                if os.path.exists(os.path.join(project_dir, 'main.py')):
                    self.project_dir = project_dir
                    break
                parent = os.path.dirname(project_dir)
                if parent == project_dir:
                    # On est à la racine du filesystem, s'arrêter
                    self.project_dir = current_dir
                    break
                project_dir = parent
            
            self.input_dir = os.path.join(self.project_dir, 'input')
            self.output_dir = os.path.join(self.project_dir, 'output')
    
    def _setup_directories(self):
        """Crée les dossiers input/ et output/ s'ils n'existent pas."""
        try:
            os.makedirs(self.input_dir, exist_ok=True)
            os.makedirs(self.output_dir, exist_ok=True)
        except (OSError, PermissionError) as e:
            print(f"Warning: Impossible de créer les dossiers: {e}")
    
    def get_input_path(self, filename):
        """
        Retourne le chemin complet d'un fichier dans input/.
        
        Args:
            filename: Nom du fichier (ex: 'ma_musique.mp3')
            
        Returns:
            str: Chemin complet (ex: '/app/input/ma_musique.mp3' ou './input/ma_musique.mp3')
        """
        return os.path.join(self.input_dir, filename)
    
    def get_output_path(self, filename):
        """
        Retourne le chemin complet d'un fichier dans output/.
        
        Args:
            filename: Nom du fichier (ex: 'ma_video.mp4')
            
        Returns:
            str: Chemin complet
        """
        return os.path.join(self.output_dir, filename)
    
    def list_input_files(self, extensions=None):
        """
        Liste les fichiers dans input/ avec filtre optionnel d'extension.
        
        Args:
            extensions: Liste d'extensions à filtrer (ex: ['.mp3', '.wav'])
                        Si None, retourne tous les fichiers.
        
        Returns:
            list: Liste des chemins complets des fichiers
        """
        if not os.path.exists(self.input_dir):
            return []
        
        files = []
        try:
            for filename in os.listdir(self.input_dir):
                filepath = os.path.join(self.input_dir, filename)
                if os.path.isfile(filepath):
                    if extensions is None:
                        files.append(filepath)
                    else:
                        if any(filename.lower().endswith(ext) for ext in extensions):
                            files.append(filepath)
        except (OSError, PermissionError):
            pass
        
        return sorted(files)
    
    def get_media_files(self):
        """
        Retourne tous les fichiers multimédia dans input/.
        
        Returns:
            list: Liste des chemins complets des fichiers multimédia
        """
        media_extensions = [
            '.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a',
            '.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv'
        ]
        return self.list_input_files(media_extensions)
    
    def get_project_path(self, *path_parts):
        """
        Retourne un chemin relatif à la racine du projet.
        
        Args:
            *path_parts: Composants du path (ex: 'audio', 'analyzer.py')
        
        Returns:
            str: Chemin complet
        """
        return os.path.join(self.project_dir, *path_parts)
    
    def convert_to_container_path(self, path):
        """
        Convertit un chemin de l'hôte vers un chemin dans le conteneur.
        
        Args:
            path: Chemin sur l'hôte
            
        Returns:
            str: Chemin équivalent dans le conteneur
        """
        if self.in_container:
            return path
        
        # Sur l'hôte, remplacer <project>/input/ par /app/input/
        if path.startswith(self.input_dir):
            return path.replace(self.input_dir, '/app/input')
        elif path.startswith(self.output_dir):
            return path.replace(self.output_dir, '/app/output')
        elif path.startswith(self.project_dir):
            return path.replace(self.project_dir, '/app')
        
        return path
    
    def convert_to_host_path(self, path):
        """
        Convertit un chemin du conteneur vers un chemin sur l'hôte.
        
        Args:
            path: Chemin dans le conteneur
            
        Returns:
            str: Chemin équivalent sur l'hôte
        """
        if not self.in_container:
            return path
        
        # Dans le conteneur, remplacer /app/input/ par <project>/input/
        if path.startswith('/app/input'):
            return path.replace('/app/input', self.input_dir)
        elif path.startswith('/app/output'):
            return path.replace('/app/output', self.output_dir)
        elif path.startswith('/app'):
            return path.replace('/app', self.project_dir)
        
        return path
    
    def is_in_container(self):
        """Retourne True si le code s'exécute dans le conteneur."""
        return self.in_container


# Instance globale pour une utilisation facile
path_manager = PathManager()


def get_path_manager():
    """Retourne l'instance globale du PathManager."""
    return path_manager
