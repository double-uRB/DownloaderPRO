import os
import subprocess
import sys
import shutil
import urllib.request
import zipfile
import time
import hashlib
import platform
from pathlib import Path

# Platform detection
SYSTEM = platform.system()
IS_WINDOWS = SYSTEM == "Windows"
IS_MAC = SYSTEM == "Darwin"
IS_LINUX = SYSTEM == "Linux"

# Tool URLs by platform
FFMPEG_URLS = {
    "Windows": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
    "Darwin":  "https://evermeet.cx/ffmpeg/ffmpeg-7.1.zip",
    "Linux":   None  # Recommend system ffmpeg
}

ARIA2_URLS = {
    "Windows": "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip",
    "Darwin":  "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-osx-darwin.dmg",
    "Linux":   None  # Recommend system aria2
}

# SHA-256 Hashes
FFMPEG_HASHES = {
    "Windows": "8748283d821613d930b0e7be685aaa9df4ca6f0ad4d0c42fd02622b3623463c6",
    "Darwin":  None  # Placeholder: Add hash if pinning exact version
}

ARIA2_HASHES = {
    "Windows": "67d015301eef0b612191212d564c5bb0a14b5b9c4796b76454276a4d28d9b288",
    "Darwin":  None  # Placeholder
}


def verify_file(path, expected_hash):
    """Verify file integrity using SHA-256 hash."""
    sha256 = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        actual_hash = sha256.hexdigest()
        if actual_hash != expected_hash:
            print(f"FAILED Hash mismatch for {path}!")
            print(f"   Expected: {expected_hash}")
            print(f"   Actual:   {actual_hash}")
            return False
        return True
    except Exception as e:
        print(f"FAILED Error verifying {path}: {e}")
        return False

def safe_rmtree(path, max_retries=3):
    """Safely remove directory tree with retries"""
    path = Path(path)
    if not path.exists():
        return True
    
    for attempt in range(max_retries):
        try:
            # Try to make all files writable
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        file_path.chmod(0o777)  # Make writable
                    except Exception:
                        pass
            
            # Remove the directory
            shutil.rmtree(path)
            return True
            
        except PermissionError as e:
            print(f"WARNING Attempt {attempt + 1}: Permission denied - {e}")
            if attempt < max_retries - 1:
                print("INFO Waiting 3 seconds and retrying...")
                time.sleep(3)
            else:
                print("FAILED Could not remove directory after multiple attempts")
                return False
        except Exception as e:
            print(f"FAILED Unexpected error: {e}")
            return False
    
    return False

def download_ffmpeg():
    """Download FFmpeg if not present."""
    tools_dir = Path("tools")
    tools_dir.mkdir(exist_ok=True)
    
    binary_name = "ffmpeg.exe" if IS_WINDOWS else "ffmpeg"
    ffmpeg_path = tools_dir / binary_name
    
    if ffmpeg_path.exists():
        print(f"OK FFmpeg already present at {ffmpeg_path}")
        return
        
    if IS_LINUX:
        print("INFO Detected Linux: Please ensure 'ffmpeg' is installed via your package manager (e.g., sudo apt install ffmpeg).")
        return

    url = FFMPEG_URLS.get(SYSTEM)
    expected_hash = FFMPEG_HASHES.get(SYSTEM)
    if not url:
        print(f"FAILED No automated download for {SYSTEM}. Please place {binary_name} in the tools/ folder.")
        return
        
    print(f"INFO Downloading FFmpeg for {SYSTEM}...")
    temp_zip = f"ffmpeg_{SYSTEM.lower()}_temp.zip"
    
    try:
        urllib.request.urlretrieve(url, temp_zip)
        
        if expected_hash and not verify_file(temp_zip, expected_hash):
            if os.path.exists(temp_zip):
                os.remove(temp_zip)
            raise ValueError("FFmpeg download compromised - hash mismatch!")
            
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            for file_info in zip_ref.filelist:
                if file_info.filename.endswith(binary_name):
                    with zip_ref.open(file_info) as source:
                        with open(ffmpeg_path, 'wb') as target:
                            target.write(source.read())
                    break
        
        if not IS_WINDOWS:
            ffmpeg_path.chmod(0o755) # Make executable
            
        os.remove(temp_zip)
        print("OK FFmpeg downloaded successfully")
        
    except Exception as e:
        print(f"FAILED Failed to download FFmpeg: {e}")


def download_aria2c():
    """Download aria2c if not present."""
    tools_dir = Path("tools")
    tools_dir.mkdir(exist_ok=True)
    
    binary_name = "aria2c.exe" if IS_WINDOWS else "aria2c"
    aria2_path = tools_dir / binary_name
    
    if aria2_path.exists():
        print(f"OK aria2c already present at {aria2_path}")
        return
        
    if IS_LINUX:
        print("INFO Detected Linux: Please ensure 'aria2' is installed via your package manager.")
        return

    url = ARIA2_URLS.get(SYSTEM)
    expected_hash = ARIA2_HASHES.get(SYSTEM)
    if not url:
        print(f"FAILED No automated download for {SYSTEM}. Please place {binary_name} in the tools/ folder.")
        return
    
    print(f"INFO Downloading aria2c for {SYSTEM}...")
    temp_file = f"aria2_{SYSTEM.lower()}_temp" + (".zip" if IS_WINDOWS else ".dmg")
    
    try:
        urllib.request.urlretrieve(url, temp_file)
        
        if expected_hash and not verify_file(temp_file, expected_hash):
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise ValueError("aria2c download compromised - hash mismatch!")
            
        if IS_WINDOWS:
            with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                for file_info in zip_ref.filelist:
                    if file_info.filename.endswith(binary_name):
                        with zip_ref.open(file_info) as source:
                            with open(aria2_path, 'wb') as target:
                                target.write(source.read())
                        break
        elif IS_MAC:
            # DMG extraction is complex in pure python.
            # Usually better to tell user to install via Homebrew if auto-download fails.
            print("INFO Automated aria2c extraction from .dmg is not supported in this script.")
            print("   Please install aria2 via Homebrew: brew install aria2")
            print("   And copy the binary (/usr/local/bin/aria2c) to 'tools/'")
            # Don't fail the whole build if we can't auto-dowload on Mac
            return
            
        if not IS_WINDOWS and aria2_path.exists():
            aria2_path.chmod(0o755)
            
        if os.path.exists(temp_file):
            os.remove(temp_file)
        print("OK aria2c setup finished")
        
    except Exception as e:
        print(f"FAILED Failed to download aria2c: {e}")


def build_executable():
    """Build standalone executable with all dependencies"""
    
    print("### Building Standalone YouTube Downloader Pro...")
    
    # Ensure tools are present
    download_ffmpeg()
    download_aria2c()
    
    # Clean previous builds
    print("INFO Cleaning previous builds...")
    for folder in ["dist", "build"]:
        if os.path.exists(folder):
            safe_rmtree(folder)
    
    # PyInstaller command for a TRULY standalone single file
    cmd = [
        "pyinstaller",
        "--noconfirm",         # Don't ask to overwrite
        "--clean",             # Clean cache before build
        "--onefile",
        "--windowed", 
        "--name", "YouTubeDownloaderPro",
        # Bundle both tools into the internal _MEIPASS directory
        "--add-data", f"tools{os.pathsep}tools",
        "--add-data", f"assets{os.pathsep}assets",
        # Explicitly include SVG support
        "--hidden-import", "PySide6.QtCore",
        "--hidden-import", "PySide6.QtWidgets", 
        "--hidden-import", "PySide6.QtGui",
        "--hidden-import", "PySide6.QtSvg",
        "--collect-all", "PySide6",
        "--collect-all", "yt_dlp",
        # Ensure imports from src/ are found
        "--paths", "src",
        "src/main.py"
    ]
    
    # Add icon if available
    icon_path = Path("assets/logo.ico")
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    print(f"INFO Running PyInstaller...")
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "="*50)
        print("+++ BUILD SUCCESSFUL! +++")
        print("="*50)
        
        output_ext = ".exe" if IS_WINDOWS else ""
        output_exe = Path(f'dist/YouTubeDownloaderPro{output_ext}').absolute()
        print(f"INFO STANDALONE BINARY READY: {output_exe}")
        print(f"INFO This file contains EVERYTHING (Python, FFmpeg{' (Linux: system)' if IS_LINUX else ''}, aria2c{' (Linux: system)' if IS_LINUX else ''}, icons).")
        print("OK You can share just this single file with anyone!")
        print("="*50)

        
    except subprocess.CalledProcessError as e:
        print(f"FAILED Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_executable()
