"""Static and numerical checks for firmware/grblhal/macros/P100.macro."""

from __future__ import annotations

import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MACRO = ROOT / "firmware" / "grblhal" / "macros" / "P100.macro"


def validate_flow_control(text: str) -> None:
    stack: list[tuple[str, str, int]] = []
    opening = {"if": "endif", "while": "endwhile"}
    closing = {"endif": "if", "endwhile": "while"}

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip().lower()
        match = re.match(r"o(\d+)\s+(if|else|endif|while|endwhile)\b", line)
        if not match:
            continue
        label, command = match.groups()
        if command in opening:
            stack.append((label, command, line_number))
        elif command == "else":
            assert stack and stack[-1][0] == label and stack[-1][1] == "if", (
                f"line {line_number}: unmatched o{label} else"
            )
        else:
            assert stack, f"line {line_number}: unmatched o{label} {command}"
            open_label, open_command, open_line = stack.pop()
            assert open_label == label and closing[command] == open_command, (
                f"line {line_number}: o{label} {command} does not close "
                f"o{open_label} {open_command} from line {open_line}"
            )
    assert not stack, f"unclosed flow-control blocks: {stack}"


def validate_safety_contract(text: str) -> None:
    required = [
        "#<commissioned> = 0",
        "g65 p100 q0",
        "m64 p0",
        "m65 p0",
        "#<_probe_state>",
        "g38.3",
        "g38.5",
        "#5070",
        "#5061",
        "#5064",
        "g10 l20 p1 x0 y0",
        "g10 l20 p1 a0",
        "centroid approach and registration pass",
    ]
    lower = text.lower()
    for token in required:
        assert token in lower, f"required safety/interface token missing: {token}"
    assert "g38.2" not in lower and "g38.4" not in lower, (
        "P100 must use non-alarming probe variants so it can execute cleanup"
    )


def validate_centroid_math() -> None:
    expected_x = 12.5
    expected_y = -7.25
    radius = 8.0
    pitch = 0.25
    rows: list[tuple[float, float, float]] = []
    y = expected_y - radius
    while y <= expected_y + radius + 1e-9:
        half_width = math.sqrt(max(0.0, radius * radius - (y - expected_y) ** 2))
        if half_width > 0:
            entry = expected_x - half_width
            exit_ = expected_x + half_width
            rows.append((y, entry, exit_))
        y += pitch

    sum_width = 0.0
    sum_x_weight = 0.0
    sum_y_weight = 0.0
    for row_y, entry, exit_ in rows:
        width = abs(exit_ - entry)
        midpoint = (entry + exit_) / 2.0
        sum_width += width
        sum_x_weight += midpoint * width
        sum_y_weight += row_y * width

    actual_x = sum_x_weight / sum_width
    actual_y = sum_y_weight / sum_width
    assert abs(actual_x - expected_x) < 1e-9
    assert abs(actual_y - expected_y) <= pitch / 2.0


def validate_a_math() -> None:
    expected_spacing = 4320.0
    entry_1, exit_1 = 127.0, 139.0
    entry_2, exit_2 = entry_1 + expected_spacing, exit_1 + expected_spacing
    center_1 = (entry_1 + exit_1) / 2.0
    center_2 = (entry_2 + exit_2) / 2.0
    index = (center_1 + (center_2 - expected_spacing)) / 2.0
    assert center_2 - center_1 == expected_spacing
    assert index == center_1
    assert index + 2 * expected_spacing > exit_2


def main() -> None:
    text = MACRO.read_text(encoding="utf-8")
    validate_flow_control(text)
    validate_safety_contract(text)
    validate_centroid_math()
    validate_a_math()
    print(f"P100 validation passed: {MACRO.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
