"""Plotterfun Extended tab: local build of msurguy/plotterfun-extended."""

from __future__ import annotations

from pathlib import Path

from ._plotterfun_web import PlotterfunWebTab


TITLE = "Plotterfun Extended"
ORDER = 131

VENDOR_PAGE = (
    Path(__file__).resolve().parents[1]
    / "plotterfun_extended_vendor"
    / "index.html"
)


class PlotterfunExtendedTab(PlotterfunWebTab):
    GROUP = "Photo-based"
    DESCRIPTION = (
        "Locally built Plotterfun Extended with 40 algorithms, CMYK/RGB/"
        "custom channels, and optional depth or face masks."
    )

    def __init__(self, host):
        super().__init__(
            host,
            title=TITLE,
            description=self.DESCRIPTION,
            page_path=VENDOR_PAGE,
            export_slug="plotterfun-extended",
            serve_http=True,
            allow_current_artwork=True,
        )


def create_tab(host):
    return PlotterfunExtendedTab(host)
