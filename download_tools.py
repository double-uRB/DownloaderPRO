import os
import sys
import argparse
import hashlib
import subprocess
import urllib.request
import zipfile
import shutil
import platform
from pathlib import Path

# Platform detection
SYSTEM = platform.system()
IS_WINDOWS = SYSTEM == "Windows"
IS_MAC = SYSTEM == "Darwin"
IS_LINUX = SYSTEM == "Linux"

# ==============================================================================
# KNOWN CHECKSUMS (SHA-256)
# UPDATE BEFORE RELEASE
# ==============================================================================
CHECKSUMS = {
    "ffmpeg_win_gen": "8748283d821613d930b0e7be685aaa9df4ca6f0ad4d0c42fd02622b3623463c6",
    "ffmpeg_mac":     "PLACEHOLDER_MAC_FFMPEG_HASH",
    "aria2c_win":     "67d015301eef0b612191212d564c5bb0a14b5b9c4796b76454276a4d28d9b288",
    "ytdlp_win":      "PLACEHOLDER_YTDLP_WIN_HASH"
}

URLS = {
    "ffmpeg_win_gen": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
    "ffmpeg_win_hw":  "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.zip",
    "ffmpeg_mac":     "https://evermeet.cx/ffmpeg/ffmpeg-7.1.zip",
    "aria2c_win":     "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip",
    "aria2c_mac":     "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-osx-darwin.dmg",
    "ytdlp_win":      "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe",
    "ytdlp_unix":     "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
}

def detect_gpu():
    """Detect GPU vendor (NVIDIA/AMD/INTEL/GENERIC) across platforms."""
    try:
        if IS_WINDOWS:
            result = subprocess.run(["wmic", "path", "win32_VideoController", "get", "name"], capture_output=True, text=True)
            output = result.stdout.upper()
        elif IS_MAC:
            result = subprocess.run(["system_profiler", "SPDisplaysDataType"], capture_output=True, text=True)
            output = result.stdout.upper()
        elif IS_LINUX:
            # Check lspci if available, otherwise check sysfs
            try:
                result = subprocess.run(["lspci"], capture_output=True, text=True)
                output = result.stdout.upper()
            except FileNotFoundError:
                output = ""
                for path in Path("/sys/class/drm").glob("card*/device/vendor"):
                    output += path.read_text().upper()
        
        if "NVIDIA" in output: return "NVIDIA"
        if "AMD" in output or "ATI" in output: return "AMD"
        if "INTEL" in output: return "INTEL"
        if "APPLE" in output: return "APPLE" # Apple Silicon
    except Exception:
        pass
    return "GENERIC"

def verify_sha256(file_path, expected_hash):
    """Verify SHA-256 checksum of a file."""
    if not expected_hash or expected_hash.startswith("PLACEHOLDER"):
        return True
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    actual = sha256_hash.hexdigest()
    if actual != expected_hash:
        print(f"ERROR:checksum:mismatch {os.path.basename(file_path)}")
        return False
    return True

def download_with_progress(url, dest_path, tool_id):
    """Download tool with progress updates."""
    try:
        def report(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, int(block_num * block_size * 100 / total_size))
                print(f"PROGRESS:{tool_id}:{percent}", flush=True)
        urllib.request.urlretrieve(url, dest_path, reporthook=report)
        print(f"DONE:{tool_id}", flush=True)
        return True
    except Exception as e:
        print(f"ERROR:{tool_id}:{str(e)}", flush=True)
        return False

def extract_zip_tool(zip_path, extract_to, binary_names):
    """Extract specific binaries from a zip."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.filelist:
                for bin_name in binary_names:
                    if file_info.filename.endswith(bin_name):
                        filename = os.path.basename(file_info.filename)
                        dest = os.path.join(extract_to, filename)
                        with zip_ref.open(file_info) as source, open(dest, "wb") as target:
                            shutil.copyfileobj(source, target)
                        if not IS_WINDOWS:
                            os.chmod(dest, 0o755)
        return True
    except Exception:
        return False

def setup_persistence(app_path):
    """Setup weekly yt-dlp auto-update task."""
    try:
        ytdlp_path = os.path.join(app_path, "tools", "yt-dlp.exe" if IS_WINDOWS else "yt-dlp")
        if IS_WINDOWS:
            subprocess.run(["schtasks", "/Create", "/SC", "WEEKLY", "/TN", "DownloaderPRO_Update", "/TR", f'"{ytdlp_path}" -U', "/F"], check=True)
        elif IS_MAC:
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.doublerub.downloaderpro.update</string>
    <key>ProgramArguments</key>
    <array>
        <string>{ytdlp_path}</string>
        <string>-U</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key><integer>3</integer>
        <key>Minute</key><integer>0</integer>
        <key>Weekday</key><integer>0</integer>
    </dict>
</dict>
</plist>"""
            plist_path = Path.home() / "Library" / "LaunchAgents" / "com.doublerub.downloaderpro.update.plist"
            plist_path.write_text(plist_content)
            subprocess.run(["launchctl", "load", str(plist_path)], check=False)
        elif IS_LINUX:
            cron_cmd = f"0 3 * * 0 {ytdlp_path} -U\n"
            # Append to crontab if not already there
            current = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
            if ytdlp_path not in current:
                with subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE) as proc:
                    proc.communicate(input=(current + cron_cmd).encode())
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--detect-gpu", action="store_true")
    parser.add_argument("--download-tools", action="store_true")
    parser.add_argument("--install-dir", type=str)
    parser.add_argument("--setup-persistence", action="store_true")
    
    args = parser.parse_args()
    
    if args.detect_gpu:
        print(detect_gpu())
        return

    if args.download_tools and args.install_dir:
        install_dir = Path(args.install_dir)
        install_dir.mkdir(parents=True, exist_ok=True)
        
        gpu = detect_gpu()
        
        # Tools configuration
        tools = [
            {
                "id": "ffmpeg",
                "url": URLS["ffmpeg_win_hw" if gpu in ["NVIDIA", "AMD", "INTEL"] else "ffmpeg_win_gen"] if IS_WINDOWS else URLS["ffmpeg_mac"] if IS_MAC else None,
                "ext": ".zip",
                "bins": ["ffmpeg.exe", "ffprobe.exe"] if IS_WINDOWS else ["ffmpeg", "ffprobe"]
            },
            {
                "id": "aria2c",
                "url": URLS["aria2c_win"] if IS_WINDOWS else URLS["aria2c_mac"] if IS_MAC else None,
                "ext": ".zip" if IS_WINDOWS else ".dmg", # Note: DMG needs special handling outside this script usually
                "bins": ["aria2c.exe"] if IS_WINDOWS else ["aria2c"]
            },
            {
                "id": "ytdlp",
                "url": URLS["ytdlp_win"] if IS_WINDOWS else URLS["ytdlp_unix"],
                "ext": ".exe" if IS_WINDOWS else "",
                "bins": ["yt-dlp.exe"] if IS_WINDOWS else ["yt-dlp"]
            }
        ]
        
        for tool in tools:
            if not tool["url"]: continue
            temp_path = install_dir / f"temp_{tool['id']}{tool['ext']}"
            if download_with_progress(tool["url"], str(temp_path), tool["id"]):
                if tool["ext"] == ".zip":
                    extract_zip_tool(str(temp_path), str(install_dir), tool["bins"])
                    temp_path.unlink()
                else:
                    target = install_dir / tool["bins"][0]
                    if target.exists(): target.unlink()
                    temp_path.rename(target)
                    if not IS_WINDOWS: os.chmod(target, 0o755)
                    
    if args.setup_persistence and args.install_dir:
        setup_persistence(os.path.dirname(args.install_dir))

if __name__ == "__main__":
    main()
