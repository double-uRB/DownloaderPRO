import os
import sys
import shutil
import argparse
import hashlib
import platform
import subprocess
import time
import urllib.request
import zipfile
import json
from pathlib import Path

# ==============================================================================
# CONFIGURATION & SECURITY
# ==============================================================================
VERSION = "3.0.0"
SYSTEM = platform.system()
IS_WINDOWS = SYSTEM == "Windows"
IS_MAC = SYSTEM == "Darwin"
IS_LINUX = SYSTEM == "Linux"

# SHA-256 Hashes - Manual Update Required Per Release
# Update these using: python -c "import hashlib; print(hashlib.sha256(open('file','rb').read()).hexdigest())"
CHECKSUMS = {
    "win_ffmpeg": "8748283d821613d930b0e7be685aaa9df4ca6f0ad4d0c42fd02622b3623463c6",
    "win_aria2c": "67d015301eef0b612191212d564c5bb0a14b5b9c4796b76454276a4d28d9b288",
    "mac_ffmpeg": "PLACEHOLDER_MAC_FFMPEG", # Update before first Mac release
    "linux_static_ffmpeg": "PLACEHOLDER_LINUX_FFMPEG" # John Van Sickle static
}

URLS = {
    "win_ffmpeg": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
    "win_aria2c": "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip",
    "mac_ffmpeg": "https://evermeet.cx/ffmpeg/ffmpeg-7.1.zip",
    "linux_ffmpeg": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
}

# ==============================================================================
# 🧰 UTILITY FUNCTIONS
# ==============================================================================

def verify_integrity(file_path, expected_hash):
    """Verify SHA-256 hash of a file."""
    if not expected_hash or expected_hash.startswith("PLACEHOLDER"):
        print(f"⚠️ WARNING: Skipping integrity check for {file_path} (No hash provided).")
        return True
    
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    
    actual = sha256.hexdigest()
    if actual != expected_hash:
        print(f"ERROR: Integrity mismatch for {file_path}!")
        print(f"   Expected: {expected_hash}")
        print(f"   Actual:   {actual}")
        return False
    return True

def download_with_progress(url, dest, label="Download"):
    """Download a file with a simple percentage progress bar."""
    print(f"INFO: {label}: {url}")
    try:
        def report(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, int(block_num * block_size * 100 / total_size))
                sys.stdout.write(f"\r   [{'#' * (percent // 2)}{' ' * (50 - percent // 2)}] {percent}%")
                sys.stdout.flush()

        urllib.request.urlretrieve(url, dest, reporthook=report)
        print("\n   OK: Done.")
        return True
    except Exception as e:
        print(f"\n   ERROR: Failed: {e}")
        return False

def safe_rmtree(path):
    """Recursively delete folder with permission handling."""
    if not os.path.exists(path):
        return
    for _ in range(3):
        try:
            shutil.rmtree(path, ignore_errors=False)
            return
        except (PermissionError, OSError):
            time.sleep(1)
    shutil.rmtree(path, ignore_errors=True)

# ==============================================================================
# 📦 BINARY ACQUISITION
# ==============================================================================

def fetch_ffmpeg():
    """Acquire FFmpeg for the target platform."""
    tools_dir = Path("tools")
    tools_dir.mkdir(exist_ok=True)
    binary_name = "ffmpeg.exe" if IS_WINDOWS else "ffmpeg"
    target = tools_dir / binary_name
    
    if target.exists():
        print(f"OK: FFmpeg already present in tools/ folder.")
        return True

    # Cross-Platform Strategy
    if IS_WINDOWS:
        temp_zip = "temp_ffmpeg.zip"
        if download_with_progress(URLS["win_ffmpeg"], temp_zip, "FFmpeg (Win)"):
            if verify_integrity(temp_zip, CHECKSUMS["win_ffmpeg"]):
                with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                    for f in zip_ref.namelist():
                        if f.endswith("ffmpeg.exe"):
                            with zip_ref.open(f) as src, open(target, 'wb') as dst:
                                shutil.copyfileobj(src, dst)
                                break
                os.remove(temp_zip)
                return True
    
    elif IS_MAC:
        # Check system/brew first
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            print(f"OK: Found system FFmpeg: {system_ffmpeg}")
            shutil.copy2(system_ffmpeg, target)
            return True
        print("TIP: Install via Homebrew: 'brew install ffmpeg'")
        
    elif IS_LINUX:
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            print(f"OK: Found system FFmpeg: {system_ffmpeg}")
            shutil.copy2(system_ffmpeg, target)
            return True
        print("TIP: Install via apt: 'sudo apt install ffmpeg'")
    
    return target.exists()

def fetch_aria2c():
    """Acquire aria2c for the target platform."""
    tools_dir = Path("tools")
    tools_dir.mkdir(exist_ok=True)
    binary_name = "aria2c.exe" if IS_WINDOWS else "aria2c"
    target = tools_dir / binary_name
    
    if target.exists():
        return True

    if IS_WINDOWS:
        temp_zip = "temp_aria2.zip"
        if download_with_progress(URLS["win_aria2c"], temp_zip, "aria2c (Win)"):
            if verify_integrity(temp_zip, CHECKSUMS["win_aria2c"]):
                with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                    for f in zip_ref.namelist():
                        if f.endswith("aria2c.exe"):
                            with zip_ref.open(f) as src, open(target, 'wb') as dst:
                                shutil.copyfileobj(src, dst)
                                break
                os.remove(temp_zip)
                return True
    else:
        # Unix-like: usually system PATH
        system_aria2 = shutil.which("aria2c")
        if system_aria2:
            print(f"OK: Found system aria2c: {system_aria2}")
            shutil.copy2(system_aria2, target)
            return True
        print(f"TIP: Install {('Homebrew' if IS_MAC else 'aria2c package')}.")

    return target.exists()

# ==============================================================================
# 🚀 PYINSTALLER ORCHESTRATION
# ==============================================================================

def run_build(onefile=False, skip_tools=False):
    """Run PyInstaller build."""
    print(f"INFO: Initializing Build for {SYSTEM} (v{VERSION})...")
    
    if not skip_tools:
        if not (fetch_ffmpeg() and fetch_aria2c()):
            print("ERROR: Critical binary dependencies missing. Aborting.")
            sys.exit(1)

    # Icons
    icon_ext = "ico" if IS_WINDOWS else "icns" if IS_MAC else "png"
    icon_path = Path("assets") / f"logo.{icon_ext}"
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--onedir" if not onefile else "--onefile",
        "--windowed",
        "--name", "YouTubeDownloaderPro",
        # Resource bundling
        "--add-data", f"tools{os.pathsep}tools",
        "--add-data", f"assets{os.pathsep}assets",
        # Python core
        "--paths", "src",
        # Frameworks
        "--collect-all", "PySide6",
        "--collect-all", "yt_dlp",
        "src/main.py"
    ]
    
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    if IS_MAC:
        cmd.extend(["--osx-bundle-identifier", "com.doublerub.downloaderpro"])

    print(f"INFO: Running PyInstaller: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

# ==============================================================================
# 📦 PACKAGING & POST-PROCESS
# ==============================================================================

def create_appimage():
    """Create Linux AppImage."""
    if not IS_LINUX: return
    print("INFO: Constructing AppDir for AppImage creation...")
    appdir = Path("dist/AppDir")
    appdir.mkdir(exist_ok=True)
    
    # Simple AppDir layout (mock - requiring appimagetool in PATH)
    if shutil.which("appimagetool"):
        print("   OK: appimagetool found. packaging...")
        # (Real implementation would use linuxdeploy or manual AppDir layout)
    else:
        print("   WARNING: appimagetool not found in PATH. Skipping AppImage creation.")

def print_notarization_help():
    """Print macOS notarization guide."""
    if not IS_MAC: return
    print("\n" + "="*80)
    print("INFO: MACOS NOTARIZATION FLOW")
    print("="*80)
    print("1. Archive: zip -r dist/DownloaderPRO.zip dist/YouTubeDownloaderPro.app")
    print("2. Submit:  xcrun notarytool submit dist/DownloaderPRO.zip --apple-id <EMAIL>")
    print("3. Staple:  xcrun stapler staple dist/YouTubeDownloaderPro.app")
    print("="*80 + "\n")

# ==============================================================================
# 🏁 MAIN
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="DownloaderPRO Advanced Build System")
    parser.add_argument("--skip-tools", action="store_true", help="Skip binary dependency checks")
    parser.add_argument("--onefile", action="store_true", help="Windows: standalone .exe")
    parser.add_argument("--no-appimage", action="store_true", help="Linux: skip AppImage creation")
    parser.add_argument("--package", action="store_true", help="Build native installers (.dmg, .deb, .AppImage, .exe)")
    parser.add_argument("--clean-only", action="store_true", help="Wipe build folders and exit")
    
    args = parser.parse_args()
    
    if args.clean_only:
        print("INFO: Cleaning environment...")
        for f in ["build", "dist"]: safe_rmtree(f)
        sys.exit(0)

    # Phase 1: Build
    run_build(onefile=args.onefile, skip_tools=args.skip_tools)
    
    # Phase 2: Post-Processing & Packaging
    if args.package:
        print("\n📦 Starting Installer Packaging...")
        if IS_WINDOWS:
            # Look for Inno Setup Compiler
            iscc = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
            if os.path.exists(iscc):
                print("INFO: Running Inno Setup Compiler...")
                subprocess.run([iscc, "setup.iss"], check=False)
            else:
                print("WARNING: Inno Setup (ISCC.exe) not found. Please install it to build the .exe installer.")
        
        elif IS_MAC:
            print("INFO: Building macOS DMG...")
            subprocess.run(["bash", "scripts/create_dmg.sh"], check=False)
            print_notarization_help()
            
        elif IS_LINUX:
            print("INFO: Building Linux packages...")
            if not args.no_appimage:
                subprocess.run(["bash", "scripts/create_appimage.sh"], check=False)
            subprocess.run(["bash", "scripts/create_deb.sh"], check=False)
    else:
        # Standard hints if not packaging
        if IS_WINDOWS and not args.onefile:
            print("\nOK: Build ready for Inno Setup. Use 'setup.iss' to create the installer.")
        
        if IS_MAC:
            print_notarization_help()

    print("\nINFO: Build process complete.")

if __name__ == "__main__":
    main()
