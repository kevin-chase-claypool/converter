"""Shared bed-angle planning for equidistant rotating-bed Wave rows."""

import numpy as np

from .geometry import WaveTrail
# Below this ink coverage a mark is dropped so paper stays clean.
INK_FLOOR = 0.06
# Preserve broad vertical image tone in wave height, but average over enough
# rows that row-frequency detail cannot make neighbouring curves jitter.
WAVE_DEPTH_ROW_WINDOW = 7
# Keep paper texture and sharp image detail from modulating the legacy
# fixed-baseline depth field as a second waveform. ``waves_fidelity`` bypasses
# this smoother for amplitude and uses immediate adjacent contrast instead.
WAVE_DEPTH_ALONG_SMOOTHING_PITCHES = 1.5
# Use a smoothed coverage field to decide where a Wave row exists. Raw
# per-pixel channel coverage can cross INK_FLOOR repeatedly inside one dark
# area, chopping the carrier into many short wavelets that read as nested
# waveforms in a zoomed preview.
WAVE_COVERAGE_ALONG_SMOOTHING_PITCHES = 2.5
WAVE_COVERAGE_ROW_WINDOW = 3
# A row may not depart from its neighbour by more than this fraction of the
# nominal pitch. The resulting gap remains between 88% and 112% of pitch,
# keeping the intended depth variation without crossings or runaway gaps.
WAVE_MAX_ADJACENT_GAP_FRACTION = 0.12
# The second clearance check measures the actual shortest distance between
# emitted row segments, not only their separation at matching sample columns.
# Keep at least this much bare paper between the nominal pen edges.
WAVE_MIN_EDGE_GAP_MM = 0.25
WAVE_CLEARANCE_SEARCH_STEPS = 7
# Smoothly vary the shared Wave carrier frequency across the image. The phase
# remains common to every row, so this breaks coherent crest/trough columns
# without changing the perpendicular distance between row baselines.
WAVE_FREQUENCY_VARIATION = 0.18
# The fixed-baseline mode keeps each row's own phase and lets local scene
# depth vary its winding rate by up to this fraction. Baseline spacing remains
# independent of that waveform choice.
WAVE_FIXED_FREQUENCY_TONE_GAIN = 0.32
DEFAULT_WAVE_PERIOD_PITCHES = 2.0
DEFAULT_WAVE_PERIOD_VARIATION = 0.35
DEFAULT_WAVE_DEPTH_INTENSITY = 1.0
WAVE_CLEARANCE_SAFETY_MARGIN_MM = 0.02
WAVE_ANALYTIC_CLEARANCE_MARGIN_MM = 0.001
WAVE_FIDELITY_CLEARANCE_ENVELOPE_MARGIN_MM = 0.012
WAVE_NESTED_PITCH_SAFETY_FACTOR = 1.05
WAVE_DEPTH_INTENSITY_HEADROOM = 0.02
# A rasterized stroke exposes less than its nominal width/pitch area because
# only the stroke body covers a pixel. Compensate for that sampling floor so
# the row-selection probability still maps light coverage below the continuous
# line floor instead of systematically under-inking high-coverage channels.
WAVE_FIDELITY_LINE_COVERAGE_SCALE = 0.88
# Fidelity density decisions use coarse 2-D cells rather than one probability
# per whole row. The size is expressed in row pitches, then clamped to a
# paper-space useful range. A complete cell is at least as long as the normal
# minimum Wave run, so the density gate cannot create per-pixel dashes.
WAVE_FIDELITY_CELL_PITCHES = 1.5
WAVE_FIDELITY_MIN_CELL_MM = 1.5
WAVE_FIDELITY_MAX_CELL_MM = 3.0
WAVE_FIDELITY_CELL_SMOOTHING_CELLS = 8
WAVE_FIDELITY_BRIDGE_CELLS = 1
WAVE_FIDELITY_BRIDGE_MIN_COVERAGE = 0.65
# Adjacent-pixel tone differences are usually much smaller than full black to
# white. This gain makes a moderate image edge visually decisive without
# introducing a nonzero amplitude floor: uniform tone remains a straight line.
WAVE_FIDELITY_CONTRAST_GAIN = 4.0
WAVE_FIDELITY_CONTRAST_EDGE_THRESHOLD = 0.025
# Fixed-baseline crest height as a fraction of the carrier wavelength. A
# quarter wavelength at full tone is clearly wavy; the old constant half-pitch
# amplitude became near-invisible once operators lengthened the Wave period.
WAVE_AMPLITUDE_FRACTION = 0.25
def fixed_wave_minimum_pitch_mm(
    clearance_mm,
    **_options,
):
    """Minimum effective pitch for nested fixed-baseline Wave rows.

    The clearance margin alone only guarantees that rows can be built; the
    ``1.05`` nesting factor additionally reserves a minimum step between
    adjacent amplitudes so the carrier is not flattened to invisibility when
    the pitch approaches the pen envelope.
    """
    clearance = max(0.0, float(clearance_mm))
    return (
        clearance + WAVE_CLEARANCE_SAFETY_MARGIN_MM
    ) * WAVE_NESTED_PITCH_SAFETY_FACTOR
def _local_frame(bounds, angle_deg):
    """Rotated bounding box of a rectangle plus the local->world basis."""
    left, top, right, bottom = (float(value) for value in bounds)
    angle = math.radians(float(angle_deg))
    ca, sa = math.cos(angle), math.sin(angle)
    cs, sn = math.cos(-angle), math.sin(-angle)
    corners = [(left, top), (right, top), (right, bottom), (left, bottom)]
    rotated = [(x * cs - y * sn, x * sn + y * cs) for x, y in corners]
    return (
        min(point[0] for point in rotated),
        max(point[0] for point in rotated),
        min(point[1] for point in rotated),
        max(point[1] for point in rotated),
        ca,
        sa,
    )
def _point_segment_distance(point, start, end):
    """Return the shortest distance from *point* to a finite segment."""
    vx = end[0] - start[0]
    vy = end[1] - start[1]
    wx = point[0] - start[0]
    wy = point[1] - start[1]
    length_sq = vx * vx + vy * vy
    if length_sq <= 1e-18:
        return math.hypot(wx, wy)
    fraction = max(0.0, min(1.0, (wx * vx + wy * vy) / length_sq))
    return math.hypot(
        point[0] - (start[0] + fraction * vx),
        point[1] - (start[1] + fraction * vy),
    )


def _segment_distance(first_a, first_b, second_a, second_b):
    """Return the shortest distance between two finite 2-D segments."""
    first_x = first_b[0] - first_a[0]
    first_y = first_b[1] - first_a[1]
    second_x = second_b[0] - second_a[0]
    second_y = second_b[1] - second_a[1]
    denominator = first_x * second_y - first_y * second_x
    if abs(denominator) > 1e-12:
        delta_x = second_a[0] - first_a[0]
        delta_y = second_a[1] - first_a[1]
        first_fraction = (
            delta_x * second_y - delta_y * second_x
        ) / denominator
        second_fraction = (
            delta_x * first_y - delta_y * first_x
        ) / denominator
        if (
            0.0 <= first_fraction <= 1.0
            and 0.0 <= second_fraction <= 1.0
        ):
            return 0.0
    return min(
        _point_segment_distance(first_a, second_a, second_b),
        _point_segment_distance(first_b, second_a, second_b),
        _point_segment_distance(second_a, first_a, first_b),
        _point_segment_distance(second_b, first_a, first_b),
    )


def _polyline_segments(points):
    """Return the non-blank segments from one row of sampled points."""
    return [
        (first, second)
        for first, second in zip(points, points[1:])
        if first is not None and second is not None
    ]


def _polyline_pair_is_clear(first_segments, second_segments, minimum):
    """Check two x-monotone polylines using a linear segment sweep."""
    if not first_segments or not second_segments:
        return True
    if len(first_segments) * len(second_segments) >= 256:
        first = np.asarray(
            first_segments,
            dtype=np.float64,
        ).reshape(-1, 4)
        second = np.asarray(
            second_segments,
            dtype=np.float64,
        ).reshape(-1, 4)
        first_min_x = np.minimum(first[:, 0], first[:, 2])
        first_max_x = np.maximum(first[:, 0], first[:, 2])
        second_min_x = np.minimum(second[:, 0], second[:, 2])
        second_max_x = np.maximum(second[:, 0], second[:, 2])
        overlapping = (
            (second_min_x[None, :] <= first_max_x[:, None] + minimum)
            & (second_max_x[None, :] >= first_min_x[:, None] - minimum)
        )
        first_index, second_index = np.nonzero(overlapping)
        if not len(first_index):
            return True
        first = first[first_index]
        second = second[second_index]
        first_x = first[:, 2] - first[:, 0]
        first_y = first[:, 3] - first[:, 1]
        second_x = second[:, 2] - second[:, 0]
        second_y = second[:, 3] - second[:, 1]
        denominator = first_x * second_y - first_y * second_x
        delta_x = second[:, 0] - first[:, 0]
        delta_y = second[:, 1] - first[:, 1]
        nonzero = np.abs(denominator) > 1e-12
        first_fraction = np.divide(
            delta_x * second_y - delta_y * second_x,
            denominator,
            out=np.full_like(denominator, -1.0),
            where=nonzero,
        )
        second_fraction = np.divide(
            delta_x * first_y - delta_y * first_x,
            denominator,
            out=np.full_like(denominator, -1.0),
            where=nonzero,
        )
        if np.any(
            nonzero
            & (first_fraction >= 0.0)
            & (first_fraction <= 1.0)
            & (second_fraction >= 0.0)
            & (second_fraction <= 1.0)
        ):
            return False

        def point_segment_distance(
            point_x,
            point_y,
            start_x,
            start_y,
            end_x,
            end_y,
        ):
            vector_x = end_x - start_x
            vector_y = end_y - start_y
            length_sq = vector_x * vector_x + vector_y * vector_y
            projection = np.divide(
                (point_x - start_x) * vector_x
                + (point_y - start_y) * vector_y,
                length_sq,
                out=np.zeros_like(length_sq),
                where=length_sq > 1e-18,
            )
            projection = np.clip(projection, 0.0, 1.0)
            return np.hypot(
                point_x - (start_x + projection * vector_x),
                point_y - (start_y + projection * vector_y),
            )

        distances = np.minimum.reduce(
            (
                point_segment_distance(
                    first[:, 0],
                    first[:, 1],
                    second[:, 0],
                    second[:, 1],
                    second[:, 2],
                    second[:, 3],
                ),
                point_segment_distance(
                    first[:, 2],
                    first[:, 3],
                    second[:, 0],
                    second[:, 1],
                    second[:, 2],
                    second[:, 3],
                ),
                point_segment_distance(
                    second[:, 0],
                    second[:, 1],
                    first[:, 0],
                    first[:, 1],
                    first[:, 2],
                    first[:, 3],
                ),
                point_segment_distance(
                    second[:, 2],
                    second[:, 3],
                    first[:, 0],
                    first[:, 1],
                    first[:, 2],
                    first[:, 3],
                ),
            )
        )
        return bool(np.all(distances >= minimum - 1e-9))
    second_index = 0
    for first_a, first_b in first_segments:
        first_min_x = min(first_a[0], first_b[0])
        first_max_x = max(first_a[0], first_b[0])
        while (
            second_index < len(second_segments)
            and max(
                second_segments[second_index][0][0],
                second_segments[second_index][1][0],
            )
            < first_min_x - minimum
        ):
            second_index += 1
        check_index = second_index
        while check_index < len(second_segments):
            second_a, second_b = second_segments[check_index]
            second_min_x = min(second_a[0], second_b[0])
            second_max_x = max(second_a[0], second_b[0])
            if second_min_x > first_max_x + minimum:
                break
            if (
                _segment_distance(first_a, first_b, second_a, second_b)
                < minimum - 1e-9
            ):
                return False
            check_index += 1
    return True


def _wave_clearance_ok(
    positions,
    spacing,
    minimum_clearance_mm=0.0,
):
    """Check the shortest distance between adjacent visible row segments."""
    minimum_clearance = max(0.0, float(minimum_clearance_mm))
    if minimum_clearance:
        visible_rows = [
            segments
            for row in positions
            if (segments := _polyline_segments(row))
        ]
        for first_row, second_row in zip(visible_rows, visible_rows[1:]):
            if not _polyline_pair_is_clear(
                first_row,
                second_row,
                minimum_clearance,
            ):
                return False
    return True


def _smooth_tone_row(values, radius):
    """Return a horizontal box-smoothed tone row without per-pixel ripples."""
    if radius <= 0 or len(values) < 3:
        return list(values)
    prefix = [0.0]
    for value in values:
        prefix.append(prefix[-1] + float(value))
    smoothed = []
    last = len(values) - 1
    for index in range(len(values)):
        low = max(0, index - radius)
        high = min(last, index + radius)
        smoothed.append(
            (prefix[high + 1] - prefix[low]) / max(high - low + 1, 1)
        )
    return smoothed


def _smooth_tone_rows(rows, along_radius, row_window):
    """Smooth tone spatially in the Wave screen's row frame."""
    if not rows:
        return []
    horizontally_smoothed = [
        _smooth_tone_row(row, along_radius)
        for row in rows
    ]
    window = min(max(1, int(row_window)), len(horizontally_smoothed))
    if window <= 1:
        return horizontally_smoothed
    smoothed = []
    for row_index in range(len(horizontally_smoothed)):
        low = min(
            max(0, row_index - window // 2),
            len(horizontally_smoothed) - window,
        )
        high = low + window
        smoothed.append(
            [
                sum(
                    horizontally_smoothed[index][x_index]
                    for index in range(low, high)
                )
                / window
                for x_index in range(len(horizontally_smoothed[row_index]))
            ]
        )
    return smoothed


def _directional_tone_contrast(rows):
    """Return an edge envelope from immediate along-row tone differences.

    The absolute, smoothed tone field still controls row density. This
    unsmoothed contrast field controls only local wave amplitude, so a narrow
    light/dark transition produces a matching narrow spike and uniform tone
    remains flat.
    """
    contrast_rows = []
    for row in rows:
        if not row:
            contrast_rows.append([])
            continue
        contrast = [0.0] * len(row)
        for index, value in enumerate(row):
            differences = []
            if index:
                differences.append(abs(float(value) - float(row[index - 1])))
            if index + 1 < len(row):
                differences.append(abs(float(value) - float(row[index + 1])))
            if differences:
                contrast[index] = min(1.0, max(differences))
        contrast_rows.append(contrast)
    return contrast_rows


def _windowed_tone_contrast(
    rows,
    x_values,
    row_ys,
    min_x,
    max_x,
    ca,
    sa,
    source_step_mm,
    sampler,
):
    """Find immediate light/dark differences around each output sample.

    Sampling one source pixel to either side catches a one-pixel line even
    when its centre falls between the Wave carrier's normal output samples.
    The small dead band discards compression or paper-texture noise without
    smoothing the remaining edge response.
    """
    source_step = max(0.0, float(source_step_mm or 0.0))
    if source_step <= 1e-9:
        return _directional_tone_contrast(rows)
    contrast_rows = []
    for row_index, y in enumerate(row_ys):
        contrast = []
        for x_index, x in enumerate(x_values):
            center = float(rows[row_index][x_index])
            left_x = max(min_x, x - source_step)
            right_x = min(max_x, x + source_step)
            left = float(
                sampler(
                    left_x * ca - y * sa,
                    left_x * sa + y * ca,
                )
            )
            right = float(
                sampler(
                    right_x * ca - y * sa,
                    right_x * sa + y * ca,
                )
            )
            difference = max(center, left, right) - min(
                center,
                left,
                right,
            )
            contrast.append(
                max(
                    0.0,
                    difference
                    - WAVE_FIDELITY_CONTRAST_EDGE_THRESHOLD,
                )
                / (1.0 - WAVE_FIDELITY_CONTRAST_EDGE_THRESHOLD)
            )
        contrast_rows.append(contrast)
    return contrast_rows


def _bound_fixed_baseline_amplitudes(
    amplitudes,
    maximum_step,
):
    """Keep the shared-phase amplitude field within a row-gap budget.

    Consecutive fixed-baseline rows have the same phase, so their relative
    displacement is ``(a_i - a_i+1) * sin(phase)``. Limiting that amplitude
    difference bounds the relative motion at every along-row position. The
    forward and backward passes construct the lowest amplitude field that is
    both at least the tone-driven request and satisfies that bound. The
    coverage mask still decides whether a row emits a mark; this envelope only
    controls the relative motion of rows that do appear there.
    """
    maximum_step = max(0.0, float(maximum_step))
    bounded = [0.0] * len(amplitudes)
    for row_index, amplitude in enumerate(amplitudes):
        bounded[row_index] = max(0.0, float(amplitude))
    for row_index in range(1, len(bounded)):
        bounded[row_index] = max(
            bounded[row_index],
            bounded[row_index - 1] - maximum_step,
        )
    for row_index in range(len(bounded) - 2, -1, -1):
        bounded[row_index] = max(
            bounded[row_index],
            bounded[row_index + 1] - maximum_step,
        )
    return bounded


def _bound_visible_fixed_baseline_amplitudes(
    amplitudes,
    visible,
    spacing,
    clearance,
):
    """Bound amplitude changes across the rows a fidelity grid actually emits.

    Tone-density gating can remove whole candidate rows. The remaining rows are
    still on the original integer baseline lattice, so a gap of two or more
    pitches leaves proportionally more room for their shared-phase amplitudes
    to differ. This keeps the tone-driven depth that the skip created instead
    of applying the one-pitch envelope as if every intermediate row existed.
    """
    spacing = max(0.0, float(spacing))
    clearance = max(0.0, float(clearance))
    bounded = [0.0] * len(amplitudes)
    active = [
        index
        for index, is_visible in enumerate(visible)
        if is_visible
    ]
    for index in active:
        bounded[index] = max(0.0, float(amplitudes[index]))

    def enforce(forward):
        indexes = active if forward else reversed(active)
        previous = None
        for index in indexes:
            if previous is not None:
                row_gap = abs(index - previous)
                maximum_step = max(
                    0.0,
                    row_gap * spacing - clearance,
                )
                if forward:
                    bounded[index] = max(
                        bounded[index],
                        bounded[previous] - maximum_step,
                    )
                else:
                    bounded[index] = max(
                        bounded[index],
                        bounded[previous] - maximum_step,
                    )
            previous = index

    enforce(forward=True)
    enforce(forward=False)
    return bounded


def _ordered_cell_threshold(seed, row_index, cell_index):
    """Return a stable ordered threshold for one Wave density cell.

    Mixing independent row and along-row cell coordinates extends the existing
    low-discrepancy row dithering into two dimensions. Every cell is complete
    rather than sampled per raster pixel, so a light field can turn whole
    coarse strokes on and off without producing one-sample dashes.
    """
    value = (
        (int(row_index) * 0x9E3779B1)
        ^ (int(cell_index) * 0x85EBCA77)
        ^ (int(seed) * 0xC2B2AE3D)
    ) & 0xFFFFFFFF
    reversed_value = 0
    for _bit in range(32):
        reversed_value = (reversed_value << 1) | (value & 1)
        value >>= 1
    return (reversed_value + 0.5) / 4294967296.0


def _ordered_density_thresholds(seed, row_index, cell_count):
    """Build a smooth deterministic threshold field along one Wave row.

    Independent cell thresholds match local tone but break every coarse cell
    into a separate pen-down mark. Smoothing the ordered field before
    normalizing it keeps several adjacent cells on the same side of the
    cutoff, so the density dither forms strokes rather than a cell checkerboard.
    """
    if cell_count <= 0:
        return []
    thresholds = [
        _ordered_cell_threshold(seed, row_index, cell_index)
        for cell_index in range(cell_count)
    ]
    smoothed = _smooth_tone_row(
        thresholds,
        min(WAVE_FIDELITY_CELL_SMOOTHING_CELLS, max(0, (cell_count - 1) // 2)),
    )
    low = min(smoothed)
    high = max(smoothed)
    if high - low <= 1e-12:
        return thresholds
    return [
        (value - low) / (high - low)
        for value in smoothed
    ]


def _fill_short_density_gaps(
    visible_cells,
    cell_coverage,
    minimum_coverage=INK_FLOOR,
    bridge_cells=1,
):
    """Close short hidden gaps between visible tone cells in one row.

    A cell-scale ordered threshold can leave one isolated hidden cell between
    two inked runs. Closing only that bounded gap keeps the nominal coarse
    threshold while preventing a one-cell checkerboard from turning into
    separate pen-down strokes.
    """
    if len(visible_cells) < 3 or bridge_cells <= 0:
        return visible_cells
    visible = list(visible_cells)
    index = 0
    while index < len(visible):
        if visible[index]:
            index += 1
            continue
        gap_start = index
        while index < len(visible) and not visible[index]:
            index += 1
        gap_end = index
        if (
            gap_start > 0
            and gap_end < len(visible)
            and visible[gap_start - 1]
            and visible[gap_end]
            and gap_end - gap_start <= int(bridge_cells)
            and sum(cell_coverage[gap_start:gap_end])
            / max(gap_end - gap_start, 1)
            >= max(INK_FLOOR, float(minimum_coverage))
        ):
            visible[gap_start:gap_end] = [True] * (gap_end - gap_start)
    return visible


def _clearance_limited_wave_amplitude(
    requested_amplitude,
    spacing,
    clearance,
    maximum_amplitude_difference,
    maximum_phase_slope,
):
    """Limit a shared carrier so its steep flanks stay outside the pen gap.

    Equal fixed-baseline rows are parallel curves. At phase zero their
    perpendicular separation is smaller than their vertical separation, while
    at a crest or trough the slope is zero and the full amplitude difference
    controls the gap. Sampling both terms together avoids treating the pen
    envelope as a purely vertical budget.
    """
    requested = max(0.0, float(requested_amplitude))
    spacing = max(0.0, float(spacing))
    clearance = max(0.0, float(clearance))
    difference = max(0.0, float(maximum_amplitude_difference))
    phase_slope = max(0.0, float(maximum_phase_slope))
    if requested <= 1e-12 or spacing <= clearance:
        return 0.0 if spacing <= clearance else requested

    def is_clear(amplitude):
        for sample in range(64):
            phase = math.pi * sample / 63.0
            vertical = spacing - difference * abs(math.sin(phase))
            tangent = amplitude * phase_slope * abs(math.cos(phase))
            if vertical / math.sqrt(1.0 + tangent * tangent) < clearance:
                return False
        return True

    if is_clear(requested):
        return requested
    low = 0.0
    high = requested
    for _iteration in range(28):
        middle = 0.5 * (low + high)
        if is_clear(middle):
            low = middle
        else:
            high = middle
    return low


def _visible_depth_anchor(smoothed_tone, coverage_rows):
    """Median depth value over the samples an ink actually draws.

    The depth-intensity curve must be centered on the ink's own visible
    mid-tone. A fixed 0.5 anchor pushes every below-mid value toward zero as
    intensity rises, which collapses a dark ink (for example black after
    gray-component replacement) onto a straight baseline even though its
    relative light/dark structure is real.
    """
    visible = [
        float(value)
        for row_index, row in enumerate(smoothed_tone)
        for value_index, value in enumerate(row)
        if coverage_rows[row_index][value_index] >= INK_FLOOR
    ]
    if not visible:
        return 0.5
    ordered = sorted(visible)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return 0.5 * (ordered[middle - 1] + ordered[middle])


def _wave_rows(
    darkness,
    bounds,
    angle_deg,
    spacing,
    amplitude_scale,
    min_length_mm=0.8,
    cancel_check=None,
    path_tolerance_mm=0.05,
    depth_darkness=None,
    equal_spacing=False,
    zero_anchored_depth=False,
    fixed_baseline_depth=False,
    minimum_clearance_mm=0.0,
    wave_frequency_variation=0.0,
    wave_period_pitches=DEFAULT_WAVE_PERIOD_PITCHES,
    wave_period_variation=DEFAULT_WAVE_PERIOD_VARIATION,
    wave_depth_intensity=DEFAULT_WAVE_DEPTH_INTENSITY,
    seed=0,
    fidelity_row_density=False,
    row_pen_diameter_mm=None,
    fidelity_cell_pitches=WAVE_FIDELITY_CELL_PITCHES,
    contrast_source_step_mm=None,
):
    """Sine rows with tone-driven depth and a safety envelope.

    Local tone still masks each mark to the image. A locally smoothed two-axis
    tone field also varies wave shape without turning image texture into a
    second high-frequency wave. The phase-locked depth mode
    keeps one phase carrier across all rows and varies only their amplitude
    from scene depth. The equidistant mode translates one common waveform with
    no row-specific movement. The fixed-baseline mode keeps the equal row
    lattice but lets local depth vary each row's amplitude, phase, and phase
    rate. All modes use the final shortest-segment check to preserve the
    configured pen envelope.

    The fidelity variant keeps that same baseline lattice but applies a stable
    ordered threshold field over coarse along-row cells. Sparse, light cells
    therefore skip whole short runs instead of paying the continuous-line
    coverage floor everywhere, while dark cells keep the carrier continuous.
    Its amplitude comes from unsmoothed immediate along-row luminance contrast,
    so a narrow edge produces a narrow spike and uniform tone stays flat.
    The threshold is keyed only by seed, row index, and cell index; it does not
    introduce random state or per-row phases.
    """
    min_x, max_x, min_y, max_y, ca, sa = _local_frame(bounds, angle_deg)
    spacing = max(0.2, float(spacing))
    amplitude_scale = max(0.05, float(amplitude_scale))
    if zero_anchored_depth:
        # Adjacent row bands meet, but cannot overlap, at half the pitch. This
        # keeps nearest-neighbour checking local to consecutive rows.
        amplitude_scale = min(1.0, amplitude_scale)
    amplitude_max = spacing * 0.5 * amplitude_scale
    if fixed_baseline_depth:
        clearance = max(0.0, float(minimum_clearance_mm))
        if clearance > spacing + 1e-9:
            raise ValueError(
                "Wave screen cannot keep adjacent pen strokes apart: "
                "the effective pitch is smaller than the pen width plus "
                "edge gap."
            )
    wavelength = (
        spacing * max(0.5, float(wave_period_pitches))
        if fixed_baseline_depth
        else spacing * 2.0
    )
    frequency_variation = max(
        0.0, min(0.45, float(wave_frequency_variation))
    )
    max_frequency_scale = (
        1.0
        + (
            frequency_variation
            if equal_spacing or fixed_baseline_depth
            else 0.0
        )
        + (
            WAVE_FIXED_FREQUENCY_TONE_GAIN * 0.5
            if fixed_baseline_depth and wave_period_variation <= 0.0
            else max(0.0, float(wave_period_variation)) * 0.5
            if fixed_baseline_depth
            else 0.0
        )
    )
    if fixed_baseline_depth:
        # Keep crest height proportional to wavelength so a long period still
        # reads as a wave instead of a near-straight line. Cap at one row
        # pitch so the fixed baselines stay legible; adjacent rows share the
        # same phase carrier, so equal amplitude never changes the row gap.
        wave_amplitude = (
            min(spacing, wavelength * WAVE_AMPLITUDE_FRACTION)
            * amplitude_scale
        )
        base_wavenumber = 2.0 * math.pi / wavelength
    else:
        wave_amplitude = amplitude_max
        base_wavenumber = math.pi / spacing
    # A piecewise-linear sine turns into visible facets when its samples are
    # too far apart. Bound the sagitta against the configured path budget:
    # max|y''| for amplitude * sin(k*x) is amplitude * k^2, and a chord of
    # length h has about h^2/8 times that curvature as its midpoint error.
    curvature = wave_amplitude * (base_wavenumber * max_frequency_scale) ** 2
    tolerance_step = math.sqrt(
        8.0 * max(0.001, float(path_tolerance_mm)) / curvature
    )
    sample_step = max(
        0.05,
        min(spacing * 0.25, 0.8, tolerance_step),
    )
    row_ys = []
    y = min_y + spacing * 0.5
    while y <= max_y:
        row_ys.append(y)
        y += spacing

    x_values = []
    x = min_x
    while x <= max_x:
        x_values.append(x)
        x += sample_step

    base_phases = [
        2.0 * math.pi * (x - min_x) / wavelength for x in x_values
    ]
    wave_phases = base_phases
    if equal_spacing and frequency_variation > 1e-9 and len(x_values) > 1:
        span = max(max_x - min_x, wavelength)
        long_period = max(wavelength * 7.0, span * 0.73)
        short_period = max(wavelength * 2.2, span * 0.29)
        phase_offset = (
            2.0
            * math.pi
            * ((int(seed) * 0.6180339887498949) % 1.0)
        )
        short_phase_offset = (
            2.0
            * math.pi
            * ((int(seed) * 0.4142135623730950 + 0.31) % 1.0)
        )
        frequency_scales = [
            1.0
            + frequency_variation
            * (
                0.67
                * math.sin(
                    2.0
                    * math.pi
                    * (x - min_x)
                    / long_period
                    + phase_offset
                )
                + 0.33
                * math.sin(
                    2.0
                    * math.pi
                    * (x - min_x)
                    / short_period
                    + short_phase_offset
                )
            )
            for x in x_values
        ]
        radians_per_mm = 2.0 * math.pi / wavelength
        wave_phases = [0.0]
        for index in range(1, len(x_values)):
            delta_x = x_values[index] - x_values[index - 1]
            mean_frequency_scale = 0.5 * (
                frequency_scales[index - 1] + frequency_scales[index]
            )
            wave_phases.append(
                wave_phases[-1]
                + radians_per_mm * mean_frequency_scale * delta_x
            )

    tone_rows = []
    depth_rows = []
    for y in row_ys:
        check_cancelled(cancel_check)
        tone_rows.append(
            [
                darkness(x * ca - y * sa, x * sa + y * ca)
                for x in x_values
            ]
        )
        if depth_darkness is not None:
            depth_rows.append(
                [
                    depth_darkness(x * ca - y * sa, x * sa + y * ca)
                    for x in x_values
                ]
            )
    if depth_darkness is None:
        depth_rows = tone_rows
    coverage_rows = tone_rows
    if fixed_baseline_depth and len(x_values) > 2:
        contrast_rows = (
            _windowed_tone_contrast(
                depth_rows,
                x_values,
                row_ys,
                min_x,
                max_x,
                ca,
                sa,
                contrast_source_step_mm,
                depth_darkness if depth_darkness is not None else darkness,
            )
            if fidelity_row_density
            else None
        )
        depth_span_samples = max(
            1,
            int(
                round(
                    WAVE_DEPTH_ALONG_SMOOTHING_PITCHES
                    * spacing
                    / max(sample_step, 1e-9)
                )
            ),
        )
        coverage_span_samples = max(
            1,
            int(
                round(
                    WAVE_COVERAGE_ALONG_SMOOTHING_PITCHES
                    * spacing
                    / max(sample_step, 1e-9)
                )
            ),
        )
        coverage_rows = _smooth_tone_rows(
            tone_rows,
            max(0, coverage_span_samples // 2),
            WAVE_COVERAGE_ROW_WINDOW,
        )
        smoothed_tone = _smooth_tone_rows(
            depth_rows,
            max(0, depth_span_samples // 2),
            WAVE_DEPTH_ROW_WINDOW,
        )
    else:
        contrast_rows = None
        smoothed_tone = _smooth_tone_rows(
            depth_rows,
            0,
            WAVE_DEPTH_ROW_WINDOW,
        )
    depth_intensity = max(0.0, float(wave_depth_intensity))
    if depth_intensity <= 1e-9:
        smoothed_tone = [
            [0.0] * len(row)
            for row in smoothed_tone
        ]
    elif abs(depth_intensity - 1.0) > 1e-9:
        anchor = _visible_depth_anchor(smoothed_tone, coverage_rows)
        shaped = []
        for row in smoothed_tone:
            shaped_row = []
            for value in row:
                value = max(0.0, min(1.0, float(value)))
                if depth_intensity < 1.0:
                    shaped_row.append(
                        anchor + (value - anchor) * depth_intensity
                    )
                    continue
                band = max(0.08, 0.5 / depth_intensity)
                normalized = max(
                    0.0,
                    min(
                        1.0,
                        0.5 + (value - anchor) / (2.0 * band),
                    ),
                )
                smooth = normalized * normalized * (
                    3.0 - 2.0 * normalized
                )
                linear = max(
                    0.0,
                    min(
                        1.0,
                        anchor + (value - anchor) * depth_intensity,
                    ),
                )
                weight = min(1.0, depth_intensity - 1.0)
                shaped_row.append(
                    linear * (1.0 - weight) + smooth * weight
                )
            shaped.append(shaped_row)
        smoothed_tone = shaped
    shared_tone = [
        sum(row[x_index] for row in smoothed_tone)
        / max(len(smoothed_tone), 1)
        for x_index in range(len(x_values))
    ]
    amplitude_tone = smoothed_tone
    if contrast_rows is not None:
        contrast_gain = (
            max(0.0, float(depth_intensity))
            * WAVE_FIDELITY_CONTRAST_GAIN
        )
        amplitude_tone = [
            [
                min(1.0, value * contrast_gain)
                for value in row
            ]
            for row in contrast_rows
        ]
    density_visible = [
        [True] * len(x_values)
        for _row_index in range(len(row_ys))
    ]
    if fidelity_row_density:
        pen_diameter = (
            max(0.0, float(row_pen_diameter_mm))
            if row_pen_diameter_mm is not None
            else max(
                0.0,
                float(minimum_clearance_mm) - WAVE_MIN_EDGE_GAP_MM,
            )
        )
        # One selected row adds about pen-width / pitch coverage. Dividing
        # the requested local ink by that floor makes the row-selection
        # probability approximate the separated channel coverage, while dark
        # cells still retain every row.
        line_coverage = max(
            0.02,
            min(
                1.0,
                WAVE_FIDELITY_LINE_COVERAGE_SCALE
                * pen_diameter
                / spacing,
            ),
        )
        cell_width = max(
            WAVE_FIDELITY_MIN_CELL_MM,
            min(
                WAVE_FIDELITY_MAX_CELL_MM,
                spacing * max(0.01, float(fidelity_cell_pitches)),
            ),
        )
        cell_indexes = [int((x - min_x) / cell_width) for x in x_values]
        cell_count = max(cell_indexes, default=-1) + 1
        for row_index in range(len(row_ys)):
            thresholds = _ordered_density_thresholds(
                seed,
                row_index,
                cell_count,
            )
            cell_samples = {}
            for value_index, cell_index in enumerate(cell_indexes):
                cell_samples.setdefault(cell_index, []).append(
                    coverage_rows[row_index][value_index]
                )
            visible_cells = {}
            for cell_index, samples in cell_samples.items():
                cutoff = (
                    thresholds[cell_index]
                    * line_coverage
                )
                sample = sum(samples) / len(samples)
                visible_cells[cell_index] = (
                    sample >= max(INK_FLOOR, cutoff)
                )
            visible_values = _fill_short_density_gaps(
                [
                    visible_cells.get(cell_index, False)
                    for cell_index in range(cell_count)
                ],
                [
                    sum(cell_samples.get(cell_index, [0.0]))
                    / max(len(cell_samples.get(cell_index, [1])), 1)
                    for cell_index in range(cell_count)
                ],
                bridge_cells=WAVE_FIDELITY_BRIDGE_CELLS,
                minimum_coverage=(
                    WAVE_FIDELITY_BRIDGE_MIN_COVERAGE * line_coverage
                ),
            )
            visible_cells = {
                cell_index: visible_values[cell_index]
                for cell_index in range(cell_count)
            }
            density_visible[row_index] = [
                visible_cells[cell_indexes[x_index]]
                and coverage_rows[row_index][x_index] >= INK_FLOOR
                for x_index in range(len(x_values))
            ]
        coverage_rows = [
            [
                coverage if density_visible[row_index][x_index] else 0.0
                for x_index, coverage in enumerate(coverage_rows[row_index])
            ]
            for row_index in range(len(row_ys))
        ]
    row_clearance_scales = [None] * len(row_ys)

    if equal_spacing:
        # Every row receives the same displacement at each x. The vertical
        # distance between all row centre lines is therefore exactly `spacing`.
        positions = [
            [None] * len(x_values)
            for _row_index in range(len(row_ys))
        ]
        for row_index, y in enumerate(row_ys):
            for x_index, x in enumerate(x_values):
                if coverage_rows[row_index][x_index] >= INK_FLOOR:
                    offset = (
                        amplitude_max
                        * shared_tone[x_index]
                        * math.sin(wave_phases[x_index])
                    )
                    positions[row_index][x_index] = (x, y + offset)
    elif fixed_baseline_depth:
        clearance = max(0.0, float(minimum_clearance_mm))
        clearance_target = clearance + WAVE_CLEARANCE_SAFETY_MARGIN_MM
        if clearance_target > spacing + 1e-9:
            raise ValueError(
                "Wave screen cannot keep adjacent pen strokes apart: "
                "the effective pitch is smaller than the pen width plus "
                "edge gap."
            )
        required_pitch = fixed_wave_minimum_pitch_mm(
            clearance,
            period_pitches=wave_period_pitches,
            period_variation=wave_period_variation,
            frequency_variation=wave_frequency_variation,
            amplitude_scale=amplitude_scale,
        )
        if spacing < required_pitch - 1e-9:
            raise ValueError(
                "Variable-depth Wave needs a larger effective pitch for "
                "the selected period and tonal variation: current %.3f mm, "
                "minimum %.3f mm."
                % (spacing, required_pitch)
            )
        radians_per_mm = 2.0 * math.pi / wavelength
        period_variation = max(
            0.0,
            float(wave_period_variation),
        )
        common_phase_offset = (
            2.0
            * math.pi
            * ((int(seed) * 0.6180339887498949) % 1.0)
        )
        span = max(max_x - min_x, wavelength)

        def common_frequency_variation(x_index, phase_offset):
            if frequency_variation <= 1e-9:
                return 0.0
            return frequency_variation * (
                0.6
                * math.sin(
                    2.0
                    * math.pi
                    * (x_values[x_index] - min_x)
                    / max(span * 0.71, wavelength * 5.0)
                    + phase_offset * 0.37
                )
                + 0.4
                * math.sin(
                    2.0
                    * math.pi
                    * (x_values[x_index] - min_x)
                    / max(span * 0.29, wavelength * 2.2)
                    + phase_offset * 0.83
                )
            )

        nested_phases = [common_phase_offset]
        for x_index in range(1, len(x_values)):
            delta_x = x_values[x_index] - x_values[x_index - 1]
            common_variation = common_frequency_variation(
                x_index,
                common_phase_offset,
            )
            frequency_scale = max(
                0.5,
                1.0
                + common_variation
                + period_variation
                * (shared_tone[x_index] - 0.5),
            )
            nested_phases.append(
                nested_phases[-1]
                + radians_per_mm * frequency_scale * delta_x
            )

        analytic_clearance = (
            clearance_target
            + (
                WAVE_FIDELITY_CLEARANCE_ENVELOPE_MARGIN_MM
                if fidelity_row_density
                else WAVE_ANALYTIC_CLEARANCE_MARGIN_MM
            )
        )
        available_step = max(0.0, spacing - analytic_clearance)
        uncapped_wave_amplitude = wave_amplitude
        wave_amplitude = _clearance_limited_wave_amplitude(
            wave_amplitude,
            spacing,
            analytic_clearance,
            available_step,
            radians_per_mm * max_frequency_scale,
        )
        if fidelity_row_density:
            fidelity_depth_gain = 0.82 + 0.22 * min(
                1.0,
                max(0.0, (depth_intensity - 0.5) / 1.0),
            )
            wave_amplitude *= fidelity_depth_gain
        depth_normalization = 1.0
        if (
            contrast_rows is None
            and wave_amplitude < uncapped_wave_amplitude - 1e-12
        ):
            intensity_fill = min(
                1.0,
                1.0
                - WAVE_DEPTH_INTENSITY_HEADROOM
                + WAVE_DEPTH_INTENSITY_HEADROOM
                * min(1.5, max(0.0, depth_intensity))
                / 1.5,
            )
            wave_amplitude *= intensity_fill
            visible_depth = [
                smoothed_tone[row_index][x_index]
                for row_index in range(len(row_ys))
                for x_index in range(len(x_values))
                if coverage_rows[row_index][x_index] >= INK_FLOOR
            ]
            depth_peak = max(visible_depth, default=0.0)
            if depth_peak > 1e-12:
                depth_normalization = 1.0 / depth_peak
        bounded_amplitudes = [
            [0.0] * len(x_values)
            for _row_index in range(len(row_ys))
        ]
        amplitude_rows = []
        for row_index in range(len(row_ys)):
            amplitude_row = []
            for x_index in range(len(x_values)):
                tone = min(
                    1.0,
                    amplitude_tone[row_index][x_index]
                    * depth_normalization,
                )
                amplitude_row.append(wave_amplitude * tone)
            amplitude_rows.append(amplitude_row)
        for x_index in range(len(x_values)):
            column_amplitudes = [
                amplitude_rows[row_index][x_index]
                for row_index in range(len(row_ys))
            ]
            if fidelity_row_density:
                bounded_column = _bound_visible_fixed_baseline_amplitudes(
                    column_amplitudes,
                    [
                        density_visible[row_index][x_index]
                        for row_index in range(len(row_ys))
                    ],
                    spacing,
                    analytic_clearance,
                )
            else:
                bounded_column = _bound_fixed_baseline_amplitudes(
                    column_amplitudes,
                    available_step,
                )
            for row_index, amplitude in enumerate(bounded_column):
                bounded_amplitudes[row_index][x_index] = amplitude
        def candidate_positions(scale=1.0):
            positions = [
                [None] * len(x_values)
                for _row_index in range(len(row_ys))
            ]
            for row_index, y in enumerate(row_ys):
                for x_index, x in enumerate(x_values):
                    if coverage_rows[row_index][x_index] < INK_FLOOR:
                        continue
                    offset = (
                        scale
                        * bounded_amplitudes[row_index][x_index]
                        * math.sin(nested_phases[x_index])
                    )
                    positions[row_index][x_index] = (x, y + offset)
            return positions

        positions = candidate_positions()
        if not _wave_clearance_ok(
            positions,
            spacing,
            clearance_target,
        ):
            flat = candidate_positions(scale=0.0)
            if not _wave_clearance_ok(
                flat,
                spacing,
                clearance_target,
            ):
                raise ValueError(
                    "Wave screen cannot keep the fixed baseline rows apart."
                )
            low = 0.0
            high = 1.0
            positions = flat
            for _step in range(WAVE_CLEARANCE_SEARCH_STEPS):
                scale = (low + high) * 0.5
                candidate = candidate_positions(scale=scale)
                if _wave_clearance_ok(
                    candidate,
                    spacing,
                    clearance_target,
                ):
                    low = scale
                    positions = candidate
                else:
                    high = scale
        row_clearance_scales = [1.0] * len(row_ys)
    elif zero_anchored_depth:
        clearance = max(0.0, float(minimum_clearance_mm))
        if clearance > spacing + 1e-9:
            raise ValueError(
                "Wave screen cannot keep adjacent pen strokes apart: "
                "the effective pitch is smaller than the pen width plus "
                "edge gap."
            )

        def candidate_positions(
            depth_scale=1.0,
        ):
            result = [
                [None] * len(x_values)
                for _row_index in range(len(row_ys))
            ]
            for x_index, x in enumerate(x_values):
                check_cancelled(cancel_check)
                for row_index, y in enumerate(row_ys):
                    if coverage_rows[row_index][x_index] < INK_FLOOR:
                        continue
                    offset = (
                        amplitude_max
                        * depth_scale
                        * smoothed_tone[row_index][x_index]
                        * math.sin(base_phases[x_index])
                    )
                    result[row_index][x_index] = (x, y + offset)
            return result

        positions = candidate_positions(
            depth_scale=1.0
        )
        if not _wave_clearance_ok(
            positions,
            spacing,
            minimum_clearance_mm,
        ):
            flat = candidate_positions(depth_scale=0.0)
            if not _wave_clearance_ok(
                flat,
                spacing,
                minimum_clearance_mm,
            ):
                raise ValueError(
                    "Wave screen cannot keep adjacent pen strokes apart: "
                    "the effective pitch is too small for the configured "
                    "pen width and edge gap."
                )
            low = 0.0
            high = 1.0
            best = flat
            for _step in range(WAVE_CLEARANCE_SEARCH_STEPS):
                depth_scale = (low + high) * 0.5
                candidate = candidate_positions(depth_scale=depth_scale)
                if _wave_clearance_ok(
                    candidate,
                    spacing,
                    minimum_clearance_mm,
                ):
                    low = depth_scale
                    best = candidate
                else:
                    high = depth_scale
            positions = best
        row_clearance_scales = [None] * len(row_ys)
    else:
        max_tone_step = min(
            1.0,
            spacing * WAVE_MAX_ADJACENT_GAP_FRACTION / amplitude_max,
        )
        depth_tone = []
        for x_index in range(len(x_values)):
            column = []
            for row_index in range(len(smoothed_tone)):
                current = smoothed_tone[row_index][x_index]
                if column:
                    previous = column[-1]
                    current = previous + max(
                        -max_tone_step,
                        min(max_tone_step, current - previous),
                    )
                column.append(current)
            depth_tone.append(column)
        positions = [
            [None] * len(x_values)
            for _row_index in range(len(row_ys))
        ]
        for row_index, y in enumerate(row_ys):
            for x_index, x in enumerate(x_values):
                if coverage_rows[row_index][x_index] >= INK_FLOOR:
                    offset = (
                        amplitude_max
                        * depth_tone[x_index][row_index]
                        * math.sin(base_phases[x_index])
                    )
                    positions[row_index][x_index] = (x, y + offset)
        row_clearance_scales = [None] * len(row_ys)

    rows = []
    row_policy = (
        "fixed_baselines"
        if fixed_baseline_depth
        else "translated_shared_wave"
        if equal_spacing
        else "phase_locked_row_depth"
        if zero_anchored_depth
        else "bounded_row_depth"
    )
    for row_index in range(len(row_ys)):
        check_cancelled(cancel_check)
        baseline = (
            min_x * ca - row_ys[row_index] * sa,
            min_x * sa + row_ys[row_index] * ca,
        )
        current = []
        for point in positions[row_index]:
            if point is not None:
                current.append(point)
            elif current:
                if current[-1][0] - current[0][0] >= min_length_mm:
                    trail = WaveTrail(
                        [
                            (px * ca - py * sa, px * sa + py * ca)
                            for px, py in current
                        ],
                        wave_row_index=row_index,
                        wave_baseline_mm=baseline,
                        wave_row_policy=row_policy,
                    )
                    trail.wave_clearance_scale = row_clearance_scales[
                        row_index
                    ]
                    trail.wave_period_pitches = float(
                        wave_period_pitches
                    )
                    trail.wave_period_variation = float(
                        wave_period_variation
                    )
                    trail.wave_depth_intensity = float(
                        wave_depth_intensity
                    )
                    rows.append(trail)
                current = []
        if current and current[-1][0] - current[0][0] >= min_length_mm:
            trail = WaveTrail(
                [
                    (px * ca - py * sa, px * sa + py * ca)
                    for px, py in current
                ],
                wave_row_index=row_index,
                wave_baseline_mm=baseline,
                wave_row_policy=row_policy,
            )
            trail.wave_clearance_scale = row_clearance_scales[row_index]
            trail.wave_period_pitches = float(wave_period_pitches)
            trail.wave_period_variation = float(
                wave_period_variation
            )
            trail.wave_depth_intensity = float(wave_depth_intensity)
            rows.append(trail)
    return rows
import bisect
import math

from .cancellation import check_cancelled


# Bound the midpoint shrink between adjacent rows caused by linear X/Y/A
# interpolation. For row pitch h and one emitted angle interval d:
# shrink ~= h * (1 - cos(d / 2)).
WAVE_ROW_INTERPOLATION_TOLERANCE_MM = 0.0005


def wave_row_screen_axes(settings):
    """Return ``(along, across)`` for final paper-space Wave rows."""
    angle_deg = float(
        getattr(settings, "row_lock_screen_angle_deg", 0.0)
    )
    if bool(getattr(settings, "flip_y", True)):
        angle_deg = -angle_deg
    return _screen_axes_from_angle(angle_deg)


def _screen_axes_from_angle(angle_deg):
    angle = math.radians(float(angle_deg))
    return (
        (math.cos(angle), math.sin(angle)),
        (-math.sin(angle), math.cos(angle)),
    )


def _project(point, axis):
    return point[0] * axis[0] + point[1] * axis[1]


def _median(values):
    ordered = sorted(values)
    if not ordered:
        return 0.0
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return 0.5 * (ordered[middle - 1] + ordered[middle])


def wave_row_theta_lock_enabled(settings):
    """Whether explicit Wave rows require one shared rotating-bed schedule."""
    if not bool(getattr(settings, "row_locked_compensation", False)):
        return False
    contour_order = str(
        getattr(settings, "contour_order", "optimized")
    ).strip().lower()
    if contour_order not in ("rows_ascending", "rows_descending"):
        return False
    theta_mode = str(
        getattr(settings, "theta_mode", "optimized")
    ).strip().lower()
    return theta_mode != "fixed"


def wave_row_theta_schedule(
    planned_items,
    settings,
    center,
    theta_planner,
    cancel_check=None,
):
    """Build one bed-angle schedule shared by every parallel Wave row.

    A rotating bed is valid for an equidistant Wave layer only if adjacent
    rows have the same orientation wherever they cross the same along-row
    coordinate. The representative row is planned once in the converter's
    screen frame, then every row samples the same ``theta(along)`` function.
    """
    if not wave_row_theta_lock_enabled(settings):
        return None

    along_axis, across_axis = wave_row_screen_axes(settings)
    row_groups = {}
    for item in planned_items:
        path = item["path"]
        row_index = getattr(path, "wave_row_index", None)
        if row_index is not None:
            row_groups.setdefault(int(row_index), []).append(path)
    if len(row_groups) < 2:
        return None

    row_across = {}
    candidates = []
    global_along = []
    for row_index, paths in row_groups.items():
        check_cancelled(cancel_check)
        values = [
            _project(point, across_axis)
            for path in paths
            for point in path
        ]
        if not values:
            continue
        row_across[row_index] = _median(values)
        for path in paths:
            check_cancelled(cancel_check)
            along_values = [_project(point, along_axis) for point in path]
            if along_values:
                global_along.extend(along_values)
                candidates.append(
                    (max(along_values) - min(along_values), path)
                )
    if len(row_across) < 2 or not candidates:
        return None

    pitch_mm = _row_pitch(row_across)
    if pitch_mm <= 1e-9:
        return None

    _span, template = max(candidates, key=lambda item: item[0])
    template_points = sorted(
        (_project(point, along_axis), _project(point, across_axis))
        for point in template
    )
    baseline = _median(value for _along, value in template_points)
    guide_screen = [
        (along, across - baseline)
        for along, across in template_points
    ]
    _extend_guide(
        guide_screen,
        min(global_along),
        max(global_along),
    )
    guide = [
        (
            along * along_axis[0] + across * across_axis[0],
            along * along_axis[1] + across * across_axis[1],
        )
        for along, across in guide_screen
    ]
    guide_thetas, _strategies = theta_planner(
        guide,
        settings,
        None,
        center,
        None,
        cancel_check,
    )
    if len(guide_thetas) != len(guide):
        return None
    positions, thetas = _deduplicate_along(
        guide,
        guide_thetas,
        along_axis,
    )
    if len(positions) < 2:
        return None

    configured_cap = max(
        float(getattr(settings, "theta_max_step_deg", 15.0)),
        0.0,
    )
    row_tolerance = min(
        WAVE_ROW_INTERPOLATION_TOLERANCE_MM,
        0.49 * pitch_mm,
    )
    spacing_cap = math.degrees(
        2.0 * math.acos(1.0 - row_tolerance / pitch_mm)
    )
    max_step_deg = max(0.25, min(configured_cap, spacing_cap))
    return {
        "positions": tuple(positions),
        "thetas": tuple(thetas),
        "pitch_mm": pitch_mm,
        "max_step_deg": max_step_deg,
        "angle_deg": math.degrees(
            math.atan2(along_axis[1], along_axis[0])
        ),
    }


def _row_pitch(row_across):
    index_gaps = []
    ordered_rows = sorted(row_across)
    for first, second in zip(ordered_rows, ordered_rows[1:]):
        row_delta = second - first
        if row_delta > 0:
            pitch = abs(row_across[second] - row_across[first]) / row_delta
            if pitch > 1e-9:
                index_gaps.append(pitch)
    return _median(index_gaps)


def _extend_guide(guide_screen, low_along, high_along):
    if not guide_screen:
        return
    if guide_screen[0][0] > low_along:
        guide_screen.insert(0, (low_along, guide_screen[0][1]))
    if guide_screen[-1][0] < high_along:
        guide_screen.append((high_along, guide_screen[-1][1]))


def _deduplicate_along(guide, thetas, along_axis):
    positions = []
    values = []
    for point, theta in zip(guide, thetas):
        along = _project(point, along_axis)
        if positions and abs(along - positions[-1]) <= 1e-9:
            values[-1] = theta
        else:
            positions.append(along)
            values.append(theta)
    return positions, values


def wave_row_thetas(path, schedule):
    """Sample one shared Wave-row schedule at every path point."""
    along_axis, _across_axis = _screen_axes_from_angle(
        schedule["angle_deg"]
    )
    positions = schedule["positions"]
    values = schedule["thetas"]
    thetas = []
    for point in path:
        along = _project(point, along_axis)
        right = bisect.bisect_right(positions, along)
        if right <= 0:
            theta = values[0]
        elif right >= len(positions):
            theta = values[-1]
        else:
            left = right - 1
            span = positions[right] - positions[left]
            fraction = (
                0.0
                if span <= 1e-12
                else (along - positions[left]) / span
            )
            theta = values[left] + fraction * (values[right] - values[left])
        thetas.append(theta)
    return thetas
