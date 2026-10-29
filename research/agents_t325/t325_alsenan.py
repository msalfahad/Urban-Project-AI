"""T-325 development-villa run: sills and thresholds, every census opening x component once, bound to the candidate
record's line (V3_0_20_BOQ_LINES.json) or NO_LINE. Read only; every output goes to --out. Printed: opening ids, item
codes, line ids, quantities, states (no coordinates, no names).

    python3 -I research/agents_t325/t325_alsenan.py <P7757.dxf> <V3_0_20_BOQ_LINES.json> \
        --floor-areas <run>/ARCH_FLOOR_AREAS.json --rooms <run>/ARCH_ROOMS.json --out <dir>

Committed inputs (merged, Checker-verified): T-249 census (OPENINGS_T249.csv), T-313 reveal ledger (window sill /
threshold depths per side, door width x wall thickness from the head rows) and its every-family search
(FAMILY_SEARCH_T313.csv: census opening -> candidate line), T-237 rooms (door sides), T-240 TO_THRESHOLD records
(external-door sills and lift landings), T-321 roof / terrace outlines (what lies beyond a floor-level window).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RES = ROOT / "research"
for p in (HERE, RES / "agents_t313", RES / "agents_t321"):
    sys.path.insert(0, str(p))

import sills_thresholds as S  # noqa: E402

FAMILIES = ("ARCH.THRESHOLD", "FIN.MARBLE.THRESHOLD", "FIN.FLOOR.PORCELAIN", "ARCH.WINDOW_REVEAL")
WET_WORDS = re.compile(r"\b(w\.?c|bath|wash|basin|kitchen|laundry|ironing)\b", re.I)
# T-240 TO_THRESHOLD records (research/agents_t240/t240_inputs.py, merged): engine opening -> class
T240 = {("GF", "OP-005"): "EXTERIOR_SILL", ("GF", "OP-008"): "EXTERIOR_SILL", ("GF", "OP-009"): "EXTERIOR_SILL",
        ("GF", "OP-013"): "EXTERIOR_SILL", ("GF", "OP-021"): "EXTERIOR_SILL", ("2F", "OP-001"): "EXTERIOR_SILL",
        ("GF", "OP-011"): "LIFT_LANDING", ("1F", "OP-007"): "LIFT_LANDING", ("2F", "OP-002"): "LIFT_LANDING"}


def sha8(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:8]


def read_csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(p, rows):
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def outside_of_windows(plan, inv, room_polys):
    """census window -> 'FLOOR:<zone>' / 'AIR' for the side away from the engine room (T-313 probe 0.30 m beyond the
    face; zones = the T-321 roof / terrace outlines traced from named entities)."""
    import ezdxf
    from shapely import affinity
    from shapely.geometry import Point, Polygon
    import t313_alsenan as T
    import t321_measure as M
    from roof_buildup import outline
    doc = ezdxf.readfile(plan)
    unit = {4: 0.001, 6: 1.0, 5: 0.01}[doc.header.get("$INSUNITS")]
    segs = T.segments(doc, unit)
    by = {}
    for s in segs:
        by.setdefault(s[0], []).append(s)
    zones = {}
    for zid, z in M.ROOFS.items():
        ox, oy = M._x(doc, z["origin"][0]), M._y(doc, z["origin"][1])
        spec = M._spec(doc, z["face_wall"], ox, oy)
        pg = Polygon(outline([tuple(v[:2]) if v[0] != "ARC" else ("ARC", tuple(v[1]), v[2], v[3], v[4]) for v in spec]))
        zones[zid] = affinity.translate(pg, ox * unit, oy * unit)
    out = {}
    for r in inv:
        if r["KIND"] != "WINDOW" or r["ID"] in T.CURVED:
            continue
        g, _why = T.measure_window(r["HANDLES"].split(), by, segs)
        if not g:
            continue
        inroom = {side: any(fl == r["FLOOR"] and pg.contains(Point(g[side])) for fl, pg in room_polys)
                  for side in ("probe_lo", "probe_hi")}
        if sum(inroom.values()) != 1:
            out[r["ID"]] = None                     # the room side is not established: the outside stays HELD
            continue
        far = "probe_hi" if inroom["probe_lo"] else "probe_lo"
        out[r["ID"]] = [z for z, pg in zones.items() if pg.contains(Point(g[far]))]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("lines")
    ap.add_argument("--floor-areas")
    ap.add_argument("--rooms")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    doc = json.loads(Path(a.lines).read_text(encoding="utf-8"))
    lines = doc if isinstance(doc, list) else doc["lines"]
    by_id = {ln["line_id"]: ln for ln in lines}
    inv = read_csv(RES / "agents_t249" / "OPENINGS_T249.csv")
    led = read_csv(RES / "agents_t313" / "REVEAL_LEDGER_T313.csv")
    fam = read_csv(RES / "agents_t313" / "FAMILY_SEARCH_T313.csv")
    depths = {x["opening"]: x for x in read_csv(RES / "agents_t313" / "WINDOW_DEPTHS_T313.csv")}
    rooms237 = {x["room"]: x["room_name"] for x in read_csv(RES / "agents_t237" / "ROOMS_T237.csv")}

    # ---- 1. every line of the four families in the record, tied to a census opening or not
    fam_lines = [ln for ln in lines if ln["item_code"] in FAMILIES and (
        ln["item_code"] != "FIN.FLOOR.PORCELAIN" or "STRIP" in ((ln.get("location") or {}).get("element_id") or ""))]
    census_of_line = {}
    for x in fam:
        if x["item_code"] in FAMILIES:
            census_of_line.setdefault(x["line_id"], set()).add(x["opening"])
    eref, sym_census = {}, {}
    for r in inv:
        for h in (r["HANDLES"] or "").split():
            sym_census[(r["FLOOR"], h.upper())] = r["ID"]
        ref = r["ENGINE_REF"].split(" / ")[-1].split(" ")[0]
        if ref.startswith("OP-"):
            eref[(r["FLOOR"], ref)] = r["ID"]
    line_rows, lines_by_opening = [], {}
    for ln in fam_lines:
        loc = ln.get("location") or {}
        fl = loc.get("floor")
        inp = (ln.get("calculation") or {}).get("inputs") or {}
        ops = inp.get("opening_ids") or ([inp["opening_id"]] if inp.get("opening_id") else [])
        if not ops:
            m = re.search(r"(OP-\d{3})", loc.get("element_id") or "")
            ops = [m.group(1)] if m else []
        cen = sorted(census_of_line.get(ln["line_id"], ()))
        if not cen:
            cen = sorted({eref[(fl, o)] for o in ops if (fl, o) in eref})
        how = "T-313 family search" if census_of_line.get(ln["line_id"]) else ("engine opening id" if cen else "")
        if not cen:                      # a door-closure strip: 'CLOSURE|D2:<decimal handle>|...' names the door symbol
            for c in inp.get("door_closures") or []:
                m = re.match(r"CLOSURE\|D2:(\d+)", c)
                if m and (fl, format(int(m.group(1)), "X")) in sym_census:
                    cen = [sym_census[(fl, format(int(m.group(1)), "X"))]]
                    how = f"door symbol handle {format(int(m.group(1)), 'X')} (closure {c.split('|')[1]})"
        br = ln.get("bounded_range") or {}
        rng = (br.get("low"), br.get("high")) if isinstance(br, dict) else (None, None)
        if isinstance(ln.get("bounded_range"), (list, tuple)):
            rng = tuple(ln["bounded_range"][:2])
        row = {"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": fl,
               "element": loc.get("element_id"), "engine_openings": ";".join(ops),
               "census": ";".join(cen) if cen else "NOT_IN_CENSUS",
               "t240_class": ";".join(sorted({T240[(fl, o)] for o in ops if (fl, o) in T240})),
               "evidence_state": ln["evidence_state"], "measured_net": ln.get("measured_net"),
               "low": rng[0], "high": rng[1], "length_m": inp.get("length_m") or inp.get("opening_width_m"),
               "depth_m": inp.get("depth_m") or inp.get("wall_t_m"), "strip_m2": inp.get("measured_strip_m2"),
               "geometry_verified": inp.get("geometry_verified"), "census_by": how,
               "rfi": ((ln.get("rfi") or {}).get("question") or "")[:60], "physical_element": ln.get("physical_element")}
        line_rows.append(row)
        for c in cen:
            lines_by_opening.setdefault(c, []).append((ln["item_code"], ln["line_id"]))

    # ---- 2. the ledger: every census opening x component once
    from shapely.geometry import Polygon as _P
    rm_all = json.loads(Path(a.rooms).read_text(encoding="utf-8"))["rooms"] if a.rooms else []
    outside = outside_of_windows(a.plan, inv, [(r["floor"], _P(r["polygon_m"]).buffer(0)) for r in rm_all
                                               if r.get("polygon_m")])
    ops = []
    head = {x["opening"]: x for x in led if x["component"] == "HEAD" and x["kind"] in ("DOOR", "GATE", "ARCH")}
    sillrows = {(x["opening"], x["side"], x["component"]): x for x in led if x["component"] in ("SILL", "THRESHOLD")}
    for r in inv:
        oid, kind, fl = r["ID"], r["KIND"], r["FLOOR"]
        if kind == "WINDOW":
            out_row = sillrows.get((oid, "OUT", "SILL")) or sillrows.get((oid, "OUT", "THRESHOLD"))
            in_row = sillrows.get((oid, "IN", "SILL"))
            fg = out_row is not None and out_row["component"] == "THRESHOLD"
            d = depths.get(oid, {})
            w = None
            if out_row and num(out_row["depth_m"]) and num(out_row["m2"]) is not None:
                w = round(num(out_row["m2"]) / num(out_row["depth_m"]), 6)
            if w is None:
                w = num(d.get("width_symbol_m")) if oid not in ("W03", "W17") else None
            op = {"id": oid, "kind": "FLOOR_GLAZING" if fg else "WINDOW", "floor": fl, "width_m": w,
                  "depth_in_m": num(d.get("depth_in_m")) if (in_row or fg) and oid not in ("W03", "W17") else None,
                  "depth_out_m": num(out_row["depth_m"]) if out_row and out_row["state"] == "MEASURED" else None}
            if fg:
                far = outside.get(oid)          # None: room side not established -> outside HELD
                if far is not None:
                    op["outside"] = "FLOOR" if far else "AIR"
                    op["outside_zone"] = ";".join(far) if far else "none (outside air)"
            ops.append(op)
        elif kind in ("DOOR", "GATE", "OPENING"):
            h = head.get(oid)
            w = num(h["ml"]) if h else None
            t = num(h["depth_m"]) if h else None
            wsrc = "T-313 head row (T-237 width x T-150 wall)" if w is not None else ""
            if w is None:                     # arch / gate: the width only where a candidate strip line measured it
                for f, lid in lines_by_opening.get(oid, ()):
                    lr = next(l for l in line_rows if l["line_id"] == lid)
                    if num(lr["length_m"]) and num(lr["depth_m"]):
                        w, t, wsrc = num(lr["length_m"]), num(lr["depth_m"]), f"strip line {lid} inputs"
                        break
            rms = (h["room"] if h else "") or ""
            names = [rooms237.get(x, "") for x in rms.split(";") if x]
            ref = r["ENGINE_REF"].split(" / ")[-1].split(" ")[0]
            cls = T240.get((fl, ref))
            fams = {f for f, _ in lines_by_opening.get(oid, ())}
            wet = "FIN.MARBLE.THRESHOLD" in fams or (not fams - {"ARCH.THRESHOLD"} and
                                                     any(WET_WORDS.search(n) for n in names))
            ops.append({"id": oid, "kind": "ARCH" if kind == "OPENING" else "DOOR", "floor": fl,
                        "clear_width_m": w, "wall_t_m": t, "sides": ["BATHROOM"] if wet else ["DRY"],
                        "external": cls == "EXTERIOR_SILL", "side_names": " | ".join(names),
                        "side_source": ("candidate line family" if fams - {"ARCH.THRESHOLD"} else "T-237 room names")
                        + "; width / depth: " + (wsrc or "not established")})
    rows = S.ledger(ops)
    extra = {o["id"]: o for o in ops}
    for x in rows:
        o = extra[x["opening"]]
        x["outside"] = o.get("outside_zone", "")
        x["side_source"] = o.get("side_source", "")
        x["external"] = o.get("external", "")

    # ---- 3. binding: the component to the one line that carries it
    binding = {}
    for lr in line_rows:
        for c in (lr["census"].split(";") if lr["census"] != "NOT_IN_CENSUS" else []):
            o = extra[c]
            if lr["item_code"] == "ARCH.WINDOW_REVEAL":
                comp = "THRESHOLD_OUT" if o["kind"] == "FLOOR_GLAZING" else "SILL_OUT"
            elif lr["item_code"] == "FIN.FLOOR.PORCELAIN" and lr["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE":
                continue                      # the strip left the porcelain line for its ARCH.THRESHOLD twin (T-240)
            else:
                comp = "THRESHOLD"
            binding[(c, comp)] = lr["line_id"]
    S.bind(rows, binding)
    S.refuse_double(rows, lines_by_opening)

    # ---- 4. per bound line: ledger quantity vs the line's own quantity
    rec = []
    for x in rows:
        if x["binding"] != "BOUND":
            continue
        ln = next(l for l in line_rows if l["line_id"] == x["line_id"])
        q = num(ln["measured_net"])
        lo, hi = num(ln["low"]), num(ln["high"])
        led_m2 = x["m2"]
        if led_m2 is None:
            res, verdict = "", "LEDGER_UNRESOLVED (no number on either side)" if q is None else \
                "LEDGER_UNRESOLVED (the line has a number the ledger cannot confirm)"
        elif q is not None:
            res, verdict = round(led_m2 - q, 6), ("EQUAL" if abs(led_m2 - q) <= 1e-6 else "DIFFERS")
        elif lo is not None and hi is not None:
            res = f"{round(led_m2 - lo, 6)} .. {round(led_m2 - hi, 6)}"
            verdict = "WITHIN_BOUND" if lo - 1e-6 <= led_m2 <= hi + 1e-6 else "OUTSIDE_BOUND"
        elif num(ln.get("strip_m2")) is not None:
            sm = num(ln["strip_m2"])
            res = round(led_m2 - sm, 6)
            verdict = ("LINE_BLANK (no number; the line's own strip polygon %.6f m2, geometry_verified %s, vs the "
                       "ledger clear width x wall t)" % (sm, ln.get("geometry_verified")))
        else:
            res, verdict = "", "LINE_BLANK (the line carries no number; the ledger quantity is its fill)"
        rec.append({"opening": x["opening"], "component": x["component"], "line_id": x["line_id"],
                    "item_code": ln["item_code"], "line_state": ln["evidence_state"], "line_m2": q,
                    "line_low": lo, "line_high": hi, "ledger_m2": led_m2, "ledger_state": x["state"],
                    "material": x["material"], "residual_m2": res, "verdict": verdict})

    # ---- 5. double count against the floor lines: every bound strip polygon vs every room floor polygon
    overlap = []
    if a.floor_areas and a.rooms:
        from shapely.geometry import Polygon
        fa = json.loads(Path(a.floor_areas).read_text(encoding="utf-8"))
        rm = json.loads(Path(a.rooms).read_text(encoding="utf-8"))["rooms"]
        rp = [(r["room_id"], r["floor"], Polygon(r["polygon_m"]).buffer(0)) for r in rm if r.get("polygon_m")]
        strips = []
        for f in fa["floors"] if isinstance(fa["floors"], list) else fa["floors"].values():
            for key in ("strips", "threshold_strips", "unresolved_strips"):
                for s in f.get(key, []) if isinstance(f, dict) else []:
                    strips.append(s)
        if not strips:                              # fall back to a walk of the document
            def walk(o):
                if isinstance(o, dict):
                    if "strip_id" in o and "polygon_m" in o:
                        strips.append(o)
                    for v in o.values():
                        walk(v)
                elif isinstance(o, list):
                    for v in o:
                        walk(v)
            walk(fa)
        seen = set()
        for s in strips:
            if s["strip_id"] in seen or s.get("class") not in ("THRESHOLD", "SILL", "WINDOW_SILL") and \
                    not s.get("opening_ids"):
                continue
            seen.add(s["strip_id"])
            pg = Polygon(s["polygon_m"]).buffer(0)
            ov = sum(p.intersection(pg).area for rid, fl, p in rp if fl == s["floor"])
            overlap.append({"strip_id": s["strip_id"], "floor": s["floor"], "class": s.get("class"),
                            "openings": ";".join(s.get("opening_ids") or []), "strip_m2": round(pg.area, 6),
                            "overlap_with_room_floors_m2": round(ov, 6)})

    # ---- 6. freelancer (committed normalised raw rows, tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json): every
    # row searched for a threshold / sill / marble term; the door-step block of his marble sheet read cell by cell
    raw = json.loads((ROOT / "tests" / "alsenan" / "registers_b1" / "FREELANCER_RAW_ROWS.json").read_text(
        encoding="utf-8"))["rows"]
    term = re.compile("\u0639\u062a\u0628|\u062c\u0644\u0633|threshold|sill", re.I)      # عتب / جلس
    hits = [r for r in raw if term.search(json.dumps(r["cells"], ensure_ascii=False))]
    fl_rows = []
    blk = [r for r in raw if r["file"] == "FIN" and r["row"] in range(35, 42) and r["sheet"].startswith("\u0631\u062e")]
    for r in blk:
        c = r["cells"]
        b, cc, h = (c.get(f"{k}{r['row']}", {}).get("v") for k in ("B", "C", "H"))
        if cc is None:
            continue
        fl_rows.append({"file": "FIN", "sheet": "marble + court", "row": r["row"], "B_count": b, "C_length_m": cc,
                        "H_area_col": h, "H_formula": c.get(f"H{r['row']}", {}).get("f")})
    fl_rows.append({"file": "FIN", "sheet": "all 885 rows", "row": "-", "B_count": None, "C_length_m": None,
                    "H_area_col": None, "H_formula": f"rows naming a threshold / sill term: {len(hits)}"})
    write_csv(out / "FREELANCER_T325.csv", fl_rows)

    # ---- 7. outputs
    write_csv(out / "SILL_THRESHOLD_LEDGER_T325.csv", rows)
    write_csv(out / "LINES_T325.csv", line_rows)
    write_csv(out / "LINE_RECONCILIATION_T325.csv", rec)
    if overlap:
        write_csv(out / "STRIP_FLOOR_OVERLAP_T325.csv", overlap)
    tot = S.totals(rows)
    summary = {
        "inputs": {"plan_sha8": sha8(a.plan), "lines_sha8": sha8(a.lines), "lines": len(lines),
                   "floor_areas_sha8": sha8(a.floor_areas) if a.floor_areas else None,
                   "rooms_sha8": sha8(a.rooms) if a.rooms else None},
        "family_lines": {f: sum(1 for l in fam_lines if l["item_code"] == f) for f in FAMILIES},
        "lines_not_in_census": [l["line_id"] + " " + l["item_code"] + " " + str(l["floor"]) + " " + l["engine_openings"]
                                + " " + l["t240_class"] + " " + l["evidence_state"] for l in line_rows
                                if l["census"] == "NOT_IN_CENSUS"],
        "census_openings": len(ops), "ledger_rows": len(rows),
        "bound": sum(1 for x in rows if x["binding"] == "BOUND"),
        "no_line": sorted(f"{x['opening']} {x['component']} {x['state']} {x['m2']}" for x in rows
                          if x["binding"] == "UNBOUND" and x["state"] in ("MEASURED", "HELD", "UNRESOLVED")),
        "verdicts": {v: sum(1 for x in rec if x["verdict"].startswith(v)) for v in
                     ("EQUAL", "DIFFERS", "WITHIN_BOUND", "OUTSIDE_BOUND", "LINE_BLANK")},
        "max_strip_floor_overlap_m2": max((o["overlap_with_room_floors_m2"] for o in overlap), default=None),
        "freelancer": {"door_step_rows": len(fl_rows) - 1,
                       "door_step_length_sum_m": round(math.fsum(x["C_length_m"] for x in fl_rows[:-1]), 6),
                       "threshold_or_sill_rows": len(hits)},
        "totals": tot}
    (out / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
