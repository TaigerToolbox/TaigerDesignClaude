# Explore view (layer 3: real-time 3D)

A browser 3D view of a new build, made from its IFC: the exterior, a storey-by-storey cutaway with a capped section, and hero rooms you can stand in and walk around. Phone first, static files only, no server code, no build step for the page.

## Rebuild a project

```
npm install                                  # once, in this folder: three.js and gltfpack
python build.py <project>/project.json       # IFC -> <out>/index.html + explore.json + models/*.glb
```

Then serve the output folder's parent with any static server, e.g. `npx http-server <out>/.. -p 8780`, and open `/explore/`.

Proof run on the public sample house: `python build.py ../examples/sample-house/project.json` (download `Building-Architecture.ifc` into that folder first; see its README).

Needs Python with `ifcopenshell` and `Pillow`, and Node. No Blender: the IFC is tessellated by IfcOpenShell (through `../scripts/ifc_to_obj.py`, the same converter the stills use) and packed by gltfpack.

## project.json

```json
{
  "name": "Project name shown in the viewer",
  "ifc": "work/model.ifc",
  "work": "work",
  "out": "explore",
  "finishes": ["spec-library-export.csv", "more-finishes.csv"],
  "convert_args": ["--target", "kitchen=Kitchen Island|PANTRY"],
  "convert_per_storey": false,
  "convert_jobs": 3,
  "skip_storeys": "DATUM|AHD",
  "ground_level": "GROUND",
  "default_level": "GROUND",
  "rooms": [{"id": "living", "name": "Living", "match": "living", "storey": "LEVEL 1"}],
  "cut_height": 1.2,
  "sun": {"az": 35, "el": 50}
}
```

- `ifc`, `work`, `out`: relative to project.json. Keep client models and output outside this repo.
- `finishes`: CSVs in the stills pipeline's `finishes.csv` format, tried in order. The spec library's export (`python -m speclib.lookup <data> finishes-csv <job> out.csv`) goes first. A material matches a row by exact IFC name, else by schedule code inside the name (`K TBV-02 - TIMBER VENEER OAK` matches row `TBV-02`). Colour comes from the row, else the average of the row's supplier swatch (averaged in linear light). A swatch is drawn as a texture only when the row also has a verified `tile_m`; without a real size it would be a guess. Anything unmatched is a neutral placeholder, and the viewer's "i" panel lists every material and says which are placeholders.
- `convert_args`: passed to `ifc_to_obj.py`. Revit exports often have no IfcSpace, so make hero rooms with `--target "name=regex on element names"`.
- `convert_per_storey`: for big models (200 MB+). The whole-model conversion holds every shape in memory and died on a 232 MB IFC with 16 GB of RAM; this converts storey by storey, `convert_jobs` at a time, and merges. Elements not contained in any storey are left out in this mode.
- `rooms`: hero rooms. `match` is a regex on the space name (or the `--target` name); the largest match wins, `storey` narrows it, and spaces outside the building's height (some exports carry them) are ignored. The camera is scouted on the IFC triangles: a grid of standing spots at 1.6 m inside the room, each raycast for a floor under it, a ceiling over it and 0.45 m clear all round (glazing counts as a wall, so it looks into the room, not out), and the spot with the most open 90 degree view wins. Give `"camera": {"pos": [x, y, z], "look": [x, y, z]}` in model coordinates (Z up, the numbers `scene.json` uses) to place it yourself.
- `skip_storeys`: regex for datum levels with no building in them. `ground_level`: where the ground disc sits. `default_level`: the first cutaway level.

## What it writes

```
<out>/
  index.html       the viewer (open from any static server)
  viewer.js
  explore.json     storeys, rooms, views, camera presets, finishes legend: the shell builds its links from this
  models/<storey>.glb   one per storey with geometry, plus site.glb when the IFC has terrain
  lib/three/       the few three.js modules the viewer imports (no CDN, works offline)
```

URL parameters: `?view=exterior|cutaway|room:<id>`, `?level=<storey name or id>`, `?fps=1` (meter, continuous render). For checks from scripts: `window.__explore.render()` draws a frame now (a page in a hidden tab doesn't animate), `.setView(kind, arg, instant)`, `.bench(n)`. The viewer keeps the URL in sync and, inside an iframe, posts `{type: "explore:view", view, level}` to the parent.

## How it works and why

- **One file per storey.** Elements go to the storey the IFC contains them in (aggregates such as stair flights follow their parent; anything uncontained goes by height). Storey heights come from the storey placements, not the Elevation attribute, so they line up with the geometry. Per-storey files give progressive loading (ground floor first, then up, then down) and make the cutaway a visibility switch.
- **Merged by material, compressed with meshopt.** gltfpack merges each storey into one mesh per material (draw calls = materials, not elements), quantises positions to 16 bits (well under a millimetre on a 60 m building) and applies meshopt compression, which decodes on the main thread faster than Draco and needs no worker. No simplification: the geometry stays the IFC's. No normals are stored; the viewer flat-shades, which suits planar architecture and saves a third of the vertex data.
- **Cutaway.** Storeys above the chosen level are hidden and one clipping plane cuts the chosen level at `cut_height` above its floor. Faces are double-sided, and any back face seen through the cut is drawn in a flat section colour, which reads as a solid cut (a poché) without stencil passes.
- **Lighting.** Hemisphere sky plus one sun with a soft shadow map. The shadow map is re-rendered only when what's visible changes, so it costs nothing while orbiting. Neutral tone mapping, so scheduled colours stay close to their swatches.
- **Hero rooms.** Drag to look, double-click or double-tap the floor to walk there, WASD/arrows/scroll/pinch to step. The room's storey and the one above stay visible so there is a ceiling.
- **Render on demand.** Frames are drawn only when the camera or scene changes, which keeps phones cool; `?fps=1` forces continuous rendering to measure.

## Not done yet

- Baked lighting (lightmaps or AO baked in Blender into a second UV set). Real-time sun and sky only for now.
- KTX2 textures: the npm build of gltfpack has no Basis encoder, so textures stay JPEG (512 px max).
- Gaussian splats of dressed rooms: training needs a GPU.
- Per-element picking and info (layer 1 has the data).
