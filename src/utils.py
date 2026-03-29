import os
import sys
from pathlib import Path

def get_resource_path(relative_path):
    """
    Get the absolute path to a resource, supporting both development and PyInstaller bundles.
    
    PyInstaller extracts resources to a temporary folder (sys._MEIPASS).
    In development, the resource is relative to the project root.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    except Exception:
        # Fallback to the real directory containing the app sources
        # (project root, assuming utils.py is in src/)
        base_path = Path(__file__).parent.parent

    resource_path = base_path / relative_path
    
    if not resource_path.exists():
        # Debugging aid for bundling issues
        print(f"⚠️  Resource NOT FOUND: {resource_path}")
        
    return str(resource_path)
