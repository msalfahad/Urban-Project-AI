"""T-590: RULE_DIFF provenance audit of the STRUCTURAL sections (B10 concrete, B11 reinforcement, B1 earthworks) of
statement V7 (T-587; V6 byte-equal inside it), on the training villa. Reads the committed V7 statement JSON
(sha256-pinned) and the repository's rule registers; writes out/T590_RULE_DIFF_PROVENANCE.json / .md. No private input
is read by this script (his conventions below were read once by the worker from his workbook, Drive 'Alsenan chalet
project', the concrete + rebar workbook sha256 ae608411, in .work/private only; only sheet roles, row numbers and
heights / typed figures already in the merged reports are written here). Nothing released, no candidate / rule /
knowledge / registry file touched; a reclass is a statement-level label (-> UNRESOLVED), never a quantity change.

  python3 -I research/agents_t590/t590_alsenan.py --write
  python3 -I research/agents_t590/t590_alsenan.py --check
"""
from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t590_rules as R  # noqa: E402

D = Decimal
ROOT = R.ROOT
V7 = ROOT / "research" / "agents_t587" / "out" / "RECONCILED_STATEMENT_T587.json"
PINS = {
    "research/agents_t587/out/RECONCILED_STATEMENT_T587.json":
        "3cd55327d5d0b960cc8ee5d3b91655a38630af2973533e0d50ca77678bd79745",
    "rules/methods/URBAN_METHOD_REGISTER_V3.json": "d124d19647cdd754f11045b259836f1ae1440656701bba5b7a0ca6b3f8a400b1",
    "rules/rulebook/URBAN_COMPANY_RULEBOOK_1.0.0.json":
        "4e9c57cef33d32ede26bea4eaf3823e2dc3880d56708dd18ec5df3760b84c055",
    "rules/coverage/BOQ_FAMILY_MASTER_1.55.0.json": "22cb3ffc2a747ad3992508717c0840f926def6885f695d8de6e53700821d8c99",
    "research/agents_t591/t591_rules.py": "d42f358734e63dba807b55b2c7fd93d18aa2c6673f48865751a69ecee7410464",
    "research/agents_t189/R-CONC-OWN-1.json": "38ad237b9c34044d911c0dd1e8bfb3fff25eb1ad236c27f990973e56ee61ad78",
}
OUT = HERE / "out"
JSON_OUT = OUT / "T590_RULE_DIFF_PROVENANCE.json"
MD_OUT = OUT / "T590_RULE_DIFF_PROVENANCE.md"
STRUCTURAL = ("B10", "B11", "B1 ")
LEVELS = ("sections", "sections_v5", "sections_v6", "sections_v7")
# A measured-set section is a SUBSET of the members of its parent: its joint rows are the same physical joints as rows
# of the parent, so they are audited but never added to the parent's unit total (R-T590-1, nested).
NESTED = {"T-576/columns-GF": "T-551/columns", "T-576/columns-1F": "T-551/columns",
          "T-576/columns-GF-reading-10E0-C7": "T-551/columns", "T-576/columns-1F-reading-10E0-C7": "T-551/columns",
          "T-572/measured-columns_GF": "T-551/columns", "T-572/measured-columns_1F": "T-551/columns"}

# ------------------------------------------------------------------------------ registers for this audit --------
# Q-62 (owner 2026-10-20, OWNER_DIRECTIVE_2026-10-20 'Q-62'): "the same concrete is measured once ... assign it to the
# slab / landing under the chosen convention ... No double count at stair-landing, beam-slab, column-beam or
# footing-ground-beam junctions ... One convention for the whole project." It REQUIRES once + one convention; it does
# not choose who owns a column-beam joint (clause (h)).
REQUIREMENT_ONLY = {"Q-62": "the joint is measured exactly once under ONE project convention; the owner element is "
                            "left to 'the chosen convention' (not chosen in the answer)"}

# ------------------------------------------------------------------------------------ the audited rows ----------
OWN_TRACED = ["Q-62", "R-T394-1", "R-T395-4",
              "REGISTER:R-CONC-OWN-1 1.0.0-proposed (T-189; precedence column > beam; 'not in force: adoption = a NEW "
              "rule version'; in no rule register)",
              "REGISTER:ERS s.7 lessons row 2026-10-31 (Lead ADOPTED: the column line owns the joint to the slab top; "
              "beams face to face)",
              "REGISTER:ELEMENT_REGISTER 'COLUMN-BEAM JOINT' (Lead 2026-11-06 20:14: the BEAM owns the joint volume at "
              "every column head; the column takes the clear height floor-to-soffit)"]
OWN_CONFLICT = ("CONVENTION_RECORD_CONFLICT: ERS s.7 2026-10-31 (Lead) and R-T394-1 / R-CONC-OWN-1 (engine, V3.0.58 "
                "column lines slab top to slab top) say the COLUMN owns the joint; ELEMENT_REGISTER 2026-11-06 20:14 "
                "(Lead, 'restates T-189 / R-CONC-OWN-1') says the BEAM owns it and the column runs floor-to-soffit, "
                "which is HIS convention. R-CONC-OWN-1 itself states column > beam: the 11-06 entry misstates it")
HIS_BEAM = ("his beam sheet rows carry each beam at full depth (e.g. GF 0.75) with lengths that run through the column "
            "/ carrier footprints (T-545 s.2, R-T395 support allowance per mark); his column rows stop 0.75 below the "
            "slab top: the joint is in his beam rows")
HIS_COL_GF = ("his walls-and-columns sheet, GF rows 36-47: every column height 3.75 = storey 4.50 (+0.95 -> +5.45) - 0.75 "
              "= clear height to a 0.75 beam soffit, one global head depth on every row; joint left to his beams")
HIS_COL_1F = ("his walls-and-columns sheet, 1F rows 52-61 (2F rows 66-71): every column height 3.45 = storey 4.20 "
              "(+5.45 -> +9.65) - 0.75 = clear height to a 0.75 beam soffit; joint left to his beams")
REBAR_TRACED = ["URBAN-REBAR-NET-AND-PROCUREMENT@v1", "Q-71", "OWNER_FILE:OWNER_RULE_REBAR_2026-10-24#all"]
HIS_REBAR = {0: "summary sheet H17 5.8 + H18 9.75 = 15.55 t (footings; ground beams + ground slab)",
             1: "summary sheet H19 7.95 t (walls and columns)", 2: "summary sheet H20 9.89 t (beams)",
             3: "summary sheet H21 5.4 t (slabs)", 4: "summary sheet H22 3.9 t (stair + dome)",
             5: "summary sheet H23 1.5 t (pool)"}
REBAR_NOTE = (": a typed constant, no formula, no bar row on any of his 8 sheets (worker own read; Checker T-560 Gate A "
              "TYPED_LUMP CONFIRMED 7 / 7): no convention is readable")

A: dict[tuple[str, int], dict] = {}


def put(sec, rows, traced, his, *, readable=True, conflict=None, flag=None, miscited=None):
    for i in rows:
        h = his[i] if isinstance(his, dict) else his
        A[(sec, i)] = {"traced": list(traced), "his": h, "readable": readable, "conflict": conflict, "flag": flag,
                       "miscited": miscited or {}}


B7_FLAG = ("THROUGH_SUPPORT on this B7 row is accepted by the Checker on 2 / 14 piece ends only (T-576 Gate A); "
           "the other 12 rest on the worker; was UNRESOLVED before T-587 F-T587-2")
for sec in ("T-545/beams", "T-545/beams@V7"):
    put(sec, [2, 11, 19], OWN_TRACED, HIS_BEAM, conflict=OWN_CONFLICT)
put("T-545/beams@V7", [7], OWN_TRACED, HIS_BEAM, conflict=OWN_CONFLICT, flag=B7_FLAG)
put("T-551/columns", [6], OWN_TRACED, HIS_COL_GF, conflict=OWN_CONFLICT)
put("T-551/columns", [15], OWN_TRACED, HIS_COL_1F, conflict=OWN_CONFLICT)
put("T-572/measured-columns_GF", [1], OWN_TRACED, HIS_COL_GF, conflict=OWN_CONFLICT)
put("T-572/measured-columns_1F", [0], OWN_TRACED, HIS_COL_1F, conflict=OWN_CONFLICT)
put("T-576/columns-GF", [1, 2, 5, 8, 10, 11, 13, 15, 18], OWN_TRACED, HIS_COL_GF, conflict=OWN_CONFLICT)
put("T-576/columns-GF-reading-10E0-C7", [1, 2, 5, 8, 10, 11, 13, 16, 19], OWN_TRACED, HIS_COL_GF,
    conflict=OWN_CONFLICT)
put("T-576/columns-1F", [0, 1, 3, 5], OWN_TRACED, HIS_COL_1F, conflict=OWN_CONFLICT)
put("T-576/columns-1F-reading-10E0-C7", [0, 1, 3, 5, 7], OWN_TRACED, HIS_COL_1F, conflict=OWN_CONFLICT)
put("T-560/rebar", [0, 1, 2, 3, 4, 5], REBAR_TRACED, {k: v + REBAR_NOTE for k, v in HIS_REBAR.items()},
    readable=False,
    flag="the row also carries HELD-blank engine lines and, on G2 / G5, a CONFIRMED engine omission (lift-pit walls, "
         "dome shells / rings): not a pure convention gap even before his side is read")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_pins() -> None:
    for rel, h in PINS.items():
        if sha(ROOT / rel) != h:
            raise R.ProvenanceError(f"{rel}: sha256 differs from its pin (rebuild the audit on the new input)")


def structural_sections(st: dict):
    for lvl in LEVELS:
        for s in st[lvl]:
            if str(s.get("trade", "")).startswith(STRUCTURAL):
                yield lvl, s


def build() -> dict:
    check_pins()
    st = json.loads(V7.read_text(encoding="utf-8"))
    superseded = {k: v for k, v in st["supersedes_v7"].items() if not k.startswith("beside")}
    reg = R.Registers(requirement_only=REQUIREMENT_ONLY)
    rows_out, used, sections_out, no_row_sections = [], set(), [], []
    head_items, all_items = [], []
    for lvl, s in structural_sections(st):
        sid = s["section_id"]
        if "rows" not in s:
            no_row_sections.append({"level": lvl, "section_id": sid, "trade": s.get("trade"),
                                    "class": s.get("class") or s.get("kind"), "rd_rows": 0})
            continue
        recs = {}
        live = sid not in superseded and str(s.get("reading_of_record", "True")) != "False"
        for i, r in enumerate(s["rows"]):
            if r.get("class") != "RULE_DIFFERENCE":
                continue
            key = (sid, i)
            if key not in A:
                raise R.ProvenanceError(f"{key}: RULE_DIFFERENCE row with no audit entry")
            a = A[key]
            used.add(key)
            rec = R.classify(reg, r, a["traced"], a["his"], his_readable=a["readable"], miscited=a["miscited"],
                             conflict=a["conflict"])
            recs[i] = rec
            d = D(str(r["delta"]))
            rows_out.append({"level": lvl, "section_id": sid, "row": i, "unit": s["unit"], "delta": str(d),
                             "name": r.get("name", ""), "row_source": r.get("source", ""),
                             "our_side": rec["sources"], "our_side_outcome": rec["our_side_outcome"],
                             "requirements": rec["requirements"], "cited_in_row": rec["cited_in_row"],
                             "cited_not_governing": rec["cited_not_governing"], "his_side": rec["his_convention"],
                             "his_readable": rec["his_readable"], "outcome": rec["outcome"],
                             "class_after": rec["class_after"], "conflict": rec["convention_record_conflict"],
                             "flag": a["flag"], "live": live, "nested_in": NESTED.get(sid),
                             "superseded_by": superseded.get(sid),
                             "reading_of_record": str(s.get("reading_of_record", "True")) != "False"})
            all_items.append((s["unit"], rec["outcome"], d))
            if live and sid not in NESTED:
                head_items.append((s["unit"], rec["outcome"], d))
        moved = R.reclass_section(s["rows"], recs) if recs else None
        total = sum((D(str(x["delta"])) for x in s["rows"]), D(0))
        if recs and "difference" in s and s["difference"] not in (None, "None") and total != D(str(s["difference"])):
            raise R.ProvenanceError(f"{sid}: rows do not close to the statement difference")
        sections_out.append({"level": lvl, "section_id": sid, "trade": s.get("trade"), "unit": s["unit"],
                             "rd_rows": len(recs), "difference": str(total), "live": live,
                             "nested_in": NESTED.get(sid), "superseded_by": superseded.get(sid),
                             "by_class_before": {k: str(v) for k, v in sorted(moved["before"].items())} if moved else {},
                             "by_class_after": {k: str(v) for k, v in sorted(moved["after"].items())} if moved else {}})
    missing = set(A) - used
    if missing:
        raise R.ProvenanceError(f"audit entries with no RULE_DIFFERENCE row: {sorted(missing)}")

    def tab(items):
        return {u: {o: {"n": b["n"], "signed": str(b["signed"]), "gross": str(b["gross"])} for o, b in sorted(v.items())}
                for u, v in sorted(R.per_unit(items).items())}
    counts: dict[str, int] = {}
    for r in rows_out:
        if r["live"] and not r["nested_in"]:
            counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
    b1 = [x for x in no_row_sections if "B1" in str(x["trade"])]
    t551 = next(s for s in st["sections"] if s["section_id"] == "T-551/columns")
    return {
        "schema": "URBAN_T590_RULE_DIFF_PROVENANCE_V1",
        "rule": "R-T590-1 (= R-T591-1 + (g) method register, (h) requirement only, (i) choice record, (j) his side "
                "unreadable)",
        "input": "statement V7 (T-587; V6 byte-equal inside it): B10 / B11 / B1 sections; architectural = T-591",
        "pins": PINS,
        "q_register_snapshot": "OWNER_QUESTIONS.md, agents/control @344858ff (2026-11-07T11:30Z): answered Q-01..Q-78 "
                               "(not a rule Q-23 / Q-34 / Q-36; scenario only Q-29 S1), open Q-80, withdrawn Q-79 "
                               "(unchanged since T-591's @189683b3)",
        "his_side_read": "worker own read 2026-11-07 of Drive 'Alsenan chalet project', the concrete + rebar workbook "
                         "(sha256 ae608411 = T-560 / T-576 manifest), .work/private only",
        "rows_audited": len(rows_out),
        "rows_headline": sum(1 for r in rows_out if r["live"] and not r["nested_in"]),
        "rows_nested_live": sum(1 for r in rows_out if r["live"] and r["nested_in"]),
        "rows_superseded_or_conflict_reading": sum(1 for r in rows_out if not r["live"]),
        "outcome_counts_headline": dict(sorted(counts.items())),
        "per_unit_headline": tab(head_items),
        "per_unit_all_rows": tab(all_items),
        "b1_earthworks": {"rd_rows": 0, "sections": b1,
                          "note": "B1 sits in no V7 rows section: T-565/earthworks is NOT_COMPARABLE (his NO_ROW on "
                                  "every component, Checker CONFIRMED) and T-572/held-bounds carries families only; "
                                  "0 RULE_DIFFERENCE rows to audit, nothing reclassed"},
        "column_beam_pair_net_m3": t551.get("beside", {}).get("column_beam_pairing_m3"),
        "pair_note": "per storey the column JOINT_HEAD and the beam THROUGH_SUPPORT do not cancel (GF -0.620464, 1F "
                     "-1.208362, 2F -0.532760 m3, reference - engine): even under one recorded ownership rule only the "
                     "matched part of each pair is a convention; the remainder is a residual of its own (T-551 s.3 "
                     "per-crossing bound), never a RULE_DIFFERENCE by default",
        "sections": sections_out,
        "rows": rows_out,
        "lead_actions": [
            "ADOPT one column-beam joint ownership as a rule version (R-CONC-OWN-1 column > beam, as the engine bills, "
            "or the beam as ELEMENT_REGISTER 2026-11-06 says, which would re-split V3.0.58 column and beam lines): "
            "Q-62 leaves the choice to the project ('the chosen convention', 'one convention'), so ERS s.2.7 is not "
            "met and no owner question is raised",
            "CORRECT the ELEMENT_REGISTER 'COLUMN-BEAM JOINT' entry of 2026-11-06 20:14: it contradicts the engine, "
            "the ERS s.7 row of 2026-10-31 and R-CONC-OWN-1 which it says it restates",
            "RELABEL engine/source/arch_v3012.py:84 'owner_rules' R-CONC-OWN-1 (a proposed worker rule, not an owner "
            "rule) in the next method version that touches it (frozen module: never in place)",
            "B11 typed lump: keep the six groups UNRESOLVED (his side unreadable) until a bar-level reference exists; "
            "the engine's own bar takeoff is checked against the drawings, not against his constants",
        ],
        "released_quantities_changed": 0,
    }


def to_markdown(o: dict) -> str:
    L = ["# T-590 RULE_DIFF provenance, structural B10 / B11 / B1 (generated)", "",
         f"Input: {o['input']}. Rule {o['rule']}. Rows audited {o['rows_audited']}: headline {o['rows_headline']} "
         f"(live, not nested), nested live {o['rows_nested_live']} (T-576 measured set inside T-551/columns), "
         f"superseded / conflict reading {o['rows_superseded_or_conflict_reading']}. No % anywhere; units apart.", "",
         "## Outcome per unit (headline rows; signed = reference - engine, gross = sum of |delta|)", "",
         "| Unit | Outcome | Rows | Signed | Gross |", "|---|---|---|---|---|"]
    for u, v in o["per_unit_headline"].items():
        for oc, b in v.items():
            L.append(f"| {u} | {oc} | {b['n']} | {b['signed']} | {b['gross']} |")
    L += ["", "## Every audited row", "",
          "| Section | Row | Unit | Delta | Name | Our side (rule kinds) | His side | Outcome -> class | Live |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in o["rows"]:
        kinds = ", ".join(sorted({s["kind"] for s in r["our_side"]}))
        live = "yes" if r["live"] and not r["nested_in"] else ("nested" if r["live"] else "no")
        L.append(f"| {r['section_id']} | {r['row']} | {r['unit']} | {r['delta']} | {r['name'][:60]} | {kinds} | "
                 f"{'readable' if r['his_readable'] else 'UNREADABLE'} | {r['outcome']} -> {r['class_after']} | {live} |")
    L += ["", "## B1 earthworks", "", o["b1_earthworks"]["note"], "",
          "## Column / beam pair (m3, reference - engine)", "", o["pair_note"], ""]
    L += ["## Convention record conflict", "", next((r["conflict"] for r in o["rows"] if r["conflict"]), "none"), "",
          "## Lead actions (no number moved here)", ""]
    L += [f"- {a}" for a in o["lead_actions"]]
    L += ["", "## Sections: classes before / after (difference unchanged)", "",
          "| Section | Unit | RD rows | Difference | RULE_DIFFERENCE before | after | UNRESOLVED after | Live |",
          "|---|---|---|---|---|---|---|---|"]
    for s in o["sections"]:
        if not s["rd_rows"]:
            continue
        b, a = s["by_class_before"], s["by_class_after"]
        L.append(f"| {s['section_id']} | {s['unit']} | {s['rd_rows']} | {s['difference']} | "
                 f"{b.get('RULE_DIFFERENCE', '0')} | {a.get('RULE_DIFFERENCE', '0')} | {a.get('UNRESOLVED', '0')} | "
                 f"{'nested' if s['nested_in'] else s['live']} |")
    return "\n".join(L) + "\n"


def main(argv: list[str]) -> int:
    o = build()
    js = json.dumps(o, indent=1, ensure_ascii=False, sort_keys=False) + "\n"
    md = to_markdown(o)
    if "--write" in argv:
        OUT.mkdir(exist_ok=True)
        JSON_OUT.write_text(js, encoding="utf-8")
        MD_OUT.write_text(md, encoding="utf-8")
        return 0
    if "--check" in argv:
        ok = JSON_OUT.read_text(encoding="utf-8") == js and MD_OUT.read_text(encoding="utf-8") == md
        print("T-590 check:", "identical" if ok else "DIFFERS")
        return 0 if ok else 1
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
