"""Optional machine-space compensation for repeatable bed irregularities.

The profile is a periodic lookup over bed angle and registered G54 bed XY.
Values are additive corrections to the nominal machine X/Y coordinate:

    machine = R(theta) * bed_point + correction(theta, bed_point)

Stored samples are machine-XY corrections. Between measured bed angles, they
are first rotated back into bed coordinates, linearly interpolated there, and
then rotated into machine coordinates at the requested angle. Blending the
already-rotated machine vectors would shorten or misdirect the correction.

P100 remains the owner of the registration centre. This profile corrects the
residual shape/pose error left after registration. Spatial samples are stored
as scattered bed points so a round sheet does not need fictitious measurements
in the four square-grid corners.

CMYK Wave screens can request a row-locked projection instead. It evaluates
the same complete profile, resolves correction vectors in the ink's screen
frame, and retains only displacement common to every parallel row. Raw
row-normal variation is discarded because it necessarily changes row pitch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
from typing import Sequence


SCHEMA = "theta-bed-compensation-v2"
MAX_ABS_CORRECTION_MM = 5.0
SPATIAL_NEIGHBOURS = 8
FAST_COMPENSATION_PROBE_SAMPLES = 4
FAST_COMPENSATION_PROBE_TOLERANCE_FRACTION = 0.25
ROW_LOCK_ALONG_SAMPLES = 129
ROW_LOCK_ACROSS_SAMPLES = 33


def _finite(value, name):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("%s must be finite" % name)
    return value


def _periodic_angles(values: Sequence[float]) -> tuple[float, ...]:
    parsed = tuple(sorted(_finite(value, "angle") % 360.0 for value in values))
    if not parsed:
        raise ValueError("angle grid needs at least one sample")
    if len(set(round(value, 9) for value in parsed)) != len(parsed):
        raise ValueError("angle samples must be unique modulo 360 degrees")
    return parsed


def _spatial_slice(profile, angle_index: int):
    return profile.samples_mm[angle_index], profile.corrections_mm[angle_index]


def _solve_three(matrix, rhs):
    a, b, c = matrix[0]
    d, e, f = matrix[1]
    g, h, i = matrix[2]
    determinant = (
        a * (e * i - f * h)
        - b * (d * i - f * g)
        + c * (d * h - e * g)
    )
    if abs(determinant) <= 1e-12:
        return None
    inverse = (
        (e * i - f * h, c * h - b * i, b * f - c * e),
        (f * g - d * i, a * i - c * g, c * d - a * f),
        (d * h - e * g, b * g - a * h, a * e - b * d),
    )
    return tuple(
        sum(inverse[row][column] * rhs[column] for column in range(3))
        / determinant
        for row in range(3)
    )


def interpolate_bed_correction(samples, corrections, x_mm, y_mm):
    """Local affine interpolation over a measured bed-space correction field."""
    if not samples:
        raise ValueError("bed compensation has no spatial samples")
    if len(samples) != len(corrections):
        raise ValueError("bed compensation sample and correction counts disagree")
    x_mm = _finite(x_mm, "bed X")
    y_mm = _finite(y_mm, "bed Y")
    if len(samples) == 1:
        return corrections[0]
    distances = []
    for index, (sx, sy) in enumerate(samples):
        dx = x_mm - sx
        dy = y_mm - sy
        distance_sq = dx * dx + dy * dy
        if distance_sq <= 1e-12:
            return corrections[index]
        distances.append((distance_sq, index))
    distances.sort()
    selected = distances[: min(SPATIAL_NEIGHBOURS, len(distances))]
    # A local affine fit reproduces smooth bed-scale and shear terms, unlike
    # plain inverse distance. Distance weighting keeps nearby samples dominant.
    matrix = [[0.0] * 3 for _ in range(3)]
    rhs_x = [0.0] * 3
    rhs_y = [0.0] * 3
    for distance_sq, index in selected:
        sx, sy = samples[index]
        dx = sx - x_mm
        dy = sy - y_mm
        basis = (1.0, dx, dy)
        weight = 1.0 / (distance_sq + 1e-6)
        for row in range(3):
            for column in range(3):
                matrix[row][column] += weight * basis[row] * basis[column]
            rhs_x[row] += weight * basis[row] * corrections[index][0]
            rhs_y[row] += weight * basis[row] * corrections[index][1]
    solution_x = _solve_three(matrix, rhs_x)
    solution_y = _solve_three(matrix, rhs_y)
    if solution_x is not None and solution_y is not None:
        return solution_x[0], solution_y[0]

    # Degenerate local geometry falls back to normalized inverse distance.
    weight_sum = 0.0
    correction_x = 0.0
    correction_y = 0.0
    for distance_sq, index in selected:
        weight = 1.0 / (distance_sq + 1e-6)
        correction_x += corrections[index][0] * weight
        correction_y += corrections[index][1] * weight
        weight_sum += weight
    return correction_x / weight_sum, correction_y / weight_sum


@dataclass(frozen=True)
class BedCompensationProfile:
    angle_values_deg: tuple[float, ...]
    samples_mm: tuple[tuple[tuple[float, float], ...], ...]
    corrections_mm: tuple[tuple[tuple[float, float], ...], ...]
    coverage_radius_mm: float
    source: str = ""
    _bed_corrections_mm: tuple[tuple[tuple[float, float], ...], ...] = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self):
        object.__setattr__(
            self, "angle_values_deg", _periodic_angles(self.angle_values_deg)
        )
        coverage = _finite(self.coverage_radius_mm, "coverage radius")
        if coverage <= 0.0:
            raise ValueError("coverage radius must be greater than zero")
        object.__setattr__(self, "coverage_radius_mm", coverage)
        angle_count = len(self.angle_values_deg)
        if len(self.samples_mm) != angle_count:
            raise ValueError("sample angle count does not match the angle grid")
        if len(self.corrections_mm) != angle_count:
            raise ValueError("correction angle count does not match the angle grid")
        normalized_samples = []
        normalized_corrections = []
        for angle_index, (sample_grid, correction_grid) in enumerate(
            zip(self.samples_mm, self.corrections_mm)
        ):
            if len(sample_grid) != len(correction_grid):
                raise ValueError(
                    "sample and correction counts disagree at angle index %d"
                    % angle_index
                )
            if len(sample_grid) < 3:
                raise ValueError("each angle grid needs at least three bed samples")
            samples = []
            seen = set()
            for pair in sample_grid:
                sx, sy = (_finite(value, "bed sample") for value in pair)
                key = (round(sx, 6), round(sy, 6))
                if key in seen:
                    raise ValueError("bed samples must be unique within an angle")
                if math.hypot(sx, sy) > coverage + 1e-6:
                    raise ValueError("bed sample lies outside the coverage radius")
                seen.add(key)
                samples.append((sx, sy))
            corrections = []
            for pair in correction_grid:
                dx, dy = (_finite(value, "correction") for value in pair)
                if math.hypot(dx, dy) > MAX_ABS_CORRECTION_MM:
                    raise ValueError(
                        "correction exceeds the %.1f mm safety bound"
                        % MAX_ABS_CORRECTION_MM
                    )
                corrections.append((dx, dy))
            normalized_samples.append(tuple(samples))
            normalized_corrections.append(tuple(corrections))
        object.__setattr__(self, "samples_mm", tuple(normalized_samples))
        object.__setattr__(self, "corrections_mm", tuple(normalized_corrections))
        bed_corrections = []
        for angle, corrections in zip(
            self.angle_values_deg,
            normalized_corrections,
        ):
            radians = math.radians(angle)
            cosine = math.cos(radians)
            sine = math.sin(radians)
            bed_corrections.append(
                tuple(
                    (
                        cosine * correction_x + sine * correction_y,
                        -sine * correction_x + cosine * correction_y,
                    )
                    for correction_x, correction_y in corrections
                )
            )
        object.__setattr__(self, "_bed_corrections_mm", tuple(bed_corrections))

    @property
    def identity(self) -> bool:
        return all(
            abs(dx) <= 1e-12 and abs(dy) <= 1e-12
            for angle_grid in self.corrections_mm
            for dx, dy in angle_grid
        )

    def _spatial_bed_correction(
        self,
        angle_index: int,
        x_mm: float,
        y_mm: float,
    ):
        samples = self.samples_mm[angle_index]
        corrections = self._bed_corrections_mm[angle_index]
        return interpolate_bed_correction(samples, corrections, x_mm, y_mm)

    def _angle_position(self, angle_deg: float) -> tuple[int, int, float]:
        angles = self.angle_values_deg
        if len(angles) == 1:
            return 0, 0, 0.0
        angle = _finite(angle_deg, "bed angle") % 360.0
        for index in range(len(angles) - 1):
            if angle <= angles[index + 1]:
                return (
                    index,
                    index + 1,
                    (angle - angles[index])
                    / (angles[index + 1] - angles[index]),
                )
        span = angles[0] + 360.0 - angles[-1]
        wrapped_angle = angle + 360.0 if angle < angles[0] else angle
        return len(angles) - 1, 0, (wrapped_angle - angles[-1]) / span

    def correction(
        self, angle_deg: float, x_mm: float, y_mm: float
    ) -> tuple[float, float]:
        """Return the additive machine-XY correction for one bed point."""
        if math.hypot(float(x_mm), float(y_mm)) > self.coverage_radius_mm + 1e-6:
            raise ValueError(
                "bed point lies outside the %.3f mm measured compensation radius"
                % self.coverage_radius_mm
            )
        i0, i1, t = self._angle_position(angle_deg)
        bed_x0, bed_y0 = self._spatial_bed_correction(i0, x_mm, y_mm)
        if i0 == i1:
            bed_x = bed_x0
            bed_y = bed_y0
        else:
            bed_x1, bed_y1 = self._spatial_bed_correction(i1, x_mm, y_mm)
            bed_x = bed_x0 * (1.0 - t) + bed_x1 * t
            bed_y = bed_y0 * (1.0 - t) + bed_y1 * t
        angle = math.radians(angle_deg)
        cosine = math.cos(angle)
        sine = math.sin(angle)
        return (
            bed_x * cosine - bed_y * sine,
            bed_x * sine + bed_y * cosine,
        )

    @property
    def max_correction_mm(self) -> float:
        return max(
            math.hypot(dx, dy)
            for angle_grid in self.corrections_mm
            for dx, dy in angle_grid
        )

    def as_dict(self) -> dict:
        return {
            "schema": SCHEMA,
            "units": "mm",
            "source": self.source,
            "coverage_radius_mm": self.coverage_radius_mm,
            "angle_values_deg": list(self.angle_values_deg),
            "samples_mm": [
                [[x_mm, y_mm] for x_mm, y_mm in sample_grid]
                for sample_grid in self.samples_mm
            ],
            "corrections_mm": [
                [[dx, dy] for dx, dy in correction_grid]
                for correction_grid in self.corrections_mm
            ],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.as_dict(), indent=indent, sort_keys=True) + "\n"

    @classmethod
    def from_dict(cls, data: dict) -> "BedCompensationProfile":
        if not isinstance(data, dict) or data.get("schema") != SCHEMA:
            raise ValueError("bed compensation profile has an unsupported schema")
        try:
            return cls(
                angle_values_deg=tuple(data["angle_values_deg"]),
                samples_mm=tuple(
                    tuple(tuple(pair) for pair in sample_grid)
                    for sample_grid in data["samples_mm"]
                ),
                corrections_mm=tuple(
                    tuple(tuple(pair) for pair in correction_grid)
                    for correction_grid in data["corrections_mm"]
                ),
                coverage_radius_mm=data["coverage_radius_mm"],
                source=str(data.get("source", "")),
            )
        except KeyError as error:
            raise ValueError(
                "bed compensation profile is missing %s" % error.args[0]
            ) from error

    @classmethod
    def from_json(cls, text: str) -> "BedCompensationProfile":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as error:
            raise ValueError("bed compensation profile is not valid JSON") from error
        return cls.from_dict(data)

    @property
    def fingerprint(self) -> str:
        payload = json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


@dataclass(frozen=True)
class RowLockedBedCompensation:
    """A full profile projected onto displacement common to all parallel rows.

    The measured correction is resolved in a screen frame. At each
    along-row coordinate it is averaged across the perpendicular coordinate,
    removing the only component that can change row-to-row pitch under the
    equidistant-lattice contract. The resulting bed-frame displacement is
    rotated into machine coordinates at the requested bed angle.
    """

    profile: BedCompensationProfile
    screen_angle_deg: float
    angle_values_deg: tuple[float, ...]
    row_coordinates_mm: tuple[float, ...]
    across_samples: int
    corrections_bed_mm: tuple[tuple[tuple[float, float], ...], ...]

    @classmethod
    def from_profile(
        cls,
        profile: BedCompensationProfile,
        screen_angle_deg: float,
        along_samples: int = ROW_LOCK_ALONG_SAMPLES,
        across_samples: int = ROW_LOCK_ACROSS_SAMPLES,
        bed_angle_deg: float | None = None,
    ) -> "RowLockedBedCompensation":
        screen_angle = _finite(screen_angle_deg, "Wave screen angle") % 180.0
        along_samples = max(3, int(along_samples))
        across_samples = max(2, int(across_samples))
        screen_radians = math.radians(-screen_angle)
        cosine = math.cos(screen_radians)
        sine = math.sin(screen_radians)
        radius = profile.coverage_radius_mm
        angle_values = (
            (_finite(bed_angle_deg, "fixed bed angle") % 360.0,)
            if bed_angle_deg is not None
            else profile.angle_values_deg
        )
        row_coordinates = tuple(
            -radius + 2.0 * radius * index / (along_samples - 1)
            for index in range(along_samples)
        )
        projected_angles = []
        for angle in angle_values:
            angle_radians = math.radians(angle)
            angle_cosine = math.cos(angle_radians)
            angle_sine = math.sin(angle_radians)
            row = []
            for along in row_coordinates:
                half_width = math.sqrt(
                    max(0.0, radius * radius - along * along)
                )
                bed_x = 0.0
                bed_y = 0.0
                for index in range(across_samples):
                    fraction = index / (across_samples - 1)
                    across = -half_width + 2.0 * half_width * fraction
                    sample_x = along * cosine - across * sine
                    sample_y = along * sine + across * cosine
                    correction_x, correction_y = profile.correction(
                        angle, sample_x, sample_y
                    )
                    bed_x += (
                        angle_cosine * correction_x
                        + angle_sine * correction_y
                    )
                    bed_y += (
                        -angle_sine * correction_x
                        + angle_cosine * correction_y
                    )
                bed_x /= across_samples
                bed_y /= across_samples
                row.append(
                    (
                        bed_x * cosine + bed_y * sine,
                        -bed_x * sine + bed_y * cosine,
                    )
                )
            projected_angles.append(tuple(row))
        return cls(
            profile=profile,
            screen_angle_deg=screen_angle,
            angle_values_deg=angle_values,
            row_coordinates_mm=row_coordinates,
            across_samples=across_samples,
            corrections_bed_mm=tuple(projected_angles),
        )

    @property
    def coverage_radius_mm(self) -> float:
        return self.profile.coverage_radius_mm

    @property
    def source(self) -> str:
        return self.profile.source

    @property
    def row_locked(self) -> bool:
        return True

    @property
    def full_profile_fingerprint(self) -> str:
        return self.profile.fingerprint

    @property
    def full_max_correction_mm(self) -> float:
        return self.profile.max_correction_mm

    @property
    def identity(self) -> bool:
        return all(
            abs(dx) <= 1e-12 and abs(dy) <= 1e-12
            for angle_grid in self.corrections_bed_mm
            for dx, dy in angle_grid
        )

    @property
    def max_correction_mm(self) -> float:
        return max(
            math.hypot(dx, dy)
            for angle_grid in self.corrections_bed_mm
            for dx, dy in angle_grid
        )

    @property
    def fingerprint(self) -> str:
        payload = "%s|row-lock|%.9f|%s|%d|%d" % (
            self.full_profile_fingerprint,
            self.screen_angle_deg,
            ",".join("%.9f" % value for value in self.angle_values_deg),
            len(self.row_coordinates_mm),
            self.across_samples,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]

    def _sample(self, angle_index: int, along_mm: float):
        coordinates = self.row_coordinates_mm
        if along_mm <= coordinates[0]:
            return self.corrections_bed_mm[angle_index][0]
        if along_mm >= coordinates[-1]:
            return self.corrections_bed_mm[angle_index][-1]
        position = (
            (along_mm - coordinates[0])
            / (coordinates[-1] - coordinates[0])
            * (len(coordinates) - 1)
        )
        lower = int(position)
        fraction = position - lower
        correction_0 = self.corrections_bed_mm[angle_index][lower]
        correction_1 = self.corrections_bed_mm[angle_index][lower + 1]
        return (
            correction_0[0] * (1.0 - fraction) + correction_1[0] * fraction,
            correction_0[1] * (1.0 - fraction) + correction_1[1] * fraction,
        )

    def _angle_position(self, angle_deg: float) -> tuple[int, int, float]:
        angles = self.angle_values_deg
        if len(angles) == 1:
            return 0, 0, 0.0
        angle = _finite(angle_deg, "bed angle") % 360.0
        for index in range(len(angles) - 1):
            if angle <= angles[index + 1]:
                return (
                    index,
                    index + 1,
                    (angle - angles[index])
                    / (angles[index + 1] - angles[index]),
                )
        span = angles[0] + 360.0 - angles[-1]
        wrapped_angle = angle + 360.0 if angle < angles[0] else angle
        return len(angles) - 1, 0, (wrapped_angle - angles[-1]) / span

    def correction(
        self, angle_deg: float, x_mm: float, y_mm: float
    ) -> tuple[float, float]:
        if math.hypot(float(x_mm), float(y_mm)) > self.coverage_radius_mm + 1e-6:
            raise ValueError(
                "bed point lies outside the %.3f mm measured compensation radius"
                % self.coverage_radius_mm
            )
        screen_radians = math.radians(-self.screen_angle_deg)
        screen_cosine = math.cos(screen_radians)
        screen_sine = math.sin(screen_radians)
        along = x_mm * screen_cosine + y_mm * screen_sine
        i0, i1, fraction = self._angle_position(angle_deg)
        correction_0 = self._sample(i0, along)
        if i0 == i1:
            bed_x, bed_y = correction_0
        else:
            correction_1 = self._sample(i1, along)
            bed_x = correction_0[0] * (1.0 - fraction) + correction_1[0] * fraction
            bed_y = correction_0[1] * (1.0 - fraction) + correction_1[1] * fraction
        angle = math.radians(angle_deg)
        cosine = math.cos(angle)
        sine = math.sin(angle)
        return (
            bed_x * cosine - bed_y * sine,
            bed_x * sine + bed_y * cosine,
        )


def row_locked_bed_compensation(
    profile: BedCompensationProfile | None,
    screen_angle_deg: float,
    along_samples: int = ROW_LOCK_ALONG_SAMPLES,
    across_samples: int = ROW_LOCK_ACROSS_SAMPLES,
    bed_angle_deg: float | None = None,
):
    """Project an optional profile onto row-common displacement."""
    if profile is None or profile.identity:
        return profile
    return RowLockedBedCompensation.from_profile(
        profile,
        screen_angle_deg,
        along_samples=along_samples,
        across_samples=across_samples,
        bed_angle_deg=bed_angle_deg,
    )


def load_bed_compensation(path_value: str | None):
    """Load an optional profile path; blank means no correction."""
    path_text = str(path_value or "").strip()
    if not path_text:
        return None
    path = Path(path_text)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError("cannot read bed compensation profile: %s" % error) from error
    return BedCompensationProfile.from_json(text)


def compensated_machine_point(
    point: tuple[float, float],
    angle_deg: float,
    center: tuple[float, float],
    profile: BedCompensationProfile | RowLockedBedCompensation | None,
) -> tuple[float, float]:
    angle = math.radians(angle_deg)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    dx = point[0] - center[0]
    dy = point[1] - center[1]
    machine = (
        center[0] + dx * cos_a - dy * sin_a,
        center[1] + dx * sin_a + dy * cos_a,
    )
    if profile is None or profile.identity:
        return machine
    correction = profile.correction(angle_deg, point[0], point[1])
    return machine[0] + correction[0], machine[1] + correction[1]


def _compensation_probe_worst(
    start,
    end,
    start_theta,
    end_theta,
    center,
    profile,
    machine_start,
    machine_end,
    chord,
    samples,
):
    worst = 0.0
    chord_x = machine_end[0] - machine_start[0]
    chord_y = machine_end[1] - machine_start[1]
    for index in range(1, samples):
        t = index / samples
        point = (
            start[0] + t * (end[0] - start[0]),
            start[1] + t * (end[1] - start[1]),
        )
        theta = start_theta + t * (end_theta - start_theta)
        actual = compensated_machine_point(point, theta, center, profile)
        expected_x = machine_start[0] + t * chord_x
        expected_y = machine_start[1] + t * chord_y
        deviation = abs(
            (actual[0] - expected_x) * chord_y
            - (actual[1] - expected_y) * chord_x
        ) / chord
        worst = max(worst, deviation)
    return worst


def compensation_step_count(
    start,
    end,
    start_theta,
    end_theta,
    center,
    profile,
    tolerance,
    samples=16,
    adaptive=True,
) -> int:
    """Extra subdivision needed for a varying machine-space correction.

    A few coarse probes can establish a conservative flatness margin for the
    requested tolerance. Only uncertain segments pay for the full sample grid;
    sharp or varying fields therefore keep the previous behavior.
    """
    if profile is None or profile.identity:
        return 1
    tolerance = max(float(tolerance), 1e-6)
    ma = compensated_machine_point(start, start_theta, center, profile)
    mb = compensated_machine_point(end, end_theta, center, profile)
    chord_x = mb[0] - ma[0]
    chord_y = mb[1] - ma[1]
    chord = math.hypot(chord_x, chord_y)
    if chord <= 1e-9:
        return 1
    probe_samples = int(samples)
    if probe_samples <= 1:
        return 1
    if adaptive and probe_samples > FAST_COMPENSATION_PROBE_SAMPLES:
        quick_worst = _compensation_probe_worst(
            start,
            end,
            start_theta,
            end_theta,
            center,
            profile,
            ma,
            mb,
            chord,
            FAST_COMPENSATION_PROBE_SAMPLES,
        )
        if (
            quick_worst
            <= tolerance * FAST_COMPENSATION_PROBE_TOLERANCE_FRACTION
        ):
            return 1
    worst = _compensation_probe_worst(
        start,
        end,
        start_theta,
        end_theta,
        center,
        profile,
        ma,
        mb,
        chord,
        probe_samples,
    )
    return max(1, min(600, int(math.ceil(worst / tolerance))))
