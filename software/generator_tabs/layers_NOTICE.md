# Layers tab - third-party notice

The Layers tab re-implements the colour-splitting concept of the MIT-licensed
**jdbrande/Svg-Layer-Painter**
(https://github.com/jdbrande/Svg-Layer-Painter): drawable SVG elements are
grouped by stroke (or fill) colour and written as separate per-layer SVG
files.

The Python implementation in `layers_tab.py` uses `xml.etree.ElementTree` to
prune a deep copy of the document while preserving its structure (groups and
transforms); no upstream code was copied.
