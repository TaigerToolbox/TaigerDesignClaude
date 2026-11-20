"""Explore view builder: one IFC + a small project.json -> a static 3D viewer folder.

    python build.py path/to/project.json [--force]

Steps (each one cached in the project's work folder, --force redoes them):
  1. ifc_to_obj.py (the stills pipeline's converter): IFC -> model.obj + scene.json
  2. storey containment from the IFC (which storey each element belongs to, storey heights from placements)
  3. finishes: every IFC material resolved against the finishes sources in project.json, in order
     (spec library export first). Unresolved materials become a labelled neutral placeholder.
  4. split model.obj into one OBJ per storey (Y-up, box-mapped UVs for finishes that have a texture AND
     a verified real-world size), then gltfpack: meshopt compression + 16-bit positions -> storey .glb
  5. explore.json (storeys, hero rooms, camera presets, finishes legend) and the viewer files

Normal Python with ifcopenshell and Pillow. Node for gltfpack (npm install in this folder).
"""
import argparse, csv, json, math, os, re, shutil, subprocess, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
PLACEHOLDER = "#c9c7c1"  # neutral, labelled "placeholder" in the viewer legend
GLASS_RX = re.compile(r"glass|glaz|^\W?GLS?[\s\-_]?\d", re.I)
NOT_GLASS_RX = re.compile(r"solar|miele|appliance|mirror", re.I)  # opaque glass products
is_glass = lambda m: bool(GLASS_RX.search(m)) and not NOT_GLASS_RX.search(m)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "x"


def run(cmd, **kw):
    print(">", " ".join('"%s"' % c if " " in c else c for c in cmd), flush=True)
    subprocess.run(cmd, check=True, **kw)


def fresh(out, *inputs):
    return os.path.exists(out) and all(os.path.getmtime(out) >= os.path.getmtime(i) for i in inputs if os.path.exists(i))


# ---------- 1. geometry
def convert(cfg, ifc, work, force):
    obj, scene = os.path.join(work, "model.obj"), os.path.join(work, "scene.json")
    if not force and fresh(obj, ifc) and fresh(scene, ifc):
        print("geometry cached:", obj)
        return
    conv = [sys.executable, os.path.join(SCRIPTS, "ifc_to_obj.py"), ifc]
    if not cfg.get("convert_per_storey"):
        run(conv + [work] + cfg.get("convert_args", []))
        return
    # Big models (200 MB+) run out of memory tessellated in one go: convert storey by storey, a few at a time
    # (each process holds only its storey), then merge into the one model.obj + scene.json the rest expects.
    import ifcopenshell
    names = sorted({s.Name for s in ifcopenshell.open(ifc).by_type("IfcBuildingStorey") if s.Name and "," not in s.Name})
    parts, procs = [], []
    for i, name in enumerate(names):
        pdir = os.path.join(work, "parts", "%02d" % i)
        os.makedirs(pdir, exist_ok=True)
        parts.append(pdir)
        while len([p for p in procs if p.poll() is None]) >= int(cfg.get("convert_jobs", 3)):
            procs[[p.poll() is None for p in procs].index(True)].wait()
        print("converting storey %r" % name, flush=True)
        procs.append(subprocess.Popen(conv + [pdir, "--storey", name] + cfg.get("convert_args", []),
                                      stdout=open(os.path.join(pdir, "log.txt"), "w"), stderr=subprocess.STDOUT))
    for p in procs:
        p.wait()
    merged, off0, vbase = None, None, 0
    with open(obj, "w", encoding="utf-8") as out:
        for pdir in parts:
            pj = os.path.join(pdir, "scene.json")
            if not os.path.exists(pj):
                print("  (no geometry in %s: %s)" % (pdir, open(os.path.join(pdir, "log.txt")).read().strip().splitlines()[-1:]))
                continue
            sc = json.load(open(pj))
            off0 = off0 or sc["offset"]
            dx, dy = sc["offset"][0] - off0[0], sc["offset"][1] - off0[1]
            sh = lambda b: [b[0] + dx, b[1] + dy, b[2], b[3] + dx, b[4] + dy, b[5]]
            for sp in sc["spaces"]:
                sp["bounds"] = sh(sp["bounds"])
                sp["centroid"] = [sp["centroid"][0] + dx, sp["centroid"][1] + dy, sp["centroid"][2]]
            if merged is None:
                merged = sc
            else:
                merged["materials"] = sorted(set(merged["materials"]) | set(sc["materials"]))
                merged["spaces"] += sc["spaces"]
                merged["skipped"] += sc["skipped"]
            n = 0
            for line in open(os.path.join(pdir, "model.obj"), encoding="utf-8"):
                if line.startswith("v "):
                    x, y, z = map(float, line[2:].split())
                    out.write("v %.5f %.5f %.5f\n" % (x + dx, y + dy, z)); n += 1
                elif line.startswith("f "):
                    out.write("f %s\n" % " ".join(str(int(t) + vbase) for t in line[2:].split()))
                elif not line.startswith("#"):
                    out.write(line)
            vbase += n
    assert merged, "no storey produced geometry"
    merged["bounds"] = None
    json.dump(merged, open(scene, "w"), indent=1)


# ---------- 2. storeys
def containment(ifc, work, force):
    out = os.path.join(work, "storeys.json")
    if not force and fresh(out, ifc):
        return json.load(open(out))
    import ifcopenshell, ifcopenshell.util.element as uel, ifcopenshell.util.placement as up, ifcopenshell.util.unit
    print("reading storey containment ...", flush=True)
    f = ifcopenshell.open(ifc)
    unit = ifcopenshell.util.unit.calculate_unit_scale(f)
    storeys = {}
    for st in f.by_type("IfcBuildingStorey"):
        z = float(up.get_local_placement(st.ObjectPlacement)[2][3]) * unit if st.ObjectPlacement else float(st.Elevation or 0) * unit
        storeys[st.GlobalId] = {"name": st.Name or st.GlobalId, "z": round(z, 4)}
    elems = {}
    for e in f.by_type("IfcProduct"):
        c, p = uel.get_container(e), e
        while c is None:  # stair flights, curtain wall panels and the like hang off an aggregate
            p = uel.get_aggregate(p)
            if p is None:
                break
            c = uel.get_container(p)
        if c is not None and c.GlobalId in storeys:
            elems[e.GlobalId] = c.GlobalId
    data = {"storeys": storeys, "elements": elems}
    json.dump(data, open(out, "w"))
    return data


# ---------- 3. finishes
CODE_RX = re.compile(r"(?<![A-Z])([A-Z]{1,4})[\s\-_]*(\d{1,3})([A-Z]?)(?![0-9])")


def codes(name):
    """Schedule codes inside a material name: 'K TBV-02 - TIMBER VENEER OAK' -> ['TBV02', 'K'...]."""
    out = []
    for a, n, s in CODE_RX.findall(name.upper()):
        out.append("%s%02d%s" % (a, int(n), s))
        if s:
            out.append("%s%02d" % (a, int(n)))
    return out


def mean_colour(path):
    from PIL import Image
    im = Image.open(path).convert("RGB").resize((64, 64))
    px = list(im.get_flattened_data()) if hasattr(im, "get_flattened_data") else list(im.getdata())
    lin = lambda c: (c / 255 / 12.92) if c / 255 <= 0.04045 else ((c / 255 + 0.055) / 1.055) ** 2.4
    m = [sum(lin(p[i]) for p in px) / len(px) for i in range(3)]  # average in linear light, not sRGB
    srgb = lambda v: 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
    return "#%02x%02x%02x" % tuple(round(min(1, srgb(v)) * 255) for v in m)


def resolve_finishes(cfg, root, materials):
    sources = []
    for s in cfg.get("finishes", []):
        p = s if os.path.isabs(s) else os.path.join(root, s)
        rows = list(csv.DictReader(open(p, encoding="utf-8-sig")))
        byname = {r["ifc_material"].strip(): r for r in rows}
        bycode = {}
        for r in rows:
            for part in r["ifc_material"].split("/"):  # 'TIL-01 / STN-04'
                for c in codes(part):
                    bycode.setdefault(c, r)
        sources.append((p, byname, bycode))
    out = {}
    for m in materials:
        res, matched = None, None
        for p, byname, bycode in sources:
            r = byname.get(m) or next((bycode[c] for c in codes(m) if c in bycode), None)
            if not r:
                continue
            matched = matched or r
            if (r.get("hide") or "").strip() in ("1", "yes", "true"):
                res = {"hide": True, "source": r.get("source", "")}
                break
            tex = (r.get("texture") or "").strip()
            if tex and not os.path.isabs(tex):
                tex = os.path.normpath(os.path.join(os.path.dirname(p), tex))
            colour = (r.get("color") or "").strip()
            how = "schedule colour"
            if not colour and tex and os.path.exists(tex):
                colour, how = mean_colour(tex), "mean of supplier swatch"
            if not colour:
                continue  # matched but nothing to show yet: try the next source
            tile = (r.get("tile_m") or "").strip()
            res = {"color": colour, "roughness": float(r.get("roughness") or 0.7), "metallic": float(r.get("metallic") or 0),
                   "glass": float(r.get("transmission") or 0) > 0 or is_glass(m),
                   "texture": tex if tex and tile and os.path.exists(tex) else "",  # no verified size, no texture
                   "tile_m": float(tile) if tile else 0, "code": r["ifc_material"].strip(),
                   "source": "%s (%s; %s)" % (r.get("source", "").strip()[:160], how, os.path.basename(p)), "placeholder": False}
            break
        if res is None:
            glass = is_glass(m)
            res = {"color": "#a9c4d0" if glass else PLACEHOLDER, "roughness": 0.1 if glass else 0.8, "metallic": 0, "glass": glass,
                   "texture": "", "tile_m": 0, "code": matched["ifc_material"].strip() if matched else "", "placeholder": True,
                   "source": ("scheduled as %s but no colour or swatch yet: %s" % (matched["ifc_material"].strip(), matched.get("source", "")[:160]))
                   if matched else "not in the finishes sources"}
        out[m] = res
    return out


# ---------- 4. split + pack
def lin(hexc):
    h = hexc.lstrip("#")
    return [(c / 12.92) if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))]


def split_obj(work, scene, cont, fin, outdir):
    """Stream model.obj into one Y-up OBJ per storey. Returns {group: stats}."""
    st = cont["storeys"]
    levels = sorted(((v["z"], gid) for gid, v in st.items()), key=lambda x: x[0])

    def by_z(zmin):  # fallback when the IFC doesn't say: highest storey at or below the element's bottom
        best = None
        for z, gid in levels:
            if z <= zmin + 0.3:
                best = gid
        return best or (levels[0][1] if levels else "site")

    mats = {m: "m%d" % i for i, m in enumerate(sorted(fin))}
    os.makedirs(outdir, exist_ok=True)
    texdir = os.path.join(outdir, "tex")
    files, stats = {}, {}

    def handle(group):
        if group not in files:
            fh = open(os.path.join(outdir, group + ".obj"), "w", encoding="utf-8")
            fh.write("mtllib materials.mtl\n")
            files[group] = [fh, 0, 0]  # handle, verts written, uvs written
            stats[group] = {"tris": 0, "elements": 0, "zmin": 1e9, "zmax": -1e9}
        return files[group]

    def flush(name, verts, faces):
        if not faces:
            return
        gid = name.split("|")[1] if name.count("|") >= 2 else ""
        cls = name.split("|")[0]
        sgid = cont["elements"].get(gid)
        group = "site" if cls in ("IfcSite", "IfcGeographicElement") and not sgid else (sgid or by_z(min(v[2] for v in verts)))
        fh, nv, nt = handle(group)
        s = stats[group]
        s["elements"] += 1
        w = fh.write
        for x, y, z in verts:
            w("v %.4f %.4f %.4f\n" % (x, z, -y))
        s["zmin"] = min(s["zmin"], min(v[2] for v in verts))
        s["zmax"] = max(s["zmax"], max(v[2] for v in verts))
        cur = None
        for m, a, b, c in faces:
            f = fin.get(m)
            if f is None or f.get("hide"):
                continue
            if m != cur:
                w("usemtl %s\n" % mats[m])
                cur = m
            if f["texture"]:
                pa, pb, pc = verts[a], verts[b], verts[c]
                u = [pb[i] - pa[i] for i in range(3)]
                v = [pc[i] - pa[i] for i in range(3)]
                n = [abs(u[1] * v[2] - u[2] * v[1]), abs(u[2] * v[0] - u[0] * v[2]), abs(u[0] * v[1] - u[1] * v[0])]
                ax = n.index(max(n))  # box mapping: project on the plane the face mostly faces, at true scale
                i, j = [(1, 2), (0, 2), (0, 1)][ax]
                t = f["tile_m"]
                for p in (pa, pb, pc):
                    w("vt %.4f %.4f\n" % (p[i] / t, p[j] / t))
                w("f %d/%d %d/%d %d/%d\n" % (nv + a + 1, nt + 1, nv + b + 1, nt + 2, nv + c + 1, nt + 3))
                nt += 3
            else:
                w("f %d %d %d\n" % (nv + a + 1, nv + b + 1, nv + c + 1))
            s["tris"] += 1
        files[group][1] = nv + len(verts)
        files[group][2] = nt

    name, verts, faces, base, cur = None, [], [], 1, None
    total = 1
    with open(os.path.join(work, "model.obj"), encoding="utf-8") as src:
        for line in src:
            k = line[:2]
            if k == "v ":
                verts.append(tuple(map(float, line[2:].split())))
                total += 1
            elif k == "f ":
                a, b, c = (int(x) - base for x in line[2:].split())
                faces.append((cur, a, b, c))
            elif k == "us":
                cur = line[7:].rstrip("\n")
            elif k == "o ":
                flush(name, verts, faces)
                name, verts, faces, base = line[2:].strip(), [], [], total
    flush(name, verts, faces)
    for fh, _, _ in files.values():
        fh.close()

    with open(os.path.join(outdir, "materials.mtl"), "w", encoding="utf-8") as mtl:
        for m, mid in mats.items():
            f = fin[m]
            if f.get("hide"):
                continue
            r, g, b = lin(f["color"])
            mtl.write("newmtl %s\nKd %.4f %.4f %.4f\n" % (mid, r, g, b))
            if f["glass"]:
                mtl.write("d 0.3\n")
            if f["texture"]:
                os.makedirs(texdir, exist_ok=True)
                from PIL import Image
                tn = slug(os.path.splitext(os.path.basename(f["texture"]))[0])[:60] + ".jpg"
                im = Image.open(f["texture"]).convert("RGB")
                im.thumbnail((512, 512))  # phone GPU memory: 512 px is plenty at true scale
                im.save(os.path.join(texdir, tn), quality=82)
                mtl.write("map_Kd tex/%s\n" % tn)
                mtl.write("Kd 1 1 1\n")  # the swatch carries the colour
    return stats, mats


def pack(objdir, group, out_glb):
    gp = os.path.join(HERE, "node_modules", "gltfpack", "cli.js")
    if not os.path.exists(gp):
        run(["npm", "install", "--no-audit", "--no-fund"], cwd=HERE, shell=os.name == "nt")
    # -cc meshopt compression, -vp 16: positions to 16 bits (sub-mm on a 60 m building); no simplification:
    # the geometry stays the IFC's.
    run(["node", gp, "-i", os.path.join(objdir, group + ".obj"), "-o", out_glb, "-cc", "-vp", "16"])


# ---------- 5. explore.json + viewer
def to_y(p):  # model Z-up -> viewer Y-up
    return [round(p[0], 3), round(p[2], 3), round(-p[1], 3)]


def room_camera(b, eye=1.6):
    """Stand at one end of the room's long axis, look down its length at the far end."""
    x0, y0, z0, x1, y1, z1 = b
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if x1 - x0 >= y1 - y0:
        pos, look = [x0 + 0.12 * (x1 - x0), cy, z0 + eye], [x1, cy, z0 + 1.2]
    else:
        pos, look = [cx, y0 + 0.12 * (y1 - y0), z0 + eye], [cx, y1, z0 + 1.2]
    return {"pos": to_y(pos), "look": to_y(look)}


def room_triangles(obj_path, boxes, skip_mats):
    """One pass over model.obj: the triangles inside each box (x0,y0,z0,x1,y1,z1), as numpy arrays."""
    import numpy as np
    found = [[] for _ in boxes]
    def flush(verts, faces):
        if not faces:
            return
        xs, ys, zs = zip(*verts)
        ob = (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))
        for i, b in enumerate(boxes):
            if ob[0] <= b[3] and ob[3] >= b[0] and ob[1] <= b[4] and ob[4] >= b[1] and ob[2] <= b[5] and ob[5] >= b[2]:
                found[i].extend((verts[a], verts[c2], verts[c3]) for m, a, c2, c3 in faces if m not in skip_mats)
    verts, faces, base, total, cur = [], [], 1, 1, None
    with open(obj_path, encoding="utf-8") as src:
        for line in src:
            k = line[:2]
            if k == "v ":
                verts.append(tuple(map(float, line[2:].split()))); total += 1
            elif k == "f ":
                a, b, c = (int(x) - base for x in line[2:].split()); faces.append((cur, a, b, c))
            elif k == "us":
                cur = line[7:].rstrip("\n")
            elif k == "o ":
                flush(verts, faces); verts, faces, base = [], [], total
    flush(verts, faces)
    return [np.array(f, dtype=np.float64).reshape(-1, 3, 3) for f in found]


def raycast(orig, dirs, tris, far=30.0):
    """Nearest hit distance per ray (Moller-Trumbore, vectorised in chunks of triangles)."""
    import numpy as np
    best = np.full(len(orig), far)
    for i in range(0, len(tris), 800):  # chunk keeps the R x N arrays to ~50 MB
        t = tris[i:i + 800]
        v0, e1, e2 = t[:, 0], t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]
        p = np.cross(dirs[:, None, :], e2[None])                      # R,N,3
        det = np.einsum("rnk,nk->rn", p, e1)
        ok = np.abs(det) > 1e-9
        inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
        s = orig[:, None, :] - v0[None]
        u = np.einsum("rnk,rnk->rn", s, p) * inv
        qv = np.cross(s, e1[None])
        v = np.einsum("rk,rnk->rn", dirs, qv) * inv
        d = np.einsum("rnk,nk->rn", qv, e2) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (d > 1e-4)
        best = np.minimum(best, np.where(hit, d, far).min(axis=1))
    return best


def scout_camera(b, tris, eye=1.6):
    """Search a grid of standing spots in the room at eye height and keep the most open one that stands on the
    room's floor, is under a ceiling and is clear of walls; look the way the view runs furthest. Same idea as the
    stills pipeline's `scout` shot, done on the IFC triangles so it needs no renderer."""
    import numpy as np
    x0, y0, z0, x1, y1, z1 = b
    if len(tris) == 0:
        return None
    nx, ny = (int(min(10, max(3, (hi - lo) / 0.7))) for lo, hi in ((x0, x1), (y0, y1)))
    pts = np.array([(x, y, z0 + eye) for x in np.linspace(x0 + 0.35, x1 - 0.35, nx) for y in np.linspace(y0 + 0.35, y1 - 0.35, ny)])
    ang = np.linspace(0, 2 * np.pi, 16, endpoint=False)
    hd = np.stack([np.cos(ang), np.sin(ang), np.zeros(16)], 1)
    dirs = np.concatenate([hd, [[0, 0, 1], [0, 0, -1]]])
    R = len(dirs)
    d = raycast(np.repeat(pts, R, 0), np.tile(dirs, (len(pts), 1)), tris).reshape(len(pts), R)
    best, cam = -1, None
    for i, p in enumerate(pts):
        h, up, down = np.minimum(d[i, :16], 10), d[i, 16], d[i, 17]
        if abs(down - eye) > 0.25 or up > 5 or h.min() < 0.45:
            continue
        win = np.array([h[(k + np.arange(-2, 3)) % 16].mean() for k in range(16)])  # ~90 deg view
        k = int(win.argmax())
        score = 0.6 * win[k] + 0.4 * h.mean()
        if score > best:
            look = p + hd[k] * min(4.0, h[k])
            best, cam = score, {"pos": to_y(p.tolist()), "look": to_y([look[0], look[1], z0 + 1.3])}
    return cam


def build(cfg_path, force):
    root = os.path.dirname(os.path.abspath(cfg_path))
    cfg = json.load(open(cfg_path, encoding="utf-8"))
    P = lambda p: p if os.path.isabs(p) else os.path.normpath(os.path.join(root, p))
    ifc, work, out = P(cfg["ifc"]), P(cfg.get("work", "work")), P(cfg.get("out", "explore"))
    assert os.path.exists(ifc), "IFC not found: %s" % ifc
    os.makedirs(work, exist_ok=True)

    convert(cfg, ifc, work, force)
    scene = json.load(open(os.path.join(work, "scene.json")))
    cont = containment(ifc, work, force)
    fin = resolve_finishes(cfg, root, scene["materials"])
    n_ph = sum(1 for f in fin.values() if f.get("placeholder"))
    print("finishes: %d materials, %d from sources, %d neutral placeholders" % (len(fin), len(fin) - n_ph, n_ph))

    objdir = os.path.join(work, "explore_obj")
    shutil.rmtree(objdir, ignore_errors=True)
    stats, mats = split_obj(work, scene, cont, fin, objdir)

    skip = re.compile(cfg["skip_storeys"], re.I) if cfg.get("skip_storeys") else None
    os.makedirs(os.path.join(out, "models"), exist_ok=True)
    for old in os.listdir(os.path.join(out, "models")):
        os.remove(os.path.join(out, "models", old))
    storeys = []
    for g, s in stats.items():
        if s["tris"] == 0:
            continue
        name = "Site" if g == "site" else cont["storeys"][g]["name"]
        if skip and skip.search(name):
            print("skipping storey", name)
            continue
        z = s["zmin"] if g == "site" else cont["storeys"][g]["z"]
        fn = "models/%s.glb" % slug(name)
        pack(objdir, g, os.path.join(out, fn))
        storeys.append({"id": slug(name), "name": name, "z": round(z, 3), "top": round(s["zmax"], 3),
                        "file": fn, "bytes": os.path.getsize(os.path.join(out, fn)), "tris": s["tris"], "elements": s["elements"],
                        "site": g == "site"})
    storeys.sort(key=lambda s: (not s["site"], s["z"]))
    levels = [s for s in storeys if not s["site"]]
    assert levels, "no storeys with geometry"

    # bounds of what is shown
    zs = [s["z"] for s in levels]
    b = scene["bounds"] if scene.get("bounds") else None
    def storey_of(z):
        best = levels[0]
        for s in levels:
            if s["z"] <= z + 0.3:
                best = s
        return best

    rooms = []
    spaces = scene.get("spaces", [])
    for r in cfg.get("rooms", []):
        rx = re.compile(r.get("match", re.escape(r.get("name", r.get("id", "")))), re.I)
        cand = [sp for sp in spaces if rx.search(sp.get("name") or "") or rx.search(sp.get("id") or "")]
        lo, hi = min(zs) - 1.0, max(s["top"] for s in levels)
        bad = [sp for sp in cand if not lo <= sp["bounds"][2] <= hi]
        if bad:  # some exports carry spaces from elsewhere (design options, linked files): keep the ones in the building
            print("room %r: ignoring %d matching spaces outside the building's height" % (r.get("id"), len(bad)))
            cand = [sp for sp in cand if sp not in bad]
        if r.get("storey"):
            srx = re.compile(r["storey"], re.I)
            cand = [sp for sp in cand if srx.search(storey_of(sp["bounds"][2])["name"])]
        if not cand and not r.get("camera"):
            print("WARNING room %r matched no space; give it a camera or a match regex" % r.get("id"))
            continue
        sp = max(cand, key=lambda sp: (sp["bounds"][3] - sp["bounds"][0]) * (sp["bounds"][4] - sp["bounds"][1])) if cand else None
        cam = r.get("camera")
        if cam:
            cam = {"pos": to_y(cam["pos"]), "look": to_y(cam["look"])}
        floor_z = sp["bounds"][2] if sp else cam["pos"][1] - 1.6
        rooms.append({"id": r.get("id") or slug(r["name"]), "name": r.get("name") or sp["name"], "storey": storey_of(floor_z)["id"],
                      "camera": cam, "space": sp["name"] if sp else None,
                      "bounds": [to_y(sp["bounds"][:3]), to_y(sp["bounds"][3:])] if sp else None,
                      "_b": sp["bounds"] if sp else None, "_eye": r.get("eye", 1.6)})

    todo = [i for i, r in enumerate(rooms) if r["camera"] is None]
    if todo:
        print("scouting cameras for %d rooms ..." % len(todo), flush=True)
        boxes = []
        for i in todo:
            x0, y0, z0, x1, y1, z1 = rooms[i]["_b"]
            boxes.append((x0 - 0.3, y0 - 0.3, z0 - 0.4, x1 + 0.3, y1 + 0.3, z0 + 5.5))
        skip_mats = {m for m, f in fin.items() if f.get("hide")}  # glazing blocks: the view should run into the room, not out
        for i, tris in zip(todo, room_triangles(os.path.join(work, "model.obj"), boxes, skip_mats)):
            r = rooms[i]
            r["camera"] = scout_camera(r["_b"], tris, r.pop("_eye")) or room_camera(r["_b"])
            print("  %s: %d triangles, camera %s" % (r["id"], len(tris), r["camera"]))
    for r in rooms:
        r.pop("_b", None); r.pop("_eye", None)

    default_level = cfg.get("default_level")
    if default_level:
        default_level = next((s["id"] for s in levels if re.search(default_level, s["name"], re.I)), None)
    if not default_level:
        default_level = rooms[0]["storey"] if rooms else levels[0]["id"]
    ground = cfg.get("ground_level")
    ground_z = next((s["z"] for s in levels if ground and re.search(ground, s["name"], re.I)), None)
    if ground_z is None:
        ground_z = next((s["z"] for s in levels if re.search(r"ground|level 0\b|^gf$", s["name"], re.I)), levels[0]["z"])

    src_list = [os.path.basename(P(s)) for s in cfg.get("finishes", [])]
    legend = [{"material": m, "code": f.get("code", ""), "color": f.get("color"), "placeholder": f.get("placeholder", False),
               "textured": bool(f.get("texture")), "source": f.get("source", "")} for m, f in sorted(fin.items()) if not f.get("hide")]
    ex = {
        "name": cfg.get("name", ""),
        "generated": datetime.datetime.now().isoformat(timespec="minutes"),
        "source": scene.get("source"),
        "disclaimer": cfg.get("disclaimer", "Artist's impression from the design model. Geometry from the IFC; finishes from the spec library "
                                             "where scheduled, otherwise a neutral placeholder. Final design and finishes may vary."),
        "units": "m", "up": "y",
        "views": ["exterior", "cutaway"] + ["room:" + r["id"] for r in rooms],
        "cut_height": cfg.get("cut_height", 1.2),
        "ground_y": round(ground_z, 3),
        "default_level": default_level,
        "sun": cfg.get("sun", {"az": 35, "el": 50}),
        "storeys": storeys,
        "rooms": rooms,
        "finishes": {"sources": src_list, "total": len(legend), "placeholders": sum(1 for x in legend if x["placeholder"]), "list": legend},
        "bytes": sum(s["bytes"] for s in storeys),
    }
    json.dump(ex, open(os.path.join(out, "explore.json"), "w", encoding="utf-8"), indent=1)

    # viewer: index.html + viewer.js + the few three.js modules it imports
    for f in ("index.html", "viewer.js"):
        shutil.copy(os.path.join(HERE, "viewer", f), os.path.join(out, f))
    three = os.path.join(HERE, "node_modules", "three")
    for rel in ("build/three.module.min.js", "examples/jsm/controls/OrbitControls.js", "examples/jsm/loaders/GLTFLoader.js",
                "examples/jsm/utils/BufferGeometryUtils.js", "examples/jsm/libs/meshopt_decoder.module.js", "LICENSE"):
        dst = os.path.join(out, "lib", "three", rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(os.path.join(three, rel), dst)
    mb = ex["bytes"] / 1e6
    print("explore view written: %s\n  %d storeys, %d rooms, %.1f MB of models, %d triangles" % (
        out, len(storeys), len(rooms), mb, sum(s["tris"] for s in storeys)))
    for s in storeys:
        print("  %-28s z=%7.2f  %6.2f MB  %8d tris" % (s["name"], s["z"], s["bytes"] / 1e6, s["tris"]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--force", action="store_true", help="redo the cached IFC conversion and containment")
    a = ap.parse_args()
    if not os.path.exists(os.path.join(HERE, "node_modules", "three")):
        run(["npm", "install", "--no-audit", "--no-fund"], cwd=HERE, shell=os.name == "nt")
    build(a.project, a.force)
