# Force calibration results package

## Purpose

This is the required evidence package for the Pico 2 / Pro Micro force
calibration. It supplies reproducible figures for the final course paper while
preserving the unmodified measurement record from the installed toolhead load
cell and the 5 N reference sensor.

The force traces originate at the Pico: CS1238 #1 supplies the toolhead raw
count and ADC0 supplies the INA101/reference raw value. The Pro Micro does not
provide a competing sensor timestamp. Instead, its `MOTION_ACTIVE` output is
captured on Pico `GP14`, placing every actuator start/end edge on the same
monotonic Pico time base as both sensor channels.

## Required run package

Store each run in a dated, automatically named directory. Do not edit any raw
file after capture.

| File | Required content | Purpose |
|---|---|---|
| `samples.csv` | `toolhead_time_us`, `toolhead_cs1238_raw`, `reference_time_us`, `reference_adc_raw` | Primary raw measurements. |
| `events.csv` | `pico_time_us`, `event`, `marker_level` | Pico-timestamped Pro Micro `MOTION_ACTIVE` edges; `event` is `motion_start` or `motion_end`. |
| `promicro-command.log` | PC wall-clock time, sent command, received reply, controller build ID | Audit trail only; its times are not used to align force measurements. |
| `metadata.json` | Run ID, operator, sensor IDs, CS1238 configuration, INA101 rails/gain, Pico/Pro Micro builds, fixture description, and safety limits | Reproducibility and paper caption source. |
| `analysis/` | Versioned analysis script, figure files, and a short analysis summary | Allows each plotted result to be regenerated from the raw run package. |

The Pico time origin is `t = 0` at `TEST_START`. PC wall-clock time identifies
the experiment; it is never substituted for Pico time.

## Required figures

Each figure must identify the run ID, sensor configuration, and units. Export
both SVG or PDF (paper-quality vector form) and PNG (easy review form) from a
versioned analysis script; do not manually redraw plots for the paper.

1. **Time-aligned raw overlay.** Plot toolhead CS1238 raw count and reference
   ADC raw count against Pico time. Use two clearly labelled vertical axes or
   two aligned panels; raw ADC counts and CS1238 counts are not interchangeable.
   Add a bottom event lane showing each Pico-timestamped `MOTION_ACTIVE` HIGH
   interval. This is the overlay of Pico measurements and Pro Micro-actuation
   state.
2. **Reference-force / toolhead-count overlay.** After independently
   calibrating the reference channel, plot reference force (N, with grams-force
   only if helpful) against time beside or against the toolhead CS1238 raw
   count. Retain separate y axes and show the same Pro Micro motion-event lane.
   Do not label the toolhead axis as force until its calibration fit is accepted.
3. **Transfer relationship and residuals.** Pair each reference-force sample
   with the closest-in-time CS1238 sample, report their time difference, and
   plot reference force versus CS1238 raw count. Distinguish increasing-force
   and decreasing-force paths. Include residuals for every candidate model;
   a straight-line fit is a result to test, not an assumption.
4. **Timestamp/sample-quality figure.** Plot or summarize consecutive CS1238
   timestamp intervals, delivered sample rate, missing records, and the marker
   edge timing. This establishes whether the nominal 640 SPS setting was
   actually delivered.

For each overlay, mark the no-contact baseline, first contact, peak force,
and release only when those events are determined from the recorded data.
Caption every figure with the mechanical fixture, pulse sequence, and whether
the trace is an increasing or decreasing force path.

## Paper result table

For each accepted or failed run, record: run ID; date; CS1238 rate; measured
samples/s; reference-sensor calibration version; INA101 rail voltages and gain
setting; tool identity; pulse sequence; peak/reference force; no-contact and
contact noise; approach/release hysteresis; candidate-model coefficients with
units; residual/error statistics; and the reason for acceptance, rejection, or
repeat.

No moving average belongs in the preserved raw file. If a display smoothing
method is used in a figure, state the method and window in the caption and
provide the corresponding unsmoothed figure or data trace.

## Acceptance boundary

The figures document E-09C; they do not by themselves authorize production
force control. A calibration relationship can enter toolhead firmware only
after the reference calibration, raw data, fit/residual review, hysteresis
assessment, and relevant safety tests are recorded in a dated lab note.
