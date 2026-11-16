"""Unit and finishes schedules -> site/data/schedule.js, so every number on the site comes from the schedule.

    python schedule_to_site.py --units units.csv [--specs specs.csv] --out site/data/schedule.js

units.csv: id,type,typeName,level,beds,baths,internal,external,aspect,status[,anchor][,x,y]
  (anchor = the space name in the model, so the render places the hotspot; x,y in % only for previews)
  (internal/external in m2 by the contract's measuring method; blank = not shown)
specs.csv: area,item,supplier,code
Stops on a missing column, a duplicate unit id or a number that doesn't parse: a wrong figure on a
sales site is worse than no site.
"""
import argparse, csv, json, sys

NUM = {"level": int, "beds": int, "baths": float, "internal": float, "external": float, "x": float, "y": float}


def read(path, need):
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    if not rows:
        sys.exit("%s is empty" % path)
    missing = [c for c in need if c not in rows[0]]
    if missing:
        sys.exit("%s is missing columns: %s" % (path, ", ".join(missing)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--units"); ap.add_argument("--specs"); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = {"source": {}}
    if a.units:
        units, seen = [], set()
        for n, r in enumerate(read(a.units, ["id", "type", "level", "beds", "baths", "status"]), start=2):
            u = {k: (v or "").strip() for k, v in r.items() if k}
            if u["id"] in seen:
                sys.exit("line %d: duplicate unit id %s" % (n, u["id"]))
            seen.add(u["id"])
            for k, f in NUM.items():
                if u.get(k, "") == "":
                    u[k] = None
                    continue
                try:
                    v = f(u[k]); u[k] = int(v) if isinstance(v, float) and v.is_integer() else v
                except ValueError:
                    sys.exit("line %d: %s=%r is not a number" % (n, k, u[k]))
            u.setdefault("typeName", "Type " + u["type"])
            units.append(u)
        out["units"] = units; out["source"]["units"] = a.units
    if a.specs:
        out["specs"] = [{k: (v or "").strip() or None for k, v in r.items() if k} for r in read(a.specs, ["area", "item", "supplier", "code"])]
        out["source"]["specs"] = a.specs
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("// Written by scripts/schedule_to_site.py from the unit and finishes schedules. Do not edit by hand.\n")
        fh.write("window.SCHEDULE = %s;\n" % json.dumps(out, indent=1, ensure_ascii=False))
    print("wrote %s: %d units, %d spec items" % (a.out, len(out.get("units", [])), len(out.get("specs", []))))


if __name__ == "__main__":
    main()
