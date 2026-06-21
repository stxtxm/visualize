#!/bin/bash

# Script pour tester et debuguer le problème de lecture
# Capture TOUS les logs et les affiche dans un fichier

echo "=========================================="
echo "Test et Debug du Visualisateur Psychédélique"
echo "=========================================="
echo ""

# Nettoyer les anciens conteneurs
echo "Nettoyage des anciens conteneurs..."
podman stop -t 2 psychedelic-visualizer-gui psychedelic-visualizer-cli 2>/dev/null || true
podman rm -f psychedelic-visualizer-gui psychedelic-visualizer-cli 2>/dev/null || true
echo "✓ Nettoyage terminé"
echo ""

# Vérifier si PulseAudio est disponible
PULSE_AVAILABLE=false
if [ -d "/run/user/${UID}/pulse" ] && [ -S "/run/user/${UID}/pulse/pulseaudio.socket" ]; then
    PULSE_AVAILABLE=true
    echo "✓ PulseAudio détecté sur l'hôte"
else
    echo "⚠ PulseAudio non détecté - mode NO_SOUND activé"
fi
echo ""

# Autoriser X11 (avec timeout pour éviter le blocage)
timeout 2 xhost +local: 2>/dev/null || true

# Créer le fichier de log
LOG_FILE="/tmp/visualize_gui_debug_$(date +%Y%m%d_%H%M%S).log"
echo "Logs seront enregistrés dans: $LOG_FILE"
echo ""

# Fonction pour afficher les logs dans une fenêtre Tkinter
show_logs_in_gui() {
    python3 - << 'PYTHON_EOF'
import tkinter as tk
from tkinter import scrolledtext, messagebox
import sys

root = tk.Tk()
root.title("Logs de Debug - Visualisateur Psychédélique")
root.geometry("800x600")

text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=40)
text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

try:
    with open("'$LOG_FILE'", "r") as f:
        content = f.read()
    text.insert(tk.END, content)
    text.config(state=tk.DISABLED)
    
    # Ajouter un bouton pour copier les logs
    def copy_logs():
        root.clipboard_clear()
        root.clipboard_append(content)
        messagebox.showinfo("Copié", "Logs copiés dans le presse-papiers!")
    
    btn_copy = tk.Button(root, text="Copier les logs", command=copy_logs)
    btn_copy.pack(pady=5)
    
    # Ajouter un bouton pour quitter
    btn_quit = tk.Button(root, text="Quitter", command=root.quit)
    btn_quit.pack(pady=5)
    
except FileNotFoundError:
    text.insert(tk.END, "Fichier de log non trouvé: '$LOG_FILE'\n")
    text.insert(tk.END, "Le test n'a pas encore généré de logs.\n")

root.mainloop()
PYTHON_EOF
}

# Lancer le conteneur avec redirection des logs
echo "Lancement du conteneur avec capture des logs..."
echo ""

if [ "$PULSE_AVAILABLE" = true ]; then
    # Avec PulseAudio
    podman run --rm \
        --name "psychedelic-visualizer-gui" \
        --net=host \
        --ipc=host \
        --security-opt label=disable \
        --volume /tmp/.X11-unix:/tmp/.X11-unix:ro \
        --env DISPLAY \
        --env XAUTHORITY="${HOME}/.Xauthority" \
        --volume "${HOME}/.Xauthority":"${HOME}/.Xauthority":ro \
        --volume /run/user/"${UID}"/pulse:/run/user/"${UID}"/pulse:ro \
        --env PULSE_SERVER=unix:/run/user/"${UID}"/pulse/pulseaudio.socket \
        --env PULSE_COOKIE=/run/user/"${UID}"/pulse/cookie \
        --volume /run/user/"${UID}"/pulse/cookie:/run/user/"${UID}"/pulse/cookie:ro \
        --volume "$(pwd)/input":/app/input:ro,Z \
        --volume "$(pwd)/output":/app/output:Z \
        --volume "$(pwd)":/app:ro,Z \
        --device /dev/snd \
        psychedelic-visualizer:latest \
        bash -c "python3 /app/main.py 2>&1 | tee /tmp/container_output.log" \
        > "$LOG_FILE" 2>&1
else
    # Sans PulseAudio (mode NO_SOUND)
    podman run --rm \
        --name "psychedelic-visualizer-gui" \
        --net=host \
        --ipc=host \
        --security-opt label=disable \
        --volume /tmp/.X11-unix:/tmp/.X11-unix:ro \
        --env DISPLAY \
        --env XAUTHORITY="${HOME}/.Xauthority" \
        --volume "${HOME}/.Xauthority":"${HOME}/.Xauthority":ro \
        --volume "$(pwd)/input":/app/input:ro,Z \
        --volume "$(pwd)/output":/app/output:Z \
        --volume "$(pwd)":/app:ro,Z \
        --env NO_SOUND=1 \
        --env SDL_VIDEODRIVER=x11 \
        --env SDL_RENDER_DRIVER=software \
        --env SDL_AUDIODRIVER=dummy \
        psychedelic-visualizer:latest \
        bash -c "python3 /app/main.py 2>&1 | tee /tmp/container_output.log" \
        > "$LOG_FILE" 2>&1
fi

# Attendre que le conteneur démarre et afficher les logs en temps réel
echo ""
echo "Attendez quelques secondes... Le conteneur démarre..."
echo ""
sleep 5

# Vérifier si le conteneur est toujours en vie
if podman ps --filter "name=psychedelic-visualizer-gui" --format "{{.Status}}" 2>/dev/null | grep -q "Up"; then
    echo "✓ Conteneur en cours d'exécution"
    echo ""
    echo "=========================================="
    echo "Logs du conteneur:"
    echo "=========================================="
    cat "$LOG_FILE" 2>/dev/null | head -50
    echo ""
    echo "=========================================="
    echo "Pour afficher les logs dans une fenêtre GUI:"
    echo "  ./run_test_and_debug.sh --show-logs"
    echo ""
    echo "Pour arrêter le conteneur:"
    echo "  podman stop psychedelic-visualizer-gui"
    echo "=========================================="
else
    echo "⚠ Conteneur s'est arrêté"
    echo ""
    echo "=========================================="
    echo "Logs complets:"
    echo "=========================================="
    cat "$LOG_FILE" 2>/dev/null
    echo ""
    echo "=========================================="
fi

# Option pour afficher les logs dans une GUI
if [ "$1" = "--show-logs" ]; then
    show_logs_in_gui
fi

# Copier aussi les logs du conteneur
if [ -f /tmp/container_output.log ]; then
    cat /tmp/container_output.log >> "$LOG_FILE" 2>/dev/null
fi

echo ""
echo "Fichier de log: $LOG_FILE"
