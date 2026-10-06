"""Generator tab plug-ins for the main converter window.

Every ``<name>_tab.py`` module in this package is discovered at startup and
added to the main window's tab bar after the ``Convert`` tab. A tab module
must define::

    TITLE = "Tab Title"

    def create_tab(host):
        ...  # return a QWidget

``host`` is the MainWindow and exposes:

* ``host.use_svg(path, preview=False)`` - load the generated SVG into Convert
* ``host.generator_status(text)`` - write the window status line
* ``host.log`` - the bottom log widget (a ``QTextEdit``)

Tabs must be self-contained: do not edit the main window, converter settings,
or another tab. Ported or vendored third-party code keeps its license and
attribution in a sibling ``<name>_NOTICE.md``.
"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent


def load_tabs(host):
    """Return ``[(title, widget_or_None, error_text), ...]`` for every tab."""
    tabs = []
    for path in sorted(PACKAGE.glob("*_tab.py")):
        title = path.stem.replace("_", " ").title()
        try:
            module = import_module(f"{__name__}.{path.stem}")
            title = str(getattr(module, "TITLE", title))
            widget = module.create_tab(host)
            tabs.append((title, widget, ""))
        except Exception as exc:  # one broken tab must not kill the window
            tabs.append((title, None, f"{type(exc).__name__}: {exc}"))
    return tabs
