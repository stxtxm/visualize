#!/usr/bin/env python3
"""Generate a 10s sine wave WAV for CI testing."""
import numpy as np
import wave, os

sr = 44100
duration = 10
t = np.linspace(0, duration, int(sr * duration), endpoint=False)
sine = (np.sin(2 * np.pi * 220 * t) + np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 880 * t))
sine = (sine / 3 * 32767).astype(np.int16)

os.makedirs('input', exist_ok=True)
with wave.open('input/test.wav', 'w') as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(sr)
    wf.writeframes(sine.tobytes())
print("Generated input/test.wav")
