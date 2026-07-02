"""
Renderer headless Pygame : utilise Pygame pour le rendu (draw, surface),
mais NE crée PAS de fenêtre d'affichage.
Le frame est capturé via pygame.image.tobytes() pour le preview Tkinter.
"""

import os
import time

HAS_PYGAME = False
try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False


class HeadlessRenderer:
    """
    Renderer Pygame sans fenêtre.
    Crée une Surface Pygame offscreen pour le rendu des effets,
    sans ouvrir de fenêtre d'affichage.
    
    Compatible avec effect.render(surface) qui utilise pygame.draw.*
    Le frame est capturé via pygame.image.tobytes().
    """

    def __init__(self, width=1920, height=1080, fps=60):
        self.width = width
        self.height = height
        self.fps = fps
        self._surface = None
        self._initialized = False
        self._no_sound = os.environ.get('NO_SOUND', '').lower() in ('1', 'true', 'yes')

        class SimpleClock:
            def __init__(self):
                self._last_tick = time.time()

            def tick(self, target_fps=None):
                now = time.time()
                elapsed = now - self._last_tick
                self._last_tick = now
                # Si le temps est trop petit (premier appel), retourner ~30fps
                if elapsed < 0.001:
                    return 33
                return int(elapsed * 1000)

        self.clock = SimpleClock()

    def init(self):
        """
        Initialise le renderer headless.
        Configure SDL en mode 'dummy' (pas de fenêtre), puis initialise Pygame,
        et crée une Surface offscreen pour le rendu.
        """
        if self._initialized:
            return

        if not HAS_PYGAME:
            self._initialized = False
            return

        # Forcer SDL en mode dummy avant toute initialisation : PAS DE FENÊTRE
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        os.environ['SDL_RENDER_DRIVER'] = 'software'

        # Initialiser Pygame (mode dummy = pas de fenêtre X11)
        pygame.display.init()
        pygame.time.init()

        # Créer une Surface offscreen pour le rendu
        self._surface = pygame.Surface((self.width, self.height))
        self._initialized = True

    def get_surface(self):
        """Retourne la surface de rendu (pygame.Surface offscreen)."""
        if not HAS_PYGAME:
            if not self._initialized:
                self.init()
            class MockSurface:
                def __init__(self, w, h):
                    self.width = w
                    self.height = h
                def fill(self, color):
                    pass
                def get_size(self):
                    return (self.width, self.height)
                def copy(self):
                    return MockSurface(self.width, self.height)
            return MockSurface(self.width, self.height)

        if not self._initialized:
            self.init()
        return self._surface

    def handle_events(self):
        """Pas de gestion d'événements (pas de fenêtre). Retourne toujours True."""
        return True

    def present(self):
        """Pas d'affichage fenêtré. La capture Tkinter est externe."""
        pass

    def clear(self):
        """Nettoie la surface (remet à noir)."""
        if not HAS_PYGAME or not self._initialized:
            return
        if self._surface is not None:
            self._surface.fill((0, 0, 0))

    def cleanup(self):
        """Nettoie les ressources.
        
        NE fait PAS pygame.quit() ici car cela peut être appelé depuis un thread
        et pygame.quit() doit être appelé depuis le thread principal.
        """
        if not HAS_PYGAME:
            self._initialized = False
            self._surface = None
            self.clock = None
            return

        if self._initialized:
            # pygame.quit() est appelé depuis le thread principal via stop_pygame()
            self._initialized = False
            self._surface = None
            self.clock = None

    @property
    def is_initialized(self):
        return self._initialized

    def get_frame_size(self):
        return (self.width, self.height)

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