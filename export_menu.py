#!/usr/bin/env python3
"""
Menu interactif pour exporter des vidéos psychédéliques.
Parfait pour Fedora sans besoin de GUI complexe.
"""

import os
import subprocess
import sys

# Chemin du projet - gérer le cas où on est dans /app dans le conteneur
if os.path.exists('/app/main.py'):
    PROJECT_DIR = '/app'
else:
    PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, PROJECT_DIR)

from quality_presets import QUALITY_PRESETS, RESOLUTIONS


def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')


def print_header():
    clear_screen()
    print("=" * 70)
    print("  🎨 VISUALISATEUR PSYCHÉDÉLIQUE - Menu d'Export 🎵")
    print("=" * 70)
    print()


def print_presets():
    print("\n📊 PRESETS DE QUALITÉ/VITESSE :")
    print("-" * 70)
    for i, (name, config) in enumerate(QUALITY_PRESETS.items(), 1):
        res = RESOLUTIONS[config['resolution']]
        print(f"  [{i}] {config['name']}")
        print(f"      → {res[0]}x{res[1]}, {config['fps']}fps, {config['description']}")
        print(f"      ⏱️  Temps : {config['export_time_factor']}x temps réel")
    print()


def print_effects():
    effects = ['bars', 'circles', 'particles', 'tunnel', 'wave', 'random']
    effect_names = {
        'bars': '📊 Barres (égaliseur)',
        'circles': '⭕ Cercles pulsants',
        'particles': '✨ Particules',
        'tunnel': '🌀 Tunnel psychédélique',
        'wave': '🌊 Vagues',
        'random': '🎲 Aléatoire'
    }
    print("\n🎨 EFFETS VISUELS :")
    print("-" * 70)
    for i, effect in enumerate(effects, 1):
        print(f"  [{i}] {effect_names.get(effect, effect)}")
    print()


def print_colors():
    colors = ['psychedelic', 'retro', 'dark', 'rainbow']
    color_names = {
        'psychedelic': '🌈 Psychédélique (couleurs vives)',
        'retro': '💿 Rétro (style Winamp)',
        'dark': '🌑 Sombre (pour fond noir)',
        'rainbow': '🌟 Arc-en-ciel (dégradé fluide)'
    }
    print("\n🎨 PALETTES DE COULEURS :")
    print("-" * 70)
    for i, color in enumerate(colors, 1):
        print(f"  [{i}] {color_names.get(color, color)}")
    print()


def select_option(prompt, options, option_type=""):
    while True:
        try:
            choice = input(prompt)
            if not choice:
                return options[0]  # Default to first
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
            print(f"❌ Choix invalide. Veuillez choisir entre 1 et {len(options)}")
        except ValueError:
            print(f"❌ Veuillez entrer un nombre entre 1 et {len(options)}")


def browse_audio_file():
    """Simple file browser for audio files."""
    audio_extensions = ['.mp3', '.wav', '.flac', '.ogg', '.aac']
    
    # Check common directories (dans le conteneur, /audio contient les fichiers)
    # Prioriser /audio pour éviter de prendre les fichiers dans /app
    search_dirs = [
        '/audio',  # Dossier monté depuis ~/Music de l'hôte - PRIORITÉ
        os.path.expanduser('~/Music'),
        os.path.expanduser('~'),
    ]
    # Ne pas chercher dans PROJECT_DIR (/app) car les fichiers audio ne devraient pas être là
    
    audio_files = []
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in audio_extensions):
                        audio_files.append(os.path.join(root, file))
    
    if not audio_files:
        return input("📁 Chemin vers fichier audio : ").strip()
    
    print("\n📁 Fichiers audio trouvés :")
    print("-" * 70)
    for i, file in enumerate(audio_files[:50], 1):  # Limit to 50 files
        rel_path = os.path.relpath(file, os.path.expanduser('~'))
        print(f"  [{i}] {rel_path}")
    print()
    
    choice = input(f"📌 Sélectionner un fichier (1-{min(len(audio_files), 50)}) ou entrer le chemin : ").strip()
    
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(audio_files):
            return audio_files[idx]
    
    return choice


def main():
    print_header()
    
    # Sélection du fichier audio
    print("📄 SÉLECTION DU FICHIER AUDIO")
    print("-" * 70)
    audio_file = browse_audio_file()
    
    if not os.path.exists(audio_file):
        print(f"❌ Fichier introuvable: {audio_file}")
        sys.exit(1)
    
    audio_duration = None
    try:
        import subprocess
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', audio_file],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5
        )
        if result.returncode == 0:
            audio_duration = float(result.stdout.strip())
    except:
        pass
    
    print(f"✅ Fichier sélectionné: {os.path.basename(audio_file)}")
    if audio_duration:
        print(f"   Durée: {int(audio_duration//60)}:{int(audio_duration%60):02d}")
    print()
    
    # Sélection du preset
    print_presets()
    preset_name = select_option("⚡ Sélectionner un preset (1-5) [1=dev] : ", list(QUALITY_PRESETS.keys()))
    
    # Sélection de l'effet
    print_effects()
    effects = ['bars', 'circles', 'particles', 'tunnel', 'wave', 'random']
    effect = select_option("🎨 Sélectionner un effet (1-6) [1=barres] : ", effects)
    
    # Sélection de la palette
    print_colors()
    colors = ['psychedelic', 'retro', 'dark', 'rainbow']
    color = select_option("🎨 Sélectionner une palette (1-4) [1=psychedelic] : ", colors)
    
    # Sélection du fichier de sortie
    print("\n💾 FICHIER DE SORTIE")
    print("-" * 70)
    print("⚠️  Dans le conteneur, utilisez /app/output/ comme dossier de sortie")
    print("    Exemple: /app/output/ma_video.mp4")
    print("    Cela correspondra à ./output/ma_video.mp4 dans le projet")
    print()
    # Utiliser /app/output comme dossier de sortie par défaut
    default_output = os.path.join(
        '/app/output',
        f"{os.path.splitext(os.path.basename(audio_file))[0]}_export.mp4"
    )
    output_file = input(f"📄 Chemin de sortie [{default_output}] : ").strip()
    if not output_file:
        output_file = default_output
    
    # Créer le dossier si nécessaire
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Résumé
    clear_screen()
    print_header()
    print("✅ RÉSUMÉ DE L'EXPORT")
    print("-" * 70)
    print(f"📄 Fichier audio: {audio_file}")
    print(f"💾 Fichier sortie: {output_file}")
    
    preset = QUALITY_PRESETS[preset_name]
    res = RESOLUTIONS[preset['resolution']]
    print(f"⚡ Preset: {preset['name']}")
    print(f"   Résolution: {res[0]}x{res[1]}")
    print(f"   FPS: {preset['fps']}")
    print(f"   Vitesse: {preset['export_time_factor']}x temps réel")
    print(f"🎨 Effet: {effect}")
    print(f"🎨 Couleurs: {color}")
    
    if audio_duration:
        estimated_time = audio_duration * float(preset['export_time_factor'])
        print(f"\n⏱️  Temps d'export estimé: {int(estimated_time//60)}:{int(estimated_time%60):02d}")
    
    print()
    
    # Confirmation
    confirm = input("✅ Lancer l'export ? (O/n) : ").strip().lower()
    if confirm != 'o' and confirm != 'y' and confirm != '':
        print("❌ Export annulé.")
        sys.exit(0)
    
    # Lancer l'export
    clear_screen()
    print_header()
    print("⏳ EXPORT EN COURS...")
    print("-" * 70)
    
    cmd = [
        sys.executable, '-m', 'main',
        audio_file,
        '--export', output_file,
        '--effect', effect,
        '--color', color,
        '--preset', preset_name,
        '--no-gui'
    ]
    
    print(f"Commande: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    
    if result.returncode == 0:
        print(f"\n✅ EXPORT TERMINÉ AVEC SUCCÈS !")
        print(f"📄 Fichier: {output_file}")
        if os.path.exists(output_file):
            size_mb = os.path.getsize(output_file) / (1024 * 1024)
            print(f"   Taille: {size_mb:.1f} Mo")
        
        # Proposer de lancer la vidéo
        launch = input("\n🎬 Voulez-vous lancer la vidéo ? (O/n) : ").strip().lower()
        if launch in ('o', 'y', ''):
            try:
                if os.name == 'posix':
                    subprocess.run(['xdg-open', output_file])
                else:
                    print(f"Ouvrir: {output_file}")
            except:
                print(f"Ouvrir manuellement: {output_file}")
    else:
        print(f"\n❌ L'EXPORT A ÉCHOUÉ (code: {result.returncode})")
    
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Export annulé par l'utilisateur.")
        sys.exit(0)
