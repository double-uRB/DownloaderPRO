"""
Downloads management page for Downloader PRO.
Shows summary stats, active downloads with progress, and completed items.
"""

import os
import subprocess
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QProgressBar, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon
from utils import get_resource_path


class StatCard(QWidget):
    """A compact stat card (Active Downloads, Avg Speed, Storage)."""

    def __init__(self, icon_name, label, value, unit="", parent=None):
        super().__init__(parent)
        self.setObjectName("surface_card")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(80)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # Icon container — use SVG if available
        icon_label = QLabel()
        icon_path = get_resource_path(f"assets/icons/{icon_name}.svg")
        if Path(icon_path).exists():
            icon_label.setPixmap(QIcon(icon_path).pixmap(24, 24))
        else:
            icon_label.setText(icon_name[:2])
        icon_label.setFixedSize(44, 44)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background-color: rgba(76, 215, 246, 0.1); border-radius: 10px;")
        layout.addWidget(icon_label)

        # Text column
        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        stat_label = QLabel(label.upper())
        stat_label.setObjectName("stat_label")
        stat_label.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        text_col.addWidget(stat_label)

        value_row = QHBoxLayout()
        value_row.setSpacing(4)

        self.value_label = QLabel(str(value))
        self.value_label.setObjectName("stat_value")
        self.value_label.setFont(QFont("Segoe UI", 18, QFont.Weight.ExtraBold))
        value_row.addWidget(self.value_label)

        if unit:
            unit_label = QLabel(unit)
            unit_label.setObjectName("section_subtitle")
            unit_label.setFont(QFont("Segoe UI", 10))
            value_row.addWidget(unit_label)

        value_row.addStretch()
        text_col.addLayout(value_row)

        layout.addLayout(text_col)

    def set_value(self, value, unit=""):
        self.value_label.setText(str(value))


class DownloadItemCard(QWidget):
    """A single active download item with progress bar."""

    pause_clicked = Signal(str)
    cancel_clicked = Signal(str)

    def __init__(self, video_id: str, title: str, quality: str, parent=None):
        super().__init__(parent)
        self.video_id = video_id
        self.setObjectName("download_card")
        self.setMinimumHeight(100)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)
        
        # Thumbnail placeholder
        self.thumb = QLabel()
        video_icon_path = get_resource_path("assets/icons/video.svg")
        if Path(video_icon_path).exists():
            self.thumb.setPixmap(QIcon(video_icon_path).pixmap(32, 32))
        else:
            self.thumb.setText("V")
        self.thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb.setFixedSize(120, 68)
        self.thumb.setStyleSheet("background-color: #1a1e2d; border-radius: 6px;")
        layout.addWidget(self.thumb)

        # Info column
        info_col = QVBoxLayout()
        info_col.setSpacing(6)

        # Title row
        title_row = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title_row.addWidget(title_label)
        title_row.addStretch()

        self.speed_label = QLabel("")
        self.speed_label.setObjectName("speed_label")
        self.speed_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_row.addWidget(self.speed_label)

        info_col.addLayout(title_row)

        # Source info
        source_row = QHBoxLayout()
        source_label = QLabel(quality)
        source_label.setObjectName("section_subtitle")
        source_label.setFont(QFont("Segoe UI", 10))
        source_row.addWidget(source_label)
        source_row.addStretch()

        self.eta_label = QLabel("")
        self.eta_label.setObjectName("section_subtitle")
        self.eta_label.setFont(QFont("Segoe UI", 9))
        source_row.addWidget(self.eta_label)

        info_col.addLayout(source_row)

        # Progress row
        progress_row = QHBoxLayout()
        progress_row.setSpacing(8)

        self.bytes_label = QLabel("")
        self.bytes_label.setObjectName("section_subtitle")
        self.bytes_label.setFont(QFont("Segoe UI", 9))
        progress_row.addWidget(self.bytes_label)

        progress_row.addStretch()

        self.percent_label = QLabel("0%")
        self.percent_label.setObjectName("section_subtitle")
        self.percent_label.setFont(QFont("Segoe UI", 9))
        progress_row.addWidget(self.percent_label)

        info_col.addLayout(progress_row)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        info_col.addWidget(self.progress_bar)

        layout.addLayout(info_col, stretch=1)

        # Action buttons
        btn_layout = QVBoxLayout()
        
        self.pause_btn = QPushButton()
        pause_icon_path = get_resource_path("assets/icons/pause.svg")
        if Path(pause_icon_path).exists():
            self.pause_btn.setIcon(QIcon(pause_icon_path))
            self.pause_btn.setIconSize(QSize(14, 14))
        else:
            self.pause_btn.setText("||")
        self.pause_btn.setFixedSize(32, 32)
        self.pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pause_btn.setToolTip("Pause/Resume")
        self.pause_btn.clicked.connect(lambda: self.pause_clicked.emit(self.video_id))
        btn_layout.addWidget(self.pause_btn)
        
        self.cancel_btn = QPushButton()
        x_icon_path = get_resource_path("assets/icons/x.svg")
        if Path(x_icon_path).exists():
            self.cancel_btn.setIcon(QIcon(x_icon_path))
            self.cancel_btn.setIconSize(QSize(14, 14))
        else:
            self.cancel_btn.setText("X")
        self.cancel_btn.setFixedSize(32, 32)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setToolTip("Cancel")
        self.cancel_btn.setStyleSheet("color: #ffb4ab; border-color: rgba(255, 180, 171, 0.2);")
        self.cancel_btn.clicked.connect(lambda: self.cancel_clicked.emit(self.video_id))
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

    def update_progress(self, progress, status):
        self.progress_bar.setValue(int(progress))
        self.percent_label.setText(f"{int(progress)}%")
        self.speed_label.setText(status)


class CompletedItemCard(QWidget):
    """A compact completed download item with working Open Folder and Play buttons."""

    def __init__(self, title, file_size, completion_time, file_path="", parent=None):
        super().__init__(parent)
        self._file_path = file_path
        self.setObjectName("surface_card_low")
        self.setMinimumHeight(64)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(14)

        # Icon
        icon = QLabel()
        file_icon_path = get_resource_path("assets/icons/file.svg")
        if Path(file_icon_path).exists():
            icon.setPixmap(QIcon(file_icon_path).pixmap(22, 22))
        else:
            icon.setText("📄")
            icon.setFont(QFont("Segoe UI", 18))
        icon.setFixedSize(42, 42)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("background-color: rgba(76, 215, 246, 0.08); border-radius: 8px;")
        layout.addWidget(icon)

        # Info
        info_col = QVBoxLayout()
        info_col.setSpacing(2)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        info_col.addWidget(title_label)

        detail_label = QLabel(f"{file_size} • {completion_time}")
        detail_label.setObjectName("section_subtitle")
        detail_label.setFont(QFont("Segoe UI", 9))
        info_col.addWidget(detail_label)

        layout.addLayout(info_col, stretch=1)

        # Actions — Open Folder
        open_btn = QPushButton()
        folder_icon_path = get_resource_path("assets/icons/folder.svg")
        if Path(folder_icon_path).exists():
            open_btn.setIcon(QIcon(folder_icon_path))
            open_btn.setIconSize(QSize(16, 16))
        open_btn.setText("  Open Folder")
        open_btn.setFixedHeight(30)
        open_btn.setFont(QFont("Segoe UI", 10))
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.clicked.connect(self._open_folder)
        layout.addWidget(open_btn)

        # Actions — Play
        play_btn = QPushButton()
        video_icon_path = get_resource_path("assets/icons/video.svg")
        if Path(video_icon_path).exists():
            play_btn.setIcon(QIcon(video_icon_path))
            play_btn.setIconSize(QSize(16, 16))
        play_btn.setText("  Play")
        play_btn.setObjectName("primary_button")
        play_btn.setFixedHeight(30)
        play_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        play_btn.clicked.connect(self._play_file)
        layout.addWidget(play_btn)

    def _open_folder(self):
        """Open the file's containing folder in the system file explorer."""
        if self._file_path and os.path.exists(self._file_path):
            folder = os.path.dirname(self._file_path)
            # On Windows, select the file in Explorer
            subprocess.Popen(f'explorer /select,"{self._file_path}"')
        elif self._file_path:
            # Try opening the parent folder at least
            folder = os.path.dirname(self._file_path)
            if os.path.exists(folder):
                os.startfile(folder)

    def _play_file(self):
        """Open the downloaded file with the default system player."""
        if self._file_path and os.path.exists(self._file_path):
            os.startfile(self._file_path)


class DownloadsPage(QWidget):
    """Full downloads management page."""

    def __init__(self, download_path="", parent=None):
        super().__init__(parent)
        self._download_cards: dict[str, DownloadItemCard] = {}
        self._download_path = download_path  # Default download folder
        self._setup_ui()

    def _setup_ui(self):
        # Scroll area wrapper
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self.main_layout = QVBoxLayout(content)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(20)

        # ── Summary Stats ──
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self.active_stat = StatCard("refresh", "Active Downloads", "0")
        stats_layout.addWidget(self.active_stat)

        self.speed_stat = StatCard("zap", "Current Speed", "0 B/s")
        stats_layout.addWidget(self.speed_stat)

        self.storage_stat = StatCard("hard-drive", "Free Space", "Calculating...")
        stats_layout.addWidget(self.storage_stat)

        self.main_layout.addLayout(stats_layout)

        # ── Filter tabs ──
        filter_row = QHBoxLayout()
        filter_row.setSpacing(20)

        filters = ["All", "Downloading", "Completed", "Paused"]
        self.filter_buttons = []
        for i, f in enumerate(filters):
            btn = QPushButton(f)
            btn.setObjectName("filter_button")
            btn.setProperty("active", "true" if i == 0 else "false")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont("Segoe UI", 12))
            btn.clicked.connect(lambda checked, idx=i: self._on_filter_click(idx))
            self.filter_buttons.append(btn)
            filter_row.addWidget(btn)

        filter_row.addStretch()
        self.main_layout.addLayout(filter_row)

        # Separator
        sep = QWidget()
        sep.setObjectName("separator_line")
        sep.setFixedHeight(1)
        self.main_layout.addWidget(sep)

        # ── Active Tasks section ──
        active_label = QLabel("ACTIVE TASKS")
        active_label.setObjectName("stat_label")
        active_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.main_layout.addWidget(active_label)

        self.active_downloads_layout = QVBoxLayout()
        self.active_downloads_layout.setSpacing(8)

        # Placeholder for no downloads
        self.no_downloads_label = QLabel("No active downloads. Paste a URL on the Dashboard to start.")
        self.no_downloads_label.setObjectName("section_subtitle")
        self.no_downloads_label.setFont(QFont("Segoe UI", 12))
        self.no_downloads_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_downloads_label.setFixedHeight(80)
        self.active_downloads_layout.addWidget(self.no_downloads_label)

        self.main_layout.addLayout(self.active_downloads_layout)

        # ── Completed section ──
        completed_label = QLabel("RECENT COMPLETED")
        completed_label.setObjectName("stat_label")
        completed_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.main_layout.addWidget(completed_label)

        self.completed_layout = QVBoxLayout()
        self.completed_layout.setSpacing(6)

        no_completed = QLabel("No completed downloads yet.")
        no_completed.setObjectName("section_subtitle")
        no_completed.setFont(QFont("Segoe UI", 11))
        no_completed.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_completed.setFixedHeight(50)
        self.completed_layout.addWidget(no_completed)

        self.main_layout.addLayout(self.completed_layout)
        self.main_layout.addStretch()

        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def set_download_path(self, path):
        """Update the default download path."""
        self._download_path = path

    def _on_filter_click(self, idx):
        for i, btn in enumerate(self.filter_buttons):
            btn.setProperty("active", "true" if i == idx else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def add_active_download(self, download_id, title, source_info="YouTube • MP4"):
        """Add a new active download card."""
        self.no_downloads_label.setVisible(False)
        card = DownloadItemCard(download_id, title, source_info)
        self._download_cards[download_id] = card
        self.active_downloads_layout.addWidget(card)
        self.active_stat.set_value(str(len(self._download_cards)))
        return card

    def update_download_progress(self, download_id, progress, status):
        """Update an active download's progress."""
        if download_id in self._download_cards:
            self._download_cards[download_id].update_progress(progress, status)

    def complete_download(self, download_id, title, file_size, file_path=""):
        """Move a download from active to completed."""
        if download_id in self._download_cards:
            card = self._download_cards.pop(download_id)
            card.setParent(None)
            card.deleteLater()

        # If no file_path, try to find the file in the download directory
        actual_path = file_path
        if not actual_path and self._download_path:
            # Look for the most recently created file matching the title
            try:
                dl_dir = Path(self._download_path)
                if dl_dir.exists():
                    # Get files sorted by modification time (newest first)
                    files = sorted(dl_dir.iterdir(),
                                   key=lambda f: f.stat().st_mtime, reverse=True)
                    for f in files[:10]:  # Check last 10 files
                        if f.is_file() and title[:20].lower() in f.name.lower():
                            actual_path = str(f)
                            file_size = self._format_file_size(f.stat().st_size)
                            break
                    # If no title match, just use the newest file
                    if not actual_path and files:
                        newest = files[0]
                        if newest.is_file():
                            actual_path = str(newest)
                            file_size = self._format_file_size(newest.stat().st_size)
            except Exception:
                pass

        completed = CompletedItemCard(title, file_size, "Just now", file_path=actual_path)
        self.completed_layout.insertWidget(0, completed)

        if not self._download_cards:
            self.no_downloads_label.setVisible(True)

        self.active_stat.set_value(str(len(self._download_cards)))

    @staticmethod
    def _format_file_size(size_bytes):
        if size_bytes >= 1_073_741_824:
            return f"{size_bytes / 1_073_741_824:.1f} GB"
        elif size_bytes >= 1_048_576:
            return f"{size_bytes / 1_048_576:.1f} MB"
        elif size_bytes >= 1024:
            return f"{size_bytes / 1024:.0f} KB"
        return f"{size_bytes} B"
