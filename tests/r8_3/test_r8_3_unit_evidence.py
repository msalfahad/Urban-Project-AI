"""R8.3 — the real-source unit-evidence extractor emits EVIDENCE; the resolver decides (review §6-§7)."""

from __future__ import annotations

from engine.source import findings as F
from engine.source import frame as FR
from engine.source.cad import unit_evidence as UE

SHA = "c" * 64


def decode(insunits, ratio, n=3, notes=("1:100",), extra_ratio=None):
    objs = [{"object": "DIMSTYLE", "handle": [0, 1, 39], "name": "S1", "DIMLFAC": ratio}]
    h = 100
    for i in range(n):
        objs.append({"type": 21, "handle": [0, 2, h + i], "_subclass": "AcDbRotatedDimension", "dim_rotation": 0.0,
                     "xline1_pt": [0.0, 0.0, 0.0], "xline2_pt": [100.0 + i, 0.0, 0.0],
                     "act_measurement": (100.0 + i) * ratio, "dimstyle": [5, 1, 39, 39], "entmode": 2})
    if extra_ratio:
        objs.append({"type": 21, "handle": [0, 2, 999], "_subclass": "AcDbRotatedDimension", "dim_rotation": 0.0,
                     "xline1_pt": [0.0, 0.0, 0.0], "xline2_pt": [50.0, 0.0, 0.0],
                     "act_measurement": 50.0 * extra_ratio, "dimstyle": [5, 1, 39, 39], "entmode": 2})
    for j, t in enumerate(notes):
        objs.append({"type": 1, "handle": [0, 2, 500 + j], "text_value": f"SCALE {t}", "entmode": 2})
    return {"HEADER": {"INSUNITS": insunits}, "OBJECTS": objs}


def resolve(dec):
    x = UE.extract(dec, SHA)
    return x, FR.unit_context(SHA, "MODEL_SPACE", FR.MODEL_SPACE, x["evidence"], insunits=dec["HEADER"]["INSUNITS"])


def test_extractor_emits_roles_and_never_a_status():
    x = UE.extract(decode(4, 0.1), SHA)
    roles = {r["role"] for r in x["rows"]}
    assert roles == {"DECLARATION", "CANDIDATE"}
    fam = next(r for r in x["rows"] if r["role"] == "CANDIDATE")
    assert fam["parsed_ratio"] == 0.1 and fam["count"] == 3 and len(fam["source_handles"]) == 3
    assert {i["display_unit"] for i in fam["possible_interpretations"]} == {"mm", "cm", "m", "in", "ft"}
    assert "ASSUMPTION:DISPLAY_IN_STANDARD_UNIT" in fam["lineage"]
    assert not any("status" in r for r in x["rows"])


def test_declaration_compatible_with_the_dimension_set_is_only_unconfirmed():
    """geometry 100, DIMLFAC 0.1, display 10: '10' could be mm, cm, m, in, ft. The declared mm
    fits one member; that is compatibility, not support (review §3)."""
    _, u = resolve(decode(4, 0.1))
    assert u.status == FR.UNCONFIRMED and u.machine_support == "DECLARATION_ONLY"
    assert FR.FINAL_MEASUREMENT not in u.allowed_use and u.contesting_candidates == ()


def test_declaration_outside_every_interpretation_is_contested():
    _, u = resolve(decode(1, 100.0))                     # inch declared; ratio 100 excludes 25.4 mm/unit
    assert u.status == FR.CONFLICT and len(u.contesting_candidates) == 1
    assert F.UNIT_DECLARATION_CONFLICT in {f.code for f in u.findings}


def test_unitless_declaration_with_only_candidates_is_blocked_not_guessed():
    _, u = resolve(decode(0, 1.0))
    assert u.status == FR.BLOCKED and u.native_to_mm is None


def test_two_dimension_families_and_mixed_scale_notes_raise_findings():
    x = UE.extract(decode(4, 0.1, notes=("1:100", "1:500"), extra_ratio=0.2), SHA)
    assert len(x["families"]) == 2
    assert sum(1 for f in x["findings"] if f.code == F.REGION_MIXED_SCALE_NOTES) == 2


def test_one_scale_ratio_written_two_ways_is_not_mixed():
    x = UE.extract(decode(5, 1.0, notes=("1:100", "1/100")), SHA)
    assert not [f for f in x["findings"] if f.code == F.REGION_MIXED_SCALE_NOTES]
