# Hardware CAD

This directory contains project CAD references, generated models, and exported
geometry used for fit checks and course documentation.

## Onshape API workflow

Use the Onshape API helper when CAD exports need to be reproducible from the
current cloud model instead of manually downloaded.

Credentials are stored in Windows user environment variables, not in the
repository:

```powershell
powershell -ExecutionPolicy Bypass -File tools\onshape\set_onshape_env.ps1
```

After opening a new terminal, check access:

```powershell
python tools\onshape\onshape_client.py list-documents --limit 5
```

Useful commands:

```powershell
python tools\onshape\onshape_client.py parse-url "https://cad.onshape.com/documents/.../w/.../e/..."
python tools\onshape\onshape_client.py document --url "https://cad.onshape.com/documents/.../w/.../e/..."
python tools\onshape\onshape_client.py elements "https://cad.onshape.com/documents/.../w/..."
python tools\onshape\onshape_client.py export-partstudio-step "https://cad.onshape.com/documents/.../w/.../e/..." "docs\hardware\cad\exports\part-name.step"
```

Record the Onshape document URL, workspace or version ID, exported filename, and
date in the relevant report or lab note when a model snapshot is used as
evidence.

The helper implements Onshape API-key request signing using `ONSHAPE_ACCESS_KEY`,
`ONSHAPE_SECRET_KEY`, and `ONSHAPE_BASE_URL`. It uses only the Python standard
library.

## Tecmojo 14130201 sliding shelf

This section documents reference CAD for the Tecmojo 1U adjustable-depth sliding
rack shelf sold as Amazon ASIN `B0BMW9V6MS`.

The product is a shelf for a four-post 19-inch rack, not a complete rack
enclosure.

## Files

- `tecmojo-14130201-350mm.step`: shelf configured at the minimum rack-post
  depth.
- `tecmojo-14130201-500mm.step`: shelf configured at the maximum rack-post
  depth.
- Matching `*-preview.png` files: rendered checks of each STEP configuration.
- `../../../tools/cad/generate_tecmojo_14130201.py`: parametric CadQuery source.

## Published dimensions

| Property | Value |
|---|---:|
| SKU | `14130201` |
| Rack interface | 19 inch, EIA/ECA-310-E |
| Rack height | 1U |
| Overall mounting width | 482.6 mm |
| Shelf body height | 44.45 mm listing image; 44 mm current manual |
| Fixed tray depth | 350 mm |
| Adjustable rack-post depth | 350-500 mm |
| Listed capacity | 110 lb / 50 kg |
| Material | Cold-rolled steel |

The STEP files use 44.45 mm for the shelf body because the dimensioned listing
image gives that more precise value. Optional anti-slip stops rise above the
1U body envelope.

## Accuracy boundary

Tecmojo publishes the overall interface dimensions but not production drawings
for the sheet-metal thickness, bend radii, slide profiles, vent pattern, cable
passage, stop geometry, fastener holes, or component tolerances. Those details
were scaled from the listing images and current manufacturer manual.

Use this model for:

- rack and electronics layout;
- mounting-envelope and cable-clearance planning;
- identifying useful mounting regions on the tray;
- early assembly visualization.

Do not use inferred details to manufacture replacement slides or sheet-metal
parts. Measure the received shelf before drilling a mating plate or relying on
individual vent and fastener locations.

Loose mounting screws, cage nuts, hook-and-loop cable ties, and the instruction
sheet are not included in the installed assembly STEP files.

## Sources

- Amazon listing: https://www.amazon.com/dp/B0BMW9V6MS
- Tecmojo product page:
  https://tecmojo.com/products/tecmojo-1u-adjustable-vented-sliding-server-rack-mount-shelf-110lbs-14-16inch-adjustable-mounting-depth-4-post-universal-tray-for-19inch-av-network-equipment-rack
- Current Tecmojo manual:
  https://cdn.shopify.com/s/files/1/0923/0001/7947/files/14130201_14130203.pdf?v=1756802220
- Tecmojo specification sheet:
  https://cdn.shopify.com/s/files/1/0923/0001/7947/files/141302_1U_Adjustable_Vented_Sliding_Server_Rack_Mount_Shelf.pdf?v=1749275624

## Regeneration

Install CadQuery, then run:

```powershell
python tools\cad\generate_tecmojo_14130201.py
```

Replace the image-derived constants near the top of the generator when
physical measurements become available.
