#!/usr/bin/env python3
"""Builds the site report + scope + drawing set for 1 Toombul Ave rooftop bar.

Output: ../1-Toombul-Ave_Rooftop_Site-Report-Scope-Drawings_RevA.html (rendered to PDF by render.js)
All drawing geometry is in real millimetres; SVG width is set from the drawing scale.
"""
import html, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "1-Toombul-Ave_Rooftop_Site-Report-Scope-Drawings_RevA.html"

PROJECT = "1 Toombul Ave — Rooftop Terrace"
SUB = "Covered outdoor bar, joinery & stone, synthetic turf"
DATE = "15 Nov 2026"
REV = "A"
REV_NOTE = "Issued for discussion & pricing"
BY = "Taiger Design"

# ---------------------------------------------------------------- drawing kit
class D:
    def __init__(self):
        self.o = []

    def add(self, s):
        self.o.append(s)

    def rect(self, x, y, w, h, cls="l"):
        self.add(f'<rect x="{x}" y="{-(y + h)}" width="{w}" height="{h}" class="{cls}"/>')

    def line(self, x1, y1, x2, y2, cls="l"):
        self.add(f'<line x1="{x1}" y1="{-y1}" x2="{x2}" y2="{-y2}" class="{cls}"/>')

    def poly(self, pts, cls="l", closed=False):
        p = " ".join(f"{x},{-y}" for x, y in pts)
        tag = "polygon" if closed else "polyline"
        self.add(f'<{tag} points="{p}" class="{cls}"/>')

    def circle(self, x, y, r, cls="l"):
        self.add(f'<circle cx="{x}" cy="{-y}" r="{r}" class="{cls}"/>')

    def text(self, x, y, t, size=55, anchor="middle", cls="t", rot=0):
        tr = f' transform="rotate({rot} {x} {-y})"' if rot else ""
        self.add(f'<text x="{x}" y="{-y}" font-size="{size}" text-anchor="{anchor}" class="{cls}"{tr}>{html.escape(t)}</text>')

    def tick(self, x, y):
        self.line(x - 22, y - 22, x + 22, y + 22, "dimt")

    def dimh(self, x1, x2, y, label=None, size=50, ext_from=None):
        if ext_from is not None:
            for x in (x1, x2):
                self.line(x, ext_from, x, y + (30 if y > ext_from else -30), "ext")
        self.line(x1 - 40, y, x2 + 40, y, "dim")
        self.tick(x1, y); self.tick(x2, y)
        self.text((x1 + x2) / 2, y + 18, label if label is not None else f"{round(x2 - x1)}", size, cls="dt")

    def dimv(self, y1, y2, x, label=None, size=50, ext_from=None):
        if ext_from is not None:
            for y in (y1, y2):
                self.line(ext_from, y, x + (30 if x > ext_from else -30), y, "ext")
        self.line(x, y1 - 40, x, y2 + 40, "dim")
        self.tick(x, y1); self.tick(x, y2)
        self.text(x - 18, (y1 + y2) / 2, label if label is not None else f"{round(y2 - y1)}", size, cls="dt", rot=-90)

    def leader(self, x1, y1, x2, y2, t, size=48, anchor="start"):
        self.line(x1, y1, x2, y2, "lead")
        self.circle(x1, y1, 9, "dot")
        dx = 15 if anchor == "start" else -15
        self.text(x2 + dx, y2 - 15, t, size, anchor=anchor, cls="note")

    def swing(self, x, y, w, h, hinge="L"):
        """Elevation door-swing convention: apex at hinge side."""
        if hinge == "L":
            self.poly([(x + w, y), (x, y + h / 2), (x + w, y + h)], "swing")
        else:
            self.poly([(x, y), (x + w, y + h / 2), (x, y + h)], "swing")

    def handle_v(self, x, y, l=160):
        self.rect(x - 6, y, 12, l, "hdl")

    def handle_h(self, x, y, l=160):
        self.rect(x - l / 2, y - 6, l, 12, "hdl")

    def svg(self, x0, y0, x1, y1, scale, extra_cls=""):
        """viewBox in real mm (y up: y0 bottom, y1 top). Paper width = real/scale."""
        w, h = x1 - x0, y1 - y0
        return (f'<svg class="dwg {extra_cls}" viewBox="{x0} {-y1} {w} {h}" '
                f'style="width:{w / scale:.1f}mm;height:{h / scale:.1f}mm" xmlns="http://www.w3.org/2000/svg">'
                + DEFS + "".join(self.o) + "</svg>")


DEFS = """<defs>
<pattern id="stone" width="60" height="60" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
 <line x1="0" y1="0" x2="0" y2="60" stroke="#8a8a8a" stroke-width="3"/></pattern>
<pattern id="turf" width="120" height="120" patternUnits="userSpaceOnUse">
 <path d="M20 90 l10 -25 l10 25 M70 40 l10 -25 l10 25" stroke="#5f8f55" stroke-width="7" fill="none"/></pattern>
<pattern id="wall" width="80" height="80" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
 <line x1="0" y1="0" x2="0" y2="80" stroke="#444" stroke-width="5"/></pattern>
<pattern id="slab" width="100" height="100" patternUnits="userSpaceOnUse">
 <circle cx="25" cy="30" r="5" fill="#777"/><circle cx="70" cy="75" r="4" fill="#777"/><path d="M60 20 l12 8 l-14 4z" fill="none" stroke="#777" stroke-width="3"/></pattern>
</defs>"""

# ---------------------------------------------------------------- A-201 back bar
BB_L = 2800
KICK = 120
BB_TOP = 900      # finished bench height
APRON = 40        # 20mm top with 40mm mitred apron
OH_U, OH_T = 1550, 2250   # overhead underside / top
SOFFIT = 2450     # assumed, TBC on measure


def back_bar_elev():
    d = D()
    ct = BB_TOP - APRON  # carcass top
    # floor + soffit
    d.line(-300, 0, BB_L + 300, 0, "floor")
    d.line(-300, SOFFIT, BB_L + 300, SOFFIT, "hid")
    d.text(BB_L + 290, SOFFIT + 25, "U/S EXISTING SOFFIT (HEIGHT TBC)", 40, anchor="end", cls="note")
    # end panels
    d.rect(0, 0, 30, ct, "l"); d.rect(BB_L - 30, 0, 30, ct, "l")
    # kick to sink + drawers
    d.rect(30, 0, 1500, KICK, "kick")
    # sink cabinet pair
    for i in range(2):
        x = 30 + i * 450
        d.rect(x + 2, KICK, 446, ct - KICK, "door")
        d.swing(x + 2, KICK, 446, ct - KICK, "L" if i == 0 else "R")
    d.handle_v(30 + 450 - 30, ct - 220); d.handle_v(30 + 450 + 30, ct - 220)
    d.rect(0, BB_TOP, BB_L, OH_U - BB_TOP, "splash")
    # sink (hidden, undermount) + tap
    d.rect(150, ct - 220, 660, 200, "hid")
    d.poly([(480, BB_TOP), (480, BB_TOP + 330), (500, BB_TOP + 380), (560, BB_TOP + 400), (620, BB_TOP + 370), (630, BB_TOP + 300)], "tap")
    # 3 drawer bank
    hs = [200, 270, ct - KICK - 470]
    y = ct
    for h in hs:
        d.rect(932, y - h, 596, h - 2, "door"); d.handle_h(1230, y - 60)
        y -= h
    # fridge cavity (appliances by others)
    for i in range(2):
        x = 1530 + i * 620
        d.rect(x + 10, 0, 600, ct - 15, "appl")
        d.text(x + 310, ct / 2 + 30, "BAR FRIDGE", 46, cls="appt")
        d.text(x + 310, ct / 2 - 40, f"0{i + 1} (BY OTHERS)", 40, cls="appt")
    d.handle_v(1530 + 620 - 50, ct - 520, 320); d.handle_v(1530 + 620 + 50, ct - 520, 320)
    # stone top
    d.rect(0, ct, BB_L, APRON, "stone")
    # GPOs
    for x in (1150, 2300):
        d.rect(x - 60, 1080, 120, 70, "gpo")
    # overheads
    oh_h = OH_T - OH_U
    d.rect(0, OH_U, 900, oh_h, "door"); d.rect(450, OH_U, 0.1, oh_h, "l")
    d.swing(2, OH_U, 446, oh_h, "L"); d.swing(452, OH_U, 446, oh_h, "R")
    d.handle_v(420, OH_U + 40); d.handle_v(480, OH_U + 40)
    # open cubbies 2 x 3
    d.rect(900, OH_U, 600, oh_h, "l")
    d.line(1200, OH_U, 1200, OH_T, "l")
    for k in (1, 2):
        d.line(900, OH_U + k * oh_h / 3, 1500, OH_U + k * oh_h / 3, "l")
    d.rect(1500, OH_U, 800, oh_h, "door"); d.line(1900, OH_U, 1900, OH_T, "l")
    d.swing(1502, OH_U, 396, oh_h, "L"); d.swing(1902, OH_U, 396, oh_h, "R")
    d.handle_v(1870, OH_U + 40); d.handle_v(1930, OH_U + 40)
    d.rect(2300, OH_U, 500, oh_h, "door"); d.swing(2302, OH_U, 496, oh_h, "R")
    d.handle_v(2330, OH_U + 40)
    # LED strip
    d.line(20, OH_U - 12, BB_L - 20, OH_U - 12, "led")
    # bulkhead infill option
    d.rect(0, OH_T, BB_L, SOFFIT - OH_T, "opt")
    # dims - horizontal
    d.dimh(0, BB_L, -330, f"{BB_L} OVERALL (TBC ON SITE MEASURE)")
    for a, b in [(0, 930), (930, 1530), (1530, 2770)]:
        d.dimh(a, b, -170)
    d.dimh(2770, BB_L, -170, "30")
    for a, b in [(0, 900), (900, 1500), (1500, 2300), (2300, 2800)]:
        d.dimh(a, b, SOFFIT + 150)
    # dims - vertical
    d.dimv(0, KICK, -150); d.dimv(0, BB_TOP, -300); d.dimv(0, OH_U, -450)
    d.dimv(OH_U, OH_T, -150); d.dimv(BB_TOP - APRON, BB_TOP, BB_L + 150, "40")
    # leaders
    d.leader(2700, BB_TOP - 20, 3000, BB_TOP + 120, "20mm STONE, 40mm MITRED APRON")
    d.leader(2600, 1300, 3000, 1450, "SPLASHBACK – STONE / TILE (OPTION)")
    d.leader(2500, OH_U - 12, 3000, OH_U - 180, "LED STRIP, IP65, U/S OVERHEADS")
    d.leader(1150, 1115, 1350, 1300, "DBL GPO (WEATHERPROOF)")
    d.leader(1200, 1950, 1300, 2150 + 60, "OPEN SHELVING")
    d.leader(600, BB_TOP + 380, 760, BB_TOP + 520, "SINK MIXER (316 SS)")
    d.leader(2600, 2350, 3000, 2380, "BULKHEAD INFILL (OPTION)")
    d.leader(1700, 60, 3000, 260, "VENTED KICK / FRIDGE CLEARANCE")
    return d.svg(-650, -450, 3700, SOFFIT + 330, 20)


def back_bar_section():
    d = D()
    dep = 600
    d.rect(-150, 0, 150, SOFFIT, "wallcut")
    d.line(-150, 0, 1300, 0, "floor")
    d.line(-150, SOFFIT, 1300, SOFFIT, "hid")
    d.rect(0, KICK, 580, BB_TOP - APRON - KICK, "cut")
    d.rect(0, 0, 520, KICK, "kick")
    d.rect(0, BB_TOP - 20, 620, 20, "stone")
    d.rect(600, BB_TOP - APRON, 20, APRON, "stone")
    d.rect(0, OH_U, 350, OH_T - OH_U, "cut")
    d.line(0, OH_U + (OH_T - OH_U) / 2, 350, OH_U + (OH_T - OH_U) / 2, "thin")
    d.rect(0, OH_T, 350, SOFFIT - OH_T, "opt")
    d.dimh(0, 620, -180, "620"); d.dimh(0, 350, OH_T + 120, "350")
    d.dimv(0, BB_TOP, 820); d.dimv(OH_U, OH_T, 820, "700"); d.dimv(BB_TOP, OH_U, 820, "650")
    d.leader(300, BB_TOP - 10, 500, BB_TOP + 250, "STONE TOP")
    d.leader(200, 400, 450, 560, "EXT. GRADE CARCASS")
    return d.svg(-300, -350, 1300, SOFFIT + 300, 25)


def bar_plan():
    d = D()
    WY = 3100
    d.rect(-300, WY, 3400, 150, "wallcut")
    d.rect(0, WY - 620, 2800, 620, "stoneP")
    d.rect(0, WY - 600, 2800, 600, "hidP")
    d.rect(180, WY - 520, 600, 380, "l"); d.circle(480, WY - 80, 30, "l")
    for i in range(2):
        d.rect(1540 + i * 620, WY - 580, 600, 560, "hid")
    d.text(1430, WY - 330, "BACK BAR", 110, cls="appt")
    fy0, fy1 = 510, 1430
    d.rect(0, fy0, 2700, fy1 - fy0, "stoneP")
    d.rect(20, fy1 - 600, 2660, 580, "hid")
    d.rect(550 + 20 - 200, fy1 - 140, 400, 120, "tap")
    d.text(1350, 980, "FRONT BAR", 110, cls="appt")
    for i in range(4):
        d.circle(1350 - 900 + i * 600, 240, 180, "ghost")
    d.dimh(0, 2800, WY + 400, "2800", 100)
    d.dimv(fy1, WY - 620, 3050, "1050 AISLE", 90)
    d.dimv(fy0, fy1, 3050, "920", 90)
    d.dimv(WY - 620, WY, 3050, "620", 90)
    d.text(1350, -150, "TERRACE / STOOLS", 100, cls="note")
    return d.svg(-400, -300, 3500, WY + 550, 50)


# ---------------------------------------------------------------- A-202 front bar
FB_L = 2700
FB_TOP = 1050
END = 20  # waterfall stone end thickness


def front_bar_server():
    d = D()
    ct = FB_TOP - APRON
    d.line(-300, 0, FB_L + 300, 0, "floor")
    d.rect(0, 0, END, FB_TOP, "stone"); d.rect(FB_L - END, 0, END, FB_TOP, "stone")
    d.rect(0, ct, FB_L, APRON, "stone")
    d.rect(END, 0, FB_L - 2 * END, KICK, "kick")
    # keg cabinet pair 1100
    x0 = END
    for i in range(2):
        x = x0 + i * 550
        d.rect(x + 2, KICK, 546, ct - KICK, "door")
        d.swing(x + 2, KICK, 546, ct - KICK, "L" if i == 0 else "R")
    d.handle_v(x0 + 550 - 30, ct - 260, 200); d.handle_v(x0 + 550 + 30, ct - 260, 200)
    d.rect(x0 + 120, KICK + 20, 860, 760, "appl")
    d.text(x0 + 550, KICK + 470, "KEG FRIDGE", 44, cls="appt")
    d.text(x0 + 550, KICK + 400, "(BY OTHERS)", 38, cls="appt")
    # open shelving 900
    x1 = x0 + 1100
    d.rect(x1, KICK, 900, ct - KICK, "l")
    d.line(x1, KICK + (ct - KICK) / 2, x1 + 900, KICK + (ct - KICK) / 2, "l")
    d.text(x1 + 450, KICK + (ct - KICK) * 0.72, "OPEN", 46, cls="note")
    # bin bay 660: drawer + bin pull-out
    x2 = x1 + 900
    w2 = FB_L - END - x2
    d.rect(x2 + 2, ct - 200, w2 - 4, 198, "door"); d.handle_h(x2 + w2 / 2, ct - 70)
    d.rect(x2 + 2, KICK, w2 - 4, ct - 200 - KICK - 2, "door"); d.handle_h(x2 + w2 / 2, ct - 280)
    d.text(x2 + w2 / 2, KICK + 300, "BIN PULL-OUT", 40, cls="note")
    # beer font + drip tray
    fx = x0 + 550
    d.rect(fx - 60, FB_TOP, 120, 380, "tap")
    d.rect(fx - 200, FB_TOP + 380, 400, 90, "tap")
    for dx in (-110, 110):
        d.rect(fx + dx - 12, FB_TOP + 230, 24, 150, "tap")
        d.rect(fx + dx - 18, FB_TOP + 470, 36, 120, "tap")
    d.rect(fx - 260, FB_TOP, 520, 25, "tap")
    # dims
    d.dimh(0, FB_L, -330, f"{FB_L} OVERALL (TBC)")
    for a, b in [(END, x1), (x1, x2), (x2, FB_L - END)]:
        d.dimh(a, b, -170)
    d.dimv(0, KICK, -150); d.dimv(0, FB_TOP, -300)
    d.leader(fx + 200, FB_TOP + 430, fx + 600, FB_TOP + 560, "2-TAP BEER FONT + DRIP TRAY")
    d.leader(FB_L - 10, 600, FB_L + 250, 760, "STONE WATERFALL END (OPTION)")
    return d.svg(-650, -430, 3700, FB_TOP + 720, 20)


def front_bar_customer():
    d = D()
    ct = FB_TOP - APRON
    d.line(-300, 0, FB_L + 300, 0, "floor")
    d.rect(0, 0, END, FB_TOP, "stone"); d.rect(FB_L - END, 0, END, FB_TOP, "stone")
    d.rect(0, ct, FB_L, APRON, "stone")
    # cladding: vertical battens / fluted panel
    d.rect(END, 0, FB_L - 2 * END, ct, "l")
    x = END + 40
    while x < FB_L - END - 20:
        d.line(x, 60, x, ct - 20, "thin")
        x += 80
    d.rect(END, 0, FB_L - 2 * END, 60, "kick")
    # footrest
    d.rect(60, 230, FB_L - 120, 40, "rail")
    for bx in (300, FB_L / 2, FB_L - 300):
        d.line(bx, 230, bx, 0, "rail2")
    # 4 stools, 600 centres
    c0 = FB_L / 2 - 900
    for i in range(4):
        cx = c0 + i * 600
        d.rect(cx - 200, 740, 400, 40, "ghost")
        d.line(cx - 160, 740, cx - 200, 0, "ghost"); d.line(cx + 160, 740, cx + 200, 0, "ghost")
        d.line(cx - 185, 300, cx + 185, 300, "ghost")
    d.dimh(0, FB_L, -330, f"{FB_L} OVERALL (TBC)")
    for i in range(3):
        d.dimh(c0 + i * 600, c0 + (i + 1) * 600, 1250, "600 CRS")
    d.dimv(0, 270, -150, "270"); d.dimv(0, 780, -300, "~760 SEAT"); d.dimv(0, FB_TOP, -450)
    d.leader(FB_L - 400, 600, FB_L + 250, 760, "FLUTED / BATTEN CLADDING – TBC")
    d.leader(FB_L - 200, 250, FB_L + 250, 380, "FOOTREST RAIL – 316 SS / BRASS")
    d.leader(c0 + 1800 + 150, 760, FB_L + 250, 1100, "BAR STOOLS x4 (FF&E, BY OTHERS)")
    return d.svg(-800, -430, 3700, FB_TOP + 300, 20)


def front_bar_section():
    d = D()
    ct = FB_TOP - APRON
    # server side at x=0, customer face at x=600, overhang to 900
    d.line(-700, 0, 1500, 0, "floor")
    d.rect(0, KICK, 580, ct - KICK, "cut")
    d.rect(60, 0, 520, KICK, "kick")
    d.rect(580, 0, 20, ct, "cut")
    d.rect(-20, FB_TOP - 20, 920, 20, "stone")
    d.rect(-20, ct, 20, APRON, "stone"); d.rect(880, ct, 20, APRON, "stone")
    d.line(0, KICK + (ct - KICK) / 2, 580, KICK + (ct - KICK) / 2, "thin")
    # footrest
    d.circle(690, 250, 25, "rail")
    d.line(600, 250, 665, 250, "rail2")
    # stool ghost
    d.rect(950, 740, 400, 40, "ghost"); d.line(990, 740, 950, 0, "ghost"); d.line(1310, 740, 1350, 0, "ghost")
    # back bar ghost at walkway
    d.rect(-1100 - 620, 0, 620, BB_TOP, "ghost")
    d.dimh(-20, 900, FB_TOP + 150, "920 TOP")
    d.dimh(600, 900, FB_TOP + 300, "300 O/HANG")
    d.dimh(-1100, -20, 500, "1000–1100 WORK AISLE")
    d.dimv(0, FB_TOP, 1500 - 60)
    d.text(-1100 - 310, BB_TOP + 60, "BACK BAR", 44, cls="appt")
    d.text(290, 300, "SERVER SIDE", 40, cls="note"); d.text(1150, 950, "CUSTOMER", 40, cls="note")
    return d.svg(-1800, -260, 1600, FB_TOP + 460, 20)


# ---------------------------------------------------------------- A-101 plan (schematic)
def plan():
    d = D()
    W, H = 12400, 6600   # schematic only, NTS
    # parapet outline with entry notch at bottom middle (as client sketch)
    outline = [(0, 0), (0, H), (W, H), (W, 0), (7300, 0), (7300, 1300), (3100, 1300), (3100, 0)]
    # turf zone (indicative)
    d.poly([(2600, 1500), (2600, H - 250), (W - 250, H - 250), (W - 250, 250), (7550, 250), (7550, 1500)], "turfz", closed=True)
    d.poly(outline + [(0, 0)], "parapet")
    # covers (dashed)
    d.rect(150, 3600, 6500, 2850, "covr"); d.text(4500, 6250, "EXISTING COVER 01", 150, cls="note")
    d.rect(7400, 1600, 4850, 4850, "covr"); d.text(9825, 6250, "EXISTING COVER 02", 150, cls="note")
    # columns
    for cx, cy in [(2500, 3700), (6550, 3700), (7500, 1700), (7500, 4500), (12150, 1700), (12150, 4500)]:
        d.rect(cx - 150, cy - 150, 300, 300, "col")
        d.rect(cx - 45, cy - 45, 90, 90, "colk")
    # bar zone top-left
    d.rect(0, 3800, 600, 2800, "bbar")           # back bar against wall
    d.rect(1700, 3900, 900, 2500, "fbar")        # front bar
    for k in range(4):
        d.circle(2900, 4400 + k * 600, 170, "stool")
    d.text(300, 5200, "BACK BAR", 140, cls="lbl", rot=-90)
    d.text(2150, 5150, "FRONT BAR", 140, cls="lbl", rot=-90)
    d.dimh(600, 1700, 3250, "1000–1100", 130)
    d.text(1150, 3200, "BAR ZONE — SEE A-201 / A-202", 140, cls="lblb")
    # entry
    d.line(3100, 1300, 3100, 400, "door")
    d.add(f'<path d="M3100 -400 A900 900 0 0 1 4000 -1300" class="swingp"/>')
    d.text(5200, 650, "ENTRY / STAIR & LIFT LOBBY", 160, cls="lblb")
    # shed, lounge, dining
    d.rect(10200, 300, 1900, 1100, "furn"); d.text(11150, 780, "EXIST. SHED (RETAIN)", 130, cls="note")
    d.rect(8200, 2600, 2600, 1400, "furn"); d.text(9500, 3220, "DINING (LOOSE)", 130, cls="note")
    d.rect(8000, 5000, 3500, 1000, "furn"); d.text(9750, 5420, "LOUNGE (LOOSE)", 130, cls="note")
    d.rect(4200, 5200, 2200, 1000, "furn"); d.text(5300, 5620, "LOUNGE / BAR SEATING", 130, cls="note")
    # services
    d.circle(5200, 2600, 120, "fw"); d.text(5200, 2300, "FW", 120, cls="note")
    d.circle(9600, 1500, 120, "fw"); d.text(9600, 1200, "FW", 120, cls="note")
    d.text(1200, 2600, "HOSE REEL & GATE", 120, cls="note")
    # north / NTS
    d.text(W - 300, H + 450, "SCHEMATIC — NOT TO SCALE", 170, anchor="end", cls="lblb")
    return d.svg(-600, -900, W + 600, H + 800, 45, "plan")


# ---------------------------------------------------------------- report content
PHOTOS = [
    ("IMG_9192", "Looking across covered dining zone to shed, planter and south-east corner. Second cover at right. Downpipe discharges at column plinth."),
    ("IMG_9193", "Open corner beside cover: folding table + stools. Membrane coating stained/worn. Rendered parapet ~1.1–1.2 m."),
    ("IMG_9194", "Walkway between the two skillion covers. Quad gutters each side; open sky over walkway — rain & UV exposure here."),
    ("IMG_9196", "Plastic garden shed (fridge + boards stored). Weatherproof GPO on wall at right. Hose lying across floor."),
    ("IMG_9197", "Covered zone near entry gate — candidate bar location. Bunker light on wall, steel column on rendered plinth."),
    ("IMG_9199", "Main covered area: black steel columns, FC soffit with exposed fixings. Mould / dark staining on membrane."),
    ("IMG_9200", "Shed side & column. Floor waste grate visible mid-image. Hose and debris on floor."),
    ("IMG_9202", "Under-cover view to entry gate & hose reel. Tall rendered wall (lift/plant) shows vertical water staining."),
]

OBS = [
    ("Structure / roof", "Two skillion roof covers on black-painted steel columns, set on rendered concrete plinths (~400 sq). FC sheet soffit with exposed fixings; quad gutters & downpipes.", "Bar fits under Cover 01. Confirm soffit height (assumed ~2450). No fixings into soffit/columns without BC/engineer OK."),
    ("Floor", "Concrete slab with sand-coloured trafficable membrane coating. Widespread dark staining & mould, worn patches, ponding marks near drains. Floor wastes (round grates) present.", "Membrane condition & warranty must be confirmed before turf. Turf must not be mechanically fixed through membrane; drains to stay accessible."),
    ("Walls / parapets", "Rendered masonry parapets ~1.1–1.2 m; taller rendered lift/plant wall. Water streaking & mould to wall faces; minor cracking.", "Soft-wash + mould treatment, repaint. Back bar fixes to wall — check wall build-up & membrane upturn."),
    ("Drainage", "Downpipes discharge directly onto deck beside plinths, causing staining. Floor wastes appear clear (to verify).", "Extend downpipes to floor waste / spreader. Sink waste CANNOT go to stormwater — needs sewer connection or pump-out."),
    ("Services", "Weatherproof GPO near shed, garden tap & wall hose reel at entry, bunker lights, festoon string lights on hooks. No plumbing or dedicated circuits visible at bar zone.", "New hot/cold + sewer drainage and dedicated circuits needed for sink, keg fridge, 2 x bar fridges, LED."),
    ("Access", "Rooftop accessed via entry gate from stair/lift lobby.", "Check lift car size for stone slabs (2.8 m bench) & joinery modules — may need a joint or crane lift."),
    ("Exposure", "Elevated coastal rooftop: high wind, UV and salt air. Covers give partial protection only.", "Use exterior-grade joinery materials, 316 SS hardware, UV-stable sintered/porcelain stone (NOT engineered quartz)."),
    ("Existing items", "Loose outdoor furniture, folding tables, wire bar stools, egg-chair stand, mirror, clothes airer, planter (rubber tree), shed, bike, hoses, debris.", "Clear and dispose / store before works. Shed retained (confirm)."),
]

SCOPE = [
    ("1. Preliminaries & approvals", [
        "Body corporate approval — confirm exclusive-use vs common property, by-laws, contractor induction & lift booking.",
        "Detailed site measure; confirm soffit height, wall set-out, column positions & falls to drains.",
        "Protect membrane, lift & common areas throughout works. Rubbish removal.",
    ]),
    ("2. Clean & make good", [
        "Remove loose items/debris; low-pressure clean slab (protect membrane); mould treatment to slab, walls, plinths.",
        "Inspect membrane; repair/recoat as required by waterproofer before turf (flood test where repaired).",
        "Extend downpipes to nearest floor waste / spreader; clear and test floor wastes.",
    ]),
    ("3. Plumbing (licensed)", [
        "Cold (and hot — under-sink instantaneous unit option) to bar sink; isolation valves.",
        "Sink waste to sewer via nearest stack, or grey-water pump-out unit if gravity not achievable. Keg drip-tray drain to sink waste.",
        "Compliance certificate on completion.",
    ]),
    ("4. Electrical (licensed)", [
        "Dedicated RCD-protected circuits: keg fridge, bar fridge 01, bar fridge 02.",
        "2 x weatherproof double GPOs in splashback; IP65 LED strip under overheads with driver & switch.",
        "Re-hang festoon lighting; optional feature pendants over front bar.",
    ]),
    ("5. Joinery — back bar (A-201)", [
        "2.8 m run: sink pair doors 900, 3-drawer bank 600, cavity for 2 x under-bench bar fridges (2 x 620).",
        "Overheads 700 h x 350 d @ 1550 AFL: pair 900 / open cubbies 600 / pair 800 / single 500. Optional bulkhead infill to soffit.",
        "Exterior-grade carcass (marine ply 2-pac or compact laminate), 316 SS hinges & runners, soft-close, adjustable feet, vented kick.",
    ]),
    ("6. Joinery — front bar (A-202)", [
        "2.7 m island: keg-fridge cabinet pair 1100, open shelving 900, bin bay 660 (drawer over twin bin pull-out).",
        "Customer face fluted / batten cladding (TBC); 316 SS or brass footrest rail @ ~270 AFL.",
        "Bar top 1050 AFL with 300 overhang for 4 stools @ 600 crs.",
    ]),
    ("7. Stone", [
        "20 mm UV-stable sintered/porcelain stone, 40 mm mitred apron to all exposed edges (per client note).",
        "Undermount sink & tap cut-outs; beer-font cut-out; waterfall ends to front bar (option); splashback (option).",
        "Template after joinery install; check lift access for slab lengths.",
    ]),
    ("8. Synthetic turf", [
        "Free-draining, UV-stabilised turf (~35–40 mm, no sand infill) on protection/drainage underlay over membrane.",
        "Loose-laid with joining tape & perimeter edging — no fixings through membrane. Removable access at floor wastes.",
        "Extent per A-101 (TBC). Lighter tone recommended to limit surface heat.",
    ]),
    ("9. Painting & finishes", [
        "Treat any rust & repaint steel columns; clean/repaint FC soffit, render walls & plinths.",
    ]),
]

EXCL = [
    "Appliances (keg fridge, bar fridges), beer system, gas & kegs — by others unless noted.",
    "Loose furniture & bar stools (FF&E) — by others.",
    "Structural engineering & body corporate fees.",
    "Membrane replacement beyond local repair (price separately once inspected).",
]

RFI = [
    "Confirm bar location (assumed under Cover 01, near entry — per sketch) and turf extent.",
    "Soffit height under Cover 01 and wall construction behind back bar.",
    "Appliance models: keg fridge (no. of kegs / taps — 2 taps shown), bar fridge sizes (≤ 600 W x 850 H assumed).",
    "Hot water at sink required? Glass rinser wanted?",
    "Stone selection & joinery colour/finish; customer-face cladding style.",
    "Lift car internal dimensions (stone & joinery delivery).",
    "Exclusive-use status, membrane age/warranty, and target budget.",
]

FINISHES = [
    ("ST-01", "Bar tops", "20 mm sintered / porcelain stone, 40 mm mitred apron", "UV-stable; colour TBC"),
    ("ST-02", "Waterfall ends / splash", "As ST-01", "Option"),
    ("JN-01", "Carcass", "Marine ply (2-pac) or compact laminate", "No HMR / MDF outdoors"),
    ("JN-02", "Door & drawer fronts", "2-pac polyurethane or compact laminate", "Colour TBC"),
    ("JN-03", "Front bar cladding", "Fluted panel / hardwood battens", "TBC"),
    ("HW-01", "Hinges / runners", "316 stainless, soft-close", "Coastal grade"),
    ("HW-02", "Handles / footrest", "316 SS or solid brass", "TBC"),
    ("PL-01", "Sink & mixer", "316 SS undermount sink, gooseneck mixer", ""),
    ("EL-01", "LED strip", "IP65 aluminium channel, 3000K", "U/S overheads"),
    ("TF-01", "Synthetic turf", "Perforated, UV-stabilised, no infill", "On drainage underlay"),
]

# ---------------------------------------------------------------- page assembly
pages = []
SHEETS = [
    ("00", "Cover & contents"), ("01", "Site report — existing conditions"),
    ("02", "Site photographs"), ("03", "Scope of works"),
    ("A-101", "Indicative layout plan"), ("A-201", "Back bar — elevation, section & bar plan"),
    ("A-202", "Front bar — elevations & section"), ("04", "Finishes schedule, RFIs & next steps"),
]


def titleblock(no, title, scale="NTS"):
    return f"""<div class="tb">
  <div class="tb-firm"><b>{BY}</b><span>Design & documentation</span></div>
  <div class="tb-proj"><span class="k">Project</span><b>{PROJECT}</b><span>{SUB}</span></div>
  <div class="tb-cell"><span class="k">Sheet</span><b>{html.escape(title)}</b></div>
  <div class="tb-cell s"><span class="k">Scale @ A3</span><b>{scale}</b></div>
  <div class="tb-cell s"><span class="k">Date</span><b>{DATE}</b></div>
  <div class="tb-cell s"><span class="k">Rev</span><b>{REV}</b></div>
  <div class="tb-no"><span class="k">Dwg no.</span><b>{no}</b></div>
</div>"""


def page(no, title, body, scale="NTS"):
    pages.append(f'<section class="sheet"><div class="body">{body}</div>{titleblock(no, title, scale)}</section>')


# cover
contents = "".join(f"<tr><td>{n}</td><td>{t}</td></tr>" for n, t in SHEETS)
page("00", "Cover & contents", f"""
<div class="cover">
  <div class="cover-l">
    <p class="eyebrow">Site report · Scope of works · Concept drawings</p>
    <h1>1 Toombul Ave<br>Rooftop Terrace</h1>
    <p class="lede">Covered outdoor bar with custom joinery and stone tops, synthetic turf, and general make-good of the rooftop terrace.</p>
    <table class="kv">
      <tr><td>Site inspected</td><td>{DATE}</td></tr>
      <tr><td>Revision</td><td>{REV} — {REV_NOTE}</td></tr>
      <tr><td>Status</td><td>Concept / indicative — all dimensions subject to site measure</td></tr>
    </table>
    <h3>Contents</h3>
    <table class="contents">{contents}</table>
  </div>
  <div class="cover-r"><img src="photos/IMG_9199.jpg"><img src="photos/IMG_9194.jpg"></div>
</div>""")

# site report
obs_rows = "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td></tr>" for a, b, c in OBS)
page("01", "Site report — existing conditions", f"""
<div class="cols2">
 <div>
  <h2>Brief</h2>
  <p>Client wants to turn the rooftop terrace into a usable entertaining space: a <b>bar under the existing cover</b> with
  custom <b>joinery and stone</b> (back bar with sink, drawers and 2 × bar fridges; island front bar with keg fridge &amp; beer taps, open shelving and bin),
  <b>synthetic turf</b>, and general clean-up / make-good. Client sketches (back bar, front bar both sides, layout) were reviewed on site and are
  reproduced with the drawings.</p>
  <h2>Site summary</h2>
  <p>Large open rooftop terrace on a multi-storey residential building, with two skillion roof covers on steel columns, rendered parapets,
  a membrane-coated slab, a plastic storage shed, and access through a gate from the stair/lift lobby. Exposed elevated coastal setting
  with district and hinterland views.</p>
  <h2>Key risks</h2>
  <ul class="risk">
   <li><b>Waterproofing</b> — every item touching the slab (turf, joinery feet, plumbing penetrations) must protect the membrane. Get it inspected first.</li>
   <li><b>Sink drainage</b> — sewer connection on a roof is the biggest unknown and cost driver. A pump-out unit is the fallback.</li>
   <li><b>Body corporate</b> — approval needed for fixed works, plumbing and electrical on (likely) common property.</li>
   <li><b>Weathering</b> — wind-driven rain, UV & salt: specify exterior materials and UV-stable stone.</li>
   <li><b>Access</b> — stone and joinery must fit the lift, or be jointed / craned.</li>
  </ul>
  <div class="mini"><figure><img src="photos/IMG_9197.jpg"><figcaption>P5 — proposed bar zone under Cover 01</figcaption></figure>
  <figure><img src="photos/IMG_9200.jpg"><figcaption>P7 — membrane staining, floor waste, hose across deck</figcaption></figure></div>
 </div>
 <div>
  <h2>Existing conditions</h2>
  <table class="grid obs"><thead><tr><th style="width:16%">Element</th><th>Observed</th><th style="width:38%">Implication</th></tr></thead><tbody>{obs_rows}</tbody></table>
 </div>
</div>""")

# photos
ph = "".join(f'<figure><img src="photos/{n}.jpg"><figcaption><b>P{i + 1}</b> {html.escape(c)}</figcaption></figure>' for i, (n, c) in enumerate(PHOTOS))
page("02", "Site photographs", f'<h2>Site photographs</h2><div class="photos">{ph}</div>')

# scope
sc = "".join(f'<div class="scope-item"><h4>{h}</h4><ul>{"".join(f"<li>{html.escape(x)}</li>" for x in items)}</ul></div>' for h, items in SCOPE)
ex = "".join(f"<li>{html.escape(x)}</li>" for x in EXCL)
page("03", "Scope of works", f"""<h2>Scope of works <span class="muted">— for pricing; read with A-101, A-201, A-202</span></h2>
<div class="scope">{sc}<div class="scope-item excl"><h4>Exclusions / by others</h4><ul>{ex}</ul></div></div>""")

# A-101
page("A-101", "Indicative layout plan", f"""
<div class="dwgrow">
 <div class="dwgbox">{plan()}
  <div class="dwgtitle"><span class="bub">1</span><div><b>INDICATIVE LAYOUT PLAN</b><br>Schematic only — traced from client sketch &amp; photos. Not to scale.</div></div>
  <div class="legend">
   <span><i class="sw turf"></i>Proposed synthetic turf (extent TBC)</span>
   <span><i class="sw cov"></i>Existing roof cover</span>
   <span><i class="sw colk"></i>Existing steel column on plinth</span>
   <span><i class="sw bar"></i>New bar joinery</span>
   <span><i class="sw fw"></i>FW Floor waste (approx.)</span>
  </div>
 </div>
 <div class="side">
  <figure class="sk"><img src="sketches/IMG_9204_plan.jpg"><figcaption>Client layout sketch</figcaption></figure>
  <div class="notes"><h4>Notes</h4><ol>
   <li>Layout is diagrammatic. Overall size, column and drain positions to be confirmed on site measure.</li>
   <li>Bar zone under Cover 01 near the entry, per client sketch. Back bar on wall; island front bar with 4 stools facing the terrace.</li>
   <li>Keep min. 1000 mm work aisle between back and front bar; 1000 mm clear path past stools.</li>
   <li>Turf loose-laid on underlay over membrane; drains stay accessible.</li>
  </ol></div>
 </div>
</div>""")

# A-201
page("A-201", "Back bar — elevation, section & bar plan", f"""
<div class="dwgrow">
 <div class="dwgbox">{back_bar_elev()}
  <div class="dwgtitle"><span class="bub">1</span><div><b>BACK BAR — ELEVATION</b><br>1:20 @ A3</div></div></div>
 <div class="stack"><div class="dwgbox">{back_bar_section()}
  <div class="dwgtitle"><span class="bub">2</span><div><b>SECTION</b><br>1:25 @ A3</div></div></div>
  <div class="dwgbox">{bar_plan()}
  <div class="dwgtitle"><span class="bub">3</span><div><b>BAR PLAN</b><br>1:50 @ A3</div></div></div></div>
 <div class="side">
  <figure class="sk"><img src="sketches/IMG_9206_back-bar.jpg"><figcaption>Client sketch — back bar</figcaption></figure>
  <div class="notes"><h4>Notes</h4><ol>
   <li>All dims in mm, indicative, subject to site measure &amp; appliance specs.</li>
   <li>Bar fridge cavity 860 clear under stone — confirm models ≤ 850 H with front venting.</li>
   <li>Door-swing triangles point to hinge side.</li>
   <li>Stone 20 mm with 40 mm mitred apron, all exposed edges.</li>
   <li>Sink waste to sewer / pump-out — never stormwater.</li>
  </ol></div>
 </div>
</div>""", "1:20 / 1:25 / 1:50")

# A-202
page("A-202", "Front bar — elevations & section", f"""
<div class="dwgrow">
 <div class="stack">
  <div class="dwgbox">{front_bar_server()}
   <div class="dwgtitle"><span class="bub">1</span><div><b>FRONT BAR — SERVER SIDE</b><br>1:20 @ A3</div></div></div>
  <div class="dwgbox">{front_bar_customer()}
   <div class="dwgtitle"><span class="bub">2</span><div><b>FRONT BAR — CUSTOMER SIDE</b><br>1:20 @ A3</div></div></div>
 </div>
 <div class="stack">
  <div class="dwgbox">{front_bar_section()}
   <div class="dwgtitle"><span class="bub">3</span><div><b>SECTION THROUGH BAR</b><br>1:20 @ A3</div></div></div>
  <div class="skrow">
   <figure class="sk"><img src="sketches/IMG_9205_front-bar-server.jpg"><figcaption>Client sketch — server side</figcaption></figure>
   <figure class="sk"><img src="sketches/IMG_9207_front-bar-customer.jpg"><figcaption>Client sketch — customer side</figcaption></figure>
  </div>
  <div class="notes"><h4>Notes</h4><ol>
   <li>Single-level top at 1050 AFL (bar height) — confirm vs split level (900 work / 1100 bar).</li>
   <li>Keg fridge needs front-breathing plinth; check model width fits 1100 bay.</li>
   <li>Beer font, lines &amp; drip tray drain coordinated with keg supplier.</li>
  </ol></div>
 </div>
</div>""", "1:20")

# finishes + RFI
fin = "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td><td class='muted'>{d}</td></tr>" for a, b, c, d in FINISHES)
rfi = "".join(f"<li>{html.escape(x)}</li>" for x in RFI)
page("04", "Finishes schedule, RFIs & next steps", f"""
<div class="cols2">
 <div><h2>Finishes &amp; materials schedule</h2>
  <table class="grid"><thead><tr><th>Code</th><th>Item</th><th>Specification</th><th>Note</th></tr></thead><tbody>{fin}</tbody></table>
  <p class="muted small">Engineered quartz is not recommended outdoors — UV causes yellowing and most suppliers void the warranty for exterior use.</p>
 </div>
 <div><h2>Questions for client (RFIs)</h2><ol class="rfi">{rfi}</ol>
  <h2>Next steps</h2>
  <ol class="rfi">
   <li>Client answers RFIs; body corporate application lodged.</li>
   <li>Waterproofer inspects membrane; plumber confirms sewer route (or pump-out).</li>
   <li>Full site measure → Rev B drawings with confirmed dimensions &amp; appliance specs.</li>
   <li>Issue Rev B to joiner, stonemason, plumber, electrician &amp; turf installer for quotes.</li>
  </ol></div>
</div>""")

CSS = (ROOT / "src" / "style.css").read_text()
OUT.write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>1 Toombul Ave Rooftop — Site Report, Scope &amp; Drawings Rev {REV}</title>
<style>{CSS}</style></head><body>{''.join(pages)}</body></html>""")
print("wrote", OUT)
