# Showcase hero review, 18 Nov 2026

A technical-artist review of the project-showcase pipeline against its goal: from any IFC model, accurate hero stills at 8 to 10/10 and the frames for a tower, cutaway, room scroll site. The test was the internal apartment kitchen (a live Revit IFC2x3 project, renders kept out of this repo) through scout camera 05, plus the public sample house.

## Verdict

**Kitchen hero: about 4/10 before, about 5.5 to 6/10 after.** The committed pipeline, run on the scout camera with the current finishes file, rendered the stone as plain white (the scanned stone stand-in had been deleted) and the room as a murky grey wash. After this pass the stone reads as veined stone, the floor reads as laid boards, exposure is set per camera by measurement and the image has contrast. The rest of the gap to 8 can't be closed in code on this machine. It needs four owner decisions, listed at the end.

These are self-scores against the architect's own marketing render (8.5 to 9 in earlier blind reviews), using the same headings as the earlier benchmark. They aren't blind. Get a blind re-score before quoting a number to anyone.

| Heading | Before | After | What moved it |
|---|---|---|---|
| Materials | 3 | 6 | Floorboards, per-panel veneer, stone veining with crisp cores |
| Light and exposure | 4 | 5.5 | Auto exposure, more diffuse bounces, contrast look, weaker camera fill |
| Composition | 5 | 5.5 | Scout camera 05, a little lens shift down |
| Styling | 3 | 3 | Unchanged: the same ten CC0 props |
| Finish (grade, noise) | 5 | 5 | Medium High Contrast helps, but the 1200 px, 256-sample CPU final (27 min) still shows denoiser blotches on the dim ceiling |

Sample house still: about 2.5/10 and not worth more work. It's a test model (a single-box kitchen, no context, a flat ground plane to the horizon). It proves the pipeline runs end to end, nothing more.

## Gaps, in order of how much they lift the score

1. **Materials and texture mapping (biggest, partly fixed).** Box projection itself was fine on this axis-aligned model. The faults were what got projected: one floor scan repeating every 1.2 m with its own board joints, every joinery panel showing the same patch of grain, and no stone pattern at all. Fixed in code: a `boards` column cuts any floor into staggered boards from a plain grain scan (random patch, +/-7% tint and a 1 mm joint per board, no UVs or geometry), every other textured finish samples a random patch per IFC object, and the procedural stone now has long meandering veins with a textured core and soft halo instead of fractal blobs. The stone is still a stand-in. The supplier's slab photo, mapped at true size, is the real fix and is free to ask for.
2. **Exposure and look (fixed).** The hand-set exposure only suited one camera. `"exposure": "auto"` renders a quarter-size, 16-sample test from the shot's camera and sets exposure so the room's log-average brightness (windows left out) hits 0.32. It costs about 20 seconds. The default look moves from AgX Base Contrast to Medium High Contrast, and diffuse bounces from 6 to 10.
3. **Geometry dressing (not the problem on this model).** The research blamed box cabinets. This Revit model already exports casework as separate carcasses, door panels and pulls, and the pipeline already welds and bevels every edge over 30 mm. A joinery skinner (panels, reveals, kick recess) only matters for models that export a kitchen as one box, like the sample house. Not built; worth building when a real job arrives with lumped casework.
4. **Light (open).** Still flat. There's no single clear key, and the far side has no shaped light. Getting it right means picking a time of day for a sun patch on the floor, adding practicals from the lighting schedule, and iterating. Each iteration takes 4 to 6 minutes at 900 px on this CPU, so that's GPU work.
5. **Camera (mostly done).** The scout's candidates are sound. The pick and the final framing are a person's job. The scout now defaults to shift Y -0.05 (the skill's own kitchen rule). A -0.08 shift showed too much empty floor.
6. **Styling (largest remaining gap, owner decision).** Ten generic CC0 props where a pro hero has 40 to 150 curated items. This is curation, not code.
7. **Post (fine).** The saved bloom and vignette grade holds. No change.

## Pipeline parts the goal needs

| Part | State |
|---|---|
| Exterior orbit, room walk, stills, plan | Built |
| Cutaway | Built (`section` dollhouse cut with capped walls, roof-off cutaway) |
| Frame to finished | **New:** `buildup` shot kind. Assembles the model from IFC classes (structure, walls, envelope, fit-out), each stage rising storey by storey, and writes each stage's first frame to the manifest for captions. A slab named "roof" counts as envelope, because Revit and the sample both export roofs as `IfcSlab`. Tested on the sample house. |
| Tower to cutaway to room | Built as separate cut shots. The research found no tool does a continuous move, so studios cut between shots too. |
| Scroll site | Built (template, manifest, hotspots) |
| Window views from drone captures, facade hotspots for towers | Not built (already listed in SKILL.md) |

## Before and after stills

Kept in the private folder `_private-showcase/out/`: `base_hero.png` (before), `p1` to `p4_hero.png` (one change at a time), `final_hero.png` (1200 px, 256 samples), `base_ext.png` and `after_ext.png` (sample house), `build_sheet2.png` (build-up frames). Each step's render time is in its `.log`.

## What's left: the owner's decisions

1. **Ask the supplier for the stone slab photo** (free). It's the single biggest material gain left, and the procedural stone must not go to a client as the real stone.
2. **Styling kit**: BlenderKit (about A$14 a month) or an Evermotion volume (A$45 to A$230), plus a person placing 40+ items. Expected gain about +1 to +1.5.
3. **GPU for iteration**: a rented RTX 4090 at about A$1 an hour, or Kaggle for public models only. Lighting and framing passes aren't practical at 5 minutes a look.
4. **AI still polish** (step 6 of the skill): needs the developer's and architect's written OK before any client design goes to an image model, plus a quoted credit cost.

With 1 to 3 and a one to two hour art-direction pass, the research's estimate of about 8 still looks right. Code alone on this laptop tops out around 6.
