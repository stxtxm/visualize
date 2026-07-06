"""
Tests pour le module utils/paths.py (PathManager).
"""

import pytest
import os
import sys
import tempfile

# Configurer les paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.paths import PathManager, get_path_manager


class TestPathManager:
    """Tests pour la classe PathManager."""
    
    def test_initialization(self):
        """Test l'initialisation de PathManager."""
        pm = PathManager()
        assert pm is not None
        assert hasattr(pm, 'input_dir')
        assert hasattr(pm, 'output_dir')
        assert hasattr(pm, 'project_dir')
    
    def test_input_output_dirs_exist(self, project_root):
        """Test que les dossiers input/ et output/ sont créés."""
        pm = PathManager()
        
        # Les dossiers devraient exister après l'initialisation
        assert os.path.exists(pm.input_dir) or os.path.isdir(pm.input_dir)
        assert os.path.exists(pm.output_dir) or os.path.isdir(pm.output_dir)
    
    def test_get_input_path(self, project_root):
        """Test la méthode get_input_path."""
        pm = PathManager()
        
        path = pm.get_input_path('test.mp3')
        assert 'input' in path
        assert 'test.mp3' in path
    
    def test_get_output_path(self, project_root):
        """Test la méthode get_output_path."""
        pm = PathManager()
        
        path = pm.get_output_path('test.mp4')
        assert 'output' in path
        assert 'test.mp4' in path
    
    def test_list_input_files_empty(self, project_root, test_input_dir):
        """Test list_input_files avec un dossier vide."""
        pm = PathManager()
        pm.input_dir = test_input_dir
        
        files = pm.list_input_files()
        assert files == []
    
    def test_list_input_files_with_files(self, project_root, test_input_dir):
        """Test list_input_files avec des fichiers."""
        pm = PathManager()
        pm.input_dir = test_input_dir
        
        # Créer des fichiers de test
        with open(os.path.join(test_input_dir, 'test.mp3'), 'w') as f:
            f.write('test')
        with open(os.path.join(test_input_dir, 'test.wav'), 'w') as f:
            f.write('test')
        with open(os.path.join(test_input_dir, 'readme.txt'), 'w') as f:
            f.write('test')
        
        # Lister tous les fichiers
        all_files = pm.list_input_files()
        assert len(all_files) == 3
        
        # Lister uniquement les fichiers audio
        audio_files = pm.list_input_files(['.mp3', '.wav'])
        assert len(audio_files) == 2
        assert any('test.mp3' in f for f in audio_files)
        assert any('test.wav' in f for f in audio_files)
        assert not any('readme.txt' in f for f in audio_files)
    
    def test_get_media_files(self, project_root, test_input_dir):
        """Test get_media_files."""
        pm = PathManager()
        pm.input_dir = test_input_dir
        
        # Créer des fichiers multimédia
        with open(os.path.join(test_input_dir, 'song.mp3'), 'w') as f:
            f.write('test')
        with open(os.path.join(test_input_dir, 'video.mp4'), 'w') as f:
            f.write('test')
        with open(os.path.join(test_input_dir, 'data.txt'), 'w') as f:
            f.write('test')
        
        media_files = pm.get_media_files()
        assert len(media_files) == 2
        assert any('song.mp3' in f for f in media_files)
        assert any('video.mp4' in f for f in media_files)
        assert not any('data.txt' in f for f in media_files)
    
    def test_get_project_path(self, project_root):
        """Test get_project_path."""
        pm = PathManager()
        
        path = pm.get_project_path('audio', 'analyzer.py')
        assert pm.project_dir in path
        assert 'audio' in path
        assert 'analyzer.py' in path
    
    def test_is_in_container_on_host(self, project_root, monkeypatch):
        """Test is_in_container quand on est sur l'hôte."""
        # S'assurer que /app/main.py n'existe pas
        original_exists = os.path.exists
        def mock_exists(path):
            if path == '/app/main.py':
                return False
            return original_exists(path)
        
        monkeypatch.setattr(os.path, 'exists', mock_exists)
        
        pm = PathManager()
        # Sur l'hôte, in_container devrait être False
        # (sauf si on est vraiment dans /app)
        assert pm.is_in_container() == False
    
    def test_is_in_container_in_container(self, mock_container_environment):
        """Test is_in_container quand on est dans le conteneur."""
        pm = PathManager()
        assert pm.is_in_container() == True
        assert pm.input_dir == '/app/input'
        assert pm.output_dir == '/app/output'
        assert pm.project_dir == '/app'
    
    def test_convert_to_container_path_on_host(self, project_root, test_input_dir, monkeypatch):
        """Test convert_to_container_path depuis l'hôte."""
        # S'assurer qu'on n'est pas dans le conteneur
        original_exists = os.path.exists
        def mock_exists(path):
            if path == '/app/main.py':
                return False
            return original_exists(path)
        
        monkeypatch.setattr(os.path, 'exists', mock_exists)
        
        pm = PathManager()
        pm.input_dir = test_input_dir
        
        # Convertir un path de l'hôte vers le conteneur
        host_path = os.path.join(test_input_dir, 'test.mp3')
        container_path = pm.convert_to_container_path(host_path)
        assert '/app/input' in container_path
    
    def test_convert_to_container_path_in_container(self, mock_container_environment):
        """Test convert_to_container_path depuis le conteneur."""
        pm = PathManager()
        
        # Dans le conteneur, le path devrait rester inchangé
        container_path = '/app/input/test.mp3'
        result = pm.convert_to_container_path(container_path)
        assert result == container_path
    
    def test_global_instance(self):
        """Test l'instance globale get_path_manager."""
        pm = get_path_manager()
        assert pm is not None
        assert isinstance(pm, PathManager)


class TestPathManagerEdgeCases:
    """Tests pour les cas particuliers de PathManager."""
    
    def test_nonexistent_input_dir(self, project_root, test_input_dir, monkeypatch):
        """Test list_input_files avec un dossier qui n'existe pas."""
        pm = PathManager()
        pm.input_dir = '/nonexistent/path'
        
        files = pm.list_input_files()
        assert files == []
    
    def test_permission_error(self, project_root, test_input_dir, monkeypatch):
        """Test list_input_files avec une erreur de permission."""
        pm = PathManager()
        pm.input_dir = test_input_dir
        
        # Simuler une erreur de permission
        def mock_listdir(path):
            if path == test_input_dir:
                raise PermissionError("Access denied")
            return os.listdir(path)
        
        monkeypatch.setattr(os, 'listdir', mock_listdir)
        
        files = pm.list_input_files()
        assert files == []
    
    def test_case_insensitive_extensions(self, project_root, test_input_dir):
        """Test que la détection d'extension est insensible à la casse."""
        pm = PathManager()
        pm.input_dir = test_input_dir
        
        # Créer un fichier avec extension en majuscules
        with open(os.path.join(test_input_dir, 'test.MP3'), 'w') as f:
            f.write('test')
        
        mp3_files = pm.list_input_files(['.mp3'])
        assert len(mp3_files) == 1
        assert 'test.MP3' in mp3_files[0]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
