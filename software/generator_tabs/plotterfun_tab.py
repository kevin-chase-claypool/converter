"""Plotterfun tab: the vendored mitxela/plotterfun web app.

Plotterfun is a 22-algorithm image-to-vector web app (MIT). Porting it to
Python would duplicate the existing fills and lose its interactive workflow,
so the upstream static site is vendored under ``software/plotterfun_vendor``
and embedded with QtWebEngine, following the Kaleidoscope Maps-tab pattern.
Interaction (image loading, algorithm, sliders, live SVG) happens inside the
page; **Export SVG to plot** captures the current ``<svg>`` with
``XMLSerializer`` and hands it to the Convert artwork pipeline.
"""

from __future__ import annotations

from pathlib import Path

from ._plotterfun_web import HAVE_WEBENGINE, PlotterfunWebTab


TITLE = "Plotterfun"
ORDER = 130

VENDOR_PAGE = (
    Path(__file__).resolve().parents[1] / "plotterfun_vendor" / "main.htm"
)

class PlotterfunTab(PlotterfunWebTab):
    GROUP = "Photo-based"
    DESCRIPTION = "The full Plotterfun web app (22 algorithms), vendored."

    def __init__(self, host):
        super().__init__(
            host,
            title=TITLE,
            description=self.DESCRIPTION,
            page_path=VENDOR_PAGE,
            export_slug="plotterfun",
        )


def create_tab(host):
    return PlotterfunTab(host)
