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
        "Experimental independent-channel comparison; use CMYK Photo for "
        "color matching."
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
            simple_workflow=True,
        )


def create_tab(host):
    return PlotterfunExtendedTab(host)
