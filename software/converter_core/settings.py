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
    theta_drive_ratio: float = 12.0
    # Bed rotation drags the pen tangentially, so bound it like the draw feed.
    theta_tangential_speed_mm_min: float = 700.0
    theta_controller_limits: ThetaControllerLimits = field(default_factory=ThetaControllerLimits)
    theta_mode: str = "optimized"
    theta_resolver: str = "rtheta"
    theta_weight: float = 1.0
    round_bias: float = 0.05
    smoothness_factor: float = 1.0
    theta_smooth_window: int = 2
    monotonic_theta: bool = True
    bed_diameter_mm: float = 457.2
    bed_margin_mm: float = 6.35
    hatch_spacing_mm: float = 0.0
    hatch_angle_deg: float = 45.0
    hatch_pattern: str = "crosshatch"
    triangle_size_mm: float = 0.0
    diamond_size_mm: float = 0.0
    hex_size_mm: float = 0.0
    circle_size_mm: float = 0.0
    dot_spacing_mm: float = 0.0
    wave_size_mm: float = 0.0
    gyroid_size_mm: float = 0.0
    cubic_size_mm: float = 0.0
    concentric_spacing_mm: float = 0.0
    shade_levels: int = 1
    shade_angle_step_deg: float = 90.0
    raster_shading: bool = False
    raster_px_per_unit: float = 2.0
    pen_diameter_mm: float = 0.3
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
    # toolhead's GP27 ready signal. Enabled by default for the commissioned
    # machine (P115.macro installed, GP27/U3 -> PRB wired, and the toolhead
    # GP27_NORMAL_STATUS_ENABLED flag true). If the macro or wiring is missing
    # the generated program will error 39; uncheck to fall back to fixed dwells.
    toolhead_status_handshake: bool = True
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


TEXT_FIELD_GROUPS = (
    ("Geometry", (
        ("Scale", "scale", "1.0"),
        ("Tolerance", "tolerance", "0.25"),
        ("Stroke fill ratio", "stroke_fill_ratio", "2"),
    )),
    ("Shading", (
        ("Fill spacing mm", "hatch_spacing_mm", "0"),
        ("Fill angle deg", "hatch_angle_deg", "45"),
        ("Fill pattern", "hatch_pattern", "crosshatch"),
        ("Triangle size mm", "triangle_size_mm", "0"),
        ("Diamond size mm", "diamond_size_mm", "0"),
        ("Hex size mm", "hex_size_mm", "0"),
        ("Circle size mm", "circle_size_mm", "0"),
        ("Dot spacing mm", "dot_spacing_mm", "0"),
        ("Wave size mm", "wave_size_mm", "0"),
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
        ("Theta ratio", "theta_drive_ratio", "12"),
        ("Theta tangential speed mm/min", "theta_tangential_speed_mm_min", "700"),
        ("Theta mode", "theta_mode", "optimized"),
        ("Theta resolver", "theta_resolver", "rtheta"),
        ("Theta weight", "theta_weight", "1.0"),
        ("Curve round bias", "round_bias", "0.05"),
        ("Smoothness factor", "smoothness_factor", "1.0"),
        ("Theta smooth", "theta_smooth_window", "2"),
    )),
    ("Pen", (
        ("Safe Z", "safe_z", "5"),
        ("Work Z", "work_z", "0"),
        ("Pen up ms", "pen_up_ms", "800"),
        ("Pen down ms", "pen_down_ms", "2500"),
        ("Pen down first ms", "pen_down_first_ms", "10000"),
        ("Pen up cmd", "pen_up_command", "M5"),
        ("Pen down cmd", "pen_down_command", "M3"),
        ("Park X machine mm", "park_x_machine", "-10"),
        ("Park Y machine mm", "park_y_machine", "-436"),
    )),
    ("Preview settings", (
        ("Preview playback speed mm/s", "print_speed", "100"),
        ("Motion estimate scale", "motion_estimate_scale", f"{DEFAULT_MOTION_ESTIMATE_SCALE:.6f}"),
        ("Bed dia mm", "bed_diameter_mm", "457.2"),
        ("Bed margin mm", "bed_margin_mm", "6.35"),
        ("Pen stroke mm", "pen_diameter_mm", "0.3"),
    )),
)

CHECKBOX_FIELDS = (
    ("Geometry", "flip_y", "Flip SVG Y axis", True),
    ("Geometry", "compensate_pen_width", "Compensate pen stroke", True),
    ("Geometry", "expand_strokes", "Expand strokes to outlines", False),
    ("Geometry", "fill_wide_strokes", "Fill wide strokes", False),
    ("Shading", "raster_shading", "Raster shading", False),
    ("Theta kinematics", "monotonic_theta", "Monotonic theta (r-theta style)", True),
    ("Pen", "include_z", "Use Z axis for pen up/down", False),
    ("Pen", "toolhead_status_handshake", "Wait for GP27 toolhead ready (commissioned only)", True),
)

SETTING_TYPES = {field.name: field.type for field in fields(Settings)}

PATTERN_SIZE_FIELDS = {
    "triangular": "triangle_size_mm",
    "diamonds": "diamond_size_mm",
    "hexagonal": "hex_size_mm",
    "circles": "circle_size_mm",
    "dots": "dot_spacing_mm",
    "waves": "wave_size_mm",
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
        "gyroid_size_mm",
        "cubic_size_mm",
        "concentric_spacing_mm",
        "pen_diameter_mm",
        "stroke_fill_ratio",
        "pen_up_ms",
        "pen_down_ms",
        "pen_down_first_ms",
        "bed_margin_mm",
    )
    for name in positive:
        value = float(getattr(settings, name))
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"{name.replace('_', ' ')} must be greater than zero.")
    for name in nonnegative:
        value = float(getattr(settings, name))
        if not math.isfinite(value) or value < 0.0:
            raise ValueError(f"{name.replace('_', ' ')} cannot be negative.")
    if int(settings.shade_levels) < 1:
        raise ValueError("shade levels must be at least one.")
    if int(settings.theta_smooth_window) < 0:
        raise ValueError("theta smooth window cannot be negative.")
    if float(settings.bed_margin_mm) * 2.0 >= float(settings.bed_diameter_mm):
        raise ValueError("bed margin must leave a positive drawable bed radius.")
    if str(settings.theta_axis).strip().upper() != "A":
        raise ValueError("theta axis must be A for this X/Y/A plotter.")
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
