"""
Quality presets for video export.
Defines different quality/speed trade-offs for export.
"""

import os

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
        'ffmpeg_preset': 'superfast',
        'crf': '18',
        'bitrate': '15M',
        'description': 'Qualité standard pour partage',
        'export_time_factor': '1.0',  # ~realtime
    },
    'high': {
        'name': 'Haute Qualité',
        'resolution': '1080p',
        'fps': 60,
        'ffmpeg_preset': 'superfast',
        'crf': '18',
        'bitrate': '20M',
        'description': 'Meilleure qualité - plus lent',
        'export_time_factor': '1.5',  # ~1.5x slower than realtime
    },
    '4k': {
        'name': '4K Cinématique',
        'resolution': '4K',
        'fps': 30,
        'ffmpeg_preset': 'superfast',
        'crf': '18',
        'bitrate': '20M',
        'description': 'Qualité maximale - compatible partout (≈4-5 Go/h)',
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


def recommended_render_workers(width, height):
    """Choose optimal worker count for parallel video rendering across CPU cores."""
    cpus = os.cpu_count() or 2
    cpu_workers = max(1, cpus - 1 if cpus > 2 else cpus)

    if width >= 3840:
        per_worker_mb = 768
    elif width >= 2560:
        per_worker_mb = 384
    else:
        per_worker_mb = 192

    available = None
    try:
        with open('/proc/meminfo', 'r', encoding='ascii') as handle:
            for line in handle:
                if line.startswith('MemAvailable:'):
                    available = int(line.split()[1]) * 1024
                    break
    except (OSError, ValueError):
        pass

    if available is None:
        try:
            available = os.sysconf('SC_AVPHYS_PAGES') * os.sysconf('SC_PAGE_SIZE')
        except (AttributeError, OSError, ValueError):
            return cpu_workers

    memory_workers = max(
        1, int(max(0, available - 1024 * 1024 ** 2) // (per_worker_mb * 1024 ** 2))
    )
    return max(1, min(cpu_workers, memory_workers))


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


def _ffmpeg_environment(ffmpeg_path):
    """Use bundled libraries only for bundled FFmpeg probes."""
    env = os.environ.copy()
    self_dir = env.get('SELF_DIR')
    try:
        bundled = self_dir and os.path.realpath(ffmpeg_path).startswith(
            os.path.realpath(self_dir) + os.sep
        )
    except OSError:
        bundled = False
    if bundled:
        env['LD_LIBRARY_PATH'] = os.path.join(self_dir, 'usr', 'lib')
    else:
        env.pop('LD_LIBRARY_PATH', None)
    return env


def _check_encoder(ffmpeg_path, encoder):
    """Check if a video encoder is actually functional in FFmpeg.

    Probes by attempting a real encode of a 64x64 frame. Returns True if
    the encoder succeeds, False otherwise.
    """
    import subprocess, tempfile, os
    out_path = None
    try:
        ext = '.webm' if encoder in ('libvpx-vp9', 'vp9') else '.mp4'
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
            out_path = f.name
        cmd = [
            ffmpeg_path, '-y',
            '-f', 'rawvideo', '-s', '64x64', '-pix_fmt', 'bgr24', '-r', '1',
            '-i', 'pipe:0',
            '-c:v', encoder,
            '-frames:v', '1',
            '-an', '-loglevel', 'quiet',
            out_path,
        ]
        proc = subprocess.run(
            cmd, input=b'\x00' * (64 * 64 * 3), capture_output=True, timeout=10,
            env=_ffmpeg_environment(ffmpeg_path),
        )
        success = (proc.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 0)
        return success
    except Exception:
        return False
    finally:
        if out_path and os.path.exists(out_path):
            try:
                os.unlink(out_path)
            except Exception:
                pass


def _check_openh264(ffmpeg_path):
    """Check if libopenh264 is functional in ffmpeg."""
    return _check_encoder(ffmpeg_path, 'libopenh264')


def _check_hardware_encoder(ffmpeg_path):
    """Check for hardware-accelerated H.264 encoders.

    Priority: h264_nvenc > h264_vaapi > h264_videotoolbox
    """
    candidates = ('h264_nvenc', 'h264_vaapi', 'h264_videotoolbox')
    for encoder in candidates:
        if _check_encoder(ffmpeg_path, encoder):
            return encoder
    return None


def build_ffmpeg_cmd(width, height, fps, audio_file, output_file, preset='normal',
                     render_width=None, render_height=None, ffmpeg_threads=0,
                     video_codec='h264'):
    """Build FFmpeg command based on preset.

    Probes for hardware encoders (NVENC > VAAPI > VideoToolbox),
    then libopenh264, then falls back to libx264.

    When render_width/render_height differ from width/height,
    a lanczos scale filter is added (render scaling).

    ``ffmpeg_threads`` can limit each encoder process. Parallel segment
    exports use one thread per FFmpeg process so codec-internal threading does
    not multiply across workers.
    """
    import os
    global _HAS_OPENH264, _HAS_HW_ENCODER, _HW_ENCODER_TYPE
    ffmpeg_path = os.environ.get('FFMPEG_PATH') or 'ffmpeg'
    preset_config = get_preset(preset)
    force_software = os.environ.get('VISUALIZE_SOFTWARE_ENCODER', '').lower() in {
        '1', 'true', 'yes', 'on'
    }
    prefer_x264 = os.environ.get('VISUALIZE_PREFER_X264', '').lower() in {
        '1', 'true', 'yes', 'on'
    }

    if render_width is None:
        render_width = width
    if render_height is None:
        render_height = height

    bitrate = preset_config['bitrate']
    if width >= 3840:
        # 20 Mbps is Netflix/YouTube 4K quality range — universally playable,
        # visually identical to higher bitrates for animated content with CRF 18.
        # The old 50M cap produced ~20 GB/hour files that choke software decoders.
        bitrate = "20M"
    elif width >= 2560:
        bitrate = "15M"
    elif width >= 1920:
        bitrate = "15M" if bitrate == "5M" else bitrate
    elif width >= 1280:
        bitrate = "8M" if bitrate == "5M" else bitrate

    if force_software:
        # Explicit compatibility override for hosts where hardware probing
        # must not touch vendor drivers. The bundled FFmpeg includes libx264.
        _HAS_OPENH264 = False
        _HAS_HW_ENCODER = False
        _HW_ENCODER_TYPE = None
    elif _HAS_OPENH264 is None:
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
        '-pix_fmt', 'rgb24',
        '-r', str(fps),
        '-i', 'pipe:0',
    ]

    if audio_file:
        cmd += ['-i', audio_file]

    needs_scale = (render_width != width or render_height != height)
    if needs_scale:
        cmd += ['-vf', f'scale={width}:{height}:flags=lanczos']

    codec = str(video_codec).lower()
    is_webm = output_file.lower().endswith('.webm')

    if codec == 'vp9':
        # VP9: royalty-free codec, plays natively on all Linux distributions.
        # -deadline realtime -cpu-used 8 + tile columns provides 4x-8x faster encoding
        # while keeping visual CRF quality intact.
        vp9_crf = '31' if width >= 3840 else '30'
        cmd += [
            '-c:v', 'libvpx-vp9',
            '-crf', vp9_crf,
            '-b:v', bitrate,
            '-deadline', 'realtime',
            '-cpu-used', '8',
            '-row-mt', '1',
            '-tile-columns', '2',
            '-tile-rows', '1',
            '-g', str(max(1, int(fps * 2))),
        ]
    elif codec in ('h265', 'hevc'):
        cmd += [
            '-c:v', 'libx265',
            '-preset', 'superfast',
            '-crf', '20',
            '-tag:v', 'hvc1',
            '-flags', '+cgop',
            '-g', str(max(1, int(fps * 2))),
        ]
    elif _HAS_HW_ENCODER and _HW_ENCODER_TYPE:
        encoder = _HW_ENCODER_TYPE
        if encoder == 'h264_nvenc':
            cmd += [
                '-c:v', 'h264_nvenc',
                '-preset', 'p7',
                '-rc', 'vbr',
                '-cq', '18',
                '-maxrate', bitrate,
                '-bufsize', bitrate,
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
    elif _HAS_OPENH264 and not prefer_x264:
        cmd += ['-c:v', 'libopenh264', '-coder', 'cavlc']
    elif _check_encoder(ffmpeg_path, 'libx264'):
        encoder_preset = preset_config['ffmpeg_preset']
        if (
            width >= 3840
            and os.environ.get('VISUALIZE_4K_SAFE', '').lower() in {
                '1', 'true', 'yes', 'on'
            }
        ):
            encoder_preset = 'superfast'
        cmd += [
            '-c:v', 'libx264',
            '-preset', encoder_preset,
            '-crf', preset_config['crf'],
            '-tune', 'animation',
            '-profile:v', 'high',
            '-flags', '+cgop',
            '-g', str(max(1, int(fps * 2))),
            '-bf', '2',
        ]
    else:
        # Host FFmpeg lacks H.264 software encoders (e.g. stock Fedora package).
        # Fall back to libvpx-vp9 which is universally shipped in all Linux FFmpeg packages.
        vp9_crf = '31' if width >= 3840 else '30'
        cmd += [
            '-c:v', 'libvpx-vp9',
            '-crf', vp9_crf,
            '-b:v', bitrate,
            '-deadline', 'realtime',
            '-cpu-used', '8',
            '-row-mt', '1',
            '-tile-columns', '2',
            '-tile-rows', '1',
            '-g', str(max(1, int(fps * 2))),
        ]

    cmd += [
        '-b:v', bitrate,
        '-maxrate', bitrate,
        '-bufsize', bitrate,
        '-pix_fmt', 'yuv420p',
    ]

    if audio_file:
        if is_webm:
            # WebM container requires Opus or Vorbis audio (not AAC).
            cmd += [
                '-c:a', 'libopus',
                '-b:a', '192k',
                '-af', 'dynaudnorm=peak=0.95',
                '-shortest',
            ]
        else:
            cmd += [
                '-c:a', 'aac',
                '-b:a', '192k',
                '-af', 'dynaudnorm=peak=0.95',
                '-shortest',
            ]

    thread_opts = [
        '-threads', str(max(0, int(ffmpeg_threads))),
        # ``-threads`` alone does not cap FFmpeg's filter graph.  With a
        # 4K scale filter, automatic filter threading can retain dozens of
        # full-size frames per segment.  Keep this bounded for long exports;
        # it prevents the multi-gigabyte RSS and swap storm seen on laptops.
        '-filter_threads', str(max(0, int(ffmpeg_threads))),
        '-filter_complex_threads', str(max(0, int(ffmpeg_threads))),
    ]
    if output_file.lower().endswith('.mp4'):
        # faststart is MP4-only (moves moov atom to the front for streaming).
        cmd += ['-movflags', '+faststart']
    cmd += thread_opts
    cmd += ['-loglevel', 'error', output_file]
    return cmd


def codec_for_output(video_codec, output_file):
    """Return the effective codec and recommended file extension.

    When *video_codec* is ``'vp9'`` and *output_file* ends in ``.mp4``,
    the extension is changed to ``.webm`` so the container matches the
    codec natively.  All other codecs keep ``.mp4``.
    """
    codec = str(video_codec).lower()
    if codec == 'vp9':
        base, ext = os.path.splitext(output_file)
        if ext.lower() != '.webm':
            output_file = base + '.webm'
        return codec, output_file
    return codec, output_file
