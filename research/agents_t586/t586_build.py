"""T-586: the reconciled-quantities statement V6 = the T-579 statement V5 (rebuilt read only and checked equal to its
committed JSON and markdown) + T-571 (lintel count, nr; lm beside), T-574 (skirting, lm / nr; outline vs deduction),
T-575 (dome / ring / lift-wall rebar HELD ranges, t, beside) and T-577 (marble by unit) as new sections; the V5 pads
section labelled 'not split' (F-C-T579-1). No private input; no quantity moves; nothing released.

  python3 -I research/agents_t586/t586_build.py --write   # write out/
  python3 -I research/agents_t586/t586_build.py --check   # rebuild and compare with out/ (exit 1 on a difference)
"""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t586_adapters as A  # noqa: E402
Z = A.Z
sys.path.insert(0, str(A.T579))
import t579_build as B579  # noqa: E402  (T-579, read only)

D = Decimal
OUT = HERE / "out"
JSON_OUT = OUT / "RECONCILED_STATEMENT_T586.json"
MD_OUT = OUT / "RECONCILED_STATEMENT_T586.md"
NEW_REPORTS = ["T-571", "T-574", "T-575", "T-577"]
PENDING = ["T-576", "T-578"]
PADS = "T-572/measured-footing_pads_and_straps"
CANDIDATE_SKIRTING_LM = "209.428592"
LESSONS_ADOPTED = [
    "T-571 (Checker ACCEPTED): when the reference has no row, put his opening list through the same rule, label it "
    "implied and reconcile per opening to cause with a closure assertion",
    "T-574 (Checker ACCEPTED): compare OUTLINE terms (gross vs gross) and DEDUCTION terms separately, every opening "
    "by id",
    "T-575 (Checker ACCEPTED): a bar group without a printed dimension is a range or a formula beside, never a number",
    "T-577 (Checker ACCEPTED): class every reference cell by its own label and its row's dimension cells; a length in "
    "an area column closes his total with a UNIT cause, never compared"]


def v5_statement() -> dict:
    st5 = B579.build()
    if st5 != json.loads(B579.JSON_OUT.read_text(encoding="utf-8")) or \
            B579.to_markdown(st5) != B579.MD_OUT.read_text(encoding="utf-8"):
        raise Z.StatementError("T-579 statement V5 does not reproduce: rebuild it before T-586")
    return st5


def check_v5_unchanged(st: dict, st5: dict) -> None:
    """Every V5 key is identical except the pads label (one new field on one section)."""
    for k in st5:
        if k == "sections_v5":
            for a, b in zip(st[k], st5[k]):
                if a["section_id"] == PADS:
                    extra = set(a) - set(b)
                    if extra != {"cause_split"} or any(a[x] != b[x] for x in b):
                        raise Z.StatementError(f"{PADS}: more than its label changed")
                elif a != b:
                    raise Z.StatementError(f"{a['section_id']}: changed in V6")
            if len(st[k]) != len(st5[k]):
                raise Z.StatementError("V5 section count changed")
        elif k in ("not_comparable", "reclasses", "reports_covered", "reports_pending", "rule", "provenance"):
            continue                                       # extended below, prefix checked
        elif st[k] != st5[k]:
            raise Z.StatementError(f"V5 key {k} changed")
    for k in ("not_comparable", "reclasses", "reports_covered"):
        if st[k][:len(st5[k])] != st5[k]:
            raise Z.StatementError(f"V5 {k} not carried as its prefix")


def build_from(st5: dict, src: dict, v8: dict) -> dict:
    st = copy.deepcopy(st5)
    for c in st["sections_v5"]:
        if c["section_id"] == PADS:
            if c["rows"] or c["closure_residual"] is not None:
                raise Z.StatementError(f"{PADS}: has cause rows; the label would be wrong")
            c["cause_split"] = ("not split (F-C-T579-1): the -0.628000 m3 difference carries no cause rows in V5; its "
                                "split lives in V4 T-551/footing-line (T-551 classes), never repeated here")
    s571, nc571 = A.t571_sections(src["T-571"])
    s574, nc574, mv574 = A.t574_sections(src["T-574"], CANDIDATE_SKIRTING_LM)
    s577, nc577, mv577 = A.t577_sections(src["T-577"])
    b575 = A.t575_beside(src["T-575"], st5, v8)
    secs = s571 + s574 + s577
    ids = [c["section_id"] for c in st["sections"] + st["sections_v5"]]
    for c in secs:
        if c["section_id"] in ids:
            raise Z.StatementError(f"{c['section_id']}: section id already in V5")
        A.refuse_pct_without_row(c)
        Z.close_section(c)                       # idempotent re-close: residual 0, unit, %
    st["sections_v6"] = secs
    st["beside_v6"] = [b575]
    st["not_comparable"] = st5["not_comparable"] + nc571 + nc574 + nc577
    st["reclasses"] = st5["reclasses"] + mv574 + mv577
    st["reports_covered"] = st5["reports_covered"] + NEW_REPORTS
    st["reports_pending"] = PENDING
    st["rule"] = st5["rule"] + " + R-T586-1"
    st["schema_v6"] = "URBAN_T586_RECONCILED_STATEMENT_V6"
    st["lessons_adopted_applied_v6"] = LESSONS_ADOPTED
    st["provenance"]["inputs_v6"] = {str(p.relative_to(Z.ROOT)): Z.sha(p) for p in
                                     list(A.PINS) + [Z.T569_JSON, B579.JSON_OUT, B579.MD_OUT,
                                                     HERE / "t586_adapters.py", HERE / "t586_build.py"]}
    st["released_quantities_changed"] = 0
    Z.refuse_manifest_as_line(st)
    out = json.loads(json.dumps(st, sort_keys=True))
    check_v5_unchanged(out, st5)
    return out


def build() -> dict:
    st5 = v5_statement()
    src = {"T-571": A.load(A.T571_JSON), "T-574": A.load(A.T574_JSON), "T-575": A.load(A.T575_JSON),
           "T-577": A.load(A.T577_JSON)}
    return build_from(st5, src, Z.load(Z.T569_JSON))


def _bc(c):
    return ", ".join(f"{k} {v}" for k, v in c["by_class"].items() if D(c["by_class_gross_abs"][k])) or "-"


def to_markdown(st: dict) -> str:
    md = ("# T-586 reconciled-quantities statement V6 (generated; reference - engine, + = in the reference only)\n\n"
          "V6 = statement V5 (T-579, rebuilt and equal to its committed output; every V5 section unchanged except the "
          "pads label) + the sections below. Development villa; not an accuracy claim; nothing released.\n\n")
    md += ("## New sections (V6)\n\n| Section | Kind | Unit | Reference | Engine valued | Difference | % of ref. | "
           "By class (non-zero, net) |\n|---|---|---|---|---|---|---|---|\n")
    for c in st["sections_v6"]:
        ref = c["reference_total"] + (" (implied)" if c["reference_kind"] == "FREELANCER_IMPLIED" else "")
        md += (f"| {c['section_id']} | {c['kind']} | {c['unit']} | {ref} | {c['engine_valued']} | {c['difference']} | "
               f"{c['difference_pct_of_reference'] or 'none'} | {_bc(c)} |\n")
    lin = [c for c in st["sections_v6"] if c["section_id"] == "T-571/lintel-count-implied"][0]
    md += ("\n### Lintels by stock length (T-571, nr; implied = his openings through the owner rule, not his figure)\n\n"
           "| Length (m) | Implied | Engine AT_MOST | Implied - engine |\n|---|---|---|---|\n")
    for L, v in lin["by_length"].items():
        md += f"| {L} | {v['implied']} | {v['engine_at_most']} | {v['difference']} |\n"
    md += (f"\nEstablished engine lintels {lin['engine_established_nr']} nr; lm beside (never summed with nr): implied "
           f"{lin['beside_lm']['implied']} vs engine {lin['beside_lm']['engine_at_most']} lm. No %.\n")
    rm = [c for c in st["sections_v6"] if c["section_id"] == "T-574/skirting-room"][0]["beside"]
    g = rm["gross_vs_gross_outline_terms"]
    md += (f"\nSkirting rooms (T-574): gross vs gross (outline terms) {g['reference_lm']} vs {g['engine_outline_lm']} "
           f"lm, difference {g['difference']} ({g['difference_pct_of_reference']} % of ref.); deduction terms "
           f"{rm['deduction_terms_lm']} lm (he deducts none); net {rm['net_pct_NOT_a_verdict']} % is NOT a verdict.\n")
    b = st["beside_v6"][0]
    e = b["expected_after_v8_rebar_rows"]
    md += ("\n### B11 dome / ring / lift-wall rebar (T-575, t; beside: V8 manifest rows, not candidate lines)\n\n"
           "| Row | Status | Range (t) / blank | T-560 group |\n|---|---|---|---|\n")
    for r in b["rows"]:
        v = " .. ".join(r["range_t"]) if "range_t" in r else "HELD_BLANK (" + r["blank_named"][:60] + ")"
        md += f"| {r['row_id']} | {r['status']} | {v} | {r['t560_group']} |\n"
    md += (f"| Total | valued 0 | {' .. '.join(b['range_t'])} | |\n\nEXPECTED after the V8 REBAR_OMISSION rows (beside "
           f"only): G5 held {' .. '.join(e['v5_held_range_t'])} + {' .. '.join(e['plus_t575_t'])} = "
           f"{' .. '.join(e['held_range_t'])} t, residual after bounded held {' .. '.join(e['residual_after_bounded_held_t'])}"
           f" t (his TYPED_LUMP, no %).\n")
    pads = [c for c in st["sections_v5"] if c["section_id"] == PADS][0]
    md += f"\nV5 {PADS}: {pads['cause_split']}\n"
    md += "\n## NOT_COMPARABLE blocks added in V6 (no difference, no %)\n\n"
    n5 = len(st["not_comparable"]) - sum(1 for x in st["not_comparable"] if x["report"] in NEW_REPORTS)
    for x in st["not_comparable"][n5:]:
        md += f"- {x['block_id']} ({x['unit']}): reference {x['reference_total']}\n"
    md += "\nReclasses (R-T586-1 (e)): " + ("; ".join(
        f"{m['tag']} {m['section_id']} {m['row'][:60]} {m['from']} -> {m['to']} {m['delta']}"
        for m in st["reclasses"] if m["tag"].startswith("F-T586")) or "none") + ".\n"
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
            print("T-586 statement differs from out/")
            return 1
        print("T-586 statement reproduces")
    if not argv:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
