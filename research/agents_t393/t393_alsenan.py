"""T-393 development-villa run table (Alsenan is one sample; the method is t393_railing_runs.py, every villa).

Reads the PRIVATE architectural DXF (P7757_DXF_COMPRESSED.zip on Drive, decoded into .work/private, never committed)
by entity handle, plus the merged T-184 stair counts and the merged T-164 run census. Writes nothing into the drawing
folder; `--write` writes RUN_TABLE_T393.csv and summary.json beside this file (lengths and handles only, no client data).

    python3 -I research/agents_t393/t393_alsenan.py <architectural plan DXF> [--write]
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t393_railing_runs as R  # noqa: E402

MM = 0.001
STAIR_INPUT = HERE.parent / "agents_t184" / "ALSENAN_STAIR_INPUT.json"
T164_CSV = HERE.parent / "agents_t164" / "RAILINGS_T164.csv"
FREELANCER_INTERNAL_LM = 18.95   # 'internal railing', FIN cover sheet, typed constant (=B39), research record only


def _db(path):
    import ezdxf
    return ezdxf.readfile(path).entitydb


def _line(db, h):
    e = db[h]
    if e.dxftype() != "LINE":
        raise R.RunInputError(f"{h} is {e.dxftype()}, expected LINE")
    return (e.dxf.start[0], e.dxf.start[1]), (e.dxf.end[0], e.dxf.end[1]), e.dxf.layer


def _len(db, h):
    a, b, _ = _line(db, h)
    return math.hypot(b[0] - a[0], b[1] - a[1]) * MM


def _flights():
    data = json.loads(STAIR_INPUT.read_text())
    st = next(s for s in data["stairs"] if s["stair_id"] == "ST-01")
    return {f["id"]: f for f in st["flights"]}


def st01(db):
    """RL-07 re-segmented: each flight, each well-end turn and the 2F guard released on its own evidence (S-9 (4))."""
    fl = _flights()
    run, segs = "RL-07", []
    src_f = "plan band drawn (GF 157/151 + 47F/4A4, 1F A8D-A90, 2F 1356-1359); section A-A sheet10 draws the rail; " \
            "riser counts T-184 (MERGED, Q-46 A)"
    for fid in ("MS1-L", "MS1-U", "MS2-L", "MS2-U"):
        f = fl[fid]
        segs.append(R.Segment(run, fid, f"{fid} inner balustrade, pitch line ({f['risers']} risers {f['riser']:.6f}, "
                              f"going {f['going']:.3f})", R.flight_pitch(f["risers"], f["riser"], f["going"]),
                              R.CONFIRMED, src_f, binds=(f"ST01-{fid}",)))
    # 1F plan well: outer band edges A8D (x) / A8F (x), closing bands AC3 (south, y) / A9B (north, y), band 50 mm
    (xa, _), _, _ = _line(db, "A8D")
    (xb, _), _, _ = _line(db, "A8F")
    (_, y_s), _, _ = _line(db, "AC3")
    (_, y_n), _, _ = _line(db, "A9B")
    w = 50.0
    # risers next to each closing band: the first / last riser lines of the flights stand 50 mm inside the band end
    # (west flight AC0 at +50 and A97 at -50 from the band ends, the first and last of its 12 riser lines)
    (_, y_ac0), _, _ = _line(db, "AC0")
    (_, y_a97), _, _ = _line(db, "A97")
    south = R.well_end_turn_plan(xa, xb, w, y_ac0, y_ac0, y_s) * MM
    north = R.well_end_turn_plan(xa, xb, w, y_a97, y_a97, y_n) * MM
    segs.append(R.turn_segment(run, "T-1F-S", "1F floor-level turn at the south well end (AC3): MS1-U arrives and "
                               "MS2-L starts at +5.50", south, 0.0, False, "1F plan AC3 / AC4 + DXF dimension 200",
                               ("ST01-TURN-1F-S",), ""))
    segs.append(R.turn_segment(run, "T-MS2-LD", "half landing MS2-LD turn at the north well end (A9B)", north, 0.168,
                               False, "1F plan A9B / A9C (plan); section A-A (landing)", ("ST01-TURN-MS2-LD",),
                               "closing riser MS2-TR +7.516 -> +7.684 on the landing: its position relative to the "
                               "rail turn and the rail profile over it are not drawn (T-184 HELD MS2-TR: landing "
                               "levels scaled, not printed)"))
    segs.append(R.turn_segment(run, "T-MS1-N", "GF -> 1F north turn: the 5 winders MS1-T and the corner MS1-LD are ONE "
                               "physical turn (Q-50 text: 5 winder steps in the 1.20 x 1.20 corner)", north, 0.8333,
                               False, "GF plan 154 / 150 dashed closure (plan); section A-A 5 winder risers",
                               ("ST01-TURN-MS1-N",), "rail profile over the 5 winders converging at the 0.10 m well "
                               "(ramp, newel posts or wreath) and the rail heights at both ends not drawn"))
    g2f = 0.5 * (_len(db, "138A") + _len(db, "138B"))
    segs.append(R.guard_segment(run, "G-2F", "2F floor-edge guard over the MS2-L opening (138A / 138B centreline, "
                                "+9.70)", g2f, "OPEN", True, "2F plan 138A / 138B layer 5", ("ST01-GUARD-2F",)))
    return segs, {"south_turn_plan_m": south, "north_turn_plan_m": north, "g2f_m": g2f,
                  "band_outer_x_mm": [xa, xb], "closing_y_mm": [y_s, y_n]}


def gf_extension(db):
    """New finding: the GF plan continues the well band SOUTH of its closure (155 / 156 at the MS1-L foot) to the
    shaft wall: 2C8 layer 5 (solid) with 2C9 layer 2 (hidden) beside it, plus the diagonal pair 2F1D / 2F1E."""
    out = {}
    for h in ("2C8", "2C9", "2F1D", "2F1E", "155", "156"):
        a, b, layer = _line(db, h)
        out[h] = {"layer": layer, "length_m": round(math.hypot(b[0] - a[0], b[1] - a[1]) * MM, 3)}
    return out


def rl04(db):
    """Sea-side GF roof strip (+5.50) in front of W15 / W16: plan band vs NW elevation."""
    plan = 0.5 * (_len(db, "C85") + _len(db, "C86"))
    # NW elevation: slab edge 27E5 / 27E2, piers 27D7 (left) and 27DD / 27DF (right), 1.000 m layer-5 line 27E7
    (lx, _), _, _ = _line(db, "27D7")
    (rx, _), _, _ = _line(db, "27DF")
    elev = {"slab_edge_27E5_m": round(_len(db, "27E5"), 3), "clear_between_piers_m": round(abs(rx - lx) * MM, 3),
            "pier_left_27D7_height_m": round(_len(db, "27D7"), 3), "pier_right_27DD_height_m": round(_len(db, "27DD"), 3),
            "pier_width_27E3_m": round(_len(db, "27E3"), 3),
            "layer5_line_27E7_m": round(_len(db, "27E7"), 3), "layer5_line_27E7_layer": _line(db, "27E7")[2]}
    seg = R.Segment("RL-04", "RL-04", "GF roof strip sea edge (+5.50) in front of W15 / W16", None, R.HELD,
                    "1F plan C85 / C86 (layer 5 band, closed C81 / C84) vs NW elevation DXF", plan_m=plan,
                    missing="what stands on the edge: the plan draws a 50 mm railing band 6.127 m; the NW elevation "
                            "draws two 0.20 m piers 0.50 m high (printed '50') with 7.500 m open between them and a "
                            "single 1.000 m layer-5 line at pier-top level from the left pier only; type, height and "
                            "extent (6.127 plan vs 7.500 elevation) not established",
                    binds=("RL-04",))
    return seg, {"plan_band_m": plan, **elev}


def internal_reconciliation(t164_rows):
    """(c) ours 19.766 (RL-05 + RL-06 + RL-08) vs his 18.95 lm, split into measured causes."""
    by = {}
    for r in t164_rows:
        if r["LENGTH_LM"]:
            by.setdefault(r["RUN"], 0.0)
            by[r["RUN"]] += float(r["LENGTH_LM"])
    rl05, rl06, rl08 = by["RL-05"], by["RL-06"], by["RL-08"]
    ours = rl05 + rl06 + rl08
    a = R.reconcile(ours, FREELANCER_INTERNAL_LM, [("RL-08 ST-01b lobby flight D1 rail (second staircase shaft)", rl08)])
    b = R.reconcile(ours, FREELANCER_INTERNAL_LM, [("RL-06 1F floor-edge guard D-23 (not a stair)", rl06),
                                                   ("RL-08 D1 lobby rail", rl08)])
    return {"ours_lm": round(ours, 3), "theirs_lm": FREELANCER_INTERNAL_LM, "RL-05": rl05, "RL-06": rl06, "RL-08": rl08,
            "decomposition_A_his_scope_ST02_plus_D23": a, "decomposition_B_his_scope_ST02_only": b}


def build(dxf):
    db = _db(dxf)
    segs, st = st01(db)
    seg04, f04 = rl04(db)
    rows = list(csv.DictReader(T164_CSV.open()))
    rec = internal_reconciliation(rows)
    return segs, seg04, st, f04, gf_extension(db), rec


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    segs, seg04, st, f04, ext, rec = build(sys.argv[1])
    t = R.totals(segs)
    summary = {"RL-07": {"segments": [s.__dict__ for s in segs], "totals": t, "geometry": st},
               "RL-04": {"segment": seg04.__dict__, "facts": f04}, "GF_band_extension": ext, "internal": rec}
    print(json.dumps(summary, indent=1, default=str))
    if "--write" in sys.argv:
        with (HERE / "RUN_TABLE_T393.csv").open("w", newline="") as fh:
            wr = csv.writer(fh)
            wr.writerow(["RUN", "SEGMENT", "WHAT", "LENGTH_LM", "STATUS", "PLAN_M", "RISE_M", "MISSING", "SOURCE",
                         "BINDS"])
            for s in segs + [seg04]:
                wr.writerow([s.run, s.seg_id, s.what, "" if s.length_m is None else f"{s.length_m:.3f}", s.status,
                             "" if s.plan_m is None else f"{s.plan_m:.3f}",
                             "" if s.rise_m is None else f"{s.rise_m:.4f}", s.missing, s.source, ";".join(s.binds)])
        (HERE / "summary.json").write_text(json.dumps(summary, indent=1, default=str) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
