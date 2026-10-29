"""Full-field one-pen bed calibration geometry and measurement analysis."""

from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
import io
import math
import statistics

from .bed_compensation import BedCompensationProfile, interpolate_bed_correction


SHEET_DIAMETER_MM = 355.6
TEST_DIAMETER_MM = 330.2
TEST_RADIUS_MM = TEST_DIAMETER_MM / 2.0
COVERAGE_RADIUS_MM = TEST_RADIUS_MM
MARK_ARM_MM = 4.0
LANE_OFFSET_MM = 10.0
LABEL_INWARD_MM = 22.0
RING_SPECS = (
    (50.0, 8, 22.5),
    (95.0, 12, 0.0),
    (150.0, 16, 11.25),
)
FIDUCIAL_RADIUS_MM = 155.0


@dataclass(frozen=True)
class CalibrationStation:
    station_id: str
    ring_radius_mm: float
    station_angle_deg: float
    x_mm: float
    y_mm: float


@dataclass(frozen=True)
class CalibrationPass:
    pass_id: str
    pass_name: str
    angle_deg: float
    lane_x_mm: float
    lane_y_mm: float
    mark_kind: str


@dataclass(frozen=True)
class CalibrationMark:
    section: str
    station_id: str
    ring_radius_mm: float
    station_angle_deg: float
    base_x_mm: float
    base_y_mm: float
    pass_id: str
    pass_name: str
    mark_kind: str
    angle_deg: float
    nominal_x_mm: float
    nominal_y_mm: float
    measured_x_mm: float
    measured_y_mm: float


@dataclass(frozen=True)
class SimilarityAlignment:
    scale: float
    rotation_deg: float
    translation_x_mm: float
    translation_y_mm: float
    rms_residual_mm: float
    max_residual_mm: float

    def inverse_point(self, x_mm: float, y_mm: float):
        zx = x_mm - self.translation_x_mm
        zy = y_mm - self.translation_y_mm
        angle = math.radians(self.rotation_deg)
        a = self.scale * math.cos(angle)
        b = self.scale * math.sin(angle)
        denominator = self.scale * self.scale
        return (
            (a * zx + b * zy) / denominator,
            (a * zy - b * zx) / denominator,
        )

    def forward_point(self, x_mm: float, y_mm: float):
        angle = math.radians(self.rotation_deg)
        a = self.scale * math.cos(angle)
        b = self.scale * math.sin(angle)
        return (
            a * x_mm - b * y_mm + self.translation_x_mm,
            b * x_mm + a * y_mm + self.translation_y_mm,
        )


@dataclass(frozen=True)
class ErrorSummary:
    count: int
    rms_mm: float
    p95_mm: float
    max_mm: float
    mean_x_mm: float
    mean_y_mm: float


def _make_pass_specs(lane_offset_mm):
    diagonal = float(lane_offset_mm) * math.sqrt(0.5)
    return (
        CalibrationPass("1", "A000-REFERENCE", 0.0, 0.0, 0.0, "reference"),
        CalibrationPass(
            "2",
            "A045",
            45.0,
            diagonal,
            diagonal,
            "angle_45",
        ),
        CalibrationPass(
            "3",
            "A090",
            90.0,
            lane_offset_mm,
            0.0,
            "angle_90",
        ),
        CalibrationPass(
            "4",
            "A135",
            135.0,
            -diagonal,
            diagonal,
            "angle_135",
        ),
        CalibrationPass(
            "5",
            "A180",
            180.0,
            0.0,
            lane_offset_mm,
            "angle_180",
        ),
        CalibrationPass(
            "6",
            "A225",
            225.0,
            -diagonal,
            -diagonal,
            "angle_225",
        ),
        CalibrationPass(
            "7",
            "A270",
            270.0,
            -lane_offset_mm,
            0.0,
            "angle_270",
        ),
        CalibrationPass(
            "8",
            "A315",
            315.0,
            diagonal,
            -diagonal,
            "angle_315",
        ),
        CalibrationPass(
            "9",
            "A000-CONTROL",
            0.0,
            0.0,
            -lane_offset_mm,
            "control",
        ),
    )


PASS_SPECS = _make_pass_specs(LANE_OFFSET_MM)


@dataclass(frozen=True)
class CalibrationLayout:
    layout_id: str
    display_name: str
    ring_specs: tuple[tuple[float, int, float], ...]
    mark_arm_mm: float
    lane_offset_mm: float
    label_inward_mm: float
    label_height_mm: float
    test_diameter_mm: float
    fiducial_radius_mm: float
    fiducial_angles_deg: tuple[float, ...]
    fiducial_radial_arm_mm: float
    fiducial_tangent_arm_mm: float
    pass_specs: tuple[CalibrationPass, ...]

    @property
    def test_radius_mm(self):
        return self.test_diameter_mm / 2.0


STANDARD_LAYOUT = CalibrationLayout(
    layout_id="standard-37",
    display_name="37-station three-ring field",
    ring_specs=RING_SPECS,
    mark_arm_mm=MARK_ARM_MM,
    lane_offset_mm=LANE_OFFSET_MM,
    label_inward_mm=LABEL_INWARD_MM,
    label_height_mm=2.4,
    test_diameter_mm=TEST_DIAMETER_MM,
    fiducial_radius_mm=FIDUCIAL_RADIUS_MM,
    fiducial_angles_deg=(45.0, 135.0, 225.0, 315.0),
    fiducial_radial_arm_mm=-12.0,
    fiducial_tangent_arm_mm=7.0,
    pass_specs=PASS_SPECS,
)
DENSE_LAYOUT = CalibrationLayout(
    layout_id="dense-91",
    display_name="91-station balanced dense field",
    ring_specs=(
        (30.0, 6, 30.0),
        (60.0, 12, 15.0),
        (90.0, 18, 10.0),
        (120.0, 22, 8.1818181818),
        (148.5, 32, 50.625),
    ),
    mark_arm_mm=3.0,
    lane_offset_mm=7.0,
    label_inward_mm=10.0,
    label_height_mm=1.8,
    test_diameter_mm=TEST_DIAMETER_MM,
    fiducial_radius_mm=160.0,
    fiducial_angles_deg=(45.0, 135.0, 225.0, 315.0),
    fiducial_radial_arm_mm=4.0,
    fiducial_tangent_arm_mm=7.0,
    pass_specs=_make_pass_specs(7.0),
)
CALIBRATION_LAYOUTS = {
    layout.layout_id: layout
    for layout in (STANDARD_LAYOUT, DENSE_LAYOUT)
}


def calibration_layout(layout="standard-37"):
    """Return a known calibration layout by id or object."""
    if isinstance(layout, CalibrationLayout):
        return layout
    key = str(layout)
    try:
        return CALIBRATION_LAYOUTS[key]
    except KeyError as error:
        raise ValueError("unknown calibration layout %r" % key) from error

PROFILE_ANGLE_VALUES_DEG = tuple(
    sorted(
        {
            calibration_pass.angle_deg
            for calibration_pass in PASS_SPECS
        }
    )
)


_DIGIT_GLYPHS = {
    "0": (((0.0, 1.0), (0.0, 4.0), (3.0, 4.0), (3.0, 1.0), (0.0, 1.0)),),
    "1": (((1.5, 1.0), (1.5, 4.0)),),
    "2": (
        ((0.0, 4.0), (3.0, 4.0), (3.0, 2.5), (0.0, 2.5), (0.0, 1.0), (3.0, 1.0)),
    ),
    "3": (
        ((0.0, 4.0), (3.0, 4.0), (3.0, 1.0), (0.0, 1.0)),
        ((1.0, 2.5), (3.0, 2.5)),
    ),
    "4": (
        ((0.0, 4.0), (0.0, 2.5), (3.0, 2.5)),
        ((3.0, 4.0), (3.0, 1.0)),
    ),
    "5": (
        ((3.0, 4.0), (0.0, 4.0), (0.0, 2.5), (3.0, 2.5), (3.0, 1.0), (0.0, 1.0)),
    ),
    "6": (
        ((3.0, 4.0), (0.0, 4.0), (0.0, 1.0), (3.0, 1.0), (3.0, 2.5), (0.0, 2.5)),
    ),
    "7": (((0.0, 4.0), (3.0, 4.0), (3.0, 1.0)),),
    "8": (
        ((0.0, 1.0), (0.0, 4.0), (3.0, 4.0), (3.0, 1.0), (0.0, 1.0)),
        ((0.0, 2.5), (3.0, 2.5)),
    ),
    "9": (
        ((3.0, 1.0), (3.0, 4.0), (0.0, 4.0), (0.0, 2.5), (3.0, 2.5)),
    ),
}


def _fmt(value: float) -> str:
    if abs(float(value)) < 1e-9:
        return "0"
    return ("%.4f" % float(value)).rstrip("0").rstrip(".")


def calibration_stations(layout=STANDARD_LAYOUT):
    layout = calibration_layout(layout)
    stations = [
        CalibrationStation("00", 0.0, 0.0, 0.0, 0.0),
    ]
    station_number = 1
    for ring_radius_mm, count, phase_deg in layout.ring_specs:
        for index in range(count):
            station_angle_deg = phase_deg + index * 360.0 / count
            angle = math.radians(station_angle_deg)
            stations.append(
                CalibrationStation(
                    "%02d" % station_number,
                    ring_radius_mm,
                    station_angle_deg,
                    ring_radius_mm * math.cos(angle),
                    ring_radius_mm * math.sin(angle),
                )
            )
            station_number += 1
    return tuple(stations)


def fiducial_points(layout=STANDARD_LAYOUT):
    layout = calibration_layout(layout)
    points = []
    for number, angle_deg in enumerate(layout.fiducial_angles_deg, 1):
        angle = math.radians(angle_deg)
        x_mm = layout.fiducial_radius_mm * math.cos(angle)
        y_mm = layout.fiducial_radius_mm * math.sin(angle)
        points.append((number, angle_deg, x_mm, y_mm))
    return tuple(points)


def station_label_position(station, layout=STANDARD_LAYOUT):
    layout = calibration_layout(layout)
    if station.ring_radius_mm <= 1e-9:
        return station.x_mm, station.y_mm - layout.label_inward_mm
    scale = (
        station.ring_radius_mm - layout.label_inward_mm
    ) / station.ring_radius_mm
    return station.x_mm * scale, station.y_mm * scale


def l_mark_points(x_mm, y_mm, arm_mm=MARK_ARM_MM):
    return ((x_mm - arm_mm, y_mm), (x_mm, y_mm), (x_mm, y_mm + arm_mm))


def fiducial_mark_points(
    angle_deg,
    x_mm,
    y_mm,
    radial_arm_mm=-12.0,
    tangent_arm_mm=7.0,
):
    angle = math.radians(angle_deg)
    radial_x, radial_y = math.cos(angle), math.sin(angle)
    tangent_x, tangent_y = -radial_y, radial_x
    return (
        (x_mm, y_mm),
        (
            x_mm + radial_x * radial_arm_mm,
            y_mm + radial_y * radial_arm_mm,
        ),
        (
            x_mm + tangent_x * tangent_arm_mm,
            y_mm + tangent_y * tangent_arm_mm,
        ),
    )


def station_label_points(text, x_mm, y_mm, height_mm=2.4):
    scale = height_mm / 3.0
    char_width = 3.0 * scale
    spacing = 1.0 * scale
    total_width = len(text) * char_width + max(0, len(text) - 1) * spacing
    start_x = x_mm - total_width / 2.0
    base_y = y_mm - height_mm / 2.0
    output = []
    for char_index, char in enumerate(text):
        glyph = _DIGIT_GLYPHS.get(char)
        if glyph is None:
            raise ValueError("no calibration label glyph for %r" % char)
        char_x = start_x + char_index * (char_width + spacing)
        for polyline in glyph:
            output.append(
                tuple(
                    (char_x + point_x * scale, base_y + point_y * scale)
                    for point_x, point_y in polyline
                )
            )
    return tuple(output)


def mark_geometry(station, calibration_pass, layout=STANDARD_LAYOUT):
    layout = calibration_layout(layout)
    target_x = station.x_mm + calibration_pass.lane_x_mm
    target_y = station.y_mm + calibration_pass.lane_y_mm
    return target_x, target_y, l_mark_points(
        target_x,
        target_y,
        arm_mm=layout.mark_arm_mm,
    )


def expected_marks(layout=STANDARD_LAYOUT):
    layout = calibration_layout(layout)
    stations = calibration_stations(layout)
    marks = [
        CalibrationMark(
            "fiducial",
            "F%d" % number,
            layout.fiducial_radius_mm,
            angle_deg,
            x_mm,
            y_mm,
            layout.pass_specs[0].pass_id,
            layout.pass_specs[0].pass_name,
            "fiducial",
            0.0,
            x_mm,
            y_mm,
            math.nan,
            math.nan,
        )
        for number, angle_deg, x_mm, y_mm in fiducial_points(layout)
    ]
    for calibration_pass in layout.pass_specs:
        for station in stations:
            target_x, target_y, _points = mark_geometry(
                station,
                calibration_pass,
                layout,
            )
            marks.append(
                CalibrationMark(
                    "station",
                    station.station_id,
                    station.ring_radius_mm,
                    station.station_angle_deg,
                    station.x_mm,
                    station.y_mm,
                    calibration_pass.pass_id,
                    calibration_pass.pass_name,
                    calibration_pass.mark_kind,
                    calibration_pass.angle_deg,
                    target_x,
                    target_y,
                    math.nan,
                    math.nan,
                )
            )
    return tuple(marks)


def measurement_template_csv(marks=None, *, layout=STANDARD_LAYOUT):
    layout = calibration_layout(layout)
    marks = expected_marks(layout) if marks is None else marks
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(
        (
            "layout_id",
            "section",
            "station_id",
            "ring_radius_mm",
            "station_angle_deg",
            "pass_id",
            "pass_name",
            "mark_kind",
            "angle_deg",
            "base_x_mm",
            "base_y_mm",
            "nominal_x_mm",
            "nominal_y_mm",
            "measured_x_mm",
            "measured_y_mm",
        )
    )
    for mark in marks:
        writer.writerow(
            (
                layout.layout_id,
                mark.section,
                mark.station_id,
                _fmt(mark.ring_radius_mm),
                _fmt(mark.station_angle_deg),
                mark.pass_id,
                mark.pass_name,
                mark.mark_kind,
                _fmt(mark.angle_deg),
                _fmt(mark.base_x_mm),
                _fmt(mark.base_y_mm),
                _fmt(mark.nominal_x_mm),
                _fmt(mark.nominal_y_mm),
                "",
                "",
            )
        )
    return output.getvalue()


def _measurement_layout(fieldnames, rows, layout):
    explicit = calibration_layout(layout) if layout is not None else None
    if "layout_id" not in (fieldnames or ()):
        return explicit or STANDARD_LAYOUT
    layout_ids = {
        str(row.get("layout_id") or "").strip()
        for row in rows
        if str(row.get("layout_id") or "").strip()
    }
    if len(layout_ids) > 1:
        raise ValueError("measurement CSV mixes calibration layouts")
    detected = None
    if layout_ids:
        detected = calibration_layout(next(iter(layout_ids)))
    if explicit is not None and detected is not None:
        if explicit.layout_id != detected.layout_id:
            raise ValueError(
                "measurement CSV layout %s does not match requested layout %s"
                % (detected.layout_id, explicit.layout_id)
            )
    return explicit or detected or STANDARD_LAYOUT


def parse_measurement_csv(
    text,
    *,
    require_complete=True,
    layout=None,
):
    reader = csv.DictReader(io.StringIO(text))
    required = {
        "section",
        "station_id",
        "pass_id",
        "pass_name",
        "mark_kind",
        "angle_deg",
        "base_x_mm",
        "base_y_mm",
        "nominal_x_mm",
        "nominal_y_mm",
        "measured_x_mm",
        "measured_y_mm",
    }
    if reader.fieldnames is None or not required.issubset(reader.fieldnames):
        missing = sorted(required - set(reader.fieldnames or ()))
        raise ValueError("measurement CSV is missing columns: %s" % ", ".join(missing))
    rows = list(reader)
    layout = _measurement_layout(reader.fieldnames, rows, layout)
    marks = []
    missing_rows = []
    for row_number, row in enumerate(rows, 2):
        measured_x = (row.get("measured_x_mm") or "").strip()
        measured_y = (row.get("measured_y_mm") or "").strip()
        if not measured_x or not measured_y:
            missing_rows.append(
                "%s/%s" % (row.get("station_id", "?"), row.get("pass_id", "?"))
            )
            if require_complete:
                continue
            continue
        try:
            mark = CalibrationMark(
                section=str(row["section"]).strip(),
                station_id=str(row["station_id"]).strip(),
                ring_radius_mm=float(row.get("ring_radius_mm") or "0"),
                station_angle_deg=float(row.get("station_angle_deg") or "0"),
                base_x_mm=float(row["base_x_mm"]),
                base_y_mm=float(row["base_y_mm"]),
                pass_id=str(row["pass_id"]).strip(),
                pass_name=str(row["pass_name"]).strip(),
                mark_kind=str(row["mark_kind"]).strip(),
                angle_deg=float(row["angle_deg"]),
                nominal_x_mm=float(row["nominal_x_mm"]),
                nominal_y_mm=float(row["nominal_y_mm"]),
                measured_x_mm=float(measured_x),
                measured_y_mm=float(measured_y),
            )
        except (TypeError, ValueError) as error:
            raise ValueError("measurement row %d: %s" % (row_number, error)) from error
        if not all(
            math.isfinite(value)
            for value in (
                mark.ring_radius_mm,
                mark.station_angle_deg,
                mark.base_x_mm,
                mark.base_y_mm,
                mark.angle_deg,
                mark.nominal_x_mm,
                mark.nominal_y_mm,
                mark.measured_x_mm,
                mark.measured_y_mm,
            )
        ):
            raise ValueError("measurement row %d contains a non-finite value" % row_number)
        marks.append(mark)
    if require_complete and missing_rows:
        preview = ", ".join(missing_rows[:8])
        if len(missing_rows) > 8:
            preview += ", ..."
        raise ValueError(
            "%d measurement rows are incomplete: %s" % (len(missing_rows), preview)
        )
    if not marks:
        raise ValueError("measurement CSV has no measured rows")
    keys = [(mark.station_id, mark.pass_id) for mark in marks]
    if len(set(keys)) != len(keys):
        raise ValueError("measurement CSV has duplicate station/pass rows")
    expected_marks_by_key = {
        (mark.station_id, mark.pass_id): mark
        for mark in expected_marks(layout)
    }
    expected = set(expected_marks_by_key)
    actual = set(keys)
    missing = expected - actual
    extra = actual - expected
    if require_complete and missing:
        raise ValueError(
            "measurement CSV is missing %d generated station/pass rows" % len(missing)
        )
    if extra:
        raise ValueError("measurement CSV has %d unknown station/pass rows" % len(extra))
    for mark in marks:
        expected_mark = expected_marks_by_key[(mark.station_id, mark.pass_id)]
        if (
            mark.section != expected_mark.section
            or mark.mark_kind != expected_mark.mark_kind
            or abs(mark.angle_deg - expected_mark.angle_deg) > 1e-6
            or math.hypot(
                mark.base_x_mm - expected_mark.base_x_mm,
                mark.base_y_mm - expected_mark.base_y_mm,
            )
            > 1e-6
            or math.hypot(
                mark.nominal_x_mm - expected_mark.nominal_x_mm,
                mark.nominal_y_mm - expected_mark.nominal_y_mm,
            )
            > 1e-6
        ):
            raise ValueError(
                "measurement template geometry changed at %s/%s; regenerate "
                "the CSV from the matching G-code generator"
                % (mark.station_id, mark.pass_id)
            )
    return tuple(marks)


def fit_similarity(fiducials):
    if len(fiducials) < 3:
        raise ValueError("at least three fiducials are required")
    mean_nominal_x = statistics.fmean(mark.nominal_x_mm for mark in fiducials)
    mean_nominal_y = statistics.fmean(mark.nominal_y_mm for mark in fiducials)
    mean_measured_x = statistics.fmean(mark.measured_x_mm for mark in fiducials)
    mean_measured_y = statistics.fmean(mark.measured_y_mm for mark in fiducials)
    denominator = 0.0
    scale_cos = 0.0
    scale_sin = 0.0
    for mark in fiducials:
        px = mark.nominal_x_mm - mean_nominal_x
        py = mark.nominal_y_mm - mean_nominal_y
        qx = mark.measured_x_mm - mean_measured_x
        qy = mark.measured_y_mm - mean_measured_y
        denominator += px * px + py * py
        scale_cos += px * qx + py * qy
        scale_sin += px * qy - py * qx
    if denominator <= 1e-12:
        raise ValueError("fiducial target positions do not span an area")
    a = scale_cos / denominator
    b = scale_sin / denominator
    scale = math.hypot(a, b)
    if not math.isfinite(scale) or not 0.95 <= scale <= 1.05:
        raise ValueError("fiducial scale is implausible: %.6f" % scale)
    rotation_deg = math.degrees(math.atan2(b, a))
    translation_x = mean_measured_x - (a * mean_nominal_x - b * mean_nominal_y)
    translation_y = mean_measured_y - (b * mean_nominal_x + a * mean_nominal_y)
    alignment = SimilarityAlignment(
        scale,
        rotation_deg,
        translation_x,
        translation_y,
        0.0,
        0.0,
    )
    residuals = []
    for mark in fiducials:
        px, py = alignment.forward_point(mark.nominal_x_mm, mark.nominal_y_mm)
        residuals.append(math.hypot(px - mark.measured_x_mm, py - mark.measured_y_mm))
    return SimilarityAlignment(
        scale,
        rotation_deg,
        translation_x,
        translation_y,
        math.sqrt(statistics.fmean(value * value for value in residuals)),
        max(residuals),
    )


def error_summary(errors):
    errors = tuple(errors)
    if not errors:
        raise ValueError("cannot summarize an empty error set")
    magnitudes = sorted(math.hypot(dx, dy) for dx, dy in errors)
    p95_index = min(len(magnitudes) - 1, int(math.ceil(0.95 * len(magnitudes))) - 1)
    return ErrorSummary(
        len(errors),
        math.sqrt(statistics.fmean(dx * dx + dy * dy for dx, dy in errors)),
        magnitudes[p95_index],
        magnitudes[-1],
        statistics.fmean(dx for dx, _dy in errors),
        statistics.fmean(dy for _dx, dy in errors),
    )


def machine_frame_correction(angle_deg, bed_error):
    """Rotate a required bed-frame correction into machine XY."""
    angle = math.radians(float(angle_deg))
    cosine = math.cos(angle)
    sine = math.sin(angle)
    bed_x = -float(bed_error[0])
    bed_y = -float(bed_error[1])
    return (
        bed_x * cosine - bed_y * sine,
        bed_x * sine + bed_y * cosine,
    )


def _summary_dict(summary):
    return {
        "count": summary.count,
        "rms_mm": round(summary.rms_mm, 6),
        "p95_mm": round(summary.p95_mm, 6),
        "max_mm": round(summary.max_mm, 6),
        "mean_x_mm": round(summary.mean_x_mm, 6),
        "mean_y_mm": round(summary.mean_y_mm, 6),
    }


def _normalized_errors(marks, alignment):
    output = []
    for mark in marks:
        bed_x, bed_y = alignment.inverse_point(mark.measured_x_mm, mark.measured_y_mm)
        output.append(
            {
                "mark": mark,
                "error": (
                    bed_x - mark.nominal_x_mm,
                    bed_y - mark.nominal_y_mm,
                ),
            }
        )
    return output


def _build_profile(
    stations,
    normalized_by_key,
    *,
    layout=STANDARD_LAYOUT,
    source,
    coverage_radius_mm=COVERAGE_RADIUS_MM,
):
    layout = calibration_layout(layout)
    reference = {}
    controls = {}
    angled_passes = tuple(
        calibration_pass
        for calibration_pass in layout.pass_specs
        if calibration_pass.angle_deg != 0.0
    )
    angled = {
        calibration_pass.angle_deg: {} for calibration_pass in angled_passes
    }
    for station in stations:
        reference[station.station_id] = normalized_by_key[
            (station.station_id, "reference")
        ]["error"]
        controls[station.station_id] = normalized_by_key[
            (station.station_id, "control")
        ]["error"]
        for angle in angled:
            angled[angle][station.station_id] = normalized_by_key[
                (station.station_id, "angle_%d" % int(angle))
            ]["error"]
    sample_points = ((station.x_mm, station.y_mm) for station in stations)
    sample_points = tuple(sample_points)
    spatial_samples = sample_points
    reference_errors = tuple(reference[station.station_id] for station in stations)

    angle_fields = {}
    lane_by_angle = {
        calibration_pass.angle_deg: (
            calibration_pass.lane_x_mm,
            calibration_pass.lane_y_mm,
        )
        for calibration_pass in angled_passes
    }
    for calibration_pass in angled_passes:
        angle = calibration_pass.angle_deg
        lane_samples = []
        lane_residuals = []
        lane_x_mm, lane_y_mm = lane_by_angle[angle]
        for station in stations:
            raw_error = angled[angle][station.station_id]
            target_x = station.x_mm + lane_x_mm
            target_y = station.y_mm + lane_y_mm
            spatial_error = interpolate_bed_correction(
                spatial_samples,
                reference_errors,
                target_x,
                target_y,
            )
            lane_samples.append((target_x, target_y))
            lane_residuals.append(
                (
                    raw_error[0] - spatial_error[0],
                    raw_error[1] - spatial_error[1],
                )
            )
        angle_fields[angle] = (tuple(lane_samples), tuple(lane_residuals))

    angle_values = []
    sample_grids = []
    correction_grids = []
    for angle in PROFILE_ANGLE_VALUES_DEG:
        corrections = []
        for station in stations:
            error_x, error_y = reference[station.station_id]
            if angle != 0.0:
                lane_samples, lane_residuals = angle_fields[angle]
                residual_x, residual_y = interpolate_bed_correction(
                    lane_samples,
                    lane_residuals,
                    station.x_mm,
                    station.y_mm,
                )
                error_x += residual_x
                error_y += residual_y
            corrections.append(machine_frame_correction(angle, (error_x, error_y)))
        angle_values.append(angle)
        sample_grids.append(sample_points)
        correction_grids.append(tuple(corrections))

    profile = BedCompensationProfile(
        angle_values_deg=tuple(angle_values),
        samples_mm=tuple(sample_grids),
        corrections_mm=tuple(correction_grids),
        coverage_radius_mm=coverage_radius_mm,
        source=source,
    )
    return (
        profile,
        reference,
        controls,
        angled,
        angle_fields,
        spatial_samples,
        reference_errors,
    )


def _pearson(values_a, values_b):
    if len(values_a) != len(values_b) or len(values_a) < 3:
        return None
    mean_a = statistics.fmean(values_a)
    mean_b = statistics.fmean(values_b)
    numerator = sum(
        (a - mean_a) * (b - mean_b) for a, b in zip(values_a, values_b)
    )
    denominator_a = math.sqrt(sum((a - mean_a) ** 2 for a in values_a))
    denominator_b = math.sqrt(sum((b - mean_b) ** 2 for b in values_b))
    if denominator_a <= 1e-12 or denominator_b <= 1e-12:
        return None
    return numerator / (denominator_a * denominator_b)


def parse_bed_mesh_csv(text):
    filtered = "\n".join(
        line
        for line in text.splitlines()
        if not line.lstrip().startswith("#")
    )
    reader = csv.DictReader(io.StringIO(filtered))
    if reader.fieldnames is None or not {"x", "y"}.issubset(reader.fieldnames):
        raise ValueError("bed mesh CSV needs x and y columns")
    height_column = None
    for candidate in ("gap_mm", "height_mm", "z_mm", "height"):
        if candidate in reader.fieldnames:
            height_column = candidate
            break
    if height_column is None:
        raise ValueError("bed mesh CSV needs gap_mm or height_mm")
    points = []
    for row_number, row in enumerate(reader, 2):
        try:
            x_mm = float(row["x"])
            y_mm = float(row["y"])
            height_mm = float(row[height_column])
        except (TypeError, ValueError) as error:
            raise ValueError(
                "bed mesh row %d has a malformed value" % row_number
            ) from error
        if all(math.isfinite(value) for value in (x_mm, y_mm, height_mm)):
            points.append((x_mm, y_mm, height_mm))
    if len(points) < 3:
        raise ValueError("bed mesh needs at least three numeric points")
    return tuple(points)


def _scalar_at_mesh_points(mesh_points, x_mm, y_mm):
    distances = sorted(
        (
            (point_x - x_mm) ** 2 + (point_y - y_mm) ** 2,
            height_mm,
        )
        for point_x, point_y, height_mm in mesh_points
    )
    if distances[0][0] <= 1e-12:
        return distances[0][1]
    selected = distances[: min(8, len(distances))]
    weights = [1.0 / (distance_sq + 1e-6) for distance_sq, _height in selected]
    return sum(
        weight * height_mm
        for weight, (_distance_sq, height_mm) in zip(weights, selected)
    ) / sum(weights)


def _height_correlations(stations, reference, angled, mesh_points):
    heights = [
        _scalar_at_mesh_points(mesh_points, station.x_mm, station.y_mm)
        for station in stations
    ]
    reference_x = [reference[station.station_id][0] for station in stations]
    reference_y = [reference[station.station_id][1] for station in stations]
    reference_magnitude = [
        math.hypot(dx, dy) for dx, dy in zip(reference_x, reference_y)
    ]
    result = {
        "sample_count": len(stations),
        "reference": {
            "error_x_r": _pearson(heights, reference_x),
            "error_y_r": _pearson(heights, reference_y),
            "magnitude_r": _pearson(heights, reference_magnitude),
        },
        "angles": {},
    }
    for angle, errors in angled.items():
        magnitudes = [
            math.hypot(*errors[station.station_id]) for station in stations
        ]
        result["angles"][str(int(angle))] = {
            "magnitude_r": _pearson(heights, magnitudes)
        }
    values = [
        result["reference"]["error_x_r"],
        result["reference"]["error_y_r"],
        result["reference"]["magnitude_r"],
    ]
    values.extend(item["magnitude_r"] for item in result["angles"].values())
    finite = [abs(value) for value in values if value is not None]
    strongest = max(finite) if finite else 0.0
    if strongest >= 0.55:
        result["summary"] = (
            "moderate-to-strong height correlation; height coupling is plausible, "
            "but this mesh includes the paper and cannot separate paper from bed"
        )
    elif strongest >= 0.25:
        result["summary"] = (
            "weak-to-moderate height correlation; height may contribute but does "
            "not explain the whole field"
        )
    else:
        result["summary"] = (
            "little height correlation; the field is more consistent with lateral "
            "bed/pen mapping than with vertical contact height"
        )
    return result


def analyze_measurements(
    measurements_csv,
    *,
    layout=None,
    bed_mesh_csv=None,
    bed_mesh_source="",
    bed_mesh_sha256="",
    source="bed-error-map.csv",
    max_cross_validation_rms_mm=0.35,
    max_cross_validation_error_mm=0.90,
    minimum_improvement_pct=10.0,
    coverage_radius_mm=None,
):
    if coverage_radius_mm is None:
        coverage_radius_mm = COVERAGE_RADIUS_MM
    coverage_radius_mm = float(coverage_radius_mm)
    if (
        not math.isfinite(coverage_radius_mm)
        or coverage_radius_mm <= 0.0
        or coverage_radius_mm > SHEET_DIAMETER_MM / 2.0 + 1e-6
    ):
        raise ValueError(
            "coverage radius must be positive and no larger than the "
            "%.3f mm calibration stock radius" % (SHEET_DIAMETER_MM / 2.0)
        )
    reader = csv.DictReader(io.StringIO(measurements_csv))
    rows = list(reader)
    layout = _measurement_layout(reader.fieldnames, rows, layout)
    marks = parse_measurement_csv(
        measurements_csv,
        require_complete=True,
        layout=layout,
    )
    fiducials = tuple(mark for mark in marks if mark.section == "fiducial")
    if len(fiducials) != 4:
        raise ValueError("the calibration needs all four fiducial measurements")
    alignment = fit_similarity(fiducials)
    normalized = _normalized_errors(marks, alignment)
    normalized_by_key = {
        (item["mark"].station_id, item["mark"].mark_kind): item for item in normalized
    }
    stations = calibration_stations(layout)
    (
        profile,
        reference,
        controls,
        angled,
        angle_fields,
        spatial_samples,
        reference_errors,
    ) = _build_profile(
        stations,
        normalized_by_key,
        layout=layout,
        source=source,
        coverage_radius_mm=coverage_radius_mm,
    )

    raw_errors = [
        item["error"] for item in normalized if item["mark"].section == "station"
    ]
    raw_summary = error_summary(raw_errors)
    reference_summary = error_summary(reference.values())
    control_residuals = []
    for station in stations:
        control_mark = next(
            item["mark"]
            for item in normalized
            if item["mark"].station_id == station.station_id
            and item["mark"].mark_kind == "control"
        )
        spatial_error = interpolate_bed_correction(
            spatial_samples,
            reference_errors,
            control_mark.nominal_x_mm,
            control_mark.nominal_y_mm,
        )
        error = controls[station.station_id]
        control_residuals.append(
            (error[0] - spatial_error[0], error[1] - spatial_error[1])
        )

    angle_summaries = {}
    angle_position_spread = {}
    for angle, field in angle_fields.items():
        lane_samples, lane_residuals = field
        errors = {
            station.station_id: interpolate_bed_correction(
                lane_samples,
                lane_residuals,
                station.x_mm,
                station.y_mm,
            )
            for station in stations
        }
        angle_summaries[str(int(angle))] = error_summary(errors.values())
        mean_x = statistics.fmean(value[0] for value in errors.values())
        mean_y = statistics.fmean(value[1] for value in errors.values())
        deviations = [
            (value[0] - mean_x, value[1] - mean_y) for value in errors.values()
        ]
        angle_position_spread[str(int(angle))] = error_summary(deviations)

    loo_residuals = []
    for held_out in stations:
        subset = tuple(
            station for station in stations if station.station_id != held_out.station_id
        )
        (
            held_profile,
            _ref,
            _ctrl,
            _ang,
            _angle_fields,
            _samples,
            _errors,
        ) = _build_profile(
            subset,
            normalized_by_key,
            layout=layout,
            source=source + " leave-one-out",
            coverage_radius_mm=coverage_radius_mm,
        )
        for item in normalized:
            mark = item["mark"]
            if mark.section != "station" or mark.station_id != held_out.station_id:
                continue
            correction_needed = machine_frame_correction(
                mark.angle_deg, item["error"]
            )
            try:
                predicted = held_profile.correction(
                    mark.angle_deg, mark.nominal_x_mm, mark.nominal_y_mm
                )
            except ValueError:
                continue
            loo_residuals.append(
                (
                    correction_needed[0] - predicted[0],
                    correction_needed[1] - predicted[1],
                )
            )
    loo_summary = error_summary(loo_residuals)
    improvement_pct = (
        max(0.0, 100.0 * (1.0 - loo_summary.rms_mm / raw_summary.rms_mm))
        if raw_summary.rms_mm > 0.0
        else 0.0
    )
    accepted = (
        loo_summary.rms_mm <= max_cross_validation_rms_mm
        and loo_summary.max_mm <= max_cross_validation_error_mm
        and improvement_pct >= minimum_improvement_pct
    )
    height_data = None
    if bed_mesh_csv:
        mesh_points = parse_bed_mesh_csv(bed_mesh_csv)
        height_data = _height_correlations(
            stations, reference, angled, mesh_points
        )
        height_data["source"] = bed_mesh_source
        height_data["sha256"] = bed_mesh_sha256 or hashlib.sha256(
            bed_mesh_csv.encode("utf-8")
        ).hexdigest()

    angle_weighted_rms = statistics.fmean(
        summary.rms_mm for summary in angle_summaries.values()
    )
    if height_data and abs(height_data["reference"]["magnitude_r"] or 0.0) >= 0.55:
        diagnosis = (
            "height-coupled spatial field; inspect bed/paper support and pen-carriage "
            "height before accepting an XY software map"
        )
    elif angle_weighted_rms >= 0.30:
        diagnosis = (
            "angle-dependent error remains after removing the A=0 spatial field; "
            "rotation/runout/carriage coupling remains a credible source"
        )
    else:
        diagnosis = (
            "the A=0 spatial field dominates; height correlation is weak or absent, "
            "so lateral bed/pen mapping is the stronger candidate"
        )

    report = {
        "schema": "theta-bed-calibration-report-v1",
        "source": source,
        "layout": {
            "id": layout.layout_id,
            "name": layout.display_name,
            "test_diameter_mm": layout.test_diameter_mm,
            "sheet_diameter_mm": SHEET_DIAMETER_MM,
            "station_count": len(stations),
            "ring_count": len(layout.ring_specs),
            "mark_arm_mm": layout.mark_arm_mm,
            "lane_offset_mm": layout.lane_offset_mm,
            "label_height_mm": layout.label_height_mm,
            "angle_values_deg": list(profile.angle_values_deg),
            "fiducial_count": len(fiducials),
            "coverage_radius_mm": round(float(coverage_radius_mm), 6),
        },
        "alignment": {
            "scale": alignment.scale,
            "rotation_deg": alignment.rotation_deg,
            "translation_x_mm": alignment.translation_x_mm,
            "translation_y_mm": alignment.translation_y_mm,
            "fiducial_rms_mm": alignment.rms_residual_mm,
            "fiducial_max_mm": alignment.max_residual_mm,
        },
        "raw_error": _summary_dict(raw_summary),
        "a0_spatial_error": _summary_dict(reference_summary),
        "a0_control_residual": _summary_dict(error_summary(control_residuals)),
        "angles": {
            angle: _summary_dict(summary)
            for angle, summary in angle_summaries.items()
        },
        "angle_position_spread": {
            angle: _summary_dict(summary)
            for angle, summary in angle_position_spread.items()
        },
        "leave_one_out": {
            **_summary_dict(loo_summary),
            "improvement_pct": improvement_pct,
            "max_rms_gate_mm": max_cross_validation_rms_mm,
            "max_error_gate_mm": max_cross_validation_error_mm,
            "minimum_improvement_pct": minimum_improvement_pct,
            "accepted": accepted,
        },
        "bed_mesh_correlation": height_data,
        "diagnosis": diagnosis,
        "profile": {
            "fingerprint": profile.fingerprint,
            "coverage_radius_mm": profile.coverage_radius_mm,
            "max_correction_mm": profile.max_correction_mm,
        },
    }
    return profile, report, accepted


def compare_measurements(
    baseline_csv,
    verification_csv,
    *,
    layout=None,
    baseline_source="baseline.csv",
    verification_source="verification.csv",
    max_rms_mm=0.35,
    max_error_mm=0.90,
    minimum_improvement_pct=30.0,
):
    """Compare independently normalized measurements from two printed sheets."""
    baseline_reader = csv.DictReader(io.StringIO(baseline_csv))
    baseline_rows = list(baseline_reader)
    baseline_layout = _measurement_layout(
        baseline_reader.fieldnames,
        baseline_rows,
        layout,
    )
    verification_reader = csv.DictReader(io.StringIO(verification_csv))
    verification_rows = list(verification_reader)
    verification_layout = _measurement_layout(
        verification_reader.fieldnames,
        verification_rows,
        layout,
    )
    if baseline_layout.layout_id != verification_layout.layout_id:
        raise ValueError(
            "baseline and verification measurement layouts differ: %s vs %s"
            % (baseline_layout.layout_id, verification_layout.layout_id)
        )
    baseline_marks = parse_measurement_csv(
        baseline_csv,
        require_complete=True,
        layout=baseline_layout,
    )
    verification_marks = parse_measurement_csv(
        verification_csv,
        require_complete=True,
        layout=verification_layout,
    )
    baseline_alignment = fit_similarity(
        tuple(mark for mark in baseline_marks if mark.section == "fiducial")
    )
    verification_alignment = fit_similarity(
        tuple(mark for mark in verification_marks if mark.section == "fiducial")
    )
    baseline = {
        (item["mark"].station_id, item["mark"].pass_id): item
        for item in _normalized_errors(baseline_marks, baseline_alignment)
        if item["mark"].section == "station"
    }
    verification = {
        (item["mark"].station_id, item["mark"].pass_id): item
        for item in _normalized_errors(verification_marks, verification_alignment)
        if item["mark"].section == "station"
    }
    all_errors_before = [item["error"] for item in baseline.values()]
    all_errors_after = [item["error"] for item in verification.values()]
    before_summary = error_summary(all_errors_before)
    after_summary = error_summary(all_errors_after)
    improvement_pct = (
        max(0.0, 100.0 * (1.0 - after_summary.rms_mm / before_summary.rms_mm))
        if before_summary.rms_mm > 0.0
        else 0.0
    )

    def grouped_errors(items):
        output = {}
        kinds = tuple(
            dict.fromkeys(
                item["mark"].mark_kind for item in items.values()
            )
        )
        for kind in kinds:
            values = [
                item["error"]
                for item in items.values()
                if item["mark"].mark_kind == kind
            ]
            output[kind] = error_summary(values)
        return output

    before_groups = grouped_errors(baseline)
    after_groups = grouped_errors(verification)
    station_comparison = []
    for key in sorted(baseline):
        before_mark = baseline[key]["mark"]
        before_error = baseline[key]["error"]
        after_error = verification[key]["error"]
        previous_magnitude = math.hypot(*before_error)
        current_magnitude = math.hypot(*after_error)
        station_comparison.append(
            {
                "station_id": before_mark.station_id,
                "pass_name": before_mark.pass_name,
                "angle_deg": before_mark.angle_deg,
                "before_x_mm": before_error[0],
                "before_y_mm": before_error[1],
                "after_x_mm": after_error[0],
                "after_y_mm": after_error[1],
                "before_magnitude_mm": previous_magnitude,
                "after_magnitude_mm": current_magnitude,
                "improved": current_magnitude < previous_magnitude,
            }
        )
    per_angle_ok = all(
        after_groups[kind].rms_mm <= before_groups[kind].rms_mm + 0.05
        for kind in before_groups
        if kind.startswith("angle_")
    )
    accepted = (
        after_summary.rms_mm <= max_rms_mm
        and after_summary.max_mm <= max_error_mm
        and improvement_pct >= minimum_improvement_pct
        and per_angle_ok
    )
    return {
        "schema": "theta-bed-verification-comparison-v1",
        "baseline_source": baseline_source,
        "verification_source": verification_source,
        "alignment": {
            "baseline": {
                "scale": baseline_alignment.scale,
                "rotation_deg": baseline_alignment.rotation_deg,
            },
            "verification": {
                "scale": verification_alignment.scale,
                "rotation_deg": verification_alignment.rotation_deg,
            },
        },
        "before": _summary_dict(before_summary),
        "after": _summary_dict(after_summary),
        "rms_improvement_pct": improvement_pct,
        "groups": {
            kind: {
                "before": _summary_dict(before_groups[kind]),
                "after": _summary_dict(after_groups[kind]),
            }
            for kind in before_groups
        },
        "every_angle_stage_not_worse": per_angle_ok,
        "acceptance": {
            "accepted": accepted,
            "max_rms_mm": max_rms_mm,
            "max_error_mm": max_error_mm,
            "minimum_improvement_pct": minimum_improvement_pct,
        },
        "stations": station_comparison,
    }
