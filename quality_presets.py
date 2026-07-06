"""
Quality presets for video export.
Defines different quality/speed trade-offs for export.
"""

# Quality presets: (resolution, fps, ffmpeg_preset, crf, bitrate, description)
QUALITY_PRESETS = {
    'dev': {
        'name': 'Dev (Très rapide)',
        'resolution': '720p',
        'fps': 15,
        'ffmpeg_preset': 'ultrafast',
        'crf': '28',
        'bitrate': '5M',
        'description': 'Pour tests rapides - faible qualité',
        'export_time_factor': '0.25',  # ~4x faster than realtime
    },
    'fast': {
        'name': 'Rapide',
        'resolution': '720p',
        'fps': 20,
        'ffmpeg_preset': 'superfast',
        'crf': '23',
        'bitrate': '8M',
        'description': 'Bon compromis vitesse/qualité',
        'export_time_factor': '0.5',  # ~2x faster than realtime
    },
    'normal': {
        'name': 'Normale',
        'resolution': '1080p',
        'fps': 30,
        'ffmpeg_preset': 'fast',
        'crf': '18',
        'bitrate': '15M',
        'description': 'Qualité standard pour partage',
        'export_time_factor': '1.0',  # ~realtime
    },
    'high': {
        'name': 'Haute Qualité',
        'resolution': '1080p',
        'fps': 60,
        'ffmpeg_preset': 'medium',
        'crf': '18',
        'bitrate': '20M',
        'description': 'Meilleure qualité - plus lent',
        'export_time_factor': '1.5',  # ~1.5x slower than realtime
    },
    '4k': {
        'name': '4K Cinématique',
        'resolution': '4K',
        'fps': 30,
        'ffmpeg_preset': 'slow',
        'crf': '18',
        'bitrate': '40M',
        'description': 'Qualité maximale pour archives',
        'export_time_factor': '2.0',  # ~2x slower than realtime
    },
}

# Resolution mappings
RESOLUTIONS = {
    '720p': (1280, 720),
    '1080p': (1920, 1080),
    '1440p': (2560, 1440),
    '4K': (3840, 2160),
}


def get_preset(preset_name):
    """Get a quality preset by name."""
    return QUALITY_PRESETS.get(preset_name, QUALITY_PRESETS['normal'])


def get_available_presets():
    """Get list of available preset names."""
    return list(QUALITY_PRESETS.keys())


def get_preset_names():
    """Get list of preset display names."""
    return [p['name'] for p in QUALITY_PRESETS.values()]


_HAS_OPENH264 = None

def _check_openh264(ffmpeg_path):
    """Check if libopenh264 is available in ffmpeg."""
    import subprocess
    try:
        result = subprocess.run([ffmpeg_path, '-encoders'], capture_output=True, text=True, timeout=10)
        return 'libopenh264' in result.stdout
    except Exception:
        return False


def build_ffmpeg_cmd(width, height, fps, audio_file, output_file, preset='normal'):
    """Build FFmpeg command based on preset. Probes for libopenh264; falls back to libx264."""
    import os
    global _HAS_OPENH264
    ffmpeg_path = os.environ.get('FFMPEG_PATH') or 'ffmpeg'
    preset_config = get_preset(preset)
    resolution = f"{width}x{height}"
    
    bitrate = preset_config['bitrate']
    if width >= 3840:
        bitrate = "50M"
    elif width >= 2560:
        bitrate = "35M"
    elif width >= 1920:
        bitrate = "20M" if bitrate == "5M" else bitrate
    elif width >= 1280:
        bitrate = "10M" if bitrate == "5M" else bitrate
    
    if _HAS_OPENH264 is None:
        _HAS_OPENH264 = _check_openh264(ffmpeg_path)
    
    cmd = [
        ffmpeg_path,
        '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', resolution,
        '-pix_fmt', 'bgr24',
        '-r', str(fps),
        '-i', 'pipe:0',
        '-i', audio_file,
    ]
    
    if _HAS_OPENH264:
        cmd += ['-c:v', 'libopenh264', '-coder', 'cavlc']
    else:
        cmd += ['-c:v', 'libx264', '-preset', preset_config['ffmpeg_preset']]
    
    cmd += [
        '-b:v', bitrate,
        '-maxrate', bitrate,
        '-bufsize', bitrate,
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-movflags', '+faststart',
        '-shortest',
        '-threads', '0',
        '-loglevel', 'error',
        output_file
    ]
    return cmd
