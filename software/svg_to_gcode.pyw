import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from converter_core import *


def _main():
    if len(sys.argv) == 3:
        settings = Settings()
        contours, lines = convert_file(sys.argv[1], sys.argv[2], settings)
        print(f"Converted {contours} contours to {lines} G-code lines: {sys.argv[2]}")
        return 0
    print("svg_to_gcode.pyw is now the converter engine shim. Run qt_svg_to_gcode.pyw for the desktop app, or pass: input.svg output.gcode")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

