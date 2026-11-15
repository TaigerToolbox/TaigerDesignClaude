---
name: project-showcase
description: Build an accurate, high-end interactive showcase website (scroll-driven tower hero, unit hotspots, apartment cutaways, room fly-throughs, construction progress timeline) for any construction build or development. Use when asked to make a project website, development showcase, scroll experience, cutaway, fly-through or marketing page for a building. Geometry and finishes come from the real design model, never from generative AI.
---

# Project showcase

A repeatable pipeline that produces the "tower → cutaway → room" scroll experience, built from the project's real model so every wall, window, view and finish is correct.

## The one rule

**Generative AI never decides what the building looks like.** All geometry, layouts, finishes and views come from the source documents below. AI is allowed only for finishing touches that don't misrepresent the building (see step 5). Image or video generators that invent rooms are what make results look like AI slop and can mislead buyers.

## Step 0: Intake (don't start without these)

Ask for these and record what's missing in `brief.md` in the project folder:

| Input | Why | Usual source |
|---|---|---|
| Design model: IFC (preferred), Revit, ArchiCAD or SketchUp | All geometry | Architect |
| Architectural set: plans, elevations, sections (PDF) | QA checks | Architect |
| Finishes and FF&E schedule, plus supplier product codes | Real materials | Architect or interior designer |
| Unit schedule: unit no., type, level, beds/baths, internal/external m², aspect | Hotspot data, spec panels | Developer or sales agent |
| Site survey and coordinates | Placing the model in the real world | Surveyor |
| Drone photos/video of the site and surroundings, plus a capture from each key floor height | Real context and real views from apartments | Drone operator (CASA licensed) |
| Brand: logo, fonts, colours, the project name | Look of the site | Developer |
| Written approval to use the design and renders publicly | IP and marketing sign-off | Developer and architect |

## Step 1: Model to clean scene

1. Convert IFC to a Blender scene (Bonsai add-on, formerly BlenderBIM) or `IfcConvert model.ifc model.glb` (IfcOpenShell). Revit can go out as IFC or via Datasmith/Twinmotion.
2. Clean up: remove hidden services, structure and annotation; merge by material; fix normals; keep real dimensions (metres, Z up → Y up for glTF).
3. Map materials from the finishes schedule (script it: schedule code → material). Use supplier textures and scanned PBR materials, at real-world scale.
4. Geolocate with the survey coordinates and set the true sun position for the site's latitude.

## Step 2: Build the scene library

Every project uses the same set of scenes, so the site template stays the same:

1. **Hero:** exterior at golden hour or dusk, placed into drone footage or a Gaussian splat of the real street.
2. **Context:** orbit of the neighbourhood (splat or photogrammetry from drone capture), with labels for transport, parks and amenities.
3. **Unit picker:** tower with a hotspot on each unit. Hotspot positions come from the model's room centroids, not placed by hand.
4. **Cutaway:** one per apartment type, roof and upper slab removed, built from the same model and labelled with the unit schedule data.
5. **Rooms:** 2 to 4 per type (living/kitchen, main bed, main bath, balcony view). Views out of the windows use the real drone capture from that floor height.
6. **Specs:** finishes and appliance brands from the schedule.
7. **Progress (for builders):** monthly drone splat of site progress on a timeline slider, side by side with the model. Builders can show this and marketing agencies can't.

## Step 3: Render

Two delivery modes; most sites use both:

- **Photoreal scroll sequences:** path-traced in Blender Cycles (or D5, Twinmotion, Enscape) from the real model. Camera moves (facade push-in → cutaway → into room) rendered as image sequences at 30 fps, 1920 wide for desktop and a separate portrait 1080×1920 for mobile. Claude writes the Blender Python for camera paths, materials and batch rendering. CPU renders are slow, so use a GPU box or render farm for final frames.
- **Real-time 3D:** glTF/GLB with Draco or meshopt compression and KTX2 textures, baked lighting, in three.js. Use for the unit picker and any free orbit. Keep under about 15 MB for the first load.

Gaussian splats (Postshot, Luma, Polycam or similar) for real-world context, shown with a three.js splat viewer.

## Step 4: Build the site

- Stack: Vite + three.js + GSAP ScrollTrigger. Scroll-scrub image sequences on a `<canvas>` (WebP or AVIF frames, preloaded in chunks).
- All text, labels, hotspots and spec panels are HTML over the canvas, driven by `units.json` (from the unit schedule), so they stay sharp, clickable and editable without re-rendering.
- Mobile first: portrait sequences, fewer frames, tap instead of hover. Respect `prefers-reduced-motion` with a still-image fallback.
- Performance budget: Lighthouse performance 85+ on mobile, first view under 3 s on 4G.

## Step 5: Where AI is allowed

Only for these, and each one gets checked against the drawings:

- Upscaling and denoising rendered frames.
- Sky replacement on renders (not on real photos of views).
- Adding people and cars to scenes as entourage.
- Copywriting drafts, which the developer approves.

Never for: building geometry, layouts, room sizes, window positions, finishes, views from windows, or anything a buyer could rely on.

## Step 6: Accuracy QA gate (must pass before anything is shown)

1. **Overlay check:** render the plan view and each elevation from the scene camera, then overlay them on the architect's PDFs at 50% opacity. Window, door and wall positions must line up.
2. **Finishes check:** every visible material matches the current finishes schedule revision. Note the revision on the site.
3. **Data check:** every hotspot, area and bed/bath count matches the unit schedule.
4. **View check:** window views match the drone capture for that level and orientation.
5. **Sign-off:** architect and developer approve in writing. Keep a record in `qa/`.
6. **Disclaimer:** "Artist's impression. Final design, finishes and views may vary." on every render and in the footer.

## Step 7: Hand over

- Host on Vercel, Netlify or the client's site; give the client a private preview link first.
- Promo cut for social media: record the scroll experience as a video, then follow the sound design steps in the repo's CLAUDE.md.
- Save the scene file, render settings and `units.json` so the next design revision can be re-rendered in hours instead of weeks.

## Project folder layout

```
<project>/
  brief.md          intake checklist and what's missing
  source/           IFC, PDFs, schedules (read only)
  scene/            .blend, materials, camera paths
  renders/          sequences per scene, desktop/ and mobile/
  splats/           context and progress captures
  site/             Vite app, units.json
  qa/               overlays, sign-offs
```
