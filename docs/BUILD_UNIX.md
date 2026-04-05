# Multiplatform Build Guide (macOS & Linux)

This guide explains how to generate native binaries and installers for macOS and Linux from the source code.

## 🛠️ Prerequisites

Before you begin, ensure you have **Python 3.10+** and the core dependencies installed:
```bash
pip install -r requirements.txt
pip install pyinstaller
```

---

## 🍎 Building for macOS (.app / .dmg)

### 1. Generate the .app Bundle
Run the build script on your Mac. It will automatically detect the OS and apply the correct flags:
```bash
python build_app.py
```
After completion, a standalone **`YouTubeDownloaderPro.app`** will be available in the `dist/` directory.

### 2. Packaging as a .DMG (Disk Image)
To create a professional disk image with "Drag to Applications" support, use a tool like `create-dmg`:
```bash
brew install create-dmg
create-dmg \
  --volname "Downloader PRO Installer" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "DownloaderPRO.app" 200 190 \
  --hide-extension "DownloaderPRO.app" \
  --app-drop-link 600 185 \
  "dist/DownloaderPRO_v3.0.0.dmg" \
  "dist/"
```

---

## 🐧 Building for Linux (AppImage / Portable)

### 1. Build the Binary
Run the build script on your Linux machine (Ubuntu, Fedora, Arch, etc.):
```bash
python build_app.py
```
This produces a single portable binary in `dist/YouTubeDownloaderPro`.

### 2. Packaging as an AppImage
To create a single-file AppImage, we recommend using `go-appimage`:
1.  Download `appimagetool` from the [AppImage GitHub](https://github.com/probonopd/go-appimage/releases).
2.  Follow the standard AppDir structure:
    ```
    AppDir/
    ├── AppRun (Link to binary)
    ├── DownloaderPRO.desktop
    ├── DownloaderPRO.png
    └── usr/
        └── bin/ (Your build artifacts)
    ```
3.  Run the tool:
    ```bash
    ./appimagetool-x86_64.AppImage AppDir/ DownloaderPRO.AppImage
    ```

---

## 🔩 Internal Tool Management
Once installed on macOS or Linux, the app will run **`download_tools.py`** on first launch to:
- Detect the system GPU.
- Fetch hardware-accelerated **FFmpeg** and **Aria2**.
- Setup a **LaunchAgent** (Mac) or **Crontab** (Linux) for automatic `yt-dlp` engine updates.

## ⚠️ Known Issues
- **macOS Gatekeeper**: Unsigned `.app` bundles will show a warning ("Developer cannot be verified"). To bypass, Right-click -> Open, or run `xattr -cr /path/to/DownloaderPRO.app` in the terminal.
- **Linux Wayland**: If the browser UI flickers, run with `QT_QPA_PLATFORM=xcb python src/main.py`.
