"""T-712 concrete ground beams: the 20 HELD BLANK STR.CONC.GROUND_BEAM lines of the candidate of record
ARCH_TAKEOFF_V3.0.70, each given the one-sided AT_LEAST the drawings guarantee (R-T712-1) or kept HELD BLANK with its
designer item and its m3 per m of depth (R-T712-2). Research only: nothing wired, released or VERIFIED, no line summed
into a released total.

Committed inputs only (no drawing is opened here):
  line index  research/agents_t693/out/LINE_INDEX_V3_0_70.json (V3.0.70 ids, classes, bounds)
  plan areas  research/agents_t712/out/T712_AREAS.json (own DXF outlines, t712_measure.py, ST7757 dxf sha 9f9d1179)
  cross-check research/agents_t658/out/T658_LEDGER.json (T-658 r2, Verifier Gate A PASS 2026-11-10: the floors the
              V3.0.64+ candidates carry as AT_LEAST text beside the 16 LOWER_ONLY lines)
Printed facts used (sheet; approval): ST p.13 'Ground Beams for exterior walls': top 'Ground Floor slab level', depth
'FOLLOW ARCH.', underside 'Outer Normal ground level', 3T16 top + 2T12/30cm sides + 6T16 bottom (two rows); ST p.13
interior sections 'Less then 2.5m' 30x30, 'Less than 5m' 30x40, 'More than 5m' 30x60, all 'without concentrated load';
annex structural top +0.25 (LEVEL.STRUCTURAL_TOP.GF.ANNEX, APPROVED DESIGNER 2026-10-25), outer N.G. +-0.00
(LEVEL.NATURAL_GROUND.OUTER, APPROVED DESIGNER 2026-10-24); ST p.3 annex marks +0.30 inside, +0.15 yard outside (a
finished yard level, not 'normal ground'); ST p.3 / arch sheet03: the west entrance landing between the yard stair and
the main west wall and the C4 -> plot-end stretch carry no level mark.

    python3 -I research/agents_t712/t712_alsenan.py [--write]
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import t712_rules as R  # noqa: E402

D = Decimal
INDEX = RES / "agents_t693" / "out" / "LINE_INDEX_V3_0_70.json"
AREAS = HERE / "out" / "T712_AREAS.json"
T658 = RES / "agents_t658" / "out" / "T658_LEDGER.json"
OUT_JSON = HERE / "out" / "T712_LEDGER.json"
OUT_MD = HERE / "out" / "T712_CENSUS.md"

TOP_ANNEX, NG = D("0.25"), D("0.00")
TITLES = [("LT", "2.5", "0.30"), ("LT", "5", "0.40"), ("GT", "5", "0.60")]       # ST p.13
HIS_SECTION_D = D("0.60")                                                       # freelancer: one section 0.30 x 0.60
D35 = "D-35 (exterior ground-beam depth 'FOLLOW ARCH.'; annex literal +0.25 -> N.G. 0.00 cannot hold the printed bars)"
D33 = "D-33 (run carrying a landing beam; ST p.13 prints sections only 'without concentrated load')"
D35C = ("D-35 court stretch (exterior section; neither the slab / landing level it carries nor the yard ground under it "
        "is printed; GB.EXTERIOR.DEPTH_BASIS.COURT not declared)")

ANNEX = {   # line -> (member, run keys in T712_AREAS)
    "L-402dbe61d1c924144a3c": ("annex south band F8/7D4, col 207 -> col 20B -> east band face 7D1", ["BAND0015#1", "BAND0015#2"]),
    "L-6bf14711798e5af93594": ("annex east band 10B/7D1 run 1, incl. the SE corner square (T-669) -> col 22C", ["BAND0012.1"]),
    "L-3284f44000c02179ace7": ("annex east band 10B/7D1 run 2, col 22C -> col 223 (C5)", ["BAND0012.2"]),
    "L-4783c6e18002c3a8a37e": ("annex west band 136/7D5, col 207 -> col 204", ["BAND0016"]),
    "L-00465df980165c529476": ("annex north band 137/138, col 204 -> col 214", ["BAND0035"]),
    "L-e16c98075f69532a3dc7": ("annex NE quarter ring r 1.00 .. 1.30, col 214 -> band 13E/7D6", ["BAND0042"]),
    "L-b4a13a43967ee4765662": ("annex band 13E/7D6 run 2, face 13D -> ring end", ["BAND0017.2"]),
    "L-d8b98b143e293d30833b": ("annex band 13D/7D2 run 1, col 211 (C3) -> col 223 (C5)", ["BAND0013.2"]),
}
JUNCTION = ("L-be6708e07b40efa02779", "annex junction remainder of 13D/7D2 on 13E/7D6: face 7D6 -> col 211 (0.10 x 0.30)",
            "BAND0013.1")
D33_RUNS = {   # line -> (member, run key, span readings m, extra area readings m2, landing)
    "L-0bb78accf8c0a0fbdbaf": ("oblique band 17E/17F, face 7E6 -> col 1EF", "BAND0037.1", ["2.4269"], [], "182+183"),
    "L-d53e5eb08e2c6c668254": ("band 177/7CD run 2, col 245 -> curved band outer face", "BAND0008.2", ["1.5367"], [], "7E7+7E8"),
    "L-a8c5c32c7a785c1e3f05": ("band 180D/180E, face 176 -> face 175", "BAND0040", ["2.1"], [], "180+181"),
    "L-1487bdda099006e0c4ba": ("band 142/7D8 (drawn ends)", "BAND0019", ["2.45"], [], "141+7DA"),
    "L-5af89b9f1e5b90daf8f5": ("band 184/7CF run 3, col 23C -> drawn end (5.00 m ON_LIMIT)", "BAND0010.3", ["5.0"], [], "7E7+7E8"),
    "L-e24946df436cbc25fca6": ("band 177/7CD run 1, drawn end -> col 245", "BAND0008.1", ["5.02", "4.97"], ["1.491"],
                               "175+7DE / 176+7E6 / 7DC+7DD"),
    "L-95a1f198cfe7f398d6ae": ("band 7DC/7DD run 1, face 7CF -> col 7F5", "BAND0023:7DC+7DD#1", ["3.525"], [], "7E1+7E2"),
    "L-cfb4555cb26b39934bff": ("band 7E7/7E8 run 2, col 7ED -> face 177", "BAND0032:7E7+7E8#2", ["3.525"], [], "114+115+7DF"),
}
COURT = {
    "L-62243c74c430d383be86": ("west entrance: band 185/7C7, col 230 (C7) -> main west face 109; landing north edge",
                               ["BAND0002.1"]),
    "L-21795b350fbd09150c43": ("west entrance: band 178/7DB, face 145 -> face 7C7; edge between the yard stair (+0.15) "
                               "and the landing", ["BAND0022"]),
    "L-a55bfa01b726ef11650c": ("band 1811/1812, col 1E8 (C4) -> drawn end at the plot line (pool-deck side)",
                               ["BAND0041:RUN", "BAND0041:STRIP"]),
}


def _index():
    d = json.loads(INDEX.read_text())
    assert d["candidate_version"] == "ARCH_TAKEOFF_V3.0.70"
    rows = [l for l in d["lines"] if l["item_code"] == "STR.CONC.GROUND_BEAM" and l["class"] == "HELD"
            and l["held_low"] is None and l["held_high"] is None and l["measured_net"] is None]
    assert len(rows) == 20, len(rows)
    bounded = [l for l in d["lines"] if l["item_code"] == "STR.CONC.GROUND_BEAM" and l["class"] == "HELD"
               and l["held_low"] is not None]
    return {l["line_id"]: l for l in rows}, bounded


def _areas():
    a = json.loads(AREAS.read_text())
    assert a["dxf_sha256_16"] == "9f9d1179a5d2a663"
    assert a["overlaps_between_outlines"] == [] and a["outline_inside_column"] == []
    return a["runs"]


def _t658():
    return {r["line_id"]: r for r in json.loads(T658.read_text())["rows"]}


def _his(area):
    return R.BR.round_point(R.BR.mul(area, HIS_SECTION_D))


def build():
    idx, bounded = _index()
    ar = _areas()
    t658 = _t658()
    rows = []
    depth_annex = R.depth_literal_levels(top=TOP_ANNEX, underside=NG)
    assert depth_annex == D("0.25")
    for lid, (mem, keys) in ANNEX.items():
        area = R.BR.add(*(D(ar[k]["area_m2"]) for k in keys))
        f = R.floor(areas_m2=[area], depth=depth_annex, basis="LITERAL_LEVELS")
        old = D(t658[lid]["low"])
        rows.append({**R.statement(lid, idx[lid]["element_id"], "AT_LEAST", at_least=f["at_least"], item=D35),
                     "member": mem, "d_id": "D-35", "basis": "LITERAL_LEVELS",
                     "hand": f"drawn area {area} m2 x (+0.25 - 0.00) = {R.BR.mul(area, depth_annex)}",
                     "area_m2": str(area), "depth_floor_m": "0.25", "at_most_why_none":
                     "underside printed only as 'Outer Normal ground level' (the conflicting reading); no footing-top "
                     "or formation level is printed (ST p.9 note 1 prints a MINIMUM depth only)",
                     "m3_per_0_10m_depth": str(R.BR.round_low(R.BR.mul(area, "0.10"))),
                     "t658_floor": str(old), "vs_t658": str(f["at_least"] - old),
                     "freelancer_section_on_drawn_plan": str(_his(area))})
    # junction remainder
    lid, mem, key = JUNCTION
    area = D(ar[key]["area_m2"])
    dj = R.depth_junction({"13D/7D2 annex exterior (D-35 floor)": depth_annex,
                           "13E/7D6 through-band (0.40 in the released span 0017.1; 0.25 floor in the exterior span "
                           "0017.2: the section may step at the junction face)": depth_annex})
    f = R.floor(areas_m2=[area], depth=dj, basis="JUNCTION")
    rows.append({**R.statement(lid, idx[lid]["element_id"], "AT_LEAST", at_least=f["at_least"], item=D35),
                 "member": mem, "d_id": "D-35", "basis": "JUNCTION", "area_m2": str(area), "depth_floor_m": str(dj),
                 "hand": f"0.10 x 0.30 = {area} m2 x 0.25 (least of the members that may own the square)",
                 "beside": "if the 30x40 of the released interior span 0017.1 runs through the square: 0.012000 "
                           "(reading, not the floor); col 211 owns its full section (R-T666-1)",
                 "was": "OPEN BOUND 'neck-cut sliver section not printed' (R-GB-NECK-CUT-1, T-669 census)",
                 "m3_per_0_10m_depth": str(R.BR.round_low(R.BR.mul(area, "0.10"))),
                 "freelancer_section_on_drawn_plan": str(_his(area))})
    # loaded runs
    for lid, (mem, key, spans, extra, land) in D33_RUNS.items():
        area = D(ar[key]["area_m2"])
        dl = R.depth_least_title(spans, TITLES)
        f = R.floor(areas_m2=[area] + extra, depth=dl, basis="LEAST_TITLE")
        old = D(t658[lid]["low"])
        rows.append({**R.statement(lid, idx[lid]["element_id"], "AT_LEAST", at_least=f["at_least"], item=D33),
                     "member": mem, "d_id": "D-33", "basis": "LEAST_TITLE", "landing_beam": land,
                     "spans_m": spans, "titles_holding": {s: [str(x) for x in R.titles_holding(s, TITLES)] for s in spans},
                     "area_m2": str(area), "area_readings_m2": [str(area)] + extra, "depth_floor_m": str(dl),
                     "hand": f"min area {f['area_min_m2']} m2 x least title {dl} = {R.BR.mul(f['area_min_m2'], dl)}",
                     "at_most_why_none": "loaded run: the unloaded titles are a reference, not a ceiling (R-T658-8)",
                     "m3_per_0_10m_depth": str(R.BR.round_low(R.BR.mul(f["area_min_m2"], "0.10"))),
                     "t658_floor": str(old), "vs_t658": str(f["at_least"] - old),
                     "freelancer_section_on_drawn_plan": str(_his(area))})
    # court stretches: blank
    for lid, (mem, keys) in COURT.items():
        run = D(ar[keys[0]]["area_m2"])
        reads = [run] if len(keys) == 1 else [run, R.BR.add(run, D(ar[keys[1]]["area_m2"]))]
        b = R.blank(item=D35C, why="no printed level for the slab / landing the beam carries nor for the ground under "
                                   "it; the exterior section's depth is 'FOLLOW ARCH.': any figure would be chosen",
                    areas_m2=reads)
        rows.append({**R.statement(lid, idx[lid]["element_id"], "BLANK_NAMED", item=D35C), "member": mem,
                     "d_id": "D-35 (court)", "basis": None, "why": b["why"], "m3_per_m_depth": b["m3_per_m_depth"],
                     "plan_readings": "run net of col 1E8 / strip of band 1812 under col 1E8 (0.025 m2) as a second "
                                      "reading" if len(keys) > 1 else "run net of columns",
                     "freelancer_section_on_drawn_plan": str(_his(run))})
    assert sorted(r["line_id"] for r in rows) == sorted(idx), "census 20 / 20 by id"
    by = {}
    for r in rows:
        k = r["d_id"]
        g = by.setdefault(k, {"lines": 0, "at_least_lines": 0, "at_least_m3": D(0), "blank": 0, "area_m2": D(0)})
        g["lines"] += 1
        g["area_m2"] += D(r.get("area_m2") or r["m3_per_m_depth"][0])
        if r["bound"] == "AT_LEAST":
            g["at_least_lines"] += 1
            g["at_least_m3"] += D(r["at_least_m3"])
        else:
            g["blank"] += 1
    for g in by.values():
        g["at_least_m3"], g["area_m2"] = str(g["at_least_m3"]), str(g["area_m2"])
    tot = R.BR.add(*(D(r["at_least_m3"]) for r in rows if r["at_least_m3"]))
    his = R.BR.add(*(D(r["freelancer_section_on_drawn_plan"]) for r in rows))
    return {
        "schema": "T712_LEDGER_V1", "task": "T-712", "candidate": "ARCH_TAKEOFF_V3.0.70", "rules": R.RULES,
        "not_claimed": "nothing wired, released or VERIFIED; no AT_MOST; floors never summed into a released total",
        "census": {"lines": len(rows), "at_least": sum(1 for r in rows if r["bound"] == "AT_LEAST"),
                   "blank_named": sum(1 for r in rows if r["bound"] == "BLANK_NAMED")},
        "by_designer_item": by, "at_least_family_beside_m3": str(tot),
        "bounded_lines_unchanged": {"lines": len(bounded),
                                    "low": str(R.BR.add(*(D(str(l["held_low"])) for l in bounded))),
                                    "high": str(R.BR.add(*(D(str(l["held_high"])) for l in bounded)))},
        "freelancer_section_on_the_20_drawn_plans_m3": str(his),
        "lines": rows,
    }


def _md(d):
    L = ["# T-712 census (V3.0.70, 20 HELD blank STR.CONC.GROUND_BEAM lines)", "",
         f"{d['census']['at_least']} AT_LEAST, {d['census']['blank_named']} BLANK_NAMED; AT_LEAST beside "
         f"{d['at_least_family_beside_m3']} m3 (never summed into a released total).", "",
         "| line | member | D-id | basis | area m2 | AT_LEAST m3 | T-658 floor | m3 per 0.10 m / per m depth |",
         "|---|---|---|---|---|---|---|---|"]
    for r in d["lines"]:
        pu = r.get("m3_per_0_10m_depth") or ("per m: " + " / ".join(r["m3_per_m_depth"]))
        L.append(f"| {r['line_id'][:10]} | {r['member']} | {r['d_id']} | {r['basis'] or '-'} | "
                 f"{r.get('area_m2') or '-'} | {r['at_least_m3'] or 'BLANK'} | {r.get('t658_floor', '-')} | {pu} |")
    L += ["", "| D-id | lines | AT_LEAST lines | AT_LEAST m3 | blank | drawn plan m2 |", "|---|---|---|---|---|---|"]
    for k, g in sorted(d["by_designer_item"].items()):
        L.append(f"| {k} | {g['lines']} | {g['at_least_lines']} | {g['at_least_m3']} | {g['blank']} | {g['area_m2']} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    d = build()
    s = json.dumps(d, indent=1, sort_keys=True, default=str)
    if "--write" in sys.argv:
        OUT_JSON.parent.mkdir(exist_ok=True)
        OUT_JSON.write_text(s + "\n")
        OUT_MD.write_text(_md(d))
    print(json.dumps({k: d[k] for k in ("census", "by_designer_item", "at_least_family_beside_m3",
                                         "bounded_lines_unchanged", "freelancer_section_on_the_20_drawn_plans_m3")},
                     indent=1, default=str))
