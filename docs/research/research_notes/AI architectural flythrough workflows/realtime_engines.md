# Real-time and production render engines for archviz fly-throughs (2025-2026)

Research date: 16 Nov 2026. About 22 searches and fetches. Several vendor pages returned 403 or were only partly readable, so some figures come from secondary or reseller sources. Each one is flagged. All prices are USD unless stated. **I found no official AUD price lists.** Any AUD figure below is my own conversion and is marked as an inference.

## Which engines dominate archviz in 2025-2026

### Takeaway
The latest CGarchitect (now Chaos-owned "CGconnect") survey, 2024-25 with results published 2025, still has V-Ray and Corona dominating final-quality work. Real-time engines (Unreal Engine, Lumion, Chaos Vantage) are named as gaining ground, and 56% of respondents already use AI tools in their rendering workflow. I could not extract exact market-share percentages. Blender/Cycles is not a mainstream studio production renderer for off-the-plan marketing.

### Cited Findings
- 2024-25 CGarchitect survey summary: "continued dominance" of V-Ray and Corona; real-time rendering adoption rising, with Unreal Engine, Lumion and Chaos Vantage "gaining traction"; 56% of respondents already integrate AI tools into their workflow. The page gives no per-engine percentages; the full numbers sit in a linked PDF report, and a formula error was corrected and the file re-uploaded. — [CGarchitect/CGconnect 2024-25 survey results](https://cgconnect.chaos.com/features/articles/2120b451-2024-25-rendering-engine-survey-results?from=cgarchitect)
- Note: CGarchitect now redirects to cgconnect.chaos.com. Chaos owns the survey host and also sells V-Ray, Corona, Enscape and Vantage, so treat the survey as potentially vendor-adjacent. — same URL (redirect observed)
- Historical trend (older, 2021): the biggest usage gains were for Unreal Engine and Twinmotion; D5 Render and Blender Eevee entered the top ten. — [CGarchitect 2021 survey results](https://www.cgarchitect.com/features/articles/712bd906-2021-architectural-visualization-rendering-engine-survey-results)
- A CGarchitect editorial says the survey shows AI-assisted tools spreading across more production stages. — [CGarchitect: rise of real-time rendering and AI](https://cgarchitect.com/features/articles/b29a561d-the-rise-of-real-time-rendering-and-ai-in-visualization)

### Inferences
- In practice the market splits into two tiers. **Production path tracers (V-Ray, Corona, usually inside 3ds Max)** make hero stills at 8.5-9/10 off-the-plan quality. **Real-time and hybrid tools (Lumion, Twinmotion, D5, Enscape, Vantage, Unreal)** make animations and architect-facing visuals. Top marketing studios mostly use 3ds Max + Corona/V-Ray for stills, and Unreal or Corona/V-Ray for film.
- Our stack (Blender Cycles) is a capable path tracer. The 4.5 vs 8.5 gap is unlikely to come from the engine itself. More likely causes are assets (furniture, plants, people, scanned materials), lighting and HDRI choice, camera craft and post-production. See the asset-library section below.

### Gaps
- Exact 2025 per-engine percentages (primary and secondary engine share). They live in the survey PDF, which I could not fetch.
- No independent (non-Chaos) 2025-26 survey found. A 2025-26 CGarchitect survey edition, if one exists, did not surface.

## How each engine takes in BIM (Revit / ArchiCAD / IFC / Datasmith / LiveSync), and whether IFC works directly

### Takeaway
**Native IFC import is rare.** Unreal Engine has a Datasmith IFC importer. Twinmotion's official import table **does not list IFC**: it relies on Datasmith Direct Link from Revit, ArchiCAD and others, or on FBX, glTF, SKP or OBJ. For D5, Lumion and Enscape I found no confirmation of direct IFC import; they are fed by live-sync plugins inside the authoring tool. For an IFC-first pipeline, Unreal (Datasmith IFC) or our own IFC-to-FBX/glTF/USD conversion is the realistic route.

### Cited Findings
- **Twinmotion** supported imports: geometry `.udatasmith`, `.gltf`, `.glb`, `.fbx`, `.skp`, `.obj`, `.wire`. It also takes Datasmith Direct Link "with most major design applications", animation via fbx/gltf, and point clouds (.e57, .las and others). **IFC is not listed.** From 2026.2 Preview, `.3ds`, `.c4d`, `.dae`, `.dxf` and `.stl` can no longer be imported directly. glTF materials with complex shaders get converted to generic Twinmotion materials. — [Epic: Import process in Twinmotion](https://dev.epicgames.com/documentation/en-us/twinmotion/import-process-in-twinmotion)
- Twinmotion 2025.2 notes cover Datasmith imports, Revit and Rhino Direct Link, SketchUp, Archicad via Datasmith, FBX, glTF/GLB, Alias .wire and E57 point clouds. Meshes now use Nanite, and Datasmith export to Unreal (5.5.4-5.6.0) is supported. — [Twinmotion 2025.2 release notes](https://dev.epicgames.com/documentation/en-us/twinmotion/twinmotion-2025-2-release-notes)
- A reseller (IMAGINiT, Sep 2025) names FBX, OBJ, SKP and C4D as the "preferred" Twinmotion formats that keep hierarchy, geometry and materials. IFC is not mentioned. — [IMAGINiT: Autodesk to Twinmotion formats](https://resources.imaginit.com/building-solutions-blog/autodesk-to-twinmotion-preferred-and-accepted-file-formats)
- **Unreal Engine**: Epic documents a Datasmith IFC importer in the editor toolbar. IFC carries little surface-property control, so Epic advises replacing Datasmith's default materials with physically based ones. IFC element properties are kept as metadata, accessible in the editor and at runtime. — [Epic: Importing IFC files into Unreal using Datasmith](https://dev.epicgames.com/documentation/unreal-engine/importing-ifc-files-into-unreal-engine-using-datasmith?lang=en-US)
- I found no evidence that UE 5.6's newer Interchange framework handles IFC. The Interchange USD import is reported to have production blockers in 5.6. — [UE forum: Interchange USD in 5.6](https://forums.unrealengine.com/t/interchange-usd-import-in-ue-5-6-unsupported-schemas-incomplete-blueprint-conversion-block-production-adoption/2653604)
- **D5 Render**: LiveSync plugins exist for SketchUp (D5 2.5+), 3ds Max (2.6+), Rhino and Vectorworks (2.7+). The requirements page does not mention IFC. — [Renderahouse: D5 system requirements](https://www.renderahouse.com/blog/d5-render-system-requirements). Other sources list SketchUp, Revit, Rhino and ArchiCAD import but not IFC. — [summary of D5 pricing sources, e.g. Capterra](https://www.capterra.com/p/10005615/D5-Render/pricing/)
- D5 3.0 adds alpha-stage import of 3D Gaussian Splatting (.ply/.gs) and a procedural City Generator. — [CGPress: D5 3.0](https://cgpress.org/archives/d5-render-3-0-introduces-ocean-simulation-volumetric-clouds-ai-tools-and-more.html)
- **Lumion**: LiveSync plugins for Revit, ArchiCAD and Rhino; imported models carry lights and material settings. No IFC import was found in 2025 sources. — [Lumion 2025 release (search summary)](https://lumion.com/news/lumion-2025-release)
- **Chaos Vantage 3** (15 Oct 2025) supports USD and MaterialX for asset exchange across pipelines; Vantage 3.4 (Sep 2026) adds OpenPBR. — [Chaos: Vantage 3 press release](https://www.chaos.com/press/chaos-releases-vantage-3-unlocking-real-time-creative-options-to-accelerate-the-aec-workflow); [CG Channel: Vantage 3.4](https://www.cgchannel.com/2026/09/chaos-releases-vantage-3-4/)
- **Enscape** runs as a plugin inside Revit (now Revit 2026), SketchUp, Rhino, ArchiCAD and Vectorworks. No IFC import route was found. — [Chaos Enscape premium page](https://www.chaos.com/enscape/premium)

### Inferences
- Studios almost never feed raw IFC to a renderer. Typically Revit or ArchiCAD goes through LiveSync/Direct Link into Lumion, Twinmotion, D5 or Enscape, or BIM is exported to 3ds Max (FBX/Datasmith) and **re-materialised and dressed by hand**. Our IFC-to-Python-to-Blender conversion is not unusual. The automated step studios skip is the manual dressing pass.
- For our pipeline, **USD** is the most future-proof hand-off: Vantage, Unreal (with caveats) and Blender all read it, and Blender exports it headlessly.

### Gaps
- Whether D5, Lumion or Enscape accept a raw .ifc file in 2026. Vendor docs were not reachable (D5's site returned 403).
- Datasmith IFC importer status in UE 5.6/5.7 (still supported or deprecated) is unconfirmed.

## Asset libraries: size, quality, and how much of the photorealism they supply

### Takeaway
Every commercial tool ships a curated library of 10,000 to 22,000+ scanned or high-poly assets: furniture, plants, people, decals and PBR materials. Chaos also has an AI pass that upgrades people and vegetation. This is the single biggest difference from "a few CC0 props". Off-the-plan realism comes largely from dense, believable dressing: books, throws, styled kitchens, plants, scanned materials with real imperfection.

### Cited Findings
- **Chaos Cosmos**: Chaos added ~30,000 assets (Evermotion and Globe Plants) in August 2025 and calls Cosmos "the largest, smartest curated 3D asset library for AEC". — [Chaos press release](https://www.chaos.com/press/chaos-adds-30000-assets-to-chaos-cosmos-making-it-the-largest-smartest-curated-3d-asset-library-for-aec-professionals); [CG Channel Aug 2025](https://www.cgchannel.com/2025/08/chaos-cosmos-gets-30000-new-evermotion-and-globe-plants-assets/)
- Cosmos tiering: the Chaos FAQ cites 11,824 assets for Solo, 13,236 for Premium and 14,648 for the top tier. Chaos upgrade pages show around 14,443-14,596 for Solo accounts and invite users to "unlock" 4,310-7,555 more. A 2026 third-party guide quotes up to 15,000 (V-Ray Solo) and 22,000+ (Collection). These figures conflict; the Cosmos browser shows the true count per login. — [Chaos Cosmos](https://www.chaos.com/cosmos); [Chaos V-Ray Cosmos upgrade](https://www.chaos.com/vray/cosmos-assets); [Renderahouse V-Ray pricing](https://www.renderahouse.com/blog/vray-pricing)
- Vantage 3 adds the Chaos AI Material Generator inside the Cosmos browser. — [Chaos Vantage 3 press](https://www.chaos.com/press/chaos-releases-vantage-3-unlocking-real-time-creative-options-to-accelerate-the-aec-workflow)
- **D5**: "over 16,000 official assets" (third-party summary of D5 material). — [Renderahouse: D5 requirements](https://www.renderahouse.com/blog/d5-render-system-requirements). D5 3.0 adds AI Asset Recommendation and AI image-to-3D. — [CG Channel D5 3.0](https://www.cgchannel.com/?p=173279)
- **Lumion**: total library quoted as "+10,000 objects, characters and materials"; a reseller says 6,900+ objects and 1,250+ materials (conflicting). Lumion 2025 added 129 children/education models, 68 fine-detail nature assets, 14 materials and 9 styles. — [Lumion 2025 features](https://support.lumion.com/hc/en-us/articles/19338614680732-Latest-Features-and-Improvements-of-Lumion-2025); [Lumion 2025 release search summary](https://lumion.com/news/lumion-2025-release)
- Lumion discontinued its $749/yr Standard tier, which had about half the library assets. — [CG Channel: Lumion 2025.0](https://www.cgchannel.com/2025/05/lumion-releases-lumion-2025-0/)
- **Twinmotion**: Megascans content through its Library with on-demand cloud downloads (2025.2). 2026.1 added 10 new European tree species with three variations each, plus a persistent asset folder. — [Twinmotion 2025.2 notes](https://dev.epicgames.com/documentation/en-us/twinmotion/twinmotion-2025-2-release-notes); [Twinmotion 2026.1 news](https://www.twinmotion.com/news/twinmotion-2026-1-is-here)
- **Chaos AI Enhancer** automatically upgrades flat or low-quality people and vegetation in renders to photoreal. It started in Enscape in 2024 and reached Corona and V-Ray 7 for 3ds Max by late 2025, with advanced refinement controls planned for Enscape, Corona and V-Ray 7 (Max, SketchUp, Rhino, Revit). — [Digital Engineering: Chaos debuts AI tools](https://www.digitalengineering247.com/article/chaos-debuts-several-ai-tools); [Chaos Veras 3.0 announcement](https://www.chaos.com/blog/chaos-unveils-several-new-ai-tools-led-by-veras-30-with-image-to-video-generator-for-aec)

### Inferences
- People and vegetation are the classic realism killers. Chaos built an AI feature just to fix them, which suggests even studios with big libraries struggle there. Our CC0 people and plants are probably a major drag on the 4.5 score.
- **Unverified, from background knowledge:** Megascans/Fab licensing for Unreal-engine use is free, and Blender can use Megascans via Fab or Bridge under the Fab licence. Check current Fab terms before relying on this.

### Gaps
- No source quantifies "percent of realism from the library". The weighting is a qualitative inference.
- Fab/Megascans licence terms for non-Unreal renders (Blender) in 2026 were not verified.

## Built-in AI features: what they actually do

### Takeaway
The AI in these tools is mostly **assistive post-processing and scene setup**: upscaling, people and vegetation enhancement, mood or lighting matching from a prompt or reference, material generation from photos, text or image to 3D props, and image-to-video concept tools. None of them generates a whole finished render from BIM; geometry and lighting remain classic rendering.

### Cited Findings
- **D5 Render 3.0** (released 7 Jan 2026): the AI Agent (first in 2.11) gains **Scene Match**. You describe a mood, the agent generates reference visuals, then one click matches your scene's lighting and post-processing parameters. It also gains **Asset Recommendation** from text or reference images. Other AI items: AI PBR Material Snap, enhanced AI Atmosphere Match, optimised "Post-AI" image enhancement, and AI image-to-3D (single or multi-view photos) on top of the text-to-3D from 2.7. Non-AI 3.0 additions: ocean simulation, volumetric clouds, displacement material (beta) and Gaussian splat import (alpha). — [D5 forum release notes](https://forum.d5render.com/t/release-notes-of-d5-render/5791); [CG Channel D5 3.0](https://www.cgchannel.com/?p=173279); [CGPress D5 3.0](https://cgpress.org/archives/d5-render-3-0-introduces-ocean-simulation-volumetric-clouds-ai-tools-and-more.html); [Architosh D5 3](https://architosh.com/2026/02/d5-version-3-released-new-ai-workflows/)
- D5 3.1 released 15 July 2026 (content not detailed). — [Renderahouse](https://www.renderahouse.com/blog/d5-render-system-requirements)
- **Lumion 2025**: the only AI feature is an AI upscaler for Photo Mode that "doubles the resolution of images in seconds", at launch for classic import only (not LiveSync). Other 2025 features are non-AI: RT volumetrics, fully ray-traced water, and a Radiance Cache GI that reduces flicker. A Lumion Pro 2026 release exists (contents not verified). — [Lumion 2025 features](https://support.lumion.com/hc/en-us/articles/19338614680732-Latest-Features-and-Improvements-of-Lumion-2025); [Lumion 2025.0 release notes](https://support.lumion.com/hc/en-us/articles/19336065135516-Lumion-2025-0-Release-Notes)
- **Chaos Veras 3.0** (Sep 2025): generative AI with image-to-video for AEC, turning a render or viewport into short AI video clips. Veras became fully integrated into Enscape, V-Ray and Corona (Architosh, May 2026). — [Chaos Veras 3.0 press](https://www.chaos.com/press/chaos-unveils-several-new-ai-tools-led-by-veras-30-with-image-to-video-generator-for-aec); [AEC Magazine](https://aecmag.com/news/chaos-launches-ai-image-to-video-generator); [Architosh: Veras integration](https://architosh.com/2026/05/enscape-v-ray-and-corona-get-veras-ai-integration/)
- **Chaos AI Enhancer**: see the asset-library section (people and vegetation upgrade). Enscape Premium includes Veras Basic and AI Enhancer. Chaos sells AI credits as top-ups. — [Chaos Enscape premium](https://www.chaos.com/enscape/premium); [Chaos credits](https://www.chaos.com/get-more)
- **Chaos AI Material Generator** (in the Cosmos browser, Vantage 3). — [Chaos Vantage 3](https://www.chaos.com/press/chaos-releases-vantage-3-unlocking-real-time-creative-options-to-accelerate-the-aec-workflow)
- **Twinmotion**: the 2025.2 and 2026.1 notes show **no generative AI features**. 2026.1 adds photo-match backplates (vanishing points auto-solve camera and focal length), anamorphic and Petzval bokeh, barrel distortion, autofocus, "Autosoft Edge" (soft bevelled edges in Standard, Lumen and Path Tracer) and reworked fire, smoke and water VFX. — [Twinmotion 2026.1 news](https://www.twinmotion.com/news/twinmotion-2026-1-is-here); [CG Channel 2026.1](https://www.cgchannel.com/?p=175368)
- The CGarchitect AI article asks whether AI is "a shift in workflow or just a trend". — [CGarchitect AI article](https://cgarchitect.com/features/articles/d2128492-ai-in-architectural-visualization-a-shift-in-workflow-or-just-a-trend)

### Inferences
- Twinmotion's **Autosoft Edge** speaks to a likely tell in our renders: perfectly sharp CAD edges from IFC geometry. Small bevels on edges are a classic realism fix that our Python conversion could add automatically, for example with Blender's Bevel modifier or a bevel shader node.
- AI enhancers are applied **after** the render on stills. For animation, temporal consistency is a problem, which is why Veras video is pitched at concepts, not final marketing films.

### Gaps
- Enscape-specific AI beyond AI Enhancer and Veras (for example any 2026 Enscape AI features) was not verified.
- No independent quality evaluation of D5 Scene Match or Lumion's upscaler found.

## Fly-through specifics: camera paths, interior and exterior transitions, phasing and 4D, render times

### Takeaway
All the real-time tools have keyframe camera paths and sequencers. Twinmotion added animator time offsets for **phasing** and an **Exploder** animator (2025.2), and its Sequence tool now drives animators. Unreal's Sequencer plus Movie Render Queue is the high-end standard. I found no reliable cross-engine render-time benchmark. One measured UE5 data point is about 14 s per frame at 4K (Lumen or Path Tracer, TAA x64), GPU unstated.

### Cited Findings
- **Twinmotion 2025.2**: Translator and Rotator animators redesigned; time offset on children creates a **phasing effect**; new **Exploder Animator** for exploded views; the Sequence tool playhead now controls animators and animated assets, with new Track edit modes (Default, Scale, Loop). — [Twinmotion 2025.2 release notes](https://dev.epicgames.com/documentation/en-us/twinmotion/twinmotion-2025-2-release-notes)
- **Twinmotion 2025.1**: the path tracer is declared **production-ready**, with volumetric clouds and spatial denoiser improvements. 2025.1.1 fixes black viewports in path tracer with animated imports in sequences. — [Twinmotion 2025.1 release notes](https://dev.epicgames.com/documentation/twinmotion/twinmotion-2025-1-release-notes); [2025.1.1 notes](https://dev.epicgames.com/documentation/en-us/twinmotion/twinmotion-2025-1-1-release-notes)
- Twinmotion path tracer needs Windows and a DX12 DXR GPU. — [search summary of Epic docs](https://dev.epicgames.com/documentation/twinmotion/twinmotion-2025-1-release-notes)
- **D5 3.0**: path tool optimisations; Showreel, Spatial Tour and XR Tour opened to individual users. — [CGPress D5 3.0](https://cgpress.org/archives/d5-render-3-0-introduces-ocean-simulation-volumetric-clouds-ai-tools-and-more.html)
- **UE5 render time (measured)**: a 4K, 1,109-frame sequence took 4h15m with Lumen and 4h12m with Path Tracer (about 13.8 and 13.6 s per frame), TAA x64, PNG, 24 fps. The GPU was not stated (the host offers RTX 4090 servers), the scene is a film scene not archviz, and the article's prose contradicts its own numbers. — [iRender: UE5 Lumen vs Path Tracer](https://irendering.net/unreal-engine-5-on-rtx-5090-for-archviz-lumen-path-tracer-and-movie-render-queue/)
- RTX 5090 is about 17% faster than 4090 in Unreal 5.5 (Puget, via reseller); Lumion stills and 4K video export 15-38% faster on 5090 vs 4090. — [iRender: RTX 5090 for archviz](https://irendering.net/rtx-5090-for-architectural-visualization-d5-lumion-twinmotion-and-unreal-engine-tested/)
- D5 RTX 4090 review: about 34 fps average in an archviz viewport (vendor, 2023, older). — [D5: RTX 4090 review](https://www.d5render.com/post/nvidia-rtx-4090-d5-render-review)
- UE 5.6 MRQ: a forum report of a memory-leak crash after 2-3 h on long 1080p sequences with 64 GB RAM. — [UE forum](https://forums.unrealengine.com/t/movie-render-queue-long-sequence-memory-leak-crashes-after-2-3-hours-ue5-6-1080p-64gb-ram/2636773)

### Inferences
- Rough arithmetic: a 45 s, 30 fps scroll animation is 1,350 frames. At ~14 s per frame (4K) that is about 5 h on a high-end GPU in UE5. At 1080p, or in Lumen real-time mode with lower AA, it is plausibly under an hour. Real-time tools (Lumion, D5, Twinmotion standard mode) typically render 1080p frames in about 1 s or less. This is an inference from the single data point plus the fact that these engines run in real time; it is not a benchmark.
- Tower-to-unit-to-room transitions are not a named feature anywhere. Studios cut between separate camera shots, or use section planes and cutaways plus a continuous camera in Sequencer or Twinmotion sequences. Twinmotion's Exploder and phasing animators are the closest built-in tool for a "cutaway" reveal.
- **4D**: no 2025-26 source found on Synchro or Navisworks tie-ins to these engines. Twinmotion phasing is animator-based, not schedule-driven.

### Gaps
- No apples-to-apples render-time benchmark of Lumion, D5, Twinmotion, Unreal and V-Ray on one consumer GPU for a 30-60 s animation.
- Synchro / Navisworks 4D to Twinmotion or Unreal integration in 2025-26 was not researched within the call budget.

## Scripting and headless automation for a repeatable per-project pipeline

### Takeaway
**Only Unreal Engine (and Blender, which we already use) are properly scriptable and headless-ish.** Unreal Movie Render Queue runs from the command line with Python executors. Epic and the community recommend launching the full editor via command line rather than true headless, and there are 5.6 stability caveats. I found no documented scripting or headless API for Twinmotion, D5, Lumion or Enscape; they are GUI tools.

### Cited Findings
- Epic: MRQ command-line rendering has a reduced argument set; customisation goes through Python executors, registered via `init_unreal.py` so the engine can parse them into a UClass usable from the command line. — [Epic: Command-line rendering with MRQ](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-command-line-rendering-with-move-render-queue-in-unreal-engine)
- Community tutorial: run a custom Python executor in the full editor launched from the command line, calling `subsystem.render_queue_with_executor_instance(custom_executor)`. A forum reply says it is "generally recommended to launch the full editor" on render farms; fully headless attempts had issues (VRAM growth past 11 GB and crashes on early UE5). — [UE forum community tutorial](https://forums.unrealengine.com/t/community-tutorial-command-line-rendering-with-unreal-engine-movie-render-queue/681764/13); [UE forum: render without editor](https://forums.unrealengine.com/t/movie-render-queue-render-without-launching-editor/491881)
- UE 5.6 issues: memory-leak crashes on long sequences, and single-frame ranges not rendering. — [UE forum leak](https://forums.unrealengine.com/t/movie-render-queue-long-sequence-memory-leak-crashes-after-2-3-hours-ue5-6-1080p-64gb-ram/2636773); [UE forum single frame](https://forums.unrealengine.com/t/ue-5-6-cannot-render-a-single-frame-extra-frame-required/2762889)
- Twinmotion 2025.2 release notes mention no automation or scripting. — [Twinmotion 2025.2 notes](https://dev.epicgames.com/documentation/en-us/twinmotion/twinmotion-2025-2-release-notes)

### Inferences
- A repeatable automated pipeline realistically means **Blender (current)** or **Unreal**: IFC to Datasmith or USD, Python placing assets, Sequencer cameras, MRQ. Lumion, D5, Twinmotion and Enscape fit a human artist dressing each project, not a hands-off pipeline.
- **Unverified, from background knowledge:** Unreal's Python editor API covers asset placement, material assignment and Sequencer authoring, so the whole of our Blender script logic could be ported. The cost is a much heavier toolchain (about 100 GB install, C++/Python plugin setup).

### Gaps
- Whether D5 or Twinmotion expose any undocumented CLI or batch render. None was found.
- Chaos Vantage, V-Ray and Corona scripting: V-Ray and Corona are scriptable through 3ds Max (MAXScript or pymxs), but this was not verified in sources this session.

## Pricing (AUD where possible) and hardware

### Takeaway
Twinmotion and Unreal are free below US$1M company revenue, so cost does not block a pilot. D5 Pro is about US$360/yr, Lumion Pro about US$1,149/yr (reseller figure), V-Ray Solo about US$515-540/yr and Corona Solo about US$395/yr. Vantage is now bundle-only. The GPU baseline is an RTX 3060-class card (12 GB) recommended and RTX 3090/4090 (24 GB) for animation. **No official AUD prices were found.**

### Cited Findings
- **Twinmotion**: free for companies under US$1M annual gross revenue, plus students, educators and hobbyists, with commercial work allowed. The free edition lacks Twinmotion Cloud. Above the threshold, about US$445 per seat per year. From 27 May 2026, Unreal Subscriptions no longer include Twinmotion and RealityScan. — [Epic blog: pricing update](https://www.unrealengine.com/en-US/blog/we-are-updating-unreal-engine-twinmotion-and-realitycapture-pricing-in-late-april); [Renderahouse Twinmotion pricing 2026](https://www.renderahouse.com/blog/twinmotion-pricing); [CG Channel: new pricing](https://www.cgchannel.com/2024/03/new-pricing-for-unreal-engine-twinmotion-and-realitycapture)
- **Unreal Engine**: non-game use is free below US$1M revenue; above that the Unreal Subscription was US$1,850 per seat per year (2024 figure, may be outdated). — [CG Channel 2024](https://www.cgchannel.com/2024/03/new-pricing-for-unreal-engine-twinmotion-and-realitycapture)
- **D5**: Community free for non-commercial use; Pro US$38/mo or US$360/yr; Teams US$708 per seat per year (two-seat minimum). Windows only (DX12). — [Capterra D5 pricing](https://www.capterra.com/p/10005615/D5-Render/pricing/); [D5 pricing post](https://www.d5render.com/posts/render-pricing-d5-plans)
- **D5 hardware**: minimum GTX 1060, Intel Arc A3 or AMD RX 6400 (DXR); recommended RTX 3060 or 3060 Ti with 32 GB RAM; "optimal" RTX 3090 with 128 GB RAM. This predates 3.0. Another source says the minimum is an RTX 2060. — [Renderahouse D5 requirements](https://www.renderahouse.com/blog/d5-render-system-requirements)
- **Lumion**: Pro about US$1,149/yr, View US$229/yr, Studio US$1,499/yr (aggregator, Oct 2025, unverified). The Standard US$749/yr tier was discontinued. — [Lumion 2025 search summary / CG Channel](https://www.cgchannel.com/2025/05/lumion-releases-lumion-2025-0/)
- **Chaos**: V-Ray Solo US$84.90/mo or US$514.80/yr; Corona Solo US$59.90/mo or US$394.80/yr (May 2025). A 2026 article gives V-Ray Solo at US$540/yr. Vantage is no longer sold standalone, only in the V-Ray or Corona Collection. — [CG Channel May 2025: Chaos plans](https://www.cgchannel.com/2025/05/chaos-updates-v-ray-corona-and-enscape-subscription-plans/); [Renderahouse V-Ray pricing](https://www.renderahouse.com/blog/vray-pricing); [CG Channel Vantage 3.4](https://www.cgchannel.com/2026/09/chaos-releases-vantage-3-4/)
- **Enscape**: pricing text on Chaos pages was garbled (around US$250-575/yr per licence shown); Impact is a separate add-on. — [Chaos Enscape premium](https://www.chaos.com/enscape/premium)

### Inferences
- AUD (my conversion at roughly 1 USD = 1.5 AUD, unsourced, ex GST; Australian resellers often price higher): D5 Pro about A$540/yr; Lumion Pro about A$1,700/yr; V-Ray Solo about A$780-810/yr; Corona Solo about A$590/yr; Twinmotion and Unreal A$0 for Taiger Group at its current revenue.
- For a team on a 16 GB-RAM machine (per owner memory), every engine here prefers 32 GB RAM and a 12-24 GB VRAM GPU for tower-scale scenes and animation.

### Gaps
- Official AUD price lists (vendor sites blocked or USD only).
- Current Lumion 2026 pricing and Enscape 2026 pricing from primary sources.
- Official minimum and recommended GPUs for Lumion 2025/2026, Twinmotion 2026 and Enscape 4.6 (not fetched).
