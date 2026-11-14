"""T-792 (DELIVERY MODE fix-row set, lane S): SCHEDULE-FIRST vs CANDIDATE for columns and footings.

Two methods side by side per member (ACCURACY_PLAN change F):
  * drawing-derived: the candidate line (V3.0.85), drawn outline x storey frame height;
  * schedule-first: merged T-784 (research/agents_t784/out/SCHEDULE_FIRST.json, reproduced byte-identically this run
    from the Drive ST DXF): schedule row (frozen SCHEDULE_READER_V1) bound to the drawn outlines, count x B x D x H.
Where the company default 'a schedule governs a column' applies, a fix row restates the candidate line from the
schedule. The only open question at a member is WHICH schedule row (the mark), when two printed sheets tag the same
member with different marks (T-566 CONFLICT). It is settled by MARK_BY_OUTLINE_FIT (below): the mark whose schedule
section shares a side with the drawn outline on EVERY sheet that draws the member wins, if it is the only such mark;
otherwise the member stays as the candidate carries it (named, never 0).

    python3 -I research/agents_t792/fill_t792.py [--write | --check | --selftest]
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
IDX = os.path.join(ROOT, "research/agents_t770/out/LINE_INDEX_V3_0_85.json")
T784 = os.path.join(ROOT, "research/agents_t784/out/SCHEDULE_FIRST.json")
T778 = os.path.join(ROOT, "research/agents_t778/out/NONBEAM_CAUSES.json")
TOL = 0.005  # m: printed sizes are whole cm


# ---------------------------------------------------------------------------------------------- the rule (generic)
def shares_side(outline, section, tol=TOL):
    """outline (a, b) drawn, section (B, D) scheduled: True when one drawn side equals one scheduled side."""
    return any(abs(o - s) <= tol for o in outline for s in section)


def mark_by_outline_fit(tagged_marks, drawn, schedule):
    """MARK_BY_OUTLINE_FIT_V1 (proposed). tagged_marks: marks printed at the member on any sheet; drawn: {band:
    (a, b)} outlines of the member per band; schedule: {(band, mark): (B, D)}. Returns (mark or None, reason)."""
    marks = sorted(set(tagged_marks))
    if not marks:
        return None, "NO_TAG"
    if not drawn:
        return (marks[0], "SINGLE_TAG") if len(marks) == 1 else (None, "NO_OUTLINE")
    fit = []
    for mk in marks:
        rows = [(band, schedule.get((band, mk))) for band in drawn]
        if any(r is None for _, r in rows):
            continue  # the mark has no schedule row at a band where the member is drawn
        if all(shares_side(drawn[band], r) for band, r in rows):
            fit.append(mk)
    if len(fit) == 1:
        return fit[0], "FITS_EVERY_OUTLINE"
    return None, "NONE_FITS" if not fit else "SEVERAL_FIT"


# ---------------------------------------------------------------------------------------------- Alsenan evidence
# members in CONFLICT (T-566), read from the Drive ST DXF this run (entity handles, sizes in m; no client data).
CONFLICTS = {
    "10AE": {"tags": {"setting-out plan (text 20D)": "C", "foundation plan (text 1681)": "C3"},
             "drawn": {"FOUNDATION": (0.50, 0.30), "GF": (0.40, 0.20)},
             "outlines": "FOU 10AE 0.50 x 0.30, GF roof slab plan GFRS 350 0.40 x 0.20 (single-storey annex)",
             "lines": {"GF": ("L-694a75c84dd6e4bb4491", 3.875,
                              "annex h 3.875 = +4.30 printed finished - 0.175 roof build-up default - base +0.25 "
                              "(T-757 basis, kept)")}},
    "10E0": {"tags": {"setting-out plan (text 24E)": "C7", "foundation plan (text 10E1)": "C8"},
             "drawn": {"FOUNDATION": (0.80, 0.30), "GF": (0.80, 0.25), "1F": (0.80, 0.25)},
             "outlines": "FOU 10E0 0.80 x 0.30, GFRS 380 0.80 x 0.25, FFRS 69A 0.80 x 0.25",
             "lines": {"GF": ("L-4c4496579e5bfa20ae9f", 4.50, "GF h 4.50 (slab tops +0.95 .. +5.45)"),
                       "1F": ("L-1dc713c83bf62e525ff2", 4.20, "1F h 4.20 (+5.45 .. +9.65)")}},
}
BAND = {"FOUNDATION": "NECK", "GF": "GF_COLUMN", "1F": "1F_COLUMN"}
PLANTED = {  # planted columns: not in the column schedule by type (legend 'Planted column (P.C)'), own printed size
    "L-2ac3c9b3b4c2221a0299": ("PC-1F-A", "text 544 'P.C 20x70', GFRS 329 / FFRS 66A drawn 0.70 x 0.20 agree",
                               0.14, 4.20),
    "L-31a0424bd0efcc93efba": ("PC-1F-B", "text 548 'P.C 20x50', GFRS 386 / FFRS 69D drawn 0.50 x 0.20 agree",
                               0.10, 4.20),
    "L-541c7e565bb93ecdb78b": ("PC-2F", "text 77C 'P.C 20x50' (drawn FFRS 77B 0.20 x 0.40; printed size governs, "
                               "T-757 DEFAULT)", 0.10, 3.325),
}
OUTLINES_EXPLAINED = {  # T-784 storey outlines with no schedule mark (UNSCHEDULED / AMBIGUOUS): every one named
    "P322": "GF start of the turned T.C at C9 / F9 (note 324; T-217 s.7 item 4): the GF member is the SOLID 37A, carried",
    "P329": "GF start outline of PC-1F-A (text 544 'P.C 20x70'): line L-2ac3c9b3",
    "P344": "GF C3 at FP 10A0, drawn 0.20 x 0.50 vs GR 25 x 50 (T-256 row 55): carried as a candidate C3 line at the "
            "schedule section; schedule-first bound that C3 tag to 31B instead (31B = ANSI35 start of the turned C8 T.C "
            "at F8, T-217 s.2): count and m3 neutral (one C3 at GR 25 x 50 x 4.50 either way)",
    "P386": "GF start outline of PC-1F-B (text 548 'P.C 20x50'): line L-31a0424b",
    "P66A": "1F PC-1F-A body: line L-2ac3c9b3",
    "P69D": "1F PC-1F-B body: line L-31a0424b",
    "P77B": "1F roof start outline of PC-2F (text 77C 'P.C 20x50'): line L-541c7e56",
    "P778": "2F PC-2F body: line L-541c7e56",
}
FOOT_HAND = ("F12", 4.4, 3.2, 0.7)   # one footing for the Checker: schedule B x L x H, one drawn outline TAGGED


def r4(x):
    return round(x + 0.0, 4)


def build():
    idx = json.load(open(IDX))
    by = {l["line_id"]: l for l in idx["lines"]}
    sf = json.load(open(T784))
    sched = {}
    for band, key in BAND.items():
        for q in sf[key]["q"]["lines"]:
            if q["B"] is not None:
                sched[(band, q["mark"])] = (round(q["B"], 3), round(q["D"], 3))
    rows, confirmed, member_log = [], [], []
    for h, m in CONFLICTS.items():
        mk, why = mark_by_outline_fit(m["tags"].values(), m["drawn"], sched)
        assert mk, (h, why)
        fits = {t: {band: shares_side(m["drawn"][band], sched[(band, t)]) for band in m["drawn"]}
                for t in sorted(set(m["tags"].values()))}
        member_log.append({"member": h, "tags": m["tags"], "outlines": m["outlines"], "fit_by_mark": fits,
                           "resolved_mark": mk, "reason": why})
        for st, (lid, hgt, hb) in m["lines"].items():
            l = by[lid]
            assert l["item_code"] == "STR.CONC.COLUMN" and l["class"] == "RELEASED", lid
            B, D = sched[(st, mk)]
            new = r4(B * D * hgt)
            old = l["measured_net"]
            other = [t for t in fits if t != mk][0]
            ob, od = sched[(st, other)] if (st, other) in sched else (None, None)
            drawn_a = m["drawn"][st][0] * m["drawn"][st][1]
            basis = (f"{h} {st}: mark {mk} by MARK_BY_OUTLINE_FIT_V1 ({', '.join(f'{k} {v}' for k, v in m['tags'].items())}; "
                     f"{m['outlines']}; {mk} fits every outline, {other} does not); schedule {st} {mk} "
                     f"{B * 100:.0f} x {D * 100:.0f} governs (company default) = {B * D:.3f} m2 x {hb} = {new:.4f} m3")
            beside = {"drawing_derived": r4(drawn_a * hgt), "schedule_other_mark": r4(ob * od * hgt) if ob else None,
                      "schedule_first": new}
            if abs(new - old) < 5e-5:
                lab = "DRAWING-READ"   # drawn = scheduled section: both methods agree
                confirmed.append({"line_id": lid, "net": old, "label": lab, "basis": basis + "; drawn section = "
                                  "scheduled section: both methods agree, mark only (was carried as C8)",
                                  "beside": beside})
                continue
            rows.append({"line_id": lid, "item_code": "STR.CONC.COLUMN", "unit": "m3", "element_id": l["element_id"],
                         "before": {"class": "RELEASED", "net": old, "label": l.get("method_label")},
                         "after": {"class": "RELEASED", "net": new}, "label": "DEFAULT", "designer_item": "D-66",
                         "basis": basis + "; D-66 answer replaces it", "beside": beside})
    for lid, (name, ev, a, hgt) in PLANTED.items():
        l = by[lid]
        assert abs(l["measured_net"] - r4(a * hgt)) < 5e-5, lid
        confirmed.append({"line_id": lid, "net": l["measured_net"], "label": l.get("method_label") or "DRAWING-READ",
                          "basis": f"{name}: planted column, no schedule row by type (legend P.C); {ev}: {a:.2f} m2 x "
                                   f"{hgt} = {l['measured_net']:.4f} m3; the freelancer carries the same section; "
                                   f"ENGINE_RIGHT vs schedule-first (which cannot see a P.C)",
                          "beside": {"drawing_derived": l["measured_net"], "schedule_first": None}})
    # ---- per storey: candidate before / after vs schedule-first vs freelancer --------------------------------------
    col = {"GF": 0.0, "1F": 0.0, "2F": 0.0}
    pc = {"GF": 0.0, "1F": 0.0, "2F": 0.0}
    for l in idx["lines"]:
        if l["item_code"] != "STR.CONC.COLUMN" or l["class"] != "RELEASED":
            continue
        e = l["element_id"]
        st = e.split("|")[-1] if "|" in e else ("1F" if "-1F-" in e else "2F")
        col[st] += l["measured_net"]
        if e.startswith("HL:PLANTED_COLUMN"):
            pc[st] += l["measured_net"]
    delta = {"GF": 0.0, "1F": 0.0, "2F": 0.0}
    for r in rows:
        delta[r["element_id"].split("|")[-1]] += r["after"]["net"] - r["before"]["net"]
    t778 = json.load(open(T778))
    fam = [f for f in t778["families"] if f["family"] == "STR.CONC.COLUMN"][0]
    his = {"GF": 0.0, "1F": 0.0, "2F": 0.0}
    for pm in fam["per_mark"]:
        his[pm["storey"]] += pm["his"]
    named = {"GF": "storey frame: candidate drawing-read bases (annex 3.875 on 4 C members incl. 10AE, +0.25 base 5.20 "
                   "on C3 / C5) vs the flat 4.50 schedule-first frame: ENGINE_RIGHT (T-576; heights are not in the "
                   "schedule)",
             "1F": "PC-1F-A / PC-1F-B planted columns 1.008: no schedule row by type; ENGINE_RIGHT (printed P.C size "
                   "texts, the freelancer carries both)",
             "2F": "PC-2F 0.3325 (no schedule row by type, ENGINE_RIGHT) and the 2F frame 4.075 (13.90 - 0.175 roof "
                   "DEFAULT - 9.65) vs 4.20 on six members -0.075: ENGINE_RIGHT (closer drawing read, both DEFAULT)"}
    storeys = []
    for st in ("GF", "1F", "2F"):
        s = sf[st + "_COLUMN"]["q"]["total_m3"]
        b, a = col[st], col[st] + delta[st]
        like = a - pc[st]
        storeys.append({"storey": st, "candidate_before": r4(b), "candidate_after": r4(a), "schedule_first": r4(s),
                        "after_vs_schedule_pct": round(100 * (a - s) / s, 1), "planted_m3": r4(pc[st]),
                        "like_for_like_pct": round(100 * (like - s) / s, 1), "within_5pct": abs(a - s) / s <= 0.05,
                        "cause": named[st], "freelancer": r4(his[st]),
                        "after_vs_freelancer": f"{a - his[st]:+.2f} m3 ({100 * (a - his[st]) / his[st]:+.1f} %)"})
    # ---- footings: no fix row (schedule-first -0.09 %, both causes named by T-784) --------------------------------
    fo = [l for l in idx["lines"] if l["item_code"] == "STR.CONC.FOOTING" and l["class"] == "RELEASED"]
    fo_c = sum(l["measured_net"] for l in fo)
    fo_s = sf["FOOTING"]["q"]["total_m3"]
    mk, B, L, H = FOOT_HAND
    q = [x for x in sf["FOOTING"]["q"]["lines"] if x["mark"] == mk][0]
    assert abs(q["volume_m3"] - B * L * H) < 1e-6 and q["count"] == 1
    footing = {"candidate": r4(fo_c), "schedule_first": r4(fo_s), "diff": f"{fo_c - fo_s:+.3f} m3 "
               f"({100 * (fo_c - fo_s) / fo_s:+.2f} %)", "freelancer": 65.634,
               "vs_freelancer": f"{fo_c - 65.634:+.3f} m3 ({100 * (fo_c - 65.634) / 65.634:+.2f} %)",
               "causes": ["F10 + F drawn as one outline 3.25 x 1.40 x 0.50 (owner Q-31 C 'bigger area') vs schedule "
                          "rows F10 1.96 + F 0.216: +0.099 RULE_DIFFERENCE (Q-31 C governs)",
                          "FN clipped by F9: notch 0.40 x 0.35 x 0.30 owned by F9 (R-CONC-OWN-1): -0.042 ENGINE_RIGHT",
                          "F7: schedule row, no plan symbol: no member, no line (designer list)"],
               "hand_check": f"{mk}: schedule {B:.2f} x {L:.2f} x {H:.2f} = {B * L * H:.4f} m3, one drawn outline TAGGED"}
    # ---- necks: count only (heights Q-21 stay as carried) ---------------------------------------------------------
    nk = [l for l in idx["lines"] if l["item_code"] == "STR.CONC.NECK" and l["class"] == "RELEASED"]
    cnt = {}
    for l in nk:
        m_ = l["element_id"].split(":")[-1].split("@")[0]
        cnt[m_] = cnt.get(m_, 0) + 1
    sfc = {x["mark"]: x["count"] or 0 for x in sf["NECK"]["q"]["lines"]}
    sfc["CN"] = sum(1 for d in sf["NECK"]["bind"]["designer"] if d["status"] == "NOT_IN_SCHEDULE")
    necks = {"candidate_count": sum(cnt.values()), "schedule_first_count": sum(sfc.values()),
             "by_mark": {k: [cnt.get(k, 0), sfc.get(k, 0)] for k in sorted(set(cnt) | set(sfc))},
             "note": "totals agree 36 = 36; per mark only the two CONFLICT members move (10AE C3 -> C, 10E0 C8 -> C7); "
                     "their neck lines already carry the 30 x 50 / 30 x 80 sections of the resolved marks (L-15b8ad39 "
                     "0.4272 = 0.24 x 1.78): mark only, no m3 change; heights stay (Q-21)"}
    expl = []
    for key in ("GF_COLUMN", "1F_COLUMN", "2F_COLUMN"):
        for dd in sf[key]["bind"]["designer"]:
            if dd["status"] in ("UNSCHEDULED_OUTLINE", "AMBIGUOUS_OUTLINE"):
                h = dd["outline"].split("@")[0]
                assert h in OUTLINES_EXPLAINED, h
                expl.append({"storey": key[:2], "outline": dd["outline"], "status": dd["status"],
                             "size_m": dd["size_m"], "reading": OUTLINES_EXPLAINED[h]})
    assert len(expl) == len(OUTLINES_EXPLAINED)
    dsum = sum(r["after"]["net"] - r["before"]["net"] for r in rows)
    summary = {"lines_changed": len(rows), "lines_new": 0, "column_m3_before": r4(sum(col.values())),
               "column_m3_after": r4(sum(col.values()) + dsum), "column_delta_m3": r4(dsum),
               "freelancer_column_m3": fam["his_m3"],
               "column_vs_freelancer_before": f"{sum(col.values()) - fam['his_m3']:+.2f} m3 "
                                              f"({100 * (sum(col.values()) - fam['his_m3']) / fam['his_m3']:+.1f} %)",
               "column_vs_freelancer_after": f"{sum(col.values()) + dsum - fam['his_m3']:+.2f} m3 "
                                             f"({100 * (sum(col.values()) + dsum - fam['his_m3']) / fam['his_m3']:+.1f} %)",
               "blank_lines_before_after": "0 / 0 (COLUMN, FOOTING, NECK)",
               "acceptance": "per storey schedule-first vs candidate: GF within 5 %; 1F / 2F outside only by the planted "
                             "columns (like-for-like within 5 %), both figures carried with the cause"}
    return idx, {"schema": "URBAN_FIX_ROWS_V1", "task": "T-792", "candidate_version": idx["candidate_version"],
                 "rule": "MARK_BY_OUTLINE_FIT_V1 (proposed, research/agents_t792/fill_t792.py) + company default "
                         "'schedule governs a column'",
                 "inputs": {"index": "LINE_INDEX_V3_0_85.json", "t784": "research/agents_t784/out/SCHEDULE_FIRST.json "
                            "(re-run on the Drive DXF this run: byte-identical md)", "t778":
                            "research/agents_t778/out/NONBEAM_CAUSES.json (freelancer per mark)",
                            "drawings": "Drive 'Alsenan chalet project' ST7757 dxf.dxf: column schedule (GF / 1ST / FOU "
                                        "bands), column setting-out plan, foundation plan, GF / 1F roof slab plans "
                                        "(handles 10AE 10E0 350 380 69A 329 386 66A 69D 77B, texts 20D 24E 1681 10E1 "
                                        "544 548 77C)"},
                 "summary": summary, "rows": rows, "new_lines": [], "confirmed_no_change": confirmed,
                 "conflict_members": member_log, "storeys": storeys, "footing": footing, "necks": necks,
                 "outlines_explained": expl, "not_changed": "formwork of 10AE / 10E0 (face-ledger ESTIMATE lines L-7fe93376 / L-ae0d688f): perimeter "
                                "+0.20 x 3.875 = +0.78 m2 and -0.10 x 4.20 = -0.42 m2 (net +0.36, gross 1.20 m2 = 0.3 % of "
                                "the 384.1 m2 column formwork line set, below 1 %): logged, not restated"}


def md(out):
    s = out["summary"]
    L = [f"# T-792 fix rows on {out['candidate_version']}: schedule-first vs candidate (columns, footings)", "",
         "Rule: " + out["rule"], "", "## Summary", "", "```", json.dumps(s, indent=1), "```", "", "## Changed lines", "",
         "| line | before | after | label | basis | drawing-derived | other mark |", "|---|---|---|---|---|---|---|"]
    L += [f"| {r['line_id']} | {r['before']['net']:.4f} | {r['after']['net']:.4f} | {r['label']} | {r['basis']} | "
          f"{r['beside']['drawing_derived']:.4f} | {r['beside']['schedule_other_mark']} |" for r in out["rows"]]
    L += ["", "## Confirmed, no change", "", "| line | m3 | label | basis |", "|---|---|---|---|"]
    L += [f"| {c['line_id']} | {c['net']:.4f} | {c['label']} | {c['basis']} |" for c in out["confirmed_no_change"]]
    L += ["", "## CONFLICT members (two sheets, two marks)", "", "| member | tags | outlines | fit by mark | mark |",
          "|---|---|---|---|---|"]
    L += [f"| {m['member']} | {json.dumps(m['tags'])} | {m['outlines']} | {json.dumps(m['fit_by_mark'])} | "
          f"{m['resolved_mark']} ({m['reason']}) |" for m in out["conflict_members"]]
    L += ["", "## Per storey (m3)", "", "| storey | candidate before | after | schedule-first | after vs schedule | "
          "planted | like-for-like | freelancer | after vs freelancer | cause |", "|---|---|---|---|---|---|---|---|---|---|"]
    L += [f"| {x['storey']} | {x['candidate_before']:.4f} | {x['candidate_after']:.4f} | {x['schedule_first']:.4f} | "
          f"{x['after_vs_schedule_pct']:+.1f} % | {x['planted_m3']:.4f} | {x['like_for_like_pct']:+.1f} % | "
          f"{x['freelancer']:.4f} | {x['after_vs_freelancer']} | {x['cause']} |" for x in out["storeys"]]
    f = out["footing"]
    L += ["", "## Footings (no fix row)", "", f"Candidate {f['candidate']:.4f} vs schedule-first {f['schedule_first']:.4f}: "
          f"{f['diff']}; vs freelancer {f['freelancer']}: {f['vs_freelancer']}. Hand check: {f['hand_check']}.", ""]
    L += ["- " + c for c in f["causes"]]
    n = out["necks"]
    L += ["", "## Necks (count only)", "", f"Candidate {n['candidate_count']} vs schedule-first "
          f"{n['schedule_first_count']}: {n['note']}.", "", "| mark | candidate | schedule-first |", "|---|---|---|"]
    L += [f"| {k} | {v[0]} | {v[1]} |" for k, v in n["by_mark"].items()]
    L += ["", "## Storey outlines with no schedule mark (all named; no missing member)", "",
          "| storey | outline | status | size m | reading |", "|---|---|---|---|---|"]
    L += [f"| {e['storey']} | {e['outline']} | {e['status']} | {e['size_m']} | {e['reading']} |"
          for e in out["outlines_explained"]]
    L += ["", "Not changed: " + out["not_changed"]]
    return "\n".join(L) + "\n"


def selftest():
    """MARK_BY_OUTLINE_FIT_V1 on a synthetic non-Alsenan villa: normal and adverse cases."""
    sch = {("GF", "K1"): (0.30, 0.60), ("GF", "K2"): (0.30, 0.90), ("1F", "K1"): (0.25, 0.60),
           ("1F", "K2"): (0.25, 0.90), ("GF", "K3"): (0.40, 0.40)}
    ok = []
    # normal: two sheets disagree; GF fits both, 1F 0.60 x 0.20 fits only K1 (shares 0.60)
    ok.append(mark_by_outline_fit(["K1", "K2"], {"GF": (0.60, 0.30), "1F": (0.60, 0.20)}, sch) == ("K1", "FITS_EVERY_OUTLINE"))
    # rotation / units: outline given rotated (b, a) still fits
    ok.append(mark_by_outline_fit(["K2", "K3"], {"GF": (0.30, 0.90)}, sch) == ("K2", "FITS_EVERY_OUTLINE"))
    # adverse: both marks fit -> undecided, never a guess
    ok.append(mark_by_outline_fit(["K1", "K2"], {"GF": (0.30, 0.50)}, sch) == (None, "SEVERAL_FIT"))
    # adverse: neither fits -> undecided
    ok.append(mark_by_outline_fit(["K1", "K2"], {"GF": (0.45, 0.55)}, sch) == (None, "NONE_FITS"))
    # adverse: missing schedule row at a drawn band -> that mark cannot win
    ok.append(mark_by_outline_fit(["K3", "K1"], {"GF": (0.40, 0.30), "1F": (0.40, 0.25)}, sch) == ("K1", "FITS_EVERY_OUTLINE"))
    # adverse: no tag at all
    ok.append(mark_by_outline_fit([], {"GF": (0.3, 0.6)}, sch) == (None, "NO_TAG"))
    print("SELFTEST", "PASS" if all(ok) else f"FAIL {ok}")
    return 0 if all(ok) else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    _, out = build()
    d = os.path.join(HERE, "out")
    pj, pm = os.path.join(d, "FIX_ROWS.json"), os.path.join(d, "FIX_ROWS.md")
    txt = json.dumps(out, indent=1) + "\n"
    if "--check" in argv:
        ok = open(pj).read() == txt and open(pm).read() == md(out)
        print("CHECK OK" if ok else "CHECK FAILED: out/ differs from a fresh build")
        return 0 if ok else 1
    print(json.dumps(out["summary"], indent=1))
    if "--write" in argv:
        os.makedirs(d, exist_ok=True)
        open(pj, "w").write(txt)
        open(pm, "w").write(md(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
