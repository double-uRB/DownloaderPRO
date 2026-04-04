"""
Settings persistence manager for Downloader PRO using Qt's native QSettings.
"""

import json
import os
import keyring
from pathlib import Path
from PySide6.QtCore import QSettings


class SettingsManager:
    # Keyring constants
    APP_NAME = "DownloaderPRO"
    PO_TOKEN_KEY = "po_token"

    def __init__(self):
        # organization="DownloaderPRO", application="DownloaderPRO"
        # On Windows, this goes to Registry: Computer\HKEY_CURRENT_USER\Software\DownloaderPRO\DownloaderPRO
        self.qsettings = QSettings(self.APP_NAME, self.APP_NAME)
        
        self.default_settings = {
            "theme": "dark",
            "download_path": str(Path.home() / "Downloads"),
            "last_quality": "auto",
            "audio_only": False,
            "window_geometry": "1100x750",
            "filename_pattern": "{date}_{filename}.{ext}",
            "auto_resume": True,
            "max_concurrent": 5,
            "speed_limit": 0,
            "thread_intensity": "high",
            "cookies_path": "",
            "use_oauth2": False,
            "advanced_mode_enabled": False,
            "preferred_video_codec": "auto",
            "preferred_audio_codec": "auto",
            "preferred_bitrate_mode": "balanced",
            "preferred_bitrate_custom": 0,
        }
        
        # Check for legacy JSON to migrate (to avoid losing user settings)
        self._migrate_legacy_json()
        
        # Migrate po_token from QSettings to Keyring if found in Registry
        self._migrate_po_token_to_keyring()

    def _migrate_legacy_json(self):
        """One-time migration from settings.json to QSettings."""
        legacy_path = Path("config/settings.json")
        if legacy_path.exists():
            try:
                with open(legacy_path, 'r') as f:
                    legacy_data = json.load(f)
                    for key, value in legacy_data.items():
                        # Handle po_token separately if present in legacy
                        if key == "po_token":
                            keyring.set_password(self.APP_NAME, self.PO_TOKEN_KEY, str(value))
                        else:
                            self.qsettings.setValue(key, value)
                
                # Rename the file so we don't migrate again every time
                new_name = legacy_path.with_suffix(".json.migrated")
                legacy_path.rename(new_name)
            except Exception:
                pass

    def _migrate_po_token_to_keyring(self):
        """Move PO token from Registry to system's secure store."""
        reg_token = self.qsettings.value("po_token", "")
        if reg_token:
            try:
                keyring.set_password(self.APP_NAME, self.PO_TOKEN_KEY, str(reg_token))
                self.qsettings.remove("po_token")
            except Exception:
                pass

    def get(self, key, default=None):
        """Base getter with default fallback."""
        val = self.qsettings.value(key, self.default_settings.get(key, default))
        if isinstance(self.default_settings.get(key), bool) and isinstance(val, str):
            return val.lower() == 'true'
        if isinstance(self.default_settings.get(key), int) and val is not None:
            try: return int(val)
            except: pass
        return val

    def set(self, key, value):
        """Base setter."""
        self.qsettings.setValue(key, value)

    def get_theme(self): return self.get("theme", "dark")
    def set_theme(self, theme): self.set("theme", theme)

    def get_download_path(self): return self.get("download_path", str(Path.home() / "Downloads"))
    def set_download_path(self, path): self.set("download_path", path)

    def get_last_quality(self): return self.get("last_quality", "auto")
    def set_last_quality(self, quality): self.set("last_quality", quality)

    def get_po_token(self):
        """Retrieve securely stored token."""
        try:
            return keyring.get_password(self.APP_NAME, self.PO_TOKEN_KEY) or ""
        except Exception:
            return ""

    def set_po_token(self, token):
        """Store token securely using DPAPI/Credential Manager."""
        try:
            keyring.set_password(self.APP_NAME, self.PO_TOKEN_KEY, token)
        except Exception:
            pass

    def get_cookies_path(self): return self.get("cookies_path", "")
    def set_cookies_path(self, path): self.set("cookies_path", path)

    def get_use_oauth2(self): return self.get("use_oauth2", False)
    def set_use_oauth2(self, enabled): self.set("use_oauth2", enabled)

    def get_advanced_mode(self): return self.get("advanced_mode_enabled", False)
    def set_advanced_mode(self, enabled): self.set("advanced_mode_enabled", enabled)

    def get_preferred_video_codec(self): return self.get("preferred_video_codec", "auto")
    def set_preferred_video_codec(self, codec): self.set("preferred_video_codec", codec)

    def get_preferred_audio_codec(self): return self.get("preferred_audio_codec", "auto")
    def set_preferred_audio_codec(self, codec): self.set("preferred_audio_codec", codec)

    def get_preferred_bitrate_mode(self): return self.get("preferred_bitrate_mode", "balanced")
    def set_preferred_bitrate_mode(self, mode): self.set("preferred_bitrate_mode", mode)

    def get_preferred_bitrate_custom(self): return self.get("preferred_bitrate_custom", 0)
    def set_preferred_bitrate_custom(self, kbps): self.set("preferred_bitrate_custom", kbps)
