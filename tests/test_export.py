"""Test: export a short video and verify with ffprobe."""
import subprocess, sys, os, tempfile


def test_export():
    audio = 'input/test.wav'
    if not os.path.exists(audio):
        subprocess.run([sys.executable, 'scripts/gen_test_audio.py'], check=True)

    output = os.path.join(tempfile.gettempdir(), 'test_ci_export.mp4')

    result = subprocess.run([
        sys.executable, 'main.py', audio,
        '--effect', 'random',
        '--color', 'psychedelic',
        '--export', output,
        '--preset', 'dev'
    ], capture_output=True, text=True, timeout=120)

    assert result.returncode == 0, f"Export failed:\n{result.stderr}"
    assert os.path.getsize(output) > 100000, f"Export too small: {os.path.getsize(output)}"

    result = subprocess.run(['ffprobe', output], capture_output=True, text=True)
    stderr = result.stderr + result.stdout
    assert 'Video:' in stderr, f"No video stream in output:\n{stderr}"
    assert 'Audio:' in stderr, f"No audio stream in output:\n{stderr}"

    os.unlink(output)
    print("Export test PASSED")


def test_cli_progress_output():
    """CLI export emits \\r progress markers and completion message."""
    audio = 'input/test.wav'
    if not os.path.exists(audio):
        subprocess.run([sys.executable, 'scripts/gen_test_audio.py'], check=True)

    output = os.path.join(tempfile.gettempdir(), 'test_cli_progress.mp4')

    result = subprocess.run([
        sys.executable, 'main.py', audio,
        '--effect', 'random',
        '--color', 'psychedelic',
        '--export', output,
        '--preset', 'dev'
    ], capture_output=True, text=True, timeout=120)

    try:
        assert result.returncode == 0, f"Export failed:\n{result.stderr}"
        # The progress line starts with \r and contains "Export:"
        assert 'Export:' in result.stdout, \
            f"CLI progress 'Export:' not found in stdout:\n{result.stdout}"
        # Completion message before or after newline
        assert 'complete' in result.stdout.lower(), \
            "Export completion message missing"
        assert os.path.getsize(output) > 100000
    finally:
        if os.path.exists(output):
            os.unlink(output)
    print("CLI progress output test PASSED")


def test_progress_callback_invoked():
    """VideoRecorder.record() calls progress_callback for each frame."""
    import numpy as np
    from recorder.video_recorder import VideoRecorder

    audio = 'input/test.wav'
    if not os.path.exists(audio):
        subprocess.run([sys.executable, 'scripts/gen_test_audio.py'], check=True)

    output = os.path.join(tempfile.gettempdir(), 'test_progress_cb.mp4')
    width, height, fps = 128, 72, 5

    def dummy_gen():
        for _ in range(10):
            yield np.zeros((height, width, 3), dtype=np.uint8)

    recorder = VideoRecorder(
        audio_file=audio,
        output_file=output,
        width=width, height=height, fps=fps,
        effect_type='bars',
    )

    calls = []
    try:
        recorder.record(
            effect_generator=dummy_gen(),
            progress_callback=lambda c, t: calls.append((c, t))
        )
        assert len(calls) == 10, f"Expected 10 callback invocations, got {len(calls)}"
        assert calls[-1][0] == 10, f"Last frame_count should be 10, got {calls[-1][0]}"
        assert calls[-1][1] > 0, f"total_frames should be > 0, got {calls[-1][1]}"
    finally:
        if os.path.exists(output):
            os.unlink(output)
    print("Progress callback test PASSED")


def test_audio_frame_reader_preserves_non_integer_samples_per_frame():
    """24 FPS must not lose frames because 44100 / 24 is fractional."""
    from audio.analyzer import AudioFrameReader

    audio = 'input/test.wav'
    if not os.path.exists(audio):
        subprocess.run([sys.executable, 'scripts/gen_test_audio.py'], check=True)

    reader = AudioFrameReader(audio, sample_rate=44100, fps=24)
    frames = 0
    try:
        while reader.read_frame() is not None:
            frames += 1
    finally:
        reader.close()

    # input/test.wav is five seconds long.
    assert frames == 120


def test_parallel_recorder_keeps_native_output_duration():
    """Parallel rendering keeps the requested video geometry and duration."""
    from recorder.video_recorder import VideoRecorder

    audio = 'input/test.wav'
    if not os.path.exists(audio):
        subprocess.run([sys.executable, 'scripts/gen_test_audio.py'], check=True)

    output = os.path.join(tempfile.gettempdir(), 'test_parallel_export.mp4')
    calls = []
    recorder = VideoRecorder(
        audio_file=audio,
        output_file=output,
        width=128,
        height=72,
        fps=5,
        effect_type='bars',
        render_workers=2,
    )
    try:
        recorder.record(progress_callback=lambda c, t: calls.append((c, t)))
        probe = subprocess.run([
            'ffprobe', '-v', 'error',
            '-show_entries', 'stream=width,height,duration',
            '-of', 'json', output,
        ], capture_output=True, text=True, check=True)
        assert '128' in probe.stdout
        assert '72' in probe.stdout
        assert calls[-1] == (25, 25)
    finally:
        if os.path.exists(output):
            os.unlink(output)


def test_export_with_background():
    """Export a short video with a real background image."""
    from PIL import Image
    bg_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            bg_path = tmp.name
        Image.new('RGB', (64, 64), (40, 80, 180)).save(bg_path)

        audio = 'input/test.wav'
        if not os.path.exists(audio):
            subprocess.run([sys.executable, 'scripts/gen_test_audio.py'], check=True)

        output = os.path.join(tempfile.gettempdir(), 'test_ci_export_bg.mp4')
        result = subprocess.run([
            sys.executable, 'main.py', audio,
            '--effect', 'trance_scope',
            '--color', 'psychedelic',
            '--background', bg_path,
            '--export', output,
            '--preset', 'dev'
        ], capture_output=True, text=True, timeout=120)

        assert result.returncode == 0, f"Export with background failed:\n{result.stderr}"
        assert os.path.getsize(output) > 100000, f"Export too small: {os.path.getsize(output)}"

        result = subprocess.run(['ffprobe', output], capture_output=True, text=True)
        stderr = result.stderr + result.stdout
        assert 'Video:' in stderr, f"No video stream:\n{stderr}"

        os.unlink(output)
    finally:
        if bg_path and os.path.exists(bg_path):
            os.unlink(bg_path)
    print("Export with background PASSED")


def test_export_with_background_opacity():
    """Export with --background-opacity flag."""
    from PIL import Image
    bg_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            bg_path = tmp.name
        Image.new('RGB', (64, 64), (40, 80, 180)).save(bg_path)

        audio = 'input/test.wav'
        if not os.path.exists(audio):
            subprocess.run([sys.executable, 'scripts/gen_test_audio.py'], check=True)

        output = os.path.join(tempfile.gettempdir(), 'test_ci_export_opacity.mp4')
        result = subprocess.run([
            sys.executable, 'main.py', audio,
            '--effect', 'trance_scope',
            '--color', 'psychedelic',
            '--background', bg_path,
            '--background-opacity', '0.5',
            '--export', output,
            '--preset', 'dev'
        ], capture_output=True, text=True, timeout=120)

        assert result.returncode == 0, f"Export with opacity failed:\n{result.stderr}"
        assert os.path.getsize(output) > 100000, f"Export too small: {os.path.getsize(output)}"

        result = subprocess.run(['ffprobe', output], capture_output=True, text=True)
        stderr = result.stderr + result.stdout
        assert 'Video:' in stderr, f"No video stream:\n{stderr}"

        os.unlink(output)
    finally:
        if bg_path and os.path.exists(bg_path):
            os.unlink(bg_path)
    print("Export with background opacity PASSED")


def test_export_vp9():
    """Export a short video using VP9 codec."""
    audio = 'input/test.wav'
    if not os.path.exists(audio):
        subprocess.run([sys.executable, 'scripts/gen_test_audio.py'], check=True)

    output = os.path.join(tempfile.gettempdir(), 'test_ci_export.webm')

    result = subprocess.run([
        sys.executable, 'main.py', audio,
        '--effect', 'random',
        '--color', 'psychedelic',
        '--export', output,
        '--preset', 'dev',
        '--codec', 'vp9',
    ], capture_output=True, text=True, timeout=120)

    assert result.returncode == 0, f"VP9 Export failed:\n{result.stderr}"
    assert os.path.exists(output), f"Output file does not exist: {output}"
    assert os.path.getsize(output) > 50000, f"VP9 Export too small: {os.path.getsize(output)}"

    result = subprocess.run(['ffprobe', output], capture_output=True, text=True)
    stderr = result.stderr + result.stdout
    assert 'vp9' in stderr.lower(), f"No VP9 video stream in output:\n{stderr}"
    assert 'opus' in stderr.lower(), f"No Opus audio stream in output:\n{stderr}"

    os.unlink(output)
    print("VP9 Export test PASSED")


def test_render_to_array_returns_fresh_buffer_each_frame():
    """Rendered frames must never be mutated while callers still own them.

    Export pipelines keep the previous frame(s) alive in the asynchronous
    FFmpeg writer queue while the next render executes.  If an effect returns
    (and rewrites) a cached internal buffer, queued bytes get overwritten:
    torn/black flashes in exports.  Model exactly that: keep every returned
    frame alive and require it to stay byte-identical after subsequent
    renders.  Allocator address reuse after release is harmless and allowed.
    """
    import random
    import numpy as np
    from effects.manager import EFFECT_MAP

    random.seed(42)
    np.random.seed(42)

    data = {
        'volume': 0.5, 'volume_smooth': 0.5,
        'frequency_bands': [0.1, 0.2, 0.3, 0.4, 0.5],
        'visual_bands': [0.2 + (i % 5) * 0.08 for i in range(32)],
        'spectrum': [0.1] * 512,
        'beat': True, 'beat_strength': 0.8, 'beat_phase': 0.1,
        'energy': 0.5, 'spectral_flux': 0.3, 'onset_strength': 0.4,
        'spectral_centroid': 0.4, 'bpm': 120.0, 'bpm_confidence': 0.9,
        'bass': 0.4, 'mids': 0.3, 'treble': 0.2,
    }

    checked = 0
    for effect_id, entry in EFFECT_MAP.items():
        module_name, class_name = entry
        if module_name == 'manager':
            continue  # 'random' selection placeholder
        module = __import__(f'effects.{module_name}', fromlist=[class_name])
        cls = getattr(module, class_name)
        effect = cls(width=160, height=90, color_palette='psychedelic')

        live = []  # frames a downstream writer could still be reading
        for _step in range(8):
            effect.update(data, 1.0 / 24)
            frame = effect.render_to_array()
            assert isinstance(frame, np.ndarray), f"{effect_id}: not ndarray"
            assert frame.shape == (90, 160, 3), f"{effect_id}: bad shape {frame.shape}"
            assert frame.dtype == np.uint8, f"{effect_id}: bad dtype {frame.dtype}"

            snapshots = [(buf, buf.copy()) for buf in live]
            effect.update(data, 1.0 / 24)
            effect.render_to_array()  # another render runs while frames stream
            for old, snapshot in snapshots:
                assert np.array_equal(old, snapshot), (
                    f"{effect_id} rewrote a previously returned frame; "
                    "asynchronous exports would encode corrupted bytes"
                )

            live.append(frame)
            if len(live) > 3:
                live.pop(0)  # mimic queue maxsize=2 + in-flight frame
        checked += 1
    assert checked >= 9, f"too few deterministic effects checked: {checked}"
    print("Frame ownership test PASSED")


def test_recorder_pads_truncated_source_to_exact_duration():
    """A source shorter than ffprobe's duration must still yield total_frames.

    Regression guard for 'audio ended N frame(s) early' warnings: the recorder
    generator pads silence until total_frames so published videos reach the
    requested duration exactly.
    """
    import io
    import contextlib
    from recorder.video_recorder import VideoRecorder

    audio = 'input/test.wav'
    if not os.path.exists(audio):
        subprocess.run([sys.executable, 'scripts/gen_test_audio.py'], check=True)

    output = os.path.join(tempfile.gettempdir(), 'test_pad_tail.mp4')
    if os.path.exists(output):
        os.unlink(output)

    recorder = VideoRecorder(
        audio_file=audio,
        output_file=output,
        width=128, height=72, fps=10,
        effect_type='bars',
        preset='dev',
        video_codec='h264',
    )

    real_probe = recorder._get_audio_duration  # bound method snapshot
    real_duration = real_probe(audio)

    def inflated_probe(path):
        # Simulate MP3 gapless/VBR: ffprobe overstates decodable PCM.
        return real_probe(path) + 1.5

    recorder._get_audio_duration = inflated_probe

    try:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            recorder.record()
        out = buffer.getvalue()
        assert 'audio ended' not in out, "recording stopped early:\n" + out[-800:]
        assert 'Video exported successfully' in out

        probe = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', output],
            capture_output=True, text=True, timeout=30,
        )
        measured = float(probe.stdout.strip())
        target = real_duration + 1.5
        # Padding must extend past the raw PCM length (old bug stopped here).
        assert measured >= real_duration + 1.05, (
            f"padding missing: measured={measured:.3f}s pcm={real_duration:.3f}s"
        )
        assert abs(measured - target) <= 0.6, (
            f"duration drift: measured={measured:.3f}s target={target:.3f}s"
        )
    finally:
        if os.path.exists(output):
            os.unlink(output)
    print("Tail-padding export test PASSED")


def test_validate_export_output_rejects_invalid_media():
    """validate_export_output fails loudly on non-media content."""
    import pytest
    from quality_presets import validate_export_output

    bogus = os.path.join(tempfile.gettempdir(), 'test_validate_bogus.mp4')
    with open(bogus, 'wb') as handle:
        handle.write(b'\x00' * 4096)
    try:
        with pytest.raises(RuntimeError):
            validate_export_output(bogus, expected_duration=30.0, fps=30)
    finally:
        if os.path.exists(bogus):
            os.unlink(bogus)
    print("Validation rejection test PASSED")


def test_validate_export_output_accepts_valid_clip():
    """A well-formed clip passes structural validation."""
    from quality_presets import validate_export_output

    good = os.path.join(tempfile.gettempdir(), 'test_validate_good.mp4')
    if os.path.exists(good):
        os.unlink(good)
    ffmpeg = os.environ.get('FFMPEG_PATH') or 'ffmpeg'
    try:
        subprocess.run(
            [ffmpeg, '-y', '-f', 'lavfi', '-i', 'color=c=black:s=64x64:d=0.5:r=10',
             '-loglevel', 'error', good],
            check=True, timeout=60,
        )
        info = validate_export_output(good, expect_audio=False)
        assert info.get('frames', 0) > 0
        assert abs((info.get('duration') or 0.0) - 0.5) <= 0.35
    finally:
        if os.path.exists(good):
            os.unlink(good)
    print("Validation acceptance test PASSED")


if __name__ == '__main__':
    test_export()
    test_export_vp9()
