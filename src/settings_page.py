"""
Settings page for Downloader PRO.
Storage & Location, Task Management, Network Optimization, and Theme selector.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox, QSlider, QComboBox, QFileDialog,
    QScrollArea, QFrame, QSizePolicy, QButtonGroup
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon
from pathlib import Path


class SettingsPage(QWidget):
    """Full settings page matching the Stitch design."""

    theme_changed = Signal(str)
    settings_changed = Signal(dict)

    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self._setup_ui()
        self._load_current_settings()

    def _create_icon_label(self, emoji: str, icon_name: str, size: int = 24) -> QLabel:
        label = QLabel()
        p = Path(__file__).parent.parent / "assets" / "icons" / f"{icon_name}.svg"
        if p.exists():
            label.setPixmap(QIcon(str(p)).pixmap(size, size))
        else:
            label.setText(emoji)
            label.setFont(QFont("Segoe UI", size - 8))
        return label

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(28, 28, 28, 80)
        main_layout.setSpacing(24)

        # ── Page header ──
        header_label = QLabel("Download Settings")
        header_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Black))
        main_layout.addWidget(header_label)

        desc_label = QLabel("Configure your data engine and automation parameters.\nThese settings affect all active and future download threads.")
        desc_label.setObjectName("section_subtitle")
        desc_label.setFont(QFont("Segoe UI", 12))
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)

        # ── Two-column grid ──
        columns = QHBoxLayout()
        columns.setSpacing(24)

        # LEFT COLUMN
        left = QVBoxLayout()
        left.setSpacing(20)

        # ── Storage & Location ──
        storage_card = self._create_card()
        storage_layout = QVBoxLayout(storage_card)
        storage_layout.setContentsMargins(24, 20, 24, 20)
        storage_layout.setSpacing(16)

        storage_title_row = QHBoxLayout()
        storage_icon = self._create_icon_label("📁", "folder")
        storage_title_row.addWidget(storage_icon)
        storage_title = QLabel("Storage & Location")
        storage_title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        storage_title_row.addWidget(storage_title)
        storage_title_row.addStretch()
        storage_layout.addLayout(storage_title_row)

        # Download path
        path_label = QLabel("DEFAULT DOWNLOAD LOCATION")
        path_label.setObjectName("stat_label")
        path_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        storage_layout.addWidget(path_label)

        path_row = QHBoxLayout()
        path_row.setSpacing(10)
        self.path_input = QLineEdit()
        self.path_input.setMinimumHeight(36)
        self.path_input.setFont(QFont("Consolas", 11))
        self.path_input.setReadOnly(True)
        path_row.addWidget(self.path_input)

        change_btn = QPushButton("Change")
        change_btn.setMinimumHeight(36)
        change_btn.setFixedWidth(90)
        change_btn.clicked.connect(self._browse_folder)
        path_row.addWidget(change_btn)
        storage_layout.addLayout(path_row)

        # Filename pattern
        pattern_label = QLabel("FILENAME PATTERN")
        pattern_label.setObjectName("stat_label")
        pattern_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        storage_layout.addWidget(pattern_label)

        self.pattern_input = QLineEdit("{date}_{filename}.{ext}")
        self.pattern_input.setMinimumHeight(36)
        self.pattern_input.setFont(QFont("Consolas", 11))
        storage_layout.addWidget(self.pattern_input)

        hint = QLabel("Available tags: {date}, {time}, {filename}, {ext}, {id}")
        hint.setObjectName("section_subtitle")
        hint.setFont(QFont("Segoe UI", 9))
        hint.setStyleSheet("font-style: italic;")
        storage_layout.addWidget(hint)

        left.addWidget(storage_card)

        # ── Task Management ──
        task_card = self._create_card()
        task_card.setStyleSheet(task_card.styleSheet() + "border-left: 4px solid #571bc1;")
        task_layout = QVBoxLayout(task_card)
        task_layout.setContentsMargins(24, 20, 24, 20)
        task_layout.setSpacing(16)

        task_title_row = QHBoxLayout()
        task_icon = self._create_icon_label("📋", "clipboard")
        task_title_row.addWidget(task_icon)
        task_title = QLabel("Task Management")
        task_title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        task_title_row.addWidget(task_title)
        task_title_row.addStretch()
        task_layout.addLayout(task_title_row)

        # Auto-resume toggle
        resume_row = QHBoxLayout()
        resume_col = QVBoxLayout()
        resume_col.setSpacing(2)
        resume_label = QLabel("Auto-resume interrupted tasks")
        resume_label.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        resume_col.addWidget(resume_label)
        resume_desc = QLabel("Automatically restarts failed downloads on app launch.")
        resume_desc.setObjectName("section_subtitle")
        resume_desc.setFont(QFont("Segoe UI", 10))
        resume_col.addWidget(resume_desc)
        resume_row.addLayout(resume_col)
        resume_row.addStretch()

        self.auto_resume_cb = QCheckBox()
        self.auto_resume_cb.setChecked(True)
        resume_row.addWidget(self.auto_resume_cb)

        task_layout.addLayout(resume_row)

        # Concurrent downloads slider
        concurrent_header = QHBoxLayout()
        concurrent_label = QLabel("Maximum concurrent downloads")
        concurrent_label.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        concurrent_header.addWidget(concurrent_label)
        concurrent_header.addStretch()

        self.concurrent_value = QLabel("5 Tasks")
        self.concurrent_value.setObjectName("badge_primary")
        self.concurrent_value.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        concurrent_header.addWidget(self.concurrent_value)

        task_layout.addLayout(concurrent_header)

        self.concurrent_slider = QSlider(Qt.Orientation.Horizontal)
        self.concurrent_slider.setMinimum(1)
        self.concurrent_slider.setMaximum(10)
        self.concurrent_slider.setValue(5)
        self.concurrent_slider.valueChanged.connect(
            lambda v: self.concurrent_value.setText(f"{v} Tasks")
        )
        task_layout.addWidget(self.concurrent_slider)

        range_labels = QHBoxLayout()
        range_labels.addWidget(QLabel("1"))
        range_labels.addStretch()
        range_labels.addWidget(QLabel("10"))
        task_layout.addLayout(range_labels)

        left.addWidget(task_card)

        # ── Network Optimization ──
        network_card = self._create_card()
        network_layout = QVBoxLayout(network_card)
        network_layout.setContentsMargins(24, 20, 24, 20)
        network_layout.setSpacing(16)

        net_title_row = QHBoxLayout()
        net_icon = self._create_icon_label("⚡", "zap")
        net_title_row.addWidget(net_icon)
        net_title = QLabel("Network Optimization")
        net_title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        net_title_row.addWidget(net_title)
        net_title_row.addStretch()
        network_layout.addLayout(net_title_row)

        net_grid = QHBoxLayout()
        net_grid.setSpacing(16)

        # Speed limit
        speed_col = QVBoxLayout()
        speed_col.setSpacing(6)
        speed_label = QLabel("DOWNLOAD SPEED LIMIT")
        speed_label.setObjectName("stat_label")
        speed_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        speed_col.addWidget(speed_label)

        speed_row = QHBoxLayout()
        self.speed_limit_input = QLineEdit("0")
        self.speed_limit_input.setMinimumHeight(36)
        self.speed_limit_input.setFont(QFont("Segoe UI", 12))
        speed_row.addWidget(self.speed_limit_input)

        kb_label = QLabel("KB/s")
        kb_label.setObjectName("section_subtitle")
        kb_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        speed_row.addWidget(kb_label)
        speed_col.addLayout(speed_row)

        hint2 = QLabel("Set to 0 for unlimited bandwidth.")
        hint2.setObjectName("section_subtitle")
        hint2.setFont(QFont("Segoe UI", 9))
        hint2.setStyleSheet("font-style: italic;")
        speed_col.addWidget(hint2)

        net_grid.addLayout(speed_col)

        # Thread intensity
        thread_col = QVBoxLayout()
        thread_col.setSpacing(6)
        thread_label = QLabel("MULTI-THREAD INTENSITY")
        thread_label.setObjectName("stat_label")
        thread_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        thread_col.addWidget(thread_label)

        self.thread_combo = QComboBox()
        self.thread_combo.setMinimumHeight(36)
        self.thread_combo.addItems([
            "Low - 2 Threads",
            "Medium - 4 Threads",
            "High - 8 Threads",
            "Extreme - 16 Threads",
        ])
        self.thread_combo.setCurrentIndex(2)
        thread_col.addWidget(self.thread_combo)

        net_grid.addLayout(thread_col)
        network_layout.addLayout(net_grid)

        left.addWidget(network_card)
        left.addStretch()

        columns.addLayout(left, stretch=2)

        # RIGHT COLUMN
        right = QVBoxLayout()
        right.setSpacing(20)

        # ── Theme Selector ──
        theme_card = self._create_card()
        theme_layout = QVBoxLayout(theme_card)
        theme_layout.setContentsMargins(24, 20, 24, 20)
        theme_layout.setSpacing(16)

        theme_title = QLabel("INTERFACE PERSONALITY")
        theme_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        theme_layout.addWidget(theme_title)

        theme_grid = QHBoxLayout()
        theme_grid.setSpacing(10)

        self.theme_buttons = {}
        icon_map = {"light": "sun", "dark": "moon", "auto": "refresh"}
        for icon, label, key in [("☀️", "Light", "light"), ("🌙", "Dark", "dark"), ("🔄", "System", "auto")]:
            btn = QPushButton(f"  {label}")
            p = Path(__file__).parent.parent / "assets" / "icons" / f"{icon_map[key]}.svg"
            if p.exists():
                btn.setIcon(QIcon(str(p)))
                btn.setIconSize(QSize(20, 20))
            btn.setMinimumHeight(64)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, k=key: self._on_theme_selected(k))
            self.theme_buttons[key] = btn
            theme_grid.addWidget(btn)

        theme_grid.addStretch()
        theme_layout.addLayout(theme_grid)

        right.addWidget(theme_card)

        # ── Engine Status Widget ──
        engine_card = self._create_card()
        engine_card.setStyleSheet(engine_card.styleSheet() + "border: 1px solid rgba(76, 215, 246, 0.1);")
        engine_layout = QVBoxLayout(engine_card)
        engine_layout.setContentsMargins(24, 20, 24, 20)
        engine_layout.setSpacing(8)

        engine_header = QHBoxLayout()
        engine_title = QLabel("ENGINE STATUS")
        engine_title.setStyleSheet("color: #4cd7f6; font-weight: 800; font-size: 10px; letter-spacing: 2px;")
        engine_header.addWidget(engine_title)
        engine_header.addStretch()
        status_dot = QLabel("●")
        status_dot.setStyleSheet("color: #4cd7f6; font-size: 8px;")
        engine_header.addWidget(status_dot)
        engine_layout.addLayout(engine_header)

        stable_label = QLabel("Stable Core")
        stable_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Black))
        engine_layout.addWidget(stable_label)

        sync_label = QLabel("Download engine synchronized")
        sync_label.setObjectName("section_subtitle")
        sync_label.setFont(QFont("Segoe UI", 10))
        engine_layout.addWidget(sync_label)

        # Mini bar chart
        chart_row = QHBoxLayout()
        chart_row.setSpacing(2)
        bar_heights = [40, 60, 30, 80, 55, 95, 45, 20]
        for h in bar_heights:
            bar = QWidget()
            bar.setFixedHeight(h)
            bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            opacity = int(h * 0.6 + 10)
            bar.setStyleSheet(f"background-color: rgba(76, 215, 246, {min(opacity, 150)}); border-radius: 2px;")
            chart_row.addWidget(bar)
        engine_layout.addLayout(chart_row)

        engine_layout.addSpacing(4)

        metrics = QHBoxLayout()
        temp = QLabel("TEMP: 32°C")
        temp.setObjectName("section_subtitle")
        temp.setFont(QFont("Consolas", 9))
        metrics.addWidget(temp)
        metrics.addStretch()
        latency = QLabel("LATENCY: 14MS")
        latency.setObjectName("section_subtitle")
        latency.setFont(QFont("Consolas", 9))
        metrics.addWidget(latency)
        engine_layout.addLayout(metrics)

        right.addWidget(engine_card)
        right.addStretch()

        columns.addLayout(right, stretch=1)
        main_layout.addLayout(columns)

        scroll.setWidget(content)

        # ── Footer bar ──
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(scroll)

        footer = QWidget()
        footer.setObjectName("glass_panel")
        footer.setMinimumHeight(60)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(28, 10, 28, 10)

        unsaved_icon = None
        p = Path(__file__).parent.parent / "assets" / "icons" / "info.svg"
        if p.exists():
            unsaved_icon = QLabel()
            unsaved_icon.setPixmap(QIcon(str(p)).pixmap(18, 18))
            footer_layout.addWidget(unsaved_icon)
            
        unsaved_label = QLabel(" Unsaved changes detected" if unsaved_icon else "ℹ️  Unsaved changes detected")
        unsaved_label.setObjectName("section_subtitle")
        unsaved_label.setFont(QFont("Segoe UI", 11))
        footer_layout.addWidget(unsaved_label)

        footer_layout.addStretch()

        discard_btn = QPushButton("Discard Changes")
        discard_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        discard_btn.clicked.connect(self._load_current_settings)
        footer_layout.addWidget(discard_btn)

        save_btn = QPushButton("Save Configuration")
        save_btn.setObjectName("primary_button")
        save_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        save_btn.clicked.connect(self._save_settings)
        footer_layout.addWidget(save_btn)

        outer.addWidget(footer)

    def _create_card(self):
        card = QWidget()
        card.setObjectName("surface_card_low")
        return card

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Download Folder", self.path_input.text()
        )
        if folder:
            self.path_input.setText(folder)

    def _on_theme_selected(self, theme_key):
        for key, btn in self.theme_buttons.items():
            is_active = (key == theme_key)
            btn.setChecked(is_active)
            if is_active:
                btn.setStyleSheet("border: 2px solid #4cd7f6; background-color: #222a3d;")
            else:
                btn.setStyleSheet("")
        self.theme_changed.emit(theme_key)

    def _load_current_settings(self):
        self.path_input.setText(self.settings.get_download_path())
        current_theme = self.settings.get_theme()
        self._on_theme_selected(current_theme)

        # Load extended settings
        settings = self.settings.settings
        self.pattern_input.setText(settings.get("filename_pattern", "{date}_{filename}.{ext}"))
        self.auto_resume_cb.setChecked(settings.get("auto_resume", True))
        self.concurrent_slider.setValue(settings.get("max_concurrent", 5))
        self.speed_limit_input.setText(str(settings.get("speed_limit", 0)))

        intensity = settings.get("thread_intensity", "high")
        intensity_map = {"low": 0, "medium": 1, "high": 2, "extreme": 3}
        self.thread_combo.setCurrentIndex(intensity_map.get(intensity, 2))

    def _save_settings(self):
        self.settings.set_download_path(self.path_input.text())

        intensity_map = {0: "low", 1: "medium", 2: "high", 3: "extreme"}

        self.settings.settings.update({
            "filename_pattern": self.pattern_input.text(),
            "auto_resume": self.auto_resume_cb.isChecked(),
            "max_concurrent": self.concurrent_slider.value(),
            "speed_limit": int(self.speed_limit_input.text() or 0),
            "thread_intensity": intensity_map.get(self.thread_combo.currentIndex(), "high"),
        })
        self.settings.save_settings()
