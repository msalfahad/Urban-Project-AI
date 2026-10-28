"""T-316 Alsenan run (development villa; research ledger, nothing wired, no candidate or released kg changed).

Stage 1 (needs the private faces file, written only into the git-excluded private folder by T-139 slab_faces.py from
Drive "Alsenan chalet project" / "ST7757 dxf.dxf"):
    python3 -I research/agents_t316/t316_alsenan.py --geometry <private faces.json>
  -> TOP_END_DETAIL_T316.csv: every top-bar end of the 98 candidate top lines (T-152 note-2 placement, readings A / B):
     T-152 booking (continuity, band gap, other chord) and the T-307 support class, band face id, neighbour (numbers and
     T-139 face ids only; no coordinates, no drawing content).
Stage 2 (merged research files + the committed detail only):
    python3 -I research/agents_t316/t316_alsenan.py --write | --check
  -> TOP_GROUP_LEDGER_T316.csv (one row per support group and reading), TOP_LINE_LEDGER_T316.csv (= lane I consumer:
     one row per candidate top line id), TOP_SUMMARY_T316.json (class closure of the T-306 top cause rows).
"""

import csv
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import t316_top_bars as tb  # noqa: E402

T306_CSV = os.path.join(ROOT, "research", "agents_t306", "SLAB_SPREAD_DECOMPOSITION_T306.csv")
T306_SUM = os.path.join(ROOT, "research", "agents_t306", "SLAB_SPREAD_SUMMARY_T306.json")
T152_INPUT = os.path.join(ROOT, "research", "agents_t152", "T152_INPUT.csv")
PANELS = os.path.join(ROOT, "research", "agents_t139", "PANELS.csv")
T149 = os.path.join(ROOT, "research", "agents_t149", "T149_SPANS_INPUT.csv")
T213 = os.path.join(ROOT, "research", "agents_t213", "SUNKEN_PANELS_T213.json")
T307_DIR = os.path.join(ROOT, "research", "agents_t307")
DETAIL = os.path.join(HERE, "TOP_END_DETAIL_T316.csv")
GROUPS = os.path.join(HERE, "TOP_GROUP_LEDGER_T316.csv")
LINES = os.path.join(HERE, "TOP_LINE_LEDGER_T316.csv")
SUMMARY = os.path.join(HERE, "TOP_SUMMARY_T316.json")
TOP = "TOP BARS OVER SUPPORTS"
DOME_SPLIT = {"1F-073": (16.380, 41.651, 2.4111), "1F-076": (30.828, 41.651, 2.4111)}   # T-139 / T-152 / T-307
CAUSES = ("TOP_NOTE2_WORDING", "TOP_NOTE2_VS_P15", "TOP_CROSSING", "COUNT_CONVENTION")


def rows(p):
    csv.field_size_limit(10 ** 9)
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(p, out):
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)


# ------------------------------------------------------------------------------------------------ stage 1 (private)
def geometry(faces_json):
    from shapely import wkt
    from shapely.geometry import Point
    sys.path.insert(0, os.path.join(ROOT, "research", "agents_t152"))
    sys.path.insert(0, T307_DIR)
    import t152_slab_steel as t152  # noqa: E402  (read only: bar placement)
    import t307_geometry as tg  # noqa: E402  (read only: support classes)

    faces = json.load(open(faces_json))
    panels = {r["id"]: r for r in rows(PANELS)}
    sunken = {p[0] for p in json.load(open(T213))["t139_match"]["pairs"]}
    marks = defaultdict(list)
    for r in rows(T149):
        marks[(r["floor"], r["mark"])].append(r["width_m"])
    by_sheet = {}
    for sh, fl in faces.items():
        d = {}
        for f in fl:
            p = panels[f["id"]]
            poly = wkt.loads(f["wkt"])
            if f["id"] in DOME_SPLIT:
                cx, cy, r_out = DOME_SPLIT[f["id"]]
                disc = Point(cx, cy).buffer(r_out, quad_segs=256)
                k = 0
                for c in getattr(poly.difference(disc), "geoms", [poly.difference(disc)]):
                    if c.area >= 0.02:
                        cid = "%s/c%d" % (f["id"], k)
                        mr = c.minimum_rotated_rectangle.exterior.coords
                        dd = sorted([((mr[0][0] - mr[1][0]) ** 2 + (mr[0][1] - mr[1][1]) ** 2) ** 0.5,
                                     ((mr[1][0] - mr[2][0]) ** 2 + (mr[1][1] - mr[2][1]) ** 2) ** 0.5])
                        if abs(float(panels[cid]["area"]) - c.area) > 1e-3:
                            raise ValueError(f"dome corner {cid} area differs from T-139")
                        d[cid] = dict(poly=c, cls=panels[cid]["cls"], w=dd[0], l=dd[1], marks=[])
                        k += 1
                poly = poly.intersection(disc)
            if abs(float(p["area"]) - poly.area) > 1e-3:
                raise ValueError(f"face {f['id']} area differs from T-139: not the same drawing file")
            d[f["id"]] = dict(poly=poly, cls=p["cls"], w=f["w"], l=f["l"],
                              marks=[t for t in f["texts"] if t[:1] in "BC" and t[1:2] in "B0123456789"])
        by_sheet[sh] = d
    slab_ids = [i for i, p in panels.items() if p["cls"] == "SLAB"]
    tops = [r for r in rows(T306_CSV) if r["population"] == TOP]
    inp = {(f"SLAB:{r['panel']}", r["dir"]): r for r in rows(T152_INPUT)}
    detail, mism = [], 0
    for r in tops:
        ir = inp[(r["element"], r["direction"])]
        pid, axis = ir["panel"], ir["dir"]
        sh = pid.split("-")[0]
        fs = by_sheet[sh]
        others = [(q, fs[q]["poly"]) for q in slab_ids if q.startswith(sh + "-") and q != pid]
        mw = {mk: ws for (fl, mk), ws in marks.items() if fl == sh}
        top = json.loads(ir["top"])
        _H, lines = tg.bar_lines(fs[pid]["poly"], axis, len(top["A"]), t152._segments)
        for tag in ("A", "B"):
            if len(lines[tag]) != len(top[tag]):
                raise ValueError(f"{r['line_id']}: top bar lines differ from T-152")
            for bi, (segs, tsegs) in enumerate(zip(lines[tag], top[tag])):
                for si, ((ln, a, b, u), (tln, t0, t1)) in enumerate(zip(segs, tsegs)):
                    if abs(ln - tln) > 1e-4:
                        raise ValueError(f"{r['line_id']}: top segment length differs from T-152")
                    for side, pt, uu, te in (("lo", a, (-u[0], -u[1]), t0), ("hi", b, u, t1)):
                        e = tg.classify_end(pt, uu, pid, fs, others, sunken, mw)
                        band = tg._face_at((pt[0] + uu[0] * tg.STEP, pt[1] + uu[1] * tg.STEP), fs) or ""
                        pc = e["cls"] in ("CONTINUOUS", "STEP_EDGE") and e["beyond"] == "SLAB" and e["pieces"] == 0
                        mism += int(pc != bool(te[0]))
                        detail.append(dict(line_id=r["line_id"], element=r["element"], direction=axis, reading=tag,
                                           bar=bi, segment=si, end=side, seg_len_m=ln,
                                           t152_cont=int(bool(te[0])), t152_gap_m="" if te[1] is None else te[1],
                                           t152_other_chord_m="" if te[2] is None else te[2],
                                           support=e["cls"], width_m="" if e["w"] is None else e["w"],
                                           pieces=e["pieces"], beyond=e["beyond"], neighbour=e["neighbour"],
                                           band=band, note=e["note"]))
    if mism:
        raise ValueError(f"{mism} top ends: T-307 continuity differs from T-152")
    write_csv(DETAIL, detail)
    print("top-end detail written:", len(detail), "ends; T-152 continuity mismatches 0")


# ------------------------------------------------------------------------------------------------ stage 2
def _f(v):
    return None if v in ("", None) else float(v)


def build():
    t306 = {r["line_id"]: r for r in rows(T306_CSV) if r["population"] == TOP}
    det = rows(DETAIL)
    by_line = defaultdict(lambda: {"A": [], "B": []})
    for d in det:
        by_line[d["line_id"]][d["reading"]].append(d)
    if set(by_line) != set(t306):
        raise ValueError("detail lines differ from the T-306 top lines")
    tb_panels = {r["element"] for r in t306.values() if int(r["layers"]) == 2}
    u10 = tb.kgm(tb.NOTE2_D)
    cls_tot = defaultdict(lambda: defaultdict(float))
    resid = defaultdict(float)
    group_rows, line_rows = [], []
    gsides = []
    counts = defaultdict(Counter)
    across = {"A": [0.0, 0.0], "B": [0.0, 0.0]}
    facing_tb = Counter()
    overlap = {"A": defaultdict(float), "B": defaultdict(float)}
    for lid, r in sorted(t306.items()):
        tbp = r["element"] in tb_panels
        ends = {}
        for tag in ("A", "B"):
            ends[tag] = []
            for d in by_line[lid][tag]:
                e = tb.t152_end(float(d["seg_len_m"]), d["t152_cont"] == "1", _f(d["t152_gap_m"]),
                                _f(d["t152_other_chord_m"]))
                ends[tag].append((d["support"], e))
                counts[tag][d["support"]] += 1
        lo_r, hi_r, ct = tb.line_path(ends["A"], ends["B"])
        sp = tb.split_causes(ends["A"], ends["B"], lo_r, hi_r, ct)
        fig = {c: float(r["c_" + c]) for c in CAUSES}
        res = tb.close_line(lid, fig, sp, u10)
        for c in CAUSES:
            resid[c] += res[c]
            for k, v in sp[c].items():
                cls_tot[c][k] += v * u10
        # drawing-derived p.15 ledger of the line (R316-2 .. R316-5), per reading
        val, beyond = {}, {}
        held, unres = Counter(), Counter()
        note2 = {}
        for tag in ("A", "B"):
            lo = hi = 0.0
            n2i = n2ii = 0.0
            beyond_line = 0.0
            segx = defaultdict(dict)       # (bar, segment) -> end -> (in_panel, t152 p15); R316-10 overlap in one span
            for d in by_line[lid][tag]:
                s = d["support"]
                oth = _f(d["t152_other_chord_m"]) if s == "CONTINUOUS" else None
                w = _f(d["width_m"])
                if s == "CONTINUOUS" and w is None:
                    w = _f(d["t152_gap_m"])
                rec = tb.end_record(s, float(d["seg_len_m"]), w=w, l_other=oth, beyond=d["beyond"])
                across[tag][0] += rec["across"][0] * u10
                across[tag][1] += rec["across"][1] * u10
                if not tbp and "SLAB:" + d["neighbour"] in tb_panels:
                    facing_tb[tag] += 1
                n2i += rec["note2_i"]
                n2ii += rec["note2_ii"] + (rec["over_band"] if rec["in_panel"] is not None else 0.0)
                segx[(d["bar"], d["segment"])][d["end"]] = (rec["in_panel"], float(d["seg_len_m"]), tb.t152_end(
                    float(d["seg_len_m"]), d["t152_cont"] == "1", _f(d["t152_gap_m"]), _f(d["t152_other_chord_m"]))["p15"])
                if rec["in_panel"] is not None:
                    lo += rec["in_panel"] + rec["over_band"] + rec["across"][0]
                    hi += rec["in_panel"] + rec["over_band"] + rec["across"][1]
                for h in rec["held"]:
                    held[(tag, h)] += 1
                for x in rec["unresolved"]:
                    unres[(tag, x)] += 1
                gkey = _group_key(d)
                gsides.append(dict(group=gkey, panel=r["element"], side_key=(tag, d["bar"], d["segment"], d["end"])))
                group_rows.append(dict(group=gkey, line_id=lid, element=r["element"], direction=d["direction"],
                                       reading=tag, support=s, status=rec["status"],
                                       seg_len_m=d["seg_len_m"], width_m=d["width_m"],
                                       other_span_m=d["t152_other_chord_m"] if s == "CONTINUOUS" else "",
                                       p15_in_panel_m="" if rec["in_panel"] is None else round(rec["in_panel"], 4),
                                       over_band_m=round(rec["over_band"], 4) if rec["in_panel"] is not None else "",
                                       across_edge_beam_m="%.4f..%.4f" % rec["across"] if s == "EDGE_BEAM" else "",
                                       note2_i_m=round(rec["note2_i"], 4), note2_ii_m=round(rec["note2_ii"], 4),
                                       t152_p15_m=round(tb.t152_end(float(d["seg_len_m"]), d["t152_cont"] == "1",
                                                                    _f(d["t152_gap_m"]),
                                                                    _f(d["t152_other_chord_m"]))["p15"], 4),
                                       held=";".join(rec["held"]), unresolved=";".join(rec["unresolved"])))
            for k, ee in segx.items():
                ln = next(iter(ee.values()))[1]
                ov = tb.span_overlap(ln, ee.get("lo", (None,))[0], ee.get("hi", (None,))[0])
                lo -= ov["cut_low"]
                hi -= ov["cut_high"]
                if ov["overlap"]:
                    overlap[tag]["bar_lines"] += 1
                    overlap[tag]["drawn_excess_m"] += ov["cut_low"]
                t15 = sum(v[2] for v in ee.values()) - ln
                if t15 > 1e-9 and len(ee) == 2:
                    overlap[tag]["t152_p15_beyond_span_kg"] += t15 * u10
                    beyond_line += t15 * u10
                    overlap[tag]["t152_bar_lines"] += 1
            beyond[tag] = beyond_line
            val[tag] = (lo * u10, hi * u10)
            note2[tag] = (n2i * u10, n2ii * u10)
        vlo, vhi = min(val["A"][0], val["B"][0]), max(val["A"][1], val["B"][1])
        hA = sum(v for (t, h), v in held.items() if t == "A" and h != "HOOK_DOWN_LEG")
        hB = sum(v for (t, h), v in held.items() if t == "B" and h != "HOOK_DOWN_LEG")
        legs = (held.get(("A", "HOOK_DOWN_LEG"), 0), held.get(("B", "HOOK_DOWN_LEG"), 0))
        ext = (unres.get(("A", "EXTEND_50PCT_INTO_ADJACENT_SLAB"), 0), unres.get(("B", "EXTEND_50PCT_INTO_ADJACENT_SLAB"), 0))
        nA = Counter(d["support"] for d in by_line[lid]["A"])
        nB = Counter(d["support"] for d in by_line[lid]["B"])
        if tbp:
            status = "UNRESOLVED_TB_PANEL"
        elif hA == 0 and hB == 0:
            status = "DRAWING_DERIVED_P15_PART_WITH_HELD_LEGS" if legs[1] else "DRAWING_DERIVED_P15"
        elif vhi > 0:
            status = "DRAWING_DERIVED_P15_PART_WITH_HELD"
        else:
            status = "HELD"
        items = []
        if hA or hB:
            items.append("held ends %d..%d (%s)" % (min(hA, hB), max(hA, hB), ",".join(sorted(
                {h for (t, h) in held if h != "HOOK_DOWN_LEG"}))))
        if legs[1]:
            items.append("HOOK_DOWN_LEG at %d..%d edge-beam ends (drawn, not dimensioned)" % (min(legs), max(legs)))
        if ext[1] or ext[0]:
            items.append("EXTEND_50PCT_INTO_ADJACENT_SLAB at %d..%d ends (UNRESOLVED, blank)" % (min(ext), max(ext)))
        if tbp:
            items.append("(T&B) panel: full top mesh printed; whether note 2 adds bars over it, and p.15 note 3 'use "
                         "larger reinf.' at its supports, are designer items (F-T306-02 / F-T316-03)")
        line_rows.append(dict(
            line_id=lid, element=r["element"], direction=r["direction"], population=TOP,
            candidate_low_kg=r["low_kg"], candidate_high_kg=r["high_kg"], proposed_status=status,
            p15_valued_low_kg="" if status in ("HELD", "UNRESOLVED_TB_PANEL") else round(vlo, 3),
            p15_valued_high_kg="" if status in ("HELD", "UNRESOLVED_TB_PANEL") else round(vhi, 3),
            note2_i_A_kg=round(note2["A"][0], 3), note2_ii_cross_B_kg=round(note2["B"][1], 3),
            t306_path="%s->%s" % (lo_r, hi_r),
            t152_p15_beyond_span_A_kg=round(beyond["A"], 3), t152_p15_beyond_span_B_kg=round(beyond["B"], 3),
            ends_A=";".join("%s=%d" % kv for kv in sorted(nA.items())),
            ends_B=";".join("%s=%d" % kv for kv in sorted(nB.items())),
            held_items=" | ".join(items),
            basis="p.15 extent by support class (R316-2 .. R316-4); note-2 readings carried as NOTE_BASIS"))
    groups = tb.check_groups(gsides)
    extra = dict(across_edge_beam_kg={t: [round(v[0], 3), round(v[1], 3)] for t, v in across.items()},
                 ends_facing_TB_panel_A_B=[facing_tb["A"], facing_tb["B"]],
                 span_overlap={t: {k: round(v, 3) for k, v in sorted(o.items())} for t, o in overlap.items()})
    return line_rows, group_rows, cls_tot, resid, counts, groups, extra


def _group_key(d):
    s, p, nb, band = d["support"], d["element"].split(":")[1], d["neighbour"], d["band"]
    if s in ("CONTINUOUS", "STEP_EDGE") and d["beyond"] == "SLAB" and d["pieces"] == "0":
        a, b = sorted([p, nb])           # one physical support between two panels in one direction (band pieces
        return "%s|%s+%s" % (d["direction"], a, b)   # of one beam split by junctions are the same support)
    return "%s|%s|%s|%s" % (d["direction"], p, band or "none", d["end"])


def summary(line_rows, cls_tot, resid, counts, groups, extra):
    t306s = json.load(open(T306_SUM))["by_population"][TOP]
    cause_tot = {c: round(sum(v.values()), 3) for c, v in cls_tot.items()}
    by_class = {c: {k: round(v, 3) for k, v in sorted(cls_tot[c].items())} for c in CAUSES}
    phys = defaultdict(float)
    for c in ("TOP_NOTE2_WORDING", "TOP_NOTE2_VS_P15", "TOP_CROSSING"):
        for k, v in cls_tot[c].items():
            phys[k] += v
    vl = [r for r in line_rows if r["p15_valued_low_kg"] != ""]
    st = Counter(r["proposed_status"] for r in line_rows)
    two = sum(1 for g, ps in groups.items() if len(ps) == 2)
    return dict(
        **extra,
        t152_p15_beyond_span_in_candidate_high_kg=round(sum(r["t152_p15_beyond_span_B_kg"] for r in line_rows
                                                            if r["t306_path"].endswith("p15")), 3),
        lines_high_reading_p15=sum(1 for r in line_rows if r["t306_path"].endswith("p15")),
        lines=len(line_rows), statuses=dict(sorted(st.items())),
        ends_by_class_A_B={k: [counts["A"].get(k, 0), counts["B"].get(k, 0)] for k in sorted(
            set(counts["A"]) | set(counts["B"]))},
        groups=len(groups), groups_two_sided=two, groups_one_sided=len(groups) - two,
        t306_top_causes_kg={c: t306s.get(c, 0.0) for c in CAUSES},
        split_totals_kg=cause_tot,
        residual_kg={c: round(v, 6) for c, v in resid.items()},
        by_class_kg=by_class,
        the_1113_683_by_class_kg={k: round(v, 3) for k, v in sorted(phys.items())},
        the_1113_683_total_kg=round(sum(phys.values()), 3),
        p15_valued_lines=len(vl),
        p15_valued_low_kg=round(sum(r["p15_valued_low_kg"] for r in vl), 3),
        p15_valued_high_kg=round(sum(r["p15_valued_high_kg"] for r in vl), 3),
        candidate_top_low_kg=round(sum(float(r["candidate_low_kg"]) for r in line_rows), 3),
        candidate_top_high_kg=round(sum(float(r["candidate_high_kg"]) for r in line_rows), 3),
        candidate_on_valued_lines_kg=[round(sum(float(r["candidate_low_kg"]) for r in vl), 3),
                                      round(sum(float(r["candidate_high_kg"]) for r in vl), 3)],
        note2_on_valued_lines_kg=[round(sum(r["note2_i_A_kg"] for r in vl), 3),
                                  round(sum(r["note2_ii_cross_B_kg"] for r in vl), 3)])


def aggregate(group_rows):
    """one ledger row per support group side x reading x identical bar geometry, with its number of bars."""
    agg, order = Counter(), []
    for g in group_rows:
        k = tuple(g.items())
        if k not in agg:
            order.append(k)
        agg[k] += 1
    return [dict(k, n_bars=agg[k]) for k in order]


def run(write):
    line_rows, group_rows, cls_tot, resid, counts, groups, extra = build()
    group_rows = aggregate(group_rows)
    s = summary(line_rows, cls_tot, resid, counts, groups, extra)
    if write:
        write_csv(LINES, line_rows)
        write_csv(GROUPS, group_rows)
        json.dump(s, open(SUMMARY, "w"), indent=1, sort_keys=True)
        print(json.dumps(s, indent=1, sort_keys=True))
        return 0
    old = json.load(open(SUMMARY))
    if old != json.loads(json.dumps(s, sort_keys=True)):
        print("SUMMARY differs")
        return 1
    if rows(LINES) != [{k: str(v) for k, v in r.items()} for r in line_rows] or \
            rows(GROUPS) != [{k: str(v) for k, v in r.items()} for r in group_rows]:
        print("LINE LEDGER differs")
        return 1
    print("check OK")
    return 0


def main(argv):
    if argv[:1] == ["--geometry"]:
        geometry(argv[1])
        return 0
    if argv[:1] in (["--write"], ["--check"]):
        return run(argv[0] == "--write")
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
