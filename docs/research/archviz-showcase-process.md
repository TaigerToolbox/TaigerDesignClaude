# Arch-viz showcase process: how the pros do it, and how we get there

Research note for the `project-showcase` skill. Written 16 Nov 2026. Research only: nothing in the skill was changed.

Prices are converted at an assumed A$1.55 per US$1 and rounded. Most vendor prices below come from third-party pages, so each one says where it came from; check the vendor's own page before buying. Where a source is a vendor or a competitor blog, it is flagged.

---

## 1. The short answer

The gap between our 3/10 and the architect's 8.5/10 isn't mainly the renderer. Blender Cycles is a production path tracer and is good enough. The gap is the work pro studios put into each hero image: a paid furniture and styling library, real material scans, a camera composed like a photograph, practical lights, a post-production grade, and roughly a working day of an artist's time per interior still ([ArchiCGI, about eight working hours per residential interior](https://archicgi.com/?p=3287), studio marketing so treat as indicative). Our pipeline already does the accuracy half better than most studios (schedule-driven finishes, drift checks, revision lock). What it lacks is the taste half, plus the hardware to iterate.

**Honest verdict, in one paragraph.** Automation will get a fully scripted Blender interior to about 6 or 7 out of 10. The last two points come from a person with an eye making 20 to 40 small decisions per shot (what's on the bench, where the throw falls, which light leads), and from rendering fast enough to make those decisions by looking. So the fastest route to 8+ stills is: rent a GPU, buy a curated styling kit once, get the supplier's stone photos, and give every hero shot a one to two hour art-direction pass against a reference, with optional AI polish only as the last 10%, drift-checked. For scroll sequences, "flawless" is already within reach with what we have, because sequences forgive less detail per frame but punish flicker, and our pipeline handles flicker properly. The main thing sequences need is GPU time.

---

## 2. Recommended end-to-end process (any project type)

This keeps the skill's eight steps and adds what the research says is missing. New or changed items are marked **NEW**.

### Step 0. Intake (as now, plus)
- **NEW: the reference set.** Collect two or three published marketing renders or photos the client likes, and for each hero shot write one line on the intended mood (time of day, warm or cool, styled or sparse). Pros start with a reference board before touching the scene; it's the yardstick the art director will use anyway ([Ronen Bekerman making-of showcases](https://ronenbekerman.com/?p=118628) follow this pattern; the Architizer "Art of Rendering" series shows reference-led lighting choices: [House on the Lake](https://architizer.com/blog/?p=11284)).
- **NEW: supplier slab and sample photos** for every stone, timber and tile the camera gets within about 2 m of. Ask the supplier for the full-slab photo or scan; most stone yards photograph each slab for sale.
- **NEW: styling approval** at intake, as a short list (sofa type, stool type, art, plants) so props are approved before rendering, not after.
- **NEW for frame-stage scenes:** ask the frame and truss fabricator whether their detailing software can export IFC or another 3D format. Architect models usually don't contain studs, noggins or trusses, so without the fabricator's model a frame stage is illustrative only and must be labelled so.

### Step 1. Geometry
As now (IFC whitelist, storey and `--around` cropping, rebuild-from-drawings rules). Add:
- **NEW: missing-detail pass.** Skirtings, architraves, shadow lines, tap and handle detail, power points and switch plates. Missing trim is one of the commonest reasons a render reads as fake even with good lighting ([D5 on detailing for realism](https://www.d5render.com/posts/detailing-architectural-rendering)). Revit often omits them; add them as scheduled items from the finishes and electrical drawings, never invented.

### Step 2. Materials
As now. Add:
- **NEW: imperfection layer.** One shared node group that adds subtle roughness variation, faint smudges on glossy surfaces, dust in corners and slight colour variation per board or tile. "A flawless scene looks fake" is the most repeated finding across realism guides ([ArchiCGI](https://archicgi.com/?p=10573), [Renderahouse on why renders look fake](https://blog.renderahouse.com/blog/why-renders-look-fake-6-common-problems-solved)). Keep it at the "you only notice when it's gone" level; it must not change the finish colour.
- **NEW: fabric shader** for sheers and upholstery: transmission plus low translucency (about 0.1 to 0.7) and sheen. Thin fabric always has some translucency ([Advanced Curtain Shader docs](https://superhivemarket.com/products/advanced-curtain-shader/docs); [Blender Artists thread on sheer setup](https://blenderartists.org/t/translucent-material-and-light/1266758)).

### Step 3. Scene library
As now. The project-type table is good and matches what award-winning property sites do.

### Step 4. Styling (NEW as its own step)
Pros build every interior from a curated, paid library (Evermotion Archinteriors, Design Connected, iMeshh, Chaos Cosmos for V-Ray/Corona/Enscape users) because the models come with production materials and believable proportions ([Chaos Cosmos](https://www.chaos.com/cosmos), [Design Connected subscriptions](https://designconnected.com/subscriptions), [Evermotion](https://evermotion.org)). Free libraries help for small items: Poly Haven is CC0, commercial use, no credit needed ([Poly Haven licence](https://polyhaven.com/license)); Megascans on Fab is now free under Fab's standard licence ([CG Channel](https://www.cgchannel.com/?p=179945), [Creative Bloq](https://creativebloq.com/news/the-worlds-biggest-library-of-scanned-assets-for-3d-artists-is-now-free-and-it-seems-that-this-time-its-for-good)).

Styling density rules (from the art-director review and the realism guides):
- Every room gets a **soft layer** (sheers or curtains, a throw, cushions, a rug) and a **life layer** (a book, a cup, a bowl of fruit, one plant). The soft layer is what our kitchen lacked most.
- Clusters in odd numbers; vary heights; leave most surfaces clear; nothing in the front 300 mm of a bench.
- Contact matters: objects must sit in their own contact shadow, not float. Mismatched reflections and contact shadows make even a good composition feel synthetic ([Renderahouse](https://blog.renderahouse.com/blog/why-renders-look-fake-6-common-problems-solved)).
- Furniture stays in the `furniture` collection and the site captions "furniture indicative, not included" (already built).

### Step 5. Lighting (as now, plus)
Our recipe (HDRI, window portals, fills, AgX, exposure, white balance, sun from real lat/long) matches the standard pro recipe: establish daylight first, set a believable exposure, then add practicals in layers ([Novedge, V-Ray interior lighting](https://novedge.com/blogs/design-news/v-ray-tip-v-ray-techniques-for-balanced-and-natural-interior-lighting)). Portals are an optimisation, not a substitute for sun ([Novedge, Redshift portals](https://novedge.com/blogs/design-news/cinema-4d-tip-optimizing-redshift-interior-lighting-with-portal-area-lights); [blender3darchitect on portals](https://blender3darchitect.com/?p=57937)). Add:
- **NEW: one lead light per shot.** Every 8+ interior has a clear key: a shaft of low sun across the floor, or a bright window wall with the room falling off. "Every surface equally lit" is the commonest lighting tell ([Renderahouse](https://blog.renderahouse.com/blog/why-renders-look-fake-6-common-problems-solved)).
- **NEW: practicals from the lighting schedule.** Downlights with IES profiles and pendants on at low level for warmth, even in daytime shots. Listed in the skill as "not built yet".
- **NEW: sheers as diffusers.** Drawn sheers soften the window and fix the blown-out glazing problem without dropping exposure.

### Step 6. Camera and composition (as now, plus a checklist)
The skill's lens, height, lens-shift and doorway rules are already pro practice ([lens shift beats tilt, ArchiCGI](https://archicgi.com/?p=10573)). Add the composition checklist in section 4 below and a mandatory "three layers of depth" check (foreground object softly framing, mid-ground subject, background window or view).

### Step 7. Render
- **Drafts:** EEVEE at 600 to 900 px, as now.
- **Finals: GPU, not CPU.** An RTX 4090 scores about 11,600 on Blender's own Cycles benchmark and an RTX 5090 about 16,100 ([Renderjuice, from Blender Open Data, Blender 5.2](https://www.renderjuice.com/gpus/rtx-4090-for-blender)); laptop and desktop CPUs score an order of magnitude lower on the same test (compare at [Blender Open Data, CPU](https://opendata.blender.org/benchmarks/query/?compute_type=CPU&group_by=device_name&blender_version=5.2.0)). Our 37 minute CPU still should land in a few minutes on one rented 4090. That turns one attempt per hour into ten, which is what art direction needs.
- Finals at an adaptive noise threshold of about 0.01 with OIDN (albedo and normal), sequences with a fixed seed (already), more glossy bounces (6 or so) where glass and stone reflect each other.
- **NEW: render passes for post.** AO, mist (depth), cryptomatte (object and material) and a separate light-group pass for windows vs practicals. These let the grade adjust one light or one material without re-rendering, which is standard in studio post.

### Step 8. Post-production (NEW as its own step)
Studios finish in Photoshop, Resolve or the renderer's frame buffer: exposure and white balance, a light S-curve, gentle bloom/glare on highlights, a subtle vignette, sharpening at output size, and restraint ([ArchiCGI: avoid extreme post](https://archicgi.com/?p=10573); the Architizer making-ofs show Photoshop as the last stage: [Lugano Lake House](https://architizer.com/blog/practice/tools/the-art-of-rendering-how-to-create-lugano-lake-house/)). For us, a saved Blender compositor setup (Glare, Lens Distortion with very low dispersion, a vignette mask, Color Balance) applied identically to stills and sequences keeps sequences flicker-free. Never sky replacement or object removal on a buyer-facing image.

### Step 9. Optional AI polish (narrowed)
See section 6. Stills only by default; sequences only through the clay-driving route with `qa_drift.py` passed.

### Step 10. Site build, QA gate, hand-over
As now. The QA gate in the skill is stronger than anything found in published studio practice. Add a finishes-drift check for AI output (gap 9 below).

---

## 3. What separates a 3/10 render from an 8.5/10 one

Grouped by what an art director looks at first. Each line is a pass/fail check for the hero-shot review.

**Light**
- [ ] One clear key light with a direction you can point to; the room falls off from it.
- [ ] No pure blacks in uprights or under joinery; no blown windows unless softened by sheers.
- [ ] Contact shadows under every object; reflections agree with the light.
- [ ] Practicals warm (2700 to 3000 K) against cooler daylight (about 6000 to 6500 K), giving colour contrast.

**Materials**
- [ ] Stone near the camera is a real slab image, not procedural.
- [ ] Glossy surfaces show soft variation, not mirror-perfect.
- [ ] Timber boards and tiles vary slightly from piece to piece.
- [ ] Edges are bevelled (already built: 3 mm).
- [ ] Texture scale checks out against a known object (door, tile, board width). Wrong scale is a classic tell ([D5](https://www.d5render.com/posts/detailing-architectural-rendering)).

**Styling**
- [ ] Soft layer present (sheers, throw, cushions, rug).
- [ ] Life layer present (book, cup, fruit, plant), odd-numbered clusters, varied heights.
- [ ] Nothing floating, nothing intersecting, nothing at an impossible scale.
- [ ] At least 60% of horizontal surfaces clear.

**Camera**
- [ ] Verticals vertical (lens shift, never tilt).
- [ ] Foreground, mid-ground and background all present.
- [ ] Shot from a doorway or edge, wall ends framing the image.
- [ ] Interior horizontal FOV no wider than 90 degrees (already enforced); doesn't oversell size.
- [ ] Subject (island, view, feature wall) on a third, not dead centre unless symmetrical on purpose.

**Finish**
- [ ] Grade is subtle: no crushed shadows, no orange-and-teal look, no heavy bloom.
- [ ] Output sharpened for the final size; no denoiser smear on fine textures (check at 100%).
- [ ] Nothing in the image that a buyer could rely on and isn't in the documents.

These checks come from [ArchiCGI](https://archicgi.com/?p=10573), [Renderahouse](https://blog.renderahouse.com/blog/why-renders-look-fake-6-common-problems-solved), [D5](https://www.d5render.com/posts/detailing-architectural-rendering), [Novedge](https://novedge.com/blogs/design-news/v-ray-tip-v-ray-techniques-for-balanced-and-natural-interior-lighting) and our own blind review.

---

## 4. Scroll experiences: how they're built and shipped

| Approach | Realism | Freedom | Mobile | When to use |
|---|---|---|---|---|
| **Pre-rendered image sequence on canvas** (ours) | Highest: full path-traced frames | Fixed path only | Good if frames are budgeted per breakpoint | Default for every project |
| Video scrubbed by scroll | High | Fixed path | Poor: seeking is asynchronous and lags the scroll ([scroll-sequence skill notes](https://www.ui-skills.com/skills/mengto/scroll-scrubbed-visual-sequence)) | Autoplay loops only, not scrubbing |
| WebGL / Three.js real-time | Medium (baked lighting) | Free camera, configurators | Heavy; needs optimised assets | Unit configurators, later phase |
| Gaussian splats (Spark, SuperSplat) | Photographic, but only of things that exist | Free camera | Keep under about 1M splats; 3M+ splats fail on phones ([PlayCanvas forum](https://forum.playcanvas.com/t/solved-large-3d-gaussian-splatting-file-doesnt-load-on-mobile/38758)); mobile browsers cap GPU memory ([Spark 2.0](https://worldlabs.ai/blog/spark-2.0)) | Progress stories, as-built handover, site context from drone capture. Never for unbuilt interiors |
| Unreal pixel streaming | High, interactive | Full | Needs a GPU server per viewer; about US$0.13 to US$6.60 per user-hour depending on provider ([Game-Ace](https://game-ace.com/blog/unreal-engine-pixel-streaming/), [ZeroLight OmniStream](https://fr.zerolight.com/omnistream), [Eagle 3D at US$100 per concurrent user per month](https://www.eagle3dstreaming.com/?p=4251)) | Display-suite kiosks, not marketing websites |

What award-winning property sites do: full-screen photoreal renders, scroll-revealed, often with WebGL for transitions ([Videinfra on Springs, ERA and Silver Pinewood, Awwwards Site of the Day](https://videinfra.com/blog/best-real-estate-websites-examples); studio-reported). The OPTIKKA case study on Codrops moved from HTML5 video to frame sequences for exactly the seek-lag reason, with separate per-breakpoint sequences and fewer frames on mobile, loaded through a parallel background queue ([Codrops, OPTIKKA](https://tympanus.net/codrops/2025/10/16/creating-smooth-scroll-synchronized-animation-for-optikka-from-html5-video-to-frame-sequences/)). That's what our template already does, plus coarse-to-fine loading and a decode window, which is ahead of most published examples.

**Budgets that hold up:** 90 to 180 frames per move on desktop, about 60% on mobile; WebP quality 70 to 80; under about 120 KB per desktop frame and 8 MB per mobile sequence (current skill numbers, consistent with the 90 frames at about 25 KB mobile example in the [scroll-sequence notes](https://www.ui-skills.com/skills/mengto/scroll-scrubbed-visual-sequence)). Nothing to change here except the render quality going into it.

---

## 5. Cutaways and construction sequences (4D)

- **Pro tools:** Navisworks TimeLiner and Synchro link model elements to programme activities. Twinmotion has its own phasing tool, prettier but less detailed than Navisworks ([IMAGINiT comparison](https://resources.imaginit.com/videos-webcasts/4d-timeline-simulation-navisworks-versus-twinmotion)), and TimeLiner schedules don't carry across into Twinmotion phasing, so phasing gets rebuilt ([Unreal forum](https://forums.unrealengine.com/t/ying-to-import-navisworks-2024-tim-liner-schedule-into-twin-motion-the-animation-schedule-that-was-created-in-navisworks-is-not-showing-in-the-phasing-group/1832139)).
- **Section planes:** V-Ray Clipper does render-time sections with capping (cut faces filled with a solid colour) ([Novedge, V-Ray Clipper capping](https://novedge.com/blogs/design-news/v-ray-tip-v-ray-clipper-non-destructive-render-time-sections-with-capping)); Lumion can animate its clip plane through a construction sequence ([Lumion](https://support.lumion.com/knowledge-base/api/v2/help-center/en-us/articles/how-does-the-clipping-plane-work-in-lumion-2026)); D5 has section planes and section cubes but no confirmed keyframing for growth animation ([D5 docs](https://docs.d5render.com/user-guide/view/how-to-set-section-render-section-diagram)).
- **Our route (no new software needed):** we already keep `IfcClass|GlobalId|Name` per object, which is exactly the key a 4D link needs.
  1. Export the programme (MS Project or P6) to CSV: activity, start, finish.
  2. A mapping CSV from activity to IFC class plus storey (for example "L2 slab pour" to `IfcSlab@LEVEL 02`), checked by the builder.
  3. Blender keys each element's visibility (or a short rise from below) to its activity's dates, one frame per working day or week.
  4. **Slab-by-slab cutaway:** hide every storey above the target, and cut walls of the target storey at about 1.2 m with a boolean or a clip, with capped cut faces in a flat colour. This is the "dollhouse" read buyers understand instantly. Today we only take the roof off.
  5. **Frame to finish:** same camera, two collections (structure only, then everything) rendered as a `compare` pair or a dissolve sequence. Only call it the real frame if the fabricator's model was used (see intake).
- **Progress stories with real captures:** monthly drone or photo captures from fixed positions, optionally splatted, compared against the model at the same camera. That's real evidence, the strongest sales asset a builder can show.

---

## 6. AI in arch-viz: what's responsible now

**Where studios actually use it (late 2026):**
- **Entourage only:** Chaos AI Enhancer turns flat CG people and plants into photoreal ones inside Corona and V-Ray ([Digital Engineering 24/7](https://www.digitalengineering247.com/article/chaos-debuts-several-ai-tools/rendering)). That's the narrowest, safest use.
- **Concept and client review:** Chaos Veras 4.0 runs Nano Banana Pro inside Revit, SketchUp and Rhino ([Architosh](https://architosh.com/2026/02/chaos-releases-veras-4-0-with-nano-banana-pro/)). Practitioner guidance treats the model as fixed geometry and rejects any output that moves a window, wall or perspective ([laozhang blog, constraint-first prompts](https://blog.laozhang.ai/en/posts/nano-banana-pro-interior-design-architecture)); it's "not a CAD, BIM or construction-document system".
- **Upscaling:** Magnific's Creativity slider controls how much detail it invents; low settings stay close to the source, high settings hallucinate ([Scenario help](https://help.scenario.com/articles/8823252319-magnific-upscaling-the-essentials), [Studio Matrx course notes](https://www.studiomatrx.org/students/ai-assisted-design-workflows/upscaling-and-detail)). For anything accurate, the advice is Topaz or low-creativity enlargement.
- **Video:** first and last frame interpolation (Kling, Seedance) between two real renders is the common pattern ([Higgsfield on Kling start/end frames](https://higgsfield.ai/blog/Kling-Start-End-Frames); [RebusFarm news on Nano Banana Pro plus Kling interiors](https://ie.rebusfarm.net/news/nuno-silva-insane-ways-to-use-nano-banana-pro-and-kling-for-interior-animations)). Start and end frames that differ a lot in light or style break the transition. The clay-driving-video variant (white model film as pure motion information) is documented by fal ([fal.ai, clay to AI pipeline](https://blog.fal.ai/from-clay-3d-render-to-a-real-action-short-a-3d-to-ai-pipeline-with-total-control/)); video-to-video restylers (Runway Aleph 2, Kling O3 edit, Luma Modify) claim to keep structure, but those are vendor claims ([Scenario on Aleph](https://help.scenario.com/articles/6499445829-runway-aleph-the-essentials); Krea says Aleph was retired 30 July 2026, [Krea](https://www.krea.ai/apps/video-to-video)).
- **Industry mood:** in CGarchitect's 2024 AI survey, 76.8% named inconsistency as the top concern and 62% said AI isn't production-ready ([CGarchitect](https://cgarchitect.com/features/articles/b24a7fe4-ai-in-architectural-visualization-2024-survey-insights)).

**What nobody publishes:** a geometry verification step. We found no studio or tool that checks AI output against the model. Our `qa_drift.py` (edge maps, per-cell, against the clay render) is ahead of published practice. Keep it; it's a selling point.

**Australian law and disclosure:**
- In *Ripani v Century Legend* [2022] FCA 242 the court found an off-the-plan render misleading under s 18 ACL and held that an "artist's impression" label and contract disclaimers didn't cure it ([Mondaq case note](https://www.mondaq.com/australia/construction-planning/1181696/marketing-offtheplan-apartments-learnings-from-ripani-v-century-legend), [Mallesons](https://pulse.mallesons.com/in-competition/off-the-plan-off-guard-misleading-or-deceptive-conduct-in-property-marketing/)). The Full Court later ordered a limited retrial on reliance only ([Maddocks](https://www.maddocks.com.au/insights/off-the-plan-sales-misleading-deceptive-conduct), [2022] FCAFC 191). The takeaway stands: **accuracy is the defence, the label isn't.**
- NSW agent advertising guidelines already bar altering photos so they no longer fairly represent a property, adding or removing features, or zooming views to look closer ([Aurum Render summary](https://aurumrender.com.au/journal/ai-altered-property-images-australia/), secondary source). A 2025 NSW bill targets misleading AI or digitally altered rental listing images ([ACS Information Age](https://ia.acs.org.au/article/2025/nsw-tackles-ai-real-estate-pics.html)). Check the primary text before relying on its dates.
- Practice guidance: put the disclosure on or beside the image and say what changed ([Aurum Render](https://aurumrender.com.au/journal/ai-altered-property-images-australia/)). Our label "Artist's impression, AI-enhanced from the design model" plus the drawing and finishes revision is the right shape.

**Our rule, unchanged in spirit, narrowed in practice:**
1. AI may add realism to surfaces already decided by the model and schedule. It may not add, move or remove anything.
2. Stills: image-edit polish allowed after Cycles, then `qa_drift.py --samples 1` must pass and a finishes check must pass (gap 9).
3. Sequences: by default no AI. Use the clay-driving route only for a short hero clip, drift-checked frame by frame, and never for window views.
4. Entourage (people, cars) only on stills, never sequences, and never implying amenities that aren't in the documents.

---

## 7. Gap list against SKILL.md, ranked by quality gained per hour

| # | Gap | Fix | Effort | Quality impact |
|---|---|---|---|---|
| 1 | **CPU-only finals.** One attempt per 20 to 60 min kills art direction. | Add a "GPU final" recipe: rent a 4090 by the hour, same `blender -b` command with `device=GPU`, OptiX. Script uploads the `.blend`, shots and assets, pulls frames back. | 3 to 4 h once | Very high: enables everything below, and cleaner frames at the same time |
| 2 | **Styling density (scored 1/10).** | Buy one curated library and build a reusable "styling kit" per room type (kitchen, living, bed, bath, outdoor): soft layer plus life layer, real scale, production materials. Extend `props` with kit presets. | 8 to 12 h once, 1 to 2 h per project | Very high |
| 3 | **No sheers or curtains.** Windows blow out, rooms feel unfinished. | Buy a sheer and curtain pack (Cycles-ready), add a `curtains` prop type that fits a track to each window from the IFC opening bounds. | 3 to 4 h | High |
| 4 | **No art-direction pass.** | Add the section 3 checklist as a required hero-shot review, against the client's reference, before the final render. A person spends 1 to 2 h per hero shot moving props and lights at GPU speed. | 1 to 2 h per shot | High |
| 5 | **Procedural or stand-in stone near camera.** | Intake asks for supplier slab photos (section 2). Map them as `texture` with true slab size. | 1 h per project | High for kitchens and bathrooms |
| 6 | **No imperfection layer.** | One shared node group: roughness variation, smudge on gloss, corner dust, per-piece colour jitter. Off for colour accuracy checks. | 4 h once | Medium to high |
| 7 | **No post-production stage.** | Saved compositor graph (glare, faint dispersion, vignette, curve) applied the same way to stills and sequences; add AO, mist, cryptomatte and light-group passes. | 3 h once | Medium |
| 8 | **No practicals.** Already in "not built yet". | Read the lighting schedule, place IES downlights and pendants at low warm output. | 4 to 6 h once | Medium (high for evening shots) |
| 9 | **No finishes check on AI output** (also in "not built yet"). | Extend `qa_drift.py`: per material region from a cryptomatte or material-index pass, compare mean colour (delta E) between the start render and the AI take; fail over a threshold. | 4 h | Medium, but it's the legal safety net for any AI polish |
| 10 | **Cutaway is roof-off only.** | Storey-off plus wall cut at about 1.2 m with capped faces (section 5). | 3 to 4 h | Medium for apartments |
| 11 | **No 4D or frame stage.** | Programme CSV plus activity-to-IFC mapping, visibility keyed by date (section 5). Frame stage only from the fabricator's model or labelled illustrative. | 8 to 16 h | Medium; high for builder progress stories |
| 12 | **Exposure guidance disagrees.** The script comment at `blender_render.py` line 381 says interiors want +3 to +4.5; SKILL.md says +1.5 to +2.5. | Pick one after the GPU and portal setup, write it once. | 5 min | Low, but stops confusion |
| 13 | **Final noise threshold** is 0.03 with 384 samples. | On GPU, finals at 0.01 and up to 2,048 samples; glossy bounces to 6 for stone and glass. | 10 min | Low to medium |
| 14 | Window views from real capture are specified but rarely available. | Keep the rule (drop the scene rather than fake it). Add a "sheers drawn" fallback so windows read as bright and soft instead of showing an invented view. | 0 h | Protects accuracy |

Items 1 to 5 together are about 20 to 25 hours of build plus a few hours per project, and they cover every gap the blind review named.

---

## 8. Shopping list (AU dollars)

| Item | Cost | Source | Need |
|---|---|---|---|
| Cloud GPU, RTX 4090, by the hour (Vast.ai or RunPod) | about A$0.55 to A$1.15 per hour (US$0.34 to US$0.74 median) | [Findstack comparison](https://findstack.com/resources/runpod-vs-vast-ai) | **Buy now.** A hero still is a few minutes; a 180-frame sequence in two aspect ratios is a few hours: single-digit dollars |
| Managed render farm (GarageFarm, RebusFarm, others), Cycles GPU | about A$0.14 to A$0.40 per 1080p frame (estimate) | [Super Renders Farm estimate](https://superrendersfarm.com/article/cheapest-render-farm-2026) (competitor blog) | Alternative to self-managed cloud for big sequences |
| BlenderKit Full plan | about A$14 per month (US$9) | [BlenderKit pricing](https://www.blenderkit.com/plans/pricing) | Good first styling library, Blender-native |
| Evermotion Archinteriors or Archmodels volume (Blender versions) | about A$45 to A$230 per volume (US$29 to US$149) | [Superhive Evermotion listings](https://superhivemarket.com/tags/evermotion) | One kitchen and one living volume to seed the kit |
| Design Connected or iMeshh subscription | price not found in research; check vendor | [Design Connected](https://designconnected.com/subscriptions), [iMeshh](https://imeshh.com/pricing) | Optional, higher-end furniture |
| Sheer and curtain pack (Cycles) | about A$60 (US$39) | [Superhive curtain pack](https://superhivemarket.com/products/curtain-sheer-pack) | **Buy now** |
| Poly Haven models, HDRIs, textures | free, CC0 | [Poly Haven](https://polyhaven.com/license) | Already used |
| Megascans via Fab | free | [CG Channel](https://www.cgchannel.com/?p=179945) | Plants, scanned surfaces |
| Supplier slab photos | usually free on request | supplier | **Every project with stone** |
| Magnific or Topaz (upscale, AI polish) | price not confirmed in research; check vendor | [Magnific API docs](https://docs.magnific.com/api-reference/image-upscaler-creative/image-upscaler.md) | Optional, stills only |
| D5 Render Pro | about A$560 per year (US$360) | [aitoolsbakery](https://aitoolsbakery.com/blog/d5-render-vs-enscape/) (third party) | Not recommended for us (see below) |
| Enscape Solo | about A$890 per year (US$575) | [MyArchitectAI](https://www.myarchitectai.com/blog/enscape-pricing) (third party) | Not recommended |
| Twinmotion | free under US$1M revenue (verify), else about A$690 per year | [Renderahouse](https://www.renderahouse.com/blog/twinmotion-pricing) (third party) | Optional for quick 4D phasing demos |
| Own GPU workstation (RTX 4090 or 5090) | a 4090 card alone was listed at US$4,899 lowest offer on 13 Nov 2026 | [Renderjuice](https://www.renderjuice.com/gpus/rtx-4090-for-blender) | Not until cloud spend passes about A$150 per month |
| Outsourced hero still from a studio | about A$230 to A$1,240 per interior still (US$150 to US$800, currency unstated in sources) | [Omega Render](https://omegarender.com/3d-rendering-cost), [Contra listing](https://contra.com/s/elsZNeFX-photoreal-3-d-architectural-visualization-and-walkthroughs) | Fallback for a hero shot on a tight deadline |

**Engine choice for a small studio.** Stay on Blender. D5, Twinmotion and Enscape are real-time engines that trade realism for speed and need a GPU anyway; their strength is fast client walkthroughs from Revit or SketchUp, not hero stills at 8+. They'd also replace our scripted, auditable pipeline (finishes CSV, per-element IDs, drift checks) with manual scene work. Corona or V-Ray with Chaos Cosmos is the true studio standard for stills ([Architizer, Corona making-of](https://architizer.com/blog/?p=11284); [Corona blog](https://blog.corona-renderer.com/?p=4954)), but it means 3ds Max and a new pipeline. Not worth it while Cycles plus a GPU plus a styling library closes the gap.

**Laptop CPU, realistically:** framing and EEVEE drafts, clay and outline renders, plan renders, QA, small previews. Not hero finals, not sequences.

---

## 9. Verdict: fastest route to 8+ stills and flawless sequences

**For 8+ hero stills (about two weeks of part-time build, then per project):**
1. Rent a GPU and render finals there (gap 1). Same afternoon.
2. Buy BlenderKit plus one Evermotion volume plus a sheer pack (about A$120 to A$300 one-off), build the kitchen and living styling kits (gaps 2, 3).
3. Get the supplier's slab photo for every stone near camera (gap 5).
4. Add the imperfection node group and the saved post graph (gaps 6, 7).
5. Give each hero shot a 1 to 2 hour art-direction pass against the client's reference, checklist in hand (gap 4).
6. Re-run the blind test on the same kitchen. Expect 6 to 7 after steps 1 to 4 and 7.5 to 8.5 after step 5. If it still sits under 8, the AI still polish with drift and finishes checks is the last 10%, not the first.

**For flawless scroll sequences:** we're already close. Sequences need GPU time (gap 1), the same styling kits (they read at a distance, so less detail is fine), sheers (gap 3), a fixed post graph applied identically to every frame (gap 7), and the 2x scrub and contact-sheet checks already in the QA gate. Don't AI-polish sequences by default; the one exception is a short hero clip through the clay-driving route, frame-checked.

**The honest truth about what it takes:** an 8.5 render is roughly a day of a skilled artist's attention plus a paid asset library and fast hardware. We can automate the accuracy and most of the setup, which no studio does as well, but we can't automate taste. Budget 1 to 2 hours of human judgement per hero still and a few dollars of GPU per shot. If a hero shot is needed faster than that, outsource that one image and keep our pipeline for the sequences, cutaways, plans and QA, where accuracy matters most and our system is already stronger than the market.

---

## Sources not reachable or thin

- The Codrops OPTIKKA article returned 403 to the fetcher; details are from search summaries of it.
- Blender Open Data CPU medians didn't render in the fetcher; GPU scores are from Renderjuice, which cites Blender Open Data.
- No official Design Connected, iMeshh, Magnific or Topaz prices were found.
- No CGarchitect 2025 AI figures were found; the 2024 survey is quoted.
- The final outcome of the *Ripani* retrial wasn't confirmed.
