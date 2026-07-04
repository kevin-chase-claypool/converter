"""Generate reference CAD for the Tecmojo 14130201 sliding rack shelf.

Published dimensions are taken from the current Tecmojo manual/specification
and the Amazon listing for ASIN B0BMW9V6MS. Unpublished sheet, rail, slot, and
accessory dimensions are scaled from the product images and are intentionally
kept as named constants for later replacement with physical measurements.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cadquery as cq


# Manufacturer-published dimensions, millimeters.
RACK_WIDTH = 482.6
BODY_HEIGHT = 44.45
TRAY_DEPTH = 350.0
MIN_MOUNT_DEPTH = 350.0
MAX_MOUNT_DEPTH = 500.0

# EIA-310-derived interface geometry.
RACK_OPENING = 450.85
EAR_WIDTH = (RACK_WIDTH - RACK_OPENING) / 2.0
EAR_THICKNESS = 1.5

# Image-derived geometry. These values require physical verification.
SHEET_THICKNESS = 1.5
TRAY_WIDTH = 430.0
TRAY_X = (RACK_WIDTH - TRAY_WIDTH) / 2.0
TRAY_TOP_Z = BODY_HEIGHT - SHEET_THICKNESS
SIDE_FLANGE_BOTTOM_Z = 12.0
FRONT_SUPPORT_LENGTH = TRAY_DEPTH
REAR_SUPPORT_LENGTH = 250.0
SLIDE_LENGTH = 330.0


def box(
    length_x: float,
    length_y: float,
    length_z: float,
    x: float,
    y: float,
    z: float,
) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(length_x, length_y, length_z, centered=(False, False, False))
        .translate((x, y, z))
    )


def cylinder_cutter(
    radius: float,
    length: float,
    origin: tuple[float, float, float],
    direction: tuple[float, float, float],
) -> cq.Workplane:
    solid = cq.Solid.makeCylinder(
        radius,
        length,
        cq.Vector(*origin),
        cq.Vector(*direction),
    )
    return cq.Workplane("XY").newObject([solid])


def make_mount_ear(x: float, y: float, mount_depth: float) -> cq.Workplane:
    ear = box(EAR_WIDTH, EAR_THICKNESS, BODY_HEIGHT, x, y, 0.0)
    center_x = x + EAR_WIDTH / 2.0
    slot_centers = [(center_x, 8.2), (center_x, BODY_HEIGHT - 8.2)]
    slots = cq.Workplane("XZ").pushPoints(slot_centers).slot2D(10.0, 5.5).extrude(4.0)
    cutter_y = 2.0 if y == 0.0 else mount_depth + 2.0
    return ear.cut(slots.translate((0.0, cutter_y, 0.0)))


def make_front_support(left: bool) -> cq.Workplane:
    y = EAR_THICKNESS
    length = FRONT_SUPPORT_LENGTH - EAR_THICKNESS
    z0 = 4.5
    height = 35.5
    lip = 14.0

    if left:
        x_outer = EAR_WIDTH
        support = box(SHEET_THICKNESS, length, height, x_outer, y, z0)
        support = support.union(box(lip, length, SHEET_THICKNESS, x_outer, y, z0))
        support = support.union(
            box(lip, length, SHEET_THICKNESS, x_outer, y, z0 + height - SHEET_THICKNESS)
        )
        hole_x = EAR_WIDTH - 1.0
    else:
        x_outer = RACK_WIDTH - EAR_WIDTH - SHEET_THICKNESS
        support = box(SHEET_THICKNESS, length, height, x_outer, y, z0)
        support = support.union(
            box(lip, length, SHEET_THICKNESS, x_outer - lip + SHEET_THICKNESS, y, z0)
        )
        support = support.union(
            box(
                lip,
                length,
                SHEET_THICKNESS,
                x_outer - lip + SHEET_THICKNESS,
                y,
                z0 + height - SHEET_THICKNESS,
            )
        )
        hole_x = x_outer - 1.0

    for hole_y in (268.0, 298.0, 328.0):
        support = support.cut(
            cylinder_cutter(2.4, 4.0, (hole_x, hole_y, BODY_HEIGHT / 2.0), (1, 0, 0))
        )
    return support


def make_rear_support(left: bool, mount_depth: float) -> cq.Workplane:
    y = mount_depth - REAR_SUPPORT_LENGTH
    length = REAR_SUPPORT_LENGTH - EAR_THICKNESS
    z0 = 6.0
    height = 32.5
    lip = 11.0

    if left:
        x_outer = EAR_WIDTH + 2.2
        support = box(SHEET_THICKNESS, length, height, x_outer, y, z0)
        support = support.union(box(lip, length, SHEET_THICKNESS, x_outer, y, z0))
        support = support.union(
            box(lip, length, SHEET_THICKNESS, x_outer, y, z0 + height - SHEET_THICKNESS)
        )
        hole_x = x_outer - 1.0
    else:
        x_outer = RACK_WIDTH - EAR_WIDTH - 2.2 - SHEET_THICKNESS
        support = box(SHEET_THICKNESS, length, height, x_outer, y, z0)
        support = support.union(
            box(lip, length, SHEET_THICKNESS, x_outer - lip + SHEET_THICKNESS, y, z0)
        )
        support = support.union(
            box(
                lip,
                length,
                SHEET_THICKNESS,
                x_outer - lip + SHEET_THICKNESS,
                y,
                z0 + height - SHEET_THICKNESS,
            )
        )
        hole_x = x_outer - 1.0

    for hole_y in (mount_depth - 210.0, mount_depth - 180.0):
        support = support.cut(
            cylinder_cutter(2.4, 4.0, (hole_x, hole_y, BODY_HEIGHT / 2.0), (1, 0, 0))
        )
    return support


def make_slide_member(left: bool) -> cq.Workplane:
    y = 5.0
    z0 = 8.0
    height = 29.0
    lip = 8.5

    if left:
        x_outer = TRAY_X + SHEET_THICKNESS
        slide = box(1.2, SLIDE_LENGTH, height, x_outer, y, z0)
        slide = slide.union(box(lip, SLIDE_LENGTH, 1.2, x_outer, y, z0))
        slide = slide.union(box(lip, SLIDE_LENGTH, 1.2, x_outer, y, z0 + height - 1.2))
        hole_x = x_outer - 1.0
    else:
        x_outer = TRAY_X + TRAY_WIDTH - SHEET_THICKNESS - 1.2
        slide = box(1.2, SLIDE_LENGTH, height, x_outer, y, z0)
        slide = slide.union(box(lip, SLIDE_LENGTH, 1.2, x_outer - lip + 1.2, y, z0))
        slide = slide.union(
            box(lip, SLIDE_LENGTH, 1.2, x_outer - lip + 1.2, y, z0 + height - 1.2)
        )
        hole_x = x_outer - 1.0

    for hole_y in (42.0, 122.0, 202.0, 282.0):
        slide = slide.cut(
            cylinder_cutter(1.8, 4.0, (hole_x, hole_y, BODY_HEIGHT / 2.0), (1, 0, 0))
        )
    return slide


def make_tray() -> cq.Workplane:
    tray = box(TRAY_WIDTH, TRAY_DEPTH, SHEET_THICKNESS, TRAY_X, 0.0, TRAY_TOP_Z)
    tray = tray.union(box(TRAY_WIDTH, SHEET_THICKNESS, BODY_HEIGHT, TRAY_X, 0.0, 0.0))
    tray = tray.union(
        box(
            SHEET_THICKNESS,
            TRAY_DEPTH,
            BODY_HEIGHT - SIDE_FLANGE_BOTTOM_Z,
            TRAY_X,
            0.0,
            SIDE_FLANGE_BOTTOM_Z,
        )
    )
    tray = tray.union(
        box(
            SHEET_THICKNESS,
            TRAY_DEPTH,
            BODY_HEIGHT - SIDE_FLANGE_BOTTOM_Z,
            TRAY_X + TRAY_WIDTH - SHEET_THICKNESS,
            0.0,
            SIDE_FLANGE_BOTTOM_Z,
        )
    )
    tray = tray.union(
        box(
            TRAY_WIDTH,
            SHEET_THICKNESS,
            BODY_HEIGHT - SIDE_FLANGE_BOTTOM_Z,
            TRAY_X,
            TRAY_DEPTH - SHEET_THICKNESS,
            SIDE_FLANGE_BOTTOM_Z,
        )
    )

    vent_points: list[tuple[float, float]] = []
    first_x = TRAY_X + 35.7
    x_pitch = 35.0
    first_y = 45.0
    y_pitch = 29.5
    for row in range(10):
        columns = 11 if row % 2 == 0 else 10
        row_offset = 0.0 if row % 2 == 0 else x_pitch / 2.0
        for column in range(columns):
            vent_points.append(
                (first_x + row_offset + column * x_pitch, first_y + row * y_pitch)
            )

    vent_cutters = (
        cq.Workplane("XY")
        .pushPoints(vent_points)
        .slot2D(22.0, 5.0)
        .extrude(4.0)
        .translate((0.0, 0.0, TRAY_TOP_Z - 1.0))
    )
    tray = tray.cut(vent_cutters)

    face_slot_points = [
        (83.0 + column * 44.5, z)
        for column in range(8)
        for z in (13.5, 30.5)
    ]
    face_slot_cutters = (
        cq.Workplane("XZ")
        .pushPoints(face_slot_points)
        .slot2D(25.0, 6.0)
        .extrude(4.0)
        .translate((0.0, 2.0, 0.0))
    )
    tray = tray.cut(face_slot_cutters)

    for cable_x in (TRAY_X + 21.5, TRAY_X + TRAY_WIDTH - 21.5):
        tray = tray.cut(
            cylinder_cutter(10.5, 4.0, (cable_x, -1.0, BODY_HEIGHT / 2.0), (0, 1, 0))
        )

    for flange_x, direction in (
        (TRAY_X - 1.0, (1, 0, 0)),
        (TRAY_X + TRAY_WIDTH + 1.0, (-1, 0, 0)),
    ):
        for hole_y in (36.0, 116.0, 196.0, 276.0):
            tray = tray.cut(
                cylinder_cutter(
                    2.0,
                    4.0,
                    (flange_x, hole_y, BODY_HEIGHT / 2.0),
                    direction,
                )
            )
    return tray


def make_anti_slip_stop(x: float, y: float) -> cq.Workplane:
    stop = box(20.0, 14.0, 1.5, x - 10.0, y - 7.0, BODY_HEIGHT)
    stop = stop.union(box(20.0, 1.8, 18.0, x - 10.0, y + 5.2, BODY_HEIGHT))
    return stop


def make_assembly(mount_depth: float) -> tuple[cq.Assembly, dict[str, cq.Workplane]]:
    if not MIN_MOUNT_DEPTH <= mount_depth <= MAX_MOUNT_DEPTH:
        raise ValueError(
            f"mount depth must be {MIN_MOUNT_DEPTH:g}-{MAX_MOUNT_DEPTH:g} mm"
        )

    parts = {
        "sliding_shelf": make_tray(),
        "left_slide_member": make_slide_member(True),
        "right_slide_member": make_slide_member(False),
        "left_front_support": make_front_support(True),
        "right_front_support": make_front_support(False),
        "left_rear_support": make_rear_support(True, mount_depth),
        "right_rear_support": make_rear_support(False, mount_depth),
        "left_front_ear": make_mount_ear(0.0, 0.0, mount_depth),
        "right_front_ear": make_mount_ear(RACK_WIDTH - EAR_WIDTH, 0.0, mount_depth),
        "left_rear_ear": make_mount_ear(
            0.0, mount_depth - EAR_THICKNESS, mount_depth
        ),
        "right_rear_ear": make_mount_ear(
            RACK_WIDTH - EAR_WIDTH,
            mount_depth - EAR_THICKNESS,
            mount_depth,
        ),
        "left_anti_slip_stop": make_anti_slip_stop(TRAY_X + 130.0, 126.0),
        "right_anti_slip_stop": make_anti_slip_stop(
            TRAY_X + TRAY_WIDTH - 130.0, 126.0
        ),
    }

    assembly = cq.Assembly(
        name=f"Tecmojo_14130201_{mount_depth:g}mm_mount_depth"
    )
    for name, part in parts.items():
        color = cq.Color(0.11, 0.12, 0.13)
        if "slide_member" in name:
            color = cq.Color(0.18, 0.19, 0.20)
        elif "support" in name:
            color = cq.Color(0.14, 0.15, 0.16)
        assembly.add(part, name=name, color=color)
    return assembly, parts


def render_preview(parts: dict[str, cq.Workplane], output_path: Path) -> None:
    import vtk

    compound = cq.Compound.makeCompound([part.val() for part in parts.values()])
    stl_path = output_path.with_suffix(".preview.stl")
    cq.exporters.export(compound, str(stl_path), exportType="STL", tolerance=0.08)

    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(stl_path))
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.13, 0.15, 0.18)
    actor.GetProperty().SetSpecular(0.25)
    actor.GetProperty().SetSpecularPower(18.0)

    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor)
    renderer.SetBackground(0.95, 0.96, 0.98)
    reader.Update()
    bounds = reader.GetOutput().GetBounds()
    center_x = (bounds[0] + bounds[1]) / 2.0
    center_y = (bounds[2] + bounds[3]) / 2.0
    center_z = (bounds[4] + bounds[5]) / 2.0
    span = max(bounds[1] - bounds[0], bounds[3] - bounds[2])
    camera = renderer.GetActiveCamera()
    camera.SetFocalPoint(center_x, center_y, center_z)
    camera.SetPosition(
        center_x + span * 1.15,
        center_y - span * 1.55,
        center_z + span * 0.95,
    )
    camera.SetViewUp(0.0, 0.0, 1.0)
    camera.ParallelProjectionOn()
    renderer.ResetCamera()
    camera.Zoom(1.08)

    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetSize(1400, 1000)
    window.AddRenderer(renderer)
    window.Render()

    capture = vtk.vtkWindowToImageFilter()
    capture.SetInput(window)
    capture.SetScale(1)
    capture.SetInputBufferTypeToRGBA()
    capture.ReadFrontBufferOff()
    capture.Update()

    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(output_path))
    writer.SetInputConnection(capture.GetOutputPort())
    writer.Write()
    stl_path.unlink(missing_ok=True)


def export_configuration(output_dir: Path, mount_depth: float) -> None:
    assembly, parts = make_assembly(mount_depth)
    depth_label = int(round(mount_depth))
    stem = f"tecmojo-14130201-{depth_label}mm"
    step_path = output_dir / f"{stem}.step"
    preview_path = output_dir / f"{stem}-preview.png"

    assembly.save(str(step_path), exportType="STEP", mode="default")
    render_preview(parts, preview_path)

    body_shapes = [part.val() for name, part in parts.items() if "anti_slip" not in name]
    body_box = cq.Compound.makeCompound(body_shapes).BoundingBox()
    full_box = cq.Compound.makeCompound([part.val() for part in parts.values()]).BoundingBox()
    print(
        f"{step_path}: body "
        f"{body_box.xlen:.2f} x {body_box.ylen:.2f} x {body_box.zlen:.2f} mm; "
        f"with optional stops height {full_box.zlen:.2f} mm"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/hardware/cad"),
        help="directory for STEP files and PNG previews",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    export_configuration(args.output_dir, MIN_MOUNT_DEPTH)
    export_configuration(args.output_dir, MAX_MOUNT_DEPTH)


if __name__ == "__main__":
    main()
