"""M9 RULE STORE MANIFEST - build or check rules/RULES_MANIFEST.json.

    python3 -I tools/m9_rules_manifest.py build     copy the owner library, export the Urban method registers, write the manifest
    python3 -I tools/m9_rules_manifest.py check     exit 1 when any rules/ file or its source drifted from the manifest

The store holds COPIES: the originals (data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json, engine/source/urban_methods*.py,
engine/profiles/*.json) are never edited, and the frozen M2-M8 packages keep reading them where they are. The manifest
records the sha256 of every store file and of the original it was copied from, so a drift on either side is visible.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.source import urban_methods as UM1  # noqa: E402
from engine.source import urban_methods_v3 as UM3  # noqa: E402

STORE = ROOT / "rules"
COPIES = {"owner_library/URBAN_PROJECTS_RULE_LIBRARY_1.4.0.json": "data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json"}
EXPORTS = {"methods/URBAN_METHOD_REGISTER_V1.json": ("engine/source/urban_methods.py", UM1.register),
           "methods/URBAN_METHOD_REGISTER_V3.json": ("engine/source/urban_methods_v3.py", UM3.register)}
AUTHORED = ("owner_decisions/URBAN_RULES_1.5.0.json", "materials/URBAN_MATERIAL_SPECS_1.0.0.json",
            "coverage/BOQ_FAMILY_MASTER_1.0.0.json",
            "coverage/BOQ_FAMILY_MASTER_1.1.0.json",    # T-130: re-derived from code and runs; read by no method yet
            "coverage/BOQ_FAMILY_MASTER_1.2.0.json",    # T-203: + candidate-level state per family; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.3.0.json",    # T-231: 1.2.0 + the pending V3.0.8 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.4.0.json",    # T-211: 1.3.0 + the pending V3.0.9 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.5.0.json",    # T-232: 1.4.0 + the pending V3.0.10 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.6.0.json",    # T-239: 1.5.0 + the pending V3.0.11 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.7.0.json",    # T-146: 1.6.0 + the pending V3.0.12 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.8.0.json",    # T-268: 1.7.0 + the pending V3.0.13 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.9.0.json",    # T-240: 1.8.0 + the pending V3.0.14 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.10.0.json",   # T-270: 1.9.0 + the pending V3.0.15 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.11.0.json",   # T-245: 1.10.0 + the pending V3.0.16 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.12.0.json",   # T-254: 1.11.0 + the pending V3.0.17 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.13.0.json",   # T-266: 1.12.0 + the pending V3.0.18 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.14.0.json",   # T-255: 1.13.0 + the pending V3.0.19 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.15.0.json",   # T-244: 1.14.0 + the pending V3.0.20 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.16.0.json",   # T-315: 1.15.0 + the pending V3.0.21 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.17.0.json",   # T-331: 1.16.0 + the pending V3.0.22 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.18.0.json",   # T-319: 1.17.0 + the pending V3.0.23 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.19.0.json",   # T-338: 1.18.0 + the pending V3.0.24 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.20.0.json",   # T-343: 1.19.0 + the pending V3.0.25 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.21.0.json",   # T-279: 1.20.0 + the pending V3.0.26 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.22.0.json",   # T-318: 1.21.0 + the pending V3.0.27 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.23.0.json",   # T-326: 1.22.0 + the pending V3.0.28 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.24.0.json",   # T-327: 1.23.0 + the pending V3.0.29 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.25.0.json",   # T-199: 1.24.0 + the pending V3.0.30 package (r3); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.26.0.json",   # T-328: 1.25.0 + the pending V3.0.31 package + ownership census; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.27.0.json",   # T-284: 1.26.0 + the pending V3.0.32 package + owners of its codes; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.28.0.json",   # T-397: 1.27.0 + the pending V3.0.33 package (no new code); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.29.0.json",   # T-399: 1.28.0 + the pending V3.0.34 package + B4-02 coverage evidence; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.30.0.json",   # T-400: 1.29.0 + the pending V3.0.35 package + owners of its codes (B13-04, B10-11); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.31.0.json",   # T-246: 1.30.0 + the pending V3.0.36 package (lists only; no family change); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.32.0.json",   # T-420: 1.31.0 + the pending V3.0.37 package + B3-05 owns the bed codes; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.33.0.json",   # T-421: 1.32.0 + the pending V3.0.38 package + owners of its codes (B3-01, B6-06, B6-07); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.34.0.json",   # T-429: 1.33.0 + the pending V3.0.39 package (B7-02 / B7-03 / B7-06 rebound; no family owner change); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.35.0.json",   # T-430: 1.34.0 + the pending V3.0.40 package (B10-04 ground beams split per run / held; no family owner change); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.36.0.json",   # T-431: 1.35.0 + the pending V3.0.41 package (B3-01 / B2-02 / B3-05 / B3-06 / B5-01 / B4-06 / B5-04 evidence and text; no owner change); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.37.0.json",   # T-442: 1.36.0 + the pending V3.0.42 package (B10-05 / B10-06 / B10-10 evidence and text; no owner change); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.38.0.json",   # T-350: 1.37.0 + the pending V3.0.43 package (B1-01 .. B1-04, B10-01, B10-04 evidence, item codes and text; no owner change); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.39.0.json",   # T-422: 1.38.0 + the pending V3.0.44 package (B3-06 skirting evidence and text; no owner change); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.40.0.json",   # T-478: 1.39.0 + the pending V3.0.45 package (B10-01 evidence and text; no owner change); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.41.0.json",   # T-479: 1.40.0 + family B13-09, not_a_boq_line_codes, candidate_census, B8-08 / B10-13 / B7-13 reader text; no owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.42.0.json",   # T-419: 1.41.0 + the pending V3.0.46 package (B10-10 / B10-13 / B11-01 / B9-01 / B8-08 evidence and text; no owner change); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.43.0.json",   # T-485: 1.42.0 + the 39 merged pending packages promoted, every family's candidate block at V3.0.46 (census + line diff); no owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.44.0.json",   # T-443: 1.43.0 + the pending V3.0.47 package (B3-06 evidence and text; no owner change); read by no method
            "coverage/BOQ_FAMILY_MASTER_1.45.0.json",   # T-350 r4: 1.44.0 + the pending V3.0.48 package (B1-02 / B1-03 / B1-04 text; 7 no-code families N/A, F-C-T485-1); no owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.47.0.json",   # T-497: 1.45.0 + the pending V3.0.50 package (B1-02 evidence and text; 1.46.0 is T-483 r2's, parallel); no owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.48.0.json",   # T-483 r2: 1.47.0 + T-443 / T-350b / T-497 promoted (R-T485-1, census + line diff at V3.0.50) + the pending V3.0.51 package (B3-06 text); no owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.50.0.json",   # T-487: 1.48.0 + the pending V3.0.53 package (B9-02 evidence and text; 1.49.0 is T-310's, parallel); no owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.51.0.json",   # T-480: 1.50.0 + T-487 promoted (R-T485-1, census + line diff at V3.0.53) + the pending V3.0.54 package (B7-09 evidence and text); no owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.52.0.json",   # T-488: 1.51.0 + T-480 promoted (R-T485-1, census + line diff at V3.0.54) + the pending V3.0.55 package (B9-01 / B10-12 evidence and text); no owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.53.0.json",   # T-508: 1.52.0 + T-488 promoted (R-T485-1, census + line diff at V3.0.55) + the pending V3.0.56 package (B3-06 / B7-07 / B7-08 text; B7-07 / B7-08 item codes); no owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.54.0.json",   # T-310 r7: 1.53.0 + T-508 promoted (R-T485-1, census + line diff at V3.0.56) + the pending V3.0.57 package (B8-01 / B8-02 / B8-03 / B8-09 text; B8-09 owns the two pool layer codes); no owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.55.0.json",   # T-507: 1.54.0 + T-310 promoted (R-T485-1, census + line diff at V3.0.57) + the pending V3.0.58 package (B8-06 text: exposed-slab roof WP lines)
            "coverage/BOQ_FAMILY_MASTER_1.56.0.json",   # T-637: 1.55.0 + R-T637-1 (UNCODED codes to families, register codes NOT_A_BOQ_LINE, V11 trade-key crosswalk); no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.57.0.json",   # T-525: 1.56.0 + T-507 promoted (R-T485-1, census + line diff at V3.0.58); no pending package; no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.58.0.json",   # T-498: 1.57.0 + pending ARCH_TAKEOFF_V3.0.59 (blockwork material lines) + B9-01 / B9-04 text + B9-04 capability NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED; no promotion, no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.59.0.json",   # T-651: 1.58.0 + T-498 promoted (R-T485-1, census + line diff at V3.0.59) + one dated B9-04 note; no pending package; no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.60.0.json",   # T-423 r3: 1.59.0 + pending ARCH_TAKEOFF_V3.0.60 (split remainder: ceiling dome lists, D-1F-04 face piece, threshold material state / measure pairs) + B3-01 / B3-04 / B4-01 / B4-03 / B5-01 text; no promotion, no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.61.0.json",   # T-563: 1.60.0 + pending ARCH_TAKEOFF_V3.0.61 (PLASTER_HEIGHT_V1_WIRING: 11 dry plaster lines at the slab / roof soffit, HELD) after the pending V3.0.60 + B4-03 / B4-06 text; no promotion, no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.62.0.json",   # T-655: 1.61.0 + T-423 (V3.0.60) and T-563 (V3.0.61) promoted (R-T485-1, census + line diff at V3.0.61); no pending package; no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.63.0.json",   # T-661: 1.62.0 + ARCH_TAKEOFF_V3.0.62 (CONCRETE_GATE_B_V1: held necks / beams restated from the merged member ledgers), pending on the task branch and promoted IN the merge (--promote); no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.64.0.json",   # T-665: 1.63.0 + ARCH_TAKEOFF_V3.0.63 (CONCRETE_GATE_B_V2: held column / ground-beam / footing lines restated from the merged T-658 r2 / T-595 ledgers), pending on the task branch and promoted IN the merge (--promote); no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.65.0.json",   # T-668: 1.64.0 + ARCH_TAKEOFF_V3.0.64 (CONCRETE_GATE_B_V3: junction-square owners, boundary band bound, one new pool blinding line HELD, from the merged T-666 / T-659 / T-667 ledgers), pending on the task branch and promoted IN the merge (--promote); no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.66.0.json",   # T-671: 1.65.0 + ARCH_TAKEOFF_V3.0.65 (CONCRETE_GATE_B_V4: 2F roof-column lower ends bound, CN columns not applicable with evidence, one strip valued with a held depth companion line, from the merged T-669 / T-647 / T-642 ledgers), pending on the task branch and promoted IN the merge (--promote); no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.67.0.json",   # T-677: 1.66.0 + ARCH_TAKEOFF_V3.0.66 (CONCRETE_GATE_B_V5: 16 held lintels bounded on drawn heads + one shared pier-remainder line, ST-03 steps lower end beside its held waist, 3 ground-slab panels re-derived from the drawn faces with the BAND0038 strip bound, from the merged T-673 / T-674 ledgers), pending on the task branch and promoted IN the merge (--promote); no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.68.0.json",   # T-682: 1.67.0 + ARCH_TAKEOFF_V3.0.67 (CONCRETE_GATE_B_V6: 9 held lintels on a soffit lower bound (7 bounded, 2 lower end only), PC-2F and annex C3 bounded, from the merged T-678 ledger), pending on the task branch and promoted IN the merge (--promote); no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.69.0.json",   # T-672: 1.68.0 + ARCH_TAKEOFF_V3.0.68 (MASONRY_GATE_B_V1: B9 materials re-produced on rulebook 1.1.0, AAC lines on black below-ground hosts not applicable, perimeter joint and lintel bed mortar lines, from the merged T-670 / T-372 / T-675) and the two new B9-04 codes, pending on the task branch and promoted IN the merge (--promote); no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.70.0.json",   # T-687: 1.69.0 + ARCH_TAKEOFF_V3.0.69 (FINISH_GATE_B_V1: held FIN.PLASTER / FIN.PAINT lines restated from the merged T-676 / T-680 / T-686 ledgers, wet-room plaster bands above the ceiling from T-690), pending on the task branch and promoted IN the merge (--promote); no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.71.0.json",   # T-693: 1.70.0 + ARCH_TAKEOFF_V3.0.70 (CONCRETE_GATE_B_V7: held STR.CONC.COLUMN ranges from the merged T-689 (B8 joint low, five conflict columns bounded) and the T-688 R-T688-3 slab label), pending on the task branch and promoted IN the merge (--promote); no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.72.0.json",   # T-704: 1.71.0 + ARCH_TAKEOFF_V3.0.71 (CONCRETE_GATE_B_V8: one-sided bounds beside the HELD blank STR.CONC.LINTEL lines from the merged T-699 ledger), pending on the task branch and promoted IN the merge (--promote); no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.73.0.json",   # T-703: 1.72.0 + ARCH_TAKEOFF_V3.0.72 (MASONRY_GATE_B_V4: one-ended figures beside HELD blank masonry lines from the merged T-696 / T-713 ledgers, B9 held ranges restated with R-T696-1), pending on the task branch and promoted IN the merge (--promote); no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.74.0.json",   # T-722: 1.73.0 + ARCH_TAKEOFF_V3.0.73 (CONCRETE_GATE_B_V9: held column lows raised by a one-plane slab-top transfer, lower-end figures beside HELD blank STR.CONC lines, holding items named, from the merged T-707 / T-711 / T-712 / T-721 ledgers as mapped by T-723), pending on the task branch and promoted IN the merge (--promote); no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.75.0.json",   # T-717: 1.74.0 + ARCH_TAKEOFF_V3.0.74 (FINISH_GATE_B_V2: annex plaster bounds, GF wet bands restated, return paint and stairwell bands added HELD from the merged T-701 / T-702 / T-709 ledgers as mapped by T-723), pending on the task branch and promoted IN the merge (--promote); no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.76.0.json",   # T-729: 1.75.0 + ARCH_TAKEOFF_V3.0.75 (FORMWORK_GATE_B_V1 + CONCRETE_GATE_B_V10: the merged T-714 / T-724 / T-725 / T-731 / T-732 / T-735 formwork lines and concrete round 10 as mapped by T-730; B2-03 register note), pending on the task branch and promoted IN the merge (--promote); no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.77.0.json",   # T-736: 1.76.0 + ARCH_TAKEOFF_V3.0.76 (BEADS_GATE_B_V1 + CEILING_GATE_B_V3 + CHECKER_DOWNGRADE_MATERIALISE_V1: the merged T-728 interior bead lines (B4-09 item code FIN.PLASTER.BEAD), the T-727 ceiling exclusion and the Checker record DG-98cbadebaecc5ede as mapped by T-730), pending on the task branch and promoted IN the merge (--promote); no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.78.0.json",   # T-749: 1.77.0 + ARCH_TAKEOFF_V3.0.77 (PAINT_GATE_B_V1 + PAINT_EDGE_GATE_B_V1 + EXT_PAINT_EDGE_GATE_B_V1: the merged T-740 paint restatement, the T-746 return edges as lm (B4-06 item code FIN.PAINT.EDGE) and the T-747 / T-751 exterior paint edges (B4-07 item code FIN.EXT.PAINT.EDGE) as mapped by T-748), pending on the task branch and promoted IN the merge (--promote); no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.79.0.json",   # T-738: 1.78.0 + ARCH_TAKEOFF_V3.0.78 (TILE_GATE_B_V1 + STAIR_FINISH_GATE_B_V1: the merged T-702 wall tile bounds and the T-715 / T-718 stair finish lines with the T-733 tread verdict as mapped by T-730), pending on the task branch and promoted IN the merge (--promote); no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.80.0.json",   # T-314 r4: 1.79.0 + the merged-pending T-738 promoted (R-T485-1, merge 208c5689; its in-merge --promote did not run) + ARCH_TAKEOFF_V3.0.79 (EXT_RENDER_GATE_B_V1 + EXT_PAINT_GATE_B_V1 + EXT_EDGE_DELTA_V1: exterior render / paint face rows from the merged T-756 ledger; B4-07 item code FIN.EXT.PAINT), pending on the task branch and promoted IN the merge (--promote); no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.81.0.json",   # T-770: 1.80.0 + ARCH_TAKEOFF_V3.0.81 (FILL_WIRE_V1, R-T770-1 / R-T770-2: the MAIN_FILL_ALL, T-762 formwork and T-761 concrete fix-row sets by line id; B9-02 item code STR.CONC.SAFETY), pending on the task branch and promoted IN the merge (--promote); no quantity or owner change; read by no method
            "coverage/BOQ_FAMILY_MASTER_1.82.0.json",   # T-770 r5: 1.81.0 + ARCH_TAKEOFF_V3.0.82 (FILL_WIRE_V2, R-T770-3: T-764 / T-767 / T-769 with the T-776 restatement by line id; SITE item codes for B1-01 / B1-05 / B1-07), pending on the task branch as T-770b and promoted IN the merge (--promote); no quantity or owner change; read by no method
            "owner_decisions/URBAN_RULES_1.6.0.json",   # T-158: owner stair rule UP-STAIR-015 over 1.5.0; rule_store not yet
            "owner_decisions/URBAN_RULES_1.7.0.json",   # T-267: owner stair finish-level rule UP-STAIR-016 over 1.6.0; rule_store not yet
            "rulebook/URBAN_COMPANY_RULEBOOK_1.0.0.json",  # T-448: Company Rulebook (owner 2026-11-02); read by company_rulebook_v1 only
            "owner_decisions/URBAN_RULES_1.8.0.json",  # T-461: UP-GEN-003 1.2.0 (Q-73 A) + UP-STAIR-017 (Q-53 C) over 1.7.0; rule_store_v2 only
            "conventions/URBAN_CONVENTIONS_1.0.0.json",  # T-599: UP-CONC-JOINT-001 LEAD_ADOPTED (Q-62 A delegated); read by no method
            "rulebook/URBAN_COMPANY_RULEBOOK_1.1.0.json",  # T-615: 1.0.0 + UPC-BLACK-BLOCK-001 1.1.0 (Q-80: 0.15 m module 40 x 20); read by research/agents_t615 only
            "rulebook/URBAN_COMPANY_RULEBOOK_1.2.0.json")  # T-740: 1.1.0 + UP-FIN-PAINT-002 1.0.0 (owner 2026-11-12: paint area = plaster area of the same faces); read by research/agents_t740 only
REFERENCED = tuple(f"engine/profiles/URBAN_M{m}_GENERIC_CONVENTIONS_V{v}.json"
                   for m, v in ((2, 1), (3, 2), (4, 3), (5, 4), (7, 5), (8, 6)))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def export_text(fn):
    return json.dumps(fn(), indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def manifest():
    files = {}
    for rel, src in COPIES.items():
        files[rel] = {"kind": "COPY", "sha256": sha(STORE / rel), "source": src, "source_sha256": sha(ROOT / src)}
    for rel, (src, _fn) in EXPORTS.items():
        files[rel] = {"kind": "EXPORT", "sha256": sha(STORE / rel), "source": src, "source_sha256": sha(ROOT / src)}
    for rel in AUTHORED:
        files[rel] = {"kind": "AUTHORED", "sha256": sha(STORE / rel)}
    return {"store": "URBAN_RULE_STORE", "version": "1.0.0",
            "rule_sets": {"1.4.0": ["owner_library/URBAN_PROJECTS_RULE_LIBRARY_1.4.0.json"],
                          "1.5.0": ["owner_library/URBAN_PROJECTS_RULE_LIBRARY_1.4.0.json",
                                    "owner_decisions/URBAN_RULES_1.5.0.json"],
                          # T-461: 1.6.0 .. 1.8.0 registered; resolved by engine/source/rule_store_v2.py (opt-in);
                          # engine/source/rule_store.py (V1, default 1.5.0) is unchanged
                          **{v: ["owner_library/URBAN_PROJECTS_RULE_LIBRARY_1.4.0.json"]
                             + [f"owner_decisions/URBAN_RULES_{w}.json" for w in ("1.5.0", "1.6.0", "1.7.0", "1.8.0")[:i + 2]]
                             for i, v in enumerate(("1.6.0", "1.7.0", "1.8.0"))}},
            "resolvers": {"engine/source/rule_store.py": ["1.4.0", "1.5.0"],
                          "engine/source/rule_store_v2.py": ["1.4.0", "1.5.0", "1.6.0", "1.7.0", "1.8.0"]},
            "latest_owner_approved": "1.5.0",
            "files": files,
            "referenced_not_copied": {p: sha(ROOT / p) for p in REFERENCED},
            "rule": "copies and exports are byte-equal to what their source gives; authored files change only with a new "
                    "version; the structural convention profiles are referenced in place (frozen packages pin them)"}


def build():
    for rel, src in COPIES.items():
        shutil.copyfile(ROOT / src, STORE / rel)
    for rel, (_src, fn) in EXPORTS.items():
        (STORE / rel).write_text(export_text(fn), encoding="utf-8")
    (STORE / "RULES_MANIFEST.json").write_text(json.dumps(manifest(), indent=1, sort_keys=True) + "\n", encoding="utf-8")


def check():
    """-> list of drift messages (empty when the store, its sources and the manifest agree)."""
    out = []
    m = json.loads((STORE / "RULES_MANIFEST.json").read_text(encoding="utf-8"))
    for rel, rec in m["files"].items():
        if sha(STORE / rel) != rec["sha256"]:
            out.append(f"store file changed: rules/{rel}")
        if rec.get("source") and sha(ROOT / rec["source"]) != rec["source_sha256"]:
            out.append(f"source changed since the copy: {rec['source']}")
    for rel, src in COPIES.items():
        if (STORE / rel).read_bytes() != (ROOT / src).read_bytes():
            out.append(f"copy differs from its source: rules/{rel}")
    for rel, (_src, fn) in EXPORTS.items():
        if (STORE / rel).read_text(encoding="utf-8") != export_text(fn):
            out.append(f"export differs from the live register: rules/{rel}")
    for p, h in m["referenced_not_copied"].items():
        if sha(ROOT / p) != h:
            out.append(f"referenced profile changed: {p}")
    return out


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "check"
    if cmd == "build":
        build()
        print("rules/RULES_MANIFEST.json written")
        return 0
    problems = check()
    print(json.dumps({"drift": problems}, indent=1))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
