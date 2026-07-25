#!/usr/bin/env python3
"""Download static ffmpeg binaries for Windows bundling."""
import os
import sys
import urllib.request
import zipfile
import shutil
import platform

FFMPEG_URLS = {
    "64": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
}

def download_ffmpeg(target_dir: str) -> str:
    os.makedirs(target_dir, exist_ok=True)
    arch = platform.machine()
    key = "64" if "64" in arch else "32"
    url = FFMPEG_URLS.get(key)
    if not url:
        print(f"Unsupported architecture: {arch}")
        sys.exit(1)

    zip_path = os.path.join(target_dir, "ffmpeg.zip")
    extract_dir = os.path.join(target_dir, "ffmpeg_extracted")

    if os.path.exists(os.path.join(target_dir, "ffmpeg.exe")):
        print("ffmpeg already downloaded, skipping")
        return target_dir

    print(f"Downloading ffmpeg from {url}...")
    urllib.request.urlretrieve(url, zip_path)

    print("Extracting...")
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_dir)

    # Find the bin directory
    for root, dirs, files in os.walk(extract_dir):
        if "ffmpeg.exe" in files:
            bin_dir = root
            break
    else:
        print("Could not find ffmpeg.exe in extracted archive")
        sys.exit(1)

    for exe in ("ffmpeg.exe", "ffprobe.exe", "ffplay.exe"):
        src = os.path.join(bin_dir, exe)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(target_dir, exe))
            print(f"  Copied {exe}")

    # Cleanup
    os.remove(zip_path)
    shutil.rmtree(extract_dir)
    print(f"ffmpeg binaries ready in {target_dir}")
    return target_dir


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "ffmpeg_bin"
    download_ffmpeg(out)
