# Neural 3D, world models and 4D construction visualisation for archviz (2025-2026)

Context: current pipeline is IFC model -> headless Blender Cycles -> frame sequences for a scroll website (tower exterior -> cutaway -> room; frame -> finished construction stages). Research date: 16 Nov 2026. Maturity labels used: RESEARCH (paper/demo only), BETA/PREVIEW (gated or beta product), PRODUCTION (shipping, documented, used commercially).

## 1. Gaussian splatting / NeRF: can a synthetic Cycles render set become a splat for smooth web fly-throughs?

### Takeaway
Yes, and it is now a documented workflow (PRODUCTION for the web viewers, BETA/early for Blender-native training add-ons). Training from Blender renders is easier than from photos because camera poses are exact, so the structure-from-motion step goes away. The output is a free-camera, real-time asset that streams to the browser. Known weak spots are glass, plain walls, thin structures and view-dependent effects, which are exactly the features of a glazed tower. A splat augments the frame-sequence pipeline rather than replacing it.

### Cited Findings
- Training splats from renders rather than photos: poses are exact, so no structure-from-motion step is needed, and alpha masks come free. A headless Blender script rendered 120-200 views at 1024² with alpha in about 30 s per model. Training took 21-22 s (6,000 steps at 400²) on an RTX 3060 using gsplat. Web exports came out at 39-229 KB per object as SPZ, against 25-55 MB source meshes. The web viewer was Spark on three.js. Article dated 11 Nov 2026; the use case is game props, not buildings. — [RadianceFields: Training Gaussian Splats From Renders, Not Photos](https://radiancefields.com/training-gaussian-splats-from-renders-not-photos)
- The same article lists failure modes: floaters, lighting baked into the training renders, detail lost when source textures were low-res, and the trade between opaque splats and "soft, view-dependent look". It does not address glass or reflections. — [RadianceFields](https://radiancefields.com/training-gaussian-splats-from-renders-not-photos)
- Splatlight (Blender add-on) builds splats from Blender scenes without a COLMAP solve, passing Blender's known camera poses straight to the trainer. It supports Blender 4.2-5.2 with EEVEE or Cycles, and its LITE tier is free. — [RadianceFields: Splatlight](https://radiancefields.com/splatlight-generates-gaussian-splats-from-blender-scenes-without-a-colmap-solve)
- Splat Stage (Superhive add-on) is in beta and requires Blender 5.3 with native Gaussian splat support. — [Superhive: Splat Stage](https://superhivemarket.com/products/splat-stage)
- A peer-reviewed precedent: a 2026 ISPRS paper uses Blender Cycles renders of a parametric (castle) model as synthetic training images for a 3DGS hybrid used in real-time visualisation. — [ISPRS Archives XLIX-B2-2026-551](https://isprs-archives.copernicus.org/articles/XLIX-B2-2026/551/2026/)
- World Labs Marble opened splat creation on 30 Oct 2026, in Marble Studio and as a beta API task, `posedImages2Splats`. The task takes two or more ordered frames, each with an image, its camera and a linear-depth EXR, which is exactly what a Blender render pass can emit. Pricing is 5,000 credits ($5) per refined run and $0.50 per draft run; a run takes 10-20 min. World Labs suggests 8-16 overlapping views for a single room. Its stated weak cases are "skies, foliage, plain walls, windows, thin structures". Output is SPZ/PLY, with `splats2Mesh` available. Atlas for Blender 0.1.2 requires Blender 5.3. — [RadianceFields: World Labs Opens Gaussian Splat Creation in Marble](https://radiancefields.com/world-labs-opens-gaussian-splat-creation-in-marble)
- Web viewers:
  - **Spark** (World Labs) is an MIT-licensed three.js renderer that mixes splats with ordinary meshes and reads PLY, SPZ, SPLAT, KSPLAT and SOG. Spark 2.0 added LoD and streaming; 2.4.0 reads SPZ v4 and accepts custom paged-LoD fetchers. — [GitHub sparkjsdev/spark](https://github.com/sparkjsdev/spark); [RadianceFields Spark 2.4.0](https://radiancefields.com/spark-2.4.0-reads-spz-v4-files-and-opens-paged-lod-to-custom-fetchers)
  - **three.js** merged a native WebGPU splat renderer in r186, with no LoD or chunked streaming. — [RadianceFields: three.js r186](https://radiancefields.com/three.js-merges-a-native-gaussian-splat-renderer-for-webgpu-in-r186)
  - **PlayCanvas / SuperSplat** compresses to the SOG format and streams LoD automatically for large splats (Streamed SOG: LoD levels plus spatial chunks, indexed by `lod-meta.json`, built with splat-transform). It also has a global splat budget for performance tuning. — [PlayCanvas docs: Streaming & Performance](https://developer.playcanvas.com/user-manual/supersplat/streaming/); [Streamed SOG](https://developer.playcanvas.com/user-manual/splat-transform/streamed-sog/); [Performance](https://developer.playcanvas.com/user-manual/gaussian-splatting/building/performance/)
  - PlayCanvas claims a 24M-Gaussian scan streams to a browser at a steady 60 fps on its compute-based WebGPU renderer (June 2026). This is a vendor claim with no independent benchmark found. — [CGWorld](https://cgworld.jp/flashnews/01-202606-SuperSplat.html)
  - PlayCanvas reports SOG compression at about 20x versus PLY. — [PlayCanvas blog: SOGS 20x](https://blog.playcanvas.com/playcanvas-adopts-sogs-for-20x-3dgs-compression)
  - Engine v2.12.0 tuned SOG import for mobile performance. — [RadianceFields v2.12.0](https://radiancefields.com/playcanvas-releases-v2-12-0)
- A vendor guide recommends delivering via Blender -> PLY -> SPZ (about 90% compression, keeps spherical harmonics) or SOG (maximum compression). — [polyvia3d guide](https://polyvia3d.pages.dev/guides/deploy-gaussian-splatting-web)
- The KHR_gaussian_splatting glTF extension is at release-candidate stage, so a standard glTF splat format is near. — [RadianceFields](https://radiancefields.com/training-gaussian-splats-from-renders-not-photos)
- Capture-app status:
  - **Luma AI** stopped radiance-field capture uploads (from about Nov 2024) and sunset its Genie text-to-3D on 1 Jan 2026. It has pivoted to generative video. — [RadianceFields: uploads suspended](https://radiancefields.com/radiance-field-uploads-suspended-on-luma-ai); [Luma sunset](https://radiancefields.com/luma-ai-to-sunset-flythroughs-on-january-1-2026)
  - **Polycam** offers splats on paid tiers and can build splats from existing images and videos. Its pricing conflicts between sources. — [Polycam help](https://learn.poly.cam/hc/en-us/articles/30549121659412-How-to-Create-Photogrammetry-and-Gaussian-splats-from-Existing-Images-and-Videos)
  - **Postshot** (Jawset) is listed at "Free to $199/yr" on one undated comparison page, which is unconfirmed. — [polyvia3d comparison](https://polyvia3d.pages.dev/guides/gaussian-splatting-tools-comparison)

### Inferences
- For an unbuilt building this works well: the BIM model already gives perfect geometry and poses, so splats suit "bake the Cycles look once, explore freely on the web". The likely sweet spot is interiors (the room scene) and a cutaway hero object, more than a glazed tower exterior. Windows, plain walls and sky are documented weak points.
- Because splats bake lighting, each construction stage would be a separate splat (or a per-stage diff). That is feasible but multiplies training runs and payload.
- Cheapest experiment: add a camera-orbit render pass (150-300 views plus depth) to the existing headless Cycles job. Then train with Splatlight, gsplat or Postshot locally, or send views plus depth to Marble `posedImages2Splats` ($5/run). Deliver with Spark (three.js) or a PlayCanvas Streamed SOG.
- A frame sequence still wins on guaranteed look, mobile reliability and art direction. A splat wins on freedom and smoothness, and has a much smaller payload than hundreds of JPG/WebP frames for one shot.

### Gaps
- No independent archviz-specific benchmark of splat quality versus Cycles frames (glass, reflections) was found.
- No independent mobile benchmark of Streamed SOG or Spark LoD was found.
- Postshot's current pricing could not be verified. Spline's splat support was not confirmed; no source found.

## 2. World models and camera-controlled video generation: usable for a specific designed building today?

### Takeaway
Not as a source of truth. World models (World Labs Marble, Google Genie 3) generate plausible environments from a prompt or image but do not preserve exact design geometry. Genie 3 sessions are 60-second explorations at Google Labs preview stage. Video models (Veo 3.1, Kling, Runway) steer the camera mainly by prompt or by first and last frames, not by geometry. The usable path today is to restyle or animate your own renders with structure conditioning: depth via Wan VACE, video-to-video via Runway Aleph, or Veo first/last-frame interpolation between two Cycles frames. Treat it as BETA quality for marketing filler, not for accurate fly-throughs.

### Cited Findings
- Project Genie (Genie 3) launched 29 Jan 2026 as an "experimental research prototype" in Google Labs, for US Google AI Ultra subscribers aged 18+. It takes text or an uploaded image. Generations are limited to 60 seconds, and worlds "may not look completely true-to-life or always adhere closely to prompts, images". The only export is a downloaded video. — [Google blog: Project Genie](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/project-genie/)
- One non-authoritative source reports Genie 4 announced in Oct 2026 as a limited trusted-tester research preview. Unverified. — [SmartScope](https://smartscope.blog/en/blog/genie-4-release-date-access-differences-genie-3-2026/)
- World Labs Marble generates 3D worlds and exports SPZ/PLY splats and GLB meshes. A high-quality mesh export costs 3,500 credits ($2.80), and PLY splat export is free. Export and commercial rights require paid tiers; the free plan cannot export. — [World Labs docs: splat export](https://docs.worldlabs.ai/marble/export/gaussian-splat); [World Labs API pricing](https://docs.worldlabs.ai/api/pricing)
- Subscription tier prices conflict between sources: Standard about $20/mo and Pro about $35/mo, per secondary reviews. — [invideo](https://invideo.io/blog/world-labs-marble-3d-worlds/)
- Major video platforms (Sora, Runway Gen-4, Veo) "primarily expose prompt-level controls rather than native structural inputs" (secondary source). — [search summary from tractionco / invideo comparisons](https://tractionco.com/insights/can-ai-simulate-cinematic-camera-movement)
- Veo 3.1 first/last-frame mode takes two endpoint frames and interpolates between them under a text prompt. Camera moves are named in the prompt (dolly, pan, tracking and so on). It is available via Replicate and fal. — [Replicate blog: Veo 3.1](https://replicate.com/blog/veo-3-1); [fal: Veo 3.1](https://blog.fal.ai/veo-3-1-is-now-available-on-fal/); [Scenario: Veo 3.1 essentials](https://help.scenario.com/articles/1049410120-veo-3-1-the-essentials)
- Runway Gen-4 is credited with the strongest multi-shot consistency. A critique notes styling can drift from the photoreal reference, which is a risk for architectural accuracy. Kling 3.0 is positioned as the cheapest per clip. — [Atlas Cloud comparison](https://www.atlascloud.ai/sv/blog/guides/kling-ai-vs-runway-vs-luma); [seeles.ai](https://www.seeles.ai/resources/blogs/runway-vs-kling-multi-scene-consistency)
- Wan VACE (open weights) supports depth, pose, layout and inpainting as video-to-video structure controls. A ComfyUI "Video Restyle" workflow pairs Wan VACE with Depth Anything v2, and depth preserves 3D structure better than edges. Render time is about 90-180 s per pass. — [VACE paper arXiv 2503.07598](https://arxiv.org/pdf/2503.07598); [Comfy hub: Video Restyle](https://comfy.org/hub/workflows/video-restyle-5931e9bdf9db/); [fal Wan 2.2 VACE depth](https://fal.ai/models/fal-ai/wan-22-vace-fun-a14b/depth/llms.txt); [martini.art](https://martini.art/en/how-to/edit-existing-video/wan)
- Runway Aleph is a video-to-video model that restyles existing footage from a prompt, at source resolution and timing. A launch article claims architecture firms use it (marketing claim). — [Runware: Aleph 2.0](https://runware.ai/models/runway-aleph-2-0); [cliprise](https://www.cliprise.app/news/runway-aleph-launch)

### Inferences
- For a designed tower, accuracy matters: facade module count, floor count and balcony rhythm. Pure prompt or image generation will hallucinate these. The safe uses are:
  - (a) Veo or Kling first/last-frame between two of your own Cycles keyframes, for short connective shots. Expect geometry drift mid-clip.
  - (b) Wan VACE depth video-to-video over a cheap EEVEE or clay Blender animation, to add photoreal atmosphere (weather, people-free ambience) while geometry stays locked by the depth pass.
  - (c) Runway Aleph for restyling, such as time of day or season.
- Generated frames have to be checked frame by frame against the model before they go on a site that sells a real building. That review is a consumer-law exposure for off-the-plan marketing.
- World models are best used for context and environment (a generated neighbourhood or landscape around a real model), not the building itself.

### Gaps
- No source tests these models specifically on architectural straight lines or facade consistency.
- Exact current pricing for Veo, Kling and Runway per second was not gathered; it changes frequently.
- Native depth or camera-trajectory inputs in Kling or Runway were not confirmed from official docs.

## 3. AI 3D asset generation for furniture and styling props: quality versus real catalogue models

### Takeaway
PRODUCTION-usable for background and mid-ground props, not yet for hero furniture or exact branded pieces. A real catalogue model (manufacturer-supplied or a curated archviz library) still beats generated assets on dimensional accuracy, clean topology and material fidelity. All comparisons found are vendor-affiliated.

### Cited Findings
- A June 2026 industry overview positions the tools as follows: Hunyuan3D leads on texture/PBR quality, TRELLIS.2 is the open-source standout, Tripo is fastest, and Rodin is for "film-grade hero assets". — [3D AI Studio: State of AI 3D generation 2026](https://3daistudio.com/state-of-ai-3d-generation-2026)
- Meshy 6 is credited with quad topology, pose and texture-guidance control. Meshy's own blind test claims a 63.8% preference over Tripo 3.1 among 1,331 artists; this is a vendor-run test. — [3D AI Studio: Hitem3D vs Meshy vs Tripo](https://www.3daistudio.com/blog/hitem3d-vs-meshy-vs-tripo-comparison)
- Tripo v3.1 offers quad-mesh FBX output. — [wavespeed.ai](https://wavespeed.ai/blog/3d-model-access/tripo-ai-alternatives/)
- Hunyuan3D-2.5 and TRELLIS are stronger on raw geometry but less clean on production topology. Hunyuan3D's licence is not unrestricted open source. — [cmarix: open source 3D generators](https://www.cmarix.com/blog/top-open-source-ai-models-for-3d-image-generation/)
- For repeatable furniture-type assets, procedural tools such as Sloyd may give more predictable structural control. — [wavespeed.ai: game asset generators](https://wavespeed.ai/blog/3d-model-access/best-ai-tools-for-3d-game-assets/)
- The only furniture-specific claim found, that Rodin suits "industrial furniture design prototypes with accurate dimensional inference", comes from a competitor vendor page. — [Neural4D comparison](https://www.neural4d.com/zh/features/neural4d-vs-tripo-vs-meshy-vs-rodin)

### Inferences
- For our pipeline, generated props are useful for filling rooms quickly (decor, books, plants, ceramics) in a Cycles interior. Hero sofa, kitchen and joinery should come from real models or the IFC itself, because buyers judge finishes and the developer's spec list governs what is shown.
- Generated meshes need a decimate/cleanup pass and material re-assignment before Cycles. Topology matters less for static renders than for games, so the topology weakness is less of a problem for us.

### Gaps
- No independent, same-prompt furniture bake-off across Meshy, Tripo, Rodin, Hunyuan3D and TRELLIS was found.
- Per-asset pricing was not compiled; commercial-licence terms per tool need checking before client use.

## 4. 4D BIM and construction sequencing: how "frame to finished" build-ups are made, and can IFC drive them automatically?

### Takeaway
Two traditions exist. (a) Technical 4D (Synchro, Navisworks TimeLiner, Bentley) links model elements to a real schedule; it is accurate but visually plain. (b) Marketing build-up animations are made in render tools: Twinmotion's Phasing timeline, Lumion, 3ds Max or Blender, by sequencing element visibility and growth by storey and trade. Our IFC-to-Blender pipeline can generate the marketing version automatically. IFC element classes (IfcFooting, IfcColumn, IfcSlab, IfcWall, IfcCurtainWall, IfcCovering...) crossed with IfcBuildingStorey give a natural "frame -> slab -> envelope -> fit-out" ordering without any schedule. Bonsai (ex-BlenderBIM) has basic IfcTask-driven 4D animation, which is still rough.

### Cited Findings
- Bonsai/IfcOpenShell has a sequence module that animates tasks. A developer describes it as "pretty basic right now and hardcoded to a default". Schedules can be imported from P6, MS Project or CSV, and tasks can be scripted with `sequence.add_work_schedule` / `sequence.add_task` and linked to building products. — [OSArch: Make a simple construction sequence](https://community.osarch.org/discussion/comment/9871/); [OSArch: 4D workflow recommendation](https://community.osarch.org/discussion/comment/12520)
- For a sequence without dates, OSArch replies suggest an IfcWorkPlan or IfcWorkSchedule with nested IfcTasks ordered by sequence relationships. Another user reports that Bonsai may not visualise IfcWorkPlan contents. — [OSArch: Visualize an IfcWorkPlan in Bonsai](https://community.osarch.org/discussion/comment/23490)
- A late-2025 proposal aims to bring Bonsai's 4D features closer to commercial tools (work in progress). — [OSArch: Advanced Interactive 4D Planning proposal](https://community.osarch.org/discussion/comment/27307)
- IMAGINiT contrasts Twinmotion's Phasing Timeliner, which gives "less detailed but more visually appealing" output, with Navisworks TimeLiner's schedule-accurate output. Its Jan 2025 guide covers 4D phasing simulations in Twinmotion. — [IMAGINiT: Navisworks vs Twinmotion 4D](https://resources.imaginit.com/twinmotion-tips-and-tricks/4d-timeline-simulation-navisworks-versus-twinmotion); [IMAGINiT: Simulating construction sequences in Twinmotion](https://resources.imaginit.com/twinmotion-tips-and-tricks/simulating-construction-sequences-and-phasing)
- A user request on the Unreal forums asks for Twinmotion to integrate Synchro and Navisworks schedules. Undated, so there may be no direct schedule import. — [Unreal forums](https://forums.unrealengine.com/t/twinmotion-navisworks-integration/126801)
- Industry sources distinguish marketing 4D animations from technically grounded ones and treat both as legitimate. 4D build-ups are widely sold as a service for tenders and marketing. — [Illusion CGI: 4D animation](https://www.illusioncgi.com/blog/blog-title/4D%20Animation%20-%20Bringing%20Architectural%20Projects%20to%20Life); [constructionplacements](https://www.constructionplacements.com/architectural-animation-in-construction-projects/)

### Inferences
- An automatic build-up is achievable in our existing headless Blender job with a small script. Group IFC products by `IfcBuildingStorey` (via IfcOpenShell `get_container`) and by class, in a fixed trade order:
  1. foundations
  2. columns
  3. slabs, storey by storey
  4. cores and walls
  5. curtain wall and windows
  6. roof
  7. coverings and furniture

  Then keyframe visibility, or a growth effect (Z-scale from the slab or a boolean "reveal plane"), per group per frame range. No schedule or IfcTask data is required. If a real programme exists, Bonsai's IfcTask route is the more defensible "true 4D".
- Data quality is the risk: the class and storey assignment in the architect's IFC must be clean. Mis-classed elements (IfcBuildingElementProxy) break automatic grouping, so plan a fallback mapping by layer or name.
- Synchro, Navisworks and Fuzor are planning tools. Their visual output is not marketing-grade, and they add licence cost for no visual gain in our use case. Licence pricing was not researched.

### Gaps
- No primary source was found for Synchro or Fuzor 2025-2026 features or pricing.
- No published end-to-end tutorial for IFC class/storey-driven Blender build-up animation was found (only forum threads).
- How top marketing studios specifically make tower build-ups (tooling share) was not found in a citable form.

## 5. Scroll-driven web 3D: frame sequences versus real-time WebGL versus pixel streaming; what top property sites use

### Takeaway
Award-winning property sites mostly combine pre-rendered imagery with targeted WebGL (an interactive 3D model, map or massing) and GSAP scroll choreography. Frame-sequence scrollytelling remains the safe hero technique. Unreal Pixel Streaming is used for configurators and unit selectors (PRODUCTION, but with ongoing cloud-GPU cost). Gaussian splats are the new middle ground: near-render look at real-time freedom, with no GPU server.

### Cited Findings
- Vide Infra's real-estate work wins Awwwards, FWA and CSSDA Site of the Day:
  - ERA residence: WebGL 3D plus GSAP horizontal scroll.
  - A triple-SOTD project: an interactive WebGL 3D area map, with the camera zooming into render details on scroll.
  - Likova and Silver Pinewood: WebGL scenes built around custom 3D models.

  Source: the agency's own case studies, so self-reported. — [Vide Infra: triple SOTD case study](https://videinfra.com/blog/case-study-a-triple-site-of-the-day-winner-powered-by-webgl); [Vide Infra: Silver Pinewood](https://videinfra.com/work/silver-pinewood-residences); [Awwwards: ERA Residence](https://www.awwwards.com/inspiration/horizontal-scroll-era-residence); [Awwwards real-estate inspiration](https://www.awwwards.com/inspiration_search/real-estate/)
- Pixel streaming for off-the-plan property:
  - APlace runs off-plan tours in the browser via Unreal pixel streaming with Cesium 3D tiles.
  - Buildmedia's pixel-streamed Realspace tool for DevelopWise reportedly cut sales acquisition time (Epic case study, vendor-reported).
  - Away Digital Home streams configurable elevations and finishes.

  — [Cesium blog: APlace](https://cesium.com/blog/2024/03/13/aplace-visualizes-and-customizes-architecture-with-cesium/); [Unreal Engine: buyers fall in love with unbuilt homes](https://www.unrealengine.com/en-US/spotlights/real-time-technology-helps-buyers-fall-in-love-with-unbuilt-homes); [Unreal Engine: home building and real estate sales](https://www.unrealengine.com/spotlights/shaping-the-future-of-home-building-and-real-estate-sales-with-unreal-engine)
- Pixel streaming renders on a local or cloud GPU server and sends video to the browser, so it needs ongoing cloud GPU hosting. — [ArchiCGI: immersive 3D tours](https://archicgi.com/immersive-3d-tours/); [Eagle 3D Streaming real estate](https://eagle3dstreaming.com/solutions/by-use-case/real-estate)
- Other vendors in this space: ZeroLight, Eagle 3D Streaming, PropVR (Epic case study claims 10x revenue, vendor-reported). — [ZeroLight](https://zerolight.com/industries/architecture-real-estate-visualisation); [Unreal: PropVR](https://www.unrealengine.com/en-US/spotlights/propvrs-digital-twins-help-real-estate-developer-boost-revenue-by-10x)
- Splat web delivery uses Spark (three.js) or PlayCanvas Streamed SOG with LoD and a splat budget (see section 1). — [PlayCanvas LoD streaming](https://developer.playcanvas.com/user-manual/gaussian-splatting/building/lod-streaming/); [Spark](https://github.com/sparkjsdev/spark)

### Inferences
- Recommended hybrid for our site:
  - (1) Keep Cycles frame sequences for the hero scroll (exterior -> cutaway -> room, frame -> finished). They give deterministic quality, work on every phone, and are cheap to host.
  - (2) Add one optional "explore" moment as a splat (an apartment interior or a cutaway model) using Spark or PlayCanvas. This is real-time freedom with no GPU server.
  - (3) Reserve pixel streaming for a sales-suite configurator, if a client funds per-session GPU cost.
- A Matterport-style tour of an unbuilt unit is achievable today by rendering 360 panoramas from Cycles at fixed nodes, the classic approach. Splats from the same Cycles scene are the newer, smoother alternative.

### Gaps
- No source quantified which technique the top property marketing sites use most. Evidence is case studies only, mostly agency self-reports.
- Vagon and PureWeb pricing and features were not researched (search budget). Matterport's support for synthetic or unbuilt units was not confirmed.
- No measured payload or performance comparison of frame-sequence versus splat versus WebGL mesh for the same scene was found.
