import math
from dataclasses import dataclass, field, fields


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
    feed_rate: float = 1200.0
    travel_rate: float = 3000.0
    safe_z: float = 5.0
    work_z: float = 0.0
    theta_axis: str = "A"
    theta_offset: float = 0.0
    theta_drive_ratio: float = 12.0
    theta_tangential_speed_mm_min: float = 1200.0
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
    pen_up_ms: float = 300.0
    pen_down_ms: float = 600.0
    pen_up_command: str = "M5"
    pen_down_command: str = "M3"
    flip_y: bool = True
    # This machine exposes a Z slot only to enable A in the controller build;
    # its pen contract is M3/M5, not physical Z motion.
    include_z: bool = False
    compensate_pen_width: bool = True


TEXT_FIELD_GROUPS = (
    ("Geometry", (
        ("Scale", "scale", "1.0"),
        ("Tolerance", "tolerance", "0.25"),
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
        ("Feed rate", "feed_rate", "1200"),
        ("Travel rate", "travel_rate", "3000"),
    )),
    ("Theta kinematics", (
        ("Theta axis", "theta_axis", "A"),
        ("Theta offset", "theta_offset", "0"),
        ("Theta ratio", "theta_drive_ratio", "12"),
        ("Theta tangential speed mm/min", "theta_tangential_speed_mm_min", "1200"),
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
        ("Pen up ms", "pen_up_ms", "300"),
        ("Pen down ms", "pen_down_ms", "600"),
        ("Pen up cmd", "pen_up_command", "M5"),
        ("Pen down cmd", "pen_down_command", "M3"),
    )),
    ("Preview settings", (
        ("Preview playback speed mm/s", "print_speed", "100"),
        ("Bed dia mm", "bed_diameter_mm", "457.2"),
        ("Bed margin mm", "bed_margin_mm", "6.35"),
        ("Pen stroke mm", "pen_diameter_mm", "0.3"),
    )),
)

CHECKBOX_FIELDS = (
    ("Geometry", "flip_y", "Flip SVG Y axis", True),
    ("Geometry", "compensate_pen_width", "Compensate pen stroke", True),
    ("Shading", "raster_shading", "Raster shading", False),
    ("Theta kinematics", "monotonic_theta", "Monotonic theta (r-theta style)", True),
    ("Pen", "include_z", "Use Z axis for pen up/down", False),
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


def pattern_size_values(settings):
    return {pattern: float(getattr(settings, field, 0.0)) for pattern, field in PATTERN_SIZE_FIELDS.items()}


def pattern_size_override(pattern, fallback, values=None):
    value = 0.0
    if values:
        value = float(values.get(pattern, 0.0))
    return value if value > 0.0 else fallback


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
        "pen_up_ms",
        "pen_down_ms",
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
    return settings
