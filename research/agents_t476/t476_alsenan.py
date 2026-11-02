"""T-476 development-villa run (Alsenan is one sample; the method is t476_handrail_runs.py, every villa).

Inputs (private, decoded into .work/private by the wrapper, never committed):
  1. the architectural plan DXF (P7757_DXF_COMPRESSED.zip on Drive) read by entity handle;
  2. the released plan reader's BOQ_LINES.json (ARCH_TAKEOFF_V2.9 on that DXF:
     `tools/urban_boq_m9.py arch --drawings <P7757.dxf> --out <dir> --method ARCH_TAKEOFF_V2.9 --no-svg --no-m9-xlsx`),
     for the 14 per-flight FIN.RAILING lines (finding F-T199-1) that every candidate since V3.0.29 carries unchanged.
Committed inputs: research/agents_t184/ALSENAN_STAIR_INPUT.json (MERGED riser counts), research/agents_t164 and
research/agents_t393 run tables (MERGED).

    python3 -I research/agents_t476/t476_alsenan.py <P7757.dxf> <V2.9 BOQ_LINES.json> [--write]

`--write` writes FLIGHT_CENSUS_T476.csv, READER_BINDING_T476.csv and summary.json beside this file (lengths, handles,
engine line ids only: no coordinates, no client data).
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t476_handrail_runs as H  # noqa: E402

MM = 0.001
STAIR_INPUT = HERE.parent / "agents_t184" / "ALSENAN_STAIR_INPUT.json"
T164_CSV = HERE.parent / "agents_t164" / "RAILINGS_T164.csv"
T393_CSV = HERE.parent / "agents_t393" / "RUN_TABLE_T393.csv"
# candidate V3.0.42 (T-471 matrix, research/agents_t471/out): B7-09 19 lines = 2 released + 17 held, 17.366 lm valued
CANDIDATE_B709 = {"lines": 19, "released": 2, "held": 17, "valued_lm": 17.366}
CANDIDATE_B1308 = {"lines": 6, "released": 4, "held": 2, "valued_lm": 21.550}


def _db(path):
    import ezdxf
    return ezdxf.readfile(path).entitydb


def _ln(db, h):
    e = db[h]
    if e.dxftype() != "LINE":
        raise H.RailInputError(f"{h} is {e.dxftype()}, expected LINE")
    return (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y), e.dxf.layer


def _len(db, h):
    a, b, _ = _ln(db, h)
    return math.hypot(b[0] - a[0], b[1] - a[1]) * MM


def _stairs():
    data = json.loads(STAIR_INPUT.read_text())
    return {s["stair_id"]: {f["id"]: f for f in s["flights"]} for s in data["stairs"]}


def st02_split(db):
    """Independent re-measure of the ST-02 inner band per flight (not the T-164 code): band centreline radius from
    the two concentric edge arcs; each curved going = r x the angle between consecutive riser lines (their inner
    ends); the transition going from the last curved riser along the arc to its end then straight to the first
    straight riser; straight goings from the straight riser lines; one sloped piece per going (variable pitch)."""
    o, i = db["B9C"], db["BA2"]
    c = (o.dxf.center.x, o.dxf.center.y)
    if math.hypot(i.dxf.center.x - c[0], i.dxf.center.y - c[1]) > 1.0:
        raise H.RailInputError("ST-02 band arcs not concentric")
    r = 0.5 * (o.dxf.radius + i.dxf.radius)
    curved = ["BB9", "BB7", "BB5", "BB3", "BB1", "BAF", "BAD", "BAB", "BA9", "BA7", "BA5", "BA3"]
    straight = ["B43", "B4A", "B49", "B48", "B47", "B46", "B45", "B44", "B4B", "B4C", "B4D"]

    def ang(h):
        a, b, _ = _ln(db, h)
        p = min((a, b), key=lambda q: math.hypot(q[0] - c[0], q[1] - c[1]))
        return math.degrees(math.atan2(p[1] - c[1], p[0] - c[0])) % 360.0
    angs = [ang(h) for h in curved]
    if any(b <= a for a, b in zip(angs, angs[1:])):
        raise H.RailInputError("ST-02 curved riser lines not in sweep order")
    arcs = [r * math.radians(b - a) * MM for a, b in zip(angs, angs[1:])]
    end = o.dxf.end_angle % 360.0
    ex = c[0] + r * math.cos(math.radians(end))
    xs = [_ln(db, h)[0][0] for h in straight]
    transition = (r * math.radians(end - angs[-1]) + abs(xs[0] - ex)) * MM
    straights = [abs(b - a) * MM for a, b in zip(xs, xs[1:])]
    riser = _stairs()["ST-02"]["RS-S"]["riser"]
    rsc = [*arcs, transition]                       # RS-C: 12 risers -> 12 goings to the first RS-S riser
    rs_c = sum(math.hypot(g, riser) for g in rsc)
    rs_s = sum(math.hypot(g, riser) for g in straights)
    ys = [_ln(db, h)[0][1] for h in ("B59", "B5A", "B5B", "B5C", "D22")]
    ra_plan = abs(ys[-1] - ys[0]) * MM
    return {"r_m": r * MM, "RS-C_goings": len(rsc), "RS-C_plan": sum(rsc), "RS-C_rise": len(rsc) * riser,
            "RS-C_len": rs_c, "RS-S_goings": len(straights), "RS-S_plan": sum(straights),
            "RS-S_rise": len(straights) * riser, "RS-S_len": rs_s, "RS-A_plan": ra_plan, "RS-A_rise": 4 * riser,
            "RS-A_len": H.segment_length(H.INCLINED, ra_plan, 4 * riser), "riser": riser,
            "outer_band_plan": (_len_arc(db["BA1"]), _len_arc(db["BA0"])),
            "outer_band_end_deg": (db["BA1"].dxf.end_angle, db["BA0"].dxf.end_angle)}


def _len_arc(e):
    sweep = (e.dxf.end_angle - e.dxf.start_angle) % 360.0
    return e.dxf.radius * math.radians(sweep) * MM


def checks(db):
    """Drawing facts the census relies on, each re-read by handle."""
    a138, b138 = _ln(db, "138A")[:2], _ln(db, "1358")[:2]
    rs_a_west = _ln(db, "B75")[0][0]
    d23 = _ln(db, "AF5")[0][0]
    return {
        # R-T476-3: the 2F floor-edge guard band starts where the MS2-U well band ends (one continuous band)
        "G-2F_continuous_with_1358": math.hypot(a138[0][0] - b138[0][0], a138[0][1] - b138[0][1]) < 1.0,
        # RS-A: west side band B75 vs the east-side floor-edge band AF5 / AF6 (D-23): two separate bands 1.15 m apart
        "RS-A_band_spacing_m": round(abs(d23 - rs_a_west) * MM, 3),
        # GF east-lane well band beyond D1 (finding F-T476-1)
        "GF_east_band_47F_4A4_m": (round(_len(db, "47F"), 3), round(_len(db, "4A4"), 3)),
        "GF_east_band_layers": (_ln(db, "47F")[2], _ln(db, "4A4")[2]),
    }


def census(db):
    st = _stairs()
    s2 = st02_split(db)
    rows = []

    def add(stair, flight, side, kind, family, status, length, plan, rise, src, missing="", run="", phys=None):
        rows.append({"phys": phys, "stair": stair, "flight": flight, "side": side, "kind": kind, "family": family, "status": status,
                     "length": None if length is None else round(length, 6), "plan": None if plan is None else
                     round(plan, 6), "rise": None if rise is None else round(rise, 6), "source": src,
                     "missing": missing, "run": run, "id": f"{flight}:{side}"})
    for fid in ("MS1-L", "MS1-U", "MS2-L", "MS2-U"):
        f = st["ST-01"][fid]
        F = H.Flight(fid, f["risers"], f["riser"], f["going"])
        fam, status = H.classify_side(H.OPEN, rail_drawn=True)
        add("ST-01", fid, "inner (well)", H.INCLINED, fam, status, H.segment_length(H.INCLINED, F.plan, F.rise), F.plan,
            F.rise, "well band (T-164 / T-393 handles) + section A-A rail; riser counts T-184", run="RL-07")
        fam, status = H.classify_side(H.WALL, rail_drawn=False)
        add("ST-01", fid, "outer (shaft wall)", H.INCLINED, fam, status, None, F.plan, F.rise,
            "no layer-5 band along the shaft walls on GF / 1F / 2F (scan of the shaft boxes)")
    add("ST-01", "T-1F-S", "well-end turn", H.HORIZONTAL, H.FAM_STAIR, H.CONFIRMED,
        H.segment_length(H.HORIZONTAL, 0.200, 0.0), 0.200, 0.0, "AC3 / AC4 (T-393 R-T393-1)", run="RL-07")
    add("ST-01", "T-MS1-N", "well-end turn (5 winders)", "TURN", H.FAM_STAIR, H.HELD, None, 0.200, 5 * 0.166667,
        "T-393", "rail profile over the 5 winders at the 0.10 m well not drawn", run="RL-07")
    add("ST-01", "T-MS2-LD", "well-end turn (half landing)", "TURN", H.FAM_STAIR, H.HELD, None, 0.200, 0.168,
        "T-393", "closing riser MS2-TR position against the turn not drawn", run="RL-07")
    add("ST-01", "G-2F", "2F floor edge over MS2-L", H.HORIZONTAL, H.FAM_STAIR, H.CONFIRMED,
        H.segment_length(H.HORIZONTAL, 1.325, 0.0), 1.325, 0.0, "138A / 138B, one band with 1358 (R-T476-3)",
        run="RL-07")
    d1 = st["ST-01b"]["D1"]
    F = H.Flight("D1", d1["risers"], d1["riser"], d1["going"])
    add("ST-01b", "D1", "well side", H.INCLINED, H.FAM_STAIR, H.CONFIRMED,
        H.segment_length(H.INCLINED, F.plan, F.rise), F.plan, F.rise, "section A-A one rail; T-184 D1", run="RL-08")
    add("ST-01b", "D1", "lift-shaft wall", H.INCLINED, None, H.NOT_APPLICABLE, None, F.plan, F.rise,
        "wall side; no wall rail drawn")
    add("ST-02", "RS-C", "inner (void)", H.INCLINED, H.FAM_STAIR, H.CONFIRMED, s2["RS-C_len"], s2["RS-C_plan"],
        s2["RS-C_rise"], "band B9C / BA2 r 1.5555; 12 riser lines BB9..BA3, per going", run="RL-05")
    add("ST-02", "RS-C", "outer (corner)", H.INCLINED, H.FAM_STAIR, H.UNKNOWN, None,
        round(sum(s2["outer_band_plan"]) / 2, 6), s2["RS-C_rise"], "band BA0 / BA1 r 2.7305 / 2.7805 (layer 5)",
        "guard or string: what closes the corner between the outer band and the two walls (open to the floor below "
        "or filled) is not drawn; band end 259.1 deg (BA1, 1F) vs 270.4 deg (GF copy 23E)", run="RL-09")
    add("ST-02", "RS-S", "north (void)", H.INCLINED, H.FAM_STAIR, H.CONFIRMED, s2["RS-S_len"], s2["RS-S_plan"],
        s2["RS-S_rise"], "band B76; 11 riser lines B43..B4D", run="RL-05")
    add("ST-02", "RS-S", "south (outer wall)", H.INCLINED, None, H.NOT_APPLICABLE, None, s2["RS-S_plan"],
        s2["RS-S_rise"], "outer wall; no wall rail drawn")
    add("ST-02", "RS-A", "west (void)", H.INCLINED, H.FAM_STAIR, H.CONFIRMED, s2["RS-A_len"], s2["RS-A_plan"],
        s2["RS-A_rise"], "band B75; 5 riser lines B59..D22", run="RL-05")
    fam, status = H.classify_side(H.OPEN, rail_drawn=True, floor_level_band=True)
    add("ST-02", "RS-A", "east (living floor edge D-23)", H.HORIZONTAL, fam, status,
        H.segment_length(H.HORIZONTAL, 2.400, 0.0), 2.400, 0.0,
        "AF5 / AF6 separate band at the +5.50 floor edge (horizontal, not on the slope)", run="RL-06")
    for what, L in (("volute", 0.810720), ("corner landing RS-LD", 0.050), ("1F void edge beside RS-A", 1.625),
                    ("1F gallery void edge", 5.845)):
        add("ST-02", what, "level", H.HORIZONTAL, H.FAM_STAIR, H.CONFIRMED, L, L, 0.0,
            "T-164 (one continuous band with the flights)", run="RL-05")
    e1 = st["ST-03"]["E1"]
    F = H.Flight("E1", e1["risers"], e1["riser"], e1["going"])
    for side in ("side 1", "side 2"):
        fam, status = H.classify_side(H.OPEN, rail_drawn=False)
        add("ST-03", "E1", side, H.INCLINED, fam, status, None, F.plan, F.rise, "GF plan: no rail drawn",
            "open edge (0.85 m rise) with no guard drawn: designer item (RL-11)", run="RL-11")
    chk = checks(db)
    d1_plan = H.Flight("D1", d1["risers"], d1["riser"], d1["going"]).plan
    beyond = round(0.5 * sum(chk["GF_east_band_47F_4A4_m"]) - d1_plan, 6)
    add("ST-01b", "GF east-lane band beyond D1", "well side", H.HORIZONTAL, H.FAM_STAIR, H.UNKNOWN, None, beyond, None,
        "47F / 4A4 solid layer-5 band 2.750 / 2.800 m vs D1 run 0.900 m (finding F-T476-1)",
        "whether D1's rail continues along the east lane beside the well south of D1, at what level, or the band is a "
        "drafting edge (no level change printed across it)", run="none")
    add("ST-01", "MS1-T", "outer (shaft wall corner)", "TURN", None, H.NOT_APPLICABLE, None, None, None,
        "winder corner against the shaft walls; no wall rail drawn")
    phys = {("ST-01", "MS1-L"): "ST01-MS1-L", ("ST-01", "MS1-U"): "ST01-MS1-U", ("ST-01", "MS2-L"): "ST01-MS2-L",
            ("ST-01", "MS2-U"): "ST01-MS2-U", ("ST-01", "T-MS1-N"): "ST01-MS1-T", ("ST-01", "MS1-T"): "ST01-MS1-T",
            ("ST-01b", "D1"): "ST01b-D1", ("ST-02", "RS-C"): "ST02-RS-C", ("ST-02", "RS-S"): "ST02-RS-S",
            ("ST-02", "RS-A"): "ST02-RS-A"}
    for r in rows:
        r["phys"] = phys.get((r["stair"], r["flight"]))
    return rows, s2


# 14 per-flight FIN.RAILING lines of the plan reader (V2.9, carried unchanged in every candidate since V3.0.29):
# line id -> (floor, reader flight suffix, expected treads, physical flight, reading, census sides by reader side name)
BINDINGS = {
    "L-7248a8eb8255e2b1002d": ("GF", "F1", 12, "ST02-RS-C", "PRIMARY"),
    "L-da416ad0fac1f96f1f4a": ("GF", "F2", 6, "ST02-RS-S", "PARTIAL_PRIMARY"),
    "L-4e2dd6e9d0aadaed1e71": ("GF", "F3", 3, "ST02-RS-S", "SPLIT_PART"),
    "L-6c67a5111c6ac79a5ad3": ("GF", "F4", 3, "ST02-RS-A", "SEEN_THROUGH_VOID"),
    "L-5a12ecf5ba4cd2c0c596": ("GF", "F1", 7, "ST01-MS1-L", "PARTIAL_PRIMARY"),
    "L-820a4035813bddf434a2": ("GF", "F2", 3, "ST01b-D1", "PRIMARY"),
    "L-6a0af8d265d64b2a29b4": ("1F", "F1", 12, "ST02-RS-C", "SEEN_THROUGH_VOID"),
    "L-ff7765e42da7f24a85b4": ("1F", "F2", 11, "ST01-MS2-L", "PRIMARY"),
    "L-ffe82ff407834e14c9d6": ("1F", "F3", 10, "ST01-MS1-U", "PRIMARY"),
    "L-f2b90e48ddb8006d6bd6": ("1F", "F4", 10, "ST02-RS-S", "SEEN_THROUGH_VOID"),
    "L-1b41f6db9634081084e0": ("1F", "F5", 4, "ST01-MS1-T", "PRIMARY"),
    "L-6c636d1ceccb1eaab7bd": ("1F", "F6", 4, "ST02-RS-A", "PRIMARY"),
    "L-01db55b3b76ea3a736ea": ("2F", "F1", 10, "ST01-MS2-L", "SEEN_THROUGH_OPENING"),
    "L-67f25abf5bb9d13eb39b": ("2F", "F2", 10, "ST01-MS2-U", "PRIMARY"),
}
HOMES = {"ST02-RS-C": ["RL-05 RS-C inner", "RL-09 RS-C outer (UNKNOWN)"], "ST02-RS-S": ["RL-05 RS-S north"],
         "ST02-RS-A": ["RL-05 RS-A west", "RL-06 D-23 east (B13-08)"], "ST01-MS1-L": ["RL-07 MS1-L"],
         "ST01b-D1": ["RL-08 D1"], "ST01-MS2-L": ["RL-07 MS2-L"], "ST01-MS1-U": ["RL-07 MS1-U"],
         "ST01-MS1-T": ["RL-07 T-MS1-N (HELD)"], "ST01-MS2-U": ["RL-07 MS2-U"]}
NOTES = {  # why each reading, from the reader's own flight geometry vs the census (no coordinates)
    "L-7248a8eb8255e2b1002d": "radial 12 treads, r 1.589 / 2.739 = the RS-C band radii; also drawn on layer 5",
    "L-da416ad0fac1f96f1f4a": "6 of the 10 RS-S goings (1.80 m) on the GF plan; the other 3 are F3 beside it (0.25 m apart)",
    "L-4e2dd6e9d0aadaed1e71": "3 more RS-S goings, same line of risers as F2: one physical flight split in two readings",
    "L-6c67a5111c6ac79a5ad3": "3 of the 4 RS-A goings, layer 2 (overhead) on the GF plan; 1F F6 is its primary",
    "L-5a12ecf5ba4cd2c0c596": "7 of the 9 MS1-L goings (2.10 vs 2.70 m), layer 2 part; a figure here would undercount",
    "L-820a4035813bddf434a2": "3 goings 0.90 m, 4 solid riser lines in the east lane = D1 (T-184)",
    "L-6a0af8d265d64b2a29b4": "the reader itself marks it SEEN_THROUGH_VOID of GF F1",
    "L-ff7765e42da7f24a85b4": "west lane, 12 lines 3.30 m = MS2-L (DXF dimension 3300)",
    "L-ffe82ff407834e14c9d6": "east lane, 11 lines 3.00 m = MS1-U arriving at +5.50 (12 risers on A-A)",
    "L-f2b90e48ddb8006d6bd6": "the reader itself marks it SEEN_THROUGH_VOID of GF F2",
    "L-1b41f6db9634081084e0": "radial, inner r 0.099 = the 0.10 m well: the GF -> 1F winder corner",
    "L-6c636d1ceccb1eaab7bd": "5 lines 1.20 m = RS-A (B59..D22); the reader's east OPEN side is the D-23 floor edge: "
                              "a horizontal B13-08 guard, not a rail on the slope",
    "L-01db55b3b76ea3a736ea": "west lane on 2F = MS2-L seen through the 2F opening (T-111: no flight leaves +9.70); "
                              "the reader did NOT flag it as seen from below",
    "L-67f25abf5bb9d13eb39b": "east lane, 11 lines 3.00 m = MS2-U arriving at +9.70",
}


def reader_lines(path):
    data = json.loads(Path(path).read_text())
    lines = data["lines"] if isinstance(data, dict) else data
    out = []
    for ln in lines:
        if ln["item_code"] != "FIN.RAILING":
            continue
        inp = ln["calculation"]["inputs"]
        lid = ln["line_id"]
        if lid not in BINDINGS:
            raise H.RailInputError(f"{lid}: reader line not in the binding table (reader changed?)")
        floor, suffix, treads, *_ = BINDINGS[lid]
        if (ln["location"]["floor"], inp["flight_id"].rsplit(":", 1)[1], inp["treads"]) != (floor, suffix, treads):
            raise H.RailInputError(f"{lid}: floor / flight / treads differ from the binding table")
        sides = tuple((s["side"], s["kind"], s["plan_lm"]) for s in inp["sides"])
        out.append(H.ReaderLine(lid, floor, suffix, sides, ln.get("measured_net")))
    if len(out) != len(BINDINGS):
        raise H.RailInputError(f"{len(out)} reader lines, binding table has {len(BINDINGS)}")
    return out


def build(dxf, v29_lines):
    db = _db(dxf)
    rows, s2 = census(db)
    rd = reader_lines(v29_lines)
    bind = {k: (v[3], v[4]) for k, v in BINDINGS.items()}
    sides = {}
    for r in rows:
        if r.get("phys"):
            sides.setdefault(r["phys"], []).append(H.WALL if r["status"] == H.NOT_APPLICABLE else H.OPEN)
    bound = H.bind_reader_lines(rd, bind, sides, HOMES)
    for b in bound:
        b["note"] = NOTES[b["line_id"]]
    fam = H.family_totals(rows)
    t393 = list(csv.DictReader(T393_CSV.open()))
    rl07 = round(sum(float(r["LENGTH_LM"]) for r in t393 if r["RUN"] == "RL-07" and r["STATUS"] == H.CONFIRMED), 3)
    proposal = {
        "B7-09 FIN.RAILING": {
            "candidate_V3.0.42": CANDIDATE_B709,
            "proposed_valued_lm": round(fam[H.FAM_STAIR]["confirmed_lm"], 3),
            "proposed_valued_runs": {"RL-05": 16.324, "RL-07 (T-393 segments)": rl07, "RL-08": 1.042},
            "proposed_held_blank": ["RL-07 T-MS1-N", "RL-07 T-MS2-LD", "RL-09 RS-C outer", "RL-11 E1 (2 sides)"],
            "per_flight_reader_lines": "14 RETIRED (each bound to one physical flight, all sides homed in runs)"},
        "B13-08 MET.RAILING.GUARD": {"candidate_V3.0.42": CANDIDATE_B1308, "proposed_valued_lm": 21.550,
                                     "change": "none (RL-06 D-23 confirmed as the RS-A east-side floor-edge guard)",
                                     "held_blank": ["RL-04", "RL-10"]},
        "B7-10 FIN.HANDRAIL": {"state": "NOT_APPLICABLE", "evidence": "every WALL side of 8 flights + winders: no "
                               "layer-5 band along a wall on GF / 1F / 2F (UP-STAIR-013)"},
    }
    return rows, bound, fam, s2, checks(db), proposal


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    rows, bound, fam, s2, chk, proposal = build(sys.argv[1], sys.argv[2])
    summary = {"family_totals_census": fam, "st02_split": s2, "checks": chk, "proposal": proposal,
               "reader_binding": {"retire": sum(b["action"] == "RETIRE" for b in bound),
                                  "side_differs": [b["line_id"] for b in bound if b["side_check"] != "AGREE"]}}
    print(json.dumps(summary, indent=1, default=str))
    if "--write" in sys.argv:
        with (HERE / "FLIGHT_CENSUS_T476.csv").open("w", newline="") as fh:
            wr = csv.writer(fh)
            wr.writerow(["STAIR", "FLIGHT", "SIDE", "KIND", "FAMILY", "STATUS", "LENGTH_LM", "PLAN_M", "RISE_M", "RUN",
                         "SOURCE", "MISSING"])
            for r in rows:
                wr.writerow([r["stair"], r["flight"], r["side"], r["kind"], r["family"] or "", r["status"],
                             "" if r["length"] is None else f"{r['length']:.6f}",
                             "" if r["plan"] is None else f"{r['plan']:.6f}",
                             "" if r["rise"] is None else f"{r['rise']:.6f}", r["run"], r["source"], r["missing"]])
        with (HERE / "READER_BINDING_T476.csv").open("w", newline="") as fh:
            wr = csv.writer(fh)
            wr.writerow(["LINE_ID", "FLOOR", "READER_FLIGHT", "PHYSICAL_FLIGHT", "READING", "ACTION", "HOMES",
                         "SIDE_CHECK", "NOTE"])
            for b in bound:
                wr.writerow([b["line_id"], b["floor"], b["reader_flight"], b["flight"], b["reading"], b["action"],
                             " | ".join(b["homes"]), b["side_check"], b["note"]])
        (HERE / "summary.json").write_text(json.dumps(summary, indent=1, default=str) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
