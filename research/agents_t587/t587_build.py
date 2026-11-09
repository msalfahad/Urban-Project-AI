"""T-587: the reconciled-quantities statement V7 = the T-586 statement V6 (rebuilt read only and checked equal to its
committed JSON and markdown; every V6 key carried byte-equal, lists extended as a prefix) + T-576 (B10 GF / 1F
columns m3 by signed cause, both 10E0 readings; V4 GF B7 beam row restated), T-578 (rails lm; nosing lm / nr as a
cross-reference), T-583 (bar components t, beside) and T-584 (stair steps lm / nr; E1 and door steps restated in
T-577/marble-lm@V7), the F-C-T586-1 headline by evidence and the F-T586-1 E1 reclass. No private input; no quantity
moves; nothing released.

  python3 -I research/agents_t587/t587_build.py --write   # write out/
  python3 -I research/agents_t587/t587_build.py --check   # rebuild and compare with out/ (exit 1 on a difference)
"""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t587_adapters as A  # noqa: E402
Z = A.Z
sys.path.insert(0, str(A.T586))
import t586_build as B586  # noqa: E402  (T-586, read only)

D = Decimal
OUT = HERE / "out"
JSON_OUT = OUT / "RECONCILED_STATEMENT_T587.json"
MD_OUT = OUT / "RECONCILED_STATEMENT_T587.md"
NEW_REPORTS = ["T-576", "T-578", "T-583", "T-584"]
PENDING = ["T-581 (pending r2: its rows enter V8)"]
EXTENDED = ("not_comparable", "reclasses", "reports_covered", "reports_pending", "rule", "provenance")
SUPERSEDES = {
    "T-572/measured-columns_GF": "T-576/columns-GF",
    "T-572/measured-columns_1F": "T-576/columns-1F",
    "T-545/beams": "T-545/beams@V7",
    "T-577/marble-lm": "T-577/marble-lm@V7",
    "beside_v6 T-575/dome-lift-rebar": "beside_v7 T-583/dome-lift-components",
}
LESSONS_ADOPTED = [
    "T-576 (Checker ACCEPTED): a head term is read at the printed depth of the named framing member, with the "
    "controlling depth open: the JOINT_HEAD / GLOBAL_DEPTH split is bounded while the total closes",
    "T-578 (Checker ACCEPTED): rails along the pitch, nosing-to-nosing; a lone typed constant is decomposed only as a "
    "labelled hypothesis",
    "T-583 (Checker ACCEPTED): n bars leave n + 1 gaps: the strict low is ceil(L / s) - 1; a high that excludes laps "
    "is not a high",
    "T-584 (Checker ACCEPTED): one drawn edge pair on the wall face is one element (threshold nosing + riser)"]


def v6_statement() -> dict:
    st6 = B586.build()
    if st6 != json.loads(B586.JSON_OUT.read_text(encoding="utf-8")) or \
            B586.to_markdown(st6) != B586.MD_OUT.read_text(encoding="utf-8"):
        raise Z.StatementError("T-586 statement V6 does not reproduce: rebuild it before T-587")
    return st6


def check_v6_unchanged(st: dict, st6: dict) -> None:
    """Every V6 key is byte-equal (sorted JSON); the extended lists keep V6 as their prefix."""
    for k in st6:
        if k in EXTENDED:
            continue
        if json.dumps(st[k], sort_keys=True) != json.dumps(st6[k], sort_keys=True):
            raise Z.StatementError(f"V6 key {k} changed in V7")
    for k in ("not_comparable", "reclasses", "reports_covered"):
        if st[k][:len(st6[k])] != st6[k]:
            raise Z.StatementError(f"V6 {k} not carried as its prefix")
    if not st["rule"].startswith(st6["rule"]):
        raise Z.StatementError("V6 rule text not carried as its prefix")
    if {k: v for k, v in st["provenance"].items() if k in st6["provenance"]} != st6["provenance"]:
        raise Z.StatementError("V6 provenance changed")


def expected_evidence(sid: str, r: dict) -> str:
    """The verdict map (R-T587-1 (a)): what every row's evidence status must be."""
    if sid.startswith("T-576/"):
        return A.ev_t576(r["term"], r["name"].split(" ", 1)[0], r["source_class"])
    if sid == "T-578/rails":
        return A.ev_t578_rail(r["name"], r["source_verdict"])
    if sid.startswith("T-584/"):
        return A.ev_t584(r["name"].split(":", 1)[0], r["source_verdict"], r["name"])
    if sid == "T-577/marble-lm@V7":
        if r["name"].startswith("E1_STEPS"):
            return A.CV
        return A.PV if r["name"].startswith("EXT:") and r["class"] == "UNRESOLVED" else A.ev_v6(sid, r)
    if sid == "T-545/beams@V7":
        return A.V4_EVIDENCE[r["verification"]]
    if sid.startswith(("T-571/", "T-574/", "T-577/")):
        return A.ev_v6(sid, r)
    raise Z.StatementError(f"{sid}: no evidence map")


def headline(secs: list[dict], superseded: dict) -> list[dict]:
    out = []
    for c in secs:
        sid = c["section_id"]
        bce = A.by_class_evidence(c["rows"], c["unit"], lambda r, sid=sid: expected_evidence(sid, r))
        out.append({"section_id": sid, "unit": c["unit"], "reference_total": c["reference_total"],
                    "engine_valued": c["engine_valued"], "difference": c["difference"],
                    "difference_pct_of_reference": c["difference_pct_of_reference"],
                    "by_class_evidence": bce, "superseded_by": superseded.get(sid)})
    return out


def build_from(st6: dict, src: dict, v8: dict) -> dict:
    st = copy.deepcopy(st6)
    s576, mv576 = A.t576_sections(src["T-576"], st6)
    beams, mvb = A.t576_beam_restate(src["T-576"], st6)
    rails = A.t578_rails(src["T-578"])
    steps, nc584 = A.t584_sections(src["T-584"], src["T-578"])
    mlm, mv584 = A.t584_marble_lm_restate(st6, src["T-584"])
    xref = A.t578_nosing_xref(src["T-578"], steps, mlm)
    b583 = A.t583_beside(src["T-583"], st6, v8)
    secs = s576 + [beams, rails] + steps + [mlm]
    ids = [c["section_id"] for c in st6["sections"] + st6["sections_v5"] + st6["sections_v6"]]
    for c in secs:
        if c["section_id"] in ids:
            raise Z.StatementError(f"{c['section_id']}: section id already in V6")
        A.A6.refuse_pct_without_row(c)
        if c["section_id"] == "T-545/beams@V7":
            A.reclose_v4(c)                  # V4 schema (its % stands: V4 class rules)
        else:
            Z.close_section(c)
        if c.get("restates") and c["restates"] not in SUPERSEDES:
            raise Z.StatementError(f"{c['section_id']}: restates {c['restates']} without a supersession entry")
        A.audit_evidence(c, lambda r, sid=c["section_id"]: expected_evidence(sid, r))
    for old, new in SUPERSEDES.items():
        if not old.startswith("beside") and old not in ids:
            raise Z.StatementError(f"supersession of an unknown section {old}")
    st["sections_v7"] = secs
    st["beside_v7"] = [xref, b583]
    st["supersedes_v7"] = SUPERSEDES
    st["headline_v7"] = headline(st6["sections_v6"] + secs, SUPERSEDES)
    st["corrections_v7"] = [
        {"finding": "F-C-T586-1", "applied": "headline_v7 prints every V6 and V7 class split by evidence status "
         "(Checker VERIFIED / partially verified / worker-proposed) from the verdict lines; T-577 ENGINE_RIGHT "
         "-11.6888 m2 / -49.13 lm / -47 nr now read worker-proposed", "verdict": A.V586},
        {"finding": "F-T586-1", "applied": "E1 step lm 11.20 UNRESOLVED -> ENGINE_WRONG (Checker VERIFIED "
         "ENGINE_OMISSION, fix row FR-T584-1) in T-577/marble-lm@V7; the V6 row is kept byte-equal and superseded",
         "verdict": A.V584}]
    st["not_comparable"] = st6["not_comparable"] + nc584
    st["reclasses"] = st6["reclasses"] + mv576 + [mvb] + mv584
    st["reports_covered"] = st6["reports_covered"] + NEW_REPORTS
    st["reports_pending"] = PENDING
    st["rule"] = st6["rule"] + " + R-T587-1"
    st["schema_v7"] = "URBAN_T587_RECONCILED_STATEMENT_V7"
    st["lessons_adopted_applied_v7"] = LESSONS_ADOPTED
    st["provenance"]["inputs_v7"] = {str(p.relative_to(Z.ROOT)): Z.sha(p) for p in
                                     list(A.PINS) + [Z.T569_JSON, B586.JSON_OUT, B586.MD_OUT,
                                                     HERE / "t587_adapters.py", HERE / "t587_build.py"]}
    st["released_quantities_changed"] = 0
    Z.refuse_manifest_as_line(st)
    out = json.loads(json.dumps(st, sort_keys=True))
    check_v6_unchanged(out, st6)
    return out


def build() -> dict:
    st6 = v6_statement()
    src = {"T-576": A.load(A.T576_JSON), "T-578": A.load(A.T578_JSON), "T-583": A.load(A.T583_JSON),
           "T-584": A.load(A.T584_JSON)}
    return build_from(st6, src, Z.load(Z.T569_JSON))


EV = {A.CV: "V", A.PV: "PV", A.WP: "WP"}


def _bce(h: dict) -> str:
    parts = []
    for k, m in h["by_class_evidence"].items():
        tot = sum((D(v) for v in m.values()), D(0))
        if not any(D(v) for v in m.values()):
            continue
        parts.append(f"{k} {Z.s(tot)} [" + ", ".join(f"{EV[e]} {v}" for e, v in m.items() if D(v)) + "]")
    return "; ".join(parts) or "-"


def to_markdown(st: dict) -> str:
    md = ("# T-587 reconciled-quantities statement V7 (generated; reference - engine, + = in the reference only)\n\n"
          "V7 = statement V6 (T-586, rebuilt and equal to its committed output; every V6 key carried byte-equal) + the "
          "sections below. Development villa; not an accuracy claim; nothing released.\n\n"
          "Evidence (R-T587-1 (a), F-C-T586-1): V = Checker VERIFIED, PV = partially verified, WP = worker-proposed, "
          "each from the Checker's verdict line, never from a handoff.\n\n")
    md += ("## Headline by class and evidence (V6 + V7 sections)\n\n| Section | Unit | Reference | Engine valued | "
           "Difference | % of ref. | By class [evidence] | Superseded by |\n|---|---|---|---|---|---|---|---|\n")
    for h in st["headline_v7"]:
        md += (f"| {h['section_id']} | {h['unit']} | {h['reference_total']} | {h['engine_valued']} | {h['difference']} "
               f"| {h['difference_pct_of_reference'] or 'none'} | {_bce(h)} | {h['superseded_by'] or '-'} |\n")
    md += "\n## T-576 columns (m3): reading of record and the 10E0 C7 conflict reading\n\n"
    md += "| Section | Reading | Reference | Engine | Difference | % |\n|---|---|---|---|---|---|\n"
    for c in st["sections_v7"]:
        if c["section_id"].startswith("T-576/"):
            md += (f"| {c['section_id']} | {c['reading']} | {c['reference_total']} | {c['engine_valued']} | "
                   f"{c['difference']} | {c['difference_pct_of_reference'] or 'none (beside)'} |\n")
    beams = [c for c in st["sections_v7"] if c["section_id"] == "T-545/beams@V7"][0]
    md += (f"\nT-545/beams@V7: totals unchanged ({beams['reference_total']} vs {beams['engine_valued']} m3); the GF B7 "
           "UNTRACED row moves UNRESOLVED -> RULE_DIFFERENCE (F-T587-2, PV: 2 / 14 ends re-read).\n")
    x = [b for b in st["beside_v7"] if b["block_id"] == "T-578/nosing-xref"][0]
    md += ("\n## Stair-step reference cells: one owner each (R-T587-1 (b))\n\n| Stair | His cells | His lm | Owned by | "
           "Nosing census lm (beside, no line) |\n|---|---|---|---|---|\n")
    for c in x["census"]:
        md += f"| {c['stair']} | {c['his_cells']} | {c['his_lm']} | {c['owned_by_section']} | {c['nosing_census_lm']} |\n"
    md += (f"\nT-578 nosing totals beside only: lm his {x['units']['lm']['his']} vs census "
           f"{x['units']['lm']['nosing_census']} ({x['units']['lm']['held_n']} HELD), nr {x['units']['nr']['his']} vs "
           f"{x['units']['nr']['nosing_census']}; never re-added.\n")
    m = [c for c in st["sections_v7"] if c["section_id"] == "T-577/marble-lm@V7"][0]["beside"]["door_steps_t584"]
    md += (f"\nExternal door steps (T-584, beside T-577/marble-lm@V7): drawn {m['drawn_lm']} lm / {m['drawn_nr']} nr, "
           f"risers {m['riser_m2']} m2 (+ D-GF-09 {' .. '.join(m['riser_held_m2'])} m2 HELD), gate "
           f"{m['gate_lm_not_re_read']} lm not re-read; {m['status']}.\n")
    b = [b for b in st["beside_v7"] if b["block_id"] == "T-583/dome-lift-components"][0]
    e = b["expected_after_v8_rebar_rows"]
    md += ("\n## B11 dome / ring / lift-wall bar components (T-583, t; beside: V8 manifest rows, valued 0)\n\n"
           "| Row | Status | At least (t) | Bounded part, not a high (t) | T-575 range (t) |\n|---|---|---|---|---|\n")
    for r in b["rows"]:
        if "at_least_t" in r:
            md += (f"| {r['row_id']} | {r['status']} | {r['at_least_t']} | {r['bounded_part_t_not_a_high']} | "
                   f"{' .. '.join(r['t575'])} |\n")
        else:
            md += f"| {r['row_id']} | {r['status']} | blank: {r['blank_named'][:60]} | - | - |\n"
    md += (f"| Total | valued 0 | {b['at_least_t']} | {b['bounded_part_t_not_a_high']} | {' .. '.join(b['t575_was_t'])} "
           f"|\n\nHigh OPEN (laps, hooks, anchorage, ring depth by name); F-C-T583-1 tighter low "
           f"{b['tighter_low_if_per_face_F_C_T583_1_t']} t if the side-bar label is per face. EXPECTED after the V8 rows: "
           f"G5 held at least {e['held_at_least_t']} t (high open); residual vs his TYPED_LUMP at most "
           f"{e['residual_after_held_at_most_t']} t, no %.\n")
    md += "\n## Reclasses added in V7\n\n"
    for r in st["reclasses"]:
        if r["tag"].startswith("F-T587"):
            md += f"- {r['tag']} {r['section_id']}: {r['row'][:90]} {r['from']} -> {r['to']} {r['delta']}\n"
    md += "\n## NOT_COMPARABLE blocks added in V7 (no difference, no %)\n\n"
    for nc in st["not_comparable"]:
        if nc["report"] in NEW_REPORTS:
            md += f"- {nc['block_id']} ({nc['unit']}): reference {nc['reference_total']}\n"
    md += "\nSuperseded (kept byte-equal in V6 / V5 / V4): " + "; ".join(f"{k} -> {v}" for k, v in
                                                                      st["supersedes_v7"].items()) + ".\n"
    md += f"\nReports covered: {', '.join(st['reports_covered'])}; pending: {', '.join(st['reports_pending'])}.\n"
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
            print("T-587 statement differs from out/")
            return 1
        print("T-587 statement reproduces")
    if not argv:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
