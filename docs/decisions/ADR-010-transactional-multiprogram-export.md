# ADR-010: Publish multi-program G-code sets transactionally

- Status: accepted and implemented
- Date: 2026-11-25

## Context

CMYK output is one physical print made from four separate G-code programs in
Y/M/C/K order plus a set manifest. The files must share one artwork frame,
placement, calibration identity, and motion contract. Their hashes and
per-program verification results are the evidence that the set belongs
together.

Sequential direct writes make that contract fragile. A permission error, full
disk, interrupted process, or late manifest failure can leave a mixture of old
and new ink programs. Reporting such a directory as a successful four-file
export would invite a partial or mismatched physical plot.

## Decision

The host publishes all files in a multi-program set through one logical
transaction:

1. Validate every target name and reject duplicates.
2. Write every program and companion manifest to temporary files beside their
   final targets, flush each file, and synchronize it to disk.
3. Move any existing targets to same-directory backups.
4. Atomically replace each target.
5. Delete backups only after every replacement succeeds.
6. On an exception, remove newly installed files and restore the previous
   complete set before reporting failure.

The export call returns success only after the complete commit. It does not
return a partially written list. The CMYK tab supplies the manifest in the same
transaction and records hashes computed from the exact bytes staged for the
programs.

The logical set also carries one common identity. Scale, artwork placement,
page frame, theta ratio and mode, feed/travel limits, and the full compensation
profile must match across all analyzed inks. Guided CMYK requires all four
channels; it does not preserve a stale unchecked channel from Advanced
settings.

## Consequences

- A failed export no longer destroys an earlier valid set when the filesystem
  permits rollback.
- The output manifest can state that it was published with the programs rather
  than written later as optional metadata.
- Export uses additional temporary disk space equal to the complete set while
  it is being staged.
- Cross-file atomicity is implemented by staged replacements and rollback, not
  by one filesystem-wide primitive. A process or operating-system crash during
  the commit window can leave same-directory backup files that require manual
  recovery.
- The G-code format, machine coordinate contract, M3/M5 behavior, controller
  limits, registration procedure, and print order do not change.

## Verification

- Successful publication writes programs and manifest together.
- A forced staging failure leaves every previous target byte-identical.
- A forced commit failure restores every previous target.
- Duplicate and path-escaping labels are rejected.
- Guided defaults restore all four output channels.
- Differing per-ink frame identities block the complete set.

This decision is host-side behavior. It does not provide physical
registration, pen alignment, color, density, or machine-motion validation.
