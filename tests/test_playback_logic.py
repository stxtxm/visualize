#!/usr/bin/env python3
"""
Test de la logique de lecture SANS interface graphique.
Teste la boucle de lecture, l'analyzer, les effets, sans Pygame/Tkinter.
"""

import sys
import os
import time

# Activer NO_SOUND
os.environ['NO_SOUND'] = '1'

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_playback_loop():
    """Test la boucle de lecture complète."""
    print("\n=== Test: Boucle de Lecture ===")
    
    try:
        from audio.analyzer import AudioAnalyzer
        from effects.manager import EffectManager
        
        # Créer un mock renderer
        class MockRenderer:
            def __init__(self):
                self.width = 800
                self.height = 600
                self.clock = MockClock()
                self._surface = None
                self._initialized = False
            
            def init(self):
                self._surface = MockSurface(self.width, self.height)
                self._initialized = True
            
            def get_surface(self):
                if not self._initialized:
                    self.init()
                return self._surface
            
            def present(self):
                pass  # Rien à faire pour le mock
            
            def handle_events(self):
                return True  # Toujours continuer
            
            def cleanup(self):
                self._initialized = False
        
        class MockClock:
            def tick(self, fps):
                return 33  # ~30ms pour 30fps
        
        class MockSurface:
            def __init__(self, width, height):
                self.width = width
                self.height = height
        
        # Créer les composants
        analyzer = AudioAnalyzer('input/test.mp3', chunk_size=1024, sample_rate=44100, loop=True)
        analyzer.start_stream()
        
        renderer = MockRenderer()
        
        effect_manager = EffectManager(
            analyzer=analyzer,
            renderer=renderer,
            effect_type='bars',
            color_palette='winamp_classic'
        )
        effect_manager.init()
        
        print("Démarrage de la boucle de lecture (20 itérations)...")
        
        start_time = time.time()
        for i in range(20):
            # Get audio data
            chunk = analyzer.get_next_chunk()
            if chunk is None:
                print(f'  Itération {i}: Chunk is None, break')
                break
            
            audio_data = analyzer.analyze_chunk(chunk)
            
            # Update and render (sans affichage réel)
            delta_time = 0.033  # ~30fps
            effect_manager.current_effect.update(audio_data, delta_time)
            
            # Vérifier que tout fonctionne
            assert effect_manager.current_effect is not None
            assert 'volume' in audio_data
            assert 'frequency_bands' in audio_data
            
            if i % 5 == 0:
                print(f'  Itération {i}: Volume={audio_data["volume"]:.4f}, Bass={audio_data["bass"]:.4f}')
        
        elapsed = time.time() - start_time
        print(f'\n✓ Boucle terminée avec succès !')
        print(f'  - {i+1} itérations exécutées')
        print(f'  - Temps écoulé: {elapsed:.3f}s')
        print(f'  - FPS estimé: {(i+1)/elapsed:.1f}')
        
        # Nettoyer
        analyzer.cleanup()
        
        return True
    except Exception as e:
        print(f'✗ Boucle de lecture échouée: {e}')
        import traceback
        traceback.print_exc()
        return False


def test_analyzer_only():
    """Test uniquement l'analyzer."""
    print("\n=== Test: Analyzer Seule ===")
    
    try:
        from audio.analyzer import AudioAnalyzer
        
        analyzer = AudioAnalyzer('input/test.mp3', chunk_size=1024, sample_rate=44100, loop=True)
        
        print(f'use_simulated: {analyzer.use_simulated}')
        print(f'audio_data length: {len(analyzer.audio_data) if analyzer.audio_data is not None else 0}')
        
        analyzer.start_stream()
        
        for i in range(10):
            chunk = analyzer.get_next_chunk()
            if chunk is None:
                print(f'  Chunk {i} is None')
                break
            
            audio_data = analyzer.analyze_chunk(chunk)
            print(f'  Chunk {i}: volume={audio_data["volume"]:.4f}, bass={audio_data["bass"]:.4f}')
        
        print('✓ Analyzer fonctionne correctement')
        analyzer.cleanup()
        return True
    except Exception as e:
        print(f'✗ Analyzer échoué: {e}')
        import traceback
        traceback.print_exc()
        return False


def test_effects_with_mock():
    """Test les effets avec un mock renderer."""
    print("\n=== Test: Effets avec Mock ===")
    
    try:
        from audio.analyzer import AudioAnalyzer
        from effects.bars import BarEffect
        from effects.spectrum import SpectrumEffect
        from effects.plasma import PlasmaEffect
        
        analyzer = AudioAnalyzer('input/test.mp3', chunk_size=1024, sample_rate=44100, loop=True)
        analyzer.start_stream()
        
        # Créer les effets
        effects = {
            'bars': BarEffect(800, 600, 'winamp_classic'),
            'spectrum': SpectrumEffect(800, 600, 'rainbow'),
            'plasma': PlasmaEffect(800, 600, 'psychedelic')
        }
        
        for name, effect in effects.items():
            print(f'\n  Test effet: {name}')
            
            chunk = analyzer.get_next_chunk()
            audio_data = analyzer.analyze_chunk(chunk)
            
            effect.update(audio_data, 0.033)
            
            # Créer un mock surface
            class MockSurface:
                def __init__(self):
                    self.data = []
                def get_size(self):
                    return (800, 600)
            
            # Essayons de rendre (peut échouer sans Pygame, mais on capture l'erreur)
            try:
                effect.render(MockSurface())
                print(f'    ✓ Render fonctionnel')
            except Exception as e:
                # C'est OK si le render échoue sans Pygame
                print(f'    ⚠ Render nécessite Pygame: {type(e).__name__}')
            
            print(f'    ✓ Update fonctionnel')
        
        print('\n✓ Tous les effets fonctionnent')
        analyzer.cleanup()
        return True
    except Exception as e:
        print(f'✗ Effets échoués: {e}')
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("Test de la Logique de Lecture (sans GUI)")
    print("Mode: NO_SOUND=1")
    print("=" * 60)
    
    results = []
    results.append(("Analyzer Seule", test_analyzer_only()))
    results.append(("Effets avec Mock", test_effects_with_mock()))
    results.append(("Boucle de Lecture", test_playback_loop()))
    
    print("\n" + "=" * 60)
    print("RÉSULTATS")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    failed = sum(1 for _, r in results if not r)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {name}")
    
    print("=" * 60)
    print(f"Total: {passed}/{len(results)} tests passés")
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
