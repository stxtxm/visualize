"""
Video recorder module for exporting psychedelic visualizations to MP4.
"""

import subprocess
import numpy as np
import sys
import os


class VideoRecorder:
    """
    Exports audio visualization as MP4 video using FFmpeg.
    """

    def __init__(self, audio_file, output_file, width=1920, height=1080,
                 fps=60, effect_type='random', color_palette='psychedelic'):
        """
        Initialize the video recorder.
        
        Args:
            audio_file: Path to input audio file
            output_file: Path to output video file
            width: Video width in pixels
            height: Video height in pixels
            fps: Frames per second
            effect_type: Type of visual effect to use
            color_palette: Color palette to use
        """
        self.audio_file = audio_file
        self.output_file = output_file
        self.width = width
        self.height = height
        self.fps = fps
        self.effect_type = effect_type
        self.color_palette = color_palette
        self._ffmpeg_cmd = self._build_ffmpeg_command()
        self._process = None

    def _build_ffmpeg_command(self):
        """Build the FFmpeg command for encoding."""
        resolution = f"{self.width}x{self.height}"
        
        # Video bitrate based on resolution
        bitrate = "20M"  # 20 Mbps for 1080p
        if self.width >= 2560:  # 1440p+
            bitrate = "35M"
        elif self.width >= 3840:  # 4K
            bitrate = "50M"
        
        # FFmpeg command
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite without asking
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', resolution,
            '-pix_fmt', 'bgr24',
            '-r', str(self.fps),
            '-i', 'pipe:0',  # Video input from stdin
            '-i', self.audio_file,  # Audio input
            '-c:v', 'mpeg4',
            '-qscale:v', '2',
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',  # Stop when audio ends
            '-threads', '0',  # Use all available threads
            self.output_file
        ]
        
        return cmd

    def _get_audio_duration(self, audio_file):
        """Get duration of audio file in seconds."""
        try:
            # Use ffprobe to get duration
            import subprocess
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                audio_file
            ]
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                return duration
        except Exception:
            pass
        
        # Fallback: estimate from file size
        # Assume MP3 at 128 kbps
        file_size = os.path.getsize(audio_file)
        bitrate = 128000  # 128 kbps
        duration = (file_size * 8) / bitrate
        return duration

    def record(self, effect_generator):
        """
        Record the visualization to a video file.
        
        Args:
            effect_generator: A callable or iterator that yields frames
                           as numpy arrays (height, width, 3) in BGR format
        """
        # Validate audio file
        if not os.path.exists(self.audio_file):
            raise FileNotFoundError(f"Audio file not found: {self.audio_file}")
        
        # Get audio duration
        audio_duration = self._get_audio_duration(self.audio_file)
        total_frames = int(audio_duration * self.fps)
        
        print(f"Exporting {self.audio_file} to {self.output_file}")
        print(f"  Resolution: {self.width}x{self.height}")
        print(f"  FPS: {self.fps}")
        print(f"  Duration: {audio_duration:.1f}s")
        print(f"  Total frames: {total_frames}")
        print(f"  Effect: {self.effect_type}")
        print(f"  Colors: {self.color_palette}")
        print()
        
        # Start FFmpeg process
        self._process = subprocess.Popen(
            self._ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        try:
            # Write frames to FFmpeg
            frame_count = 0
            
            for frame in effect_generator:
                # Ensure frame is in correct format (height, width, 3)
                if isinstance(frame, np.ndarray):
                    if frame.dtype != np.uint8:
                        frame = frame.astype(np.uint8)
                    
                    # Ensure BGR format (OpenCV default)
                    # If RGB, convert to BGR
                    if frame.shape[2] == 3:
                        pass  # Already correct shape
                
                # Write frame to FFmpeg
                try:
                    self._process.stdin.write(frame.tobytes())
                except (BrokenPipeError, ConnectionResetError, ValueError) as e:
                    # Pipe fermé ou FFmpeg a crashé
                    print(f"Warning: Pipe error at frame {frame_count}: {e}")
                    break
                
                frame_count += 1
                
                # Show progress
                if frame_count % 100 == 0:
                    progress = (frame_count / total_frames) * 100
                    print(f"Export: {progress:.1f}% ({frame_count}/{total_frames} frames)")
                
                # Check if we've reached the end
                if total_frames > 0 and frame_count >= total_frames:
                    break
                
                # Check if FFmpeg is still alive periodically
                if frame_count % 200 == 0 and self._process.poll() is not None:
                    print(f"Warning: FFmpeg exited at frame {frame_count}")
                    break
            
            # Close stdin to signal FFmpeg that we're done
            try:
                self._process.stdin.close()
            except:
                pass
            
            # Wait for FFmpeg to finish
            try:
                stdout, stderr = self._process.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                self._process.kill()
                stdout, stderr = self._process.communicate()
                raise RuntimeError("FFmpeg timeout - export took too long")
            
            if self._process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else 'Unknown error'
                raise RuntimeError(f"FFmpeg error (code {self._process.returncode}):\n{error_msg}")
            
            print(f"\nVideo exported successfully: {self.output_file}")
            
        finally:
            if self._process and self._process.poll() is None:
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except:
                    self._process.kill()
            self._process = None

    def cleanup(self):
        """Clean up resources."""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except:
                self._process.kill()
        self._process = None
