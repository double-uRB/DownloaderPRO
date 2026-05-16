"""
Modern UI components for Downloader PRO.
Card-based quality selector, video info panel with thumbnail, advanced download panel
with split video/audio sections, and embedded progress widget.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton, QProgressBar, QSizePolicy, QGridLayout,
    QComboBox, QLineEdit, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QUrl, QSize, QThread, QObject
from PySide6.QtGui import QFont, QPixmap, QIcon, QImage
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from pathlib import Path
from utils import get_resource_path
from downloader_core import parse_available_streams, estimate_file_size, _format_bytes, _format_bitrate


class ImageProcessor(QThread):
    """Processes image data into a scaled pixmap in a background thread."""
    finished = Signal(QPixmap)

    def __init__(self, data, target_width):
        super().__init__()
        self.data = data
        self.target_width = target_width

    def run(self):
        image = QImage()
        if image.loadFromData(self.data):
            # Scaling in the background thread
            scaled = image.scaledToWidth(self.target_width, Qt.TransformationMode.SmoothTransformation)
            pixmap = QPixmap.fromImage(scaled)
            self.finished.emit(pixmap)


class VideoInfoPanel(QWidget):
    """Displays video thumbnail, title, channel, views, and description."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.network_manager = QNetworkAccessManager(self)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.card = QWidget()
        self.card.setObjectName("surface_card")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # Thumbnail area
        self.thumbnail_container = QWidget()
        self.thumbnail_container.setMinimumHeight(280)
        self.thumbnail_container.setMaximumHeight(400)
        self.thumbnail_container.setStyleSheet("background-color: #060e20; border-radius: 12px 12px 0 0;")
        thumb_layout = QVBoxLayout(self.thumbnail_container)
        thumb_layout.setContentsMargins(0, 0, 0, 0)

        self.thumbnail_label = QLabel()
        icon_path = get_resource_path("assets/icons/film.svg")
        if Path(icon_path).exists():
            self.thumbnail_label.setPixmap(QIcon(icon_path).pixmap(64, 64))
        else:
            self.thumbnail_label.setText("📹")
            self.thumbnail_label.setFont(QFont("Segoe UI", 60))
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        thumb_layout.addWidget(self.thumbnail_label)

        badge_container = QHBoxLayout()
        badge_container.setContentsMargins(16, 0, 16, 12)
        self.duration_badge = QLabel("")
        self.duration_badge.setObjectName("badge_primary")
        self.duration_badge.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.duration_badge.setVisible(False)
        badge_container.addWidget(self.duration_badge)
        badge_container.addStretch()
        self.hd_badge = QLabel("HD")
        self.hd_badge.setObjectName("badge_primary")
        self.hd_badge.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.hd_badge.setVisible(False)
        badge_container.addWidget(self.hd_badge)
        thumb_layout.addLayout(badge_container)
        card_layout.addWidget(self.thumbnail_container)

        # Info section
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(20, 16, 20, 20)
        info_layout.setSpacing(12)

        title_row = QHBoxLayout()
        self.title_label = QLabel("")
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.title_label.setWordWrap(True)
        self.title_label.setObjectName("section_title")
        title_row.addWidget(self.title_label)
        info_layout.addLayout(title_row)

        channel_row = QHBoxLayout()
        channel_row.setSpacing(10)
        self.channel_label = QLabel("")
        self.channel_label.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        channel_row.addWidget(self.channel_label)
        channel_row.addStretch()
        info_layout.addLayout(channel_row)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(32)
        self.views_widget = self._create_stat("VIEWS", "—")
        stats_row.addLayout(self.views_widget)
        self.date_widget = self._create_stat("PUBLISHED", "—")
        stats_row.addLayout(self.date_widget)
        self.likes_widget = self._create_stat("LIKES", "—")
        stats_row.addLayout(self.likes_widget)
        stats_row.addStretch()
        info_layout.addLayout(stats_row)

        desc_container = QWidget()
        desc_container.setObjectName("surface_card_low")
        desc_container.setStyleSheet(desc_container.styleSheet() + "padding: 12px;")
        desc_layout = QVBoxLayout(desc_container)
        desc_layout.setContentsMargins(12, 10, 12, 10)
        desc_layout.setSpacing(6)
        self.description_label = QLabel("")
        self.description_label.setFont(QFont("Segoe UI", 11))
        self.description_label.setWordWrap(True)
        self.description_label.setMaximumHeight(50)
        self.description_label.setObjectName("section_subtitle")
        desc_layout.addWidget(self.description_label)
        self.show_more_btn = QPushButton("Show more")
        self.show_more_btn.setStyleSheet("color: #4cd7f6; background: transparent; border: none; font-weight: 700; font-size: 11px; text-align: left; padding: 0;")
        self.show_more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.show_more_btn.clicked.connect(self._toggle_description)
        self.show_more_btn.setVisible(False)
        desc_layout.addWidget(self.show_more_btn)
        info_layout.addWidget(desc_container)
        card_layout.addWidget(info_widget)
        layout.addWidget(self.card)

    def _create_stat(self, label_text, value_text):
        stat_layout = QVBoxLayout()
        stat_layout.setSpacing(2)
        label = QLabel(label_text)
        label.setObjectName("stat_label")
        label.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        stat_layout.addWidget(label)
        value = QLabel(value_text)
        value.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        stat_layout.addWidget(value)
        stat_layout._value_label = value
        return stat_layout

    def _toggle_description(self):
        if self.description_label.maximumHeight() == 50:
            self.description_label.setMaximumHeight(500)
            self.show_more_btn.setText("Show less")
        else:
            self.description_label.setMaximumHeight(50)
            self.show_more_btn.setText("Show more")

    def update_info(self, video_info):
        title = video_info.get('title', 'Unknown Title')
        duration = video_info.get('duration', 0)
        uploader = video_info.get('uploader', 'Unknown')
        view_count = video_info.get('view_count', 0)
        like_count = video_info.get('like_count', 0)
        upload_date = video_info.get('upload_date', '')
        description = video_info.get('description', '')

        self.title_label.setText(title)
        self.channel_label.setText(f"  {uploader}")

        if duration:
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60
            dur_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"
            self.duration_badge.setText(dur_str)
            self.duration_badge.setVisible(True)
            self.hd_badge.setVisible(True)

        self.views_widget._value_label.setText(self._format_number(view_count))
        self.likes_widget._value_label.setText(self._format_number(like_count))
        if upload_date and len(upload_date) == 8:
            formatted_date = f"{upload_date[6:8]}/{upload_date[4:6]}/{upload_date[:4]}"
            self.date_widget._value_label.setText(formatted_date)
        if description:
            self.description_label.setText(description[:300])
            if len(description) > 100:
                self.show_more_btn.setVisible(True)
        thumbnail_url = video_info.get('thumbnail', '')
        if thumbnail_url:
            self._load_thumbnail(thumbnail_url)

    def _format_number(self, num):
        if not num:
            return "—"
        if num >= 1_000_000_000:
            return f"{num / 1_000_000_000:.1f}B"
        elif num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}K"
        return str(num)

    def _load_thumbnail(self, url):
        request = QNetworkRequest(QUrl(url))
        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self._on_thumbnail_loaded(reply))

    def _on_thumbnail_loaded(self, reply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            # Offload heavy image loading and scaling to a background worker
            self.thumbnail_worker = ImageProcessor(data, self.thumbnail_container.width())
            self.thumbnail_worker.finished.connect(self._set_thumbnail_pixmap)
            self.thumbnail_worker.start()
        reply.deleteLater()

    def _set_thumbnail_pixmap(self, pixmap):
        """Sets the scaled pixmap once processing is complete."""
        if not pixmap.isNull():
            self.thumbnail_label.setPixmap(pixmap)
            self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)


class QualityCard(QPushButton):
    """A single quality option card."""

    selected_changed = Signal(str)

    def __init__(self, format_id, resolution, codec, file_size, height="auto", is_hdr=False, parent=None):
        super().__init__(parent)
        self.format_id = format_id
        self.height = height
        self.setObjectName("quality_card")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(60)
        self.setMinimumWidth(200)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        res_badge = QLabel(self._short_resolution(resolution))
        res_badge.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        res_badge.setFixedSize(42, 42)
        res_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        res_badge.setStyleSheet("""
            background-color: rgba(76, 215, 246, 0.1);
            border-radius: 8px;
            color: #bcc9cd;
        """)
        layout.addWidget(res_badge)
        self._res_badge = res_badge

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        res_label = QLabel(f"{resolution}")
        res_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        text_col.addWidget(res_label)
        detail_label = QLabel(f"{codec} • {file_size}")
        detail_label.setFont(QFont("Segoe UI", 9))
        detail_label.setObjectName("section_subtitle")
        text_col.addWidget(detail_label)
        layout.addLayout(text_col)
        layout.addStretch()

        if is_hdr:
            hdr = QLabel("HDR")
            hdr.setObjectName("badge_hdr")
            hdr.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            layout.addWidget(hdr)

        self.check_label = QLabel()
        icon_path = get_resource_path("assets/icons/check.svg")
        if Path(icon_path).exists():
            self.check_label.setPixmap(QIcon(icon_path).pixmap(20, 20))
        else:
            self.check_label.setText("✅")
            self.check_label.setFont(QFont("Segoe UI", 14))
        self.check_label.setVisible(False)
        layout.addWidget(self.check_label)
        self.clicked.connect(lambda: self.selected_changed.emit(self.format_id))

    def _short_resolution(self, resolution):
        if "2160" in resolution:
            return "4K"
        elif "1080" in resolution:
            return "HD"
        elif "720" in resolution:
            return "720p"
        elif "480" in resolution:
            return "480p"
        elif "360" in resolution:
            return "360p"
        elif "Best" in resolution:
            return "AUTO"
        return resolution[:4]

    def set_selected(self, selected: bool):
        self.setChecked(selected)
        self.setProperty("selected", "true" if selected else "false")
        self.check_label.setVisible(selected)
        self._res_badge.setStyleSheet(f"""
            background-color: {'rgba(76, 215, 246, 0.2)' if selected else 'rgba(76, 215, 246, 0.1)'};
            border-radius: 8px;
            color: {'#4cd7f6' if selected else '#bcc9cd'};
        """)
        self.style().unpolish(self)
        self.style().polish(self)


class QualitySelector(QWidget):
    """Card-based quality selector."""

    resolution_changed = Signal(int)

    def __init__(self, formats, parent=None):
        super().__init__(parent)
        self.formats = formats
        self.selected_quality = "auto"
        self.quality_cards: list[QualityCard] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title_row = QHBoxLayout()
        icon = QLabel()
        icon_path = get_resource_path("assets/icons/film.svg")
        if Path(icon_path).exists():
            icon.setPixmap(QIcon(icon_path).pixmap(24, 24))
        else:
            icon.setText("🎬")
        title_row.addWidget(icon)
        title = QLabel("Select Quality")
        title.setObjectName("section_title")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_row.addWidget(title)
        title_row.addStretch()
        layout.addLayout(title_row)

        quality_options = self._parse_formats()
        for i, qinfo in enumerate(quality_options):
            card = QualityCard(
                format_id=qinfo["format_id"],
                resolution=qinfo["resolution"],
                codec=qinfo["video_codec"],
                file_size=qinfo["size_estimate"],
                height=qinfo.get("height", "auto"),
                is_hdr=qinfo.get("is_hdr", False),
            )
            card.selected_changed.connect(self._on_card_selected)
            self.quality_cards.append(card)
            layout.addWidget(card)
            if i == 0:
                card.set_selected(True)
                self.selected_quality = qinfo.get("height", "auto")

    def _parse_formats(self):
        options = [{
            "format_id": "auto", "height": "auto",
            "resolution": "Best Available", "video_codec": "Auto Select",
            "size_estimate": "Best", "is_hdr": False,
        }]
        if not self.formats:
            return options
        seen_heights = set()
        video_formats = []
        for fmt in self.formats:
            vcodec = fmt.get('vcodec', 'none')
            height = fmt.get('height', 0)
            if not vcodec or vcodec == 'none' or not height or height < 360 or height in seen_heights:
                continue
            seen_heights.add(height)
            video_formats.append(fmt)
        video_formats.sort(key=lambda f: f.get('height', 0), reverse=True)

        for fmt in video_formats[:5]:
            height = fmt.get('height', 0)
            vcodec = fmt.get('vcodec', '')
            format_note = fmt.get('format_note', '').lower()
            filesize = fmt.get('filesize', 0) or fmt.get('filesize_approx', 0)
            codec_name = "Auto"
            if 'avc1' in vcodec or 'h264' in vcodec.lower(): codec_name = "H.264"
            elif 'vp9' in vcodec.lower(): codec_name = "VP9"
            elif 'av01' in vcodec.lower(): codec_name = "AV1"
            res_label = f"{height}p"
            if height >= 2160: res_label += " (Ultra HD)"
            elif height >= 1080: res_label += " (Full HD)"
            elif height >= 720: res_label += " (HD)"
            if filesize:
                size_str = f"{filesize / 1_073_741_824:.1f} GB" if filesize >= 1_073_741_824 else f"{filesize / 1_048_576:.0f} MB"
            else:
                size_str = "~Unknown"
            is_hdr = any(h in format_note for h in ['hdr', 'hdr10', 'dolby'])
            options.append({
                "format_id": fmt.get('format_id', 'unknown'), "height": str(height),
                "resolution": res_label, "video_codec": codec_name,
                "size_estimate": size_str, "is_hdr": is_hdr,
            })
        return options

    def _on_card_selected(self, format_id):
        for card in self.quality_cards:
            if card.format_id == format_id:
                self.selected_quality = card.height
            card.set_selected(card.format_id == format_id)
        try:
            height = int(self.selected_quality)
        except (ValueError, TypeError):
            height = 0
        self.resolution_changed.emit(height)

    def get_selected_quality(self):
        return self.selected_quality


# ── Styled ComboBox ──────────────────────────────────────────────────────────

COMBO_STYLE = """
    QComboBox {
        padding: 6px 12px;
        background-color: #0d1b2a;
        border: 1px solid rgba(76, 215, 246, 0.2);
        border-radius: 8px;
        color: #e0e6ed;
    }
    QComboBox::drop-down { border: none; width: 24px; }
    QComboBox QAbstractItemView {
        background-color: #0d1b2a;
        border: 1px solid rgba(76, 215, 246, 0.3);
        selection-background-color: rgba(76, 215, 246, 0.15);
        color: #e0e6ed;
    }
"""


class AdvancedDownloadPanel(QWidget):
    """Inline panel for advanced codec, bitrate, and audio selection.
    
    Split into VIDEO and AUDIO sections. Audio has its own toggle for
    audio-only downloads. All data comes from cached format list.
    """

    # Emitted when audio-only mode changes
    audio_only_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_streams = {'video_streams': [], 'audio_streams': []}
        self._duration = 0
        self._preferred_video_codec = "auto"
        self._preferred_audio_codec = "auto"
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("surface_card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        # ── Header ──
        header = QHBoxLayout()
        header.setSpacing(8)
        settings_icon = QLabel()
        icon_path = get_resource_path("assets/icons/settings.svg")
        if Path(icon_path).exists():
            settings_icon.setPixmap(QIcon(icon_path).pixmap(18, 18))
        else:
            settings_icon.setText("⚙️")
        header.addWidget(settings_icon)
        title = QLabel("Advanced Download")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setObjectName("section_title")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # ═══════════════════════════════════════════════════════════════════
        # VIDEO SECTION
        # ═══════════════════════════════════════════════════════════════════
        video_header = QHBoxLayout()
        video_header.setSpacing(8)
        vid_icon = QLabel()
        vid_icon_path = get_resource_path("assets/icons/film.svg")
        if Path(vid_icon_path).exists():
            vid_icon.setPixmap(QIcon(vid_icon_path).pixmap(16, 16))
        video_header.addWidget(vid_icon)
        vid_title = QLabel("VIDEO")
        vid_title.setObjectName("stat_label")
        vid_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        video_header.addWidget(vid_title)
        video_header.addStretch()
        layout.addLayout(video_header)

        # Video Codec
        self.video_combo = QComboBox()
        self.video_combo.setMinimumHeight(38)
        self.video_combo.setFont(QFont("Segoe UI", 11))
        self.video_combo.setStyleSheet(COMBO_STYLE)
        self.video_combo.currentIndexChanged.connect(self._on_selection_changed)
        layout.addWidget(self.video_combo)

        # Bitrate Preference
        bitrate_label = QLabel("BITRATE PREFERENCE")
        bitrate_label.setObjectName("stat_label")
        bitrate_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        layout.addWidget(bitrate_label)

        bitrate_row = QHBoxLayout()
        bitrate_row.setSpacing(8)
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["Max Quality", "Balanced", "Data Saver", "Custom..."])
        self.bitrate_combo.setMinimumHeight(38)
        self.bitrate_combo.setFont(QFont("Segoe UI", 11))
        self.bitrate_combo.setStyleSheet(COMBO_STYLE)
        self.bitrate_combo.setCurrentIndex(1)
        self.bitrate_combo.currentIndexChanged.connect(self._on_bitrate_mode_changed)
        bitrate_row.addWidget(self.bitrate_combo, stretch=2)

        self.custom_bitrate_input = QLineEdit()
        self.custom_bitrate_input.setPlaceholderText("kbps")
        self.custom_bitrate_input.setMinimumHeight(38)
        self.custom_bitrate_input.setFont(QFont("Segoe UI", 11))
        self.custom_bitrate_input.setFixedWidth(90)
        self.custom_bitrate_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 10px; background-color: #0d1b2a;
                border: 1px solid rgba(76, 215, 246, 0.2);
                border-radius: 8px; color: #e0e6ed;
            }
        """)
        self.custom_bitrate_input.setVisible(False)
        bitrate_row.addWidget(self.custom_bitrate_input)
        layout.addLayout(bitrate_row)

        # ── Separator ──
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: rgba(76, 215, 246, 0.1); max-height: 1px;")
        layout.addWidget(sep)

        # ═══════════════════════════════════════════════════════════════════
        # AUDIO SECTION
        # ═══════════════════════════════════════════════════════════════════
        audio_header = QHBoxLayout()
        audio_header.setSpacing(8)
        aud_icon = QLabel()
        aud_icon_path = get_resource_path("assets/icons/music.svg")
        if Path(aud_icon_path).exists():
            aud_icon.setPixmap(QIcon(aud_icon_path).pixmap(16, 16))
        audio_header.addWidget(aud_icon)
        aud_title = QLabel("AUDIO")
        aud_title.setObjectName("stat_label")
        aud_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        audio_header.addWidget(aud_title)
        audio_header.addStretch()

        # Audio-only toggle
        audio_only_label = QLabel("Audio Only")
        audio_only_label.setFont(QFont("Segoe UI", 10))
        audio_header.addWidget(audio_only_label)
        self.audio_only_cb = QCheckBox()
        self.audio_only_cb.toggled.connect(self._on_audio_only_changed)
        audio_header.addWidget(self.audio_only_cb)
        layout.addLayout(audio_header)

        # Audio Format
        self.audio_combo = QComboBox()
        self.audio_combo.setMinimumHeight(38)
        self.audio_combo.setFont(QFont("Segoe UI", 11))
        self.audio_combo.setStyleSheet(COMBO_STYLE)
        self.audio_combo.currentIndexChanged.connect(self._on_selection_changed)
        layout.addWidget(self.audio_combo)

        # ── Separator ──
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("background-color: rgba(76, 215, 246, 0.1); max-height: 1px;")
        layout.addWidget(sep2)

        # ═══════════════════════════════════════════════════════════════════
        # FILE SIZE ESTIMATE
        # ═══════════════════════════════════════════════════════════════════
        estimate_container = QWidget()
        estimate_container.setStyleSheet("""
            background-color: rgba(76, 215, 246, 0.06);
            border-radius: 8px;
        """)
        estimate_layout = QHBoxLayout(estimate_container)
        estimate_layout.setContentsMargins(12, 10, 12, 10)

        est_icon = QLabel()
        est_icon_path = get_resource_path("assets/icons/hard-drive.svg")
        if Path(est_icon_path).exists():
            est_icon.setPixmap(QIcon(est_icon_path).pixmap(18, 18))
        else:
            est_icon.setText("💾")
        estimate_layout.addWidget(est_icon)

        est_title = QLabel("Estimated Size:")
        est_title.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        estimate_layout.addWidget(est_title)
        estimate_layout.addStretch()

        self.size_estimate_label = QLabel("—")
        self.size_estimate_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.size_estimate_label.setStyleSheet("color: #4cd7f6;")
        estimate_layout.addWidget(self.size_estimate_label)

        layout.addWidget(estimate_container)

    # ── Public API ────────────────────────────────────────────────────────────

    def load_streams(self, formats, duration):
        """Parse and cache available streams from fetched video info."""
        self._all_streams = parse_available_streams(formats)
        self._duration = duration
        self._populate_audio()

    def filter_by_resolution(self, height):
        """Update video codec dropdown based on selected resolution."""
        self._populate_video(height)
        self._update_estimate()

    def is_audio_only(self):
        return self.audio_only_cb.isChecked()

    def get_selected_format_ids(self):
        """Return (video_format_id, audio_format_id) or (None, None) for auto."""
        video_data = self.video_combo.currentData()
        audio_data = self.audio_combo.currentData()
        vid = video_data.get('format_id') if video_data else None
        aud = audio_data.get('format_id') if audio_data else None
        return vid, aud

    def get_selected_audio_format_id(self):
        """Return the selected audio format_id for audio-only downloads."""
        audio_data = self.audio_combo.currentData()
        return audio_data.get('format_id') if audio_data else None

    def get_quality_tag(self):
        video_data = self.video_combo.currentData()
        if video_data:
            return f"{video_data.get('height', 'x')}p_{video_data.get('codec', 'auto')}"
        return "custom"

    def set_preferences(self, video_codec="auto", audio_codec="auto",
                        bitrate_mode="balanced", custom_bitrate=0):
        mode_map = {"max": 0, "balanced": 1, "saver": 2, "custom": 3}
        idx = mode_map.get(bitrate_mode, 1)
        self.bitrate_combo.setCurrentIndex(idx)
        if bitrate_mode == "custom" and custom_bitrate > 0:
            self.custom_bitrate_input.setText(str(custom_bitrate))
            self.custom_bitrate_input.setVisible(True)
        self._preferred_video_codec = video_codec
        self._preferred_audio_codec = audio_codec

    def get_preferences(self):
        mode_map = {0: "max", 1: "balanced", 2: "saver", 3: "custom"}
        return {
            "video_codec": self._get_selected_video_codec(),
            "audio_codec": self._get_selected_audio_codec(),
            "bitrate_mode": mode_map.get(self.bitrate_combo.currentIndex(), "balanced"),
            "custom_bitrate": self._get_custom_bitrate(),
        }

    # ── Private ───────────────────────────────────────────────────────────────

    def _populate_video(self, target_height):
        self.video_combo.blockSignals(True)
        self.video_combo.clear()

        if target_height == 0:
            self.video_combo.addItem("Auto (Best Available)", None)
            self.video_combo.blockSignals(False)
            self._update_estimate()
            return

        matching = [s for s in self._all_streams['video_streams'] if s['height'] == target_height]
        if not matching:
            all_heights = sorted(set(s['height'] for s in self._all_streams['video_streams']), reverse=True)
            closest = min(all_heights, key=lambda h: abs(h - target_height)) if all_heights else 0
            matching = [s for s in self._all_streams['video_streams'] if s['height'] == closest]

        # Sort based on bitrate preference
        bitrate_mode = self.bitrate_combo.currentText()
        if bitrate_mode == "Max Quality":
            matching.sort(key=lambda s: s['bitrate'], reverse=True)
        elif bitrate_mode == "Data Saver":
            matching.sort(key=lambda s: s['bitrate'])
        elif bitrate_mode == "Custom...":
            custom_kbps = self._get_custom_bitrate()
            if custom_kbps > 0:
                matching.sort(key=lambda s: abs(s['bitrate'] - custom_kbps))
            else:
                matching.sort(key=lambda s: s['bitrate'], reverse=True)
        else:  # Balanced
            matching.sort(key=lambda s: (
                1 if s['codec'] == 'H.264' else 0,
                s['bitrate']
            ), reverse=True)

        for stream in matching:
            size_str = _format_bytes(stream['filesize']) if stream['filesize'] else "~?"
            bitrate_str = _format_bitrate(stream['bitrate'])
            label = f"{stream['codec']}  —  {bitrate_str}  —  {size_str}"
            if stream.get('fps', 30) > 30:
                label += f"  ({stream['fps']}fps)"
            if stream.get('dynamic_range', 'SDR') != 'SDR':
                label += f"  [{stream['dynamic_range']}]"
            self.video_combo.addItem(label, stream)

        self.video_combo.blockSignals(False)
        self._update_estimate()

    def _populate_audio(self):
        self.audio_combo.blockSignals(True)
        self.audio_combo.clear()

        streams = self._all_streams.get('audio_streams', [])
        if not streams:
            self.audio_combo.addItem("No audio streams found", None)
            self.audio_combo.blockSignals(False)
            return

        for stream in streams:
            size_str = _format_bytes(stream['filesize']) if stream['filesize'] else "~?"
            bitrate_str = _format_bitrate(stream['bitrate'])
            ch_count = stream.get('channels', 2)
            ch_str = f"{ch_count}ch" if ch_count > 2 else "stereo"
            lang = stream.get('language', '')
            lang_str = f"  [{lang}]" if lang and lang != 'und' else ""

            label = f"{stream['codec']}  —  {bitrate_str}  —  {ch_str}  —  {size_str}{lang_str}"
            self.audio_combo.addItem(label, stream)

        self.audio_combo.blockSignals(False)

    def _on_selection_changed(self):
        self._update_estimate()

    def _on_audio_only_changed(self, checked):
        # Dim video section when audio-only is selected
        self.video_combo.setEnabled(not checked)
        self.bitrate_combo.setEnabled(not checked)
        self.custom_bitrate_input.setEnabled(not checked)
        self.audio_only_changed.emit(checked)
        self._update_estimate()

    def _on_bitrate_mode_changed(self, index):
        is_custom = self.bitrate_combo.currentText() == "Custom..."
        self.custom_bitrate_input.setVisible(is_custom)
        video_data = self.video_combo.currentData()
        if video_data:
            self._populate_video(video_data.get('height', 0))
        self._update_estimate()

    def _get_custom_bitrate(self):
        try: return int(self.custom_bitrate_input.text())
        except (ValueError, TypeError): return 0

    def _update_estimate(self):
        is_audio_only = self.audio_only_cb.isChecked()
        video_data = self.video_combo.currentData() if not is_audio_only else None
        audio_data = self.audio_combo.currentData()

        if not video_data and not audio_data:
            self.size_estimate_label.setText("—")
            return

        v_size, a_size, total = estimate_file_size(video_data, audio_data, self._duration)

        if is_audio_only:
            if a_size:
                self.size_estimate_label.setText(f"{_format_bytes(a_size)}  (Audio only)")
            else:
                self.size_estimate_label.setText("~Unknown")
        else:
            parts = []
            if v_size: parts.append(f"V: {_format_bytes(v_size)}")
            if a_size: parts.append(f"A: {_format_bytes(a_size)}")
            if total:
                detail = f"  ({' + '.join(parts)})" if parts else ""
                self.size_estimate_label.setText(f"~{_format_bytes(total)}{detail}")
            else:
                self.size_estimate_label.setText("~Unknown")

    def _get_selected_video_codec(self):
        data = self.video_combo.currentData()
        return data.get('codec', 'auto').lower() if data else 'auto'

    def _get_selected_audio_codec(self):
        data = self.audio_combo.currentData()
        return data.get('codec', 'auto').lower() if data else 'auto'


class ProgressWidget(QWidget):
    """Embedded download progress widget."""

    cancel_requested = Signal()  # Emitted when user clicks Cancel

    def __init__(self, video_info, parent=None):
        super().__init__(parent)
        self.video_info = video_info
        self._is_finished = False
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("glass_panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        title = self.video_info.get('title', 'Unknown Video')
        title_label = QLabel(title[:60] + "..." if len(title) > 60 else title)
        title_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title_label.setObjectName("section_title")
        layout.addWidget(title_label)

        stats_row = QHBoxLayout()
        self.status_label = QLabel("")
        dl_icon = get_resource_path("assets/icons/download.svg")
        if Path(dl_icon).exists():
            self.status_label.setText("  Starting...")
        else:
            self.status_label.setText("Starting...")
        self.status_label.setObjectName("speed_label")
        self.status_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        stats_row.addWidget(self.status_label)
        
        stats_row.addStretch()
        
        self.speed_label = QLabel("")
        self.speed_label.setObjectName("section_subtitle")
        self.speed_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.speed_label.setStyleSheet("color: #4cd7f6;")
        stats_row.addWidget(self.speed_label)
        layout.addLayout(stats_row)

        progress_info = QHBoxLayout()
        self.bytes_label = QLabel("")
        self.bytes_label.setObjectName("section_subtitle")
        self.bytes_label.setFont(QFont("Segoe UI", 9))
        progress_info.addWidget(self.bytes_label)
        progress_info.addStretch()
        self.percent_label = QLabel("0%")
        self.percent_label.setObjectName("section_subtitle")
        self.percent_label.setFont(QFont("Segoe UI", 9))
        progress_info.addWidget(self.percent_label)
        layout.addLayout(progress_info)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.cancel_btn = QPushButton("  Cancel")
        x_icon = get_resource_path("assets/icons/x.svg")
        if Path(x_icon).exists():
            self.cancel_btn.setIcon(QIcon(x_icon))
            self.cancel_btn.setIconSize(QSize(16, 16))
        self.cancel_btn.setMinimumHeight(36)
        self.cancel_btn.setStyleSheet("color: #ffb4ab;")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self._on_cancel_or_close)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

    def _on_cancel_or_close(self):
        if self._is_finished:
            # Download is done — just remove this widget
            self.setParent(None)
            self.deleteLater()
        else:
            # Download in progress — emit cancel signal
            self.cancel_requested.emit()

    def update_progress(self, progress, status):
        self.progress_bar.setValue(int(progress))
        self.percent_label.setText(f"{int(progress)}%")
        parts = [p.strip() for p in status.split("|")]
        if len(parts) >= 1:
            dl_icon = get_resource_path("assets/icons/download.svg")
            prefix = "  " if Path(dl_icon).exists() else ""
            self.status_label.setText(f"{prefix}{parts[0]}")
        if len(parts) >= 2: self.bytes_label.setText(parts[1])
        if len(parts) >= 3: self.speed_label.setText(parts[2])
        else: self.speed_label.setText("")

    def download_complete(self):
        self._is_finished = True
        
        dl_icon = get_resource_path("assets/icons/download.svg")
        prefix = "  " if Path(dl_icon).exists() else ""
        self.status_label.setText(f"{prefix}✅ Download completed!")
        self.status_label.setStyleSheet("color: #a8d5a2;")
        
        self.progress_bar.setValue(100)
        self.percent_label.setText("100%")
        check_icon = get_resource_path("assets/icons/check.svg")
        if Path(check_icon).exists():
            self.cancel_btn.setIcon(QIcon(check_icon))
        self.cancel_btn.setText("  Close")
        self.cancel_btn.setStyleSheet("color: #a8d5a2;")

    def download_failed(self, error_msg=""):
        self._is_finished = True
        display_msg = "Download failed!"
        if error_msg:
            short_err = error_msg[:120] + "..." if len(error_msg) > 120 else error_msg
            display_msg = f"Download failed: {short_err}"
            
        dl_icon = get_resource_path("assets/icons/download.svg")
        prefix = "  " if Path(dl_icon).exists() else ""
        self.status_label.setText(f"{prefix}{display_msg}")
        self.status_label.setStyleSheet("color: #ffb4ab;")
        self.cancel_btn.setText("  Dismiss")

