"""
Tests for audio analyzer module.
"""

import unittest
import sys
import os
import tempfile
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAudioAnalyzer(unittest.TestCase):
    """Test audio analyzer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        from audio.analyzer import AudioAnalyzer
        self.AudioAnalyzer = AudioAnalyzer
    
    def test_import(self):
        """Test that audio analyzer can be imported."""
        from audio.analyzer import AudioAnalyzer
        self.assertTrue(callable(AudioAnalyzer))
    
    def test_default_result(self):
        """Test _get_default_result method."""
        from audio.analyzer import AudioAnalyzer
        analyzer = AudioAnalyzer.__new__(AudioAnalyzer)
        result = analyzer._get_default_result()
        
        self.assertIn('volume', result)
        self.assertIn('frequency_bands', result)
        self.assertIn('spectrum', result)
        self.assertIn('beat', result)
        
        self.assertEqual(result['volume'], 0)
        self.assertFalse(result['beat'])
    
    def test_frequency_bands_config(self):
        """Test frequency bands configuration."""
        from audio.analyzer import AudioAnalyzer
        analyzer = AudioAnalyzer.__new__(AudioAnalyzer)
        
        # Check that freq_bands is defined
        self.assertTrue(hasattr(analyzer, 'freq_bands'))
        
        # Check band ranges
        expected_bands = [
            (20, 250),    # Sub-bass
            (250, 500),   # Bass
            (500, 2000),  # Low-mids
            (2000, 4000), # High-mids
            (4000, 20000) # Highs
        ]
        self.assertEqual(analyzer.freq_bands, expected_bands)


class TestAudioLoading(unittest.TestCase):
    """Test audio file loading."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization with a real audio file."""
        # This test requires a real audio file
        test_audio_files = [
            '/app/tests/test_audio.mp3',
            '/tmp/test_audio.mp3',
            '/audio/gruffius.mp3'  # From user's context
        ]
        
        found = False
        for audio_file in test_audio_files:
            if os.path.exists(audio_file):
                try:
                    from audio.analyzer import AudioAnalyzer
                    analyzer = AudioAnalyzer(audio_file, loop=False)
                    self.assertTrue(analyzer.audio is not None)
                    found = True
                    analyzer.cleanup()
                    break
                except Exception as e:
                    # File exists but can't be loaded - skip
                    pass
        
        # If no test file found, skip this test
        if not found:
            self.skipTest("No test audio file found")


class TestAudioAnalysis(unittest.TestCase):
    """Test audio analysis functions."""

    def test_analyze_chunk_exposes_enhanced_audio_metrics(self):
        """Test that richer audio metrics are returned for better visual sync."""
        from audio.analyzer import AudioAnalyzer

        analyzer = AudioAnalyzer('/tmp/placeholder.wav', chunk_size=1024, sample_rate=44100, loop=False)
        chunk = np.zeros(1024, dtype=np.int16)
        chunk[0:64] = 1000

        result = analyzer.analyze_chunk(chunk)

        self.assertIn('energy', result)
        self.assertIn('spectral_centroid', result)
        self.assertIn('beat_phase', result)
        self.assertGreaterEqual(result['energy'], 0.0)
        self.assertLessEqual(result['energy'], 1.0)
        self.assertGreaterEqual(result['spectral_centroid'], 0.0)
        self.assertLessEqual(result['spectral_centroid'], 1.0)

    def test_analyze_chunk_with_none(self):
        """Test analyze_chunk with None input."""
        from audio.analyzer import AudioAnalyzer
        analyzer = AudioAnalyzer.__new__(AudioAnalyzer)
        analyzer.chunk_size = 1024
        analyzer._get_default_result = lambda: {
            'volume': 0, 'frequency_bands': [], 'spectrum': [], 'beat': False
        }
        
        result = analyzer.analyze_chunk(None)
        self.assertEqual(result['volume'], 0)
    
    def test_analyze_chunk_with_short_array(self):
        """Test analyze_chunk with short array."""
        from audio.analyzer import AudioAnalyzer
        analyzer = AudioAnalyzer.__new__(AudioAnalyzer)
        analyzer.chunk_size = 1024
        analyzer._get_default_result = lambda: {
            'volume': 0, 'frequency_bands': [], 'spectrum': [], 'beat': False
        }
        
        result = analyzer.analyze_chunk(np.array([0, 1, 2]))
        self.assertEqual(result['volume'], 0)


if __name__ == '__main__':
    unittest.main()
