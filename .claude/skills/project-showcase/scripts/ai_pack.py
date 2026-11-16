"""Bundle one shot for an optional AI polish pass (e.g. Seedance on Higgsfield).

    python ai_pack.py --driving work/ai/living_clay_desktop.mp4 --start work/render/living_start.png
                      --end work/render/living_end.png --finishes finishes.csv --room "Living room"
                      --materials "K-TIM-01 - Hekke Flooring WIDE,K-ST-01 Granite" --out work/ai/living

    python ai_pack.py --start work/render/kitchen.png --clay work/render/kitchen_clay.png ... --out work/ai/kitchen_still

Video mode (--driving): driving.mp4, start.png, end.png, prompt.txt and CHECKLIST.md.
Still mode (no --driving): an image-to-image polish of one accurate render (e.g. Nano Banana or Seedream
edit on Higgsfield). start.png is the input image, clay.png the QA reference.
It does not call any AI service. Generating costs credits, and sending a client's design to a
third party needs the developer's and architect's written OK: both are on the checklist.

The model keeps geometry locked (driving video) and the finishes come from the schedule (start and
end frames are accurate renders, the prompt names the scheduled finishes). The AI adds realism only.
"""
import argparse, csv, os, shutil, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--driving", help="video mode: clay render of the move (blender_render.py style: clay, video: true)")
    ap.add_argument("--start", required=True, help="accurate render of the first frame, or the still to polish")
    ap.add_argument("--end", help="video mode: accurate render of the last frame")
    ap.add_argument("--clay", help="still mode: clay render from the same camera, the QA reference")
    ap.add_argument("--finishes", required=True)
    ap.add_argument("--room", required=True)
    ap.add_argument("--materials", help="comma list of finishes.csv ifc_material names visible in this shot (default: all textured/procedural rows)")
    ap.add_argument("--styling", default="", help="approved loose furniture/styling, e.g. 'linen sofa, oak dining chairs'. Blank = keep the room as modelled")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    video = bool(a.driving)
    if video and not a.end:
        sys.exit("video mode needs --end")
    if not video and not a.clay:
        sys.exit("still mode needs --clay (same shot with style: clay) so the output can be checked")

    rows = [r for r in csv.DictReader(open(a.finishes, encoding="utf-8-sig")) if r.get("hide", "").strip() not in ("1", "yes", "true")]
    if a.materials:
        want = [m.strip() for m in a.materials.split(",")]
        missing = [m for m in want if m not in {r["ifc_material"] for r in rows}]
        if missing:
            sys.exit("not in finishes.csv: %s" % ", ".join(missing))
        rows = [r for r in rows if r["ifc_material"] in want]
    else:
        rows = [r for r in rows if (r.get("texture") or "").strip() or (r.get("procedural") or "").strip()]
    finishes = [(r.get("source") or r["ifc_material"]).split(";")[0].strip() for r in rows]

    os.makedirs(a.out, exist_ok=True)
    ins = ((a.driving, "driving" + os.path.splitext(a.driving)[1]), (a.start, "start.png"), (a.end, "end.png")) if video         else ((a.start, "start.png"), (a.clay, "clay.png"))
    for src, name in ins:
        if not os.path.exists(src):
            sys.exit("missing input: %s" % src)
        shutil.copyfile(src, os.path.join(a.out, name))

    lock = ("Follow the driving video's camera move exactly, frame for frame. " if video else
            "Keep the exact camera, framing, perspective and composition of the input image. ")
    prompt = (
        f"Photoreal architectural visualisation, {a.room}. " + lock +
        "Every wall, opening, window, door, joinery line, benchtop edge and appliance stays exactly where the "
        + ("driving video and the start and end frames show it. " if video else "input image shows it. ")
        + "Do not add, remove, move or resize any of them. "
        + ("Finishes exactly as shown: " + "; ".join(finishes) + ". " if finishes else "Finishes exactly as shown. ")
        + "Do not change any material, colour or stone pattern. Improve only realism: soft natural daylight and "
        "bounce light, true-to-life exposure, subtle surface wear, contact shadows, no lens distortion. "
        + (f"Loose styling only: {a.styling}. " if a.styling else "No added furniture or props. ")
        + "No people, no text, no logos."
    )
    open(os.path.join(a.out, "prompt.txt"), "w", encoding="utf-8").write(prompt + "\n")

    tag = a.room.replace(" ", "_")
    if not video:
        open(os.path.join(a.out, "CHECKLIST.md"), "w", encoding="utf-8").write(f"""# AI polish (still): {a.room}

Before generating
- [ ] Written OK from the developer and architect to send this design to an AI service (file it in qa/).
- [ ] Credit cost quoted and approved by the owner. Try 2 to 4 takes at the cheapest setting first.
- [ ] start.png is the accurate Cycles render with approved props, not a draft.

Generate
- Image edit model that keeps the input's composition (e.g. Nano Banana or Seedream edit on Higgsfield).
- Inputs: start.png as the image, prompt.txt as the instruction. Same aspect ratio as start.png.

After generating (must pass before use)
- [ ] `python qa_drift.py clay.png <ai output.png> --samples 1 --finishes start.png --report qa/drift_{tag}.json --sheet qa/drift_{tag}.png`
      Fails if any wall, opening, joinery line or appliance moved, or a finish changed colour. Look at the sheet either way.
- [ ] Finishes still match start.png (floor, benchtop veining, joinery colour, tapware finish). Reject any take where they changed.
- [ ] No invented objects beyond the approved props, no extra windows, no changed views.
- [ ] Label the image "Artist's impression, AI-enhanced from the design model".
""")
        print("pack written:", a.out)
        print(prompt)
        return 0
    clip = os.path.basename(a.driving)
    open(os.path.join(a.out, "CHECKLIST.md"), "w", encoding="utf-8").write(f"""# AI polish: {a.room}

Before generating
- [ ] Written OK from the developer and architect to send this design to an AI service (file it in qa/).
- [ ] Credit cost quoted and approved by the owner. Draft at low resolution first, finish only the approved take.
- [ ] start.png and end.png are the accurate Cycles renders, not drafts.

Generate
- Video model with a driving/reference video plus start and end frames (e.g. Seedance on Higgsfield).
- Inputs: {clip} -> driving video, start.png, end.png, prompt.txt. Same aspect ratio and length as the driving video.

After generating (must pass before use)
- [ ] `python qa_drift.py <clay frames folder or {clip}> <ai output.mp4> --finishes start.png --report qa/drift_{a.room.replace(' ', '_')}.json --sheet qa/drift_{a.room.replace(' ', '_')}.png`
      Fails if any wall, opening or joinery line moved, or the first frame's finishes changed colour. Look at the sheet either way.
- [ ] Finishes still match the start frame (floor, benchtop veining, joinery colour). Reject any take where they changed.
- [ ] Scrub at 2x for morphing (tapware, handles, stone pattern crawling).
- [ ] Label the scene "Artist's impression, AI-enhanced from the design model".
- [ ] Extract frames (`ffmpeg -i take.mp4 -vf fps=24 %04d.png`), encode to WebP and drop them into site/frames/<shot>/ as usual.
""")
    print("pack written:", a.out)
    print(prompt)


if __name__ == "__main__":
    sys.exit(main())
