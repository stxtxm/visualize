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

### 4. Nouveau script de lancement intelligent
**Fichier** : `run_gui_fallback.sh`
- Détection automatique de PulseAudio sur l'hôte
- Si PulseAudio n'est pas disponible → lance en mode **NO_SOUND=1**
- Plus besoin de configurer manuellement

## 🚀 Marche à suivre pour démarrer

### Option 1 : Utiliser le fallback automatique (RECOMMANDÉ)

```bash
# Seit dans le dossier du projet
cd /home/timo/dev/visualize

# Reconstruire l'image (obligatoire après les changements)
make rebuild

# Lancer avec fallback automatique (détecte si PulseAudio est disponible)
make run-fallback

# Ou directement
./run_gui_fallback.sh
```

### Option 2 : Mode sans son (si PulseAudio ne fonctionne pas)

```bash
# Lancer explicitement sans son
make run-no-sound

# Ou avec variables d'environnement
NO_SOUND=1 ./podman-run.sh
```

### Option 3 : Vérifier que PulseAudio est démarré

Si vous voulez le son, démarrez PulseAudio d'abord :

```bash
# Démarrer PulseAudio (si pas déjà démarré)
pulseaudio --start --exit-idle-time=-1

# Vérifier que le socket existe
ls -la /run/user/$(id -u)/pulse/

# Puis lancer normalement
make run
```

## 📝 Commandes utiles

| Commande | Description |
|----------|-------------|
| `make rebuild` | Reconstruire l'image Podman avec les dernières modifications |
| `make run` | Lancer la GUI (nécessite PulseAudio) |
| `make run-fallback` | Lancer avec détection automatique PulseAudio |
| `make run-no-sound` | Lancer sans son (désactive pydub/ffmpeg) |
| `make clean` | Nettoyer les conteneurs |
| `make stop` | Arrêter tous les conteneurs |

## 🔍 Dépannage

### Problème : La GUI freeze toujours

**Solution 1** : Utilisez le mode sans son
```bash
make run-no-sound
```

**Solution 2** : Vérifiez que PulseAudio est démarré
```bash
pulseaudio --check && echo "PulseAudio OK" || echo "PulseAudio non démarré"
```

**Solution 3** : Vérifiez que le conteneur a bien été reconstruite
```bash
podman images | grep psychedelic
# Devrait montrer "psychedelic-visualizer:latest" avec la date du jour
```

### Problème : La fenêtre ne se ferme pas

**Solution** : Ce bug est corrigé. Si vous avez toujours le problème :
1. Fermez le terminal avec Ctrl+C (si le conteneur est lancé en foreground)
2. Ou exécutez :
```bash
podman stop psychedelic-visualizer-ui
```

### Problème : Pas de son dans la vidéo exportée

Le mode NO_SOUND ne désactive que la **lecture** dans la GUI. Pour l'export vidéo, le son est géré par FFmpeg directement et devrait fonctionner.

## 📁 Fichiers modifiés

- ✅ `main.py` - Correction du bug de fermeture
- ✅ `audio/analyzer.py` - Meilleure gestion des erreurs + mode NO_SOUND
- ✅ `ui/main_window.py` - Arrêt forcé des threads
- ✅ `run_gui_fallback.sh` - Nouveau script intelligent
- ✅ `Makefile` - Nouvelles cibles `run-fallback` et `run-no-sound`

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
