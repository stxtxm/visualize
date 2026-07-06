"""
Renderer headless Pygame : utilise Pygame pour le rendu (draw, surface),
mais NE crée PAS de fenêtre d'affichage.
Le frame est capturé via pygame.image.tobytes() pour le preview Tkinter.

Utilise une résolution de rendu interne plus petite pour les performances
(le preview Tkinter est affiché en 800x450 de toute façon).
"""

import os
import time
import numpy as np

HAS_PYGAME = False
try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False


class SimpleClock:
    """
    Horloge simple avec limitation de FPS.
    tick(fps) bloque jusqu'à ce que le temps de frame soit écoulé.
    """
    def __init__(self):
        self._last_tick = time.time()

    def tick(self, target_fps=None):
        """Attend le temps restant pour maintenir le FPS cible."""
        now = time.time()
        elapsed = now - self._last_tick
        
        if target_fps and target_fps > 0:
            target_frame_time = 1.0 / target_fps
            if elapsed < target_frame_time:
                sleep_time = target_frame_time - elapsed
                if sleep_time > 0.001:
                    time.sleep(sleep_time * 0.9)  # Sleep 90%, busy-wait 10%
                    # Fine-grained wait for precision
                    while time.time() - now < target_frame_time:
                        pass
                now = time.time()
                elapsed = now - self._last_tick
        
        self._last_tick = now
        return int(elapsed * 1000)


class HeadlessRenderer:
    """
    Renderer Pygame sans fenêtre.
    Crée une Surface Pygame offscreen pour le rendu des effets,
    sans ouvrir de fenêtre d'affichage.
    
    Utilise une résolution de rendu réduite (800x450 par défaut)
    pour des performances optimales dans le preview Tkinter.
    """
    RENDER_WIDTH = 800
    RENDER_HEIGHT = 450

    def __init__(self, width=1920, height=1080, fps=60):
        """
        Initialize the renderer.
        
        Args:
            width: Width (résolution d'effet pour render_to_array)
            height: Height (résolution d'effet pour render_to_array)
            fps: Target frames per second
        """
        self.width = width
        self.height = height
        self.fps = fps
        self._surface = None
        self._initialized = False
        self._no_sound = os.environ.get('NO_SOUND', '').lower() in ('1', 'true', 'yes')
        self.clock = SimpleClock()
        self._frame_count = 0
        self._last_fps_log = time.time()

    def init(self):
        """
        Initialise le renderer headless.
        Configure SDL en mode 'dummy', crée une Surface offscreen en résolution réduite.
        """
        if self._initialized:
            return

        if not HAS_PYGAME:
            self._initialized = False
            return

        # Forcer SDL en mode dummy avant toute initialisation : PAS DE FENÊTRE
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        os.environ['SDL_RENDER_DRIVER'] = 'software'

        # Initialiser Pygame en mode offscreen (dummy = pas de fenêtre X11)
        if not pygame.get_init():
            pygame.init()

        # Créer une Surface offscreen en résolution réduite pour le preview
        self._surface = pygame.Surface((self.RENDER_WIDTH, self.RENDER_HEIGHT))
        self._initialized = True

    def get_surface(self):
        """Retourne la surface de rendu (pygame.Surface offscreen en 800x450)."""
        if not HAS_PYGAME:
            if not self._initialized:
                self.init()
            class MockSurface:
                def __init__(self):
                    self.width = HeadlessRenderer.RENDER_WIDTH
                    self.height = HeadlessRenderer.RENDER_HEIGHT
                def fill(self, color):
                    pass
                def get_size(self):
                    return (self.width, self.height)
                def copy(self):
                    return MockSurface()
            return MockSurface()

        if not self._initialized:
            self.init()
        return self._surface

    def handle_events(self):
        """Pas de gestion d'événements (pas de fenêtre). Retourne toujours True."""
        return True

    def present(self):
        """Pas d'affichage fenêtré. Log périodique du FPS."""
        self._frame_count += 1
        now = time.time()
        if now - self._last_fps_log >= 5.0:
            actual_fps = self._frame_count / (now - self._last_fps_log)
            try:
                from ui.log_display import log_message
                log_message(f"HeadlessRenderer: ~{actual_fps:.1f} FPS (target {self.fps})")
            except Exception:
                pass
            self._frame_count = 0
            self._last_fps_log = now

    def clear(self):
        """Nettoie la surface (remet à noir)."""
        if not HAS_PYGAME or not self._initialized:
            return
        if self._surface is not None:
            self._surface.fill((0, 0, 0))

    def cleanup(self):
        """Nettoie les ressources."""
        if not HAS_PYGAME:
            self._initialized = False
            self._surface = None
            self.clock = None
            return

        if self._initialized:
            self._initialized = False
            self._surface = None
            self.clock = None

    @property
    def is_initialized(self):
        return self._initialized

    def get_frame_size(self):
        return (self.RENDER_WIDTH, self.RENDER_HEIGHT)

    def get_frame_as_bytes(self):
        """
        Retourne le frame actuel comme bytes RGB via pygame.image.tobytes().
        Retourne None si Pygame n'est pas disponible.
        """
        if not HAS_PYGAME or self._surface is None:
            return None
        try:
            return pygame.image.tobytes(self._surface, 'RGB')
        except Exception:
            return None