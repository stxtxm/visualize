#!/usr/bin/env python3
"""
Test E2E simplifié pour vérifier la chaîne de rendu SANS affichage.
Teste que les effets peuvent être créés, mis à jour et rendre des frames
sans avoir besoin d'afficher réellement à l'écran.
"""

import sys
import os
import numpy as np

# Ajouter le projet au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Activer NO_SOUND pour les tests
os.environ['NO_SOUND'] = '1'


def test_audio_analyzer():
    """Test l'AudioAnalyzer en mode NO_SOUND."""
    print("\n=== Test 1: AudioAnalyzer (mode NO_SOUND) ===")
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
        
        # Obtenir plusieurs chunks et analyser
        for i in range(10):
            chunk = analyzer.get_next_chunk()
            assert chunk is not None, f"Chunk {i} non obtenu"
            assert len(chunk) > 0, f"Chunk {i} vide"
            
            audio_data = analyzer.analyze_chunk(chunk)
            assert audio_data is not None, f"Analyse {i} échouée"
            assert 'volume' in audio_data, f"volume manquant {i}"
            assert 'frequency_bands' in audio_data, f"frequency_bands manquant {i}"
            assert 'spectrum' in audio_data, f"spectrum manquant {i}"
            assert 'bass' in audio_data, f"bass manquant {i}"
            assert 'mids' in audio_data, f"mids manquant {i}"
            assert 'treble' in audio_data, f"treble manquant {i}"
            
            # Vérifier les valeurs
            assert 0 <= audio_data['volume'] <= 1, f"Volume hors plage: {audio_data['volume']}"
            assert 0 <= audio_data['bass'] <= 1, f"Bass hors plage: {audio_data['bass']}"
            assert len(audio_data['frequency_bands']) == 16, f"Nombre de bandes incorrect: {len(audio_data['frequency_bands'])}"
        
        print("✓ AudioAnalyzer fonctionne correctement")
        print(f"  - 10 chunks analysés avec succès")
        print(f"  - Dernier volume: {audio_data['volume']:.4f}")
        print(f"  - Dernier bass: {audio_data['bass']:.4f}")
        
        # Nettoyer
        analyzer.cleanup()
        return True
    except Exception as e:
        print(f"✗ AudioAnalyzer échoué: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_effect_bars_logic():
    """Test la logique de l'effet Bars (sans rendu visuel)."""
    print("\n=== Test 2: Logique Effet Bars ===")
    try:
        from effects.bars import BarEffect
        from audio.analyzer import AudioAnalyzer
        
        # Créer l'analyzer
        analyzer = AudioAnalyzer("/app/input/test.mp3", chunk_size=1024, sample_rate=44100, loop=True)
        analyzer.start_stream()
        
        # Créer l'effet Bars
        effect = BarEffect(width=800, height=600, color_palette='winamp_classic')
        
        # Obtenir des données audio
        chunk = analyzer.get_next_chunk()
        audio_data = analyzer.analyze_chunk(chunk)
        
        # Mettre à jour l'effet
        effect.update(audio_data, delta_time=0.033)
        
        # Vérifier que l'effet a bien été mis à jour
        assert effect.bar_heights is not None, "bar_heights non initialisé"
        assert len(effect.bar_heights) > 0, "bar_heights vide"
        assert effect.time > 0, "time non incrémenté"
        
        print("✓ Logique Effet Bars fonctionne correctement")
        print(f"  - Nombre de barres: {len(effect.bar_heights)}")
        print(f"  - Hauteur moyenne: {np.mean(effect.bar_heights):.2f}")
        
        # Nettoyer
        analyzer.cleanup()
        return True
    except Exception as e:
        print(f"✗ Logique Effet Bars échoué: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_effect_spectrum_logic():
    """Test la logique de l'effet Spectrum."""
    print("\n=== Test 3: Logique Effet Spectrum ===")
    try:
        from effects.spectrum import SpectrumEffect
        from audio.analyzer import AudioAnalyzer
        
        # Créer l'analyzer
        analyzer = AudioAnalyzer("/app/input/test.mp3", chunk_size=1024, sample_rate=44100, loop=True)
        analyzer.start_stream()
        
        # Créer l'effet Spectrum
        effect = SpectrumEffect(width=800, height=600, color_palette='rainbow')
        
        # Obtenir des données audio
        chunk = analyzer.get_next_chunk()
        audio_data = analyzer.analyze_chunk(chunk)
        
        # Mettre à jour l'effet
        effect.update(audio_data, delta_time=0.033)
        
        # Vérifier que l'effet a bien été mis à jour
        assert effect.time > 0, "time non incrémenté"
        
        print("✓ Logique Effet Spectrum fonctionne correctement")
        
        # Nettoyer
        analyzer.cleanup()
        return True
    except Exception as e:
        print(f"✗ Logique Effet Spectrum échoué: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_effect_plasma_logic():
    """Test la logique de l'effet Plasma."""
    print("\n=== Test 4: Logique Effet Plasma ===")
    try:
        from effects.plasma import PlasmaEffect
        from audio.analyzer import AudioAnalyzer
        
        # Créer l'analyzer
        analyzer = AudioAnalyzer("/app/input/test.mp3", chunk_size=1024, sample_rate=44100, loop=True)
        analyzer.start_stream()
        
        # Créer l'effet Plasma
        effect = PlasmaEffect(width=800, height=600, color_palette='psychedelic')
        
        # Obtenir des données audio
        chunk = analyzer.get_next_chunk()
        audio_data = analyzer.analyze_chunk(chunk)
        
        # Mettre à jour l'effet
        effect.update(audio_data, delta_time=0.033)
        
        # Vérifier que l'effet a bien été mis à jour
        assert effect.time > 0, "time non incrémenté"
        
        print("✓ Logique Effet Plasma fonctionne correctement")
        
        # Nettoyer
        analyzer.cleanup()
        return True
    except Exception as e:
        print(f"✗ Logique Effet Plasma échoué: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_effect_manager():
    """Test le gestionnaire d'effets."""
    print("\n=== Test 5: EffectManager ===")
    try:
        from effects.manager import EffectManager
        from audio.analyzer import AudioAnalyzer
        from renderer.pygame_renderer import PygameRenderer
        
        # Créer les composants
        analyzer = AudioAnalyzer("/app/input/test.mp3", chunk_size=1024, sample_rate=44100, loop=True)
        analyzer.start_stream()
        
        # Créer un mock renderer (pour obtenir width/height)
        class MockRenderer:
            def __init__(self):
                self.width = 800
                self.height = 600
        
        # Créer le gestionnaire d'effets
        effect_manager = EffectManager(
            analyzer=analyzer,
            renderer=MockRenderer(),
            effect_type='bars',
            color_palette='winamp_classic'
        )
        effect_manager.init()
        
        # Vérifier que l'effet a été créé
        assert effect_manager.current_effect is not None, "Effet non créé"
        
        # Obtenir des données audio
        chunk = analyzer.get_next_chunk()
        audio_data = analyzer.analyze_chunk(chunk)
        
        # Mettre à jour l'effet via le manager
        effect_manager.update(audio_data, delta_time=0.033)
        
        print("✓ EffectManager fonctionne correctement")
        print(f"  - Effet actif: {effect_manager._current_effect_name}")
        
        # Nettoyer
        analyzer.cleanup()
        return True
    except Exception as e:
        print(f"✗ EffectManager échoué: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_pipeline_logic():
    """Test la chaîne complète (sans rendu visuel)."""
    print("\n=== Test 6: Chaîne complète (10 itérations) ===")
    try:
        from effects.manager import EffectManager
        from audio.analyzer import AudioAnalyzer
        
        # Créer l'analyzer
        analyzer = AudioAnalyzer("/app/input/test.mp3", chunk_size=1024, sample_rate=44100, loop=True)
        analyzer.start_stream()
        
        # Créer un mock renderer
        class MockRenderer:
            def __init__(self):
                self.width = 800
                self.height = 600
        
        # Créer le gestionnaire d'effets
        effect_manager = EffectManager(
            analyzer=analyzer,
            renderer=MockRenderer(),
            effect_type='bars',
            color_palette='winamp_classic'
        )
        effect_manager.init()
        
        # Tester 10 itérations
        print("  Exécution de 10 itérations...")
        for i in range(10):
            chunk = analyzer.get_next_chunk()
            if chunk is None:
                break
            
            audio_data = analyzer.analyze_chunk(chunk)
            effect_manager.update(audio_data, delta_time=0.033)
            
            # Vérifier que l'effet a été mis à jour
            assert effect_manager.current_effect is not None, f"Effet None à l'itération {i}"
        
        print(f"✓ Chaîne complète fonctionne - {i+1} itérations exécutées")
        
        # Nettoyer
        analyzer.cleanup()
        return True
    except Exception as e:
        print(f"✗ Chaîne complète échouée: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Exécute tous les tests E2E simplifiés."""
    print("=" * 60)
    print("Test E2E Simplifié: Affichage vidéo dans la GUI")
    print("Mode: NO_SOUND=1 (sans dépendance audio)")
    print("= Sans affichage graphique =")
    print("=" * 60)
    
    results = []
    
    # Exécuter les tests
    results.append(("AudioAnalyzer", test_audio_analyzer()))
    results.append(("Effet Bars Logic", test_effect_bars_logic()))
    results.append(("Effet Spectrum Logic", test_effect_spectrum_logic()))
    results.append(("Effet Plasma Logic", test_effect_plasma_logic()))
    results.append(("EffectManager", test_effect_manager()))
    results.append(("Chaîne complète", test_full_pipeline_logic()))
    
    # Afficher le résumé
    print("\n" + "=" * 60)
    print("RÉSULTATS DES TESTS E2E SIMPLIFIÉS")
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
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
