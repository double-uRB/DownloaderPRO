# Downloader PRO

A modern, professional YouTube video and audio downloader built with Python and PySide6. Evolved into an **All-in-One Media Suite**, it features a fully embedded Chromium browser for discovery, high-fidelity downloading (up to 8K), and a native offline media player. Features a clean, glassmorphic GUI with dark/light themes and robust multithreaded downloading. **Fully compatible with Windows, macOS, and Linux.**

[![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white)](#) [![PySide6](https://img.shields.io/badge/-PySide6-41CD52?style=flat-square&logo=qt&logoColor=white)](#) [![FFmpeg](https://img.shields.io/badge/-FFmpeg-007808?style=flat-square)](#) [![aria2](https://img.shields.io/badge/-aria2-333333?style=flat-square)](#) [![yt--dlp](https://img.shields.io/badge/-yt--dlp-FF0000?style=flat-square&logo=youtube&logoColor=white)](#)

---

## ✨ Why Downloader PRO?

Unlike most downloaders, Downloader PRO provides a **Zero-Dependency** experience. Our standalone executable bundles everything needed (Python, FFmpeg, aria2c, and SSL certificates) into a single file.

- **🌐 Embedded Browser**: Surf YouTube and media sites directly in the app. URLs are auto-intercepted for one-click downloading!
- **🎬 Native Video Player**: Play your downloaded media offline immediately without leaving the app.
- **🚀 10x Faster Downloads**: Integrated `aria2` multithreading for maximum bandwidth utilization.
- **💎 Ultra-HD Support**: Full 4K and 8K support via official YouTube Account Login (OAuth2).
- **🎨 Stunning UI**: Modern Glassmorphism design with real-time theme switching.
- **🛡️ Security Hardened**: Built-in SHA-256 verification for external tools (FFmpeg/aria2c), path traversal protection, and secure credential storage (Keyring/DPAPI).
- **📦 Portable & Multiplatform**: No installation required on Windows (standalone `.exe`). Native macOS (.app) and Linux (AppImage) support with automated tool-chain setup.


## 🖼️ Screenshots

<p align="center">
  <img src="assets/Screenshots/Landing%20Page.png" alt="Landing Page" width="45%">
  <img src="assets/Screenshots/Feting%20Info.png" alt="Fetching Video Info" width="45%">
</p>
<p align="center">
  <img src="assets/Screenshots/Downloading%20Video.png" alt="Active Download" width="45%">
  <img src="assets/Screenshots/Downloads.png" alt="Downloads Library" width="45%">
</p>

---

## 🚀 Getting Started

### 📦 For Users (Easiest)
1. Go to the **[Releases](https://github.com/double-uRB/DownloaderPRO/releases)** page.
2. Download the package for your OS:
   - **Windows**: `DownloaderPRO_Setup.exe` (Installer) or `YouTubeDownloaderPro.exe` (Standalone).
   - **macOS**: `DownloaderPRO.dmg`.
   - **Linux**: `DownloaderPRO.AppImage`.
3. Run it! All tools (FFmpeg, aria2c, yt-dlp) are managed automatically.

> [!TIP]
> On macOS/Linux, the app will automatically detect your GPU and fetch hardware-accelerated binaries on first launch.

### 🛠️ For Developers / Advanced Users
If you want to run from source or build your own version:
1. **[View the Installation Guide](docs/INSTALLATION.md)** for detailed setup and cross-platform dependencies.
2. **[View the Multiplatform Build Guide](docs/BUILD_UNIX.md)** to generate your own binaries for Windows, Mac, or Linux.
3. Run `python src/main.py` once dependencies are installed.

---

## 📖 Key Features

| Feature | Details |
|---|---|
| **YouTube Login** | Uses Google's Device Flow (OAuth2) to unlock premium streams safely without sharing passwords. |
| **Advanced Mode** | Select exact video/audio formats and bitrates (H.264, VP9, AV1, MP3, AAC) for maximum control. |
| **Library Actions** | Functional "Open in Folder" and "Play" buttons in the Downloads page with cross-platform support (`open`, `xdg-open`, `explorer`) and shell-safe execution. |
| **Security Hardening** | SHA-256 binary integrity checks, Windows DPAPI/Keyring token storage, log sanitization (no tokens in logs), and filename path traversal prevention. |
| **Aria2 Acceleration** | Parallel chunk downloading for extremely high speeds with optimized SSD file allocation. |
| **Advanced History** | Peristent download history with intelligent batch-loading for zero UI stutters even with thousands of items. |
| **AIO Browser** | Multitab Chromium-based browser with one-click download interception. |
| **Native Player** | Integrated QMediaPlayer for offline playback with hardware acceleration. |


---

## 🏗️ Architecture & Contributing

- **[Architecture Overview](docs/ARCHITECTURE.md)**: Deep dive into the threading model and UI design system.
- **[Contributing Guide](CONTRIBUTING.md)**: Guidelines for bug reports and feature requests.

## ⚖️ Legal Notice
For educational and personal use only. Please respect YouTube's Terms of Service and content creators' copyrights.

---
Developed with ❤️ by [Rajesh Barai](https://github.com/double-uRB)
