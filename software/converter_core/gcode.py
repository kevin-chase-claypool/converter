import math
import re

from .cancellation import check_cancelled
from .geometry import FillTrail, clip_contours_to_bed, contour_center, distance, format_float, normalized_hatch_pattern, read_svg, retag_contour
from .kinematics import (
    _polar_move_deviation,
    bed_to_machine,
    plan_radius_aware_draw_feed,
    planned_contours,
    plan_contour_thetas,
    plan_travel_move,
    polar_segment_steps,
)
from .settings import pattern_size_override, pattern_size_values, validate_settings

def append_custom_command(lines, command):
    for raw_line in (command or "").replace(";", "\n").splitlines():
        line = raw_line.strip()
        if line and (not lines or lines[-1] != line):
            lines.append(line)


def pen_up_duration_ms(settings):
    return max(float(getattr(settings, "pen_up_ms", 300.0)), 0.0)


def pen_down_duration_ms(settings):
    return max(float(getattr(settings, "pen_down_ms", 600.0)), 0.0)


def pen_down_first_duration_ms(settings):
    # Only the program's first pen-down starts from the GP2 lift switch; see
    # Settings.pen_down_first_ms.
    return max(float(getattr(settings, "pen_down_first_ms", 0.0)), 0.0)


def pen_dwell_duration_ms(settings, direction, is_first_down=False):
    if direction == "down":
        return pen_down_first_duration_ms(settings) if is_first_down else pen_down_duration_ms(settings)
    return pen_up_duration_ms(settings)


def handshake_command(settings, requires_transition, direction, is_first_down=False):
    """Build the P115 call, adding the optional commissioned arguments.

    P115 accepts ``B`` (completion bound), ``A`` (fallback dwell), ``W1``
    (warn-only), and ``W2`` (recover: lift and continue). Older macros ignore
    the extra words, so emitting them stays backward compatible: an un-updated
    controller keeps the 5.00 s bound and its fatal timeout.
    """
    command = "G65 P115 Q1" if requires_transition else "G65 P115 Q0"
    if is_first_down:
        # The program's first M3 travels the whole GP2 retract distance and is
        # measured at about 7 s, longer than P115's default 5.00 s completion
        # bound. Derive the bound from the configured first-down dwell so a
        # healthy slow seek is not reported as a handshake failure.
        bound_s = max(5.0, pen_down_first_duration_ms(settings) / 1000.0 + 2.0)
        command += f" B{format_float(bound_s)}"
    if getattr(settings, "toolhead_handshake_recover", False):
        # On a miss the macro lifts the pen (M5) to the fail-safe state, so the
        # fallback dwell only needs to cover the lift, not the original M3/M5
        # transition. The first-down completion bound above is unchanged.
        lift_s = pen_up_duration_ms(settings) / 1000.0
        if lift_s > 0:
            command += f" A{format_float(lift_s)}"
        command += " W2"
    return command


def append_pen_dwell(lines, settings, direction, requires_transition=True, is_first_down=False):
    # Pause after an M3/M5 pen actuation so the pen reaches the paper (or lifts
    # clear) before motion resumes. grblHAL runs the next line immediately after
    # M3/M5, so without this the pen would drag or start a stroke mid-air. In Z
    # mode the pen move is itself a timed motion, so no dwell is needed.
    if settings.include_z:
        return
    if getattr(settings, "toolhead_status_handshake", False):
        # P115 runs on RP23CNC and polls GP27/PRB with bounded timeouts. Q1
        # requires the output to deassert then reassert, preventing the
        # previous M3/M5 completion from being mistaken for this command's
        # acknowledgment. The program-opening M5 uses Q0 because it may
        # already be proven clear before the program begins.
        lines.append(handshake_command(settings, requires_transition, direction, is_first_down))
        return
    ms = pen_dwell_duration_ms(settings, direction, is_first_down)
    if ms > 0:
        lines.append(f"G4 P{format_float(ms / 1000.0)}")


def format_xy_command(point):
    x, y = point
    return f"X{format_float(x)} Y{format_float(y)}"


def park_home_command(settings):
    # End-of-print park in machine coordinates. G53 bypasses G54 so the pen
    # moves to the fixed homed rest position regardless of the work offset the
    # controller registered at runtime; this is what clears the pen off the
    # rotating bed so the paper can be removed.
    park_x = float(getattr(settings, "park_x_machine", -10.0))
    park_y = float(getattr(settings, "park_y_machine", -436.0))
    return f"G53 G0 X{format_float(park_x)} Y{format_float(park_y)} (park home)"


def append_full_retract(lines, settings):
    # After the final pen-up, request a full retract to the GP2 lift-home
    # switch through the Aux0/GP28 arm line, so the pen is fully clear of the
    # bed for paper removal instead of resting at the ~1 mm clearance gap. The
    # toolhead acknowledges by asserting GP27 clear-ready when GP2 is reached.
    lines.append("M65 P0")  # assert Aux0/GP28 (active-low arm)
    if getattr(settings, "toolhead_status_handshake", False):
        command = "G65 P115 Q0"  # wait for clear-ready at GP2
        if getattr(settings, "toolhead_handshake_recover", False):
            # The full retract is driven by the Aux0/GP28 arm line, not M5, and
            # the pen is already up here, so recover degrades to a warn-only
            # dwell instead of issuing a normal-clear M5 mid-retract.
            command += " A3 W1"
        lines.append(command)
    else:
        lines.append("G4 P3.0")  # fixed dwell covering the full retract
    lines.append("M64 P0")  # release Aux0/GP28


def _is_open_contour(path, tol=0.5):
    # Infill lattice trails are open polylines; stroke outlines (letters, star)
    # are closed loops. Only bridge between two open trails so the pen never
    # drags across a visible shape boundary (e.g. the A -> star gap).
    return len(path) >= 2 and distance(path[0], path[-1]) > tol


def bridge_motion(prev_machine, prev_motor_theta, next_machine, next_motor_theta, center, settings):
    if not bool(getattr(settings, "keep_down_bridges", False)):
        return None
    pattern = normalized_hatch_pattern(getattr(settings, "hatch_pattern", "crosshatch"))
    # Patterns whose consecutive passes `line_region_contours` already emits
    # head-to-tail (it reverses every other row). Keeping the pen down across
    # those passes turns a solid fill into one continuous zigzag instead of one
    # pen cycle per row. The gap guards below are what make this safe: a
    # connector is only drawn when it is short, so sparse parallel hatching
    # still gets separate passes and crosshatch still lifts between its two
    # angle families.
    bridge_patterns = {
        "concentric",
        "triangular",
        "diamonds",
        "hexagonal",
        "linear",
        "crosshatch",
        "diagonal",
        "diagonal_crosshatch",
        "cubic",
    }
    if pattern not in bridge_patterns:
        return None
    xy_len = distance(prev_machine, next_machine)
    spacing = max(float(getattr(settings, "hatch_spacing_mm", 0.0)), 0.0)
    spacing = pattern_size_override(pattern, spacing, pattern_size_values(settings))
    if spacing <= 0.0:
        return None
    pattern_gap = spacing * (1.35 if pattern == "concentric" else 0.85)
    max_gap = max(pattern_gap, float(getattr(settings, "pen_diameter_mm", 0.0)) * 6.0)
    if xy_len <= 1e-9 or xy_len > max_gap:
        return None
    motor_delta = abs(next_motor_theta - prev_motor_theta)
    feed_plan = plan_radius_aware_draw_feed(
        prev_machine,
        next_machine,
        center,
        xy_len,
        motor_delta,
        settings,
    )
    motion_len = feed_plan["motion_length"]
    draw_ms = feed_plan["duration_ms"]
    travel_ms = motion_len / max(float(getattr(settings, "travel_rate", 1.0)), 1e-9) * 60000.0
    lift_lower_ms = pen_up_duration_ms(settings) + pen_down_duration_ms(settings)
    if draw_ms >= travel_ms + lift_lower_ms:
        return None
    return {
        "xy_len": xy_len,
        "motor_delta": motor_delta,
        "motion_len": motion_len,
        "duration_ms": draw_ms,
        "feed_plan": feed_plan,
    }


def _reregister_thetas(thetas, settings):
    """Shift a contour's bed angles by whole revolutions.

    The bed has no absolute multi-turn reference, so subtracting ``k * 360``
    degrees of bed angle leaves every drawn point exactly where it was. What it
    changes is the commanded A: the value ioSender's DRO shows. On a machine
    whose A axis carries a small scale error, the positional error at a feature
    grows with the *commanded* angle, so re-registering each contour keeps the
    worst-case error near half a revolution instead of letting it accumulate
    over the whole program.
    """
    if not getattr(settings, "theta_wrap", True) or not thetas:
        return thetas
    turns = round(thetas[0] / 360.0)
    if not turns:
        return thetas
    shift = -360.0 * turns
    return [theta + shift for theta in thetas]


def plan_program(contours, settings, cancel_check=None):
    """Plan clipped contours in the G54 bed-center work frame.

    SVG coordinates are document-local. The controller's G54 frame is instead
    registered with its origin at the physical bed center, so normalize the
    clipped artwork once here before any theta planning, preview, or G-code
    emission consumes it.
    """
    validate_settings(settings)
    check_cancelled(cancel_check)
    source_center = contour_center(contours)
    bed_radius = max(
        float(getattr(settings, "bed_diameter_mm", 457.2)) / 2.0
        - float(getattr(settings, "bed_margin_mm", 0.0)),
        0.0,
    )
    reach = float(getattr(settings, "machine_reach_radius_mm", 0.0))
    radius = min(bed_radius, reach) if reach > 0.0 else bed_radius
    # The artwork's own center is placed at this offset from the bed center, so
    # the reachable disc - which is fixed on the bed center - corresponds to the
    # artwork point `offset` away from its own center. Clipping is expressed in
    # artwork coordinates, hence the subtraction; the placement is then applied
    # when the contours are moved into the bed frame.
    placement_x = float(getattr(settings, "artwork_offset_x_mm", 0.0))
    placement_y = float(getattr(settings, "artwork_offset_y_mm", 0.0))
    clip_center = (source_center[0] - placement_x, source_center[1] - placement_y)
    clipped_contours = clip_contours_to_bed(
        contours,
        clip_center,
        radius,
        cancel_check,
    )
    center = (0.0, 0.0)
    clipped_contours = [
        retag_contour(
            contour,
            [
                (
                    point[0] - source_center[0] + placement_x,
                    point[1] - source_center[1] + placement_y,
                )
                for point in contour
            ],
        )
        for contour in clipped_contours
    ]
    planned_jobs = []
    previous_theta = None
    previous_machine = None
    for planned in planned_contours(clipped_contours, settings, center, cancel_check):
        check_cancelled(cancel_check)
        points = planned["path"]
        thetas, strategies = plan_contour_thetas(
            points,
            settings,
            previous_theta,
            center,
            previous_machine,
            cancel_check,
        )
        if not thetas:
            continue
        thetas = _reregister_thetas(thetas, settings)
        planned_jobs.append((planned, points, thetas, strategies))
        previous_theta = thetas[-1]
        previous_machine = bed_to_machine(points[-1], thetas[-1], center)
    return {
        "center": center,
        "source_center": source_center,
        "contours": clipped_contours,
        "planned_jobs": planned_jobs,
    }


def contours_to_gcode(contours, settings, program_plan=None, stats=None):
    validate_settings(settings)
    program_plan = program_plan or plan_program(contours, settings)
    axis = re.sub(r"[^A-Za-z]", "", settings.theta_axis.upper())[:1] or "A"
    center = program_plan["center"]
    # Establish the drawing file's own units, distance, feed, plane, and work
    # coordinate modes. ioSender streams these lines; it does not repair modal
    # state inherited from an earlier console command or macro.
    lines = [
        "(Generated by svg_to_gcode.pyw)",
        # Record the numbers that make a plot reproducible. Without this the
        # A values cannot be checked after the fact: a bed-ratio change is
        # invisible in the file, which has cost a diagnosis round already.
        "(theta ratio %.5f motor deg per bed deg, offset %.3f)"
        % (settings.theta_drive_ratio, settings.theta_offset),
        "(feed %.1f mm/min, travel %.1f mm/min, tolerance %.3f mm, pen %.2f mm)"
        % (
            settings.feed_rate,
            settings.travel_rate,
            settings.tolerance,
            settings.pen_diameter_mm,
        ),
        # The A limits the planner assumed, so a file can be compared with the
        # controller's `$$` after the fact: the two drifting apart is invisible
        # otherwise, and it silently makes the emitted feeds unachievable.
        "(A limits assumed %.0f motor deg/min, %.0f motor deg/s^2)"
        % (
            settings.theta_controller_limits.max_rate_deg_min,
            settings.theta_controller_limits.max_acceleration_deg_s2,
        ),
        "G21",
        "G90",
        "G94",
        "G17",
        "G54",
        f"G0 F{format_float(settings.travel_rate)}",
    ]
    if settings.include_z:
        lines.append(f"G0 Z{format_float(settings.safe_z)}")
    else:
        append_custom_command(lines, settings.pen_up_command)
        append_pen_dwell(lines, settings, "up", requires_transition=False)

    previous_machine = None
    previous_motor_theta = 0.0
    pen_is_down = False
    # Only the program's first pen-down starts from GP2 and needs the long
    # cold-seek dwell; every later one starts from the M5 clearance height.
    first_pen_down_pending = True
    previous_pts = None
    for planned, pts, thetas, strategies in program_plan["planned_jobs"]:
        first_theta = thetas[0]

        x0, y0 = bed_to_machine(pts[0], first_theta, center)
        first_motor_theta = first_theta * settings.theta_drive_ratio
        lines.append(f"(contour {planned['index'] + 1}{' reversed' if planned.get('reversed') else ''})")
        bridge = None
        if (
            previous_machine is not None
            and previous_pts is not None
            and isinstance(previous_pts, FillTrail)
            and isinstance(pts, FillTrail)
            and _is_open_contour(previous_pts)
            and _is_open_contour(pts)
        ):
            bridge = bridge_motion(
                previous_machine,
                previous_motor_theta,
                (x0, y0),
                first_motor_theta,
                center,
                settings,
            )
        if bridge and pen_is_down:
            bridge_feed = bridge["feed_plan"]["feed_rate"]
            lines.append(f"G1 {format_xy_command((x0, y0))} {axis}{format_float(first_motor_theta)} F{format_float(bridge_feed)} (keep-down bridge)")
        else:
            if pen_is_down:
                if settings.include_z:
                    lines.append(f"G0 Z{format_float(settings.safe_z)}")
                else:
                    append_custom_command(lines, settings.pen_up_command)
                    append_pen_dwell(lines, settings, "up")
                pen_is_down = False
            if settings.include_z:
                lines.append(f"G0 {format_xy_command((x0, y0))} {axis}{format_float(first_motor_theta)} Z{format_float(settings.safe_z)}")
                lines.append(f"G1 Z{format_float(settings.work_z)} F{format_float(settings.feed_rate)}")
            else:
                # A pen-up move that rotates the bed must not be a bare rapid:
                # a theta re-registration unwinds a whole bed revolution here,
                # and at the controller's configured A rapid rate that stalls the
                # stepper and silently rotates every contour that follows.
                travel_xy = distance(previous_machine, (x0, y0)) if previous_machine is not None else 0.0
                travel_plan = plan_travel_move(
                    settings,
                    travel_xy,
                    abs(first_motor_theta - previous_motor_theta),
                )
                if travel_plan is None:
                    lines.append(f"G0 {format_xy_command((x0, y0))} {axis}{format_float(first_motor_theta)}")
                else:
                    lines.append(
                        f"G1 {format_xy_command((x0, y0))} {axis}{format_float(first_motor_theta)}"
                        f" F{format_float(travel_plan['feed_rate'])} (travel)"
                    )
                append_custom_command(lines, settings.pen_down_command)
                append_pen_dwell(lines, settings, "down", is_first_down=first_pen_down_pending)
                first_pen_down_pending = False
                lines.append(f"G1 F{format_float(settings.feed_rate)}")
            pen_is_down = True

        for k in range(len(pts) - 1):
            a, b = pts[k], pts[k + 1]
            if distance(a, b) <= 1e-9:
                continue
            theta = thetas[k + 1]
            strategy = strategies[k] or "tangent"
            start_theta = thetas[k]
            start_machine = bed_to_machine(a, start_theta, center)
            end_machine = bed_to_machine(b, theta, center)
            motor_theta = theta * settings.theta_drive_ratio
            start_motor_theta = start_theta * settings.theta_drive_ratio
            feed_plan = plan_radius_aware_draw_feed(
                a,
                b,
                center,
                distance(start_machine, end_machine),
                motor_theta - start_motor_theta,
                settings,
            )
            # One coordinated X/Y/A move interpolates linearly, so a single move
            # that spans a bed rotation bows the pen off the straight bed path.
            # Subdivide so the drawn bed path stays within tolerance.
            steps = polar_segment_steps(a, b, center, start_theta, theta, settings.tolerance)
            if stats is not None:
                # Report what the *commanded* path can still deviate from the
                # intended line on the bed: the bow of a whole move divided by
                # its subdivision. This is the number that explains wobble in
                # tight curves near the centre and on long sweeping arcs, and it
                # scales with the Tolerance setting.
                residual = _polar_move_deviation(
                    a, b, center, start_theta, theta
                ) / max(steps, 1)
                if residual > stats.get("worst_bed_deviation_mm", 0.0):
                    stats["worst_bed_deviation_mm"] = residual
                    stats["worst_bed_deviation_radius_mm"] = 0.5 * (
                        math.hypot(*a) + math.hypot(*b)
                    )
                    stats["worst_bed_deviation_strategy"] = strategy
            feed_text = format_float(feed_plan["feed_rate"])
            for step in range(1, steps + 1):
                t = step / steps
                bed_point = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
                sub_theta = start_theta + t * (theta - start_theta)
                sx, sy = bed_to_machine(bed_point, sub_theta, center)
                sub_motor_theta = sub_theta * settings.theta_drive_ratio
                lines.append(
                    f"G1 {format_xy_command((sx, sy))} {axis}{format_float(sub_motor_theta)} F{feed_text} ({strategy})"
                )
        previous_pts = pts
        previous_theta = thetas[-1]
        previous_machine = bed_to_machine(pts[-1], thetas[-1], center)
        previous_motor_theta = previous_theta * settings.theta_drive_ratio

    if pen_is_down:
        if settings.include_z:
            lines.append(f"G0 Z{format_float(settings.safe_z)}")
        else:
            append_custom_command(lines, settings.pen_up_command)
            append_pen_dwell(lines, settings, "up")
            append_full_retract(lines, settings)
    if previous_machine is not None:
        lines.append(park_home_command(settings))
    lines.append("M2")
    return "\n".join(lines) + "\n"

def convert_file(svg_path, gcode_path, settings):
    contours = read_svg(svg_path, settings)
    if not contours:
        raise ValueError("No drawable SVG geometry was found.")
    gcode = contours_to_gcode(contours, settings)
    with open(gcode_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(gcode)
    return len(contours), len(gcode.splitlines())


def build_preview_moves(contours, settings, cancel_check=None, program_plan=None):
    validate_settings(settings)
    check_cancelled(cancel_check)
    moves = []
    program_plan = program_plan or plan_program(contours, settings, cancel_check)
    center = program_plan["center"]
    last_machine_end = None
    previous_theta = None
    previous_motor_theta = 0.0
    axis = re.sub(r"[^A-Za-z]", "", settings.theta_axis.upper())[:1] or "A"
    previous_theta = None
    previous_motor_theta = 0.0
    pen_is_down = False
    first_pen_down_pending = True
    previous_path = None
    for planned, path, thetas, strategies in program_plan["planned_jobs"]:
        check_cancelled(cancel_check)
        contour_index = planned["index"]
        first_theta = thetas[0]

        machine_start = bed_to_machine(path[0], first_theta, center)
        first_motor_theta = first_theta * settings.theta_drive_ratio
        bridge = None
        if (
            last_machine_end is not None
            and previous_path is not None
            and isinstance(previous_path, FillTrail)
            and isinstance(path, FillTrail)
            and _is_open_contour(previous_path)
            and _is_open_contour(path)
        ):
            bridge = bridge_motion(
                last_machine_end,
                previous_motor_theta,
                machine_start,
                first_motor_theta,
                center,
                settings,
            )
        if last_machine_end is None:
            pen_up = f"G0 Z{format_float(settings.safe_z)}" if settings.include_z else (settings.pen_up_command or "(pen up)")
            moves.append({"type": "pen_up", "start": machine_start, "end": machine_start, "bed_start": path[0], "bed_end": path[0], "contour": contour_index, "duration_ms": pen_up_duration_ms(settings), "gcode": pen_up})
            g0 = f"G0 {format_xy_command(machine_start)}"
            g0 += f" {axis}{format_float(first_motor_theta)}"
            initial_motor_delta = abs(first_motor_theta - previous_motor_theta)
            initial_travel = plan_travel_move(settings, 0.0, initial_motor_delta)
            initial_travel_ms = initial_motor_delta / max(settings.travel_rate, 1e-9) * 60000.0
            if initial_travel is not None:
                # A pen-up move that rotates the bed is not a rapid: it gets a
                # feed the A axis can actually hold.
                g0 = (
                    f"G1 {format_xy_command(machine_start)}"
                    f" {axis}{format_float(first_motor_theta)}"
                    f" F{format_float(initial_travel['feed_rate'])} (travel)"
                )
                initial_travel_ms = initial_travel["duration_ms"]
            moves.append({"type": "travel", "start": machine_start, "end": machine_start, "bed_start": path[0], "bed_end": path[0], "bed_theta": first_theta, "motor_theta": first_motor_theta, "contour": contour_index, "duration_ms": initial_travel_ms, "motion_length": initial_motor_delta, "xy_length": 0.0, "gcode": g0})
            previous_motor_theta = first_motor_theta
        elif bridge and pen_is_down:
            bridge_feed = bridge["feed_plan"]["feed_rate"]
            gcode = f"G1 {format_xy_command(machine_start)}"
            gcode += f" {axis}{format_float(first_motor_theta)}"
            gcode += f" F{format_float(bridge_feed)} (keep-down bridge)"
            # The connector is drawn ink, so it needs real bed-frame endpoints or
            # the preview cannot show the passes joined up. The previous path
            # ends where this connector starts; this path starts where it ends.
            moves.append({
                "type": "draw",
                "start": last_machine_end,
                "end": machine_start,
                "bed_start": previous_path[-1],
                "bed_end": path[0],
                "bed_theta": first_theta,
                "motor_theta": first_motor_theta,
                "strategy": "keep_down_bridge",
                "contour": contour_index,
                "duration_ms": bridge["duration_ms"],
                "motion_length": bridge["motion_len"],
                "xy_length": bridge["xy_len"],
                "feed_rate": bridge_feed,
                "radius_mm": bridge["feed_plan"]["radius_mm"],
                "tangential_speed_mm_min": bridge["feed_plan"]["tangential_speed_mm_min"],
                "limited_by": bridge["feed_plan"]["limited_by"],
                "gcode": gcode,
            })
            previous_motor_theta = first_motor_theta
        else:
            if pen_is_down:
                pen_up = f"G0 Z{format_float(settings.safe_z)}" if settings.include_z else (settings.pen_up_command or "(pen up)")
                moves.append({"type": "pen_up", "start": last_machine_end, "end": last_machine_end, "bed_start": path[0], "bed_end": path[0], "contour": contour_index, "duration_ms": pen_up_duration_ms(settings), "gcode": pen_up})
                pen_is_down = False
            if distance(last_machine_end, machine_start) > 1e-9 or abs(first_motor_theta - previous_motor_theta) > 1e-9:
                travel_xy = distance(last_machine_end, machine_start)
                travel_motor = abs(first_motor_theta - previous_motor_theta)
                travel_len = math.hypot(travel_xy, travel_motor)
                travel_plan = plan_travel_move(settings, travel_xy, travel_motor)
                travel_ms = travel_len / max(settings.travel_rate, 1e-9) * 60000.0
                g0 = f"G0 {format_xy_command(machine_start)}"
                g0 += f" {axis}{format_float(first_motor_theta)}"
                if travel_plan is not None:
                    # Same as the opening move: a travel that rotates the bed is
                    # fed, not a rapid, so a re-registration cannot ask the A
                    # axis for a whole revolution at the controller's rapid rate.
                    g0 = (
                        f"G1 {format_xy_command(machine_start)}"
                        f" {axis}{format_float(first_motor_theta)}"
                        f" F{format_float(travel_plan['feed_rate'])} (travel)"
                    )
                    travel_ms = travel_plan["duration_ms"]
                moves.append({"type": "travel", "start": last_machine_end, "end": machine_start, "bed_start": path[0], "bed_end": path[0], "bed_theta": first_theta, "motor_theta": first_motor_theta, "contour": contour_index, "duration_ms": travel_ms, "motion_length": travel_len, "xy_length": travel_xy, "gcode": g0})
                previous_motor_theta = first_motor_theta

        if not pen_is_down:
            pen_down = f"G1 Z{format_float(settings.work_z)} F{format_float(settings.feed_rate)}" if settings.include_z else (settings.pen_down_command or "(pen down)")
            pen_down_ms = pen_down_first_duration_ms(settings) if first_pen_down_pending else pen_down_duration_ms(settings)
            first_pen_down_pending = False
            moves.append({"type": "pen_down", "start": machine_start, "end": machine_start, "bed_start": path[0], "bed_end": path[0], "contour": contour_index, "duration_ms": pen_down_ms, "gcode": pen_down})
            moves.append({"type": "feed", "start": machine_start, "end": machine_start, "bed_start": path[0], "bed_end": path[0], "contour": contour_index, "duration_ms": 0, "gcode": f"G1 F{format_float(settings.feed_rate)}"})
            pen_is_down = True

        last_machine = machine_start
        for k in range(len(path) - 1):
            check_cancelled(cancel_check)
            a, b = path[k], path[k + 1]
            if distance(a, b) <= 1e-9:
                continue
            bed_theta = thetas[k + 1]
            strategy = strategies[k] or "tangent"
            machine_end = bed_to_machine(b, bed_theta, center)
            motor_theta = bed_theta * settings.theta_drive_ratio
            xy_len = distance(last_machine, machine_end)
            motor_delta = motor_theta - previous_motor_theta
            feed_plan = plan_radius_aware_draw_feed(
                a,
                b,
                center,
                xy_len,
                motor_delta,
                settings,
            )
            move_len = feed_plan["motion_length"]
            move_ms = feed_plan["duration_ms"]
            previous_motor_theta = motor_theta
            gcode = f"G1 {format_xy_command(machine_end)} {axis}{format_float(motor_theta)} F{format_float(feed_plan['feed_rate'])} ({strategy})"
            moves.append({
                "type": "draw",
                "start": last_machine,
                "end": machine_end,
                "bed_start": a,
                "bed_end": b,
                "bed_theta": bed_theta,
                "motor_theta": motor_theta,
                "strategy": strategy,
                "contour": contour_index,
                "duration_ms": move_ms,
                "motion_length": move_len,
                "xy_length": xy_len,
                "feed_rate": feed_plan["feed_rate"],
                "radius_mm": feed_plan["radius_mm"],
                "tangential_speed_mm_min": feed_plan["tangential_speed_mm_min"],
                "limited_by": feed_plan["limited_by"],
                "gcode": gcode,
            })
            last_machine = machine_end
        previous_path = path
        previous_theta = thetas[-1]
        last_machine_end = last_machine
    if last_machine_end is not None:
        if pen_is_down:
            pen_up = f"G0 Z{format_float(settings.safe_z)}" if settings.include_z else (settings.pen_up_command or "(pen up)")
            moves.append({"type": "pen_up", "start": last_machine_end, "end": last_machine_end, "bed_start": last_machine_end, "bed_end": last_machine_end, "contour": None, "duration_ms": pen_up_duration_ms(settings), "gcode": pen_up})
        # The real program ends with the full retract to GP2 and a G53
        # machine-coordinate park. The park target has no fixed G54 equivalent
        # (the work offset is registered at run time), so the preview accounts
        # for a nominal off-bed travel plus the full-retract bound instead of
        # drawing an exact G54 destination.
        park_len = max(float(getattr(settings, "bed_diameter_mm", 457.2)) / 2.0, 1.0)
        park_ms = park_len / max(settings.travel_rate, 1e-9) * 60000.0
        park_ms += 3000.0  # nominal full-retract to the GP2 lift-home switch
        gcode = park_home_command(settings)
        moves.append({
            "type": "travel",
            "start": last_machine_end,
            "end": last_machine_end,
            "bed_start": last_machine_end,
            "bed_end": last_machine_end,
            "bed_theta": previous_theta if previous_theta is not None else 0.0,
            "motor_theta": previous_motor_theta,
            "contour": None,
            "duration_ms": park_ms,
            "motion_length": park_len,
            "xy_length": park_len,
            "gcode": gcode,
        })
    return moves
