"""
Downloads management page for Downloader PRO.
Shows summary stats, active downloads with progress, and completed items.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QProgressBar, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class StatCard(QWidget):
    """A compact stat card (Active Downloads, Avg Speed, Storage)."""

    def __init__(self, icon, label, value, unit="", parent=None):
        super().__init__(parent)
        self.setObjectName("surface_card")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(80)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # Icon container
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI", 20))
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

    def __init__(self, download_id, title, source_info, parent=None):
        super().__init__(parent)
        self.download_id = download_id
        self.setObjectName("glass_panel")
        self.setMinimumHeight(90)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # Icon / thumbnail placeholder
        thumb = QLabel("📹")
        thumb.setFont(QFont("Segoe UI", 24))
        thumb.setFixedSize(64, 54)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb.setStyleSheet("background-color: #060e20; border-radius: 8px;")
        layout.addWidget(thumb)

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
        source_label = QLabel(source_info)
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
        btn_col = QVBoxLayout()
        btn_col.setSpacing(4)

        pause_btn = QPushButton("⏸")
        pause_btn.setFixedSize(38, 38)
        pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pause_btn.clicked.connect(lambda: self.pause_clicked.emit(self.download_id))
        btn_col.addWidget(pause_btn)

        cancel_btn = QPushButton("✕")
        cancel_btn.setFixedSize(38, 38)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("color: #ffb4ab;")
        cancel_btn.clicked.connect(lambda: self.cancel_clicked.emit(self.download_id))
        btn_col.addWidget(cancel_btn)

        layout.addLayout(btn_col)

    def update_progress(self, progress, status):
        self.progress_bar.setValue(int(progress))
        self.percent_label.setText(f"{int(progress)}%")
        self.speed_label.setText(status)


class CompletedItemCard(QWidget):
    """A compact completed download item."""

    def __init__(self, title, file_size, completion_time, parent=None):
        super().__init__(parent)
        self.setObjectName("surface_card_low")
        self.setFixedHeight(64)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(14)

        # Icon
        icon = QLabel("📄")
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

        # Actions
        open_btn = QPushButton("Open Folder")
        open_btn.setFixedHeight(30)
        open_btn.setFont(QFont("Segoe UI", 10))
        layout.addWidget(open_btn)

        play_btn = QPushButton("Play")
        play_btn.setObjectName("primary_button")
        play_btn.setFixedHeight(30)
        play_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(play_btn)


class DownloadsPage(QWidget):
    """Full downloads management page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._download_cards: dict[str, DownloadItemCard] = {}
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
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)

        self.active_stat = StatCard("🔄", "Active Downloads", "0", "/ 0 total")
        stats_row.addWidget(self.active_stat)

        self.speed_stat = StatCard("⚡", "Avg. Speed", "—", "MB/s")
        stats_row.addWidget(self.speed_stat)

        self.storage_stat = StatCard("💾", "Storage Remaining", "—", "GB")
        stats_row.addWidget(self.storage_stat)

        self.main_layout.addLayout(stats_row)

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

    def complete_download(self, download_id, title, file_size):
        """Move a download from active to completed."""
        if download_id in self._download_cards:
            card = self._download_cards.pop(download_id)
            card.setParent(None)
            card.deleteLater()

        completed = CompletedItemCard(title, file_size, "Just now")
        self.completed_layout.insertWidget(0, completed)

        if not self._download_cards:
            self.no_downloads_label.setVisible(True)

        self.active_stat.set_value(str(len(self._download_cards)))
