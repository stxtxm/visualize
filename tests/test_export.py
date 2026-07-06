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


if __name__ == '__main__':
    test_export()
