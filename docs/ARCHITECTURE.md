# Downloader PRO - Internal Architecture

This document describes the internal structure and design of the YouTube Downloader PRO application. 

The application is built using **Python 3**, **PySide6** (Qt for Python) for the GUI, and **yt-dlp** for video processing and downloading.

## High-Level Architecture

The project is structured into three main layers:
1. **User Interface (UI) Layer**: Handles the presentation, user input, and progress feedback using PySide6.
2. **Core Logic / Processing Layer**: Handles the actual fetching of video information and the execution of downloads using `yt-dlp` and `FFmpeg`.
3. **Threading / Asynchronous Layer**: Bridges the UI and Core Logic to ensure the UI remains responsive during heavy networking/processing tasks.

---

## 1. User Interface (UI) Layer
The UI is built with a modern, glassmorphic design and consists of modular components located primarily in `src/`.

### Main Application (`main.py`)
- Sets up the `QMainWindow`.
- Manages the **Sidebar** and a **Stacked Widget** (`QStackedWidget`) that switches between different views (Dashboard, Downloads, Settings).
- Orchestrates the instantiation of worker threads and binds signals to UI slots.

### UI Components
- **`sidebar.py`**: The navigation menu on the left.
- **`downloads_page.py`**: The queue and history of actively downloading and completed files.
- **`settings_page.py`**: The configuration interface (theme selection, download path).
- **`ui_components.py`**: Reusable generic widgets, such as `VideoInfoPanel` (shows video thumbnail, title, stats), `QualitySelector`, and `ProgressWidget`.
- **`theme.py`**: Manages the dynamic generation of Qt Style Sheets (QSS) for light and dark modes.

---

## 2. Core Logic (`downloader_core.py`)
This module encapsulates all interactions with the external `yt-dlp` library and filesystem.

### `VideoDownloader` Class
- **FFmpeg Discovery**: Locates the `FFmpeg` executable needed for merging video and audio streams.
- **Cookie Extraction**: Scans the user's local browsers (Chrome, Firefox, Edge, etc.) to extract cookies. This is critical for bypassing age restrictions and rate limits on YouTube.
- **`get_video_info()`**: Fetches metadata (title, thumbnails, available quality formats) without actually downloading the video.
- **`download_video()`**: The primary function that configures `yt-dlp` options (quality, output path, post-processors, format selection) and starts the download.

### Custom Logging & Progress Parsing
`YtDlpLogger` intercepts the console output of `yt-dlp`. It uses regex matching on the output stream to extract the download percentage, file size, speed, and ETA. These values are sent via a callback to the UI layer for real-time progress bars.

---

## 3. Asynchronous Execution (Threading)
To prevent the PySide6 UI from freezing during network requests, all heavy lifting is pushed to background threads using `QThread`.

- **`VideoInfoThread`**: 
  - Takes a URL and fetches the metadata via `VideoDownloader.get_video_info`.
  - Emits an `info_fetched(dict)` signal upon success, which populates the `VideoInfoPanel`.

- **`DownloadThread`**:
  - Handles the downloading process via `VideoDownloader.download_video`.
  - Emits `progress_updated(int, str)` as `yt-dlp` downloads data.
  - Emits `download_completed()` or `download_failed(str)` upon conclusion.

---

## Configuration & State Management
- **`settings_manager.py`**: Uses Python's `json` module to persist user preferences (e.g., default download directory, dark/light theme). The settings are loaded on startup and saved on exit.
- **`app_logger.py`**: A centralized logging utility to write execution logs to `logs/app.log` and standard output, aiding in debugging.
