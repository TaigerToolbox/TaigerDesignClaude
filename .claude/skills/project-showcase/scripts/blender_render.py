"""Render showcase sequences from the real model, straight into the site template.

    blender -b --factory-startup -P blender_render.py -- shots.json

shots.json (paths relative to that file):
{
  "model": "work/model.obj",          # from ifc_to_obj.py
  "scene": "work/scene.json",         # from ifc_to_obj.py
  "finishes": "finishes.csv",         # ifc_material,color,roughness,metallic,transmission,hide
  "site": "site",                     # the template folder; frames land in site/frames/
  "location": {"lat": -27.47, "lon": 153.02, "utc": "2026-06-21T05:00"},   # 3 pm AEST winter
  "engine": "EEVEE",                  # EEVEE for drafts, CYCLES for finals (needs a GPU box)
  "samples": 64, "scale": 0.5,        # scale 1.0 = 1920x1080 desktop / 1080x1920 mobile
  "ground": "#6f7a5a",
  "shots": [
    {"name": "hero", "kind": "orbit", "frames": 120, "az": [200, 250], "el": 18},
    {"name": "inside", "kind": "cutaway", "frames": 120, "target": "living room", "hide": ["roof"]},
    {"name": "living", "kind": "room", "frames": 90, "target": "living room", "corner": 2},
    {"name": "picker", "kind": "still", "az": 215, "el": 50, "hide": ["roof"]},
    {"name": "qa_plan", "kind": "plan", "hide": ["roof"]}
  ]
}
Every move is eased (smoothstep), cameras never exceed 90 deg horizontal FOV indoors, and eye-level
shots keep the camera level (verticals stay vertical). Fails loudly on unmapped materials.
"""
import bpy, bmesh, csv, json, math, os, re, subprocess, sys, shutil, datetime
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

cfg_path = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
ROOT = os.path.dirname(cfg_path)
C = json.load(open(cfg_path))
P = lambda p: os.path.join(ROOT, p)
FFMPEG = shutil.which("ffmpeg") or C.get("ffmpeg", "ffmpeg")
ease = lambda t: t * t * (3 - 2 * t)
lerp = lambda a, b, t: a + (b - a) * t


def hex_rgba(h):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]  # colours in Blender are linear
    return (*lin, 1.0)


# ---------- scene setup
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.wm.obj_import(filepath=P(C["model"]), forward_axis="Y", up_axis="Z")
model = [o for o in sc.objects if o.type == "MESH"]
meta = json.load(open(P(C["scene"])))

# Finishes: every IFC material must be mapped. A missing row is an error, not a grey default.
base_name = lambda n: re.sub(r"\.\d{3}$", "", n)  # strip only Blender's .001 suffix; ".EARTH" is a real name
rows = {r["ifc_material"].strip(): r for r in csv.DictReader(open(P(C["finishes"]), encoding="utf-8-sig"))}
used = {base_name(s.material.name) for o in model for s in o.material_slots if s.material}
missing = sorted(used - set(rows))
if missing and not C.get("allow_unmapped"):
    sys.exit("UNMAPPED MATERIALS (add them to %s): %s" % (C["finishes"], ", ".join(missing)))
hidden_mats = set()
_img_cache = {}


def load_img(path, color=True):
    key = (path, color)
    if key not in _img_cache:
        img = bpy.data.images.load(path, check_existing=True)
        img.colorspace_settings.name = "sRGB" if color else "Non-Color"
        _img_cache[key] = img
    return _img_cache[key]


def pixels(img):
    import numpy as np
    px = np.empty(len(img.pixels), dtype=np.float32); img.pixels.foreach_get(px)
    return px.reshape(-1, 4)[:, :3]


def mean_rgb(img):
    import numpy as np
    px = pixels(img)
    if not img.is_float:  # measured: 8-bit images come back as raw sRGB values, not linear
        px = np.where(px <= 0.04045, px / 12.92, ((px + 0.055) / 1.055) ** 2.4)
    return px.mean(axis=0)


def sibling(path, kind, explicit=""):
    """The roughness/height map next to a diffuse scan. Poly Haven: _diff/_rough/_disp, older Poly Haven:
    Diffuse/Rough, ambientCG: _Color/_Roughness/_Displacement. Only the file name is rewritten."""
    if explicit:
        return P(explicit)
    d, f = os.path.split(path)
    pairs = {"rough": (("_Color", "_Roughness"), ("Diffuse", "Rough"), ("_diff", "_rough")),
             "height": (("_Color", "_Displacement"), ("Diffuse", "Displacement"), ("_diff", "_disp"))}[kind]
    for a, b in pairs:
        if a in f and os.path.exists(os.path.join(d, f.replace(a, b))):
            return os.path.join(d, f.replace(a, b))
    return None


def world_coords(nt, tile, rotate_deg=0.0):
    """IFC has no UVs: project textures from world position (metres), so a 1.2 m board stays 1.2 m.
    rotate_deg turns the pattern in plan, e.g. floorboards running north-south."""
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / tile, 1 / tile, 1 / tile)
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(rotate_deg))
    nt.links.new(geo.outputs["Position"], mp.inputs["Vector"])
    return mp.outputs["Vector"]


def textured(m, b, r):
    """Grain from a texture photo, colour from the approved sample: tex * (sample / mean(tex))."""
    import numpy as np
    nt = m.node_tree
    L = nt.links.new
    vec = world_coords(nt, float(r.get("tile_m") or 1.0), float(r.get("rotate_deg") or 0))
    diff_path = P(r["texture"])

    def img_node(path, color=True):
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = load_img(path, color)
        t.projection, t.projection_blend = "BOX", 0.15
        L(vec, t.inputs["Vector"])
        return t

    tex = img_node(diff_path)
    target = hex_rgba(r["color"])[:3]
    mean = mean_rgb(tex.image)
    tint = nt.nodes.new("ShaderNodeVectorMath"); tint.operation = "MULTIPLY"
    keep = (r.get("recolor") or "1").strip().lower() in ("0", "no", "false")  # a supplier slab photo is already the colour
    tint.inputs[1].default_value = (1, 1, 1) if keep else tuple(t / max(mu, 1e-4) for t, mu in zip(target, mean))
    L(tex.outputs["Color"], tint.inputs[0])
    cap = nt.nodes.new("ShaderNodeVectorMath"); cap.operation = "MINIMUM"  # albedo over ~0.85 adds energy and fireflies
    cap.inputs[1].default_value = (0.85, 0.85, 0.85)
    L(tint.outputs["Vector"], cap.inputs[0]); L(cap.outputs["Vector"], b.inputs["Base Color"])
    rough = float(r.get("roughness") or 0.5)
    rp = sibling(diff_path, "rough", (r.get("roughness_map") or "").strip())
    if rp:  # keep the map's variation, centred on the CSV value: its 5th..95th percentile maps to rough +/- 0.1
        t2 = img_node(rp, color=False)
        v = pixels(t2.image)[:, 0]
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = float(np.percentile(v, 5)), float(np.percentile(v, 95)) + 1e-3
        mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = max(0.02, rough - 0.1), min(1.0, rough + 0.1)
        L(t2.outputs["Color"], mr.inputs["Value"]); L(mr.outputs["Result"], b.inputs["Roughness"])
    # Tangent-space normal maps need UVs, which IFC geometry doesn't have. Bump from the height map
    # (or the diffuse's own luminance) works in world space.
    hp = sibling(diff_path, "height", (r.get("bump_map") or "").strip())
    src = img_node(hp, color=False) if hp else tex
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.4 * float(r.get("normal_strength") or 0.5)
    bump.inputs["Distance"].default_value = 0.002
    L(src.outputs["Color"], bump.inputs["Height"]); L(bump.outputs["Normal"], b.inputs["Normal"])


def marble(m, b, r):
    """Procedural veined stone for slabs with no CC0 scan. color = base, vein = vein colour, tile_m = vein spacing."""
    # Marble veins are long, meandering and mostly parallel (a closed Voronoi network reads as crazy
    # paving): ridges of a heavily distorted wave, a finer set at another angle only in patches, the vein
    # colour broken up, and a low-frequency cloud for the tonal drift every slab has.
    nt = m.node_tree
    L = nt.links.new
    vec = world_coords(nt, float(r.get("tile_m") or 0.6), float(r.get("rotate_deg") or 0))
    base = hex_rgba(r["color"]); vein = hex_rgba(r.get("vein") or "#6b4a33")

    def node(kind, **inp):
        n = nt.nodes.new(kind)
        for k, v in inp.items():
            n.inputs[k].default_value = v
        return n

    def ridge(scale, direction, lo):
        w = node("ShaderNodeTexWave", Scale=scale, Distortion=10.0, Detail=8.0)
        w.wave_type, w.bands_direction = "BANDS", direction
        w.inputs["Detail Roughness"].default_value = 0.7
        L(vec, w.inputs["Vector"])
        mr = node("ShaderNodeMapRange", **{"From Min": lo, "From Max": 1.0})  # only the crest of each band
        L(w.outputs["Fac"], mr.inputs["Value"])
        pw = node("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 2.5
        L(mr.outputs["Result"], pw.inputs[0])
        return pw.outputs[0]

    big, fine = ridge(0.4, "DIAGONAL", 0.9), ridge(1.6, "Y", 0.95)
    patch = node("ShaderNodeTexNoise", Scale=1.1, Detail=4.0); L(vec, patch.inputs["Vector"])
    pm = node("ShaderNodeMapRange", **{"From Min": 0.55, "From Max": 0.65}); L(patch.outputs["Fac"], pm.inputs["Value"])
    fw = node("ShaderNodeMath"); fw.operation = "MULTIPLY"; L(fine, fw.inputs[0]); L(pm.outputs["Result"], fw.inputs[1])
    both = node("ShaderNodeMath"); both.operation = "MAXIMUM"; both.use_clamp = True
    L(big, both.inputs[0]); L(fw.outputs[0], both.inputs[1])
    cloud = node("ShaderNodeTexNoise", Scale=0.6, Detail=3.0); L(vec, cloud.inputs["Vector"])
    tone = node("ShaderNodeMix"); tone.data_type = "RGBA"
    tone.inputs["A"].default_value = base
    tone.inputs["B"].default_value = tuple(c * 0.88 for c in base[:3]) + (1,)
    L(cloud.outputs["Fac"], tone.inputs["Factor"])
    vtone = node("ShaderNodeMix"); vtone.data_type = "RGBA"  # veins fade in and out along their length
    vtone.inputs["A"].default_value = vein
    vtone.inputs["B"].default_value = tuple(lerp(v, c, 0.6) for v, c in zip(vein[:3], base[:3])) + (1,)
    L(patch.outputs["Fac"], vtone.inputs["Factor"])
    out = node("ShaderNodeMix"); out.data_type = "RGBA"
    L(both.outputs[0], out.inputs["Factor"]); L(tone.outputs["Result"], out.inputs["A"]); L(vtone.outputs["Result"], out.inputs["B"])
    L(out.outputs["Result"], b.inputs["Base Color"])
    rough = float(r.get("roughness") or 0.35)  # honed stone isn't uniformly matte
    rr = node("ShaderNodeMapRange", **{"To Min": max(0.05, rough - 0.07), "To Max": rough + 0.07})
    L(cloud.outputs["Fac"], rr.inputs["Value"]); L(rr.outputs["Result"], b.inputs["Roughness"])


for m in bpy.data.materials:
    r = rows.get(base_name(m.name))
    if not r:
        continue
    if r.get("hide", "").strip() in ("1", "yes", "true"):
        hidden_mats.add(m.name)
        continue
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = hex_rgba(r["color"])
    b.inputs["Roughness"].default_value = float(r.get("roughness") or 0.6)
    b.inputs["Metallic"].default_value = float(r.get("metallic") or 0)
    tr = float(r.get("transmission") or 0)
    if tr:
        b.inputs["Transmission Weight"].default_value = tr
        # Path tracers treat daylight through real glass as caustics and the room goes black.
        # Camera rays see proper glass; every other ray passes straight through.
        nt = m.node_tree
        lp = nt.nodes.new("ShaderNodeLightPath"); tp = nt.nodes.new("ShaderNodeBsdfTransparent")
        mx = nt.nodes.new("ShaderNodeMixShader"); out = nt.nodes.get("Material Output")
        nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs["Fac"])
        nt.links.new(tp.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs["Surface"])
    if (r.get("procedural") or "").strip() == "marble":
        marble(m, b, r)
    elif (r.get("texture") or "").strip():
        textured(m, b, r)
    if C.get("imperfection", True) and not tr and not b.inputs["Roughness"].is_linked:
        # A flawless surface reads as CG. Faint roughness drift (smudges, wear), never a colour change.
        nt = m.node_tree
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 6.0
        nt.links.new(world_coords(nt, 1.0), nz.inputs["Vector"])
        rv = float(r.get("roughness") or 0.6)
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = max(0.02, rv - 0.06), min(1.0, rv + 0.06)
        nt.links.new(nz.outputs["Fac"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])

glass_objs = []
for o in model:
    slot_mats = [s.material.name if s.material else "" for s in o.material_slots]
    bm = bmesh.new(); bm.from_mesh(o.data)
    # markers and virtual elements: drop their faces, so a mixed object keeps only what's real
    gone = [f for f in bm.faces if f.material_index < len(slot_mats) and slot_mats[f.material_index] in hidden_mats]
    if gone:
        bmesh.ops.delete(bm, geom=gone, context="FACES")
    # IFC edges are razor sharp, the biggest CG tell. Weld, then a small bevel catches light like real arrises.
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    bm.to_mesh(o.data); bm.free()
    if not o.data.polygons:
        o.hide_render = o.hide_viewport = True
        continue
    if any(float((rows.get(base_name(n)) or {}).get("transmission") or 0) > 0 for n in slot_mats):
        glass_objs.append(o)
    dims = sorted(o.dimensions)
    if dims[0] > 0.03:  # a 3 mm bevel would eat blind slats, glass and thin trims
        bv = o.modifiers.new("arris", "BEVEL")
        bv.width, bv.segments, bv.limit_method, bv.angle_limit = 0.003, 2, "ANGLE", math.radians(30)
        bv.harden_normals = True
    o.data.shade_smooth()
    try:
        o.data.set_sharp_from_angle(angle=math.radians(30))  # smooth curves, crisp corners
    except AttributeError:
        pass

visible = [o for o in model if not o.hide_render]
pts = [o.matrix_world @ Vector(c) for o in visible for c in o.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center, radius = (lo + hi) / 2, (hi - lo).length / 2


def place_props():
    """Approved styling in its own 'furniture' collection: real-scale CC0 or manufacturer models.
    Each prop: {"asset": "x.gltf", "on": "<object name regex>", "uv": [0.3, 0.6]} sits it on the top of the
    matching objects at that fraction of their plan extent; or "pos": [x, y, z]. Optional "yaw" (deg),
    "scale", "height" (m: rescale to it). Real heights are printed for the QA record."""
    if not C.get("props"):
        return
    col = bpy.data.collections.new("furniture"); sc.collection.children.link(col)
    for i, p in enumerate(C["props"]):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=P(p["asset"]))
        new = [o for o in bpy.data.objects if o not in before]
        assert new, "prop %s imported nothing" % p["asset"]
        for o in new:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            col.objects.link(o)
        bpy.context.view_layer.update()
        pts_ = [o.matrix_world @ Vector(c) for o in new if o.type == "MESH" for c in o.bound_box]
        plo = Vector((min(q.x for q in pts_), min(q.y for q in pts_), min(q.z for q in pts_)))
        phi = Vector((max(q.x for q in pts_), max(q.y for q in pts_), max(q.z for q in pts_)))
        foot = Vector(((plo.x + phi.x) / 2, (plo.y + phi.y) / 2, plo.z))
        piv = bpy.data.objects.new("prop|%d|%s" % (i, os.path.splitext(os.path.basename(p["asset"]))[0]), None)
        col.objects.link(piv)
        for o in new:
            if o.parent not in new:
                o.location -= foot; o.parent = piv
        s = p.get("scale", 1.0)
        if p.get("height"):
            s = p["height"] / max(phi.z - plo.z, 1e-4)
        if p.get("pos"):
            at = Vector(p["pos"])
        else:
            rx = re.compile(p["on"], re.I)
            hosts = [o for o in model if rx.search(o.name) and not o.hide_render]
            assert hosts, "prop %s: 'on' %r matched no object" % (p["asset"], p["on"])
            vs = [o.matrix_world @ v.co for o in hosts for v in o.data.vertices]
            x0, x1 = min(v.x for v in vs), max(v.x for v in vs)
            y0, y1 = min(v.y for v in vs), max(v.y for v in vs)
            u, v_ = p.get("uv", [0.5, 0.5])
            # "z": the benchtop height when the host also holds taller parts (a rangehood, a shelf)
            at = Vector((lerp(x0, x1, u), lerp(y0, y1, v_), p.get("z", max(v.z for v in vs)) + 0.0005))
        piv.location, piv.scale = at, (s, s, s)
        piv.rotation_euler = (0, 0, math.radians(p.get("yaw", 0)))
        print("prop %s: %.2f m tall at (%.2f, %.2f, %.2f)" % (piv.name, (phi.z - plo.z) * s, at.x, at.y, at.z))


place_props()

# Ground
bpy.ops.mesh.primitive_plane_add(size=max(400, radius * 40), location=(center.x, center.y, lo.z - 0.01))
gm =bpy.data.materials.new("ground"); gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = hex_rgba(C.get("ground", "#6f7a5a"))
gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
bpy.context.active_object.data.materials.append(gm)


# ---------- sun from real location and time (NOAA approximation), rotated to the model's true north
def sun_vector(lat, lon, utc):
    dt = datetime.datetime.fromisoformat(utc)
    hour = dt.hour + dt.minute / 60
    gam = 2 * math.pi / 365 * (dt.timetuple().tm_yday - 1 + (hour - 12) / 24)
    decl = (0.006918 - 0.399912 * math.cos(gam) + 0.070257 * math.sin(gam) - 0.006758 * math.cos(2 * gam)
            + 0.000907 * math.sin(2 * gam) - 0.002697 * math.cos(3 * gam) + 0.00148 * math.sin(3 * gam))
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(gam) - 0.032077 * math.sin(gam)
                    - 0.014615 * math.cos(2 * gam) - 0.040849 * math.sin(2 * gam))
    ha = math.radians((hour * 60 + eqt + 4 * lon) / 4 - 180)
    la = math.radians(lat)
    el = math.asin(math.sin(la) * math.sin(decl) + math.cos(la) * math.cos(decl) * math.cos(ha))
    az = math.atan2(math.sin(ha), math.cos(ha) * math.sin(la) - math.tan(decl) * math.cos(la)) + math.pi
    nx, ny = meta.get("trueNorth") or (0.0, 1.0)
    n = math.hypot(nx, ny); nx, ny = nx / n, ny / n
    dx, dy = nx * math.cos(az) + ny * math.sin(az), -nx * math.sin(az) + ny * math.cos(az)
    return Vector((dx * math.cos(el), dy * math.cos(el), math.sin(el))), math.degrees(el), math.degrees(az)


loc = C["location"]
to_sun, sun_el, sun_az = sun_vector(loc["lat"], loc["lon"], loc["utc"])
assert sun_el > 0, "sun is below the horizon at %s, pick a daytime UTC" % loc["utc"]
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
sun.data.energy, sun.data.angle = C.get("sun_strength", 4.0), math.radians(0.53)  # ~1.5 for soft interiors
print("sun: elevation %.1f, azimuth %.1f (rotate an HDRI so its sun agrees, or it casts a second shadow)" % (sun_el, sun_az))
sun.rotation_euler = to_sun.to_track_quat("Z", "Y").to_euler()
sc.collection.objects.link(sun)

world = bpy.data.worlds.new("sky"); sc.world = world; world.use_nodes = True
wn = world.node_tree.nodes
if C.get("hdri"):
    # A photographed sky lights interiors far better than a procedural one. Rotate it so its sun roughly
    # agrees with the computed sun; record that it is a stand-in, not the site's real view.
    env = wn.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(P(C["hdri"]))
    mp = wn.new("ShaderNodeMapping"); tc = wn.new("ShaderNodeTexCoord")
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(C.get("hdri_rotation", 0)))
    world.node_tree.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    world.node_tree.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    world.node_tree.links.new(env.outputs["Color"], wn["Background"].inputs[0])
    wn["Background"].inputs[1].default_value = C.get("hdri_strength", 1.0)
else:
  try:
    sky = wn.new("ShaderNodeTexSky")
    for t in ("MULTIPLE_SCATTERING", "SINGLE_SCATTERING", "NISHITA"):  # names differ across Blender versions
        try:
            sky.sky_type = t; break
        except TypeError:
            pass
    sky.sun_disc = False
    sky.sun_elevation, sky.sun_rotation = math.radians(sun_el), math.radians(sun_az)
    world.node_tree.links.new(sky.outputs[0], wn["Background"].inputs[0])
    wn["Background"].inputs[1].default_value = 0.35
  except Exception as ex:
    print("sky texture unavailable, using flat sky:", ex)
    wn["Background"].inputs[0].default_value = (0.55, 0.65, 0.8, 1)

# ---------- colour and render settings
sc.view_settings.view_transform = "AgX"
sc.view_settings.exposure = C.get("exposure", 0.0)  # interiors with window lights: +1.5 to +2.5 (benchmarked)
if C.get("white_balance"):  # kelvin; ~5300 K keeps warm greige walls from reading grey under a blue sky
    try:
        sc.view_settings.use_white_balance = True
        sc.view_settings.white_balance_temperature = C["white_balance"]
    except AttributeError:
        print("white balance needs Blender 4.3+, skipped")
# Base contrast by default: interiors already starve the shadows, a punchier look crushes them to black.
for look in (C.get("look", "AgX - Base Contrast"), "AgX - Base Contrast", "Base Contrast", "None"):
    try:
        sc.view_settings.look = look; break
    except TypeError:
        pass
engine = C.get("engine", "EEVEE").upper()


def setall(obj, **kw):
    for k, v in kw.items():
        try:
            setattr(obj, k, v)
        except (AttributeError, TypeError) as ex:
            print("setting %s skipped: %s" % (k, ex))


if engine == "CYCLES":
    sc.render.engine = "CYCLES"
    cy = sc.cycles
    setall(cy, samples=C.get("samples", 384), use_adaptive_sampling=True, adaptive_threshold=C.get("noise_threshold", 0.03),
           adaptive_min_samples=32, use_denoising=True, denoiser="OPENIMAGEDENOISE",
           denoising_input_passes="RGB_ALBEDO_NORMAL", denoising_prefilter="ACCURATE",
           seed=0, use_animated_seed=False,  # fixed seed: no boiling noise between frames
           max_bounces=16, diffuse_bounces=6, glossy_bounces=3, transmission_bounces=4, transparent_max_bounces=16,
           caustics_reflective=False, caustics_refractive=False, blur_glossy=1.0,
           sample_clamp_indirect=C.get("clamp_indirect", 5.0), use_light_tree=True)
    sc.render.use_persistent_data = True  # sequences: don't rebuild the scene every frame
    if C.get("device", "CPU").upper() == "GPU":  # finals on a rented RTX box: same command, ~10x faster
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for backend in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
            try:
                prefs.compute_device_type = backend
                prefs.get_devices()
                if any(d.type == backend for d in prefs.devices):
                    break
            except TypeError:
                continue
        for d in prefs.devices:
            d.use = d.type != "CPU"
        assert any(d.use for d in prefs.devices), "device GPU requested but no GPU found"
        cy.device = "GPU"
        print("GPU render:", prefs.compute_device_type, [d.name for d in prefs.devices if d.use])
else:
    for e in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            sc.render.engine = e; break
        except TypeError:
            pass
    for attr, v in (("taa_render_samples", C.get("samples", 64)), ("use_raytracing", True), ("use_shadows", True)):
        try:
            setattr(sc.eevee, attr, v)  # ray-traced GI and contact shadows lift drafts off the flat-shaded look
        except AttributeError:
            pass
sc.render.image_settings.file_format = "PNG"


def apply_post():
    """One saved grade for every frame, so sequences stay flicker-free: soft bloom on highlights and a
    faint vignette. "post": {"glare": 0.15, "vignette": 0.15} or false. Never sky replacement or retouching."""
    pc = C.get("post", {})
    if pc is False:
        return
    try:
        t = bpy.data.node_groups.new("post", "CompositorNodeTree")
        t.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        N, L = t.nodes.new, t.links.new
        rl = N("CompositorNodeRLayers")
        gl = N("CompositorNodeGlare")
        for k, v in (("Type", "Bloom"), ("Threshold", 1.0), ("Strength", pc.get("glare", 0.15))):
            try:
                gl.inputs[k].default_value = v
            except (KeyError, TypeError):
                pass
        L(rl.outputs["Image"], gl.inputs["Image"])
        em = N("CompositorNodeEllipseMask")
        em.inputs["Size"].default_value = (0.95, 0.95)
        bl = N("CompositorNodeBlur"); bl.inputs["Size"].default_value = (300, 300)
        L(em.outputs["Mask"], bl.inputs["Image"])
        vg = N("ShaderNodeMix"); vg.data_type = "RGBA"; vg.blend_type = "MULTIPLY"
        vg.inputs["Factor"].default_value = pc.get("vignette", 0.15)
        inv = N("ShaderNodeMix"); inv.data_type = "RGBA"  # mask 1 in the centre -> white, edges -> dark
        inv.inputs["A"].default_value = (0.0, 0.0, 0.0, 1); inv.inputs["B"].default_value = (1, 1, 1, 1)
        L(bl.outputs["Image"], inv.inputs["Factor"])
        L(gl.outputs["Image"], vg.inputs["A"]); L(inv.outputs["Result"], vg.inputs["B"])
        out = N("NodeGroupOutput"); L(vg.outputs["Result"], out.inputs[0])
        sc.compositing_node_group = t
        sc.render.use_compositing = True
    except Exception as ex:
        print("post grade skipped (compositor API differs in this Blender):", ex)


apply_post()
sc.render.film_transparent = False

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam); sc.camera = cam


def space(name):
    """By id, by name, or "name@storey" (every unit has a "Bedroom")."""
    want = str(name).lower()
    hits = [s for s in meta["spaces"] if want in (str(s.get("id", "")).lower(), s["name"].lower(),
                                                  ("%s@%s" % (s["name"], s.get("storey"))).lower())]
    if len(hits) > 1:
        sys.exit("target '%s' is ambiguous (%d spaces): use its id or name@storey" % (name, len(hits)))
    if hits:
        return hits[0]
    sys.exit("target space '%s' not in scene.json (have: %s)" % (name, [s["name"] for s in meta["spaces"]]))


def kelvin_rgb(k):
    """Blackbody colour, Tanner Helland's fit; good enough for light tints."""
    t = k / 100
    r = 1.0 if t <= 66 else min(1, 1.2930 * (t - 60) ** -0.1332)
    g = min(1, 0.3901 * math.log(t) - 0.6318) if t <= 66 else min(1, 1.1299 * (t - 60) ** -0.0755)
    b = 1.0 if t >= 66 else (0.0 if t <= 19 else min(1, 0.5432 * math.log(t - 10) - 1.1962))
    return (r, g, b)


def area_light(name, size, loc, facing, watts, kelvin, camera_visible=False, portal=False):
    """Rectangular area light at loc pointing along `facing`."""
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape, ld.size, ld.size_y = "RECTANGLE", max(size[0], 0.05), max(size[1], 0.05)
    ld.energy, ld.color = watts, kelvin_rgb(kelvin)
    if portal:
        try:
            ld.cycles.is_portal = True
        except AttributeError:
            print("portals unavailable in this Blender")
    ob = bpy.data.objects.new(name, ld); sc.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (-facing).to_track_quat("Z", "Y").to_euler()  # a light shines along its -Z
    ob.visible_camera = camera_visible
    return ob


def window_lights(campos, camdir, shot):
    """Interiors lit through glass on a CPU budget: a portal (guides sky samples, 3 to 5x less noise)
    and a soft fill at every glazed opening near the camera, plus a fill behind the camera the way a
    photographer bounces light. Fills are invisible to the camera but show in reflections."""
    made = []
    wl = {**C.get("window_lights", {}), **shot.get("window_lights", {})}
    for o in glass_objs:
        if o.hide_render:
            continue
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        lo_ = Vector((min(p.x for p in bb), min(p.y for p in bb), min(p.z for p in bb)))
        hi_ = Vector((max(p.x for p in bb), max(p.y for p in bb), max(p.z for p in bb)))
        mid, ext = (lo_ + hi_) / 2, hi_ - lo_
        if (mid - campos).length > wl.get("radius", 9) or ext.z < 0.3:
            continue
        thin = min(range(2), key=lambda i: ext[i])  # vertical glazing: the thin plan axis is the normal
        n = Vector((0, 0, 0)); n[thin] = 1.0
        if n.dot(mid - campos) < 0:
            n = -n  # n now points from the room out through the glass
        size = (ext[1 - thin], ext.z)
        at = mid + n * (ext[thin] / 2 + 0.05)
        made.append(area_light("portal|" + o.name[:40], size, at, -n, 1.0, 6500, portal=True))
        made.append(area_light("winfill|" + o.name[:40], size, mid + n * (ext[thin] / 2 + 0.06), -n,
                               wl.get("w_per_m2", 100) * size[0] * size[1], wl.get("kelvin", 5500)))
    f = wl.get("camera_fill", {"watts": 40, "kelvin": 4500, "size": 2.0})
    if f:
        # tilted up so it bounces off the ceiling: a level fill paints a hot patch on the floor in front of the lens
        up = (camdir + Vector((0, 0, 0.8))).normalized()
        made.append(area_light("camfill", (f["size"], f["size"]), campos - camdir * 1.0 + Vector((0, 0, 0.6)),
                               up, f["watts"], f["kelvin"]))
    print("window lights: %d glazed openings, camera fill %s" % ((len(made) - (1 if f else 0)) // 2, "on" if f else "off"))
    return made


def sheers(shot, campos):
    """Drawn sheer curtains inside the glazing whose object name matches shot["sheers"] (regex, or true
    for all glazing within 9 m). Softens blown windows and adds the soft layer a styled room has. A styling
    choice like props: it needs approval and is captioned as indicative."""
    want = shot.get("sheers")
    if not want:
        return []
    rx = re.compile(".*" if want is True else want, re.I)
    mat = bpy.data.materials.get("sheer") or bpy.data.materials.new("sheer")
    if not mat.node_tree or "Translucent BSDF" not in mat.node_tree.nodes:
        mat.use_nodes = True
        nt = mat.node_tree; nt.nodes.clear()
        tl = nt.nodes.new("ShaderNodeBsdfTranslucent"); tl.inputs["Color"].default_value = hex_rgba(shot.get("sheer_color", "#f1ece2"))
        tp = nt.nodes.new("ShaderNodeBsdfTransparent")
        mx = nt.nodes.new("ShaderNodeMixShader"); mx.inputs["Fac"].default_value = 0.6  # 40% see-through
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(tp.outputs[0], mx.inputs[1]); nt.links.new(tl.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs["Surface"])
    made = []
    for o in glass_objs:
        if o.hide_render or not rx.search(o.name):
            continue
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        lo_ = Vector((min(p.x for p in bb), min(p.y for p in bb), min(p.z for p in bb)))
        hi_ = Vector((max(p.x for p in bb), max(p.y for p in bb), max(p.z for p in bb)))
        mid, ext = (lo_ + hi_) / 2, hi_ - lo_
        if not 2.0 < (mid - campos).length < 9 or ext.z < 0.8:  # not the window beside the camera: it would fill the frame edge
            continue
        thin = min(range(2), key=lambda i: ext[i]); side = 1 - thin
        n = Vector((0, 0, 0)); n[thin] = 1.0
        if n.dot(mid - campos) < 0:
            n = -n
        w, h, cols = ext[side] * 1.05, ext.z, max(8, int(ext[side] * 1.05 / 0.012))
        bm = bmesh.new()
        grid = []
        for i in range(cols + 1):
            u = i / cols
            fold = 0.035 * math.sin(2 * math.pi * u * w / 0.14) + 0.01 * math.sin(2 * math.pi * u * w / 0.37)  # 140 mm pleats
            col_ = []
            for z in (lo_.z, lo_.z + h):
                p = mid.copy(); p[side] = mid[side] - w / 2 + u * w; p.z = z
                col_.append(bm.verts.new(p - n * (ext[thin] / 2 + 0.12 + fold)))
            grid.append(col_)
        for i in range(cols):
            bm.faces.new((grid[i][0], grid[i + 1][0], grid[i + 1][1], grid[i][1]))
        me = bpy.data.meshes.new("sheer"); bm.to_mesh(me); bm.free()
        me.materials.append(mat); me.shade_smooth()
        ob = bpy.data.objects.new("sheer|" + o.name[:40], me); sc.collection.objects.link(ob)
        made.append(ob)
    print("sheers: %d windows" % len(made))
    return made


def check_camera_clear(shot):
    """Stop if the camera sits inside a solid: those inside faces render as flat black slabs at the frame
    edges. Rays through the frame start at clip_start; hitting a back face means we see inside a solid."""
    if shot.get("allow_inside"):
        return
    dg = bpy.context.evaluated_depsgraph_get()
    mw = cam.matrix_world
    frame = [Vector(v) for v in cam.data.view_frame(scene=sc)]
    pts_ = frame + [(frame[i] + frame[(i + 1) % 4]) / 2 for i in range(4)] + [sum(frame, Vector()) / 4]
    for q in pts_:
        d = (mw.to_3x3() @ q).normalized()
        o = mw.translation + d * cam.data.clip_start
        hit, loc_, nrm, _, ob, _ = sc.ray_cast(dg, o, d)
        if hit and nrm.dot(d) > 0 and ob and not ob.name.startswith(("portal|", "winfill|", "camfill", "sheer|")):
            sys.exit("CAMERA INSIDE '%s' in shot %s (camera at %s). Move it into the room, or set the shot's "
                     "clip_start past %.2f m to cut through that wall." % (ob.name, shot["name"], tuple(round(x, 2) for x in mw.translation),
                                                                         (loc_ - mw.translation).length + 0.05))


def look_at(pos, target):
    cam.location = pos
    cam.rotation_euler = (target - pos).to_track_quat("-Z", "Y").to_euler()


def fit_distance(rad, lens, aspect):
    """Distance at which a sphere of radius rad fills the frame. Sensor fit AUTO: the long side gets 36 mm."""
    wide = 2 * math.atan(18 / lens)
    narrow = 2 * math.atan(math.tan(wide / 2) / max(aspect, 1 / aspect))
    return rad / math.sin(narrow / 2) * 1.02


def orbit_pos(c, az, el, d):
    a, e = math.radians(az), math.radians(el)
    return c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * d


def keyframes(shot, aspect, n):
    """Yield (pos, target) per frame for this shot and aspect."""
    kind = shot["kind"]
    lens = shot.get("lens", 20 if kind == "room" else 35)
    cam.data.lens, cam.data.sensor_width, cam.data.shift_y = lens, 36, 0
    cam.data.sensor_fit = "AUTO"
    tgt = space(shot["target"]) if shot.get("target") else None
    cm = shot.get("camera")
    for f in range(n):
        t = ease(f / max(1, n - 1))
        if cm:  # explicit camera, e.g. matching a reference render; pos2/look2 make it a move
            pos = lerp(Vector(cm["pos"]), Vector(cm.get("pos2", cm["pos"])), t)
            look = lerp(Vector(cm["look"]), Vector(cm.get("look2", cm["look"])), t)
            if cm.get("level", True):
                look.z = pos.z  # keep verticals vertical; frame with shift instead of tilt
                cam.data.shift_y = cm.get("shift_y", 0)
            yield pos, look
        elif kind in ("orbit", "still"):
            az = shot.get("az", 215); az = lerp(az[0], az[1], t) if isinstance(az, list) else az
            d = fit_distance(radius, lens, aspect) * shot.get("zoom", 1.0)
            yield orbit_pos(center, az, shot.get("el", 18), d), center
        elif kind == "cutaway":
            s = tgt or {"centroid": list(center), "bounds": [*lo, *hi]}
            c = Vector(s["centroid"]) + Vector((0, 0, 1.0))
            az = shot.get("az", 215)
            d0 = fit_distance(radius, lens, aspect)
            sb = s["bounds"]; d1 = fit_distance(math.hypot(sb[3] - sb[0], sb[4] - sb[1]) / 2 + 1.0, lens, aspect)
            yield orbit_pos(lerp(center, c, t), az, lerp(shot.get("el", [60, 38])[0], shot.get("el", [60, 38])[1], t), lerp(d0, d1, t)), lerp(center, c, t)
        elif kind == "room":
            b = tgt["bounds"]; eye = b[2] + 1.6; inset = 0.35
            # corner 0..3 = (minx,miny) (maxx,miny) (maxx,maxy) (minx,maxy); the camera looks to the opposite corner
            xs, ys = (b[0] + inset, b[3] - inset), (b[1] + inset, b[4] - inset)
            cx, cy = [(0, 0), (1, 0), (1, 1), (0, 1)][shot.get("corner", 0) % 4]
            start = Vector((xs[cx], ys[cy], eye)); far = Vector((xs[1 - cx], ys[1 - cy], eye))
            dirv = (far - start).normalized()
            pos = start + dirv * lerp(0, shot.get("dolly", 0.8), t)
            yield pos, pos + dirv * 5  # level camera: verticals stay vertical


def render_shot(shot):
    out_site = P(os.path.join(C["site"], "frames", shot["name"]))
    hidden = []
    pats = [re.compile(h, re.I) for h in shot.get("hide", [])]
    for o in visible:
        if any(p.search(o.name) for p in pats):
            o.hide_render = o.hide_viewport = True; hidden.append(o)  # viewport too, so ray checks agree
    cam.data.clip_start = shot.get("clip_start", 0.05)  # > 0.05: cut through a wall behind the camera
    lights = []
    scale = C.get("scale", 1.0)
    manifest = {}
    prev_engine, prev_view, prev_comp = sc.render.engine, sc.view_settings.view_transform, sc.render.use_compositing
    if shot.get("style") == "clay":
        # White model with outlines: the driving video for an AI pass. Clean edges are what the video
        # model locks onto, and the same frames are the reference qa_drift.py checks the AI output against.
        sc.render.engine = "BLENDER_WORKBENCH"
        sh = sc.display.shading
        sh.light, sh.color_type, sh.single_color = "STUDIO", "SINGLE", (0.92, 0.92, 0.92)
        sh.show_cavity, sh.cavity_type = True, "BOTH"
        sh.show_object_outline, sh.object_outline_color = True, (0.05, 0.05, 0.05)
        sh.show_shadows = False
        sc.view_settings.view_transform = "Standard"
        sc.render.use_compositing = False  # the QA reference must be geometry only, no bloom or vignette
    variants = {"desktop": tuple(shot.get("size", (1920, 1080))), "mobile": (1080, 1920)}
    variants = {k: v for k, v in variants.items() if k in shot.get("variants", variants)}
    for variant, (w, h) in variants.items():
        s_ = 1.0 if shot.get("size") and variant == "desktop" else scale  # an explicit size is exact
        sc.render.resolution_x, sc.render.resolution_y = int(w * s_), int(h * s_)
        sc.render.resolution_percentage = 100
        aspect = w / h
        if shot["kind"] == "plan":
            if variant == "mobile":
                continue
            cam.data.type = "ORTHO"
            ext = max(hi.x - lo.x, (hi.y - lo.y) * aspect) * 1.1
            cam.data.ortho_scale = ext
            cam.location = (center.x, center.y, hi.z + 50); cam.rotation_euler = (0, 0, 0)
            path = os.path.join(out_site, "plan.png")
            sc.render.filepath = path
            bpy.ops.render.render(write_still=True)
            manifest = {"image": "frames/%s/plan.png" % shot["name"], "metresPerPixel": ext / sc.render.resolution_x,
                        "centre": [center.x, center.y]}
            cam.data.type = "PERSP"
            continue
        n = 1 if shot["kind"] == "still" else shot.get("frames", 120)
        if variant == "mobile":
            n = max(1, round(n * 0.6)) if n > 1 else 1  # phones get fewer frames
        cam.animation_data_clear()
        for f, (pos, tg) in enumerate(keyframes(shot, aspect, n), start=1):
            look_at(pos, tg)
            cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)  # a key per frame: easing is ours
        sc.frame_start, sc.frame_end = 1, n
        sc.frame_set(1)
        if shot.get("style") != "clay":
            check_camera_clear(shot)
        if not lights and engine == "CYCLES" and shot.get("style") != "clay" and (shot["kind"] == "room" or shot.get("camera")) \
                and C.get("window_lights", {}) is not False and shot.get("window_lights", {}) is not False:
            lights = window_lights(cam.matrix_world.translation.copy(), (cam.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized(), shot)
        if not any(o.name.startswith("sheer|") for o in lights):
            lights += sheers(shot, cam.matrix_world.translation.copy())
        tmp = P(os.path.join("work", "render", shot["name"], variant))
        shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
        dest = os.path.join(out_site, variant)
        shutil.rmtree(dest, ignore_errors=True); os.makedirs(dest)
        sc.render.filepath = os.path.join(tmp, "")
        bpy.ops.render.render(animation=True)
        q = str(shot.get("quality", 78))
        if shot["kind"] == "still":
            src = os.path.join(tmp, "0001.png")
            subprocess.run([FFMPEG, "-v", "error", "-y", "-i", src, "-c:v", "libwebp", "-quality", "85", os.path.join(out_site, variant + ".webp")], check=True)
            shutil.rmtree(dest, ignore_errors=True)
            entry = {"image": "frames/%s/%s.webp" % (shot["name"], variant), "w": sc.render.resolution_x, "h": sc.render.resolution_y}
            if variant == "desktop":
                sc.frame_set(1); hs = {}
                for s in meta["spaces"]:
                    b = s["bounds"]
                    p = world_to_camera_view(sc, cam, Vector((s["centroid"][0], s["centroid"][1], b[2] + 1.0)))
                    if p.z > 0 and 0 <= p.x <= 1 and 0 <= p.y <= 1:
                        hs[s["name"]] = [round(p.x * 100, 2), round((1 - p.y) * 100, 2)]
                    else:
                        print("WARNING hotspot '%s' falls outside the picker frame" % s["name"])
                entry["hotspots"] = hs
            manifest[variant] = entry
        else:
            subprocess.run([FFMPEG, "-v", "error", "-y", "-i", os.path.join(tmp, "%04d.png"), "-c:v", "libwebp",
                            "-quality", q, "-start_number", "1", os.path.join(dest, "%04d.webp")], check=True)
            got = len([x for x in os.listdir(dest) if x.endswith(".webp")])
            assert got == n, "expected %d frames, encoded %d" % (n, got)
            kb = sum(os.path.getsize(os.path.join(dest, x)) for x in os.listdir(dest)) / 1024
            print("%s/%s: %d frames, %.0f KB total, %.0f KB/frame" % (shot["name"], variant, n, kb, kb / n))
            manifest[variant] = {"count": n, "w": sc.render.resolution_x, "h": sc.render.resolution_y}
            if shot.get("video"):  # an MP4 of the same frames, e.g. the driving video for ai_pack.py
                os.makedirs(P(os.path.join("work", "ai")), exist_ok=True)
                mp4 = P(os.path.join("work", "ai", "%s_%s.mp4" % (shot["name"], variant)))
                subprocess.run([FFMPEG, "-v", "error", "-y", "-framerate", str(shot.get("fps", 24)), "-i", os.path.join(tmp, "%04d.png"),
                                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", mp4], check=True)
                print("video:", mp4)
    for o in hidden:
        o.hide_render = o.hide_viewport = False
    for o in lights:
        bpy.data.objects.remove(o, do_unlink=True)
    sc.render.engine, sc.view_settings.view_transform, sc.render.use_compositing = prev_engine, prev_view, prev_comp
    return manifest


frames = {}
mf = P(os.path.join(C["site"], "frames", "manifest.js"))
if os.path.exists(mf):  # keep shots rendered in earlier runs
    txt = open(mf, encoding="utf-8").read()
    frames = json.loads(txt[txt.index("{"):txt.rindex("}") + 1] or "{}")
only = C.get("only")
for shot in C["shots"]:
    if only and shot["name"] not in only:
        continue
    os.makedirs(P(os.path.join(C["site"], "frames", shot["name"])), exist_ok=True)
    frames[shot["name"]] = render_shot(shot)
frames["_meta"] = {"source": meta["source"], "rendered": datetime.datetime.now().isoformat(timespec="minutes"),
                   "sun": {"utc": loc["utc"], "elevation": round(sun_el, 1), "azimuth": round(sun_az, 1)}, "engine": engine,
                   "styling": "indicative" if C.get("props") else None}
with open(mf, "w", encoding="utf-8") as fh:
    fh.write("// Written by blender_render.py. Do not edit by hand.\nwindow.FRAMES = %s;\n" % json.dumps(frames, indent=1))
print("manifest:", mf)
