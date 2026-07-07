"""Test: export a short video and verify with ffprobe."""
import subprocess, sys, os


def test_export():
    audio = 'input/test.wav'
    if not os.path.exists(audio):
        subprocess.run([sys.executable, 'scripts/gen_test_audio.py'], check=True)

    output = '/tmp/test_ci_export.mp4'

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


def test_export_with_background():
    """Export a short video with a real background image."""
    from PIL import Image
    import tempfile

    bg_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            bg_path = tmp.name
        Image.new('RGB', (64, 64), (40, 80, 180)).save(bg_path)

        audio = 'input/test.wav'
        if not os.path.exists(audio):
            subprocess.run([sys.executable, 'scripts/gen_test_audio.py'], check=True)

        output = '/tmp/test_ci_export_bg.mp4'
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


if __name__ == '__main__':
    test_export()
