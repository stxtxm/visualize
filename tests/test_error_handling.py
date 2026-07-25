"""
Tests for error handling: corrupt audio files, NO_SOUND mode, missing ffmpeg.
"""
import unittest
import sys
import os
import tempfile
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestNO_SOUNDMode(unittest.TestCase):
    """AudioAnalyzer should fall back to simulated data when NO_SOUND=1."""

    def setUp(self):
        self._prev = os.environ.get('NO_SOUND')
        os.environ['NO_SOUND'] = '1'

    def tearDown(self):
        if self._prev is None:
            os.environ.pop('NO_SOUND', None)
        else:
            os.environ['NO_SOUND'] = self._prev

    def test_simulated_data_used(self):
        from audio.analyzer import AudioAnalyzer
        # Non-existent file; NO_SOUND forces simulated data
        a = AudioAnalyzer(os.path.join(tempfile.gettempdir(), 'does_not_exist_xyz.wav'), loop=True)
        self.assertTrue(a.use_simulated)
        self.assertIsNotNone(a.audio_data)
        self.assertGreater(len(a.audio_data), 0)
        a.cleanup()

    def test_analyze_chunk_works_in_no_sound(self):
        from audio.analyzer import AudioAnalyzer
        a = AudioAnalyzer(os.path.join(tempfile.gettempdir(), 'does_not_exist_xyz.wav'), loop=True)
        a.start_stream()
        chunk = a.get_next_chunk()
        self.assertIsNotNone(chunk)
        res = a.analyze_chunk(chunk)
        self.assertIn('volume', res)
        self.assertIn('bass', res)
        a.cleanup()


class TestCorruptAudio(unittest.TestCase):
    """A corrupt/garbage file should not crash the analyzer."""

    def test_corrupt_wav_file(self):
        # Create a garbage file that is not valid audio
        fd, path = tempfile.mkstemp(suffix='.wav')
        with os.fdopen(fd, 'wb') as f:
            f.write(b'THIS IS NOT A VALID WAV FILE AT ALL ' * 100)
        try:
            from audio.analyzer import AudioAnalyzer
            # Should fall back to simulated data rather than crash
            a = AudioAnalyzer(path, loop=False)
            self.assertTrue(a.use_simulated)
            self.assertIsNotNone(a.audio_data)
            a.cleanup()
        finally:
            os.unlink(path)

    def test_empty_file(self):
        fd, path = tempfile.mkstemp(suffix='.mp3')
        os.close(fd)  # empty file
        try:
            from audio.analyzer import AudioAnalyzer
            a = AudioAnalyzer(path, loop=False)
            # Either simulated or empty data; must not raise on analyze
            a.start_stream()
            chunk = a.get_next_chunk()
            if chunk is not None:
                a.analyze_chunk(chunk)
            a.cleanup()
        finally:
            os.unlink(path)


class TestMissingFFmpeg(unittest.TestCase):
    """Analyzer should handle missing ffmpeg gracefully."""

    def test_missing_ffmpeg_falls_back(self):
        # Point FFMPEG_PATH to a nonexistent binary
        old = os.environ.get('FFMPEG_PATH')
        os.environ['FFMPEG_PATH'] = '/no/such/ffmpeg_binary_xyz'
        old_sound = os.environ.get('NO_SOUND')
        os.environ.pop('NO_SOUND', None)
        try:
            from audio.analyzer import AudioAnalyzer
            # Use a real-ish but tiny file; pydub may also fail -> simulated fallback
            fd, path = tempfile.mkstemp(suffix='.wav')
            os.close(fd)
            a = AudioAnalyzer(path, loop=False)
            # Must not raise; either loads or falls back to simulated
            self.assertIsNotNone(a.audio_data)
            a.cleanup()
        finally:
            if old is None:
                os.environ.pop('FFMPEG_PATH', None)
            else:
                os.environ['FFMPEG_PATH'] = old
            if old_sound is None:
                os.environ.pop('NO_SOUND', None)
            else:
                os.environ['NO_SOUND'] = old_sound


if __name__ == '__main__':
    unittest.main()