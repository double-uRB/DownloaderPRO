# YouTube Downloader PRO

A modern, professional YouTube video and audio downloader built with Python and PySide6. Features a clean, glassmorphic GUI with dark/light themes, detailed quality selection, and robust progress tracking powered by `yt-dlp` and `FFmpeg`.

## ✨ Features

- **Modern PySide6 GUI**: Clean, responsive, glassmorphic design with fluid layouts.
- **SVG Icon System**: All-new professional vector icons (replacing emojis) for a truly crisp, modern look.
- **Multithreaded Turbo Downloads**: Integration with `aria2c` for 10x faster concurrent downloads (up to 16 threads).
- **YouTube Bypass Engine**: Advanced `extractor-args` configuration to bypass "content not available on this app" blocks.
- **Dark/Light Theme Toggle**: Proper contrast support with dynamic stylesheet generation.
- **Detailed Quality Selection**: Shows resolution, codec (H.264, VP9, AV1), bitrate, and HDR/SDR info.
- **Audio-only Downloads**: Extract high-quality MP3s easily.
- **Real-time Progress Tracking**: Shows live download speed, ETA, and file size.
- **Browser Cookie Integration**: Bypasses YouTube's rate-limiting automatically by reading browser cookies.
- **Clipboard Integration**: Quick-paste button for URLs.
- **Persistent Settings**: Remembers your preferred download location and theme.

## 🖼️ Screenshots

<p align="center">
  <img src="assets/Screenshots/Landing%20Page.png" alt="Landing Page" width="45%">
  <img src="assets/Screenshots/Feting%20Info.png" alt="Fetching Video Info" width="45%">
</p>
<p align="center">
  <img src="assets/Screenshots/Downloading%20Video.png" alt="Active Download" width="45%">
  <img src="assets/Screenshots/Downloads.png" alt="Downloads Library" width="45%">
</p>
<p align="center">
  <img src="assets/Screenshots/Settings.png" alt="Settings Page" width="45%">
</p>

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- [FFmpeg](https://ffmpeg.org/download.html) (Required for merging video/audio).
- [aria2c](https://aria2.github.io/) (Recommended for multithreaded performance).
- Place `ffmpeg.exe` and `aria2c.exe` in the `tools/` folder or ensure they are in your system PATH.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/double-uRB/DownloaderPRO.git
   cd DownloaderPRO
   ```

2. **Create a Virtual Environment (Recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application:**
    Ensure you are in the project root directory.
   ```bash
   python src/main.py
   ```

## 📖 Usage

1. Copy a YouTube URL to your clipboard.
2. Open the app and click the **Paste** button, securely fetching the video info.
3. Once the video stats are displayed, select your preferred video quality or check the **Audio (MP3)** box.
4. Choose the download directory via the folder icon.
5. Click **Download** and monitor the progress on the dashboard or in the Downloads tab.

## 🏗️ Architecture & Contributing

- Check out **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** for an in-depth look at how the application works internaly.
- Read **[CONTRIBUTING.md](CONTRIBUTING.md)** if you would like to contribute features or bug fixes to this project.

## ⚖️ Legal Notice
For educational and personal use only. Respect YouTube's Terms of Service and content creators' copyrights. Do not use this tool to pirate protected content.
