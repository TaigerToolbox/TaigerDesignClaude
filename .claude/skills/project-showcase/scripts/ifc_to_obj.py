"""IFC -> OBJ + scene.json, ready for blender_render.py.

Run with normal Python (pip install ifcopenshell), not Blender's Python:
    python ifc_to_obj.py model.ifc out_dir [--classes IfcWall,IfcSlab,...]

Keeps per-element identity: every OBJ object is named "IfcClass|GlobalId|Name" and every face keeps
its IFC surface style (or IfcMaterial) name, so finishes map by name and QA can trace any face back
to the model. Spaces and storeys are exported to scene.json (centroids, bounds) for cameras,
cutaways and hotspots; they are not drawn.
"""
import argparse, json, os, sys
import ifcopenshell, ifcopenshell.geom, ifcopenshell.util.element as uel

# Whitelist, not blacklist: services, footings, openings and annotation never sneak into a render.
KEEP = (
    "IfcWall IfcWallStandardCase IfcCurtainWall IfcSlab IfcRoof IfcCovering IfcWindow IfcDoor "
    "IfcColumn IfcBeam IfcMember IfcPlate IfcStair IfcStairFlight IfcRamp IfcRampFlight IfcRailing "
    "IfcChimney IfcBuildingElementProxy IfcFurniture IfcFurnishingElement IfcSite IfcGeographicElement "
    "IfcPavement IfcCourse IfcKerb IfcEarthworksFill IfcBearing IfcDeepFoundation"
).split()


def style_name(f, mat, element):
    """Readable name for a triangle's material: surface style name, else the element's IfcMaterial."""
    inst = getattr(mat, "instance", None)
    try:
        ent = f.by_id(inst.id()) if inst is not None else None
    except Exception:
        ent = None
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
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    f = ifcopenshell.open(a.ifc)
    keep = a.classes.split(",") if a.classes else KEEP
    schema = ifcopenshell.ifcopenshell_wrapper.schema_by_name(f.schema_identifier)
    known = {d.name() for d in schema.declarations()}
    elements = [e for c in keep if c in known for e in f.by_type(c, include_subtypes=False)]  # IFC2x3/4/4.3 differ
    elements = list({e.id(): e for e in elements}.values())

    s = ifcopenshell.geom.settings()
    s.set("use-world-coords", True)

    obj = open(os.path.join(a.out, "model.obj"), "w", encoding="utf-8")
    obj.write("# from %s\n" % os.path.basename(a.ifc))
    voff, skipped, written, mats = 1, [], 0, set()
    for e in elements:
        try:
            g = ifcopenshell.geom.create_shape(s, e).geometry
        except Exception as ex:  # elements with no body geometry (e.g. an IfcSite without terrain)
            skipped.append("%s %s: %s" % (e.is_a(), e.GlobalId, str(ex)[:60]))
            continue
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
        if b:
            spaces.append({"id": sp.GlobalId, "name": sp.LongName or sp.Name or sp.GlobalId, "bounds": b,
                           "centroid": [(b[0] + b[3]) / 2, (b[1] + b[4]) / 2, b[2]]})

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
        "storeys": sorted([{"name": st.Name, "elevation": float(st.Elevation or 0)} for st in f.by_type("IfcBuildingStorey")], key=lambda x: x["elevation"]),
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
