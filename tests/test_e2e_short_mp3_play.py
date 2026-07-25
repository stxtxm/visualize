#!/usr/bin/env python3
"""
Test E2E spécifique : Ajouter le MP3 short et appuyer sur lecture.
Ce test reproduit exactement le flux utilisateur pour déboguer les problèmes de lecture.

Flow:
1. Sélectionner le fichier input/gruffius_short.mp3
2. Appuyer sur le bouton "▶ Lecture"
3. Vérifier que la lecture démarre correctement
4. Capturer les logs de débogage
"""

import sys
import os
import time
import threading
import queue
import logging

# Configuration
AUDIO_FILE = 'input/gruffius_short.mp3'  # Fichier MP3 court
TEST_DURATION = 5  # Durée du test en secondes
DEBUG_MODE = True  # Mode debug activé

# Fichier de log
LOG_FILE = '/tmp/visualize_short_mp3_debug.log'

# Setup paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Activer NO_SOUND pour éviter les dépendances audio
os.environ['NO_SOUND'] = '1'
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_RENDER_DRIVER'] = 'software'
os.environ['SDL_AUDIODRIVER'] = 'dummy'


def setup_logging():
    """Configure le logging détaillé pour le débogage."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, mode='w'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Désactiver les logs trop verbeux de certaines bibliothèques
    logging.getLogger('PIL').setLevel(logging.WARNING)
    return logging.getLogger('short_mp3_test')


class ShortMP3PlayTest:
    """Test E2E pour le flux: fichier short MP3 + lecture."""
    
    def __init__(self):
        self.logger = setup_logging()
        self.log_queue = queue.Queue()
        self.test_passed = False
        self.test_failed = False
        self.error_message = ""
        self.iteration_count = 0
        self.max_volume = 0
        self.min_volume = 1
        self.volume_samples = []
        
    def test_file_exists(self):
        """Test 1: Vérifier que le fichier MP3 court existe."""
        self.logger.info("=== Test 1: Vérification fichier MP3 court ===")
        
        audio_path = AUDIO_FILE
        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', audio_path)
        
        if not os.path.exists(full_path):
            # Essayer le chemin absolu
            full_path = os.path.abspath(audio_path)
        
        if os.path.exists(full_path):
            file_size = os.path.getsize(full_path)
            self.logger.info(f"✓ Fichier trouvé: {full_path}")
            self.logger.info(f"  Taille: {file_size} octets ({file_size/1024:.1f} KB)")
            return full_path
        else:
            # Vérifier dans le répertoire courant
            if os.path.exists(audio_path):
                file_size = os.path.getsize(audio_path)
                self.logger.info(f"✓ Fichier trouvé: {audio_path}")
                self.logger.info(f"  Taille: {file_size} octets ({file_size/1024:.1f} KB)")
                return audio_path
        
        self.logger.error(f"✗ Fichier non trouvé: {audio_path}")
        self.logger.error(f"  Chemin testé: {full_path}")
        return None
    
    def test_audio_analyzer_with_short_mp3(self):
        """Test 2: Analyzer avec le fichier MP3 court."""
        self.logger.info("\n=== Test 2: AudioAnalyzer avec gruffius_short.mp3 ===")
        
        try:
            from audio.analyzer import AudioAnalyzer
            
            audio_path = self.test_file_exists()
            if audio_path is None:
                return False
            
            self.logger.info(f"Création analyzer pour: {audio_path}")
            start_time = time.time()
            
            # Créer l'analyzer avec le vrai fichier
            analyzer = AudioAnalyzer(
                audio_path,
                chunk_size=1024,
                sample_rate=44100,
                loop=True
            )
            
            creation_time = time.time() - start_time
            self.logger.info(f"Analyzer créé en {creation_time:.3f}s")
            self.logger.info(f"  use_simulated: {analyzer.use_simulated}")
            self.logger.info(f"  audio_data: {analyzer.audio_data is not None}")
            if analyzer.audio_data is not None:
                self.logger.info(f"  audio_data length: {len(analyzer.audio_data)}")
            
            # Démarrer le stream
            self.logger.info("Démarrage du stream...")
            start_stream_time = time.time()
            analyzer.start_stream()
            stream_time = time.time() - start_stream_time
            self.logger.info(f"Stream démarré en {stream_time:.3f}s")
            self.logger.info(f"  is_playing: {analyzer.is_playing}")
            
            # Tester la récupération de chunks
            self.logger.info("Récupération des premiers chunks...")
            
            chunk = analyzer.get_next_chunk()
            if chunk is None:
                self.logger.error("  ✗ ERREUR: Premier chunk est None!")
                analyzer.cleanup()
                return False
            
            self.logger.info(f"  ✓ Premier chunk: type={type(chunk)}, length={len(chunk)}")
            
            # Analyser plusieurs chunks
            for i in range(5):
                if chunk is None:
                    self.logger.warning(f"  Chunk {i} is None - break")
                    break
                    
                audio_data = analyzer.analyze_chunk(chunk)
                
                if audio_data is None:
                    self.logger.error(f"  ✗ Audio data None à chunk {i}")
                    break
                
                volume = audio_data.get('volume', 0)
                self.volume_samples.append(volume)
                self.max_volume = max(self.max_volume, volume)
                self.min_volume = min(self.min_volume, volume)
                
                self.logger.info(f"  Chunk {i}: volume={volume:.4f}, bass={audio_data.get('bass', 0):.4f}, "
                               f"mids={audio_data.get('mids', 0):.4f}, treble={audio_data.get('treble', 0):.4f}")
                
                # Vérifier que les données sont valides
                assert volume is not None, f"Volume manquant à chunk {i}"
                assert 0 <= volume <= 1, f"Volume hors plage: {volume}"
                
                # Prochain chunk
                chunk = analyzer.get_next_chunk()
            
            # Résumé
            self.logger.info(f"\n  Statistiques après 5 chunks:")
            self.logger.info(f"    - Volume min: {self.min_volume:.4f}")
            self.logger.info(f"    - Volume max: {self.max_volume:.4f}")
            self.logger.info(f"    - Volume moyen: {sum(self.volume_samples)/len(self.volume_samples):.4f}")
            
            # Nettoyer
            self.logger.info("Nettoyage analyzer...")
            analyzer.cleanup()
            
            self.logger.info("✓ Test AudioAnalyzer PASSED")
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Test AudioAnalyzer FAILED: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def test_playback_start_stop(self):
        """Test 3: Démarrage et arrêt de la lecture (simule appui sur bouton Lecture)."""
        self.logger.info("\n=== Test 3: Démarrage/Arrêt Lecture (simule GUI) ===")
        
        try:
            from audio.analyzer import AudioAnalyzer
            from effects.manager import EffectManager
            from renderer.pygame_renderer import PygameRenderer
            
            audio_path = self.test_file_exists()
            if audio_path is None:
                return False
            
            self.logger.info("Création des composants...")
            
            # Créer l'analyzer
            analyzer = AudioAnalyzer(
                audio_path,
                chunk_size=1024,
                sample_rate=44100,
                loop=True
            )
            
            self.logger.info("  Analyzer créé")
            
            # Créer le renderer
            renderer = PygameRenderer(
                width=800,
                height=600,
                fullscreen=False,
                fps=30
            )
            
            self.logger.info("  Renderer créé")
            
            # Initialiser le renderer
            renderer.init()
            self.logger.info("  Renderer initialisé")
            
            # Créer le effect manager
            effect_manager = EffectManager(
                analyzer=analyzer,
                renderer=renderer,
                effect_type='bars',
                color_palette='winamp_classic'
            )
            effect_manager.init()
            
            self.logger.info(f"  Effect manager créé (effet: {effect_manager._current_effect_name})")
            
            # Démarrer le stream (simule appui sur Lecture)
            self.logger.info("\nDémarrage du stream (simule ▶ Lecture)...")
            analyzer.start_stream()
            
            # Simuler la boucle de lecture
            self.logger.info(f"Exécution de la boucle pour {TEST_DURATION}s...")
            
            start_time = time.time()
            iteration = 0
            
            while time.time() - start_time < TEST_DURATION:
                iteration += 1
                
                # Gérer les événements
                if not renderer.handle_events():
                    self.logger.warning(f"  Événement QUIT à itération {iteration}")
                    break
                
                # Obtenir delta time
                delta_time = renderer.clock.tick(30) / 1000.0
                
                # Obtenir les données audio
                chunk = analyzer.get_next_chunk()
                if chunk is None:
                    self.logger.warning(f"  Chunk None à itération {iteration} - FIN DU FICHIER ?")
                    break
                
                audio_data = analyzer.analyze_chunk(chunk)
                
                # Mettre à jour et rendre
                effect_manager.current_effect.update(audio_data, delta_time)
                surface = renderer.get_surface()
                effect_manager.current_effect.render(surface)
                renderer.present()
                
                # Log tous les 10 itérations
                if iteration % 10 == 0:
                    volume = audio_data.get('volume', 0)
                    self.volume_samples.append(volume)
                    self.logger.info(f"  Itération {iteration}: Volume={volume:.4f}, Temps écoulé={time.time()-start_time:.1f}s")
                
                self.iteration_count = iteration
            
            elapsed = time.time() - start_time
            
            self.logger.info(f"\nBoucle terminée:")
            self.logger.info(f"  - Itérations: {iteration}")
            self.logger.info(f"  - Durée: {elapsed:.1f}s")
            self.logger.info(f"  - FPS: {iteration/elapsed:.1f}")
            
            if iteration == 0:
                self.logger.error("✗ Aucune itération exécutée!")
                return False
            
            # Arrêter (simule appui sur Arrêter)
            self.logger.info("\nArrêt de la lecture (simule ⏹ Arrêter)...")
            
            # Nettoyer
            effect_manager.current_effect.cleanup()
            analyzer.cleanup()
            renderer.cleanup()
            
            self.logger.info("✓ Test Playback PASSED")
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Test Playback FAILED: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def test_minimal_gui_flow(self):
        """Test 4: Flux GUI minimal (sans interface réelle)."""
        self.logger.info("\n=== Test 4: Flux GUI Minimal ===")
        
        try:
            from audio.analyzer import AudioAnalyzer
            from effects.manager import EffectManager
            
            audio_path = self.test_file_exists()
            if audio_path is None:
                return False
            
            self.logger.info("Simule le flux utilisateur:")
            self.logger.info("  1. Sélectionner fichier: " + audio_path)
            
            # Étape 1: Sélection du fichier (équivalent à _open_file)
            # self.audio_file.set(audio_path)
            
            self.logger.info("  2. Appui sur ▶ Lecture")
            
            # Étape 2: _toggle_playback -> _start_playback
            
            # Initialisation (comme dans _start_playback)
            self.logger.info("     - Création AudioAnalyzer...")
            analyzer = AudioAnalyzer(audio_path)
            
            self.logger.info("     - Récupération résolution...")
            width, height = 800, 600  # dev preset
            
            self.logger.info("     - Création PygameRenderer...")
            try:
                from renderer.pygame_renderer import PygameRenderer
                renderer = PygameRenderer(
                    width=width,
                    height=height,
                    fullscreen=False,
                    fps=30
                )
            except Exception as e:
                self.logger.warning(f"     ⚠ PygameRenderer échoué: {e}")
                # Utiliser un mock si Pygame échoue
                class MockRenderer:
                    def __init__(self):
                        self.width = width
                        self.height = height
                        self.clock = type('obj', (object,), {'tick': lambda fps: 33})()
                    def init(self): pass
                    def get_surface(self): return type('obj', (object,), {'fill': lambda x: None})()
                    def present(self): pass
                    def handle_events(self): return True
                    def cleanup(self): pass
                renderer = MockRenderer()
            
            self.logger.info("     - Création EffectManager...")
            effect_manager = EffectManager(
                analyzer=analyzer,
                renderer=renderer,
                effect_type='bars',
                color_palette='winamp_classic'
            )
            effect_manager.init()
            
            self.logger.info("     - Démarrage playback thread...")
            
            # Démarrer le stream
            analyzer.start_stream()
            
            # Exécuter quelques itérations
            self.logger.info("     - Exécution de 10 itérations...")
            for i in range(10):
                if hasattr(renderer, 'clock'):
                    delta_time = renderer.clock.tick(30) / 1000.0
                else:
                    delta_time = 0.033
                
                chunk = analyzer.get_next_chunk()
                if chunk is None:
                    self.logger.warning(f"       Chunk None à itération {i}")
                    break
                
                audio_data = analyzer.analyze_chunk(chunk)
                effect_manager.current_effect.update(audio_data, delta_time)
                
                if i % 3 == 0:
                    self.logger.info(f"       Itération {i}: OK")
            
            # Nettoyer (comme dans _stop_playback)
            self.logger.info("  3. Appui sur ⏹ Arrêter")
            analyzer.cleanup()
            if hasattr(renderer, 'cleanup'):
                renderer.cleanup()
            
            self.logger.info("✓ Flux GUI Minimal PASSED")
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Flux GUI Minimal FAILED: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def run_all_tests(self):
        """Exécute tous les tests."""
        self.logger.info("=" * 70)
        self.logger.info("TEST E2E: MP3 Court + Lecture")
        self.logger.info(f"Fichier: {AUDIO_FILE}")
        self.logger.info(f"Durée test: {TEST_DURATION}s")
        self.logger.info(f"Mode debug: {DEBUG_MODE}")
        self.logger.info("=" * 70)
        
        results = []
        
        # Exécuter les tests dans l'ordre
        file_path = self.test_file_exists()
        if file_path:
            results.append(("Fichier Existe", True))
        else:
            results.append(("Fichier Existe", False))
            self.logger.error("Arrêt: fichier MP3 court non trouvé")
            return False
        
        results.append(("AudioAnalyzer", self.test_audio_analyzer_with_short_mp3()))
        results.append(("Playback Start/Stop", self.test_playback_start_stop()))
        results.append(("Flux GUI Minimal", self.test_minimal_gui_flow()))
        
        # Résumé
        self.logger.info("\n" + "=" * 70)
        self.logger.info("RÉSULTATS")
        self.logger.info("=" * 70)
        
        passed = 0
        for name, result in results:
            status = "✓ PASSED" if result else "✗ FAILED"
            self.logger.info(f"{status} - {name}")
            if result:
                passed += 1
        
        self.logger.info("=" * 70)
        self.logger.info(f"Total: {passed}/{len(results)} tests passés")
        
        if passed == len(results):
            self.logger.info("\n🎉 TOUS LES TESTS PASSÉS !")
            self.logger.info(f"Le flux 'Ajouter MP3 short + Lecture' fonctionne correctement.")
        else:
            self.logger.info(f"\n⚠️  {len(results)-passed} TEST(S) ÉCHOUÉ(S) !")
            self.logger.info(f"Voir {LOG_FILE} pour les détails.")
        
        # Statistiques
        if self.volume_samples:
            self.logger.info(f"\nStatistiques audio:")
            self.logger.info(f"  Volume samples: {len(self.volume_samples)}")
            self.logger.info(f"  Volume moyen: {sum(self.volume_samples)/len(self.volume_samples):.4f}")
            self.logger.info(f"  Volume max: {self.max_volume:.4f}")
            self.logger.info(f"  Itérations totales: {self.iteration_count}")
        
        return passed == len(results)


def main():
    """Point d'entrée principal."""
    print("=" * 70)
    print("Test E2E: Ajouter MP3 Short + Appuyer sur Lecture")
    print("=" * 70)
    print(f"Fichier test: {AUDIO_FILE}")
    print(f"Log file: {LOG_FILE}")
    print()
    
    # Exécuter les tests
    test = ShortMP3PlayTest()
    success = test.run_all_tests()
    
    # Message final
    print("\n" + "=" * 70)
    if success:
        print("✓ TESTS TERMINÉS AVEC SUCCÈS")
        print(f"  Fichier de log: {LOG_FILE}")
    else:
        print("✗ CERTAINS TESTS ONT ÉCHOUÉ")
        print(f"  Voir {LOG_FILE} pour les détails du débogage")
    print("=" * 70)
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
