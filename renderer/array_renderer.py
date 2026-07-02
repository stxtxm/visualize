"""Renderer basé sur numpy/Pillow (sans Pygame) pour l'affichage Tkinter."""

import os
import time

HAS_NUMPY = False
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class ArrayRenderer:
    """
    Renderer qui n'utilise PAS Pygame.
    Il fournit une surface numpy array pour le rendu des effets.
    Les effets qui supportent render_to_array() peuvent l'utiliser.
    Compatible avec les environnements sans Pygame.
    """

    def __init__(self, width=1920, height=1080, fps=60):
        self.width = width
        self.height = height
        self.fps = fps
        self._frame = None
        self._initialized = False
        self._start_time = time.time()
        self._no_sound = os.environ.get('NO_SOUND', '').lower() in ('1', 'true', 'yes')

        # Définir un mock clock compatible
        class SimpleClock:
            def __init__(self, target_fps):
                self._target_fps = target_fps
                self._last_tick = time.time()

            def tick(self, target_fps=None):
                """Simule pygame.time.Clock.tick() : retourne ms depuis dernier appel."""
                now = time.time()
                elapsed = now - self._last_tick
                self._last_tick = now
                return int(elapsed * 1000)

        self.clock = SimpleClock(fps)

    def init(self):
        """Initialise le renderer (crée le tableau numpy de rendu)."""
        if self._initialized:
            return

        if not HAS_NUMPY:
            self._initialized = False
            return

        self._frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self._initialized = True

    def get_surface(self):
        """Retourne la surface de rendu (numpy array)."""
        if not HAS_NUMPY:
            if not self._initialized:
                self.init()
            # Mock sans numpy
            class MockArray:
                def __init__(self, w, h):
                    self.width = w
                    self.height = h
                    self.shape = (h, w, 3)

                def fill(self, value):
                    pass

                def get_size(self):
                    return (self.width, self.height)

                def copy(self):
                    return MockArray(self.width, self.height)

            return MockArray(self.width, self.height)

        if not self._initialized:
            self.init()
        return self._frame

    def handle_events(self):
        """Pas de gestion d'événements (pas de fenêtre). Retourne toujours True."""
        return True

    def present(self):
        """
        Pas d'affichage fenêtré. 
        La capture Tkinter est gérée séparément dans _capture_frame_copy.
        """
        pass

    def clear(self):
        """Nettoie le tableau de rendu (remet à noir)."""
        if not HAS_NUMPY or not self._initialized:
            return
        if self._frame is not None:
            self._frame.fill(0)

    def cleanup(self):
        """Nettoie les ressources."""
        self._initialized = False
        self._frame = None

    @property
    def is_initialized(self):
        return self._initialized

    def get_frame_size(self):
        return (self.width, self.height)

    def get_frame_as_bytes(self):
        """
        Retourne le frame actuel comme bytes RGB pour conversion PIL.
        Retourne None si numpy n'est pas disponible.
        """
        if not HAS_NUMPY or self._frame is None:
            return None
        return self._frame.tobytes()