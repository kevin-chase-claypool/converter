"""Generate and validate documentation indexes."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CHANGES = DOCS / "changes"
CATEGORIES = {
    "windows-software": "Windows Software Changes",
    "rp23cnc-software": "RP23CNC Software Changes",
    "hardware": "Hardware Changes",
}
ENGINEERING_LOG = DOCS / "project" / "ENGINEERING_LOG.md"
CHANGE_BEGIN = "<!-- BEGIN GENERATED CHANGES -->"
CHANGE_END = "<!-- END GENERATED CHANGES -->"
LOG_BEGIN = "<!-- BEGIN GENERATED TOPIC INDEX -->"
LOG_END = "<!-- END GENERATED TOPIC INDEX -->"
LOG_TOPICS = (
    ("Windows software", {"software"}),
    ("RP23CNC and machine software", {"firmware"}),
    ("Hardware and wiring", {"hardware", "wiring"}),
    ("Testing and verification", {"test"}),
    ("Decisions and architecture", {"decision"}),
    ("Documentation and project organization", {"documentation", "project management"}),
)
INDEXED_LOG_CATEGORIES = set().union(*(categories for _, categories in LOG_TOPICS))


def parse_front_matter(path: Path) -> dict[str, object]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path.relative_to(ROOT)}: missing front matter")
    try:
        closing = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError(f"{path.relative_to(ROOT)}: unterminated front matter") from exc

    data: dict[str, object] = {}
    active_list: str | None = None
    for line in lines[1:closing]:
        if line.startswith("  - ") and active_list:
            value = line[4:].strip()
            cast = data.setdefault(active_list, [])
            assert isinstance(cast, list)
            cast.append(value)
            continue
        match = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if not match:
            continue
        key, value = match.groups()
        if value:
            data[key] = value
            active_list = None
        else:
            data[key] = []
            active_list = key

    title = next(
        (line[2:].strip() for line in lines[closing + 1 :] if line.startswith("# ")),
        path.stem,
    )
    data["title"] = title
    data["path"] = path
    return data


def load_notes() -> list[dict[str, object]]:
    notes = []
    seen_ids: dict[str, Path] = {}
    required = {"id", "date", "category", "affected_categories", "status", "tags"}
    for category in CATEGORIES:
        for path in sorted((CHANGES / category).rglob("*.md")):
            if path.name == "README.md":
                continue
            note = parse_front_matter(path)
            missing = sorted(required - note.keys())
            if missing:
                raise ValueError(
                    f"{path.relative_to(ROOT)}: missing {', '.join(missing)}"
                )
            note_id = str(note["id"])
            if note_id in seen_ids:
                raise ValueError(
                    f"duplicate change ID {note_id}: "
                    f"{seen_ids[note_id].relative_to(ROOT)} and {path.relative_to(ROOT)}"
                )
            seen_ids[note_id] = path
            affected = note["affected_categories"]
            if not isinstance(affected, list) or not affected:
                raise ValueError(f"{path.relative_to(ROOT)}: affected_categories must be a list")
            unknown = sorted(set(affected) - CATEGORIES.keys())
            if unknown:
                raise ValueError(
                    f"{path.relative_to(ROOT)}: unknown categories {', '.join(unknown)}"
                )
            notes.append(note)
    return sorted(notes, key=lambda note: (str(note["date"]), str(note["id"])), reverse=True)


def relative_link(note: dict[str, object], index_path: Path) -> str:
    path = note["path"]
    assert isinstance(path, Path)
    return Path(os.path.relpath(path, index_path.parent)).as_posix()


def combined_table(notes: list[dict[str, object]], index_path: Path) -> str:
    rows = [
        "| Date | ID | Category | Status | Summary |",
        "|---|---|---|---|---|",
    ]
    for note in notes:
        affected = note["affected_categories"]
        assert isinstance(affected, list)
        category = ", ".join(affected)
        rows.append(
            f"| {note['date']} | `{note['id']}` | {category} | {note['status']} | "
            f"[{note['title']}]({relative_link(note, index_path)}) |"
        )
    return "\n".join(rows)


def category_table(
    notes: list[dict[str, object]], category: str, index_path: Path
) -> str:
    rows = [
        "| Date | ID | Status | Summary | Tags |",
        "|---|---|---|---|---|",
    ]
    matching = [note for note in notes if category in note["affected_categories"]]
    if not matching:
        rows.append("| - | - | - | No categorized change notes yet. | - |")
    for note in matching:
        tags = note["tags"]
        assert isinstance(tags, list)
        tag_text = ", ".join(f"`{tag}`" for tag in tags)
        rows.append(
            f"| {note['date']} | `{note['id']}` | {note['status']} | "
            f"[{note['title']}]({relative_link(note, index_path)}) | {tag_text} |"
        )
    return "\n".join(rows)


def replace_generated(path: Path, content: str, begin: str, end: str) -> str:
    text = path.read_text(encoding="utf-8")
    block = f"{begin}\n{content}\n{end}"
    pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(text):
        raise ValueError(f"{path.relative_to(ROOT)}: missing generated markers")
    return pattern.sub(block, text)


def engineering_anchor(heading: str) -> str:
    timestamp = re.search(
        r"(\d{4})-(\d{2})-(\d{2})(?:\s+(\d{2}):(\d{2}):(\d{2}))?",
        heading,
    )
    if timestamp:
        parts = [part for part in timestamp.groups() if part is not None]
        anchor = "elog-" + "".join(parts)
        if timestamp.group(4) is not None:
            return anchor
        title = heading.rsplit(" - ", 1)[-1].lower()
        slug = re.sub(r"[^a-z0-9]+", "-", title).strip("-")
        return f"{anchor}-{slug}"
    title = heading.rsplit(" - ", 1)[-1].lower()
    slug = re.sub(r"[^a-z0-9]+", "-", title).strip("-")
    return f"elog-before-{slug}"


def parse_engineering_entries(text: str) -> list[dict[str, object]]:
    separator = "\n---\n"
    if separator not in text:
        raise ValueError(f"{ENGINEERING_LOG.relative_to(ROOT)}: missing log separator")
    body = text.split(separator, 1)[1]
    entry_pattern = re.compile(
        r"(?ms)^(?:<a id=\"(?P<existing>[^\"]+)\"></a>\n)?"
        r"### (?P<heading>.+?)\n\n(?P<body>.*?)(?=^(?:<a id=\"[^\"]+\"></a>\n)?### |\Z)"
    )
    entries = []
    seen_anchors = set()
    for match in entry_pattern.finditer(body):
        heading = match.group("heading").strip()
        category_match = re.search(r"(?m)^- Category:\s*(.+)$", match.group("body"))
        if not category_match:
            raise ValueError(
                f"{ENGINEERING_LOG.relative_to(ROOT)}: entry lacks Category: {heading}"
            )
        categories = {
            category.strip().lower()
            for category in category_match.group(1).split(",")
        }
        if not categories & INDEXED_LOG_CATEGORIES:
            raise ValueError(
                f"{ENGINEERING_LOG.relative_to(ROOT)}: entry has no indexed topic: "
                f"{heading}"
            )
        anchor = engineering_anchor(heading)
        if anchor in seen_anchors:
            raise ValueError(
                f"{ENGINEERING_LOG.relative_to(ROOT)}: duplicate entry anchor {anchor}"
            )
        seen_anchors.add(anchor)
        entries.append(
            {
                "heading": heading,
                "body": match.group("body").rstrip(),
                "categories": categories,
                "anchor": anchor,
            }
        )
    if not entries:
        raise ValueError(f"{ENGINEERING_LOG.relative_to(ROOT)}: no log entries found")
    return entries


def engineering_topic_index(entries: list[dict[str, object]]) -> str:
    lines = [
        "The links below are alternate views of the single chronological log.",
        "Entry details remain only in the chronology.",
        "",
    ]
    for topic, topic_categories in LOG_TOPICS:
        matching = [
            entry for entry in entries if entry["categories"] & topic_categories
        ]
        lines.append(f"### {topic}")
        if not matching:
            lines.append("- No entries yet.")
        for entry in matching:
            heading = str(entry["heading"])
            link_text = re.sub(r"^[^\dB]*", "", heading)
            lines.append(f"- [{link_text}](#{entry['anchor']})")
        lines.append("")
    return "\n".join(lines).rstrip()


def engineering_log_output() -> str:
    original = ENGINEERING_LOG.read_text(encoding="utf-8")
    entries = parse_engineering_entries(original)
    indexed = replace_generated(
        ENGINEERING_LOG,
        engineering_topic_index(entries),
        LOG_BEGIN,
        LOG_END,
    )
    separator = "\n---\n"
    header = indexed.split(separator, 1)[0]
    chronology = []
    for entry in entries:
        chronology.append(
            f'<a id="{entry["anchor"]}"></a>\n'
            f'### {entry["heading"]}\n\n{entry["body"]}'
        )
    return f"{header}{separator}\n" + "\n\n".join(chronology) + "\n"


def expected_files(notes: list[dict[str, object]]) -> dict[Path, str]:
    outputs = {}
    combined = CHANGES / "INDEX.md"
    outputs[combined] = replace_generated(
        combined, combined_table(notes, combined), CHANGE_BEGIN, CHANGE_END
    )
    for category in CATEGORIES:
        path = CHANGES / category / "README.md"
        outputs[path] = replace_generated(
            path,
            category_table(notes, category, path),
            CHANGE_BEGIN,
            CHANGE_END,
        )
    outputs[ENGINEERING_LOG] = engineering_log_output()
    return outputs


def markdown_link_errors() -> list[str]:
    errors = []
    link_pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    for path in ROOT.rglob("*.md"):
        if ".git" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for target in link_pattern.findall(text):
            target = target.strip()
            if re.match(r"^(https?://|mailto:|#|<)", target):
                continue
            path_only = target.split("#", 1)[0]
            if path_only and not (path.parent / path_only).exists():
                errors.append(f"{path.relative_to(ROOT)}: broken link {target}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true", help="rebuild generated indexes")
    action.add_argument("--check", action="store_true", help="validate indexes and links")
    args = parser.parse_args()

    try:
        notes = load_notes()
        outputs = expected_files(notes)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    if args.write:
        for path, text in outputs.items():
            path.write_text(text, encoding="utf-8", newline="\n")
        print(f"Updated {len(outputs)} change indexes from {len(notes)} notes.")
        return 0

    errors = []
    for path, expected in outputs.items():
        if path.read_text(encoding="utf-8") != expected:
            errors.append(
                f"{path.relative_to(ROOT)} is stale; run "
                "python tools\\docs_index.py --write"
            )
    errors.extend(markdown_link_errors())
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Documentation checks passed for {len(notes)} change notes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
