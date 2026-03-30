"""
Downloader PRO — Main Application
Modern sidebar + stacked content layout with glassmorphism UI.
"""

import sys
import os
import pyperclip
from pathlib import Path
from app_logger import get_logger

# Window icon and taskbar handling will be done in main()

log = get_logger(__name__)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFileDialog, QCheckBox,
    QMessageBox, QStackedWidget, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QFont, QIcon

from downloader_core import VideoDownloader
from ui_components import VideoInfoPanel, QualitySelector, ProgressWidget, AdvancedDownloadPanel
from settings_manager import SettingsManager
from sidebar import Sidebar
from theme import generate_stylesheet
from downloads_page import DownloadsPage
from settings_page import SettingsPage
from utils import get_resource_path


class YouTubeDownloaderApp(QMainWindow):

    def __init__(self):
        super().__init__()

        # Initialize managers
        self.settings = SettingsManager()
        self.downloader = VideoDownloader(
            po_token=self.settings.get_po_token(),
            cookies_path=self.settings.get_cookies_path(),
            use_oauth2=self.settings.get_use_oauth2()
        )
        self.current_video_info = None
        self.cached_formats = []  # Cache fetched formats — no extra API calls
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
        
        # Set window icon (taskbar)
        icon_path = get_resource_path("assets/logo.ico")
        if Path(icon_path).exists():
            self.setWindowIcon(QIcon(icon_path))

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
        self.downloads_page = DownloadsPage(download_path=self.download_path)
        self.page_stack.addWidget(self.downloads_page)

        # Page 2: Settings
        self.settings_page = SettingsPage(self.settings)
        self.settings_page.theme_changed.connect(self._on_theme_changed)
        self.settings_page.settings_changed.connect(self._on_settings_saved)
        self.settings_page.oauth_login_requested.connect(self._handle_oauth_login)
        self.settings_page.oauth_logout_requested.connect(self._handle_oauth_logout)
        self.page_stack.addWidget(self.settings_page)

        main_layout.addWidget(self.page_stack)
        root_layout.addWidget(main_container)

    def _create_top_header(self, parent_layout):
        """Top bar with page title, theme toggle, and user avatar."""
        header = QWidget()
        header.setObjectName("top_header")
        header.setMinimumHeight(56)

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

        from PySide6.QtGui import QIcon
        icon_dir = Path(__file__).parent.parent / "assets" / "icons"

        self.light_icon = QLabel()
        sun_path = get_resource_path("assets/icons/sun.svg")
        if Path(sun_path).exists():
            self.light_icon.setPixmap(QIcon(sun_path).pixmap(18, 18))
        else:
            self.light_icon.setText("S")
        self.light_icon.setFixedSize(22, 22)
        self.light_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toggle_layout.addWidget(self.light_icon)

        toggle_layout.addStretch()

        self.dark_icon = QLabel()
        moon_path = get_resource_path("assets/icons/moon.svg")
        if Path(moon_path).exists():
            self.dark_icon.setPixmap(QIcon(moon_path).pixmap(16, 16))
        else:
            self.dark_icon.setText("M")
        self.dark_icon.setFixedSize(22, 22)
        self.dark_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toggle_layout.addWidget(self.dark_icon)

        toggle_container.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_container.mousePressEvent = lambda e: self._toggle_theme()

        h_layout.addWidget(toggle_container)

        # User avatar placeholder
        avatar = QLabel()
        user_path = get_resource_path("assets/icons/user.svg")
        if Path(user_path).exists():
            avatar.setPixmap(QIcon(user_path).pixmap(20, 20))
        else:
            avatar.setText("U")
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
        link_icon = QLabel()
        link_path = get_resource_path("assets/icons/link.svg")
        if Path(link_path).exists():
            link_icon.setPixmap(QIcon(link_path).pixmap(20, 20))
        else:
            link_icon.setText("L")
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
        self.url_entry.setMinimumHeight(46)
        self.url_entry.setFont(QFont("Segoe UI", 12))
        url_input_layout.addWidget(self.url_entry)

        paste_btn = QPushButton(" Paste")
        clip_path = get_resource_path("assets/icons/clipboard.svg")
        if Path(clip_path).exists():
            from PySide6.QtCore import QSize
            paste_btn.setIcon(QIcon(clip_path))
            paste_btn.setIconSize(QSize(16, 16))
        paste_btn.setObjectName("paste_button")
        paste_btn.setMinimumHeight(30)
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(self._paste_url)
        url_input_layout.addWidget(paste_btn)

        input_row.addWidget(url_input_container)

        # Fetch button
        self.fetch_btn = QPushButton(" Fetch Info")
        search_path = get_resource_path("assets/icons/search.svg")
        if Path(search_path).exists():
            self.fetch_btn.setIcon(QIcon(search_path))
            self.fetch_btn.setIconSize(QSize(20, 20))
        self.fetch_btn.setObjectName("primary_button")
        self.fetch_btn.setMinimumSize(140, 46)
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

        # ── Advanced Download Toggle ──
        self.advanced_toggle_btn = QPushButton("  Advanced Download ▼")
        settings_icon = get_resource_path("assets/icons/settings.svg")
        if Path(settings_icon).exists():
            self.advanced_toggle_btn.setIcon(QIcon(settings_icon))
            self.advanced_toggle_btn.setIconSize(QSize(16, 16))
        self.advanced_toggle_btn.setObjectName("paste_button")
        self.advanced_toggle_btn.setMinimumHeight(36)
        self.advanced_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.advanced_toggle_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self.advanced_toggle_btn.setCheckable(True)
        self.advanced_toggle_btn.setChecked(self.settings.get_advanced_mode())
        self.advanced_toggle_btn.clicked.connect(self._toggle_advanced)
        right_layout.addWidget(self.advanced_toggle_btn)

        # ── Advanced Download Panel ──
        self.advanced_panel = AdvancedDownloadPanel()
        self.advanced_panel.setVisible(self.settings.get_advanced_mode())
        # Restore saved preferences
        self.advanced_panel.set_preferences(
            video_codec=self.settings.get_preferred_video_codec(),
            audio_codec=self.settings.get_preferred_audio_codec(),
            bitrate_mode=self.settings.get_preferred_bitrate_mode(),
            custom_bitrate=self.settings.get_preferred_bitrate_custom(),
        )
        right_layout.addWidget(self.advanced_panel)

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

        browse_btn = QPushButton("")
        folder_path = get_resource_path("assets/icons/folder.svg")
        if Path(folder_path).exists():
            browse_btn.setIcon(QIcon(folder_path))
            browse_btn.setIconSize(QSize(20, 20))
        else:
            browse_btn.setText("F")
        browse_btn.setFixedSize(38, 34)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_folder)
        path_row.addWidget(browse_btn)

        actions_layout.addLayout(path_row)

        # Download button
        self.download_btn = QPushButton("  Download")
        dl_icon_path = get_resource_path("assets/icons/download.svg")
        if Path(dl_icon_path).exists():
            self.download_btn.setIcon(QIcon(dl_icon_path))
            self.download_btn.setIconSize(QSize(24, 24))
        self.download_btn.setObjectName("download_button")
        self.download_btn.setMinimumHeight(52)
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

    def _on_settings_saved(self, settings):
        """Handle settings saved event."""
        po_token = settings.get("po_token", "")
        cookies_path = settings.get("cookies_path", "")
        use_oauth2 = settings.get("use_oauth2", False)
        self.downloader.set_advanced_settings(po_token, cookies_path, use_oauth2)
        self.statusBar().showMessage("Engine configuration updated")

    def _handle_oauth_login(self):
        """Start the OAuth2 login flow with a dialog."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit
        from PySide6.QtGui import QFont, QDesktopServices
        from PySide6.QtCore import QUrl
        
        self.login_dialog = QDialog(self)
        self.login_dialog.setWindowTitle("YouTube Login")
        self.login_dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(self.login_dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("Authentication Required")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        self.login_instr = QLabel("Initializing login flow...")
        self.login_instr.setWordWrap(True)
        layout.addWidget(self.login_instr)
        
        self.code_input = QLineEdit()
        self.code_input.setReadOnly(True)
        self.code_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_input.setFont(QFont("Consolas", 18, QFont.Weight.Bold))
        self.code_input.setStyleSheet("padding: 10px; background: #060e20; color: #4cd7f6; border-radius: 8px;")
        self.code_input.hide()
        layout.addWidget(self.code_input)
        
        self.link_btn = QPushButton("Open Login Page")
        self.link_btn.setObjectName("primary_button")
        self.link_btn.hide()
        layout.addWidget(self.link_btn)
        
        # Start the worker thread
        self.oauth_thread = OAuthLoginThread(self.downloader)
        
        def on_instructions(url, code):
            self.login_instr.setText("1. Click the button below to open the Google login page.\n2. Enter the following code:")
            self.code_input.setText(code)
            self.code_input.show()
            self.link_btn.show()
            self.link_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
            
        self.oauth_thread.instructions_received.connect(on_instructions)
        self.oauth_thread.finished.connect(self._on_oauth_finished)
        self.oauth_thread.start()
        
        self.login_dialog.exec()

    def _on_oauth_finished(self):
        if hasattr(self, 'login_dialog'):
            self.login_dialog.accept()
        self.settings.set_use_oauth2(True)
        self.settings_page.load_settings() # Refresh UI status
        self.downloader.use_oauth2 = True
        log.info("OAuth login process completed")
        QMessageBox.information(self, "Success", "YouTube account connected successfully!")

    def _handle_oauth_logout(self):
        self.downloader.use_oauth2 = False
        self.statusBar().showMessage("Logged out from YouTube")

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
        if hasattr(self, "fetch_thread") and self.fetch_thread.isRunning():
            self._cancel_fetch()
            return

        url = self.url_entry.text().strip()
        if not url:
            QMessageBox.critical(self, "Error", "Please enter a YouTube URL")
            return

        self.statusBar().showMessage("Fetching video information...")
        self.fetch_btn.setText(" Stop Fetch")
        x_icon_path = get_resource_path("assets/icons/x.svg")
        if Path(x_icon_path).exists():
            from PySide6.QtGui import QIcon
            from PySide6.QtCore import QSize
            self.fetch_btn.setIcon(QIcon(x_icon_path))
            self.fetch_btn.setIconSize(QSize(16, 16))
        
        self.fetch_thread = VideoInfoThread(url, self.downloader)
        self.fetch_thread.info_fetched.connect(self._on_video_info_fetched)
        self.fetch_thread.error_occurred.connect(self._on_fetch_error)
        self.fetch_thread.start()

    def _cancel_fetch(self):
        if hasattr(self, "fetch_thread") and self.fetch_thread.isRunning():
            self.statusBar().showMessage("Stopping fetch...")
            self.fetch_thread.terminate()
            self.fetch_thread.wait()
            self._reset_fetch_btn()
            self.statusBar().showMessage("Fetch cancelled")

    def _reset_fetch_btn(self):
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText(" Fetch Info")
        search_path = get_resource_path("assets/icons/search.svg")
        if Path(search_path).exists():
            from PySide6.QtGui import QIcon
            from PySide6.QtCore import QSize
            self.fetch_btn.setIcon(QIcon(search_path))
            self.fetch_btn.setIconSize(QSize(20, 20))

    def _on_video_info_fetched(self, info):
        self.current_video_info = info

        # Cache formats for advanced panel (no extra API calls)
        self.cached_formats = info.get('formats', [])
        duration = info.get('duration', 0)

        # Update video info panel
        self.video_info_panel.update_info(info)
        self.video_info_panel.show()

        # Show quality selector
        self._show_quality_selector(self.cached_formats)

        # Load streams into advanced panel from cached data
        self.advanced_panel.load_streams(self.cached_formats, duration)

        # Show right panel
        self.right_panel.show()

        self._reset_fetch_btn()
        self.statusBar().showMessage("Video information loaded successfully")
        log.info("Video info loaded: %s", info.get('title', 'Unknown'))

    def _on_fetch_error(self, error_msg):
        self._reset_fetch_btn()
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
        # Connect resolution_changed to update advanced panel
        self.quality_selector.resolution_changed.connect(
            self.advanced_panel.filter_by_resolution
        )
        self.quality_container.addWidget(self.quality_selector)

    def _toggle_advanced(self):
        is_on = self.advanced_toggle_btn.isChecked()
        self.advanced_panel.setVisible(is_on)
        self.settings.set_advanced_mode(is_on)
        arrow = "▲" if is_on else "▼"
        self.advanced_toggle_btn.setText(f"  Advanced Download {arrow}")
        if is_on and self.quality_selector:
            # Trigger initial population based on current selection
            try:
                height = int(self.quality_selector.get_selected_quality())
            except (ValueError, TypeError):
                height = 0
            self.advanced_panel.filter_by_resolution(height)

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
        output_path = self.download_path

        # Check audio-only from advanced panel (if open), otherwise False
        advanced_open = self.advanced_toggle_btn.isChecked() and self.advanced_panel.isVisible()
        audio_only = advanced_open and self.advanced_panel.is_audio_only()

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
        file_type = "YouTube • MP3" if audio_only else "YouTube • MP4"
        dl_card = self.downloads_page.add_active_download(dl_id, title[:50], file_type)

        # Determine download mode
        if audio_only and advanced_open:
            # Audio-only with specific format from advanced panel
            aud_id = self.advanced_panel.get_selected_audio_format_id()
            if aud_id:
                self.download_thread = AudioDownloadThread(
                    url, aud_id, output_path, self.downloader
                )
            else:
                # Fallback to simple audio download
                self.download_thread = DownloadThread(
                    url, 'auto', output_path, True, self.downloader
                )
        elif advanced_open and not audio_only:
            vid_id, aud_id = self.advanced_panel.get_selected_format_ids()
            if vid_id and aud_id:
                quality_tag = self.advanced_panel.get_quality_tag()
                self.download_thread = AdvancedDownloadThread(
                    url, vid_id, aud_id, output_path, quality_tag, self.downloader
                )
            else:
                quality = self.quality_selector.get_selected_quality()
                self.download_thread = DownloadThread(
                    url, quality, output_path, False, self.downloader
                )
        else:
            quality = self.quality_selector.get_selected_quality()
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

        # Wire cancel button
        def _cancel_download():
            log.info("User cancelled download for: %s", title[:50])
            if self.download_thread and self.download_thread.isRunning():
                self.download_thread.terminate()
                self.download_thread.wait(2000)
            progress_widget.download_failed("Cancelled by user")
            self.statusBar().showMessage("Download cancelled")

        progress_widget.cancel_requested.connect(_cancel_download)
        self.download_thread.start()

        mode_str = "advanced" if (advanced_open and not audio_only) else "simple"
        log.info("Download started (%s) for: %s", mode_str, title[:50])
        self.statusBar().showMessage("Download started...")

    def closeEvent(self, event):
        # Save advanced download preferences
        if hasattr(self, 'advanced_panel'):
            prefs = self.advanced_panel.get_preferences()
            self.settings.set_preferred_video_codec(prefs['video_codec'])
            self.settings.set_preferred_audio_codec(prefs['audio_codec'])
            self.settings.set_preferred_bitrate_mode(prefs['bitrate_mode'])
            self.settings.set_preferred_bitrate_custom(prefs['custom_bitrate'])
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


class AdvancedDownloadThread(QThread):
    """Download thread using exact format IDs from Advanced mode."""
    progress_updated = Signal(int, str)
    download_completed = Signal()
    download_failed = Signal(str)

    def __init__(self, url, video_format_id, audio_format_id, output_path,
                 quality_tag, downloader):
        super().__init__()
        self.url = url
        self.video_format_id = video_format_id
        self.audio_format_id = audio_format_id
        self.output_path = output_path
        self.quality_tag = quality_tag
        self.downloader = downloader

    def run(self):
        def progress_callback(progress, status):
            self.progress_updated.emit(int(progress), status)

        try:
            result = self.downloader.download_video_advanced(
                self.url, self.video_format_id, self.audio_format_id,
                self.output_path, self.quality_tag, progress_callback
            )
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


class AudioDownloadThread(QThread):
    """Download thread for audio-only using exact format ID from Advanced mode."""
    progress_updated = Signal(int, str)
    download_completed = Signal()
    download_failed = Signal(str)

    def __init__(self, url, audio_format_id, output_path, downloader):
        super().__init__()
        self.url = url
        self.audio_format_id = audio_format_id
        self.output_path = output_path
        self.downloader = downloader

    def run(self):
        def progress_callback(progress, status):
            self.progress_updated.emit(int(progress), status)

        try:
            result = self.downloader.download_audio_advanced(
                self.url, self.audio_format_id, self.output_path,
                quality_tag="audio", progress_callback=progress_callback
            )
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

class OAuthLoginThread(QThread):
    instructions_received = Signal(str, str)
    login_completed = Signal()

    def __init__(self, downloader):
        super().__init__()
        self.downloader = downloader

    def run(self):
        def on_instr(url, code):
            self.instructions_received.emit(url, code)

        success = self.downloader.start_oauth_login(on_instr)
        if success:
            self.login_completed.emit()


def main():
    if sys.platform == "win32":
        import ctypes
        myappid = "downloaderpro.app.1.0"
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("Downloader PRO")
    app.setOrganizationName("DownloaderPRO")

    # Set app-wide icon (important for Taskbar)
    icon_path = get_resource_path("assets/logo.ico")
    if Path(icon_path).exists():
        app.setWindowIcon(QIcon(icon_path))

    window = YouTubeDownloaderApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
