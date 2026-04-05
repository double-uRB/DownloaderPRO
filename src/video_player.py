"""
VideoPlayerPage for Downloader PRO.
Embedded media player using QMediaPlayer + QVideoWidget.
Supports video and audio-only files. Fits into the existing QStackedWidget.
"""

import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSlider, QFileDialog, QSizePolicy
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, QUrl, QSize, Signal
from PySide6.QtGui import QFont, QIcon

from app_logger import get_logger
from utils import get_resource_path

log = get_logger(__name__)

# Audio-only extensions — show waveform placeholder, not a black video surface
AUDIO_EXTENSIONS = {".mp3", ".aac", ".opus", ".ogg", ".flac", ".wav", ".m4a"}


class VideoPlayerPage(QWidget):
    """
    Embedded media player page — lives as Page 3 in the QStackedWidget.

    Signals
    -------
    back_requested          Emitted when Back is clicked. main.py switches
                            back to the Downloads page.
    full_screen_requested   Emitted with True/False to ask main window to
                            toggle fullscreen. Connect in main.py:
                            self.player_page.full_screen_requested.connect(
                                lambda fs: self.showFullScreen() if fs else self.showNormal()
                            )
    """

    back_requested        = Signal()
    full_screen_requested = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("player_page")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._duration_ms: int = 0

        self.media_player = QMediaPlayer()
        self.audio_output  = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)

        self._setup_ui()
        self._setup_connections()

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def showEvent(self, event):
        """Grab keyboard focus the moment this page becomes visible."""
        super().showEvent(event)
        self.setFocus()

    # ── UI Construction ────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── Top bar: Back button + now-playing title ─────────────────────
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        self.back_btn = QPushButton()
        self._set_icon(self.back_btn, "arrow-left", "← Back")
        self.back_btn.setObjectName("icon_button")
        self.back_btn.setFixedSize(36, 36)
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setToolTip("Back to Downloads")
        top_bar.addWidget(self.back_btn)

        self.now_playing_label = QLabel("No file loaded")
        self.now_playing_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.now_playing_label.setObjectName("player_title")
        self.now_playing_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        top_bar.addWidget(self.now_playing_label, stretch=1)

        layout.addLayout(top_bar)

        # ── Video surface ────────────────────────────────────────────────
        self.video_container = QWidget()
        self.video_container.setObjectName("surface_card")
        self.video_container.setStyleSheet(
            "#surface_card { background-color: #000000; border-radius: 12px;"
            " border: 1px solid rgba(76, 215, 246, 0.2); }"
        )
        vc_layout = QVBoxLayout(self.video_container)
        vc_layout.setContentsMargins(0, 0, 0, 0)

        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)
        vc_layout.addWidget(self.video_widget)

        # Audio-only placeholder
        self.audio_placeholder = QLabel("♪")
        self.audio_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.audio_placeholder.setFont(QFont("Segoe UI", 48))
        self.audio_placeholder.setStyleSheet(
            "color: rgba(76, 215, 246, 0.5); background: transparent;"
        )
        vc_layout.addWidget(self.audio_placeholder)

        self.video_widget.hide()
        self.audio_placeholder.show()

        layout.addWidget(self.video_container, stretch=1)

        # ── Controls card ────────────────────────────────────────────────
        self.controls_card = QWidget()
        self.controls_card.setObjectName("surface_card_low")
        self.controls_card.setMinimumHeight(100)
        ctrl = QVBoxLayout(self.controls_card)
        ctrl.setContentsMargins(16, 12, 16, 12)
        ctrl.setSpacing(8)

        # Seek row
        seek_row = QHBoxLayout()
        seek_row.setSpacing(12)

        self.time_label = QLabel("00:00")
        self.time_label.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        seek_row.addWidget(self.time_label)

        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setObjectName("seek_slider")
        self.seek_slider.setRange(0, 0)
        self.seek_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        seek_row.addWidget(self.seek_slider)

        self.duration_label = QLabel("00:00")
        self.duration_label.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self.duration_label.setObjectName("section_subtitle")
        seek_row.addWidget(self.duration_label)

        ctrl.addLayout(seek_row)

        # Button row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.play_btn = QPushButton()
        self._set_icon(self.play_btn, "play", "▶")
        self.play_btn.setObjectName("primary_button")
        self.play_btn.setFixedSize(48, 48)
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.play_btn)

        self.stop_btn = QPushButton()
        self._set_icon(self.stop_btn, "stop", "■")
        self.stop_btn.setFixedSize(40, 40)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.stop_btn)

        self.fullscreen_btn = QPushButton()
        self._set_icon(self.fullscreen_btn, "maximize", "[ ]")
        self.fullscreen_btn.setFixedSize(40, 40)
        self.fullscreen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fullscreen_btn.setToolTip("Toggle fullscreen  (F / F11)")
        btn_row.addWidget(self.fullscreen_btn)

        btn_row.addSpacing(16)

        vol_icon = QLabel()
        self._set_pixmap(vol_icon, "volume-2", "🔊")
        btn_row.addWidget(vol_icon)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setObjectName("volume_slider")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(110)
        self.volume_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.volume_slider)

        btn_row.addStretch()

        self.open_btn = QPushButton("  Open File")
        folder_path = get_resource_path("assets/icons/folder.svg")
        if Path(folder_path).exists():
            self.open_btn.setIcon(QIcon(folder_path))
            self.open_btn.setIconSize(QSize(16, 16))
        self.open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.open_btn)

        ctrl.addLayout(btn_row)
        layout.addWidget(self.controls_card)

    # ── Signal Wiring ──────────────────────────────────────────────────────

    def _setup_connections(self):
        self.back_btn.clicked.connect(self._on_back)
        self.play_btn.clicked.connect(self._toggle_playback)
        self.stop_btn.clicked.connect(self.media_player.stop)
        self.open_btn.clicked.connect(self._open_file_dialog)
        self.fullscreen_btn.clicked.connect(self._toggle_fullscreen)

        self.seek_slider.sliderMoved.connect(self.media_player.setPosition)
        self.volume_slider.valueChanged.connect(
            lambda v: self.audio_output.setVolume(v / 100.0)
        )

        self.media_player.playbackStateChanged.connect(self._on_state_changed)
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.errorOccurred.connect(self._on_error)

    # ── Public API ─────────────────────────────────────────────────────────

    def play_file(self, file_path: str):
        """
        Load and play a local file.
        Called from downloads_page Play button via main.py signal chain.
        Shows audio placeholder automatically for audio-only formats.
        """
        if not os.path.exists(file_path):
            log.error("Cannot play — file not found: %s", file_path)
            return

        ext = Path(file_path).suffix.lower()
        is_audio = ext in AUDIO_EXTENSIONS

        if is_audio:
            self.video_widget.hide()
            self.audio_placeholder.show()
            self.media_player.setVideoOutput(None)
        else:
            self.audio_placeholder.hide()
            self.video_widget.show()
            self.media_player.setVideoOutput(self.video_widget)

        name = Path(file_path).name
        self.now_playing_label.setText(name if len(name) <= 65 else name[:62] + "…")
        self.media_player.setSource(QUrl.fromLocalFile(file_path))
        self.media_player.play()
        log.info("Playback started: %s", name)

    def stop_playback(self):
        """
        Pause (not stop) when navigating away — preserves position
        so the user can resume naturally when they return.
        """
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()

    # ── Slots ──────────────────────────────────────────────────────────────

    def _on_back(self):
        self.stop_playback()
        self.back_requested.emit()

    def _toggle_playback(self):
        state = self.media_player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        elif self.media_player.source().isEmpty():
            self._open_file_dialog()
        else:
            self.media_player.play()

    def _open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Media File", "",
            "Video/Audio Files (*.mp4 *.mkv *.webm *.avi *.mov *.mp3 *.aac *.flac *.wav *.m4a)"
            ";;All Files (*.*)"
        )
        if path:
            self.play_file(path)

    def _toggle_fullscreen(self):
        """
        Emit full_screen_requested so main.py handles window state.

        Connect in main.py __init__:
            self.player_page.full_screen_requested.connect(
                lambda fs: self.showFullScreen() if fs else self.showNormal()
            )
        """
        going_fs = not self.window().isFullScreen()
        self._set_icon(
            self.fullscreen_btn,
            "minimize" if going_fs else "maximize",
            "[X]"      if going_fs else "[ ]",
        )
        self.full_screen_requested.emit(going_fs)

    def _on_state_changed(self, state: QMediaPlayer.PlaybackState):
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        self._set_icon(
            self.play_btn,
            "pause" if playing else "play",
            "||"    if playing else "▶",
        )

    def _on_position_changed(self, position_ms: int):
        if not self.seek_slider.isSliderDown():
            self.seek_slider.setValue(position_ms)
        self.time_label.setText(self._fmt(position_ms))

    def _on_duration_changed(self, duration_ms: int):
        self._duration_ms = duration_ms
        self.seek_slider.setRange(0, duration_ms)
        self.duration_label.setText(self._fmt(duration_ms))

    def _on_error(self, error, error_string: str):
        log.error("MediaPlayer error (%s): %s", error, error_string)
        self.now_playing_label.setText("Error: " + error_string)

    # ── Keyboard shortcuts ─────────────────────────────────────────────────

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Space:
            self._toggle_playback()
        elif key == Qt.Key.Key_Right:
            self.media_player.setPosition(self.media_player.position() + 5000)
        elif key == Qt.Key.Key_Left:
            self.media_player.setPosition(max(0, self.media_player.position() - 5000))
        elif key in (Qt.Key.Key_F, Qt.Key.Key_F11):
            self._toggle_fullscreen()
        elif key == Qt.Key.Key_Escape:
            if self.window().isFullScreen():
                self._toggle_fullscreen()
            else:
                self._on_back()
        else:
            super().keyPressEvent(event)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _set_icon(self, button: QPushButton, icon_name: str, fallback: str):
        path = get_resource_path(f"assets/icons/{icon_name}.svg")
        if Path(path).exists():
            button.setIcon(QIcon(path))
            button.setIconSize(QSize(20, 20))
            button.setText("")
        else:
            button.setIcon(QIcon())
            button.setText(fallback)

    def _set_pixmap(self, label: QLabel, icon_name: str, fallback: str):
        path = get_resource_path(f"assets/icons/{icon_name}.svg")
        if Path(path).exists():
            label.setPixmap(QIcon(path).pixmap(20, 20))
        else:
            label.setText(fallback)

    @staticmethod
    def _fmt(ms: int) -> str:
        s = round(ms / 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"