"""T-603: the reconciled-quantities statement V9 = the T-594 statement V8 (rebuilt read only and checked equal to its
committed JSON and markdown; every V8 key carried byte-equal, lists extended as a prefix) + restated sections for the
merged provenance audits T-590 (structural: column / beam joint and rebar RULE_DIFFERENCE -> UNRESOLVED, the joint
pointer T-599 not merged) and T-591 (finishes: 40 SOURCED / 76 SOURCED_RECITE / 1 NONE; the A-1F-01 arch jambs
ENGINE_WRONG 0.30 lm), the T-598 nosing beside restatement, and the F-C-T593-1 stair-skirting one-element guard. No
private input; no quantity moves; nothing released.

  python3 -I research/agents_t603/t603_build.py --write   # write out/
  python3 -I research/agents_t603/t603_build.py --check   # rebuild and compare with out/ (exit 1 on a difference)
"""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t603_adapters as A  # noqa: E402
Z, A7, A8 = A.Z, A.A7, A.A8
sys.path.insert(0, str(A.T594))
import t594_build as B594  # noqa: E402  (T-594, read only)

D = Decimal
OUT = HERE / "out"
JSON_OUT = OUT / "RECONCILED_STATEMENT_T603.json"
MD_OUT = OUT / "RECONCILED_STATEMENT_T603.md"
NEW_REPORTS = ["T-590", "T-591", "T-598"]
PENDING = ["T-599 (column / beam joint rule version: REJECTED 2026-11-07 13:58; the 37 joint rows stay UNRESOLVED "
           "with its pointer)", "T-601 (doorless jamb census, MERGED after this claim's scope: FR-T601-n rows in "
           "manifest V12, T-604; the A-1F-01 class is restated here from T-591)",
           "T-602 (external door steps, his UNRESOLVED 2.90 lm: MERGED 15:02, not in this scope)"]
EXTENDED = B594.EXTENDED
LESSONS_ADOPTED = [
    "T-590 (Checker ACCEPTED): a convention choice is sourced only by an adopted rule version; a requirement-only owner "
    "answer is a requirement; opposite records on one junction = CONVENTION_RECORD_CONFLICT, row UNRESOLVED; a "
    "typed-lump reference has no readable convention",
    "T-591 (Checker ACCEPTED): every RULE_DIFFERENCE names the governing rule id read in its text, for that trade and "
    "opening class (door vs doorless); a row with none is UNRESOLVED",
    "T-598 (Checker ACCEPTED): a held edge is closed by existence and length separately; a curtail front is a nosing "
    "on its developed arc",
    "F-C-T593-1 (Checker): two forms of one element enter a statement as one element, range min..max, never summed"]


def v8_statement() -> dict:
    st8 = B594.build()
    if st8 != json.loads(B594.JSON_OUT.read_text(encoding="utf-8")) or \
            B594.to_markdown(st8) != B594.MD_OUT.read_text(encoding="utf-8"):
        raise Z.StatementError("T-594 statement V8 does not reproduce: rebuild it before T-603")
    return st8


def check_v8_unchanged(st: dict, st8: dict) -> None:
    """Every V8 key is byte-equal (sorted JSON); the extended lists keep V8 as their prefix."""
    for k in st8:
        if k in EXTENDED:
            continue
        if json.dumps(st[k], sort_keys=True) != json.dumps(st8[k], sort_keys=True):
            raise Z.StatementError(f"V8 key {k} changed in V9")
    for k in ("not_comparable", "reclasses", "reports_covered"):
        if st[k][:len(st8[k])] != st8[k]:
            raise Z.StatementError(f"V8 {k} not carried as its prefix")
    if not st["rule"].startswith(st8["rule"]):
        raise Z.StatementError("V8 rule text not carried as its prefix")
    if {k: v for k, v in st["provenance"].items() if k in st8["provenance"]} != st8["provenance"]:
        raise Z.StatementError("V8 provenance changed")


def expected_v9(sid: str, r: dict) -> str:
    """Verdict map for every headline row, independent of the stamps the adapters wrote."""
    if sid.endswith("@V9"):
        base = sid[:-3]
        if base == "T-545/beams":
            base = "T-545/beams@V7"
        if base == "T-574/skirting-room":
            return A.PV if r.get("tag") == A.TAG_JAMB else A7.ev_v6("T-574/", r)
        return A.evid_structural(base, r)
    return B594.expected_v8(sid, r)


def headline(secs: list[dict], superseded: dict) -> list[dict]:
    out = []
    for c in secs:
        sid = c["section_id"]
        bce = A7.by_class_evidence(c["rows"], c["unit"], lambda r, sid=sid: expected_v9(sid, r))
        out.append({"section_id": sid, "unit": c["unit"], "reference_total": c["reference_total"],
                    "engine_valued": c["engine_valued"], "difference": c["difference"],
                    "difference_pct_of_reference": c["difference_pct_of_reference"],
                    "by_class_evidence": bce, "superseded_by": superseded.get(sid)})
    return out


NESTED = {"T-576/columns-GF@V9": "T-551/columns@V9", "T-576/columns-1F@V9": "T-551/columns@V9"}
ALTERNATIVE = ("-reading-10E0-C7@V9",)


def class_shift(moves: list[dict], headline_ids: set) -> dict:
    """Per unit, the class moves of V9 (from -> to, signed), for the sections of record (not nested, not an
    alternative reading) and for every audited row."""
    out: dict = {}
    for m in moves:
        for scope in ("of_record", "all_rows"):
            if scope == "of_record" and m["section_id"] not in headline_ids:
                continue
            u = m["unit"]
            k = f"{m['from']} -> {m['to']}"
            x = out.setdefault(scope, {}).setdefault(u, {}).setdefault(k, {"n": 0, "signed": D(0), "gross": D(0)})
            x["n"] += 1
            x["signed"] += D(m["delta"])
            x["gross"] += abs(D(m["delta"]))
    return {sc: {u: {k: {"n": v["n"], "signed": Z.s(v["signed"]), "gross": Z.s(v["gross"])} for k, v in sorted(m.items())}
                 for u, m in sorted(us.items())} for sc, us in sorted(out.items())}


def build_from(st8: dict, src: dict, rules_index_text: str) -> dict:
    st = copy.deepcopy(st8)
    s590 = A.t590_sections(st8, src["T-590"], rules_index_text)
    prov = A.t591_provenance(st8, src["T-591"])
    f591 = A.check_t591_findings(prov)
    jamb, mvj = A.t591_jamb_section(st8, prov["none"])
    secs = s590["sections"] + [jamb]
    moves = s590["moves"] + mvj
    old_ids = set(A.all_sections(st8))
    unit_of = {c["section_id"]: c["unit"] for c in secs}
    for m in moves:
        m["unit"] = unit_of[m["section_id"]]
    sup9 = {}
    for c in secs:
        if c["section_id"] in old_ids:
            raise Z.StatementError(f"{c['section_id']}: section id already in V8")
        old = A.all_sections(st8)[c["restates"]]
        A.check_section_totals(old, c)
        A7.audit_evidence(c, lambda r, sid=c["section_id"]: expected_v9(sid, r))
        sup9[c["restates"]] = c["section_id"]
    nosing = A.t598_nosing(st8, src["T-598"])
    element = A.skirting_element(src["T-593"]["rows"])
    sup = dict(st8["supersedes_v7"], **st8["supersedes_v8"], **sup9)
    sup9["beside_v7 T-578/nosing-xref"] = "beside_v9 T-598/nosing@V9"
    of_record_ids = {c["section_id"] for c in secs if c["section_id"] not in NESTED and
                     not c["section_id"].endswith(ALTERNATIVE)}
    joint = s590["groups"]
    jrec = [g for g in joint["JOINT"] if g["section_id"] in of_record_ids]
    st["sections_v9"] = secs
    st["supersedes_v9"] = sup9
    st["headline_v9"] = headline(st8["sections_v6"] + st8["sections_v7"] + st8["sections_v8"] + secs, sup)
    st["class_shift_v9"] = class_shift(moves, of_record_ids)
    st["structural_provenance_v9"] = {
        "report": "T-590", "rule": "R-T590-1", "verification": A.V590, "joint_rule_pointer": dict(
            A.JOINT_RULE, in_rules_index=f"| {A.JOINT_RULE['rule_id']} |" in rules_index_text),
        "joint_rows": {"of_record": {"n": len(jrec), "signed_m3": Z.s(sum((D(g["delta"]) for g in jrec), D(0))),
                                     "gross_m3": Z.s(sum((abs(D(g["delta"])) for g in jrec), D(0)))},
                       "all_audited_in_record_sections": len(joint["JOINT"]),
                       "superseded_audited_beside": len(s590["superseded_audited"])},
        "counted_apart": joint["APART"], "rebar_rows": joint["REBAR"],
        "pairs_per_storey": A.joint_pairs(st8),
        "nested_and_alternative": {"nested": NESTED, "alternative_readings": sorted(
            c["section_id"] for c in secs if c["section_id"].endswith(ALTERNATIVE)),
            "note": "nested measured sets and conflict readings are restated with the same outcome and never added to "
                    "the sections of record"},
        "b1_earthworks": "0 RULE_DIFFERENCE rows (T-565 NOT_COMPARABLE; T-572 bounds only): nothing reclassed"}
    st["finishes_provenance_v9"] = {
        "report": "T-591", "rule": "R-T591-1", "verification": A.V591, "per_unit_live": prov["per_unit_live"],
        "counts_live": {"SOURCED": sum(v.get("SOURCED", {}).get("n", 0) for v in prov["per_unit_live"].values()),
                        "SOURCED_RECITE": sum(v.get("SOURCED_RECITE", {}).get("n", 0)
                                              for v in prov["per_unit_live"].values()),
                        "NONE": sum(v.get("NONE", {}).get("n", 0) for v in prov["per_unit_live"].values())},
        "citations_corrected": f591, "annotations": prov["applied"], "overtaken_by_v8": prov["overtaken"],
        "none_row": prov["none"],
        "class_questions_not_reclassed": "F-T591-4: T-534 MS1-LD 0.0625 m2 (size), T-577 DRY strips vs his NO_ROW, "
                                         "boundary wall +74.4 m2 and pool soffit +12.834 m2 (placements): named, "
                                         "class kept"}
    st["beside_v9"] = [nosing]
    st["stair_skirting_element_v9"] = element
    st["reclasses"] = st8["reclasses"] + [{k: v for k, v in m.items() if k != "unit"} for m in moves]
    st["reports_covered"] = st8["reports_covered"] + NEW_REPORTS
    st["reports_pending"] = PENDING
    st["rule"] = st8["rule"] + " + R-T603-1"
    st["schema_v9"] = "URBAN_T603_RECONCILED_STATEMENT_V9"
    st["lessons_adopted_applied_v9"] = LESSONS_ADOPTED
    st["provenance"]["inputs_v9"] = {str(p.relative_to(Z.ROOT)): Z.sha(p) for p in
                                     [A.T590_JSON, A.T591_JSON, A.T598_JSON, A.T593_JSON,
                                      B594.JSON_OUT, B594.MD_OUT, HERE / "t603_adapters.py", HERE / "t603_build.py"]}
    st["released_quantities_changed"] = 0
    Z.refuse_manifest_as_line(st)
    A.refuse_form_sum(st, element)
    out = json.loads(json.dumps(st, sort_keys=True))
    check_v8_unchanged(out, st8)
    return out


def sources() -> dict:
    return {"T-590": A.load(A.T590_JSON), "T-591": A.load(A.T591_JSON), "T-598": A.load(A.T598_JSON),
            "T-593": A.load(A.T593_JSON)}


def build() -> dict:
    return build_from(v8_statement(), sources(), A.RULES_INDEX.read_text(encoding="utf-8"))


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
    md = ("# T-603 reconciled-quantities statement V9 (generated; reference - engine, + = in the reference only)\n\n"
          "V9 = statement V8 (T-594, rebuilt and equal to its committed output; every V8 key carried byte-equal) + the "
          "sections and blocks below. Development villa; not an accuracy claim; nothing released.\n\n"
          "Evidence (R-T587-1 (a)): V = Checker VERIFIED, PV = partially verified, WP = worker-proposed, each from the "
          "row's own verdict; a provenance reclass keeps it (R-T603-1 (e)).\n\n")
    md += ("## Headline by class and evidence (V6 + V7 + V8 + V9 sections)\n\n| Section | Unit | Reference | Engine "
           "valued | Difference | % of ref. | By class [evidence] | Superseded by |\n|---|---|---|---|---|---|---|---|\n")
    for h in st["headline_v9"]:
        md += (f"| {h['section_id']} | {h['unit']} | {h['reference_total']} | {h['engine_valued']} | {h['difference']} "
               f"| {h['difference_pct_of_reference'] or 'none'} | {_bce(h)} | {h['superseded_by'] or '-'} |\n")
    md += "\n## Class moves in V9, per unit (sections of record; all audited rows)\n\n| Scope | Unit | Move | n | Signed | Gross |\n|---|---|---|---|---|---|\n"
    for sc, us in st["class_shift_v9"].items():
        for u, m in us.items():
            for k, v in m.items():
                md += f"| {sc} | {u} | {k} | {v['n']} | {v['signed']} | {v['gross']} |\n"
    sp = st["structural_provenance_v9"]
    j = sp["joint_rows"]["of_record"]
    md += (f"\n## Structural provenance (T-590)\n\nColumn / beam joint: {j['n']} rows of record, {j['signed_m3']} m3 signed "
           f"({j['gross_m3']} gross): RULE_DIFFERENCE -> UNRESOLVED, CONVENTION_RECORD_CONFLICT; pointer "
           f"{sp['joint_rule_pointer']['task']} {sp['joint_rule_pointer']['status']} ({sp['joint_rule_pointer']['rule_id']} "
           f"not in RULES_INDEX). Counted apart (F-C-T590-2): " +
           "; ".join(f"{g['row']} {g['delta']} m3" for g in sp["counted_apart"]) + ". Rebar: " +
           f"{len(sp['rebar_rows'])} groups {Z.s(sum((D(g['delta']) for g in sp['rebar_rows']), D(0)))} t "
           "HIS_SIDE_UNREADABLE -> UNRESOLVED (no %).\n\nPairs per storey (reference - engine; 2F on the V7 reading): " +
           "; ".join(f"{f} beam {v['beam_THROUGH_SUPPORT_m3']} + column {v['column_JOINT_HEAD_m3']} = {v['net_m3']}"
                     for f, v in sp["pairs_per_storey"]["by_storey"].items()) + " m3. " +
           sp["pairs_per_storey"]["note"] + ".\n")
    fp = st["finishes_provenance_v9"]
    c = fp["counts_live"]
    md += (f"\n## Finishes provenance (T-591)\n\nLive rows: SOURCED {c['SOURCED']} / SOURCED_RECITE {c['SOURCED_RECITE']} "
           f"/ NONE {c['NONE']}; annotated on the row of record {len(fp['annotations'])}, overtaken by V8 "
           f"{len(fp['overtaken_by_v8'])} (" + "; ".join(f"{e['row'][:60]}: {e['overtaken']}"
                                                         for e in fp["overtaken_by_v8"]) + ").\n\n")
    for k, v in fp["citations_corrected"].items():
        md += f"- {k}: {v['rows']} rows re-cite {v['governing']} (refused {v['refused']}).\n"
    md += ("- NONE row: T-574/skirting-room A-1F-01 arch jambs 0.30 lm RULE_DIFFERENCE -> ENGINE_WRONG (PV; owner "
           "method includes doorless jambs).\n")
    n = st["beside_v9"][0]
    lm, nr = n["units"]["lm"], n["units"]["nr"]
    md += (f"\n## Stair nosing (T-598, beside, valued 0; supersedes the T-578 cross-reference)\n\nHis {lm['his']} lm vs "
           f"ours valued {lm['ours_valued']} lm: his - ours {lm['gap_his_minus_ours']} (was {lm['gap_was']}); by class "
           + ", ".join(f"{k} {v}" for k, v in lm["by_class"].items()) + f"; residual {lm['residual']}; ours HELD "
           f"{' .. '.join(lm['held_bound_lm'])} lm. nr: his {nr['his']} vs ours {nr['ours_valued']} valued + "
           f"{nr['ours_held']} HELD, gap {nr['gap_his_minus_ours']} {nr['gap_class']}. {n['status_correction']}. "
           "No %.\n")
    e = st["stair_skirting_element_v9"]
    md += (f"\n## Stair skirting: one element, two forms (F-C-T593-1 guard)\n\n{e['two_form_pieces']} two-form pieces: "
           f"range {' .. '.join(e['range_lm'])} lm (" + "; ".join(f"{k} {' .. '.join(v['range_lm'])}"
                                                               for k, v in e["by_stair"].items()) +
           f"); payable form {e['payable_form']}; the sum over forms {e['sum_over_forms_refused_lm']} lm is refused "
           f"anywhere in the statement; {len(e['held_one_form_pieces'])} one-form held pieces stay on their own "
           "bounds.\n")
    md += "\n## Reclasses added in V9\n\n"
    for r in st["reclasses"]:
        if r["tag"].startswith("F-T603"):
            md += f"- {r['tag']} {r['section_id']}: {r['row'][:80]} {r['from']} -> {r['to']} {r['delta']}\n"
    md += "\nSuperseded (kept byte-equal in their versions): " + "; ".join(f"{k} -> {v}" for k, v in
                                                                         st["supersedes_v9"].items()) + ".\n"
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
            print("T-603 statement differs from out/")
            return 1
        print("T-603 statement reproduces")
    if not argv:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
