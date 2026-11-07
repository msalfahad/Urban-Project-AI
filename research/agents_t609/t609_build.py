"""T-609: the reconciled-quantities statement V10 = the T-603 statement V9 (rebuilt read only and checked equal to its
committed JSON and markdown; every V9 key carried byte-equal, lists extended as a prefix) + restated sections for the
merged T-602 (door steps 2.90 lm = G-01 2.50 ENGINE_OMISSION + 0.40 UNRESOLVED), T-606 (1F living room outline -8.66
lm by cause) and the T-180 pack verdicts P01 / P02 / P03 (beam evidence only), and beside blocks for T-597 (B1 plan
side), the packs and the pending fix F-T606-1 (R-T609-1). r2 (rework after REJECTED r1, rebuilt on the merged V9
pointer): the merged T-599 r2 joint split (beams + columns + nested / alternative column sets), T-607 (ST-01 7 nr /
8.4 lm ENGINE_RIGHT, one cause once, nosing beside), T-612 (GF open room outline +0.10 ENGINE_RIGHT + 17.013904
UNRESOLVED), T-605 (footing overlap verdict beside), T-610 (F-C-P03-2 restated UNDER) and T-611 (FR-T606-1 in manifest
V13, candidate unchanged). No private input; no quantity moves; nothing released.

  python3 -I research/agents_t609/t609_build.py --write   # write out/
  python3 -I research/agents_t609/t609_build.py --check   # rebuild and compare with out/ (exit 1 on a difference)
"""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t609_adapters as A  # noqa: E402
Z, A7, A8, A9 = A.Z, A.A7, A.A8, A.A9
sys.path.insert(0, str(A.T603))
import t603_build as B603  # noqa: E402  (T-603, read only)

D = Decimal
OUT = HERE / "out"
JSON_OUT = OUT / "RECONCILED_STATEMENT_T609.json"
MD_OUT = OUT / "RECONCILED_STATEMENT_T609.md"
NEW_REPORTS = ["T-597", "T-602", "T-604", "T-606", "T-180 P01", "T-180 P02 (2F; 1F partial)", "T-180 P03",
               "T-599 r2", "T-605", "T-607", "T-610", "T-611", "T-612"]
PENDING = ["T-600 (column per-storey residuals GF 0.620464 / 1F 1.208362 / 2F 0.42 m3 and GF B7 0.120452: TODO)",
           "F-T606-1 in manifest V13 (FR-T606-1, VERIFIED 4 / 4) but not wired in the candidate: beside, not applied",
           "FR-T610-1 .. 4 (beam-beam overlaps, F-C-P03-2 restated UNDER): not wired, beside in the packs",
           "T-180 P02 GF (not read) and P02 1F CB10 / CB11 / CB12 (Checker 22:57 read: F-C-P02-3 CB11 corner "
           "omission +0.018750 m3, no merged task yet)",
           "T-608 (lift landing doors by trade: READY, not merged at the r2 claim 2026-11-07T23:00Z)"]
EXTENDED = ("not_comparable", "reclasses", "reports_covered", "reports_pending", "rule", "provenance")
LESSONS_ADOPTED = [
    "T-602 (Checker ACCEPTED): census every boundary gap and every edge pair before calling a residual his scope; "
    "a figure equal to his residual is not an attribution",
    "T-606 (Checker ACCEPTED, amended): split a gross-vs-gross gap by room and by reading before naming its size; a "
    "column straddling a void edge is split at that edge",
    "T-597 (Checker ACCEPTED, R-T597-5): a pit volume is stated on the union of the drawn outlines, overlap named; the "
    "drawn outline, not its bounding box",
    "T-604 (Checker ACCEPTED): a fix row from an unmerged task is refused; a family figure moves only by its fix rows",
    "T-599 r2 (Checker PROPOSED row): a rule explains only the matched magnitude of a paired difference; the remainder "
    "is its own residual row, never promoted with it",
    "T-607 (Checker): one physical cause feeding several lines is entered once per line and never summed across"]
SECTION_IDS = {v: k for k, v in A.V10_BASE.items()}


def v9_statement() -> dict:
    st9 = B603.build()
    if st9 != json.loads(B603.JSON_OUT.read_text(encoding="utf-8")) or \
            B603.to_markdown(st9) != B603.MD_OUT.read_text(encoding="utf-8"):
        raise Z.StatementError("T-603 statement V9 does not reproduce: rebuild it before T-609")
    return st9


def check_v9_unchanged(st: dict, st9: dict) -> None:
    """Every V9 key is byte-equal (sorted JSON); the extended lists keep V9 as their prefix."""
    for k in st9:
        if k in EXTENDED:
            continue
        if json.dumps(st[k], sort_keys=True) != json.dumps(st9[k], sort_keys=True):
            raise Z.StatementError(f"V9 key {k} changed in V10")
    for k in ("not_comparable", "reclasses", "reports_covered"):
        if st[k][:len(st9[k])] != st9[k]:
            raise Z.StatementError(f"V9 {k} not carried as its prefix")
    if not st["rule"].startswith(st9["rule"]):
        raise Z.StatementError("V9 rule text not carried as its prefix")
    if {k: v for k, v in st["provenance"].items() if k in st9["provenance"]} != st9["provenance"]:
        raise Z.StatementError("V9 provenance changed")


def expected(sid: str, r: dict) -> str:
    return A.expected_v10(sid, r, B603.expected_v9)


def headline(secs: list[dict], superseded: dict) -> list[dict]:
    out = []
    for c in secs:
        sid = c["section_id"]
        bce = A7.by_class_evidence(c["rows"], c["unit"], lambda r, sid=sid: expected(sid, r))
        out.append({"section_id": sid, "unit": c["unit"], "reference_total": c["reference_total"],
                    "engine_valued": c["engine_valued"], "difference": c["difference"],
                    "difference_pct_of_reference": c["difference_pct_of_reference"],
                    "by_class_evidence": bce, "superseded_by": superseded.get(sid)})
    return out


def class_shift(moves: list[dict]) -> dict:
    out: dict = {}
    for m in moves:
        u = m["unit"]
        k = f"{m['from']} -> {m['to']}"
        x = out.setdefault(u, {}).setdefault(k, {"n": 0, "signed": D(0), "gross": D(0)})
        x["n"] += 1
        x["signed"] += D(m["delta"])
        x["gross"] += abs(D(m["delta"]))
    return {u: {k: {"n": v["n"], "signed": Z.s(v["signed"]), "gross": Z.s(v["gross"])} for k, v in sorted(m.items())}
            for u, m in sorted(out.items())}


def build_from(st9: dict, src: dict) -> dict:
    st = copy.deepcopy(st9)
    marble, mv_m = A.t602_marble_lm(st9, src["T-602"], src["T-604"])
    room6, mv_r = A.t606_skirting_room(st9, src["T-606"])
    room, mv_r2 = A.t612_room(room6, src["T-612"])
    beams_p, ev_moves, packs = A.t180_beams(st9)
    joint, mv_j, mv_alt, joint_rec = A.t599_joint(st9, src["T-599"], beams_p)
    steps, mv_s, nosing = A.t607_steps(st9, src["T-607"])
    secs = [marble, room] + joint + steps
    old_all = A.all_sections(st9)
    for c in secs:
        if c["section_id"] in old_all:
            raise Z.StatementError(f"{c['section_id']}: section id already in V9")
        if SECTION_IDS[c["restates"]] != c["section_id"]:
            raise Z.StatementError(f"{c['section_id']}: restates {c['restates']}, not its section of record")
        A9.check_section_totals(old_all[c["restates"]], c)
        A7.audit_evidence(c, lambda r, sid=c["section_id"]: expected(sid, r))
    moves = [dict(m, unit=marble["unit"]) for m in mv_m] + [dict(m, unit=room["unit"]) for m in mv_r + mv_r2] + \
        mv_j + mv_s
    if any(m["section_id"] in A.NESTED_OR_ALT_V10 for m in moves):
        raise Z.StatementError("a nested / alternative move in the class shift of record (R-T609-1 (f))")
    sup10 = {c["restates"]: c["section_id"] for c in secs}
    sup = dict(st9["supersedes_v7"], **st9["supersedes_v8"], **st9["supersedes_v9"], **sup10)
    st["sections_v10"] = secs
    st["supersedes_v10"] = sup10
    st["headline_v10"] = headline(st9["sections_v6"] + st9["sections_v7"] + st9["sections_v8"] + st9["sections_v9"] +
                                  secs, sup)
    st["class_shift_v10"] = class_shift(moves)
    st["class_shift_v10_nested_alternative"] = class_shift(mv_alt)
    st["evidence_shift_v10"] = ev_moves
    st["joint_rule_v10"] = joint_rec
    st["beside_v10"] = [A.t597_beside(st9, src["T-597"]), A.packs_beside(packs, ev_moves, src["T-589"], src["T-610"]),
                        A.t606_pending(src["T-606"], src["T-604"], src["T-611"]), A.t605_beside(st9, src["T-605"]),
                        nosing]
    st["reclasses"] = st9["reclasses"] + [{k: v for k, v in m.items() if k != "unit"} for m in moves + mv_alt]
    st["reports_covered"] = st9["reports_covered"] + NEW_REPORTS
    st["reports_pending"] = PENDING
    st["rule"] = st9["rule"] + " + R-T609-1"
    st["schema_v10"] = "URBAN_T609_RECONCILED_STATEMENT_V10"
    st["lessons_adopted_applied_v10"] = LESSONS_ADOPTED
    st["provenance"]["inputs_v10"] = {str(p.relative_to(Z.ROOT)): Z.sha(p) for p in
                                      [A.T597_JSON, A.T602_JSON, A.T604_JSON, A.T606_JSON, A.T589_JSON,
                                       A.T599_JSON, A.T605_JSON, A.T607_JSON, A.T610_JSON, A.T611_JSON, A.T612_JSON,
                                       B603.JSON_OUT, B603.MD_OUT, HERE / "t609_adapters.py", HERE / "t609_build.py"]}
    st["released_quantities_changed"] = 0
    Z.refuse_manifest_as_line(st)
    A9.refuse_form_sum(st, st9["stair_skirting_element_v9"])
    A.refuse_cause_summed(st)
    out = json.loads(json.dumps(st, sort_keys=True))
    check_v9_unchanged(out, st9)
    return out


def sources() -> dict:
    return {"T-597": A.load(A.T597_JSON), "T-602": A.load(A.T602_JSON), "T-604": A.load(A.T604_JSON),
            "T-606": A.load(A.T606_JSON), "T-589": A.load(A.T589_JSON), "T-599": A.load(A.T599_JSON),
            "T-605": A.load(A.T605_JSON), "T-607": A.load(A.T607_JSON), "T-610": A.load(A.T610_JSON),
            "T-611": A.load(A.T611_JSON), "T-612": A.load(A.T612_JSON)}


def build() -> dict:
    return build_from(v9_statement(), sources())


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
    md = ("# T-609 reconciled-quantities statement V10 (generated; reference - engine, + = in the reference only)\n\n"
          "V10 = statement V9 (T-603, rebuilt and equal to its committed output; every V9 key carried byte-equal) + the "
          "sections and blocks below. Development villa; not an accuracy claim; nothing released (ARCH_TAKEOFF_V3.0.58 "
          "NOT RELEASED; V2.9 + route G unchanged).\n\n"
          "Evidence (R-T587-1 (a)): V = Checker VERIFIED, PV = partially verified, WP = worker-proposed, each from the "
          "row's own verdict; a pack moves evidence only (R-T609-1 (b)).\n\n")
    md += ("## Headline by class and evidence (V6 .. V10 sections)\n\n| Section | Unit | Reference | Engine valued | "
           "Difference | % of ref. | By class [evidence] | Superseded by |\n|---|---|---|---|---|---|---|---|\n")
    for h in st["headline_v10"]:
        md += (f"| {h['section_id']} | {h['unit']} | {h['reference_total']} | {h['engine_valued']} | {h['difference']} "
               f"| {h['difference_pct_of_reference'] or 'none'} | {_bce(h)} | {h['superseded_by'] or '-'} |\n")
    md += "\n## Class moves in V10, per unit\n\n| Unit | Move | n | Signed | Gross |\n|---|---|---|---|---|\n"
    for u, m in st["class_shift_v10"].items():
        for k, v in m.items():
            md += f"| {u} | {k} | {v['n']} | {v['signed']} | {v['gross']} |\n"
    md += "\n## Rows restated in V10 (split parts; reference - engine)\n\n| Section | Class | Delta | Evidence | Row |\n|---|---|---|---|---|\n"
    for c in st["sections_v10"]:
        for r in c["rows"]:
            if r.get("tag") in (A.TAG_STEP, A.TAG_ROOM, A.TAG_ROOM2, A.TAG_STAIR) or r.get("joint_sub"):
                md += f"| {c['section_id']} | {r['class']} | {r['delta']} {c['unit']} | {EV[r['evidence_status']]} | {r['name'][:150]} |\n"
    md += "\n## Nested / alternative column sets: class moves (apart, never added)\n\n| Unit | Move | n | Signed | Gross |\n|---|---|---|---|---|\n"
    for u, m in st["class_shift_v10_nested_alternative"].items():
        for k, v in m.items():
            md += f"| {u} | {k} | {v['n']} | {v['signed']} | {v['gross']} |\n"
    jr = st["joint_rule_v10"]
    md += (f"\n## Joint rule (T-599 r2)\n\n{jr['rule_id']} {jr['version']} {jr['status']}; merge {jr['merge']}. Residual of "
           f"record {jr['residual_of_record_m3']} m3 -> {jr['residual_to']}; untraced apart {jr['untraced_apart_m3']}. "
           f"Rows kept whole (residual only): {len(jr['rows_kept_whole_residual'])}; superseded readings audited beside: "
           f"{len(jr['superseded_audited_beside'])}. {jr['v9_pointer']}.\n")
    md += "\n## Evidence moves (T-180 packs; class and delta unchanged)\n\n"
    for m in st["evidence_shift_v10"]:
        md += f"- {m['row']} ({m['class']} {m['delta']} m3): {EV[m['from']]} -> {EV[m['to']]} by {m['pack']}.\n"
    marble = [c for c in st["sections_v10"] if c["section_id"] == "T-577/marble-lm@V10"][0]
    ds = marble["beside"]["door_steps_t602"]
    md += (f"\n## Door steps (T-602; beside the marble lm section, no %)\n\nOurs {ds['ours_lm']} lm / {ds['ours_nr']} nr "
           f"/ riser {ds['ours_riser_m2']} m2 (was {ds['was']['ours_lm']} lm / {ds['was']['nr']} nr) vs his "
           f"{ds['his_lm']} lm / {ds['his_nr']} nr: his - ours {ds['his_minus_ours_lm']} lm UNRESOLVED; count: "
           f"{ds['count']}. {ds['omitted_step']['opening']} {ds['omitted_step']['lm']} lm / {ds['omitted_step']['riser_m2']} "
           f"m2, {ds['omitted_step']['status']}, {ds['omitted_step']['fix_row']} ({ds['omitted_step']['manifest']}).\n")
    b597, bpk, b606, b605, bnos = st["beside_v10"]
    z = b597["pits_zone_m2"]
    md += (f"\n## B1 plan side (T-597; beside the NOT_COMPARABLE earthworks, his NO_ROW, no %)\n\nPits union "
           f"{z['union']} m2 (in plot {z['in_plot']}, beyond {z['beyond_plot']}), pool share {z['pool_share_given_up']}, "
           f"zone owned {z['own_in_plot']} m2; drawn sum {z['sum_drawn_F_C_T597_1']} / overlap "
           f"{z['overlap_drawn_F_C_T597_1']} m2 (F-C-T597-1; json {z['sum_json']} / {z['overlap_json']}); pool envelope "
           f"{b597['pool_envelope_m2']['in_plot']} m2 in plot. Engine plan {b597['engine_difference']['plan_m2']} m2 / "
           f"{b597['engine_difference']['m3_at_S01']} m3 at S01: {b597['engine_difference']['class']}.\n\n")
    for k, v in b597["statuses"].items():
        md += f"- {k}: {v}\n"
    md += "\n## T-180 packs P01 .. P03 (beside)\n\n| Pack | Row | State | Evidence moved |\n|---|---|---|---|\n"
    for p in bpk["packs"]:
        for n, r in p["rows"].items():
            md += f"| {p['pack']} | {n} | {r['state']} | {'yes' if r['evidence_moved'] else 'no'} |\n"
    md += "\n" + "".join(f"- {f}\n" for p in bpk["packs"] for f in p["findings"])
    for p in bpk["packs"]:
        if "t610_restatement" in p:
            r6 = p["t610_restatement"]
            md += (f"- {r6['finding']} restated by {r6['restated_by']}: billed {r6['billed']}; zone {r6['zone_m2']} m2; "
                   f"fix rows (m3) " + ", ".join(f"{k} {v}" for k, v in r6["fix_rows_m3"].items()) + "; not applied.\n")
    md += (f"\n## Pending fix F-T606-1 (beside, not applied)\n\nLine {b606['line'][:12]} FIN.SKIRTING: worker "
           f"{b606['worker_lm']} lm, Checker {b606['checker_lm']} lm ({b606['class']}); candidate V3.0.58 "
           f"{b606['candidate_v3_0_58']['before']} -> {b606['candidate_v3_0_58']['after_if_wired']} lm; after manifest "
           f"V12 {b606['after_manifest_v12']['before']} -> {b606['after_manifest_v12']['after_if_wired']} lm. "
           f"{b606['fix_row']}." + (f" Manifest V13: {b606['manifest_v13']['before']} -> {b606['manifest_v13']['after']} lm."
                                     if "manifest_v13" in b606 else "") + "\n")
    cm = b605["concrete_m3"]
    md += (f"\n## Footing overlap (T-605; beside, row unchanged)\n\nRow '{b605['row'][:60]}' {b605['row_delta_m3']} m3 "
           f"{b605['row_class']}: pair concrete engine {cm['engine']} = own {cm['own']} vs his {cm['his']} (notch "
           f"{cm['notch']}); blinding union {b605['blinding_m2']['union']} m2; side forms "
           f"{' .. '.join(b605['side_forms_m2']['bound'])} m2 {b605['side_forms_m2']['status']}. {b605['evidence']}.\n")
    ul = bnos["units"]["lm"]
    md += (f"\n## Nosing (T-598 + T-607; beside, never added)\n\nHis {ul['his']} vs ours {ul['ours_valued']} lm, gap "
           f"{ul['gap_his_minus_ours']}: " + ", ".join(f"{k} {v}" for k, v in ul["by_class"].items()) +
           f" (was UNRESOLVED {ul['was_by_class'].get('UNRESOLVED')}); nr gap {bnos['units']['nr']['gap_his_minus_ours']} "
           f"{bnos['units']['nr']['gap_class']}. {bnos['once']}.\n")
    md += ("\nSuperseded (kept byte-equal in their versions): " +
           "; ".join(f"{k} -> {v}" for k, v in st["supersedes_v10"].items()) + ".\n")
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
            print("T-609 statement differs from out/")
            return 1
        print("T-609 statement reproduces")
    if not argv:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
