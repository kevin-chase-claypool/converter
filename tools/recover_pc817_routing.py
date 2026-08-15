"""Recover KiCad 10 track geometry into the KiCad 9 perfboard assembly view."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
HARDWARE = ROOT / "hardware" / "pc817-interface"
SOURCE = HARDWARE / "pc817-perfboard-v1.2.kicad_sch.kicad_pcb"
TEMPLATE = HARDWARE / "pc817-perfboard-v1.2.kicad_pcb"
OUTPUT = HARDWARE / "pc817-perfboard-v1.2-routed-kicad9.kicad_pcb"


def blocks(text: str, kind: str) -> list[str]:
    """Return complete top-level KiCad S-expression blocks of one kind."""
    result = []
    cursor = 0
    marker = f"\n\t({kind}\n"
    while True:
        start = text.find(marker, cursor)
        if start < 0:
            return result
        opening = start + 2  # Skip the leading newline and tab; land on `(`.
        depth = 0
        for end in range(opening, len(text)):
            if text[end] == "(":
                depth += 1
            elif text[end] == ")":
                depth -= 1
                if depth == 0:
                    result.append(text[opening : end + 1])
                    cursor = end + 1
                    break
        else:
            raise ValueError(f"Unclosed {kind} block")


def atom(block: str, name: str) -> str:
    match = re.search(rf"\({name}\s+([^()]+?)\)", block)
    if not match:
        raise ValueError(f"Missing {name} in:\n{block}")
    return match.group(1).strip()


source = SOURCE.read_text(encoding="utf-8")
template = TEMPLATE.read_text(encoding="utf-8")
net_ids = {
    name: number
    for number, name in re.findall(r'\(net\s+(\d+)\s+"([^"]*)"\)', template)
}


def net_id(block: str) -> str:
    name = atom(block, "net").strip('"')
    try:
        return net_ids[name]
    except KeyError as error:
        raise ValueError(f"Unknown recovery net: {name}") from error


segments = [
    "  (segment (start {start}) (end {end}) (width {width}) (layer {layer}) (net {net}))".format(
        start=atom(block, "start"),
        end=atom(block, "end"),
        width=atom(block, "width"),
        layer=atom(block, "layer"),
        net=net_id(block),
    )
    for block in blocks(source, "segment")
]
vias = [
    "  (via (at {at}) (size {size}) (drill {drill}) (layers {layers}) (net {net}))".format(
        at=atom(block, "at"),
        size=atom(block, "size"),
        drill=atom(block, "drill"),
        layers=atom(block, "layers"),
        net=net_id(block),
    )
    for block in blocks(source, "via")
]

recovered = template.rstrip()
if not recovered.endswith(")"):
    raise ValueError("KiCad 9 template does not end with a board S-expression")
recovered = recovered[:-1].rstrip() + "\n" + "\n".join(segments + vias) + "\n)\n"
OUTPUT.write_text(recovered, encoding="utf-8")
print(f"Recovered {len(segments)} segments and {len(vias)} vias into {OUTPUT}")
