"""T-456 step 1 (owner directive 2026-11-02 C1): REPRODUCE the m2 x unit^2 defect of FINISH_MATERIALS_TABLE_V1 on a
synthetic hand case and CONFIRM its reachability (static import closure + run-time loaders) from the released
V2.9 + route G path and from the candidate of record (arch_v3041 / tools/urban_boq_m9.py).

Synthetic only: no drawing, no client data. Run from the tree root:
    python3 -I research/agents_t456/t456_reproduce.py [--out research/agents_t456/out/T456_REPRODUCTION.json]
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import finish_materials_table as V1      # noqa: E402
from engine.source import finish_materials_table_v2 as V2   # noqa: E402

TARGET = "engine/source/finish_materials_table.py"
TARGET_MOD = "finish_materials_table"
RELEASED_PATH = ROOT / "research/freeze_integrity/RELEASED_PATH_V2_9_ROUTE_G.json"
CANDIDATE_ENTRIES = ["engine/source/arch_v3041.py", "tools/urban_boq_m9.py"]
DYNAMIC = re.compile(r"importlib|__import__|spec_from_file_location|runpy|exec\(")


# ------------------------------------------------------------------ 1. reproduction (hand case)
def hand_case():
    """20 m2 dry porcelain floor given as an AREA; the same room in mm as a POLYGON (4000 x 5000 mm)."""
    cases = []
    for unit_name, u in (("m", 1.0), ("mm", 0.001)):
        e_area = {"id": f"A-{unit_name}", "floor": "GF", "kind": V1.DRY_FLOOR, "area_m2": 20.0, "unit_m": u}
        s = 1.0 if u == 1.0 else 1000.0
        e_poly = {"id": f"P-{unit_name}", "floor": "GF", "kind": V1.DRY_FLOOR,
                  "polygon": [(0, 0), (4 * s, 0), (4 * s, 5 * s), (0, 5 * s)], "unit_m": u}
        for e in (e_area, e_poly):
            r1, r2 = V1.row(e), V2.row(e)
            cases.append({"id": e["id"], "unit": unit_name, "input": "area_m2 20" if "area_m2" in e else "polygon 4 x 5",
                          "hand_m2": 20.0,
                          # hand: 20 x 0.03 x 1.05 = 0.63 m3; 20 x 0.04 x 1.05 = 0.84 m3; x 8 bags; x 1.1 sand; 20 / 5 bags
                          "hand_mortar_m3": [0.63, 0.84], "hand_cement_bags": [5.04, 6.72],
                          "hand_sand_m3": [0.693, 0.924], "hand_adhesive_bags": 4.0,
                          "v1": {k: r1[k] for k in ("area_m2", "mortar_m3_low", "mortar_m3_high", "cement_bags_low",
                                                     "cement_bags_high", "sand_m3_low", "sand_m3_high", "adhesive_bags")},
                          "v2": {k: r2[k] for k in ("area_m2", "mortar_m3_low", "mortar_m3_high", "cement_bags_low",
                                                     "cement_bags_high", "sand_m3_low", "sand_m3_high", "adhesive_bags")}})
    return cases


# ------------------------------------------------------------------ 2. reachability
def _module_path(name, frm):
    """engine.source.x / from engine.source import x / relative -> repo path, else None."""
    cands = []
    if name:
        cands.append(name.replace(".", "/"))
    for c in cands:
        for p in (ROOT / f"{c}.py", ROOT / c / "__init__.py"):
            if p.is_file():
                return p.relative_to(ROOT).as_posix()
    return None


def imports_of(path):
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    out = set()
    base = Path(path).parent
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                p = _module_path(a.name, None)
                if p:
                    out.add(p)
        elif isinstance(n, ast.ImportFrom):
            mod = n.module or ""
            if n.level:
                pkg = base
                for _ in range(n.level - 1):
                    pkg = pkg.parent
                mod = ".".join([*pkg.parts, *([mod] if mod else [])])
            p = _module_path(mod, None)
            if p:
                out.add(p)
            for a in n.names:
                q = _module_path(f"{mod}.{a.name}" if mod else a.name, None)
                if q:
                    out.add(q)
    # sibling imports used by tools/ scripts that put their own folder on sys.path
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                q = base / f"{a.name}.py"
                if (ROOT / q).is_file():
                    out.add(q.as_posix())
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            q = base / f"{n.module}.py"
            if (ROOT / q).is_file():
                out.add(q.as_posix())
    return out


def closure(entries):
    seen, todo = set(), list(entries)
    while todo:
        p = todo.pop()
        if p in seen or not (ROOT / p).is_file():
            continue
        seen.add(p)
        try:
            todo.extend(imports_of(p) - seen)
        except SyntaxError:
            pass
    return seen


def dynamic_refs(files):
    """Files in the closure that load modules at run time, and whether any string in them names the target."""
    out = []
    for p in sorted(files):
        src = (ROOT / p).read_text(encoding="utf-8")
        if not DYNAMIC.search(src):
            continue
        strings = {n.value for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        hit = sorted(s for s in strings if TARGET_MOD in s)
        out.append({"file": p, "names_target": hit})
    return out


def repo_mentions():
    """Every tracked .py / .json outside docs and rules/coverage that names the module (rules/coverage holds evidence
    citations, not loaders)."""
    hits = []
    for p in sorted(ROOT.rglob("*")):
        rel = p.relative_to(ROOT).as_posix()
        if p.suffix not in (".py", ".json") or not p.is_file() or rel.startswith((".git", "docs/", "rules/coverage/")):
            continue
        if "/.venv/" in f"/{rel}" or rel.startswith(".venv"):
            continue
        try:
            txt = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if TARGET_MOD in txt:
            hits.append(rel)
    return hits


HARNESS = ("research/freeze_integrity/freeze_verify_v2.py", "tools/freeze_verify.py")


def _closure_check(released):
    traced = [p for p in released["code"] if p.endswith(".py") and p not in HARNESS]
    static = closure(["tools/urban_boq_m9.py"])
    missed = sorted(p for p in traced if p not in static)
    return {"runtime_traced_modules": len(traced), "missed_by_static_closure": missed, "pass": not missed}


def reachability():
    released = json.loads(RELEASED_PATH.read_text(encoding="utf-8"))
    # 'code' = the run-time trace (every module imported by a V2.9 run on three synthetic drawings) + static closure;
    # the hub tools/urban_boq_m9.py is listed under 'hubs'
    rel_files = list(released["code"]) + [h["path"] for h in released.get("hubs", ())]
    if not rel_files:
        raise SystemExit("released path spec lists no code: reachability cannot be stated")
    cand = closure(CANDIDATE_ENTRIES)
    # the two run-time loaders in the closure load fixed files (rule_store.py:114 tools/m9_rules_manifest.py;
    # urban_structural_boq.py:61 the structural adapter): follow their static closures too
    runtime_loaded = ["tools/m9_rules_manifest.py", "research/alsenan_m1_usable_boq/alsenan_adapter.py"]
    rt = closure(runtime_loaded)
    return {
        "runtime_loaded_files": runtime_loaded,
        "runtime_loaded_closure_modules": len(rt),
        "target_in_runtime_loaded_closure": TARGET in rt,
        # method check: this static closure of the hub must contain every module the T-467 RUN-TIME trace saw
        # (the trace harness itself excepted), else the static answer above is not trusted
        "closure_method_check": _closure_check(released),
        "released_path_file": RELEASED_PATH.relative_to(ROOT).as_posix(),
        "released_path_modules": len(rel_files),
        "target_in_released_path": TARGET in rel_files,
        "candidate_entries": CANDIDATE_ENTRIES,
        "candidate_closure_modules": len(cand),
        "target_in_candidate_closure": TARGET in cand,
        "runtime_loaders_in_candidate_closure": dynamic_refs(cand),
        "runtime_loaders_in_released_path": dynamic_refs([f for f in rel_files if f.endswith(".py")
                                                          and (ROOT / f).is_file()]),
        "files_naming_the_module": repo_mentions(),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    res = {"task": "T-456", "defect": "finish_materials_table.py:112 area_m2 * unit_m * unit_m",
           "cases": hand_case(), "reachability": reachability()}
    txt = json.dumps(res, indent=1, sort_keys=True) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
