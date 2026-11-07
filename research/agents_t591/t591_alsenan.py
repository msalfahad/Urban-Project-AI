"""T-591: RULE_DIFF provenance audit of the architectural / finishes sections of statement V6 (carried byte-equal in
V7) plus the finishes sections V7 added, on the training villa. Reads the committed V7 statement JSON (sha256-pinned)
and the repository's rule registers; writes out/T591_RULE_DIFF_PROVENANCE.json / .md. No private input, no candidate,
rule, knowledge or registry file touched, nothing released; a reclass is a statement-level label (NONE -> UNRESOLVED),
never a quantity change.

  python3 -I research/agents_t591/t591_alsenan.py --write
  python3 -I research/agents_t591/t591_alsenan.py --check
"""
from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t591_rules as R  # noqa: E402

D = Decimal
ROOT = R.ROOT
V7 = ROOT / "research" / "agents_t587" / "out" / "RECONCILED_STATEMENT_T587.json"
PINS = {
    "research/agents_t587/out/RECONCILED_STATEMENT_T587.json":
        "3cd55327d5d0b960cc8ee5d3b91655a38630af2973533e0d50ca77678bd79745",
    "rules/rulebook/URBAN_COMPANY_RULEBOOK_1.0.0.json":
        "4e9c57cef33d32ede26bea4eaf3823e2dc3880d56708dd18ec5df3760b84c055",
    "rules/coverage/BOQ_FAMILY_MASTER_1.55.0.json": "22cb3ffc2a747ad3992508717c0840f926def6885f695d8de6e53700821d8c99",
    "research/agents_t175/T175_OPENING_HOSTS.csv": "d96cfbce9c732db50b7737038b374cab6fc91d5325cc36182416dd0dc35ac3e9",
    "research/agents_t296/DEDUCTIONS_BY_OPENING_T296.csv":
        "be797b612f96dd2482c13aa0261aa1bf470abb4046ca0e5f1ee5657af9ec6074",
}
# F-T591-1 condition check (URBAN-SKIRTING-OPENING-METHOD DOORLESS_OPENING) for every doorless opening the skirting
# table deducts, from the committed drawing-derived records (T-175 hosts: kind, wall thickness, sides; T-296: the
# skirting line that deducts it). Jamb lm = 2 jambs x wall thickness. Never 0 for an unknown depth.
DOORLESS = [
    {"opening": "A-1F-01 / 1F OP-011", "line_t296": "L-a8aea28451168e4032b6", "wall_t_m": "0.15",
     "sides": "1F bed room 380 x 430 | dressing passage (both dry)",
     "conditions": "no door (census kind OPENING, arch); real masonry jamb 0.15; both sides skirting-eligible dry "
                   "rooms; floor porcelain continues through (UP-THR-001 dry strip); not a full-tile room",
     "status": "CONDITIONS_MET", "jamb_lm": "0.30", "statement_row": "T-574/skirting-room row 29",
     "verdict_proposal": "ENGINE_WRONG 0.30 lm (his 2 x 0.15 agrees with the owner method)"},
    {"opening": "A-GF-01 / GF OP-027", "line_t296": "L-d32414916cfbd04c27be", "wall_t_m": "0.15",
     "sides": "dewaneya | wash by the dewaneya (wet, Q-06 A)",
     "conditions": "the floor at the jambs is the wet doorway's marble threshold (UP-THR-001 wet), not the dry floor "
                   "finish: 'the floor finish reaches the jamb' fails (register: a marble-threshold opening into a "
                   "full-tile wet space takes no skirting)",
     "status": "NOT_APPLICABLE", "jamb_lm": "0", "statement_row": "none (his gross row has no jambs either)",
     "verdict_proposal": "none"},
    {"opening": "P-GF-01 / GF OP-020", "line_t296": "(T-443 stair hall child)", "wall_t_m": "0.20",
     "sides": "GF stair hall doorless 0.90 opening with head lines",
     "conditions": "doorless with a real head; already the candidate's HELD line SKIRT-T443:GF-ST-HALL:OP-020-JAMBS",
     "status": "HELD_LINE_EXISTS", "jamb_lm": "0.40 (held, its own cause)", "statement_row": "none",
     "verdict_proposal": "none (carried by its HELD line)"},
    {"opening": "P-GF-04 / GF OP-003 11.22", "line_t296": "L-71e2e002a3af624097f0 / L-af6fb2d3474c5fbdb80a",
     "wall_t_m": "none", "sides": "open side along the side passage (Q-67)",
     "conditions": "an open side in no wall run, not an opening in a wall: the opening method does not apply",
     "status": "NOT_AN_OPENING", "jamb_lm": "0", "statement_row": "T-574/skirting-room row 1",
     "verdict_proposal": "none"},
    {"opening": "GF OP-011 (no census id)", "line_t296": "L-71e2e002a3af624097f0", "wall_t_m": "not established",
     "sides": "GF open room", "conditions": "no host record (T-175): door / doorless and jamb depth not established",
     "status": "HELD", "jamb_lm": "HELD (2 x wall thickness, never 0)", "statement_row": "T-574/skirting-room row 1",
     "verdict_proposal": "UNRESOLVED until the opening is read"},
    {"opening": "1F OP-007 (no census id)", "line_t296": "L-ba3599ec2dc82c221617", "wall_t_m": "not established",
     "sides": "1F living / open stair hall", "conditions": "no host record (T-175): jamb depth not established",
     "status": "HELD", "jamb_lm": "HELD (2 x wall thickness, never 0)", "statement_row": "T-574/skirting-room row 19",
     "verdict_proposal": "UNRESOLVED until the opening is read"},
]
# docs/RULES_INDEX.md and data/registry/URBAN_OWNER_METHOD_RULES.json are read live (they grow with every rule
# version): an outcome changes only if a cited rule disappears or is deprecated, which the rebuild test then reports.
OUT = HERE / "out"
JSON_OUT = OUT / "T591_RULE_DIFF_PROVENANCE.json"
MD_OUT = OUT / "T591_RULE_DIFF_PROVENANCE.md"
STRUCTURAL = ("B10", "B11", "B1 ")          # T-590's scope (lane S); everything else in the statement is ours
LEVELS = ("sections", "sections_v5", "sections_v6", "sections_v7")

# ----------------------------------------------------------------------------------- the audited provenance ----
Q73 = {"Q-73": "Q-73 / UPC-BLOCK-OPENINGS-001 govern BLOCKWORK deductions; a plaster / paint face deduction is "
               "UP-OPEN-SCHED-001 (the opening's own length x its band) under UP-GEN-003"}
Q29 = {"Q-29": "skylight reading = scenario S1 only (owner 2026-10-22: approved design keeps the concrete domes); the "
               "deduction rests on Q-24 (membrane stops at the dome base, 0.20 m upturn round it) in either scenario"}
Q53 = {"Q-53": "Q-53 is the stair-bed mortar mix; it does not set a landing size"}
DOOR_H = ["Q-55", "UP-DOOR-HGT-001", "UP-DOOR-AREA-001"]
BLOCK_OPEN = ["UPC-BLOCK-OPENINGS-001", "Q-73"]
SKIRT_DOOR = ["UP-CER-003", "URBAN-SKIRTING-OPENING-METHOD", "UP-SKIRT-001"]
SKIRT_PASS = ["URBAN-SKIRTING-OPENING-METHOD", "UP-SKIRT-001"]
FIN_OPEN = ["UP-OPEN-SCHED-001", "UP-GEN-003"]
HIS_DOOR_H = "every door in his opening list at a flat 2.40 m height"
HIS_SKIRT = "his room perimeter rows are gross outlines with no opening deducted (tiles sheet C13..C29)"
HIS_FIN_OPEN = "he deducts half of his own opening list at his net step (owner Sigma item 1: a freelancer practice)"
HIS_TILE_H = "one flat tile height per room on his ceramic sheet, not tied to the decor-ceiling underside"
HIS_PAINT_H = "one flat paint height per storey (3.60 GF, 3.40 1F / 2F)"

A: dict[tuple[str, int], dict] = {}


def put(sec: str, rows, traced, his, miscited=None, flag=None, contrary=None):
    for i in rows:
        A[(sec, i)] = {"traced": list(traced), "his": his, "miscited": miscited or {}, "flag": flag,
                       "contrary": contrary}


put("T-541/membrane", [1], ["Q-24"], "his roof membrane row takes the +13.90 roof with the third dome footprint inside",
    Q29, flag="engine side NONE: the 2F top roof is HELD (Q-34 deferred); the dome footprint is a component only")
put("T-541/membrane", [2], ["Q-24"], "his roof membrane row keeps both +9.70 dome footprints inside the area", Q29)
put("T-541/upturn", [1], ["Q-24"], "his upturn row has no ring round the +9.70 domes")
put("T-534/stair-bed", [0], ["Q-66", "UP-STAIR-005"], "his T-086-era figure keeps the 1F arrival out of the stair bed")
put("T-534/stair-bed", [7], ["UP-STAIR-002", "UP-STAIR-005"],
    "he counts the top E1 step as a tread and carries no entrance landing")
put("T-534/stair-bed", [12], ["UP-STAIR-002"], "the reference figure's own landing size 1.20 x 1.25", Q53,
    flag="CLASS QUESTIONED: a size difference against the drawn 1.25 x 1.15, not a convention (Checker to class)")
put("T-534/stair-bed", [24, 25], ["Q-50", "UP-STAIR-002"], "his figure predates the Q-50 A reconstruction scope")
put("T-543/blockwork", [8, 68], ["Q-60", "UP-MAS-HEIGHT-001"],
    "one flat storey height per storey (GF 3.838211 m, 1F 3.668934 m) on every wall")
put("T-543/blockwork", [11, 24, 28, 43, 45, 47, 48, 50], DOOR_H + BLOCK_OPEN, HIS_DOOR_H)
put("T-543/blockwork", [33], ["UP-DOOR-OPEN-003", "UP-DOOR-AREA-001"] + BLOCK_OPEN,
    "1.10 m wide = the owner wall-opening minimum, not the drawn 1.000 m")
put("T-543/blockwork", [76], ["FAMILY:EXT.FENCE.WALL"], "his 15 cm boundary wall sits in his blockwork section",
    flag="PLACEMENT, not a convention: the same wall is compared under the fence family (no quantity convention)")
put("T-546/floor", [1], ["UP-WP-003", "UP-WP-DOOR-001"],
    "his room 1.55 x 1.10 takes the 0.20 m passage reveal into the room floor")
put("T-546/floor", [17], ["Q-37", "UP-WET-001"], "he keeps the pantry in his dry reception row (no wet floor)")
put("T-546/upturn", [2, 6, 26], ["Q-35", "UP-WP-003"], "his upturn runs the full boundary, open edges included")
put("T-546/upturn", [7], ["UP-WP-003", "Q-35"], "his perimeter takes the two 0.20 m reveal returns (2 x 0.20)",
    flag="the reveal jamb faces belong to the passage termination (UP-WP-003 PASSAGE clause), not the wall upturn")
put("T-547/wall-tile", [1, 4, 9, 13, 17, 22, 26, 30, 34, 38, 43], ["Q-48", "UP-CER-009"], HIS_TILE_H)
put("T-547/wall-tile", [46], ["Q-37", "UP-PANTRY-003"], "he keeps the pantry in his dry reception row (no wall tile)")
put("T-552/plaster-internal", [5, 11, 14, 26], FIN_OPEN, HIS_FIN_OPEN, Q73)
put("T-552/plaster-internal", [31], ["Q-06", "UP-WET-001", "UPC-WETWALL-001"],
    "the GF-02 wash space sits in his dry plaster rows (6.75 x 3.60)")
put("T-552/plaster-external", [3], ["OWNER_FILE:OWNER_NOTES_SIGMA_2026-10-21#item 3"],
    "his row 72: domes inside and outside 6 x 3.14 x 9.65 in the render", flag="project-specific (owner item 3)")
put("T-552/plaster-external", [4], ["OWNER_FILE:OWNER_NOTES_SIGMA_2026-10-21#item 4", "Q-68"],
    "his row 73: the pool-court soffit inside the external render", flag="PLACEMENT: owned by the FIN.CEILING line")
put("T-553/floor-tile", [0], ["UP-CER-001", "UP-STAIR-005"],
    "his reception / dining / entrance rows take the round-stair footprint as floor tile")
put("T-553/floor-tile", [1, 12, 21], ["UP-ELEV-005"], "his room rows run through the lift landing threshold")
put("T-553/floor-tile", [10, 18, 23], ["UP-THR-001"], "he measures rooms to the wall face: no doorway strip")
put("T-553/floor-tile", [11], ["Q-66", "UP-STAIR-005"], "his 1F living rows take the main-stair arrival as tile")
put("T-553/floor-tile", [20], ["Q-70", "UP-STAIR-005"], "his 2F 'corridor' row takes the main-stair arrival as tile")
put("T-553/floor-tile", [25], ["UP-THR-001", "Q-06"], "his room takes the 0.20 m passage reveal into the floor")
put("T-561/paint-internal", [5, 11, 14, 26], FIN_OPEN, HIS_FIN_OPEN, Q73)
put("T-561/paint-internal", [6, 12, 15, 27], ["UPC-HEIGHT-001", "Q-48", "UP-HGT-001"], HIS_PAINT_H)
put("T-561/paint-internal", [31], ["UP-FIN-PAINT-001", "Q-06", "UPC-WETWALL-001"],
    "the GF-02 wash space in his paint rows (he also tiles it, ceramic row 51)")
put("T-568/alu-doors-m2", [0, 1, 3, 5, 6], DOOR_H, HIS_DOOR_H)
put("T-568/internal-doors-m2", [1, 3, 4, 6, 8, 9, 11, 12, 13, 14, 15, 17, 18], DOOR_H, HIS_DOOR_H)
put("T-568/internal-doors-m2", [7], ["UP-DOOR-OPEN-003", "UP-DOOR-AREA-001"],
    "1.10 m wide = the owner wall-opening minimum, not the drawn 1.000 m")
put("T-573/ceiling-paint", [5], ["Q-57", "UP-CEIL-001"], "cove-light strips 0.10 m x room perimeters, no detail drawn")
put("T-571/lintel-count-implied", [0, 1], ["UPC-LINTEL-001"],
    "his opening width through the owner rule gives the same stock length (0 net)")
put("T-574/skirting-room", [0, 10, 13, 17, 18, 24, 27, 28, 30, 32, 35, 38], SKIRT_DOOR, HIS_SKIRT)
put("T-574/skirting-room", [1, 7, 19], SKIRT_PASS, HIS_SKIRT)
put("T-574/skirting-room", [21], ["UP-STAIR-004", "REGISTER:STAIR SKIRTING vs ROOM SKIRTING"],
    "his 1F living perimeter runs along W13 1.20 + W25 1.00, faces the stair owns")
put("T-574/skirting-room", [29], [],
    "his outline adds the two 0.15 m jamb returns of the doorless arch (2 x 0.15 = 0.30 lm)",
    contrary="URBAN-SKIRTING-OPENING-METHOD DOORLESS_OPENING real_floor_side_jambs INCLUDED (conditions: no door, real "
             "jamb, eligible side, floor reaches it, not a full-tile room) and UP-SKIRT-001 1.4.0 doorless_opening_jambs "
             "included; the row's R-T443-1 says 'door jambs never', which does not cover a doorless arch",
    flag="candidate ENGINE_WRONG 0.30 lm if the Checker confirms the arch jambs meet the method's conditions")
put("T-574/skirting-room", [37], ["UP-CER-003", "UP-DOOR-CLS-005", "URBAN-SKIRTING-OPENING-METHOD"], HIS_SKIRT)
put("T-574/skirting-room", [39], SKIRT_PASS, "his 2F corridor perimeter runs along the flight-top slab edge (no floor)")
put("T-574/skirting-pieces", [0, 1, 2], ["UP-STAIR-004"], "stair-side skirting counted as pieces per step (nr)")
for s in ("T-577/marble-m2", "T-577/marble-lm", "T-577/marble-nr", "T-577/marble-lm@V7"):
    put(s, [1], ["UP-THR-001"], "NO_ROW: none of his 885 rows names a doorway strip; may sit in his room floor rows",
        flag="CLASS QUESTIONED: his side has no row (R-T586-1 (a) NO_ROW); Checker to class NOT_COMPARABLE or keep")
for s, i in (("T-577/marble-lm", 11), ("T-577/marble-lm@V7", 11), ("T-577/marble-nr", 5)):
    put(s, [i], ["UP-STAIR-002", "UP-STAIR-005"], "his fifth E1 step x 2.80 = the top step to the landing")
put("T-584/stair-steps-lm", [2, 6], ["UP-STAIR-008", "UP-STAIR-004"],
    "one piece per riser, the arrival edge included")
put("T-584/stair-steps-nr", [1, 4], ["UP-STAIR-008", "UP-STAIR-004"], "arrival edges counted as pieces")

SUPERSEDED = {"T-577/marble-lm": "T-577/marble-lm@V7"}     # supersedes_v7; both audited, the old one marked


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_pins() -> None:
    for rel, h in PINS.items():
        if sha(ROOT / rel) != h:
            raise R.ProvenanceError(f"{rel}: sha256 differs from its pin (rebuild the audit on the new input)")


def finishes_sections(st: dict):
    for lvl in LEVELS:
        for s in st[lvl]:
            if str(s.get("trade", "")).startswith(STRUCTURAL):
                continue
            yield lvl, s


def build() -> dict:
    check_pins()
    st = json.loads(V7.read_text(encoding="utf-8"))
    if st["supersedes_v7"].get("T-577/marble-lm") != SUPERSEDED["T-577/marble-lm"]:
        raise R.ProvenanceError("V7 supersession of T-577/marble-lm changed")
    reg = R.Registers()
    rows_out, used, sections_out, unit_items, unit_items_live = [], set(), [], [], []
    for lvl, s in finishes_sections(st):
        recs = {}
        for i, r in enumerate(s.get("rows", [])):
            if r.get("class") != "RULE_DIFFERENCE":
                continue
            key = (s["section_id"], i)
            if key not in A:
                raise R.ProvenanceError(f"{key}: RULE_DIFFERENCE row with no audit entry")
            a = A[key]
            used.add(key)
            rec = R.classify(reg, r, a["traced"], a["his"], a["miscited"])
            recs[i] = rec
            live = s["section_id"] not in SUPERSEDED
            row = {"level": lvl, "section_id": s["section_id"], "row": i, "unit": s["unit"], "delta": str(r["delta"]),
                   "name": r.get("name", ""), "our_side": rec["sources"], "cited_in_row": rec["cited_in_row"],
                   "cited_not_governing": rec["cited_not_governing"], "his_side": rec["his_convention"],
                   "outcome": rec["outcome"], "provisional": rec["provisional"], "class_after": rec["class_after"],
                   "flag": a["flag"], "contrary_rule": a["contrary"],
                   "live": live, "superseded_by": SUPERSEDED.get(s["section_id"])}
            rows_out.append(row)
            unit_items.append((s["unit"], rec["outcome"], D(str(r["delta"]))))
            if live:
                unit_items_live.append((s["unit"], rec["outcome"], D(str(r["delta"]))))
        if recs:
            moved = R.reclass_section(s["rows"], recs)
            total = sum((D(str(x["delta"])) for x in s["rows"]), D(0))
            if "difference" in s and total != D(str(s["difference"])):
                raise R.ProvenanceError(f"{s['section_id']}: rows do not close to the statement difference")
            sections_out.append({"level": lvl, "section_id": s["section_id"], "unit": s["unit"],
                                 "rd_rows": len(recs),
                                 "difference": str(sum((D(str(x["delta"])) for x in s["rows"]), D(0))),
                                 "by_class_before": {k: str(v) for k, v in sorted(moved["before"].items())},
                                 "by_class_after": {k: str(v) for k, v in sorted(moved["after"].items())}})
    missing = set(A) - used
    if missing:
        raise R.ProvenanceError(f"audit entries with no RULE_DIFFERENCE row: {sorted(missing)}")

    def tab(items):
        return {u: {o: {"n": b["n"], "signed": str(b["signed"]), "gross": str(b["gross"])} for o, b in sorted(v.items())}
                for u, v in sorted(R.per_unit(items).items())}
    counts = {}
    for r in rows_out:
        if r["live"]:
            counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
    return {
        "schema": "URBAN_T591_RULE_DIFF_PROVENANCE_V1",
        "rule": "R-T591-1",
        "input": "statement V7 (T-587; V6 byte-equal inside it) finishes sections; structural B1 / B10 / B11 = T-590",
        "pins": PINS,
        "q_register_snapshot": "OWNER_QUESTIONS.md index, agents/control @189683b3 (2026-11-07T08:40Z): answered Q-01..Q-78 "
                               "(not a rule: Q-23, Q-34, Q-36; scenario only: Q-29 S1), open Q-80, withdrawn Q-79",
        "rows_audited": len(rows_out),
        "rows_live": sum(1 for r in rows_out if r["live"]),
        "outcome_counts_live": dict(sorted(counts.items())),
        "per_unit_live": tab(unit_items_live),
        "per_unit_all_incl_superseded": tab(unit_items),
        "sections": sections_out,
        "rows": rows_out,
        "doorless_jamb_check": DOORLESS,
        "released_quantities_changed": 0,
    }


def to_markdown(o: dict) -> str:
    L = ["# T-591 RULE_DIFF provenance, architectural and finishes (generated)", "",
         f"Input: {o['input']}. Rule R-T591-1. Rows audited {o['rows_audited']} (live {o['rows_live']}; the V6 "
         "T-577/marble-lm rows are superseded by T-577/marble-lm@V7 and audited beside). No % anywhere; units apart.",
         "", "## Outcome per unit (live rows; signed = reference - engine, gross = sum of |delta|)", "",
         "| Unit | Outcome | Rows | Signed | Gross |", "|---|---|---|---|---|"]
    for u, v in o["per_unit_live"].items():
        for oc, b in v.items():
            L.append(f"| {u} | {oc} | {b['n']} | {b['signed']} | {b['gross']} |")
    L += ["", "## Reclassed NONE -> UNRESOLVED (delta unchanged, never 0)", ""]
    for r in o["rows"]:
        if r["outcome"] == "NONE":
            L.append(f"- {r['section_id']} row {r['row']} ({r['unit']} {r['delta']}): {r['name'][:160]}. His side: "
                     f"{r['his_side']}. Contrary rule: {r['contrary_rule']}. {r['flag'] or ''}")
    L += ["", "## Citation corrections (SOURCED_RECITE: the source exists, the row cites none or the wrong one)", "",
          "| Section | Rows | Unit | Delta sum | Our source (traced) | Not governing as cited |", "|---|---|---|---|---|---|"]
    groups: dict = {}
    for r in o["rows"]:
        if r["outcome"] != "SOURCED_RECITE" or not r["live"]:
            continue
        k = (r["section_id"], tuple(s["source"] for s in r["our_side"]), tuple(sorted(r["cited_not_governing"])))
        g = groups.setdefault(k, {"rows": [], "unit": r["unit"], "sum": D(0)})
        g["rows"].append(str(r["row"]))
        g["sum"] += D(r["delta"])
    for (sec, srcs, bad), g in groups.items():
        L.append(f"| {sec} | {', '.join(g['rows'])} | {g['unit']} | {g['sum']} | {', '.join(srcs)} | "
                 f"{', '.join(bad) or '-'} |")
    L += ["", "## Flags for the Lead / Checker (no number moved here)", ""]
    seen = set()
    for r in o["rows"]:
        if r["flag"] and r["live"] and (r["section_id"], r["flag"]) not in seen:
            seen.add((r["section_id"], r["flag"]))
            L.append(f"- {r['section_id']} row {r['row']}: {r['flag']}")
    L += ["", "## F-T591-1: doorless-opening jamb skirting, condition check (committed T-175 / T-296 records)", "",
          "| Opening | Wall t (m) | Status | Jamb lm | Statement row | Proposal |", "|---|---|---|---|---|---|"]
    for d in o["doorless_jamb_check"]:
        L.append(f"| {d['opening']} | {d['wall_t_m']} | {d['status']} | {d['jamb_lm']} | {d['statement_row']} | "
                 f"{d['verdict_proposal']} |")
    L += ["", "## Sections: classes before / after (difference unchanged)", "",
          "| Section | Unit | RD rows | Difference | RULE_DIFFERENCE before | after | UNRESOLVED after |",
          "|---|---|---|---|---|---|---|"]
    for s in o["sections"]:
        b, a = s["by_class_before"], s["by_class_after"]
        L.append(f"| {s['section_id']} | {s['unit']} | {s['rd_rows']} | {s['difference']} | "
                 f"{b.get('RULE_DIFFERENCE', '0')} | {a.get('RULE_DIFFERENCE', '0')} | {a.get('UNRESOLVED', '0')} |")
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
        print("T-591 check:", "identical" if ok else "DIFFERS")
        return 0 if ok else 1
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
