"""
Sidebar navigation widget for Downloader PRO.
Fixed-width vertical panel with app branding, nav items, and CTA button.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from pathlib import Path
from utils import get_resource_path


class NavButton(QPushButton):
    """A sidebar navigation button with icon + label."""

    def __init__(self, icon_name: str, label: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.label_text = label
        self.subtitle_text = subtitle
        self.setObjectName("nav_item")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(48)
        
        # Load SVG icon
        icon_path = get_resource_path(f"assets/icons/{icon_name}.svg")
        from PySide6.QtGui import QIcon
        from PySide6.QtCore import QSize
        if Path(icon_path).exists():
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(20, 20))
            
        self._update_text()

    def _update_text(self):
        text = f"  {self.label_text}"
        self.setText(text)
        self.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))

    def set_active(self, active: bool):
        self.setChecked(active)
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


class Sidebar(QWidget):
    """Collapsible sidebar with navigation and branding."""

    page_changed = Signal(str)

    PAGES = [
        ("home", "Dashboard",  "dashboard"),
        ("download", "Downloads",  "downloads"),
        ("settings", "Settings",   "settings"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setMinimumWidth(220)
        self.setMaximumWidth(280)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)
        self.nav_buttons: dict[str, NavButton] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 24, 16, 24)
        layout.setSpacing(4)

        # ── App Branding ──
        brand_layout = QVBoxLayout()
        brand_layout.setSpacing(2)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        app_icon = QLabel()
        app_icon.setFixedSize(36, 36)
        logo_path = get_resource_path("assets/logo.png")
        if Path(logo_path).exists():
            pixmap = QPixmap(logo_path)
            app_icon.setPixmap(pixmap.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            fallback_path = get_resource_path("assets/icons/download.svg")
            if Path(fallback_path).exists():
                from PySide6.QtGui import QIcon
                app_icon.setPixmap(QIcon(fallback_path).pixmap(32, 32))
        
        app_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_row.addWidget(app_icon)

        title_col = QVBoxLayout()
        title_col.setSpacing(0)

        app_title = QLabel("Downloader PRO")
        app_title.setObjectName("app_title")
        app_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Black))
        title_col.addWidget(app_title)

        app_subtitle = QLabel("PREMIUM")
        app_subtitle.setObjectName("app_subtitle")
        app_subtitle.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
        title_col.addWidget(app_subtitle)

        title_row.addLayout(title_col)
        title_row.addStretch()
        brand_layout.addLayout(title_row)

        layout.addLayout(brand_layout)
        layout.addSpacing(24)

        # ── Navigation Items ──
        for icon, label, page_key in self.PAGES:
            btn = NavButton(icon, label)
            btn.clicked.connect(lambda checked, key=page_key: self._on_nav_click(key))
            self.nav_buttons[page_key] = btn
            layout.addWidget(btn)

        # Default active
        self.nav_buttons["dashboard"].set_active(True)

        layout.addStretch()

        # ── CTA Button ──
        new_download_btn = QPushButton("  NEW TASK")
        from PySide6.QtGui import QIcon
        from PySide6.QtCore import QSize
        plus_icon_path = get_resource_path("assets/icons/plus.svg")
        if Path(plus_icon_path).exists():
            new_download_btn.setIcon(QIcon(plus_icon_path))
            new_download_btn.setIconSize(QSize(18, 18))
        new_download_btn.setObjectName("cta_button")
        new_download_btn.setMinimumHeight(48)
        new_download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_download_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        new_download_btn.clicked.connect(lambda: self._on_nav_click("dashboard"))
        layout.addWidget(new_download_btn)

        layout.addSpacing(12)

        # ── Bottom links ──
        sep = QWidget()
        sep.setObjectName("separator_line")
        sep.setFixedHeight(1)
        layout.addWidget(sep)
        layout.addSpacing(8)

        help_btn = NavButton("info", "Help Center")
        help_btn.setMinimumHeight(40)
        layout.addWidget(help_btn)

        # ── Status indicator ──
        status_row = QHBoxLayout()
        status_row.setSpacing(6)
        status_dot = QLabel("●")
        status_dot.setFont(QFont("Segoe UI", 6))
        status_dot.setStyleSheet("color: #4cd7f6;")
        status_dot.setFixedWidth(12)
        status_row.addWidget(status_dot)

        status_text = QLabel("SYSTEM STATUS: OPTIMAL")
        status_text.setObjectName("app_subtitle")
        status_text.setFont(QFont("Segoe UI", 8))
        status_row.addWidget(status_text)
        status_row.addStretch()

        layout.addLayout(status_row)

    def _on_nav_click(self, page_key: str):
        for key, btn in self.nav_buttons.items():
            btn.set_active(key == page_key)
        self.page_changed.emit(page_key)

    def set_active_page(self, page_key: str):
        """Programmatically set the active page."""
        self._on_nav_click(page_key)
