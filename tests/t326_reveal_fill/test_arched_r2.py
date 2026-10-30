"""T-326 r2 (D-T326-1): rule R-T326-2, an ARCHED opening's reveal = 2 x d x springing + d x developed arch length,
never the enclosing / band-crown rectangle. Normal and adverse on the non-Alsenan villa V326, plus the Alsenan
correction ledger cross-checked against the merged T-238 outlines (no drawing is read here).

Villa V326 extra window W4 (by hand): w 1.00, semicircular head r 0.50, springing 1.40 above the sill, crown 1.90,
outside depth 0.08 (frame flush with the room face):
  jambs 2 x 0.08 x 1.40 = 0.224 m2; head soffit 0.08 x (pi x 0.50 = 1.570796) = 0.125664 m2; line 0.349664 m2
  the enclosing rectangle would give 2 x 0.08 x 1.90 + 0.08 x 1.00 = 0.384 m2 (+9.8 %): refused.
"""
from __future__ import annotations

import csv
import hashlib
import math
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t326"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_arched_correction as BC  # noqa: E402
import t326_inputs as T  # noqa: E402
import test_arch_v3028 as V  # noqa: E402
from engine.source import arch_v3028 as A  # noqa: E402

ARC = math.pi * 0.50
W4_OUTLINE = {"shape": "ARCHED", "width_m": 1.0, "spring_m": 1.40, "crown_m": 1.90, "arch_length_m": ARC,
              "status": "DRAWING-CONFIRMED", "source_task": "T-238"}


def _w4(jambs, head):
    return {"opening": "W4", "kind": "WINDOW", "floor": "GF", "side": "OUT", "item_code": "ARCH.WINDOW_REVEAL",
            "group": "JAMBS_HEAD", "status": "VALUED", "rooms": "GF-03", "source_task": "T-313",
            "outline": W4_OUTLINE,
            "components": [V._c("JAMBS", jambs, "2 x 0.080 x 1.400"), V._c("HEAD", head, "0.080 x 1.5708")]}


def _doc(add, outlines=None):
    lines = V.lines_3027()
    d = V.doc(lines)
    d["adds"].append(add)
    d["outlines"] = {"W4": W4_OUTLINE} if outlines is None else outlines
    return lines, d


# ------------------------------------------------------------------------------------------------ normal
def test_arched_window_on_its_outline():
    lines, d = _doc(_w4(0.224, 0.08 * ARC))
    _l, out, ident, _ch, _log = V.run(d, lines)
    w4 = V._by(out, "ARCH.WINDOW_REVEAL", "W4:OUT:JAMBS_HEAD")[0]
    assert w4["measured_net"] == pytest.approx(0.349664, abs=1e-6)
    rec = w4["calculation"]["inputs"][A.REC_KEY]
    assert rec["outline_rule"] == "R-T326-2" and rec["outline"]["spring_m"] == 1.40
    assert ident["opening_reveals"]["added_valued"] == 5      # W1, W2 x2, D1 + W4


def test_rectangular_window_unchanged_by_the_rule():
    """W1 / W2 have no outline record: their lines are those of r1 byte for byte."""
    _l, out_r1, *_ = V.run()
    lines, d = _doc(_w4(0.224, 0.08 * ARC))
    _l2, out_r2, *_ = V.run(d, lines)
    from engine.source import arch_v30 as A30
    r1 = {ln["line_id"]: A30.line_sha(ln) for ln in out_r1}
    r2 = {ln["line_id"]: A30.line_sha(ln) for ln in out_r2}
    assert set(r2) - set(r1) and all(r2[k] == v for k, v in r1.items())
    w1 = V._by(out_r2, "ARCH.WINDOW_REVEAL", "W1:OUT:JAMBS_HEAD")[0]
    assert w1["measured_net"] == pytest.approx(0.336) and "outline" not in w1["calculation"]["inputs"][A.REC_KEY]


# ------------------------------------------------------------------------------------------------ adverse
def test_arched_window_on_its_rectangle_refused():
    lines, d = _doc(_w4(2 * 0.08 * 1.90, 0.08 * 1.00))            # band-crown / enclosing rectangle
    with pytest.raises(A.InputsError, match="R-T326-2"):
        A.load_inputs(d, V.PID)


def test_jambs_to_the_crown_with_arch_head_refused():
    lines, d = _doc(_w4(2 * 0.08 * 1.90, 0.08 * ARC))
    with pytest.raises(A.InputsError, match="arched outline value"):
        A.load_inputs(d, V.PID)


def test_chord_instead_of_arc_refused():
    lines, d = _doc(_w4(0.224, 0.08 * 1.00))                      # head on the chord (= width)
    with pytest.raises(A.InputsError, match="R-T326-2"):
        A.load_inputs(d, V.PID)


def test_arched_face_without_depth_refused():
    a = _w4(0.224, 0.08 * ARC)
    a["components"][0]["depth_m"] = None
    lines, d = _doc(a)
    with pytest.raises(A.InputsError, match="without a reveal depth"):
        A.load_inputs(d, V.PID)


@pytest.mark.parametrize("bad", [{"spring_m": None}, {"arch_length_m": 0}, {"spring_m": 2.0}, {"shape": "RECT"}])
def test_bad_outline_refused(bad):
    lines, d = _doc(_w4(0.224, 0.08 * ARC), {"W4": dict(W4_OUTLINE, **bad)})
    with pytest.raises(A.InputsError, match="outline W4"):
        A.load_inputs(d, V.PID)


# ------------------------------------------------------------------------------------------------ Alsenan ledger
def test_correction_ledger_is_the_build_and_matches_t238():
    assert BC.OUT.read_text(encoding="utf-8") == BC.text(BC.rows())
    rows = list(csv.DictReader(BC.OUT.open(encoding="utf-8")))
    got = {(r["opening"], r["component"]): float(r["m2"]) for r in rows}
    # T-238 outlines (merged 242e50b2): W15 / W16 springing 2.1609, arch 2.5243; W26 springing 1.05, arch 1.9709
    assert got == pytest.approx({("W15", "JAMBS"): 2 * 0.08 * 2.1609, ("W15", "HEAD"): 0.08 * 2.5243,
                                 ("W16", "JAMBS"): 2 * 0.08 * 2.1609, ("W16", "HEAD"): 0.08 * 2.5243,
                                 ("W26", "JAMBS"): 2 * 0.10 * 1.05, ("W26", "HEAD"): 0.10 * 1.9709}, abs=1e-9)
    assert {r["ledger_basis"] for r in rows} == {"2 x 0.080 x 3.100", "0.080 x 1.550", "2 x 0.100 x 1.700",
                                                 "0.100 x 1.200"}          # the rectangles replaced
    # the Checker's own 2026-10-30 walk (arch chain 2.5240 / 1.9706): within 0.0001 m2 per line
    assert 2 * 0.08 * 2.1609 + 0.08 * 2.5240 == pytest.approx(0.5477, abs=1e-4)
    assert 2 * 0.10 * 1.05 + 0.10 * 1.9706 == pytest.approx(0.4071, abs=1e-4)


def test_merged_t313_ledger_untouched():
    assert hashlib.sha256(T.LED.read_bytes()).hexdigest() == T.PINS[T.LED]


def test_alsenan_arched_lines_and_total():
    doc = T.build("p")
    inp = A.load_inputs(doc, "p")
    jh = {a["opening"]: round(sum(c["m2"] for c in a["components"]), 6) for a in inp["adds"]
          if a["opening"] in ("W15", "W16", "W26") and a["group"] == "JAMBS_HEAD"}
    assert jh == {"W15": 0.547688, "W16": 0.547688, "W26": 0.40709}
    assert set(doc["outlines"]) == {"W15", "W16", "W26"}
    total = sum(f["m2"] for f in doc["fills"]) + sum(c["m2"] for a in doc["adds"] if a["status"] == "VALUED"
                                                     and a["item_code"] == "ARCH.WINDOW_REVEAL" for c in a["components"])
    assert round(total, 6) == 12.438866                       # r1 12.6364 - 0.197534


def test_alsenan_rectangle_back_in_refused():
    doc = T.build("p")
    for a in doc["adds"]:
        if a["opening"] == "W15" and a["group"] == "JAMBS_HEAD":
            a["components"] = [dict(c, m2=0.496 if c["component"] == "JAMBS" else 0.124) for c in a["components"]]
    with pytest.raises(A.InputsError, match="R-T326-2"):
        A.load_inputs(doc, "p")


def test_edited_correction_stops_the_build(tmp_path, monkeypatch):
    cp = tmp_path / "ARCHED_REVEAL_CORRECTION_T326.csv"
    shutil.copy(T.ARC, cp)
    cp.write_text(cp.read_text(encoding="utf-8").replace("0.345744", "0.496", 1), encoding="utf-8")
    monkeypatch.setattr(T, "ARC", cp)
    monkeypatch.setitem(T.PINS, cp, hashlib.sha256(cp.read_bytes()).hexdigest())    # even re-pinned
    with pytest.raises(T.PinError, match="not the T-238 outline value"):
        T.build("p")
