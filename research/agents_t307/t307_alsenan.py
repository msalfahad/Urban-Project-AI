"""T-307 Alsenan run (development villa; research ledger, nothing wired, no candidate or released kg changed).

Stage 1 (needs the private faces file, written only into the git-excluded private folder by T-139 slab_faces.py from
Drive "Alsenan chalet project" / "ST7757 dxf.dxf"):
    python3 -I research/agents_t307/t307_alsenan.py --geometry <private faces.json>
  -> BAR_END_CENSUS_T307.csv: per candidate development line, the number of bar ends per support class at readings A
     and B, the summed straight lengths of the EDGE_BEAM ends, and the T-152 continuity cross-check (numbers only, no
     coordinates, no drawing content).
Stage 2 (merged research files + the committed census only):
    python3 -I research/agents_t307/t307_alsenan.py --write | --check
  -> BAR_END_SUMMARY_T307.json, LANE_I_CONSUMER_T307.csv (line id -> proposed status / bound / held items).
"""

import csv
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import t307_bar_ends as be  # noqa: E402

T306_CSV = os.path.join(ROOT, "research", "agents_t306", "SLAB_SPREAD_DECOMPOSITION_T306.csv")
T152_CSV = os.path.join(ROOT, "research", "agents_t152", "T152_SLAB_STEEL.csv")
T152_INPUT = os.path.join(ROOT, "research", "agents_t152", "T152_INPUT.csv")
PANELS = os.path.join(ROOT, "research", "agents_t139", "PANELS.csv")
T149 = os.path.join(ROOT, "research", "agents_t149", "T149_SPANS_INPUT.csv")
T213 = os.path.join(ROOT, "research", "agents_t213", "SUNKEN_PANELS_T213.json")
CENSUS = os.path.join(HERE, "BAR_END_CENSUS_T307.csv")
DETAIL = os.path.join(HERE, "BAR_END_DETAIL_T307.csv")
SUMMARY = os.path.join(HERE, "BAR_END_SUMMARY_T307.json")
CONSUMER = os.path.join(HERE, "LANE_I_CONSUMER_T307.csv")
CLASSES = list(be.SUPPORT_CLASSES)
IRR_CODES = {"composite": "COMPOSITE_SUPPORT", "short piece": "SHORT_PIECE_COLUMN_OR_JUNCTION",
             "crossing": "OBLIQUE_OR_PARTIAL_CROSSING", "mark": "MARK_WIDTH_CONFLICT",
             "support not crossed": "SUPPORT_NOT_CROSSED"}
DOME_SPLIT = {"1F-073": (16.380, 41.651, 2.4111), "1F-076": (30.828, 41.651, 2.4111)}   # T-139 slab_ledger / T-152
DEV = "DEVELOPMENT / ANCHORAGE"


def rows(p):
    csv.field_size_limit(10 ** 9)
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ------------------------------------------------------------------------------------------------ stage 1 (private)
def geometry(faces_json):
    from shapely import wkt
    sys.path.insert(0, os.path.join(ROOT, "research", "agents_t152"))
    import t152_slab_steel as t152  # noqa: E402  (read only: bar placement)
    import t307_geometry as tg  # noqa: E402

    faces = json.load(open(faces_json))
    panels = {r["id"]: r for r in rows(PANELS)}
    sunken = {p[0] for p in json.load(open(T213))["t139_match"]["pairs"]}
    marks = defaultdict(list)
    for r in rows(T149):
        marks[(r["floor"], r["mark"])].append(r["width_m"])
    from shapely.geometry import Point
    by_sheet = {}
    for sh, fl in faces.items():
        d = {}
        for f in fl:
            p = panels.get(f["id"])
            if p is None:
                raise ValueError(f"face {f['id']} not in the T-139 panel table")
            poly = wkt.loads(f["wkt"])
            if f["id"] in DOME_SPLIT:       # T-139 / T-152: the dome face keeps the ring, its corners are slab rows
                cx, cy, r_out = DOME_SPLIT[f["id"]]
                disc = Point(cx, cy).buffer(r_out, quad_segs=256)
                parts = poly.difference(disc)
                k = 0
                for c in getattr(parts, "geoms", [parts]):
                    if c.area >= 0.02:
                        cid = "%s/c%d" % (f["id"], k)
                        cp = panels[cid]
                        if abs(float(cp["area"]) - c.area) > 1e-3:
                            raise ValueError(f"dome corner {cid} area differs from T-139")
                        mr = c.minimum_rotated_rectangle.exterior.coords
                        dd = sorted([((mr[0][0] - mr[1][0]) ** 2 + (mr[0][1] - mr[1][1]) ** 2) ** 0.5,
                                     ((mr[1][0] - mr[2][0]) ** 2 + (mr[1][1] - mr[2][1]) ** 2) ** 0.5])
                        d[cid] = dict(poly=c, cls=cp["cls"], w=dd[0], l=dd[1], marks=[])
                        k += 1
                poly = poly.intersection(disc)
            if abs(float(p["area"]) - poly.area) > 1e-3:
                raise ValueError(f"face {f['id']} area differs from T-139: not the same drawing file")
            d[f["id"]] = dict(poly=poly, cls=p["cls"], w=f["w"], l=f["l"],
                              marks=[t for t in f["texts"] if t[:1] in "BC" and t[1:2] in "B0123456789"])
        by_sheet[sh] = d
    slab_ids = [i for i, p in panels.items() if p["cls"] == "SLAB"]
    dev = [r for r in rows(T306_CSV) if r["population"] == DEV]
    inp = {(f"SLAB:{r['panel']}", r["dir"]): r for r in rows(T152_INPUT)}
    out, detail = [], []
    for r in dev:
        ir = inp[(r["element"], r["direction"])]
        pid, axis = ir["panel"], ir["dir"]
        sh = pid.split("-")[0]
        faces_sh = by_sheet[sh]
        others = [(q, faces_sh[q]["poly"]) for q in slab_ids if q.startswith(sh + "-") and q != pid]
        mw = {mk: ws for (fl, mk), ws in marks.items() if fl == sh}
        mesh = json.loads(ir["mesh"])
        res = tg.classify_panel(pid, faces_sh[pid]["poly"], axis, len(mesh["A"]), faces_sh, others, sunken, mw,
                                t152._segments)
        o = dict(line_id=r["line_id"], element=r["element"], direction=axis, d_mm=int(r["d_mm"]),
                 layers=int(r["layers"]), bars_A=len(mesh["A"]), bars_B=len(mesh["B"]))
        mism = 0
        beyond = Counter()
        irr = Counter()
        pc = Counter()
        sb_ = Counter()
        for tag in ("A", "B"):
            cnt = Counter()
            ext = 0.0
            adj = 0
            bar_ext = []
            for bi, (segs, tsegs) in enumerate(zip(res[tag], mesh[tag])):
                if len(segs) != len(tsegs):
                    raise ValueError(f"{r['line_id']}: bar line segments differ from T-152")
                bsum = 0.0
                for si, ((ln, e0, e1), (tln, t0, t1)) in enumerate(zip(segs, tsegs)):
                    if abs(ln - tln) > 1e-4:
                        raise ValueError(f"{r['line_id']}: segment length differs from T-152")
                    for side, e, te in (("lo", e0, t0), ("hi", e1, t1)):
                        detail.append(dict(line_id=r["line_id"], element=r["element"], direction=axis, reading=tag,
                                           bar=bi, segment=si, end=side, seg_len_m=ln, support=e["cls"],
                                           width_m="" if e["w"] is None else e["w"], pieces=e["pieces"],
                                           beyond=e["beyond"], neighbour=e["neighbour"], note=e["note"]))
                        probe_cont = e["cls"] in ("CONTINUOUS", "STEP_EDGE") and e["beyond"] == "SLAB" \
                            and e["pieces"] == 0
                        mism += int(probe_cont != bool(te[0]))
                        if probe_cont:
                            pc[tag] += 1
                        if e["cls"] == "IRREGULAR_SUPPORT":
                            for nt in e["note"].split("; "):
                                irr[(tag, IRR_CODES[next(k for k in IRR_CODES if nt.startswith(k))])] += 1
                        cnt[e["cls"]] += 1
                        beyond[(tag, e["cls"], e["beyond"])] += 1
                        if e["beyond"] == "SLAB" and e["pieces"] > 0:
                            sb_[tag] += 1
                        if e["cls"] == "EDGE_BEAM":
                            s = be.end_basis("EDGE_BEAM", o["d_mm"], w_m=e["w"])["straight_m"]
                            ext += s
                            bsum += s
                            if e["beyond"] in ("EDGE_HELD", "NOT_THIS_SLAB", "NOT_SLAB"):
                                adj += 1
                bar_ext.append(bsum)
            for c in CLASSES:
                o[f"n{tag}_{c}"] = cnt.get(c, 0)
            o[f"ext{tag}_m"] = round(ext, 4)
            o[f"adjacent_beyond_{tag}"] = adj
            o[f"bar_ext_min_{tag}"] = round(min(bar_ext), 4) if bar_ext else ""
            o[f"bar_ext_max_{tag}"] = round(max(bar_ext), 4) if bar_ext else ""
        # the top bars over the supports (note-2 rate 5 / m lines, T-152 'top' geometry): the same support classes,
        # for the top-line consumer (O-T306-01: 'EXTEND 50% OF TOP REINF. INTO ADJACENT SLAB WHERE POSSIBLE')
        top = json.loads(ir["top"])
        tres = tg.classify_panel(pid, faces_sh[pid]["poly"], axis, len(top["A"]), faces_sh, others, sunken, mw,
                                 t152._segments)
        for tag in ("A", "B"):
            tc, tadj, tsb = Counter(), 0, 0
            for segs, tsegs in zip(tres[tag], top[tag]):
                for (ln, e0, e1), (tln, t0, t1) in zip(segs, tsegs):
                    if abs(ln - tln) > 1e-4:
                        raise ValueError(f"{r['line_id']}: top segment length differs from T-152")
                    for e, te in ((e0, t0), (e1, t1)):
                        pcont = e["cls"] in ("CONTINUOUS", "STEP_EDGE") and e["beyond"] == "SLAB" and e["pieces"] == 0
                        mism += int(pcont != bool(te[0]))
                        tc[e["cls"]] += 1
                        if e["beyond"] == "SLAB" and e["pieces"] > 0:
                            tsb += 1
                        if e["cls"] == "EDGE_BEAM" and e["beyond"] in ("EDGE_HELD", "NOT_THIS_SLAB", "NOT_SLAB"):
                            tadj += 1
            for c in CLASSES:
                o[f"top{tag}_{c}"] = tc.get(c, 0)
            o[f"top_adjacent_beyond_{tag}"] = tadj
            o[f"top_slab_beyond_wide_support_{tag}"] = tsb
        o["probe_cont_A"], o["probe_cont_B"] = pc["A"], pc["B"]
        o["slab_beyond_wide_support_A"], o["slab_beyond_wide_support_B"] = sb_["A"], sb_["B"]
        o["t152_continuity_mismatch"] = mism
        o["irregular"] = ";".join("%s:%s=%d" % (k[0], k[1], v) for k, v in sorted(irr.items()))
        o["beyond"] = ";".join("%s:%s>%s=%d" % (k[0], k[1], k[2], v) for k, v in sorted(beyond.items()))
        out.append(o)
    with open(CENSUS, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    with open(DETAIL, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(detail[0]))
        w.writeheader()
        w.writerows(detail)
    print("census written", len(out), "lines; T-152 continuity mismatches", sum(o["t152_continuity_mismatch"]
                                                                               for o in out))
    return out


# ------------------------------------------------------------------------------------------------ stage 2
def _row(r, status, lo, hi, status_note, nA, nB, held, basis):
    """lane I consumer shape: one row per candidate line id."""
    return dict(line_id=r["line_id"], element=r["element"], direction=r["direction"], population=r["population"],
                candidate_low_kg=r["low_kg"], candidate_high_kg=r["high_kg"], proposed_status=status,
                valued_low_kg="" if status == "HELD" else round(lo, 3),     # HELD stays blank, never 0
                valued_high_kg="" if status == "HELD" else round(hi, 3), status_note=status_note,
                ends_A=";".join("%s=%d" % kv for kv in sorted(nA.items())),
                ends_B=";".join("%s=%d" % kv for kv in sorted(nB.items())),
                held_items=" | ".join(held), basis=basis)


def run():
    cen = {r["line_id"]: r for r in rows(CENSUS)}
    dec = rows(T306_CSV)
    devs = [r for r in dec if r["population"] == DEV]
    if set(cen) != {r["line_id"] for r in devs}:
        raise ValueError("census lines differ from the candidate development lines")
    T = defaultdict(float)
    N = Counter()
    consumer, label_lines = [], []
    for r in devs:
        c = cen[r["line_id"]]
        d, lay = int(r["d_mm"]), int(r["layers"])
        nA = {k: int(c[f"nA_{k}"]) for k in CLASSES if int(c[f"nA_{k}"])}
        nB = {k: int(c[f"nB_{k}"]) for k in CLASSES if int(c[f"nB_{k}"])}
        cl = be.close_line(r["line_id"], float(r["low_kg"]), float(r["high_kg"]), nA, nB, int(c["bars_A"]),
                           int(c["bars_B"]), d, lay)
        for k, v in cl["class_low"].items():
            T["cand_low_" + k] += v
        for k, v in cl["class_high"].items():
            T["cand_high_" + k] += v
        T["cand_unbooked_low"] += cl["unbooked_low"]
        T["cand_unbooked_high"] += cl["unbooked_high"]
        T["cand_low"] += float(r["low_kg"])
        T["cand_high"] += float(r["high_kg"])
        T["rounding_low"] += cl["rounding_low"]
        T["rounding_high"] += cl["rounding_high"]
        for k in CLASSES:
            N["A_" + k] += nA.get(k, 0)
            N["B_" + k] += nB.get(k, 0)
        lo_e, hi_e = be.candidate_end_kg(d, lay)
        sp_a = int(c["probe_cont_A"]) - nA.get("CONTINUOUS", 0)      # STEP_EDGE ends found by the T-152 probe
        sp_b = int(c["probe_cont_B"]) - nB.get("CONTINUOUS", 0)
        T["step_probe_low"] += sp_a * lo_e
        T["step_probe_high"] += sp_b * hi_e
        lo, hi = be.straight_bound(float(c["extA_m"]), float(c["extB_m"]), d, 1)
        readings = {"A": float(c["extA_m"]) * be.kgm(d), "B": float(c["extB_m"]) * be.kgm(d)}
        if r["label_status"] == "HELD_LABEL":          # bare '5 o 10': 5 bars in all is a reading (T-306 F-04)
            n5 = int(r["printed"].split("ø")[0].split("o")[0])
            mins = [float(c[f"bar_ext_min_{t}"]) for t in "AB" if c[f"bar_ext_min_{t}"] != ""]
            maxs = [float(c[f"bar_ext_max_{t}"]) for t in "AB" if c[f"bar_ext_max_{t}"] != ""]
            if mins:
                r5lo, r5hi = n5 * min(mins) * be.kgm(d), n5 * max(maxs) * be.kgm(d)
                lo, hi = min(lo, r5lo), max(hi, r5hi)
                readings.update({"five_in_all_low": r5lo, "five_in_all_high": r5hi})
                label_lines.append(dict(line=r["line_id"], element=r["element"], direction=r["direction"],
                                        old_basis_low_corrected=round(n5 * 2 * be.DEV_K[0] * d / 1000 * be.kgm(d)
                                                                      * lay, 3),
                                        new_low=round(lo, 3), new_high=round(hi, 3)))
        be.contains(r["line_id"], lo, hi, readings)
        status = be.proposed_status(set(nA) | set(nB))
        held = []
        upA, upB = int(c["nA_EDGE_BEAM"]), int(c["nB_EDGE_BEAM"])
        if upA or upB:
            held.append("UPTURN_LEG at %d..%d edge-beam ends: on the curtailed half (p.15 trace, T-307) .. on every "
                        "bar (Checker T-306 reading); leg not dimensioned" % (min(upA, upB), max(upA, upB)))
        if lay == 2 and (upA or upB):
            held.append("TB_TOP_LAYER_ENDS %d..%d (no top-mesh end drawn)" % (min(upA, upB), max(upA, upB)))
        for k in ("STEP_EDGE", "OPENING_EDGE", "IRREGULAR_SUPPORT"):
            a, b = nA.get(k, 0), nB.get(k, 0)
            if a or b:
                held.append("%s ends %d..%d" % (k, min(a, b), max(a, b)))
        ub = (sum(nA.values()) - 2 * int(c["bars_A"]), sum(nB.values()) - 2 * int(c["bars_B"]))
        if any(ub):
            held.append("UNBOOKED_SEGMENT_ENDS %d..%d (counted in the classes above; the candidate books 2 per bar "
                        "line)" % (min(ub), max(ub)))
        T["new_low"] += lo
        T["new_high"] += hi
        consumer.append(_row(r, status, lo, hi, "DRAWING_DERIVED_LENGTH_COUNT_BOUND" if (upA or upB) else "",
                             nA, nB, held, "development re-based end by end on p.15 (note-9 40 d .. 70 d dropped)"))
    # F-02 / F-03: top lines (old basis, corrected bounds; T-306 readings)
    s306 = json.load(open(os.path.join(ROOT, "research", "agents_t306", "SLAB_SPREAD_SUMMARY_T306.json")))
    outs = s306["readings_outside_bound"]
    tops = {r["line_id"]: r for r in dec if r["population"] == "TOP BARS OVER SUPPORTS"}
    corr = {}
    for o in outs:
        lid = o["line"]
        if lid in tops:
            lo0, hi0 = corr.get(lid, (float(tops[lid]["low_kg"]), float(tops[lid]["high_kg"])))
            corr[lid] = (min(lo0, o["kg"]), max(hi0, o["kg"]))
    f02 = {k: v for k, v in corr.items() if v[0] == 0.0}
    f03 = {k: v for k, v in corr.items() if v[0] != 0.0}
    bottom = [r for r in dec if r["population"] == "BOTTOM MESH"]
    by_el = {(c["element"], c["direction"]): c for c in cen.values()}
    for r in tops.values():          # top lines: support classes of the note-2 bar ends; F-02 / F-03 bounds
        c = by_el[(r["element"], r["direction"])]
        tA = {k: int(c[f"topA_{k}"]) for k in CLASSES if int(c[f"topA_{k}"])}
        tB = {k: int(c[f"topB_{k}"]) for k in CLASSES if int(c[f"topB_{k}"])}
        lo, hi = corr.get(r["line_id"], (float(r["low_kg"]), float(r["high_kg"])))
        held = []
        a, b = tA.get("EDGE_BEAM", 0), tB.get("EDGE_BEAM", 0)
        if a or b:
            held.append("HOOK_DOWN_LEG of the 0.25 L1 anchor bar at %d..%d edge-beam ends (drawn, not dimensioned; "
                        "not in any top reading)" % (min(a, b), max(a, b)))
        ca, cb = int(c["top_adjacent_beyond_A"]), int(c["top_adjacent_beyond_B"])
        if ca or cb:
            held.append("CONDITIONAL_EXTENSION 'EXTEND 50%% OF TOP REINF. INTO ADJACENT SLAB WHERE POSSIBLE' at "
                        "%d..%d edge-beam ends with concrete beyond (UNRESOLVED, blank; length not printed)"
                        % (min(ca, cb), max(ca, cb)))
        for k in ("STEP_EDGE", "OPENING_EDGE", "IRREGULAR_SUPPORT"):
            a, b = tA.get(k, 0), tB.get(k, 0)
            if a or b:
                held.append("%s ends %d..%d (p.15 extent / crossing not drawn there)" % (k, min(a, b), max(a, b)))
        a, b = int(c["top_slab_beyond_wide_support_A"]), int(c["top_slab_beyond_wide_support_B"])
        if a or b:
            held.append("SLAB_BEYOND_WIDE_SUPPORT ends %d..%d: a slab lies past a support wider than the T-152 0.80 m "
                        "probe; T-152 booked them non-continuous (0.25 L1, no crossing)" % (min(a, b), max(a, b)))
        consumer.append(_row(r, "BOUND_CORRECTED" if r["line_id"] in corr else "BOUND", lo, hi,
                             "F-02 (T&B low 0)" if lo == 0.0 and r["line_id"] in corr else
                             ("F-03 (skew envelope)" if r["line_id"] in corr else ""), tA, tB, held,
                             "top bars: support classes for the follow-up; kg unchanged except F-02 / F-03"))
    for r in bottom:                 # bottom lines: ends whose p.15 curtailment / crossing case is not settled
        c = by_el[(r["element"], r["direction"])]
        nA = {k: int(c[f"nA_{k}"]) for k in CLASSES if int(c[f"nA_{k}"])}
        nB = {k: int(c[f"nB_{k}"]) for k in CLASSES if int(c[f"nB_{k}"])}
        held = []
        a, b = nA.get("STEP_EDGE", 0), nB.get("STEP_EDGE", 0)
        if a or b:
            held.append("STEP_EDGE ends %d..%d: T-152 booked the p.15 continuous case (curtailment + crossing half) at "
                        "a sunken-panel level step that no detail draws" % (min(a, b), max(a, b)))
        a, b = int(c["slab_beyond_wide_support_A"]), int(c["slab_beyond_wide_support_B"])
        if a or b:
            held.append("SLAB_BEYOND_WIDE_SUPPORT ends %d..%d: T-152 booked them non-continuous (no curtailment, no "
                        "crossing); a slab lies past a support wider than its 0.80 m probe" % (min(a, b), max(a, b)))
        consumer.append(_row(r, "BOUND_FLAGGED" if held else "BOUND", float(r["low_kg"]), float(r["high_kg"]), "",
                             nA, nB, held, "bottom mesh: kg unchanged; flags for the follow-up"))
    top_lo = sum(corr.get(r["line_id"], (float(r["low_kg"]),))[0] for r in tops.values())
    top_hi = sum(corr.get(r["line_id"], (0, float(r["high_kg"])))[1] for r in tops.values())
    bot_lo = sum(float(r["low_kg"]) for r in bottom)
    bot_hi = sum(float(r["high_kg"]) for r in bottom)
    total_ends = {k: (N["A_" + k], N["B_" + k]) for k in CLASSES}
    summ = dict(
        dev_lines=len(devs),
        ends_by_class_A_B=total_ends,
        candidate_dev_kg=dict(low=round(T["cand_low"], 3), high=round(T["cand_high"], 3)),
        candidate_dev_by_class_kg={k: (round(T["cand_low_" + k], 3), round(T["cand_high_" + k], 3)) for k in CLASSES},
        candidate_unbooked_kg=(round(T["cand_unbooked_low"], 3), round(T["cand_unbooked_high"], 3)),
        closure_rounding_kg=(round(T["rounding_low"], 6), round(T["rounding_high"], 6)),
        dev_spread_candidate_basis_by_class_kg={k: round(T["cand_high_" + k] - T["cand_low_" + k], 3)
                                                for k in CLASSES},
        dev_spread_on_t152_continuous_ends_kg=round(T["cand_high_CONTINUOUS"] - T["cand_low_CONTINUOUS"]
                                                    + T["step_probe_high"] - T["step_probe_low"], 3),
        new_dev_straight_kg=dict(low=round(T["new_low"], 3), high=round(T["new_high"], 3)),
        f02_tank_top_lines=sorted([dict(line=k, low=v[0], high=v[1]) for k, v in f02.items()],
                                  key=lambda x: x["line"]),
        f03_skew_top_line=sorted([dict(line=k, low=round(v[0], 3), high=round(v[1], 3)) for k, v in f03.items()],
                                 key=lambda x: x["line"]),
        f04_label_lines=label_lines,
        slab_bound_t306_kg=dict(low=4643.766, high=6832.326),
        slab_bound_restated_kg=dict(
            bottom=(round(bot_lo, 3), round(bot_hi, 3)), top=(round(top_lo, 3), round(top_hi, 3)),
            development_valued=(round(T["new_low"], 3), round(T["new_high"], 3)),
            low=round(bot_lo + top_lo + T["new_low"], 3), high=round(bot_hi + top_hi + T["new_high"], 3)),
        proposed_status_counts={p: dict(Counter(c["proposed_status"] for c in consumer if c["population"] == p))
                                for p in (DEV, "TOP BARS OVER SUPPORTS", "BOTTOM MESH")},
        consumer_lines=len(consumer),
        slab_beyond_wide_support_ends=dict(
            bottom=[sum(int(c["slab_beyond_wide_support_" + t]) for c in cen.values()) for t in "AB"],
            top=[sum(int(c["top_slab_beyond_wide_support_" + t]) for c in cen.values()) for t in "AB"]),
        top_end_classes_A_B={k: [sum(int(c[f"top{t}_{k}"]) for c in cen.values()) for t in "AB"] for k in CLASSES},
        top_conditional_extension_ends=[sum(int(c["top_adjacent_beyond_" + t]) for c in cen.values()) for t in "AB"],
        t152_continuity_mismatches=sum(int(c["t152_continuity_mismatch"]) for c in cen.values()),
    )
    sb = summ["slab_bound_restated_kg"]
    sb["spread"] = round(sb["high"] - sb["low"], 3)
    sb["spread_change_vs_t306"] = round(sb["spread"] - (6832.326 - 4643.766), 3)
    return consumer, json.loads(json.dumps(summ))          # plain JSON types (tuples -> lists)


def main(argv):
    if "--geometry" in argv:
        geometry(argv[argv.index("--geometry") + 1])
        return
    consumer, summ = run()
    if "--write" in argv:
        with open(CONSUMER, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(consumer[0]))
            w.writeheader()
            w.writerows(consumer)
        with open(SUMMARY, "w", encoding="utf-8") as f:
            json.dump(summ, f, indent=1, ensure_ascii=False)
    if "--check" in argv:
        assert json.load(open(SUMMARY)) == json.loads(json.dumps(summ)), "summary differs from the committed file"
    print(json.dumps(summ, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])
