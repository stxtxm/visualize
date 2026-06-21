"""
Helper functions for psychedelic visualizer.
"""

import os
import subprocess
import numpy as np


def get_audio_duration(audio_file):
    """
    Get duration of audio file in seconds.
    
    Args:
        audio_file: Path to audio file
        
    Returns:
        float: Duration in seconds
    """
    try:
        # Use ffprobe to get duration
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_file
        ]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            duration = float(result.stdout.strip())
            return duration
    except Exception:
        pass
    
    # Fallback: estimate from file size
    # Assume MP3 at 128 kbps
    try:
        file_size = os.path.getsize(audio_file)
        bitrate = 128000  # 128 kbps
        duration = (file_size * 8) / bitrate
        return duration
    except:
        return 0.0


def format_time(seconds):
    """
    Format seconds as MM:SS.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        str: Formatted time string
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def ensure_directory(path):
    """
    Ensure a directory exists.
    
    Args:
        path: Directory path
        
    Returns:
        str: The directory path
    """
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def clamp(value, min_val, max_val):
    """
    Clamp a value between min and max.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


def lerp(a, b, t):
    """
    Linear interpolation.
    
    Args:
        a: Start value
        b: End value
        t: Interpolation factor (0-1)
        
    Returns:
        Interpolated value
    """
    return a + (b - a) * t


def smoothstep(edge0, edge1, x):
    """
    Smoothstep interpolation (smooth Hermite interpolation).
    
    Args:
        edge0: Lower bound
        edge1: Upper bound
        x: Input value
        
    Returns:
        Smooth interpolated value
    """
    t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def normalize_audio_data(audio_data, chunk_size=1024):
    """
    Normalize audio data for visualization.
    
    Args:
        audio_data: Raw audio data array
        chunk_size: Expected chunk size
        
    Returns:
        numpy.ndarray: Normalized audio data
    """
    if isinstance(audio_data, np.ndarray):
        data = audio_data.astype(np.float32)
    else:
        data = np.array(audio_data, dtype=np.float32)
    
    # Normalize to [-1, 1] range
    max_val = np.max(np.abs(data))
    if max_val > 0:
        data = data / max_val
    
    return data


def hsv_to_rgb(h, s, v):
    """
    Convert HSV to RGB color.
    
    Args:
        h: Hue (0-360)
        s: Saturation (0-1)
        v: Value (0-1)
        
    Returns:
        tuple: RGB color (0-255)
    """
    h = float(h)
    s = float(s)
    v = float(v)
    h60 = h / 60.0
    h60f = int(h60)
    p = v * (1 - s)
    q = v * (1 - s * (h60 - h60f))
    t = v * (1 - s * (1 - (h60 - h60f)))
    
    if h60f == 0:
        r, g, b = v, t, p
    elif h60f == 1:
        r, g, b = q, v, p
    elif h60f == 2:
        r, g, b = p, v, t
    elif h60f == 3:
        r, g, b = p, q, v
    elif h60f == 4:
        r, g, b = t, p, v
    elif h60f == 5:
        r, g, b = v, p, q
    else:
        r, g, b = 0, 0, 0
    
    return (int(r * 255), int(g * 255), int(b * 255))


def generate_rainbow_color(index, num_colors=7):
    """
    Generate a rainbow color based on index.
    
    Args:
        index: Color index
        num_colors: Number of colors in the rainbow
        
    Returns:
        tuple: RGB color
    """
    hue = (index % num_colors) / num_colors * 360.0
    return hsv_to_rgb(hue, 1.0, 1.0)
