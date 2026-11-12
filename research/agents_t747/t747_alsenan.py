"""T-747 (development villa; method R-T747-1 .. -3 every villa): exterior paint faces by the owner paint rule, per
facade side and storey, from the T-314 r2 render stage faces (pinned in in/T314_FACES_T747.json) on the candidate of
record ARCH_TAKEOFF_V3.0.75. Research only: no candidate line, hub, registry or rule / knowledge version file moves.

    python3 -I research/agents_t747/t747_alsenan.py [--write | --check]

Inputs (sha256 pinned in the output): the stage faces / holes (t747_extract_faces.py), the T-737 stage pin (line
figures), LINE_INDEX_V3_0_75 (fence and FIN.EXT / FIN.PAINT census), the T-746 edge output (window OUT rows, door
return rows), the T-737 bead re-binding (rings and corners by host line), the T-405 arched-head outlines.
Drawing evidence read in this run from the private decode (P7757.dxf sha256 ab54dd55; architectural sheets 6-9
elevations): recorded below as handles, counts and areas only.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t747_rules as R  # noqa: E402

SCHEMA = "URBAN_T747_EXT_PAINT_V1"
CANDIDATE = "ARCH_TAKEOFF_V3.0.75"
FACES = "research/agents_t747/in/T314_FACES_T747.json"
STAGE = "research/agents_t737/in/T314_STAGE_T737.json"
IDX = "research/agents_t729/out/LINE_INDEX_V3_0_75.json"
T746 = "research/agents_t746/out/T746_PAINT_EDGES.json"
T737 = "research/agents_t737/out/T737_ROWS.csv"
T405 = "research/agents_t405/EDGE_LEDGER_T405.csv"
PINS = [FACES, STAGE, IDX, T746, T737, T405]
OUT_JSON = HERE / "out" / "T747_EXT_PAINT.json"
OUT_CSV = HERE / "out" / "T747_FACES.csv"

# ---- drawing evidence (this run, private decode; no drawing content copied) ------------------------------------------
DXF_SHA16 = "ab54dd55"
ELEVATION_CENSUS = {
    "sheets": "architectural PDF p.6 SOUTH EAST, p.7 SOUTH WEST, p.8 NORTH WEST, p.9 NORTH EAST (single sheet 09) "
              "ELEVATION 1:100; DXF titles SOUTH EAST / NORTH WEST ELEVATION (handles 24DB, 2A69)",
    "dxf_text_entities": 177, "dxf_finish_words": 0,
    "finish_words_searched": "clad / stone / marble / granite / ceramic / tile / plaster / paint / sigma / coat / "
                             "finish and their Arabic equivalents",
    "material_hatch_on_facade_faces": 0,
    "se_hatches": "1C01 annex roof section, 23DE ground slab section, 23E3 section block, 23E7 AR-PARQ1 ground: "
                  "sections / ground, none on a facade face",
    "drawn_distinct_surfaces": 1,
    "verdict": "no facade face is printed as clad or tiled on any elevation: deduction CLAD / TILED = 0 by the "
               "drawing; one distinct surface is drawn (the SE entrance stone surround), material printed nowhere",
}
# the SE entrance surround: quoin + voussoir outlines, layer '1' LINEs (119 in the window x -279800 .. -277300,
# y -805300 .. -800800 mm), 1C02 .. 2413; levels from +-0.00 at y -805246 (level block 2439; +0.30 / +4.30 markers
# 244A / 244C 4,000 mm apart); +1.00 = the landing line 1BFE and the D-GF-07 sill (door line 1C00 +1.00 .. +3.50)
SURROUND = {
    "handles": "layer '1' LINE 1CA6 .. 1CF0, 23AE .. 2402 (+ 1C58 .. 1C63 annex coping arc excluded by area)",
    "levels": "+0.15 .. +4.36 (stone bottom on the +0.15 landing, arch crown +4.36)",
    "stones_only_m2": "1.154674", "zone_m2": "1.298383",
    "zone_plinth_m2": "0.222500", "zone_storey_m2": "1.075883",
    "why_zone": "stones + the three wedges between the voussoirs and the drawn intrados (closed at 1 mm snap); "
                "stones alone 1.154674 (0.1 mm snap); split at +1.00 (plinth band 0.15 .. 1.00 / storey 1.00 ..)",
    "faces": {"GF/SE-2/COVERED/plinth": "0.222500", "GF/SE-2/COVERED/storey": "1.075883"},
    "attribution": "the face that holds D-GF-07 (sill +1.00, head +3.50 = the door the surround frames); "
                   "the Checker confirms the face by handle",
}


def _p(rel):
    return ROOT / rel


def sha(rel):
    return hashlib.sha256(_p(rel).read_bytes()).hexdigest()


def jload(rel):
    return json.loads(_p(rel).read_text(encoding="utf-8"))


def rows(rel):
    with open(_p(rel), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def s6(x):
    return None if x is None else str(R.q6(x))


def pair(p):
    return None if p is None else [str(p[0]), str(p[1])]


# ---- render faces, net of their holes ---------------------------------------------------------------------------------
def render_faces(fx):
    holes = defaultdict(list)
    for o in fx["openings"]:
        holes[o["face_id"]].append(o)
    out = []
    for f in fx["faces"]:
        hs = holes.get(f["face_id"], [])
        if f["lo"] is None:
            if hs:
                raise R.RuleError(f"{f['face_id']}: blank face holds a hole")
            out.append(dict(f, holes=[], render=None))
            continue
        fixed = sum((R.D(h["hole_m2"]) for h in hs if h["hole_m2"] is not None), Decimal(0))
        cap = sum((R.D(h["cap_m2"]) for h in hs if h["hole_m2"] is None), Decimal(0))
        lo = R.D(f["lo"]) - fixed - cap
        hi = R.D(f["hi"]) - fixed
        if lo < 0:
            raise R.RuleError(f"{f['face_id']}: holes larger than the face")
        out.append(dict(f, holes=[h["opening_id"] for h in hs], render=(lo, hi), fixed=fixed, cap=cap))
    return out


def side_of(face_id):
    p = face_id.split("/")
    if len(p) < 4:                       # PARAPET_INNER/ANNEX, PARAPET_TOP/GF: roof-level items, no side
        return "ROOF " + p[-1]
    s = p[1]
    return s.split("-")[0] if s[:2] in ("SE", "SW", "NE", "NW") else s


def floor_of(face_id, lines):
    return lines[face_id]


def paint_all(fx):
    ln = {x["key"]: x for x in fx["lines"]}
    rf = render_faces(fx)
    res = []
    for f in rf:
        ded = []
        z = SURROUND["faces"].get(f["face_id"])
        if z is not None:
            ded.append({"kind": "NOT_PRINTED_FINISH", "m2": z,
                        "why": f"SE entrance stone surround drawn (DXF {DXF_SHA16} {SURROUND['handles']}), material "
                               "printed nowhere: paint low end - zone"})
        p = R.paint_face(f["face_id"], f["element"], f["render"], deductions=ded)
        line = ln[f["line"]]
        p.update(line_key=f["line"], line_id=line["line_id"], floor=line["floor"], side=side_of(f["face_id"]),
                 face_status=f["status"], holes=f["holes"], bottom=f["bottom"], top=f["top"])
        res.append(p)
    return res


def line_rollup(fx, faces, stage):
    pin = {r["line_key"]: r for r in stage["rows"]}
    out = []
    for x in fx["lines"]:
        fs = [f for f in faces if f["line_key"] == x["key"]]
        r = R.roll_up(fs)
        st = pin[x["key"]]
        # assert the render roll-up equals the stage line figure (net) exactly (6 dp)
        stage_net = st["net"]
        got = r["render"]
        if stage_net is None:
            ok = r["state"] in ("BLANK", "BLANK_PART")      # R-T314-1 (4): a blank face makes the line blank
        else:
            ok = r["state"] not in ("BLANK", "BLANK_PART") and [str(got[0]), str(got[1])] == [s6(stage_net[0]), s6(stage_net[1])]
        if not ok:
            raise R.RuleError(f"{x['key']}: render faces {got} != stage net {stage_net}")
        out.append({"line_key": x["key"], "line_id": st["line_id"], "element": x["element"], "floor": x["floor"],
                    "element_id": st["element_id"], "stage_after": st["after"], "faces": r["faces"],
                    "blank_faces": r["blank_faces"], "state": r["state"], "render_m2": pair(r["render"]),
                    "paint_m2": pair(r["paint"]), "deducted_m2": pair(r["deducted"]),
                    "residual_m2": pair(r["residual"]), "render_equals_stage": True,
                    "line_paint": (None if r["state"] in ("BLANK", "BLANK_PART") else pair(r["paint"])),
                    "paint_state": ("blank (HELD, never 0)" if r["state"] in ("BLANK", "BLANK_PART") else
                                    st["after"]["state"] if r["deducted"] == (R.q6(0), R.q6(0))
                                    else "BOUNDED_EXPOSURE")})
    return out


def side_table(faces):
    g = defaultdict(list)
    for f in faces:
        g[(f["floor"], f["side"], f["element"])].append(f)
    out = []
    for (fl, sd, el), fs in sorted(g.items()):
        r = R.roll_up(fs)
        out.append({"floor": fl, "side": sd, "element": el, "faces": r["faces"], "blank_faces": r["blank_faces"],
                    "state": r["state"], "render_m2": pair(r["render"]), "paint_m2": pair(r["paint"]),
                    "deducted_m2": pair(r["deducted"]), "residual_m2": pair(r["residual"])})
    return out


def totals(faces, key=None):
    g = defaultdict(list)
    for f in faces:
        g[key(f) if key else "ALL"].append(f)
    return {k: {kk: (pair(v) if isinstance(v, tuple) else v) for kk, v in R.roll_up(fs).items()}
            for k, fs in sorted(g.items())}


# ---- R-T747-3 edges -------------------------------------------------------------------------------------------------
def edges(fx):
    t746 = jload(T746)
    wo = {r["opening"]: r for r in t746["window_rows"] if r["side"] == "OUT"}
    dr = {r["opening"]: r for r in t746["return_rows"]}
    ring = {r["id"].split("#")[0]: r for r in rows(T737) if r["kind"] == "BEAD" and
            r["bead_class"] in ("WINDOW_JAMB_HEAD", "DOOR_JAMB_HEAD")}
    arched = {r["edge_id"].split("#")[0]: r for r in rows(T405)
              if r["basis"] == "ARC_DEVELOPED" and r["edge_id"].endswith("#OUT")}
    out, seen = [], set()
    for o in fx["openings"]:
        oid = o["opening_id"]
        if oid.startswith("W03 (frame end"):
            out.append({"opening": oid, "face_id": o["face_id"], "lm": None, "state": "PART_OF",
                        "source": "W03", "basis": None, "others": [],
                        "why": "frame-end part of W03 on a neighbour face: its edge is W03's (one opening, once)"})
            continue
        if oid in seen:
            raise R.RuleError(f"{oid}: opening twice")
        seen.add(oid)
        src = {}
        rg = ring.get(oid)
        if oid.startswith("W"):
            w = wo.get(oid)
            if w is not None:
                src["T-746 window OUT"] = {"lm": None if w["edge_lm"] is None else tuple(w["edge_lm"]),
                                           "basis": "RECTANGLE"}
            if oid in arched:
                v = arched[oid]["dwg_m"]
                if rg is None or R.D(rg["value"] or rg["high"]) != R.D(v):
                    raise R.RuleError(f"{oid}: T-405 developed outline {v} != T-737 ring")
                src["T-405 / T-737 ring"] = {"lm": (v, v), "basis": "ARC_DEVELOPED"}
            elif rg is not None and (rg["value"] or rg["high"]):
                v = rg["value"] or rg["high"]
                src["T-737 ring"] = {"lm": (v, v), "basis": "RECTANGLE"}
            elif rg is not None:
                src["T-737 ring"] = {"lm": None, "basis": "RECTANGLE"}
        else:
            d = dr.get(oid)
            if d is not None:
                src["T-746 door return"] = {"lm": tuple(d["edge_lm_after_B"]) if d.get("edge_lm_after_B") else None,
                                            "basis": "DRAWN_FRAME"}
            if rg is not None:
                v = rg["value"] or rg["high"]
                src["T-737 ring"] = {"lm": (v, v) if v else None, "basis": "RECTANGLE"}
        e = R.opening_edge(oid, src)
        e["face_id"] = o["face_id"]
        e["kind"] = "WINDOW" if oid.startswith("W") else "DOOR"
        e["lm"] = pair(e["lm"])
        for x in e["others"]:
            x["lm"], x["diff"] = pair(x["lm"]), pair(x["diff"])
        e["why"] = ("arched head: developed outline governs the rectangle (T-405 ARCHED, Checker-merged)"
                    if e["basis"] == "ARC_DEVELOPED" else
                    "door: frame posts drawn over the full wall depth at the jambs (T-746): jambs 0, head 0 .. w; "
                    "already inside T-746's door edge total, cited, never added again" if e["basis"] == "DRAWN_FRAME"
                    else "window outside jambs + head (T-313 / T-746); sill / threshold are their own item")
        out.append(e)
    win = [e for e in out if e.get("kind") == "WINDOW" and e["state"] != "PART_OF"]
    door = [e for e in out if e.get("kind") == "DOOR"]

    def _s(es):
        lo = hi = Decimal(0)
        held = []
        for e in es:
            if e["lm"] is None:
                held.append(e["opening"])
                continue
            lo += R.D(e["lm"][0])
            hi += R.D(e["lm"][1])
        return {"lm": [s6(lo), s6(hi)], "held": held, "count": len(es)}

    ws, ds = _s(win), _s(door)
    t746_facade = sum((R.D(wo[e["opening"]]["edge_lm"][0]) for e in win
                       if wo.get(e["opening"]) and wo[e["opening"]]["edge_lm"]), Decimal(0))
    t746_all = R.D(t746["windows"]["outside_edge_lm"][0])
    not_facade = sorted(k for k, r in wo.items() if k not in seen and r["status"] == "PAINT_LM")
    arched_diff = sum((R.D(x["diff"][0]) for e in win for x in e["others"]
                       if e["basis"] == "ARC_DEVELOPED" and x["diff"]), Decimal(0))
    recon = {
        "t746_outside_edge_lm_all": s6(t746_all),
        "t746_on_facade_openings": s6(t746_facade),
        "t746_windows_not_on_a_facade_face": not_facade,
        "t746_not_on_facade_lm": s6(t746_all - t746_facade),
        "arched_rectangle_over_developed": s6(arched_diff),
        "governing_window_edge_lm": ws["lm"][0],
        "check": s6(t746_facade - arched_diff - R.D(ws["lm"][0])),
    }
    if R.D(recon["check"]) != 0:
        raise R.RuleError(f"window edge reconciliation residual {recon['check']}")
    return out, {"windows": ws, "doors": ds, "reconciliation": recon}


def corners():
    out = defaultdict(lambda: {"point_lm": Decimal(0), "low_lm": Decimal(0), "high_lm": Decimal(0), "rows": [],
                               "no_host_lm_text": []})
    for r in rows(T737):
        if r["kind"] != "BEAD" or r["bead_class"] not in ("EXTERNAL_CORNER", "MOUTH_WALL_END"):
            continue
        h = r["host_after"]
        g = out[h]
        g["rows"].append(f"{r['id']} {r['bead_class']} {r['bead_state_after']}")
        if r["bead_state_after"] == "HELD_BLANK":
            g["no_host_lm_text"].append(f"{r['id']} {r['part_m']} m (reference text, not a quantity)")
            continue
        if r["value"]:
            g["point_lm"] += R.D(r["value"])
            g["low_lm"] += R.D(r["value"])
            g["high_lm"] += R.D(r["value"])
        else:
            g["low_lm"] += R.D(r["low"])
            g["high_lm"] += R.D(r["high"])
    res = {}
    tlo = thi = Decimal(0)
    for h, g in sorted(out.items()):
        res[h] = {"lm": [s6(g["low_lm"]), s6(g["high_lm"])], "rows": g["rows"], "no_host": g["no_host_lm_text"]}
        tlo += g["low_lm"]
        thi += g["high_lm"]
    return {"by_host": res, "total_lm": [s6(tlo), s6(thi)],
            "basis": "T-737 re-binding of the T-697 exterior arrises (vertical convex corners, mouths, stop-ends, "
                     "plinth): one arris = one corner lm, the same arrises as the B4-09 beads (arris once)",
            "not_restated": "horizontal arrises (parapet top edges, slab edges, copings) are in T-337 FILL_ITEMS "
                            "FIN.EXT.CORNERS 710.171878 .. 821.858800 m.l (stage missing item, HELD bounded): "
                            "cited, not restated here"}


def fence_census(idx):
    fence = [ln for ln in idx["lines"] if ln["item_code"] in ("EXT.FENCE.PAINT", "EXT.FENCE.PLASTER")]
    ext_paint = [ln for ln in idx["lines"] if ln["item_code"].startswith("FIN.PAINT") and
                 any(k in ln["element_id"].upper() for k in ("FACADE", "EXT"))]
    fin_ext = [ln for ln in idx["lines"] if ln["item_code"] == "FIN.EXT.FINISH"]
    return {
        "fence_pairs": sorted(f"{ln['line_id']} {ln['item_code']} {ln['element_id']} {ln['class']} "
                              f"{ln['measured_net'] if ln['measured_net'] is not None else 'blank'}" for ln in fence),
        "fence_lines": len(fence),
        "fence_verdict": "REFUSED here (R-T747-1 rule 3, Q-65): boundary wall faces have their own EXT.FENCE.* "
                         "plaster / paint pairs; none is a facade face; unchanged",
        "facade_paint_lines_now": len(ext_paint),
        "fin_ext_finish_lines_now": sorted(f"{ln['line_id']} {ln['element_id']} {ln['class']}" for ln in fin_ext),
    }


def build():
    fx = jload(FACES)
    stage = jload(STAGE)
    idx = jload(IDX)
    if idx.get("candidate_version") != CANDIDATE:
        raise R.RuleError(f"index is {idx.get('candidate_version')}")
    faces = paint_all(fx)
    lines = line_rollup(fx, faces, stage)
    ed, ed_sum = edges(fx)
    rec = {
        "schema": SCHEMA, "rules": list(R.RULE_IDS), "version": R.VERSION, "owner_rule": R.OWNER_RULE,
        "candidate": CANDIDATE, "pins": {p: sha(p)[:16] for p in PINS},
        "stage": fx["stage"], "evidence": {"elevations": ELEVATION_CENSUS, "surround": SURROUND},
        "index_census": fence_census(idx),
        "lines": lines, "sides": side_table(faces),
        "by_floor": totals(faces, key=lambda f: f["floor"]),
        "by_element": totals(faces, key=lambda f: f["element"]),
        "total": totals(faces)["ALL"],
        "faces": [{k: (pair(v) if isinstance(v, tuple) else v) for k, v in f.items()
                   if k not in ("deductions",)} | {"deductions": [{"kind": d["kind"], "m2": str(d["m2"])}
                                                                  for d in f["deductions"]]} for f in faces],
        "edges": {"openings": ed, "summary": ed_sum, "corners": corners()},
    }
    return rec


CSV_COLS = ["face_id", "line_key", "line_id", "floor", "side", "element", "face_status", "holes", "render_lo",
            "render_hi", "deduction", "paint_lo", "paint_hi", "state"]


def to_csv(d):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_COLS, lineterminator="\n")
    w.writeheader()
    for f in d["faces"]:
        w.writerow({"face_id": f["face_id"], "line_key": f["line_key"], "line_id": f["line_id"] or "NEW",
                    "floor": f["floor"], "side": f["side"], "element": f["element"], "face_status": f["face_status"],
                    "holes": ";".join(f["holes"]),
                    "render_lo": f["render"][0] if f["render"] else "", "render_hi": f["render"][1] if f["render"] else "",
                    "deduction": ";".join(f"{x['kind']} {x['m2']}" for x in f["deductions"]),
                    "paint_lo": f["paint"][0] if f["paint"] else "", "paint_hi": f["paint"][1] if f["paint"] else "",
                    "state": f["state"]})
    return buf.getvalue()


def main(argv):
    d = build()
    js = json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    cs = to_csv(d)
    if "--write" in argv:
        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(js, encoding="utf-8")
        OUT_CSV.write_text(cs, encoding="utf-8")
        print("T747 outputs written")
    elif "--check" in argv:
        ok = OUT_JSON.read_text(encoding="utf-8") == js and OUT_CSV.read_text(encoding="utf-8") == cs
        print("T747 outputs AGREE" if ok else "T747 outputs DIFFER")
        return 0 if ok else 1
    print(json.dumps({"total": d["total"], "by_floor": d["by_floor"], "edges": d["edges"]["summary"],
                      "corners": d["edges"]["corners"]["total_lm"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
