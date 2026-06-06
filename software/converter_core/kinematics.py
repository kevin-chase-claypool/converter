import math

from .geometry import distance, filtered_contour, normalized_hatch_pattern, unwrap_angle
from .settings import pattern_size_override, pattern_size_values

def bed_to_machine(point, bed_theta, center):
    angle = math.radians(bed_theta)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    dx = point[0] - center[0]
    dy = point[1] - center[1]
    return (
        center[0] + dx * cos_a - dy * sin_a,
        center[1] + dx * sin_a + dy * cos_a,
    )


def tool_offset(settings):
    return (
        float(getattr(settings, "tool_offset_x_mm", 0.0)),
        float(getattr(settings, "tool_offset_y_mm", 0.0)),
    )


def tool_to_command(point, settings):
    ox, oy = tool_offset(settings)
    return (point[0] - ox, point[1] - oy)


def command_to_tool(point, settings):
    ox, oy = tool_offset(settings)
    return (point[0] + ox, point[1] + oy)


def _axis_locked_roots(point, center, axis, target):
    # Principal bed orientations (degrees) that put point's *machine* coordinate
    # on `axis` exactly at `target` (i.e. a pure-X or pure-Y machine move from a
    # point already at `target`). Two roots, no winding applied — callers add the
    # k*360 family themselves with whatever reference/spread they need.
    dx = point[0] - center[0]
    dy = point[1] - center[1]
    radius = math.hypot(dx, dy)
    if radius <= 1e-9:
        return []
    beta = math.atan2(dy, dx)
    value = (target - center[0 if axis == "x" else 1]) / radius
    if value < -1.0 - 1e-9 or value > 1.0 + 1e-9:
        return []
    value = max(-1.0, min(1.0, value))
    if axis == "x":
        roots = [math.acos(value) - beta, -math.acos(value) - beta]
    else:
        asin_value = math.asin(value)
        roots = [asin_value - beta, math.pi - asin_value - beta]
    return [math.degrees(r) for r in roots]


def axis_locked_theta_candidates(point, center, axis, target, reference):
    out = []
    for base in _axis_locked_roots(point, center, axis, target):
        for k in range(-8, 9):
            out.append(unwrap_angle(base + k * 360.0, reference))
    return out


def candidate_cost(previous_machine, machine, previous_theta, theta, settings, tangent=None):
    # Physical move cost: the GRBL vector length of the coordinated X/Y/A move,
    # with the bed rotation priced in *motor* degrees (bed degrees * drive ratio)
    # so the slow 12:1 bed is charged honestly — not at the old 1 deg == 1 mm.
    # This is the same currency build_preview_moves uses for duration, so the
    # planner optimizes what actually determines runtime, and it scores every
    # candidate identically (no per-strategy dx/dy/hypot split).
    ratio = max(float(getattr(settings, "theta_drive_ratio", 1.0)), 1e-9)
    theta_weight = max(float(getattr(settings, "theta_weight", 1.0)), 0.0)
    smoothness_factor = _smoothness_factor(settings)
    round_bias = max(float(getattr(settings, "round_bias", 1.0)), 0.0) * smoothness_factor
    xy_dist = math.hypot(machine[0] - previous_machine[0], machine[1] - previous_machine[1])
    motor_move = abs(theta - previous_theta) * ratio
    cost = math.hypot(xy_dist, theta_weight * motor_move)
    # Rounding bias: reward orientations close to the path tangent *line* (mod
    # 180, so a 180 flip counts as aligned). Tangent-tracking is what bends the
    # per-segment interpolation into an arc, so this is what rounds curves; on
    # straight runs the tangent is constant so it costs nothing.
    if tangent is not None and round_bias > 0.0:
        dev = (theta - tangent) % 180.0
        if dev > 90.0:
            dev -= 180.0
        cost += round_bias * abs(dev) * ratio
    return cost


def _rtheta_start_theta(settings, previous_theta):
    if previous_theta is not None:
        return previous_theta
    return float(getattr(settings, "theta_offset", 0.0))


def _rtheta_axis_plan(point, settings, previous_theta, previous_machine, center, strategy):
    # r-theta style axis solve:
    # - x_theta: keep machine Y fixed, move X + theta
    # - y_theta: keep machine X fixed, move Y + theta
    # Then score the realized coordinated move in the same physical currency
    # used by preview timing.
    if previous_machine is None:
        return None
    reference = previous_theta if previous_theta is not None else float(getattr(settings, "theta_offset", 0.0))
    if strategy == "x_theta":
        roots = axis_locked_theta_candidates(point, center, "y", previous_machine[1], reference)
    else:
        roots = axis_locked_theta_candidates(point, center, "x", previous_machine[0], reference)
    if not roots:
        return None

    best = None
    best_cost = None
    for theta in roots:
        machine = bed_to_machine(point, theta, center)
        cost = candidate_cost(previous_machine, machine, reference, theta, settings)
        if best_cost is None or cost < best_cost:
            best_cost = cost
            best = {
                "theta": theta,
                "machine": machine,
                "strategy": strategy,
                "cost": cost,
            }
    return best


def _rtheta_segment_plan(a, b, settings, previous_theta, previous_machine, center):
    x_plan = _rtheta_axis_plan(b, settings, previous_theta, previous_machine, center, "x_theta")
    y_plan = _rtheta_axis_plan(b, settings, previous_theta, previous_machine, center, "y_theta")
    plans = [plan for plan in (x_plan, y_plan) if plan is not None]
    if plans:
        return min(plans, key=lambda plan: plan["cost"])

    # Near the bed center, or if the pure-axis root is unreachable, fall back to
    # the nearest no-frills theta. This is a geometric singularity escape, not a
    # smoothing candidate.
    base = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) + settings.theta_offset
    reference = previous_theta if previous_theta is not None else base
    theta = unwrap_angle(base, reference)
    machine = bed_to_machine(b, theta, center) if center is not None else b
    return {
        "theta": theta,
        "machine": machine,
        "strategy": "fallback",
        "cost": candidate_cost(previous_machine, machine, reference, theta, settings) if previous_machine is not None else 0.0,
    }


def _plan_contour_thetas_rtheta(path, settings, previous_theta, center, previous_machine):
    n = len(path)
    if n < 2:
        return [], []
    theta0 = _rtheta_start_theta(settings, previous_theta)
    thetas = [theta0] + [0.0] * (n - 1)
    strategies = [None] * (n - 1)
    prev_theta = theta0
    prev_machine = bed_to_machine(path[0], theta0, center)
    for k in range(n - 1):
        a, b = path[k], path[k + 1]
        if distance(a, b) <= 1e-9:
            thetas[k + 1] = prev_theta
            strategies[k] = "fallback"
            continue
        plan = _rtheta_segment_plan(a, b, settings, prev_theta, prev_machine, center)
        thetas[k + 1] = plan["theta"]
        strategies[k] = plan["strategy"]
        prev_theta = plan["theta"]
        prev_machine = plan["machine"]
    return thetas, strategies


def plan_segment_kinematics(a, b, settings, previous_theta, center=None, previous_machine=None):
    base = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) + settings.theta_offset
    mode = getattr(settings, "theta_mode", "optimized").strip().lower()
    if mode == "fixed":
        theta = unwrap_angle(settings.theta_offset, previous_theta)
        return {"theta": theta, "strategy": "fixed"}
    if mode in ("tangent", "raw"):
        theta = unwrap_angle(base, previous_theta)
        return {"theta": theta, "strategy": "tangent"}

    tangent_candidates = []
    step = 180.0 if mode in ("optimized", "min_rotation", "min-rotation") else 360.0
    reference = previous_theta if previous_theta is not None else base
    for k in range(-8, 9):
        candidate = base + k * step
        candidate = unwrap_angle(candidate, reference)
        tangent_candidates.append(candidate)

    if mode in ("min_rotation", "min-rotation") or center is None or previous_machine is None:
        theta = min(tangent_candidates, key=lambda candidate: abs(candidate - reference))
        return {"theta": theta, "strategy": "min_rotation"}

    # Pool axis-lock candidates (x_theta locks Y, y_theta locks X) plus the
    # segment-tangent candidates so the bed actively rotates with the curve.
    # No hold-steady candidate: by design every draw segment uses the theta
    # axis (bed never parks across consecutive segments).
    if mode in ("x_theta", "x-theta", "x"):
        candidate_sets = [("x_theta", axis_locked_theta_candidates(b, center, "y", previous_machine[1], reference))]
    elif mode in ("y_theta", "y-theta", "y"):
        candidate_sets = [("y_theta", axis_locked_theta_candidates(b, center, "x", previous_machine[0], reference))]
    else:
        candidate_sets = [
            ("x_theta", axis_locked_theta_candidates(b, center, "y", previous_machine[1], reference)),
            ("y_theta", axis_locked_theta_candidates(b, center, "x", previous_machine[0], reference)),
            ("tangent", tangent_candidates),
        ]

    best = None
    best_cost = None
    for label, candidates in candidate_sets:
        for candidate in candidates:
            machine = bed_to_machine(b, candidate, center)
            cost = candidate_cost(previous_machine, machine, reference, candidate, settings, base)
            if best_cost is None or cost < best_cost:
                best = {"theta": candidate, "strategy": label, "cost": cost}
                best_cost = cost

    if best is not None:
        # Relabel the winning candidate by which gantry axis did more work in
        # the realized move, so G-code labels stay accurate to motion even
        # when hold-steady wins.
        machine = bed_to_machine(b, best["theta"], center)
        dx = abs(machine[0] - previous_machine[0])
        dy = abs(machine[1] - previous_machine[1])
        best["strategy"] = "x_theta" if dx >= dy else "y_theta"
        return best

    # No axis-lock root exists for this point (e.g. the bed-center singularity
    # or a target outside the reachable disc). Fall back to tracking the
    # segment tangent so the bed still has a defined orientation.
    theta = min(tangent_candidates, key=lambda candidate: abs(candidate - reference))
    return {"theta": theta, "strategy": "tangent"}


def segment_bed_theta(a, b, settings, previous_theta, center=None, previous_machine=None):
    return plan_segment_kinematics(a, b, settings, previous_theta, center, previous_machine)["theta"]


def smooth_sequence(values, window):
    n = len(values)
    if window <= 0 or n <= 2:
        return list(values)
    out = []
    for i in range(n):
        lo = max(0, i - window)
        hi = min(n, i + window + 1)
        seg = values[lo:hi]
        out.append(sum(seg) / len(seg))
    return out


def _plan_contour_thetas_greedy(path, settings, previous_theta, center, previous_machine):
    # Greedy per-point bed orientation along the contour, then a moving-average
    # smoothing pass to remove segment-to-segment jitter (e.g. erratic
    # axis-locking) and ease the bed through sharp tangent flips. Cheap, but it
    # can't see ahead, so it accumulates wasteful back-and-forth winding; the DP
    # resolver below addresses that. Kept as a fallback (theta_resolver="greedy").
    n = len(path)
    if n < 2:
        return [], []
    thetas = [0.0] * n
    strategies = [None] * (n - 1)
    first = plan_segment_kinematics(path[0], path[1], settings, previous_theta, center, previous_machine)
    thetas[0] = first["theta"]
    prev_theta = thetas[0]
    prev_machine = bed_to_machine(path[0], thetas[0], center)
    for k in range(n - 1):
        a, b = path[k], path[k + 1]
        if distance(a, b) <= 1e-9:
            thetas[k + 1] = prev_theta
            strategies[k] = "tangent"
            continue
        plan = plan_segment_kinematics(a, b, settings, prev_theta, center, prev_machine)
        thetas[k + 1] = plan["theta"]
        strategies[k] = plan.get("strategy", "tangent")
        prev_theta = thetas[k + 1]
        prev_machine = bed_to_machine(b, thetas[k + 1], center)
    window = int(getattr(settings, "theta_smooth_window", 0) or 0)
    if window > 0:
        thetas = smooth_sequence(thetas, window)
    return thetas, strategies


# DP/Viterbi theta resolver tuning. Candidates per point are *principal*
# orientations (mod 360); the lattice is O(points * K^2). Two candidates within
# DEDUPE_DEG are merged. The pool is built so every draw segment is either an
# X+theta or a Y+theta coordinated move — the bed always uses the theta axis,
# never parks at a fixed angle:
#   - **tangent flips** (the segment's tangent line in both orientations) put
#     the bed onto an angle that varies smoothly with the curve direction, so
#     the bed actively rotates through curves (continuous theta motion → the
#     bed-frame trace within each segment matches the curve shape, not a
#     polyline approximation).
#   - **axis-lock roots** put one machine-axis delta to zero relative to the
#     previous nominal point, turning that segment into a pure-X (y_theta) or
#     pure-Y (x_theta) gantry move with theta sweeping alongside. These let
#     the DP pick whichever pure-axis machine move is cheaper than tracking.
# A uniform "park here" grid was tried (`_THETA_DP_GRID_DEG`) and disabled —
# it gave the DP a way to keep the bed *stationary* across many segments,
# which contradicts the design intent that theta moves on every draw move.
# Segment labels are not taken from the candidate that won — after the DP
# backtracks, each segment is relabeled `x_theta`/`y_theta` by whichever
# gantry axis (|dx| vs |dy|) carried the larger share of the realized move.
_THETA_DP_DEDUPE_DEG = 0.5
_THETA_DP_GRID_DEG = 0.0


def _smoothness_factor(settings):
    return max(float(getattr(settings, "smoothness_factor", 1.0)), 0.0)


def _effective_theta_smooth_window(settings):
    window = int(getattr(settings, "theta_smooth_window", 0) or 0)
    if window <= 0:
        return 0
    return int(round(window * _smoothness_factor(settings)))


def _theta_hold_grid_deg(settings):
    if _THETA_DP_GRID_DEG > 0:
        return _THETA_DP_GRID_DEG
    return 45.0


def _theta_hold_penalty(settings, ratio):
    # Hold-steady grid candidates are always available to avoid a candidate-pool
    # cliff near 1.0. This penalty makes them progressively cheaper as the user
    # lowers Smoothness factor.
    smooth = min(_smoothness_factor(settings), 1.0)
    if smooth >= 1.0:
        return float("inf")
    if smooth <= 0.0:
        return 0.0
    return 5.0 * smooth / max(1.0 - smooth, 1e-9)


def _wrap180(delta):
    # Signed nearest angular difference in (-180, 180].
    d = (delta + 180.0) % 360.0 - 180.0
    return d + 360.0 if d <= -180.0 else d


def _dp_point_candidates(point, center, tlines, prev_nom_machine, hold_grid_deg=0.0):
    # Candidate *principal* orientations (deg, in [0,360)) for one contour point:
    #   - tangent flips: each adjacent segment's tangent line in both directions.
    #     Bed angle tracks the curve, so theta sweeps smoothly along each draw
    #     segment instead of parking. This is what makes curves render as actual
    #     curves on the bed at coarse tolerances rather than as polylines.
    #   - axis-lock roots: orientations that null one machine-axis delta to the
    #     previous nominal point, so the segment becomes pure-X (y_theta locks
    #     X) or pure-Y (x_theta locks Y) gantry motion with theta sweeping.
    # No grid / hold-steady candidates: by design, every segment must use the
    # theta axis (the bed never parks at a fixed angle across many segments).
    # Labels here are provisional; the resolver assigns the final per-segment
    # label (x_theta / y_theta) by dominant gantry axis after backtracking.
    raw = []  # (principal_angle_deg, label)
    for tline in tlines:
        raw.append((tline % 360.0, "tangent"))
        raw.append(((tline + 180.0) % 360.0, "tangent"))
    if prev_nom_machine is not None:
        for axis, target, label in (
            ("y", prev_nom_machine[1], "x_theta"),
            ("x", prev_nom_machine[0], "y_theta"),
        ):
            for root in _axis_locked_roots(point, center, axis, target):
                raw.append((root % 360.0, label))
    if hold_grid_deg > 0:
        g = hold_grid_deg
        steps = int(round(360.0 / g))
        for i in range(steps):
            raw.append((i * g, "hold"))
    raw.sort(key=lambda it: it[0])
    deduped = []
    for ang, label in raw:
        if deduped and abs(ang - deduped[-1][0]) < _THETA_DP_DEDUPE_DEG:
            continue
        deduped.append((ang, label))
    if len(deduped) > 1 and (deduped[0][0] + 360.0 - deduped[-1][0]) < _THETA_DP_DEDUPE_DEG:
        deduped.pop()
    return deduped


def _dp_edge_cost(ma_i, mb_j, ang_i, ang_j, label_j, tan, ratio, theta_weight, round_bias, hold_penalty):
    # Same physical+rounding currency as candidate_cost, but the motor term uses
    # the *nearest-wrap* delta between principal angles so a 350->10 step is priced
    # as 20deg, not 340. Because that nearest-wrap delta accumulates along the path
    # (reconstructed continuously after backtracking), the global shortest path
    # minimizes total winding while still able to track a curve through full turns.
    xy = math.hypot(mb_j[0] - ma_i[0], mb_j[1] - ma_i[1])
    motor = abs(_wrap180(ang_j - ang_i)) * ratio
    cost = math.hypot(xy, theta_weight * motor)
    if round_bias > 0.0:
        dev = (ang_j - tan) % 180.0
        if dev > 90.0:
            dev -= 180.0
        cost += round_bias * abs(dev) * ratio
    if label_j == "hold":
        cost += hold_penalty
    return cost


def _plan_contour_thetas_dp(path, settings, previous_theta, center, previous_machine):
    # Viterbi shortest-path over a per-point lattice of principal bed orientations.
    # The motor term |dtheta|*ratio accumulates along the whole contour, so the
    # global optimum avoids the wasteful back-and-forth winding the greedy (which
    # can't see ahead) accumulates. Returns absolute (unwound) thetas.
    n = len(path)
    if n < 2:
        return [], []
    ratio = max(float(getattr(settings, "theta_drive_ratio", 1.0)), 1e-9)
    theta_weight = max(float(getattr(settings, "theta_weight", 1.0)), 0.0)
    smoothness_factor = _smoothness_factor(settings)
    round_bias = max(float(getattr(settings, "round_bias", 1.0)), 0.0) * smoothness_factor
    hold_grid_deg = _theta_hold_grid_deg(settings)
    hold_penalty = _theta_hold_penalty(settings, ratio)

    base = [
        math.degrees(math.atan2(path[k + 1][1] - path[k][1], path[k + 1][0] - path[k][0]))
        + settings.theta_offset
        for k in range(n - 1)
    ]

    # Nominal per-point machine positions (at the incoming tangent) feed the
    # axis-lock candidate targets — they're the "previous machine point" each
    # candidate's pure-X/pure-Y move is measured against.
    nom = [base[0]] + [base[k] for k in range(n - 1)]
    nom_machine = [bed_to_machine(path[j], nom[j], center) for j in range(n)]

    cand = []
    for j in range(n):
        tlines = []
        if j - 1 >= 0:
            tlines.append(base[j - 1])
        if j <= n - 2:
            tlines.append(base[j])
        prev_nm = nom_machine[j - 1] if j >= 1 else None
        cand.append(_dp_point_candidates(path[j], center, tlines, prev_nm, hold_grid_deg))

    mach = [[bed_to_machine(path[j], ang, center) for ang, _ in cand[j]] for j in range(n)]

    INF = float("inf")
    # Seed the first column from inter-contour continuity: rotating from the prior
    # contour's exit orientation costs motor degrees (nearest wrap), so the DP
    # won't gratuitously re-wind at each contour start.
    if previous_theta is not None:
        cost = [
            theta_weight * abs(_wrap180(ang - previous_theta)) * ratio
            + (hold_penalty if label == "hold" else 0.0)
            for ang, label in cand[0]
        ]
    else:
        cost = [0.0] * len(cand[0])
    back = [[-1] * len(cand[0])]

    for k in range(n - 1):
        ca, ma = cand[k], mach[k]
        cb, mb = cand[k + 1], mach[k + 1]
        tan = base[k]
        next_cost = [INF] * len(cb)
        next_back = [-1] * len(cb)
        for j in range(len(cb)):
            ang_j = cb[j][0]
            m_j = mb[j]
            best = INF
            best_i = -1
            for i in range(len(ca)):
                e = _dp_edge_cost(ma[i], m_j, ca[i][0], ang_j, cb[j][1], tan, ratio, theta_weight, round_bias, hold_penalty)
                tot = cost[i] + e
                if tot < best:
                    best = tot
                    best_i = i
            next_cost[j] = best
            next_back[j] = best_i
        cost = next_cost
        back.append(next_back)

    last = min(range(len(cand[n - 1])), key=lambda i: cost[i])
    idx = [0] * n
    idx[n - 1] = last
    for k in range(n - 1, 0, -1):
        idx[k - 1] = back[k][idx[k]]

    # Reconstruct absolute (continuous) thetas: take the nearest wrap on each step,
    # matching the edge cost, so accumulated winding is exactly what the DP priced.
    principals = [cand[j][idx[j]][0] for j in range(n)]
    thetas = [0.0] * n
    thetas[0] = unwrap_angle(principals[0], previous_theta) if previous_theta is not None else principals[0]
    for j in range(1, n):
        thetas[j] = unwrap_angle(principals[j], thetas[j - 1])

    window = _effective_theta_smooth_window(settings)
    if window > 0:
        thetas = smooth_sequence(thetas, window)

    # Label each segment by whichever gantry axis carried the larger share of
    # the move. This is the post-hoc truth — independent of which DP candidate
    # the angle came from — so hold-steady, axis-lock, and partial-axis
    # segments are all named after the axis that actually did the work.
    strategies = []
    for k in range(n - 1):
        ma = bed_to_machine(path[k], thetas[k], center)
        mb = bed_to_machine(path[k + 1], thetas[k + 1], center)
        dx = abs(mb[0] - ma[0])
        dy = abs(mb[1] - ma[1])
        strategies.append("x_theta" if dx >= dy else "y_theta")
    return thetas, strategies


def plan_contour_thetas(path, settings, previous_theta, center, previous_machine):
    # Centralized per-contour theta selection. Returns (thetas, strategies):
    # thetas[k] is the bed orientation at path[k]; strategies[k] labels segment
    # path[k]->path[k+1]. Smoothing/DP only change *how the bed is oriented while
    # drawing* — the drawn bed points are exact for any theta, so artwork is
    # unchanged. The DP resolver runs for the auto theta_mode ("optimized") where
    # candidate pooling applies; explicit single-strategy modes keep the greedy
    # per-segment path.
    resolver = str(getattr(settings, "theta_resolver", "rtheta")).strip().lower()
    mode = str(getattr(settings, "theta_mode", "optimized")).strip().lower()
    if resolver in ("rtheta", "r-theta", "axis_cost", "axis-cost") and mode in ("optimized", "auto", "select"):
        return _plan_contour_thetas_rtheta(path, settings, previous_theta, center, previous_machine)
    if resolver == "dp" and mode in ("optimized", "auto", "select"):
        return _plan_contour_thetas_dp(path, settings, previous_theta, center, previous_machine)
    return _plan_contour_thetas_greedy(path, settings, previous_theta, center, previous_machine)


def ne_park_position(center, settings):
    radius = max(float(getattr(settings, "bed_diameter_mm", 457.2)), 1.0) / 2.0
    return (center[0] + radius, center[1] + radius)


def first_segment_theta(path, settings, previous_theta, center, previous_machine):
    resolver = str(getattr(settings, "theta_resolver", "rtheta")).strip().lower()
    mode = str(getattr(settings, "theta_mode", "optimized")).strip().lower()
    if resolver in ("rtheta", "r-theta", "axis_cost", "axis-cost") and mode in ("optimized", "auto", "select"):
        return _rtheta_start_theta(settings, previous_theta)
    for a, b in zip(path, path[1:]):
        if distance(a, b) > 1e-9:
            return segment_bed_theta(a, b, settings, previous_theta, center, previous_machine)
    return None


def simulate_contour_exit(path, settings, center, previous_theta, previous_machine):
    thetas, _ = plan_contour_thetas(path, settings, previous_theta, center, previous_machine)
    if not thetas:
        return None
    return {
        "first_theta": thetas[0],
        "start_machine": bed_to_machine(path[0], thetas[0], center),
        "end_theta": thetas[-1],
        "end_machine": bed_to_machine(path[-1], thetas[-1], center),
    }


def contour_entry_cost(start_machine, first_theta, previous_machine, previous_theta, settings, running_direction=0):
    # Penalty for travel + bed rotation + the pen up/down dwell that fences the
    # transition. The theta penalty has two modes:
    #   - free (running_direction == 0 or monotonic_theta off): symmetric
    #     |Δθ|. Whichever direction has less rotation wins.
    #   - directional (running_direction = ±1, monotonic_theta on): rotation
    #     in the running direction is charged at |Δθ_signed|; rotation that
    #     reverses direction is penalised by an extra (360 - |Δθ|) term, the
    #     cost of going "the long way around" to keep spinning the same way.
    # The r-theta sand-table lesson: pick contours so the bed never reverses;
    # the motor stays accelerated, backlash is constant-sign, and the visual
    # reads as a continuous sweep instead of jerking back and forth.
    pen_cycle_ms = max(float(getattr(settings, "pen_up_ms", 300.0)), 0.0) + max(float(getattr(settings, "pen_down_ms", 600.0)), 0.0)
    if previous_machine is None:
        return pen_cycle_ms
    travel_cost = distance(previous_machine, start_machine)
    theta_weight = max(float(getattr(settings, "theta_weight", 1.0)), 0.0)
    theta_reference = previous_theta if previous_theta is not None else first_theta
    delta = first_theta - theta_reference
    monotonic = bool(getattr(settings, "monotonic_theta", True))
    if monotonic and running_direction != 0:
        if (delta >= 0) == (running_direction > 0):
            # same direction — charge the actual rotation
            theta_cost = abs(delta) * theta_weight
        else:
            # would reverse — penalise by the long-way-around residual
            theta_cost = (360.0 - abs(delta)) * theta_weight
    else:
        theta_cost = abs(delta) * theta_weight
    pattern = normalized_hatch_pattern(getattr(settings, "hatch_pattern", "crosshatch"))
    spacing = max(float(getattr(settings, "hatch_spacing_mm", 0.0)), 0.0)
    spacing = pattern_size_override(pattern, spacing, pattern_size_values(settings))
    if pattern in ("concentric", "triangular", "diamonds", "hexagonal") and spacing > 0.0:
        pattern_gap = spacing * (1.35 if pattern == "concentric" else 0.85)
        max_gap = max(pattern_gap, float(getattr(settings, "pen_diameter_mm", 0.0)) * 6.0)
        if 1e-9 < travel_cost <= max_gap:
            ratio = max(float(getattr(settings, "theta_drive_ratio", 1.0)), 1e-9)
            motor_delta = abs(delta) * ratio
            motion_len = math.hypot(travel_cost, motor_delta)
            draw_ms = motion_len / max(float(getattr(settings, "feed_rate", 1.0)), 1e-9) * 60000.0
            travel_ms = motion_len / max(float(getattr(settings, "travel_rate", 1.0)), 1e-9) * 60000.0
            if draw_ms < travel_ms + pen_cycle_ms:
                return math.hypot(travel_cost, theta_cost)
    return travel_cost + theta_cost + pen_cycle_ms


import heapq as _heapq

_PLANNER_CANDIDATE_COUNT = 12


def _machine_to_bed(point, theta_deg, center):
    angle = math.radians(-theta_deg)
    dx = point[0] - center[0]
    dy = point[1] - center[1]
    c = math.cos(angle)
    s = math.sin(angle)
    return (center[0] + dx * c - dy * s, center[1] + dx * s + dy * c)


def _ring_cells(cx, cy, r):
    if r == 0:
        yield (cx, cy)
        return
    for dx in range(-r, r + 1):
        yield (cx + dx, cy - r)
        yield (cx + dx, cy + r)
    for dy in range(-r + 1, r):
        yield (cx - r, cy + dy)
        yield (cx + r, cy + dy)


def planned_contours(contours, settings, center):
    items = []
    for index, contour in enumerate(contours):
        path = filtered_contour(contour)
        if len(path) >= 2:
            items.append({"index": index, "path": path})
    if not items:
        return []

    bed_radius = max(float(getattr(settings, "bed_diameter_mm", 457.2)), 1.0) / 2.0
    cell_size = max(bed_radius / 8.0, 1.0)
    cell_sq = cell_size * cell_size
    max_ring = int(math.ceil(bed_radius / cell_size)) + 4

    grid = {}
    active = [True] * len(items)

    def cell_key(point):
        return (int(math.floor(point[0] / cell_size)), int(math.floor(point[1] / cell_size)))

    for i, item in enumerate(items):
        path = item["path"]
        grid.setdefault(cell_key(path[0]), []).append((i, False))
        grid.setdefault(cell_key(path[-1]), []).append((i, True))

    ordered = []
    previous_theta = None
    previous_machine = None
    # Sign of the last inter-contour bed rotation: +1 = increasing theta, -1 =
    # decreasing, 0 = unknown (start of job). Drives contour_entry_cost when
    # monotonic_theta is enabled — r-theta tables embrace continuous rotation;
    # we mimic that by biasing the ordering against reversals.
    running_direction = 0
    K = _PLANNER_CANDIDATE_COUNT

    while True:
        if previous_machine is None:
            search_pt = center
        else:
            search_pt = _machine_to_bed(previous_machine, previous_theta or 0.0, center)
        scx, scy = cell_key(search_pt)
        sx, sy = search_pt

        top_k = []  # max-heap by (-squared_distance, slot)
        any_seen = False
        for r in range(max_ring + 1):
            ring_had_active = False
            for key in _ring_cells(scx, scy, r):
                if key not in grid:
                    continue
                bucket = grid[key]
                live = []
                for slot in bucket:
                    item_idx, reverse_flag = slot
                    if not active[item_idx]:
                        continue
                    live.append(slot)
                    ring_had_active = True
                    path = items[item_idx]["path"]
                    pt = path[-1] if reverse_flag else path[0]
                    dx = pt[0] - sx
                    dy = pt[1] - sy
                    d2 = dx * dx + dy * dy
                    if len(top_k) < K:
                        _heapq.heappush(top_k, (-d2, slot))
                    elif d2 < -top_k[0][0]:
                        _heapq.heappushpop(top_k, (-d2, slot))
                if len(live) != len(bucket):
                    grid[key] = live
            if ring_had_active:
                any_seen = True
            if any_seen and len(top_k) >= K:
                worst = -top_k[0][0]
                if worst <= (r * cell_size) ** 2:
                    break

        candidates = [slot for _, slot in top_k]
        if not candidates:
            break

        best = None
        for item_idx, reverse_flag in candidates:
            item = items[item_idx]
            path = list(reversed(item["path"])) if reverse_flag else item["path"]
            first_theta = first_segment_theta(path, settings, previous_theta, center, previous_machine)
            if first_theta is None:
                continue
            start_machine = bed_to_machine(path[0], first_theta, center)
            cost = contour_entry_cost(start_machine, first_theta, previous_machine, previous_theta, settings, running_direction)
            if best is None or cost < best["cost"]:
                best = {
                    "item_idx": item_idx,
                    "index": item["index"],
                    "path": path,
                    "first_theta": first_theta,
                    "start_machine": start_machine,
                    "cost": cost,
                    "reversed": reverse_flag,
                }

        if best is None:
            for item_idx, _ in candidates:
                active[item_idx] = False
            continue

        state = simulate_contour_exit(best["path"], settings, center, previous_theta, previous_machine)
        active[best["item_idx"]] = False
        if state is None:
            continue
        best["state"] = state
        ordered.append(best)
        # Update running direction from the *entry* rotation that brought the
        # bed to this contour. Internal-to-contour winding can flip back and
        # forth (DP minimizes that), but the inter-contour sign is what the
        # next pick should honor.
        if previous_theta is not None:
            entry_delta = best["first_theta"] - previous_theta
            if abs(entry_delta) > 1e-6:
                running_direction = 1 if entry_delta > 0 else -1
        previous_theta = state["end_theta"]
        previous_machine = state["end_machine"]

    return _two_opt_pass(ordered, window=24)


def _two_opt_pass(ordered, window=24):
    # Bounded 2-opt on bed-frame endpoints. Adjacent contours rotate the bed
    # little, so bed-frame distance tracks machine travel closely enough to fix
    # gross ordering mistakes. Downstream recomputes exact kinematics, so we only
    # need to settle order + direction here — no re-simulation required.
    n = len(ordered)
    if n < 4:
        return ordered

    def gap(p, q):
        dx = p[0] - q[0]
        dy = p[1] - q[1]
        return math.hypot(dx, dy)

    for i in range(n - 2):
        a_end = ordered[i]["path"][-1]
        b_start = ordered[i + 1]["path"][0]
        best_j = -1
        best_delta = -1e-9
        for j in range(i + 2, min(i + 1 + window, n)):
            c_end = ordered[j]["path"][-1]
            base = gap(a_end, b_start)
            swap = gap(a_end, c_end)
            if j + 1 < n:
                d_start = ordered[j + 1]["path"][0]
                base += gap(c_end, d_start)
                swap += gap(b_start, d_start)
            delta = swap - base
            if delta < best_delta:
                best_delta = delta
                best_j = j
        if best_j > 0:
            sub = ordered[i + 1 : best_j + 1]
            sub.reverse()
            for item in sub:
                item["path"] = list(reversed(item["path"]))
                item["reversed"] = not item.get("reversed", False)
            ordered[i + 1 : best_j + 1] = sub
    return ordered


