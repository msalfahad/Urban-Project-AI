"""T-689 development villa (Alsenan): the held STR.CONC.COLUMN / STR.CONC.BEAM ranges of V3.0.67, ranked by width, the
lines making 80 % of each family's width defined member by member, each tied to its designer item per cause, and the
ranges narrowed only where a drawn datum moves an end (R-T689-1 / -2 / -3). Research only, unwired: no candidate line,
key map, rule or knowledge version file changes. Inputs are committed files only:

  research/agents_t682/out/LINE_INDEX_V3_0_67.json  (candidate of record after T-682)
  research/agents_t683/out/T683_STATEMENT.json      (held causes, V3.0.66; V3.0.67 adds PC-2F and annex C3 bounds)
  research/agents_t256/LEDGER_T256.csv              (D-66 / D-16 member evidence by DXF handle, Checker-verified)
  research/agents_t201/HEADS_T201.csv               (2F window heads, DRAWING-CONFIRMED with read tolerance)
  research/agents_t566/POSITION_INPUT_T566.json     (2F slab-plan outline handle -> FP position -> mark)
  research/agents_t689/out/T689_OWN_READ.json       (own read this run: B8 row, span, supports, SFRS texts)

    python3 -I research/agents_t689/t689_alsenan.py --write | --check
"""
from __future__ import annotations

import csv
import json
import sys
from decimal import Decimal as X
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t689_rules as R  # noqa: E402

OUT_JSON = HERE / "out" / "T689_HELD_RANGES.json"
OUT_MD = HERE / "out" / "T689_HELD_RANGES.md"

BASE_2F = X("9.65")      # 2F column base, APPROVED datum (T-214 / T-248; T-669)
FINISHED_ROOF = X("13.90")  # printed finished mark of the 2F roof (section A-A), D-39 ceiling
S_LO_BEFORE = X("12.68")   # R-T669-2: W26 apex +12.50 printed + T 18

# Designer register membership as printed in DESIGNER_CLARIFICATIONS (board, read this run): D-66 names 13 outline
# handles; D-16 = C8 at F14 (GFRS 380, FFRS 69A); D-63 the lift C9 neck (+ T-256 proposal for FFRS 679 above it);
# D-39 roof datum; D-04 six unlabelled spans; D-27 / D-02 width conflicts; D-03 two marks. No item names PC-2F's
# section (FFRS 77B / SFRS 778 drawn 0.20 x 0.40 vs FFRS text 77C 'P.C 20x50').
REGISTER = {"D-02", "D-03", "D-04", "D-16", "D-27", "D-39", "D-44", "D-46", "D-63", "D-66"}
D66_HANDLES = {"347", "359", "344", "691", "676", "697", "673", "694", "685", "688", "68E", "679", "667"}

# line -> member (from the T-256 ledger by mark / storey / area range, T-566 handle map for 2F, T-668 / T-666 for beams)
MEMBERS = {
    "L-755eb56b55e86301b488": ("C9 1F lift column, FFRS 679", [("SECTION", "D-66")], "679"),
    "L-a87ea657a42a311cb851": ("C6 1F, FFRS 688", [("SECTION", "D-66")], "688"),
    "L-831f6fe3de133294bb8f": ("C5 1F, FFRS 673 / 694 (one of the pair)", [("SECTION", "D-66")], "673"),
    "L-c677b628a776d3b87b02": ("C5 1F, FFRS 694 / 673 (one of the pair)", [("SECTION", "D-66")], "694"),
    "L-53f223b06db14ac41d47": ("C9 2F 20x70, SFRS 418", [("TOP DATUM", "D-39")], None),
    "L-85809d3db52bb93dfe96": ("C7 1F, FFRS 68E", [("SECTION", "D-66")], "68E"),
    "L-541c7e565bb93ecdb78b": ("PC-2F planted column, FFRS 77B / SFRS 778", [("SECTION", None), ("TOP DATUM", "D-39")], None),
    "L-26f6b6f2365c72e42291": ("C2 2F 20x50, SFRS 41B", [("TOP DATUM", "D-39")], None),
    "L-33a9b7728781fcba12e2": ("C2 2F 20x50, SFRS 41E", [("TOP DATUM", "D-39")], None),
    "L-919a5749ef79759e01ca": ("C2 2F 20x50, SFRS 412 (B8 west support)", [("TOP DATUM", "D-39")], None),
    "L-d79d17d14f39d5148cb8": ("C1 2F 20x50, SFRS 421", [("TOP DATUM", "D-39")], None),
    "L-8de64040a1c3ae6cf137": ("C3 GF, GFRS 344", [("SECTION", "D-66")], "344"),
    "L-4c4496579e5bfa20ae9f": ("C8 GF at F14, GFRS 380", [("SECTION", "D-16")], None),
    "L-8f8ad257d9b2cb9e027f": ("C4 1F, FFRS 676 / 697 (one of the pair)", [("SECTION", "D-66")], "676"),
    "L-cc702b8541c15fdfd98c": ("C3 1F, FFRS 691", [("SECTION", "D-66")], "691"),
    "L-e112e2add2f8979a6c39": ("C4 1F, FFRS 697 / 676 (one of the pair)", [("SECTION", "D-66")], "697"),
    "L-fad18af6e7139a5e99d1": ("C3 GF annex", [("TOP DATUM", "D-39"), ("SECTION", "D-66")], None),
    "L-43dae3d6dfec957b26a8": ("C GF, GFRS 347 / 359", [("SECTION", "D-66")], "347"),
    "L-9cb26d86575a92694880": ("C GF, GFRS 359 / 347", [("SECTION", "D-66")], "359"),
    "L-291ba2ddf4bbe4f14cf7": ("C5 1F, FFRS 685", [("SECTION", "D-66")], "685"),
    "L-1dc713c83bf62e525ff2": ("C8 1F at F14, FFRS 69A", [("SECTION", "D-16")], None),
    "L-4aed92c117a7ab1c90ee": ("C9 1F T.C, FFRS 667", [("SECTION", "D-66")], "667"),
    # beams
    "L-d62d2fcf3d0023ad1ad1": ("2F unlabelled piece BAND0006.1, 3.10 m x 0.20 drawn", [("DEPTH", "D-04")], None),
    "L-1fd49f3e7c5a7dd19d4d": ("GF BM-GF-056 (BAND0042), width conflict", [("WIDTH", "D-27")], None),
    "L-9e4895663f76d7f03ac9": ("GF BM-GF-054 (BAND0008), width conflict", [("WIDTH", "D-27")], None),
    "L-7c3edce23ec8faa3d674": ("2F unlabelled piece BAND0011.1, 1.40 m", [("DEPTH", "D-04")], None),
    "L-dc8cbfc119d006ff3927": ("2F unlabelled piece BAND0008.1, 1.40 m", [("DEPTH", "D-04")], None),
    "L-88ccf8d4505411deb9e5": ("GF CB3 / 'B3 (With Stair)' span BAND0019.2", [("MARK", "D-03")], None),
    "L-8d031491396379f0cbb1": ("2F BM-2F-015 (BAND0001.3), 1.13 m east of 415", [("DEPTH", "D-04")], None),
    "L-f83c4a469845c7e14dfa": ("1F BM-1F-032 (BAND0005.1), 0.80 m", [("DEPTH", "D-04")], None),
    "L-39ca5340879eafc35355": ("1F B6 vertical span (BAND0009)", [("WIDTH", "D-27")], None),
    "L-43e804ba4a4c07529fd5": ("1F CB10 span 2 (BAND0026.2)", [("WIDTH", "D-02")], None),
    "L-2c7b0b1e1a439d9ffd1e": ("GF CB2 span 1 (BAND0036.1)", [("WIDTH", "D-27")], None),
    "L-60f09eece6568b15f6ce": ("GF CB2 span 2 (BAND0036.2)", [("WIDTH", "D-27")], None),
    "L-50667f69855b6d588011": ("1F CB10 span 1 (BAND0026.1)", [("WIDTH", "D-02")], None),
    "L-bef35462630d4b76596f": ("GF BAND0030.2 depth companion (B4 0.50 vs B7 0.75)", [("DEPTH", "FR-T642-2")], None),
}
# what was searched for each cause (merged evidence; the drawing searches are not repeated, they are cited)
SEARCHED = {
    "SECTION": "T-256 (Checker-verified): p.9 schedule, p.4-6 slab plans + PDF plot, A-A / B-B / C-C / D-D cuts, CAP, "
               "p.10-16, architectural plans: no third member-specific print; owner X6 (Q-61 (1)): a schedule / drawing "
               "conflict is never settled by picking the printed one",
    "TOP DATUM": "T-669 / T-678: slab top not printed (finished +13.90 only); this run: W28 / W29 heads under printed B8 "
                 "(R-T689-1), plate transfer refused by R-T678-2 (T 18 printed inside the plate)",
    "DEPTH": "T-402 r2 (Checker-verified): 14 S-SEC.LINE cuts reach none of these pieces, 377 plan dimensions, marks "
             "within 1.2 m: none; edge continuity does not bind a mark (R-T402-3); this run: no drawn head under a "
             "piece bounds its soffit",
    "WIDTH": "T-402 r2: no section cuts the member, no plan dimension within 0.06 m; schedule row vs drawn edges",
    "MARK": "T-402 / T-241: two printed marks on one span, one row each in p.10 / p.11",
}


def D6(v):
    return X(str(v)).quantize(X("0.000001"))


def load(p):
    return json.loads((ROOT / p).read_text())


def heads_2f():
    rows = {r["ID"]: r for r in csv.DictReader((ROOT / "research/agents_t201/HEADS_T201.csv").open())}
    out = {}
    for w in ("W28", "W29"):
        r = rows[w]
        tol = r["ISSUE_CHECK"].split("max edge offset ")[1].split(" m")[0]
        out[w] = {"id": w, "head_abs": r["HEAD_LEVEL_M"], "tol": tol, "status": r["STATUS"]}
    # jamb positions along the B8 clear span from the face of 412 (T-261 r2, merged: 2F-W02 B8 piece 3.470 hosts
    # W28 0.375 .. 0.975 and W29 2.270 .. 3.470)
    out["W28"]["at"] = ("0.375", "0.975")
    out["W29"]["at"] = ("2.270", "3.470")
    return out


def build():
    idx = load("research/agents_t682/out/LINE_INDEX_V3_0_67.json")
    own = load("research/agents_t689/out/T689_OWN_READ.json")
    t566 = load("research/agents_t566/POSITION_INPUT_T566.json")
    marks_2f = {p["members"]["2F"]["handle"]: p["labels"]["FP"]["mark"] for p in t566["positions"] if "2F" in p["members"]}
    assert marks_2f["412"] == "C2" and marks_2f["415"] == "C5", marks_2f
    b8 = own["b8"]
    assert b8["schedule_row"]["H_cm"] == "75" and b8["schedule_row"]["W_cm"] == "20" and b8["label_in_span_412_415"]
    assert b8["supports_on_band"]["412"] and b8["supports_on_band"]["415"]
    span = X(str(b8["clear_span_412_to_415_m"]))
    hd = heads_2f()
    beam = {"id": "B8 2F (79E, row 1EBA)", "depth": X(b8["schedule_row"]["H_cm"]) / 100, "stand": "DOWN",
            "span": (X("0"), span)}
    top = R.beam_top_lower_bound(beam=beam, heads=[hd["W28"], hd["W29"]], finished_mark=FINISHED_ROOF)
    s_lo = X(top["s_lo"])
    one_plane = not own["sfrs_texts"]["thickness_texts_inside"] and not own["sfrs_texts"]["level_marks_inside"]
    plate = R.plate_transfer(top_lo=s_lo, base=BASE_2F, one_plane=one_plane,
                             why_not="R-T678-2: thickness 'T 18' printed inside the 2F roof outline (7B3 / 7B4, "
                                     "1A7D / 1A7E, the two tank panels): one plane not established")
    h412 = R.support_column_height_lo(top_lo=s_lo, base=BASE_2F, supports={"412", "415"}, column="412")

    fam = {}
    rows = []
    for ic in ("STR.CONC.COLUMN", "STR.CONC.BEAM"):
        L = [l for l in idx["lines"] if l["item_code"] == ic and l["class"] == "HELD" and l["held_low"] is not None]
        ranked, tot = R.width_share([{"line_id": l["line_id"], "low": str(l["held_low"]), "high": str(l["held_high"])}
                                     for l in L])
        top_set = set(ranked)
        L.sort(key=lambda l: (-(D6(l["held_high"]) - D6(l["held_low"])), l["line_id"]))
        lo_b = sum((D6(l["held_low"]) for l in L), X(0))
        hi_b = sum((D6(l["held_high"]) for l in L), X(0))
        lo_a, hi_a = lo_b, hi_b
        cum = X(0)
        for l in L:
            lid = l["line_id"]
            member, causes, handle = MEMBERS[lid]
            if handle is not None:
                assert handle in D66_HANDLES, (lid, handle)
            before = (D6(l["held_low"]), D6(l["held_high"]))
            w = before[1] - before[0]
            cum += w
            cond = None
            if lid == "L-919a5749ef79759e01ca":
                after = R.narrow(before=before, after=(R.q6(X("0.10") * X(h412)), before[1]),
                                 source={"kind": "DRAWN_HEAD_UNDER_PRINTED_BEAM",
                                         "ref": f"R-T689-1: W28 head 12.200 - tol 0.013 + B8 0.75 = {s_lo}; "
                                                f"column 412 supports B8; h >= {h412} m"})
            else:
                after = R.keep(before, "; ".join(f"{k} {i or 'NO REGISTER ITEM'}" for k, i in causes))
                if any(k == "TOP DATUM" for k, _ in causes) and lid in COND:
                    a, h_extra = COND[lid]
                    cond = {"low_if_one_plane": str(R.q6(a * (s_lo - h_extra - BASE_2F))),
                            "premise": "the same one-plate premise the current low (R-T669-2, 12.68) rests on; "
                                       "R-T678-2 refuses it (T 18 printed inside the plate)"}
            new_lo = X(after["low"])
            lo_a += new_lo - before[0]
            rows.append({"family": ic, "line_id": lid, "element_id": l["element_id"], "member": member,
                         "top_80pct": lid in top_set, "rank_cum_pct": str((100 * cum / tot).quantize(X("0.1"))),
                         "before": [str(before[0]), str(before[1])], "width": str(w),
                         "after": [str(after["low"]), str(after["high"])], "after_state": after["state"],
                         "causes": [{"kind": k, "item": i} for k, i in causes],
                         "searched": "; ".join(sorted({SEARCHED[k] for k, _ in causes if k in SEARCHED})),
                         "conditional": cond})
        fam[ic] = {"bounded_lines": len(L), "before": [str(lo_b), str(hi_b)], "width_before": str(hi_b - lo_b),
                   "after": [str(lo_a), str(hi_a)], "width_after": str(hi_a - lo_a),
                   "width_reduced_m3": str((hi_b - lo_b) - (hi_a - lo_a)), "top_80pct_lines": len(top_set)}
    gaps = R.register_gaps([{"line_id": r["line_id"], "causes": r["causes"]} for r in rows if r["top_80pct"]],
                           REGISTER | {"FR-T642-2"})
    cond_total = sum((X(r["conditional"]["low_if_one_plane"]) - X(r["before"][0]) for r in rows if r["conditional"]),
                     X(0))

    # Next related item: BLANK column lines whose two section readings are both known (CONFLICT pair, drawn outline
    # vs schedule band; own read of the outline) and whose height is bounded by a merged / this-run datum:
    # bound = a_min x h_lo .. a_max x h_hi (R-COL-SECTION-CONFLICT-1, as the bounded D-66 lines), never one reading.
    sched = t566["schedule"]
    gf_sec = {p["members"]["GF"]["handle"]: (p["labels"]["FP"]["mark"], p["members"]["GF"]["section_mm"])
              for p in t566["positions"] if "GF" in p["members"]}
    blank = {l["line_id"]: l for l in idx["lines"] if l["item_code"] == "STR.CONC.COLUMN" and l["class"] == "HELD"
             and l["held_low"] is None}
    annex_h = (X("3.544") - X("0.25"), X("4.30") - X("0.25"))  # R-T678-2 annex datum (merged, Checker-verified)
    c5_h = (X(h412), FINISHED_ROOF - BASE_2F)                  # R-T689-1 at 415 (B8 support) .. D-39 ceiling
    plan = [  # line, member, outline handle, storey band, height pair, height source, own-read outline
        ("L-9f5a647014bbf83359f9", "C GF annex (one of the trio 34A / 34D / 356, identical readings; pairing not asserted)", "34A", "GR", annex_h, "R-T678-2 annex 3.294 .. 4.05"),
        ("L-c0b3340a906c2c7650f8", "C GF annex (one of the trio, pairing not asserted)", "34D", "GR", annex_h, "R-T678-2 annex 3.294 .. 4.05"),
        ("L-e6c1c9a7feec10f64975", "C GF annex (one of the trio, pairing not asserted)", "356", "GR", annex_h, "R-T678-2 annex 3.294 .. 4.05"),
        ("L-694a75c84dd6e4bb4491", "C3 GF annex", "350", "GR", annex_h, "R-T678-2 annex 3.294 .. 4.05"),
        ("L-bc01297b1c4a4c45a15f", "C5 2F (B8 east support)", "415", "2ND", c5_h,
         f"R-T689-1 B8 joint {h412} .. D-39 ceiling 4.25"),
    ]
    sec_2f = {h: (marks_2f[h], [int(1000 * own["sfrs_columns"][h]["w_m"] + 0.5),
                                int(1000 * own["sfrs_columns"][h]["d_m"] + 0.5)]) for h in ("415",)}
    blank_rows = []
    for lid, member, h, band, (hl, hh), hsrc in plan:
        assert lid in blank, lid
        mark, drawn = gf_sec[h] if h in gf_sec else sec_2f[h]
        w, d = sched[mark]["bands"][band]
        a_draw = X(drawn[0]) * X(drawn[1]) / X(10**6)
        a_sch = X(w) * X(d) / X(10**4)
        assert a_draw != a_sch, (lid, "AGREE: not a conflict pair")
        cb = R.conflict_bound(areas=(a_draw, a_sch), height=(hl, hh), item="D-39 / Q-54 B / section CONFLICT")
        lo, hi = cb["low"], cb["high"]
        nb = R.narrow(before=(None, None), after=(lo, hi),
                      source={"kind": "CONFLICT_PAIR_X_HEIGHT_BOUND",
                              "ref": f"outline {h} {drawn[0]}x{drawn[1]} mm vs schedule {mark} {band} {w}x{d} cm; {hsrc}"})
        blank_rows.append({"line_id": lid, "element_id": blank[lid]["element_id"], "member": f"{member}, outline {h}",
                           "before": "blank (OPEN)", "after": [str(nb["low"]), str(nb["high"])],
                           "areas_m2": [str(min(a_draw, a_sch)), str(max(a_draw, a_sch))],
                           "height_m": [str(hl), str(hh)], "source": nb["source"]["ref"],
                           "section_item": "D-66" if h in D66_HANDLES else None})
    gaps_blank = [[r["line_id"], "SECTION"] for r in blank_rows if r["section_item"] is None]
    blo = sum((X(r["after"][0]) for r in blank_rows), X(0))
    bhi = sum((X(r["after"][1]) for r in blank_rows), X(0))
    return {
        "schema": "T689_HELD_RANGES_V1", "task": "T-689", "candidate": idx["candidate_version"],
        "rules": ["R-T689-1 1.0.0", "R-T689-2 1.0.0", "R-T689-3 1.0.0"],
        "not_claimed": "research only; no candidate line, rule / knowledge version file, key map or default changed; "
                       "nothing released; development villa, not an accuracy claim",
        "families": fam,
        "b8_bound": {"beam": beam["id"], "depth_m": str(beam["depth"]), "clear_span_m": str(span),
                     "heads": [hd["W28"], hd["W29"]], "s_lo": str(s_lo), "s_lo_before": str(S_LO_BEFORE),
                     "governing": top["governing"], "supports": {"412": marks_2f["412"], "415": marks_2f["415"]},
                     "h_lo_412": h412, "plate_transfer": plate,
                     "c5_415_note": "2F C5 (L-bc01297b) is a B8 support too, but its line is blank (section D-66): "
                                    f"it gains the height floor h >= {h412} m only, no m3 (section not settled)"},
        "conditional_on_one_plane_m3": str(cond_total),
        "register_gaps": [list(g) for g in gaps],
        "lines": rows,
        "blank_to_bounded": {"lines": blank_rows, "low": str(blo), "high": str(bhi),
                             "column_blank_before": len(blank), "column_blank_after": len(blank) - len(blank_rows),
                             "register_gaps": gaps_blank},
    }


# lines whose low would move under the plate premise: (section area m2, member below the slab top)
COND = {
    "L-53f223b06db14ac41d47": (X("0.14"), X("0")),
    "L-26f6b6f2365c72e42291": (X("0.10"), X("0")),
    "L-33a9b7728781fcba12e2": (X("0.10"), X("0")),
    "L-d79d17d14f39d5148cb8": (X("0.10"), X("0")),
    "L-541c7e565bb93ecdb78b": (X("0.08"), X("0.75")),  # PC-2F top = B7 soffit (T-678)
}


def md(res):
    o = ["# T-689 held COLUMN / BEAM ranges on " + res["candidate"], "",
         "Generated by `t689_alsenan.py`; m3; before = V3.0.67 index, after = this research (unwired).", ""]
    for ic, f in res["families"].items():
        o.append(f"- {ic}: {f['bounded_lines']} bounded lines, {f['before'][0]} .. {f['before'][1]} (width "
                 f"{f['width_before']}) -> {f['after'][0]} .. {f['after'][1]} (width {f['width_after']}, reduced "
                 f"{f['width_reduced_m3']}); top 80 %: {f['top_80pct_lines']} lines")
    b = res["b8_bound"]
    o += ["", f"B8 bound: s_lo {b['s_lo']} (before {b['s_lo_before']}), governing {b['governing']}; 412 h_lo {b['h_lo_412']} m; "
          f"plate transfer {b['plate_transfer']['state']}: {b['plate_transfer'].get('why', '')}",
          f"Conditional on one plane (not applied): +{res['conditional_on_one_plane_m3']} m3 on the low ends.",
          f"Register gaps (top 80 %): {res['register_gaps']}", "",
          "| Family | Line | Member | cum % | Before | After | Causes (item) | Conditional low |", "|---|---|---|---|---|---|---|---|"]
    for r in res["lines"]:
        c = ", ".join(f"{x['kind']} {x['item'] or 'NONE'}" for x in r["causes"])
        o.append(f"| {r['family'].split('.')[-1]} | {r['line_id'][:10]} | {r['member']} | {r['rank_cum_pct']}"
                 f"{'' if r['top_80pct'] else ' (outside 80 %)'} | {r['before'][0]} .. {r['before'][1]} | "
                 f"{r['after'][0]} .. {r['after'][1]} | {c} | "
                 f"{r['conditional']['low_if_one_plane'] if r['conditional'] else ''} |")
    b = res["blank_to_bounded"]
    o += ["", f"Blank COLUMN lines bounded (conflict pair x height bound): {len(b['lines'])}, {b['low']} .. {b['high']} m3; "
          f"blank {b['column_blank_before']} -> {b['column_blank_after']}; section register gaps {b['register_gaps']}", "",
          "| Line | Member | Areas m2 | Height m | After | Section item |", "|---|---|---|---|---|---|"]
    for r in b["lines"]:
        o.append(f"| {r['line_id'][:10]} | {r['member']} | {r['areas_m2'][0]} .. {r['areas_m2'][1]} | "
                 f"{r['height_m'][0]} .. {r['height_m'][1]} | {r['after'][0]} .. {r['after'][1]} | "
                 f"{r['section_item'] or 'NONE'} |")
    return "\n".join(o) + "\n"


def main():
    res = build()
    js = json.dumps(res, indent=1, sort_keys=True, default=str) + "\n"
    if "--write" in sys.argv:
        OUT_JSON.write_text(js)
        OUT_MD.write_text(md(res))
    if "--check" in sys.argv:
        assert OUT_JSON.read_text() == js and OUT_MD.read_text() == md(res), "outputs stale"
        print("T689 outputs reproduce")
    print(json.dumps(res["families"], indent=1, default=str), res["b8_bound"]["s_lo"], res["conditional_on_one_plane_m3"],
          res["register_gaps"])


if __name__ == "__main__":
    main()
