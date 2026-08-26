"""
Fixtures pytest pour les tests de Visualize.
Ce fichier fournit des fixtures réutilisables pour tous les tests.
"""

import pytest
import os
import sys
import tempfile
import numpy as np


# Configurer les paths pour les imports
# Le répertoire racine du projet doit être dans le path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


@pytest.fixture
def project_root():
    """Retourne le répertoire racine du projet."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def sample_audio_path(project_root):
    """Chemin vers un fichier audio de test."""
    # Essayer plusieurs emplacements
    possible_paths = [
        os.path.join(project_root, 'input', 'gruffius.mp3'),
        os.path.join(project_root, 'tests', 'samples', 'test_440hz.wav'),
        os.path.join(project_root, 'audio', 'gruffius.mp3'),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Si aucun fichier trouvé, en créer un temporaire
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        # Créer un simple fichier WAV silencieux
        # En-tête WAV minimal (44 bytes) + données
        sample_rate = 44100
        duration = 0.1  # 100ms
        num_samples = int(sample_rate * duration)
        
        # Créer des données audio (silence)
        import struct
        wav_header = b'RIFF' + struct.pack('<I', 36 + num_samples * 2) + b'WAVEfmt '
        wav_header += struct.pack('<IHHIHH', 16, 1, 1, sample_rate, sample_rate * 2, 2, 16)
        wav_header += b'data' + struct.pack('<I', num_samples * 2)
        
        # Écrire des zéros (silence)
        f.write(wav_header + b'\x00' * (num_samples * 2))
        return f.name


@pytest.fixture
def sample_audio_data():
    """Retourne des données audio synthétiques pour les tests."""
    sample_rate = 44100
    duration = 0.5
    frequency = 440.0  # LA4
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = np.sin(2 * np.pi * frequency * t) * 0.5
    
    return wave.astype(np.float32)


@pytest.fixture
def test_audio_file():
    """Crée un fichier audio temporaire pour les tests."""
    import tempfile
    from pydub import AudioSegment
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        # Créer un audio silencieux de 100ms
        audio = AudioSegment.silent(duration=100)
        audio.export(f.name, format='wav')
        yield f.name
        
        # Nettoyer
        try:
            os.unlink(f.name)
        except:
            pass


@pytest.fixture
def test_input_dir(project_root):
    """Crée un dossier input de test."""
    input_dir = os.path.join(project_root, 'tests', 'test_input')
    os.makedirs(input_dir, exist_ok=True)
    yield input_dir
    
    # Nettoyer
    try:
        import shutil
        shutil.rmtree(input_dir, ignore_errors=True)
    except:
        pass


@pytest.fixture
def test_output_dir(project_root):
    """Crée un dossier output de test."""
    output_dir = os.path.join(project_root, 'tests', 'test_output')
    os.makedirs(output_dir, exist_ok=True)
    yield output_dir
    
    # Nettoyer
    try:
        import shutil
        shutil.rmtree(output_dir, ignore_errors=True)
    except:
        pass


@pytest.fixture
def mock_container_environment(monkeypatch):
    """Simule l'environnement conteneur pour les tests."""
    # Faire croire que /app/main.py existe
    original_exists = os.path.exists
    def mock_exists(path):
        if path == '/app/main.py':
            return True
        return original_exists(path)
    
    monkeypatch.setattr(os.path, 'exists', mock_exists)
    
    # Sauvegarder l'original
    original_getcwd = os.getcwd
    
    # Changer le répertoire courant
    monkeypatch.setattr(os, 'getcwd', lambda: '/app')
    
    yield
    
    # Restorer
    monkeypatch.setattr(os.path, 'exists', original_exists)
    monkeypatch.setattr(os, 'getcwd', original_getcwd)


@pytest.fixture
def path_manager():
    """Retourne une instance de PathManager pour les tests."""
    from utils.paths import PathManager
    return PathManager()
