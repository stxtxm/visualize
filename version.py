import os
import subprocess

__version__ = "0.3.3"

# Si on est en mode dev, on essaie de récupérer dynamiquement la version via git
if __version__ == "dev":
    try:
        project_dir = os.path.dirname(os.path.abspath(__file__))
        __version__ = subprocess.check_output(
            ["git", "describe", "--tags", "--always"],
            cwd=project_dir,
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
    except Exception:
        __version__ = "0.0.2"
