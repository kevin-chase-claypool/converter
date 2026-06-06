from dataclasses import dataclass, fields

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
    tool_offset_x_mm: float = 34.544
    tool_offset_y_mm: float = -13.538
    pen_up_command: str = "M5"
    pen_down_command: str = "M3"
    flip_y: bool = True
    include_z: bool = True
    preview_xy_only: bool = False
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
        ("Tool offset X mm", "tool_offset_x_mm", "34.544"),
        ("Tool offset Y mm", "tool_offset_y_mm", "-13.538"),
        ("Pen up cmd", "pen_up_command", "M5"),
        ("Pen down cmd", "pen_down_command", "M3"),
    )),
    ("Preview settings", (
        ("Print speed mm/s", "print_speed", "100"),
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
    ("Pen", "include_z", "Use Z axis for pen up/down", True),
    ("Other settings", "preview_xy_only", "Preview mode: omit theta axis", False),
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
    return Settings(**kwargs)
