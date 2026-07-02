# Visualisateur Psychédélique - Dockerfile
# Conteneur complet avec toutes les dépendances pour Podman/Docker

FROM python:3.11-slim

# Configurer l'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DISPLAY=:0 \
    PATH="/root/.local/bin:${PATH}" \
    PYTHONPATH="/root/.local/lib/python3.11/site-packages:${PYTHONPATH}"

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    portaudio19-dev \
    gcc \
    python3-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libsdl2-2.0-0 \
    libsdl2-image-2.0-0 \
    libsdl2-mixer-2.0-0 \
    libsdl2-ttf-2.0-0 \
    ffmpeg \
    libx264-dev \
    libx11-6 \
    libx11-xcb1 \
    libxcb-glx0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    libxcb-dri3-0 \
    libxkbcommon-x11-0 \
    tk-dev \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
COPY . .

# Permissions
RUN chmod -R a+rX /app
RUN find /app -type f -iname "*.py" -exec chmod +x {} \;
RUN find /app -type f -iname "*.sh" -exec chmod +x {} \;

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

RUN chmod +x /app/docker-entrypoint.sh /app/export_menu.py

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python3", "main.py"]

EXPOSE 5900