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
- **`sidebar.py`**: The navigation menu on the left (now using fluid sizing).
- **`downloads_page.py`**: The queue and history of actively downloading and completed files.
- **`settings_page.py`**: The configuration interface (theme selection, download path, and advanced YouTube authentication).
- **`ui_components.py`**: Reusable generic widgets, such as `VideoInfoPanel`, `QualitySelector`, and `ProgressWidget`.
- **`theme.py`**: Manages the dynamic generation of Qt Style Sheets (QSS) for light and dark modes.

### Assets & Icons
The application has transitioned from system-emoji icons to a professional **SVG Vector Icon System**. Icons are stored in `assets/icons/` and loaded dynamically using a helper method in `ui_components.py` and `settings_page.py`, ensuring a crisp look at any DPI.

---

## 2. Core Logic (`downloader_core.py`)
This module encapsulates all interactions with the external `yt-dlp` library and filesystem.

### `VideoDownloader` Class
- **FFmpeg/ffprobe Discovery**: Locates the `FFmpeg` and `ffprobe` executables in the `tools/` folder. `ffprobe` is critical for accurate audio codec detection.
- **Turbo Multi-threading (`aria2`)**: Automatically detects the `aria2` executable and configures `yt-dlp` as an external downloader. It uses up to **16 parallel connections** (`-n 16 -x 16 -k 1M`) to maximize bandwidth utilization and bypass per-connection speed limits.
- **Resilient Stream Parsing**: Implements a robust metadata parser in `parse_available_streams()`. If YouTube's manifest is missing audio codec info (common in DASH streams), the system uses a **resolution-based fallback** (`resolution='audio only'`) to identify valid audio tracks.
- **Advanced Download Engine**: 
    - **`download_video_advanced()`**: Merges specific video and audio format IDs selected by the user.
    - **`download_audio_advanced()`**: Performs high-quality extraction of a single selected audio format.
- **YouTube Bypass Engine**: Implements a prioritized `player_client` list (`ios`, `android`, `web`) and applies **PO Tokens** (Proof of Origin) to extractor arguments. This prevents 360p caps and "content unavailable" blocks.
- **Authentication (OAuth2 & Cookies)**: 
    - **OAuth2 Device Flow**: Implements the `start_oauth_login` method which runs a `yt-dlp` subprocess to trigger Google's device activation flow, capturing the link and code for the user.
    - **Custom Cookies**: Provides a fallback for manual Netscape-formatted `cookies.txt` files, bypassing Windows DPAPI (App-Bound Encryption) issues in modern browsers.
- **`get_video_info()`**: Fetches metadata (title, thumbnails, available quality formats) without actually downloading the video.
- **`download_video()`**: The primary function for simple downloads with automatic quality selection.

### Custom Logging & Progress Parsing
`YtDlpLogger` intercepts the console output of `yt-dlp`. It uses regex matching on the output stream to extract the download percentage, file size, speed, and ETA. These values are sent via a callback to the UI layer for real-time progress bars.

---

## 3. UI Component Logic

### Advanced Download Panel
The `AdvancedDownloadPanel` in `ui_components.py` provides a granular interface for selecting specific video and audio streams. It features:
- **Video Section**: Displays available resolutions, codecs (H.264, VP9, AV1), and bitrates.
- **Audio Section**: Shows available audio formats (MP3, AAC, OPUS) and bitrates.
- **Audio-Only Mode**: A toggle that disables the video section and configures the downloader for a pure audio stream.

### Downloads Library (`downloads_page.py`)
Each download item is managed as a `CompletedItemCard`. These cards feature:
- **Smart Directory Discovery**: Automatically locates downloaded files in the target directory if the absolute path is unavailable.
- **System Integration**: Working "Open Folder" (using `explorer /select`) and "Play" (using `os.startfile`) buttons for immediate access to content.
- **State Management**: Persists download history across application restarts (future implementation).

---

## 4. Asynchronous Execution (Threading)
To prevent the PySide6 UI from freezing during network requests, all heavy lifting is pushed to background threads using `QThread`.

- **`VideoInfoThread`**: 
  - Takes a URL and fetches the metadata via `VideoDownloader.get_video_info`.
  - Emits an `info_fetched(dict)` signal upon success, which populates the `VideoInfoPanel`.

- **`DownloadThread`**:
  - Handles the downloading process via `VideoDownloader.download_video`.
  - Emits `progress_updated(int, str)` as `yt-dlp` downloads data.
  - Emits `download_completed()` or `download_failed(str)` upon conclusion.

- **`OAuthLoginThread`**:
  - Manages the asynchronous YouTube login process.
  - Intercepts `yt-dlp` output to find activation instructions.
  - Signals the UI to show the login dialog and activation code.

---

## Configuration & State Management
- **`settings_manager.py`**: Uses Python's `json` module to persist user preferences (e.g., default download directory, dark/light theme). The settings are loaded on startup and saved on exit.
- **`app_logger.py`**: A centralized logging utility to write execution logs to `logs/app.log` and standard output, aiding in debugging.
