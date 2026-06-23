#!/bin/bash

# Script pour exécuter le test E2E spécifique: MP3 short + Lecture
# Ce test est conçu pour déboguer les problèmes de lecture

echo "=========================================="
echo "Test E2E: MP3 Short + Appuyer sur Lecture"
echo "=========================================="
echo ""

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/tmp/visualize_short_mp3_debug.log"

# Nettoyer les anciens logs
rm -f "$LOG_FILE"

# Vérifier que le fichier MP3 existe
if [ -f "$PROJECT_DIR/input/gruffius_short.mp3" ]; then
    echo "✓ Fichier trouvé: input/gruffius_short.mp3"
else
    echo "✗ Fichier non trouvé: input/gruffius_short.mp3"
    exit 1
fi

echo ""
echo "Démarrage du test..."
echo "Fichier de log: $LOG_FILE"
echo ""

# Exécuter le test en mode debug
cd "$PROJECT_DIR"
python3 tests/test_e2e_short_mp3_play.py

TEST_RESULT=$?

echo ""
if [ $TEST_RESULT -eq 0 ]; then
    echo "✓ Test terminé avec succès !"
    echo "  Logs détaillés: $LOG_FILE"
else
    echo "✗ Test échoué !"
    echo "  Voir $LOG_FILE pour les détails du débogage"
fi

exit $TEST_RESULT
