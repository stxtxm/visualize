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
        'ffmpeg_preset': 'medium',
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
_HAS_HW_ENCODER = None
_HW_ENCODER_TYPE = None  # 'h264_nvenc', 'h264_vaapi', 'h264_videotoolbox', or None

HW_ENCODERS = {
    'h264_nvenc': 'NVIDIA NVENC',
    'h264_vaapi': 'Intel/AMD VAAPI',
    'h264_videotoolbox': 'Apple VideoToolbox',
}


def _check_openh264(ffmpeg_path):
    """Check if libopenh264 is available in ffmpeg."""
    import subprocess
    try:
        result = subprocess.run([ffmpeg_path, '-encoders'], capture_output=True, text=True, timeout=10)
        return 'libopenh264' in result.stdout
    except Exception:
        return False


def _check_hardware_encoder(ffmpeg_path):
    """Check for hardware-accelerated H.264 encoders.

    Probes each candidate encoder by attempting a real encode of a
    single 2x2 frame. This catches cases where the encoder is listed
    in ffmpeg output but the required runtime (e.g. libcuda.so) is not
    actually usable.

    Returns encoder name (e.g. 'h264_nvenc') or None if none found.
    Priority: h264_nvenc > h264_vaapi > h264_videotoolbox
    """
    import subprocess, tempfile, os

    candidates = ('h264_nvenc', 'h264_vaapi', 'h264_videotoolbox')
    for encoder in candidates:
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
                out_path = f.name
            cmd = [
                ffmpeg_path, '-y',
                '-f', 'rawvideo', '-s', '2x2', '-pix_fmt', 'bgr24', '-r', '1',
                '-i', 'pipe:0',
                '-c:v', encoder,
                '-frames:v', '1',
                '-an', '-loglevel', 'quiet',
                out_path,
            ]
            proc = subprocess.run(cmd, input=b'\x00' * 12,
                                  capture_output=True, timeout=10)
            os.unlink(out_path)
            if proc.returncode == 0:
                return encoder
        except Exception:
            try:
                os.unlink(out_path)
            except Exception:
                pass
    return None


def build_ffmpeg_cmd(width, height, fps, audio_file, output_file, preset='normal',
                     render_width=None, render_height=None):
    """Build FFmpeg command based on preset.

    Probes for hardware encoders (NVENC > VAAPI > VideoToolbox),
    then libopenh264, then falls back to libx264.

    When render_width/render_height differ from width/height,
    a lanczos scale filter is added (render scaling).
    """
    import os
    global _HAS_OPENH264, _HAS_HW_ENCODER, _HW_ENCODER_TYPE
    ffmpeg_path = os.environ.get('FFMPEG_PATH') or 'ffmpeg'
    preset_config = get_preset(preset)

    if render_width is None:
        render_width = width
    if render_height is None:
        render_height = height

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

    if _HAS_HW_ENCODER is None:
        hw_encoder = _check_hardware_encoder(ffmpeg_path)
        if hw_encoder:
            _HAS_HW_ENCODER = True
            _HW_ENCODER_TYPE = hw_encoder
        else:
            _HAS_HW_ENCODER = False
            _HW_ENCODER_TYPE = None

    cmd = [
        ffmpeg_path,
        '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f"{render_width}x{render_height}",
        '-pix_fmt', 'bgr24',
        '-r', str(fps),
        '-i', 'pipe:0',
        '-i', audio_file,
    ]

    needs_scale = (render_width != width or render_height != height)
    if needs_scale:
        cmd += ['-vf', f'scale={width}:{height}:flags=lanczos']

    if _HAS_HW_ENCODER and _HW_ENCODER_TYPE:
        encoder = _HW_ENCODER_TYPE
        if encoder == 'h264_nvenc':
            cmd += [
                '-c:v', 'h264_nvenc',
                '-preset', 'p7',
                '-rc', 'vbr',
                '-cq', '18',
                '-profile:v', 'high',
                '-g', str(max(1, int(fps * 2))),
                '-bf', '2',
            ]
        elif encoder == 'h264_vaapi':
            cmd += [
                '-c:v', 'h264_vaapi',
                '-global_quality', '18',
                '-profile:v', 'high',
                '-g', str(max(1, int(fps * 2))),
                '-bf', '2',
            ]
        elif encoder == 'h264_videotoolbox':
            cmd += [
                '-c:v', 'h264_videotoolbox',
                '-q:v', '18',
                '-profile:v', 'high',
            ]
    elif _HAS_OPENH264:
        cmd += ['-c:v', 'libopenh264', '-coder', 'cavlc']
    else:
        cmd += [
            '-c:v', 'libx264',
            '-preset', preset_config['ffmpeg_preset'],
            '-crf', preset_config['crf'],
            '-tune', 'animation',
            '-profile:v', 'high',
            '-g', str(max(1, int(fps * 2))),
            '-bf', '2',
        ]

    cmd += [
        '-b:v', bitrate,
        '-maxrate', bitrate,
        '-bufsize', bitrate,
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-af', 'dynaudnorm=peak=0.95',
        '-movflags', '+faststart',
        '-shortest',
        '-threads', '0',
        '-loglevel', 'error',
        output_file
    ]
    return cmd
