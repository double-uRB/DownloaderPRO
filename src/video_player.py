"""
Video Player Module
Provides a fully functional native media player using QMediaPlayer and QVideoWidget.
Allows users to play their downloaded files directly within the application.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QFileDialog
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, QUrl, QSize, Signal
from PySide6.QtGui import QFont, QIcon
from pathlib import Path
from app_logger import get_logger
from utils import get_resource_path

log = get_logger(__name__)

class VideoPlayerPage(QWidget):
    """
    A unified video player utilizing QMediaPlayer and QVideoWidget.
    Supports basic playback controls: Play/Pause, Stop, scrubbing, volume, and fullscreen.
    """
    full_screen_requested = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("player_page")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Core multimedia objects
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        # Audio default volume
        self.audio_output.setVolume(1.0)
        
        self._setup_ui()
        self._setup_connections()

    def showEvent(self, event):
        """Auto-focus the player widget when page becomes visible for keyboard shortcuts."""
        super().showEvent(event)
        self.setFocus()

    def _setup_ui(self):
        """Constructs the player layout and controls."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── Video Display Area ──
        # Wrap video widget in a styled frame
        self.video_container = QWidget()
        self.video_container.setObjectName("surface_card")
        self.video_container.setStyleSheet("""
            #surface_card {
                background-color: #000000;
                border-radius: 12px;
                border: 1px solid rgba(76, 215, 246, 0.2);
            }
        """)
        vc_layout = QVBoxLayout(self.video_container)
        vc_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)
        vc_layout.addWidget(self.video_widget)
        
        # Overlay for empty state
        self.empty_label = QLabel("No Video Loaded")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.empty_label.setStyleSheet("color: rgba(255,255,255,0.4); background: transparent;")
        
        # We use a trick to layer the label over the video widget when nothing is playing,
        # but to keep it simple, we just switch visibility.
        vc_layout.addWidget(self.empty_label)
        self.video_widget.hide() # Hidden until a file is loaded
        
        layout.addWidget(self.video_container, stretch=1)

        # ── Controls Area ──
        self.controls_card = QWidget()
        self.controls_card.setObjectName("surface_card_low")
        self.controls_card.setMinimumHeight(100)
        controls_layout = QVBoxLayout(self.controls_card)
        controls_layout.setContentsMargins(16, 12, 16, 12)
        controls_layout.setSpacing(8)

        # Progress slider row
        progress_row = QHBoxLayout()
        progress_row.setSpacing(12)
        
        self.time_label = QLabel("00:00")
        self.time_label.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        progress_row.addWidget(self.time_label)

        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 0)
        progress_row.addWidget(self.seek_slider)

        self.duration_label = QLabel("00:00")
        self.duration_label.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self.duration_label.setObjectName("section_subtitle")
        progress_row.addWidget(self.duration_label)
        
        controls_layout.addLayout(progress_row)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        # Play/Pause
        self.play_btn = QPushButton()
        self._set_icon(self.play_btn, "play", "▶")
        self.play_btn.setFixedSize(48, 48)
        self.play_btn.setObjectName("primary_button")
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.play_btn)

        # Stop
        self.stop_btn = QPushButton()
        self._set_icon(self.stop_btn, "stop", "■")
        self.stop_btn.setFixedSize(40, 40)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.stop_btn)

        # Fullscreen
        self.fullscreen_btn = QPushButton()
        self._set_icon(self.fullscreen_btn, "maximize", "[ ]")
        self.fullscreen_btn.setFixedSize(40, 40)
        self.fullscreen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.fullscreen_btn)
        
        btn_row.addSpacing(12)

        # Volume
        volume_icon = QLabel()
        volume_path = get_resource_path("assets/icons/volume.svg")
        if Path(volume_path).exists():
            volume_icon.setPixmap(QIcon(volume_path).pixmap(20, 20))
        else:
            volume_icon.setText("🔊")
        btn_row.addWidget(volume_icon)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(100)
        btn_row.addWidget(self.volume_slider)

        btn_row.addStretch()

        # Open File Button
        self.open_btn = QPushButton(" Open File")
        folder_icon = get_resource_path("assets/icons/folder.svg")
        if Path(folder_icon).exists():
            self.open_btn.setIcon(QIcon(folder_icon))
            self.open_btn.setIconSize(QSize(16, 16))
        self.open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.open_btn)

        controls_layout.addLayout(btn_row)
        
        # Now Playing info
        self.now_playing_label = QLabel("Now Playing: None")
        self.now_playing_label.setFont(QFont("Segoe UI", 9))
        self.now_playing_label.setObjectName("section_subtitle")
        controls_layout.addWidget(self.now_playing_label)

        layout.addWidget(self.controls_card)

    def _set_icon(self, button, icon_name, fallback_text):
        """Helper to safely apply SVG icons"""
        icon_path = get_resource_path(f"assets/icons/{icon_name}.svg")
        if Path(icon_path).exists():
            button.setIcon(QIcon(icon_path))
            button.setIconSize(QSize(20, 20))
        else:
            button.setText(fallback_text)

    def _setup_connections(self):
        """Maps user interaction and media player signals."""
        self.play_btn.clicked.connect(self._toggle_playback)
        self.stop_btn.clicked.connect(self.media_player.stop)
        self.open_btn.clicked.connect(self._open_file_dialog)
        self.fullscreen_btn.clicked.connect(self._toggle_fullscreen)
        
        self.volume_slider.valueChanged.connect(self._set_volume)
        self.seek_slider.sliderMoved.connect(self._set_position)

        # Media Player state binding
        self.media_player.playbackStateChanged.connect(self._on_state_changed)
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.errorOccurred.connect(self._on_error)

    def play_file(self, file_path):
        """Public API to load and play a video file programmatically."""
        if not os.path.exists(file_path):
            log.error(f"Cannot play file, does not exist: {file_path}")
            return
            
        url = QUrl.fromLocalFile(file_path)
        self.media_player.setSource(url)
        self.now_playing_label.setText(f"Now Playing: {Path(file_path).name}")
        
        # Hide placeholder, show video
        self.empty_label.hide()
        self.video_widget.show()
        
        self.media_player.play()
        log.info(f"Started playback of {file_path}")

    def _open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Video", "", "Video Files (*.mp4 *.mkv *.webm *.avi);;All Files (*.*)"
        )
        if file_path:
            self.play_file(file_path)

    def _toggle_playback(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            if self.media_player.source().isEmpty():
                self._open_file_dialog()
            else:
                self.media_player.play()

    def _set_volume(self, volume):
        # AudioOutput volume is 0.0 to 1.0 (linear scale)
        self.audio_output.setVolume(volume / 100.0)

    def _set_position(self, position):
        self.media_player.setPosition(position)

    def _on_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._set_icon(self.play_btn, "pause", "||")
        else:
            self._set_icon(self.play_btn, "play", "▶")

    def _on_position_changed(self, position):
        if not self.seek_slider.isSliderDown():
            self.seek_slider.setValue(position)
        self.time_label.setText(self._format_time(position))

    def _on_duration_changed(self, duration):
        self.seek_slider.setRange(0, duration)
        self.duration_label.setText(self._format_time(duration))

    def _on_error(self, error, error_string):
        log.error(f"MediaPlayer Error ({error}): {error_string}")
        self.now_playing_label.setText(f"Playback Error: {error_string}")

    def _format_time(self, ms):
        """Converts milliseconds into MM:SS or HH:MM:SS format."""
        s = round(ms / 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def stop_playback(self):
        """Used to forcefully halt playback when switching pages/exiting"""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode for the player. Hides controls for cinematic view."""
        is_fs = self.window().isFullScreen()
        if not is_fs:
            # Entering fullscreen
            self._set_icon(self.fullscreen_btn, "minimize", "[X]")
        else:
            # Exiting fullscreen
            self._set_icon(self.fullscreen_btn, "maximize", "[ ]")
        self.full_screen_requested.emit(not is_fs)

    def keyPressEvent(self, event):
        """Handle media keyboard shortcuts."""
        if event.key() == Qt.Key.Key_Space:
            self._toggle_playback()
        elif event.key() == Qt.Key.Key_Right:
            pos = self.media_player.position()
            self.media_player.setPosition(pos + 5000)
        elif event.key() == Qt.Key.Key_Left:
            pos = self.media_player.position()
            self.media_player.setPosition(max(0, pos - 5000))
        elif event.key() == Qt.Key.Key_Escape:
            if self.window().isFullScreen():
                self._toggle_fullscreen()
        else:
            super().keyPressEvent(event)
