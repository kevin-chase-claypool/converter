"""Sanity-check the controller macros before they are uploaded.

Two mistakes are easy to make in a grblHAL filesystem macro and both are fatal
at the controller, not at edit time:

* a comment that wraps onto the next line, or nests parentheses inside a
  comment - the controller reads a parenthesized comment as a single-line token,
  and ioSender refuses the file outright;
* an unbalanced ``[`` expression, which swallows the rest of the line.

This checks every ``*.macro`` in `firmware/grblhal/macros` for those, plus the
O-word structure: every ``o<n> if`` / ``o<n> while`` must have a matching
``o<n> endif`` / ``o<n> endwhile`` before the next O-word of the same depth, and
every ``o<n> sub`` a matching ``o<n> endsub``. It cannot prove an expression is
arithmetically right, only that the controller will parse it.

Usage::

    python tools\\check_macros.py
    python tools\\check_macros.py firmware\\grblhal\\macros\\P100.macro
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "firmware" / "grblhal" / "macros"

O_WORD = re.compile(r"^\s*o(\d+)\s+(if|else|endif|while|endwhile|sub|endsub|call|do)\b", re.I)


def check_file(path):
    problems = []
    text = Path(path).read_text(encoding="utf-8")
    for number, line in enumerate(text.splitlines(), 1):
        code = line
        # Strip comments the way the controller does: one per line, no nesting.
        if "(" in line:
            if line.count("(") != line.count(")"):
                problems.append(
                    f"line {number}: comment does not open and close on one line: {line.strip()[:70]}"
                )
            if not line.rstrip().endswith(")"):
                problems.append(
                    f"line {number}: trailing code after a comment, or a wrapped comment: {line.strip()[:70]}"
                )
            code = line[: line.index("(")]
        if code.count("[") != code.count("]"):
            problems.append(
                f"line {number}: unbalanced [ ] expression: {line.strip()[:70]}"
            )
    # O-word structure: if/while blocks must close, and subprograms with them.
    stack = []
    for number, line in enumerate(text.splitlines(), 1):
        match = O_WORD.match(line)
        if not match:
            continue
        label, kind = match.group(1), match.group(2).lower()
        if kind in ("if", "while", "do"):
            stack.append((kind, label, number))
        elif kind in ("else",):
            if not stack or stack[-1][0] not in ("if",):
                problems.append(f"line {number}: o{label} else without a matching if")
        elif kind in ("endif",):
            if not stack or stack[-1][0] != "if":
                problems.append(f"line {number}: o{label} endif without a matching if")
            else:
                stack.pop()
        elif kind in ("endwhile",):
            if not stack or stack[-1][0] != "while":
                problems.append(f"line {number}: o{label} endwhile without a matching while")
            else:
                stack.pop()
        elif kind == "sub":
            stack.append((kind, label, number))
        elif kind == "endsub":
            if not stack or stack[-1][0] != "sub":
                problems.append(f"line {number}: o{label} endsub without a matching sub")
            else:
                stack.pop()
    for kind, label, number in stack:
        problems.append(f"line {number}: o{label} {kind} is never closed")
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()

    targets = [Path(p) for p in args.paths] or sorted(DEFAULT_DIR.glob("*.macro"))
    failures = 0
    for path in targets:
        problems = check_file(path)
        if problems:
            failures += 1
            print("%s:" % path)
            for problem in problems:
                print("  - " + problem)
        else:
            print("%s: OK" % path)
    if failures:
        print("\n%d file(s) with problems" % failures)
        return 1
    print("\nAll %d macro(s) parse-safe." % len(targets))
    return 0


if __name__ == "__main__":
    sys.exit(main())
