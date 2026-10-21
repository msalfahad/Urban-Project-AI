"""T-150: doors and windows as BOQ lines, by hand (research only; nothing in the engine imports this file).

    python3 -I calc.py OPENINGS_T150.csv summary.json      # Alsenan hand table -> per opening, per type and floor
    python3 -I calc.py --check                             # synthetic NON-Alsenan fixture, hand-computed expectations

Rules applied (no other rule, no typical size):
- UP-DOOR-CLS-001..006: class per door from its two sides; one physical door = one item, leaves only recorded.
- UP-DOOR-AREA-001: AS_DRAWN area = CAD / printed wall opening x height; an assumed height gives an ASSUMED area,
  never a confirmed one; the OWNER_STANDARD view is a separate CONDITIONAL scenario, never added to AS_DRAWN.
- UP-DOOR-HGT-001 + owner Q-55 C: door height printed (main entrance 2.50) or the 2.20 m fallback, ASSUMED.
- UP-OPEN-SCHED-001: an opening without a printed height keeps its width; its area is HELD (no number, never 0).
- Owner Q-32 A (arched head: enclosing rectangle to the crown), Q-38 A (curved glass in a straight opening: printed
  width), Q-39 C (window curved on plan: outer arc), Q-33 (windows aluminium by default), Q-04 (owner minimum view:
  ordinary 1.00 nominal = 1.10 wall to wall, bathroom 0.90 = 1.00; drawn size when wider).
- UP-QTY-STATUS-001 / WORKFLOW_CONTROLS section 5: evidence statuses kept apart in every total; HELD / UNKNOWN never
  count as 0. INFERRED (Q-17) is listed beside HELD and never released.
Standard library only.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from collections import OrderedDict

ROUND = 3
# Owner minimum view (Q-04 / UP-DOOR-OPEN-002 table): required wall opening per class; kept as a CONDITIONAL scenario.
OWNER_MIN_WALL = {"DOOR.INTERNAL.PVC": 1.10, "BATHROOM_PVC": 1.00, "DOOR.EXTERNAL.ALUMINIUM": 1.10}
SUPPLY_LINES = ("DOOR.EXTERNAL.ALUMINIUM", "DOOR.INTERNAL.PVC", "DOOR.MAIN_ENTRANCE", "WINDOW.ALUMINIUM")


def _f(v):
    v = (v or "").strip()
    return float(v) if v else None


def _r(x):
    return None if x is None else round(x + 0.0, ROUND)


def is_bathroom(row):
    return "UP-DOOR-CLS-003" in row["CLASS_EVIDENCE"]


def evaluate(row):
    """One opening -> its quantities. Width / height in metres (the table is metric; --check covers mm input)."""
    w, wlo, h = _f(row["WIDTH_M"]), _f(row["WIDTH_LO_M"]), _f(row["HEIGHT_M"])
    hs = row["HEIGHT_STATUS"].strip()
    out = OrderedDict(id=row["ID"], kind=row["KIND"], floor=row["FLOOR"], line=row["BOQ_LINE"],
                      class_status=row["CLASS_STATUS"], width_m=w, width_lo_m=wlo, height_m=h, height_status=hs,
                      count=1, area_m2=None, area_lo_m2=None, area_status=None, owner_min_area_m2=None)
    if w is None:
        out["area_status"] = "HELD"            # width not established: nothing measured, never 0
        return out
    if hs == "PRINTED":
        status = "DRAWING-CONFIRMED"
    elif hs == "ASSUMED":
        status = "ASSUMED"                     # Q-55 C fallback: OWNER-APPROVED fallback, never confirmed
    elif hs == "INFERRED":
        status = "INFERRED"                    # Q-17: candidate only
    else:
        status = "HELD"
    if status != "HELD" and h is not None:
        out["area_m2"] = _r(w * h)
        if wlo is not None:                    # width itself a range: the area is held as bounds
            out["area_lo_m2"] = _r(wlo * h)
            status = "HELD" if status == "DRAWING-CONFIRMED" else status + "_RANGE"
    out["area_status"] = status
    # OWNER_STANDARD (Q-04) scenario for ordinary doors only: CONDITIONAL, never added to AS_DRAWN.
    if row["KIND"] == "DOOR" and row["BOQ_LINE"] in ("DOOR.INTERNAL.PVC", "DOOR.EXTERNAL.ALUMINIUM") and h:
        key = "BATHROOM_PVC" if is_bathroom(row) else row["BOQ_LINE"]
        out["owner_min_area_m2"] = _r(max(w, OWNER_MIN_WALL[key]) * h)
    return out


def freelancer(row):
    key = row["FREELANCER_KEY"].strip()
    if not key or key == "none" or key.endswith("?"):
        return None
    return _f(row["FREELANCER_W"]) * _f(row["FREELANCER_H"])


def totals(rows, evs):
    """Per BOQ line and floor: count, m2 by evidence status; the freelancer's same openings beside them."""
    t = OrderedDict()
    for row, ev in zip(rows, evs):
        k = (ev["line"], ev["floor"])
        b = t.setdefault(k, OrderedDict(count=0, width_m=0.0, m2_confirmed=0.0, n_confirmed=0, m2_assumed=0.0,
                                        n_assumed=0, n_held=0, held_width_m=0.0, m2_held_range=[0.0, 0.0],
                                        n_inferred=0, m2_inferred=0.0, owner_min_m2=0.0,
                                        fl_count=0, fl_m2_all=0.0, fl_m2_same_confirmed=0.0))
        b["count"] += 1
        b["width_m"] += ev["width_m"] or 0.0
        s = ev["area_status"]
        if s == "DRAWING-CONFIRMED":
            b["n_confirmed"] += 1
            b["m2_confirmed"] += ev["area_m2"]
        elif s == "ASSUMED":
            b["n_assumed"] += 1
            b["m2_assumed"] += ev["area_m2"]
        elif s == "ASSUMED_RANGE":           # assumed height and a width range: carried as an assumed range
            b["n_held"] += 1
            b["m2_held_range"][0] += ev["area_lo_m2"]
            b["m2_held_range"][1] += ev["area_m2"]
        elif s == "INFERRED":
            b["n_inferred"] += 1
            b["m2_inferred"] += ev["area_m2"]
        else:
            b["n_held"] += 1
            b["held_width_m"] += ev["width_m"] or 0.0
        if ev["owner_min_area_m2"] is not None:
            b["owner_min_m2"] += ev["owner_min_area_m2"]
        fl = freelancer(row)
        if fl is not None:
            b["fl_count"] += 1
            b["fl_m2_all"] += fl
            if s == "DRAWING-CONFIRMED":
                b["fl_m2_same_confirmed"] += fl
    for b in t.values():
        for k, v in list(b.items()):
            if isinstance(v, float):
                b[k] = _r(v)
        b["m2_held_range"] = [_r(x) for x in b["m2_held_range"]]
        # re-add: every opening sits in exactly one evidence bucket
        assert b["n_confirmed"] + b["n_assumed"] + b["n_held"] + b["n_inferred"] == b["count"], b
    return t


def run(rows):
    evs = [evaluate(r) for r in rows]
    ids = [e["id"] for e in evs]
    assert len(ids) == len(set(ids)), "one row per physical opening (UP-DOOR-CLS-006)"
    t = totals(rows, evs)
    # cross-check: the per-line totals re-add to the per-opening sums
    for status in ("DRAWING-CONFIRMED", "ASSUMED"):
        a = _r(sum(e["area_m2"] for e in evs if e["area_status"] == status))
        key = "m2_confirmed" if status == "DRAWING-CONFIRMED" else "m2_assumed"
        assert abs(a - sum(b[key] for b in t.values())) < 0.0015, (status, a)
    return evs, t


def read(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------------------------------------- synthetic check
HDR = ("ID,KIND,FLOOR,BOQ_LINE,CLASS_STATUS,CLASS_EVIDENCE,LEAVES,FORM,WIDTH_M,WIDTH_LO_M,WIDTH_BASIS,WIDTH_SOURCE,"
       "HEIGHT_M,SILL_M,HEIGHT_STATUS,HEIGHT_SOURCE,MATERIAL,MATERIAL_SOURCE,WALL_T_M,SIDE_A,SIDE_B,ENGINE_REF,"
       "PRIOR_REF,FREELANCER_KEY,FREELANCER_W,FREELANCER_H,VERDICT,NOTE")


def _syn(i, kind, fl, line, cev, leaves, form, w, h, hs, wlo="", fk="", fw="", fh=""):
    return {k: v for k, v in zip(HDR.split(","), [i, kind, fl, line, "DRAWING-CONFIRMED", cev, str(leaves), form,
                                                   w, wlo, "", "", h, "", hs, "", "", "", "0.20", "a", "b", "", "",
                                                   fk, fw, fh, "", ""])}


def mm(v):
    """Input in millimetres -> metres string (unit adversarial case)."""
    return "%.3f" % (float(v) / 1000.0)


def check():
    """A made-up two-storey house (not Alsenan); every expectation below is computed by hand in the comment."""
    rows = [
        # S1 single internal PVC 0.90 jamb to jamb, height not printed -> 2.20 ASSUMED: 0.90 x 2.20 = 1.980;
        #    owner minimum view max(0.90, 1.10) x 2.20 = 2.420 (CONDITIONAL, never added)
        _syn("S1", "DOOR", "GF", "DOOR.INTERNAL.PVC", "UP-DOOR-CLS-001", 1, "single swing", "0.90", "2.20", "ASSUMED"),
        # S2 double main entrance 1.60 printed, 2.40 printed: ONE door set (2 leaves): 1.60 x 2.40 = 3.840 confirmed
        _syn("S2", "DOOR", "GF", "DOOR.MAIN_ENTRANCE", "UP-DOOR-CLS-004", 2, "double swing", "1.60", "2.40",
             "PRINTED"),
        # S3 sliding glazed external door 2400 x 2200 mm printed: 2.400 x 2.200 = 5.280 confirmed; owner view
        #    max(2.40, 1.10) = 2.40 -> 5.280 (wider than the minimum: the drawn size is used, Q-04)
        _syn("S3", "DOOR", "GF", "DOOR.EXTERNAL.ALUMINIUM", "UP-DOOR-CLS-002", 2, "sliding", mm(2400), mm(2200),
             "PRINTED", fk="x", fw="2.50", fh="2.20"),
        # S4 window curved on plan, outer arc 2.80 (chord 2.40), arched head to the crown 2.60 (springing 2.20):
        #    Q-39 C x Q-32 A = 2.80 x 2.60 = 7.280 confirmed; the freelancer row 2.40 x 2.20 = 5.280
        _syn("S4", "WINDOW", "1F", "WINDOW.ALUMINIUM", "", 1, "curved + arched", "2.80", "2.60", "PRINTED",
             fk="y", fw="2.40", fh="2.20"),
        # S5 window 1.20 with no printed height: width kept, area HELD (never 0, never a usual size)
        _syn("S5", "WINDOW", "1F", "WINDOW.ALUMINIUM", "", 1, "rectangular", "1.20", "", "HELD", fk="z", fw="1.20",
             fh="2.00"),
        # S6 bathroom door 0.80 jamb, height ASSUMED 2.20: 1.760; owner view max(0.80, 1.00) x 2.20 = 2.200
        _syn("S6", "DOOR", "1F", "DOOR.INTERNAL.PVC", "UP-DOOR-CLS-003", 1, "single swing", "0.80", "2.20",
             "ASSUMED"),
        # S7 bathroom door whose width is only a range 0.69 .. 0.80 (loose arc): ASSUMED range 1.518 .. 1.760
        _syn("S7", "DOOR", "1F", "DOOR.INTERNAL.PVC", "UP-DOOR-CLS-003", 1, "single swing", "0.80", "2.20",
             "ASSUMED", wlo="0.69"),
        # S8 mirrored twin of S5 with an INFERRED height 2.00: 2.400 INFERRED, never in a confirmed total
        _syn("S8", "WINDOW", "1F", "WINDOW.ALUMINIUM", "", 1, "rectangular", "1.20", "2.00", "INFERRED"),
        # S9 gate with no width: HELD, no area
        _syn("S9", "GATE", "GF", "SITE.GATE_HELD", "", 1, "single swing", "", "", "HELD"),
    ]
    evs, t = run(rows)
    e = {x["id"]: x for x in evs}
    exp = {"S1": (1.980, "ASSUMED", 2.420), "S2": (3.840, "DRAWING-CONFIRMED", None),
           "S3": (5.280, "DRAWING-CONFIRMED", 5.280), "S4": (7.280, "DRAWING-CONFIRMED", None),
           "S5": (None, "HELD", None), "S6": (1.760, "ASSUMED", 2.200), "S7": (1.760, "ASSUMED_RANGE", 2.200),
           "S8": (2.400, "INFERRED", None), "S9": (None, "HELD", None)}
    bad = []
    for k, (a, s, om) in exp.items():
        got = (e[k]["area_m2"], e[k]["area_status"], e[k]["owner_min_area_m2"])
        if got != (a, s, om):
            bad.append((k, got, (a, s, om)))
    if e["S7"]["area_lo_m2"] != 1.518:
        bad.append(("S7 lo", e["S7"]["area_lo_m2"], 1.518))
    w1 = t[("WINDOW.ALUMINIUM", "1F")]
    # 1F windows: confirmed S4 7.280 only; S5 held (width 1.20), S8 inferred 2.400; freelancer same-confirmed 5.280
    if (w1["count"], w1["m2_confirmed"], w1["n_held"], w1["held_width_m"], w1["m2_inferred"],
            w1["fl_m2_same_confirmed"], w1["fl_m2_all"]) != (3, 7.28, 1, 1.2, 2.4, 5.28, 7.68):
        bad.append(("1F windows", dict(w1)))
    d1 = t[("DOOR.INTERNAL.PVC", "1F")]
    # 1F PVC: S6 assumed 1.760; S7 assumed range 1.518 .. 1.760; owner view 2.200 + 2.200 = 4.400 (never added)
    if (d1["m2_assumed"], d1["m2_held_range"], d1["owner_min_m2"]) != (1.76, [1.518, 1.76], 4.4):
        bad.append(("1F PVC", dict(d1)))
    # mutation guards: a held window must not turn into 0; an assumed area must not reach the confirmed total
    if any(x["area_m2"] == 0 for x in evs):
        bad.append("a held opening became 0")
    if t[("DOOR.INTERNAL.PVC", "GF")]["m2_confirmed"] != 0.0:
        bad.append("an ASSUMED door area reached the confirmed total")
    # duplicate opening ids are refused (one physical door = one item)
    try:
        run(rows + [rows[0]])
        bad.append("duplicate opening accepted")
    except AssertionError:
        pass
    print("check:", "PASS" if not bad else "FAIL", len(exp), "openings,", 4, "aggregate / mutation guards")
    for b in bad:
        print("  ", b)
    return 0 if not bad else 1


def main(argv):
    if argv[1:2] == ["--check"]:
        return check()
    rows = read(argv[1])
    evs, t = run(rows)
    out = OrderedDict(openings=evs, by_line_floor=[OrderedDict(line=k[0], floor=k[1], **v) for k, v in t.items()])
    # house-level supply totals (site gate, lift candidates, passages and the unresolved census item excluded)
    house = OrderedDict()
    for (line, fl), b in t.items():
        if line not in SUPPLY_LINES:
            continue
        h = house.setdefault(line, OrderedDict(count=0, width_m=0.0, m2_confirmed=0.0, m2_assumed=0.0, n_held=0,
                                               held_width_m=0.0, m2_inferred=0.0, owner_min_m2=0.0,
                                               m2_held_range=[0.0, 0.0], fl_count=0, fl_m2_all=0.0,
                                               fl_m2_same_confirmed=0.0))
        for k in ("count", "width_m", "m2_confirmed", "m2_assumed", "n_held", "held_width_m", "m2_inferred",
                  "owner_min_m2", "fl_count", "fl_m2_all", "fl_m2_same_confirmed"):
            h[k] += b[k]
        h["m2_held_range"] = [h["m2_held_range"][0] + b["m2_held_range"][0],
                              h["m2_held_range"][1] + b["m2_held_range"][1]]
    for h in house.values():
        for k, v in list(h.items()):
            if isinstance(v, float):
                h[k] = _r(v)
        h["m2_held_range"] = [_r(x) for x in h["m2_held_range"]]
    out["house_supply_lines"] = house
    if len(argv) > 2:
        with open(argv[2], "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
    buf = io.StringIO()
    for o in out["by_line_floor"]:
        buf.write("%-28s %-3s n=%-3d conf %7.3f (%d) assumed %7.3f (%d) held %d (width %.2f, range %s) inferred "
                  "%.3f | owner-min %.3f | freelancer n=%d all %.3f same-conf %.3f\n" % (
                      o["line"], o["floor"], o["count"], o["m2_confirmed"], o["n_confirmed"], o["m2_assumed"],
                      o["n_assumed"], o["n_held"], o["held_width_m"], o["m2_held_range"], o["m2_inferred"],
                      o["owner_min_m2"], o["fl_count"], o["fl_m2_all"], o["fl_m2_same_confirmed"]))
    for k, h in house.items():
        buf.write("HOUSE %-26s %s\n" % (k, json.dumps(h)))
    sys.stdout.write(buf.getvalue())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
