"""T-524: CROSS-TRADE ownership of the lintel concrete at FLAGGED_DEFICIT ends (research rule proposal R-T524-1; research
only, nothing in engine/ or tools/ imports it; no candidate or released quantity changes here).

Physical element (ERS s.2.1). The cast RC lintel over an opening: its span over the opening, its two END ZONES beyond the
jambs, and the HOST each end zone meets. The merged T-453 lintel concrete is B x D x (w + 2 b_min) with b_min = the
printed 'MIN.40cm' bearing on BOTH ends. T-516 (merged) measured the masonry a beside every jamb: 10 ends have
a < b_min (FLAGGED_DEFICIT). At such an end the T-453 end zone (length b_min) cannot be built as drawn; the part
r = b_min - a beyond the masonry lies in one of three places, and each is a different BOQ fact:

  COLUMN          the lintel runs into an RC column. The column is cast before the masonry and its line
                  (STR.CONC.COLUMN = section x storey height) already holds every m3 inside its outline. The part of r
                  inside the column outline (min(r, column depth along the wall line)) is COLUMN concrete, counted ONCE
                  in that column line, never in B9-02. A lintel does not pass through a column: the part of r beyond
                  the column's far face is NOT BUILT. The lintel itself ends at the column face (extension <= a).
  END_OF_MASONRY  the masonry stops at the far face of a cross wall (or a free end): r lies in the next space; nothing is
                  built there. NOT BUILT (never a quantity of any trade). The lintel extension is <= a (through the own
                  stub and the cross wall at most); where it does pass through the cross wall it displaces at most a
                  B x D window of that wall's masonry (listed for the masonry MATERIAL base, never the contract area).
  OPENING (pier)  two lintels share a pier p < 2 b_min. The T-453 end zones overlap each other along the wall line by
                  2 b_min - p (the pier twice plus each zone over the neighbour's span, where the neighbour's own span
                  already is): LINTEL ON LINTEL, counted twice. The pair occupies the pier once: pair length at most
                  (w1 + o1) + (w2 + o2) + min(p, 2 b_min) (one lintel over both openings, or two meeting in the pier).

Per lintel (concrete, m3): lo = B D (w_net + sum of the BOUNDED ends' b_min); hi on the MIN-BEARING basis (comparable with
T-453: a BOUNDED end keeps b_min) = B D (w_net + sum over ends of (b_min if BOUNDED else a if DEFICIT)); w_net = w minus
any span strip that lies inside a column outline (an opening jamb drawn inside a column). State: HELD BY NAME (designer
detail of the deficit end: RC column connection, wall end, shared pier; RFI never blocks integration) with [lo, hi]
beside; never 0 (w_net > 0 is refused otherwise). A HELD end (junction not resolved) keeps the T-453 b_min in hi (the
T-453 basis) and 0 in lo, labelled.
Conservation (asserted): T-453 m3 of the set - corrected hi = INSIDE_COLUMN + LINTEL_ON_LINTEL + NOT_BUILT.
Formwork (T-453 = 2 L D + w B): corrected 2 L D + w_net B on lo / hi; end-stop faces at END_OF_MASONRY ends [0, B D]
listed for T-474 part 2 (not added). Host masonry face deducted by T-453 ((w + 2 b_min) D): over-deducted AT LEAST
D r per COLUMN / END_OF_MASONRY end and D (2 b_min - p) per pier pair (listed for the T-498 resume). Bars untouched
(T-515).

Refused: lengths not in metres (negative or > 30 m), a deficit end with a >= b_min, a T-453 length that is not
w + 2 b_min, a pier listed on one side only or with two different values, a pair of different section or head, a
column whose drawn gap to the jamb differs from the T-516 a by more than the frame tolerance, a w_net <= 0.

    (training villa) build() reads only committed files: research/agents_t516/out/JAMB_BEARING_T516.json,
    research/agents_t453/out/LINTELS_T453.csv, research/alsenan_lintels_s8_6/01_OPENING_CENSUS.csv and
    research/R9_1_CHRIS_POST_FREEZE/09_COLUMN_CROSSWALK.csv. Run it through tests/t524_lintel_end_ownership.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULE_ID = "R-T524-1"
B_MIN = 0.40
BOUNDED, DEFICIT, HELD, MEASURED = "BOUNDED", "FLAGGED_DEFICIT", "HELD", "MEASURED"
COLUMN, END, OPENING = "COLUMN", "END_OF_MASONRY", "OPENING"
INSIDE_COLUMN, LINTEL_ON_LINTEL, NOT_BUILT = "INSIDE_COLUMN", "LINTEL_ON_LINTEL", "NOT_BUILT"
FRAME_TOL_M = 0.030          # arch DXF vs structural-frame registration (W18 jamb 32.7 mm vs 7.8 mm by the two frames)
EPS = 1e-9


class Refused(ValueError):
    pass


def _m(x, what):
    if x is None:
        return None
    if not isinstance(x, (int, float)) or x < -EPS or x > 30:
        raise Refused(f"{what}: {x!r} is not a length in metres")
    return float(x)


def _r6(x):
    return None if x is None else round(x + 0.0, 6)


def assess_end(lintel, end, b_min=B_MIN):
    """One end of one lintel -> extension bounds and the fate of the T-453 end zone beyond the masonry."""
    st = end["state"]
    a = _m(end.get("available_m"), f"{lintel['id']} {end['side']} available")
    B, D = lintel["B"], lintel["D"]
    out = {"side": end["side"], "state": st, "stopper": end.get("stopper"), "stopper_id": end.get("stopper_id", ""),
           "available_m": a, "overrun_m": 0.0, "inside_column_m": 0.0, "not_built_m": 0.0, "host": None,
           "pier_shared_with": None, "ext_lo_m": None, "ext_hi_m": None, "end_stop_face_max_m2": 0.0,
           "host_face_overdeduct_min_m2": 0.0, "cross_wall_window_max_m2": 0.0}
    if st in (BOUNDED, MEASURED):
        out.update(ext_lo_m=b_min, ext_hi_m=b_min, why="BOUNDED: kept at the printed minimum (MIN-BEARING basis)")
        return out
    if st == HELD:
        out.update(ext_lo_m=0.0, ext_hi_m=b_min, why="HELD end (junction not resolved): T-453 b_min kept in hi, 0 in lo")
        return out
    if st != DEFICIT:
        raise Refused(f"{lintel['id']} {end['side']}: unknown end state {st!r}")
    if a is None:
        raise Refused(f"{lintel['id']} {end['side']}: a deficit end needs its measured masonry a")
    if a >= b_min - EPS:
        raise Refused(f"{lintel['id']} {end['side']}: a = {a} >= b_min is not a deficit")
    r = b_min - a
    out.update(overrun_m=r, ext_lo_m=0.0, ext_hi_m=a)
    stop = end.get("stopper")
    if stop == COLUMN:
        host = end.get("host")
        if host and host.get("along_m") is not None:
            along = _m(host["along_m"], "column depth along the wall")
            if lintel.get("span_column_id") == host["id"]:
                # the jamb itself lies inside this column: the span strip already holds that part of the column
                along = max(0.0, along - (lintel.get("span_in_column_m") or 0.0))
            inside = min(r, along)
            out.update(inside_column_m=inside, not_built_m=r - inside, host=host,
                       why=(f"lintel ends at the column face (extension <= a = {a}); {inside:.3f} m of the T-453 zone "
                            f"inside column {host['id']} (its line holds it), {r - inside:.3f} m beyond its far face "
                            "not built"))
        else:
            out.update(inside_column_m=None, not_built_m=None, host=None,
                       why="column not identified: the zone is inside a column for (0, r] m, split HELD by name")
        out["host_face_overdeduct_min_m2"] = D * r
    elif stop == END:
        out.update(not_built_m=r, end_stop_face_max_m2=B * D,
                   cross_wall_window_max_m2=B * D if end.get("through_walls") else 0.0,
                   why=(f"masonry ends {a} m beyond the jamb (far face of {end.get('through_walls') or 'the wall end'})"
                        f": {r:.3f} m of the T-453 zone lies in the next space, not built"))
        out["host_face_overdeduct_min_m2"] = D * r
    elif stop == OPENING:
        out.update(pier_shared_with=end.get("stopper_id"),
                   why=f"shared pier {a} m with {end.get('stopper_id')}: settled by the pair (pier occupied once)")
    else:
        raise Refused(f"{lintel['id']} {end['side']}: deficit stopper {stop!r} not handled")
    return out


def assess_lintel(lintel, b_min=B_MIN):
    w = _m(lintel["width_m"], f"{lintel['id']} width")
    strip = _m(lintel.get("span_in_column_m", 0.0), f"{lintel['id']} span strip")
    w_net = w - strip
    if w_net <= EPS:
        raise Refused(f"{lintel['id']}: net span {w_net} <= 0")
    B, D = _m(lintel["B"], "B"), _m(lintel["D"], "D")
    t453_len = _m(lintel["t453_length_m"], "T-453 length")
    if abs(t453_len - (w + 2 * b_min)) > 1e-6:
        raise Refused(f"{lintel['id']}: T-453 length {t453_len} is not w + 2 b_min = {w + 2 * b_min}")
    if abs(lintel["t453_concrete_m3"] - B * D * t453_len) > 5e-4:
        raise Refused(f"{lintel['id']}: T-453 concrete {lintel['t453_concrete_m3']} is not B D L")
    ends = [assess_end(lintel, e, b_min) for e in lintel["ends"]]
    if len(ends) != 2 or {e["side"] for e in ends} != {"START", "END"}:
        raise Refused(f"{lintel['id']}: needs one START and one END")
    L_lo = w_net + sum(e["ext_lo_m"] for e in ends)
    L_hi = w_net + sum(e["ext_hi_m"] for e in ends)
    flagged = any(e["state"] in (DEFICIT, HELD) for e in ends)
    rec = {"id": lintel["id"], "rule": RULE_ID, "width_m": w, "span_in_column_m": strip, "w_net_m": w_net, "B": B, "D": D,
           "t453_length_m": t453_len, "t453_concrete_m3": lintel["t453_concrete_m3"],
           "t453_formwork_m2": lintel.get("t453_formwork_m2"),
           "length_lo_m": _r6(L_lo), "length_hi_m": _r6(L_hi),
           "concrete_lo_m3": _r6(B * D * L_lo), "concrete_hi_m3": _r6(B * D * L_hi),
           "formwork_lo_m2": _r6(2 * L_lo * D + w_net * B), "formwork_hi_m2": _r6(2 * L_hi * D + w_net * B),
           "state": "HELD_BY_NAME" if flagged else "MIN_BEARING_LOWER_BOUND",
           "span_strip_inside_column_m3": _r6(B * D * strip), "span_strip_column": lintel.get("span_column_id"),
           "ends": ends}
    return rec


def assess_pair(l1, l2, rec1, rec2, b_min=B_MIN):
    """Two lintels sharing one pier: the pier is occupied once; the T-453 overlap is lintel on lintel."""
    e1 = [e for e in rec1["ends"] if e["pier_shared_with"] == l2["id"]]
    e2 = [e for e in rec2["ends"] if e["pier_shared_with"] == l1["id"]]
    if len(e1) != 1 or len(e2) != 1:
        raise Refused(f"pier {l1['id']} / {l2['id']} listed on one side only")
    p1, p2 = e1[0]["available_m"], e2[0]["available_m"]
    if abs(p1 - p2) > 1e-6:
        raise Refused(f"pier {l1['id']} / {l2['id']}: two values {p1} / {p2}")
    if (l1["B"], l1["D"]) != (l2["B"], l2["D"]):
        raise Refused(f"pair {l1['id']} / {l2['id']}: different sections, overlap not a shared volume")
    if l1.get("head_m") is None or l1.get("head_m") != l2.get("head_m"):
        raise Refused(f"pair {l1['id']} / {l2['id']}: heads not equal / not known, overlap in elevation not established")
    p, B, D = p1, l1["B"], l1["D"]
    o1 = [e for e in rec1["ends"] if e is not e1[0]][0]
    o2 = [e for e in rec2["ends"] if e is not e2[0]][0]
    overlap = max(0.0, 2 * b_min - p)
    L_lo = rec1["w_net_m"] + o1["ext_lo_m"] + rec2["w_net_m"] + o2["ext_lo_m"]
    L_hi = rec1["w_net_m"] + o1["ext_hi_m"] + rec2["w_net_m"] + o2["ext_hi_m"] + min(p, 2 * b_min)
    return {"pair": [l1["id"], l2["id"]], "pier_m": p, "head_m": l1["head_m"], "B": B, "D": D,
            "t453_overlap_m": _r6(overlap), "lintel_on_lintel_m3": _r6(B * D * overlap),
            "length_lo_m": _r6(L_lo), "length_hi_m": _r6(L_hi),
            "concrete_lo_m3": _r6(B * D * L_lo), "concrete_hi_m3": _r6(B * D * L_hi),
            "formwork_lo_m2": _r6(2 * L_lo * D + (rec1["w_net_m"] + rec2["w_net_m"]) * B),
            "formwork_hi_m2": _r6(2 * L_hi * D + (rec1["w_net_m"] + rec2["w_net_m"]) * B),
            "host_face_overdeduct_min_m2": _r6(D * overlap),
            "why": ("the two T-453 end zones overlap by 2 b_min - p along the wall line; one lintel over both "
                    "openings or two meeting in the pier occupy the pier once; per-lintel split HELD (designer)")}


def assess_set(lintels, pairs=(), b_min=B_MIN):
    ids = [l["id"] for l in lintels]
    if len(ids) != len(set(ids)):
        raise Refused("a second record for one lintel")
    by = {l["id"]: l for l in lintels}
    recs = {l["id"]: assess_lintel(l, b_min) for l in lintels}
    paired, prs = set(), []
    for a_id, b_id in pairs:
        prs.append(assess_pair(by[a_id], by[b_id], recs[a_id], recs[b_id], b_min))
        paired |= {a_id, b_id}
    for rid, r in recs.items():
        if rid not in paired and any(e["pier_shared_with"] for e in r["ends"]):
            raise Refused(f"{rid}: shared pier without its pair")
    t453 = sum(l["t453_concrete_m3"] for l in lintels)
    lo = sum(r["concrete_lo_m3"] for k, r in recs.items() if k not in paired) + sum(p["concrete_lo_m3"] for p in prs)
    hi = sum(r["concrete_hi_m3"] for k, r in recs.items() if k not in paired) + sum(p["concrete_hi_m3"] for p in prs)
    inside, not_built, held_split = {}, 0.0, []
    for r in recs.values():
        BD = r["B"] * r["D"]
        if r["span_in_column_m"]:
            key = r["span_strip_column"] or "column not identified"
            inside[key] = inside.get(key, 0.0) + BD * r["span_in_column_m"]
        for e in r["ends"]:
            if e["state"] != DEFICIT or e["stopper"] == OPENING:
                continue
            if e["inside_column_m"] is None:
                held_split.append(f"{r['id']} {e['side']}")
                continue
            if e["inside_column_m"]:
                inside[e["host"]["id"]] = inside.get(e["host"]["id"], 0.0) + BD * e["inside_column_m"]
            not_built += BD * e["not_built_m"]
    on_lintel = sum(p["lintel_on_lintel_m3"] for p in prs)
    removed = t453 - hi
    if not held_split:
        acc = sum(inside.values()) + on_lintel + not_built
        if abs(acc - removed) > 1e-6:
            raise Refused(f"conservation: removed {removed} != inside {sum(inside.values())} + on-lintel {on_lintel} "
                          f"+ not built {not_built}")
    return {"rule": RULE_ID, "lintels": recs, "pairs": prs,
            "summary": {"t453_m3": _r6(t453), "corrected_lo_m3": _r6(lo), "corrected_hi_m3": _r6(hi),
                        "removed_m3": _r6(removed), "inside_column_m3": {k: _r6(v) for k, v in sorted(inside.items())},
                        "inside_column_total_m3": _r6(sum(inside.values())), "lintel_on_lintel_m3": _r6(on_lintel),
                        "not_built_m3": _r6(not_built), "split_held": held_split,
                        "t453_formwork_m2": _r6(sum(l.get("t453_formwork_m2") or 0 for l in lintels)),
                        "formwork_hi_m2": _r6(sum(r["formwork_hi_m2"] for k, r in recs.items() if k not in paired)
                                              + sum(p["formwork_hi_m2"] for p in prs)),
                        "formwork_lo_m2": _r6(sum(r["formwork_lo_m2"] for k, r in recs.items() if k not in paired)
                                              + sum(p["formwork_lo_m2"] for p in prs)),
                        "end_stop_faces_max_m2": _r6(sum(e["end_stop_face_max_m2"] for r in recs.values()
                                                         for e in r["ends"])),
                        "cross_wall_window_max_m2": _r6(sum(e["cross_wall_window_max_m2"] for r in recs.values()
                                                            for e in r["ends"])),
                        "host_face_overdeduct_min_m2": _r6(sum(e["host_face_overdeduct_min_m2"] for r in recs.values()
                                                               for e in r["ends"]) +
                                                           sum(p["host_face_overdeduct_min_m2"] for p in prs))}}


# ---------------------------------------------------------------------------------------------- training villa (data)
T516 = ROOT / "research" / "agents_t516" / "out" / "JAMB_BEARING_T516.json"
T516_EV = ROOT / "research" / "agents_t516" / "out" / "JAMB_EVIDENCE_T516.csv"
T453 = ROOT / "research" / "agents_t453" / "out" / "LINTELS_T453.csv"
CENSUS = ROOT / "research" / "alsenan_lintels_s8_6" / "01_OPENING_CENSUS.csv"
XWALK = ROOT / "research" / "R9_1_CHRIS_POST_FREEZE" / "09_COLUMN_CROSSWALK.csv"

# T-175 host id -> S8.6 census opening (floor, width, wall thickness, the rooms on its two sides; the column gap the
# builder re-derives below must reproduce the T-516 a within FRAME_TOL_M, otherwise the build is refused)
CENSUS_OF = {"D-1F-04": "OP-1F-006", "D-2F-03": "OP-2F-007", "D-GF-06": "OP-GF-015", "W18": "OP-1F-026"}
# W18 start jamb lies 32.7 mm inside column C8 (2FD8): ELEMENT_REGISTER 'Opening OP-1F-026 (W18 of 1F-W00)', VERIFIED by
# two routes (T-274 MERGED aba9399a); the column face owns that strip of the span.
SPAN_IN_COLUMN = {"W18": (0.0327, "COL-C8-X15-Y06-1F")}
# candidate V3.0.56 / V3.0.58 STR.CONC.COLUMN lines (LINE_INDEX, value = section x storey height): named for the Lead
CANDIDATE_LINE = {
    "COL-PC-X08-Y02-1F": "HL:PLANTED_COLUMN:PC-1F-A:CONCRETE (RELEASED 0.588 = 0.70 x 0.20 x 4.20; by section match)",
    "COL-C2-X10-Y09-2F": "one of the four P-C:COL:SH12:C2@...|2F lines, all HELD (sheet-frame id not pinned here)",
    "COL-C6-X08-Y04-GF": "P-C:COL:SH12:C6@250087,56100|GF (RELEASED 0.7875 = 0.25 x 0.70 x 4.50; the only C6|GF line)",
    "COL-C8-X15-Y06-1F": "P-C:COL:SH12:C8@262766,57890|1F (RELEASED 0.756 = 0.20 x 0.90 x 4.20; the other C8|1F line is "
                         "X12-Y02 with the drawn 80x25 / schedule 20x90 conflict, HELD 0.756 .. 0.84)",
}


def _columns():
    """One entry per (column, storey occurrence): the drawn outline position of the plan that carries that storey
    (CHRIS_INTERVALS), e.g. C8 X15-Y06 1F is the 31658 / 15087 outline, its GF / neck outline is 150 mm away."""
    cols = []
    for c in csv.DictReader(XWALK.open(encoding="utf-8")):
        m = re.match(r"COLPOS-(X\d+-Y\d+)-(\d+)-(\d+)", c["URBAN_CHAIN"] or "")
        if not m or not c["TYPE_URBAN"]:
            continue
        typ = c["TYPE_URBAN"].replace(".", "")
        x = float(c["X_LOCAL"]) if c["X_LOCAL"] else float(m.group(2))
        y = float(c["Y_LOCAL"]) if c["Y_LOCAL"] else float(m.group(3))
        sec = json.loads(c["SECTION_URBAN_BY_FLOOR"] or "{}")
        floors = [f for f in (c["CHRIS_INTERVALS"] or c["URBAN_FLOORS"] or "").split("|") if f]
        for fl in floors:
            cols.append((typ, m.group(1), fl, x, y, sec))
    return cols


def column_at(opening_id, a_m, census, cols):
    """The column beside a COLUMN-stopped deficit end: re-derived in the structural frame, must reproduce a."""
    r = census[CENSUS_OF[opening_id]]
    x, y = json.loads(r["CENTRE_STRUCT_XY"])
    ang = float(r["WALL_ANGLE_DEG"])
    if ang not in (0.0, 90.0):
        raise Refused(f"{opening_id}: wall angle {ang} not handled")
    ux, uy = (1.0, 0.0) if ang == 0.0 else (0.0, 1.0)
    half_w = float(r["WIDTH_MM"]) / 2.0
    t = float(r["WALL_THICKNESS_MM"]) / 1000.0
    fl = r["FLOOR"]
    best = []
    for (typ, grid, cfl, cx, cy, sec) in cols:
        if cfl != fl or fl not in sec:
            continue
        m = re.fullmatch(r"(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)", str(sec[fl]).strip().lower())
        if not m:
            continue                                  # a section that is not 'A x B' cm is never read as a size
        sx, sy = float(m.group(1)) / 100.0, float(m.group(2)) / 100.0
        along_dim, across_dim = (sx, sy) if ang == 0.0 else (sy, sx)
        s = ((cx - x) * ux + (cy - y) * uy) / 1000.0
        o = ((cx - x) * -uy + (cy - y) * ux) / 1000.0
        cover = min(o + across_dim / 2, t / 2) - max(o - across_dim / 2, -t / 2)
        if cover <= t / 2:
            continue
        gap = abs(s) - along_dim / 2 - half_w / 1000.0
        if abs(gap - a_m) <= FRAME_TOL_M:
            best.append({"id": f"COL-{typ}-{grid}-{fl}", "along_m": along_dim, "across_m": across_dim,
                         "expected_gap_m": round(a_m, 4),
                         "gap_struct_frame_m": round(gap, 4), "covers_wall_width": cover >= t - FRAME_TOL_M, "cover_m": round(cover, 4),
                         "candidate_line": CANDIDATE_LINE.get(f"COL-{typ}-{grid}-{fl}", "not named")})
    if len(best) != 1:
        raise Refused(f"{opening_id}: {len(best)} columns reproduce a = {a_m} within {FRAME_TOL_M} m")
    return best[0]


def villa_inputs():
    doc = json.loads(T516.read_text(encoding="utf-8"))
    t453 = {r["opening_id"]: r for r in csv.DictReader(T453.open(encoding="utf-8"))}
    ev = {(r["opening_id"], r["side"]): r for r in csv.DictReader(T516_EV.open(encoding="utf-8"))}
    census = {r["OPENING_ID"]: r for r in csv.DictReader(CENSUS.open(encoding="utf-8"))}
    cols = _columns()
    lintels = []
    for row in doc["rows"]:
        if not any(e["state"] == DEFICIT for e in row["ends"]):
            continue
        oid = row["opening_id"]
        t = t453[oid]
        L = float(t["length_m"])
        B = float(t["wall_t_m"])
        D = round(float(t["concrete_m3"]) / (B * L), 6)
        ends = []
        for e in row["ends"]:
            x = {"side": e["side"], "state": e["state"], "available_m": e["available_m"], "stopper": e["stopper"],
                 "stopper_id": e.get("stopper_id", ""), "through_walls": ev[(oid, e["side"])]["through_walls"]}
            ends.append(x)
        strip, strip_col = SPAN_IN_COLUMN.get(oid, (0.0, None))
        for x in ends:
            if x["state"] == DEFICIT and x["stopper"] == COLUMN:
                # a jamb drawn inside the column has a negative face gap (T-516 a is clamped at 0)
                x["host"] = column_at(oid, x["available_m"] - strip, census, cols)
        lintels.append({"id": oid, "width_m": float(t["width_m"]), "B": B, "D": D, "t453_length_m": L,
                        "t453_concrete_m3": float(t["concrete_m3"]), "t453_formwork_m2": float(t["formwork_m2"]),
                        "head_m": float(t["head_above_ffl_m"]) if t["head_above_ffl_m"] else None,
                        "span_in_column_m": strip, "span_column_id": strip_col, "ends": ends})
    pairs = []
    for l in lintels:
        for e in l["ends"]:
            if e["state"] == DEFICIT and e["stopper"] == OPENING and l["id"] < e["stopper_id"]:
                pairs.append((l["id"], e["stopper_id"]))
    return lintels, pairs


def build():
    lintels, pairs = villa_inputs()
    out = assess_set(lintels, pairs)
    out["drawing"] = ("numbers only, from committed records: T-516 jamb census (P7757.dxf sha ab54dd55 through the merged "
                      "MASONRY_CENTRELINE_V2), T-453 r2 lintel ledger, S8.6 opening census and the R9.1 column crosswalk "
                      "(ST7757 plans, schedule p.9)")
    return out
