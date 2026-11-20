"""Build a project's interactive showcase (plans, panoramas, shell) from its IFC and a small project.json.

    python build.py <project_dir>                       # plans + manifest + shell (minutes)
    python build.py <project_dir> --panos               # also render the 360 panoramas (Blender, slow on CPU)
    python build.py <project_dir> --panos --final       # final quality (run on a GPU box)

Writes into <project_dir>: plan/ (one SVG per storey + plan.json), pano/, manifest.json, index.html and
the shell's assets. The 3D explore view lives in explore/ and is built elsewhere; the shell links to it.
See README.md for project.json.
"""
import argparse, csv, html, json, math, os, re, shutil, subprocess, sys, datetime
import shapely
from shapely import affinity
from shapely.geometry import Point

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import extract as X

BLENDER = os.environ.get("BLENDER", r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")
TYPE_LOCS = {  # room type -> where the finishes schedule says something is used
    "Kitchen": r"kitchen|scullery|butler|pantry",
    "Open-plan kitchen": r"kitchen|scullery|butler|pantry",
    "Bathroom": r"bath|ensuite|wet area|shower",
    "WC / powder": r"powder|toilet|\bwc\b",
    "Laundry": r"laund",
    "Bedroom": r"bedroom|robe",
}
GENERAL_LOCS = r"throughout|general|^apartments?\b|typical apartment|apartment typical"


# ---------------------------------------------------------------- plan SVG
def path_d(geom, nd=3):
    out = []
    for p in X.polys_of(geom):
        for ring in [p.exterior, *p.interiors]:
            c = list(ring.coords)
            out.append("M" + " L".join("%.*f %.*f" % (nd, x, nd, -y) for x, y in c[:-1]) + "Z")
    return "".join(out)


def square_angle(geom):
    """Degrees to turn the plan so the building's long walls run across the page (drawings do the same)."""
    r = geom.minimum_rotated_rectangle
    c = list(r.exterior.coords)
    (x0, y0), (x1, y1), (x2, y2) = c[0], c[1], c[2]
    a = (x1 - x0, y1 - y0) if math.hypot(x1 - x0, y1 - y0) >= math.hypot(x2 - x1, y2 - y1) else (x2 - x1, y2 - y1)
    deg = math.degrees(math.atan2(a[1], a[0]))
    return -((deg + 90) % 180 - 90)


def storey_svg(st, units, rooms, rot=0.0):
    R = lambda g: affinity.rotate(g, rot, origin=(0, 0)) if rot else g
    st = {**st, **{k: R(st[k]) for k in ("walls", "outline")}, **{k: [R(g) for g in st[k]] for k in ("doors", "windows", "other")}}
    units = [{**u, "poly": R(u["poly"])} for u in units]
    rooms = [{**r, "poly": R(r["poly"])} for r in rooms]
    geoms = [st["walls"], st["outline"]] + [u["poly"] for u in units] + [r["poly"] for r in rooms]
    minx, miny, maxx, maxy = shapely.union_all([g for g in geoms if not g.is_empty]).bounds
    pad = 1.5
    vb = (minx - pad, -maxy - pad, maxx - minx + 2 * pad, maxy - miny + 2 * pad)
    e = html.escape
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="%.2f %.2f %.2f %.2f" data-storey="%s">' % (*vb, e(st["id"]))]
    if not st["outline"].is_empty:
        s.append('<path class="slab" d="%s"/>' % path_d(st["outline"]))
    for u in units:
        s.append('<path class="unit" data-unit="%s" d="%s"><title>%s</title></path>' % (e(u["id"]), path_d(u["poly"]), e(u["name"])))
    for r in rooms:
        s.append('<path class="room%s" data-room="%s" d="%s"><title>%s</title></path>'
                 % ("" if r["unit"] else " common", e(r["id"]), path_d(r["poly"]), e(r["name"])))
    s.append('<path class="other" d="%s"/>' % path_d(shapely.union_all(st["other"])) if st["other"] else "")
    s.append('<path class="window" d="%s"/>' % path_d(shapely.union_all(st["windows"])) if st["windows"] else "")
    s.append('<path class="door" d="%s"/>' % path_d(shapely.union_all(st["doors"])) if st["doors"] else "")
    s.append('<path class="wall" d="%s"/>' % path_d(st["walls"]))
    fs = max(0.3, vb[2] / 80)  # labels readable at building scale, not just house scale
    s.append('<g class="labels" style="font-size:%.2fpx">' % fs)
    for r in rooms:
        if r["poly"].area < max(3, (fs * 5) ** 2):  # too small to hold its label: name shows on tap
            continue
        p = r["poly"].representative_point()
        s.append('<text x="%.2f" y="%.2f" data-for="%s"><tspan x="%.2f">%s</tspan><tspan x="%.2f" dy="1.15em" class="a">%s m²</tspan></text>'
                 % (p.x, -p.y, e(r["id"]), p.x, e(r["name"]), p.x, ("%.1f" % r["area"])))
    s.append("</g></svg>")
    return "\n".join(x for x in s if x)


# ---------------------------------------------------------------- spec library
def load_speclib(cfg):
    if not cfg or not os.path.isdir(cfg.get("dir", "")):
        return None
    d, job = cfg["dir"], str(cfg["job"])
    prods = {r["product_id"]: r for r in csv.DictReader(open(os.path.join(d, "products.csv"), encoding="utf-8-sig"))}
    uses = [u for u in csv.DictReader(open(os.path.join(d, "usages.csv"), encoding="utf-8-sig")) if u["job_id"] == job]
    print("spec library: %d usages for job %s" % (len(uses), job))
    return {"dir": d, "prods": prods, "uses": uses}


def finishes_for(lib, rx, out_dir):
    """Spec library entries whose scheduled location matches rx. Nothing is inferred beyond the schedule wording."""
    if not lib:
        return []
    got, seen = [], set()
    for u in lib["uses"]:
        if not re.search(rx, u["location"] or "", re.I) or u["product_id"] in seen:
            continue
        seen.add(u["product_id"])
        p = lib["prods"].get(u["product_id"], {})
        thumb = None
        if p.get("thumbnail") and os.path.exists(os.path.join(lib["dir"], p["thumbnail"])):
            os.makedirs(os.path.join(out_dir, "thumbs"), exist_ok=True)
            shutil.copy2(os.path.join(lib["dir"], p["thumbnail"]), os.path.join(out_dir, "thumbs", os.path.basename(p["thumbnail"])))
            thumb = "plan/thumbs/" + os.path.basename(p["thumbnail"])
        got.append({k: v for k, v in {
            "code": u["schedule_code"], "category": p.get("category"), "item": p.get("item_type"), "maker": p.get("maker"),
            "range": p.get("range_name"), "model": p.get("model_code"), "finish": p.get("finish_colour"), "material": p.get("material"),
            "location": u["location"], "status": u["status"],
            "source": "%s %s" % (os.path.basename(u["source_doc"] or ""), u["source_ref"] or ""), "thumb": thumb}.items() if v})
    return sorted(got, key=lambda g: (g.get("category") or "", g.get("code") or ""))


def room_rx(room):
    parts = [rx for t, rx in TYPE_LOCS.items() if room["name"] == t or room["name"].startswith(t + " and ")][:1]
    if room["type"] == "space":  # an IfcSpace name such as "Cinema" or "Bin Room": match its words
        parts += [re.escape(w) for w in re.findall(r"[A-Za-z]{4,}", room["name"]) if w.lower() not in ("room", "area", "apt.")]
    return "|".join(parts) or None


# ---------------------------------------------------------------- stages
def build_plans(proj, cfg):
    plan_dir = os.path.join(proj, "plan")
    os.makedirs(plan_dir, exist_ok=True)
    d = X.extract(os.path.join(proj, cfg["ifc"]), cfg.get("extract", {}))
    lib = load_speclib(cfg.get("speclib"))
    storeys = []
    big = max(d["storeys"], key=lambda st: st["walls"].area)["walls"] if d["storeys"] else None
    rot = float(cfg.get("plan_rotate_deg", square_angle(big) if big is not None else 0.0))
    for st in d["storeys"]:
        us = [u for u in d["units"] if u["storey"] == st["name"]]
        rs = [r for r in d["rooms"] if r["storey"] == st["name"]]
        open(os.path.join(plan_dir, st["id"] + ".svg"), "w", encoding="utf-8").write(storey_svg(st, us, rs, rot))
        storeys.append({"id": st["id"], "name": st["name"], "elevation": st["elevation"], "svg": "plan/%s.svg" % st["id"],
                        "units": [u["id"] for u in us], "rooms": [r["id"] for r in rs]})
    general = finishes_for(lib, GENERAL_LOCS, plan_dir)
    units = [{"id": u["id"], "name": u["name"], "storey": u["storey"], "area": u["area"], "area_source": u["area_source"],
              "ifc": u["ifc"], "finishes": general} for u in d["units"]]
    rooms = []
    for r in d["rooms"]:
        rx = room_rx(r)
        rooms.append({"id": r["id"], "name": r["name"], "storey": r["storey"], "unit": r["unit"], "area": r["area"],
                      "area_source": r["area_source"], "named_by": r["named_by"], "ifc": r["ifc"],
                      "finishes": finishes_for(lib, rx, plan_dir) if rx else [],
                      "centroid": [round(r["poly"].centroid.x, 3), round(r["poly"].centroid.y, 3)], "floor_z": round(r["z"], 3),
                      "spots": X.camera_spots(r["poly"]) if r["poly"].area >= 4 else []})
    plan = {"source": os.path.basename(cfg["ifc"]), "schema": d["schema"], "built": datetime.datetime.now().isoformat(timespec="minutes"),
            "cut_height": cfg.get("extract", {}).get("cut_height", 1.2), "plan_rotation": round(rot, 2), "storeys": storeys, "units": units, "rooms": rooms,
            "speclib": {"job": cfg["speclib"]["job"], "general": len(general)} if lib else None}
    json.dump(plan, open(os.path.join(plan_dir, "plan.json"), "w", encoding="utf-8"), indent=1)
    print("plans: %d storeys, %d units, %d rooms -> %s" % (len(storeys), len(units), len(rooms), plan_dir))
    return plan


def pick_panos(plan, pcfg):
    rooms = {r["id"]: r for r in plan["rooms"]}
    want = [rooms[i] for i in pcfg.get("rooms", []) if i in rooms]
    missing = [i for i in pcfg.get("rooms", []) if i not in rooms]
    if missing:
        sys.exit("pano rooms not in the plan: %s" % missing)
    if not want and pcfg.get("auto"):  # a kitchen, then the biggest other room and a bathroom in the same unit
        for k in [r for r in plan["rooms"] if r["name"] == "Kitchen" and r["spots"]]:
            same = [r for r in plan["rooms"] if r["unit"] == k["unit"] and r["storey"] == k["storey"] and r["spots"] and r is not k]
            big = sorted([r for r in same if r["name"] not in ("Bathroom", "WC / powder", "Laundry")], key=lambda r: -r["area"])
            want = [k] + big[:1] + [r for r in same if r["name"] == "Bathroom"][:1]
            break
        want = want[: pcfg["auto"]]
    return want


def build_panos(proj, cfg, plan, final=False):
    pcfg = cfg.get("panos", {})
    want = pick_panos(plan, pcfg)
    if not want:
        print("panos: none selected (set panos.rooms or panos.auto in project.json)")
        return
    pano_dir = os.path.join(proj, "pano")
    os.makedirs(pano_dir, exist_ok=True)
    scripts = os.path.join(os.path.dirname(HERE), "scripts")
    storeys = [s["name"] for s in plan["storeys"]]
    by_storey = {}
    for r in want:
        by_storey.setdefault(r["storey"], []).append(r)
    for stname, rs in by_storey.items():
        work = os.path.join(pano_dir, "work", X.slug(stname))
        i = storeys.index(stname)
        keep = ",".join(storeys[i:i + 2])  # the storey above holds the ceiling slab
        if not os.path.exists(os.path.join(work, "model.obj")):
            subprocess.run([sys.executable, os.path.join(scripts, "ifc_to_obj.py"), os.path.join(proj, cfg["ifc"]), work, "--storey", keep], check=True)
        meta = json.load(open(os.path.join(work, "scene.json")))
        off = meta.get("offset", [0, 0, 0])
        fin = os.path.join(proj, pcfg.get("finishes", "pano/finishes.csv"))
        placeholder_finishes(fin, meta["materials"])
        size = pcfg.get("final_size", [8192, 4096]) if final else pcfg.get("size", [4096, 2048])
        shots = {"model": os.path.relpath(os.path.join(work, "model.obj"), pano_dir), "scene": os.path.relpath(os.path.join(work, "scene.json"), pano_dir),
                 "finishes": os.path.relpath(fin, pano_dir), "site": ".", "engine": "CYCLES",
                 "location": pcfg.get("location", {"lat": -37.81, "lon": 144.96, "utc": "2026-03-20T02:00"}),
                 "samples": pcfg.get("final_samples", 512) if final else pcfg.get("samples", 24),
                 "noise_threshold": 0.01 if final else 0.1, "device": "GPU" if final else "CPU",
                 "exposure": "auto", "sun_strength": 1.5, "ground": "#7b7a6c", "shots": [],
                 "panos": [{"name": r["id"], "spots": [[x - off[0], y - off[1]] for x, y in r["spots"]],
                            "z": r["floor_z"] + pcfg.get("eye", 1.5), "size": size,
                            "hide": pcfg.get("hide", [])} for r in rs]}
        sj = os.path.join(pano_dir, "shots_%s.json" % X.slug(stname))
        json.dump(shots, open(sj, "w"), indent=1)
        print("rendering %d panoramas on %s (%dx%d, %d samples)..." % (len(rs), stname, size[0], size[1], shots["samples"]))
        subprocess.run([BLENDER, "-b", "--factory-startup", "-P", os.path.join(HERE, "pano_render.py"), "--", sj], check=True)


def placeholder_finishes(path, materials):
    """Every IFC material needs a row or the renderer stops. Rows we add are neutral and say so: real
    finishes come from the spec library or a calibrated sample, never from a guess."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig"))) if os.path.exists(path) else []
    have = {r["ifc_material"] for r in rows}
    cols = ["ifc_material", "color", "roughness", "metallic", "transmission", "hide", "texture", "tile_m", "normal_strength", "procedural", "vein", "source"]
    for m in materials:
        if m in have:
            continue
        glass = re.search(r"glass|glaz", m, re.I)
        rows.append({"ifc_material": m, "color": "#d9e2e6" if glass else "#cfcac2", "roughness": "0.05" if glass else "0.7",
                     "metallic": "0", "transmission": "1" if glass else "0", "hide": "",
                     "source": "PLACEHOLDER neutral, not the scheduled finish"})
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols + [c for c in (rows[0].keys() if rows else []) if c not in cols])
        w.writeheader()
        w.writerows(rows)


def build_manifest(proj, cfg, plan):
    panos = {}
    pj = os.path.join(proj, "pano", "panos.json")
    if os.path.exists(pj):
        panos = json.load(open(pj))
    rooms = {r["id"]: r for r in plan["rooms"]}
    for pid, p in panos.items():  # hotspots: every other panorama in the same unit (or storey)
        if cfg.get("panos", {}).get("finishes_note"):
            p["finishes_note"] = cfg["panos"]["finishes_note"]
        r = rooms.get(pid)
        if not r:
            continue
        p["hotspots"] = []
        for qid, q in panos.items():
            o = rooms.get(qid)
            if qid == pid or not o or (o["unit"] or o["storey"]) != (r["unit"] or r["storey"]) or o["storey"] != r["storey"]:
                continue
            dx, dy = q["pos"][0] - p["pos"][0], q["pos"][1] - p["pos"][1]
            dist = math.hypot(dx, dy)
            p["hotspots"].append({"to": qid, "label": o["name"], "yaw": round(math.degrees(math.atan2(dx, dy)), 1),
                                  "pitch": round(-math.degrees(math.atan2(p["pos"][2] - r["floor_z"] - 0.4, dist)), 1), "dist": round(dist, 1)})
    m = {"name": cfg["name"], "subtitle": cfg.get("subtitle", ""), "disclaimer": cfg.get("disclaimer", ""),
         "source": plan["source"], "built": plan["built"], "cut_height": plan["cut_height"], "plan_rotation": plan.get("plan_rotation", 0), "speclib": plan["speclib"],
         "storeys": plan["storeys"], "units": plan["units"], "rooms": plan["rooms"], "panos": panos,
         "hero": cfg.get("hero", []), "explore": "explore/index.html"}
    for r in m["rooms"]:
        r.pop("spots", None)
    json.dump(m, open(os.path.join(proj, "manifest.json"), "w", encoding="utf-8"), indent=1)
    print("manifest: %d panoramas, %d with hotspots" % (len(panos), sum(1 for p in panos.values() if p.get("hotspots"))))


def build_shell(proj):
    src = os.path.join(HERE, "shell")
    for name in os.listdir(src):
        shutil.copy2(os.path.join(src, name), os.path.join(proj, name))
    emblem = os.path.join(os.path.dirname(HERE), "template", "assets", "taiger-emblem.png")
    os.makedirs(os.path.join(proj, "assets"), exist_ok=True)
    shutil.copy2(emblem, os.path.join(proj, "assets", "taiger-emblem.png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--panos", action="store_true", help="render the 360 panoramas (Blender)")
    ap.add_argument("--final", action="store_true", help="final-quality panoramas (GPU)")
    ap.add_argument("--skip-plans", action="store_true", help="reuse plan/plan.json")
    a = ap.parse_args()
    proj = os.path.abspath(a.project)
    cfg = json.load(open(os.path.join(proj, "project.json"), encoding="utf-8"))
    pj = os.path.join(proj, "plan", "plan.json")
    plan = json.load(open(pj, encoding="utf-8")) if a.skip_plans and os.path.exists(pj) else build_plans(proj, cfg)
    if a.panos:
        build_panos(proj, cfg, plan, a.final)
    build_manifest(proj, cfg, plan)
    build_shell(proj)
    print("done: serve %s and open index.html" % proj)


if __name__ == "__main__":
    main()
