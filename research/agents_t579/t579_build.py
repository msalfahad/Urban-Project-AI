"""T-579: the reconciled-quantities statement V5 = the T-570 statement V4 (rebuilt read only and checked equal to its
committed output) + T-560 (B11 rebar, t, TYPED_LUMP), T-568 (doors / windows nr and m2 apart; the T-559 opening rows
of T-543/blockwork restated), T-572 (structural HELD bounds + like-for-like measured set), T-573 (ceilings by face
class) as new sections, and the T-569 manifest V8 rows beside (never candidate lines). No private input.

  python3 -I research/agents_t579/t579_build.py --write   # write out/
  python3 -I research/agents_t579/t579_build.py --check   # rebuild and compare with out/ (exit 1 on a difference)
"""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t579_adapters as Z  # noqa: E402
import t570_build as B570  # noqa: E402  (T-570, read only)

D = Decimal
OUT = HERE / "out"
JSON_OUT = OUT / "RECONCILED_STATEMENT_T579.json"
MD_OUT = OUT / "RECONCILED_STATEMENT_T579.md"
NEW_REPORTS = ["T-560", "T-568", "T-569", "T-572", "T-573"]
PENDING = ["T-571", "T-574"]
TOUCHED_V4 = ("T-543/blockwork",)
LESSONS_ADOPTED = [
    "T-560 (Checker ADOPT): classify the benchmark basis first (COUNTED / RATIO / TYPED_LUMP); compare only on the "
    "smallest common scope group; valued / held range / held blank apart; residual as named causes, never a %",
    "T-568 (Checker ADOPT): a count difference is settled by reading the drawn leaves; a pairing only splits m2 "
    "between width and count terms and never changes a class total"]


def v4_statement() -> dict:
    st4 = B570.build()
    if st4 != Z.load(Z.V4_JSON) or B570.to_markdown(st4) != B570.MD_OUT.read_text(encoding="utf-8"):
        raise Z.StatementError("T-570 statement V4 does not reproduce: rebuild it before T-579")
    return st4


def build_from(st4: dict, index: dict, src: dict) -> dict:
    st = copy.deepcopy(st4)
    moves = []
    # T-568 restates the 8 T-559 opening rows of V4 T-543/blockwork (class only)
    ids = [c["section_id"] for c in st["sections"]]
    i = ids.index("T-543/blockwork")
    st["sections"][i], mv = Z.restate_blockwork_t568(st["sections"][i])
    moves += mv
    for t in st["totals"]:
        if t["sections"] == ["T-543/blockwork"]:
            t["by_class"] = dict(st["sections"][i]["by_class"])
            t["by_class_gross_abs"] = dict(st["sections"][i]["by_class_gross_abs"])
    check_v4_unchanged(st, st4)
    s560, nc560 = Z.t560_sections(src["T-560"])
    s568, nc568 = Z.t568_sections(src["T-568"], st4)
    s573, nc573, mv573 = Z.t573_sections(src["T-573"], st4)
    moves += mv573
    s572 = [Z.t572_bounds(src["T-572"], st4)] + Z.t572_measured(src["T-572"])
    secs = s560 + s568 + s572 + s573
    for c in secs:
        Z.refuse_one_sided_as_point(c)
        if "rows" in c and "by_class" in c:
            Z.close_section(c)                       # idempotent re-close: residual 0, unit, %
    st["sections_v5"] = secs
    st["not_comparable"] = st4["not_comparable"] + ([nc560] if nc560 else []) + nc568 + nc573
    st["manifest_beside"] = [Z.t569_manifest(src["T-569"], index, st4)]
    st["reclasses"] = st4["reclasses"] + moves
    st["reports_covered"] = st4["reports_covered"] + NEW_REPORTS
    st["reports_pending"] = PENDING
    st["rule"] = st4["rule"] + " + R-T579-1"
    st["schema_v5"] = "URBAN_T579_RECONCILED_STATEMENT_V5"
    st["lessons_adopted_applied"] = LESSONS_ADOPTED
    st["provenance"]["inputs_v5"] = {str(p.relative_to(Z.ROOT)): Z.sha(p) for p in
                                     list(Z.PINS) + [HERE / "t579_adapters.py", HERE / "t579_build.py"]}
    st["released_quantities_changed"] = 0
    Z.refuse_manifest_as_line(st)
    return json.loads(json.dumps(st, sort_keys=True))


def check_v4_unchanged(st: dict, st4: dict) -> None:
    """Every V4 section other than T-543/blockwork is identical; in it only the 8 named rows change class."""
    for a, b in zip(st["sections"], st4["sections"]):
        if a["section_id"] in TOUCHED_V4:
            for k in ("reference_total", "engine_valued", "difference", "engine_bounded", "held_count"):
                if a[k] != b[k]:
                    raise Z.StatementError(f"{a['section_id']}: {k} moved")
            for r, r0 in zip(a["rows"], b["rows"]):
                if r["name"] in Z.T559_ROWS:
                    if r["delta"] != r0["delta"]:
                        raise Z.StatementError(f"{r['name']}: delta moved")
                elif r != r0:
                    raise Z.StatementError(f"{a['section_id']}: row '{r['name']}' changed outside T-568")
        elif a != b:
            raise Z.StatementError(f"{a['section_id']}: changed outside the T-579 target")
    if len(st["sections"]) != len(st4["sections"]):
        raise Z.StatementError("V4 section count changed")


def build() -> dict:
    st4 = v4_statement()
    src = {"T-560": Z.load(Z.T560_JSON), "T-568": Z.load(Z.T568_JSON), "T-569": Z.load(Z.T569_JSON),
           "T-572": Z.load(Z.T572_JSON), "T-573": Z.load(Z.T573_JSON)}
    return build_from(st4, Z.load_index(), src)


def _rng(x):
    return " .. ".join(str(v) for v in x) if x else "none"


def to_markdown(st: dict) -> str:
    md = ("# T-579 reconciled-quantities statement V5 (generated; reference - engine, + = in the reference only)\n\n"
          "V5 = statement V4 (T-570, rebuilt and equal to its committed output; 18 sections, only T-543/blockwork "
          "restated) + the sections below. Development villa; not an accuracy claim; nothing released.\n\n")
    md += "## V4 sections (as carried)\n\n| Section | Unit | Reference | Engine valued | Difference | UNRESOLVED |\n"
    md += "|---|---|---|---|---|---|\n"
    for c in st["sections"]:
        md += (f"| {c['section_id']} | {c['unit']} | {c['reference_total']} | {c['engine_valued']} | "
               f"{c['difference']} | {c['by_class']['UNRESOLVED']} |\n")
    bw = [c for c in st["sections"] if c["section_id"] == "T-543/blockwork"][0]
    md += (f"\nT-543/blockwork restated by T-568 (F-T579-1, class only, deltas unchanged): the 8 T-559 opening rows "
           f"(+6.30 m2) UNRESOLVED -> ENGINE_RIGHT +6.54 / RULE_DIFFERENCE -0.24; section classes now "
           + ", ".join(f"{k} {v}" for k, v in bw["by_class"].items()) + ".\n")
    md += ("\n## New sections (V5)\n\n| Section | Kind | Unit | Reference | Engine valued | Difference | % of ref. | "
           "By class (non-zero; net / gross abs) |\n|---|---|---|---|---|---|---|---|\n")
    for c in st["sections_v5"]:
        if "by_class" in c:
            bc = ", ".join(f"{k} {v} / {c['by_class_gross_abs'][k]}" for k, v in c["by_class"].items()
                           if D(c["by_class_gross_abs"][k]))
            md += (f"| {c['section_id']} | {c['kind']} | {c['unit']} | {c['reference_total']} | {c['engine_valued']} | "
                   f"{c['difference']} | {c['difference_pct_of_reference'] or 'none'} | {bc or '-'} |\n")
        elif c["kind"] == "ONE_SIDED":
            md += (f"| {c['section_id']} | ONE_SIDED | m3 | {c['reference_total']} | AT_LEAST "
                   f"{c['engine']['at_least']} (high OPEN) | none | none | {c['class']} |\n")
        elif c["kind"] == "CROSS_REFERENCE":
            md += f"| {c['section_id']} | CROSS_REFERENCE | {c['unit']} | counted in {c['reference_counted_in']} | | | none | |\n"
    r = [c for c in st["sections_v5"] if c["section_id"] == "T-560/rebar"][0]
    md += ("\n### B11 reinforcement (T-560, t; TYPED_LUMP: RULE_DIFFERENCE, quantity UNRESOLVED, no %)\n\n"
           "| Group | His (t) | Engine valued | Engine held range | Held blank | His - valued | Residual after bounded "
           "held | Omission of a line |\n|---|---|---|---|---|---|---|---|\n")
    for x in r["rows"]:
        om = "; ".join(o["element"] for o in x["engine_omission_of_a_line"]) or "-"
        md += (f"| {x['name'].split(':')[0]} | {x['his_t']} | {x['engine_valued_t']} | {_rng(x['engine_held_range_t'])} | "
               f"{x['engine_held_blank_lines']} | {x['delta']} | {_rng(x['residual_after_bounded_held_t'])} | {om} |\n")
    eh = r["engine_held"]
    md += (f"| Total | {r['reference_total']} | {r['engine_valued']} | {_rng(eh['held_range_t'])} | "
           f"{eh['held_blank_lines']} (incl. tank 1) | {r['difference']} | | |\n\nTank: his NO_ROW, NOT_COMPARABLE.\n")
    w = [c for c in st["sections_v5"] if c["section_id"] == "T-568/windows-m2"][0]["beside"]
    a, b = w["like_for_like_settled_both_sides"], w["expected_after_V8_W17_row"]
    md += (f"\nWindows like for like (T-568): {a['reference_m2']} vs {a['engine_m2']} m2 on {a['openings']}, "
           f"difference {a['difference']} ({a['difference_pct_of_reference']} % of ref.; engine vs reference "
           f"{a['engine_vs_reference_pct']} %); EXPECTED after the V8 W17 row (beside only): {b['reference_m2']} vs "
           f"{b['engine_m2']} on {b['openings']} ({b['engine_vs_reference_pct']} %).\n")
    hb = [c for c in st["sections_v5"] if c["section_id"] == "T-572/held-bounds"][0]
    md += ("\n### B10 / B1 HELD bounds (T-572, m3, engine side; a one-sided end is AT_LEAST, high OPEN)\n\n"
           "| Family | V4 section | Valued | Held n | Both ends drawn | Lower end only | No drawn bound | Family held |\n"
           "|---|---|---|---|---|---|---|---|\n")
    for f in hb["families"]:
        lo = f["lower_end_only"]
        ft = f["family_total"]["family_held"]
        ftxt = ("AT_LEAST " + ft["at_least"]) if isinstance(ft, dict) else (_rng(ft) if ft else "not stateable")
        md += (f"| {f['family']} | {f['relates_to_v4']} | {f['engine_valued']} | {f['held_components']} | "
               f"{f['both_ends_drawn']['n']}: {_rng(f['both_ends_drawn']['range'])} | {lo['n']}"
               f"{': AT_LEAST ' + lo['at_least'] if lo['n'] else ''} | {f['no_drawn_bound']['n']} | {ftxt} |\n")
    for c in st["sections_v5"]:
        if c["section_id"].startswith("T-572/measured-") and "beside" in c and "net_of_RULE_DIFFERENCE" in c["beside"]:
            n = c["beside"]["net_of_RULE_DIFFERENCE"]
            md += (f"\n{c['section_id']}: like for like {c['difference']} m3 ({c['difference_pct_of_reference']} % of "
                   f"ref.), net of RULE_DIFFERENCE (JOINT_HEAD) {n['difference']} ({n['difference_pct_of_reference']} %).")
    bd = [c for c in st["sections_v5"] if c["section_id"] == "T-573/ceiling-board"][0]["beside"]
    md += (f"\n\nCeiling board (T-573): headline {bd['headline_pct_NOT_a_verdict']['engine_vs_reference_pct']} % "
           f"engine vs reference is NOT a verdict; like for like {bd['like_for_like_no_held']['reference_m2']} vs "
           f"{bd['like_for_like_no_held']['engine_m2']} m2 ({bd['like_for_like_no_held']['engine_vs_reference_pct']} %)."
           "\n")
    md += "\n## NOT_COMPARABLE blocks (no difference, no %)\n\n"
    for b in st["not_comparable"]:
        md += f"- {b['block_id']} ({b.get('unit', 'per family')}): reference {b['reference_total'] or 'NO_ROW'}\n"
    md += "\n## Manifest V8 rows (beside; NOT candidate lines; valued columns unchanged)\n\n"
    md += "| Row | Evidence status | Statement row | Switch condition |\n|---|---|---|---|\n"
    for x in st["manifest_beside"][0]["rows"]:
        md += f"| {x['id']} | {x['evidence_status']} | {x['statement_row']} | {x['switch_condition']} |\n"
    md += "\nReclasses (R-T579-1): " + "; ".join(
        f"{m['tag']} {m['section_id']} {m['row'][:48]} {m['from']} -> {m['to']} {m['delta']}"
        for m in st["reclasses"] if m["tag"].startswith("F-T579")) + ".\n"
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
            print("T-579 statement differs from out/")
            return 1
        print("T-579 statement reproduces")
    if not argv:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
