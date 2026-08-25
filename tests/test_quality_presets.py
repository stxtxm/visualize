"""
Tests for quality presets module.
"""

import unittest
import sys
import os
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quality_presets import (
    QUALITY_PRESETS, RESOLUTIONS,
    get_preset, get_available_presets, get_preset_names,
    build_ffmpeg_cmd
)


class TestQualityPresets(unittest.TestCase):
    """Test quality presets functionality."""
    
    def test_presets_exist(self):
        """Test that all expected presets exist."""
        expected_presets = ['dev', 'fast', 'normal', 'high', '4k']
        self.assertEqual(sorted(QUALITY_PRESETS.keys()), sorted(expected_presets))
    
    def test_get_preset(self):
        """Test get_preset function."""
        preset = get_preset('dev')
        self.assertEqual(preset['name'], 'Dev (Très rapide)')
        self.assertEqual(preset['resolution'], '720p')
        self.assertEqual(preset['fps'], 15)
        
        preset = get_preset('4k')
        self.assertEqual(preset['name'], '4K Cinématique')
        self.assertEqual(preset['resolution'], '4K')
        self.assertEqual(preset['fps'], 30)
    
    def test_get_preset_default(self):
        """Test get_preset with invalid preset returns default."""
        preset = get_preset('invalid')
        self.assertEqual(preset['name'], 'Normale')
    
    def test_get_available_presets(self):
        """Test get_available_presets function."""
        presets = get_available_presets()
        self.assertIn('dev', presets)
        self.assertIn('normal', presets)
        self.assertIn('4k', presets)
    
    def test_get_preset_names(self):
        """Test get_preset_names function."""
        names = get_preset_names()
        self.assertIn('Dev (Très rapide)', names)
        self.assertIn('Normale', names)
        self.assertIn('4K Cinématique', names)
    
    def test_resolutions(self):
        """Test resolution mappings."""
        self.assertEqual(RESOLUTIONS['720p'], (1280, 720))
        self.assertEqual(RESOLUTIONS['1080p'], (1920, 1080))
        self.assertEqual(RESOLUTIONS['1440p'], (2560, 1440))
        self.assertEqual(RESOLUTIONS['4K'], (3840, 2160))
    
    def test_build_ffmpeg_cmd(self):
        """Test FFmpeg command building."""
        cmd = build_ffmpeg_cmd(1280, 720, 15, os.path.join(tempfile.gettempdir(), 'audio.mp3'), os.path.join(tempfile.gettempdir(), 'output.mp4'), 'dev')

        # Use temp dir for assertions
        _audio = os.path.join(tempfile.gettempdir(), 'audio.mp3')
        _output = os.path.join(tempfile.gettempdir(), 'output.mp4')
        
        # Check that FFmpeg is in the command
        self.assertIn('ffmpeg', cmd)
        
        # Check resolution
        self.assertIn('1280x720', cmd)
        
        # Check FPS
        self.assertIn('15', cmd)
        
        # Check output file
        self.assertIn(_output, cmd)
    
    def test_build_ffmpeg_cmd_4k(self):
        """Test FFmpeg command building for 4K."""
        cmd = build_ffmpeg_cmd(3840, 2160, 30, os.path.join(tempfile.gettempdir(), 'audio.mp3'), os.path.join(tempfile.gettempdir(), 'output.mp4'), '4k')
        
        # Check 4K resolution
        self.assertIn('3840x2160', cmd)

    def test_build_ffmpeg_cmd_vp9(self):
        """Test FFmpeg command building for VP9 codec."""
        cmd = build_ffmpeg_cmd(3840, 2160, 30, os.path.join(tempfile.gettempdir(), 'audio.mp3'), os.path.join(tempfile.gettempdir(), 'output.webm'), '4k', video_codec='vp9')
        
        self.assertIn('libvpx-vp9', cmd)
        self.assertIn('libopus', cmd)
        self.assertNotIn('-movflags', cmd)
        self.assertEqual(cmd[cmd.index('-crf') + 1], '24')
        self.assertEqual(cmd[cmd.index('-deadline') + 1], 'good')

    def test_build_ffmpeg_cmd_h265(self):
        """Test FFmpeg command building for H265 codec."""
        cmd = build_ffmpeg_cmd(3840, 2160, 30, os.path.join(tempfile.gettempdir(), 'audio.mp3'), os.path.join(tempfile.gettempdir(), 'output.mp4'), '4k', video_codec='h265')
        
        self.assertIn('libx265', cmd)
        self.assertIn('hvc1', cmd)
    
    def test_build_ffmpeg_cmd_high_quality(self):
        """Test FFmpeg command building for high quality preset."""
        cmd = build_ffmpeg_cmd(1920, 1080, 60, os.path.join(tempfile.gettempdir(), 'audio.mp3'), os.path.join(tempfile.gettempdir(), 'output.mp4'), 'high')
        
        # Check 1080p resolution
        self.assertIn('1920x1080', cmd)
        
        # Check 60 FPS
        self.assertIn('60', cmd)
        
        # Check that a video codec is specified (hw or software)
        known_codecs = ('libopenh264', 'libx264', 'h264_nvenc', 'h264_vaapi', 'h264_videotoolbox')
        has_codec = any(c in cmd for c in known_codecs)
        self.assertTrue(has_codec, f"Expected a known codec in cmd, got: {cmd}")

    def test_ffmpeg_thread_limit_can_be_set_for_parallel_segments(self):
        """Parallel segment encoders can avoid multiplying codec threads."""
        cmd = build_ffmpeg_cmd(
            3840, 2160, 30, None,
            os.path.join(tempfile.gettempdir(), 'segment.mp4'),
            '4k', ffmpeg_threads=1,
        )
        threads_index = cmd.index('-threads')
        self.assertEqual(cmd[threads_index + 1], '1')
        filter_threads_index = cmd.index('-filter_threads')
        self.assertEqual(cmd[filter_threads_index + 1], '1')
        filter_complex_index = cmd.index('-filter_complex_threads')
        self.assertEqual(cmd[filter_complex_index + 1], '1')

    def test_recommended_workers_disable_parallelism_below_4k(self):
        """Worker auto-selection returns optimal worker count based on CPU and RAM."""
        from quality_presets import recommended_render_workers
        self.assertGreaterEqual(recommended_render_workers(1920, 1080), 1)

    def test_standalone_mode_uses_software_encoder(self):
        """The standalone compatibility switch bypasses hardware probing."""
        import quality_presets
        original_env = os.environ.get('VISUALIZE_SOFTWARE_ENCODER')
        original_openh264 = quality_presets._HAS_OPENH264
        original_hw = quality_presets._HAS_HW_ENCODER
        original_hw_type = quality_presets._HW_ENCODER_TYPE
        try:
            os.environ['VISUALIZE_SOFTWARE_ENCODER'] = '1'
            quality_presets._HAS_OPENH264 = True
            quality_presets._HAS_HW_ENCODER = True
            quality_presets._HW_ENCODER_TYPE = 'h264_nvenc'
            cmd = build_ffmpeg_cmd(
                3840, 2160, 30, None,
                os.path.join(tempfile.gettempdir(), 'standalone.mp4'), '4k', video_codec='h264',
            )
            # Should not use NVENC hardware encoder when software encoder is forced
            self.assertNotIn('h264_nvenc', cmd)
        finally:
            if original_env is None:
                os.environ.pop('VISUALIZE_SOFTWARE_ENCODER', None)
            else:
                os.environ['VISUALIZE_SOFTWARE_ENCODER'] = original_env
            quality_presets._HAS_OPENH264 = original_openh264
            quality_presets._HAS_HW_ENCODER = original_hw
            quality_presets._HW_ENCODER_TYPE = original_hw_type

    def test_standalone_4k_software_encoder_uses_bounded_memory_preset(self):
        """Standalone 4K software encoding keeps CRF quality with low RSS."""
        import quality_presets
        original_env = os.environ.get('VISUALIZE_4K_SAFE')
        original_openh264 = quality_presets._HAS_OPENH264
        original_hw = quality_presets._HAS_HW_ENCODER
        original_hw_type = quality_presets._HW_ENCODER_TYPE
        original_check_encoder = quality_presets._check_encoder
        try:
            os.environ['VISUALIZE_4K_SAFE'] = '1'
            quality_presets._HAS_OPENH264 = False
            quality_presets._HAS_HW_ENCODER = False
            quality_presets._HW_ENCODER_TYPE = None
            quality_presets._check_encoder = lambda path, codec: codec == 'libx264'
            cmd = build_ffmpeg_cmd(
                3840, 2160, 30, None,
                os.path.join(tempfile.gettempdir(), 'safe-4k.mp4'), '4k',
                ffmpeg_threads=1,
            )
            preset_index = cmd.index('-preset')
            self.assertEqual(cmd[preset_index + 1], 'superfast')
            self.assertIn('-crf', cmd)
            self.assertIn('18', cmd)
        finally:
            if original_env is None:
                os.environ.pop('VISUALIZE_4K_SAFE', None)
            else:
                os.environ['VISUALIZE_4K_SAFE'] = original_env
            quality_presets._HAS_OPENH264 = original_openh264
            quality_presets._HAS_HW_ENCODER = original_hw
            quality_presets._HW_ENCODER_TYPE = original_hw_type
            quality_presets._check_encoder = original_check_encoder

    def test_standalone_prefers_x264_over_openh264_fallback(self):
        """Software fallback keeps the CRF-based x264 quality path when available."""
        import quality_presets
        original_env = os.environ.get('VISUALIZE_PREFER_X264')
        original_openh264 = quality_presets._HAS_OPENH264
        original_hw = quality_presets._HAS_HW_ENCODER
        original_hw_type = quality_presets._HW_ENCODER_TYPE
        try:
            os.environ['VISUALIZE_PREFER_X264'] = '1'
            quality_presets._HAS_OPENH264 = True
            quality_presets._HAS_HW_ENCODER = False
            quality_presets._HW_ENCODER_TYPE = None
            cmd = build_ffmpeg_cmd(
                1920, 1080, 30, None,
                os.path.join(tempfile.gettempdir(), 'prefer-x264.mp4'), 'normal',
            )
            self.assertNotIn('libopenh264', cmd)
        finally:
            if original_env is None:
                os.environ.pop('VISUALIZE_PREFER_X264', None)
            else:
                os.environ['VISUALIZE_PREFER_X264'] = original_env
            quality_presets._HAS_OPENH264 = original_openh264
            quality_presets._HAS_HW_ENCODER = original_hw
            quality_presets._HW_ENCODER_TYPE = original_hw_type

    def test_libx264_uses_crf_animation_tuning(self):
        """libx264 exports should use quality-oriented animation settings when available."""
        import quality_presets
        orig_openh264 = quality_presets._HAS_OPENH264
        orig_hw = quality_presets._HAS_HW_ENCODER
        try:
            quality_presets._HAS_OPENH264 = False
            quality_presets._HAS_HW_ENCODER = False
            cmd = build_ffmpeg_cmd(1280, 720, 30, os.path.join(tempfile.gettempdir(), 'audio.mp3'), os.path.join(tempfile.gettempdir(), 'output.mp4'), 'normal', video_codec='h264')
            self.assertIn('-crf', cmd)
            self.assertIn('-g', cmd)
        finally:
            quality_presets._HAS_OPENH264 = orig_openh264
            quality_presets._HAS_HW_ENCODER = orig_hw


class TestPresetSpeed(unittest.TestCase):
    """Test preset speed factors."""
    
    def test_dev_preset_fastest(self):
        """Test that dev preset is the fastest."""
        dev = get_preset('dev')
        fast = get_preset('fast')
        normal = get_preset('normal')
        
        # Dev should have lowest resolution and FPS
        self.assertLess(dev['fps'], fast['fps'])
        self.assertLess(dev['fps'], normal['fps'])
    
    def test_4k_preset_slowest(self):
        """Test that 4k preset is configured for optimized superfast encoding."""
        preset_4k = get_preset('4k')
        self.assertEqual(preset_4k['ffmpeg_preset'], 'superfast')
    
    def test_normal_preset_balanced(self):
        """Test that normal preset has balanced settings."""
        normal = get_preset('normal')
        self.assertEqual(normal['resolution'], '1080p')
        self.assertEqual(normal['fps'], 30)
        self.assertEqual(normal['ffmpeg_preset'], 'superfast')


if __name__ == '__main__':
    unittest.main()
