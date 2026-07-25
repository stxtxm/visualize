#!/usr/bin/env python3
"""
Test E2E pour vérifier l'affichage vidéo dans la GUI.
Teste le rendu Pygame + les effets visuels sans interface graphique.
"""

import sys
import os
import time
import numpy as np

# Ajouter le projet au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Activer NO_SOUND pour les tests
os.environ['NO_SOUND'] = '1'
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_RENDER_DRIVER'] = 'software'

def test_pygame_renderer():
    """Test le PygameRenderer en mode NO_SOUND."""
    print("\n=== Test 1: PygameRenderer ===")
    try:
        from renderer.pygame_renderer import PygameRenderer
        
        # Créer un renderer en petit format pour le test
        renderer = PygameRenderer(width=800, height=600, fullscreen=False, fps=30)
        renderer.init()
        
        # Vérifier que le renderer est initialisé
        assert renderer.is_initialized, "Renderer non initialisé"
        
        # Obtenir la surface de rendu
        surface = renderer.get_surface()
        assert surface is not None, "Surface non créée"
        
        # Tester le rendu d'une frame
        surface.fill((255, 0, 0))  # Rouge
        renderer.present()
        
        # Attendre un peu pour que le rendu soit visible
        time.sleep(1)
        
        # Tester handle_events
        result = renderer.handle_events()
        assert result == True, "handle_events a retourné False"
        
        # Nettoyer
        renderer.cleanup()
        assert not renderer.is_initialized, "Renderer toujours initialisé après cleanup"
        
        print("✓ PygameRenderer fonctionne correctement")
        return True
    except Exception as e:
        print(f"✗ PygameRenderer échoué: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_audio_analyzer():
    """Test l'AudioAnalyzer en mode NO_SOUND."""
    print("\n=== Test 2: AudioAnalyzer (mode NO_SOUND) ===")
    try:
        from audio.analyzer import AudioAnalyzer
        
        # Créer un analyzer avec un fichier fictif (NO_SOUND activé)
        analyzer = AudioAnalyzer("/app/input/test.mp3", chunk_size=1024, sample_rate=44100, loop=True)
        
        # Vérifier que les données simulées sont utilisées
        assert analyzer.use_simulated, "Données simulées non activées"
        assert analyzer.audio_data is not None, "Pas de données audio"
        assert len(analyzer.audio_data) > 0, "Données audio vides"
        
        # Démarrer le flux
        analyzer.start_stream()
        assert analyzer.is_playing, "Stream non démarré"
        
        # Obtenir un chunk
        chunk = analyzer.get_next_chunk()
        assert chunk is not None, "Chunk non obtenu"
        assert len(chunk) > 0, "Chunk vide"
        
        # Analyser le chunk
        audio_data = analyzer.analyze_chunk(chunk)
        assert audio_data is not None, "Analyse échouée"
        assert 'volume' in audio_data, "volume manquant"
        assert 'frequency_bands' in audio_data, "frequency_bands manquant"
        assert 'spectrum' in audio_data, "spectrum manquant"
        
        print(f"✓ AudioAnalyzer fonctionne correctement")
        print(f"  - Volume: {audio_data['volume']:.4f}")
        print(f"  - Bass: {audio_data['bass']:.4f}")
        print(f"  - Bands: {len(audio_data['frequency_bands'])} bandes")
        
        # Nettoyer
        analyzer.cleanup()
        return True
    except Exception as e:
        print(f"✗ AudioAnalyzer échoué: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_effect_bars():
    """Test l'effet Bars avec des données audio simulées."""
    print("\n=== Test 3: Effet Bars ===")
    try:
        from effects.bars import BarEffect
        from renderer.pygame_renderer import PygameRenderer
        from audio.analyzer import AudioAnalyzer
        import pygame
        
        # Créer les composants
        renderer = PygameRenderer(width=800, height=600, fullscreen=False, fps=30)
        renderer.init()
        
        analyzer = AudioAnalyzer("/app/input/test.mp3", chunk_size=1024, sample_rate=44100, loop=True)
        analyzer.start_stream()
        
        # Créer l'effet Bars directement
        effect = BarEffect(renderer.width, renderer.height, color_palette='winamp_classic')
        
        # Obtenir des données audio
        chunk = analyzer.get_next_chunk()
        audio_data = analyzer.analyze_chunk(chunk)
        
        # Mettre à jour et rendre l'effet
        effect.update(audio_data, delta_time=0.033)
        surface = renderer.get_surface()
        effect.render(surface)
        
        # Vérifier que le rendu a produit quelque chose
        surface_array = pygame.surfarray.array3d(surface)
        assert surface_array is not None, "Rendu échoué"
        
        print("✓ Effet Bars fonctionne correctement")
        
        # Nettoyer
        analyzer.cleanup()
        renderer.cleanup()
        return True
    except Exception as e:
        print(f"✗ Effet Bars échoué: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_effect_spectrum():
    """Test l'effet Spectrum."""
    print("\n=== Test 4: Effet Spectrum ===")
    try:
        from effects.spectrum import SpectrumEffect
        from renderer.pygame_renderer import PygameRenderer
        from audio.analyzer import AudioAnalyzer
        import pygame
        
        # Créer les composants
        renderer = PygameRenderer(width=800, height=600, fullscreen=False, fps=30)
        renderer.init()
        
        analyzer = AudioAnalyzer("/app/input/test.mp3", chunk_size=1024, sample_rate=44100, loop=True)
        analyzer.start_stream()
        
        # Créer l'effet Spectrum
        effect = SpectrumEffect(renderer.width, renderer.height, color_palette='rainbow')
        
        # Obtenir des données audio
        chunk = analyzer.get_next_chunk()
        audio_data = analyzer.analyze_chunk(chunk)
        
        # Mettre à jour et rendre
        effect.update(audio_data, delta_time=0.033)
        surface = renderer.get_surface()
        effect.render(surface)
        
        print("✓ Effet Spectrum fonctionne correctement")
        
        # Nettoyer
        analyzer.cleanup()
        renderer.cleanup()
        return True
    except Exception as e:
        print(f"✗ Effet Spectrum échoué: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_effect_plasma():
    """Test l'effet Plasma."""
    print("\n=== Test 5: Effet Plasma ===")
    try:
        from effects.plasma import PlasmaEffect
        from renderer.pygame_renderer import PygameRenderer
        from audio.analyzer import AudioAnalyzer
        
        # Créer les composants
        renderer = PygameRenderer(width=800, height=600, fullscreen=False, fps=30)
        renderer.init()
        
        analyzer = AudioAnalyzer("/app/input/test.mp3", chunk_size=1024, sample_rate=44100, loop=True)
        analyzer.start_stream()
        
        # Créer l'effet Plasma
        effect = PlasmaEffect(renderer.width, renderer.height, color_palette='psychedelic')
        
        # Obtenir des données audio
        chunk = analyzer.get_next_chunk()
        audio_data = analyzer.analyze_chunk(chunk)
        
        # Mettre à jour et rendre
        effect.update(audio_data, delta_time=0.033)
        surface = renderer.get_surface()
        effect.render(surface)
        
        print("✓ Effet Plasma fonctionne correctement")
        
        # Nettoyer
        analyzer.cleanup()
        renderer.cleanup()
        return True
    except Exception as e:
        print(f"✗ Effet Plasma échoué: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_pipeline():
    """Test la chaîne complète : Renderer + Analyzer + Effect + Multiple frames."""
    print("\n=== Test 6: Chaîne complète (10 frames) ===")
    try:
        from renderer.pygame_renderer import PygameRenderer
        from audio.analyzer import AudioAnalyzer
        from effects.manager import EffectManager
        import pygame
        
        # Créer les composants
        renderer = PygameRenderer(width=800, height=600, fullscreen=False, fps=30)
        renderer.init()
        
        analyzer = AudioAnalyzer("/app/input/test.mp3", chunk_size=1024, sample_rate=44100, loop=True)
        analyzer.start_stream()
        
        # Créer le gestionnaire d'effets avec l'effet bars
        effect_manager = EffectManager(
            analyzer=analyzer,
            renderer=renderer,
            effect_type='bars',
            color_palette='winamp_classic'
        )
        effect_manager.init()
        
        # Tester 10 frames
        print("  Rendu de 10 frames...")
        for i in range(10):
            chunk = analyzer.get_next_chunk()
            if chunk is None:
                break
            
            audio_data = analyzer.analyze_chunk(chunk)
            effect_manager.current_effect.update(audio_data, delta_time=0.033)
            effect_manager.current_effect.render(renderer.get_surface())
            renderer.present()
            
            # Vérifier que le rendu fonctionne
            surface = renderer.get_surface()
            assert surface is not None, f"Frame {i}: surface None"
        
        print(f"✓ Chaîne complète fonctionne - {i+1} frames rendues")
        
        # Nettoyer
        effect_manager.current_effect.cleanup()
        analyzer.cleanup()
        renderer.cleanup()
        return True
    except Exception as e:
        print(f"✗ Chaîne complète échouée: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Exécute tous les tests E2E."""
    print("=" * 60)
    print("Test E2E: Affichage vidéo dans la GUI")
    print("Mode: NO_SOUND=1 (sans dépendance audio)")
    print("=" * 60)
    
    # Initialiser Pygame une fois pour tous les tests
    import pygame
    # Initialiser Pygame - pygame.init() sans arguments initialise tout
    # ou bien on peut initialiser uniquement les sous-systèmes nécessaires
    pygame.init()
    
    results = []
    
    # Exécuter les tests
    results.append(("PygameRenderer", test_pygame_renderer()))
    results.append(("AudioAnalyzer", test_audio_analyzer()))
    results.append(("Effet Bars", test_effect_bars()))
    results.append(("Effet Spectrum", test_effect_spectrum()))
    results.append(("Effet Plasma", test_effect_plasma()))
    results.append(("Chaîne complète", test_full_pipeline()))
    
    # Afficher le résumé
    print("\n" + "=" * 60)
    print("RÉSULTATS DES TESTS E2E")
    print("=" * 60)
    
    passed = 0
    failed = 0
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("=" * 60)
    print(f"Total: {passed}/{len(results)} tests passés")
    
    # Quitter Pygame
    pygame.quit()
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
