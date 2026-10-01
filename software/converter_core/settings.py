import math
import re
from dataclasses import dataclass, field, fields


# M-06 pen-free radius sweep: 75.05 s observed movement / 160.58 s model.
# This is a display-only correction for the installed RP23CNC motion profile;
# it must never alter emitted feeds or G-code.
DEFAULT_MOTION_ESTIMATE_SCALE = 75.05 / 160.58


def calibrated_motion_seconds(model_seconds, scale=DEFAULT_MOTION_ESTIMATE_SCALE):
    """Return a display-only calibrated motion duration in seconds."""
    model_seconds = float(model_seconds)
    scale = float(scale)
    if not math.isfinite(model_seconds) or model_seconds < 0.0:
        raise ValueError("model motion time must be finite and non-negative.")
    if not math.isfinite(scale) or scale <= 0.0:
        raise ValueError("motion estimate scale must be finite and greater than zero.")
    return model_seconds * scale


@dataclass(frozen=True)
class ThetaControllerLimits:
    """Installed RP23CNC A-axis limits in motor-shaft units.

    These defaults mirror the validated controller configuration ($113/$123).
    They are intentionally not exposed as another Qt control: changing them
    requires a matching machine-controller change and hardware verification.
    """

    max_rate_deg_min: float = 80000.0
    max_acceleration_deg_s2: float = 6000.0

@dataclass
class Settings:
    scale: float = 1.0
    tolerance: float = 0.25
    # Slower pen travel means smaller, slower friction changes for the toolhead
    # force loop to absorb. 700 mm/min is the calm first-plot setting; raise it
    # once the hold is proven.
    feed_rate: float = 700.0
    travel_rate: float = 3000.0
    safe_z: float = 5.0
    work_z: float = 0.0
    theta_axis: str = "A"
    theta_offset: float = 0.0
    # Effective bed reduction: measured, not nominal. Three independent P112
    # outer-index surveys (2026-09-11 4331.818, 2026-09-24 4331.930 and
    # 2026-09-30 4332.153 A motor-degrees per bed revolution, total spread
    # 0.335) give 4331.97 / 360 = 12.03324. The hardware is nominally a
    # 60T:720T GT2 pair, but the emitted A values must use the effective ratio
    # or every commanded bed revolution lands about 1 degree short. Re-derive
    # this only from a new survey, and update the P100/P112 gate with it.
    theta_drive_ratio: float = 12.03324
    # Bed rotation drags the pen tangentially, so bound it like the draw feed.
    theta_tangential_speed_mm_min: float = 700.0
    theta_controller_limits: ThetaControllerLimits = field(default_factory=ThetaControllerLimits)
    theta_mode: str = "optimized"
    theta_resolver: str = "rtheta"
    theta_weight: float = 1.0
    # Re-register the bed at every contour: subtract whole revolutions from the
    # bed angle so the commanded A never winds far from zero. Physically
    # neutral - the bed ends at the same orientation - but on a machine whose A
    # axis has a small scale error, the positional error at a feature grows
    # with the commanded angle, so this removes most of the drift that shows up
    # at high A values.
    theta_wrap: bool = True
    round_bias: float = 0.05
    smoothness_factor: float = 1.0
    theta_smooth_window: int = 2
    monotonic_theta: bool = True
    bed_diameter_mm: float = 457.2
    bed_margin_mm: float = 6.35
    # Radius the gantry can actually reach from the registered bed center, in
    # the tightest direction. The bed rotates freely, so any artwork point at
    # radius r must be reachable at every bed angle; the safe drawable area is
    # therefore a circle of this radius, not the full bed circle.
    #
    # The binding direction is +Y, and its edge is the controller's soft-limit
    # envelope rather than the switch position. grblHAL builds that envelope in
    # limits_set_work_envelope() as [max_travel + pulloff, -pulloff] for a homed
    # axis when hard limits are enabled, so $27 (homing pull-off) shrinks the
    # homed end by that much to avoid re-triggering the switch. With $130=455,
    # $131=451, $132/27=10 and the bed center registered by HOME + REGISTER at
    # machine -232.449, -195.270 (2026-09-29), the enforced work-coordinate
    # limits are X -212.551..222.449 and Y -245.730..185.270. +Y is therefore
    # 185.270 mm from the bed center, and 185.0 leaves a hair of margin.
    #
    # $21 matters as much as the travel values: with hard limits disabled the
    # pull-off term is zero and the +Y edge moves back to machine 0, i.e.
    # 195.27 mm from the same bed center. Re-derive after every registration,
    # because the bed center, not the travel, is what moves.
    #
    # Clip radius becomes min(bed_diameter/2 - bed_margin, this).
    machine_reach_radius_mm: float = 185.0
    # Where the artwork's own center is placed relative to the registered bed
    # center, in machine millimetres. plan_program centers the artwork on the bed
    # by default; these offsets move it, which is how a drawing whose bounding
    # box is not its visual center gets placed by hand. Negative is valid.
    artwork_offset_x_mm: float = 0.0
    artwork_offset_y_mm: float = 0.0
    # Outlines only by default. Line art is the common case here, and a fill
    # that is coarse relative to a small closed shape leaves one or two short
    # fragments inside it - the "random dashes" seen on 2026-09-30. A positive
    # value opts into hatching.
    hatch_spacing_mm: float = 0.0
    hatch_angle_deg: float = 45.0
    hatch_pattern: str = "crosshatch"
    triangle_size_mm: float = 0.0
    diamond_size_mm: float = 0.0
    hex_size_mm: float = 0.0
    circle_size_mm: float = 0.0
    dot_spacing_mm: float = 0.0
    wave_size_mm: float = 0.0
    # `sine_gradient` reads its amplitude from the rendered tone. This is the
    # crest height as a percentage of the row spacing, so 50 just touches the
    # neighbouring row's baseline when the artwork is fully dark.
    gradient_wave_amplitude_pct: float = 50.0
    gyroid_size_mm: float = 0.0
    cubic_size_mm: float = 0.0
    concentric_spacing_mm: float = 0.0
    shade_levels: int = 1
    shade_angle_step_deg: float = 90.0
    # Where fill geometry comes from: "auto" resolves per SVG, "shapes" always
    # hatches the vector regions (filled shapes, or regions enclosed by closed
    # outlines), and "tone" always hatches the rendered image. See
    # `resolve_fill_source`.
    fill_source: str = "auto"
    raster_px_per_unit: float = 2.0
    # How `scale` is chosen. "manual" uses the field; "fill" and "inside" size
    # the artwork to the drawable circle automatically on every build, so the
    # artwork lands on the bed without the user computing a scale by hand.
    fit_mode: str = "fill"
    # Sakura Pigma Micron 005: the pen the machine actually plots with.
    pen_diameter_mm: float = 0.20
    pen_cycle_ms: float = 100.0
    # Measured on the integrated toolhead: M3 seeks in about 1.2 s warm and
    # ~2.9 s from GP2, and M5 clears in about 0.46 s. The dwell must cover the
    # actuation, or the drawing move starts while the pen is still in the air.
    pen_up_ms: float = 800.0
    pen_down_ms: float = 2500.0
    # Program start only. The toolhead parks on the GP2 lift switch, so the
    # program's first M3 has to travel the whole retract distance before it
    # reaches paper, while every later M3 starts from the ~1 mm M5 clearance
    # and completes in 2-3 s. Measured at about 7 s on the installed mechanism.
    # Without this longer first dwell grblHAL begins the first stroke while the
    # pen is still descending, so the leading section of the path is drawn in
    # the air. The margin above the measured 7 s covers the release-tare
    # settling and the pen-clamp variation that changes the retract distance.
    pen_down_first_ms: float = 10000.0
    pen_up_command: str = "M5"
    pen_down_command: str = "M3"
    # Emits the controller-resident P115 acknowledgement macro after each M3/M5
    # transition, replacing the fixed G4 dwells with a closed-loop wait for the
    # toolhead's GP27 ready signal. P115 is a fatal guard: when GP27/PRB does
    # not show a fresh inactive-to-active edge inside its 0.50 s / 5.00 s
    # bounds it raises error 39 and the controller aborts the streaming program
    # mid-print. F-05A (the on-bench P115/PRB validation) passed on 2026-09-29,
    # so its prerequisites are met, but the shipped default deliberately stays
    # on the fixed dwell path: the intermittent timeout seen in real printing
    # is still unexplained and the handshake remains an explicit opt-in.
    toolhead_status_handshake: bool = False
    # Only meaningful with `toolhead_status_handshake`. Emits `G65 P115 ... A<lift> W2`
    # for the normal M3/M5 handshakes so a timeout prints a controller warning,
    # issues `M5` to lift the pen to the fail-safe state, dwells for the lift, and
    # returns instead of raising error 39 and aborting the print. The end-of-print
    # full-retract wait still uses `W1` (warn + dwell, no lift) because the pen is
    # already up and the Aux0/GP28 arm drives that retract. This masks a genuinely
    # stuck toolhead signal, so it stays an explicit opt-in.
    toolhead_handshake_recover: bool = False
    # End-of-print park, expressed in machine coordinates (G53). After the last
    # pen-up the toolhead moves here so the pen clears the rotating bed and the
    # paper can be removed. Defaults match the installed machine's homed rest
    # position (X=0 and Y=-446 limit switches with the 10 mm $27 pull-off), and
    # must stay inside the configured software envelope ($130/$131).
    park_x_machine: float = -10.0
    park_y_machine: float = -436.0
    flip_y: bool = True
    # This machine exposes a Z slot only to enable A in the controller build;
    # its pen contract is M3/M5, not physical Z motion.
    include_z: bool = False
    compensate_pen_width: bool = True
    # Expand stroked paths into filled outlines of the stroke width. For a pen
    # plotter the pen already marks its own width, so drawing the centerline is
    # correct and produces far fewer M3/M5 cycles. Disabled by default.
    expand_strokes: bool = False
    # When enabled, a stroked path is drawn as a single centerline unless its
    # width is at least stroke_fill_ratio times the pen diameter; a stroke that
    # wide is instead filled with parallel passes so its interior is solid.
    # A pen already marks its own width, so thin strokes should stay one pass;
    # this only adds passes for strokes the pen cannot render in one line.
    fill_wide_strokes: bool = False
    stroke_fill_ratio: float = 2.0
    # Draw a short connector between two nearby generated fill trails instead of
    # lifting the pen (one M3/M5 cycle saved per joined pair). Off by default:
    # the connector is only invisible inside a filled region, so this stays an
    # explicit choice. Bridging is restricted to FillTrail contours, never the
    # artwork's own open strokes.
    keep_down_bridges: bool = False
    # `sine_gradient` only: join the end of one sine row to the start of the
    # next so a gradient is drawn as one continuous pen-down stroke instead of
    # one M3/M5 cycle per row. A join that would cross blank paper still breaks.
    sine_rows_connected: bool = True


TEXT_FIELD_GROUPS = (
    ("Geometry", (
        ("Scale", "scale", "1.0"),
        ("Fit", "fit_mode", "fill"),
        ("Tolerance", "tolerance", "0.25"),
        # Placement belongs with the artwork geometry: these two offsets move
        # the artwork's center away from the registered bed center and therefore
        # change the emitted program, not the view.
        ("Artwork offset X mm", "artwork_offset_x_mm", "0"),
        ("Artwork offset Y mm", "artwork_offset_y_mm", "0"),
        ("Stroke fill ratio", "stroke_fill_ratio", "2"),
    )),
    ("Fill", (
        ("Fill spacing mm", "hatch_spacing_mm", "0"),
        ("Fill pattern", "hatch_pattern", "crosshatch"),
        ("Fill angle deg", "hatch_angle_deg", "45"),
        ("Fill source", "fill_source", "auto"),
        ("Triangle size mm", "triangle_size_mm", "0"),
        ("Diamond size mm", "diamond_size_mm", "0"),
        ("Hex size mm", "hex_size_mm", "0"),
        ("Circle size mm", "circle_size_mm", "0"),
        ("Dot spacing mm", "dot_spacing_mm", "0"),
        ("Wave size mm", "wave_size_mm", "0"),
        ("Gradient wave amplitude %", "gradient_wave_amplitude_pct", "50"),
        ("Gyroid size mm", "gyroid_size_mm", "0"),
        ("Cubic size mm", "cubic_size_mm", "0"),
        ("Concentric spacing mm", "concentric_spacing_mm", "0"),
        ("Shade levels", "shade_levels", "1"),
        ("Shade angle step", "shade_angle_step_deg", "90"),
        ("Raster px/unit", "raster_px_per_unit", "2"),
    )),
    ("Motion", (
        ("Feed rate", "feed_rate", "700"),
        ("Travel rate", "travel_rate", "3000"),
    )),
    ("Theta kinematics", (
        ("Theta axis", "theta_axis", "A"),
        ("Theta offset", "theta_offset", "0"),
        ("Theta ratio", "theta_drive_ratio", "12.03324"),
        ("Theta tangential speed mm/min", "theta_tangential_speed_mm_min", "700"),
        ("Theta mode", "theta_mode", "optimized"),
        ("Theta resolver", "theta_resolver", "rtheta"),
        ("Theta weight", "theta_weight", "1.0"),
        ("Curve round bias", "round_bias", "0.05"),
        ("Smoothness factor", "smoothness_factor", "1.0"),
        ("Theta smooth", "theta_smooth_window", "2"),
    )),
    ("Pen", (
        ("Pen stroke mm", "pen_diameter_mm", "0.20"),
        ("Safe Z", "safe_z", "5"),
        ("Work Z", "work_z", "0"),
        ("Pen up ms", "pen_up_ms", "800"),
        ("Pen down ms", "pen_down_ms", "2500"),
        ("Pen down first ms", "pen_down_first_ms", "10000"),
        ("Pen up cmd", "pen_up_command", "M5"),
        ("Pen down cmd", "pen_down_command", "M3"),
    )),
    # Bed size, reach cap, and the end-of-print park are machine setup: they
    # change the emitted program (clipping and the final G53 move), so they do
    # not belong in a preview-only group.
    ("Machine", (
        ("Bed dia mm", "bed_diameter_mm", "457.2"),
        ("Bed margin mm", "bed_margin_mm", "6.35"),
        ("Gantry reach radius mm", "machine_reach_radius_mm", "185.0"),
        ("Park X machine mm", "park_x_machine", "-10"),
        ("Park Y machine mm", "park_y_machine", "-436"),
    )),
    ("Preview settings", (
        ("Preview playback speed mm/s", "print_speed", "100"),
        ("Motion estimate scale", "motion_estimate_scale", f"{DEFAULT_MOTION_ESTIMATE_SCALE:.6f}"),
    )),
)

CHECKBOX_FIELDS = (
    ("Geometry", "flip_y", "Flip SVG Y axis", True),
    ("Geometry", "compensate_pen_width", "Compensate pen stroke", True),
    ("Geometry", "expand_strokes", "Expand strokes to outlines", False),
    ("Geometry", "fill_wide_strokes", "Fill wide strokes", False),
    ("Fill", "keep_down_bridges", "Keep pen down between fill trails", False),
    ("Fill", "sine_rows_connected", "Connect sine rows (one continuous stroke)", True),
    ("Theta kinematics", "monotonic_theta", "Monotonic theta (r-theta style)", True),
    (
        "Theta kinematics",
        "theta_wrap",
        "Re-register the bed each contour (keep A small)",
        True,
    ),
    ("Pen", "include_z", "Use Z axis for pen up/down", False),
    ("Pen", "toolhead_status_handshake", "Wait for GP27 toolhead ready (commissioned only)", False),
    ("Pen", "toolhead_handshake_recover", "Lift pen and continue if the GP27 handshake times out", False),
)

# Human-readable labels for `fill_source`. The Qt combo shows the label and
# stores the value, so the setting stays a short stable string.
FILL_SOURCE_CHOICES = (
    ("Auto (recommended)", "auto"),
    ("SVG shapes (stays inside)", "shapes"),
    ("Image tone (photos, gradients)", "tone"),
)

# Human-readable labels for `fit_mode`. "Fill bed" is the default because
# settings are not persisted across launches: a manual scale would have to be
# re-derived every session.
FIT_MODE_CHOICES = (
    ("Fill bed (auto)", "fill"),
    ("Fit inside (auto)", "inside"),
    ("Manual (use Scale)", "manual"),
)

# Fields whose valid values are a fixed list. The Qt sidebar renders these as
# combos so invalid or misspelled values cannot be entered, and `validate_settings`
# checks them again for programmatic callers.
HATCH_PATTERNS = (
    "linear",
    "crosshatch",
    # Near the top on purpose: the sidebar shows this tuple in order, and the
    # gradient fill was effectively invisible at the bottom of the list.
    "sine_gradient",
    "diagonal",
    "diagonal_crosshatch",
    "triangular",
    "cubic",
    "diamonds",
    "hexagonal",
    "circles",
    "dots",
    "waves",
    "gyroid",
    "concentric",
)

# "optimized" is the per-contour resolver; "fixed" and "tangent" pin the bed
# orientation. The experimental cost resolvers stay selectable through
# `theta_resolver`.
THETA_MODES = ("optimized", "fixed", "tangent")
THETA_RESOLVERS = ("rtheta", "dp", "greedy")

VALUE_CHOICE_FIELDS = {
    "hatch_pattern": HATCH_PATTERNS,
    "theta_mode": THETA_MODES,
    "theta_resolver": THETA_RESOLVERS,
}

# Readable combo labels for the values above. The stored value stays the short
# canonical id, so settings files, the cache key, and `validate_settings` all
# keep one spelling and `normalized_hatch_pattern` can read either form.
HATCH_PATTERN_LABELS = {
    "linear": "linear (parallel lines)",
    "cubic": "cubic (isometric)",
    "waves": "waves (uniform sine rows)",
    "sine_gradient": "gradient waves (sine_gradient)",
    "concentric": "concentric (inset loops)",
}

VALUE_CHOICE_LABELS = {
    "hatch_pattern": HATCH_PATTERN_LABELS,
}

# Short in-UI explanations for the settings that are otherwise easy to
# misread. Qt shows these as tooltips.
FIELD_TOOLTIPS = {
    "scale": "Artwork scale. 1.0 plots the SVG at its document size in millimetres.",
    "tolerance": "How far a curve may deviate from a straight move, in mm. Larger is faster and coarser.",
    "artwork_offset_x_mm": "Move the artwork's center off the registered bed center, in machine mm. You can also drag the artwork in the preview.",
    "artwork_offset_y_mm": "Move the artwork's center off the registered bed center, in machine mm. You can also drag the artwork in the preview.",
    "stroke_fill_ratio": "With 'Fill wide strokes', a stroke is filled only when its width is at least this many pen diameters.",
    "keep_down_bridges": "Draw a connector between two nearby generated fill trails instead of lifting the pen. Only applies between fill trails, never across the artwork's own strokes, and off by default because a connector in blank space leaves a visible mark.",
    "hatch_spacing_mm": "Distance between fill lines in mm on paper. 0 (the default) plots outlines only.",
    "hatch_pattern": "Fill pattern drawn inside each filled region. 'gradient waves (sine_gradient)' carries tone as wave amplitude and needs the image-tone fill source.",
    "hatch_angle_deg": "Rotation of the fill line family.",
    "fill_source": "Auto hatches the SVG's own shapes, and switches to image tone only when the artwork's tone comes from an embedded image or gradient. 'SVG shapes' always stays inside the drawn regions; 'Image tone' hatches the rendered pixels.",
    "fit_mode": "How Scale is chosen. 'Fill bed' sizes the artwork's bounds to the drawable circle on every build, 'Fit inside' keeps every point inside it, and 'Manual' uses the Scale field. Both auto fits override Scale, which is why the Scale box is read-only while one is selected.",
    "scale": "Artwork scale. Set by the Fit mode while an auto fit is selected; choose Manual to type a value.",
    "shade_levels": "Density steps for tone: darker fill colour or image tone receives more fill families.",
    "shade_angle_step_deg": "Angle between the fill families that darker tone adds.",
    "gradient_wave_amplitude_pct": "Sine gradient only: crest height as a percentage of Fill spacing / Wave size mm. 50 makes a fully dark area's waves just touch the next row.",
    "sine_rows_connected": "Sine gradient only: join the end of one sine row to the start of the next so a gradient is drawn as one continuous stroke. Rows stay separate where the join would cross blank paper.",
    "raster_px_per_unit": "Image-tone sampling resolution in pixels per mm. Higher is more accurate and slower.",
    "feed_rate": "Maximum X/Y draw speed in mm/min.",
    "travel_rate": "Pen-up travel speed in mm/min.",
    "theta_mode": "How the bed orientation is chosen per contour: optimized solves it, fixed holds one angle, tangent follows the path direction.",
    "theta_resolver": "Per-segment theta solver. rtheta is the installed default; dp and greedy are fallback experiments.",
    "theta_wrap": "Subtract whole bed revolutions at every contour so the commanded A stays near zero. The bed ends in the same place, but any small A-axis scale error stops accumulating with angle - turn this off to match older programs.",
    "pen_diameter_mm": "Physical pen tip width. Used for ink-size reporting, pen-width compensation, and the 'Fill wide strokes' threshold.",
    "safe_z": "Z height for pen-up simulation. Only used when 'Use Z axis' is enabled.",
    "work_z": "Z height for pen-down simulation. Only used when 'Use Z axis' is enabled.",
    "pen_up_ms": "Dwell after M5/M3 lift. This is a fixed G4 wait; the pen height itself is owned by the toolhead.",
    "pen_down_ms": "Dwell after M3 engage. Covers the toolhead's warm contact seek from the M5 clearance.",
    "pen_down_first_ms": "Dwell after the program's first M3 only, because that seek starts at the GP2 lift switch.",
    "pen_up_command": "Pen-up command. M5 for this machine.",
    "pen_down_command": "Pen-down command. M3 for this machine.",
    "bed_diameter_mm": "Bed diameter in mm. Clipping keeps the pen inside this circle (minus bed margin and the gantry reach cap).",
    "bed_margin_mm": "Keeps the pen clear of the bed rim by this many mm.",
    "machine_reach_radius_mm": "Radius the gantry can reach from the registered bed center. Artwork beyond it is clipped so soft limits are not tripped.",
    "park_x_machine": "End-of-program park X in machine (G53) coordinates.",
    "park_y_machine": "End-of-program park Y in machine (G53) coordinates.",
    "print_speed": "Preview playback speed only. It does not change the emitted program.",
    "motion_estimate_scale": "Display-only calibration of the time estimate for this machine.",
}

SETTING_TYPES = {field.name: field.type for field in fields(Settings)}

PATTERN_SIZE_FIELDS = {
    "triangular": "triangle_size_mm",
    "diamonds": "diamond_size_mm",
    "hexagonal": "hex_size_mm",
    "circles": "circle_size_mm",
    "dots": "dot_spacing_mm",
    "waves": "wave_size_mm",
    "sine_gradient": "wave_size_mm",
    "gyroid": "gyroid_size_mm",
    "cubic": "cubic_size_mm",
    "concentric": "concentric_spacing_mm",
}

# Lattice patterns treat their dedicated "size" as the side/diameter of one
# cell, not a line spacing. If that size is left at 0 the converter currently
# falls back to `Fill spacing`, but a 5 mm line spacing interpreted as a 5 mm
# cell produces an extremely dense (and slow) lattice. Scale the fallback so an
# unset cell size lands near the visual density of the equivalent line hatch.
CELL_PATTERNS = frozenset({"triangular", "diamonds", "hexagonal", "circles"})
CELL_SPACING_SCALE = 6.0


def pattern_size_values(settings):
    return {pattern: float(getattr(settings, field, 0.0)) for pattern, field in PATTERN_SIZE_FIELDS.items()}


def pattern_size_override(pattern, fallback, values=None):
    value = 0.0
    if values:
        value = float(values.get(pattern, 0.0))
    if value > 0.0:
        return value
    fallback = float(fallback)
    if pattern in CELL_PATTERNS:
        return max(fallback * CELL_SPACING_SCALE, 1e-6)
    return fallback


def coerce_setting(name, text):
    kind = SETTING_TYPES[name]
    if kind is bool:
        return bool(text)
    if kind is int:
        return int(float(text))
    if kind is float:
        return float(text)
    return str(text)


def settings_from_values(text_values, bool_values):
    kwargs = {}
    for field in fields(Settings):
        if field.name in bool_values:
            kwargs[field.name] = bool(bool_values[field.name])
        elif field.name in text_values:
            kwargs[field.name] = coerce_setting(field.name, text_values[field.name])
    return validate_settings(Settings(**kwargs))


def validate_settings(settings):
    """Reject values that cannot produce a safe, meaningful machine program."""
    positive = (
        "scale",
        "tolerance",
        "feed_rate",
        "travel_rate",
        "theta_drive_ratio",
        "bed_diameter_mm",
        "raster_px_per_unit",
    )
    nonnegative = (
        "theta_tangential_speed_mm_min",
        "theta_weight",
        "round_bias",
        "smoothness_factor",
        "hatch_spacing_mm",
        "triangle_size_mm",
        "diamond_size_mm",
        "hex_size_mm",
        "circle_size_mm",
        "dot_spacing_mm",
        "wave_size_mm",
        "gradient_wave_amplitude_pct",
        "gyroid_size_mm",
        "cubic_size_mm",
        "concentric_spacing_mm",
        "pen_diameter_mm",
        "stroke_fill_ratio",
        "pen_up_ms",
        "pen_down_ms",
        "pen_down_first_ms",
        "bed_margin_mm",
        "machine_reach_radius_mm",
    )
    for name in positive:
        value = float(getattr(settings, name))
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"{name.replace('_', ' ')} must be greater than zero.")
    for name in nonnegative:
        value = float(getattr(settings, name))
        if not math.isfinite(value) or value < 0.0:
            raise ValueError(f"{name.replace('_', ' ')} cannot be negative.")
    # Placement offsets are deliberately signed, so only finiteness is enforced.
    for name in ("artwork_offset_x_mm", "artwork_offset_y_mm"):
        value = float(getattr(settings, name))
        if not math.isfinite(value):
            raise ValueError(f"{name.replace('_', ' ')} must be a finite number.")
    if int(settings.shade_levels) < 1:
        raise ValueError("shade levels must be at least one.")
    if float(settings.gradient_wave_amplitude_pct) > 100.0:
        raise ValueError(
            "gradient wave amplitude must not exceed 100 percent of the row spacing."
        )
    if int(settings.theta_smooth_window) < 0:
        raise ValueError("theta smooth window cannot be negative.")
    if float(settings.bed_margin_mm) * 2.0 >= float(settings.bed_diameter_mm):
        raise ValueError("bed margin must leave a positive drawable bed radius.")
    if str(settings.theta_axis).strip().upper() != "A":
        raise ValueError("theta axis must be A for this X/Y/A plotter.")
    if str(settings.fill_source).strip().lower() not in ("auto", "shapes", "tone"):
        raise ValueError("fill source must be auto, shapes, or tone.")
    if str(settings.fit_mode).strip().lower() not in ("fill", "inside", "manual"):
        raise ValueError("fit mode must be fill, inside, or manual.")
    for name, choices in VALUE_CHOICE_FIELDS.items():
        value = str(getattr(settings, name)).strip().lower()
        if value not in choices:
            raise ValueError(f"{name.replace('_', ' ')} must be one of: {', '.join(choices)}.")
    if settings.toolhead_status_handshake:
        if settings.include_z:
            raise ValueError(
                "GP27 toolhead-ready waiting requires the M3/M5 pen contract; disable Use Z axis."
            )
        if not re.search(r"\bM5\b", str(settings.pen_up_command), flags=re.IGNORECASE):
            raise ValueError(
                "GP27 toolhead-ready waiting requires an M5 pen-up command."
            )
        if not re.search(r"\bM3\b", str(settings.pen_down_command), flags=re.IGNORECASE):
            raise ValueError(
                "GP27 toolhead-ready waiting requires an M3 pen-down command."
            )
    return settings
