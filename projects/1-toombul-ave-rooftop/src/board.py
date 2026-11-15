#!/usr/bin/env python3
"""Finishes comparison board: 4 palettes x 2 views, A3 landscape, one palette per page + overview."""
import pathlib, html
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "1-Toombul-Ave_Rooftop_Finishes-Options_RevA.html"

PAL = [
    ("A", "Coastal white", "p0", "Day", [
        ("ST-01 Stone", "Calacatta-look white sintered stone, 20 mm + 40 mm mitred apron", "#efece6"),
        ("JN-02 Joinery", "Chalk white 2-pac satin", "#ebe7df"),
        ("JN-03 Cladding", "Fluted panel, joinery colour", "#ebe7df"),
        ("HW Hardware", "Brushed stainless 316", "#b9bcbf"),
        ("ST-02 Splashback", "Stone, matches top", "#efece6"),
        ("TF-01 Floor", "Synthetic turf, natural green", "#55743a"),
        ("PT-01 Walls", "Crisp white", "#efede8"),
        ("EL-02 Pendants", "Woven rattan", "#b8925c"),
        ("FF-01 Stools", "Timber seat, stainless frame", "#b48a5a"),
    ], "Bright and low-maintenance. Hides salt and dust well; the most timeless choice for resale."),
    ("B", "Sage & brass", "p1", "Golden hour", [
        ("ST-01 Stone", "Travertine-look sintered stone, honed", "#d9c6a6"),
        ("JN-02 Joinery", "Sage 2-pac satin", "#8f9c87"),
        ("JN-03 Cladding", "Fluted panel, joinery colour", "#8f9c87"),
        ("HW Hardware", "Brushed brass", "#c09a55"),
        ("ST-02 Splashback", "Green handmade tile", "#5f8a74"),
        ("TF-01 Floor", "Porcelain pavers on pedestals", "#cfc7b8"),
        ("PT-01 Walls", "Existing beige render", "#d9cbb3"),
        ("EL-02 Pendants", "Dome, brass", "#c09a55"),
        ("FF-01 Stools", "Timber seat, brass frame", "#b48a5a"),
    ], "Warm, relaxed Mediterranean feel. Works with the existing beige render, so less repainting."),
    ("C", "Charcoal & timber", "p2", "Evening", [
        ("ST-01 Stone", "Nero marble-look sintered stone", "#1d1d1e"),
        ("JN-02 Joinery", "Charcoal 2-pac satin", "#333538"),
        ("JN-03 Cladding", "Spotted gum battens on black", "#a57b52"),
        ("HW Hardware", "Matte black", "#1b1b1c"),
        ("ST-02 Splashback", "Stone, matches top", "#1d1d1e"),
        ("TF-01 Floor", "Synthetic turf, natural green", "#55743a"),
        ("PT-01 Walls", "Crisp white", "#efede8"),
        ("EL-02 Pendants", "Opal glass globe", "#f7f3ea"),
        ("FF-01 Stools", "Rope-weave seat, black frame", "#cdbb98"),
    ], "Moody night-time bar. Dark stone shows water marks and gets hot in direct sun; keep it under cover."),
    ("D", "Terrazzo & oak", "p3", "Day", [
        ("ST-01 Stone", "Terrazzo-look sintered stone", "#ece6dc"),
        ("JN-02 Joinery", "Light oak compact laminate", "#c9a678"),
        ("JN-03 Cladding", "Stone-clad, matches top", "#ece6dc"),
        ("HW Hardware", "Brushed brass", "#c09a55"),
        ("ST-02 Splashback", "Terracotta handmade tile", "#b56b4b"),
        ("TF-01 Floor", "Synthetic turf, lighter tone", "#7b9550"),
        ("PT-01 Walls", "Warm greige", "#bdb3a4"),
        ("EL-02 Pendants", "Woven rattan", "#b8925c"),
        ("FF-01 Stools", "White powdercoat", "#f1f0ec"),
    ], "Playful and textural. Compact laminate gives a timber look that is fully weatherproof."),
]

CSS = """@page { size: 420mm 297mm; margin: 0; }
*{box-sizing:border-box} body{margin:0;font-family:Inter,"DejaVu Sans",sans-serif;color:#1d1d1b;font-size:9.5pt}
.sheet{width:420mm;height:297mm;padding:12mm;display:grid;grid-template-rows:auto 1fr auto;gap:5mm;page-break-after:always;position:relative}
.sheet::before{content:"";position:absolute;inset:6mm;border:.5mm solid #1d1d1b}
.hd{display:flex;justify-content:space-between;align-items:baseline;padding:0 3mm}
.hd h1{font-size:22pt;margin:0;letter-spacing:-.01em}.hd .k{font-size:9pt;color:#777;text-transform:uppercase;letter-spacing:.12em}
.tag{display:inline-grid;place-items:center;width:11mm;height:11mm;border-radius:50%;background:#1d1d1b;color:#fff;font-weight:700;margin-right:3mm;font-size:13pt;vertical-align:middle}
.main{display:grid;grid-template-columns:1fr 88mm;gap:6mm;padding:0 3mm;min-height:0}
.imgs{display:grid;grid-template-rows:1.25fr 1fr;gap:4mm;min-height:0}
.imgs figure{margin:0;position:relative;min-height:0}.imgs img{width:100%;height:100%;object-fit:cover;display:block}
.imgs figcaption{position:absolute;left:3mm;bottom:2mm;color:#fff;font-size:8pt;text-shadow:0 1px 2px #000}
table{border-collapse:collapse;width:100%}td{padding:1.8mm 0;border-bottom:.2mm solid #ddd;vertical-align:top}
td.c{width:9mm}td.c i{display:block;width:7mm;height:7mm;border-radius:1.5mm;border:.2mm solid #aaa}
td.l{color:#777;width:28mm;font-size:8.5pt}
.why{background:#f1f2ee;padding:4mm;margin-top:5mm;font-size:9.5pt}
.ft{display:flex;justify-content:space-between;font-size:8pt;color:#777;padding:0 3mm}
.ov{display:grid;grid-template-columns:repeat(4,1fr);gap:5mm;padding:0 3mm;min-height:0}
.ov figure{margin:0;display:flex;flex-direction:column;gap:2mm;min-height:0}.ov img{width:100%;aspect-ratio:1.4;object-fit:cover}
.ov h3{margin:1mm 0 0;font-size:12pt}.chips{display:flex;gap:1.5mm;flex-wrap:wrap}.chips i{width:8mm;height:8mm;border-radius:1.5mm;border:.2mm solid #aaa}
.ov p{margin:0;font-size:8.8pt;color:#444}
"""

def foot():
    return '<div class="ft"><span>1 Toombul Ave — Rooftop Terrace · Finishes options Rev A · 15 Nov 2026</span><span>Concept visuals from the 3D model of A-201/A-202. Colours indicative; confirm with physical samples.</span></div>'

pages = []
ov = "".join(f'''<figure><img src="renders/{k}c.jpg"><img src="renders/{k}s.jpg"><h3><span class="tag">{t}</span>{n}</h3>
<div class="chips">{"".join(f'<i style="background:{c}"></i>' for _, _, c in rows[:5])}</div><p>{html.escape(why)}</p></figure>''' for t, n, k, _, rows, why in PAL)
pages.append(f'<section class="sheet"><div class="hd"><h1>Bar finishes — four options to compare</h1><span class="k">Overview</span></div><div class="ov">{ov}</div>{foot()}</section>')
for t, n, k, light, rows, why in PAL:
    tr = "".join(f'<tr><td class="c"><i style="background:{c}"></i></td><td class="l">{html.escape(a)}</td><td>{html.escape(b)}</td></tr>' for a, b, c in rows)
    pages.append(f'''<section class="sheet"><div class="hd"><h1><span class="tag">{t}</span>Option {t} — {n}</h1><span class="k">Finishes option</span></div>
<div class="main"><div class="imgs"><figure><img src="renders/{k}c.jpg"><figcaption>Customer side · {light}</figcaption></figure>
<figure><img src="renders/{k}s.jpg"><figcaption>Behind the bar · {light}</figcaption></figure></div>
<div><table>{tr}</table><div class="why">{html.escape(why)}</div></div></div>{foot()}</section>''')

OUT.write_text(f'<!doctype html><html><head><meta charset="utf-8"><title>Finishes options</title><style>{CSS}</style></head><body>{"".join(pages)}</body></html>')
print("wrote", OUT)
