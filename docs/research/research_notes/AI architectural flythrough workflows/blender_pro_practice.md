# Pro Blender archviz practice vs our headless IFC pipeline (2025-2026)

Scope: what professional Blender archviz artists do differently from our pipeline (IFC -> OBJ -> headless Blender 5.x Cycles, box-projected textures, procedural marble, ~12 Poly Haven props, AgX, portals + fill area lights, Nishita sun, scripted cameras). Our kitchen hero scores 4.5/10 vs a pro 8.5-9/10. Reviewer faults: sparse styling, camera too far back and square-on, stone pattern scale, flat joinery, tiled-looking floor, grey far side, weak AO.

Research method note: 15 web searches, no full-page fetches (budget). Search-result snippets are summaries, so figures below are as reported by the cited page and should be spot-checked before quoting to a client. Items marked "(prior knowledge, not re-checked this session)" come from the researcher's training data, with a URL given for verification.

---

## 1. Asset strategy: which libraries, free vs paid, and licensing for commercial marketing renders

### Takeaway
The single biggest gap is asset density and quality: pros dress a kitchen with dozens to hundreds of high-poly, correctly scaled props and furniture from paid or large free libraries, not a dozen CC0 items. Most major libraries allow commercial renders but forbid redistributing the raw assets, which matters if we ever ship .blend/GLB files to clients.

### Cited Findings
- **BlenderKit**: two licence types, Royalty Free and CC0. Royalty Free allows commercial use without crediting the author but not resale of the asset in the same form; selling products that embed assets is OK if assets are not directly extractable — [BlenderKit licences](https://www.blenderkit.com/docs/licenses/); [BlenderKit FAQ](https://www.blenderkit.com/faq-frequently-asked-questions/)
- BlenderKit free tier (Sept 2025): 48,000+ free models, materials and HDRIs; later reports cite 22,000+ free models, 36,000 free materials, 4,000 free HDRIs usable in commercial projects; paid plan unlocks the rest + 2 GB cloud storage. In Aug 2026 BlenderKit expanded to Maya, Godot and Rhino (60,000 free assets) — [CG Channel Sept 2025](https://www.cgchannel.com/2025/09/get-over-48000-free-3d-models-materials-and-hdris-from-blenderkit/); [CG Channel Aug 2026](https://www.cgchannel.com/2026/08/get-60000-free-3d-assets-for-maya-godot-and-rhino-from-blendkit/)
- BlenderKit has an add-on with in-Blender search/download; the add-on is scriptable in principle, which makes it the most automatable large library — inference from [BlenderKit site](https://www.blenderkit.com/) (no API docs checked)
- **Megascans via Fab**: the 2024 plan was to end free Megascans and keep ~1,500 free assets from 1 Jan 2025 under the Fab Standard License; this was reversed and Epic made the full Megascans library free on Fab, with remaining assets due free by 12 Nov 2026. Fab Standard License covers commercial use in "any engine or DCC tool". Fab listings now show AI-training use as allowed — [CG Channel](https://www.cgchannel.com/?p=179945); [Creative Bloq](https://creativebloq.com/news/the-worlds-biggest-library-of-scanned-assets-for-3d-artists-is-now-free-and-it-seems-that-this-time-its-for-good); [80.lv on 2025 plan](https://80.lv/articles/epic-games-to-launch-tool-for-free-megascans-downloads-in-fab/). Sources are news, not Epic's licence text; verify before relying on it.
- Legacy Megascans claimed via Quixel.com/Bridge fall under the Epic Content License, not Fab Standard — [Unreal forums](https://forums.unrealengine.com/t/access-legacy-megascans-on-bridge-and-quixel-com/2142664)
- **Poliigon**: Individual commercial licence is for solo professionals, not anyone in a multi-person organisation; Business licence allows sharing internally only; assets stay usable after cancelling. Price sources conflict ($12/mo Hobbyist with commercial use limited to portfolio/non-client work vs "from $23/mo" with 50% yearly discount) — [Poliigon licence help](https://help.poliigon.com/en/articles/8749749-asset-use-license); [licenseorg](https://licenseorg.com/guide/3d-assets/poliigon); [SourceForge](https://www.sourceforge.net/software/product/Poliigon); check [poliigon.com/pricing](https://www.poliigon.com/pricing)
- **Design Connected** (high-end designer-furniture replicas, the classic interior styling library): subscription page says downloads cannot be used without an active subscription, and subscriptions are non-refundable — [Design Connected subscription](https://www.designconnected.com/subscription). That makes it a recurring cost if used in a pipeline.
- **Botaniq** (polygoniq vegetation, the standard Blender plant library): full library $129.99 Extended Commercial License; studio tiers $249.99 (2-5 seats) and $389.99 (6-10). Renders may be distributed; assets may not; one licence per user — [polygoniq ArtStation](https://polygoniq.artstation.com/store/Rek0k/botaniq-vegetation-library); [Botaniq FAQ](https://docs.polygoniq.com/botaniq/7.1.1/troubleshooting/faq/)
- **Geo-Scatter** (scattering system for grass, plants, clutter): $99 individual, $299 team (2-6), $899 studio, commercial use in all tiers (older listing, may be out of date) — [Blender Market Geo-Scatter](https://blendermarket.com/products/scatter/ratings?page=1)
- Blender Market "Standard Royalty-Free" licence allows commercial use but needs permission to redistribute — [Blender Market licence types](https://support.blendermarket.com/article/226-understanding-product-license-types)
- Floor Generator 3.0 comes with materials and is sold on Superhive (Blender Market's new name); see section 2 — [Superhive Floor Generator](https://superhivemarket.com/products/floor-generator?num=3&src=top-rated)

### Inferences
- A "pro-grade" Blender interior kit for us would be: BlenderKit (free + paid tier) for furniture/decor bulk, Fab Megascans (now free) for scanned surfaces and small props, Poliigon Business or Megascans for floors/stone, Botaniq for plants, Design Connected only if we need recognisable designer pieces. Rough one-off/annual cost for a solo/small team: Botaniq ~US$130, Geo-Scatter ~US$99 (exteriors only), Poliigon ~US$150-300/yr, BlenderKit Full plan (price not checked), Design Connected subscription (price not checked).
- For automation, the binding constraint is not licence but **curation**: assets need consistent scale, origin, real-world UVs and a tag schema so a script can place them. Expect to build and tag our own curated kit (50-150 kitchen-relevant items) once, then reuse.
- Licensing risk to us: we render marketing images (allowed by all of the above). We must not ship raw assets in deliverable .blend/GLB/web viewers unless the licence allows (BlenderKit RF: OK if not extractable; Botaniq/Poliigon: no).

### Gaps
- Evermotion (Archinteriors/Archmodels), 3DSky/3ddd and Kit-bash licence terms and prices: no search results returned; check vendor sites directly. Note 3DSky is primarily 3ds Max/Corona/V-Ray format, so conversion to Blender is extra work (prior knowledge).
- Archipack (parametric walls/windows/stairs add-on): not researched; less relevant since our geometry comes from IFC.
- BlenderKit Full plan price not confirmed.

---

## 2. Materials: UVs vs box projection, stone, joinery, floors, anti-tiling, imperfections

### Takeaway
Our reviewer's "stone scale, flat joinery, tiled floor" all trace to the same root: world-space box projection on unbevelled, un-UV'd IFC solids. Pros either real-world-UV each surface or replace it with purpose-built geometry (floorboards as actual boards, cabinet doors with bevels and edge banding), then layer anti-tiling and subtle imperfections. Most of this is automatable with Geometry Nodes and scripted node groups.

### Cited Findings
- **Floorboards as geometry**: NodeCrafted Floor Generator 3.0 is a Geometry Nodes add-on that works on any mesh surface and generates boards/tiles procedurally (Standard, specified sizes, Herringbone, Chevron, Hexagon, Basket Weave). A MultiTexture node distributes up to 16 textures randomly across boards for natural variation. Docs say Blender 4.1+, Cycles and Eevee. Full version US$24 (reduced from $38) on Superhive — [Superhive Floor Generator](https://superhivemarket.com/products/floor-generator?num=3&src=top-rated); [manual](https://nodecrafted.gitbook.io/floor-generator-3.0-manual)
- Alternatives: Easy Floor Generator (StillMount, US$15, plain .blend GN setup, no add-on/Python) and an older free open-source Floorboard Generator on GitHub — [Easy Floor Generator](https://superhivemarket.com/products/easy-floor-generator/docs); [GitHub Parquet](https://github.com/clarkx/Parquet); iMeshh also has a Floor Generator v2 — [iMeshh docs](https://pro.imeshh.com/docs/asset-guides/floor-generator)
- **Anti-tiling**: Blender 5.0 has no built-in "Texture Variation" node, but 5.0 added **shader closures and bundles**: "a closure is a set of nodes that can be passed into a node group, and then evaluated one or more times. This makes it possible to perform blended box mapping, tiling and texture bombing with arbitrary procedural textures" — [Blender 5.0 rendering release notes](https://developer.blender.org/docs/release_notes/5.0/rendering/)
- Third-party anti-tile: Patchwork (lists Blender 5.0+, and a free version at kunemann.com), V-Tile Pro (Blender 4.2-5.3, anti-tile mode), Anti-Tile 2 (directional blending, micro-displacement compensation, procedural masking), original Anti-tile (no 5.0 statement found) — [Patchwork](https://superhivemarket.com/products/patchwork); [V-Tile Pro](https://superhivemarket.com/products/v-tile); [Anti-Tile 2](https://blendermarket.com/products/anti-tile-2); [Anti-tile FAQ](https://superhivemarket.com/products/anti-tile/faq)
- **Bevels**: real objects have small bevels; sharp CG corners read as fake. Use Bevel modifier and add slight asymmetry — [MyArchitectAI photoreal guide](https://www.myarchitectai.com/blog/photorealistic-rendering); [D5 detailing](https://www.d5render.com/posts/detailing-architectural-rendering)
- **Imperfections**: scratches, dust, faint stains, colour variation; keep them subtle, excessive bump/displacement looks artificial; small imperfections are more effective than large — [D5 detailing](https://www.d5render.com/posts/detailing-architectural-rendering); [Medium: 6 tips](https://medium.com/scribblings-of-an-artist/6-tips-for-more-realistic-renderings-4e7ecc41d873)
- Blender also offers a Bevel shader node (render-time rounded edges without geometry) (prior knowledge, not re-checked; see [Blender manual shader nodes](https://docs.blender.org/manual/th/5.0/render/shader_nodes/textures/index.html) section index)

### Inferences
- **Stone**: pros typically use a high-res photo of a real slab (supplier slab scans or Poliigon/Megascans marble) mapped once across the benchtop at true size (a slab is ~3.2 x 1.6 m), with veining running continuously around the edge profile and waterfall ends book-matched. Procedural marble with box projection gives wrong vein scale and visible seams. Automatable: yes, if the script UV-unwraps benchtop solids with a "real-world size" planar unwrap aligned to the longest edge and loads a slab texture with known physical dimensions.
- **Joinery**: IFC cabinets are usually single boxes. Pros model door/drawer fronts as separate panels with 1-2 mm reveals (shadow gaps), 0.5-1 mm edge bevels, edge-banding as a slightly different material, handles/pulls from an asset library, and kickboard recess. Automatable: partly. A Geometry Nodes "cabinet skinner" can split a front face into a door grid from IFC dimensions, inset gaps and bevel, but it needs rules per cabinet type and breaks on odd IFC geometry.
- **Floor**: replacing the box-projected floor with Floor Generator boards (random length, per-board texture/tint offset, micro bevels so each board catches light) fixes "tiled-looking floor" almost entirely. Automatable: yes (apply GN modifier to the floor slab's top face via script).
- **Anti-tiling on walls/large surfaces**: build one closure-based "texture bombing" node group in 5.0 and apply to every large material. Automatable: yes.
- **Imperfection layer**: a shared roughness-variation + dust/fingerprint grunge overlay driven by AO/pointiness masks, applied at low strength to all materials. Automatable: yes, but needs taste-tuning once.
- **UVs generally**: box projection is the root issue. Smart UV Project or Cube Projection with "Scale to bounds" off and a texel-density pass, run per object at import, gets most of the way to "real-world UVs". Automatable: yes.

### Gaps
- No published supplier slab library for Blender found; whether Australian stone suppliers (e.g. Caesarstone, Smartstone) provide downloadable high-res slab images under usable terms was not checked.
- No Blender-specific edge-banding generator found in this search.
- Anti-tile add-on behaviour in headless/background mode not verified.

---

## 3. Lighting and camera for interiors

### Takeaway
Pros shoot interiors from eye-level-ish heights (around 1.2-1.6 m) with level cameras and shifted lenses for straight verticals, from a corner or oblique angle (two-point), usually 24-35 mm and often tighter, and they compose close detail shots as well as wide heroes. Lighting is HDRI/sun-led with exposure set so windows are bright but not blown, then fill and light linking to rescue dark areas, then AO-like contact shadows from real geometry detail rather than an AO pass.

### Cited Findings
- Blender has no native two-point camera; the Two-Point Perspective extension (Blender 4.2 LTS+) converts a 3-point camera to 2-point with a manual target angle — [BlenderNation Nov 2025](https://www.blendernation.com/2025/11/11/blender-for-architecture-how-to-use-a-2-point-perspective-like-sketchup/); [Blender Extensions two-point](https://extensions.blender.org/add-ons/two-point-perspective/)
- Without an add-on: keep the camera level and use Shift X/Y to reframe while preserving verticals — [Columbia Smorgasbord technical camera](https://smorgasbord.cdp.arch.columbia.edu/modules/40-rendering-with-blender/252-technical-camera)
- Keep the camera level so verticals stay parallel, stand off a corner for two-point perspective, shoot at human eye height (~1.55 m) — [Studio Matrx cameras & composition](https://www.studiomatrx.org/students/real-time-vr-for-architecture/cameras-and-composition)
- D5 guidance (renderer-agnostic): 50 mm (~46 deg FOV) feels natural for human-scale interiors; wider 24-35 mm used with two-point correction for interior framing; wider lenses exaggerate the room so keep moderate — [D5 camera tips](https://www.d5render.com/posts/camera-setting-tips-must-known-for-archviz)
- Paid add-on Archviz Camera claims vertical correction for Blender 3.0-4.5 — [Gumroad Archviz Camera](https://xyz360.gumroad.com/l/blender-archviz-camera)
- Composition is "one of the hardest parts and also the most important"; start from classic setups such as central perspective — [Architizer photographic approach](https://architizer.com/blog/?p=9961)
- MIR (Bergen) describes their images as "more like emotions than stories"; a partner's stated specialism is composition and colour — [Designboom MIR interview](https://www.designboom.com/architecture/visualization-studio-mir-interview-trond-greve-andersen-mats-andersen-06-02-2021/); [MIR team](https://www.mir.no/team)
- Mark Hunter (Third Aesthetic): photorealism and grading alone are no longer enough; distinctive styling matters more — [Composite interview](https://composite.substack.com/p/composite-interview-with-mark-hunter)
- Light linking was added to Cycles in Blender 4.0, letting a light affect only chosen objects (prior knowledge, not re-checked; see [Blender 4.0 Cycles notes](https://developer.blender.org/docs/release_notes/4.0/cycles/))

### Inferences
- Map to reviewer faults:
  - **"Camera too far back and square-on"**: move to 1.1-1.4 m height (kitchen benches are 0.9 m, so slightly above looks at the benchtop), stand off a corner at roughly 20-35 deg to the main run, 24-28 mm for the hero, then 35-50 mm secondaries, plus 85-100 mm detail crops (tap, stone edge, styled vignette). Shift Y instead of tilting. Automatable: yes. Camera candidates can be generated from room bounds and the "hero" element (island/benchtop) and scored by rules (verticals straight, hero occupies 40-60% of frame, rule-of-thirds placement, no wall plane square to the lens unless deliberately one-point). A human (or a vision-model judge) picking among 10-20 candidates is the realistic middle ground.
  - **"Grey far side"**: usually exposure plus too little bounce. Pros raise exposure for the interior and let windows go bright, add a large soft area light behind camera or bounce cards linked only to the far wall/cabinets (light linking), increase light bounces (diffuse/glossy 8-12+), and use warmer HDRI/sun to give colour separation. Automatable: yes (per-scene auto-exposure from a low-sample test render's luminance histogram, plus a linked fill on the darkest large surface).
  - **"Weak AO"**: in Cycles, real contact shadows come from geometry detail (reveals, gaps, bevels, kickboard recess, objects resting on surfaces) and enough samples/bounces. Our flat IFC boxes have no crevices, so nothing occludes. Fixing joinery geometry (section 2) fixes this more than an AO pass would. An AO pass multiplied subtly in compositing is a cheap crutch. Automatable: yes.
- HDRI + sun vs portals: portals help noise in Cycles but do not add light; most pro Blender interiors use an HDRI (sky) plus sun through the window for direct patches, and portals only where the window is small. Our setup is reasonable; the gap is exposure and bounce, not the light rig type.
- "Binyan / Mir style": these studios are recognised for photographic restraint, considered styling and strong colour grading (prior knowledge). MIR's own words stress mood over literalness. No technical recipe from them found.

### Gaps
- No source found with explicit Binyan technical breakdowns (lenses, heights).
- No independent study of camera heights used by pro interior archviz; the 1.2-1.6 m range is from course material, not a survey.

---

## 4. Post-production

### Takeaway
Pros finish every hero in post: render passes (Cryptomatte, AO, light groups) into Photoshop/Lightroom or Blender's compositor for selective grading, glare/bloom on highlights, vignette, local contrast and sometimes AI upscaling or AI detail passes. Almost all of this is scriptable in Blender's compositor; the taste of the final grade is the non-automatable part.

### Cited Findings
- Cryptomatte gives pixel-precise masks per object or material with one click, for selective edits — [Studio Matrx render passes & compositing](https://www.studiomatrx.org/students/architectural-visualization-rendering/render-passes-and-compositing)
- The Glare node adds subtle bloom around bright specular highlights, simulating lens behaviour; Fog Glow or Streaks with a low threshold and conservative settings is suggested — [Studio Matrx](https://www.studiomatrx.org/students/architectural-visualization-rendering/render-passes-and-compositing); [Rays Blender lesson 49](https://rays-blender.netlify.app/lesson_49_architectural_visualization)
- GPU viewport compositing lets glare, curves and colour nodes be previewed live without re-rendering — [Studio Matrx](https://www.studiomatrx.org/students/architectural-visualization-rendering/render-passes-and-compositing)
- One studio reports spending 6-12 hours per image in Photoshop post-processing — [FlyingArchitecture process](https://flyingarchitecture.com/blog/the-process-and-communication-in-archviz-process)
- Quality bar used in a course: would someone without context assume it is a photograph? — [MyArchitectAI photoreal guide](https://www.myarchitectai.com/blog/photorealistic-rendering)

### Inferences
- A scripted Blender compositor chain for us: light groups (sun, sky, fills) so balance can be re-mixed without re-rendering; Cryptomatte for joinery/stone/floor masks; mild Glare (Fog Glow, high threshold); lens distortion/chromatic aberration at very low values; vignette; AgX with a "Punchy"/contrast look plus a curves node; denoise with OpenImageDenoise. Automatable: yes, as a fixed preset; per-image grading taste: partly (a vision-model judge can pick among 3-5 preset grades).
- AI upscaling (render at lower res then upscale) and AI "enhance" passes (img2img at low denoise to add micro-detail) are common shortcuts in 2025-26; they risk altering geometry/materials, which matters for client-accurate kitchens. Use only at low strength.

### Gaps
- No primary source found on how many pros now use AI upscalers (e.g. Topaz, Magnific) in final archviz deliverables; anecdotal only.
- Light Groups availability/behaviour in Blender 5.x background mode not verified in this session.

---

## 5. Artist time and price per hero image; who does it

### Takeaway
A pro hero still typically represents roughly 12-20+ artist hours (more with revisions) spread over days to weeks, and sells for about US$250-2,200 for interiors and US$300-3,000+ for exteriors, with offshore studios at the bottom of the range and North American/European boutiques at the top.

### Cited Findings
- Per-image ranges: exterior US$500-3,000, interior US$700-2,200 (one 2025 guide); another gives residential interiors US$250-2,000 and exteriors US$400-2,800 — [VisEngine 2025 guide](https://visengine.com/architectural-rendering-cost-guide-2025); [CadCrowd 2025](https://www.cadcrowd.com/blog/?p=41642)
- Studio starting prices: Render3DQuick interior from ~US$249, exterior from ~US$499; ArchiCGI residential interior from US$150 (US$250 large rooms), residential exterior from US$300, commercial exterior from US$600, aerial from US$1,200 — [Render3DQuick 2026](https://render3dquick.com/blog/how-much-does-3d-rendering-cost); [ArchiCGI interior cost factors](https://archicgi.com/cgi-services/interior-rendering-cost-10-factors)
- Premium: Omega Render interior from US$1,400 — [Omega Render](https://omegarender.com/3d-rendering-cost)
- Regional: UK £350-850+ per exterior, £400-850+ per interior; rates from ~US$200 in South Asia to ~US$2,500 in North America — [7CGI](https://7cgi.com/how-much-does-rendering-cost/); [Fotober 2026](https://fotober.com/3d-rendering-pricing)
- Time: one studio deck describes a ~4-week cycle per image with 2-6 h render time per frame in Corona; another source says 2-5 days per high-quality image; CGArchitect users cite ~12 h per image and ~15 h at large studios; one pricing table assumes ~20 h in-house labour per render — [Chevallier archviz course slides](https://cgg.mff.cuni.cz/~jaroslav/papers/2018-archvizcourse/slides/02-chevallier-archvizintro.pdf); [CGArchitect forum](https://forums.cgarchitect.com/topic/79516-how-long-time-do-you-get); [CGArchitect forum timeframe](https://forums.cgarchitect.com/topic/73693-timeframe-for-jobs); [CadCrowd 2026](https://www.cadcrowd.com/blog/?p=50813)
- Lighting and cameras are often handled by senior artists at studios — [CGArchitect forum](https://forums.cgarchitect.com/topic/79516-how-long-time-do-you-get)

### Inferences
- AUD conversion (approx. 1 USD = 1.5 AUD, not checked live): offshore interior ~A$225-400, mid-market A$1,000-2,000, boutique A$2,000-3,300+ per still.
- Our cost advantage only matters if output reaches roughly mid-market quality (7+/10). At 4.5/10 we compete with AI staging tools (US$1-25/month), not studios.
- The ~12-20 h per image is mostly modelling, styling, materials and revisions, not rendering; this is exactly the part our pipeline skips.

### Gaps
- No systematic time-tracking survey; all hours are anecdotal.
- No Australian-specific price survey found.

---

## 6. Published attempts to automate archviz end to end (BIM -> render, auto furnishing, AI staging)

### Takeaway
Nobody publicly ships a fully automated "BIM in, magazine render out" pipeline. The market splits into (a) geometry-faithful but not final-quality AI renderers on top of BIM (Veras), (b) layout/floorplan-to-3D platforms with auto-furnishing from large proprietary catalogues (Coohom/Manycore, Planner5D, Rayon), (c) photo-based AI staging (Collov, Spacely), which looks good but is dimensionally unreliable, and (d) research on indoor scene synthesis. Accuracy evidence is mostly vendor marketing.

### Cited Findings
- **Veras (now under Chaos)**: plugs into Revit, SketchUp, Rhino, Archicad, Vectorworks and renders from actual geometry; trades creative freedom for fidelity; "not a replacement for final-quality CGI" (studios still use Enscape/Lumion/V-Ray for print/animation); not yet suitable for planning-commission detail; from US$29/month (annual); shared image/video credit pool; reviewer scores 5.5/10 and 4.2 — [AI Tools Bakery review](https://aitoolsbakery.com/blog/veras-review/); [Nomic glossary](https://www.nomic.ai/glossary/veras-ai); [BDC Network](https://www.bdcnetwork.com/home/blog/55274792/embracing-ai-in-architectural-renderings); [AI Tools Atlas](https://aitoolsatlas.ai/tools/veras/pros-cons); [Chaos Veras](https://www.chaos.com/veras/lp)
- **Coohom (Manycore Tech)**: April 2026 "AI Instant" uses a proprietary "Spatial LM" that reads room dimensions and circulation to propose furniture arrangements (press release, no technical detail) — [Coohom press release](https://aeo.washinmura.jp/ai/coohom-hong-kong-limited/en/news/2026-04-23-coohom-announces-ai-instant-a-next-gener)
- **Manycore research**: SpatialLM (NeurIPS 2025) is an LLM that takes point clouds and outputs structured indoor layouts; SpatialGen (Aug 2025) generates 3D indoor scenes from a semantic layout plus text or a reference image, weights on Hugging Face — [SpatialLM arXiv 2506.07491](https://arxiv.org/html/2506.07491v1); [SpatialGen arXiv 2509.14981](https://arxiv.org/html/2509.14981v3); [KrASIA on Manycore](https://kr-asia.com/once-a-3d-design-startup-manycore-now-wants-to-give-ai-a-sense-of-place)
- **Rayon**: browser floor-plan tool; claims accuracy (unverified); an "AI architect" that populates furniture from prompts appears only as a community feature request — [Rayon floor plans](https://www.rayon.design/use-cases/floor-plan-creation); [Rayon community request](https://community.rayon.design/feature-request-148a63yx/post/rayon-ai-architect-VejbjRhvmxxn24Z)
- **Collov AI** (real-estate virtual staging, ~US$19/month) and **Spacely AI** (sketch/3D-model rendering for design firms, ~US$25/month) — no accuracy data found — [MyArchitectAI interior tools 2026](https://www.myarchitectai.com/blog/ai-interior-rendering-tools)
- Photo-based AI apps work from a single 2D image with no spatial model and may distort proportions or furniture sizes; renders can look convincing while containing significant errors — [Coohom: is AI home design accurate](https://www.coohom.com/article/is-ai-home-design-accurate)
- One vendor comparison claims ~99% spatial accuracy for traditional 3D vs ~75% for generative AI staging, and US$15-45 vs US$1-5 per image (single vendor, unverified) — [Bella Virtual Staging](https://www.bellastaging.ca/blogs/news/discover-the-latest-advancements-in-virtual-staging-software-for-2025-an-in-depth-guide)
- Research on LLM-driven scene layout and procedural interiors exists: Holodeck (CVPR 2024, LLM-generated 3D environments with Objaverse assets), LayoutGPT (NeurIPS 2023), Infinigen Indoors (CVPR 2024, procedural Blender-based indoor scenes) (prior knowledge, not re-checked) — [Holodeck arXiv 2312.09067](https://arxiv.org/abs/2312.09067); [LayoutGPT arXiv 2305.15393](https://arxiv.org/abs/2305.15393); [Infinigen Indoors arXiv 2406.11824](https://arxiv.org/abs/2406.11824)

### Inferences
- **Infinigen Indoors is the closest public analogue to our pipeline** (Blender, procedural, headless, constraint-based furniture/clutter placement). Its rule system for "objects on surfaces" (stacking, clutter on benches) is directly relevant to fixing "sparse styling". Worth reading its constraint language before writing our own styling placer (prior knowledge).
- **Hybrid is the realistic state of the art**: accurate geometry from BIM + rule- or LLM-driven styling placement from a curated tagged asset kit + good camera/lighting presets + optional low-strength AI img2img pass for micro-detail. Pure AI staging fails client accuracy; pure procedural fails taste.
- None of the vendors publish quality scores against pro renders; claims of "photoreal" should be read as "good enough for real-estate listings".

### Gaps
- Archilogic, Planner5D, Kujiale specifics: no results returned in this session.
- No independent benchmark comparing automated tools against studio renders on a fixed scene.

---

## Consolidated checklist (pro practice -> tools/assets -> cost -> automatable?)

Costs in USD as found; AUD ~x1.5 (unchecked rate).

| # | Pro practice | Tools / assets | Cost | Automatable? |
|---|---|---|---|---|
| 1 | Dense, curated styling (40-150 items per kitchen hero: bowls, boards, books, plants, stools, pendants, appliances) | BlenderKit, Fab Megascans, Poliigon, Botaniq, Design Connected | Free (BlenderKit free/Megascans) to ~US$130-300 one-off + subscriptions | **Partly**: placement rules (Infinigen-style constraints or LLM layout) can be scripted; curating/tagging the kit and art-directing vignettes is human |
| 2 | Real-world UVs, true-scale textures | Smart UV / cube projection per object at import, texel-density script | Free | **Yes** |
| 3 | Stone from real slab photos, continuous veining, book-matched waterfalls | Supplier slab images, Poliigon/Megascans marble | Free-subscription | **Yes** for mapping; slab choice is human |
| 4 | Joinery as real panels: reveals, bevels, edge banding, handles, kickboard recess | Geometry Nodes cabinet skinner, Bevel modifier/shader, handle assets | Free (dev time) | **Partly**: rule-based from IFC dims; odd cabinets need hand fixes |
| 5 | Floorboards as geometry with per-board variation | NodeCrafted Floor Generator 3.0 / Easy Floor Generator / free GitHub generator | US$0-24 | **Yes** |
| 6 | Anti-tiling on large surfaces | Blender 5.0 closures (texture bombing), Patchwork (free version), V-Tile Pro, Anti-Tile 2 | Free-~US$30 | **Yes** |
| 7 | Subtle imperfection layer (roughness variation, dust, smudges, edge wear) | Grunge maps (Poliigon/Megascans), AO/pointiness masks | Free-subscription | **Yes** (tune once) |
| 8 | Camera: 1.1-1.6 m height, level, Shift for verticals, oblique/two-point, 24-35 mm hero + 50-100 mm details | Blender Shift X/Y, Two-Point Perspective extension | Free | **Yes** for generating candidates; **partly** for choosing the best (human or vision-model judge) |
| 9 | Exposure set for the interior, bright windows, extra bounces, linked fills on dark zones | Cycles light linking (4.0+), bounce settings, auto-exposure from test render | Free | **Yes** |
| 10 | Contact shadows from geometry detail rather than AO pass | Follows from 4, 5 and 1 | Free | **Yes** (as a consequence) |
| 11 | Compositing: light groups, Cryptomatte masks, mild glare, vignette, curves, AgX look | Blender compositor | Free | **Yes** (preset); grading taste **partly** |
| 12 | Photoshop/Lightroom finish, sky/view replacement through windows | PS/LR, or compositor + backplate | ~US$15-25/mo Adobe | **Partly** |
| 13 | AI upscale / low-strength AI detail pass | Topaz, img2img models | Varies | **Yes**, but risks altering client-accurate detail |
| 14 | Mood, narrative, art direction (MIR/Binyan style) | Human | 12-20+ h per hero at studios | **No** |
| 15 | Exterior: scattered vegetation, entourage, context | Botaniq + Geo-Scatter | ~US$130 + US$99 | **Partly** (scatter is scriptable; composition is not) |

Priority order to close the reviewer's specific faults fastest (inference): camera rules (8) -> floor generator (5) -> joinery skinner + bevels (4) -> slab-mapped stone (3) -> exposure/linked fills (9) -> styling kit + placement rules (1) -> anti-tile + imperfections (6, 7) -> compositor preset (11). Items 8, 5, 9 and 11 are cheap and fully automatable; 1 and 4 are where the real effort lives.
