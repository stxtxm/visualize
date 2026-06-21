"""
Tests for quality presets module.
"""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quality_presets import (
    QUALITY_PRESETS, RESOLUTIONS,
    get_preset, get_available_presets, get_preset_names,
    build_ffmpeg_cmd
)


class TestQualityPresets(unittest.TestCase):
    """Test quality presets functionality."""
    
    def test_presets_exist(self):
        """Test that all expected presets exist."""
        expected_presets = ['dev', 'fast', 'normal', 'high', '4k']
        self.assertEqual(sorted(QUALITY_PRESETS.keys()), sorted(expected_presets))
    
    def test_get_preset(self):
        """Test get_preset function."""
        preset = get_preset('dev')
        self.assertEqual(preset['name'], 'Dev (Très rapide)')
        self.assertEqual(preset['resolution'], '720p')
        self.assertEqual(preset['fps'], 15)
        self.assertEqual(preset['ffmpeg_preset'], 'ultrafast')
        
        preset = get_preset('4k')
        self.assertEqual(preset['name'], '4K Cinématique')
        self.assertEqual(preset['resolution'], '4K')
        self.assertEqual(preset['fps'], 30)
        self.assertEqual(preset['ffmpeg_preset'], 'slow')
    
    def test_get_preset_default(self):
        """Test get_preset with invalid preset returns default."""
        preset = get_preset('invalid')
        self.assertEqual(preset['name'], 'Normale')
    
    def test_get_available_presets(self):
        """Test get_available_presets function."""
        presets = get_available_presets()
        self.assertIn('dev', presets)
        self.assertIn('normal', presets)
        self.assertIn('4k', presets)
    
    def test_get_preset_names(self):
        """Test get_preset_names function."""
        names = get_preset_names()
        self.assertIn('Dev (Très rapide)', names)
        self.assertIn('Normale', names)
        self.assertIn('4K Cinématique', names)
    
    def test_resolutions(self):
        """Test resolution mappings."""
        self.assertEqual(RESOLUTIONS['720p'], (1280, 720))
        self.assertEqual(RESOLUTIONS['1080p'], (1920, 1080))
        self.assertEqual(RESOLUTIONS['1440p'], (2560, 1440))
        self.assertEqual(RESOLUTIONS['4K'], (3840, 2160))
    
    def test_build_ffmpeg_cmd(self):
        """Test FFmpeg command building."""
        cmd = build_ffmpeg_cmd(1280, 720, 15, '/tmp/audio.mp3', '/tmp/output.mp4', 'dev')
        
        # Check that FFmpeg is in the command
        self.assertIn('ffmpeg', cmd)
        
        # Check resolution
        self.assertIn('1280x720', cmd)
        
        # Check FPS
        self.assertIn('15', cmd)
        
        # Check ultrafast preset for dev
        self.assertIn('ultrafast', cmd)
        
        # Check output file
        self.assertIn('/tmp/output.mp4', cmd)
    
    def test_build_ffmpeg_cmd_4k(self):
        """Test FFmpeg command building for 4K."""
        cmd = build_ffmpeg_cmd(3840, 2160, 30, '/tmp/audio.mp3', '/tmp/output.mp4', '4k')
        
        # Check 4K resolution
        self.assertIn('3840x2160', cmd)
        
        # Check slow preset for 4k
        self.assertIn('slow', cmd)
        
        # Check high bitrate for 4K
        self.assertIn('50M', cmd)
    
    def test_build_ffmpeg_cmd_high_quality(self):
        """Test FFmpeg command building for high quality preset."""
        cmd = build_ffmpeg_cmd(1920, 1080, 60, '/tmp/audio.mp3', '/tmp/output.mp4', 'high')
        
        # Check 1080p resolution
        self.assertIn('1920x1080', cmd)
        
        # Check 60 FPS
        self.assertIn('60', cmd)
        
        # Check medium preset
        self.assertIn('medium', cmd)


class TestPresetSpeed(unittest.TestCase):
    """Test preset speed factors."""
    
    def test_dev_preset_fastest(self):
        """Test that dev preset is the fastest."""
        dev = get_preset('dev')
        fast = get_preset('fast')
        normal = get_preset('normal')
        
        # Dev should have lowest resolution and FPS
        self.assertLess(dev['fps'], fast['fps'])
        self.assertLess(dev['fps'], normal['fps'])
    
    def test_4k_preset_slowest(self):
        """Test that 4k preset is configured for slowest encoding."""
        preset_4k = get_preset('4k')
        self.assertEqual(preset_4k['ffmpeg_preset'], 'slow')
    
    def test_normal_preset_balanced(self):
        """Test that normal preset has balanced settings."""
        normal = get_preset('normal')
        self.assertEqual(normal['resolution'], '1080p')
        self.assertEqual(normal['fps'], 30)
        self.assertEqual(normal['ffmpeg_preset'], 'fast')


if __name__ == '__main__':
    unittest.main()
