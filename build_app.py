import os
import subprocess
import sys
import shutil
import urllib.request
import zipfile
import time
from pathlib import Path

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
            print(f"⚠️  Attempt {attempt + 1}: Permission denied - {e}")
            if attempt < max_retries - 1:
                print("🔄 Waiting 3 seconds and retrying...")
                time.sleep(3)
            else:
                print("❌ Could not remove directory after multiple attempts")
                return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    return False

def download_ffmpeg():
    """Download FFmpeg if not present"""
    tools_dir = Path("tools")
    tools_dir.mkdir(exist_ok=True)
    
    ffmpeg_path = tools_dir / "ffmpeg.exe"
    
    if ffmpeg_path.exists():
        print("✅ FFmpeg already present")
        return
    
    print("📥 Downloading FFmpeg...")
    
    # Download FFmpeg
    ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    temp_zip = "ffmpeg_temp.zip"
    
    try:
        urllib.request.urlretrieve(ffmpeg_url, temp_zip)
        
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            # Find ffmpeg.exe in the zip
            for file_info in zip_ref.filelist:
                if file_info.filename.endswith('ffmpeg.exe'):
                    # Extract only ffmpeg.exe
                    with zip_ref.open(file_info) as source:
                        with open(ffmpeg_path, 'wb') as target:
                            target.write(source.read())
                    break
        
        os.remove(temp_zip)
        print("✅ FFmpeg downloaded successfully")
        
    except Exception as e:
        print(f"❌ Failed to download FFmpeg: {e}")
        print("Please download FFmpeg manually from https://ffmpeg.org/")

def download_aria2c():
    """Download aria2c if not present"""
    tools_dir = Path("tools")
    tools_dir.mkdir(exist_ok=True)
    
    aria2_path = tools_dir / "aria2c.exe"
    
    if aria2_path.exists():
        print("✅ aria2c already present")
        return
    
    print("📥 Downloading aria2c (Windows)...")
    
    # Download aria2c from GitHub releases
    aria2_url = "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip"
    temp_zip = "aria2_temp.zip"
    
    try:
        urllib.request.urlretrieve(aria2_url, temp_zip)
        
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            # Find aria2c.exe in the zip
            for file_info in zip_ref.filelist:
                if file_info.filename.endswith('aria2c.exe'):
                    # Extract only aria2c.exe
                    with zip_ref.open(file_info) as source:
                        with open(aria2_path, 'wb') as target:
                            target.write(source.read())
                    break
        
        os.remove(temp_zip)
        print("✅ aria2c downloaded successfully")
        
    except Exception as e:
        print(f"❌ Failed to download aria2c: {e}")
        print("Please download aria2c manually and place it in the tools/ folder.")

def build_executable():
    """Build standalone executable with all dependencies"""
    
    print("🔨 Building Standalone YouTube Downloader Pro...")
    
    # Ensure tools are present
    download_ffmpeg()
    download_aria2c()
    
    # Clean previous builds
    print("🧹 Cleaning previous builds...")
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
    
    print(f"🚀 Running PyInstaller...")
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "="*50)
        print("✨ BUILD SUCCESSFUL! ✨")
        print("="*50)
        
        output_exe = Path('dist/YouTubeDownloaderPro.exe').absolute()
        print(f"\n📦 STANDALONE EXE READY: {output_exe}")
        print("\n💡 This file contains EVERYTHING (Python, FFmpeg, aria2c, icons).")
        print("✅ You can share just this single file with anyone!")
        print("="*50)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_executable()
