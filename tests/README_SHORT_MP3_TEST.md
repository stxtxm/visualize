# Test E2E: Ajouter MP3 Short + Appuyer sur Lecture

Ce test reproduit le flux utilisateur pour déboguer les problèmes de lecture dans l'application Visualisateur Psychédélique.

## Fichiers créés

### 1. `test_e2e_short_mp3_play.py`
Test E2E complet avec logging détaillé pour le débogage. Nécessite numpy et pydub.
- **Objectif**: Tester le flux complet avec le fichier `input/gruffius_short.mp3`
- **Sortie**: Fichier de log à `/tmp/visualize_short_mp3_debug.log`
- **Durée**: 5 secondes par défaut

### 2. `test_e2e_short_mp3_play_simple.py`
Test E2E simplifié utilisant des mocks pour contourner les dépendances numpy/pydub.
- **Objectif**: Tester la LOGIQUE sans dépendre des bibliothèques audio
- **Avantage**: Fonctionne dans des environnements sans numpy
- **Sortie**: Console

### 3. `run_short_mp3_test.sh`
Script shell pour exécuter le test E2E.
- Vérifie que le fichier MP3 existe
- Nettoie les anciens logs
- Exécute le test principal
- Affiche les résultats

## Utilisation

### Avec le test complet (nécessite numpy):
```bash
# Installer les dépendances (si nécessaire)
pip install numpy pydub

# Exécuter le test
python3 tests/test_e2e_short_mp3_play.py

# Ou via le script shell
chmod +x tests/run_short_mp3_test.sh
./tests/run_short_mp3_test.sh
```

### Avec le test simplifié (sans dépendances):
```bash
# Exécuter le test simplifié
python3 tests/test_e2e_short_mp3_play_simple.py
```

## Ce que le test vérifie

1. **Accès au fichier**: Vérifie que `input/gruffius_short.mp3` existe
2. **AudioAnalyzer**: Teste l'initialisation et le streaming avec le fichier
3. **Playback Start/Stop**: Simule l'appui sur ▶ Lecture et ⏹ Arrêter
4. **Flux GUI Minimal**: Simule le flux complet de l'interface utilisateur

## Débogage

Si des problèmes se produisent:
- Vérifier le fichier de log: `/tmp/visualize_short_mp3_debug.log`
- Vérifier que le fichier `input/gruffius_short.mp3` existe
- Vérifier les permissions sur le fichier
- Vérifier que les dépendances sont installées (`numpy`, `pydub`, `pygame`)

## Fichier test utilisé

- **Nom**: `input/gruffius_short.mp3`
- **Taille**: ~1.9 MB
- **Format**: MP3, 320 kbps, 44.1 kHz, Stéréo
- **Durée**: Court (quelques secondes)

## Problèmes courants

### 1. "No module named 'numpy'"
```bash
pip install numpy
```

### 2. "No module named 'pydub'"
```bash
pip install pydub
```

### 3. "ffmpeg not found"
```bash
# Sur Ubuntu/Debian
sudo apt-get install ffmpeg

# Sur Fedora
sudo dnf install ffmpeg
```

### 4. Fichier MP3 non trouvé
- Vérifier que `input/gruffius_short.mp3` existe dans le répertoire du projet
- Créer un lien symbolique si nécessaire:
```bash
ln -s /chemin/vers/votre/fichier.mp3 input/gruffius_short.mp3
```

## Intégration avec les autres tests

Ce test peut être intégré dans la suite de tests existante:
```bash
# Exécuter tous les tests E2E
./tests/run_e2e_test.sh

# Exécuter uniquement le test MP3 short
python3 tests/test_e2e_short_mp3_play.py
```

## Personnalisation

Vous pouvez modifier les paramètres dans le test:
- `AUDIO_FILE`: Changer le fichier MP3 à tester
- `TEST_DURATION`: Changer la durée du test en secondes
- `DEBUG_MODE`: Activer/désactiver le mode debug

## Structure du test

```
1. Vérification du fichier
   └── Vérifie que input/gruffius_short.mp3 existe

2. Test AudioAnalyzer
   ├── Création de l'analyzer
   ├── Démarrage du stream
   └── Récupération et analyse de chunks

3. Test Playback Start/Stop
   ├── Création des composants (analyzer, renderer, effect_manager)
   ├── Démarrage du stream (simule ▶ Lecture)
   ├── Boucle de lecture
   └── Arrêt (simule ⏹ Arrêter)

4. Test Flux GUI Minimal
   └── Simule le flux utilisateur complet
```
