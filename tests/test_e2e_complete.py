#!/usr/bin/env python3
"""
Test E2E Complet - Reproduit le problème utilisateur
Flow: Ouvrir GUI → Sélectionner fichier → Lecture → Vérification
"""

import sys
import os
import time
import threading
import queue

# Configuration
AUDIO_FILE = 'input/gruffius_short.mp3'
TEST_DURATION = 10  # Secondes d'attente
NO_SOUND = True  # Forcer le mode sans son

# File pour les logs
LOG_FILE = '/tmp/visualize_e2e_test.log'

# Initialisation des logs
def setup_logging():
    """Configure le logging vers fichier et console"""
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, mode='w'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger('e2e_test')


class E2ETest:
    """Test E2E complet"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.log_queue = queue.Queue()
        self.test_passed = False
        self.test_failed = False
        self.error_message = ""
        
    def setup_x11(self):
        """Configure X11 pour le conteneur"""
        os.environ['DISPLAY'] = ':0'
        os.environ['NO_SOUND'] = '1' if NO_SOUND else '0'
        os.environ['SDL_VIDEODRIVER'] = 'x11'
        os.environ['SDL_RENDER_DRIVER'] = 'software'
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        
    def test_audio_analyzer(self):
        """Test 1: Analyzer avec le fichier réel"""
        self.logger.info("=== Test 1: AudioAnalyzer avec gruffius_short.mp3 ===")
        
        try:
            from audio.analyzer import AudioAnalyzer
            
            self.logger.info(f"Création analyzer pour {AUDIO_FILE}")
            start = time.time()
            
            if NO_SOUND:
                os.environ['NO_SOUND'] = '1'
            
            analyzer = AudioAnalyzer(
                AUDIO_FILE, 
                chunk_size=1024, 
                sample_rate=44100, 
                loop=True
            )
            
            elapsed = time.time() - start
            self.logger.info(f"Analyzer créé en {elapsed:.3f}s")
            self.logger.info(f"  use_simulated: {analyzer.use_simulated}")
            self.logger.info(f"  audio_data length: {len(analyzer.audio_data) if analyzer.audio_data is not None else 0}")
            
            # Tester le stream
            analyzer.start_stream()
            
            chunk = analyzer.get_next_chunk()
            if chunk is None:
                self.logger.error("  ERREUR: Premier chunk est None!")
                return False
            
            self.logger.info(f"  Premier chunk: type={type(chunk)}, length={len(chunk)}")
            
            audio_data = analyzer.analyze_chunk(chunk)
            self.logger.info(f"  Audio data: volume={audio_data.get('volume', 'N/A'):.4f}, "
                           f"bass={audio_data.get('bass', 'N/A'):.4f}")
            
            analyzer.cleanup()
            self.logger.info("✅ Test 1 PASSED")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Test 1 FAILED: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def test_pygame_renderer(self):
        """Test 2: Renderer Pygame"""
        self.logger.info("\n=== Test 2: PygameRenderer ===")
        
        try:
            from renderer.pygame_renderer import PygameRenderer
            
            self.logger.info("Initialisation du renderer...")
            start = time.time()
            
            renderer = PygameRenderer(width=800, height=600, fullscreen=False, fps=30)
            renderer.init()
            
            elapsed = time.time() - start
            self.logger.info(f"Renderer initialisé en {elapsed:.3f}s")
            self.logger.info(f"  is_initialized: {renderer.is_initialized}")
            
            # Tester get_surface
            surface = renderer.get_surface()
            self.logger.info(f"  Surface obtenue: {surface is not None}")
            
            # Tester present
            renderer.present()
            self.logger.info("  present() OK")
            
            renderer.cleanup()
            self.logger.info("✅ Test 2 PASSED")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Test 2 FAILED: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def test_effect_manager(self):
        """Test 3: EffectManager avec analyzer"""
        self.logger.info("\n=== Test 3: EffectManager ===")
        
        try:
            from audio.analyzer import AudioAnalyzer
            from effects.manager import EffectManager
            from renderer.pygame_renderer import PygameRenderer
            
            self.logger.info("Création des composants...")
            
            analyzer = AudioAnalyzer(AUDIO_FILE, chunk_size=1024, sample_rate=44100, loop=True)
            analyzer.start_stream()
            
            renderer = PygameRenderer(width=800, height=600, fullscreen=False, fps=30)
            renderer.init()
            
            effect_manager = EffectManager(
                analyzer=analyzer,
                renderer=renderer,
                effect_type='bars',
                color_palette='winamp_classic'
            )
            effect_manager.init()
            
            self.logger.info(f"  Effet actif: {effect_manager._current_effect_name}")
            self.logger.info(f"  current_effect: {effect_manager.current_effect is not None}")
            
            # Tester update et render
            chunk = analyzer.get_next_chunk()
            audio_data = analyzer.analyze_chunk(chunk)
            
            effect_manager.update(audio_data, delta_time=0.033)
            surface = renderer.get_surface()
            effect_manager.current_effect.render(surface)
            renderer.present()
            
            self.logger.info("  update() + render() OK")
            
            # Nettoyer
            effect_manager.current_effect.cleanup()
            analyzer.cleanup()
            renderer.cleanup()
            
            self.logger.info("✅ Test 3 PASSED")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Test 3 FAILED: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def test_playback_loop(self):
        """Test 4: Boucle de lecture complète (simule le clic sur Lecture)"""
        self.logger.info("\n=== Test 4: Boucle de Lecture (simule GUI) ===")
        
        try:
            from audio.analyzer import AudioAnalyzer
            from effects.manager import EffectManager
            from renderer.pygame_renderer import PygameRenderer
            
            self.logger.info("Création des composants...")
            
            analyzer = AudioAnalyzer(AUDIO_FILE, chunk_size=1024, sample_rate=44100, loop=True)
            analyzer.start_stream()
            
            renderer = PygameRenderer(width=800, height=600, fullscreen=False, fps=30)
            renderer.init()
            
            effect_manager = EffectManager(
                analyzer=analyzer,
                renderer=renderer,
                effect_type='bars',
                color_palette='winamp_classic'
            )
            effect_manager.init()
            
            self.logger.info(f"Démarrage de la boucle de lecture ({TEST_DURATION}s)...")
            
            start_time = time.time()
            iteration = 0
            
            while time.time() - start_time < TEST_DURATION:
                # Simuler la boucle de _playback_loop
                if not renderer.handle_events():
                    self.logger.warning(f"  Événement QUIT à itération {iteration}")
                    break
                
                delta_time = renderer.clock.tick(30) / 1000.0
                
                chunk = analyzer.get_next_chunk()
                if chunk is None:
                    self.logger.warning(f"  Chunk None à itération {iteration} - FIN DU FICHIER ?")
                    break
                
                audio_data = analyzer.analyze_chunk(chunk)
                
                # Update and render
                effect_manager.current_effect.update(audio_data, delta_time)
                surface = renderer.get_surface()
                effect_manager.current_effect.render(surface)
                
                # Capture frame (comme dans la GUI)
                try:
                    surface_copy = surface.copy()
                    import pygame
                    data = pygame.surfarray.array3d(surface_copy)
                    if iteration % 10 == 0:
                        self.logger.info(f"  Itération {iteration}: "
                                       f"Volume={audio_data.get('volume', 0):.4f}, "
                                       f"Temps={time.time()-start_time:.1f}s")
                except Exception as e:
                    self.logger.warning(f"  Itération {iteration}: Capture échouée: {e}")
                
                renderer.present()
                iteration += 1
            
            elapsed = time.time() - start_time
            self.logger.info(f"\nBoucle terminée:")
            self.logger.info(f"  - Itérations: {iteration}")
            self.logger.info(f"  - Durée: {elapsed:.1f}s")
            self.logger.info(f"  - FPS: {iteration/elapsed:.1f}")
            
            if iteration == 0:
                self.logger.error("❌ Test 4 FAILED: Aucune itération exécutée!")
                return False
            
            # Nettoyer
            effect_manager.current_effect.cleanup()
            analyzer.cleanup()
            renderer.cleanup()
            
            self.logger.info("✅ Test 4 PASSED")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Test 4 FAILED: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def run_all_tests(self):
        """Exécute tous les tests"""
        self.logger.info("=" * 70)
        self.logger.info("TEST E2E COMPLET - Flow Utilisateur")
        self.logger.info(f"Fichier audio: {AUDIO_FILE}")
        self.logger.info(f"Mode NO_SOUND: {NO_SOUND}")
        self.logger.info("=" * 70)
        
        results = []
        
        self.setup_x11()
        
        results.append(("AudioAnalyzer", self.test_audio_analyzer()))
        results.append(("PygameRenderer", self.test_pygame_renderer()))
        results.append(("EffectManager", self.test_effect_manager()))
        results.append(("PlaybackLoop", self.test_playback_loop()))
        
        # Résumé
        self.logger.info("\n" + "=" * 70)
        self.logger.info("RÉSULTATS")
        self.logger.info("=" * 70)
        
        passed = 0
        for name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            self.logger.info(f"{status} - {name}")
            if result:
                passed += 1
        
        self.logger.info("=" * 70)
        self.logger.info(f"Total: {passed}/{len(results)} tests passés")
        
        if passed == len(results):
            self.logger.info("\n🎉 TOUS LES TESTS PASSÉS ! La lecture devrait fonctionner.")
        else:
            self.logger.info(f"\n⚠️  {len(results)-passed} TEST(S) ÉCHOUÉ(S) !")
            self.logger.info(f"Voir {LOG_FILE} pour les détails.")
        
        return passed == len(results)


if __name__ == '__main__':
    test = E2ETest()
    success = test.run_all_tests()
    sys.exit(0 if success else 1)
