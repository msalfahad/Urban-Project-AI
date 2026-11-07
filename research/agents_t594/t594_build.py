"""T-594: the reconciled-quantities statement V8 = the T-587 statement V7 (rebuilt read only and checked equal to its
committed JSON and markdown; every V7 key carried byte-equal, lists extended as a prefix) + restated sections for T-581
r2 (lintels nr, D-GF-09 DRAWING CONFLICT; lm 91.5 .. 91.8 beside), T-585 (yard skirting RULE_DIFFERENCE / SCOPE; stair
flights two forms, MS1-T winders bounded), T-592 + register 08:15 (door / gate steps in T-577 marble lm) and beside
blocks for T-589 (structural closure classes) and T-595 (ring side bars both faces; S02 footing low). No private
input; no quantity moves; nothing released.

  python3 -I research/agents_t594/t594_build.py --write   # write out/
  python3 -I research/agents_t594/t594_build.py --check   # rebuild and compare with out/ (exit 1 on a difference)
"""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t594_adapters as A  # noqa: E402
Z = A.Z
A7 = A.A7
sys.path.insert(0, str(A.T587))
import t587_build as B587  # noqa: E402  (T-587, read only)

D = Decimal
OUT = HERE / "out"
JSON_OUT = OUT / "RECONCILED_STATEMENT_T594.json"
MD_OUT = OUT / "RECONCILED_STATEMENT_T594.md"
NEW_REPORTS = ["T-581", "T-585", "T-589", "T-592", "T-593", "T-595"]
PENDING = ["T-590 (RULE_DIFF provenance, structural: TODO)", "T-598 (stair nosing 20 HELD edges: READY, not merged; "
           "the T-578 nosing cross-reference stays as in V7)"]
EXTENDED = B587.EXTENDED
SUPERSEDES = {
    "T-571/lintel-count-implied": "T-571/lintel-count-implied@V8",
    "T-574/skirting-outdoor": "T-574/skirting-outdoor@V8",
    "T-574/skirting-stairs": "T-574/skirting-stairs@V8",
    "T-577/marble-lm@V7": "T-577/marble-lm@V8",
    "beside_v7 T-583/dome-lift-components": "beside_v8 T-595/dome-lift-components@V8",
}
LESSONS_ADOPTED = [
    "T-581 (Checker ADOPTED): a frame drawn over masonry is a DRAWING CONFLICT, UNRESOLVED with a bound, never "
    "chosen by method",
    "T-585 (Checker ACCEPTED): a yard skirting equal to a paving perimeter is scope; only a printed base makes a "
    "quantity, the wall foot is named, never valued",
    "T-589 (Checker ADOPTED, R-T589-1): every structural component is classed CLOSABLE / DESIGNER / OWNER GAP with its "
    "sheet before it is called verifiable",
    "T-592 (Checker ADOPTED, R-T592-1): one element, one payable length (the installed piece in the wall gap); the "
    "visible edge is an attribute",
    "Register 08:15: a skirting is the same physical test everywhere (finished floor + finished wall + drawn or noted "
    "base); exterior faces need a printed base"]
REGISTER_RULINGS = [
    {"entry": "EXTERNAL DOOR STEP, PAYABLE LENGTH", "ruling": "CLOSED: one length, stone in the wall gap (= T-325 "
     "strip), house 3.800 lm nr 4, riser 0.570 m2; nosing 3.500 attribute", "statement_effect": "T-577/marble-lm@V8 "
     "EXT rows (F-T594-5)"},
    {"entry": "GATE STEP", "ruling": "marble / stone door-step family, own row, 1.000 lm / 0.150 m2 PARTIAL",
     "statement_effect": "T-577/marble-lm@V8 EXT gate row HELD (PV); DRY row no longer names D-GF-15 (F-T594-6)"},
    {"entry": "E1 LANDING SKIRTING", "ruling": "NOT_IN_DRAWING, no line; ENGINE_OMISSION proposal withdrawn",
     "statement_effect": "T-574/skirting-stairs@V8 E1 row note (F-T594-4); 3.500 lm named beside, never valued"}]


def v7_statement() -> dict:
    st7 = B587.build()
    if st7 != json.loads(B587.JSON_OUT.read_text(encoding="utf-8")) or \
            B587.to_markdown(st7) != B587.MD_OUT.read_text(encoding="utf-8"):
        raise Z.StatementError("T-587 statement V7 does not reproduce: rebuild it before T-594")
    return st7


def check_v7_unchanged(st: dict, st7: dict) -> None:
    """Every V7 key is byte-equal (sorted JSON); the extended lists keep V7 as their prefix."""
    for k in st7:
        if k in EXTENDED:
            continue
        if json.dumps(st[k], sort_keys=True) != json.dumps(st7[k], sort_keys=True):
            raise Z.StatementError(f"V7 key {k} changed in V8")
    for k in ("not_comparable", "reclasses", "reports_covered"):
        if st[k][:len(st7[k])] != st7[k]:
            raise Z.StatementError(f"V7 {k} not carried as its prefix")
    if not st["rule"].startswith(st7["rule"]):
        raise Z.StatementError("V7 rule text not carried as its prefix")
    if {k: v for k, v in st["provenance"].items() if k in st7["provenance"]} != st7["provenance"]:
        raise Z.StatementError("V7 provenance changed")


def expected_v8(sid: str, r: dict) -> str:
    """The verdict map for V8 rows (R-T587-1 (a)), independent of the stamps the adapters wrote."""
    tag = r.get("tag", "")
    if tag == "F-T594-1":
        return A.CV                     # Checker own DXF read: the conflict and its bound
    if tag in ("F-T594-2", "F-T594-3", "F-T594-4"):
        return A.PV                     # basis confirmed / arithmetic AGREE; face lengths worker-measured
    if tag == "F-T594-5":
        if r["name"].startswith("EXT door steps D-GF-01"):
            return A.CV                 # T-592 pay length VERIFIED by the Checker's own DXF read
        if r["name"].startswith("WET:"):
            return A.WP                 # the remaining 13 WET strips keep the T-577 status (0 / 8 groups)
        return A.PV                     # gate PARTIAL; residual vs his unsplit block
    if tag == "F-T594-6":
        return A.WP                     # name / bound amended on T-577 rows (engine side not re-measured)
    if sid.startswith(("T-571/", "T-574/")):
        return A7.ev_v6(sid, r)
    if sid == "T-577/marble-lm@V8":
        return B587.expected_evidence("T-577/marble-lm@V7", r)
    return B587.expected_evidence(sid, r)


def headline(secs: list[dict], superseded: dict) -> list[dict]:
    out = []
    for c in secs:
        sid = c["section_id"]
        bce = A7.by_class_evidence(c["rows"], c["unit"], lambda r, sid=sid: expected_v8(sid, r))
        out.append({"section_id": sid, "unit": c["unit"], "reference_total": c["reference_total"],
                    "engine_valued": c["engine_valued"], "difference": c["difference"],
                    "difference_pct_of_reference": c["difference_pct_of_reference"],
                    "by_class_evidence": bce, "superseded_by": superseded.get(sid)})
    return out


def build_from(st7: dict, src: dict) -> dict:
    st = copy.deepcopy(st7)
    lint, mv1 = A.t581_lintels(st7, src["T-581"])
    outd, mv2 = A.t585_outdoor(st7, src["T-585"])
    stairs, mv3 = A.t585_stairs(st7, src["T-585"])
    marble, mv5, pairs = A.t592_marble_lm(st7, src["T-592"], src["T-577"], src["T-593"])
    secs = [lint, outd, stairs, marble]
    ids = [c["section_id"] for c in st7["sections"] + st7["sections_v5"] + st7["sections_v6"] + st7["sections_v7"]]
    for c in secs:
        if c["section_id"] in ids:
            raise Z.StatementError(f"{c['section_id']}: section id already in V7")
        if c["restates"] not in SUPERSEDES or SUPERSEDES[c["restates"]] != c["section_id"] or c["restates"] not in ids:
            raise Z.StatementError(f"{c['section_id']}: restates {c['restates']} without its supersession entry")
        A7.A6.refuse_pct_without_row(c)
        A7.audit_evidence(c, lambda r, sid=c["section_id"]: expected_v8(sid, r))
        for r in c["rows"]:
            if r["class"] == "HELD" and D(r["delta"]) == 0 and not r.get("bound"):
                raise Z.StatementError(f"{c['section_id']}: HELD row '{r['name'][:60]}' at 0 with no bound")
    sup = dict(st7["supersedes_v7"], **SUPERSEDES)
    st["sections_v8"] = secs
    st["beside_v8"] = [A.t589_classes(src["T-589"]), A.t595_rebar_beside(st7, src["T-595"], st7),
                       A.t595_footing_beside(st7, src["T-595"])]
    st["supersedes_v8"] = SUPERSEDES
    st["headline_v8"] = headline(st7["sections_v6"] + st7["sections_v7"] + secs, sup)
    st["register_rulings_v8"] = {"verdict": A.REG0815, "rulings": REGISTER_RULINGS}
    st["agree_pairs_v8"] = pairs
    st["reclasses"] = st7["reclasses"] + mv1 + mv2 + mv3 + mv5
    st["reports_covered"] = st7["reports_covered"] + NEW_REPORTS
    st["reports_pending"] = PENDING
    st["rule"] = st7["rule"] + " + R-T594-1"
    st["schema_v8"] = "URBAN_T594_RECONCILED_STATEMENT_V8"
    st["lessons_adopted_applied_v8"] = LESSONS_ADOPTED
    st["provenance"]["inputs_v8"] = {str(p.relative_to(Z.ROOT)): Z.sha(p) for p in
                                     list(A.PINS) + [B587.JSON_OUT, B587.MD_OUT, HERE / "t594_adapters.py",
                                                     HERE / "t594_build.py"]}
    st["released_quantities_changed"] = 0
    Z.refuse_manifest_as_line(st)
    out = json.loads(json.dumps(st, sort_keys=True))
    check_v7_unchanged(out, st7)
    return out


def sources() -> dict:
    return {"T-581": A.load(A.T581_JSON), "T-585": A.load(A.T585_JSON), "T-589": A.load(A.T589_JSON),
            "T-592": A.load(A.T592_JSON), "T-593": A.load(A.T593_JSON), "T-595": A.load(A.T595_JSON),
            "T-577": A.load(A.T577_JSON)}


def build() -> dict:
    return build_from(v7_statement(), sources())


EV = {A.CV: "V", A.PV: "PV", A.WP: "WP"}


def _bce(h: dict) -> str:
    parts = []
    for k, m in h["by_class_evidence"].items():
        if not any(D(v) for v in m.values()):
            continue
        tot = sum((D(v) for v in m.values()), D(0))
        parts.append(f"{k} {Z.s(tot)} [" + ", ".join(f"{EV[e]} {v}" for e, v in m.items() if D(v)) + "]")
    return "; ".join(parts) or "-"


def to_markdown(st: dict) -> str:
    md = ("# T-594 reconciled-quantities statement V8 (generated; reference - engine, + = in the reference only)\n\n"
          "V8 = statement V7 (T-587, rebuilt and equal to its committed output; every V7 key carried byte-equal) + the "
          "sections and beside blocks below. Development villa; not an accuracy claim; nothing released.\n\n"
          "Evidence (R-T587-1 (a)): V = Checker VERIFIED, PV = partially verified, WP = worker-proposed, each from the "
          "Checker's verdict line, never from a handoff.\n\n")
    md += ("## Headline by class and evidence (V6 + V7 + V8 sections)\n\n| Section | Unit | Reference | Engine valued | "
           "Difference | % of ref. | By class [evidence] | Superseded by |\n|---|---|---|---|---|---|---|---|\n")
    for h in st["headline_v8"]:
        md += (f"| {h['section_id']} | {h['unit']} | {h['reference_total']} | {h['engine_valued']} | {h['difference']} "
               f"| {h['difference_pct_of_reference'] or 'none'} | {_bce(h)} | {h['superseded_by'] or '-'} |\n")
    md += "\n## V8 sections: rows that moved (split or amended; every other row byte-equal to its earlier version)\n"
    for c in st["sections_v8"]:
        md += (f"\n### {c['section_id']} ({c['unit']}; restates {c['restates']}; totals {c['reference_total']} vs "
               f"{c['engine_valued']}, residual {c['closure_residual']})\n\n| Row | Class | Delta | Evidence | Tag |\n"
               "|---|---|---|---|---|\n")
        for r in c["rows"]:
            if r.get("tag", "").startswith("F-T594"):
                md += (f"| {r['name'][:150]} | {r['class']} | {r['delta']} | {EV[r['evidence_status']]} | "
                       f"{r['tag']} |\n")
    lint = st["sections_v8"][0]
    md += (f"\nLintels lm beside (never summed with nr): engine AT_MOST {lint['beside_lm']['engine_at_most']} (was "
           f"{lint['beside_lm']['engine_at_most_was']}), implied {lint['beside_lm']['implied']}; refused bases beside: "
           f"frame-clear {lint['refused_bases_beside']['frame_clear_lm']} lm, block-overall "
           f"{lint['refused_bases_beside']['block_overall_lm']} lm.\n")
    o = st["sections_v8"][1]["beside"]
    md += (f"\nYard (beside, never valued): wall foot NOT_IN_DRAWING {o['wall_foot_not_in_drawing_lm']} lm (+ up to "
           f"{o['under_unprinted_sills_hi_lm']} under sills), UNRESOLVED {' .. '.join(o['unresolved_bound_lm'])} lm "
           f"(porch / pool-court finishes HELD), no face {o['no_face_lm']} lm.\n")
    sb = st["sections_v8"][2]["beside"]
    md += (f"\nStair flights (beside): pitch {sb['flight_forms_lm']['pitch']} | zigzag {sb['flight_forms_lm']['zigzag']} "
           f"lm (two forms, never added); flight lower bound {sb['flight_lower_bounds_lm_v8']} lm (was "
           f"{sb['flight_lower_bounds_lm']}); E1 landing {sb['e1_landing_lm_not_in_drawing']} lm NOT_IN_DRAWING.\n")
    m = st["sections_v8"][3]["beside"]["door_steps_t592"]
    md += (f"\nDoor steps (T-592, beside): house {m['house_lm']} lm nr {m['house_nr']}, riser {m['house_riser_m2']} m2 "
           f"(nosing {m['house_nosing_attribute_lm']} lm attribute); gate {m['gate_lm']} lm / {m['gate_riser_m2']} m2 "
           f"{m['gate_status']}; ours - his {m['ours_minus_his_lm']['house']} (house) / "
           f"{m['ours_minus_his_lm']['with_gate']} lm (with gate), nr {m['nr_ours_with_gate']} vs {m['his_nr']}; no %.\n")
    md += "\nAgree pairs (R-T594-1 (b), net 0, out of the rows):\n\n"
    for p in st["agree_pairs_v8"]:
        md += f"- {p['section_id']}: {p['delta']} lm ({p['side']}): {p['name'][:120]}\n"
    t589 = st["beside_v8"][0]
    md += ("\n## T-589 structural closure classes (beside; classification only, no component promoted)\n\n"
           "| Section | Unit | n | VERIFIED | CLOSABLE | DESIGNER | OWNER GAP |\n|---|---|---|---|---|---|---|\n")
    for k, v in t589["sections"].items():
        n = v["n_by_class"]
        md += (f"| {k} | {v['unit']} | {v['n']} | {n['VERIFIED_ON_RECORD']} | {n['CLOSABLE_FROM_DRAWINGS']} | "
               f"{n['DESIGNER_ITEM']} | {n['OWNER_RULE_GAP']} |\n")
    md += f"\nRe-measure packs: {', '.join(t589['packs'])} (the Checker's T-180 input).\n"
    rb = st["beside_v8"][1]
    e = rb["expected_after_v8_rebar_rows"]
    md += (f"\n## T-595 dome / ring bar components (t, beside, valued 0)\n\nAt least {rb['at_least_t']} t (was "
           f"{rb['at_least_was_t']}); moved: " + "; ".join(f"{x['row_id']} {x['from_t']} -> {x['to_t']}" for x in
                                                          rb["moved_rows"]) +
           f". High OPEN. EXPECTED after the V8 manifest rows: G5 held at least {e['held_at_least_t']} t (was "
           f"{e['held_at_least_was_t']}), residual vs his TYPED_LUMP at most {e['residual_after_held_at_most_t']} t "
           f"(was {e['residual_was_at_most_t']}), no %. {rb['rounding_note']}.\n")
    fb = st["beside_v8"][2]
    md += (f"\n## T-595 footing F10 + F (m3, beside, valued 0)\n\nS02 range {' .. '.join(fb['component']['range_m3'])} "
           f"(was {' .. '.join(fb['component']['range_was_m3'])}); footing-line bounded part low "
           f"{fb['family_bounded_part_m3']['low']} (was {fb['family_bounded_part_m3']['low_was']}), high "
           f"{fb['family_bounded_part_m3']['high']}; his {fb['his']['m3']} m3 {fb['his']['class_was']} -> "
           f"{fb['his']['class']}; family total {fb['family_total']}.\n")
    md += "\n## Register rulings applied (Lead 2026-11-07 08:15)\n\n"
    for r in st["register_rulings_v8"]["rulings"]:
        md += f"- {r['entry']}: {r['ruling']} -> {r['statement_effect']}\n"
    md += "\n## Reclasses added in V8\n\n"
    for r in st["reclasses"]:
        if r["tag"].startswith("F-T594"):
            md += f"- {r['tag']} {r['section_id']}: {r['row'][:90]} {r['from']} -> {r['to']} {r['delta']}\n"
    md += "\nSuperseded (kept byte-equal in their versions): " + "; ".join(f"{k} -> {v}" for k, v in
                                                                         st["supersedes_v8"].items()) + ".\n"
    md += f"\nReports covered: {', '.join(st['reports_covered'])}; pending: {'; '.join(st['reports_pending'])}.\n"
    return md


def main(argv: list[str]) -> int:
    st = build()
    md = to_markdown(st)
    if "--write" in argv:
        OUT.mkdir(exist_ok=True)
        JSON_OUT.write_text(json.dumps(st, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        MD_OUT.write_text(md, encoding="utf-8")
    if "--check" in argv:
        old = json.loads(JSON_OUT.read_text(encoding="utf-8"))
        if old != st or MD_OUT.read_text(encoding="utf-8") != md:
            print("T-594 statement differs from out/")
            return 1
        print("T-594 statement reproduces")
    if not argv:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
