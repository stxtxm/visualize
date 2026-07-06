import os
import sys
import numpy as np
import cv2
import math

# Ensure we can import from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from effects.classic import ClassicEffect

def main():
    os.makedirs('output', exist_ok=True)
    
    width, height = 800, 450
    effect = ClassicEffect(width, height, color_palette='winamp_classic')
    
    # Mock audio data (representing an energetic peak with some bass and mid presence)
    bands = [0.2, 0.85, 0.9, 0.6, 0.4, 0.3, 0.25, 0.2, 0.15, 0.1]
    # Replicate to self.num_bars (48)
    extended_bands = []
    for i in range(48):
        idx = int(i * len(bands) / 48)
        # Add some wave variation for aesthetic organic look
        val = bands[idx] * (0.8 + 0.2 * math.sin(i * 0.5))
        extended_bands.append(val)
        
    audio_data = {
        'volume': 0.75,
        'energy': 0.7,
        'frequency_bands': extended_bands,
        'beat': True,
        'beat_strength': 0.85,
        'beat_phase': 0.0,
        'bpm': 128
    }
    
    # Simulate update frames to build peak values and smooth bars
    for f in range(15):
        # vary slightly to simulate movement
        audio_data['beat'] = (f == 10)
        effect.update(audio_data, 1.0 / 30.0)
        
    # Render
    frame = effect.render_to_array()
    
    # Save as PNG
    cv2.imwrite('output/preview.png', frame)
    print("Visual preview saved to output/preview.png")

if __name__ == '__main__':
    main()
