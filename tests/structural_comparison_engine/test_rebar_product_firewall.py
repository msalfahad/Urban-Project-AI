"""Firewall between ACCURATE_BOQ_REBAR and ROUGH_REBAR_SUMMARY (architecture correction before S4).

Static (AST) transitive import closure plus a runtime import check:
  * ACCURATE modules and builders never reach rough_rebar_sanity, the rough profile, the report layer, or any
    reference-QS / oracle comparison module, and carry no freelancer or oracle quantity;
  * the ROUGH engine never reaches an accurate module (its only input is the concrete register);
  * no arrow between the two engines - only the report layer reads both;
  * accurate BBS / known-answer tests do not use the rough engine or profile.
Plus behaviour: an accurate part with an estimating basis is refused, the rough engine refuses steel fields, variance
never changes the accurate summary, the BOQ shows two separate sections with the mandatory note."""

from __future__ import annotations

import ast
import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rebar_product_registry as RP  # noqa: E402

from engine.source import accurate_boq_rebar as AB  # noqa: E402
from engine.source import rebar_boq_sections as BS  # noqa: E402
from engine.source import rebar_sanity_variance as SV  # noqa: E402
from engine.source import rough_rebar_sanity as RR  # noqa: E402

SEARCH_DIRS = [ROOT / "research" / "external_engine_lab"] + sorted(p for p in (ROOT / "research").iterdir()
                                                                   if p.is_dir())
FORBIDDEN_STRINGS = ("URBAN_ROUGH_REBAR_PROFILE", "rough_rebar_sanity", "rebar_sanity_variance", "ROUGH_REBAR_SUMMARY",
                     "FREELANCER_QS_REFERENCE", "EXTERNAL_ORACLE", "alsenan_multi_engine_comparison",
                     "ae608411ed5b9e64811a15c353adbdd017fa3e51abfdffcf0aa1454b85d1957c",   # freelancer workbook sha
                     "d025d9f0-")                                                          # its upload file id
# Oracle tool names also appear as software-donor licence records, so oracle QUANTITIES are caught by value:
# reference-QS / oracle quantities of the comparison round (S3.1 brief §26) - never a constant upstream of a BBS
FORBIDDEN_NUMBERS = (44.19, 352.436075, 77.6305, 75.09, 39.7515, 65.965875, 59.8174, 21.8328, 12.348,
                     337.812, 333.173, 22.619, 22.916)


def forbidden_number(c):
    """A reference-QS / oracle figure, also in kg (x1000) or rounded to 4-5 significant figures."""
    if isinstance(c, bool) or not isinstance(c, (int, float)) or not c:
        return False
    return any(abs(c - x * k) <= 1e-4 * abs(x * k) for x in FORBIDDEN_NUMBERS for k in (1, 1000))


def _resolve(name, importer, level=0):
    """File(s) an import loads: the module plus every package __init__ on the way (runtime-faithful)."""
    out = []
    if level:
        base = importer.parent
        for _ in range(level - 1):
            base = base.parent
        parts = name.split(".") if name else []
        cand = base.joinpath(*parts)
        for f in (cand.with_suffix(".py"), cand / "__init__.py"):
            if f.exists():
                out.append(f)
        if (base / "__init__.py").exists():
            out.append(base / "__init__.py")
        return out
    parts = name.split(".")
    if parts[0] == "engine":
        for i in range(1, len(parts) + 1):
            p = ROOT.joinpath(*parts[:i])
            if (p / "__init__.py").exists():
                out.append(p / "__init__.py")
            elif p.with_suffix(".py").exists():
                out.append(p.with_suffix(".py"))
        return out
    if len(parts) == 1:
        for d in [importer.parent] + SEARCH_DIRS:
            f = d / f"{parts[0]}.py"
            if f.exists():
                return [f]
    return out


def _imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                out += _resolve(a.name, path)
        elif isinstance(n, ast.ImportFrom):
            mod = n.module or ""
            if n.level:
                out += _resolve(mod, path, n.level)
                for a in n.names:
                    out += _resolve(f"{mod}.{a.name}" if mod else a.name, path, n.level)
            else:
                out += _resolve(mod, path)
                for a in n.names:
                    out += [f for f in _resolve(f"{mod}.{a.name}", path) if f.stem == a.name]
    return out


def closure(start):
    seen, todo = set(), [ROOT / s for s in start]
    while todo:
        f = todo.pop().resolve()
        if f in seen or not f.exists():
            continue
        seen.add(f)
        todo += _imports(f)
    return seen


def rel(fs):
    return {str(f.relative_to(ROOT)) for f in fs}


def _constants(path):
    """String and numeric constants that are not docstrings."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docs = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body and \
                isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant):
            docs.add(id(n.body[0].value))
    return [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and id(n) not in docs]


FORBIDDEN_FOR_ACCURATE = set(RP.ROUGH_MODULES) | set(RP.REPORT_MODULES) | set(RP.COMPARISON_MODULES)


@pytest.fixture(scope="module")
def accurate_closure():
    return closure(RP.ACCURATE_MODULES + RP.ACCURATE_BUILDERS)


def test_accurate_closure_never_reaches_rough_report_or_comparison(accurate_closure):
    reached = rel(accurate_closure)
    assert set(RP.ACCURATE_MODULES) <= reached
    assert not (reached & FORBIDDEN_FOR_ACCURATE), reached & FORBIDDEN_FOR_ACCURATE
    assert not [r for r in reached if any(r.startswith(d) for d in RP.COMPARISON_DIRS)]


def test_accurate_closure_carries_no_rough_profile_reference_or_oracle_quantity(accurate_closure):
    for f in accurate_closure:
        for c in _constants(f):
            if isinstance(c, str):
                hit = [s for s in FORBIDDEN_STRINGS if s in c]
                assert not hit, (str(f.relative_to(ROOT)), hit)
            else:
                assert not forbidden_number(c), (str(f.relative_to(ROOT)), c)


def test_rough_engine_never_reaches_an_accurate_module():
    reached = rel(closure(RP.ROUGH_MODULES))
    assert reached == set(RP.ROUGH_MODULES)                     # stdlib only, no Urban import at all
    assert not (reached & (set(RP.ACCURATE_MODULES) | set(RP.ACCURATE_BUILDERS) | set(RP.REPORT_MODULES)))


def test_no_arrow_between_the_engines_only_the_report_layer_reads_both():
    for m in RP.REPORT_MODULES:
        reached = rel(closure([m])) - {m}
        assert "engine/source/rough_rebar_sanity.py" in reached and "engine/source/accurate_boq_rebar.py" in reached
        assert not (reached & set(RP.ACCURATE_BUILDERS))
    # the accurate collector is stdlib only as well
    assert rel(closure(["engine/source/accurate_boq_rebar.py"])) == {"engine/source/accurate_boq_rebar.py"}


def test_every_rebar_module_in_engine_is_declared():
    declared = set(RP.ACCURATE_MODULES) | set(RP.ROUGH_MODULES) | set(RP.REPORT_MODULES) | set(RP.SANITY_QA_MODULES) | \
        set(RP.COMPARISON_MODULES) | set(RP.OTHER_REBAR_AWARE)
    words = ("rebar", "bbs", "reinforc")
    found = {str(p.relative_to(ROOT)) for p in (ROOT / "engine").rglob("*.py")
             if any(w in p.read_text(encoding="utf-8", errors="ignore").lower() for w in words)}
    assert found <= declared, sorted(found - declared)


def test_accurate_modules_reach_sanity_qa_only_through_deprecated_shims():
    """bbs_steel.ratio_check / rebar_model.ratio_qa moved to the QA layer; the accurate code keeps only a lazy
    module __getattr__ wrapper (no top-level import, no call from accurate logic)."""
    for m in RP.ACCURATE_MODULES:
        tree = ast.parse((ROOT / m).read_text(encoding="utf-8"))
        shims = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "__getattr__"]
        inside = {id(x) for f in shims for x in ast.walk(f)}
        for n in ast.walk(tree):
            if isinstance(n, (ast.Import, ast.ImportFrom)) and id(n) not in inside:
                names = [a.name for a in n.names] + [n.module or ""] if isinstance(n, ast.ImportFrom) else \
                    [a.name for a in n.names]
                assert not any("rebar_sanity_qa" in x for x in names), m
        src = (ROOT / m).read_text(encoding="utf-8")
        assert "def ratio_check(" not in src and "def ratio_qa(" not in src, m
    from engine.source import rebar_sanity_qa as QA
    assert QA.ratio_band_check(30000, 240.0)["status"] == "OK"
    assert QA.intensity_qa(100.0, volume_m3=2.0)["use"] == "QA_ONLY"


def test_runtime_import_of_accurate_engines_loads_no_rough_module():
    mods = [m[:-3].replace("/", ".") for m in RP.ACCURATE_MODULES]
    code = ("import json, sys; sys.path.insert(0, %r)\n" % str(ROOT) +
            "".join(f"import {m}\n" for m in mods) + "print(json.dumps(sorted(sys.modules)))")
    loaded = set(json.loads(subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                                           check=True, cwd=str(ROOT)).stdout))
    for bad in ("engine.source.rough_rebar_sanity", "engine.source.rebar_sanity_variance",
                "engine.source.rebar_boq_sections", "engine.source.comparison_scope",
                "engine.source.source_oracle_comparison", "engine.source.cad_oracle"):
        assert bad not in loaded, bad


def test_accurate_bbs_tests_do_not_use_the_rough_engine_or_profile():
    bbs_tests = ["tests/column_rebar_engine/test_column_rebar.py", "tests/alsenan_rebar_truth/test_rebar_truth_r3.py",
                 "tests/alsenan_rebar_source_exhaustion/test_rebar_r4.py",
                 "tests/alsenan_structural_census/test_column_rebar_s3.py",
                 "tests/alsenan/test_v3b_engines_synthetic.py", "tests/test_finance_outturn_steel.py"]
    for t in bbs_tests:
        src = (ROOT / t).read_text(encoding="utf-8")
        assert "rough_rebar_sanity" not in src and "URBAN_ROUGH_REBAR_PROFILE" not in src, t
        for c in _constants(ROOT / t):
            assert not forbidden_number(c), (t, c)


# ------------------------------------------------------------------------------------------------- behaviour
PROFILE = json.loads((ROOT / RP.ROUGH_PROFILES[0]).read_text(encoding="utf-8"))


def part(pid, st, kg, cat="COLUMNS", comp="COLUMN_MAIN_BAR", basis=("DRAWING_OCCURRENCE", "SCHEDULE")):
    return {"part_id": pid, "category": cat, "component": comp, "state": st, "kg": kg, "basis": list(basis)}


def occ(oid, ec, m3, st="VERIFIED"):
    return {"occurrence_id": oid, "element_class": ec, "concrete_m3": m3, "concrete_state": st}


def test_forbidden_number_catches_unit_and_rounding_variants():
    assert forbidden_number(44190) and forbidden_number(352.44) and forbidden_number(44.19)
    assert not forbidden_number(30000) and not forbidden_number(240.0) and not forbidden_number(True)


def test_profile_is_owner_estimating_rule_sanity_only():
    RR.validate_profile(PROFILE)
    assert PROFILE["authority"] == "URBAN_OWNER_ESTIMATING_RULE" and PROFILE["use"] == "SANITY_CHECK_ONLY"
    assert PROFILE["ratios_kg_per_m3"] == {"FOUNDATIONS_RELATED": 75, "GROUND_BEAMS_AND_GROUND_SLAB": 130,
                                           "WALLS_AND_COLUMNS": 200, "BEAMS": 150, "SLABS": 90,
                                           "STAIRS_AND_DOME": 179, "SWIMMING_POOL": 121}
    with pytest.raises(RR.RoughRebarError):
        RR.validate_profile(dict(PROFILE, authority="URBAN_OWNER_RULE"))
    assert "BBS rules" in PROFILE["not"]


@pytest.mark.parametrize("basis", ["ROUGH_RATIO", "KG_PER_M3", "FREELANCER_QS_REFERENCE", "EXTERNAL_ORACLE",
                                   "ROUGH_REBAR_SUMMARY", "BENCHMARK"])
def test_accurate_refuses_an_estimating_or_reference_basis(basis):
    with pytest.raises(AB.AccurateRebarError):
        AB.summarise([part("p1", "VERIFIED", 10.0, basis=["SCHEDULE", basis])])


def test_accurate_keeps_five_states_and_final_not_established():
    s = AB.summarise([part("a", "VERIFIED", 100.0), part("b", "LOWER_BOUND", 50.0),
                      part("c", "PROVISIONAL", 20.0), part("d", "BLOCKED_MODELLED", 5.0),
                      part("e", "BLOCKED_UNQUANTIFIED", None)])
    c = s["categories"]["COLUMNS"]
    assert (c["verified_kg"], c["lower_bound_kg"], c["provisional_kg"], c["blocked_modelled_kg"],
            c["blocked_unquantified_parts"]) == (100.0, 50.0, 20.0, 5.0, 1)
    assert c["official_status"] == AB.PARTIAL and c["projected_kg"] == 170.0          # blocked never projected
    assert s["project"]["final_rebar"] == AB.FINAL_REBAR_NOT_ESTABLISHED and s["project"]["final_rebar_kg"] is None
    with pytest.raises(AB.AccurateRebarError):
        AB.summarise([part("x", "BLOCKED_UNQUANTIFIED", 12.0)])        # a blocked part is never given a value
    with pytest.raises(AB.AccurateRebarError):
        AB.summarise([part("x", "PROVISIONAL", None)])


def test_official_status_ladder():
    st = lambda ps: AB.summarise(ps)["categories"]["COLUMNS"]["official_status"]  # noqa: E731
    assert st([part("a", "VERIFIED", 1.0)]) == AB.FINAL
    assert st([part("a", "VERIFIED", 1.0), part("b", "LOWER_BOUND", 1.0)]) == AB.LOWER_BOUND
    assert st([part("a", "VERIFIED", 1.0), part("b", "BLOCKED_UNQUANTIFIED", None)]) == AB.PARTIAL
    assert st([part("b", "BLOCKED_UNQUANTIFIED", None)]) == AB.BLOCKED
    s = AB.summarise([part("a", "VERIFIED", 7.0)])
    assert s["project"]["final_rebar"] == AB.FINAL and s["project"]["final_rebar_kg"] == 7.0


def test_rough_engine_takes_concrete_only():
    with pytest.raises(RR.RoughRebarError):
        RR.rough_summary([dict(occ("c", "COLUMN", 1.0), steel_kg=100.0)], PROFILE)
    r = RR.rough_summary([occ("c", "COLUMN", 2.0), occ("s", "SOLID_SLAB", 10.0), occ("b", "BEAM", 1.0, "BLOCKED")],
                         PROFILE)
    assert r["product"] == RR.PRODUCT and r["note"] == RR.MANDATORY_NOTE
    assert r["categories"]["WALLS_AND_COLUMNS"]["rough_kg_modelled_basis"] == 400.0
    assert r["categories"]["SLABS"]["rough_kg_modelled_basis"] == 900.0
    assert r["categories"]["BEAMS"]["rough_kg_modelled_basis"] == 0.0                  # blocked concrete stays out


@pytest.mark.parametrize("ec", ["RAFT", "PILE_CAP", "RETAINING_WALL", "WATER_TANK", "LIFT_WALL", "SPECIAL_RC_ELEMENT"])
def test_unusual_elements_are_not_configured(ec):
    r = RR.rough_summary([occ("x", ec, 3.0)], PROFILE)
    assert not r["categories"] and r["not_configured"][0]["state"] == RR.NOT_CONFIGURED
    assert r["not_configured"][0]["why"] == "needs an explicit owner rule"
    assert RR.category_of(ec) is None


def test_keyword_classifier_does_not_guess_retaining_or_lift_walls():
    r = RR.rough_summary([{"occurrence_id": "w1", "description": "RC retaining wall", "concrete_m3": 2.0,
                           "concrete_state": "VERIFIED"},
                          {"occurrence_id": "w2", "description": "lift wall", "concrete_m3": 1.0,
                           "concrete_state": "VERIFIED"}], PROFILE)
    assert {x["element_class"] for x in r["not_configured"]} == {"RETAINING_WALL", "LIFT_WALL"}


def test_variance_is_sanity_only_and_never_changes_accurate():
    acc = AB.summarise([part("a", "VERIFIED", 300.0), part("s1", "VERIFIED", 1500.0, "SLABS", "SLAB_BOTTOM_X"),
                        part("s2", "BLOCKED_UNQUANTIFIED", None, "SLABS", "SLAB_TOP_SUPPORT")])
    rough = RR.rough_summary([occ("c", "COLUMN", 2.0), occ("s", "SOLID_SLAB", 10.0)], PROFILE)
    a0, r0 = copy.deepcopy(acc), copy.deepcopy(rough)
    v = SV.compare(acc, rough)
    assert acc == a0 and rough == r0
    rows = {r["category"]: r for r in v["rows"]}
    col = rows["WALLS_AND_COLUMNS"]
    assert col["state"] == SV.SANITY_VARIANCE and col["SANITY_VARIANCE_KG"] == -100.0
    assert col["SANITY_VARIANCE_PERCENT"] == -25.0 and SV.REVIEW_FLAG in col["flags"]
    slab = rows["SLABS"]
    assert slab["state"] == SV.SIDE_BY_SIDE and slab["SANITY_VARIANCE_KG"] is None and not slab["flags"]
    text = json.dumps(v).upper()
    assert "MISSING" not in text
    # the accurate result after the comparison is still exactly what summarise produced
    assert AB.summarise([part("a", "VERIFIED", 300.0)])["categories"]["COLUMNS"]["official_status"] == AB.FINAL


def test_boq_has_two_separate_sections_with_the_mandatory_note():
    acc = AB.summarise([part("a", "VERIFIED", 300.0), part("b", "BLOCKED_UNQUANTIFIED", None)])
    rough = RR.rough_summary([occ("c", "COLUMN", 2.0)], PROFILE)
    boq = BS.build(acc, rough, SV.compare(acc, rough))
    s1, s2 = boq["sections"][0], boq["sections"][1]
    assert s1["section_id"] == "ACCURATE_BOQ_REBAR" and s1["title_ar"] == "حديد التسليح الفعلي من المخططات"
    assert s2["section_id"] == "ROUGH_REBAR_SUMMARY" and s2["title_ar"] == "تقدير تقريبي للحديد حسب حجم الخرسانة"
    assert s2["note"] == ("ROUGH REBAR SUMMARY is an estimating and sanity-check tool only. It is not a "
                          "reinforcement takeoff and must not replace the ACCURATE BOQ REBAR / BBS quantity.")
    assert not set(s1["columns"]) & {"RATIO_KG_M3", "ROUGH_STEEL_T", "CONCRETE_M3"}
    assert not set(s2["columns"]) & {"RELEASED_T", "PROVISIONAL_T", "OFFICIAL_STATUS"}
    assert s1["project"]["FINAL_REBAR"] == AB.FINAL_REBAR_NOT_ESTABLISHED
    assert s1["rows"][0]["OFFICIAL_STATUS"] == AB.PARTIAL
    assert boq["sections"][2]["section_id"] == "REBAR_SANITY_VARIANCE"


def test_column_adapter_maps_states_without_estimating():
    parts = [{"part_id": "s|MAIN", "component": "MAIN_BARS", "release_state": "VERIFIED", "kg": 10.0},
             {"part_id": "s|X", "component": "OTHER_EXTRA", "release_state": "BLOCKED", "kg": None},
             {"part_id": "s|T", "component": "TIES", "release_state": "BLOCKED", "kg": 2.0}]
    s = AB.summarise(AB.from_column_rebar(parts))["categories"]["COLUMNS"]
    assert (s["verified_kg"], s["blocked_modelled_kg"], s["blocked_unquantified_parts"]) == (10.0, 2.0, 1)
