"""
Tests for audio/player.py (AudioPlayer backend detection and lifecycle).
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAudioPlayerBackendDetection(unittest.TestCase):
    """Test backend detection logic without actually playing audio."""

    def test_player_constructs(self):
        from audio.player import AudioPlayer
        player = AudioPlayer(sample_rate=44100, chunk_size=1024, channels=2)
        self.assertEqual(player.sample_rate, 44100)
        self.assertEqual(player.chunk_size, 1024)
        # backend may be None if no audio backend available in CI
        self.assertIn(player._backend_name, (None, 'sounddevice', 'pyaudio', 'pygame', 'pw-play', 'ffplay', 'aplay', 'paplay'))

    def test_player_no_backend_is_safe(self):
        from audio.player import AudioPlayer
        # If no backend, start/stop/cleanup must not raise
        player = AudioPlayer(sample_rate=44100, chunk_size=1024, channels=2)
        if player._backend_name is None:
            player.start()
            player.play_chunk([0] * 1024)
            player.stop()
            player.cleanup()
            self.assertFalse(player.is_playing)

    def test_play_chunk_does_not_raise(self):
        from audio.player import AudioPlayer
        player = AudioPlayer(sample_rate=44100, chunk_size=1024, channels=2)
        # play_chunk before start should be a no-op
        player.play_chunk([0] * 1024)
        player.cleanup()

    def test_cleanup_idempotent(self):
        from audio.player import AudioPlayer
        player = AudioPlayer(sample_rate=44100, chunk_size=1024, channels=2)
        player.cleanup()
        player.cleanup()
        self.assertIsNone(player._stream)

    def test_get_elapsed_and_chunk_index(self):
        from audio.player import AudioPlayer
        player = AudioPlayer(sample_rate=44100, chunk_size=1024, channels=2)
        self.assertEqual(player.get_current_chunk_index(), 0)
        # get_elapsed_seconds returns 0.0 before start
        self.assertEqual(player.get_elapsed_seconds(), 0.0)


if __name__ == '__main__':
    unittest.main()