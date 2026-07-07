"""
Pygame-based renderer for real-time preview.
Supports headless mode (no window) for Tkinter integration.
"""

import sys
import os

# Importer pygame conditionnellement
HAS_PYGAME = False
try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False


class PygameRenderer:
    """
    Renderer using Pygame for real-time preview.
    Handles display, events, and frame rendering.
    
    Si no_window=True (défaut pour GUI Tkinter), ne crée PAS de fenêtre
    et travaille uniquement avec une surface offscreen.
    """

    def __init__(self, width=1920, height=1080, fullscreen=False, fps=60, no_window=True):
        """
        Initialize the Pygame renderer.
        
        Args:
            width: Display width in pixels
            height: Display height in pixels
            fullscreen: Whether to start in fullscreen mode (ignoré si no_window=True)
            fps: Target frames per second
            no_window: Si True, ne crée pas de fenêtre (pour intégration Tkinter)
        """
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.fps = fps
        self.no_window = no_window
        self.screen = None
        self._initialized = False
        self._surface = None
        self._no_sound = os.environ.get('NO_SOUND', '').lower() in ('1', 'true', 'yes')
        
        # Si pygame n'est pas disponible, créer un clock mock
        if not HAS_PYGAME:
            class MockClock:
                def tick(self, fps):
                    return 33
            self.clock = MockClock()
        else:
            self.clock = None

    def init(self):
        """Initialize Pygame and create the display (or offscreen surface)."""
        if self._initialized:
            return
        
        # Si pygame n'est pas disponible, ne pas initialiser
        if not HAS_PYGAME:
            self._initialized = False
            return
        
        # Initialiser Pygame
        if self._no_sound:
            pygame.display.init()
            pygame.font.init()
        else:
            pygame.init()
        
        if self.no_window:
            # Mode sans fenêtre : juste une surface offscreen
            self._surface = pygame.Surface((self.width, self.height))
        else:
            # Mode avec fenêtre (CLI ou export)
            if self.fullscreen:
                info = pygame.display.Info()
                self.width = info.current_w
                self.height = info.current_h
                self.screen = pygame.display.set_mode(
                    (self.width, self.height), 
                    pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
                )
            else:
                self.screen = pygame.display.set_mode(
                    (self.width, self.height),
                    pygame.HWSURFACE | pygame.DOUBLEBUF
                )
            pygame.display.set_caption("Visualisateur Psychédélique")
            self._surface = pygame.Surface((self.width, self.height))
        
        self.clock = pygame.time.Clock()
        self._initialized = True

    def get_surface(self):
        """Get the rendering surface."""
        if not HAS_PYGAME:
            if self.clock is None:
                class MockClock:
                    def tick(self, fps):
                        return 33
                self.clock = MockClock()
            
            class MockSurface:
                def fill(self, color):
                    pass
                def get_size(self):
                    return (self.width, self.height)
                def copy(self):
                    return MockSurface(self.width, self.height)
            return MockSurface()
        
        if not self._initialized:
            self.init()
        return self._surface

    def handle_events(self):
        """Handle Pygame events. Returns True if should continue."""
        if not HAS_PYGAME or not self._initialized or self.no_window:
            return True
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_f:
                    self._toggle_fullscreen()
        return True

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if not HAS_PYGAME or not self._initialized or self.screen is None:
            return
        
        current_flags = self.screen.get_flags()
        is_fullscreen = bool(current_flags & pygame.FULLSCREEN)
        
        if is_fullscreen:
            self.screen = pygame.display.set_mode(
                (self.width, self.height),
                pygame.HWSURFACE | pygame.DOUBLEBUF
            )
            self.fullscreen = False
        else:
            info = pygame.display.Info()
            self.width = info.current_w
            self.height = info.current_h
            self.screen = pygame.display.set_mode(
                (self.width, self.height),
                pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
            )
            self._surface = pygame.Surface((self.width, self.height))
            self.fullscreen = True

    def present(self):
        """Present the rendered surface to the display."""
        if not HAS_PYGAME or not self._initialized:
            return
        
        if self.no_window:
            # Rien à présenter (pas de fenêtre)
            return
        
        if self._surface is not None and self.screen is not None:
            if self._surface.get_size() != self.screen.get_size():
                scaled = pygame.transform.scale(
                    self._surface, 
                    self.screen.get_size()
                )
                self.screen.blit(scaled, (0, 0))
            else:
                self.screen.blit(self._surface, (0, 0))
            pygame.display.flip()

    def clear(self):
        """Clear the rendering surface."""
        if not HAS_PYGAME or not self._initialized:
            return
        
        if self._surface is not None:
            self._surface.fill((0, 0, 0))

    def cleanup(self):
        """Clean up Pygame resources."""
        if not HAS_PYGAME:
            self._initialized = False
            self.screen = None
            self.clock = None
            self._surface = None
            return
        
        if self._initialized:
            # pygame.quit() seulement si on n'est pas dans un thread
            if not self.no_window:
                pygame.quit()
            self._initialized = False
            self.screen = None
            self.clock = None
            self._surface = None

    @property
    def is_initialized(self):
        """Check if renderer is initialized."""
        return self._initialized

    def get_frame_size(self):
        """Get the frame dimensions."""
        return (self.width, self.height)
    
    def get_frame_as_bytes(self):
        """
        Retourne le contenu de la surface comme bytes RGB.
        Fonctionne sans fenêtre d'affichage.
        """
        if not HAS_PYGAME or self._surface is None:
            return None
        try:
            return pygame.image.tostring(self._surface, 'RGB')
        except Exception:
            return None