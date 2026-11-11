"""T-721 concrete beams blank: the 12 HELD BLANK STR.CONC.BEAM lines of the candidate of record ARCH_TAKEOFF_V3.0.71,
each given the one-sided AT_LEAST the drawings guarantee (R-T721-1) or kept HELD BLANK with its designer item and its m3
per m of depth (R-T721-2). Research only: nothing wired, released or VERIFIED, no line summed into a released total.

Committed inputs only (no drawing is opened here):
  line index  research/agents_t704/out/LINE_INDEX_V3_0_71.json (V3.0.71 ids, classes, bounds)
  members     research/agents_t660/out/T660_BEAM_LEDGER.json (T-660, MERGED: class, item, drawn width / length, plan area)
  dome bay    research/agents_t160/DOMES_INPUT.json (T-160, MERGED: east ring radii and bay faces, own DXF read)
Printed facts used (own read this run, Drive 'Alsenan chalet project', 'ST7757 dxf.dxf' sha 9f9d1179, private copy only):
  ST p.5 first-floor roof slab: four 'SEE DETAIL' texts 1A1D / 1A1E / 1A1F / 1A20 sit ON the east ring band (circle 649
  r 2.2111, arcs 64A-64D r 2.4111, centre 30.828 / 41.651); no mark on it (Q-61 C(3)).
  ST p.7 'DETAIL OF DOME' (N.I.S.): ring section drawn with top '3%%c16' (1A47), side '2%%c14/20cm' (1A37), bottom
  '3%%c18' (1A4B), links '8%%c8/m' (1A29); bar circles on two shared verticals (x -63185 / -62525: y 29563 bottom,
  30563 / 31563 side, 32973 top; same on the mirrored section x -42074 / -41414); depth DIMENSION 182F text 'AS PER
  ARCH' (scaled 3750 x 0.02 = 0.75 on a not-to-scale detail: no quantity); no cover printed anywhere in the sheet set.
  Arch section B-B (Alsenan_Architectural_P7757_Pages_11-12, p.11) draws both first-floor-roof domes springing from the
  roof line with no ring cut and no depth; elevations p.6 / p.7 / p.8 / p.9 and section A-A (sheet 10) print the dome
  441 x 215 only.

    python3 -I research/agents_t721/t721_alsenan.py [--write]
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import t721_rules as R  # noqa: E402

D = Decimal
INDEX = RES / "agents_t704" / "out" / "LINE_INDEX_V3_0_71.json"
T660 = RES / "agents_t660" / "out" / "T660_BEAM_LEDGER.json"
T160 = RES / "agents_t160" / "DOMES_INPUT.json"
OUT_JSON = HERE / "out" / "T721_LEDGER.json"
OUT_MD = HERE / "out" / "T721_CENSUS.md"

RING_LINE = "L-ab37afa17f2ac5b0efd1"
RING_BARS = {"link_dia": "0.008", "top_dia": "0.016", "side_dia": "0.014", "side_levels": 1, "bottom_dia": "0.018"}
D28 = ("D-28 (east dome-opening ring: no mark; ST p.7 ring depth 'AS PER ARCH'; architect's sections draw no ring) - "
       "AT_LEAST from the printed bar stack, upper end open")
RELEASED_BEAM_M3_NOTE = "released STR.CONC.BEAM lines untouched (this ledger reads, never writes, the candidate)"


def load():
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    assert idx["candidate_version"] == "ARCH_TAKEOFF_V3.0.71", idx["candidate_version"]
    t660 = {b["line_id"]: b for b in json.loads(T660.read_text(encoding="utf-8"))["beams"]}
    dome = [d for d in json.loads(T160.read_text(encoding="utf-8"))["domes"] if d["id"] == "DOME-1F-E"][0]
    return idx, t660, dome


def held_beams(idx):
    return [l for l in idx["lines"] if l["item_code"] == "STR.CONC.BEAM" and l["class"] == "HELD"]


def east_ring_area(dome):
    """In-bay annulus net of the four framing faces (no column in the east bay), exact by shapely at 4096 segments."""
    from shapely.geometry import Point, box
    f = dome["faces"]
    bay = box(-f["W"]["d_m"], -f["S"]["d_m"], f["E"]["d_m"], f["N"]["d_m"])
    ring = Point(0, 0).buffer(dome["r_outer_m"], 4096).difference(Point(0, 0).buffer(dome["r_inner_m"], 4096))
    a = ring.intersection(bay)
    for c in dome.get("columns_rel_m") or []:
        a = a.difference(box(*c))
    return D(str(round(a.area, 7)))


def build():
    idx, t660, dome = load()
    held = held_beams(idx)
    blanks = [l for l in held if l["held_low"] is None and l["held_high"] is None]
    bounded = [l for l in held if l not in blanks]
    assert len(held) == 26 and len(blanks) == 12 and len(bounded) == 14, (len(held), len(blanks))
    lo = sum((D(str(l["held_low"])) for l in bounded), D(0))
    hi = sum((D(str(l["held_high"])) for l in bounded), D(0))
    rows = []
    for l in sorted(blanks, key=lambda x: x["line_id"]):
        m = t660[l["line_id"]]
        assert m["element_id"] == l["element_id"], l["line_id"]
        if l["line_id"] == RING_LINE:
            depth = R.bar_stack_depth(**RING_BARS)
            own = east_ring_area(dome)
            f = R.bar_stack_floor(areas_m2=[m["plan_area_m2"], own], depth=depth)
            st = R.statement(l["line_id"], l["element_id"], "AT_LEAST", at_least=f["at_least"], item=D28)
            st.update({"member": "east dome-opening ring 0.20 wide, in-bay (B25 / CB12 / B6 x2 own the corners)",
                       "basis": "R-T721-1 BAR_STACK", "depth_floor_m": str(depth),
                       "depth_terms": "2 x T8 link + T16 top + T14 side (1 level) + T18 bottom; cover not printed, not added",
                       "plan_area_readings_m2": [m["plan_area_m2"], str(own)], "plan_area_used_m2": str(f["area_min_m2"]),
                       "slab_overlap": "none: the 1F roof slab ledger stops at r_outer (T-160); the opening inside r_inner",
                       "not_adopted": ["0.75 scaled from the N.I.S. detail (inadmissible)",
                                       "0.50 (B4) - no B4 mark on this ring (Q-61 C(3))",
                                       "0.16 roof-slab thickness - no sheet ties the ring depth to the slab",
                                       "0.40 from '/20cm' read as layer pitch - a maximum spacing is no depth"],
                       "before": "blank"})
        else:
            assert m["cls"] == "PROJECTION", m["cls"]
            b = R.projection_blank(item=f"{m['designer_item']} (PROJECTION: no section / mark / bars / material printed)",
                                   area_m2=m["plan_area_m2"])
            st = R.statement(l["line_id"], l["element_id"], "BLANK_NAMED", item=b["item"])
            st.update({"member": f"{m['floor']} edge projection {m['drawn_width_m']} x {m['f2f_length_m']} m"
                                 f"{' (edges ' + m['edge_handles'] + ')' if m['edge_handles'] else ''}",
                       "basis": "R-T721-2 / R-T660-3", "m3_per_m_depth": b["m3_per_m_depth"], "guard": b["guard"],
                       "set_aside_not_drawn": m["trial_range_beside_not_drawn"], "before": "blank"})
        rows.append(st)
    floors = [D(r["at_least_m3"]) for r in rows if r["bound"] == "AT_LEAST"]
    census = {"lines": len(rows), "AT_LEAST": len(floors), "BLANK_NAMED": sum(r["bound"] == "BLANK_NAMED" for r in rows),
              "zero": sum(1 for r in rows if r["at_least_m3"] in ("0", "0.000000")),
              "ranges": sum(1 for r in rows if r["at_most_m3"] is not None),
              "at_least_sum_beside_m3": str(sum(floors, D(0))),
              "blank_plan_m2": str(sum((D(r["m3_per_m_depth"]) for r in rows if r["bound"] == "BLANK_NAMED"), D(0))),
              "bounded_untouched": {"lines": len(bounded), "low_m3": str(lo), "high_m3": str(hi)}}
    return {"schema": "T721_LEDGER_V1", "candidate": "ARCH_TAKEOFF_V3.0.71", "rules": R.RULES,
            "note": "research only; nothing wired, released or VERIFIED; floors beside, never summed into released; "
                    + RELEASED_BEAM_M3_NOTE, "census": census, "rows": rows}


def md(led):
    c = led["census"]
    out = ["# T-721 census: 12 HELD BLANK STR.CONC.BEAM lines on ARCH_TAKEOFF_V3.0.71", "",
           f"Lines {c['lines']}: AT_LEAST {c['AT_LEAST']} ({c['at_least_sum_beside_m3']} m3 beside), BLANK_NAMED "
           f"{c['BLANK_NAMED']} (plan {c['blank_plan_m2']} m2 = m3 per m of depth); zero {c['zero']}, ranges {c['ranges']}. "
           f"Bounded lines untouched: {c['bounded_untouched']['lines']} ({c['bounded_untouched']['low_m3']} .. "
           f"{c['bounded_untouched']['high_m3']} m3).", "",
           "| Line | Element | Before | After | m3 / basis | Item |", "|---|---|---|---|---|---|"]
    for r in led["rows"]:
        v = (f"AT_LEAST {r['at_least_m3']} ({r['plan_area_used_m2']} m2 x {r['depth_floor_m']} m)"
             if r["bound"] == "AT_LEAST" else f"blank; {r['m3_per_m_depth']} m3 per m depth")
        out.append(f"| {r['line_id']} | {r['element_id']} | blank | {r['bound']} | {v}; {r['basis']} | {r['item']} |")
    return "\n".join(out) + "\n"


def main(argv):
    led = build()
    if "--write" in argv:
        OUT_JSON.parent.mkdir(exist_ok=True)
        OUT_JSON.write_text(json.dumps(led, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        OUT_MD.write_text(md(led), encoding="utf-8")
    print(json.dumps(led["census"], indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
