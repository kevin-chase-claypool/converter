"""Transactional publishing for multi-program G-code sets."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


_REJECTED_LABEL_CHARS = frozenset('<>:"/\\|?*')
_GCODE_SUFFIXES = (".gcode", ".nc", ".tap")


class ProgramSetExportError(OSError):
    """A complete program set could not be published."""


def program_set_stem(base_path):
    """Return a set base without its final G-code extension."""
    text = os.fspath(base_path).strip()
    if not text:
        raise ValueError("A G-code destination is required.")
    lowered = text.lower()
    for suffix in _GCODE_SUFFIXES:
        if lowered.endswith(suffix):
            return text[: -len(suffix)]
    return text


def validate_program_label(label):
    """Reject labels that cannot safely become one filename component."""
    text = str(label).strip()
    if (
        not text
        or text in (".", "..")
        or text[-1] in (" ", ".")
        or any(
            character in _REJECTED_LABEL_CHARS
            or ord(character) < 32
            for character in text
        )
    ):
        raise ValueError(f"Unsafe program label: {label!r}")
    return text


def program_set_paths(base_path, labels):
    """Return the target paths for one named program set."""
    stem = program_set_stem(base_path)
    paths = []
    for label in labels:
        safe_label = validate_program_label(label)
        paths.append(Path(f"{stem}-{safe_label}.gcode"))
    _validate_unique_paths(paths)
    return paths


def _validate_unique_paths(paths):
    seen = set()
    for path in paths:
        key = os.path.normcase(os.path.abspath(os.fspath(path)))
        if key in seen:
            raise ValueError(f"Duplicate program-set target: {path}")
        seen.add(key)


def _payload_bytes(payload):
    if isinstance(payload, bytes):
        return payload
    if isinstance(payload, str):
        return payload.encode("utf-8")
    raise TypeError("Program-set file contents must be text or bytes.")


def _stage_file(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    return temporary_path


def _backup_path(path):
    descriptor, name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".backup",
        dir=path.parent,
    )
    os.close(descriptor)
    backup = Path(name)
    backup.unlink()
    return backup


def write_file_set_transaction(files):
    """Publish every ``(path, content)`` pair as one logical transaction.

    All contents are first written and flushed to temporary files beside their
    targets. Only then are targets replaced. Existing targets are moved to
    same-directory backups and restored if any commit step fails.
    """
    prepared = []
    for path, content in files:
        target = Path(path)
        payload = _payload_bytes(content)
        if target.exists() and not target.is_file():
            raise ProgramSetExportError(
                f"Program-set target is not a file: {target}"
            )
        prepared.append((target, payload))
    if not prepared:
        raise ValueError("A program-set transaction needs at least one file.")
    _validate_unique_paths(path for path, _content in prepared)

    staged = {}
    try:
        for target, payload in prepared:
            staged[target] = _stage_file(target, payload)
    except Exception as exc:
        for temporary_path in staged.values():
            temporary_path.unlink(missing_ok=True)
        if isinstance(exc, OSError):
            raise ProgramSetExportError(
                f"Could not stage the complete program set: {exc}"
            ) from exc
        raise

    backups = {}
    committed = []
    preserve_backups = False
    try:
        for target, _payload in prepared:
            if target.exists():
                backup = _backup_path(target)
                os.replace(target, backup)
                backups[target] = backup
            os.replace(staged[target], target)
            committed.append(target)
    except Exception as exc:
        rollback_errors = []
        for target in reversed(committed):
            try:
                target.unlink(missing_ok=True)
            except OSError as rollback_error:
                rollback_errors.append(str(rollback_error))
        for target in reversed(committed):
            backup = backups.get(target)
            if backup is None:
                continue
            try:
                os.replace(backup, target)
                backups.pop(target, None)
            except OSError as rollback_error:
                rollback_errors.append(str(rollback_error))
        for target, backup in list(backups.items()):
            if backup.exists():
                try:
                    os.replace(backup, target)
                    backups.pop(target, None)
                except OSError as rollback_error:
                    rollback_errors.append(str(rollback_error))
        preserve_backups = bool(rollback_errors)
        detail = (
            f" Could not restore: {'; '.join(rollback_errors)}"
            if rollback_errors
            else " Previous files were restored."
        )
        raise ProgramSetExportError(
            f"Program-set publish failed: {exc}.{detail}"
        ) from exc
    finally:
        for temporary_path in staged.values():
            temporary_path.unlink(missing_ok=True)
        if not preserve_backups:
            for backup in backups.values():
                backup.unlink(missing_ok=True)

    return [path for path, _payload in prepared]
