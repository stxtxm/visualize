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
_HAS_X264 = None

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


def _has_x264(ffmpeg_path):
    """Return a cached result for the libx264 capability probe."""
    global _HAS_X264
    if _HAS_X264 is None:
        _HAS_X264 = _check_encoder(ffmpeg_path, 'libx264')
    return _HAS_X264


def encoder_probe_state():
    """Return the cached encoder capabilities for a spawned render worker.

    Probing an encoder performs several real FFmpeg encodes.  Workers started
    with the ``spawn`` method do not inherit module globals, so passing this
    small serializable state prevents every parallel segment from repeating
    those probes before it can render its first frame.
    """
    return {
        'openh264': _HAS_OPENH264,
        'hardware': _HAS_HW_ENCODER,
        'hardware_type': _HW_ENCODER_TYPE,
        'x264': _HAS_X264,
    }


def restore_encoder_probe_state(state):
    """Restore encoder capabilities previously returned by
    :func:`encoder_probe_state`.

    Invalid or partial state is ignored so normal probing remains the safe
    fallback for callers outside the parallel export pipeline.
    """
    if not isinstance(state, dict):
        return
    global _HAS_OPENH264, _HAS_HW_ENCODER, _HW_ENCODER_TYPE, _HAS_X264
    _HAS_OPENH264 = state.get('openh264', _HAS_OPENH264)
    _HAS_HW_ENCODER = state.get('hardware', _HAS_HW_ENCODER)
    _HW_ENCODER_TYPE = state.get('hardware_type', _HW_ENCODER_TYPE)
    _HAS_X264 = state.get('x264', _HAS_X264)


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
    global _HAS_OPENH264, _HAS_HW_ENCODER, _HW_ENCODER_TYPE, _HAS_X264
    ffmpeg_path = os.environ.get('FFMPEG_PATH') or 'ffmpeg'
    preset_config = get_preset(preset)
    codec = str(video_codec).lower()
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

    # VP9 and HEVC never use an H.264 encoder.  Avoid launching four-to-five
    # probe FFmpeg processes for each export (and, without transferred state,
    # for every spawned parallel worker) when they are irrelevant.
    needs_h264_probe = codec not in ('vp9', 'h265', 'hevc')
    if needs_h264_probe:
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

    is_webm = output_file.lower().endswith('.webm')

    # CRF-based encoders (VP9 constant-quality, libx264, libx265) must NOT
    # receive the generic `-b:v/-maxrate/-bufsize` cap below: constraining a
    # CRF stream throttles quality on busy frames, which shows up as visible
    # quality pumping / flashes in 4K exports.
    crf_based_rc = False

    if codec == 'vp9':
        # VP9: royalty-free codec, plays natively on all Linux distributions.
        # `-b:v 0` + CRF = true constant-quality mode.  The previous
        # `-b:v 20M -maxrate -bufsize` constrained mode made libvpx starve
        # quality on beat-heavy content: visible flashes in 4K exports.
        vp9_crf = '24' if width >= 3840 else '28'
        cmd += [
            '-c:v', 'libvpx-vp9',
            '-crf', vp9_crf,
            '-b:v', '0',
            '-deadline', 'good',
            '-cpu-used', '4',
            # Explicit tile counts triggered frame-corruption flashes on
            # some libvpx builds; auto tiling behind row-mt stays stable.
            '-row-mt', '1',
            '-g', str(max(1, int(fps * 2))),
        ]
        crf_based_rc = True
    elif codec in ('h265', 'hevc'):
        cmd += [
            '-c:v', 'libx265',
            '-preset', 'superfast',
            '-crf', '20',
            '-tag:v', 'hvc1',
            '-flags', '+cgop',
            '-g', str(max(1, int(fps * 2))),
        ]
        crf_based_rc = True
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
    elif _has_x264(ffmpeg_path):
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
        crf_based_rc = True
    else:
        # Host FFmpeg lacks H.264 software encoders (e.g. stock Fedora package).
        # Fall back to libvpx-vp9 which is universally shipped in all Linux FFmpeg packages.
        vp9_crf = '24' if width >= 3840 else '28'
        cmd += [
            '-c:v', 'libvpx-vp9',
            '-crf', vp9_crf,
            '-b:v', '0',
            '-deadline', 'good',
            '-cpu-used', '4',
            # Explicit tile counts triggered frame-corruption flashes on
            # some libvpx builds; auto tiling behind row-mt stays stable.
            '-row-mt', '1',
            '-g', str(max(1, int(fps * 2))),
        ]
        crf_based_rc = True

    # Bitrate caps only apply to encoders that are not CRF-driven
    # (hardware encoders, libopenh264).  CRF encoders stay unconstrained.
    if not crf_based_rc:
        cmd += [
            '-b:v', bitrate,
            '-maxrate', bitrate,
            '-bufsize', bitrate,
        ]
    cmd += [
        '-pix_fmt', 'yuv420p',
    ]

    if audio_file:
        # Pad audio with silence up to the video length (total_frames ceil).
        # Without apad, `-shortest` truncates video to audio (floor) and the
        # padded last video frame is discarded.  With apad, audio is extended
        # to video and `-shortest` keeps the full ceil duration.
        #
        # NOTE: no dynaudnorm/loudness filter here — dynamic normalization
        # alters the mix over time and breaks fidelity to the source audio.
        # Higher audio bitrates keep the re-encode transparent:
        # AAC 256k / Opus 224k sit well above the transparency threshold.
        if is_webm:
            # WebM container requires Opus or Vorbis audio (not AAC).
            cmd += [
                '-c:a', 'libopus',
                '-b:a', '224k',
                '-af', 'apad',
                '-shortest',
            ]
        else:
            cmd += [
                '-c:a', 'aac',
                '-b:a', '256k',
                '-af', 'apad',
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



def preserve_failed_partial(partial_file):
    """Keep a rejected ``*.part.*`` intermediate for post-mortem analysis.

    Failed exports must not silently destroy the evidence of what FFmpeg
    actually produced: the partial is renamed next to the target as
    ``<target>.rejected.<ext>`` (any previous rejected file is replaced).
    Returns the preserved path, or ``None`` when nothing could be kept.
    """
    import logging

    try:
        if not partial_file or not os.path.exists(partial_file):
            return None
        base, ext = os.path.splitext(str(partial_file))
        # Drop the double extension produced by ``<out>.part.webm`` so the
        # rejected artefact reads like ``azer.rejected.webm``.
        first_base, first_ext = os.path.splitext(base)
        if first_ext in ('.part',):
            base = first_base
            ext = ext or first_ext
        rejected = f"{base}.rejected{ext}"
        try:
            if os.path.exists(rejected):
                os.remove(rejected)
        except OSError:
            pass
        os.replace(str(partial_file), rejected)
        print(
            f"  Preserved failed output for inspection: {rejected} "
            f"({os.path.getsize(rejected)} bytes)"
        )
        logging.getLogger(__name__).info(
            "preserved failed export artifact: %s", rejected
        )
        return rejected
    except Exception:
        # Preservation must never mask the original failure.
        return None

def validate_export_output(output_file, expected_duration=None, fps=None,
                           expect_audio=True):
    """Validate an exported media file before publishing it.

    Parses FFprobe metadata and fails loudly when the produced file cannot be
    played reliably: missing video/audio stream, zero video packets, or a
    duration far away from the requested export length.  When FFprobe is not
    installed or individual metrics are missing, the check degrades to a
    printed notice so exports are never blocked by tooling differences.

    Args:
        output_file: media file (typically the ``*.part.*`` intermediate) to
            inspect.
        expected_duration: requested video duration in seconds
            (``total_frames / fps``).
        fps: export frame rate, refines the duration tolerance.
        expect_audio: require an audio stream (exports without source audio
            can pass ``False``).

    Returns:
        dict with measured ``duration``, ``frames``, ``video_codec`` and
        ``audio_codec``.

    Raises:
        RuntimeError: when the output is unusable or badly out of spec.
    """
    import json as _json
    import subprocess as _subprocess

    ffprobe_path = os.environ.get('FFPROBE_PATH') or 'ffprobe'
    # Pair bundled FFprobe with its own libraries exactly like the encoder
    # probes do; a system FFprobe running under AppImage LD_LIBRARY_PATH or a
    # bundled one missing its libs would fail for environment reasons rather
    # than because of the produced file.
    probe_env = _ffmpeg_environment(ffprobe_path)

    strict_cmd = [ffprobe_path, '-v', 'error', '-print_format', 'json',
                  '-show_format', '-show_streams']
    lenient_cmd = [ffprobe_path, '-v', 'fatal', '-err_detect', 'ignore_err',
                   '-print_format', 'json', '-show_format', '-show_streams']

    meta = None
    errors_seen = []
    used_lenient = False
    for attempt, (probe, timeout) in enumerate(((strict_cmd, 90), (lenient_cmd, 180))):
        try:
            run_result = _subprocess.run(
                probe + [str(output_file)],
                capture_output=True, timeout=timeout, env=probe_env,
            )
        except FileNotFoundError:
            print("  Validation skipped: ffprobe not found")
            return {}
        except _subprocess.TimeoutExpired:
            print("  Validation skipped: ffprobe timed out")
            return {}

        if run_result.returncode == 0:
            try:
                meta = _json.loads(run_result.stdout.decode('utf-8', errors='ignore'))
                break
            except ValueError:
                pass

        detail = run_result.stderr.decode('utf-8', errors='ignore').strip()[:300]
        errors_seen.append(detail or f"exit code {run_result.returncode}")
        if attempt == 1:
            used_lenient = True

    if meta is None:
        joined = " | ".join(errors_seen[-2:])
        raise RuntimeError(
            "Export validation failed: FFprobe could not parse "
            f"{output_file}: {joined}"
        )
    if used_lenient:
        print("  Validation noticed stream warnings (accepted after retry)")

    streams = meta.get('streams') or []
    video_streams = [s for s in streams if s.get('codec_type') == 'video']
    audio_streams = [s for s in streams if s.get('codec_type') == 'audio']
    video_stream = video_streams[0] if video_streams else {}

    def _to_float(value):
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed == parsed else None  # filter NaN

    stream_duration = _to_float(video_stream.get('duration'))
    format_duration = _to_float((meta.get('format') or {}).get('duration'))
    measured_duration = stream_duration or format_duration

    frames = None
    try:
        frames = int(video_stream.get('nb_frames'))
    except (TypeError, ValueError):
        pass
    if frames is None:
        try:
            counter = _subprocess.run(
                [ffprobe_path, '-v', 'error', '-select_streams', 'v:0',
                 '-count_packets', '-show_entries', 'stream=nb_read_packets',
                 '-of', 'default=noprint_wrappers=1:nokey=1', str(output_file)],
                capture_output=True, timeout=120,
            )
            if counter.returncode == 0:
                frames = int(counter.stdout.strip())
        except (FileNotFoundError, _subprocess.TimeoutExpired, ValueError):
            frames = None

    problems = []
    if not video_streams:
        problems.append("no video stream")
    elif frames == 0:
        problems.append("zero video frames encoded")
    if expect_audio and not audio_streams:
        problems.append("no audio stream")

    tolerance = max(0.35, (6.0 / fps) if fps and fps > 0 else 0.0)
    if expected_duration is not None and measured_duration is not None:
        drift = abs(measured_duration - float(expected_duration))
        if drift > tolerance:
            problems.append(
                f"duration {measured_duration:.2f}s, expected "
                f"{float(expected_duration):.2f}s (+/-{tolerance:.2f}s)"
            )

    info = {
        'duration': measured_duration,
        'frames': frames,
        'video_codec': video_streams[0].get('codec_name') if video_streams else None,
        'audio_codec': audio_streams[0].get('codec_name') if audio_streams else None,
    }
    if problems:
        raise RuntimeError(
            "Export validation failed (" + "; ".join(problems) + ")"
        )

    parts = ["unknown duration" if measured_duration is None
             else f"{measured_duration:.2f}s"]
    if frames is not None:
        parts.append(f"{frames} video frames")
    for key in ('video_codec', 'audio_codec'):
        if info[key]:
            parts.append(str(info[key]))
    print("  Validated output: " + ", ".join(parts))
    return info
