# Generative-AI workflows for photoreal architectural fly-throughs and hero stills (research date 16 Nov 2026)

Scope note: 19 tool calls (searches and page fetches). Instagram, TikTok and X posts can't be fetched directly, so creator recipes come from articles, case studies, vendor docs and course pages, not from the reels themselves. Where a source is a vendor or a course seller, that is flagged. AUD conversions use an assumed ~1.53 AUD per USD (Nov 2026, approximate, not sourced). Check the live rate before quoting.

## Image stage: turning a clay, viewport or basic render into a photoreal still while keeping the geometry

### Takeaway
There are two working routes. The first is diffusion img2img with structure control (ComfyUI with Flux or SD, depth plus soft-edge or lineart ControlNet maps taken from your own render, low denoise around 0.2-0.35 on the building, higher only on a masked foreground). The second is an instruction-edit model (Nano Banana Pro / Gemini 3 Pro Image, also inside Chaos Veras 4.0) fed a colour-coded viewport with AO and a "keep framing, perspective and materials" prompt. Both hallucinate when pushed. Our pipeline already has the exact depth, normal and mask passes that the ComfyUI route needs, so it is the more controllable fit.

### Cited Findings
**Denoise and ControlNet numbers (ComfyUI / SD / Flux)**
- Global light polish on a whole finished render: denoise 0.2-0.35. Facade-only passes: 0.15-0.25 with structure controls on. Masked foreground (trees, wet paving, people, water): 0.4 and up. Avoid unmasked 0.6 and global 0.45-0.5. Published 30 Jun 2026; the source says it is a workflow essay, not a test log. — [ArchiGen AI, Enhance a Render Without Hallucinating It](https://archigenai.com/ai-render-enhance-without-hallucination-denoise-controlnet-architects-2026.html)
- Same source: use a depth pass plus a soft-edge or lineart pass generated from the original render. Keep control strength firm on the building and ease it off over the foreground. Full-weight lineart over the whole frame makes the image stiff and pulls materials back toward the original flat look. No numeric weights are given. — [ArchiGen AI](https://archigenai.com/ai-render-enhance-without-hallucination-denoise-controlnet-architects-2026.html)
- Generating from lineart (not enhancing an existing render) uses much higher values: ControlNet strength about 0.3-0.8 with KSampler denoise 0.7-1.0. This conflicts with the 0.2-0.35 polish range above. The difference is generate-from-scratch versus enhance. — [ERNIE-Image ControlNet guide (May 2026)](https://ernie-image.app/blog/ei-036-ernie-image-controlnet-practical-guide-en-20260510)
- Generic two-pass advice: several seeds per configuration, then an img2img refine at about 0.3-0.4 denoise, plus an optional second Canny pass to tighten detail. — [Botmonster ControlNet guide](https://botmonster.com/posts/stable-diffusion-controlnet-generate-images-sketches-depth-maps/)
- The usable denoise band "is narrow" and moves with the model. Consistency comes from fixed seeds, locked prompts, per-view conditioning and usually a reference image. Runs on a 24 GB card or rented GPUs. Article dated 21 Jul 2026. Names Flux and Stable Diffusion; no specific ControlNet models. — [ArchiGen AI, The ComfyUI Archviz Question Nobody Answers](https://archigenai.com/comfyui-archviz-question-nobody-answers-2026.html)
- When only a flat render exists, Depth Anything 3 can estimate relative depth from one image, but it can't recover exact dimensions or hidden surfaces. Thin elements (railings, cables, mullions) vanish or grow halos, and ControlNet may read the halos as real edges. — [ArchiGen AI, Recover Depth From Flat Renders](https://archigenai.com/depth-anything-v3-flat-render-control-comfyui-architects-2026.html)

**Nano Banana Pro / Gemini image edit**
- CGwisdom recipe (SketchUp to Nano Banana Pro, 17 Dec 2025): (1) export a view with colours and rough textures, not a clay render; (2) turn off dense edge lines on plants and decor (they become black blotches) and set edges to colour by material; (3) turn on Ambient Occlusion (SketchUp 2025) so the model reads contact and depth; (4) export with the short edge at least 1440 px; (5) paste into Nano Banana Pro in Gemini; (6) prompt for lighting, style and mood, plus a keep-clause such as "Keep the materials, framing and perspective as it is"; (7) Rerun or open a new chat to reset history. Output can exceed 4000 px. — [CGwisdom](https://cgwisdom.com/blog/sketchup-and-nano-banana-pro-photorealistic-visualizations-in-5-minutes-is-this-the-end-of-v-ray.html)
- Same source: a clay render makes the model guess materials ("doesn't know if the white floor is resin, carpet, or bleached wood"). Post-processing a finished V-Ray render gives the model less room to interpret. V-Ray and Corona stay the standard where correct scale and real lighting matter. Mirrors fail unless you describe what they reflect. — [CGwisdom](https://cgwisdom.com/blog/sketchup-and-nano-banana-pro-photorealistic-visualizations-in-5-minutes-is-this-the-end-of-v-ray.html); [CGwisdom interior guide](https://cgwisdom.com/blog/nano-banana-pro-in-interior-design-a-complete-guide-with-ready-made-prompts.html)
- Blender-native option: the Nanode AI Render Engine add-on (v2.8.0, GPL-3.0, Blender 4.5/5.0) sends depth and mist passes, Eevee renders and style references to Nano Banana models ("convert depth/mist passes into finished images" while keeping camera and geometry). Models: Nano Banana 2 Lite (`gemini-3.1-flash-lite-image`), Nano Banana 2 (`gemini-3.1-flash-image`), Nano Banana Pro (`gemini-3-pro-image`), Nano Banana (`gemini-2.5-flash-image`). It also has masked edits, first/last-frame Veo 3.1 video, and an "Omni" mode that restyles a captured Eevee or Workbench animation (720p only). A personal Google API key bypasses its credits. — [GitHub Kovname/nano-banana-render](https://github.com/Kovname/nano-banana-render)

**Vendor tools**
- Chaos Veras 4.0 (Feb 2026) runs on Google's Nano Banana. Chaos claims fewer artifacts and better accuracy. User reports are mixed: one says it respects Revit geometry, another says it "takes too much creative liberty" even with geometry override set low. — [Chaos press release](https://www.chaos.com/press/chaos-veras-40-now-powered-by-nano-banana); [aitoolsbakery Veras review 2026](https://aitoolsbakery.com/blog/veras-review/)
- Veras outputs are visualisation aids, not dimensionally, code or constructability accurate. — [datadrivenaec Veras](https://datadrivenaec.com/tools/veras)
- Magnific: Creativity invents detail, HDR adds local contrast, Resemblance pulls toward the source (positive = faithful). Magnific's own site says artifacts come mostly from Creativity or HDR set too high or Resemblance set wrong. There is an Architecture content mode, and a "Precision" mode that upscales without inventing detail. — [Magnific docs](https://www.magnific.com/de/ai/docs/image-upscaler); [Higgsfield upscaler roundup 2026](https://higgsfield.ai/blog/best-ai-image-upscalers-2026); [aitoolsatlas Magnific review](https://aitoolsatlas.ai/tools/magnific-ai/review)
- Magnific and Topaz are positioned for upscaling and detail recovery, and they work best from a reasonably strong base render. — [RunDiffusion upscaling guide (Dec 2025, updated Apr 2026)](https://www.rundiffusion.com/ai-upscaling-tools-for-architectural-renders)
- A vendor (MyArchitectAI) claims Magnific is a general creative upscaler and does not preserve structure as well as its own tool. Treat this as a competitor claim. — [MyArchitectAI, Magnific vs Topaz](https://www.myarchitectai.com/blog/magnific-vs-topaz)
- Krea positions its Agent and Enhance tools for exploration, controlled edits and final-board enhancement, and notes many AI tools stop at screen resolution without a separate upscale. — [Krea, best AI tools for architectural rendering 2026](https://www.krea.ai/blog/best-ai-tools-for-architectural-rendering-in-2026)

### Inferences
- Our 4.5/10 still most likely suffers from a clay or under-materialled look, flat light and missing entourage. The sources point to: render a colour/material pass plus AO (not clay), add depth, normal and line passes from Blender (exact, not estimated, which avoids the Depth Anything halo problem), run ComfyUI at 0.2-0.35 denoise globally with depth plus lineart, run masked entourage and sky at 0.4+, then upscale in Magnific Precision or Creative with low Creativity and high Resemblance.
- Nano Banana Pro is the fastest route to "Instagram look" but is the least controllable on window counts and mullions. Best used for mood and entourage, with QA against the source.

### Gaps
- No published side-by-side test of Seedream, GPT Image, D5 AI, mnml.ai, LookX, ArkoAI or PromeAI geometry fidelity was found in this pass.
- Magnific "Relight" and "Structure" features: no documentation was found in the results. Unconfirmed.
- No sourced numeric ControlNet end_percent values for archviz.

## Video stage: which models give stable architecture, clip limits, and stitching a tower to unit to room move

### Takeaway
The dominant pattern is still-first: perfect each keyframe as a still, then animate with image-to-video, ideally start-and-end-frame (Kling 2.5 Turbo / 3.0 / O1, Veo 3.1) with short, slow camera moves. Long moves are built by chaining clips: the last frame of clip N becomes the start frame of clip N+1. Video-to-video restyling of a clay animation exists (Runway Aleph, Nanode "Omni" on Veo/Gemini) but is capped at short durations and lower resolutions. No independent archviz-specific stability test was found.

### Cited Findings
- Kling 2.5 Turbo start/end frame: the start frame sets composition and light, the end frame sets where the shot lands, output 1080p. — [Higgsfield guide](https://higgsfield.ai/blog/A-Guide-to-Kling-Turbo-Start-End-Frame)
- Kling 3.0 / O1: the prompt should describe the movement between frames, not the scene. Chain clips by using the last frame of one video as the start of the next. — [AI FILMS Studio](https://studio.aifilms.ai/blog/kling-3-o1-video-generation-tutorial); [Tona.AI Kling 3.0 guide](https://tonaai.io/blog/kling-3-start-end-frame-tutorial)
- Start-frame resolution affects output quality. — [klingmotioncontrol Kling 3.0 guide](https://klingmotioncontrol.com/blog/klingai-3-0-ai-video-generator-model-user-guide)
- Caution: on Kling 1.6, the end frame is a conditioning target, not stitched in, and a seam artifact appears when start and end frames differ too much. Keep the two frames close. — [imagetovideo.dev Kling page](https://imagetovideo.dev/models/kling/)
- Runway is seen as the stronger fit for precise camera control (paths, velocities and zooms defined in 3D space). Kling leans toward an automated "AI Director" and multi-shot. — [Atlas Cloud, Runway Gen-4 vs Kling 3.0](https://www.atlascloud.ai/blog/runway-gen-4-vs-kling-3-0-which-image-to-video-ai-wins-for-professional-filmmaking)
- Runway Aleph is a video-to-video editor (needs source footage). It suits variations: background, object removal, relighting. Aleph 2.0 accepts up to 30 s, with longer edits costing more. — [Flami.pro Aleph review](https://flami.pro/en/blog/runway-aleph-review)
- UPenn architecture professors start from a basic 3D model, apply Runway Video-to-Video styling, then reconstruct the 3D object from the restyled video. — [Runway customer story](https://runwayml.com/customers/how-upenn-architecture-professors-transforming-3d-design-with-runway)
- Veo 3.1 tiers via the Nanode add-on: Lite (720p/1080p), Fast and Standard (720p/1080p/4K). Higher-res jobs use 8 s output. Omni restyle of an Eevee or Workbench capture runs 4/6/8/10 s at 720p. — [GitHub Kovname/nano-banana-render](https://github.com/Kovname/nano-banana-render)
- Anchor Veo with the still image to reduce style drift, and state the clip length in the prompt. — [ToolJunction](https://www.tooljunction.io/blog/how-to-create-ai-videos-with-nano-banana-2025)
- General 2026 overview: identity drift is still the main failure mode. Reference inputs (Veo's three reference images, Kling Elements, Seedance's many references) fight it. — [ocdevel MLA-26](https://ocdevel.com/mlg/mla-26)
- A Runway-focused guide notes objects can morph or melt during movement and suggests rigidity language in prompts. — [Medium, creativeaininja](https://medium.com/@creativeaininja/how-to-actually-control-next-gen-video-ai-runway-kling-veo-and-sora-prompting-strategies-92ef0055658b)
- Pulze (archviz software vendor) 10-model test (Runway Gen 4, Kling 2.1 / 2.5 Turbo, Wan 2.2, Hailuo Pro, Veo 3 / 3 Fast, Seedance 1.0 Pro, Vidu Q1, Luma Ray 2 / Ray 2 Flash): no single winner. Veo 3 and Kling 2.1 led realism, Runway Gen 4 was most cinematic for camera moves. The tests were fire, water, crowds and walking people, not building geometry. — [Pulze blog (byline 23 Feb 2026)](https://www.pulze.io/blog/ai-video-model-comparison)
- A third-party page claims Kling 4.0 launched 15 Oct 2026. Unverified against an official source. — [learnarchitecture.net](https://learnarchitecture.net/artificial-intelligence/33845-ai-video-generation-tools.html)

### Inferences
- For a tower to unit to room move, the practical recipe is: render (or AI-enhance) 4-8 keyframe stills along the camera path from Blender, each a few metres apart. Generate each segment with start+end frame at 5-10 s, keep moves slow and simple (dolly or orbit), then cross-dissolve or cut at matched frames in an editor. Our renderer can produce exact keyframes, which is a big advantage over prompt-only creators.
- A hybrid is likely the most accurate: render the full camera move in Blender (geometry exact), AI-enhance a few keyframes, then use video-to-video only as a light restyle, or simply use AI for the hero stills and keep the Cycles animation for motion.

### Gaps
- No sourced architecture-specific morphing benchmark across Kling, Veo, Runway, Seedance, Luma Ray 3, Hailuo or Wan was found. Ranking for "stable straight lines and repeated facades" is unverified.
- Hard clip-length caps per model (other than Veo 8 s at high res and Aleph 30 s) were not confirmed in this pass.

## Named creators and tutorials: their tool chains

### Takeaway
Publicly documented chains are coarse. Most AI-architecture reels are prompt-first (Midjourney still, Photoshop fix, Kling animate), which is why they look great but are not tied to a real design. Firms that need accuracy (KPF) animate their own renders.

### Cited Findings
- **Studio Tim Fu ("Living Sketches")**: Midjourney, Kling and Photoshop. Prompts combine architectural references, spatial ideas and mood; images generated; edited in Photoshop; small diagrams or narrative details sometimes added; animated into short clips. Atmosphere over technical accuracy. — [Architizer, Living Sketches (2026)](https://architizer.com/blog/?p=203116)
- **Hamza Shaikh**: sketch, then Krita plus ComfyUI with ControlNet, iterating while keeping the sketch's intent in control. — [Architizer](https://architizer.com/blog/?p=203116)
- **Rolando Cedeño de la Cruz (AIMETA STUDIO)**: Midjourney, Kling, Leonardo AI and ChatGPT, non-linear, deliberately ambiguous animated sketches shared early with clients. — [Architizer](https://architizer.com/blog/?p=203116)
- **KPF (Andy Christoforou, Senior Applied Technology Specialist)**: brief, schematic, static renders (in-house or outsourced), then animated in-house in Runway for pitches. Previously outsourced animation took about two weeks per minute of footage and cost "thousands of dollars". No Runway model or feature is named. — [Runway customer story, KPF](https://runway.com/customers/how-kpf-is-incorporating-ai-video-into-architectural-workflows)
- **Course chains (sellers, unverified)**: PAACADEMY teaches Midjourney 7, editing and extending renders with Nano Banana Pro inside Weavy, then animating keyframes in Luma AI. Another course uses Midjourney, Kling, Magnific, Krea and Flux Kontext. A common tip is to run each still through Magnific first, then use Kling Pro mode so the detail carries into video. — [PAACADEMY course](https://paacademy.com/course/cinematic-architecture-ai-powered-design-workflows); [MyArchitectAI courses list](https://www.myarchitectai.com/blog/ai-architecture-courses); [YouTube: Midjourney, Kling, Runway workflow](https://www.youtube.com/watch?v=dvnRNHL7aR4)
- **Blender-to-Nano Banana-to-Veo tutorial**: a YouTube archviz workflow goes from concept to animation using Nano Banana and Veo 3.1. — [YouTube AI Archviz Tutorial](https://www.youtube.com/watch?v=WFimhEJ4Aqg)

### Inferences
- The viral reels' look comes from: (a) a heavily art-directed still (Midjourney or Nano Banana) with dramatic golden-hour or dusk light, mist, water and reflections; (b) Magnific or Krea upscale; (c) a 5-10 s slow push or orbit in Kling or Veo; (d) music-timed cuts. Geometry accuracy is not their goal.

### Gaps
- Specific Instagram/TikTok creator handles with step-by-step settings could not be verified (social platforms not fetchable). Hassan Ragab and Ismail Seleit returned no workflow sources.

## Consistency of finishes and furniture across shots

### Takeaway
Consistency comes from fixed seeds, locked prompts, the same reference image across every shot, and per-view structure conditioning. Video models now accept multiple reference images (Veo 3.1 three refs, Kling Elements, Seedance many refs). Project LoRA training for archviz was not documented in sources found.

### Cited Findings
- Fixed seeds, locked prompts, per-view conditioning discipline and usually a reference image. — [ArchiGen AI](https://archigenai.com/comfyui-archviz-question-nobody-answers-2026.html)
- Reference inputs in video models: Veo three references, Kling Elements, Seedance dozens of references, as the counter to identity drift. — [ocdevel MLA-26](https://ocdevel.com/mlg/mla-26)
- Chaos says Nano Banana inside Veras preserves identity across views. — [Chaos CG Connect, Nano Banana for Architecture](https://cgconnect.chaos.com/insights/articles/569859ac-nano-banana-for-architecture)
- Nanode supports style-reference images and texture/material generation with references. — [GitHub Kovname/nano-banana-render](https://github.com/Kovname/nano-banana-render)

### Inferences
- In our pipeline, the strongest consistency lever is that materials are real in the Blender scene. Render a material ID pass and feed the same finish reference board to every AI shot.

### Gaps
- No sourced recipe for training a project LoRA (image count, steps, base model) for a specific building was found.

## Cost per hero still and per 30-60 s fly-through

### Takeaway
At API rates, a 60 s fly-through's generation cost runs roughly US$17 (Kling 2.6, no audio) to about US$100 (Veo 3.1 Standard), assuming about 4 tries per usable second. Labour and subscriptions dominate, not compute. A hero still is cents to a few dollars in compute.

### Cited Findings
- Veo 3.1 (Gemini API): Standard $0.40/s at 720p/1080p and $0.60/s at 4K. Fast $0.10 / $0.12 / $0.30. Lite $0.05 / $0.08. An outlier reseller claims $0.75/s. — [benchlm Veo pricing](https://benchlm.ai/media-pricing/veo); [Unifically Veo 3.1](https://unifically.com/blogs/veo-3.1); [veo3gen (outlier)](https://www.veo3gen.app/blog/veo-3-1-api-access-cost)
- Kling 2.6 Pro on fal: $0.07/s without audio, $0.14/s with native audio. Krea: $0.0735/s / $0.147/s. Kuaishou direct Standard $0.056/s. — [fal Kling 2.6 i2v](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video); [Krea API docs](https://www.krea.ai/docs/api-reference/video/kling-26.md)
- Nanode image credits: Nano Banana Pro 30 / 45 / 60 credits for 1K / 2K / 4K (credit-to-USD not listed). — [GitHub Kovname/nano-banana-render](https://github.com/Kovname/nano-banana-render)
- Chaos Veras about US$29/month on annual billing ($348/yr) per third parties; D5 Pro $38/month or $360/yr (Capterra). — [aitoolsatlas Veras pricing](https://aitoolsatlas.ai/tools/veras/pricing); [Capterra D5](https://www.capterra.com/p/10005615/D5-Render/pricing/)
- Magnific: conflicting third-party figures ($39/month vs $99/month Premium), credit-based per upscale. — [MyArchitectAI Magnific pricing](https://www.myarchitectai.com/blog/magnific-ai-pricing); [aitoolsatlas](https://aitoolsatlas.ai/tools/magnific-ai/review)
- KPF: outsourced animation used to take about two weeks and "thousands of dollars" per minute. — [Runway, KPF](https://runway.com/customers/how-kpf-is-incorporating-ai-video-into-architectural-workflows)

### Inferences (my arithmetic; the 4x reroll factor is an assumption)
- 60 s with Kling 2.6 at $0.07/s x 60 s x 4 tries is about US$17 (about A$26). Veo 3.1 Fast 1080p at $0.12/s comes to about US$29 (A$44). Veo 3.1 Standard 1080p at $0.40/s comes to about US$96 (A$147). A 30 s cut is half that.
- Hero still: 5-10 Nano Banana Pro or ComfyUI generations plus one Magnific upscale is likely under US$5 compute, plus a subscription.

### Gaps
- No creator-published "total cost per finished reel" figure was found. No reliable reroll-rate statistic.

## Failure modes and how professionals QA them

### Takeaway
The repeatable failures are redrawn facades (window and mullion counts, bays dropped), rounded corners, moved entrances, fake shadows from relighting, thin-element loss, mirror and glass hallucination, and video morph or melt and seams between clips. QA is a manual side-by-side count against the source.

### Cited Findings
- Failures: too-high denoise redraws the facade (windows added or moved, mullions changed, corners rounded, entrances shifted); denoise-only passes drop a bay every few runs; relighting adds shadows the scene could not cast. QA: side-by-side before and after, count windows bay by bay, trace the mullion grid, check the parapet line, entrance position and floor count, check shadows against light sources. — [ArchiGen AI](https://archigenai.com/ai-render-enhance-without-hallucination-denoise-controlnet-architects-2026.html)
- Thin elements vanish or halo with estimated depth. — [ArchiGen AI depth article](https://archigenai.com/depth-anything-v3-flat-render-control-comfyui-architects-2026.html)
- Mirrors and hallucinated elements in Nano Banana Pro. — [CGwisdom](https://cgwisdom.com/blog/sketchup-and-nano-banana-pro-photorealistic-visualizations-in-5-minutes-is-this-the-end-of-v-ray.html)
- Video: morphing or melting during movement; seam when start and end frames differ too much; identity drift over extensions. — [Medium](https://medium.com/@creativeaininja/how-to-actually-control-next-gen-video-ai-runway-kling-veo-and-sora-prompting-strategies-92ef0055658b); [imagetovideo.dev](https://imagetovideo.dev/models/kling/); [ocdevel](https://ocdevel.com/mlg/mla-26)
- Production pipelines fail on consistency and handoffs even when the model is good. — [systemflowhq, Jan 2026](https://systemflowhq.blogspot.com/2026/01/ai-video-production-pipeline-failure.html)

### Inferences
- We can automate part of QA: compare an edge map of the AI output against our Blender line or normal pass (for example IoU of edges) and flag drift, then do a human window count.

### Gaps
- No sourced pro studio QA checklist for AI video beyond the above.

## Disclosure norms

### Takeaway
Law is moving toward mandatory disclosure of AI-altered property marketing (California AB 723, signed 10 Oct 2025; NSW rentals from early 2027, fines up to A$22,000; Wisconsin 1 Jan 2027). A label doesn't cure a misleading image. For unbuilt projects, "artist's impression" plus an "AI-enhanced" note is the safe norm, but no specific source on that wording was found.

### Cited Findings
- California AB 723 signed 10 Oct 2025: enhancement that changes a property's condition or layout triggers disclosure. — [Beverly Hills Courier](https://beverlyhillscourier.com/2025/11/23/californias-new-disclosure-rule-for-digitally-altered-real-estate-marketing/); [Construction Defect Journal](https://constructiondefectjournal.com/archives/inside-issue/2026/01/new-california-law-requires-real-estate-agents-and-brokers-disclose-ai-alterations-listings)
- NSW: disclosure of digitally modified or AI images in rental ads, fines up to $22,000; disclosure alone does not avoid a Fair Trading breach if the image misrepresents. — [Mediaweek](https://mediaweek.com.au/nsw-cracks-down-on-ai-doctored-real-estate-listings); [ACS Information Age](https://ia.acs.org.au/article/2025/nsw-tackles-ai-real-estate-pics.html); [Money Magazine](https://www.moneymag.com.au/ai-edited-real-estate-photos-misleading-buyers)
- New York DOS trend alert 13 Nov 2025 on AI listing images. — [NY DOS](https://dos.ny.gov/news/new-york-department-state-issues-new-trend-alert-warning-homebuyers-ai-generated-home-listings)
- NZ: images must be a true representation; recommend disclosure plus human oversight. — [Simpson Grierson](https://www.simpsongrierson.com/insights-news/legal-updates/housefishing-is-using-ai-in-a-property-listing-misleading-under-the-fair-trading-act)

### Inferences
- For Australian off-the-plan marketing, label as "Artist's impression. AI-enhanced from the design model. Finishes and landscaping indicative." This is consistent with the Fair Trading principle above. Get a solicitor to confirm.

### Gaps
- No source found for an archviz-industry or ArchDaily/CGarchitect disclosure standard, or for Queensland-specific off-the-plan rules on AI renders.
