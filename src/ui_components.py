"""
Modern UI components for Downloader PRO.
Card-based quality selector, video info panel with thumbnail, and embedded progress widget.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton, QProgressBar, QSizePolicy, QGridLayout
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtCore import QUrl


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

        # ── Container card ──
        self.card = QWidget()
        self.card.setObjectName("surface_card")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # ── Thumbnail area ──
        self.thumbnail_container = QWidget()
        self.thumbnail_container.setMinimumHeight(280)
        self.thumbnail_container.setMaximumHeight(400)
        self.thumbnail_container.setStyleSheet("background-color: #060e20; border-radius: 12px 12px 0 0;")
        thumb_layout = QVBoxLayout(self.thumbnail_container)
        thumb_layout.setContentsMargins(0, 0, 0, 0)

        self.thumbnail_label = QLabel("📹")
        self.thumbnail_label.setFont(QFont("Segoe UI", 60))
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        thumb_layout.addWidget(self.thumbnail_label)

        # Duration & HD badges (overlaid at the bottom)
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

        # ── Info section ──
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(20, 16, 20, 20)
        info_layout.setSpacing(12)

        # Title row
        title_row = QHBoxLayout()
        self.title_label = QLabel("")
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.title_label.setWordWrap(True)
        self.title_label.setObjectName("section_title")
        title_row.addWidget(self.title_label)
        info_layout.addLayout(title_row)

        # Channel row
        channel_row = QHBoxLayout()
        channel_row.setSpacing(10)

        self.channel_label = QLabel("")
        self.channel_label.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        channel_row.addWidget(self.channel_label)

        channel_row.addStretch()
        info_layout.addLayout(channel_row)

        # Stats row (Views / Published / Likes)
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

        # Description
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

        # Store reference for updates
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
        """Update all fields from yt-dlp video_info dict."""
        title = video_info.get('title', 'Unknown Title')
        duration = video_info.get('duration', 0)
        uploader = video_info.get('uploader', 'Unknown')
        view_count = video_info.get('view_count', 0)
        like_count = video_info.get('like_count', 0)
        upload_date = video_info.get('upload_date', '')
        description = video_info.get('description', '')

        self.title_label.setText(title)
        self.channel_label.setText(f"👤 {uploader}")

        # Duration badge
        if duration:
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60
            dur_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"
            self.duration_badge.setText(dur_str)
            self.duration_badge.setVisible(True)
            self.hd_badge.setVisible(True)

        # Stats
        self.views_widget._value_label.setText(self._format_number(view_count))
        self.likes_widget._value_label.setText(self._format_number(like_count))

        if upload_date and len(upload_date) == 8:
            formatted_date = f"{upload_date[6:8]}/{upload_date[4:6]}/{upload_date[:4]}"
            self.date_widget._value_label.setText(formatted_date)

        # Description
        if description:
            self.description_label.setText(description[:300])
            if len(description) > 100:
                self.show_more_btn.setVisible(True)

        # Thumbnail
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
        """Download and display the video thumbnail."""
        request = QNetworkRequest(QUrl(url))
        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self._on_thumbnail_loaded(reply))

    def _on_thumbnail_loaded(self, reply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                scaled = pixmap.scaledToWidth(
                    self.thumbnail_container.width(),
                    Qt.TransformationMode.SmoothTransformation
                )
                self.thumbnail_label.setPixmap(scaled)
                self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        reply.deleteLater()


class QualityCard(QPushButton):
    """A single quality option card matching the Stitch design."""

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

        # Resolution badge
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

        # Text info
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

        # HDR badge or check badge
        if is_hdr:
            hdr = QLabel("HDR")
            hdr.setObjectName("badge_hdr")
            hdr.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            layout.addWidget(hdr)

        # Checkmark (shown when selected)
        self.check_label = QLabel("✅")
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
    """Card-based quality selector matching the Stitch design."""

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

        # Title
        title_row = QHBoxLayout()
        icon = QLabel("🎬")
        icon.setFont(QFont("Segoe UI", 14))
        title_row.addWidget(icon)

        title = QLabel("Select Quality")
        title.setObjectName("section_title")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_row.addWidget(title)
        title_row.addStretch()
        layout.addLayout(title_row)

        # Quality cards
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

            # Default select first
            if i == 0:
                card.set_selected(True)
                self.selected_quality = qinfo.get("height", "auto")

    def _parse_formats(self):
        """Parse yt-dlp formats into card-friendly options."""
        options = [{
            "format_id": "auto",
            "height": "auto",
            "resolution": "Best Available",
            "video_codec": "Auto Select",
            "size_estimate": "Best",
            "is_hdr": False,
        }]

        if not self.formats:
            return options

        seen_heights = set()
        video_formats = []

        for fmt in self.formats:
            vcodec = fmt.get('vcodec', 'none')
            height = fmt.get('height', 0)
            if vcodec == 'none' or height < 360 or height in seen_heights:
                continue
            seen_heights.add(height)
            video_formats.append(fmt)

        # Sort by resolution descending
        video_formats.sort(key=lambda f: f.get('height', 0), reverse=True)

        for fmt in video_formats[:5]:
            height = fmt.get('height', 0)
            vcodec = fmt.get('vcodec', '')
            format_note = fmt.get('format_note', '').lower()
            filesize = fmt.get('filesize', 0) or fmt.get('filesize_approx', 0)

            # Codec name
            codec_name = "Auto"
            if 'avc1' in vcodec or 'h264' in vcodec.lower():
                codec_name = "H.264"
            elif 'vp9' in vcodec.lower():
                codec_name = "VP9"
            elif 'av01' in vcodec.lower():
                codec_name = "AV1"

            # Resolution label
            res_label = f"{height}p"
            if height >= 2160:
                res_label += " (Ultra HD)"
            elif height >= 1080:
                res_label += " (Full HD)"
            elif height >= 720:
                res_label += " (HD)"

            # Size estimate
            if filesize:
                if filesize >= 1_073_741_824:
                    size_str = f"{filesize / 1_073_741_824:.1f} GB"
                else:
                    size_str = f"{filesize / 1_048_576:.0f} MB"
            else:
                size_str = "~Unknown"

            is_hdr = any(h in format_note for h in ['hdr', 'hdr10', 'dolby'])

            options.append({
                "format_id": fmt.get('format_id', 'unknown'),
                "height": str(height),
                "resolution": res_label,
                "video_codec": codec_name,
                "size_estimate": size_str,
                "is_hdr": is_hdr,
            })

        return options

    def _on_card_selected(self, format_id):
        for card in self.quality_cards:
            if card.format_id == format_id:
                self.selected_quality = card.height
            card.set_selected(card.format_id == format_id)

    def get_selected_quality(self):
        return self.selected_quality


class ProgressWidget(QWidget):
    """Embedded download progress widget (replaces the old dialog)."""

    def __init__(self, video_info, parent=None):
        super().__init__(parent)
        self.video_info = video_info
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("glass_panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Title
        title = self.video_info.get('title', 'Unknown Video')
        title_label = QLabel(title[:60] + "..." if len(title) > 60 else title)
        title_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title_label.setObjectName("section_title")
        layout.addWidget(title_label)

        # Speed + ETA row
        stats_row = QHBoxLayout()

        self.speed_label = QLabel("📥 Starting...")
        self.speed_label.setObjectName("speed_label")
        self.speed_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        stats_row.addWidget(self.speed_label)

        stats_row.addStretch()

        self.eta_label = QLabel("")
        self.eta_label.setObjectName("section_subtitle")
        self.eta_label.setFont(QFont("Segoe UI", 10))
        stats_row.addWidget(self.eta_label)

        layout.addLayout(stats_row)

        # Progress details
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

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.pause_btn = QPushButton("⏸  Pause")
        self.pause_btn.setFixedHeight(36)
        btn_row.addWidget(self.pause_btn)

        self.cancel_btn = QPushButton("✕  Cancel")
        self.cancel_btn.setFixedHeight(36)
        self.cancel_btn.setStyleSheet("color: #ffb4ab;")
        btn_row.addWidget(self.cancel_btn)

        layout.addLayout(btn_row)

    def update_progress(self, progress, status):
        self.progress_bar.setValue(int(progress))
        self.percent_label.setText(f"{int(progress)}%")

        # Parse rich status: "speed | downloaded/total | ETA Xs"
        parts = [p.strip() for p in status.split("|")]
        if len(parts) >= 1:
            self.speed_label.setText(parts[0])       # e.g. "2.50 MB/s"
        if len(parts) >= 2:
            self.bytes_label.setText(parts[1])        # e.g. "45.2 MB/120.0 MB"
        if len(parts) >= 3:
            self.eta_label.setText(parts[2])           # e.g. "ETA 30s"
        else:
            self.eta_label.setText("")

    def download_complete(self):
        self.speed_label.setText("✅ Download completed!")
        self.progress_bar.setValue(100)
        self.percent_label.setText("100%")
        self.pause_btn.setVisible(False)
        self.cancel_btn.setText("Close")

    def download_failed(self, error_msg=""):
        display_msg = "Download failed!"
        if error_msg:
            # Truncate long error messages for UI display
            short_err = error_msg[:120] + "..." if len(error_msg) > 120 else error_msg
            display_msg = f"Download failed: {short_err}"
        self.speed_label.setText(display_msg)
        self.speed_label.setStyleSheet("color: #ffb4ab;")
        self.pause_btn.setVisible(False)
        self.cancel_btn.setText("Close")
