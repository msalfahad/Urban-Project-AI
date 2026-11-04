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
            "coverage/BOQ_FAMILY_MASTER_1.49.0.json",   # T-310 r4: 1.48.0 + the pending V3.0.52 package (B8-01 / B8-02 / B8-03 / B8-09 text; B8-09 owns the two pool layer codes); no owner change; read by no method
            "owner_decisions/URBAN_RULES_1.6.0.json",   # T-158: owner stair rule UP-STAIR-015 over 1.5.0; rule_store not yet
            "owner_decisions/URBAN_RULES_1.7.0.json",   # T-267: owner stair finish-level rule UP-STAIR-016 over 1.6.0; rule_store not yet
            "rulebook/URBAN_COMPANY_RULEBOOK_1.0.0.json",  # T-448: Company Rulebook (owner 2026-11-02); read by company_rulebook_v1 only
            "owner_decisions/URBAN_RULES_1.8.0.json")  # T-461: UP-GEN-003 1.2.0 (Q-73 A) + UP-STAIR-017 (Q-53 C) over 1.7.0; rule_store_v2 only
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
