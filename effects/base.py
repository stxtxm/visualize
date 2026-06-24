"""
Classe de base pour tous les effets visuels.
"""

import math

# Importer numpy conditionnellement (peut ne pas être disponible)
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class BaseEffect:
    """
    Classe abstraite pour les effets visuels.
    """
    
    def __init__(self, width, height, color_palette='psychedelic'):
        self.width = width
        self.height = height
        self.color_palette = color_palette
        self.colors = self._get_color_palette()
        self.time = 0
    
    def _get_color_palette(self):
        """Retourne une palette de couleurs selon le mode sélectionné."""
        palettes = {
            'psychedelic': [
                (255, 0, 255),    # Magenta
                (0, 255, 255),    # Cyan
                (255, 255, 0),    # Jaune
                (255, 0, 0),      # Rouge
                (0, 255, 0),      # Vert
                (0, 0, 255),      # Bleu
                (255, 128, 0),    # Orange
                (128, 0, 255),    # Violet
            ],
            'retro': [
                (0, 255, 0),      # Vert Winamp
                (255, 255, 0),    # Jaune
                (0, 192, 255),    # Bleu clair
                (255, 0, 255),    # Magenta
                (0, 255, 255),    # Cyan
            ],
            'winamp_classic': [
                (0, 255, 0),      # Vert Winamp classique
                (0, 200, 0),      # Vert légèrement plus sombre
                (0, 180, 0),      # Vert moyen
                (0, 128, 0),      # Vert foncé
                (255, 255, 0),    # Jaune vif
                (200, 200, 0),    # Jaune moyen
                (150, 150, 0),    # Jaune foncé
            ],
            'dark': [
                (32, 32, 32),     # Gris foncé
                (64, 64, 255),    # Bleu
                (255, 64, 64),    # Rouge
                (64, 255, 64),    # Vert
                (255, 255, 64),   # Jaune
            ],
            'rainbow': [
                (255, 0, 0),      # Rouge
                (255, 127, 0),    # Orange
                (255, 255, 0),    # Jaune
                (0, 255, 0),      # Vert
                (0, 0, 255),      # Bleu
                (75, 0, 130),     # Indigo
                (148, 0, 211),    # Violet
            ]
        }
        return palettes.get(self.color_palette, palettes['psychedelic'])
    
    def get_color(self, index=None):
        """Retourne une couleur de la palette."""
        if index is None:
            index = int(self.time * 2) % len(self.colors)
        return self.colors[index % len(self.colors)]
    
    def render_to_array(self):
        """
        Rendu de l'effet vers un tableau numpy (pour l'export vidéo).
        Doit être implémenté par les classes fillles.
        """
        raise NotImplementedError("La méthode render_to_array doit être implémentée")
    
    def update(self, audio_data, delta_time):
        """
        Met à jour l'effet avec les données audio.
        
        Args:
            audio_data: dict avec les données d'analyse audio
            delta_time: Temps écoulé depuis la dernière frame (secondes)
        """
        self.time += delta_time
    
    def render(self, surface):
        """
        Rendu de l'effet sur la surface donnée.
        
        Args:
            surface: Surface de rendu (pygame.Surface)
        """
        raise NotImplementedError("La méthode render doit être implémentée")
