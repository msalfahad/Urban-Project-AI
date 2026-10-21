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
            "coverage/BOQ_FAMILY_MASTER_1.0.0.json")
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
                                    "owner_decisions/URBAN_RULES_1.5.0.json"]},
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
