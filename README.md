# Downloader PRO

A modern, professional YouTube video and audio downloader built with Python and PySide6. Features a clean, glassmorphic GUI with dark/light themes, high-fidelity quality selection (up to 8K), and robust multithreaded downloading.

[![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white)](#) [![PySide6](https://img.shields.io/badge/-PySide6-41CD52?style=flat-square&logo=qt&logoColor=white)](#) [![FFmpeg](https://img.shields.io/badge/-FFmpeg-007808?style=flat-square)](#) [![aria2](https://img.shields.io/badge/-aria2-333333?style=flat-square)](#) [![yt--dlp](https://img.shields.io/badge/-yt--dlp-FF0000?style=flat-square&logo=youtube&logoColor=white)](#)

---

## ✨ Why Downloader PRO?

Unlike most downloaders, Downloader PRO provides a **Zero-Dependency** experience. Our standalone executable bundles everything needed (Python, FFmpeg, aria2c, and SSL certificates) into a single file.

- **🚀 10x Faster Downloads**: Integrated `aria2` multithreading for maximum bandwidth utilization.
- **💎 Ultra-HD Support**: Full 4K and 8K support via official YouTube Account Login (OAuth2).
- **🎨 Stunning UI**: Modern Glassmorphism design with real-time theme switching.
- **🛡️ Anti-Block Technology**: Uses PO Tokens and custom client headers to bypass rate limits and "content unavailable" errors.
- **📦 Truly Portable**: No installation required. Just download the `.exe` and run.

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
2. Download the latest `YouTubeDownloaderPro.exe`.
3. Run it! (No Python, FFmpeg, or extra tools required).

> [!NOTE]
> Since this is a standalone tool, Windows SmartScreen may show a warning. Click "More Info" -> "Run Anyway" to proceed.

### 🛠️ For Developers / Advanced Users
If you want to run from source or build your own version:
1. **[View the Installation Guide](docs/INSTALLATION.md)** for detailed setup instructions.
2. Run `python src/main.py` once dependencies are installed.

---

## 📖 Key Features

| Feature | Details |
|---|---|
| **YouTube Login** | Uses Google's Device Flow (OAuth2) to unlock premium streams safely without sharing passwords. |
| **PO Tokens** | Built-in support for "Proof of Origin" tokens to bypass YouTube's latest anti-bot measures. |
| **Aria2 Acceleration** | Parallel chunk downloading for extremely high speeds even on slower connections. |
| **Audio Extraction** | High-fidelity MP3 extraction with correct metadata and merging using FFmpeg. |
| **Custom Patterns** | Flexible filename patterns like `{date}_{title}.{ext}` via Settings. |

---

## 🏗️ Architecture & Contributing

- **[Architecture Overview](docs/ARCHITECTURE.md)**: Deep dive into the threading model and UI design system.
- **[Contributing Guide](CONTRIBUTING.md)**: Guidelines for bug reports and feature requests.

## ⚖️ Legal Notice
For educational and personal use only. Please respect YouTube's Terms of Service and content creators' copyrights.

---
Developed with ❤️ by [Rajesh Barai](https://github.com/double-uRB)
