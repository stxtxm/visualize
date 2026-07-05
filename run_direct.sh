#!/bin/bash
# Lancement DIRECT du visualiseur (sans AppImage)
# Teste d'abord le son, puis lance la GUI

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo " Lancement direct du Visualisateur"
echo "============================================"
echo ""

# 1. Vérifier les outils audio disponibles
echo "--- Outils audio disponibles ---"
for tool in ffplay ffmpeg pw-play paplay aplay; do
    if command -v "$tool" &>/dev/null 2>&1; then
        echo "  ✓ $tool: $(command -v $tool)"
    else
        echo "  ✗ $tool: non trouvé"
    fi
done

echo ""

# 2. Vérifier le serveur audio
echo "--- Serveur audio ---"
if command -v pw-metadata &>/dev/null 2>&1; then
    echo "  ✓ PipeWire détecté"
elif pgrep -x pulseaudio &>/dev/null 2>&1; then
    echo "  ✓ PulseAudio détecté"
else
    echo "  ⚠ Aucun serveur audio détecté"
fi

# Vérifier le socket PulseAudio
PULSE_SOCKET="/run/user/$(id -u)/pulse"
if [ -d "$PULSE_SOCKET" ]; then
    echo "  ✓ Socket PulseAudio: $PULSE_SOCKET"
else
    echo "  ✗ Socket PulseAudio absent"
fi

echo ""

# 3. Tester pw-play (PipeWire natif)
if command -v pw-play &>/dev/null 2>&1; then
    echo "--- Test pw-play (bip 440Hz 0.5s) ---"
    python3 -c "
import struct, sys, math
sr = 44100
for i in range(int(sr * 0.5)):
    v = int(math.sin(2 * math.pi * 440 * i / sr) * 20000)
    sys.stdout.buffer.write(struct.pack('<h', v))
" 2>/dev/null | timeout 2 pw-play --raw --rate=44100 --channels=1 --format=s16 - 2>&1
    if [ $? -eq 0 ] || [ $? -eq 124 ]; then
        echo "  ✓ pw-play: OK (bip entendu ?)"
    else
        echo "  ✗ pw-play: ÉCHEC"
    fi
fi

echo ""

# 4. Tester sounddevice
echo "--- Test sounddevice ---"
timeout 3 python3 -c "
import sys
try:
    import sounddevice as sd
    devices = sd.query_devices()
    print(f'  ✓ sounddevice: {len(devices)} périphériques')
    for i, d in enumerate(devices):
        if d.get('max_output_channels', 0) > 0:
            print(f'    [{i}] {d[\"name\"]}')
except Exception as e:
    print(f'  ✗ sounddevice: {e}')
" 2>&1 || echo "  ✗ sounddevice: timeout"

echo ""
echo "============================================"
echo " Lancement de la GUI..."
echo "============================================"
echo ""

# Lancer la GUI directement avec Python
exec python3 main.py