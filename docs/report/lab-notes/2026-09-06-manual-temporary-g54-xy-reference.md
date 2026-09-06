# Manual temporary G54 XY reference - 2026-09-06

## Objective

Create a manually aligned, pen-corrected **temporary** G54 X/Y reference for
pen-free machine checks while P100 center-raster and A-index commissioning
remain locked.

## Configuration and measurements

- Controller: RP23CNC/RP23U5XBB V1.01 through ioSender, after successful X/Y
  physical homing.
- Center-magnet alignment of the TMAG sensing point:

  ```text
  MPos X=-232.900, Y=-283.300
  ```

- Alignment of the pen-axis centerline over the same center magnet:

  ```text
  MPos X=-232.900, Y=-253.200
  ```

- Installed vector, using `sensor_to_pen = pen - TMAG`:

  ```text
  sensor_to_pen_x =  0.000 mm
  sensor_to_pen_y = -30.100 mm
  ```

  The pen axis is 30.1 mm south of the TMAG sensing point in machine
  coordinates.

## Procedure and result

The pen-axis centerline was held over the center magnet and the following was
accepted by the controller:

```gcode
G21
G90
G54
G10 L20 P1 X0 Y0
```

The resulting status was:

```text
<Idle|MPos:-232.900,-253.200,0.000,0.000|...|WCO:-232.900,-253.200,0.000,720.000>
```

The matching X/Y `MPos` and `WCO` values establish current G54 X/Y work
position as zero. A was intentionally omitted and remains at its pre-existing,
unregistered work offset.

## Scope and limitations

- This is a manual, visual, pen-free reference, not a P100 center-raster pass.
- It does not validate TMAG thresholding, centroid arithmetic, approach
  repeatability, the contact-ready protocol, sensor-to-pen measurement
  uncertainty, or G54 A0.
- P100 must overwrite this temporary G54 reference before production drawing.

## Related records

- [`M-07 X/Y physical homing`](2026-09-06-m-07-xy-physical-homing.md)
- [`HOMING_AND_MAGNETIC_CALIBRATION.md`](../../../firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md)
- [`TEST_PLAN.md`](../../testing/TEST_PLAN.md), M-08 and M-09
