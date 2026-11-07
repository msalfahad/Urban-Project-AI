"""T-601: DOORLESS OPENING JAMB census of the training villa (Alsenan) on every storey plan, by R-T601-1.

Reads only T601_DRAWN.json (the drawing read, handles and figures, sha256-pinned) and committed records named per row
(T-175 opening hosts, T-296 deductions by opening, T-574 skirting groups, T-443 / T-441 stair-hall lines, Q-06 A); writes
out/T601_DOORLESS_CENSUS.json / .md. No candidate, engine, rule, knowledge or registry file touched, nothing released.

  python3 -I research/agents_t601/t601_alsenan.py --write
  python3 -I research/agents_t601/t601_alsenan.py --check
"""
from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t601_rules as R  # noqa: E402

D = Decimal
DRAWN = HERE / "T601_DRAWN.json"
OUT = HERE / "out"
JSON_OUT = OUT / "T601_DOORLESS_CENSUS.json"
MD_OUT = OUT / "T601_DOORLESS_CENSUS.md"
PINS = {
    "research/agents_t601/T601_DRAWN.json": None,  # filled from PIN_DRAWN below
    "research/agents_t175/T175_OPENING_HOSTS.csv": "d96cfbce9c732db50b7737038b374cab6fc91d5325cc36182416dd0dc35ac3e9",
    "research/agents_t296/DEDUCTIONS_BY_OPENING_T296.csv":
        "be797b612f96dd2482c13aa0261aa1bf470abb4046ca0e5f1ee5657af9ec6074",
}
CANDIDATE_SKIRTING_RELEASED_LM = D("209.428592")   # FIN.SKIRTING on V3.0.58 (T-574 section 1)

# Binding of each wall gap the census found WITHOUT a leaf / window, plus the framed (lift) gaps, to its record id and its
# two sides (plan reading this run + the named records). Key = the jamb face handles of the gap (T601_DRAWN.json).
BIND = {
    ("GF", "127|128|12A|12B"): {
        "opening": "A-GF-01 (engine GF OP-027)", "sides": ["DRY", "WET"],
        "side_names": "dewaneya | hand-wash space by the dewaneya (Q-06 A wet)",
        "treatment": "DEDUCTED", "line": "L-d32414916cfbd04c27be (T-296: OP-027 1.000 deducted)",
        "his": "his dewaneya row 20.00 is a gross outline with no jamb term (T-574 / T-591)", "his_lm": "0"},
    ("GF", "215|21A|21C"): {
        "opening": "P-GF-01 (engine GF OP-020)", "sides": ["DRY", "WET"],
        "side_names": "GF stair hall | hand-wash space (Q-06 A wet; T-441 RFI b 'tile return or skirting')",
        "treatment": "DEDUCTED",
        "line": "SKIRT-T443:GF-ST-HALL (6.550 - OP-010 1.000 - OP-020 0.900) + HELD SKIRT-T443:GF-ST-HALL:OP-020-JAMBS",
        "his": "his stair-hall skirting sits in his unsplit ST-01 marble row 23.10 (T-574): not comparable", "his_lm": None},
    ("GF", "120|15A"): {
        "opening": "P-GF-05 (engine GF OP-007, T-175 'open side')", "sides": ["OUTDOOR", "OUTDOOR"],
        "side_names": "court +0.15 under the canopy | open service passage between two blocks (open at its far end)",
        "treatment": "NO_LINE", "line": "none (no room skirting line on either side)",
        "his": "inside his yard skirting 81.32 lm (scope UNRESOLVED, T-574 section 4)", "his_lm": None},
    ("1F", "AD0|AD1|AD4|AD5"): {
        "opening": "A-1F-01 (engine 1F OP-011)", "sides": ["DRY", "DRY"],
        "side_names": "1F bed room 380 x 430 | dressing 165 x 180 (both dry, porcelain continues: T-175 / T-296 records)",
        "treatment": "DEDUCTED",
        "line": "L-a8aea28451168e4032b6 and L-4a85470b3a822d6fb7bb (each deducts the arch 1.00, T-574 group 'bed room 2')",
        "his": "his outline adds 2 x 0.15 arch returns (21.40, T-218 / T-574)", "his_lm": "0.30"},
    ("1F", "C09|C0A|C0B"): {
        "opening": "P-1F-01 (engine 1F OP-009)", "sides": ["DRY", "DRY"],
        "side_names": "1F curved east bed room | its lobby (one skirting cell: T-574 group 'with its lobby')",
        "treatment": "IN_CELL",
        "line": "L-309f118f6fce78b6c28e (T-296 lists no OP-009 deduction on it; doors OP-006 0.90 + OP-018 0.80 are "
                "the lobby's)",
        "his": "his 'bed room 1' 22.89 vs drawn outline 22.15067: -0.73933 UNRESOLVED (T-218), not a jamb cause",
        "his_lm": None},
}
FRAMED = {
    ("GF", "20D|20E|21D|21E"): "L-GF-01 lift landing door (engine GF OP-011; T-296 kind PASSAGE on L-71e2e002a3af624097f0)",
    ("1F", "AFD|AFE|B19|B1A"): "L-1F-01 lift landing door (engine 1F OP-007; T-296 kind PASSAGE on L-ba3599ec2dc82c221617)",
    ("2F", "1289|128A|129B|129C"): "L-2F-01 lift landing door (engine 2F OP-002; already a lift in T-443)",
}
NOT_OPENING = {
    ("GF", "103|111|85"): "1.40 junction at the service passage's outer end (T-175 P-GF-02 'open side'): a cross-wall "
                          "face (handle A3) stands inside the strip",
    ("GF", "14F|336|337"): "13.27 alignment of two collinear wall pieces across the house: crossed by four wall faces",
}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def key(st, row):
    return (st, "|".join(row["jamb_face_handles"]))


def build():
    drawn = json.loads(DRAWN.read_text(encoding="utf-8"))
    census, results, counts = [], [], {}
    for st in ("GF", "1F", "2F"):
        sv = drawn["storeys"][st]
        for row in sv["gaps"]:
            k = key(st, row)
            kind = R.kind_of(row["evidence"])
            counts[(st, kind)] = counts.get((st, kind), 0) + 1
            if kind not in ("DOORLESS", "FRAMED", "NOT_AN_OPENING"):
                continue
            b = BIND.get(k)
            if kind == "DOORLESS" and b is None:
                raise R.CensusError(f"unbound doorless gap {k}")
            op = {"evidence": row["evidence"], "ends": row["ends"], "wall_t_m": str(row["wall_t_m"]),
                  "sides": (b or {}).get("sides", [None, None]), "treatment": (b or {}).get("treatment")}
            r = R.classify(op)
            name = (b or {}).get("opening") or FRAMED.get(k) or NOT_OPENING.get(k) or "unbound"
            if kind != "DOORLESS" and name == "unbound":
                raise R.CensusError(f"unbound {kind} gap {k}")
            census.append({"storey": st, "opening": name, "jamb_face_handles": row["jamb_face_handles"],
                           "width_m": str(row["width_m"]), "wall_t_m": str(row["wall_t_m"]), "ends": row["ends"],
                           "evidence": row["evidence"], "evidence_ids": {x: v for x, v in row["ids"].items()
                                                                        if x != "crossing_lines"},
                           "sides": op["sides"], "side_names": (b or {}).get("side_names"),
                           "engine_line": (b or {}).get("line"), "his": (b or {}).get("his"),
                           "his_lm": (b or {}).get("his_lm"), **{x: r[x] for x in ("kind", "status", "jamb_lm",
                                                                                   "bound_lm", "fix_lm", "why")}})
            results.append((name, r))
        for c in sv["curved_gaps"]:
            counts[(st, "CURVED_" + ("WINDOW" if "GLAZING" in c["evidence"] else "UNREAD"))] = \
                counts.get((st, "CURVED_" + ("WINDOW" if "GLAZING" in c["evidence"] else "UNREAD")), 0) + 1
        doors = set(sv["door_inserts_on_plan"])
        hit = {h for row in sv["gaps"] for h in row["ids"].get("door_inserts", [])}
        counts[(st, "DOOR_INSERTS_NOT_IN_A_GAP")] = sorted(doors - hit)
    fix, held = R.tally(results)
    fixes = [{"id": "FR-T601-1", "line": "L-a8aea28451168e4032b6 / L-4a85470b3a822d6fb7bb (or one new jamb line)",
              "change": "+0.30 lm FIN.SKIRTING: A-1F-01 two real 0.15 jambs (DXF faces AD0 / AD1 / AD4 / AD5, arch120 "
                        "BEC), both sides dry", "effect_lm": "0.30",
              "after": str(CANDIDATE_SKIRTING_RELEASED_LM + fix)},
             {"id": "FR-T601-2", "line": "SKIRT-T443:GF-ST-HALL:OP-020-JAMBS (HELD, blank, 0.400 beside)",
              "change": "HELD -> NOT_APPLICABLE by Q-06 A (the wash side is a basin-only wet space: marble threshold, "
                        "full-height tile): the same class as A-GF-01 (T-591 NOT_APPLICABLE); RFI b stays for the "
                        "reveal's wall finish (B4 / B5), not for skirting", "effect_lm": "0 valued (held 0.40 removed)"},
             {"id": "FR-T601-3", "line": "statement labels T-574 GF open room and 1F living rows; T-296 kind of GF "
                                         "OP-011 / 1F OP-007",
              "change": "relabel 'open passage' -> 'lift landing door (LIFT DOOR GAP register)': deduction 1.00 each "
                        "stands, no jamb skirting; T-591 HELD-by-name for both is closed", "effect_lm": "0"}]
    data = {"schema": "T601_DOORLESS_CENSUS_V1", "rule": R.RULE_ID, "governing": R.GOVERNING,
            "pins": {"research/agents_t601/T601_DRAWN.json": sha(DRAWN),
                     **{p: h for p, h in PINS.items() if h}},
            "gap_counts": {f"{a}:{b}": v for (a, b), v in sorted(counts.items())},
            "census": census, "fix_rows": fixes, "valued_fix_lm": str(fix), "held_by_name": held,
            "candidate_fin_skirting_released_lm": str(CANDIDATE_SKIRTING_RELEASED_LM),
            "after_fix_rows_lm": str(CANDIDATE_SKIRTING_RELEASED_LM + fix)}
    return data


def md(data):
    L = ["# T-601 doorless opening jamb census (generated; R-T601-1)", "",
         f"Valued fix: +{data['valued_fix_lm']} lm FIN.SKIRTING ({data['candidate_fin_skirting_released_lm']} -> "
         f"{data['after_fix_rows_lm']} lm). Held by name: {', '.join(data['held_by_name']) or 'none'}.", "",
         "| Storey | Opening | Width | Wall | Ends | Evidence | Sides | Kind | Status | Jamb lm | Bound | His |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in data["census"]:
        L.append(f"| {c['storey']} | {c['opening']} | {c['width_m']} | {c['wall_t_m']} | {' / '.join(c['ends'])} | "
                 f"{', '.join(c['evidence']) or 'none'} | {' / '.join(s or '?' for s in c['sides'])} | {c['kind']} | "
                 f"{c['status']} | {c['jamb_lm'] or '-'} | {c['bound_lm'] or '-'} | {c['his_lm'] or '-'} |")
    L += ["", "Gap counts: " + "; ".join(f"{k} {v}" for k, v in data["gap_counts"].items()), "", "Fix rows:"]
    L += [f"- {f['id']}: {f['line']}: {f['change']} ({f['effect_lm']})" for f in data["fix_rows"]]
    return "\n".join(L) + "\n"


def main(argv):
    data = build()
    js = json.dumps(data, indent=1, sort_keys=True) + "\n"
    mdt = md(data)
    if "--write" in argv:
        OUT.mkdir(exist_ok=True)
        JSON_OUT.write_text(js, encoding="utf-8")
        MD_OUT.write_text(mdt, encoding="utf-8")
        print("wrote", JSON_OUT.relative_to(ROOT), MD_OUT.relative_to(ROOT))
        return 0
    ok = JSON_OUT.read_text(encoding="utf-8") == js and MD_OUT.read_text(encoding="utf-8") == mdt
    for p, h in PINS.items():
        if h and sha(ROOT / p) != h:
            print("pin differs:", p)
            ok = False
    print("byte-identical:", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
