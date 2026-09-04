"""Generate a responsive card view from the authoritative wiring Markdown table.

Usage:
    python tools/generate_wiring_table_mobile.py

The Markdown table remains the source of truth. This generator intentionally
keeps the mobile artifact derived and disposable.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "hardware" / "WIRING_TABLE.md"
OUTPUT = ROOT / "docs" / "hardware" / "wiring-table-mobile.html"


def split_row(line: str) -> list[str]:
    body = line.strip().strip("|")
    return [cell.strip() for cell in body.split("|")]


def is_separator(line: str) -> bool:
    cells = split_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def inline_markup(value: str) -> str:
    """Escape Markdown cell text while retaining useful code spans."""

    escaped = escape(value, quote=False)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)


def parse_tables(text: str) -> list[tuple[str, list[str], list[list[str]]]]:
    heading = "Wiring table"
    parsed: list[tuple[str, list[str], list[list[str]]]] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        match = re.match(r"^(#{2,3})\s+(.+?)\s*$", line)
        if match:
            heading = match.group(2)
            index += 1
            continue
        if line.lstrip().startswith("|") and index + 1 < len(lines):
            separator = lines[index + 1]
            if separator.lstrip().startswith("|") and is_separator(separator):
                headers = split_row(line)
                rows: list[list[str]] = []
                index += 2
                while index < len(lines) and lines[index].lstrip().startswith("|"):
                    if not is_separator(lines[index]):
                        row = split_row(lines[index])
                        if len(row) == len(headers):
                            rows.append(row)
                    index += 1
                parsed.append((heading, headers, rows))
                continue
        index += 1
    return parsed


def cell_map(headers: list[str], row: list[str]) -> list[tuple[str, str]]:
    return [(header, value) for header, value in zip(headers, row) if value]


def render_card(headers: list[str], row: list[str]) -> str:
    pairs = cell_map(headers, row)
    row_id = next((value for header, value in pairs if header.lower() == "id"), "")
    title = row_id or next((value for _, value in pairs[:2]), "Connection")
    fields = []
    for header, value in pairs:
        if header.lower() == "id":
            continue
        fields.append(
            f'<div class="field"><dt>{inline_markup(header)}</dt>'
            f'<dd>{inline_markup(value)}</dd></div>'
        )
    return (
        '<article class="connection" data-search="'
        + escape(" ".join([title] + [value for _, value in pairs]), quote=True)
        + '">'
        + f"<h3>{inline_markup(title)}</h3>"
        + '<dl class="fields">'
        + "".join(fields)
        + "</dl></article>"
    )


def render(source: Path) -> str:
    tables = parse_tables(source.read_text(encoding="utf-8"))
    sections = []
    for heading, headers, rows in tables:
        cards = "".join(render_card(headers, row) for row in rows)
        if cards:
            sections.append(
                f'<section class="table-section"><h2>{escape(heading)}</h2>'
                f'<div class="cards">{cards}</div></section>'
            )
    body = "\n".join(sections)
    source_name = source.name
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Master Wiring Table — Mobile View</title>
  <style>
    :root {{ color-scheme: light dark; --bg: #10141a; --panel: #19212b;
      --panel-2: #202b38; --text: #edf3f8; --muted: #a8b6c4; --accent: #6bc5ff;
      --border: #354657; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; padding: 1rem; background: var(--bg); color: var(--text);
      font: 16px/1.45 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    main {{ max-width: 1100px; margin: 0 auto; }}
    header {{ margin-bottom: 1.25rem; }}
    h1 {{ margin: 0 0 .35rem; font-size: clamp(1.45rem, 5vw, 2.2rem); }}
    h2 {{ margin: 1.4rem 0 .65rem; font-size: 1.2rem; color: var(--accent); }}
    h3 {{ margin: 0; font-size: 1rem; overflow-wrap: anywhere; }}
    p {{ margin: .35rem 0; color: var(--muted); }}
    a {{ color: var(--accent); }}
    .notice {{ padding: .75rem; border: 1px solid var(--border); border-radius: .65rem;
      background: var(--panel); }}
    .search {{ width: 100%; margin: .8rem 0 0; padding: .7rem .8rem; border-radius: .5rem;
      border: 1px solid var(--border); background: var(--panel-2); color: var(--text);
      font: inherit; }}
    .cards {{ display: grid; gap: .7rem; }}
    .connection {{ min-width: 0; padding: .8rem; border: 1px solid var(--border);
      border-radius: .65rem; background: var(--panel); }}
    .fields {{ margin: .55rem 0 0; }}
    .field {{ display: grid; grid-template-columns: minmax(6rem, 34%) 1fr; gap: .55rem;
      padding: .28rem 0; border-top: 1px solid color-mix(in srgb, var(--border) 65%, transparent); }}
    dt {{ color: var(--muted); font-size: .82rem; overflow-wrap: anywhere; }}
    dd {{ margin: 0; overflow-wrap: anywhere; }}
    code {{ font: .9em ui-monospace, SFMono-Regular, Consolas, monospace; }}
    .empty {{ display: none; color: var(--muted); }}
    @media (min-width: 700px) {{ body {{ padding: 2rem; }} .cards {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
    @media (prefers-color-scheme: light) {{ :root {{ --bg: #f5f7fa; --panel: #fff;
      --panel-2: #fff; --text: #17212b; --muted: #536575; --border: #cbd6df; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>Master Wiring Table</h1>
    <p class="notice">Mobile card view generated from <a href="{source_name}">{source_name}</a>.
      The Markdown file remains authoritative. Re-run the generator after wiring changes.</p>
    <input class="search" id="search" type="search" placeholder="Filter by axis, pin, ID, status…" aria-label="Filter wiring connections">
  </header>
  <p id="empty" class="empty">No connections match that filter.</p>
  {body}
</main>
<script>
  const search = document.querySelector('#search');
  const cards = [...document.querySelectorAll('.connection')];
  const sections = [...document.querySelectorAll('.table-section')];
  const empty = document.querySelector('#empty');
  search.addEventListener('input', () => {{
    const query = search.value.trim().toLowerCase();
    let visible = 0;
    cards.forEach(card => {{
      const show = !query || card.dataset.search.toLowerCase().includes(query);
      card.hidden = !show;
      if (show) visible += 1;
    }});
    sections.forEach(section => {{
      section.hidden = !section.querySelector('.connection:not([hidden])');
    }});
    empty.style.display = visible ? 'none' : 'block';
  }});
</script>
</body>
</html>
'''


def main() -> None:
    OUTPUT.write_text(render(SOURCE), encoding="utf-8", newline="\n")
    print(f"Generated {OUTPUT.relative_to(ROOT)} from {SOURCE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
