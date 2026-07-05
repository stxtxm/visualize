#!/bin/bash
# Script de diagnostic audio pour Fedora 44
# Teste chaque backend séparément pour identifier où le son se casse

set -e

echo "=== DIAGNOSTIC AUDIO ==="
echo ""

# 1. Vérifier les outils disponibles
echo "--- Outils disponibles ---"
for tool in ffplay ffmpeg pw-play paplay aplay python3; do
    if command -v "$tool" &>/dev/null 2>&1; then
        echo "  ✓ $tool trouvé: $(command -v $tool)"
    else
        echo "  ✗ $tool NON trouvé"
    fi
done

echo ""

# 2. Vérifier le serveur audio
echo "--- Serveur audio ---"
if pgrep -x pipewire &>/dev/null 2>&1; then
    echo "  ✓ PipeWire: en cours d'exécution"
elif pgrep -x pulseaudio &>/dev/null 2>&1; then
    echo "  ✓ PulseAudio: en cours d'exécution"
else
    echo "  ✗ Aucun serveur audio détecté en cours d'exécution"
fi

# Vérifier les sockets PulseAudio
PULSE_SOCKET="/run/user/$(id -u)/pulse"
if [ -d "$PULSE_SOCKET" ]; then
    echo "  ✓ Socket PulseAudio: $PULSE_SOCKET"
    ls -la "$PULSE_SOCKET"/ 2>/dev/null | head -5
else
    echo "  ✗ Socket PulseAudio: absent"
fi

echo ""

# 3. Vérifier pw-play
echo "--- Test pw-play ---"
if command -v pw-play &>/dev/null 2>&1; then
    # Tester avec un son minimal (440Hz, 0.5s, silence)
    echo "  Génération d'un bip de test (440Hz, 0.5s)..."
    python3 -c "
import struct, sys
sample_rate = 44100
duration = 0.5
import math
samples = []
for i in range(int(sample_rate * duration)):
    v = int(math.sin(2 * math.pi * 440 * i / sample_rate) * 20000)
    samples.append(struct.pack('<h', v))
sys.stdout.buffer.write(b''.join(samples))
" | timeout 2 pw-play --raw --rate=44100 --channels=1 --format=s16 - 2>&1 && echo "  ✓ pw-play: SUCCÈS (bip entendu?)" || echo "  ✗ pw-play: ÉCHEC (code: $?)"
else
    echo "  ✗ pw-play: non disponible"
fi

echo ""

# 4. Vérifier sounddevice
echo "--- Test sounddevice ---"
timeout 5 python3 -c "
import sys
try:
    import sounddevice as sd
    devices = sd.query_devices()
    print(f'  ✓ sounddevice: {len(devices)} périphériques trouvés')
    for i, d in enumerate(devices):
        if d.get('max_output_channels', 0) > 0:
            print(f'    Sortie {i}: {d[\"name\"]}')
except Exception as e:
    print(f'  ✗ sounddevice: {e}')
" 2>&1 || echo "  ✗ sounddevice: test bloqué/timeout"

echo ""

# 5. Vérifier ffplay
echo "--- Test ffplay ---"
if command -v ffplay &>/dev/null 2>&1; then
    # ffplay version
    ffplay -version 2>&1 | head -1
    # Test avec fichier WAV temporaire
    python3 -c "
import struct, math, wave, tempfile, os
sr = 44100
duration = 0.3
fd, path = tempfile.mkstemp(suffix='.wav')
os.close(fd)
with wave.open(path, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sr)
    frames = []
    for i in range(int(sr * duration)):
        v = int(math.sin(2 * math.pi * 440 * i / sr) * 20000)
        frames.append(struct.pack('<h', v))
    wf.writeframes(b''.join(frames))
print(f'  ✓ Fichier WAV temporaire créé: {path}')
import subprocess
result = subprocess.run(['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', path],
    capture_output=True, timeout=2)
os.unlink(path)
if result.returncode == 0:
    print('  ✓ ffplay: SUCCÈS')
else:
    err = result.stderr.decode()[:200]
    print(f'  ✗ ffplay: ÉCHEC (rc={result.returncode}): {err}')
" 2>&1
else
    echo "  ✗ ffplay: non disponible"
fi

echo ""
echo "=== FIN DU DIAGNOSTIC ==="
echo ""
echo "Pour lancer la GUI directement (sans AppImage):"
echo "  cd /home/timo/dev/visualize && python3 main.py"
echo ""