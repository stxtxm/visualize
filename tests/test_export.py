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


if __name__ == '__main__':
    test_export()
