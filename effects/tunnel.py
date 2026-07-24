"""
Effet de tunnel psychédélique amélioré - inspiré de Winamp.
Crée un effet de tunnel 3D avec distorsion, rotation et couleurs qui réagissent à la musique.
"""

import numpy as np
import math
import random
from effects.base import BaseEffect


class TunnelEffect(BaseEffect):
    """
    Effet de tunnel psychédélique avec effet 3D.
    Les cercles s'éloignent vers l'arrière avec une distorsion qui réagit au son.
    """
    
    def __init__(self, width, height, color_palette='psychedelic'):
        super().__init__(width, height, color_palette)
        self.center_x = width // 2
        self.center_y = height // 2
        self.num_rings = 40  # Nombre de cercles concentriques
        self.tunnel_depth = self.num_rings
        self.rotation = 0
        self.rotation_speed = 0.0
        
        # Pour l'effet de distorsion
        self.distortion = 0.0
        self.target_distortion = 0.0
        self.distortion_frequency = 0.5
        
        # Pour l'effet de pulsation
        self.pulse = 0.0
        self.target_pulse = 0.0
        
        # Pour l'effet de twist (torsion)
        self.twist = 0.0
        self.target_twist = 0.0
        
        # Pour les particules supplémentaires
        self.particles = []
        self.max_particles = 50
        
        # Paramètres de lissage
        self.smoothing = 0.1
        
        # Mémoire des valeurs précédentes pour les transitions douces
        self.prev_bass = 0.0
        self.prev_treble = 0.0
    
    def update(self, audio_data, delta_time):
        super().update(audio_data, delta_time)
        
        # Rotation de base lente
        self.rotation += self.rotation_speed * delta_time
        
        # Lissage des valeurs
        if audio_data:
            volume = audio_data.get('volume', 0)
            freq_bands = audio_data.get('frequency_bands', [])
            bass = audio_data.get('bass', 0)
            mids = audio_data.get('mids', 0)
            treble = audio_data.get('treble', 0)
            beat = audio_data.get('beat', False)
            beat_strength = audio_data.get('beat_strength', 0)
            bpm = audio_data.get('bpm', 120)
            
            # La distorsion dépend du volume et des basses
            self.target_distortion = (bass * 0.5 + volume * 0.3) * 0.8
            
            # La pulsation dépend du volume global
            self.target_pulse = volume * 0.3
            
            # Le twist dépend du treble
            self.target_twist = (treble - self.prev_treble) * 2
            self.prev_treble = treble
            
            # La vitesse de rotation dépend du BPM
            # Plus le BPM est élevé, plus ça tourne vite
            bpm_normalized = (bpm - 60) / (180 - 60)  # Normaliser entre 60 et 180 BPM
            self.rotation_speed = bpm_normalized * 0.3 + bass * 0.2
            
            # Ajouter un effet de beat
            if beat:
                self.target_distortion = min(self.target_distortion + beat_strength * 0.5, 1.0)
                self.target_pulse = min(self.target_pulse + beat_strength * 0.3, 1.0)
                
                # Sur un beat fort, ajouter une explosion de particules
                if beat_strength > 0.5:
                    for _ in range(10):
                        if len(self.particles) < self.max_particles:
                            angle = random.uniform(0, 2 * math.pi)
                            distance = random.uniform(0, min(self.width, self.height) * 0.4)
                            x = self.center_x + math.cos(angle) * distance
                            y = self.center_y + math.sin(angle) * distance
                            self.particles.append({
                                'x': x,
                                'y': y,
                                'vx': math.cos(angle) * (1 + beat_strength) * 2,
                                'vy': math.sin(angle) * (1 + beat_strength) * 2,
                                'size': random.uniform(2, 8),
                                'life': 1.0,
                                'color': self.colors[random.randint(0, len(self.colors) - 1)]
                            })
            
            # Ajouter des particules régulièrement
            if random.random() < 0.05 * volume:
                angle = random.uniform(0, 2 * math.pi)
                distance = min(self.width, self.height) * 0.4
                x = self.center_x + math.cos(angle) * distance
                y = self.center_y + math.sin(angle) * distance
                self.particles.append({
                    'x': x,
                    'y': y,
                    'vx': math.cos(angle) * 0.5,
                    'vy': math.sin(angle) * 0.5,
                    'size': random.uniform(1, 4),
                    'life': random.uniform(0.5, 1.5),
                    'color': self.colors[random.randint(0, len(self.colors) - 1)]
                })
        else:
            self.target_distortion = 0.0
            self.target_pulse = 0.0
            self.target_twist = 0.0
            self.rotation_speed *= 0.95
        
        # Appliquer le lissage
        self.distortion = (
            self.distortion * (1 - self.smoothing) +
            self.target_distortion * self.smoothing
        )
        self.pulse = (
            self.pulse * (1 - self.smoothing * 2) +
            self.target_pulse * self.smoothing * 2
        )
        self.twist = (
            self.twist * (1 - self.smoothing * 3) +
            self.target_twist * self.smoothing * 3
        )
        
        # Mettre à jour les particules
        for p in self.particles[:]:
            p['x'] += p['vx'] * 30 * delta_time
            p['y'] += p['vy'] * 30 * delta_time
            p['life'] -= delta_time * 2
            
            # Si la particule est morte, la supprimer
            if p['life'] <= 0:
                self.particles.remove(p)
    
    def _get_color(self, ring_idx, intensity=1.0):
        """Retourne une couleur pour un anneau donné."""
        # Utiliser la palette, mais avec une rotation basée sur le temps et l'index
        color_idx = (ring_idx * 3 + int(self.time * 5)) % len(self.colors)
        color = self.colors[color_idx]
        
        # Ajuster la luminosité
        r, g, b = color
        r = min(255, int(r * intensity))
        g = min(255, int(g * intensity))
        b = min(255, int(b * intensity))
        
        return (r, g, b)
    
    def render(self, surface):
        """Rendu avec Pygame."""
        import pygame
        
        # Fond noir
        surface.fill((0, 0, 0))
        
        max_radius = min(self.width, self.height) // 2
        
        # Dessiner les cercles du tunnel
        for i in range(self.num_rings):
            # Calculer le rayon
            radius = int(max_radius * (i + 1) / self.num_rings * (1 + self.pulse * 0.3))
            if radius < 1:
                continue
            
            # Calculer la couleur avec intensité
            intensity = 1.0 - i / self.num_rings
            color = self._get_color(i, intensity=0.5 + intensity * 0.5)
            
            # Appliquer la distorsion
            num_points = 60
            points = []
            
            for j in range(num_points):
                angle = self.rotation + j * (2 * math.pi / num_points) + self.twist * (i / self.num_rings)
                
                # Distorsion sinusoïdale complexe
                distortion_1 = math.sin(angle * 3 + self.time * 2) * self.distortion * radius * 0.3
                distortion_2 = math.cos(angle * 5 + self.time * 1.5) * self.distortion * radius * 0.2
                distortion_3 = math.sin(angle * 7 + self.time * 2.5) * self.distortion * radius * 0.1
                
                total_distortion = distortion_1 + distortion_2 + distortion_3
                
                r = radius + total_distortion
                x = self.center_x + math.cos(angle) * r
                y = self.center_y + math.sin(angle) * r
                points.append((int(x), int(y)))
            
            # Dessiner le polygone avec transparence
            if len(points) > 2:
                # Réutiliser la surface temporaire pour éviter les allocations
                if not hasattr(self, '_temp_surface') or self._temp_surface.get_size() != (self.width, self.height):
                    self._temp_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                
                self._temp_surface.fill((0, 0, 0, 0))
                alpha = int(200 * (1 - i / self.num_rings))
                pygame.draw.polygon(self._temp_surface, (*color, alpha), points)
                surface.blit(self._temp_surface, (0, 0))
        
        # Dessiner les particules (réutiliser une seule surface)
        if self.particles:
            if not hasattr(self, '_particles_surface') or self._particles_surface.get_size() != (self.width, self.height):
                self._particles_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                
            self._particles_surface.fill((0, 0, 0, 0))
            for p in self.particles:
                alpha = int(255 * p['life'])
                pygame.draw.circle(self._particles_surface, (*p['color'], alpha), (int(p['x']), int(p['y'])), int(p['size']))
            surface.blit(self._particles_surface, (0, 0))
        
        # Ajouter un effet de centre qui pulse au rythme des basses
        center_size = int(10 + self.pulse * 30)
        pygame.draw.circle(surface, 
                         self.colors[int(self.time * 2) % len(self.colors)],
                         (int(self.center_x), int(self.center_y)),
                         center_size)
    
    def render_to_array(self):
        """Rendu vers un tableau numpy pour l'export vidéo."""
        import cv2
        
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        max_radius = min(self.width, self.height) // 2
        
        # Dessiner les cercles du tunnel
        for i in range(self.num_rings):
            radius = int(max_radius * (i + 1) / self.num_rings * (1 + self.pulse * 0.3))
            if radius < 1:
                continue
            
            intensity = 1.0 - i / self.num_rings
            color = self._get_color(i, intensity=0.5 + intensity * 0.5)
            
            num_points = 60
            angles_base = np.linspace(0, 2 * np.pi, num_points, endpoint=False, dtype=np.float32)
            angles = self.rotation + angles_base + self.twist * (i / self.num_rings)
            
            d1 = np.sin(angles * 3.0 + self.time * 2.0) * (self.distortion * radius * 0.3)
            d2 = np.cos(angles * 5.0 + self.time * 1.5) * (self.distortion * radius * 0.2)
            d3 = np.sin(angles * 7.0 + self.time * 2.5) * (self.distortion * radius * 0.1)
            r = radius + d1 + d2 + d3
            
            xs = (self.center_x + np.cos(angles) * r).astype(np.int32)
            ys = (self.center_y + np.sin(angles) * r).astype(np.int32)
            polygon = np.column_stack((xs, ys))
            
            alpha = 0.8 * (1 - i / self.num_rings)
            self._draw_alpha_poly(frame, cv2, polygon, color, alpha)
        
        # Dessiner les particules
        for p in self.particles:
            alpha = p['life']
            color = p['color']
            size = int(p['size'])
            x, y = int(p['x']), int(p['y'])
            
            # Dessiner la particule avec alpha
            cv2.circle(frame, (x, y), size, color, -1)
        
        # Effet de centre
        center_size = int(10 + self.pulse * 30)
        cv2.circle(frame,
                  (int(self.center_x), int(self.center_y)),
                  center_size,
                  tuple(self.colors[int(self.time * 2) % len(self.colors)]),
                  -1)
        
        return frame
