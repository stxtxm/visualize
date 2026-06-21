#!/bin/bash

# Point d'entrée du conteneur - Configuration pour X11 et PulseAudio

# Configuration pour X11 forwarding
if [ -n "$DISPLAY" ]; then
    echo "Configuring X11 forwarding for display: $DISPLAY"
    # Permettre l'accès X11 depuis le conteneur
    xhost +local: 2>/dev/null || true
fi

# Configuration pour PulseAudio (son)
if [ -n "$PULSE_SERVER" ]; then
    echo "Configuring PulseAudio"
    export PULSE_SERVER=unix:/tmp/pulseaudio.socket
fi

# Lancer la commande principale
exec "$@"
