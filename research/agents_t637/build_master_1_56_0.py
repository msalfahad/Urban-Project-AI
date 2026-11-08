"""T-637: build rules/coverage/BOQ_FAMILY_MASTER_1.56.0.json = 1.55.0 (T-507; never edited) + the three T-630 findings.

R-T637-1 (every villa: the registry; classification of existing lines only, no quantity, capability or owner change):
  (a) EVERY LIVE ITEM CODE HAS ONE FAMILY. The overlay codes no family owned (T-630 F-T630-1) are given one:
      MAS.MORTAR.BLACK and MAS.GLUE.AAC -> B9-04 Mortar / glue; MAS.UNITS.BLACK and MAS.UNITS.WHITE -> B9-01 as MATERIAL
      ROWS of the MAS.BLOCK work line ('material_rows': pcs, never re-added into the m2 work; a material row in its work
      unit is refused); DOOR.LIFT_LANDING -> NEW family B6-08 Lift landing doors (lines stay HELD blank with their cause,
      ELEMENT_REGISTER 'LIFT LANDING HEAD'). A code owned by two families is refused.
  (b) A REGISTER CODE BESIDE ITS WORK CODE IS NOT A BOQ LINE. Blockwork is paid in m2 of laid panel (Q-75; ELEMENT_REGISTER
      'BLOCKWORK MATERIALS AND REGISTER CODES'): MAS.BLOCK m2 is the work line. ARCH.WALL_PANEL (m2), ARCH.WALL_VOLUME
      (m3) and ARCH.WALL_RUN (lm) are geometry carriers of the same walls: on the V3.0.57 index every WALL_PANEL line has a
      MAS.BLOCK line on the same element_id with the same class and quantity (26 / 26), every WALL_VOLUME = panel x
      thickness, every WALL_RUN is the run length of the thickness group. Each leaves B9-01 for 'not_a_boq_line_codes'
      (and 'item_codes_without_family', the ARCH.EXTERIOR precedent of 1.41.0), so no family re-add counts a wall twice.
      The builder ASSERTS the pairing on the index (a panel without its block twin refuses the ruling).
  (c) ONE TRADE KEY PER V11 SECTION. The scorecard / statement V11 trade codes are the reference's own grouping (B5 =
      plaster, B6 = paint, B7 = stairs AND ceilings, B12 = doors and windows): no one-to-one code map to the master groups
      exists. The one-to-one key is the V11 SECTION (its id without '@Vn'): each maps to exactly one master group, or to
      MULTI_GROUP with its groups named when the section re-adds rows of two groups (shown beside each, never inside one).
Also: the candidate census of V3.0.57 is re-run with the census tool unchanged (research/agents_t479) on the same index;
every family other than B9-01 / B9-04 / B6-08 must be equal to 1.55.0's census; B9-01's candidate texts are restated from
it. T-507 (V3.0.58) stays PENDING here: its promotion needs the reproduced chain-run line diff V3.0.57 -> V3.0.58
(R-T485-1), not part of this row.

Run only through the wrapper: URBAN_T637_WRITE=1 bash scripts/agent_env.sh pytest --tree task-T-637
tests/t637/test_t637.py::test_write_master ; check: ... pytest --tree task-T-637 tests/t637
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "research" / "agents_t479", ROOT / "research" / "agents_t485"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import t479_registry_census as C  # noqa: E402
import build_master_1_43_0 as B  # noqa: E402  (unit text of T-485, unchanged)
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.55.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.56.0.json"
VERSION = "1.56.0"
WHO = "T-637"
INDEX = ROOT / "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
INDEX_SHA = "fed5141ea31bfdd9c5f3d89c7fb1fa01365ddbf07b797002780a22016a7f5738"
SCORECARD = ROOT / "research/agents_t620/out/SCORECARD_T620.json"
STATEMENT = ROOT / "research/agents_t620/out/RECONCILED_STATEMENT_T620.json"
GROUPS = tuple(f"B{i}" for i in range(1, 14))
MULTI = "MULTI_GROUP"
CHANGED_FAMILIES = ("B9-01", "B9-04", "B6-08")


class MasterError(Exception):
    pass


# ---- (b) register codes beside the blockwork work line -------------------------------------------------------------
WORK = "MAS.BLOCK"
REGISTER = {
    "ARCH.WALL_PANEL": {
        "unit": "m2",
        "meaning": "the laid block panel area of a wall group as a GEOMETRY CARRIER: the same walls, class and quantity "
                   "as the MAS.BLOCK work line on the same element (the work line is MAS.BLOCK m2)",
        "evidence": [
            "tools/urban_boq_m9.py:1172 _v29_masonry(): ARCH.WALL_PANEL m2 / ARCH.WALL_VOLUME m3 from height evidence, "
            "written beside MAS.BLOCK on the same wall group",
            "OWNER_QUESTIONS_ANSWERED Q-75 / Q-80 (owner 2026-11-02 / 2026-11-07): blockwork is counted per m2 of laid "
            "face (12.5 blocks per m2, 40 x 20 face) for 0.20 and 0.15 m: the payable work unit is m2 of MAS.BLOCK",
            "ELEMENT_REGISTER 'BLOCKWORK MATERIALS AND REGISTER CODES' (Lead 2026-11-08 16:15): the laid block panel is "
            "ONE element with ONE work line per unit: MAS.BLOCK m2",
            "research/agents_t507/out/LINE_INDEX_V3_0_57.json: 26 / 26 ARCH.WALL_PANEL lines have a MAS.BLOCK twin on "
            "the same element_id with the same class and quantity (13 released 467.7925 m2 = 467.7925 m2; 13 HELD "
            "blank = 13 HELD blank); T-630 F-T630-3 printed the pair as REGISTER_BESIDE_WORK",
        ],
        "rule": "reported apart by every census, never dropped, never summed into a family; the blockwork BOQ line is "
                "MAS.BLOCK m2; a wall group with a panel and no block twin refuses this ruling (builder assert)",
    },
    "ARCH.WALL_VOLUME": {
        "unit": "m3",
        "meaning": "the panel area x thickness of the same wall group (a derived dimension of the MAS.BLOCK walls), "
                   "not a second payable measure; block procurement is carried by the pcs material rows",
        "evidence": [
            "tools/urban_boq_m9.py:1172 _v29_masonry(): ARCH.WALL_VOLUME m3 = panel m2 x thickness",
            "research/agents_t507/out/LINE_INDEX_V3_0_57.json: 26 / 26 ARCH.WALL_VOLUME lines sit on a panel element "
            "and each released one equals panel x the group thickness (0.15 / 0.20 m) to 1e-6",
            "OWNER_QUESTIONS_ANSWERED Q-75 / Q-80: blockwork counted per m2 of laid face; block units and mortar are the "
            "procurement rows (B9-01 material_rows, B9-04)",
        ],
        "rule": "reported apart, never dropped, never summed into a family; never a payable blockwork quantity",
    },
    "ARCH.WALL_RUN": {
        "unit": "lm",
        "meaning": "the wall run length of a thickness group (a register of the walls drawn), not a payable measure "
                   "of blockwork",
        "evidence": [
            "engine/source/arch_measure.py:789 _wall_lines(): ARCH.WALL_RUN by thickness (PROVISIONAL register line)",
            "research/agents_t507/out/LINE_INDEX_V3_0_57.json: 7 ARCH.WALL_RUN lines, one per storey x thickness base "
            "element, each beside the MAS.BLOCK lines of the same storey and thickness",
            "OWNER_QUESTIONS_ANSWERED Q-75 / Q-80: blockwork counted per m2 of laid face",
        ],
        "rule": "reported apart, never dropped, never summed into a family; never a payable blockwork quantity",
    },
}

# ---- (a) material rows of the blockwork work line, and the mortar / glue family ----------------------------------
MATERIAL = {
    "MAS.UNITS.BLACK": {"unit": "pcs", "material_of": WORK, "work_unit": "m2",
                        "basis": "black (cement) block units of the laid panel: 12.5 per m2, 40 x 20 face, 0.20 and "
                                 "0.15 m (Q-75 / Q-80); waste separate"},
    "MAS.UNITS.WHITE": {"unit": "pcs", "material_of": WORK, "work_unit": "m2",
                        "basis": "white (AAC) block units of the laid panel: per the owner pallet data (Q-60); waste "
                                 "separate"},
}
MATERIAL_RULE = ("a MATERIAL row is a procurement count of its work line's element, in its own unit: shown under the "
                 "same family, never re-added into the work line's unit (a material row in the work unit is refused)")
B9_04_CODES = {"MAS.MORTAR.BLACK": "m3", "MAS.GLUE.AAC": "kg"}

B6_08 = {
    "code": "B6-08",
    "group": "B6 Openings",
    "item_en": "Lift landing doors (supply and fix per landing)",
    "item_ar": "أبواب مداخل المصعد",
    "unit": "pcs",
    "capability": "NOT_IMPLEMENTED",
    "capability_1_0_0": "NOT_IMPLEMENTED",
    "capability_change": "UNCHANGED",
    "implementation": "none in the released or candidate methods: the 3 lines are written only by the non-candidate "
                      "wiring manifest overlay (research/agents_t619/manifest_v14.py LIFT_CODE, T-608 FR-T608-1 / -2)",
    "source_needed": "lift supplier schedule (landing door size and head height); head height printed nowhere",
    "next_slice": "S5",
    "evidence": [
        "research/agents_t619/manifest_v14.py:118 LIFT_CODE = DOOR.LIFT_LANDING (T-619: the 3 lift landing openings "
        "EXCLUDED from ARCH.PASSAGE, one HELD blank line per landing)",
        "ELEMENT_REGISTER 'LIFT LANDING DOOR' (Lead 2026-11-08 16:15): OWNER TRADE B6 openings, its own family in master "
        "1.56.0; 'LIFT LANDING HEAD': the landing door head height is printed nowhere; supply HELD (FR-T608-2)",
        "research/agents_t630/out/E2E_BOQ_DRY_RUN_T630.json: DOOR.LIFT_LANDING pcs 3 lines, all HELD blank, UNCODED "
        "(F-T630-1)",
    ],
    "released_method_reads": "none",
    "opt_in_readers": "none",
    "missing": "landing door supply: 3 lines (GF / 1F / 2F) HELD blank, cause LIFT LANDING HEAD (head height printed "
               "nowhere) until the lift supplier schedule; the wall opening deduction stays with the wall lines",
    "in_v3_0_candidate": "no",
    "v3_0_planned_tasks": [],
    "development_villa": {"released_run": [], "candidate_run_v2_13": []},
    "item_codes": ["DOOR.LIFT_LANDING"],
    "name_terms": ["landing_door", "lift_door"],
    "in_v3_0_candidate_1_1_0": "no",
    "note": "NEW in 1.56.0 (T-637, T-630 F-T630-1): the lift landing door had no family before 1.56.0; "
            "capability_1_0_0 NOT_IMPLEMENTED stands for 'no family before 1.56.0'; PROPOSED by the worker, effective "
            "with the Checker merge",
}

# ---- (c) one trade key per V11 section ------------------------------------------------------------------------------
# section base id -> (master group or MULTI_GROUP, [groups], [families], basis)
KEYS = {
    "T-534/stair-bed": ("B7", ["B7"], [], "the bed under the stair marble: no engine code of its own; stair finishes "
                                         "stay with the stair lines (OWNER_RULE_STAIRS)"),
    "T-541/membrane": ("B8", ["B8"], ["B8-06"], "FIN.WP.ROOF"),
    "T-541/upturn": ("B8", ["B8"], ["B8-06"], "FIN.WP.ROOF_UPTURN"),
    "T-543/blockwork": ("B9", ["B9"], ["B9-01"], "MAS.BLOCK m2 (the work line; register codes NOT_A_BOQ_LINE, 1.56.0)"),
    "T-545/beams": ("B10", ["B10"], ["B10-07"], "STR.CONC.BEAM"),
    "T-546/floor": ("B8", ["B8"], ["B8-01"], "FIN.WP.FLOOR"),
    "T-546/upturn": ("B8", ["B8"], ["B8-03"], "FIN.WP.WALL_UPTURN / FIN.WP.UPTURN"),
    "T-547/wall-tile": ("B4", ["B4"], ["B4-01"], "FIN.WALL.TILE"),
    "T-551/blinding": ("B10", ["B10"], ["B10-01"], "STR.CONC.BLINDING"),
    "T-551/columns": ("B10", ["B10"], ["B10-06"], "STR.CONC.COLUMN"),
    "T-551/footing-line": ("B10", ["B10"], ["B10-02", "B10-04", "B10-11"],
                           "pads STR.CONC.FOOTING + straps STR.CONC.STRAP / GROUND_BEAM + boundary band "
                           "STR.CONC.BOUNDARY_PAD: one concrete group"),
    "T-551/lift-walls": ("B10", ["B10"], ["B10-10"], "STR.CONC.LIFT"),
    "T-551/necks": ("B10", ["B10"], ["B10-03"], "STR.CONC.NECK"),
    "T-552/plaster-external": ("B4", ["B4"], ["B4-04"], "external plaster (the reference's B5)"),
    "T-552/plaster-internal": ("B4", ["B4"], ["B4-03"], "FIN.PLASTER (the reference's B5)"),
    "T-553/floor-tile": ("B3", ["B3"], ["B3-01", "B3-02"], "FIN.FLOOR.PORCELAIN / FIN.FLOOR.WET_TILE"),
    "T-560/rebar": ("B11", ["B11"], ["B11-01"], "STR.REBAR kg (the reference prints t: display boundary, "
                                               "OWNER_RULE_REBAR s.1)"),
    "T-561/paint-internal": ("B4", ["B4"], ["B4-06"], "FIN.PAINT (the reference's B6)"),
    "T-561/stair-soffit": ("B7", ["B7"], ["B7-15"], "FIN.STAIR.SOFFIT (the reference's B6 wall-paint rows)"),
    "T-568/alu-doors-m2": ("B6", ["B6"], ["B6-03"], "DOOR.EXTERNAL.ALUMINIUM (the reference's B12)"),
    "T-568/alu-doors-nr": ("B6", ["B6"], ["B6-03"], "DOOR.EXTERNAL.ALUMINIUM (the reference's B12)"),
    "T-568/internal-doors-m2": ("B6", ["B6"], ["B6-02"], "DOOR.INTERNAL.PVC (cross-check only)"),
    "T-568/internal-doors-nr": ("B6", ["B6"], ["B6-02"], "DOOR.INTERNAL.PVC (cross-check only)"),
    "T-568/windows-m2": ("B6", ["B6"], ["B6-04"], "ARCH.WINDOW (the reference's B12)"),
    "T-568/windows-nr": ("B6", ["B6"], ["B6-04"], "ARCH.WINDOW (the reference's B12)"),
    "T-571/lintel-count-implied": ("B9", ["B9"], ["B9-02"], "STR.CONC.LINTEL (count beside)"),
    "T-572/held-bounds": (MULTI, ["B1", "B10"], ["B1-02", "B1-03", "B1-04", "B10-02", "B10-03", "B10-04"],
                          "engine HELD bounds of concrete AND earthworks in one section: shown beside both groups"),
    "T-572/measured-columns_1F": ("B10", ["B10"], ["B10-06"], "STR.CONC.COLUMN"),
    "T-572/measured-columns_GF": ("B10", ["B10"], ["B10-06"], "STR.CONC.COLUMN"),
    "T-572/measured-footing_pads_and_straps": ("B10", ["B10"], ["B10-02", "B10-04"], "STR.CONC.FOOTING / STRAP"),
    "T-572/measured-necks": ("B10", ["B10"], ["B10-03"], "STR.CONC.NECK"),
    "T-573/ceiling-board": ("B5", ["B5"], ["B5-01", "B5-02"], "FIN.CEILING (the reference's B7)"),
    "T-573/ceiling-cove": ("B5", ["B5"], ["B5-03"], "cove / cornice (the reference's B7)"),
    "T-573/ceiling-exterior-soffit": ("B5", ["B5"], ["B5-01"], "FIN.CEILING over outside air (the reference's B7)"),
    "T-573/ceiling-paint": ("B4", ["B4"], ["B4-06"], "FIN.PAINT.CEILING (owned by B4-06; the reference's B6)"),
    "T-573/ceiling-stair-soffit": ("B7", ["B7"], ["B7-15"], "FIN.STAIR.SOFFIT (the reference's B7 ceilings)"),
    "T-574/skirting-outdoor": ("B3", ["B3"], ["B3-06"], "FIN.SKIRTING on a court base (the only skirting code of the "
                                                       "candidate)"),
    "T-574/skirting-pieces": ("B7", ["B7"], ["B7-07", "B7-08"], "stair-side skirting pieces per step"),
    "T-574/skirting-room": ("B3", ["B3"], ["B3-06"], "FIN.SKIRTING (the reference's B6)"),
    "T-574/skirting-stairs": ("B7", ["B7"], ["B7-07", "B7-08"], "FIN.STAIR.SKIRTING.ZIGZAG / SLOPED"),
    "T-576/columns-1F": ("B10", ["B10"], ["B10-06"], "STR.CONC.COLUMN"),
    "T-576/columns-1F-reading-10E0-C7": ("B10", ["B10"], ["B10-06"], "STR.CONC.COLUMN (reading beside)"),
    "T-576/columns-GF": ("B10", ["B10"], ["B10-06"], "STR.CONC.COLUMN"),
    "T-576/columns-GF-reading-10E0-C7": ("B10", ["B10"], ["B10-06"], "STR.CONC.COLUMN (reading beside)"),
    "T-577/marble-lm": (MULTI, ["B3", "B6"], ["B3-04", "B6-06", "B6-07"],
                        "door thresholds (B3-04) and lift threshold / surround stone (B6-06 / B6-07) in one section"),
    "T-577/marble-m2": (MULTI, ["B3", "B6"], ["B3-04", "B6-06", "B6-07"],
                        "door thresholds (B3-04) and lift threshold / surround stone (B6-06 / B6-07) in one section"),
    "T-577/marble-nr": (MULTI, ["B3", "B6"], ["B3-04", "B6-06", "B6-07"],
                        "door thresholds (B3-04) and lift threshold / surround stone (B6-06 / B6-07) in one section"),
    "T-578/rails": (MULTI, ["B7", "B13"], ["B7-09", "B7-10", "B13-08"],
                    "stair rails (B7-09 / B7-10) and guards outside stairs (B13-08) in one section"),
    "T-584/stair-steps-lm": ("B7", ["B7"], ["B7-06"], "FIN.STAIR.STEP_LM"),
    "T-584/stair-steps-nr": ("B7", ["B7"], ["B7-06"], "FIN.STAIR.STEP_LM (count beside)"),
}
CODE_RE = re.compile(r"^(B\d{1,2})\b")


def base_key(section_id):
    return section_id.split("@", 1)[0]


def v11_sections(sc, st):
    """{base key: {'ids': [...], 'trade_codes': {...}, 'labels': {...}, 'units': {...}}} from the scorecard (sections of
    record and apart) and the statement (every 'sections*' list)."""
    out = {}

    def put(sid, code, label, unit, where):
        k = out.setdefault(base_key(sid), {"ids": set(), "trade_codes": set(), "labels": set(), "units": set(),
                                           "in": set()})
        k["ids"].add(sid)
        k["labels"].add(label)
        k["units"].add(unit)
        k["in"].add(where)
        m = CODE_RE.match(code or label or "")
        k["trade_codes"].add(m.group(1) if m else "UNCODED")

    for r in sc["reference_lines"]:
        put(r["section_id"], r.get("trade_code"), r["trade"], r["unit"], "scorecard")
    for r in sc["apart"]:
        put(r["section_id"], None, r["trade"], r["unit"], "scorecard (apart)")
    for k in sorted(x for x in st if x.startswith("sections")):
        for r in st[k]:
            put(r["section_id"], None, r["trade"], r["unit"], "statement")
    return {k: {kk: sorted(v) for kk, v in d.items()} for k, d in sorted(out.items())}


def crosswalk(master, sc, st):
    secs = v11_sections(sc, st)
    if set(secs) != set(KEYS):
        raise MasterError(f"crosswalk keys differ from the V11 sections: missing {sorted(set(secs) - set(KEYS))}, "
                          f"extra {sorted(set(KEYS) - set(secs))}")
    fam = {f["code"]: f["group"].split()[0] for f in master["families"]}
    keys, by_code = {}, {}
    for k in sorted(KEYS):
        target, groups, fams, basis = KEYS[k]
        if any(g not in GROUPS for g in groups) or not groups:
            raise MasterError(f"{k}: groups {groups} not B1 .. B13")
        if target == MULTI:
            if len(groups) < 2:
                raise MasterError(f"{k}: MULTI_GROUP names fewer than two groups")
        elif groups != [target]:
            raise MasterError(f"{k}: one target {target} but groups {groups}")
        for f in fams:
            if f not in fam:
                raise MasterError(f"{k}: family {f} not in the master")
            if fam[f] not in groups:
                raise MasterError(f"{k}: family {f} is {fam[f]}, not in {groups}")
        s = secs[k]
        keys[k] = {"master_group": target, "groups": groups, "families": fams, "basis": basis,
                   "v11_trade_code": s["trade_codes"], "v11_ids": s["ids"], "units": s["units"], "in": s["in"]}
        for c in s["trade_codes"]:
            by_code.setdefault(c, set()).update(groups)
    return {
        "rule": "R-T637-1 (c): the key is the scorecard / statement V11 SECTION id without its '@Vn' version suffix "
                "(one key = one section through every version); each key maps to exactly one master group, or to "
                "MULTI_GROUP with its groups named (the section re-adds rows of two groups: shown beside each, never "
                "inside one). The V11 trade code is the reference's own grouping and is NEVER used as a master group.",
        "sources": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (SCORECARD, STATEMENT)},
        "keys": keys,
        "v11_trade_code_to_master_groups": {c: sorted(g, key=lambda x: int(x[1:])) for c, g in sorted(by_code.items())},
        "counts": {"keys": len(keys), "single_group": sum(1 for v in keys.values() if v["master_group"] != MULTI),
                   "multi_group": sum(1 for v in keys.values() if v["master_group"] == MULTI)},
    }


# ---- ruling evidence on the index -----------------------------------------------------------------------------------

def register_pairing(index):
    """(b) on the line index: every ARCH.WALL_PANEL has a MAS.BLOCK twin (same element, class, quantity); every released
    WALL_VOLUME = its panel x thickness. -> facts; raises on a breach."""
    by_el = {}
    for l in index["lines"]:
        by_el.setdefault(l["element_id"], {}).setdefault(l["item_code"], []).append(l)
    pairs = vols = 0
    released = 0.0
    for el, codes in sorted(by_el.items()):
        for p in codes.get("ARCH.WALL_PANEL", []):
            twins = [b for b in codes.get(WORK, []) if b["class"] == p["class"] and b["measured_net"] == p["measured_net"]]
            if len(twins) != 1:
                raise MasterError(f"{el}: ARCH.WALL_PANEL without exactly one MAS.BLOCK twin: the register ruling "
                                  "does not hold here")
            pairs += 1
            if p["class"] == "RELEASED":
                released += p["measured_net"]
            for v in codes.get("ARCH.WALL_VOLUME", []):
                if v["class"] != p["class"]:
                    raise MasterError(f"{el}: WALL_VOLUME class {v['class']} vs panel {p['class']}")
                if v["class"] == "RELEASED":
                    t = float(re.search(r"t=(\d+\.\d+)", el).group(1))
                    if abs(v["measured_net"] - p["measured_net"] * t) > 1e-6:
                        raise MasterError(f"{el}: WALL_VOLUME {v['measured_net']} != panel x {t}")
                vols += 1
        if codes.get("ARCH.WALL_VOLUME") and not codes.get("ARCH.WALL_PANEL"):
            raise MasterError(f"{el}: WALL_VOLUME without a panel")
    runs = sum(len(c.get("ARCH.WALL_RUN", [])) for c in by_el.values())
    return {"panel_block_pairs": pairs, "panel_released_m2": round(released, 6), "volume_lines": vols,
            "run_lines": runs,
            "block_without_panel": sorted(el for el, c in by_el.items() if c.get(WORK) and not c.get("ARCH.WALL_PANEL"))}


# ---- checks (every one refuses) ---------------------------------------------------------------------------------------

def check_t637(doc):
    """R-T637-1 problems of a registry (empty = holds)."""
    bad = []
    own = {}
    for f in doc["families"]:
        for c in f.get("item_codes") or ():
            if c in own:
                bad.append(f"item code {c} owned by {own[c]} and {f['code']} (one family per code)")
            own.setdefault(c, f["code"])
    nab = doc.get("not_a_boq_line_codes") or {}
    for c in nab:
        if c in own:
            bad.append(f"{c}: NOT_A_BOQ_LINE and owned by {own[c]}")
        if c not in doc.get("item_codes_without_family", {}):
            bad.append(f"{c}: NOT_A_BOQ_LINE but not listed in item_codes_without_family")
    for f in doc["families"]:
        for c, m in (f.get("material_rows") or {}).items():
            if c not in (f.get("item_codes") or ()):
                bad.append(f"{f['code']}: material row {c} is not an item code of the family")
            if m.get("material_of") not in (f.get("item_codes") or ()):
                bad.append(f"{f['code']}: material row {c} names work {m.get('material_of')} outside the family")
            if not m.get("unit") or m.get("unit") == m.get("work_unit"):
                bad.append(f"{f['code']}: material row {c} in its work unit {m.get('work_unit')} would be re-added "
                           "into the work line (refused)")
    return bad


def material_guard(lines, master):
    """reader side: a line of a material code in its work line's unit would be summed into the work: refused."""
    mats = {c: m for f in master["families"] for c, m in (f.get("material_rows") or {}).items()}
    bad = [(l["line_id"], l["item_code"], l["unit"]) for l in lines
           if l["item_code"] in mats and l["unit"] == mats[l["item_code"]]["work_unit"]]
    if bad:
        raise MasterError(f"material row(s) in the work unit, refused: {bad[:3]}")
    return len([l for l in lines if l["item_code"] in mats])


# ---- build ----------------------------------------------------------------------------------------------------------

def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _index():
    if hashlib.sha256(INDEX.read_bytes()).hexdigest() != INDEX_SHA:
        raise MasterError("LINE_INDEX_V3_0_57 is not the pinned index")
    return _json(INDEX)


def build():
    old = _json(OLD)
    if old["version"] != "1.55.0":
        raise MasterError("the base is not 1.55.0")
    index = _index()
    pairing = register_pairing(index)
    new = copy.deepcopy(old)
    new["version"] = VERSION
    new["supersedes"] = ("1.55.0 (kept unchanged on disk): every field copied unchanged except (R-T637-1): B9-04 owns "
                         "MAS.MORTAR.BLACK / MAS.GLUE.AAC; B9-01 owns MAS.UNITS.BLACK / MAS.UNITS.WHITE as material "
                         "rows of MAS.BLOCK and gives ARCH.WALL_PANEL / WALL_VOLUME / WALL_RUN to not_a_boq_line_codes; "
                         "new family B6-08 (DOOR.LIFT_LANDING); candidate census of V3.0.57 re-run on the same index; "
                         "trade_key_crosswalk added; T-507 (V3.0.58) stays pending (promotion needs its chain-run line "
                         "diff, R-T485-1)")
    new["source"] = (old["source"] + f" | {VERSION} ({WHO}): 1.55.0 + R-T637-1 (T-630 findings F-T630-1 / -2 / -3): "
                     "family for every live overlay code, register codes beside the blockwork work line ruled "
                     "NOT_A_BOQ_LINE, V11 section -> master group crosswalk; no quantity, capability or owner change")
    fams = {f["code"]: f for f in new["families"]}
    if "B6-08" in fams:
        raise MasterError("B6-08 already exists")
    owned = {c: f["code"] for f in new["families"] for c in f["item_codes"]}
    for c in list(MATERIAL) + list(B9_04_CODES) + ["DOOR.LIFT_LANDING"]:
        if c in owned or c in new["item_codes_without_family"]:
            raise MasterError(f"{c} is already mapped in 1.55.0")
    for c in REGISTER:
        if owned.get(c) != "B9-01":
            raise MasterError(f"{c} is not a B9-01 code in 1.55.0")

    # (b) + (a) B9-01
    f = fams["B9-01"]
    f["item_codes"] = sorted([c for c in f["item_codes"] if c not in REGISTER] + list(MATERIAL))
    f["material_rows"] = {c: dict(m, rule=MATERIAL_RULE) for c, m in sorted(MATERIAL.items())}
    f["register_codes_ruled"] = {c: f"NOT_A_BOQ_LINE ({VERSION}, {WHO}): see not_a_boq_line_codes" for c in REGISTER}
    f["note"] = (f["note"] + f" | {VERSION} ({WHO}): the work line is MAS.BLOCK m2 (Q-75); ARCH.WALL_PANEL / WALL_VOLUME "
                 "/ WALL_RUN are geometry carriers of the same walls, ruled NOT_A_BOQ_LINE (no re-add counts a wall "
                 "twice: 1.55.0's census printed m2 935.585 = 2 x 467.7925); block units MAS.UNITS.* are pcs material "
                 "rows, never re-added into the m2 work")
    # (a) B9-04
    g = fams["B9-04"]
    g["item_codes"] = sorted(B9_04_CODES)
    g["evidence"] = list(g["evidence"]) + [
        f"{VERSION} ({WHO}): MAS.MORTAR.BLACK (m3, black-block joint mortar 1:4, Q-78) and MAS.GLUE.AAC (kg, white "
        "AAC glue 3.5 / 4.5 kg per m2, owner 2026-11-02) are written only by the non-candidate wiring manifest overlay "
        "(research/agents_t629, T-498 rows): no released or candidate module writes them, so the capability stays "
        "NOT_IMPLEMENTED; ELEMENT_REGISTER 'BLOCKWORK MATERIALS AND REGISTER CODES': mortar and glue belong to B9-04"]
    g["missing"] = (g["missing"] + f" | {VERSION} ({WHO}): the overlay carries 33 MAS.MORTAR.BLACK m3 and 17 MAS.GLUE.AAC "
                    "kg lines (T-630); none is in the candidate V3.0.57, none released by a candidate method")
    g["note"] = (str(g.get("note") or "") + f" | {VERSION} ({WHO}): owns its two material codes (F-T630-1); "
                 "B9-04 no longer reads MISSING where the overlay carries its lines").lstrip(" |")
    g["candidate"] = dict(g["candidate"], candidate_basis=(
        f"CENSUS ARCH_TAKEOFF_V3.0.57 (candidate_census, re-run {VERSION} by {WHO}): no line of the family in the "
        "candidate (its codes are written only by the non-candidate overlay); state NOT_IN_CANDIDATE"))
    # (a) B6-08
    new["families"].append(dict(B6_08, candidate={
        "state": "NOT_IN_CANDIDATE", "method_version": old["candidate"]["method_version"], "packages": [],
        "as_of_package": old["candidate"]["as_of_package"], "changed": "",
        "open": "no candidate line; the 3 overlay lines stay HELD blank (LIFT LANDING HEAD)",
        "released_in_candidate": "none",
        "candidate_basis": f"CENSUS ARCH_TAKEOFF_V3.0.57 (candidate_census, re-run {VERSION} by {WHO}): no line"}))
    # (b) the register codes leave every family
    for c, r in REGISTER.items():
        new["item_codes_without_family"][c] = (f"{VERSION} ({WHO}): {r['meaning']}; declared NOT_A_BOQ_LINE "
                                               "(not_a_boq_line_codes) with its evidence")
        new["not_a_boq_line_codes"][c] = {"meaning": r["meaning"], "evidence": list(r["evidence"]), "rule": r["rule"],
                                          "unit": r["unit"], "work_line": f"{WORK} m2 (B9-01)",
                                          "since": f"{VERSION} ({WHO})"}
    new["item_code_scan"] = (new["item_code_scan"] + f" | {VERSION} ({WHO}): same scan; ARCH.WALL_PANEL / WALL_VOLUME / "
                             "WALL_RUN move from B9-01 to item_codes_without_family (NOT_A_BOQ_LINE); the overlay codes "
                             "MAS.UNITS.* (B9-01), MAS.MORTAR.BLACK / MAS.GLUE.AAC (B9-04), DOOR.LIFT_LANDING (B6-08) are "
                             "owned; 104 families")

    # census of V3.0.57 re-run on the same index (tool unchanged)
    census = C.census(index, new)
    if census["issue_counts"] or census["no_family"]:
        raise MasterError(f"census issues {census['issue_counts']} no_family {sorted(census['no_family'])}")
    oc = old["candidate_census"]["families"]
    for code, row in census["families"].items():
        if code not in CHANGED_FAMILIES and row != oc[code]:
            raise MasterError(f"{code}: census moved although R-T637-1 does not touch it")
    b901 = census["families"]["B9-01"]
    if sorted(b901["units"]) != ["m2"] or b901["item_codes_present"] != [WORK]:
        raise MasterError(f"B9-01 census after the ruling is not MAS.BLOCK m2 only: {b901['item_codes_present']}")
    rel, held = B._units_text(b901["units"], "released"), B._units_text(b901["units"], "held")
    c = f["candidate"]
    cand = old["candidate"]["method_version"]
    c["changed"] = c["changed"].split(f" | census {cand}:")[0] + (
        f" | census {cand} ({VERSION}, {WHO}: register codes NOT_A_BOQ_LINE): released {rel}")
    c["open"] = f"held in the candidate {cand}: {held} (never 0, never summed; see candidate_census)"
    c["released_in_candidate"] = rel
    c["candidate_basis"] = c["candidate_basis"] + f" | census re-run {VERSION} ({WHO}): MAS.BLOCK only"
    old_cen = old["candidate_census"]
    new["candidate_census"] = dict(
        old_cen, families=census["families"], not_a_boq_lines=census["not_a_boq_lines"],
        no_family=census["no_family"], issue_counts=census["issue_counts"],
        stale_in_candidate_vs_registry=C.compare_blocks(census, new),
        builder=old_cen.get("builder", "") + f" | {VERSION} ({WHO}): re-run with research/agents_t479/"
                "t479_registry_census.census() unchanged on the same index, families other than B9-01 / B9-04 / "
                "B6-08 asserted equal to 1.55.0",
        register_pairing_v3_0_57=pairing)

    # counts
    counts = {s: 0 for s in FMC.STATES}
    yes_no = {"yes": 0, "no": 0, "N/A": 0}
    cap = {s: 0 for s in new["capability_states"]}
    chg = {}
    for fam in new["families"]:
        counts[fam["candidate"]["state"]] += 1
        yes_no[fam["in_v3_0_candidate"]] += 1
        cap[fam["capability"]] += 1
        chg[fam["capability_change"]] = chg.get(fam["capability_change"], 0) + 1
    new["candidate_state_counts"] = counts
    new["in_v3_0_candidate_counts"] = {k: v for k, v in yes_no.items() if v or k != "N/A"}
    new["capability_counts"] = cap
    new["capability_change_counts"] = {k: chg.get(k, 0) for k in old["capability_change_counts"]}
    new["trade_key_crosswalk"] = crosswalk(new, _json(SCORECARD), _json(STATEMENT))
    new["t637"] = {"rule": "R-T637-1", "task": WHO, "from_registry": "1.55.0",
                   "families_changed": list(CHANGED_FAMILIES), "quantity_change": "none",
                   "capability_change": "none (B6-08 is new: NOT_IMPLEMENTED, no family before)",
                   "pending_not_promoted": "T-507 ARCH_TAKEOFF_V3.0.58 (merged c94b35c1): promotion needs the "
                                           "reproduced chain-run line diff V3.0.57 -> V3.0.58 (R-T485-1); a separate row"}
    bad = check_t637(new)
    if bad:
        raise MasterError(f"R-T637-1: {bad}")
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def write():
    doc = build()
    NEW.write_text(text(doc), encoding="utf-8")
    return doc
