"""360 equirectangular panoramas in Cycles, from build.py's shots_<storey>.json.

    blender -b --factory-startup -P pano_render.py -- pano/shots_level-1.json

Reuses blender_render.py's whole scene build (IFC mesh, finishes, sun, sky, colour management, window
portals, auto exposure) by running its setup section, then renders one panorama per entry in "panos".
blender_render.py is not modified. For each room it tries the candidate spots in order (furthest from
the walls first) and takes the first where the camera is clear of furniture and joinery, so a kitchen
island never swallows the lens. Writes <name>.jpg next to the shots file and merges pano/panos.json.
"""
import bpy, json, math, os, re, subprocess, sys, time
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BR = os.path.join(os.path.dirname(HERE), "scripts", "blender_render.py")
src = open(BR, encoding="utf-8").read()
cut = src.index("\nframes = {}\n")  # everything before the shot loop is scene setup
g = {"__name__": "blender_render_setup", "__file__": BR}
exec(compile(src[:cut], BR, "exec"), g)

C, P, sc, cam = g["C"], g["P"], g["sc"], g["cam"]
out_dir = os.path.dirname(os.path.abspath(sys.argv[sys.argv.index("--") + 1]))
meta = g["meta"]
off = meta.get("offset", [0, 0, 0])
DIRS = [Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e))).normalized()
        for e in (-0.6, 0, 0.6) for a in [i * math.pi / 4 for i in range(8)]] + [Vector((0, 0, 1)), Vector((0, 0, -1))]
SKIP = ("portal|", "winfill|", "camfill", "sheer|")


def probe(pos):
    """(clear, free_yaw): clear if no ray from pos starts inside a solid or hits something within 0.35 m;
    free_yaw = the level direction (deg clockwise from +Y) with the most room in front of it."""
    dg = bpy.context.evaluated_depsgraph_get()
    best, far = 0.0, -1.0
    for d in DIRS:
        hit, loc, nrm, _, ob, _ = sc.ray_cast(dg, pos, d)
        if hit and ob and ob.name.startswith(SKIP):
            continue
        if hit and (nrm.dot(d) > 0 or (loc - pos).length < 0.35):
            return False, 0.0
        dist = (loc - pos).length if hit else 99.0
        if abs(d.z) < 0.1 and dist > far:
            far, best = dist, math.degrees(math.atan2(d.x, d.y))
    return True, best


panos_path = os.path.join(out_dir, "panos.json")
done = json.load(open(panos_path)) if os.path.exists(panos_path) else {}
for p in C.get("panos", []):
    t0 = time.time()
    hidden = []
    for o in g["visible"]:
        if any(re.search(h, o.name, re.I) for h in p.get("hide", [])):
            o.hide_render = o.hide_viewport = True; hidden.append(o)
    pos, yaw0 = None, 0.0
    for x, y in p["spots"]:
        cand = Vector((x, y, p["z"]))
        ok, yaw0 = probe(cand)
        if ok:
            pos = cand; break
    if pos is None:
        print("PANO %s: every candidate spot is inside or against something, skipped" % p["name"])
        continue
    cam.animation_data_clear()
    cam.data.type = "PANO"
    try:
        cam.data.panorama_type = "EQUIRECTANGULAR"
    except AttributeError:
        cam.data.cycles.panorama_type = "EQUIRECTANGULAR"  # Blender < 4
    cam.data.clip_start = 0.05
    cam.location = pos
    cam.rotation_euler = (math.pi / 2, 0, 0)  # level, image centre looks along +Y (yaw 0)
    sc.camera = cam
    w, h = p.get("size", [4096, 2048])
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
    sc.frame_start = sc.frame_end = 1
    sc.frame_set(1)
    shot = {"name": p["name"], "window_lights": p.get("window_lights", {})}
    lights = g["window_lights"](pos.copy(), Vector((0, 1, 0)), shot) if C.get("window_lights", {}) is not False else []
    g["auto_exposure"](shot)
    png = P(os.path.join("work", "render", "pano_%s.png" % p["name"]))
    os.makedirs(os.path.dirname(png), exist_ok=True)
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = png
    bpy.ops.render.render(write_still=True)
    jpg = os.path.join(out_dir, "%s.jpg" % p["name"])
    subprocess.run([g["FFMPEG"], "-v", "error", "-y", "-i", png, "-q:v", "3", jpg], check=True)
    for o in lights:
        bpy.data.objects.remove(o, do_unlink=True)
    for o in hidden:
        o.hide_render = o.hide_viewport = False
    secs = round(time.time() - t0)
    done[p["name"]] = {"src": "pano/%s.jpg" % p["name"], "pos": [round(pos.x + off[0], 3), round(pos.y + off[1], 3), round(pos.z, 3)],
                       "yaw": round(yaw0, 1), "size": [w, h], "samples": C.get("samples"), "device": C.get("device", "CPU"),
                       "quality": "Preview render (%d samples, denoised)" % C.get("samples", 0) if C.get("device", "CPU") == "CPU" else "Final render",
                       "finishes_note": "Finishes are neutral placeholders unless listed in the room's finishes.",
                       "rendered": time.strftime("%Y-%m-%dT%H:%M"), "seconds": secs}
    json.dump(done, open(panos_path, "w"), indent=1)
    print("PANO %s: %dx%d in %d s at %s, looking %.0f deg -> %s" % (p["name"], w, h, secs, tuple(round(v, 2) for v in pos), yaw0, jpg))
