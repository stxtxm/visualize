"""
Effet de particules qui réagissent au son.
"""

import numpy as np
import math
import random
from effects.base import BaseEffect


class Particle:
    """Représente une particule individuelle."""
    
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-1, 1)
        self.size = random.randint(2, 8)
        self.life = random.uniform(0, 1)
        self.max_life = random.uniform(5, 15)
        # Générer une couleur aléatoire mais vive
        self.color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255)
        )
    
    def update(self, audio_data, delta_time):
        """Met à jour la particule."""
        self.life += delta_time
        
        if audio_data:
            volume = audio_data.get('volume', 0)
            freq_bands = audio_data.get('frequency_bands', [])
            
            # Calculer un facteur de vitesse
            speed_factor = 1.0 + volume * 2
            
            # Réagir aux beats
            if audio_data.get('beat', False):
                # Au beat, changer de direction aléatoirement
                self.vx = random.uniform(-2, 2) * speed_factor
                self.vy = random.uniform(-2, 2) * speed_factor
            
            # Appliquer la vitesse
            self.x += self.vx * speed_factor * 100 * delta_time
            self.y += self.vy * speed_factor * 100 * delta_time
        else:
            self.x += self.vx * 50 * delta_time
            self.y += self.vy * 50 * delta_time
        
        # Rebondir sur les bords
        if self.x < 0:
            self.x = 0
            self.vx = -self.vx * 0.8
        elif self.x > self.width:
            self.x = self.width
            self.vx = -self.vx * 0.8
            
        if self.y < 0:
            self.y = 0
            self.vy = -self.vy * 0.8
        elif self.y > self.height:
            self.y = self.height
            self.vy = -self.vy * 0.8
        
        # Réduire la taille avec l'âge
        age_factor = 1.0 - (self.life / self.max_life)
        self.size = max(1, int(self.size * age_factor))
    
    def is_alive(self):
        """Vérifie si la particule est encore vivante."""
        return self.life < self.max_life
    
    def draw(self, surface):
        """Dessine la particule sur une surface Pygame."""
        import pygame
        pygame.draw.circle(
            surface,
            self.color,
            (int(self.x), int(self.y)),
            self.size
        )


class ParticleEffect(BaseEffect):
    """
    Effet de particules qui réagissent à la musique.
    """
    
    def __init__(self, width, height, color_palette='psychedelic'):
        super().__init__(width, height, color_palette)
        self.particles = []
        self.max_particles = 200
        self.spawn_rate = 10  # Particules par seconde
        self.spawn_timer = 0
    
    def update(self, audio_data, delta_time):
        super().update(audio_data, delta_time)
        
        # Supprimer les particules mortes
        self.particles = [p for p in self.particles if p.is_alive()]
        
        # Ajouter de nouvelles particules
        self.spawn_timer += delta_time
        spawn_count = int(self.spawn_timer * self.spawn_rate)
        self.spawn_timer -= spawn_count / self.spawn_rate
        
        if audio_data and audio_data.get('beat', False):
            # Sur un beat, spawner plus de particules
            spawn_count += 30
        
        for _ in range(spawn_count):
            if len(self.particles) < self.max_particles:
                x = random.randint(0, self.width)
                y = random.randint(0, self.height)
                self.particles.append(Particle(x, y, self.width, self.height))
        
        # Mettre à jour les particules
        for particle in self.particles:
            particle.update(audio_data, delta_time)
    
    def render(self, surface):
        """Rendu des particules avec Pygame."""
        import pygame
        surface.fill((0, 0, 0))
        
        for particle in self.particles:
            particle.draw(surface)
    
    def render_to_array(self):
        """Rendu vers un tableau numpy pour l'export vidéo."""
        import cv2
        
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        for particle in self.particles:
            # Dessiner la particule comme un cercle
            cv2.circle(
                frame,
                (int(particle.x), int(particle.y)),
                particle.size,
                particle.color,
                -1  # Rempli
            )
        
        return frame
