# Installation Guide

YouTube Downloader PRO can be installed in two ways: as a standalone portable app for users, or from source for developers.

---

## 📦 Option 1: Standalone (For Users)

This is the recommended method for most users as it requires **zero dependencies**.

1.  **Download**: Get the latest `YouTubeDownloaderPro.exe` from the [GitHub Releases](https://github.com/double-uRB/DownloaderPRO/releases).
2.  **Run**: Just double-click the EXE to start.
3.  **Platform Support**: The standalone EXE is currently only for Windows users. macOS and Linux users should follow the **Running from Source** guide below.
4.  **Antivirus Notice**: Since this is an unsigned tool on Windows, SmartScreen may show a warning. Click "More Info" -> "Run Anyway" to skip it.

---

## 🛠️ Option 2: Running from Source (For Developers)

If you want to modify the code or contribute, follow these steps:

### 1. Prerequisites
- **Python 3.10+**: Make sure you have Python installed and added to your PATH.
- **Tools (Optional)**: For merging streams and high-quality audio extraction, **FFmpeg** and **ffprobe** are required. The application handles this automatically: it will attempt to download the latest FFmpeg essentials bundle and extract `ffmpeg.exe`, `ffprobe.exe`, and `aria2c.exe` into the `tools/` folder when first run.

### 2. Environment Setup
1.  **Clone the Repo**:
    ```bash
    git clone https://github.com/double-uRB/DownloaderPRO.git
    cd DownloaderPRO
    ```
2.  **Create a Virtual Environment**:
    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # Linux/Mac:
    source venv/bin/activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### 3. Launching
Run the application using the entry point script:
```bash
python src/main.py
```

---

## 🔨 Building Your Own EXE

We use `PyInstaller` to create a single-file portable distribution. To build your own version:

1.  Ensure all development dependencies are installed (including `pyinstaller`).
2.  Run the automated build script:
    ```bash
    python build_app.py
    ```
3.  The final standalone EXE will be available in the `dist/` folder named `YouTubeDownloaderPro.exe`.

---

## ❓ Troubleshooting

### Missing Icons
If icons are not showing in your local development environment, ensure the `assets/` folder is intact and you're running the script from the project root.

### Taskbar Icon Not Showing
When running from source, the taskbar icon may sometimes default to the Python logo. This is fixed automatically in the standalone build using Windows `AppUserModelID` registration.

### 4K/8K Options Grayed Out
YouTube restricts high-resolution streams for bots. Use the **Login with YouTube** (OAuth2) feature in the Settings tab to authenticate securely and unlock all premium qualities.

### Audio Streams Missing
If no audio streams are found in the Advanced Download panel:
1. Ensure `ffprobe.exe` exists in the `tools/` folder.
2. The application uses a fallback detection if `ffprobe` is missing, but for full codec metadata (MP3, AAC, etc.), `ffprobe` is required.
3. Check the logs in `logs/app.log` for any "format probing" errors from `yt-dlp`.
