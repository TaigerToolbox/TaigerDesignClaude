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


def mean_rgb(img):
    import numpy as np
    px = np.empty(len(img.pixels), dtype=np.float32); img.pixels.foreach_get(px)
    return px.reshape(-1, 4)[:, :3].mean(axis=0)  # linear, since Blender converts sRGB images on load


def world_coords(nt, tile):
    """IFC has no UVs: project textures from world position (metres), so a 1.2 m board stays 1.2 m."""
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / tile, 1 / tile, 1 / tile)
    nt.links.new(geo.outputs["Position"], mp.inputs["Vector"])
    return mp.outputs["Vector"]


def textured(m, b, r):
    """Grain from a texture photo, colour from the approved sample: tex * (sample / mean(tex))."""
    nt = m.node_tree
    vec = world_coords(nt, float(r.get("tile_m") or 1.0))
    diff_path = P(r["texture"])
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = load_img(diff_path)
    tex.projection, tex.projection_blend = "BOX", 0.15
    nt.links.new(vec, tex.inputs["Vector"])
    target = hex_rgba(r["color"])[:3]
    mean = mean_rgb(tex.image)
    tint = nt.nodes.new("ShaderNodeVectorMath"); tint.operation = "MULTIPLY"
    tint.inputs[1].default_value = tuple(t / max(mu, 1e-4) for t, mu in zip(target, mean))
    nt.links.new(tex.outputs["Color"], tint.inputs[0])
    nt.links.new(tint.outputs["Vector"], b.inputs["Base Color"])
    for suffix, sock in (("Rough", "Roughness"), ("nor_gl", "Normal")):
        p = diff_path.replace("Diffuse", suffix)
        if p == diff_path or not os.path.exists(p):
            continue
        t2 = nt.nodes.new("ShaderNodeTexImage"); t2.image = load_img(p, color=False)
        t2.projection, t2.projection_blend = "BOX", 0.15
        nt.links.new(vec, t2.inputs["Vector"])
        if sock == "Roughness":
            k = nt.nodes.new("ShaderNodeMath"); k.operation = "MULTIPLY"
            k.inputs[1].default_value = float(r.get("roughness") or 0.5) / 0.5  # CSV roughness scales the map around 0.5
            nt.links.new(t2.outputs["Color"], k.inputs[0]); nt.links.new(k.outputs[0], b.inputs["Roughness"])
        else:
            nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = float(r.get("normal_strength") or 0.6)
            nt.links.new(t2.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])


def marble(m, b, r):
    """Procedural veined stone for slabs with no CC0 scan. color = base, vein = vein colour, tile_m = vein spacing."""
    # Real veining is a cracked network, not stripes: Voronoi cell edges on a warped field give the
    # crackle; a low-frequency cloud adds the soft tonal drift every slab has.
    nt = m.node_tree
    L = nt.links.new
    vec = world_coords(nt, float(r.get("tile_m") or 0.6))
    warp = nt.nodes.new("ShaderNodeTexNoise"); warp.inputs["Scale"].default_value = 0.9
    warp.inputs["Detail"].default_value = 10; warp.inputs["Roughness"].default_value = 0.62
    amt = nt.nodes.new("ShaderNodeVectorMath"); amt.operation = "SCALE"; amt.inputs["Scale"].default_value = 1.9  # strong warp: long meandering veins, no visible cells
    L(warp.outputs["Color"], amt.inputs[0])
    wv = nt.nodes.new("ShaderNodeVectorMath"); wv.operation = "ADD"; L(vec, wv.inputs[0]); L(amt.outputs["Vector"], wv.inputs[1])
    base = hex_rgba(r["color"]); vein = hex_rgba(r.get("vein") or "#6b4a33")

    def veins(scale, width):
        vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"
        vo.inputs["Scale"].default_value = scale
        L(wv.outputs["Vector"], vo.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange")  # 1 on the edge, 0 a little away from it
        mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.0, width
        mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 1.0, 0.0
        L(vo.outputs["Distance"], mr.inputs["Value"])
        return mr.outputs["Result"]

    big, fine = veins(0.55, 0.022), veins(2.2, 0.008)
    # fine veins only in patches, as in a real slab
    patch = nt.nodes.new("ShaderNodeTexNoise"); patch.inputs["Scale"].default_value = 1.1
    L(wv.outputs["Vector"], patch.inputs["Vector"])
    pm = nt.nodes.new("ShaderNodeMapRange")
    pm.inputs["From Min"].default_value, pm.inputs["From Max"].default_value = 0.5, 0.65
    L(patch.outputs["Fac"], pm.inputs["Value"])
    fine_w = nt.nodes.new("ShaderNodeMath"); fine_w.operation = "MULTIPLY"
    L(fine, fine_w.inputs[0]); L(pm.outputs["Result"], fine_w.inputs[1])
    big_w = nt.nodes.new("ShaderNodeMath"); big_w.operation = "MULTIPLY"; big_w.inputs[1].default_value = 0.85
    L(big, big_w.inputs[0]); big = big_w.outputs[0]
    both = nt.nodes.new("ShaderNodeMath"); both.operation = "MAXIMUM"; both.use_clamp = True
    L(big, both.inputs[0]); L(fine_w.outputs[0], both.inputs[1])
    cloud = nt.nodes.new("ShaderNodeTexNoise"); cloud.inputs["Scale"].default_value = 0.6; cloud.inputs["Detail"].default_value = 3
    L(vec, cloud.inputs["Vector"])
    tone = nt.nodes.new("ShaderNodeMix"); tone.data_type = "RGBA"
    tone.inputs["A"].default_value = base
    tone.inputs["B"].default_value = tuple(c * 0.86 for c in base[:3]) + (1,)
    L(cloud.outputs["Fac"], tone.inputs["Factor"])
    out = nt.nodes.new("ShaderNodeMix"); out.data_type = "RGBA"
    L(both.outputs[0], out.inputs["Factor"]); L(tone.outputs["Result"], out.inputs["A"])
    out.inputs["B"].default_value = vein
    L(out.outputs["Result"], b.inputs["Base Color"])


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

for o in model:
    if o.material_slots and all(s.material and s.material.name in hidden_mats for s in o.material_slots):
        o.hide_render = True  # markers, virtual elements
    # IFC edges are razor sharp, the biggest CG tell. Weld, then a small bevel catches light like real arrises.
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    bm.to_mesh(o.data); bm.free()
    bv = o.modifiers.new("arris", "BEVEL")
    bv.width, bv.segments, bv.limit_method, bv.angle_limit = 0.006, 2, "ANGLE", math.radians(30)
    bv.harden_normals = True
    o.data.shade_smooth()

visible = [o for o in model if not o.hide_render]
pts = [o.matrix_world @ Vector(c) for o in visible for c in o.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center, radius = (lo + hi) / 2, (hi - lo).length / 2

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
sun.data.energy, sun.data.angle = 4.0, math.radians(0.53)
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
sc.view_settings.exposure = C.get("exposure", 0.0)  # interiors lit through glass want +3 to +4.5
if C.get("white_balance"):  # kelvin; ~5300 K keeps warm greige walls from reading grey under a blue sky
    try:
        sc.view_settings.use_white_balance = True
        sc.view_settings.white_balance_temperature = C["white_balance"]
    except AttributeError:
        print("white balance needs Blender 4.3+, skipped")
for look in ("AgX - Medium High Contrast", "Medium High Contrast", "None"):
    try:
        sc.view_settings.look = look; break
    except TypeError:
        pass
engine = C.get("engine", "EEVEE").upper()
if engine == "CYCLES":
    sc.render.engine = "CYCLES"
    sc.cycles.samples = C.get("samples", 256)
    sc.cycles.use_denoising, sc.cycles.seed, sc.cycles.use_animated_seed = True, 0, False  # fixed seed: no boiling noise
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
sc.render.film_transparent = False

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam); sc.camera = cam


def space(name):
    for s in meta["spaces"]:
        if s["name"].lower() == str(name).lower():
            return s
    sys.exit("target space '%s' not in scene.json (have: %s)" % (name, [s["name"] for s in meta["spaces"]]))


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
            o.hide_render = True; hidden.append(o)
    scale = C.get("scale", 1.0)
    manifest = {}
    prev_engine, prev_view = sc.render.engine, sc.view_settings.view_transform
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
        o.hide_render = False
    sc.render.engine, sc.view_settings.view_transform = prev_engine, prev_view
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
                   "sun": {"utc": loc["utc"], "elevation": round(sun_el, 1), "azimuth": round(sun_az, 1)}, "engine": engine}
with open(mf, "w", encoding="utf-8") as fh:
    fh.write("// Written by blender_render.py. Do not edit by hand.\nwindow.FRAMES = %s;\n" % json.dumps(frames, indent=1))
print("manifest:", mf)
