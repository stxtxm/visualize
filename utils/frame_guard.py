"""Ownership guards for frames queued to asynchronous FFmpeg writer threads.

Export pipelines render frames in the producer thread while a daemon writer
thread pushes queued byte views into FFmpeg's stdin pipe.  If an effect hands
back a cached internal buffer from ``render_to_array()``, the next render call
overwrites bytes the writer thread has not sent yet: encoded frames become
torn and can flash black on fast luminance transitions (for example the BPM
strobe of Trance Scope).

Effects must therefore own fresh memory for every rendered frame (see the
ownership rule in AGENTS.md).  ``FrameOwnershipGuard`` is a defence-in-depth
net used by the export loops: it remembers the memory addresses of the most
recent frames and forces an owned copy whenever an address re-enters the
window before its previous owner was consumed.
"""

from collections import deque


class FrameOwnershipGuard:
    """Ensure frames queued for async writing do not alias recent frames."""

    def __init__(self, window=8):
        self._window = deque(maxlen=max(1, int(window)))
        self.copies = 0

    def ensure_owned(self, frame):
        """Return *frame*, copied when it aliases a recently tracked buffer."""
        try:
            import numpy as np
        except ImportError:
            return frame
        if not isinstance(frame, np.ndarray):
            return frame
        flags = getattr(frame, 'flags', None)
        if flags is not None and not flags.writeable:
            return frame
        addr = frame.__array_interface__['data'][0]
        if addr in self._window:
            # Recycled buffer: give the writer thread its own bytes so the
            # next render cannot mutate what FFmpeg is still consuming.
            frame = frame.copy()
            self.copies += 1
            addr = frame.__array_interface__['data'][0]
        self._window.append(addr)
        return frame