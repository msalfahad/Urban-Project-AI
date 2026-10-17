"""M9 S1 package: the examples rebuild from the engine byte for byte, the frozen route tools are unchanged since the
S1 base commit, no external benchmark figure or forbidden number appears in the S1 code, tests or outputs, the hygiene
patterns never match, Arabic appears only as the controlled construction vocabulary, and no workbook / PDF is tracked."""

from __future__ import annotations

import csv
import importlib.util
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "urban_m9_s1"
BASE = "8177ccf"
FROZEN = ("tools/urban_boq_m2.py", "tools/urban_project_run.py", "tools/urban_structural_boq.py",
          "engine/source/provisional_estimate.py", "engine/source/generic_route.py", "engine/source/scope_quantities.py",
          "engine/source/family_coverage.py", "engine/source/waste_procurement.py", "engine/boq_m1_xlsx.py",
          "data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json")
S1_CODE = ("engine/source/rule_store.py", "engine/source/material_spec.py", "engine/source/boq_line.py",
           "engine/source/material_result.py", "engine/source/coverage_census.py", "engine/source/tile_layout.py",
           "engine/source/membrane_layout.py", "engine/source/room_boq.py", "engine/boq_room_workbook.py",
           "tools/urban_boq_m9.py", "tools/m9_rules_manifest.py")
AUTHORED = ("rules/owner_decisions/URBAN_RULES_1.5.0.json", "rules/materials/URBAN_MATERIAL_SPECS_1.0.0.json",
            "rules/coverage/BOQ_FAMILY_MASTER_1.0.0.json")
DELIVERABLES = ("00_README.md", "04_IMPLEMENTED_VS_FUTURE.md", "01_TILE_COMPARISON_3x2_BATHROOM.csv",
                "01_TILE_COMPARISON_3x2_BATHROOM.md", "02_MEMBRANE_ROLL_LAYOUT_EXAMPLE.csv",
                "02_MEMBRANE_ROLL_LAYOUT_EXAMPLE.md", "03_SYNTHETIC_ROOM_BOQ.md", "SYNTHETIC_ROOMS_S1.json",
                "build_examples.py")
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|(?i:als[ey]?n[ya]?an)")
ARABIC = re.compile(r"[؀-ۿ]+")
FORBIDDEN_NUMBERS = (44.19, 352.436075, 77.6305, 75.09, 39.7515, 65.965875, 59.8174, 21.8328, 12.348, 337.812, 333.173,
                     22.619, 22.916)


def _files():
    out = [ROOT / f for f in S1_CODE + AUTHORED]
    out += [p for p in PKG.iterdir() if p.is_file() and p.suffix in (".md", ".csv", ".json", ".py")]
    out += [p for p in (ROOT / "tests/m9_foundation").glob("*.py") if p.name != Path(__file__).name]  # this file
    return out                                                                   # holds the patterns themselves


def test_deliverables_present():
    missing = [d for d in DELIVERABLES if not (PKG / d).is_file()]
    assert not missing, missing


def test_examples_rebuild_byte_for_byte():
    spec = importlib.util.spec_from_file_location("m9_s1_examples", PKG / "build_examples.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for name, text in mod.build().items():
        assert (PKG / name).read_text(encoding="utf-8") == text, name


def test_frozen_route_files_are_unchanged_since_the_s1_base():
    for f in FROZEN:
        old = subprocess.run(["git", "-C", str(ROOT), "show", f"{BASE}:{f}"], capture_output=True, check=True).stdout
        assert (ROOT / f).read_bytes() == old, f


def test_no_external_figure_or_forbidden_number():
    ext = set()
    for r in csv.DictReader((ROOT / "research/urban_engine_m5_concrete_reconciliation/02C_FAMILY_TOTALS.csv").open(
            encoding="utf-8")):
        for col in ("FREELANCER_M3", "UC4N_M3", "CHRISTIANNP_M3"):
            try:
                x = float(r[col])
            except ValueError:
                continue
            if x:
                ext.add(round(x, 3))
    nums = re.compile(r"-?\d+\.\d+")
    method_id = re.compile(r"ARCH_TAKEOFF_V\d+\.\d+")     # a method identifier (ARCH_TAKEOFF_V2.4) is not a figure
    for p in _files():
        text = p.read_text(encoding="utf-8")
        found = {round(float(m), 3) for m in nums.findall(method_id.sub("", text))}
        assert not (found & ext), p.name                       # the value itself is never printed
        assert not any(v and abs(v - x * k) <= 1e-4 * abs(x * k) for v in found for x in FORBIDDEN_NUMBERS
                       for k in (1, 1000)), p.name
        assert "ae608411" not in text and "d025d9f0-" not in text, p.name


def test_hygiene_and_controlled_arabic_vocabulary():
    from engine.source import boq_line as BL
    from engine.source import rule_store as RS
    vocab = set()
    for _en, ar, _t, _u in BL.ITEMS.values():
        vocab.update(ARABIC.findall(ar))
    for f in RS.family_master()["families"]:
        vocab.update(ARABIC.findall(f["item_ar"]))
    for s in RS.material_specs()["specs"]:
        vocab.update(ARABIC.findall(s.get("name_ar") or ""))
    for r in RS.rule_set(include_proposed=True)["rules"].values():
        for w in (r.get("names") or {}).get("ar", []):
            vocab.update(ARABIC.findall(w))
    vocab.update(["حمام", "صالة", "مطبخ", "غرفة", "نوم", "مخزن"])          # generic room words of the fixture
    for p in _files():
        text = p.read_text(encoding="utf-8")
        assert not HYGIENE.search(text), p.name
        stray = set(ARABIC.findall(text)) - vocab
        assert not stray, (p.name, len(stray))


def test_no_workbook_or_pdf_is_tracked_in_the_package():
    tracked = subprocess.run(["git", "-C", str(ROOT), "ls-files", "research/urban_m9_s1", "rules"], capture_output=True,
                             text=True).stdout.split()
    assert not [t for t in tracked if t.endswith((".xlsx", ".pdf", ".dxf", ".dwg", ".png", ".zip"))]
