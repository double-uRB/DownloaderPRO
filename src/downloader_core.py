import yt_dlp
import os
import sys
import re
import shutil
from pathlib import Path
from app_logger import get_logger

log = get_logger(__name__)


def _format_bytes(num_bytes):
    """Format bytes into human-readable string."""
    if not num_bytes:
        return "?"
    if num_bytes >= 1_073_741_824:
        return f"{num_bytes / 1_073_741_824:.1f} GB"
    elif num_bytes >= 1_048_576:
        return f"{num_bytes / 1_048_576:.1f} MB"
    elif num_bytes >= 1024:
        return f"{num_bytes / 1024:.0f} KB"
    return f"{num_bytes} B"


def _format_speed(speed):
    """Format download speed into human-readable string."""
    if not speed:
        return "-- MB/s"
    speed_mb = speed / (1024 * 1024)
    if speed_mb >= 1:
        return f"{speed_mb:.2f} MB/s"
    speed_kb = speed / 1024
    return f"{speed_kb:.1f} KB/s"


def _has_video(fmt):
    """Check if a format has a video stream."""
    vcodec = fmt.get('vcodec')
    return vcodec and vcodec not in ('none', 'None', '', '?')


def _has_audio(fmt):
    """Check if a format has an audio stream."""
    acodec = fmt.get('acodec')
    # yt-dlp returns '?' when it can't probe the codec (missing ffmpeg)
    # but the stream IS audio — accept it
    return acodec and acodec not in ('none', 'None', '')


def _normalize_codec(raw_codec):
    """Normalize raw codec string from yt-dlp to a user-friendly name."""
    if not raw_codec or raw_codec in ('none', 'None', ''):
        return None
    if raw_codec == '?':
        return 'Unknown'
    raw = raw_codec.lower()
    if 'avc1' in raw or 'h264' in raw:
        return 'H.264'
    elif 'hev1' in raw or 'hvc1' in raw or 'h265' in raw or 'hevc' in raw:
        return 'H.265'
    elif 'vp9' in raw or 'vp09' in raw:
        return 'VP9'
    elif 'av01' in raw or 'av1' in raw:
        return 'AV1'
    elif 'mp4a' in raw or 'aac' in raw:
        return 'AAC'
    elif 'opus' in raw:
        return 'Opus'
    elif 'vorbis' in raw:
        return 'Vorbis'
    elif 'mp3' in raw:
        return 'MP3'
    elif 'flac' in raw:
        return 'FLAC'
    elif 'ec-3' in raw or 'ec3' in raw:
        return 'Dolby Digital'
    elif 'ac-3' in raw or 'ac3' in raw:
        return 'AC-3'
    elif 'dtse' in raw or 'dts' in raw:
        return 'DTS'
    return raw_codec.split('.')[0].upper()


def _format_bitrate(bitrate_kbps):
    """Format bitrate in kbps to a human-readable string."""
    if not bitrate_kbps:
        return "? kbps"
    if bitrate_kbps >= 1000:
        return f"{bitrate_kbps / 1000:.1f} Mbps"
    return f"{bitrate_kbps:.0f} kbps"


def parse_available_streams(formats):
    """Parse yt-dlp format list into structured video and audio stream lists.
    
    Returns:
        dict with keys:
            'video_streams': list of dicts sorted by height desc, then bitrate desc
            'audio_streams': list of dicts sorted by bitrate desc
    """
    video_streams = []
    audio_streams = []

    if not formats:
        return {'video_streams': video_streams, 'audio_streams': audio_streams}

    seen_video = set()
    seen_audio = set()

    for fmt in formats:
        format_id = fmt.get('format_id', '')
        has_v = _has_video(fmt)
        has_a = _has_audio(fmt)
        
        # Fallback: yt-dlp marks audio-only streams with resolution='audio only'
        # even when acodec is None (happens when ffprobe is missing)
        resolution = fmt.get('resolution', '')
        is_audio_only_by_resolution = (resolution == 'audio only') and not has_v

        # Video-only streams (separate video tracks for merging)
        if has_v and not has_a:
            height = fmt.get('height', 0)
            if not height or height < 360:
                continue

            vcodec = fmt.get('vcodec', '')
            codec_name = _normalize_codec(vcodec)
            bitrate = fmt.get('vbr') or fmt.get('tbr') or 0
            filesize = fmt.get('filesize') or fmt.get('filesize_approx') or 0
            fps = fmt.get('fps', 0)
            dynamic_range = fmt.get('dynamic_range', 'SDR')
            
            # Deduplicate by (height, codec, rounded_bitrate)
            key = (height, codec_name, round(bitrate / 100) * 100)
            if key in seen_video:
                continue
            seen_video.add(key)

            video_streams.append({
                'format_id': format_id,
                'height': height,
                'codec': codec_name or 'Unknown',
                'raw_codec': vcodec,
                'bitrate': round(bitrate, 1),
                'filesize': filesize,
                'fps': fps or 30,
                'dynamic_range': dynamic_range if dynamic_range else 'SDR',
                'format_note': fmt.get('format_note', ''),
            })

        # Audio-only streams (detected by codec or by resolution='audio only')
        elif (has_a and not has_v) or is_audio_only_by_resolution:
            acodec = fmt.get('acodec', '') or ''
            codec_name = _normalize_codec(acodec) if acodec else 'Unknown'
            bitrate = fmt.get('abr') or fmt.get('tbr') or 0
            filesize = fmt.get('filesize') or fmt.get('filesize_approx') or 0
            channels = fmt.get('audio_channels') or 2
            sample_rate = fmt.get('asr', 0)
            language = fmt.get('language', '')
            
            # Deduplicate by (codec, rounded_bitrate)
            key = (codec_name, round(bitrate / 10) * 10)
            if key in seen_audio:
                continue
            seen_audio.add(key)

            audio_streams.append({
                'format_id': format_id,
                'codec': codec_name or 'Unknown',
                'raw_codec': acodec,
                'bitrate': round(bitrate, 1),
                'filesize': filesize,
                'channels': channels,
                'sample_rate': sample_rate,
                'language': language,
                'format_note': fmt.get('format_note', ''),
            })

    # Sort video: by height desc, then bitrate desc
    video_streams.sort(key=lambda s: (s['height'], s['bitrate']), reverse=True)
    # Sort audio: by bitrate desc
    audio_streams.sort(key=lambda s: s['bitrate'], reverse=True)

    # Fallback: if NO audio streams found, extract audio info from combined formats
    if not audio_streams:
        for fmt in formats:
            has_v = _has_video(fmt)
            has_a = _has_audio(fmt)
            if has_v and has_a:
                acodec = fmt.get('acodec', '') or ''
                codec_name = _normalize_codec(acodec) if acodec else 'Auto'
                abr = fmt.get('abr') or 128  # Default estimate
                audio_streams.append({
                    'format_id': fmt.get('format_id', ''),
                    'codec': codec_name or 'Auto',
                    'raw_codec': acodec,
                    'bitrate': round(abr, 1),
                    'filesize': 0,
                    'channels': fmt.get('audio_channels') or 2,
                    'sample_rate': fmt.get('asr', 0),
                    'language': fmt.get('language', ''),
                    'format_note': 'from combined stream',
                    'is_combined': True,
                })
        log.info("No dedicated audio streams found, extracted %d from combined formats",
                 len(audio_streams))

    log.info("Parsed streams: %d video, %d audio from %d total formats",
             len(video_streams), len(audio_streams), len(formats))
    
    return {'video_streams': video_streams, 'audio_streams': audio_streams}


def estimate_file_size(video_stream, audio_stream, duration):
    """Estimate total download size from selected streams and video duration.
    
    Returns: (video_bytes, audio_bytes, total_bytes)
    """
    video_size = 0
    audio_size = 0

    if video_stream:
        video_size = video_stream.get('filesize', 0) or 0
        # Only fall back to bitrate estimation if no filesize at all
        if not video_size and video_stream.get('bitrate') and duration:
            video_size = int(video_stream['bitrate'] * 1000 / 8 * duration)

    if audio_stream:
        audio_size = audio_stream.get('filesize', 0) or 0
        if not audio_size and audio_stream.get('bitrate') and duration:
            audio_size = int(audio_stream['bitrate'] * 1000 / 8 * duration)

    return video_size, audio_size, video_size + audio_size


class YtDlpLogger:
    """Custom logger that captures yt-dlp output and drives progress updates."""

    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback

    def debug(self, msg):
        log.debug("yt-dlp: %s", msg)
        if self.progress_callback and '[download]' in msg:
            self._parse_progress_line(msg)
        elif self.progress_callback and '[#' in msg:
            self._parse_aria2_line(msg)

    def info(self, msg):
        log.info("yt-dlp: %s", msg)

    def warning(self, msg):
        log.warning("yt-dlp: %s", msg)

    def error(self, msg):
        log.error("yt-dlp: %s", msg)

    def _parse_progress_line(self, msg):
        """Parse yt-dlp [download] lines."""
        try:
            match = re.search(
                r'(\d+\.?\d*)%\s+of\s+~?([\d.]+)(\w+)\s+at\s+([\d.]+)(\w+/s)\s+ETA\s+(\S+)',
                msg
            )
            if match:
                percent = float(match.group(1))
                total_size = match.group(2) + match.group(3)
                speed = match.group(4) + " " + match.group(5)
                eta = match.group(6)
                status = f"{speed} | {total_size} | ETA {eta}"
                self.progress_callback(percent, status)
                return

            match = re.search(
                r'100%\s+of\s+~?([\d.]+)(\w+)\s+in\s+(\S+)',
                msg
            )
            if match:
                total_size = match.group(1) + match.group(2)
                self.progress_callback(95, f"Processing... ({total_size})")
                return
        except Exception as e:
            log.debug("Progress parse error: %s", e)

    def _parse_aria2_line(self, msg):
        """Parse aria2c progress output."""
        try:
            match = re.search(
                r'\[#\w+\s+([\d.]+\w+)/([\d.]+\w+)\((\d+)%\).*?DL:([\d.]+\w+)',
                msg
            )
            if match:
                downloaded = match.group(1)
                total = match.group(2)
                percent = float(match.group(3))
                speed = match.group(4) + "/s"
                status = f"{speed} | {downloaded}/{total} | Downloading..."
                self.progress_callback(min(percent, 99), status)
        except Exception as e:
            log.debug("Aria2 progress parse error: %s", e)


class VideoDownloader:
    def __init__(self, po_token="", cookies_path="", use_oauth2=False):
        self.current_download = None
        self.po_token = po_token
        self.cookies_path = cookies_path
        self.use_oauth2 = use_oauth2
        self.setup_ffmpeg_path()
        self.setup_aria2_path()
        self._cookie_browser = self._detect_cookie_browser() if not cookies_path else None

    def set_advanced_settings(self, po_token, cookies_path, use_oauth2=False):
        """Update settings dynamically."""
        self.po_token = po_token
        self.cookies_path = cookies_path
        self.use_oauth2 = use_oauth2
        if cookies_path:
            self._cookie_browser = None
        elif not self._cookie_browser:
            self._cookie_browser = self._detect_cookie_browser()

    def setup_ffmpeg_path(self):
        """Setup FFmpeg path for both development and packaged app"""
        ffmpeg_locations = []
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            ffmpeg_locations.append(Path(sys._MEIPASS) / 'tools' / 'ffmpeg.exe')
            ffmpeg_locations.append(Path(sys._MEIPASS) / 'ffmpeg.exe')
        if getattr(sys, 'frozen', False):
            base_path = Path(sys.executable).parent
            ffmpeg_locations.append(base_path / 'ffmpeg.exe')
            ffmpeg_locations.append(base_path / 'tools' / 'ffmpeg.exe')
        else:
            base_path = Path(__file__).parent.parent
            ffmpeg_locations.append(base_path / 'tools' / 'ffmpeg.exe')
            ffmpeg_locations.append(base_path / 'ffmpeg.exe')
        ffmpeg_locations.append(Path('ffmpeg.exe'))

        self.ffmpeg_path = None
        for location in ffmpeg_locations:
            if Path(location).exists() or (isinstance(location, str) and shutil.which(location)):
                self.ffmpeg_path = str(location)
                break
        if self.ffmpeg_path:
            log.info("FFmpeg found at: %s", self.ffmpeg_path)
        else:
            log.warning("FFmpeg NOT FOUND - video+audio merging will be unavailable")

    def setup_aria2_path(self):
        """Setup aria2c path for both development and packaged app"""
        aria2_locations = []
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            aria2_locations.append(Path(sys._MEIPASS) / 'tools' / 'aria2c.exe')
            aria2_locations.append(Path(sys._MEIPASS) / 'aria2c.exe')
        if getattr(sys, 'frozen', False):
            base_path = Path(sys.executable).parent
            aria2_locations.append(base_path / 'aria2c.exe')
            aria2_locations.append(base_path / 'tools' / 'aria2c.exe')
        else:
            base_path = Path(__file__).parent.parent
            aria2_locations.append(base_path / 'tools' / 'aria2c.exe')
            aria2_locations.append(base_path / 'aria2c.exe')

        self.aria2_path = None
        for location in aria2_locations:
            if Path(location).exists():
                self.aria2_path = str(location)
                break
        if not self.aria2_path and shutil.which('aria2c'):
            self.aria2_path = 'aria2c'
        if self.aria2_path:
            log.info("aria2c found for multithreaded downloads at: %s", self.aria2_path)
        else:
            log.warning("aria2c NOT FOUND - falling back to native yt-dlp downloading")

    def _detect_cookie_browser(self):
        """Try each browser to find one whose cookies are accessible."""
        for browser in ('edge', 'chrome', 'firefox', 'brave', 'opera'):
            try:
                test_opts = {'cookiesfrombrowser': (browser,), 'quiet': True}
                with yt_dlp.YoutubeDL(test_opts) as ydl:
                    _ = ydl.cookiejar
                log.info("Browser cookies available: %s", browser)
                return browser
            except Exception as e:
                log.debug("Cannot use %s cookies: %s", browser, e)
                continue
        log.warning("No browser cookies available - requests may be rate-limited by YouTube")
        return None

    def _get_base_opts(self, progress_callback=None):
        """Common yt-dlp options shared across info fetching and downloading."""
        clients = ['ios', 'android', 'web']
        youtube_args = {'player_client': clients}
        if self.po_token:
            youtube_args['po_token'] = [
                f"ios+{self.po_token}",
                f"android+{self.po_token}",
                f"web+{self.po_token}"
            ]
        opts = {
            'logger': YtDlpLogger(progress_callback),
            'extractor_args': {'youtube': youtube_args},
        }
        # Provide ffmpeg path for format probing (critical for audio stream detection)
        if self.ffmpeg_path:
            opts['ffmpeg_location'] = self.ffmpeg_path
        if self.use_oauth2:
            opts['username'] = 'oauth2'
            log.info("Using YouTube OAuth2 authentication")
        if self.cookies_path and os.path.exists(self.cookies_path):
            opts['cookiefile'] = self.cookies_path
            log.info("Using custom cookies from: %s", self.cookies_path)
        elif self._cookie_browser:
            opts['cookiesfrombrowser'] = (self._cookie_browser,)
        return opts

    def get_video_info(self, url):
        """Get video information without downloading"""
        log.info("Fetching video info for: %s", url)
        opts = self._get_base_opts()
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                log.info("Video info fetched: %s (%d formats available)",
                         info.get('title', 'Unknown'),
                         len(info.get('formats', [])))
                return info
        except Exception as e:
            log.error("Failed to fetch video info: %s", e, exc_info=True)
            return None

    def start_oauth_login(self, instructions_callback):
        """Start the yt-dlp OAuth2 login flow."""
        import subprocess
        log.info("Starting YouTube OAuth2 Login Flow")
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--username", "oauth2",
            "--no-download-archive",
            "--flat-playlist",
            # We must provide *some* valid URL to trigger the yt-dlp extractor
            # which in turn triggers the OAuth2 device auth flow.
            # Using YouTube's first video ("Me at the zoo") as a neutral standard dummy link.
            "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        ]
        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )
            for line in process.stdout:
                log.debug("OAuth check: %s", line.strip())
                if "To sign in, use a web browser to open the page" in line:
                    match = re.search(r'page\s+(\S+)\s+and\s+enter\s+the\s+code\s+(\S+)', line)
                    if match:
                        instructions_callback(match.group(1), match.group(2))
                if "logged in" in line.lower() or "completed" in line.lower():
                    pass
            # Use bounded timeout for the OAuth completion
            try:
                process.wait(timeout=120)
            except subprocess.TimeoutExpired:
                process.kill()
                process.stdout.close()
                log.error("YouTube OAuth login timed out after 120 seconds")
                return False

            return True
        except Exception as e:
            log.error("OAuth login failed: %s", e)
            return False

    def _build_common_download_opts(self, output_path, quality_tag, progress_callback):
        """Build shared download options for both simple and advanced modes."""
        outtmpl = os.path.join(output_path, f'%(title)s [{quality_tag}].%(ext)s')
        ydl_opts = self._get_base_opts(progress_callback)
        ydl_opts.update({
            'outtmpl': outtmpl,
            'noplaylist': True,
            'extract_flat': False,
            'merge_output_format': 'mp4',
            'overwrites': True,
        })
        if self.ffmpeg_path:
            ydl_opts['ffmpeg_location'] = self.ffmpeg_path
            log.info("Using FFmpeg from: %s", self.ffmpeg_path)
        if getattr(self, 'aria2_path', None):
            ydl_opts['external_downloader'] = self.aria2_path
            ydl_opts['external_downloader_args'] = [
                '-x', '16', '-s', '16', '-k', '1M',
                '--summary-interval=1'
            ]
            log.info("Using aria2c for multithreaded downloading")
        else:
            ydl_opts['concurrent_fragment_downloads'] = 5
        if progress_callback:
            self.progress_callback = progress_callback
            ydl_opts['progress_hooks'] = [self._progress_hook]
        return ydl_opts

    def download_video(self, url, quality, output_path, audio_only=False, progress_callback=None):
        """Download video with simple quality selection (backward-compatible)."""
        log.info("Download requested - quality='%s', audio_only=%s, url=%s", quality, audio_only, url)
        self.progress_callback = progress_callback

        if audio_only:
            format_selector = 'bestaudio/best'
            postprocessors = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            if '+' in quality:
                format_selector = quality
            elif quality == "auto":
                format_selector = 'bestvideo+bestaudio/best'
            elif quality in ['best', 'worst']:
                format_selector = quality
            else:
                format_selector = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best'
            postprocessors = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }]

        quality_tag = f"{quality}p" if quality not in ('auto', 'best', 'worst') and '+' not in quality else "best"
        ydl_opts = self._build_common_download_opts(output_path, quality_tag, progress_callback)
        ydl_opts['format'] = format_selector
        ydl_opts['postprocessors'] = postprocessors

        if not self.ffmpeg_path and not audio_only:
            log.warning("FFmpeg not found - using single-stream fallback")
            if quality not in ('auto', 'best', 'worst') and '+' not in quality:
                ydl_opts['format'] = f'best[height<={quality}][ext=mp4]/best[ext=mp4]/best'
            else:
                ydl_opts['format'] = 'best[ext=mp4]/best'

        log.info("Format selector: %s", ydl_opts['format'])
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            log.info("Download completed successfully")
            return True, None
        except Exception as e:
            log.error("Download failed: %s", e, exc_info=True)
            return False, str(e)

    def download_video_advanced(self, url, video_format_id, audio_format_id, output_path,
                                 quality_tag="custom", progress_callback=None):
        """Download video using exact format IDs selected by the user in Advanced mode."""
        format_selector = f"{video_format_id}+{audio_format_id}"
        log.info("Advanced download - format='%s', url=%s", format_selector, url)
        self.progress_callback = progress_callback

        ydl_opts = self._build_common_download_opts(output_path, quality_tag, progress_callback)
        ydl_opts['format'] = format_selector
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4'
        }]

        if not self.ffmpeg_path:
            log.error("FFmpeg required for advanced download but not found")
            return False, "FFmpeg is required for Advanced Download mode."

        log.info("Advanced format selector: %s", format_selector)
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            log.info("Advanced download completed successfully")
            return True, None
        except Exception as e:
            log.error("Advanced download failed: %s", e, exc_info=True)
            return False, str(e)

    def download_audio_advanced(self, url, audio_format_id, output_path,
                                 quality_tag="audio", progress_callback=None):
        """Download audio-only using exact format ID selected by the user."""
        log.info("Advanced audio download - format='%s', url=%s", audio_format_id, url)
        self.progress_callback = progress_callback

        ydl_opts = self._build_common_download_opts(output_path, quality_tag, progress_callback)
        ydl_opts['format'] = audio_format_id
        # Don't merge to MP4, just extract audio
        ydl_opts.pop('merge_output_format', None)

        if not self.ffmpeg_path:
            log.error("FFmpeg required for advanced audio download but not found")
            return False, "FFmpeg is required for Advanced Audio Download."
            
        ydl_opts['ffmpeg_location'] = self.ffmpeg_path
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '0',  # Use source quality
        }]

        log.info("Audio format selector: %s", audio_format_id)
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            log.info("Audio download completed successfully")
            return True, None
        except Exception as e:
            log.error("Audio download failed: %s", e, exc_info=True)
            return False, str(e)

    def _progress_hook(self, d):
        """Handle download progress updates from yt-dlp (primary source)."""
        if not hasattr(self, 'progress_callback') or not self.progress_callback:
            return
        try:
            status = d.get('status', 'unknown')
            if status == 'downloading':
                downloaded = d.get('downloaded_bytes', 0) or 0
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                speed = d.get('speed', 0) or 0
                eta = d.get('eta', None)

                if total > 0:
                    progress = min((downloaded / total) * 100, 100)
                else:
                    progress = 0

                speed_str = _format_speed(speed)
                total_str = _format_bytes(total) if total else "?"
                downloaded_str = _format_bytes(downloaded)

                eta_str = ""
                if eta:
                    if eta >= 3600:
                        eta_str = f" | ETA {eta // 3600}h {(eta % 3600) // 60}m"
                    elif eta >= 60:
                        eta_str = f" | ETA {eta // 60}m {eta % 60}s"
                    else:
                        eta_str = f" | ETA {eta}s"

                status_msg = f"{speed_str} | {downloaded_str}/{total_str}{eta_str}"
                self.progress_callback(progress, status_msg)

            elif status == 'finished':
                filesize = d.get('total_bytes') or d.get('total_bytes_estimate') or d.get('downloaded_bytes', 0)
                size_str = _format_bytes(filesize)
                log.info("Stream finished, size: %s. Merging/processing...", size_str)
                self.progress_callback(95, f"Processing... ({size_str})")
        except Exception as e:
            log.warning("Progress hook error: %s", e)
