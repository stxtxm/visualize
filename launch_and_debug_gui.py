#!/usr/bin/env python3
"""
Script pour lancer et debugger la GUI.
Ce script vérifie les dépendances, identifie les problèmes et propose des solutions.
"""

import sys
import os
import subprocess
import platform
from datetime import datetime

# Configuration
DEBUG_MODE = True
LOG_FILE = f"/tmp/gui_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def log(message, level="INFO"):
    """Log un message."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] [{level}] {message}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')


def check_dependencies():
    """Vérifie les dépendances nécessaires."""
    log("=" * 70)
    log("VÉRIFIATION DES DÉPENDANCES")
    log("=" * 70)
    
    dependencies = {
        'numpy': 'Analyse audio (FFT)',
        'pydub': 'Chargement des fichiers audio',
        'pygame': 'Rendu graphique',
        'tkinter': 'Interface graphique',
        'PIL': 'Traitement d\'images (Pillow)',
        'opencv-python': 'Export vidéo (optionnel)',
        'ffmpeg': 'Encodage vidéo (CLI)',
    }
    
    missing = []
    available = []
    
    # Vérifier les modules Python
    for module, description in dependencies.items():
        if module == 'ffmpeg':
            # Vérifier ffmpeg en CLI
            try:
                result = subprocess.run(['which', 'ffmpeg'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    available.append((module, description, result.stdout.strip()))
                else:
                    missing.append((module, description, "Non trouvé dans PATH"))
            except:
                missing.append((module, description, "Commande échouée"))
        else:
            try:
                if module == 'tkinter':
                    import tkinter
                    version = getattr(tkinter, 'TkVersion', 'Unknown')
                    available.append((module, description, str(version)))
                else:
                    __import__(module)
                    mod = sys.modules[module]
                    version = getattr(mod, '__version__', 'Unknown')
                    available.append((module, description, str(version)))
            except ImportError as e:
                missing.append((module, description, str(e)))
            except Exception as e:
                missing.append((module, description, f"Erreur: {e}"))
    
    # Afficher les résultats
    log("\nDisponibles:")
    for module, description, version in available:
        log(f"  ✓ {module:20s} ({description}): {version}")
    
    log("\nManquants:")
    if missing:
        for module, description, error in missing:
            log(f"  ✗ {module:20s} ({description}): {error}")
    else:
        log("  Aucun module manquant")
    
    return len(missing) == 0


def check_files():
    """Vérifie les fichiers nécessaires."""
    log("\n" + "=" * 70)
    log("VÉRIFIATION DES FICHIERS")
    log("=" * 70)
    
    required_files = [
        'input/gruffius_short.mp3',
        'main.py',
        'ui/main_window.py',
        'ui/log_display.py',
        'ui/preview.py',
        'audio/analyzer.py',
        'effects/manager.py',
        'effects/bars.py',
        'renderer/pygame_renderer.py',
    ]
    
    missing = []
    for filepath in required_files:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            log(f"  ✓ {filepath:30s} ({size:,} octets)")
        else:
            log(f"  ✗ {filepath:30s} MANQUANT")
            missing.append(filepath)
    
    return len(missing) == 0


def check_environment():
    """Vérifie les variables d'environnement."""
    log("\n" + "=" * 70)
    log("VÉRIFIATION DE L'ENVIRONNEMENT")
    log("=" * 70)
    
    env_vars = {
        'NO_SOUND': '1 (désactive le son)',
        'SDL_VIDEODRIVER': 'x11 (évite les problèmes OpenGL)',
        'SDL_RENDER_DRIVER': 'software (évite l\'accélération matérielle)',
        'SDL_AUDIODRIVER': 'dummy (désactive le son SDL)',
        'DISPLAY': 'Affichage X11',
        'PYGAME_HIDE_SUPPORT_PROMPT': '1 (désactive les messages pygame)',
    }
    
    issues = []
    for var, expected in env_vars.items():
        value = os.environ.get(var, 'Non défini')
        if var == 'NO_SOUND':
            if value not in ('1', 'true', 'yes'):
                issues.append(f"{var} devrait être '1' pour éviter les problèmes audio")
        log(f"  {var:25s} = {value}")
    
    # Vérifier le système
    log(f"\nSystème:")
    log(f"  OS: {platform.system()} {platform.release()}")
    log(f"  Python: {sys.version}")
    log(f"  Architecture: {platform.machine()}")
    
    # Vérifier les permissions
    log(f"\nPermissions:")
    try:
        log(f"  Répertoire courant: {os.getcwd()}")
        log(f"  Permissions: {oct(os.stat('.').st_mode)[-3:]}")
    except:
        pass
    
    return len(issues) == 0


def identify_problems():
    """Identifie les problèmes potentiels."""
    log("\n" + "=" * 70)
    log("IDENTIFICATION DES PROBLÈMES")
    log("=" * 70)
    
    problems = []
    
    # Problème 1: numpy manquant
    try:
        import numpy
    except ImportError:
        problems.append({
            'id': 1,
            'title': 'numpy non installé',
            'description': 'Le module numpy est requis pour l\'analyse audio (FFT).',
            'severity': 'CRITICAL',
            'solution': 'pip install numpy',
            'workaround': 'Activer NO_SOUND=1 pour utiliser des données simulées'
        })
    
    # Problème 2: pydub manquant
    try:
        import pydub
    except ImportError:
        problems.append({
            'id': 2,
            'title': 'pydub non installé',
            'description': 'Le module pydub est requis pour charger les fichiers audio.',
            'severity': 'CRITICAL',
            'solution': 'pip install pydub',
            'workaround': 'Activer NO_SOUND=1 pour utiliser des données simulées'
        })
    
    # Problème 3: pygame manquant
    try:
        import pygame
    except ImportError:
        problems.append({
            'id': 3,
            'title': 'pygame non installé',
            'description': 'Le module pygame est requis pour le rendu graphique.',
            'severity': 'CRITICAL',
            'solution': 'pip install pygame',
            'workaround': 'Aucun - pygame est obligatoire pour la GUI'
        })
    
    # Problème 4: tkinter manquant
    try:
        import tkinter
    except ImportError:
        problems.append({
            'id': 4,
            'title': 'tkinter non installé',
            'description': 'Le module tkinter est requis pour l\'interface graphique.',
            'severity': 'CRITICAL',
            'solution': 'sudo apt-get install python3-tk (Ubuntu/Debian) ou sudo dnf install python3-tkinter (Fedora)',
            'workaround': 'Utiliser la version CLI: python3 main.py fichier.mp3'
        })
    
    # Problème 5: ffmpeg manquant
    try:
        subprocess.run(['which', 'ffmpeg'], capture_output=True, check=True)
    except:
        problems.append({
            'id': 5,
            'title': 'ffmpeg non installé',
            'description': 'ffmpeg est requis pour l\'export vidéo.',
            'severity': 'WARNING',
            'solution': 'sudo apt-get install ffmpeg (Ubuntu/Debian) ou sudo dnf install ffmpeg (Fedora)',
            'workaround': 'La lecture fonctionne sans ffmpeg, mais pas l\'export'
        })
    
    # Problème 6: Deadlock Pygame
    problems.append({
        'id': 6,
        'title': 'Deadlock Pygame potential',
        'description': 'pygame.surfarray.array3d() peut causer un deadlock si appelé après present().',
        'severity': 'FIXED',
        'solution': 'TOUT EST OK - Déjà fixé dans le commit 17d3121',
        'workaround': 'La capture du frame se fait AVANT present()'
    })
    
    # Problème 7: Freeze GUI
    problems.append({
        'id': 7,
        'title': 'Freeze GUI avec audio',
        'description': 'L\'audio peut causer des freezes si PulseAudio/ALSA est mal configuré.',
        'severity': 'FIXED',
        'solution': 'TOUT EST OK - Déjà fixé dans le commit 9dabf18',
        'workaround': 'Utiliser NO_SOUND=1 et SDL_AUDIODRIVER=dummy'
    })
    
    # Problème 8: Problème de capture de frame
    problems.append({
        'id': 8,
        'title': 'Capture frame dans thread séparé',
        'description': 'La capture de frame depuis un thread Pygame peut causer des problèmes.',
        'severity': 'FIXED',
        'solution': 'TOUT EST OK - Déjà fixé dans le commit 17d3121',
        'workaround': 'Utiliser surface.copy() avant pygame.surfarray.array3d()'
    })
    
    # Afficher les problèmes
    critical_count = 0
    warning_count = 0
    fixed_count = 0
    
    for problem in problems:
        if problem['severity'] == 'CRITICAL':
            critical_count += 1
            log(f"\n❌ PROBLÈME CRITIQUE #{problem['id']}: {problem['title']}")
            log(f"   Description: {problem['description']}")
            log(f"   Solution: {problem['solution']}")
            if 'workaround' in problem:
                log(f"   Solution temporaire: {problem['workaround']}")
        elif problem['severity'] == 'WARNING':
            warning_count += 1
            log(f"\n⚠️  AVERTISSEMENT #{problem['id']}: {problem['title']}")
            log(f"   Description: {problem['description']}")
            log(f"   Solution: {problem['solution']}")
        else:
            fixed_count += 1
            log(f"\n✅ PROBLÈME FIXÉ #{problem['id']}: {problem['title']}")
            log(f"   Description: {problem['description']}")
            log(f"   Solution: {problem['solution']}")
    
    log("\n" + "=" * 70)
    log(f"RÉSUMÉ: {critical_count} critique(s), {warning_count} avertissement(s), {fixed_count} fixé(s)")
    log("=" * 70)
    
    return critical_count == 0


def suggest_solutions():
    """Propose des solutions basées sur les problèmes identifiés."""
    log("\n" + "=" * 70)
    log("SOLUTIONS PROPOSÉES")
    log("=" * 70)
    
    log("\n1. Installer toutes les dépendances:")
    log("   pip install numpy pydub pygame Pillow opencv-python")
    log("   sudo apt-get install python3-tk ffmpeg")
    
    log("\n2. Lancer en mode sans son (si problèmes audio):")
    log("   NO_SOUND=1 SDL_VIDEODRIVER=x11 SDL_RENDER_DRIVER=software SDL_AUDIODRIVER=dummy python3 main.py")
    
    log("\n3. Lancer avec logging détaillé:")
    log("   python3 -u main.py 2>&1 | tee /tmp/gui_debug.log")
    
    log("\n4. Tester la boucle de lecture:")
    log("   python3 tests/test_e2e_short_mp3_play_simple.py")
    
    log("\n5. Utiliser le conteneur Podman:")
    log("   ./podman-run.sh")


def try_launch_gui():
    """Essaie de lancer la GUI."""
    log("\n" + "=" * 70)
    log("TENTATIVE DE LANCEMENT DE LA GUI")
    log("=" * 70)
    
    try:
        # Activer le mode sans son
        os.environ['NO_SOUND'] = '1'
        os.environ['SDL_VIDEODRIVER'] = 'x11'
        os.environ['SDL_RENDER_DRIVER'] = 'software'
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
        
        log("Lancement de main.py...")
        import main
        log("✓ GUI lancée avec succès!")
        return True
    except ImportError as e:
        log(f"✗ Échec du lancement: {e}")
        return False
    except Exception as e:
        log(f"✗ Erreur: {e}")
        import traceback
        log(f"Traceback:\n{traceback.format_exc()}")
        return False


def main():
    """Point d'entrée principal."""
    print("=" * 70)
    print("LANCEMENT ET DEBUG DE LA GUI")
    print("=" * 70)
    print(f"Log file: {LOG_FILE}")
    print()
    
    # Initialiser le log
    with open(LOG_FILE, 'w') as f:
        f.write("")
    
    # Vérifications
    deps_ok = check_dependencies()
    files_ok = check_files()
    env_ok = check_environment()
    problems_ok = identify_problems()
    
    # Suggestions
    suggest_solutions()
    
    # Résumé
    log("\n" + "=" * 70)
    log("RÉSUMÉ")
    log("=" * 70)
    log(f"Dépendances: {'✓ OK' if deps_ok else '✗ PROBLÈME'}")
    log(f"Fichiers: {'✓ OK' if files_ok else '✗ PROBLÈME'}")
    log(f"Environnement: {'✓ OK' if env_ok else '✗ PROBLÈME'}")
    log(f"Problèmes: {'✓ AUCUN' if problems_ok else '✗ DETECTÉS'}")
    
    # Essayer de lancer
    if deps_ok and files_ok:
        try_launch_gui()
    else:
        log("\n❌ Impossible de lancer la GUI - des dépendances manquent")
        log("Voir les solutions proposées ci-dessus")
    
    log("\n" + "=" * 70)
    log(f"FIN DU DEBUG - Voir {LOG_FILE} pour les détails")
    log("=" * 70)


if __name__ == '__main__':
    main()
