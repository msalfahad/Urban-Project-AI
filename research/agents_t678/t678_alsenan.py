"""T-678 development-villa build: (a) the 22 OPEN BOUND STR.CONC.LINTEL lines of the T-673 census (V3.0.64 / V3.0.65,
unchanged by T-671), (b) F-C-T669-1 outline 778, (c) annex roof column C3 lower end. Research only, unwired.

Committed inputs only (no drawing is opened here; the own DXF reads of this run are in READS, values in m):
  T-673 census        research/agents_t673/out/T673_LEDGER.json (the 22 OPEN BOUND rows, line ids)
  V3.0.65 index       research/agents_t671/out/LINE_INDEX_V3_0_65.json (line ids / classes asserted)
  opening census      research/agents_t198/OPENINGS_T198.csv (width, printed / owner-fallback heights)
  payable form        research/agents_t650/out/T650_PAYABLE_FORM.json (B, D, schedule row; 60 / 60 RC cast)
  run pieces          research/agents_t274/T274_RUN_PIECES.csv + T274_CORRECTED.csv (T-274 exact pieces, MERGED)
  beam depths         research/agents_t110/BEAM_MEMBER_REGISTER.csv (schedule depths)
  drawn heads         research/agents_t201/HEADS_T201.csv (W04 / W08 annex heads +2.80, DRAWING-CONFIRMED)
  jamb evidence       research/agents_t644/out/JAMB_EVIDENCE_T644.csv, research/agents_t544/out/EXTENDED_SEARCH_T544.csv
  planted column      research/agents_t220 (PC-2F = outline 778; section CONFLICT 20x50 text / 20x40 drawn)
  2F slab-top bound   research/agents_t669 (R-T669-2: top >= W26 apex 12.50 + T18 = 12.68)

    python3 -I research/agents_t678/t678_alsenan.py [--write]
"""
from __future__ import annotations

import csv
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t678_rules as R  # noqa: E402

R73 = R.R73
RES = ROOT / "research"
T673 = RES / "agents_t673" / "out" / "T673_LEDGER.json"
INDEX = RES / "agents_t671" / "out" / "LINE_INDEX_V3_0_65.json"
OPEN = RES / "agents_t198" / "OPENINGS_T198.csv"
T650 = RES / "agents_t650" / "out" / "T650_PAYABLE_FORM.json"
PIECES = RES / "agents_t274" / "T274_RUN_PIECES.csv"
CORR = RES / "agents_t274" / "T274_CORRECTED.csv"
BEAMS = RES / "agents_t110" / "BEAM_MEMBER_REGISTER.csv"
HEADS = RES / "agents_t201" / "HEADS_T201.csv"
JAMBS = RES / "agents_t644" / "out" / "JAMB_EVIDENCE_T644.csv"
EXT = RES / "agents_t544" / "out" / "EXTENDED_SEARCH_T544.csv"
OUT = HERE / "out" / "T678_LEDGER.json"
OUT_MD = HERE / "out" / "T678_CENSUS.md"
BED = "0.06"            # R-T453-4 floor-bed stand-in, unchanged (as T-673)
X = Decimal

# Own reads this run (Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf', sha 9f9d1179, decoded into .work/private only;
# values relative, m). Sheet titles from the title blocks: SFRS 'SECOND FLOOR ROOF SLAB.', FFRS 'FIRST FLOOR ROOF SLAB.'
# (+38.724 m), GFRS 'GROUND FLOOR ROOF SLAB.' (+77.449 m).
READS = {
    "778": {"layer": "S-COL.BON", "size_m": [0.20, 0.40], "hatch": "777 S-COL.HAT (SOLID: the column's own storey)",
            "diagonal": "776 S-COL.BON", "inside_2F_roof_outline": "x 7.900 .. 8.100 of the layer-1 outline -0.075 .. "
            "8.100 (from column 40F SW corner): east face ON the slab edge; y -4.518 .. -4.118 inside -6.3 .. 0.5",
            "beam_through": "B7 edges 39A (x 0.200) / 39B (x 0.000) run y -1.782 .. 5.018 through the outline (B7 "
                            "0.20 wide = the column width)",
            "start_below": "FFRS 77B 0.20 x 0.40 (hatch 77A ANSI35 = starts here), text 77C 'P.C 20x50', 77D '8%%C16', "
                           "on B19 (edges 6B1 / 6B2); GFRS: no outline at the position (no GF / 1F column under it)"},
    "GFRS_annex": {"texts": "annex part (beams CB6 / CB7 / B9 / B4 / CB5 / B2 / B1): no level text, no 'T nn' slab "
                            "thickness, no step text; only beam marks, bar notes, 'AS PER SCH.', section marks",
                   "deeper_beams": "the only GFRS beams deeper than 0.75 are B26 / B27 0.85, which carry PC-1F-B / "
                                   "PC-1F-A at +5.45 (T-220): main roof plane, not the annex plane"},
}
# R-T678-2 inputs (annex roof, one plane: arch finished +4.30 one mark over the whole annex roof ROOF-430, T-321; ST GFRS
# annex part prints no step / level / thickness, READS above; section B-B one slab, Q-54 text)
ANNEX = {"ffl": X("0.30"), "finished": X("4.30"), "d_max_plane": X("0.75"), "column_base": X("0.25")}
C3 = {"line": "L-fad18af6", "section_m2": X("0.125"), "hi_before": X("0.50625")}
PC2F = {"line": "L-541c7e565bb93ecdb78b", "element": "HL:PLANTED_COLUMN:PC-2F:CONCRETE", "area_lo": X("0.08"),
        "area_hi": X("0.10"), "base": X("9.65"), "top_lo": X("12.68"), "top_hi": X("13.90"), "b7_depth": X("0.75")}

# per-opening evidence that is not a column of a committed table (each value cited)
EVID = {
    "D-GF-07": {"storey": "GF", "basis": "pieces", "ffl_note": "GF main +1.00 (dining / entrance landing +1.00)"},
    "W01": {"storey": "GF", "basis": "pieces", "ffl_note": "GF main +1.00 (stair hall)"},
    "D-1F-05": {"storey": "1F", "basis": "pieces", "ffl_note": "1F +5.50"},
    "D-1F-06": {"storey": "1F", "basis": "pieces", "ffl_note": "1F +5.50"},
    "W13": {"storey": "1F", "basis": "position", "band": "1F|WB-FL0074-FL0076", "ffl_note": "1F +5.50"},
    "D-GF-01": {"storey": "GF annex", "basis": "annex", "members": [("B2", "0.40")],
                "ffl_note": "dewaneya +0.30 PRINTED / open court +0.15: worst (higher) +0.30"},
    "D-GF-02": {"storey": "GF annex", "basis": "annex", "members": [("B4", "0.50"), ("slab GF-137", None)],
                "ffl_note": "wash / W.C. by the dewaneya +0.30 (T-088 DERIVED, no step drawn)"},
    "D-GF-03": {"storey": "GF annex", "basis": "annex", "members": [("CB6", "0.75")],
                "ffl_note": "driver room +0.30 PRINTED / court +0.15: worst +0.30"},
    "D-GF-04": {"storey": "GF annex", "basis": "annex", "members": [("slab GF-139", None)],
                "ffl_note": "driver room +0.30 PRINTED / driver W.C. +0.30 DERIVED"},
}
NEIGHBOURS = {"W04": "HELD", "W08": "HELD"}   # D-GF-03's piers: both windows' existence open (this census)

OPEN_NAMED = {
    "A-GF-01": ("arched head: crown level printed nowhere, drawn arch not dimensioned (T-238 SOURCE-SUPPORTED); width "
                "not drawn; a curved head is never a straight-lintel m3 (R-T673-3)",
                "the A-GF-01 crown level (with the annex bound c_lo 2.744 above +0.30 under B4: REQUIRED if crown <= "
                "2.484 above FFL) and its width"),
    "D-1F-01": ("door in the held part of 1F-W11 under the dome opening ring 1F-073 (nothing with a printed soffit; "
                "closable pieces 0.12 + 0.12 m cannot hold a 0.80 m door)", "dome ring soffit over 1F-W11 (T-227, designer)"),
    "D-1F-09": ("D-1F-09 lies wholly inside the east dome opening 1F-077: top of wall not drawn", "T-227 (designer)"),
    "D-2F-02": ("IN_HELD_PIECE under BM-2F-017 (unlabelled, depth not printed, D-04 / Q-61 C(4))",
                "BM-2F-017 depth: REQUIRED for any depth <= 0.52 m on the drawn 2F slab-top bound (12.68 - 9.70 - D >= "
                "2.20 + 0.20 + 0.06); above that the D-39 slab top decides"),
    "D-GF-05": ("floor of the side passage on the other side (Q-67 passage) printed nowhere; START stopper "
                "WB-FL0001-FL0002:NOT_WALL not recorded", "side-passage FFL (REQUIRED if <= +0.30: CB7 bound c_lo "
                "2.494, spare 0.034) and the START jamb stopper"),
    "D-GF-08": ("printed note ST p.8 n.19 calls for an unsized lift tie beam over GF-W08", "the lift tie beam depth "
                "and level (D-43)"),
    "D-GF-14": ("host GF-W30 has no drawn wall piece (no band / member in the T-274 run geometry) and no T-644 jamb row",
                "the GF-W30 run (band) and its jamb evidence"),
    "W04": ("CB6 sits over the drawn head (+2.80): lintel needed only if the annex slab top >= +3.829 (2.80 + 0.019 "
            "+ 0.20 + 0.06 + 0.75); bound today 3.544 .. 4.30", "annex roof slab top (Q-54 B / D-39)"),
    "W08": ("as W04: threshold +3.816 (2.80 + 0.006 + 0.20 + 0.06 + 0.75)", "annex roof slab top (Q-54 B / D-39)"),
    "W11": ("no drawn head (T-201 FENCE: edges not the opening's; T-207 height 2.20 DRAWING-CONFIRMED, sill HELD)",
            "W11 sill level (REQUIRED if head <= 2.234 above +0.30 under B9 0.75)"),
    "W12": ("as W11", "W12 sill level (as W11)"),
    "W25": ("in the stair-shaft piece SF B3 (With Stair): landing member over W25 at 'about +7.6', not printed "
            "(R-T228-3 F3)", "the 1F stair-shaft landing member level / depth over W25"),
    "W27": ("in the stair-shaft piece SF B3 (SL-1): no floor member at +9.70 printed on the shaft line (R-T228-3 F4)",
            "the 2F stair-shaft member level / depth over W27"),
}
OWNER_PRECAST = [X("1.20"), X("1.50"), X("2.50"), X("3.00"), X("4.00")]   # owner lintel rule 2026-11-02


def _csv(p):
    return list(csv.DictReader(Path(p).open(encoding="utf-8", newline="")))


def _f(v):
    return None if v is None else format(X(str(v)).quantize(R.R73.Q6), "f")


def owner_piece(w):
    need = X(str(w)) + 2 * X("0.15")
    for L in OWNER_PRECAST:
        if L >= need:
            return f"{L} m precast ({w} + 2 x 0.15 = {need})"
    return f"FLAGGED (> 4.00 m: {need})"


def min_clear(wall):
    for r in _csv(CORR):
        if r["wall_id"] == wall:
            hs = [X(p.split(" h ")[-1].strip()) for p in r["exact_pieces"].split("|")]
            return min(hs), max(hs), r["exact_pieces"]
    raise KeyError(wall)


def position_clear(band, jambs, storey_h=X("4.20")):
    """W13: the opening extent from its jamb availabilities, the run pieces over it (T-274 positions)."""
    rows = [r for r in _csv(PIECES) if r["run_key"] == band]
    pcs = [(r["from_m"], r["to_m"], r["kind"], r["depth_m"] or None) for r in rows]
    beam = [r for r in rows if r["kind"] == "BEAM" and X(r["len_m"]) > 1]
    st = {j["side"]: X(j["v3_available_6dp_m"]) for j in jambs}
    # the START jamb column face: the COLUMN piece that precedes the long beam piece
    cols = [r for r in rows if r["kind"] == "COLUMN"]
    assert len(cols) == 2, cols            # the opening's two jamb columns (both stoppers COLUMN)
    x0 = X(cols[0]["to_m"]) + st["START"]
    x1 = X(cols[1]["from_m"]) - st["END"]
    assert abs((x1 - x0) - X("1.20")) < X("0.002"), (x0, x1)   # = the printed width 1.20
    over = R.pieces_over(pcs, x0, x1)
    assert all(k == "BEAM" and d for _, _, k, d in over), over
    d = max(X(d) for *_, d in over)
    return storey_h - d, storey_h - d, {"extent": [_f(x0), _f(x1)], "over": [(str(a), str(b), k, d) for a, b, k, d in over],
                                        "beams": [r["mark"] for r in beam]}


def annex_bound():
    heads = {r["ID"]: r for r in _csv(HEADS)}
    hs = []
    import re
    for oid in ("W04", "W08"):
        h = heads[oid]
        tol = X(re.search(r"max edge offset ([0-9.]+) m", h["ISSUE_CHECK"]).group(1))
        hs.append({"id": oid, "head_abs": h["HEAD_LEVEL_M"], "tol": tol, "status": h["STATUS"], "beam_depth": "0.75"})
    return R.slab_top_lower_bound(heads=hs, one_plane=True, finished_ceiling=ANNEX["finished"]), hs


def lintels():
    led = json.loads(T673.read_text(encoding="utf-8"))
    ix = json.loads(INDEX.read_text(encoding="utf-8"))
    assert ix["candidate_version"].endswith("3.0.65")
    by_id = {l["line_id"]: l for l in ix["lines"]}
    cen = {r["ID"]: r for r in _csv(OPEN)}
    pf = json.loads(T650.read_text(encoding="utf-8"))["per_opening"]
    jam = {}
    for r in _csv(JAMBS):
        jam.setdefault(r["opening_id"], []).append(r)
    ext = {(r["opening_id"], r["side"]): r for r in _csv(EXT)}
    ab, ab_heads = annex_bound()
    s_lo = ab["s_lo"]
    rows = []
    for r in led["lintels"]:
        if r["cause"] != "OPEN BOUND":
            continue
        oid, lid = r["opening"], r["line_id"]
        ln = by_id[lid]
        assert ln["class"] == "HELD" and ln["measured_net"] is None and ln["held_low"] is None, lid
        p, c = pf[oid], cen[oid]
        before = "HELD blank (T-673 OPEN BOUND)"
        if oid not in EVID:
            why, missing = OPEN_NAMED[oid]
            rows.append({"opening": oid, "line_id": lid, "member": r["member"], "before": before,
                         "after": "HELD blank (OPEN BOUND, missing datum named)", "cause": "OPEN BOUND",
                         "existence": "HELD", "why": why, "missing_datum": missing, "low_m3": None, "high_m3": None,
                         "owner_manual": owner_piece(p["width_m"])})
            continue
        ev = EVID[oid]
        if c["HEIGHT_STATUS"] == "PRINTED":
            head, hst = X(c["HEIGHT_M"]) + X(c["SILL_M"]), "PRINTED"
        elif c["HEIGHT_STATUS"] == "ASSUMED" and "OWNER-APPROVED" in c["HEIGHT_SOURCE"]:
            head, hst = X(c["HEIGHT_M"]), "ASSUMED - OWNER-APPROVED"
        else:
            raise AssertionError(oid)
        host = r["why"].split()[1]
        detail = {}
        if ev["basis"] == "pieces":
            c_lo, c_hi, src = min_clear(host)
            detail = {"pieces": src, "c": "min over every T-274 exact piece of the host"}
        elif ev["basis"] == "position":
            c_lo, c_hi, detail = position_clear(ev["band"], jam[oid])
            detail["c"] = "4.20 storey - the beam over the opening's own extent (T-449 piece 3.80)"
        else:
            sof = []
            for name, dep in ev["members"]:
                sof.append(R.soffit_lower_bound(s_lo, dep, slab_only=dep is None, d_max=ANNEX["d_max_plane"]))
            c_lo = min(sof) - ANNEX["ffl"]
            deps = [X(d) for _, d in ev["members"] if d]
            c_hi = ANNEX["finished"] - (min(deps) if deps else X(0)) - ANNEX["ffl"]
            detail = {"s_lo": str(s_lo), "members": ev["members"],
                      "c": f"min soffit bound {min(sof)} - FFL 0.30 (R-T678-2; slab pieces at D_max 0.75)"}
        st, spare, why = R.existence_bounded(head=head, tol=0, head_status=hst, c_lo=c_lo, c_hi=c_hi, d=p["D_m"],
                                             bed=BED)
        assert st == R.REQUIRED, (oid, st, spare)
        ends = []
        open_end = False
        for j in jam[oid]:
            e = {"side": j["side"], "a": j["v3_available_6dp_m"], "stopper": j["stopper"], "stopper_id": j["stopper_id"]}
            if j["stopper"] == "SEARCH_LIMIT" and (oid, j["side"]) in ext:
                x = ext[(oid, j["side"])]
                e.update(extended=x["available_6dp_m"], extended_stopper=x["stopper"])
            if j["stopper"] == "OPENING" and j["stopper_id"] not in NEIGHBOURS:
                open_end = True
            ends.append(e)
        lin = {"id": oid, "width_m": p["width_m"], "B": p["B_m"], "D": p["D_m"], "form": "STRAIGHT", "ends": ends}
        q = R.lintel_m3_open_end(lin) if open_end else R73.lintel_m3(lin, NEIGHBOURS)
        rows.append({"opening": oid, "line_id": lid, "member": r["member"], "before": before,
                     "after": "HELD bounded (existence REQUIRED, quantity a range)", "cause": "MEASURABLE NOW",
                     "existence": f"REQUIRED (spare {spare} m)", "why": why, "head": [str(head), hst],
                     "clear": [_f(c_lo), _f(c_hi)], "detail": detail, "ffl": ev["ffl_note"],
                     "convention": q["convention"], "low_m3": _f(q["lo_m3"]), "high_m3": _f(q.get("hi_m3")),
                     "ends": [(e["side"], e["stopper"], e["stopper_id"], e["a"]) for e in ends],
                     "owner_manual": owner_piece(p["width_m"]), "missing_datum": None})
    return rows, ab, ab_heads


def build():
    rows, ab, ab_heads = lintels()
    meas = [r for r in rows if r["cause"] == "MEASURABLE NOW"]
    lo = sum(X(r["low_m3"]) for r in meas)
    hi_open = any(r["high_m3"] is None for r in meas)
    hi = None if hi_open else sum(X(r["high_m3"]) for r in meas)
    hi_closed = sum(X(r["high_m3"]) for r in meas if r["high_m3"] is not None)
    pc = R.column_m3(PC2F["area_lo"], PC2F["area_hi"], PC2F["base"], PC2F["top_lo"], PC2F["top_hi"], PC2F["b7_depth"])
    c3 = R.column_m3(C3["section_m2"], C3["section_m2"], ANNEX["column_base"], ab["s_lo"], ANNEX["finished"])
    assert c3["hi_m3"] == R.q6(C3["hi_before"]), c3
    return {
        "task": "T-678", "candidate": "ARCH_TAKEOFF_V3.0.65", "rules": ["R-T678-1 1.0.0", "R-T678-2 1.0.0",
                                                                         "R-T678-3 1.0.0"],
        "lintels": rows,
        "counts": {"open_bound_before": 22, "open_bound_after": len(rows) - len(meas), "measurable_now": len(meas)},
        "lintel_totals_m3": {"lines": len(meas), "low": _f(lo), "high": _f(hi), "high_of_closed_lines": _f(hi_closed),
                             "open_high_lines": [r["opening"] for r in meas if r["high_m3"] is None]},
        "annex_slab_top": {"rule": "R-T678-2", "s_lo": str(ab["s_lo"]), "governing": ab["governing"],
                           "heads": [{k: str(v) for k, v in h.items()} for h in ab_heads],
                           "finished_ceiling": str(ANNEX["finished"]), "plane_reads": READS["GFRS_annex"]},
        "outline_778": {"verdict": "MEMBER: planted column PC-2F (T-220 COL-2F-59), NOT 'owned by no line'",
                        "owner_line": PC2F["line"], "element_id": PC2F["element"], "before": "HELD blank (V3.0.65)",
                        "after": "HELD bounded", "lo_m3": _f(pc["lo_m3"]), "hi_m3": _f(pc["hi_m3"]),
                        "height_m": [_f(pc["h_lo"]), _f(pc["h_hi"])],
                        "basis": "section CONFLICT 0.08 (drawn 20x40) .. 0.10 (text 'P.C 20x50') x base +9.65 (B19 top "
                                 "= 1F roof slab top, T-214 / T-220) to the B7 soffit (B7 20x75 billed through it, owns "
                                 "the joint): slab top 12.68 (R-T669-2, same plate) .. 13.90 (R-T658-4 ceiling)",
                        "reads": READS["778"]},
        "annex_C3": {"line": C3["line"], "before": "AT_MOST 0.50625, low open by name",
                     "after_lo_m3": _f(c3["lo_m3"]), "after_hi_m3": _f(c3["hi_m3"]), "height_m": [_f(c3["h_lo"]),
                                                                                                 _f(c3["h_hi"])],
                     "basis": "0.125 x (annex slab top >= 3.544 (R-T678-2: W08 drawn head +2.80 - 0.006 under CB6 "
                              "20x75) - base 0.25 APPROVED) .. (4.30 - 0.25)",
                     "follow_up": "the same height bound 3.294 .. 4.05 m applies to the 4 other GF annex column lines "
                                  "(L-694a75c8, L-c0b3340a, L-e6c1c9a7, L-9f5a6470) once D-66 settles their section"},
    }


def write_md(led):
    L = ["# T-678 census: the 22 OPEN BOUND STR.CONC.LINTEL lines of T-673 (V3.0.65), outline 778, annex C3", "",
         f"counts: {led['counts']} ; measurable-now lintel total: {led['lintel_totals_m3']}", "",
         "| # | line | opening | before | after | existence / cause | low m3 | high m3 | owner manual (precast) | "
         "missing datum |", "|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(led["lintels"], 1):
        L.append(f"| {i} | {r['line_id']} | {r['opening']} | {r['before']} | {r['after']} | {r['existence']}: "
                 f"{r['why']} | {r['low_m3'] or '-'} | {r['high_m3'] or ('OPEN' if r['low_m3'] else '-')} | "
                 f"{r['owner_manual']} | {r['missing_datum'] or '-'} |")
    o, c = led["outline_778"], led["annex_C3"]
    L += ["", f"778: {o['verdict']}; line {o['owner_line']} {o['before']} -> {o['lo_m3']} .. {o['hi_m3']} m3 "
              f"(height {o['height_m'][0]} .. {o['height_m'][1]} m); {o['basis']}",
          "", f"annex C3 {c['line']}: {c['before']} -> {c['after_lo_m3']} .. {c['after_hi_m3']} m3 (height "
              f"{c['height_m'][0]} .. {c['height_m'][1]} m); {c['basis']}; {c['follow_up']}",
          "", "annex slab-top bound: " + json.dumps({k: led['annex_slab_top'][k] for k in ('s_lo', 'governing')}), ""]
    return "\n".join(L)


def main(argv):
    led = build()
    if "--write" in argv:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(led, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        OUT_MD.write_text(write_md(led), encoding="utf-8")
    print(json.dumps({"counts": led["counts"], "lintels": led["lintel_totals_m3"],
                      "778": [led["outline_778"]["lo_m3"], led["outline_778"]["hi_m3"]],
                      "C3": [led["annex_C3"]["after_lo_m3"], led["annex_C3"]["after_hi_m3"]],
                      "s_lo": led["annex_slab_top"]["s_lo"]}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
