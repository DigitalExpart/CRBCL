"""
CRBCL Platform — Application Configuration.

Re-exports from __init__ for explicit import path.
"""

from app.core import Settings, get_settings

__all__ = ["Settings", "get_settings"]
