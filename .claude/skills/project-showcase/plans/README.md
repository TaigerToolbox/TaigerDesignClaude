# Interactive showcase: plans, panoramas and the shell

Layers 1 and 2 of the interactive showcase, plus the page that joins all three layers, built from the project's IFC.

- **Layer 1, plans.** One clickable floor plan per storey and a stacking view of the building. Each plan is *cut* through the model at 1.2 m (the drawing convention), so walls, doors, windows and openings come out like the architect's plan. Rooms and apartments highlight on hover or tap and show name, area (with where the area came from), finishes from the spec library, and links to the room's panorama, the 3D view and any renders.
- **Layer 2, panoramas.** A 360 equirectangular Cycles render per chosen room, from the spot furthest from the walls that is clear of joinery, linked by hotspots into a walkable tour. The viewer (`shell/pano.js`) is ~150 lines of WebGL with no dependencies, so it works offline and on phones.
- **The shell.** `index.html` per project: stacking view, plans, panoramas, the 3D explore view (layer 3, built elsewhere into `explore/`) and stills, with the Taiger Group showcase look (same tokens as `../template/`).

## One command

```
python build.py <project_dir>              # plans + manifest + shell, minutes
python build.py <project_dir> --panos      # also render panoramas (CPU preview: ~5 to 15 min each)
python build.py <project_dir> --panos --final   # final quality, run on a GPU box
python build.py <project_dir> --skip-plans # only rebuild the manifest and shell (e.g. after explore/ lands)
```

Then serve the folder locally and open `index.html`. Bind to localhost when the project is a client's:

```
npx http-server <project_dir> -a 127.0.0.1 -p 8781 -c-1
```

Needs normal Python with `ifcopenshell`, `shapely` (2.x) and `numpy`, plus Blender 5.x for panoramas (`BLENDER` env var, default `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`). `python extract.py` runs a self-check.

## Project folder

```
<project_dir>/
  project.json          the only file you write (below)
  source/model.ifc      a copy of the IFC (never work on the job folder's file)
  plan/                 <storey-id>.svg per storey, plan.json, thumbs/ (spec library swatches)
  pano/                 <room-id>.jpg, panos.json, shots_*.json, finishes.csv, work/ (meshes, raw renders)
  manifest.json         storeys, units, rooms, panoramas: everything the shell shows
  index.html, shell.css, shell.js, pano.js, assets/
  explore/              layer 3, written by the explore build; the shell reads explore/explore.json if present
```

## project.json

```json
{
  "name": "Sample House",
  "subtitle": "buildingSMART IFC4 sample",
  "ifc": "source/model.ifc",
  "extract": {
    "storeys_exclude": "DATUM|UPPER",
    "units": {"from": "spaces", "match": "^(G0[0-9]|[0-9]0[0-9])$"},
    "spaces_exclude": "LANDSCAPE|GARDEN AREA"
  },
  "speclib": {"dir": "C:/path/to/Spec Library", "job": "J-001"},
  "panos": {"rooms": ["level-1-r07", "level-1-r06"], "location": {"lat": -37.84, "lon": 144.98, "utc": "2026-03-20T02:00"}},
  "hero": [{"src": "hero/kitchen.webp", "label": "Kitchen", "room": "level-1-r07"}],
  "disclaimer": "Shown in the footer."
}
```

- `extract.units.from`: `"spaces"` (apartments are IfcSpaces; `match` picks them by name, same-name parts merge), `"storey"` (one residence per level; `name` like `"{storey} residence"`), or leave out.
- `extract.spaces_exclude`: area-plan spaces that overlap real rooms (landscape, permeable area, a second copy of each apartment).
- Other `extract` keys: `cut_height` (1.2), `door_gap` (0.35 m, half the widest opening closed when finding rooms), `min_room_m2` (1.2), `open_plan_m2` (35), `room_rules` and `fixture_ignore` (regexes), `rooms_from_spaces`, `rooms_from_walls`.
- `plan_rotate_deg`: override the automatic rotation that squares the building to the page.
- `panos.rooms`: room ids from `plan/plan.json` (run once without panos to see them), or `"auto": 3` (a kitchen, the biggest other room and a bathroom in the same residence). Also `size` ([4096, 2048]), `samples` (24), `final_size`, `final_samples`, `eye` (1.5 m), `hide` (object-name regexes), `finishes` (default `pano/finishes.csv`).

## Where each value comes from (nothing is invented)

| Shown | Source |
|---|---|
| Walls, doors, windows | IFC elements on the storey, sliced at the cut height |
| Apartments | IfcSpace by name (`units.from: spaces`) or the storey's floor plate |
| Rooms | IfcSpace names where the model has them; otherwise the areas the walls enclose (door and window voids closed using the IFC opening elements), named only from a fixture inside them (cooktop or rangehood: kitchen; shower or bath: bathroom; toilet: WC; washing machine: laundry; stair flight: stair). No fixture, no name: "Room N". A typed room far bigger than its type (a 50 m² "bathroom") becomes "Bathroom and adjoining rooms", because an open doorway joined it to its neighbours |
| Areas | IFC quantity if present; else measured from the IfcSpace footprint, or inside the walls at the cut height. The panel always says which. These are model areas, not contract or sales areas |
| Finishes | Spec library usages whose scheduled location matches the room type or IfcSpace name; residences get the "throughout / generally" entries. Nothing matched: a labelled placeholder |
| Panorama finishes | `pano/finishes.csv`; rows the build adds are neutral and marked PLACEHOLDER. Put real colours and textures in from the spec library export (`speclib finishes-csv`) with a calibrated source |
| Prices, availability | Never shown. There is no field for them |

## Panoramas

`pano_render.py` runs `../scripts/blender_render.py`'s scene setup unchanged (finishes, sun from lat/long, sky, AgX, window portals, auto exposure) and renders an equirectangular camera, level, image centre looking along +Y. It tries each room's candidate spots in order and skips any inside or within 0.35 m of something (so an island bench never swallows the lens), and starts the viewer looking down the longest clear direction. Hotspots link every panorama to the others in the same residence; their yaw and pitch are computed from the camera positions (yaw clockwise from +Y, the same convention the viewer uses, checked with a test scene).

Preview (CPU tonight): 4096x2048, 24 samples, adaptive threshold 0.1, OIDN denoise. Final (GPU later):

```
python build.py <project_dir> --panos --final      # 8192x4096, 512 samples, noise threshold 0.01, device GPU
```

8192 px panoramas exceed many phones' WebGL texture limit (4096); for finals keep a 4096 copy for phones or tile the image. Client models go only to a rented GPU or Kaggle with the developer's and architect's OK, never a render farm.

## Checking a plan against the architect's PDF

Open the architect's floor plan for the same level beside `plan/<storey-id>.svg`. Rooms named "Room N" have no fixture to name them; compare positions with the PDF's labels. The SVG is in metres (viewBox units), so dimensions can be measured directly.

## Known limits

- Open-plan areas are one room in the model (no walls between kitchen, dining and living), so they show as one "Open-plan kitchen".
- Rooms without fixtures stay unnamed. Next step: read the room labels and their positions from the architect's PDF plan and register them to the cut plan.
- Overlapping IfcSpaces from area plans (lift and stair zones, duplicated apartments) need `spaces_exclude`.
- Panorama rooms are empty shells with placeholder finishes until props and real finishes are set in `pano/finishes.csv`.
