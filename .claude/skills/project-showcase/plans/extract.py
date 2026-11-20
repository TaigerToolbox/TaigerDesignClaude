"""IFC -> clickable plan data: storeys, units, rooms, wall sections, fixtures. Normal Python (ifcopenshell, shapely, numpy).

Plans are cut, not traced: every wall, door, window, column and curtain-wall part on a storey is sliced
at cut height (1.2 m by default, the drawing convention), so openings show as gaps just like the
architect's plan. Rooms come from IfcSpace when the model has them; otherwise from the wall section
itself (door gaps closed, enclosed areas kept) and are named from the fixtures inside them (a cooktop
makes a kitchen). A room the model gives no evidence for stays "Room N"; nothing is guessed.
"""
import re, multiprocessing
import numpy as np
import shapely
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.ops import polylabel
import ifcopenshell, ifcopenshell.geom, ifcopenshell.util.unit, ifcopenshell.util.placement
import ifcopenshell.util.element as uel

CUT_CLASSES = ("IfcWall IfcWallStandardCase IfcCurtainWall IfcColumn IfcDoor IfcWindow IfcPlate IfcMember "
               "IfcRailing IfcStairFlight IfcBuildingElementProxy").split()
CLOSE_CLASSES = {"IfcWall", "IfcWallStandardCase", "IfcCurtainWall", "IfcColumn", "IfcDoor", "IfcWindow", "IfcPlate",
                 "IfcMember", "IfcRailing"}  # what bounds a room
FIXTURE_CLASSES = ("IfcFurnishingElement IfcFurniture IfcFlowTerminal IfcSanitaryTerminal IfcElectricAppliance "
                   "IfcBuildingElementProxy IfcStairFlight IfcTransportElement").split()
IGNORE = r"hinge|handle|pull|knob|screen|door|rail_hafele|towel"  # hardware names that mention a room fixture
# Room type from what is physically in it. Order matters: a kitchen with a fridge is not a laundry.
ROOM_RULES = [
    ("Kitchen", r"cooktop|\boven\b|rangehood|range hood|dishwasher|kitchen sink"),
    ("Bathroom", r"shower|\bbath(tub)?\b|bath_|kaldewei"),
    ("Laundry", r"washing machine|laundry|trough|dryer"),
    ("WC / powder", r"toilet|\bwc\b|\bpan\b"),
    ("Lift", r"\blift\b|elevator|IfcTransportElement"),
    ("Stair", r"IfcStairFlight"),
    ("Bedroom", r"\bbed\b|bed_|double bed|queen bed|king bed"),
]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-") or "x"


def section_polys(verts, faces, z):
    """Slice a triangulated solid at height z -> list of shapely polygons (plan section)."""
    V = np.asarray(verts, dtype=float).reshape(-1, 3)
    F = np.asarray(faces, dtype=np.int64).reshape(-1, 3)
    if not len(F):
        return []
    T = V[F]
    d = T[:, :, 2] - z
    d[np.abs(d) < 1e-7] = 1e-7  # nudge vertices that sit exactly on the plane
    s = d > 0
    m = (s.sum(1) == 1) | (s.sum(1) == 2)
    T, d, s = T[m], d[m], s[m]
    if not len(T):
        return []
    pts, ok = [], []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        with np.errstate(divide="ignore", invalid="ignore"):  # non-crossing edges are masked out below
            t = d[:, i] / (d[:, i] - d[:, j])
            pts.append(T[:, i, :2] + t[:, None] * (T[:, j, :2] - T[:, i, :2]))
        ok.append(s[:, i] != s[:, j])
    pts, ok = np.stack(pts, 1), np.stack(ok, 1)  # (n,3,2), (n,3): exactly two edges cross per triangle
    idx = np.argsort(~ok, axis=1, kind="stable")[:, :2]
    seg = np.round(np.take_along_axis(pts, idx[:, :, None], 1), 4)
    lines = shapely.linestrings(seg)
    polys = [q for p in shapely.get_parts(shapely.polygonize(lines.tolist())) if p.area > 1e-5
             for q in polys_of(shapely.make_valid(p))]
    if not polys:  # open meshes: draw the cut lines with a hairline width instead
        u = shapely.union_all(shapely.buffer(lines, 0.01))
        return [u] if not u.is_empty else []
    return polys


def footprint(verts, faces):
    """Plan projection of the up-facing triangles (spaces, slabs)."""
    V = np.asarray(verts, dtype=float).reshape(-1, 3)
    F = np.asarray(faces, dtype=np.int64).reshape(-1, 3)
    T = V[F]
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    up = n[:, 2] > 1e-6 * np.linalg.norm(n, axis=1).clip(1e-12)
    tri = shapely.polygons(np.round(T[up][:, :, :2], 4))
    tri = tri[shapely.area(tri) > 1e-8]
    return shapely.union_all(tri).buffer(0) if len(tri) else Polygon()


def label(e):
    return " ".join(x for x in (e.Name, getattr(e, "ObjectType", None)) if x)


def area_from_quantities(e):
    for pset in uel.get_psets(e).values():
        for k in ("NetFloorArea", "GrossFloorArea", "NetArea", "GrossArea", "Area"):
            v = pset.get(k)
            if isinstance(v, (int, float)) and v > 0:
                return float(v), k
    return None, None


def polys_of(g):
    if g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g]
    return [q for p in getattr(g, "geoms", []) for q in polys_of(p)]


def extract(ifc_path, cfg, log=print):
    f = ifcopenshell.open(ifc_path)
    unit = ifcopenshell.util.unit.calculate_unit_scale(f)
    cut = float(cfg.get("cut_height", 1.2))
    gap = float(cfg.get("door_gap", 0.35))  # half the widest opening closed when finding rooms
    min_room = float(cfg.get("min_room_m2", 1.2))
    st_ex = re.compile(cfg.get("storeys_exclude", r"^$a"), re.I)
    sp_ex = re.compile(cfg.get("spaces_exclude", r"^$a"), re.I)
    units_cfg = cfg.get("units", {"from": "spaces"})
    unit_rx = re.compile(units_cfg.get("match", ".*"), re.I)
    rules = [(n, re.compile(r, re.I)) for n, r in cfg.get("room_rules", ROOM_RULES)]
    ignore = re.compile(cfg.get("fixture_ignore", IGNORE), re.I)
    known = {d.name() for d in ifcopenshell.ifcopenshell_wrapper.schema_by_name(f.schema_identifier).declarations()}

    def zworld(st):
        try:
            return float(ifcopenshell.util.placement.get_local_placement(st.ObjectPlacement)[2][3]) * unit
        except Exception:
            return float(st.Elevation or 0) * unit

    storeys = sorted(f.by_type("IfcBuildingStorey"), key=zworld)
    seen, ordered = set(), []
    for st in storeys:  # some exports repeat a datum storey
        if st.Name in seen or st_ex.search(st.Name or ""):
            continue
        seen.add(st.Name); ordered.append(st)

    # one geometry pass over everything we need, multi-threaded
    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", True)
    want = {}
    for st in ordered:
        for e in uel.get_decomposition(st):
            if e.is_a() in CUT_CLASSES or e.is_a("IfcSpace") or e.is_a("IfcSlab"):
                want[e.id()] = e
            if e.is_a() in FIXTURE_CLASSES and not ignore.search(label(e)) and any(rx.search(label(e) + " " + e.is_a()) for _, rx in rules):
                want[e.id()] = e
            for rel in getattr(e, "HasOpenings", None) or []:  # door and window voids close rooms exactly
                want[rel.RelatedOpeningElement.id()] = rel.RelatedOpeningElement
    geo = {}
    if want:
        it = ifcopenshell.geom.iterator(settings, f, max(1, multiprocessing.cpu_count() - 1), include=list(want.values()))
        if it.initialize():
            while True:
                sh = it.get()
                geo[sh.id] = (np.asarray(sh.geometry.verts), np.asarray(sh.geometry.faces))
                if not it.next():
                    break
    log("geometry: %d of %d elements" % (len(geo), len(want)))

    out_storeys, units, rooms = [], [], []
    for si, st in enumerate(ordered):
        z0 = zworld(st)
        zc = z0 + cut
        elems = uel.get_decomposition(st)
        layers = {"wall": [], "door": [], "window": [], "other": []}
        closers = []
        for e in elems:
            if e.is_a() not in CUT_CLASSES or e.id() not in geo:
                continue
            v, fc = geo[e.id()]
            zs = v[2::3]
            if not len(zs) or zs.min() > zc or zs.max() < zc:
                continue
            ps = section_polys(v, fc, zc)
            if not ps:
                continue
            k = {"IfcDoor": "door", "IfcWindow": "window", "IfcPlate": "window", "IfcMember": "window"}.get(e.is_a(), "wall")
            if e.is_a() in ("IfcBuildingElementProxy", "IfcStairFlight", "IfcRailing"):
                k = "other"
            layers[k] += ps
            if e.is_a() in CLOSE_CLASSES:
                closers += ps
        for e in elems:
            for rel in getattr(e, "HasOpenings", None) or []:
                o = rel.RelatedOpeningElement
                if o.id() in geo:
                    v, fc = geo[o.id()]
                    zs = v[2::3]
                    if len(zs) and zs.min() <= zc <= zs.max():
                        closers += section_polys(v, fc, zc)
        walls = shapely.union_all(layers["wall"]) if layers["wall"] else Polygon()
        if walls.is_empty:
            log("storey %s: nothing cut at %.2f m, skipped" % (st.Name, cut))
            continue
        sid = slug(st.Name)
        slabs = [footprint(*geo[e.id()]) for e in elems if e.is_a("IfcSlab") and e.id() in geo]
        slabs = [s for s in slabs if not s.is_empty]
        outline = shapely.union_all(slabs).buffer(0.01).buffer(-0.01) if slabs else Polygon()

        fixtures = []
        for e in elems:
            if e.is_a() not in FIXTURE_CLASSES:
                continue
            if ignore.search(label(e)):
                continue
            if e.id() in geo:
                v = geo[e.id()][0]
                fixtures.append((Point((v[0::3].min() + v[0::3].max()) / 2, (v[1::3].min() + v[1::3].max()) / 2), label(e) + " " + e.is_a()))
                continue
            try:
                m = ifcopenshell.util.placement.get_local_placement(e.ObjectPlacement)
                fixtures.append((Point(m[0][3] * unit, m[1][3] * unit), label(e) + " " + e.is_a()))
            except Exception:
                pass

        # units: named IfcSpaces (merged by name), or the whole storey
        st_units = []
        spaces = [e for e in elems if e.is_a("IfcSpace") and e.id() in geo]
        if units_cfg.get("from") == "spaces":
            byname = {}
            for sp in spaces:
                nm = (sp.LongName or sp.Name or "").strip()
                if nm and unit_rx.search(nm) and not sp_ex.search(nm):
                    byname.setdefault(nm, []).append(sp)
            for nm, sps in sorted(byname.items()):
                poly = shapely.union_all([footprint(*geo[s.id()]) for s in sps]).buffer(0)
                q = [area_from_quantities(s) for s in sps]
                qa = sum(a for a, _ in q if a) if all(a for a, _ in q) else None
                st_units.append({"id": "%s-u-%s" % (sid, slug(nm)), "name": nm, "storey": st.Name, "poly": poly,
                                 "area": round(qa, 1) if qa else round(poly.area, 1),
                                 "area_source": "IFC quantity %s" % q[0][1] if qa else "measured from the IfcSpace footprint",
                                 "ifc": [s.GlobalId for s in sps]})
        elif units_cfg.get("from") == "storey":
            name = units_cfg.get("name", "{storey}").format(storey=st.Name.title())
            st_units.append({"id": "%s-u" % sid, "name": name, "storey": st.Name, "poly": outline if not outline.is_empty else walls.convex_hull,
                             "area": None, "area_source": None, "ifc": []})

        # rooms: from IfcSpace (non-unit, non-excluded) and from the wall section
        st_rooms = []
        if cfg.get("rooms_from_spaces", True):
            for sp in spaces:
                nm = (sp.LongName or sp.Name or "").strip()
                if not nm or sp_ex.search(nm) or (units_cfg.get("from") == "spaces" and unit_rx.search(nm)):
                    continue
                poly = footprint(*geo[sp.id()])
                if poly.area < min_room:
                    continue
                qa, qk = area_from_quantities(sp)
                st_rooms.append({"name": nm.title(), "type": "space", "poly": poly, "area": round(qa or poly.area, 1),
                                 "area_source": ("IFC quantity " + qk) if qa else "measured from the IfcSpace footprint",
                                 "named_by": "IfcSpace name", "ifc": [sp.GlobalId]})
        if cfg.get("rooms_from_walls", True):
            closed = shapely.union_all(closers).buffer(gap, join_style="mitre").buffer(-gap, join_style="mitre")
            # floor plate (slabs on this storey) plus anything enclosed by walls, minus the closed walls
            rings = [Polygon(r) for p in polys_of(closed) for r in p.interiors]
            region = shapely.union_all([outline] + rings) if rings else outline
            taken = [r["poly"] for r in st_rooms]
            for room in polys_of(region.difference(closed)):
                room = room.buffer(0)
                # a room-sized space already covers it (a unit-sized one doesn't)
                if room.area < min_room or any(t.area < 3 * room.area and t.intersection(room).area > 0.5 * room.area for t in taken):
                    continue
                hits = [txt for p, txt in fixtures if room.contains(p)]
                name, why = None, None
                for nm, rx in rules:
                    w = [h for h in hits if rx.search(h)]
                    if w:
                        name, why = nm, w[0].split(" Ifc")[0][:60]
                        break
                if name == "Kitchen" and room.area > float(cfg.get("open_plan_m2", 35)):
                    name = "Open-plan kitchen"  # no walls between kitchen, dining and living: one room in the model
                elif name and room.area > {"Bathroom": 20, "WC / powder": 10, "Laundry": 12, "Bedroom": 40}.get(name, 1e9):
                    name += " and adjoining rooms"  # walls with open gaps joined it to its neighbours
                st_rooms.append({"name": name, "type": "derived", "poly": room, "area": round(room.area, 1),
                                 "area_source": "measured inside walls at %.1f m cut height" % cut,
                                 "named_by": ("fixture in model: %s" % why) if name else None, "ifc": [],
                                 "fixtures": len(hits)})
        # stable ids: sort by position (west to east, south to north)
        st_rooms.sort(key=lambda r: (round(r["poly"].centroid.x, 0), round(r["poly"].centroid.y, 0)))
        counts = {}
        for i, r in enumerate(st_rooms):
            r["id"] = "%s-r%02d" % (sid, i + 1)
            if not r["name"]:
                r["name"] = "Room %d" % (i + 1)
            else:
                counts[r["name"]] = counts.get(r["name"], 0) + 1
            c = r["poly"].centroid
            r["unit"] = next((u["id"] for u in st_units if u["poly"].buffer(0.2).contains(c)), None)
            if r["type"] == "space" and not r["unit"]:  # e.g. "G01 POS" belongs to unit G01
                r["unit"] = next((u["id"] for u in st_units if re.search(r"\b%s\b" % re.escape(u["name"]), r["name"], re.I)), None)
            r["storey"] = st.Name
            r["z"] = z0
        out_storeys.append({"id": sid, "name": st.Name, "elevation": round(z0, 3), "walls": walls,
                            "doors": layers["door"], "windows": layers["window"], "other": layers["other"],
                            "outline": outline})
        units += st_units
        rooms += st_rooms
        log("storey %-28s z=%7.2f  units %2d  rooms %3d  (%s)" % (st.Name, z0, len(st_units), len(st_rooms),
            ", ".join("%s x%d" % kv for kv in sorted(counts.items())) or "no fixtures matched"))
    return {"schema": f.schema, "storeys": out_storeys, "units": units, "rooms": rooms}


def camera_spots(poly, n=8, clear=0.6):
    """Candidate pano camera spots: the point furthest from every wall first, then a grid, all at least
    `clear` m from the walls, ranked by clearance (the renderer drops any that land inside furniture)."""
    best = polylabel(poly, 0.05)
    cands = [best]
    minx, miny, maxx, maxy = poly.bounds
    for x in np.arange(minx + clear, maxx, 0.5):
        for y in np.arange(miny + clear, maxy, 0.5):
            p = Point(x, y)
            if poly.contains(p):
                cands.append(p)
    edge = poly.boundary
    cands = sorted({(round(p.x, 2), round(p.y, 2)) for p in cands if edge.distance(p) >= min(clear, edge.distance(best) * 0.9)},
                   key=lambda q: -edge.distance(Point(q)))
    return [list(q) for q in cands[:n]]


if __name__ == "__main__":  # self-check: a 4 x 3 box sliced at mid height is a 4 x 3 rectangle
    v = [0, 0, 0, 4, 0, 0, 4, 3, 0, 0, 3, 0, 0, 0, 2, 4, 0, 2, 4, 3, 2, 0, 3, 2]
    fc = [0, 1, 2, 0, 2, 3, 4, 6, 5, 4, 7, 6, 0, 4, 5, 0, 5, 1, 1, 5, 6, 1, 6, 2, 2, 6, 7, 2, 7, 3, 3, 7, 4, 3, 4, 0]
    ps = section_polys(v, fc, 1.0)
    assert len(ps) == 1 and abs(ps[0].area - 12) < 1e-6, ps
    assert abs(footprint(v, fc).area - 12) < 1e-6
    sq = Polygon([(0, 0), (6, 0), (6, 4), (0, 4)])
    assert abs(sq.boundary.distance(Point(camera_spots(sq)[0])) - 2.0) < 0.06, camera_spots(sq)
    print("extract self-check ok")
