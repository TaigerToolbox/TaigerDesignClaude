---
name: project-showcase
description: Build an accurate, high-end scroll showcase website for any construction project (apartments, houses, renovations, fitouts, commercial, industrial, civil, builder progress stories) from the project's real design model or drawings. Rendered sequences, unit/room hotspots, cutaways, eye-level rooms, finishes, before/after. Use when asked for a project website, development showcase, scroll experience, cutaway, fly-through or marketing page for a build. Geometry, layouts, finishes and views come from the real documents, never from generative AI.
---

# Project showcase

The "building → cutaway → room" scroll experience, rendered from the project's own model so every wall, window, view and finish is right. Tested end to end on the buildingSMART IFC4 sample house: IFC → Blender → WebP sequences → this template.

## The one rule

**Generative AI never decides what the building looks like.** Geometry, layouts, sizes, finishes and views come from the source documents. AI image/video generators invent rooms and morph between frames; that's what reads as AI slop, and on an off-the-plan sale it's misleading conduct under the Australian Consumer Law. AI is allowed only for the narrow finishing jobs in step 6.

## What's in this folder

| Path | What it does |
|---|---|
| `scripts/ifc_to_obj.py` | IFC → OBJ + `scene.json`. Class whitelist (no services/footings/openings), keeps `IfcClass|GlobalId|Name` per object and the IFC style name per face, exports spaces (bounds, centroids), storeys, true north, site lat/long. Normal Python: `pip install ifcopenshell`. |
| `scripts/blender_render.py` | Builds the scene and renders every shot in `shots.json` for desktop (16:9) and mobile (9:16), encodes WebP, writes `site/frames/manifest.js` (frame counts, picker hotspots projected through the real camera, plan scale). Run with `blender -b --factory-startup -P blender_render.py -- shots.json`. |
| `template/` | The site. Plain HTML/CSS/JS, no build. Content in `data/project.js`, render output in `frames/`. |
| `scripts/ai_pack.py` | Optional AI polish: bundles a shot's clay driving video, accurate start/end renders and a prompt written from the finishes schedule, plus the approval and QA checklist. Calls no service. |
| `scripts/qa_drift.py` | Checks AI output against the model's clay frames, edge for edge, whole frame and per grid cell. Exit 1 if any wall, opening or joinery line moved. Writes a JSON report and a review sheet (missing model lines in red). |

`blender_render.py` already does: finishes from a CSV (stops on any unmapped IFC material), real textures projected at true scale from world position (IFC has no UVs) and recoloured to the approved sample, procedural veined stone, weld + 6 mm bevel on every edge (sharp IFC edges are the biggest CG tell), AgX colour with an exposure setting, sun from real lat/long/date rotated to the model's true north, a matched procedural sky or an HDRI, glass that lets daylight through for lighting (interiors otherwise go black in a path tracer), fixed Cycles seed, eased camera moves, level eye-height cameras, explicit cameras for matching a reference shot, roof-off cutaways, an orthographic plan render with metres-per-pixel, clay/outline renders and MP4 output for AI driving videos, frame-count assertions and a size report.

Shot kinds: `orbit` (hero, exterior), `cutaway` (roof off, descend into a target space), `room` (eye level 1.6 m, level camera, slow dolly; `corner` 0 to 3 picks the start corner), `still` (picker image + hotspots), `plan` (QA ortho). Any shot can take `camera: {pos, look, pos2?, look2?}`, `size: [w, h]`, `variants: ["desktop"]`, `style: "clay"`, `video: true`. Engine: `EEVEE` for drafts on a laptop, `CYCLES` for finals.

## Step 0: Intake

Record what you have and what's missing in `brief.md`. Anything you had to assume goes in an **Assumed** list for the architect to clear.

**Must:** current plans, elevations and sections with their revision letter · finishes schedule · site address and survey north point · written approval from the developer and architect to publish · for multi-unit jobs, the unit schedule (number, type, level, beds/baths, internal/external m², aspect, status).

**Should:** IFC (best) or Revit/ArchiCAD/SketchUp model · survey with MGA coordinates and RLs · supplier product codes, samples or photos · landscape plan · brand kit · drone capture of the site, plus HDR brackets or 360s at each key floor height for window views.

**Nice:** furniture/styling selections · approved neighbouring developments (massing) · monthly progress drone or photo captures · lighting plan · interior designer boards.

**Minimum that still gives a good result:** dimensioned plans + elevations, finishes schedule, address, approval. That's enough for an accurate exterior, a cutaway and 2 to 3 rooms. Window views and progress scenes need real captures: drop those scenes rather than fake them.

## Step 1: Geometry

**From IFC:** `python scripts/ifc_to_obj.py model.ifc work/`. Read the printed material list and `scene.json` `skipped` entries. Override the whitelist with `--classes` for unusual jobs (civil: `IfcCourse,IfcPavement,IfcKerb,IfcBearing,...`). Don't merge meshes before QA: per-element identity is how faces trace back to the model.

**Big real-world models (tested on a 243 MB Revit IFC2x3 of a live apartment project):** don't convert the whole building for one room. `--storey "LEVEL 01,LEVEL 02"` (always include the storey above: its slab is the ceiling), `--around "<element name regex>" --margin 7` keeps only what's near the room. Revit often exports **no IfcSpace**, so rooms don't exist by name: build them with `--target "kitchen=Kitchen Island|PANTRY|RANGEHOOD"` (a camera/hotspot target from the bounds of matching elements). Revit material names usually carry the finish codes (`K-TIM-01`, `TBV-02`), so mapping to the schedule is direct. Conversion of that region took about a minute.

**No IFC (most houses, extensions, fitouts):** rebuild in Blender from the drawings. Import each PDF page as a scaled underlay (calibrate from a long dimension string, not the printed scale). Model walls and openings **to the written dimensions**, never by tracing the PDF. Heights from the sections. SketchUp: import, then fix reversed faces, scale and material assignment. Name objects `Class|id|name` and materials by finish code so the rest of the pipeline is identical. Every dimension you had to infer goes in **Assumed**.

**Interiors with no furniture in the model:** use an approved styling layer of real products (manufacturer models or a vetted library) in its own collection named `furniture`, captioned "furniture indicative, not included". QA can switch it off.

## Step 2: Materials

`finishes.csv` columns: `ifc_material,color,roughness,metallic,transmission,hide,texture,tile_m,normal_strength,procedural,vein,source`. One row per IFC material name the converter printed; the render stops and lists any it can't find. `hide=1` for markers and virtual elements. Write in `source` where each value came from (schedule code, sample, or ASSUMED); that column is the audit trail and feeds the AI prompt.

- **Colour:** from a calibrated photo of the approved sample (grey card in frame, daylight). Approved-sample sign-off forms are usually office scans and run warm and saturated; use them only as a fallback and mark it.
- **Texture:** `texture` = a CC0 scan's diffuse map (its `_Rough` and `_nor_gl` siblings are found automatically), `tile_m` = the real width that image covers (Poly Haven lists it; for boards, count them: 8 boards in 1.7 m, scaled for 190 mm boards = 1.52 m). The script keeps the scan's grain and shifts its average to your sample colour.
- **Stone without a scan:** `procedural=marble`, `color` = ground, `vein` = vein colour, `tile_m` = vein scale. It reads as real stone at room scale; for close-ups of a named slab (e.g. Calacatta) get a scan or slab photo from the supplier.
- **Slab soffits** export as concrete but are painted ceilings: map those concrete materials to the ceiling paint.
- Glass gets `transmission=1`. Australian context only: Colorbond colours by name, eucalypts not deciduous European trees, right-hand-drive cars.

## Step 3: Scene library by project type

The template is a list of sections, so each project turns on only what it needs. Every project gets: **hero, specs, enquire**, and where the data exists, **context** and **figures**.

| Project | Scenes |
|---|---|
| Apartments / townhouses | picker (units on the facade), cutaway per type, rooms, views by level |
| Single house | exterior orbit, cutaway or plan reveal, 3 to 5 rooms at eye level, outdoor living, sun study |
| Renovation / extension | existing vs proposed `compare` from the same camera (existing from photos or a scan), extension footprint, rooms |
| Fitout | tenancy in context, cutaway per zone, finishes board |
| Commercial / industrial | site orbit with access/loading/parking captions, figures (GFA, clearance, docks, power), office interior |
| Civil / infrastructure | corridor `scrub` along the alignment, `compare` per stage or chainage, figures; no rooms, no cutaway |
| Progress story (any of the above) | `compare` pairs per milestone from the same tripod or drone spot, frame stage to handover |

## Step 4: Cameras and render

- **Lenses:** exteriors 35 to 50 mm, interiors 18 to 24 mm and never above 90° horizontal FOV. Wide lenses that make rooms look bigger are misleading, not just ugly. Eye height 1.6 m. Interior and eye-level cameras stay level (the `room` kind does this); correct with lens shift, never tilt.
- **Moves:** every move eased. 120 to 180 frames for a hero, 90 to 150 for a cutaway; phones get about 60% (the script does this). Frame count, not fps, decides scrub smoothness.
- **Sun:** pick the date and time on purpose and record it (21 June, 3 pm shows honest winter shadows). True north from the survey, not the plan's arrow; `trueNorth` from the IFC is used when present.
- **Window views:** camera-mapped backplates from the drone capture at that unit's GPS position and RL, exposure matched, capture date recorded. Model approved but unbuilt neighbours as massing so views aren't oversold.
- **Interiors:** daylight only reaches the room through glass, so: `hdri` (a photographed sky lights far better than a procedural one; record it as a stand-in, not the real view), `exposure` +2 to +3 (how a photographer exposes an interior), and the script's light-passing glass. Match a reference shot with an explicit `camera`, iterate framing with EEVEE stills at 900 px (seconds each), then one Cycles final.
- **Finals:** Cycles, enough samples that the fixed-seed denoiser is temporally stable. Scrub the sequence at 2x and look for flicker before encoding. Render at native size; don't AI-upscale sequences (it flickers and hallucinates detail).
- **Encoding:** WebP quality 70 to 80 (the script uses 78). Budget: under ~120 KB per desktop frame and ~8 MB per mobile sequence. Check the size report the script prints.

## Step 5: Build the site

Copy `template/` to `<project>/site/` and point `shots.json` `site` at it. Then edit only `data/project.js` and the `:root` tokens in `styles.css`.

- Sections: `scrub`, `cutaway`, `picker`, `stats`, `specs`, `compare`, in any order, any can be `off: true`. A section with missing data is skipped and logged; the rest of the page still builds. All labels and wording live in the data (Residence, Lot, Tenancy, Stage, Room), nothing apartment-specific is hard-coded.
- `frames: "<shot name>"` links a section to a rendered shot. Until it's rendered, the scene draws a stamped PLACEHOLDER.
- Picker units use `anchor: "<space name>"`; `blender_render.py` writes that space's exact x/y for the picker camera into the manifest. The picker box takes the image's own aspect ratio, so hotspots can't drift.
- How the scrub works: tall section, sticky stage, scroll progress eased toward the target (smooth on mouse wheels). Frames are fetched as compressed blobs coarse-to-fine (first, last, then every 16th, 8th...), six at a time, starting a screen before the section arrives; only frames near the playhead are decoded, so memory stays low on phones. Frame 1 is a real `<img>` poster (LCP, no-JS). Portrait frames on portrait screens, re-picked on rotation. Reduced motion and Save-Data load a single still.
- All data is written with `textContent`; links only accept http(s), mailto, tel and #.

## Step 6: Where AI is allowed

Copywriting drafts the developer approves, denoising single stills, and the optional polish pass below. No AI people or cars on sequences (they morph frame to frame): use licensed 3D entourage or none. No sky replacement on renders. Never for geometry, layouts, sizes, windows, finishes, views, or anything a buyer could rely on.

**Optional AI polish (model-locked video).** When renders need more realism than the render budget allows, a video model with a driving video can add it without being allowed to redesign the room:

1. Render the move twice from the same `shots.json` entry: once `style: "clay", video: true` (white model with outlines, the driving video and the QA reference) and the first and last frames as accurate Cycles stills (the finishes).
2. `python scripts/ai_pack.py --driving ... --start ... --end ... --finishes finishes.csv --room "Kitchen" --materials "..." --out work/ai/kitchen`. The prompt names only scheduled finishes and forbids moving or adding anything; styling only if approved (`--styling`).
3. Before generating: written OK from the developer and architect to send their design to an AI service, and the owner approves the quoted credit cost. Draft cheap, finish only the approved take.
4. After generating: `python scripts/qa_drift.py <clay frames> <ai.mp4> --report qa/... --sheet qa/...` must pass. The reference is the clay render (geometry only), never a colour render (its shadows aren't geometry). Tested: a wall section moved 3 to 5% of frame width or an erased element fails in its grid cell while the whole-frame score still looked fine; a 1% shift passes as tolerance; a real colour render passes against its clay frames. Then check finishes against the start frame and scrub at 2x for morphing. Label it "Artist's impression, AI-enhanced from the design model".

The difference from the "AI walkthrough" posts doing the rounds: they let the prompt choose the materials ("raw concrete, light pine"). Here the materials come from the schedule and the output is checked against the model, so it can be used on a real sale.

## Step 7: Accuracy QA gate (all must pass before anyone outside sees it)

1. **Plan overlay, measured:** the `plan` shot writes `metresPerPixel`. Register it to the architect's plan PDF on two known points and measure: openings within ±20 mm, overall within ±50 mm. Same for each elevation. Save the difference images to `qa/`.
2. **Areas:** compute room areas from the model and reconcile against the unit schedule using the contract's measuring method (internal vs external, wall centrelines).
3. **Finishes:** every visible material maps to the current schedule revision (the render stops on unmapped ones; check the mapping is right, not just present).
4. **Cameras:** no interior FOV over 90°, eye height 1.6 m recorded, furniture at true product dimensions.
5. **Sun and views:** date/time stated, north verified against the survey, views match the capture for that level and orientation.
6. **Frames:** contact sheet of every 10th frame per shot (`ffmpeg -i %04d.webp -vf "select=not(mod(n\,10)),scale=320:-1,tile=6x" sheet.png`). Look for flicker, missing geometry, and what the mobile crop cuts off.
7. **Site:** every hotspot opens the right unit, every number matches the schedule (generated, not hand-typed), disclaimer visible on every rendered scene, no console errors, phone and desktop checked.
8. **AI-polished shots only:** `qa_drift.py` passed and its report and sheet are filed in `qa/`.
9. **Revision lock:** record the source file names, revisions and render date in `qa/manifest.json` (the render manifest already carries source, date, sun and engine). A newer drawing revision voids the sign-off.
10. **Sign-off** from the architect and developer on the exact preview URL and commit, in writing, filed in `qa/`.

The disclaimer must name the drawing and finishes revisions: "Artist's impression. Final design, finishes and views may vary. Rendered from drawing revision C, finishes schedule revision B."

## Step 8: Hand over

Private preview link first (Vercel or the client's host). Promo cut for social: screen-record the scroll, then follow the sound design steps in the repo's CLAUDE.md. Keep `shots.json`, `finishes.csv`, the `.blend` and `data/project.js` so the next drawing revision re-renders in hours.

## Project folder

```
<project>/
  brief.md        intake, missing, Assumed
  source/         IFC, PDFs, schedules (read only)
  work/           model.obj, scene.json, raw renders (not shipped)
  finishes.csv
  shots.json
  site/           copy of template/; frames/ is written by blender_render.py
  qa/             overlays, contact sheets, manifest.json, sign-offs
```

## Benchmark: where this stands against a professional render

Tested on a live apartment kitchen: same IFC, same camera, scheduled finishes, CPU-only Cycles (37 min, then 12 min at 1200 px). A blind art-director review scored the architect's own marketing render 8.5/10 for sign-off and ours 2/10, then 3/10 after the setup fixes now built in (exposure, white balance, lighter sample-corrected colours, low sun). Geometry, layout and finish placement matched; the gap is everything that makes a picture sell:

1. **Styling assets (biggest gap, scored 1/10):** no props, curtains, tap detail or greenery. Needs an approved props library (vase and branches, fruit bowl, cookware, sheers, small appliances, one artwork) placed in its own `furniture` collection.
2. **Real stone:** procedural marble reads as drawn at close range. Get the supplier's slab scan for any stone the camera gets near.
3. **Light fill:** add area/portal lights in each window and light the dark uprights so nothing renders pure black; open blinds or swap to sheers.
4. **Render budget:** finals on a GPU box or render farm; a laptop CPU is for framing and drafts.

Until 1 and 2 exist, use renders for accuracy (cutaways, plans, layouts, finishes boards) and treat photoreal hero interiors as needing either those assets or the model-locked AI pass in step 6.

## Not built yet (do by hand until then)

Schedule CSV → `data/project.js` generator; automated overlay registration and deviation report; a finishes check for AI output (colour/pattern drift against the start frame; `qa_drift.py` checks geometry only); downlights/IES lighting from the lighting schedule; facade-point hotspots for apartment towers (today they project space centroids, which suits cutaway pickers; for a tower facade, anchor on a point on each unit's facade); bevel/triplanar for PDF-rebuilt models is manual; Gaussian splat and map/location sections; an enquiry form (the template links out).
