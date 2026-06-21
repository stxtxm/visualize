#!/bin/bash

# Script de test pour les nouvelles fonctionnalités
# Vérifie que tous les nouveaux effets et palettes sont correctement intégrés

echo "=========================================="
echo "  Test des Nouveautés Winamp Professionnel"
echo "=========================================="
echo

# Couleurs pour le output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success_count=0
total_tests=0

# Fonction pour tester un import Python
test_python_import() {
    local module=$1
    local class=$2
    total_tests=$((total_tests + 1))
    
    if python3 -c "import sys; sys.path.insert(0, '.'); from $module import $class" 2>/dev/null; then
        echo -e "${GREEN}✅${NC} Import: $module.$class"
        success_count=$((success_count + 1))
        return 0
    else
        echo -e "${RED}❌${NC} Import: $module.$class"
        return 1
    fi
}

# Fonction pour tester une fonctionnalité
test_feature() {
    local test_name=$1
    local command=$2
    total_tests=$((total_tests + 1))
    
    if eval "$command" 2>/dev/null; then
        echo -e "${GREEN}✅${NC} $test_name"
        success_count=$((success_count + 1))
        return 0
    else
        echo -e "${RED}❌${NC} $test_name"
        return 1
    fi
}

echo "1. Test des imports des nouveaux effets..."
echo "-------------------------------------------"

test_python_import "effects.spectrum" "SpectrumEffect"
test_python_import "effects.plasma" "PlasmaEffect"

echo
echo "2. Test des imports des effets améliorés..."
echo "-------------------------------------------"

test_python_import "effects.bars" "BarEffect"
test_python_import "effects.base" "BaseEffect"
test_python_import "effects.manager" "EffectManager"

echo
echo "3. Test des nouvelles fonctionnalités..."
echo "-------------------------------------------"

# Tester que winamp_classic est disponible
test_feature "Palette winamp_classic disponible" \
    "python3 -c \"import sys; sys.path.insert(0, '.'); from effects.base import BaseEffect; be = BaseEffect(800, 600, 'winamp_classic'); assert len(be.colors) > 0\""

# Tester que spectrum a les bonnes propriétés
test_feature "SpectrumEffect a num_bands" \
    "python3 -c \"import sys; sys.path.insert(0, '.'); from effects.spectrum import SpectrumEffect; se = SpectrumEffect(800, 600); assert hasattr(se, 'num_bands'); assert se.num_bands == 32\""

# Tester que plasma a les points de contrôle
test_feature "PlasmaEffect a plasma_points" \
    "python3 -c \"import sys; sys.path.insert(0, '.'); from effects.plasma import PlasmaEffect; pe = PlasmaEffect(800, 600); assert hasattr(pe, 'plasma_points'); assert len(pe.plasma_points) > 0\""

# Tester que bars a les améliorations
test_feature "BarEffect a peak_values" \
    "python3 -c \"import sys; sys.path.insert(0, '.'); from effects.bars import BarEffect; be = BarEffect(800, 600); assert hasattr(be, 'peak_values'); assert hasattr(be, 'peak_decay'); assert hasattr(be, 'pulse')\""

echo
echo "4. Test de l'intégration dans le manager..."
echo "-------------------------------------------"

# Tester que les nouveaux effets sont dans le manager
test_feature "spectrum dans EffectManager" \
    "python3 -c \"import sys; sys.path.insert(0, '.'); from effects.manager import EffectManager; assert 'spectrum' in EffectManager.get_available_effects()\""

test_feature "plasma dans EffectManager" \
    "python3 -c \"import sys; sys.path.insert(0, '.'); from effects.manager import EffectManager; assert 'plasma' in EffectManager.get_available_effects()\""

test_feature "winamp_classic dans les palettes" \
    "python3 -c \"import sys; sys.path.insert(0, '.'); from effects.manager import EffectManager; assert 'winamp_classic' in EffectManager.get_available_palettes()\""

echo
echo "5. Test des fichiers de configuration..."
echo "-------------------------------------------"

# Vérifier que les fichiers existent
test_feature "Fichier spectrum.py existe" "test -f effects/spectrum.py"
test_feature "Fichier plasma.py existe" "test -f effects/plasma.py"
test_feature "NOUVEAUTES.md existe" "test -f NOUVEAUTES.md"

# Vérifier que Makefile est mis à jour
test_feature "Makefile mentionne spectrum" "grep -q spectrum Makefile"
test_feature "Makefile mentionne plasma" "grep -q plasma Makefile"
test_feature "Makefile mentionne winamp_classic" "grep -q winamp_classic Makefile"

echo
echo "6. Test de la syntaxe des fichiers Python..."
echo "-------------------------------------------"

for file in effects/spectrum.py effects/plasma.py effects/bars.py effects/base.py; do
    total_tests=$((total_tests + 1))
    if python3 -m py_compile "$file" 2>/dev/null; then
        echo -e "${GREEN}✅${NC} Syntax: $file"
        success_count=$((success_count + 1))
    else
        echo -e "${RED}❌${NC} Syntax: $file"
    fi
done

echo
echo "=========================================="
echo "  Résultats: $success_count/$total_tests tests passés"
echo "=========================================="
echo

if [ $success_count -eq $total_tests ]; then
    echo -e "${GREEN}🎉 Tous les tests ont réussi !${NC}"
    echo
    echo "Votre visualisateur est prêt avec :"
    echo "  • 2 nouveaux effets: spectrum, plasma"
    echo "  • 1 effet amélioré: bars"
    echo "  • 1 nouvelle palette: winamp_classic"
    echo
    echo "Pour démarrer:"
    echo "  make build  # Si le conteneur n'est pas construit"
    echo "  make run    # Lancer l'interface graphique"
    echo
    exit 0
else
    echo -e "${RED}⚠️  Certains tests ont échoué${NC}"
    echo "Vérifiez les erreurs ci-dessus"
    exit 1
fi
