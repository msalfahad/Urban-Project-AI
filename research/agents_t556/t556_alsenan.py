"""T-556 development-villa build: the 11 dry FIN.PLASTER room lines restated to the slab / roof underside with
PLASTER_HEIGHT_METHOD_V1 (R-T556-1). Writes out/T556_PLASTER_HEIGHT.json; --check rebuilds it byte-identical.
Run: python3 -I research/agents_t556/t556_alsenan.py [--check]. Reads only repository files (sha256-pinned)."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t556_inputs as I  # noqa: E402
import t556_plaster_height as M  # noqa: E402

OUT = HERE / "out" / "T556_PLASTER_HEIGHT.json"
PINS = {I.LINE_INDEX: "fed5141ea31bfdd9", I.ROOMS: "696333bc12f0acb9", I.OPENINGS: "4d75de86848509e4",
        I.BEAMS: "368d0fa2d690fb02", I.T552_OUT: "706ff9fde046462b"}
T = Decimal


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def pins():
    for p, h in PINS.items():
        if _sha(p) != h:
            raise M.PlasterHeightError(f"input {p} changed ({_sha(p)} != {h}): restate the inputs")


def parse_opening(room, r):
    """T-292 row -> method opening dict (R-T556-1 d)."""
    ms, oid = r["merged_size"], r["opening_id"]
    op = {"id": oid, "kind": r["kind"], "source": r["merged_source"] or "T-292"}
    m = re.match(r"w ([0-9.]+) sill ([0-9.]+) head ([0-9.]+)$", ms)
    if m:
        op.update(width=m.group(1), sill=m.group(2), head=m.group(3))
        return op
    m = re.match(r"outline ([0-9.]+) m2$", ms)
    if m:
        op.update(area=m.group(1))
        return op
    m = re.search(r"deduction ([0-9.]+) \.\. ([0-9.]+) m2", ms)
    if m:
        op.update(area_range=(m.group(1), m.group(2)))
        return op
    m = re.match(r"w ([0-9.]+) h HELD", ms)
    if m:
        op.update(width=m.group(1))
        if (room, oid) in I.HOLE_HEIGHT:
            assert "h 2.20 DRAWING-CONFIRMED" in r["merged_source"], r
            op["height"] = I.HOLE_HEIGHT[(room, oid)]
        return op
    raise M.PlasterHeightError(f"{room} {oid}: size {ms!r} not parsed")


def g1_deduction(r):
    """the candidate's (paint-height) deduction of one opening, for the reproduction check."""
    v = r["owner_ded_new_m2"]
    if "HELD" in v:
        lo, hi = re.findall(r"\d+(?:\.\d+)?", v)[:2]
        return T(lo), T(hi)
    return T(v), T(v)


def build():
    pins()
    lines = {ln["line_id"][:10]: ln for ln in json.loads((ROOT / I.LINE_INDEX).read_text())["lines"]
             if ln["item_code"] == "FIN.PLASTER"}
    rooms = {r["ROW"]: r for r in csv.DictReader(open(ROOT / I.ROOMS, newline=""))}
    ops = {}
    for r in csv.DictReader(open(ROOT / I.OPENINGS, newline="")):
        if r["room"] in I.LINES:
            ops.setdefault(r["room"], []).append(r)
    t552 = {x["room"]: x for x in json.loads((ROOT / I.T552_OUT).read_text())["q72_dry_plaster_height"]["rows"]}
    slab, slab_src = I.SLAB
    rows = []
    tot = {"old": [T(0), T(0)], "t552": [T(0), T(0)], "new": [T(0), T(0)]}
    released_old = released_new_lo = released_new_hi = T(0)
    for room, (lid, zone) in I.LINES.items():
        ln, rr = lines[lid], rooms[room]
        iv, iv_src, roof_el = I.ZONES[zone]
        face, share, g1 = T(rr["FACE_M"]), T(rr["UNDER_ROOF_SHARE"]), T(rr["OWNER_H_M"])
        open_sides = T(rr["OPEN_SIDES_M"])
        if zone in I.NO_FLOOR_ABOVE and share != 1:
            raise M.PlasterHeightError(f"{room}: zone {zone} has no floor above, roof share {share}")
        H_floor = None
        if share < 1:
            H_floor = M.plaster_height(basis="SLAB_OR_ROOF_UNDERSIDE", interval=iv, interval_src=iv_src, slab=slab,
                                       slab_src=slab_src, buildup=I.FLOOR_BUILDUP[0], buildup_src=I.FLOOR_BUILDUP[1])
        H_roof = None
        if share > 0:
            H_roof = M.plaster_height(basis="SLAB_OR_ROOF_UNDERSIDE", interval=iv, interval_src=iv_src, slab=slab,
                                      slab_src=slab_src, buildup=I.ROOF_SCENARIO[0], buildup_src=I.ROOF_SCENARIO[1],
                                      segment="ROOF")
        mops = [parse_opening(room, r) for r in ops.get(room, []) if r["kind"] != "virtual"]
        # reproduction at the paint height (the candidate's own basis): face x G1 - T-292 deductions
        dg = [g1_deduction(r) for r in ops.get(room, []) if r["kind"] != "virtual"]
        g1_lo = face * g1 - sum((d[1] for d in dg), T(0))
        g1_hi = face * g1 - sum((d[0] for d in dg), T(0))
        if ln["class"] == "RELEASED":
            old = (T(str(ln["measured_net"])),) * 2
            assert g1_lo == g1_hi and abs(g1_lo - old[0]) < T("0.0001"), (room, g1_lo, old)
            reproduced = "EXACT (face x G1 - T-292 = the released line, < 0.0001 m2)"
        elif ln["held_low"] is not None:
            old = (T(str(ln["held_low"])), T(str(ln["held_high"])))
            reproduced = f"line HELD range kept as the old value; T-292 at G1 gives {g1_lo} .. {g1_hi}"
        else:
            old = None
            reproduced = f"line HELD blank (no range); T-292 at G1 gives {g1_lo} .. {g1_hi}"
        beams = [{"mark": mk, "width": w, "depth": d, "slab": slab, "ends": 2 if open_sides == 0 else (0, 2)}
                 for mk, w, d in I.BEAM_ENDS.get(room, [])]
        res = M.restate_line(face_lm=face, roof_share=share, H_floor=H_floor, H_roof_scenario=H_roof,
                             openings=mops, beams=beams)
        lo, hi = T(res["net_lo"]), T(res["net_hi"])
        # W03-type check: openings whose head lies above the paint height G1 (missed by face x (H - G1))
        above_g1 = [o["id"] for o in mops if o.get("head") and T(o["head"]) > g1]
        status = []
        if share > 0:
            status.append(f"HELD on the roof build-up over {res['face_roof_lm']} lm ({roof_el}; D-39 / DCR-6): value at "
                          "the DRAWN-SECTION SCENARIO, ESTIMATED, no lower bound printed")
        if share < 1:
            status.append(f"floor part {res['face_floor_lm']} lm at H {H_floor} DRAWING-CONFIRMED height (T-214 b, "
                          "slab 0.16)")
        if lo != hi:
            status.append("BOUNDED by openings without an established height and / or beam-end counts")
        t5 = t552[room]
        rows.append({
            "room": room, "line_id": ln["line_id"], "candidate_class": ln["class"], "zone": zone,
            "face_lm": str(face), "roof_share": str(share), "open_sides_lm": str(open_sides),
            "old_paint_height_basis": {"G1_m": str(g1), "value": None if old is None else [str(old[0]), str(old[1])],
                                       "reproduction": reproduced},
            "t552_restated": t5["corrected_net"],
            "H_floor_m": None if H_floor is None else str(H_floor),
            "H_roof_scenario_m": None if H_roof is None else str(H_roof),
            "new": res, "new_lo": str(lo), "new_hi": str(hi),
            "openings_head_above_G1": above_g1,
            "status": "HELD: " + "; ".join(status),
        })
        if old is not None:
            tot["old"][0] += old[0]
            tot["old"][1] += old[1]
        tot["t552"][0] += T(t5["corrected_net"][0])
        tot["t552"][1] += T(t5["corrected_net"][1])
        tot["new"][0] += lo
        tot["new"][1] += hi
        if ln["class"] == "RELEASED":
            released_old += old[0]
            released_new_lo += lo
            released_new_hi += hi
    return {
        "schema": "URBAN_T556_PLASTER_HEIGHT_V1", "method": "PLASTER_HEIGHT_METHOD_V1 (R-T556-1, research, unwired)",
        "candidate": "ARCH_TAKEOFF_V3.0.58 (V3.0.57 plaster lines)", "inputs_sha256_16": PINS,
        "heights": {"slab": list(I.SLAB), "floor_buildup": list(I.FLOOR_BUILDUP), "roof_scenario": list(I.ROOF_SCENARIO),
                    "zones": {k: list(v) for k, v in I.ZONES.items()}},
        "rows": rows,
        "totals": {k: [str(v[0]), str(v[1])] for k, v in tot.items()},
        "totals_note": "old = candidate values of the 9 lines that carry one (2 HELD blank lines have none); t552 and new "
                       "cover all 11 lines",
        "released_4_lines": {"old": str(released_old), "new": [str(released_new_lo), str(released_new_hi)]},
        "edge_beams": I.EDGE_BEAMS,
        "freelancer_same_rooms": freelancer_pair(rows),
    }


def freelancer_pair(rows):
    """gross to gross on the same 11 rooms (his rows as T-552 mapped them; his opening convention is his net step)."""
    t = json.loads((ROOT / I.T552_OUT).read_text())["internal"]["pairs"]["DRY"]["rooms"]
    his = sum((T(r["his_gross"]) for r in t if r.get("line_id")), T(0))
    eng = sum((T(r["new"]["gross"]) for r in rows), T(0))
    return {"his_gross": str(his), "engine_gross_at_plaster_height": str(eng), "delta": str(eng - his),
            "delta_pct": str(((eng - his) / his * 100).quantize(T("0.1"))),
            "cause": "heights: his flat 3.60 / 3.40 / 3.50 stop below the soffit (4.29 GF, 3.99 1F / 2F, 3.79 annex): "
                     "ENGINE_RIGHT under the owner rule Q-72; lengths ENGINE_RIGHT (T-128 r3 / T-552); roof faces at "
                     "the DRAWN-SECTION SCENARIO"}


def main(argv):
    txt = json.dumps(build(), indent=1, ensure_ascii=True, sort_keys=True) + "\n"
    if "--check" in argv:
        if OUT.read_text() != txt:
            print("T556 output differs")
            return 1
        print("T556 output byte-identical")
        return 0
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(txt)
    print("wrote", OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
