"""M2 generic route end to end on SYNTHETIC villas (tools/synthetic_villa: truth from the design, never from the
engine): quantities, detection, ownership / conservation, drafting defects, the beyond-snap stress case (loss must be
REPORTED), route G through the one-command CLI, and output hygiene. Synthetic drawings share the generator author's
drafting assumptions: these tests prove consistency and robustness to the listed defects, not real-drawing accuracy."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine.source import cad_heal as CH                    # noqa: E402
from engine.source import generic_route as GR               # noqa: E402
from engine.source import member_detection as MD            # noqa: E402
from tools import m2_evaluate as EV                         # noqa: E402
from tools import synthetic_villa as SV                     # noqa: E402
from tools import urban_intake as UI                        # noqa: E402
from tools import urban_boq_m2 as CLI                       # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
HYGIENE = re.compile(r"[؀-ۿ]{3,}")


def _ok(rec, tol=1e-5):
    assert rec["ok"], rec.get("error")
    for k, v in rec["range_ratio_max"].items():                  # a provisional range is never polluted
        assert v <= 2.0, (rec["seed"], k, v)
    for fam, q in rec["quantities"].items():
        assert q["error"] is None or abs(q["error"]) <= tol, (rec["seed"], fam, q)
    for k in ("detect_footings", "detect_beams", "detect_panels"):
        assert rec[k]["recall"] == 1.0 and rec[k]["precision"] == 1.0, (rec["seed"], k, rec[k])


@pytest.mark.parametrize("seed", [3, 8])
@pytest.mark.parametrize("defects", [False, True])
def test_quantities_and_detection(tmp_path, seed, defects):
    _ok(EV.evaluate(seed, tmp_path, defects))


def test_hard_defects_are_closed_and_reported(tmp_path):
    rec = EV.evaluate(4, tmp_path, "hard")
    _ok(rec)
    assert rec["coverage_risk_kinds"].get("HEAL_EXTEND_WIDE", 0) > 0          # every widened snap is in the register


def test_unclosed_cells_are_reported_never_silent(tmp_path, monkeypatch):
    monkeypatch.setattr(CH, "extend_dangling", lambda segs, lays, tgt, **k: (segs, []))
    rec = EV.evaluate(4, tmp_path, "hard")
    assert rec["slab_area"]["missing_m2"] > 1.0                              # the stress case does lose slab
    assert rec["coverage_risk_kinds"].get("SLAB_UNENCLOSED_BAND_SIDE", 0) > 0 and rec["slab_area"]["loss_reported"]


@pytest.fixture(scope="module")
def detected(tmp_path_factory):
    d = tmp_path_factory.mktemp("own")
    dxf = SV.generate(d, 5, defects=True)
    return GR.detect(UI.read(dxf))


def test_ownership_no_concrete_counted_twice(detected):
    for sid, r in detected["sheets"].items():
        if not r.get("slab"):
            continue
        straight = [b for b in r["bands"] if b.get("kind") == "STRAIGHT" and len(b["polygon"]) == 4]
        panels = [f for f in r["slab"]["faces"] if f["class"] == "PANEL"]
        for b in straight:
            for c in r["column_boxes"]:
                assert MD.overlap_area(MD.box_poly(c), b["polygon"]) <= 1e-6 * abs(MD.poly_area(b["polygon"])) + 1
            for f in panels:
                assert MD.overlap_area(f["polygon"], b["polygon"]) <= 1e-6 * abs(MD.poly_area(b["polygon"])) + 1


@pytest.mark.parametrize("defects", [False, True])
def test_conservation_every_square_metre_has_its_design_owner(tmp_path, defects):
    """Per slab sheet: the BEAM faces sum to the design's beam footprint (drawn width x clear span), the COLUMN faces
    to the column sections, the PANEL faces to the design panels - each square metre counted once, by its owner,
    whatever the drafting noise. (The free-standing curved beam has no end caps, so it encloses no face; its
    quantity comes from its band and is checked by the evaluator.)"""
    seed = 6
    dxf = SV.generate(tmp_path, seed, defects=defects)
    D = SV.design(seed)
    T = json.loads((tmp_path / f"villa_{seed}.truth.json").read_text())
    det = GR.detect(UI.read(dxf))
    beams = SV.beams_of(D)
    beam_m2 = sum(b["drawn_B"] * b["clear"] for b in beams)
    col_m2 = sum(c["sec"][0] * c["sec"][1] for c in D["cols"])
    for sid, r in det["sheets"].items():
        if not r.get("slab"):
            continue
        st = r["sheet"]["storey"]
        a = r["slab"]["area_m2"]
        panels_m2 = sum(p["area"] for p in T["component_list"]["panels"] if p["storey"] == st)
        assert a.get("BEAM", 0) == pytest.approx(beam_m2, abs=1e-6), (sid, "BEAM")
        assert a.get("COLUMN", 0) == pytest.approx(col_m2, abs=1e-6), (sid, "COLUMN")
        assert a.get("PANEL", 0) == pytest.approx(panels_m2, abs=1e-6), (sid, "PANEL")


def test_generator_truth_is_independent_of_the_engine():
    src = (ROOT / "tools/synthetic_villa.py").read_text()
    assert not re.search(r"^\s*(from|import)\s+engine", src, re.M)


def test_route_g_end_to_end(tmp_path):
    dxf = SV.generate(tmp_path, 11, defects=True)                           # seed 11: Arabic titles, metres
    prof = tmp_path / "villa_11.profile.json"
    out = tmp_path / "out"
    assert CLI.main(["run", "--drawings", str(dxf), "--profile", str(prof), "--out", str(out), "--no-pdf",
                     "--as-of", "2026-10-10"]) == 0
    s = json.loads((out / "SUMMARY.json").read_text())
    assert s["route"] == "G_GENERIC_ENGINE" and s["totals"]["CONCRETE"]["VERIFIED"] == 0.0
    assert s["totals"]["CONCRETE"]["N_VERIFIED"] == 0                       # a new project is never VERIFIED
    for name in ("STRUCTURAL_BOQ.xlsx", "COVERAGE_RISK.csv", "REBAR_COMPLETENESS.csv", "OVERLAYS.html"):
        assert (out / name).exists(), name
    assert list((out / "overlays").glob("*.svg"))
    for p in out.rglob("*"):
        if p.suffix in (".csv", ".json", ".html", ".svg"):
            assert not HYGIENE.search(p.read_text(encoding="utf-8")), p.name
    states = {r["REBAR_STATE"] for r in csv.DictReader((out / "REBAR_COMPLETENESS.csv").open())}
    assert states <= set(GR.REBAR_STATES)
    nd = s["not_detected_families"]
    assert set(nd) == set(GR.SCOPE_WORDS) and set(nd.values()) <= {"LABELS_FOUND", "NO_LABEL_FOUND"}
    boq = list(csv.DictReader((out / "CONTRACTOR_BOQ.csv").open()))
    assert sum(1 for b in boq if b["SECTION"].startswith("C")) == len(GR.SCOPE_WORDS)


def test_frozen_m1_cli_is_untouched():
    """M2 extends the M1 pipeline from a new module; the frozen M1 CLI must stay byte-identical to its freeze."""
    import hashlib
    man = json.loads((ROOT / "research/alsenan_m1_usable_boq/06_M1_FREEZE_MANIFEST.json").read_text())
    want = man["code"]["tools/urban_structural_boq.py"]
    got = hashlib.sha256((ROOT / "tools/urban_structural_boq.py").read_bytes()).hexdigest()
    assert got == (want if isinstance(want, str) else want.get("sha256"))
