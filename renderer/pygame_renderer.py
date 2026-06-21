"""
Pygame-based renderer for real-time preview.
"""

import pygame
import sys
import os


class PygameRenderer:
    """
    Renderer using Pygame for real-time preview.
    Handles display, events, and frame rendering.
    """

    def __init__(self, width=1920, height=1080, fullscreen=False, fps=60):
        """
        Initialize the Pygame renderer.
        
        Args:
            width: Display width in pixels
            height: Display height in pixels
            fullscreen: Whether to start in fullscreen mode
            fps: Target frames per second
        """
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.fps = fps
        self.screen = None
        self.clock = None
        self._initialized = False
        self._surface = None
        self._no_sound = os.environ.get('NO_SOUND', '').lower() in ('1', 'true', 'yes')

    def init(self):
        """Initialize Pygame and create the display."""
        if self._initialized:
            return
        
        # Désactiver l'accélération matérielle pour éviter les erreurs OpenGL/DRM
        # dans les conteneurs
        os.environ['SDL_VIDEODRIVER'] = 'x11'
        os.environ['SDL_RENDER_DRIVER'] = 'software'
        
        # Initialiser Pygame sans le son si NO_SOUND est activé
        if self._no_sound:
            # Désactiver l'audio et le joystick, garder uniquement video
            pygame.init(pygame.VIDEO)
        else:
            pygame.init()
        
        # Set up the display
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
        
        # Create a surface for rendering
        self._surface = pygame.Surface((self.width, self.height))
        
        self.clock = pygame.time.Clock()
        self._initialized = True

    def get_surface(self):
        """Get the rendering surface."""
        if not self._initialized:
            self.init()
        return self._surface

    def handle_events(self):
        """Handle Pygame events. Returns True if should continue."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_f:
                    # Toggle fullscreen
                    self._toggle_fullscreen()
        return True

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.screen is None:
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
        if self._surface is not None and self.screen is not None:
            # Scale surface to screen if needed
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
        if self._surface is not None:
            self._surface.fill((0, 0, 0))

    def cleanup(self):
        """Clean up Pygame resources."""
        if self._initialized:
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
