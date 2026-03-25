"""
Downloader PRO — Main Application
Modern sidebar + stacked content layout with glassmorphism UI.
"""

import sys
import os
import pyperclip
from pathlib import Path
from app_logger import get_logger

log = get_logger(__name__)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFileDialog, QCheckBox,
    QMessageBox, QStackedWidget, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QFont, QIcon

from downloader_core import VideoDownloader
from ui_components import VideoInfoPanel, QualitySelector, ProgressWidget
from settings_manager import SettingsManager
from sidebar import Sidebar
from theme import generate_stylesheet
from downloads_page import DownloadsPage
from settings_page import SettingsPage


class YouTubeDownloaderApp(QMainWindow):

    def __init__(self):
        super().__init__()

        # Initialize managers
        self.settings = SettingsManager()
        self.downloader = VideoDownloader()
        self.current_video_info = None
        self.quality_selector = None
        self.download_counter = 0

        # Load settings
        self.download_path = self.settings.get_download_path()
        self.theme_mode = self.settings.get_theme()

        # Setup UI
        self._setup_ui()
        self._apply_theme()

        # Window properties
        self.setWindowTitle("Downloader PRO")
        self.setMinimumSize(1000, 650)
        self.resize(1100, 750)

    def _setup_ui(self):
        """Create the sidebar + main content layout."""
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Sidebar ──
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._on_page_changed)
        root_layout.addWidget(self.sidebar)

        # ── Main content area ──
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top header bar
        self._create_top_header(main_layout)

        # Stacked pages
        self.page_stack = QStackedWidget()

        # Page 0: Dashboard
        self.dashboard_page = self._create_dashboard_page()
        self.page_stack.addWidget(self.dashboard_page)

        # Page 1: Downloads
        self.downloads_page = DownloadsPage()
        self.page_stack.addWidget(self.downloads_page)

        # Page 2: Settings
        self.settings_page = SettingsPage(self.settings)
        self.settings_page.theme_changed.connect(self._on_theme_changed)
        self.page_stack.addWidget(self.settings_page)

        main_layout.addWidget(self.page_stack)
        root_layout.addWidget(main_container)

    def _create_top_header(self, parent_layout):
        """Top bar with page title, theme toggle, and user avatar."""
        header = QWidget()
        header.setObjectName("top_header")
        header.setFixedHeight(56)

        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)
        h_layout.setSpacing(12)

        # Page title
        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("page_title")
        self.page_title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title_col.addWidget(self.page_title)

        self.page_subtitle = QLabel("MANAGING ACTIVE TASKS")
        self.page_subtitle.setObjectName("page_subtitle")
        self.page_subtitle.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
        title_col.addWidget(self.page_subtitle)

        h_layout.addLayout(title_col)
        h_layout.addStretch()

        # Theme toggle
        toggle_container = QWidget()
        toggle_container.setObjectName("theme_toggle_bg")
        toggle_container.setFixedSize(64, 30)

        toggle_layout = QHBoxLayout(toggle_container)
        toggle_layout.setContentsMargins(4, 4, 4, 4)
        toggle_layout.setSpacing(0)

        self.light_icon = QLabel("☀️")
        self.light_icon.setFont(QFont("Segoe UI", 10))
        self.light_icon.setFixedSize(22, 22)
        self.light_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toggle_layout.addWidget(self.light_icon)

        toggle_layout.addStretch()

        self.dark_icon = QLabel("🌙")
        self.dark_icon.setFont(QFont("Segoe UI", 10))
        self.dark_icon.setFixedSize(22, 22)
        self.dark_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toggle_layout.addWidget(self.dark_icon)

        toggle_container.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_container.mousePressEvent = lambda e: self._toggle_theme()

        h_layout.addWidget(toggle_container)

        # User avatar placeholder
        avatar = QLabel("👤")
        avatar.setFont(QFont("Segoe UI", 14))
        avatar.setFixedSize(34, 34)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("background-color: #2d3449; border-radius: 17px; border: 1px solid rgba(76, 215, 246, 0.2);")
        h_layout.addWidget(avatar)

        parent_layout.addWidget(header)

    def _create_dashboard_page(self):
        """Build the dashboard page (URL input + video info + quality + download)."""
        from PySide6.QtWidgets import QScrollArea

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # ── URL Input Card ──
        url_card = QWidget()
        url_card.setObjectName("glass_panel")
        url_layout = QVBoxLayout(url_card)
        url_layout.setContentsMargins(24, 20, 24, 20)
        url_layout.setSpacing(12)

        url_title_row = QHBoxLayout()
        link_icon = QLabel("🔗")
        link_icon.setFont(QFont("Segoe UI", 16))
        url_title_row.addWidget(link_icon)
        url_title = QLabel("Paste Video URL")
        url_title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        url_title_row.addWidget(url_title)
        url_title_row.addStretch()
        url_layout.addLayout(url_title_row)

        input_row = QHBoxLayout()
        input_row.setSpacing(12)

        # URL input with inline paste button
        url_input_container = QWidget()
        url_input_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        url_input_layout = QHBoxLayout(url_input_container)
        url_input_layout.setContentsMargins(0, 0, 0, 0)
        url_input_layout.setSpacing(0)

        self.url_entry = QLineEdit()
        self.url_entry.setPlaceholderText("https://youtube.com/watch?v=...")
        self.url_entry.setFixedHeight(46)
        self.url_entry.setFont(QFont("Segoe UI", 12))
        url_input_layout.addWidget(self.url_entry)

        paste_btn = QPushButton("📋 Paste")
        paste_btn.setObjectName("paste_button")
        paste_btn.setFixedSize(80, 30)
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(self._paste_url)
        url_input_layout.addWidget(paste_btn)

        input_row.addWidget(url_input_container)

        # Fetch button
        self.fetch_btn = QPushButton("🔍  Fetch Info")
        self.fetch_btn.setObjectName("primary_button")
        self.fetch_btn.setFixedSize(140, 46)
        self.fetch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fetch_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.fetch_btn.clicked.connect(self._fetch_video_info)
        input_row.addWidget(self.fetch_btn)

        url_layout.addLayout(input_row)
        layout.addWidget(url_card)

        # ── Main content grid: Video Info (left) + Options (right) ──
        content_row = QHBoxLayout()
        content_row.setSpacing(20)

        # Left: Video Info Panel
        self.video_info_panel = VideoInfoPanel()
        self.video_info_panel.hide()
        content_row.addWidget(self.video_info_panel, stretch=3)

        # Right: Quality + Actions
        self.right_panel = QWidget()
        self.right_panel.hide()
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)

        # Quality selector placeholder
        self.quality_container = QVBoxLayout()
        right_layout.addLayout(self.quality_container)

        # Actions panel
        actions_card = QWidget()
        actions_card.setObjectName("surface_card")
        actions_layout = QVBoxLayout(actions_card)
        actions_layout.setContentsMargins(20, 16, 20, 16)
        actions_layout.setSpacing(14)

        # Save to
        save_label = QLabel("SAVE TO")
        save_label.setObjectName("stat_label")
        save_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        actions_layout.addWidget(save_label)

        path_row = QHBoxLayout()
        path_row.setSpacing(8)

        self.path_display = QLabel(self.download_path)
        self.path_display.setFont(QFont("Segoe UI", 11))
        self.path_display.setStyleSheet("padding: 6px 10px; background-color: #060e20; border-radius: 6px;")
        self.path_display.setMaximumWidth(250)
        path_row.addWidget(self.path_display, stretch=1)

        browse_btn = QPushButton("📁")
        browse_btn.setFixedSize(38, 34)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_folder)
        path_row.addWidget(browse_btn)

        actions_layout.addLayout(path_row)

        # Audio only toggle
        audio_row = QHBoxLayout()
        audio_icon = QLabel("🎵")
        audio_icon.setFont(QFont("Segoe UI", 14))
        audio_row.addWidget(audio_icon)

        audio_label = QLabel("Audio (MP3)")
        audio_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        audio_row.addWidget(audio_label)

        audio_row.addStretch()

        self.audio_only_cb = QCheckBox()
        audio_row.addWidget(self.audio_only_cb)

        actions_layout.addLayout(audio_row)

        # Download button
        self.download_btn = QPushButton("⬇️  Download")
        self.download_btn.setObjectName("download_button")
        self.download_btn.setFixedHeight(52)
        self.download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_btn.setFont(QFont("Segoe UI", 15, QFont.Weight.Black))
        self.download_btn.clicked.connect(self._start_download)
        actions_layout.addWidget(self.download_btn)

        # SSL notice
        ssl_label = QLabel("🔒 SSL Encrypted & Ad-Free")
        ssl_label.setObjectName("section_subtitle")
        ssl_label.setFont(QFont("Segoe UI", 9))
        ssl_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        actions_layout.addWidget(ssl_label)

        right_layout.addWidget(actions_card)
        right_layout.addStretch()

        content_row.addWidget(self.right_panel, stretch=2)
        layout.addLayout(content_row)

        # ── Progress widget placeholder ──
        self.progress_container = QVBoxLayout()
        layout.addLayout(self.progress_container)

        layout.addStretch()

        scroll.setWidget(page)
        return scroll

    # ─── Navigation ─────────────────────────────────────────────────────────

    def _on_page_changed(self, page_key):
        page_map = {"dashboard": 0, "downloads": 1, "settings": 2}
        title_map = {
            "dashboard": ("Dashboard", "MANAGING ACTIVE TASKS"),
            "downloads": ("Downloads", "LIBRARY & QUEUE"),
            "settings": ("Settings", "APP CONFIGURATION"),
        }
        idx = page_map.get(page_key, 0)
        self.page_stack.setCurrentIndex(idx)
        title, subtitle = title_map.get(page_key, ("Dashboard", ""))
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)

    # ─── Theme ──────────────────────────────────────────────────────────────

    def _toggle_theme(self):
        new_theme = "light" if self.theme_mode == "dark" else "dark"
        self.theme_mode = new_theme
        self.settings.set_theme(new_theme)
        self._apply_theme()

    def _on_theme_changed(self, theme):
        if theme == "auto":
            theme = "dark"  # Default auto to dark for now
        self.theme_mode = theme
        self.settings.set_theme(theme)
        self._apply_theme()

    def _apply_theme(self):
        self.setStyleSheet(generate_stylesheet(self.theme_mode))

    # ─── URL / Fetch ────────────────────────────────────────────────────────

    def _paste_url(self):
        try:
            clipboard_content = pyperclip.paste()
            if clipboard_content and ("youtube.com" in clipboard_content or "youtu.be" in clipboard_content):
                self.url_entry.setText(clipboard_content)
                self.statusBar().showMessage("URL pasted successfully")
            else:
                QMessageBox.warning(self, "Warning", "No valid YouTube URL found in clipboard")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to paste: {str(e)}")

    def _fetch_video_info(self):
        url = self.url_entry.text().strip()
        if not url:
            QMessageBox.critical(self, "Error", "Please enter a YouTube URL")
            return

        self.statusBar().showMessage("Fetching video information...")
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("Loading...")

        self.fetch_thread = VideoInfoThread(url, self.downloader)
        self.fetch_thread.info_fetched.connect(self._on_video_info_fetched)
        self.fetch_thread.error_occurred.connect(self._on_fetch_error)
        self.fetch_thread.start()

    def _on_video_info_fetched(self, info):
        self.current_video_info = info

        # Update video info panel
        self.video_info_panel.update_info(info)
        self.video_info_panel.show()

        # Show quality selector
        self._show_quality_selector(info.get('formats', []))

        # Show right panel
        self.right_panel.show()

        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("Fetch Info")
        self.statusBar().showMessage("Video information loaded successfully")
        log.info("Video info loaded: %s", info.get('title', 'Unknown'))

    def _on_fetch_error(self, error_msg):
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("Fetch Info")
        self.statusBar().showMessage("Failed to fetch video information")
        log.error("Fetch error: %s", error_msg)
        QMessageBox.critical(self, "Error", f"Failed to fetch video info: {error_msg}")

    def _show_quality_selector(self, formats):
        # Clear existing
        while self.quality_container.count():
            child = self.quality_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.quality_selector = QualitySelector(formats)
        self.quality_container.addWidget(self.quality_selector)

    # ─── Download ───────────────────────────────────────────────────────────

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Download Folder", self.download_path
        )
        if folder:
            self.download_path = folder
            self.path_display.setText(folder)
            self.settings.set_download_path(folder)

    def _start_download(self):
        if not self.current_video_info:
            QMessageBox.warning(self, "Warning", "Please fetch video info first")
            return

        if not self.quality_selector:
            QMessageBox.warning(self, "Warning", "Please select a quality option")
            return

        url = self.url_entry.text().strip()
        quality = self.quality_selector.get_selected_quality()
        output_path = self.download_path
        audio_only = self.audio_only_cb.isChecked()

        if not output_path:
            QMessageBox.warning(self, "Warning", "Please select a download location")
            return

        # Create progress widget on dashboard
        progress_widget = ProgressWidget(self.current_video_info)
        self.progress_container.addWidget(progress_widget)

        # Also add to downloads page
        self.download_counter += 1
        dl_id = f"dl_{self.download_counter}"
        title = self.current_video_info.get('title', 'Unknown')
        dl_card = self.downloads_page.add_active_download(dl_id, title[:50], "YouTube • MP4")

        # Start download thread
        self.download_thread = DownloadThread(
            url, quality, output_path, audio_only, self.downloader
        )
        self.download_thread.progress_updated.connect(progress_widget.update_progress)
        self.download_thread.progress_updated.connect(
            lambda p, s: self.downloads_page.update_download_progress(dl_id, p, s)
        )
        self.download_thread.download_completed.connect(progress_widget.download_complete)
        self.download_thread.download_completed.connect(
            lambda: self.downloads_page.complete_download(dl_id, title[:50], "--")
        )
        self.download_thread.download_failed.connect(
            lambda err: progress_widget.download_failed(err)
        )
        self.download_thread.download_failed.connect(
            lambda err: log.error("Download failed for '%s': %s", title[:50], err)
        )
        self.download_thread.start()

        log.info("Download started for: %s (quality=%s)", title[:50], quality)
        self.statusBar().showMessage("Download started...")

    def closeEvent(self, event):
        self.settings.save_settings()
        event.accept()


# ─── Worker Threads ────────────────────────────────────────────────────────

class VideoInfoThread(QThread):
    info_fetched = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, url, downloader):
        super().__init__()
        self.url = url
        self.downloader = downloader

    def run(self):
        try:
            info = self.downloader.get_video_info(self.url)
            if info:
                self.info_fetched.emit(info)
            else:
                self.error_occurred.emit("Failed to fetch video information")
        except Exception as e:
            self.error_occurred.emit(str(e))


class DownloadThread(QThread):
    progress_updated = Signal(int, str)
    download_completed = Signal()
    download_failed = Signal(str)

    def __init__(self, url, quality, output_path, audio_only, downloader):
        super().__init__()
        self.url = url
        self.quality = quality
        self.output_path = output_path
        self.audio_only = audio_only
        self.downloader = downloader

    def run(self):
        def progress_callback(progress, status):
            self.progress_updated.emit(int(progress), status)

        try:
            result = self.downloader.download_video(
                self.url, self.quality, self.output_path,
                self.audio_only, progress_callback
            )
            # Handle both old (bool) and new (tuple) return formats
            if isinstance(result, tuple):
                success, error_msg = result
            else:
                success, error_msg = result, None

            if success:
                self.download_completed.emit()
            else:
                self.download_failed.emit(error_msg or "Unknown error")
        except Exception as e:
            self.download_failed.emit(str(e))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Downloader PRO")
    app.setOrganizationName("DownloaderPRO")

    window = YouTubeDownloaderApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
