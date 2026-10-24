"""T-248 extractor: the column / neck inventory of the whole CONC.COLUMN line (values and DXF handles only).

Reads the private copy of Drive "Alsenan chalet project" / 'ST7757 dxf.dxf' (sha256 9f9d1179...) and writes
ALSENAN_COLUMN_INPUT.json: no coordinates, no drawing content. What it does:
  1. re-runs the merged T-217 extractor (research/agents_t217/t217_extract.py) on the Drive copy and asserts that it
     reproduces the committed ALSENAN_SECTION_INPUT.json (the engine-independent member x storey inventory);
  2. binds every T-119 column row (research/agents_t119/COLUMNS_TO_CONTROLLING_MEMBER.csv, merged, Checker-verified
     ids) to its slab-plan outline handle by the outline centre (one to one, <= 0.15 m, same storey frame); this only
     carries the T-119 id and zone flags (annex / tank) onto the handle, no T-119 quantity is used;
  3. reads the footing identity at outline 1B1B (FOUNDATION PLAN): its vertices' extent, whether it is closed, which
     footing tags (TEXT on S-TEXT) and which neck outlines (S-COL.BON) lie inside it.

    python3 -I research/agents_t248/t248_extract.py <path to ST7757 dxf> [--write]
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent
SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
BIND_TOL = 0.15          # m: a T-119 row centre and its slab-plan outline centre (T-119 bound at <= 0.07)
FRAME_X = {"GFRS": (40.5, 74.5), "FFRS": (11.5, 36.0), "SFRS": (-27.0, -2.0)}   # T-119 prep_frames windows (m)
STOREY_SHEET = {"GF": "GFRS", "1F": "FFRS", "2F": "SFRS"}
FOOTING_OUTLINE = "1B1B"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _centre(e):
    pts = [(p[0] / 1000.0, p[1] / 1000.0) for p in e.get_points()]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, pts


def slab_members(sec):
    """(storey, sheet, handle, kind, key) for every storey member of the T-217 inventory."""
    out = []
    for inst in sec["instances"]:
        for st, sh in STOREY_SHEET.items():
            for d in inst["storeys"].get(st, {}).get("drawn", []):
                if d["sheet"] == sh and d["hatch"] == "SOLID":
                    out.append((st, sh, d["handle"], "ON_NECK", inst["fp_outline"]))
    own = {(m["own_outline"]["sheet"], m["own_outline"]["handle"]) for m in sec["members_starting_on_a_slab"]}
    have = {(o[1], o[2]) for o in out}
    for m in sec["members_starting_on_a_slab"]:
        k = (m["own_outline"]["sheet"], m["own_outline"]["handle"])
        if k not in have:
            out.append((m["storey"], k[0], k[1], "PLANTED", m["start_sheet"] + ":" + m["start_handle"]))
    assert len(own) == len(sec["members_starting_on_a_slab"])
    return out


def build(dxf_path: Path) -> dict:
    import ezdxf
    raw = dxf_path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SHA, "not the Drive 'ST7757 dxf.dxf' of the manifest"
    t217 = _load("t217_extract", RESEARCH / "agents_t217" / "t217_extract.py")
    fresh = t217.build(dxf_path)
    committed = json.loads((RESEARCH / "agents_t217" / "ALSENAN_SECTION_INPUT.json").read_text(encoding="utf-8"))
    reproduced = json.dumps(fresh, sort_keys=True) == json.dumps(committed, sort_keys=True)
    assert reproduced, "T-217 inventory does not reproduce from the Drive copy"
    doc = ezdxf.readfile(str(dxf_path))
    db = doc.entitydb
    members = slab_members(committed)
    cen = {}
    for st, sh, h, kind, key in members:
        cx, cy, _ = _centre(db[h])
        cen[(sh, h)] = (st, cx, cy)
    # bind the T-119 rows (merged ids) one to one by centre
    t119 = list(csv.DictReader(open(RESEARCH / "agents_t119" / "COLUMNS_TO_CONTROLLING_MEMBER.csv", encoding="utf-8")))
    pairs = []
    for r in t119:
        sh = STOREY_SHEET[r["storey"]]
        x, y = float(r["x"]), float(r["y"])
        for (s2, h), (st, cx, cy) in cen.items():
            if s2 != sh:
                continue
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            pairs.append((d, r["id"], s2, h))
    pairs.sort()
    bind, used = {}, set()
    for d, rid, sh, h in pairs:
        if rid in bind or (sh, h) in used or d > BIND_TOL:
            continue
        bind[rid] = {"sheet": sh, "handle": h, "d_mm": round(d * 1000)}
        used.add((sh, h))
    t119_zone = {r["id"]: {"hold_cause": r["hold_cause"], "mark": r["mark"]} for r in t119}
    # 4. zone of a neck-only member (no column above, e.g. CN): the GF zone of the column necks around it, accepted
    #    only when its 3 nearest column necks share one zone and it lies outside the extent of every other zone
    annex = {"GFRS:34A", "GFRS:34D", "GFRS:350", "GFRS:353", "GFRS:356"}      # T-119 LEVEL_Q54B, annex roof only
    dual = {"GFRS:35F", "GFRS:365"}                                           # T-119 LEVEL_Q54B on the CB5 line
    fp_zone, fp_pos = {}, {}
    for inst in committed["instances"]:
        cx, cy, _ = _centre(db[inst["fp_outline"]])
        fp_pos[inst["fp_outline"]] = (cx, cy)
        for d in inst["storeys"].get("GF", {}).get("drawn", []):
            k = f"GFRS:{d['handle']}"
            fp_zone[inst["fp_outline"]] = "ANNEX" if k in annex else ("BOUNDARY" if k in dual else "MAIN")
    ext = {}
    for f, z in fp_zone.items():
        x, y = fp_pos[f]
        e = ext.setdefault(z, [x, x, y, y])
        ext[z] = [min(e[0], x), max(e[1], x), min(e[2], y), max(e[3], y)]
    neck_only = {}
    for f in fp_pos:
        if f in fp_zone:
            continue
        x, y = fp_pos[f]
        near = sorted((((x - fp_pos[g][0]) ** 2 + (y - fp_pos[g][1]) ** 2) ** 0.5, fp_zone[g]) for g in fp_zone)[:3]
        zones = {z for _, z in near}
        z = zones.pop() if len(zones) == 1 else None
        outside = z is not None and all(not (e[0] <= x <= e[1] and e[2] <= y <= e[3]) for k, e in ext.items() if k != z)
        neck_only[f] = {"zone": z if outside else "NOT_ESTABLISHED", "nearest_m": [round(d, 2) for d, _ in near],
                        "other_zones_outside": outside}
    bound = {f"{v['sheet']}:{v['handle']}": {"t119_id": k, "bind_mm": v["d_mm"], **t119_zone[k]} for k, v in bind.items()}
    # footing identity at 1B1B
    fo = db[FOOTING_OUTLINE]
    _, _, pts = _centre(fo)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    box = (min(xs), min(ys), max(xs), max(ys))
    inside = lambda x, y: box[0] - 0.001 <= x <= box[2] + 0.001 and box[1] - 0.001 <= y <= box[3] + 0.001
    tags, necks = [], []
    for e in doc.modelspace():
        t = e.dxftype()
        if t == "TEXT" and e.dxf.layer == "S-TEXT":
            s = e.dxf.text.strip()
            if s.startswith("F") and inside(e.dxf.insert.x / 1000, e.dxf.insert.y / 1000):
                tags.append({"handle": e.dxf.handle, "text": s})
        elif t == "LWPOLYLINE" and e.dxf.layer == "S-COL.BON":
            cx, cy, cp = _centre(e)
            if all(inside(px, py) for px, py in cp):
                necks.append({"handle": e.dxf.handle})
    # the open edge of the polyline: the gap between its first and last vertex
    gap = abs(pts[0][0] - pts[-1][0]) + abs(pts[0][1] - pts[-1][1])
    fid = {"outline": FOOTING_OUTLINE, "layer": fo.dxf.layer, "closed": bool(fo.closed),
           "extent_m": [round(box[2] - box[0], 3), round(box[3] - box[1], 3)], "open_gap_m": round(gap, 3),
           "tags_inside": sorted(tags, key=lambda t: t["handle"]),
           "neck_outlines_inside": sorted(n["handle"] for n in necks)}
    return {"schema": "T248_COLUMN_INPUT_V1",
            "source_file": {"ST7757 dxf.dxf": f"sha256 {SHA} (Drive 'Alsenan chalet project')"},
            "t217_inventory_reproduced": reproduced,
            "members": [{"storey": st, "sheet": sh, "handle": h, "kind": kind, "key": key} for st, sh, h, kind, key in members],
            "t119_binding": dict(sorted(bound.items())),
            "t119_unbound": sorted(set(t119_zone) - set(bind)),
            "neck_only_zone": dict(sorted(neck_only.items())),
            "footing_identity": fid}


if __name__ == "__main__":
    out = build(Path(sys.argv[1]))
    if "--write" in sys.argv:
        (HERE / "ALSENAN_COLUMN_INPUT.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"members": len(out["members"]), "bound": len(out["t119_binding"]), "unbound": out["t119_unbound"],
                      "footing": out["footing_identity"]}, indent=0))
