"""
Browser Page Module
Provides a fully embedded Chromium browser utilizing PySide6.QtWebEngineWidgets.
Features a multi-tab interface, a navigation bar with back, forward, refresh, an address bar, and a dedicated 'Download' action button.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QTabWidget,
    QTabBar, QToolButton
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Signal, Qt, QSize
from PySide6.QtGui import QIcon, QFont
from pathlib import Path
from app_logger import get_logger
from utils import get_resource_path

log = get_logger(__name__)

class WebBrowserPage(QWidget):
    """
    An embedded multi-tab web browser widget.
    Includes a dedicated button to send the current tab's URL to the downloader core.
    """
    video_url_detected = Signal(str)
    full_screen_requested = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("browser_page")
        self._setup_ui()
        self._setup_connections()
        
        # Add the initial default tab
        self.add_new_tab(QUrl("https://www.youtube.com"), "New Tab")

    def _setup_ui(self):
        """Builds the browser layout containing the navigation bar and the tab widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Navigation Bar ──
        self.nav_bar = QWidget()
        self.nav_bar.setObjectName("top_header")
        self.nav_bar.setFixedHeight(56)  # STRICT height to prevent layout expansion bug
        
        nav_layout = QHBoxLayout(self.nav_bar)
        nav_layout.setContentsMargins(16, 8, 16, 8)
        nav_layout.setSpacing(8)

        # Back Button
        self.back_btn = QPushButton()
        self._safely_set_icon(self.back_btn, "back", "←")
        self.back_btn.setFixedSize(36, 36)
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setToolTip("Back")
        nav_layout.addWidget(self.back_btn)

        # Forward Button
        self.forward_btn = QPushButton()
        self._safely_set_icon(self.forward_btn, "forward", "→")
        self.forward_btn.setFixedSize(36, 36)
        self.forward_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.forward_btn.setToolTip("Forward")
        nav_layout.addWidget(self.forward_btn)

        # Reload Button
        self.reload_btn = QPushButton()
        self._safely_set_icon(self.reload_btn, "refresh", "↻")
        self.reload_btn.setFixedSize(36, 36)
        self.reload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reload_btn.setToolTip("Reload")
        nav_layout.addWidget(self.reload_btn)

        # URL Input Field
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL or search...")
        self.url_bar.setMinimumHeight(36)
        self.url_bar.setStyleSheet("""
            QLineEdit {
                background-color: #060e20;
                border: 1px solid rgba(76, 215, 246, 0.2);
                border-radius: 18px;
                padding: 0 16px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #4cd7f6;
            }
        """)
        nav_layout.addWidget(self.url_bar)

        # The Floating / Prominent Action Button
        self.download_btn = QPushButton()
        self._safely_set_icon(self.download_btn, "download", "⬇")
        self.download_btn.setText(" Extract ")
        self.download_btn.setObjectName("cta_button") 
        self.download_btn.setFixedHeight(36)
        self.download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_btn.setToolTip("Download current page video")
        # Inline modification to make it fit horizontally and perfectly
        self.download_btn.setStyleSheet("""
            #cta_button {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4cd7f6, stop:1 #2752e7);
                color: white;
                border-radius: 18px;
                padding: 0 16px;
                font-weight: bold;
                font-size: 13px;
            }
            #cta_button:hover {
                opacity: 0.9;
            }
        """)
        nav_layout.addWidget(self.download_btn)

        layout.addWidget(self.nav_bar)

        # ── Multi-Tab Engine View ──
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 0; }
            QTabBar::tab {
                background: #0d162a;
                color: #8fa1c1;
                border: 1px solid rgba(76,215,246,0.1);
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                min-width: 80px;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background: #152238;
                color: #ffffff;
                border: 1px solid rgba(76,215,246,0.4);
                border-bottom: none;
                font-weight: bold;
            }
        """)

        layout.addWidget(self.tabs)

    def _safely_set_icon(self, button, icon_name, fallback_text):
        path = get_resource_path(f"assets/icons/{icon_name}.svg")
        if Path(path).exists():
            button.setIcon(QIcon(path))
            button.setIconSize(QSize(18, 18))
        else:
            button.setText(fallback_text)

    def _setup_connections(self):
        """Wires up generic UI signals."""
        self.url_bar.returnPressed.connect(self._navigate_to_url)
        self.download_btn.clicked.connect(self._trigger_download)
        
        # Navigation controls (mapped to active tab in handlers)
        self.back_btn.clicked.connect(self._active_tab_back)
        self.forward_btn.clicked.connect(self._active_tab_forward)
        self.reload_btn.clicked.connect(self._active_tab_reload)

        # Tab UI controls
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Initialize the "+" tab at index 1
        self._plus_tab_widget = QWidget()
        i = self.tabs.addTab(self._plus_tab_widget, "+")
        # Remove close button for the + tab
        self.tabs.tabBar().setTabButton(i, QTabBar.ButtonPosition.RightSide, None)

    def add_new_tab(self, qurl=None, label="Blank"):
        """Instantiates a new embedded Chromium view."""
        if qurl is None:
            qurl = QUrl("")
            
        browser = QWebEngineView()
        browser.setUrl(qurl)
        
        # Insert BEFORE the '+' tab!
        plus_index = self.tabs.count() - 1
        if plus_index < 0: plus_index = 0
        i = self.tabs.insertTab(plus_index, browser, label)
        self.tabs.setCurrentIndex(i)

        # Track loaded URLs and Titles
        browser.urlChanged.connect(lambda qurl, browser=browser: self._on_browser_url_changed(qurl, browser))
        browser.titleChanged.connect(lambda title, browser=browser: self._on_browser_title_changed(title, browser))
        browser.loadFinished.connect(lambda _, browser=browser: self._update_active_tab_controls(browser))
        
        # Hook for Fullscreen videos
        browser.page().fullScreenRequested.connect(self._handle_fullscreen_request)

    def close_tab(self, index):
        """Closes a specific tab, preventing closing of the last tab entirely."""
        if self.tabs.count() < 2:
            return
            
        browser = self.tabs.widget(index)
        self.tabs.removeTab(index)
        browser.deleteLater()

    # == Proxy Navigation to Active Tab ==
    def _current_browser(self):
        return self.tabs.currentWidget()

    def _active_tab_back(self):
        if self._current_browser(): self._current_browser().back()

    def _active_tab_forward(self):
        if self._current_browser(): self._current_browser().forward()

    def _active_tab_reload(self):
        if self._current_browser(): self._current_browser().reload()

    # == URL & State Binding ==
    def _navigate_to_url(self):
        """Loads text from URL bar into the active tab."""
        url_text = self.url_bar.text().strip()
        if not url_text: return
            
        if not url_text.startswith("http://") and not url_text.startswith("https://"):
            if "." in url_text and " " not in url_text:
                url_text = "https://" + url_text
            else:
                # Basic google search fallback
                url_text = "https://www.google.com/search?q=" + url_text.replace(" ", "+")
            
        if self._current_browser():
            self._current_browser().setUrl(QUrl(url_text))

    def _on_tab_changed(self, index):
        """Refresh URL bar and controls when switching between tabs."""
        # If user clicked the '+' tab
        if index == self.tabs.count() - 1:
            # We want to add a new tab and not actually stay on the '+' tab
            self.add_new_tab(QUrl("https://www.google.com"), "New Tab")
            return
            
        browser = self.tabs.widget(index)
        if browser and isinstance(browser, QWebEngineView):
            self._update_active_tab_controls(browser)

    def _on_browser_url_changed(self, qurl, browser):
        """Updates the URL bar ONLY if the changed browser is currently focused."""
        if browser == self._current_browser():
            self.url_bar.setText(qurl.toString())
            self.url_bar.setCursorPosition(0)

    def _on_browser_title_changed(self, title, browser):
        """Updates the Tab text."""
        index = self.tabs.indexOf(browser)
        if index != -1:
            # truncate title for clean tabs
            short_title = (title[:18] + '..') if len(title) > 20 else title
            self.tabs.setTabText(index, short_title)

    def _update_active_tab_controls(self, browser):
        if browser == self._current_browser() and browser.url().toString():
            self.url_bar.setText(browser.url().toString())
            self.url_bar.setCursorPosition(0)

    # == Action Handlers ==
    def _trigger_download(self):
        """Passes the active tab's URL back to the main downloader core."""
        browser = self._current_browser()
        if browser and isinstance(browser, QWebEngineView) and browser.url().toString():
            url_str = browser.url().toString()
            log.info(f"User requested extraction of: {url_str}")
            self.video_url_detected.emit(url_str)

    def _handle_fullscreen_request(self, request):
        """Called when a video embedded in the page requests fullscreen."""
        request.accept()
        is_fullscreen = request.toggleOn()
        
        # Hide browser internal chrome to allow true fullscreen
        if is_fullscreen:
            self.nav_bar.hide()
            self.tabs.tabBar().hide()
            # Try to grab keyboard focus for ESC key processing
            browser = self._current_browser()
            if browser: browser.setFocus()
        else:
            self.nav_bar.show()
            self.tabs.tabBar().show()
            
        self.full_screen_requested.emit(is_fullscreen)

