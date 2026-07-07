"""
Tests for CLI argument parsing and entry-point behavior (main.py).
"""
import unittest
import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(PROJECT_ROOT, 'main.py')


class TestCLIArgumentParsing(unittest.TestCase):
    """Verify argparse choices and validation."""

    def _run_main(self, args, expect_rc=1):
        proc = subprocess.run(
            [sys.executable, MAIN] + args,
            capture_output=True, text=True, timeout=30,
            cwd=PROJECT_ROOT,
        )
        return proc

    def test_invalid_effect_rejected(self):
        proc = self._run_main(['nonexistent.wav', '--effect', 'bogus'])
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('error', proc.stderr.lower())

    def test_invalid_color_rejected(self):
        proc = self._run_main(['nonexistent.wav', '--color', 'bogus'])
        self.assertNotEqual(proc.returncode, 0)

    def test_invalid_preset_rejected(self):
        proc = self._run_main(['nonexistent.wav', '--preset', 'bogus'])
        self.assertNotEqual(proc.returncode, 0)

    def test_missing_audio_file_errors(self):
        proc = self._run_main(['/no/such/file.mp3', '--export', '/tmp/out.mp4'])
        self.assertNotEqual(proc.returncode, 0)
        # Error message goes to stdout, not stderr
        self.assertTrue('not found' in proc.stdout.lower() or 'not found' in proc.stderr.lower())

    def test_no_args_launches_gui_or_errors(self):
        # With no args and no file, main.py prints usage error and exits
        proc = self._run_main(['--no-gui'])
        self.assertNotEqual(proc.returncode, 0)
        output = (proc.stdout + proc.stderr).lower()
        # Error message is in French (Utilisation) or English (usage)
        self.assertTrue('usage' in output or 'utilisation' in output)

    def test_help_runs(self):
        proc = self._run_main(['--help'])
        self.assertEqual(proc.returncode, 0)
        self.assertIn('Psychedelic', proc.stdout)


class TestCLIExportInvocation(unittest.TestCase):
    """Verify the CLI export path is reachable (uses generated test audio)."""

    def test_export_dev_short(self):
        # Generate a short test wav if needed
        wav = os.path.join(PROJECT_ROOT, 'input', 'test.wav')
        if not os.path.exists(wav):
            subprocess.run([sys.executable, 'scripts/gen_test_audio.py'],
                           check=True, cwd=PROJECT_ROOT)
        out = '/tmp/test_cli_export.mp4'
        if os.path.exists(out):
            os.remove(out)
        proc = subprocess.run(
            [sys.executable, MAIN, wav, '--export', out, '--preset', 'dev'],
            capture_output=True, text=True, timeout=120, cwd=PROJECT_ROOT,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(os.path.exists(out))
        self.assertGreater(os.path.getsize(out), 1000)
        os.remove(out)


if __name__ == '__main__':
    unittest.main()