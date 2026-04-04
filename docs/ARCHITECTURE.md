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
- **`browser_page.py`**: Fully embedded Chromium web browser (`QWebEngineView`) for navigating media sites, with automatic URL interception for one-click downloading.
- **`video_player.py`**: Native offline media player using `QMediaPlayer` and `QVideoWidget` with transport controls.
- **`settings_page.py`**: The configuration interface (theme selection, download path).
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
    - **OAuth2 Device Flow**: Implements the `start_oauth_login` method which runs a `yt-dlp` subprocess to trigger Google's device activation flow. It captures the activation link and code and includes a **120-second timeout** to ensure the application remains responsive if the process hangs. It uses a standard dummy URL (YouTube's first video, "Me at the zoo") to safely trigger the extractor without introducing arbitrary or unprofessional links.
- **Improved Process Safety**: All internal subprocess calls (yt-dlp, FFmpeg, explorer, etc.) use **list-based arguments** instead of shell strings. This prevents shell injection vulnerabilities and ensures robust handling of file paths containing spaces or special characters.
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
- **Cross-Platform Integration**: Includes a smart `_open_path` helper that dynamically detects the platform (`sys.platform`) to use the appropriate system handler:
    - **Windows**: `explorer /select` (to highlight the file) or `os.startfile`.
    - **macOS**: `open`.
    - **Linux**: `xdg-open`.
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

## 5. Persistence & Security Layer
The application manages user data and secrets through a multi-tier persistence system:

### ⚙️ Settings Management (`settings_manager.py`)
- **Native Storage**: Migrated from simple JSON to **Qt's native `QSettings`** system. On Windows, this utilizes the Registry (`HKEY_CURRENT_USER\Software\DownloaderPRO`), providing a robust and OS-integrated way to handle application preferences.
- **Secure Secret Storage (`keyring`)**: Sensitive credentials like YouTube **PO Tokens** are no longer stored in plaintext. The system uses the `keyring` library to interface with the host OS's secure credential manager (Windows DPAPI, macOS Keychain, or Linux Secret Service), ensuring that user secrets are encrypted at rest.
- **Log Sanitization (`app_logger.py`)**: Implements a `SanitizingFilter` that dynamically redacts sensitive patterns (tokens, cookies, auth headers) before they are written to disk. Logs are rotated (5MB limit) to prevent disk exhaustion.

### 📜 History Management (`history_manager.py`)
- **JSON Metadata**: Completed downloads are persisted in `config/history.json`.
- **Intelligent Batch Loading**: To maintain a 60fps UI, the `DownloadsPage` implements an **Asynchronous Batch Loader**. It renders history items in small chunks (10 at a time) using a `QTimer`, preventing UI lockup when the history contains thousands of entries.

---

## 6. Build System & Tool Orchestration (`build_app.py`)
The project features an intelligent, cross-platform build script designed for zero-configuration for the end user.

- **Platform Detection**: Automatically detects the host OS (Windows, Darwin, Linux).
- **Binary Integrity Verification**: Implements **SHA-256 Checksum Verification** for all automated downloads (FFmpeg and aria2c). This protects against supply chain attacks and ensures the bundled binaries are authentic and uncorrupted.
- **Linux Native Integration**: For Linux builds, the script prioritizes system-installed binaries via `shutil.which`, ensuring maximum compatibility with various distribution package managers.
- **Self-Contained Bundling**: Uses PyInstaller to create a **Truly Standalone** binary. The build process packages the Python runtime, all dependencies (PySide6, yt-dlp), and the verified toolchain (FFmpeg/aria2c) into a single, portable executable.
