"""IFC -> OBJ + scene.json, ready for blender_render.py.

Run with normal Python (pip install ifcopenshell), not Blender's Python:
    python ifc_to_obj.py model.ifc out_dir [--classes IfcWall,IfcSlab,...]

Keeps per-element identity: every OBJ object is named "IfcClass|GlobalId|Name" and every face keeps
its IFC surface style (or IfcMaterial) name, so finishes map by name and QA can trace any face back
to the model. Spaces and storeys are exported to scene.json (centroids, bounds) for cameras,
cutaways and hotspots; they are not drawn.
"""
import argparse, json, os, re, sys
import ifcopenshell, ifcopenshell.geom, ifcopenshell.util.unit, ifcopenshell.util.element as uel

# Whitelist, not blacklist: services, footings, openings and annotation never sneak into a render.
KEEP = (
    "IfcWall IfcWallStandardCase IfcCurtainWall IfcSlab IfcRoof IfcCovering IfcWindow IfcDoor "
    "IfcColumn IfcBeam IfcMember IfcPlate IfcStair IfcStairFlight IfcRamp IfcRampFlight IfcRailing "
    "IfcChimney IfcBuildingElementProxy IfcFurniture IfcFurnishingElement IfcSite IfcGeographicElement "
    "IfcPavement IfcCourse IfcKerb IfcEarthworksFill IfcBearing IfcDeepFoundation"
).split()


def style_name(f, mat, element):
    """Readable name for a triangle's material: surface style name, else the element's IfcMaterial."""
    # mat.name looks like "IfcSurfaceStyleRendering-176". Resolve the id from it: touching mat.instance
    # crashes the native library on some Revit exports.
    ent, raw = None, getattr(mat, "name", "") or ""
    mm = re.match(r"^Ifc\w+-(\d+)$", raw)
    if mm:
        try:
            ent = f.by_id(int(mm.group(1)))
        except Exception:
            ent = None
    elif raw:
        return raw
    if ent is not None:
        if ent.is_a("IfcSurfaceStyle") and ent.Name:
            return ent.Name
        for inv in f.get_inverse(ent):
            if inv.is_a("IfcSurfaceStyle") and inv.Name:
                return inv.Name
        if ent.is_a("IfcMaterial") and ent.Name:
            return ent.Name
    m = uel.get_material(element)
    if m is not None and getattr(m, "Name", None):
        return m.Name
    return "unassigned"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ifc")
    ap.add_argument("out")
    ap.add_argument("--classes", help="comma list to replace the default whitelist")
    ap.add_argument("--storey", help="only elements contained in this storey (exact name)")
    ap.add_argument("--around", help="regex on element name/type: keep only elements within --margin of the matches")
    ap.add_argument("--margin", type=float, default=6.0, help="metres around --around matches (default 6)")
    ap.add_argument("--target", action="append", default=[],
                    help="NAME=REGEX, repeatable: a room for cameras/hotspots built from matching elements "
                         "(for models exported without IfcSpace, common from Revit)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    f = ifcopenshell.open(a.ifc)
    unit = ifcopenshell.util.unit.calculate_unit_scale(f)  # storey elevations are in file units (often mm); geometry comes out in metres
    keep = a.classes.split(",") if a.classes else KEEP
    schema = ifcopenshell.ifcopenshell_wrapper.schema_by_name(f.schema_identifier)
    known = {d.name() for d in schema.declarations()}
    elements = [e for c in keep if c in known for e in f.by_type(c, include_subtypes=False)]  # IFC2x3/4/4.3 differ
    elements = list({e.id(): e for e in elements}.values())
    if a.storey:  # comma list; an interior usually needs its own storey plus the one above (that slab is the ceiling)
        on = set()
        for name in a.storey.split(","):
            st = [x for x in f.by_type("IfcBuildingStorey") if x.Name == name.strip()]
            assert st, "storey %r not found; have %s" % (name, [x.Name for x in f.by_type("IfcBuildingStorey")])
            on |= {e.id() for e in uel.get_decomposition(st[0])}
        elements = [e for e in elements if e.id() in on]

    s = ifcopenshell.geom.settings()
    s.set("use-world-coords", True)

    label = lambda e: " ".join(x for x in (e.Name, getattr(e, "ObjectType", None)) if x)
    skipped, shapes = [], {}
    for e in elements:
        try:
            shapes[e.id()] = ifcopenshell.geom.create_shape(s, e)  # keep the shape: a bare .geometry dangles once it's freed (segfault)
        except Exception as ex:  # elements with no body geometry (e.g. an IfcSite without terrain)
            skipped.append("%s %s: %s" % (e.is_a(), e.GlobalId, str(ex)[:60]))
    elements = [e for e in elements if e.id() in shapes]

    def bb(shape):
        v = shape.geometry.verts
        return [min(v[0::3]), min(v[1::3]), min(v[2::3]), max(v[0::3]), max(v[1::3]), max(v[2::3])]

    def union(bs):
        return [min(b[0] for b in bs), min(b[1] for b in bs), min(b[2] for b in bs),
                max(b[3] for b in bs), max(b[4] for b in bs), max(b[5] for b in bs)]

    box = None
    if a.around:
        rx = re.compile(a.around, re.I)
        hits = [bb(shapes[e.id()]) for e in elements if rx.search(label(e))]
        assert hits, "--around %r matched nothing" % a.around
        u, m = union(hits), a.margin
        box = [u[0] - m, u[1] - m, u[2] - 1, u[3] + m, u[4] + m, u[5] + 1.2]  # slab below to slab above
        inside = lambda b: b[0] <= box[3] and b[3] >= box[0] and b[1] <= box[4] and b[4] >= box[1] and b[2] <= box[5] and b[5] >= box[2]
        elements = [e for e in elements if inside(bb(shapes[e.id()]))]
        print("around %r: %d matches, keeping %d elements" % (a.around, len(hits), len(elements)))

    obj = open(os.path.join(a.out, "model.obj"), "w", encoding="utf-8")
    obj.write("# from %s\n" % os.path.basename(a.ifc))
    voff, written, mats = 1, 0, set()
    for e in elements:
        g = shapes[e.id()].geometry
        v, fc, mid = g.verts, g.faces, g.material_ids
        if not fc:
            continue
        name = "%s|%s|%s" % (e.is_a(), e.GlobalId, (e.Name or "").replace(" ", "_"))
        obj.write("o %s\n" % name)
        for i in range(0, len(v), 3):
            obj.write("v %.5f %.5f %.5f\n" % (v[i], v[i + 1], v[i + 2]))
        names = [style_name(f, m, e) for m in g.materials] or ["unassigned"]
        cur = None
        for t in range(len(fc) // 3):
            m = names[mid[t]] if t < len(mid) and 0 <= mid[t] < len(names) else names[0]
            if m != cur:
                obj.write("usemtl %s\n" % m)
                cur = m
                mats.add(m)
            obj.write("f %d %d %d\n" % (fc[3 * t] + voff, fc[3 * t + 1] + voff, fc[3 * t + 2] + voff))
        voff += len(v) // 3
        written += 1
    obj.close()

    def bounds(e):
        try:
            v = ifcopenshell.geom.create_shape(s, e).geometry.verts
        except Exception:
            return None
        xs, ys, zs = v[0::3], v[1::3], v[2::3]
        return [min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)]

    spaces = []
    for sp in f.by_type("IfcSpace"):
        b = bounds(sp)
        if b and (box is None or (b[0] <= box[3] and b[3] >= box[0] and b[1] <= box[4] and b[4] >= box[1])):
            spaces.append({"id": sp.GlobalId, "name": sp.LongName or sp.Name or sp.GlobalId, "bounds": b,
                           "centroid": [(b[0] + b[3]) / 2, (b[1] + b[4]) / 2, b[2]]})
    for t in a.target:
        name, rx = t.split("=", 1)
        hits = [bb(shapes[e.id()]) for e in elements if re.search(rx, label(e), re.I)]
        if not hits:
            print("WARNING target %r matched nothing" % name)
            continue
        b = union(hits)
        spaces.append({"id": "target:" + name, "name": name, "bounds": b, "centroid": [(b[0] + b[3]) / 2, (b[1] + b[4]) / 2, b[2]]})

    north = None
    for c in f.by_type("IfcGeometricRepresentationContext"):
        if getattr(c, "TrueNorth", None):
            north = list(c.TrueNorth.DirectionRatios)[:2]
            break

    def dms(x):
        return None if not x else x[0] + x[1] / 60 + x[2] / 3600 + (x[3] / 3.6e9 if len(x) > 3 else 0)

    site = f.by_type("IfcSite")
    scene = {
        "source": os.path.basename(a.ifc),
        "schema": f.schema,
        "materials": sorted(mats),
        "storeys": sorted([{"name": st.Name, "elevation": float(st.Elevation or 0) * unit} for st in f.by_type("IfcBuildingStorey")], key=lambda x: x["elevation"]),
        "bounds": box,
        "spaces": spaces,
        "trueNorth": north,
        "latLon": [dms(site[0].RefLatitude), dms(site[0].RefLongitude)] if site and site[0].RefLatitude else None,
        "skipped": skipped,
    }
    json.dump(scene, open(os.path.join(a.out, "scene.json"), "w"), indent=1)
    print("wrote %d elements, %d materials, %d spaces; skipped %d" % (written, len(mats), len(spaces), len(skipped)))
    print("materials:", ", ".join(sorted(mats)))
    assert written > 0, "no geometry exported: check --classes"


if __name__ == "__main__":
    sys.exit(main())
