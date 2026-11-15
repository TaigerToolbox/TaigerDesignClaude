"""Bundle one shot for an optional AI polish pass (e.g. Seedance on Higgsfield).

    python ai_pack.py --driving work/ai/living_clay_desktop.mp4 --start work/render/living_start.png
                      --end work/render/living_end.png --finishes finishes.csv --room "Living room"
                      --materials "K-TIM-01 - Hekke Flooring WIDE,K-ST-01 Granite" --out work/ai/living

Writes the pack folder: driving.mp4, start.png, end.png, prompt.txt and CHECKLIST.md.
It does not call any AI service. Generating costs credits, and sending a client's design to a
third party needs the developer's and architect's written OK: both are on the checklist.

The model keeps geometry locked (driving video) and the finishes come from the schedule (start and
end frames are accurate renders, the prompt names the scheduled finishes). The AI adds realism only.
"""
import argparse, csv, os, shutil, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--driving", required=True, help="clay render of the move (blender_render.py style: clay, video: true)")
    ap.add_argument("--start", required=True, help="accurate render of the first frame (finishes from the schedule)")
    ap.add_argument("--end", required=True, help="accurate render of the last frame")
    ap.add_argument("--finishes", required=True)
    ap.add_argument("--room", required=True)
    ap.add_argument("--materials", help="comma list of finishes.csv ifc_material names visible in this shot (default: all textured/procedural rows)")
    ap.add_argument("--styling", default="", help="approved loose furniture/styling, e.g. 'linen sofa, oak dining chairs'. Blank = keep the room as modelled")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

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
    for src, name in ((a.driving, "driving" + os.path.splitext(a.driving)[1]), (a.start, "start.png"), (a.end, "end.png")):
        if not os.path.exists(src):
            sys.exit("missing input: %s" % src)
        shutil.copyfile(src, os.path.join(a.out, name))

    prompt = (
        f"Photoreal architectural visualisation, {a.room}.Follow the driving video's camera move exactly, frame for frame. "
        "Every wall, opening, window, door, joinery line, benchtop edge and appliance stays exactly where the driving "
        "video and the start and end frames show it. Do not add, remove, move or resize any of them. "
        "Finishes exactly as in the start and end frames: " + "; ".join(finishes) + ". "
        "Do not change any material, colour or stone pattern. Soft natural daylight as in the start frame, "
        "true-to-life exposure, gentle camera motion, no lens distortion. "
        + (f"Loose styling only: {a.styling}. " if a.styling else "No added furniture or props. ")
        + "No people, no text, no logos."
    )
    open(os.path.join(a.out, "prompt.txt"), "w", encoding="utf-8").write(prompt + "\n")

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
- [ ] `python qa_drift.py <clay frames folder or {clip}> <ai output.mp4> --report qa/drift_{a.room.replace(' ', '_')}.json --sheet qa/drift_{a.room.replace(' ', '_')}.png`
      Fails if any wall, opening or joinery line moved. Look at the sheet either way.
- [ ] Finishes still match the start frame (floor, benchtop veining, joinery colour). Reject any take where they changed.
- [ ] Scrub at 2x for morphing (tapware, handles, stone pattern crawling).
- [ ] Label the scene "Artist's impression, AI-enhanced from the design model".
- [ ] Extract frames (`ffmpeg -i take.mp4 -vf fps=24 %04d.png`), encode to WebP and drop them into site/frames/<shot>/ as usual.
""")
    print("pack written:", a.out)
    print(prompt)


if __name__ == "__main__":
    sys.exit(main())
