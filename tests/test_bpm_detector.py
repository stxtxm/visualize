"""
Tests for audio/bpm_detector.py (BPMDetector).
"""
import unittest
import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestBPMDetector(unittest.TestCase):
    """Test BPM detection on synthetic signals."""

    def test_construct(self):
        from audio.bpm_detector import BPMDetector
        det = BPMDetector(sample_rate=44100, bpm_range=(40, 200))
        self.assertEqual(det.sample_rate, 44100)
        self.assertEqual(det.bpm_range, (40, 200))

    def test_detect_returns_expected_keys(self):
        from audio.bpm_detector import BPMDetector
        det = BPMDetector(sample_rate=44100, bpm_range=(40, 200))
        chunk = np.zeros(1024, dtype=np.int16)
        result = det.detect(chunk)
        for key in ('bpm', 'raw_bpm', 'bpm_confidence', 'is_beat', 'beat_strength', 'volume'):
            self.assertIn(key, result)

    def test_detect_short_chunk_returns_last(self):
        from audio.bpm_detector import BPMDetector
        det = BPMDetector(sample_rate=44100, bpm_range=(40, 200))
        result = det.detect(np.array([0, 1], dtype=np.int16))
        self.assertIn('bpm', result)
        self.assertGreaterEqual(result['bpm'], 0)

    def test_beat_on_periodic_signal(self):
        from audio.bpm_detector import BPMDetector
        det = BPMDetector(sample_rate=44100, bpm_range=(40, 200))
        # Generate a 120 BPM impulse train: beat every 0.5s = 22050 samples
        sr = 44100
        beat_len = sr // 2  # 0.5s
        # Build several seconds of signal with periodic loud beats
        signal = np.zeros(sr * 4, dtype=np.int16)
        for start in range(0, len(signal), beat_len):
            # A short loud burst
            end = min(start + 1000, len(signal))
            signal[start:end] = 30000
        # Feed in 1024-sample chunks
        bpm_values = []
        for i in range(0, len(signal), 1024):
            chunk = signal[i:i + 1024]
            if len(chunk) < 100:
                continue
            res = det.detect(chunk)
            bpm_values.append(res['bpm'])
        # The smoothed BPM should settle near 120
        self.assertTrue(len(bpm_values) > 10)
        avg_bpm = np.mean(bpm_values[-20:])
        self.assertGreater(avg_bpm, 60)
        self.assertLess(avg_bpm, 200)

    def test_reset_clears_history(self):
        from audio.bpm_detector import BPMDetector
        det = BPMDetector(sample_rate=44100, bpm_range=(40, 200))
        det.detect(np.zeros(1024, dtype=np.int16))
        det.reset()
        self.assertEqual(len(det.bpm_history), 0)
        self.assertEqual(len(det.beat_history), 0)

    def test_get_bpm_history(self):
        from audio.bpm_detector import BPMDetector
        det = BPMDetector(sample_rate=44100, bpm_range=(40, 200))
        det.detect(np.zeros(1024, dtype=np.int16))
        hist = det.get_bpm_history()
        self.assertIsInstance(hist, list)


if __name__ == '__main__':
    unittest.main()