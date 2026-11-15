"""Check an AI-polished video against the model's own frames. Fails if geometry drifted.

    python qa_drift.py REFERENCE AI [--report qa/drift.json] [--sheet qa/drift.png]

REFERENCE and AI are each a folder of frames or a video file. REFERENCE is the clay render of the same
move (blender_render.py "style": "clay", the same frames used as the driving video): it holds geometry
only. A colour render is the wrong reference, because its shadow and horizon edges aren't geometry and
an AI relight fails falsely.

Tested on the sample house (24 points per move): restyled frames with identical geometry pass at 1.00;
a wall section moved 3% or 5% of frame width, or an element erased, fails in its grid cell (worst cell
0.23 to 0.51) even though the whole-frame score stayed 0.87 to 0.90; a 1% shift passes (within
tolerance); a real colour render checked against its clay frames passes (worst cell 0.67).

How it works: both are sampled at the same points in time and reduced to edge maps. Every edge in the
reference (wall junctions, openings, joinery lines, appliance outlines) must still have an edge within
--radius pixels in the AI frame. That's checked over the whole frame and per cell of a 4x4 grid, so
one moved wall fails even when the rest of the frame is fine. Extra edges in the AI frame (texture,
styling, furniture) are allowed. Exit code 1 on failure, so it can gate a pipeline.
"""
import argparse, json, os, subprocess, sys, tempfile, shutil
import numpy as np
from PIL import Image, ImageDraw


def frames_from(path, tmp):
    if os.path.isdir(path):
        fs = sorted(f for f in os.listdir(path) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")))
        return [os.path.join(path, f) for f in fs]
    out = os.path.join(tmp, os.path.basename(path) + "_frames")
    os.makedirs(out, exist_ok=True)
    ff = shutil.which("ffmpeg") or "ffmpeg"
    subprocess.run([ff, "-v", "error", "-y", "-i", path, os.path.join(out, "%05d.png")], check=True)
    return frames_from(out, tmp)


def gray(path, size):
    return np.asarray(Image.open(path).convert("L").resize(size, Image.BILINEAR), dtype=np.float32) / 255.0


def magnitude(a):
    a = (a[:-2, :-2] + a[:-2, 1:-1] + a[:-2, 2:] + a[1:-1, :-2] + a[1:-1, 1:-1] + a[1:-1, 2:]
         + a[2:, :-2] + a[2:, 1:-1] + a[2:, 2:]) / 9.0  # 3x3 blur first: grain and noise aren't geometry
    a = np.pad(a, 1, mode="edge")
    gx = np.zeros_like(a); gy = np.zeros_like(a)
    gx[1:-1, 1:-1] = (a[:-2, 2:] + 2 * a[1:-1, 2:] + a[2:, 2:]) - (a[:-2, :-2] + 2 * a[1:-1, :-2] + a[2:, :-2])
    gy[1:-1, 1:-1] = (a[2:, :-2] + 2 * a[2:, 1:-1] + a[2:, 2:]) - (a[:-2, :-2] + 2 * a[:-2, 1:-1] + a[:-2, 2:])
    return np.hypot(gx, gy)


def strongest(mag, count):
    """The `count` strongest edge pixels. Matching the AI's edge budget to the reference stops texture
    and noise from flooding the frame with edges that 'match' anything."""
    count = int(min(max(count, 1), mag.size - 1))
    return mag >= np.partition(mag.ravel(), -count)[-count]


def edges(a, pct, floor=0.08):
    gx = np.zeros_like(a); gy = np.zeros_like(a)
    gx[1:-1, 1:-1] = (a[:-2, 2:] + 2 * a[1:-1, 2:] + a[2:, 2:]) - (a[:-2, :-2] + 2 * a[1:-1, :-2] + a[2:, :-2])
    gy[1:-1, 1:-1] = (a[2:, :-2] + 2 * a[2:, 1:-1] + a[2:, 2:]) - (a[:-2, :-2] + 2 * a[:-2, 1:-1] + a[:-2, 2:])
    mag = np.hypot(gx, gy)
    return mag > max(np.percentile(mag, pct), floor)


def dilate(e, r):
    p = np.pad(e, r)
    out = np.zeros_like(e)
    h, w = e.shape
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out |= p[r + dy:r + dy + h, r + dx:r + dx + w]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reference"); ap.add_argument("ai")
    ap.add_argument("--samples", type=int, default=24, help="points in time to check")
    ap.add_argument("--width", type=int, default=480, help="analysis width in pixels")
    ap.add_argument("--radius", type=int, default=3, help="pixels an edge may move (at --width) before it counts as drift")
    ap.add_argument("--min-recall", type=float, default=0.85, help="share of reference edges that must survive, whole frame")
    ap.add_argument("--min-cell", type=float, default=0.60, help="same, worst grid cell (catches one moved wall)")
    ap.add_argument("--report"); ap.add_argument("--sheet")
    a = ap.parse_args()

    tmp = tempfile.mkdtemp()
    try:
        ref, ai = frames_from(a.reference, tmp), frames_from(a.ai, tmp)
        assert ref and ai, "no frames found"
        w0, h0 = Image.open(ref[0]).size
        aw, ah = Image.open(ai[0]).size
        if abs(w0 / h0 - aw / ah) > 0.02:
            sys.exit("aspect ratios differ (reference %dx%d, AI %dx%d): the AI output was cropped or reframed" % (w0, h0, aw, ah))
        size = (a.width, round(a.width * h0 / w0))
        rows, worst = [], []
        for k in range(a.samples):
            t = k / max(1, a.samples - 1)
            r_path, a_path = ref[round(t * (len(ref) - 1))], ai[round(t * (len(ai) - 1))]
            rm = magnitude(gray(r_path, size))
            re_ = rm > max(np.percentile(rm, 92), 0.06)            # the reference's clear edges
            ae = strongest(magnitude(gray(a_path, size)), 2.5 * re_.sum())  # same budget (x2.5) of the AI's strongest
            hit = re_ & dilate(ae, a.radius)
            recall = hit.sum() / max(1, re_.sum())
            H, W = re_.shape; cells = []
            for gy in range(4):
                for gx in range(4):
                    sl = (slice(gy * H // 4, (gy + 1) * H // 4), slice(gx * W // 4, (gx + 1) * W // 4))
                    n = re_[sl].sum()
                    if n >= 40:  # only cells with real geometry in them
                        cells.append((hit[sl].sum() / n, gx, gy))
            cell = min(cells) if cells else (1.0, -1, -1)
            ok = recall >= a.min_recall and cell[0] >= a.min_cell
            rows.append({"t": round(t, 3), "reference": os.path.basename(r_path), "ai": os.path.basename(a_path),
                         "recall": round(float(recall), 3), "worst_cell": round(float(cell[0]), 3), "cell_xy": cell[1:], "pass": bool(ok)})
            worst.append((cell[0], recall, a_path, re_, hit, cell))
        failed = [r for r in rows if not r["pass"]]
        summary = {"pass": not failed, "frames_checked": len(rows), "failed": len(failed),
                   "min_recall": min(r["recall"] for r in rows), "min_cell": min(r["worst_cell"] for r in rows),
                   "thresholds": {"radius_px_at_width": [a.radius, a.width], "min_recall": a.min_recall, "min_cell": a.min_cell}}
        print(json.dumps(summary, indent=1))
        for r in failed:
            print("FAIL t=%.2f recall %.2f, worst cell %.2f at grid %s (%s)" % (r["t"], r["recall"], r["worst_cell"], r["cell_xy"], r["ai"]))
        if a.report:
            os.makedirs(os.path.dirname(os.path.abspath(a.report)), exist_ok=True)
            json.dump({"summary": summary, "frames": rows}, open(a.report, "w"), indent=1)
        if a.sheet:  # the six worst frames, reference edges that went missing drawn in red
            worst.sort(key=lambda x: x[0])
            tiles = []
            for c, rc, a_path, re_, hit, cell in worst[:6]:
                im = Image.open(a_path).convert("RGB").resize(size)
                px = np.asarray(im).copy()
                miss = re_ & ~hit
                px[miss] = [255, 0, 0]
                tile = Image.fromarray(px); d = ImageDraw.Draw(tile)
                if cell[1] >= 0:
                    H, W = re_.shape
                    d.rectangle([cell[1] * W // 4, cell[2] * H // 4, (cell[1] + 1) * W // 4 - 1, (cell[2] + 1) * H // 4 - 1], outline=(255, 220, 0), width=2)
                d.rectangle([0, 0, 230, 16], fill=(0, 0, 0)); d.text((4, 2), "recall %.2f  worst cell %.2f" % (rc, c), fill=(255, 255, 255))
                tiles.append(tile)
            sheet = Image.new("RGB", (size[0] * 3, size[1] * ((len(tiles) + 2) // 3)), "black")
            for i, t_ in enumerate(tiles):
                sheet.paste(t_, ((i % 3) * size[0], (i // 3) * size[1]))
            os.makedirs(os.path.dirname(os.path.abspath(a.sheet)), exist_ok=True)
            sheet.save(a.sheet)
        return 0 if not failed else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
