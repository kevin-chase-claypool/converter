# Lab Note: 2026-10-25 - P116 macro deployment

## Objective

Determine why the ioSender **PEN UP + PARK** button reports a failure even
though its stored command is `G65 P116`.

## Configuration

- Hardware: installed RP23U5XBB V1.01, current X/Y/A machine and production
  integrated toolhead.
- Firmware: grblHAL `1.1f.20260908`, filesystem-macro plugin v0.24.
- ioSender: 2.0.47 connected over Ethernet at `10.10.10.2:23`.
- ioSender macro: `PEN UP + PARK`, confirmation enabled,
  code `G65 P116`.
- Controller macro source:
  `firmware/grblhal/macros/P116.macro`, 2,543 bytes, SHA-256
  `E08313848941C7520D1733153C2C1B5A1382C732FF8C71965B52696A7F742338`.

## Commands and configuration used

```text
ioSender macro: G65 P116

Observed controller response:
[MSG:Stop]
...
error:84 - Could not open file.

FTP control endpoint: ftp://10.10.10.2/
User: grblHAL
Binary upload: P116.macro
FTP completion response: 226 Closing data connection
```

The read-only root listing is retained in
[`controller-manifest-2026-10-25.txt`](../../../firmware/grblhal/macros/controller-manifest-2026-10-25.txt).

## Procedure

1. Capture the ioSender console response after pressing **PEN UP + PARK**.
2. List the controller filesystem over the independent FTP service.
3. Confirm whether `P116.macro` exists.
4. Validate all repository macros with `tools\check_macros.py`.
5. Upload the repository's `P116.macro` over binary FTP.
6. List the controller filesystem again and compare the deployed file size.

## Results

- Before upload, `P100.macro` through `P115.macro` were present, but
  `P116.macro` was absent.
- The controller response was exactly `error:84 - Could not open file`, so the
  ioSender button was transmitting the correct command.
- `tools\check_macros.py` reported all 17 repository macros parse-safe.
- The binary upload completed with FTP status 226.
- The post-upload listing reports `P116.macro` at 2,543 bytes, equal to the
  repository file.
- ioSender was reopened, connected to `10.10.10.2:23`, reported `IDLE`, and
  still shows both restored macro buttons.

## Difficulties and corrective actions

- The P116 source existed in the repository but had not been deployed to the
  controller filesystem after it was added.
- The first conclusion that the restored button had an empty/invalid command
  was disproved by both the ioSender `App.config` and console: the command was
  correct and the controller raised file-open error 84.
- FTP download timed out from this firmware while a second data transfer was
  attempted, so the deployed copy could not be downloaded for an independent
  SHA comparison. The successful upload response and exact remote/local byte
  count establish deployment presence, not execution acceptance.

## Interpretation

The missing controller file explains the macro failure completely. P116 is now
present, but its complete homing/parking sequence has still not completed a
clean supervised run on this machine.

## Decisions and next action

With the bed and gantry clear and the operator ready at the power cutoff, press
**PEN UP + PARK** once. Require all three phases to complete:

1. P115 proves the pen is clear.
2. The toolhead reaches GP2 during the bounded full retract.
3. P111 homes X/Y and the final G53 park completes without a limit alarm.

Capture the console result. If the sequence fails, stop and inspect the first
message after the button press rather than pressing it repeatedly.
