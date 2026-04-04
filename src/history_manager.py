"""
History manager for Downloader PRO.
Persists download information to JSON to maintain a list of completed items across sessions.
"""

import json
from pathlib import Path


class HistoryManager:
    def __init__(self):
        self.config_dir = Path("config")
        self.history_file = self.config_dir / "history.json"
        self.history = self.load_history()

    def load_history(self):
        """Load download history from JSON file."""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Failed to load history: {e}")
            return []

    def save_history(self):
        """Save history list to file."""
        try:
            self.config_dir.mkdir(exist_ok=True)
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Failed to save history: {e}")

    def add_item(self, title, size, date, file_path):
        """Add a newly completed download to history."""
        item = {
            "title": title,
            "size": size,
            "date": date,
            "file_path": file_path
        }
        # Insert at top (newest first)
        self.history.insert(0, item)
        # Limit history to 500 items for performance
        if len(self.history) > 500:
            self.history = self.history[:500]
        self.save_history()

    def get_items(self, start=0, count=50):
        """Get a batch of history items for lazy loading."""
        return self.history[start : start + count]
