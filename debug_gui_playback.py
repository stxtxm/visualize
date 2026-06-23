#!/usr/bin/env python3
"""
Script de debug pour la GUI - simule le problème de lecture.
Ce script reproduit la boucle de lecture avec des logs détaillés.
"""

import sys
import os
import time
import threading
import logging
import warnings
from datetime import datetime

# Setup paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration des logs
LOG_FILE = f"/tmp/debug_gui_playback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
DEBUG_MODE = True

# Activer NO_SOUND pour éviter les problèmes audio
os.environ['NO_SOUND'] = '1'
os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Éviter les problèmes X11
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

def setup_logging():
    """Configure le logging détaillé."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, mode='w'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Désactiver les logs trop verbeux
    logging.getLogger('PIL').setLevel(logging.ERROR)
    return logging.getLogger('debug_gui')


class DebugAudioAnalyzer:
    """Mock AudioAnalyzer avec debug."""
    def __init__(self, audio_file, chunk_size=1024, sample_rate=44100, loop=True):
        self.audio_file = audio_file
        self.chunk_size = chunk_size
        self.sample_rate = sample_rate
        self.loop = loop
        self.is_playing = False
        self.current_chunk = 0
        self.total_chunks = 1000  # Simuler un grand nombre de chunks
        self.use_simulated = True
        self.audio_data = [0] * chunk_size * 10
        self.logger = setup_logging()
        self.logger.info(f"AudioAnalyzer créé: {audio_file}")
    
    def start_stream(self):
        self.logger.info("start_stream() appelé")
        self.is_playing = True
        self.current_chunk = 0
        self.logger.info("Stream démarré")
    
    def get_next_chunk(self):
        if not self.is_playing:
            self.logger.warning("get_next_chunk() appelé mais is_playing=False")
            return None
        
        if self.current_chunk >= self.total_chunks and not self.loop:
            self.logger.info(f"Fin du stream atteint (chunk {self.current_chunk})")
            return None
        
        chunk = [0] * self.chunk_size
        self.current_chunk += 1
        
        if self.current_chunk % 100 == 0:
            self.logger.debug(f"Chunk {self.current_chunk}/{self.total_chunks} généré")
        
        return chunk
    
    def analyze_chunk(self, chunk):
        import math
        volume = abs(math.sin(self.current_chunk * 0.1)) * 0.5 + 0.3
        return {
            'volume': volume,
            'frequency_bands': [abs(math.sin(self.current_chunk * 0.1 + i * 0.5)) * 0.3 + 0.1 for i in range(16)],
            'spectrum': [abs(math.sin(self.current_chunk * 0.1 + i * 0.2)) * 0.5 for i in range(1024)],
            'bass': volume * 0.7,
            'mids': volume * 0.5,
            'treble': volume * 0.3,
            'beat': self.current_chunk % 10 == 0,
            'beat_strength': volume if self.current_chunk % 10 == 0 else 0,
            'bpm': 120
        }
    
    def cleanup(self):
        self.logger.info("AudioAnalyzer cleanup()")
        self.is_playing = False


class DebugRenderer:
    """Mock Renderer avec debug."""
    def __init__(self, width, height, fullscreen=False, fps=30):
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.fps = fps
        self.is_initialized = False
        self.clock = DebugClock()
        self._surface = None
        self.logger = setup_logging()
        self.logger.info(f"Renderer créé: {width}x{height}, {fps}fps")
    
    def init(self):
        self.logger.info("Renderer init()")
        self.is_initialized = True
        self._surface = DebugSurface(self.width, self.height)
        self.logger.info("Renderer initialisé")
    
    def get_surface(self):
        if not self.is_initialized:
            self.init()
        return self._surface
    
    def present(self):
        # C'est ici que le deadlock peut se produire avec Pygame
        self.logger.debug("present() appelé")
    
    def handle_events(self):
        self.logger.debug("handle_events() appelé")
        return True
    
    def cleanup(self):
        self.logger.info("Renderer cleanup()")
        self.is_initialized = False


class DebugClock:
    def tick(self, fps):
        return int(1000 / fps)


class DebugSurface:
    def __init__(self, width, height):
        self.width = width
        self.height = height
    
    def copy(self):
        return DebugSurface(self.width, self.height)


class DebugEffect:
    """Mock Effect avec debug."""
    def __init__(self, width, height, color_palette):
        self.width = width
        self.height = height
        self.color_palette = color_palette
        self.time = 0
        self.update_count = 0
        self.render_count = 0
        self.logger = setup_logging()
        self.logger.info(f"Effect créé: {color_palette}")
    
    def update(self, audio_data, delta_time):
        self.time += delta_time
        self.update_count += 1
        if self.update_count % 50 == 0:
            self.logger.debug(f"Effect update #{self.update_count}: time={self.time:.2f}s")
    
    def render(self, surface):
        self.render_count += 1
        if self.render_count % 50 == 0:
            self.logger.debug(f"Effect render #{self.render_count}")
    
    def cleanup(self):
        self.logger.info(f"Effect cleanup: {self.update_count} updates, {self.render_count} renders")


class DebugEffectManager:
    """Mock EffectManager avec debug."""
    def __init__(self, analyzer, renderer, effect_type='bars', color_palette='winamp_classic'):
        self.analyzer = analyzer
        self.renderer = renderer
        self.effect_type = effect_type
        self.color_palette = color_palette
        self.current_effect = DebugEffect(renderer.width, renderer.height, color_palette)
        self._current_effect_name = effect_type
        self.logger = setup_logging()
        self.logger.info(f"EffectManager créé: effet={effect_type}, palette={color_palette}")
    
    def init(self):
        self.logger.info("EffectManager init()")


def debug_playback_loop(analyzer, renderer, effect_manager, duration=5):
    """Boucle de lecture avec debug détaillé."""
    logger = setup_logging()
    logger.info("=" * 70)
    logger.info("DEBUT DE LA BOUCLE DE LECTURE (Debug Mode)")
    logger.info("=" * 70)
    
    start_time = time.time()
    iteration = 0
    errors = []
    warnings_list = []
    
    try:
        # Démarrer le stream
        logger.info("Démarrage du stream...")
        analyzer.start_stream()
        
        # Initialiser le renderer
        logger.info("Initialisation du renderer...")
        renderer.init()
        
        effect_manager.init()
        
        logger.info("Boucle de lecture démarrée")
        
        while time.time() - start_time < duration:
            iteration += 1
            
            # Gérer les événements
            logger.debug(f"Itération {iteration}: handle_events()")
            if not renderer.handle_events():
                warnings_list.append(f"Événement QUIT à itération {iteration}")
                logger.warning(f"Événement QUIT à itération {iteration}")
                break
            
            # Obtenir delta time
            delta_time = renderer.clock.tick(30) / 1000.0
            logger.debug(f"Itération {iteration}: delta_time={delta_time:.4f}s")
            
            # Obtenir les données audio
            logger.debug(f"Itération {iteration}: get_next_chunk()")
            chunk = analyzer.get_next_chunk()
            if chunk is None:
                warnings_list.append(f"Chunk None à itération {iteration}")
                logger.warning(f"Chunk None à itération {iteration} - FIN DU FICHIER ?")
                break
            
            logger.debug(f"Itération {iteration}: analyze_chunk()")
            audio_data = analyzer.analyze_chunk(chunk)
            
            # Mettre à jour et rendre
            logger.debug(f"Itération {iteration}: effect.update()")
            effect_manager.current_effect.update(audio_data, delta_time)
            
            logger.debug(f"Itération {iteration}: get_surface()")
            surface = renderer.get_surface()
            
            logger.debug(f"Itération {iteration}: effect.render()")
            effect_manager.current_effect.render(surface)
            
            # **PROBLÈME POTENTIEL ICI**
            # Dans la vraie GUI, il y a:
            # frame = self._capture_frame_copy(surface)  # AVANT present()
            # self.root.after(0, self._update_preview, frame)
            # self.preview_renderer.present()
            
            logger.debug(f"Itération {iteration}: present()")
            
            # Simuler la capture de frame (comme dans la vraie GUI)
            try:
                logger.debug(f"Itération {iteration}: capture frame (simulée)")
                # surface_copy = surface.copy()  # C'est ce qui a été ajouté pour éviter le deadlock
                # frame = self._capture_frame_copy(surface)
                # self.root.after(0, self._update_preview, frame)
            except Exception as e:
                errors.append(f"Itération {iteration}: Capture frame échouée: {e}")
                logger.error(f"Capture frame échouée: {e}")
            
            renderer.present()
            
            # Log périodique
            if iteration % 10 == 0:
                elapsed = time.time() - start_time
                logger.info(f"Itération {iteration}: Volume={audio_data.get('volume', 0):.4f}, "
                          f"Temps écoulé={elapsed:.1f}s")
            
            # Vérifier si ça bloque
            if iteration % 100 == 0:
                current_time = time.time()
                if current_time - start_time > duration:
                    break
                
        elapsed = time.time() - start_time
        
        logger.info("=" * 70)
        logger.info("FIN DE LA BOUCLE DE LECTURE")
        logger.info("=" * 70)
        logger.info(f"Itérations: {iteration}")
        logger.info(f"Durée: {elapsed:.1f}s")
        logger.info(f"FPS estimé: {iteration/elapsed:.1f}")
        logger.info(f"Erreurs: {len(errors)}")
        logger.info(f"Avertissements: {len(warnings_list)}")
        
        if errors:
            logger.error("ERREURS DETECTEES:")
            for error in errors:
                logger.error(f"  - {error}")
        
        if warnings_list:
            logger.warning("AVERTISSEMENTS:")
            for warning in warnings_list:
                logger.warning(f"  - {warning}")
        
        return True
        
    except Exception as e:
        logger.error(f"ERREUR CRITIQUE: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        analyzer.cleanup()
        renderer.cleanup()
        effect_manager.current_effect.cleanup()


def debug_gui_simulation():
    """Simule le flux GUI complet avec debug."""
    logger = setup_logging()
    logger.info("=" * 70)
    logger.info("DEBUT DE LA SIMULATION GUI")
    logger.info("=" * 70)
    
    audio_file = 'input/gruffius_short.mp3'
    
    # Vérifier le fichier
    if not os.path.exists(audio_file):
        logger.error(f"Fichier non trouvé: {audio_file}")
        # Essayer le chemin absolu
        audio_file = os.path.abspath(audio_file)
        if not os.path.exists(audio_file):
            logger.error(f"Fichier toujours non trouvé: {audio_file}")
            return False
    
    logger.info(f"Fichier audio: {audio_file}")
    
    # Créer les composants
    logger.info("Création des composants...")
    analyzer = DebugAudioAnalyzer(audio_file)
    renderer = DebugRenderer(800, 600, fullscreen=False, fps=30)
    effect_manager = DebugEffectManager(
        analyzer=analyzer,
        renderer=renderer,
        effect_type='bars',
        color_palette='winamp_classic'
    )
    
    # Simuler _start_playback
    logger.info("Simule _start_playback()...")
    
    # Exécuter la boucle de lecture
    success = debug_playback_loop(analyzer, renderer, effect_manager, duration=5)
    
    logger.info("Simule _stop_playback()...")
    
    if success:
        logger.info("✓ Simulation GUI terminée avec succès")
    else:
        logger.error("✗ Simulation GUI échouée")
    
    return success


def main():
    print("=" * 70)
    print("DEBUG GUI PLAYBACK - Visualisateur Psychédélique")
    print("=" * 70)
    print(f"Log file: {LOG_FILE}")
    print(f"Mode: Debug avec mocks")
    print()
    
    logger = setup_logging()
    logger.info("Démarrage du debug GUI playback")
    
    success = debug_gui_simulation()
    
    print("\n" + "=" * 70)
    if success:
        print("✓ DEBUG TERMINÉ AVEC SUCCÈS")
    else:
        print("✗ DEBUG ÉCHOUÉ")
    print(f"Fichier de log: {LOG_FILE}")
    print("=" * 70)
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
