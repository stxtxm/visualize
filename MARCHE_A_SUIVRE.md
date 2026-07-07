# Marche à suivre pour démarrer la GUI

## 🎯 Solution au problème de freeze

Le problème de **freeze lors de la lecture** était causé par :
1. **Erreur PulseAudio** : Le conteneur essayait d'accéder à `/run/user/1000/pulse/cookie` qui n'existe pas sur votre système
2. **Blocage pydub/ffmpeg** : Dans le conteneur, pydub ne pouvait pas lire les MP3 correctement
3. **Bug de fermeture** : La fenêtre ne se fermait pas à cause d'une lambda mal écrite

## ✅ Corrections apportées

### 1. Bug de fermeture de fenêtre (FIXED)
**Fichier** : `main.py` ligne 25
- **Avant** : `lambda: [app._stop_playback(), root.quit()]` (retourne une liste, ne fait rien)
- **Après** : `lambda: app._stop_playback() or root.quit()` (exécute les deux fonctions)

### 2. Gestion des erreurs audio améliorée (FIXED)
**Fichier** : `audio/analyzer.py`
- Détection automatique si pydub échoue → bascule sur des **données audio simulées**
- Support du mode **NO_SOUND=1** pour désactiver complètement le son
- Suppression du code dupliqué qui causait des erreurs

### 3. Arrêt forcé du thread (FIXED)
**Fichier** : `ui/main_window.py`
- Amélioration de `_stop_playback()` pour forcer l'arrêt des threads bloqués
- Utilisation de `ctypes` pour envoyer un signal d'arrêt au thread si nécessaire

### 4. Lancement unifié
**Fichier** : `main.py`
- `python3 main.py` détecte automatiquement tkinter (GUI) ou le fallback pygame plein écran
- Le mode `NO_SOUND=1` désactive la lecture audio tout en gardant la visualisation
- Plus besoin de scripts de lancement séparés

## 🚀 Marche à suivre pour démarrer

### Lancer la GUI (RECOMMANDÉ)

```bash
cd /home/timo/dev/visualize
python3 main.py
```

### Mode sans son (si PulseAudio ne fonctionne pas)

```bash
NO_SOUND=1 python3 main.py
```

## 📝 Commandes utiles

| Commande | Description |
|----------|-------------|
| `python3 main.py` | Lancer la GUI (détecte tkinter, sinon fallback pygame plein écran) |
| `NO_SOUND=1 python3 main.py` | Lancer sans son |
| `python3 main.py audio.mp3 -o video.mp4` | Export vidéo via CLI |
| `make standalone-appimage` | Construire l'AppImage autonome |
| `python3 -m pytest tests/ -v` | Lancer les tests |

## 🔍 Dépannage

### Problème : La GUI freeze toujours

**Solution 1** : Utilisez le mode sans son
```bash
NO_SOUND=1 python3 main.py
```

**Solution 2** : Vérifiez que PulseAudio est démarré
```bash
pulseaudio --check && echo "PulseAudio OK" || echo "PulseAudio non démarré"
```

### Problème : Pas de son dans la vidéo exportée

Le mode NO_SOUND ne désactive que la **lecture** dans la GUI. Pour l'export vidéo, le son est géré par FFmpeg directement et devrait fonctionner.

## 📁 Fichiers modifiés

- `main.py` - Correction du bug de fermeture + lancement GUI/CLI unifié
- `audio/analyzer.py` - Meilleure gestion des erreurs + mode NO_SOUND
- `ui/main_window.py` - Arrêt forcé des threads

## 🎨 Nouveautés visuelles

Les améliorations précédentes sont toujours incluses :
- Effets **spectrum** et **plasma** ajoutés
- Effet **bars** amélioré (peak hold, bordures, dégradés)
- Nouvelle palette **winamp_classic**

Pour les tester :
1. Lancez la GUI
2. Sélectionnez un fichier audio
3. Choisissez l'effet dans le menu déroulant
4. Cliquez sur "▶ Lecture"
