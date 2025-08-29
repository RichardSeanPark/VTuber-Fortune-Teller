"""
Fortune VTuber Backend

Live2D Fortune VTuber Backend Service
"""

__version__ = "1.0.0"
__author__ = "Fortune VTuber Team"
__description__ = "Live2D Fortune VTuber Backend Service"

from .config.settings import get_settings
from .main import app

__all__ = ["app", "get_settings"]