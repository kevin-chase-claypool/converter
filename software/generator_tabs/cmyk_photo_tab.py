"""Guided CMYK Photo generator tab.

The original full :class:`CmykTab` remains registered by ``cmyk_tab.py``.
This module exposes the guided photo workflow as a separate tool page without
removing the complete CMYK tuner from the Tools list.
"""

from .cmyk_tab import CmykPhotoTab


TITLE = "CMYK Photo"
ORDER = 26
GROUP = "Photo-based"
DESCRIPTION = "One-action color workflow with advanced controls behind it."


def create_tab(host):
    return CmykPhotoTab(host)
