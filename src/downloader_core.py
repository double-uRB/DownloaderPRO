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


class YtDlpLogger:
    """Custom logger that captures yt-dlp output and drives progress updates."""

    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback

    def debug(self, msg):
        # yt-dlp sends download progress as debug messages
        log.debug("yt-dlp: %s", msg)
        if self.progress_callback and '[download]' in msg:
            self._parse_progress_line(msg)

    def info(self, msg):
        log.info("yt-dlp: %s", msg)

    def warning(self, msg):
        log.warning("yt-dlp: %s", msg)

    def error(self, msg):
        log.error("yt-dlp: %s", msg)

    def _parse_progress_line(self, msg):
        """Parse yt-dlp [download] lines like:
        [download]  45.2% of  120.50MiB at  5.23MiB/s ETA 00:12
        [download] 100% of  120.50MiB in 00:23
        [download] Destination: /path/to/file.mp4
        """
        try:
            # Match: XX.X% of XXXMiB at XXXMiB/s ETA XX:XX
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

            # Match: 100% of XXXMiB in XX:XX
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
        # Search locations for bundled/system ffmpeg
        ffmpeg_locations = []

        # 1. Search in PyInstaller bundle (Temporary Extraction Directory)
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            ffmpeg_locations.append(Path(sys._MEIPASS) / 'tools' / 'ffmpeg.exe')
            ffmpeg_locations.append(Path(sys._MEIPASS) / 'ffmpeg.exe')

        # 2. Search relative to EXE location (Portable/Side-by-side)
        if getattr(sys, 'frozen', False):
            base_path = Path(sys.executable).parent
            ffmpeg_locations.append(base_path / 'ffmpeg.exe')
            ffmpeg_locations.append(base_path / 'tools' / 'ffmpeg.exe')
        
        # 3. Search relative to script (Development)
        else:
            base_path = Path(__file__).parent.parent
            ffmpeg_locations.append(base_path / 'tools' / 'ffmpeg.exe')
            ffmpeg_locations.append(base_path / 'ffmpeg.exe')

        # 4. Standard system path
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

        # 1. Search in PyInstaller bundle (Temporary Extraction Directory)
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            aria2_locations.append(Path(sys._MEIPASS) / 'tools' / 'aria2c.exe')
            aria2_locations.append(Path(sys._MEIPASS) / 'aria2c.exe')

        # 2. Search relative to EXE location (Portable/Side-by-side)
        if getattr(sys, 'frozen', False):
            base_path = Path(sys.executable).parent
            aria2_locations.append(base_path / 'aria2c.exe')
            aria2_locations.append(base_path / 'tools' / 'aria2c.exe')
        
        # 3. Search relative to script (Development)
        else:
            base_path = Path(__file__).parent.parent
            aria2_locations.append(base_path / 'tools' / 'aria2c.exe')
            aria2_locations.append(base_path / 'aria2c.exe')

        self.aria2_path = None
        for location in aria2_locations:
            if Path(location).exists():
                self.aria2_path = str(location)
                break

        # 4. Standard system search
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
                    # Force cookie jar creation to verify access
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
        # Use ios, android, web clients to bypass 360p limits
        clients = ['ios', 'android', 'web']
        
        # Build extractor args with PO Token if available
        youtube_args = {'player_client': clients}
        if self.po_token:
            # Apply token to all supported clients as a safe bet
            youtube_args['po_token'] = [
                f"ios+{self.po_token}",
                f"android+{self.po_token}",
                f"web+{self.po_token}"
            ]

        opts = {
            'no_warnings': True,
            'logger': YtDlpLogger(progress_callback),
            'extractor_args': {'youtube': youtube_args},
        }

        # OAuth2 Login Support
        if self.use_oauth2:
            opts['username'] = 'oauth2'
            log.info("Using YouTube OAuth2 authentication")

        # Cookie handling: Prefer manual file, otherwise browser
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
        
        # If we're using OAuth2, we specify username=oauth2
        # On the first call, it might prompt, but we expect it to be cached
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                log.info("Video info fetched: %s", info.get('title', 'Unknown'))
                return info
        except Exception as e:
            log.error("Failed to fetch video info: %s", e, exc_info=True)
            return None

    def start_oauth_login(self, instructions_callback):
        """
        Start the yt-dlp OAuth2 login flow.
        Captures the 'Device Flow' instructions and passes them to the callback.
        """
        import subprocess
        log.info("Starting YouTube OAuth2 Login Flow")
        
        # We'll use a subprocess to run yt-dlp directly because we need to interact 
        # with its stdout specifically for the login code.
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--username", "oauth2",
            "--no-download-archive",
            "--flat-playlist",
            # We use a dummy URL to trigger the login check
            "https://www.youtube.com/watch?v=jvXVmvW8ZQw"
        ]
        
        try:
            # We want to capture the output to find the "To sign in..." message
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in process.stdout:
                log.debug("OAuth check: %s", line.strip())
                if "To sign in, use a web browser to open the page" in line:
                    # Capture "https://www.google.com/device" and "XXXX-XXXX"
                    # Format: To sign in, use a web browser to open the page https://www.google.com/device and enter the code ABCD-1234
                    match = re.search(r'page\s+(\S+)\s+and\s+enter\s+the\s+code\s+(\S+)', line)
                    if match:
                        url = match.group(1)
                        code = match.group(2)
                        instructions_callback(url, code)
                
                if "logged in" in line.lower() or "completed" in line.lower():
                    # Check for completion
                    pass

            process.wait()
            return True
        except Exception as e:
            log.error("OAuth login failed: %s", e)
            return False

    def download_video(self, url, quality, output_path, audio_only=False, progress_callback=None):
        """Download video with advanced quality selection support"""
        log.info("Download requested - quality='%s', audio_only=%s, url=%s", quality, audio_only, url)

        # Store progress callback for use in _progress_hook
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

        # Filename includes quality tag: "Video Title [1080p].mp4"
        quality_tag = f"{quality}p" if quality not in ('auto', 'best', 'worst') and '+' not in quality else "best"
        outtmpl = os.path.join(output_path, f'%(title)s [{quality_tag}].%(ext)s')

        # Build options (includes cookies + logger for progress)
        ydl_opts = self._get_base_opts(progress_callback)
        ydl_opts.update({
            'format': format_selector,
            'outtmpl': outtmpl,
            'noplaylist': True,
            'extract_flat': False,
            'postprocessors': postprocessors,
            'merge_output_format': 'mp4',
            'overwrites': True,
        })

        # Add FFmpeg path
        if self.ffmpeg_path:
            ydl_opts['ffmpeg_location'] = self.ffmpeg_path
            log.info("Using FFmpeg from: %s", self.ffmpeg_path)
        else:
            log.warning("FFmpeg not found - using single-stream fallback")
            if quality not in ('auto', 'best', 'worst') and '+' not in quality:
                ydl_opts['format'] = f'best[height<={quality}][ext=mp4]/best[ext=mp4]/best'
            else:
                ydl_opts['format'] = 'best[ext=mp4]/best'

        # Add external downloader (aria2c) if available
        if getattr(self, 'aria2_path', None):
            ydl_opts['external_downloader'] = self.aria2_path
            ydl_opts['external_downloader_args'] = ['-x', '16', '-s', '16', '-k', '1M']
            log.info("Using aria2c for multithreaded downloading")
        else:
            # Fallback to yt-dlp native concurrent fragment downloading
            ydl_opts['concurrent_fragment_downloads'] = 5

        # Also add progress hooks as secondary progress source
        if progress_callback:
            ydl_opts['progress_hooks'] = [self._progress_hook]

        log.info("Format selector: %s", ydl_opts['format'])

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            log.info("Download completed successfully")
            return True, None
        except Exception as e:
            log.error("Download failed: %s", e, exc_info=True)
            return False, str(e)

    def _progress_hook(self, d):
        """Handle download progress updates from yt-dlp (secondary source)."""
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
