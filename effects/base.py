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
    
    def __init__(self, width, height, color_palette='psychedelic', background_image=None, background_opacity=0.72):
        self.width = width
        self.height = height
        self.color_palette = color_palette
        self.colors = self._get_color_palette()
        self.time = 0
        self.background_image = None
        self._background_path = None
        self.background_opacity = max(0.0, min(1.0, background_opacity))
        if background_image:
            self.set_background_image(background_image)
    
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

    def set_background_image(self, image_path):
        """Load an optional RGB background image resized to the effect size."""
        self._background_path = image_path or None
        self.background_image = None
        if not image_path or not HAS_NUMPY:
            return

        try:
            from PIL import Image
            resampling = getattr(Image, "Resampling", Image).LANCZOS
            with Image.open(image_path) as img:
                img = img.convert("RGB")
                img_ratio = img.width / max(img.height, 1)
                frame_ratio = self.width / max(self.height, 1)
                if img_ratio > frame_ratio:
                    new_h = self.height
                    new_w = int(new_h * img_ratio)
                else:
                    new_w = self.width
                    new_h = int(new_w / max(img_ratio, 1e-6))
                img = img.resize((new_w, new_h), resampling)
                left = max(0, (new_w - self.width) // 2)
                top = max(0, (new_h - self.height) // 2)
                img = img.crop((left, top, left + self.width, top + self.height))
                self.background_image = np.asarray(img, dtype=np.uint8).copy()
        except Exception:
            self.background_image = None

    def set_background_opacity(self, opacity):
        """Set the background image blend opacity (0.0 = invisible, 1.0 = fully opaque)."""
        self.background_opacity = max(0.0, min(1.0, opacity))

    def _background_frame(self, base_color=(4, 3, 8), opacity=None):
        """Return a reusable-looking RGB frame with the optional image blended in."""
        if opacity is None:
            opacity = self.background_opacity
        if not HAS_NUMPY:
            return None
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:] = base_color
        if self.background_image is not None:
            bg = self.background_image
            if bg.shape[:2] == (self.height, self.width):
                blended = (
                    bg.astype(np.float32) * opacity
                    + frame.astype(np.float32) * (1.0 - opacity)
                )
                frame[:] = np.clip(blended, 0, 255).astype(np.uint8)
        return frame
    
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
