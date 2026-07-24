#!/usr/bin/env python3
"""Create a Type 2 AppImage from a runtime ELF + squashfs filesystem.

Usage: create_appimage.py <runtime> <appdir> <output>
"""
import struct
import sys
import os
import subprocess
import tempfile


def create_appimage(runtime_path: str, appdir_path: str, output_path: str):
    with tempfile.NamedTemporaryFile(suffix='.squashfs', delete=False) as tmp:
        squashfs_path = tmp.name

    try:
        cmd = [
            'mksquashfs', appdir_path, squashfs_path,
            '-comp', 'gzip', '-noappend', '-all-root'
        ]
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, capture_output=True, text=True)

        runtime_size = os.path.getsize(runtime_path)
        squashfs_size = os.path.getsize(squashfs_path)
        print(f"Runtime size: {runtime_size}")
        print(f"Squashfs size: {squashfs_size} bytes")
        print(f"Payload offset (runtime size): {runtime_size} (0x{runtime_size:x})")

        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError as e:
                if getattr(e, 'errno', None) == 26 or "busy" in str(e).lower():
                    raise RuntimeError(
                        f"Cannot overwrite '{output_path}': The file is currently being executed. "
                        f"Please close any running instances of the AppImage and retry."
                    ) from e
                # Attempt to overwrite anyway if unlink fails for another reason

        with open(output_path, 'wb') as f:
            with open(runtime_path, 'rb') as rt:
                f.write(rt.read())
            with open(squashfs_path, 'rb') as sq:
                f.write(sq.read())

        os.chmod(output_path, 0o755)

        final_size = os.path.getsize(output_path)
        print(f"AppImage created: {output_path} ({final_size} bytes)")

    finally:
        os.unlink(squashfs_path)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <runtime> <appdir> <output>", file=sys.stderr)
        sys.exit(1)

    create_appimage(sys.argv[1], sys.argv[2], sys.argv[3])
