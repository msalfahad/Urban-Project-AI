"""S8.5 post-freeze comparison: the frozen special-column audit against earlier figures, at equal scope, after the
freeze.

    python3 -I research/alsenan_special_columns_s8_5/post_freeze/post_freeze_comparison.py

Reads the frozen S8.5 package (verified before and after; never written) and the earlier figures:
  * the old Urban V3b register: its column sets for the turned and dead columns' types and storeys, and the absence of
    any planted column or special-column extra;
  * the PRE-S8 census (now including its quantity column) and its rebar coverage rows for the special columns;
  * the freelancer lineage: the R9.1 column crosswalk and the column rows of its quantity reconciliation.
Every difference is classified (NO_DIFFERENCE, LABEL_ONLY, SCOPE, MISSED_OBJECT, OWNERSHIP_CLAIM, STOREY_CONVENTION,
SEGMENTATION, NOT_COMPARABLE) and explained. Nothing here changes a frozen quantity or chooses an interpretation.
"""

from __future__ import annotations

import csv
import io
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
ROOT = PKG.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import delta_release as DR  # noqa: E402

R = ROOT / "research"
V3B = ROOT / "tests/alsenan/registers_v3b/REBAR_POPULATION_REGISTER.json"
PRE_S8 = R / "pre_s8_structural_completeness"
R91 = R / "R9_1_CHRIS_POST_FREEZE"
MANIFEST = PKG / "17_S8_5_FREEZE_MANIFEST.json"
OUT = ["01_POST_FREEZE_COMPARISON.csv", "02_OBJECT_AND_STOREY_CROSSWALK.csv", "03_POST_FREEZE_SUMMARY.json",
       "00_POST_FREEZE_README.md"]
# the turned and dead segments whose ordinary bars V3b also counts (type, storey, bars) -> the S8.5 rows citing S3.1
TYPE_ROWS = {("C8", "GF"): ("TC-31F-01", "TC-31F-03"), ("C9", "GF"): ("TC-324-01", "TC-324-03"),
             ("C11", "GF"): ("DC-01", "DC-02"), ("C8", "1F"): ("TC-31F-02", None), ("C9", "1F"): ("TC-324-02", None)}
CHAINS = {"COLPOS-X15-Y06-31508-15062": "SPC-TURN_COLUMN-GFRS-31F", "COLPOS-X13-Y08-27308-16612":
          "SPC-TURN_COLUMN-GFRS-324", "COLPOS-X06-Y04-14438-12062": "SPC-DEAD_COLUMN-GFRS-38A",
          "COLPOS-X08-Y02-16850-8912": "SPC-PLANTED_COLUMN-GFRS-544", "COLPOS-X15-Y02-31508-8912":
          "SPC-PLANTED_COLUMN-GFRS-548", "COLPOS-X?-Y?-24888-15994": "SPC-PLANTED_COLUMN-FFRS-77C"}


def kg_m(d):
    return d * d / 162.0


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _r(v, nd=6):
    return None if v is None else round(float(v) + 0.0, nd) + 0.0


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        s = f"{v:.9f}".rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return str(v)


def _csv(name, rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in rows[0]})
    (HERE / name).write_text(buf.getvalue(), encoding="utf-8")


def v3b_columns():
    sets = json.loads(V3B.read_text(encoding="utf-8"))["sets"]
    cols = defaultdict(list)
    extras = []
    for s in sets:
        txt = json.dumps(s).lower()
        if "extra" in txt or "spiral" in txt or "planted" in txt:
            extras.append(s.get("ref"))
        if s.get("population") != "COLUMNS":
            continue
        m = re.match(r"(\S+) (\S+) (H\w+) (vertical|ties)$", s["ref"])
        if m:
            cols[(m.group(2), m.group(1), m.group(4))].append(s)
    return cols, extras


def main():
    before = DR.verify_frozen(MANIFEST, ROOT)
    s = json.loads((PKG / "16_S8_5_SUMMARY.json").read_text(encoding="utf-8"))
    comps = {r["COMPONENT_ID"]: r for n in ("04_TWISTED_COLUMN_REINFORCEMENT.csv", "05_PLANTED_COLUMN_REINFORCEMENT.csv",
                                            "06_DEAD_COLUMN_TERMINATION_AUDIT.csv") for r in _rows(PKG / n)}
    sens = {r["CASE_ID"]: r for r in _rows(PKG / "13_SENSITIVITY_CASES.csv")}
    pop = {r["SPECIAL_ID"]: r for r in _rows(PKG / "02_SIX_OCCURRENCE_POPULATION.csv")}
    cols, extras = v3b_columns()
    rows, recon = [], []

    def add(cid, item, scope, s85, s85_state, source, earlier, earlier_state, cls, why):
        rows.append({"CMP_ID": cid, "ITEM": item, "SCOPE": scope, "S8_5_FROZEN_KG": _r(s85), "S8_5_STATE": s85_state,
                     "EARLIER_SOURCE": source, "EARLIER_KG": _r(earlier), "EARLIER_STATE": earlier_state,
                     "DIFFERENCE_KG": None if s85 is None or earlier is None else _r(s85 - earlier),
                     "CLASS": cls, "EXPLANATION": why})

    # ------------------------------------------------------------ V3b ordinary bars of the same types and storeys
    n = 0
    for (typ, fl), (main_row, cont_row) in TYPE_ROWS.items():
        vs = cols[(typ, fl, "vertical")]
        assert vs, (typ, fl)
        own = [v["count"] * v["straight_m"] * kg_m(v["dia_mm"]) for v in vs]
        assert all(abs(o - v["net_kg"]) < 1e-5 for o, v in zip(own, vs)), (typ, fl)   # V3b by its own formula
        assert len({round(o, 6) for o in own}) == 1                                    # every V3b set alike
        frozen = float(comps[main_row]["EXISTING_KG"])
        n += 1
        add(f"CMP-{n:02d}", f"{typ} {fl} ordinary vertical bars", "ORDINARY (S3.1-owned; S8.5 adds nothing)", frozen,
            comps[main_row]["EXISTING_STATE"], f"V3b {', '.join(v['ref'] for v in vs)}", own[0], "tech_kg",
            "NO_DIFFERENCE" if abs(frozen - own[0]) < 5e-4 else "NOT_COMPARABLE",
            f"V3b {vs[0]['count']}Ø{vs[0]['dia_mm']} x {vs[0]['straight_m']} m per set, type level (its handles are not "
            "ST7757 handles); the S3.1 occurrence holds the same bars over the same storey")
        recon.append({"ITEM": f"{typ} {fl} vertical", "V3B_FORMULA": f"{vs[0]['count']} x {vs[0]['straight_m']} x "
                      f"{vs[0]['dia_mm']}^2/162", "V3B_KG": _r(own[0]), "V3B_LAP_KG": _r(vs[0]["lap_kg"]),
                      "S3_1_KG": _r(frozen)})
        if cont_row:
            lap = vs[0]["lap_kg"]
            frozen_c = float(comps[cont_row]["EXISTING_KG"])
            n += 1
            label = cont_row == "DC-02"
            add(f"CMP-{n:02d}", f"{typ} {fl} {'top anchorage (dead column)' if label else 'continuity at the turn'}",
                "ORDINARY (S3.1-owned)", frozen_c, comps[cont_row]["EXISTING_STATE"],
                f"V3b {vs[0]['ref']} lap_kg", lap, "lap 40Ø at the floor splice (outside tech_kg)",
                ("LABEL_ONLY" if label else "NO_DIFFERENCE") if abs(frozen_c - lap) < 5e-4 else "NOT_COMPARABLE",
                "V3b carries a 40Ø 'floor splice' on every column; on the dead column nothing continues, so S3.1 "
                "names the same 0.64 m a top anchorage" if label else
                "the same 40Ø over the bars that continue" + (" (S3.1 splits 12 lapped + 2 stopped bars)"
                                                              if typ == "C9" else ""))
    # ------------------------------------------------------------ the special components
    tc = [comps["TC-31F-05"], comps["TC-324-05"]]
    n += 1
    add(f"CMP-{n:02d}", "turn extras 4Ø16 x 2 m (31F + 324)", "SPECIAL", sum(float(c["EXISTING_KG"]) for c in tc),
        "S3.1 LOWER_BOUND, S8.5 adds 0", "V3b column sets", 0.0, "absent",
        "SCOPE", "V3b's column sets are vertical bars and ties per type; it never models the twisted detail")
    n += 1
    add(f"CMP-{n:02d}", "turn spiral 6Ø8/m over 2 m (31F + 324)", "SPECIAL", None,
        f"BLOCKED (upper bounds {sens['SA-31F-SPI-C']['KG']}-{sens['SA-31F-SPI-E']['KG']} kg per column)",
        "V3b column sets", 0.0, "absent, not registered as blocked", "SCOPE",
        "nothing is released on either side; V3b omits the spiral silently, S8.5 holds it blocked with Q-01")
    pc = ["COL-P.C-X08-Y02-1F", "COL-P.C-X15-Y02-1F", "COL-P.C-X?-Y?@24888-15994-2F"]
    pc_kg = sum(float(c["EXISTING_KG"]) for c in comps.values()
                if c["COLUMN_ID"] in pc and c["KIND"] == "ORDINARY" and c["EXISTING_KG"])
    v3b_pc = [k for k in cols if k[0] in ("P.C", "PC")]
    n += 1
    add(f"CMP-{n:02d}", "planted columns' own bars, anchorages and ties (544 + 548 + 77C)", "ORDINARY (S3.1-owned)",
        pc_kg, "S3.1 (VERIFIED main bars)", "V3b column types", 0.0 if not v3b_pc else None,
        "no P.C type in V3b" if not v3b_pc else "present", "MISSED_OBJECT" if not v3b_pc else "NOT_COMPARABLE",
        "V3b's types are C and C1-C11 only; its generic 'C' sets are GF-only with 8 bars, so the three planted columns "
        "(1F / 1F / 2F) are not in V3b. S3.1 holds them; S8.5 adds nothing")
    n += 1
    add(f"CMP-{n:02d}", "548 beam extra 4Ø16 on B26", "SPECIAL", float(comps["PC-548-08"]["EXISTING_KG"]),
        "S6.1 LOWER_BOUND", "V3b GF B26 H1228 sets", 0.0, "top / bottom / stirrups / side bars only", "SCOPE",
        f"V3b has no planted-column extra on any beam (no 'extra' set at all: {len(extras)})")
    n += 1
    add(f"CMP-{n:02d}", "544 / 77C beam extras", "SPECIAL", None,
        "BLOCKED (host unresolved; sensitivity " + ", ".join(f"{k} {v['KG']}" for k, v in sens.items()
                                                            if "-EXTRA-" in k and not k.startswith("SA-548")) + ")",
        "V3b beam sets", 0.0, "absent", "SCOPE", "nothing is released on either side")
    n += 1
    add(f"CMP-{n:02d}", "planted starters '100' (all three)", "SPECIAL", None,
        "BLOCKED (sensitivity " + ", ".join(f"{k} {v['KG']}" for k, v in sens.items() if k.endswith("STARTER")) + ")",
        "V3b", 0.0, "absent", "SCOPE", "nothing is released on either side")
    # ------------------------------------------------------------ PRE-S8
    census = {r["ELEMENT_ID"]: r for r in _rows(PRE_S8 / "02_STRUCTURAL_ELEMENT_CENSUS.csv")}
    for sid in pop:
        c = census[sid]
        n += 1
        add(f"CMP-{n:02d}", f"{sid}: concrete", "CONCRETE", 0.0, "S8.5 NOT_ADDED / NOT_IN_SOURCE",
            "PRE-S8 census CONCRETE_QUANTITY_STATE", None, c["CONCRETE_QUANTITY_STATE"],
            "NO_DIFFERENCE" if c["CONCRETE_QUANTITY_STATE"].startswith("NOT_MEASURED") else "NOT_COMPARABLE",
            "no special-column concrete in either; the parent columns keep their own concrete owner")
        n += 1
        add(f"CMP-{n:02d}", f"{sid}: ownership claim", "OWNERSHIP", None,
            f"S8.5: {pop[sid]['SPECIAL_ALREADY_OWNED'] or '[]'} already owned; blocked {pop[sid]['MISSING']}",
            "PRE-S8 census EXISTING_STAGE_OWNER / NEW_S8_OWNER", None,
            f"{c['EXISTING_STAGE_OWNER']} -> {c['NEW_S8_OWNER']}", "OWNERSHIP_CLAIM",
            "PRE-S8 assigned to S8 roles that S3.1 / S6.1 already hold (conflicts C-01 to C-03); following it would "
            "count them twice")
    rc = [r for r in _rows(PRE_S8 / "04_REBAR_COVERAGE_MATRIX.csv") if r["FAMILY"] == "SPECIAL_COLUMN"]
    n += 1
    add(f"CMP-{n:02d}", "PRE-S8 rebar coverage of the special columns", "COVERAGE", None,
        f"{len(comps)} roles: {s['lanes']['components']}", "PRE-S8 04_REBAR_COVERAGE_MATRIX",
        None, "; ".join(f"{r['COMPONENT']} {r['STATES']} owners {r['OWNERS']}" for r in rc), "SCOPE",
        "PRE-S8 held each rule as a reference only; S8.5 resolves it role by role")
    # ------------------------------------------------------------ freelancer lineage (objects and storeys)
    xw = _rows(R91 / "09_COLUMN_CROSSWALK.csv")
    obj = []
    for r in xw:
        if r["URBAN_CHAIN"] not in CHAINS:
            continue
        sid = CHAINS[r["URBAN_CHAIN"]]
        cls = {"DONOR_FALSE_POSITIVE": "STOREY_CONVENTION", "SAME_OBJECT_DIFFERENT_SEGMENTATION": "SEGMENTATION",
               "SAME_OBJECT_SAME_RESULT": "NO_DIFFERENCE"}.get(r["DIFFERENCE_CLASS"], "NOT_COMPARABLE")
        obj.append({"CHRIS_ID": r["CHRIS_ID"], "SPECIAL_ID": sid, "URBAN_CHAIN": r["URBAN_CHAIN"],
                    "S8_5_STOREYS": json.loads(pop[sid]["STOREYS"]), "CHRIS_INTERVALS": r["CHRIS_INTERVALS"],
                    "CHRIS_FLAGS": r["CHRIS_FLAGS"], "R9_1_CLASS": r["DIFFERENCE_CLASS"], "CLASS": cls,
                    "EXPLANATION": {
                        "STOREY_CONVENTION": "the freelancer counts a storey when the outline is drawn on its roof "
                                             "plan; a planted column starts on that slab and belongs to the storey "
                                             "above (S8.5 planted_storey, as S1 / S3.1)",
                        "SEGMENTATION": "the turned 1F outline is offset 150 mm from the GF one, beyond the "
                                        "freelancer's 120 mm continuity tolerance, so it splits one chain into a "
                                        "stopped column and a planted one; the T.C circle 31C reaches both outlines, "
                                        "so S8.5 reads one turned chain",
                        "NO_DIFFERENCE": "same object, same storeys"}.get(cls, r["NOTES"])})
    assert sorted({o["SPECIAL_ID"] for o in obj}) == sorted(pop)
    for o in obj:
        n += 1
        add(f"CMP-{n:02d}", f"{o['SPECIAL_ID']} ({o['CHRIS_ID']}): object and storeys", "OBJECT", None,
            f"storeys {o['S8_5_STOREYS']}", "R9.1 09_COLUMN_CROSSWALK", None,
            f"intervals {o['CHRIS_INTERVALS']} ({o['R9_1_CLASS']})", o["CLASS"], o["EXPLANATION"])
    qr = [r for r in _rows(R91 / "15_QUANTITY_RECONCILIATION_UPDATED.csv") if r["ITEM"].startswith("Columns ")]
    for r in qr:
        n += 1
        planted = "planted" in r["POPULATION_DIFF"]
        add(f"CMP-{n:02d}", f"{r['ITEM']} (whole columns, m3)", "WHOLE_COLUMNS (not S8.5 scope)", None,
            "S8.5 adds 0 m3", "R9.1 15_QUANTITY_RECONCILIATION (freelancer, UC4N, QS reference)", None,
            f"population {r['POPULATION_DIFF'] or 'n/a'}", "STOREY_CONVENTION" if planted else "NOT_COMPARABLE",
            "the extra freelancer columns are planted columns also counted in the storey below their slab, and at GF "
            "the second half of the split turned column"
            if planted else "whole-column concrete per storey; the special components add none")
    after = DR.verify_frozen(MANIFEST, ROOT)
    assert before == after

    for o in OUT:
        if (HERE / o).exists():
            (HERE / o).unlink()
    _csv(OUT[0], rows)
    _csv(OUT[1], obj)
    classes = defaultdict(int)
    for r in rows:
        classes[r["CLASS"]] += 1
    summary = {"round": "S8_5_POST_FREEZE", "frozen_manifest_sha256": before["manifest_sha256"],
               "frozen_unchanged": True, "rows": len(rows), "classes": dict(sorted(classes.items())),
               "special_component_kg": {"s8_5_incremental": s["released"]["reinforcement_kg"],
                                        "already_owned_s3_1": _r(sum(float(c["EXISTING_KG"]) for c in tc)),
                                        "already_owned_s6_1": _r(float(comps["PC-548-08"]["EXISTING_KG"])),
                                        "v3b_equal_scope": 0.0, "pre_s8": "no quantity (ownership claim only)",
                                        "freelancer": "objects only (no special-column steel)"},
               "v3b_missed_planted_columns_kg_held_by_s3_1": _r(pc_kg),
               "v3b_type_level_ordinary_bars": recon,
               "freelancer_objects": {o["CHRIS_ID"]: o["CLASS"] for o in obj},
               "rule": "post-freeze only: explains differences, changes no frozen quantity"}
    (HERE / OUT[2]).write_text(json.dumps(summary, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                               encoding="utf-8")
    L = ["# S8.5 post-freeze comparison", "",
         f"Run after the freeze (`{MANIFEST.name}` verified before and after, unchanged). Nothing here changes a frozen "
         "quantity.", "",
         "## Special-column components at equal scope", "",
         f"- S8.5 adds **{_full(s['released']['reinforcement_kg'])} kg** and **0 m3**. The special extras already counted "
         f"are S3.1's 4Ø16 at the two turns ({_full(summary['special_component_kg']['already_owned_s3_1'])} kg) and "
         f"S6.1's 548 beam extra ({_full(summary['special_component_kg']['already_owned_s6_1'])} kg).",
         "- **V3b has none of them** (0 kg): no turn extra, spiral, planted-column extra or starter. That is a SCOPE "
         "difference. V3b's ordinary bars and 40Ø laps for C8 / C9 / C11 equal S3.1's at type level. On the dead "
         "column, V3b calls the 0.64 m a floor-splice lap where S3.1 calls it a top anchorage: same kg, LABEL_ONLY.",
         f"- **V3b has no planted column at all**: MISSED_OBJECT. S3.1 holds their {_full(pc_kg)} kg of ordinary steel.",
         "- **PRE-S8**: no special-column concrete (agrees with S8.5). Its ownership claims would have re-counted "
         "S3.1 / S6.1 roles: OWNERSHIP_CLAIM, corrected by S8.5.",
         "- **Freelancer**: objects only, no special-column steel.",
         "  - It also counts each planted column in the storey below its slab (STOREY_CONVENTION).",
         "  - It splits the 31F turned column into a stopped column and a planted one (SEGMENTATION).",
         "  - C9 / C11 match exactly.",
         "  - Its whole-column counts per storey (33 vs 30 at GF, 21 vs 20 at 1F) are exactly those storey shifts.",
         "", "## Classes", ""] + [f"- {k}: {v}" for k, v in summary["classes"].items()] + [
         "", "## Outputs", ""] + [f"- `{o}`" for o in OUT]
    (HERE / OUT[3]).write_text("\n".join(L) + "\n", encoding="utf-8")
    return summary


def _full(v, nd=6):
    s = f"{float(v):.{nd}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


if __name__ == "__main__":
    print(json.dumps(main(), indent=1, ensure_ascii=False))
