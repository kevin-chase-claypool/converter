"""Static and numerical checks for firmware/grblhal/macros/P100.macro."""

from __future__ import annotations

import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MACRO = ROOT / "firmware" / "grblhal" / "macros" / "P100.macro"
HOME_MACRO = ROOT / "firmware" / "grblhal" / "macros" / "P111.macro"
INDEX_SURVEY_MACRO = ROOT / "firmware" / "grblhal" / "macros" / "P112.macro"


def assignment(text: str, name: str) -> float:
    match = re.search(
        rf"(?m)^#<{re.escape(name)}>\s*=\s*(-?\d+(?:\.\d+)?)\s*$", text
    )
    assert match, f"P100 missing numeric assignment for {name}"
    return float(match.group(1))


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


def validate_line_comments(text: str) -> None:
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if line.startswith("("):
            assert line.endswith(")"), (
                f"line {line_number}: grblHAL comments must open and close "
                "on the same physical line"
            )


def validate_safety_contract(text: str) -> None:
    required = [
        "#<commissioned> = 0",
        "#<sensor_to_pen_offset_valid> = 0",
        "g65 p100 q0",
        "m64 p0",
        "m65 p0",
        "#<_probe_state>",
        "g38.3",
        "g38.5",
        "#5070",
        "#5061",
        "#<entry> = [#5061 + #5221]",
        "#<exit> = [#5061 + #5221]",
        "#5064",
        "g10 l20 p1 x[#<sensor_to_pen_x>] y[#<sensor_to_pen_y>]",
        "g10 l20 p1 a0",
        "centroid approach and registration pass",
    ]
    lower = text.lower()
    assert "#<mode>" not in lower, (
        "P100 must not use the local named mode alias; it selected Q0 during "
        "the motorless test"
    )
    assert "$h" not in lower, (
        "P100 must not contain $H: grblHAL processes system commands even "
        "when an enclosing O-word branch is false. P111 owns physical homing."
    )
    assert "#31 = #17" in lower, (
        "P100 must preserve the G65 Q argument in #31 before named-variable "
        "initialization"
    )
    assert lower.count("#17") == 4, (
        "P100 may read #17 only for the isolated Q1/Q2 stage gates, the Q5 "
        "allow gate, and the later copy to #31"
    )
    for token in required:
        assert token in lower, f"required safety/interface token missing: {token}"
    assert "g38.2" not in lower and "g38.4" not in lower, (
        "P100 must use non-alarming probe variants so it can execute cleanup"
    )
    assert "(abort," not in lower, (
        "P100 abort comments do not stop grblHAL macro execution; use an "
        "o... error[...] command instead"
    )


def validate_commissioning_locks(text: str) -> None:
    lower = text.lower()
    required = [
        "o001 if [#17 eq 1]",
        "m64 p0\n  g4 p2.0\n  (installed u2/gp28 path is active-low: m65 asserts arm; m64 releases it.)\n  m65 p0",
        "o001 return [1]",
        "o004 if [#17 eq 2]",
        "p100 q2 retired: run g65 p111 for physical x/y home",
        "o102 if [#31 gt 5]",
        "o113 if [[#31 eq 3] or [#31 eq 5]]",
        "o200 if [[[#31 eq 0] or [#31 eq 3]] or [#31 eq 5]]",
        "o234 if [#31 eq 5]",
        "p100 q5 survey complete: tmag is at calculated centroid; inspect mpos",
        "o100 return [1]",
        "o999 error[39]",
        "o005 if [#17 ne 5]",
        "p100 mode locked: q1 readiness and q5 survey only are enabled",
        "o103 if [#31 eq 0]",
        "o105 if [#31 eq 3]",
        "o107 if [#31 eq 4]",
        "o901 error[39]",
        "o902 error[39]",
        "o903 error[39]",
        "o904 error[39]",
        "o905 error[39]",
        "o906 error[39]",
    ]
    for token in required:
        assert token in lower, f"required executable commissioning lock missing: {token}"
    assert lower.index("o001 if [#17 eq 1]") < lower.index("#31 = #17"), (
        "Q1 must dispatch before named-variable initialization and all homing paths"
    )
    assert lower.index("o004 if [#17 eq 2]") < lower.index("#31 = #17"), (
        "Q2 must dispatch before named-variable initialization and magnetic paths"
    )
    assert lower.index("o005 if [#17 ne 5]") < lower.index("#31 = #17"), (
        "only Q5 may continue past the early Q1/Q2 stage gates"
    )
    q5_return = lower.index(
        "p100 q5 survey complete: tmag is at calculated centroid; inspect mpos"
    )
    first_g54_registration = lower.index("g10 l20 p1 x[#<sensor_to_pen_x>]")
    assert q5_return < first_g54_registration, (
        "Q5 must return before any G54 XY registration"
    )
    assert "o116 if [#31 eq 5]" in lower, (
        "Q5 must establish a released baseline before prepositioning"
    )


def validate_installed_aux_polarity(text: str) -> None:
    aux_commands = [
        line.strip().lower()
        for line in text.splitlines()
        if line.strip().lower() in {"m64 p0", "m65 p0"}
    ]
    normal_handshake = re.compile(
        r"\(two-phase readiness handshake.*?\)\s*"
        r"\(installed u2/gp28 path.*?\)\s*"
        r"m65 p0\s+g4 p\[#<ready_wait_s>\].*?"
        r"o120 endif\s+m64 p0\s+g4 p\[#<edge_settle_s>\].*?"
        r"o122 endif\s+m65 p0\s+g4 p\[#<edge_settle_s>\]",
        re.DOTALL,
    )
    assert normal_handshake.search(text.lower()), (
        "installed active-low U2/GP28 normal path must arm, release, then "
        "re-arm with M65, M64, M65"
    )
    assert aux_commands.count("m65 p0") == 3, (
        "P100 must contain one Q1 stage-gate assertion plus the legacy "
        "readiness/scan assertions; cleanup must release Aux0"
    )
    assert aux_commands[-1] == "m64 p0", "P100 must release Aux0 on exit"


def validate_isolated_home_macro() -> None:
    text = HOME_MACRO.read_text(encoding="utf-8")
    lower = text.lower()
    commands = [
        line.strip().lower()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("(")
    ]
    assert commands == ["m5", "g4 p3.0", "$h", "o111 return [1]"], (
        "P111 must contain only lift, settle, one unconditional $H, and return"
    )
    assert commands.count("$h") == 1, "P111 must contain exactly one executable $H"


def validate_outer_index_survey_macro() -> None:
    text = INDEX_SURVEY_MACRO.read_text(encoding="utf-8")
    lower = text.lower()
    validate_flow_control(text)
    validate_line_comments(text)
    required = [
        "#<outer_radius> = 223.675804",
        "g91 g1 x[#<outer_radius>] f[#<xy_travel_feed>]",
        "m65 p0\ng4 p2.0",
        "g91 g38.3 a[#<a_search_degrees>] f[#<a_scan_feed>]",
        "g91 g38.5 a[#<a_maximum_width>] f[#<a_scan_feed>]",
        "#<a_entry_1> = [#5064 + #5224]",
        "#<a_exit_1> = [#5064 + #5224]",
        "#<a_entry_2> = [#5064 + #5224]",
        "#<a_exit_2> = [#5064 + #5224]",
        "#<a_expected_spacing> = 4320.0",
        "#<a_pass_two_center>",
        "g53 g1 a[#<a_pass_two_center>] f[#<a_registration_feed>]",
        "p112 survey complete: tmag is at pass-two outer-index center",
        "m64 p0\n(print,p112 survey complete",
    ]
    for token in required:
        assert token in lower, f"P112 missing required survey token: {token}"
    assert "$h" not in lower, "P112 must not contain physical homing"
    assert "g10" not in lower, "P112 must not write a work offset"
    assert lower.count("g38.3 a[#<a_search_degrees>]") == 2, (
        "P112 must make exactly two bounded A entry searches"
    )


def validate_candidate_scan_rectangle(text: str) -> None:
    min_x = assignment(text, "scan_min_x")
    max_x = assignment(text, "scan_max_x")
    min_y = assignment(text, "scan_min_y")
    max_y = assignment(text, "scan_max_y")

    # MPos envelope after the proven X/Y home configuration. The candidate
    # rectangle must retain a 20 mm clearance at every endpoint.
    assert -435.0 <= min_x < max_x <= -20.0, "unsafe candidate X scan bounds"
    assert -426.0 <= min_y < max_y <= -20.0, "unsafe candidate Y scan bounds"
    assert max_x - min_x == 100.0, "candidate X scan width must be 100 mm"
    assert max_y - min_y == 100.0, "candidate Y scan height must be 100 mm"


def validate_candidate_scan_parameters(text: str) -> None:
    assert assignment(text, "sensor_to_pen_x") == 0.0
    assert assignment(text, "sensor_to_pen_y") == -29.4892
    assert assignment(text, "row_pitch") == 10.0
    assert assignment(text, "scan_feed") == 1000.0
    assert assignment(text, "ready_wait_s") == 2.0
    assert assignment(text, "maximum_chord_width") == 50.0
    assert "#<sensor_to_pen_offset_valid> = 0" in text.lower(), (
        "candidate offset must not unlock Q3 before a supervised scan"
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


def validate_sensor_to_pen_registration() -> None:
    # At the axis coordinate where the TMAG is over center, G54 must report the
    # pen-minus-TMAG offset. A subsequent G54 X0 Y0 move then puts the pen at
    # center, not the TMAG.
    tmag_centroid_x, tmag_centroid_y = 100.0, -40.0
    sensor_to_pen_x, sensor_to_pen_y = 12.0, -8.0
    work_origin_x = tmag_centroid_x - sensor_to_pen_x
    work_origin_y = tmag_centroid_y - sensor_to_pen_y
    assert tmag_centroid_x - work_origin_x == sensor_to_pen_x
    assert tmag_centroid_y - work_origin_y == sensor_to_pen_y
    assert work_origin_x + sensor_to_pen_x == tmag_centroid_x
    assert work_origin_y + sensor_to_pen_y == tmag_centroid_y


def main() -> None:
    text = MACRO.read_text(encoding="utf-8")
    validate_flow_control(text)
    validate_line_comments(text)
    validate_safety_contract(text)
    validate_commissioning_locks(text)
    validate_installed_aux_polarity(text)
    validate_isolated_home_macro()
    validate_outer_index_survey_macro()
    validate_candidate_scan_rectangle(text)
    validate_candidate_scan_parameters(text)
    validate_centroid_math()
    validate_a_math()
    validate_sensor_to_pen_registration()
    print(f"P100 validation passed: {MACRO.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
