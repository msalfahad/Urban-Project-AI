"""T-488: ARCH_TAKEOFF_V3.0.55 (blockwork wiring conditions, R-T488-1) on the hand-calculated NON-Alsenan villa P279 of
T-279 (its V3.0.26 fill is the base candidate here), normal and adverse.

Villa P279 after V3.0.26 (tests/t279_blockwork_integration): GF t 0.20 parts VERIFIED BLACK 12.900 (W1) | DC WHITE
22.800 (W2 10.800 + W4 part 12.000) | OA WHITE 7.240 (W3); held on the GF parent W4 piece, W5, W6 drop 9.000 - 3.000 d;
1F t 0.15 part VERIFIED BLACK 11.200 (W7), the 1F parent holds nothing else.

Conditions of this villa, by hand:
  (1) 1F is the TOP storey under a ROOF-ONLY plate whose structural level is not printed (only the finished roof).
      W7 4.000 m long was carried at the architectural finished chain 2.80 m (the build-up of the floor below, 0.05,
      silently taken for the roof): at b_r = 0 the clear height is 2.85 -> U = 4.000 x 2.85 = 11.400 m2, L = 4.000 m:
      W7 = 11.400 - 4.000 x b_r m2 (U an upper bound, never a quantity); 11.400 - 4.000 x 0.05 = 11.200 = carried
      (the what-if). -> the 1F VERIFIED BLACK part line is HELD blank; 1F MAS.BLOCK released 11.200 -> 0 lines
      (HELD, never 0); volume terms x 0.15: 1.710 - 0.600 x b_r m3.
  (2) W2's head member has two printed widths (designer conflict X-1): readings 10.800 (drawn) and 10.860
      (schedule) m2. W2 leaves the DC WHITE part: 22.800 -> 12.000 m2 (W4 part); W2 CONFLICT [10.800, 10.860] m2 named
      on the GF parent (volume [2.160, 2.172] m3), outside every total.
  (3) W6's U over the same readings: 9.000 (carried) -> 9.060 (max) m2: 9.060 - 3.000 d (never evaluated).
  Totals: MAS.BLOCK released 54.140 -> 54.140 - 11.200 - 10.800 = 32.140 m2.
"""
from __future__ import annotations

import copy
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v3055 as A  # noqa: E402

T279 = importlib.import_module("tests.t279_blockwork_integration.test_arch_v3026")
PID = T279.PID
SRC = {"T-X": {"file": "conditions.json", "sha256": "c" * 64, "task": "T-X", "merge_commit": "f" * 40,
               "checker_run": "checker gate A (own re-read of the roof plate: no level printed)"}}


def base():
    out, _i, _c, _l, _b = T279.run()
    return out


def _pid(lines, fl):
    return next(ln["line_id"] for ln in lines if ln["item_code"] == "MAS.BLOCK" and ln["location"]["floor"] == fl
                and ln["location"]["element_id"].endswith(f"t={'0.20' if fl == 'GF' else '0.15'}"))


def doc(lines):
    return {"schema": A.INPUTS_SCHEMA, "project": PID, "sources": copy.deepcopy(SRC),
            "roof_datum": {"item": "X-ROOF", "plate": "roof-only plate", "what_if_buildup_m": 0.05,
                           "walls": [{"wall_id": "W7", "parent_line_id": _pid(lines, "1F"), "thickness_m": 0.15,
                                      "carried_m2": 11.2, "upper_m2": 11.4, "length_m": 4.0, "kind": "WHOLE",
                                      "evidence_status": "VERIFIED", "source_task": "T-X"}]},
            "conflicts": [{"wall_id": "W2", "parent_line_id": _pid(lines, "GF"), "thickness_m": 0.20,
                           "carried_m2": 10.8, "range_m2": [10.8, 10.86], "item": "X-1", "low_reading": "drawn",
                           "high_reading": "schedule", "source_task": "T-X"}],
            "drop_upper": [{"wall_id": "W6", "parent_line_id": _pid(lines, "GF"), "thickness_m": 0.20,
                            "carried_upper_m2": 9.0, "upper_m2": 9.06, "item": "X-1", "source_task": "T-X"}],
            "parapets": []}


def run(d=None, b=None):
    b = b or base()
    d = A.load_inputs(d or doc(b), PID)
    ch, log = A.changes_for(d, b)
    out, ident = A.integrate(b, ch)
    return out, ident, ch, log, b


def _released(lines, code):
    return round(sum(ln["measured_net"] for ln in lines if ln["item_code"] == code
                     and ln["evidence_state"] in ("SOURCE_DERIVED", "PROVISIONAL") and ln.get("measured_net")), 6)


def _parts(lines, code, fl):
    return {(ln["calculation"]["inputs"].get("blockwork_fill_v3026") or
             ln["calculation"]["inputs"].get(A.SUPERSEDED_KEY) or {}).get("part"): ln
            for ln in lines if ln["item_code"] == code and ln["location"]["floor"] == fl
            and "#BLOCKWORK:" in (ln["location"]["element_id"] or "")}


# ================================================================================================ normal
def test_hand_values():
    out, ident, ch, log, b = run()
    assert _released(b, "MAS.BLOCK") == 54.14
    assert _released(out, "MAS.BLOCK") == 32.14                 # - W7 11.200 (roof datum) - W2 10.800 (conflict)
    assert _released(out, "ARCH.WALL_PANEL") == 32.14
    assert _released(out, "ARCH.WALL_VOLUME") == round(54.14 * 0 + 12.9 * 0.2 + 12.0 * 0.2 + 7.24 * 0.2, 6)
    gf = _parts(out, "MAS.BLOCK", "GF")
    dc = next(v for k, v in gf.items() if k.startswith("DRAWING-CONFIRMED"))
    assert dc["measured_net"] == 12.0 and dc["evidence_state"] == "SOURCE_DERIVED"
    f1 = next(iter(_parts(out, "MAS.BLOCK", "1F").values()))
    assert f1["evidence_state"] == "BLOCKED_RFI" and f1["measured_net"] is None and f1["bounded_range"] is None
    assert "11.4 - 4 x b_r m2" in f1["rfi"]["question"]
    v1 = next(iter(_parts(out, "ARCH.WALL_VOLUME", "1F").values()))
    assert "1.71 - 0.6 x b_r m3" in v1["rfi"]["question"]


def test_parent_names_roof_conflict_and_drop_upper():
    out, *_ = run()
    by = {ln["line_id"]: ln for ln in out}
    gfp = by[_pid(out, "GF")]
    q = gfp["rfi"]["question"]
    assert "W6 9.06 - 3.0 d" in q and "W6 9.0 - 3.0 d" not in q
    assert "W2 CONFLICT [10.8, 10.86] m2 (X-1)" in q
    assert gfp["measured_net"] is None and gfp["evidence_state"] == "BLOCKED_RFI"
    f1p = by[_pid(out, "1F")]
    rec = f1p["calculation"]["inputs"]["blockwork_fill_v3026"]
    assert rec["parts"] == {} and len(rec["parts_held_v3055"]) == 1
    assert any(h["kind"] == "ROOF_DATUM" and h["upper"] == 11.4 and h["length"] == 4.0 for h in rec["still_held"])


def test_outside_lines_byte_identical_and_totals_only_blockwork():
    out, ident, ch, _l, b = run()
    changed = {c["after"]["line_id"] for c in ch}
    assert ident["replaced"] == len(changed) and ident["added"] == 0
    for x, y in zip(b, out):
        if x["line_id"] not in changed:
            assert A30.line_sha(x) == A30.line_sha(y)
    from engine.source import arch_v304 as A304
    moved = A.check_totals(A304.code_totals(b), A304.code_totals(out))
    assert moved and all(k.split("|")[0] in A.ITEMS for k in moved)
    assert ident["wiring"]["roof_walls"] == ["W7"] and ident["wiring"]["conflicts"] == ["W2"]


def test_write_files(tmp_path):
    b = base()
    d = A.load_inputs(doc(b), PID)
    ch, log = A.changes_for(d, b)
    names, ident, led = A.write(tmp_path, b, ch, log)
    assert "V3_0_55_BOQ_LINES.json" in names and led["integration_package"] is True
    assert (tmp_path / "V3_0_55_DIFF.csv").read_text(encoding="utf-8").count("CHANGED") == ident["replaced"]


# ================================================================================================ adverse
def _refused(mut, match, exc=A.InputsError):
    b = base()
    d = doc(b)
    mut(d, b)
    with pytest.raises((exc, ValueError), match=match):
        run(d, b)


def test_top_storey_taken_from_finished_chain_refused():
    # the carried figure IS the finished-chain what-if: claiming b_r = 0 (U as the quantity) is refused as stale
    _refused(lambda d, b: d["roof_datum"].update(what_if_buildup_m=0.0), "not U - L x")


def test_millimetres_refused():
    _refused(lambda d, b: d["roof_datum"]["walls"][0].update(length_m=4000.0, upper_m2=11.4), "above")


def test_conflict_one_end_refused():
    _refused(lambda d, b: d["conflicts"][0].update(carried_m2=10.86), "low end")


def test_conflict_inverted_range_refused():
    _refused(lambda d, b: d["conflicts"][0].update(range_m2=[10.86, 10.8]), "low .* > high")


def test_upper_below_carried_refused():
    _refused(lambda d, b: d["drop_upper"][0].update(upper_m2=8.9), "upper bound")


def test_stale_piece_refused():
    _refused(lambda d, b: d["conflicts"][0].update(carried_m2=10.7, range_m2=[10.7, 10.86]), "stale")


def test_wall_twice_refused():
    def m(d, b):
        d["conflicts"].append(dict(d["conflicts"][0]))
    _refused(m, "twice")


def test_unknown_source_refused():
    _refused(lambda d, b: d["roof_datum"]["walls"][0].update(source_task="T-NOPE"), "source_task")


def test_held_as_zero_refused():
    _refused(lambda d, b: d["roof_datum"]["walls"][0].update(carried_m2=0.0), "never 0")


def test_applied_twice_refused():
    out, *_ = run()
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(doc(out), PID), out)


def test_check_wiring_catches_a_released_held_wall():
    out, *_ = run()
    bad = copy.deepcopy(out)
    for ln in bad:
        if ln["calculation"]["inputs"].get(A.REC_KEY, {}).get("action") == "PART_HELD":
            ln["evidence_state"], ln["measured_net"] = "SOURCE_DERIVED", 11.2
            break
    with pytest.raises(ValueError):
        A.check_wiring(bad)


# ================================================================================================ named increments
def base_with_increment():
    """the T-279 fill with W2's conflict increment named outside the total (0.060 m2; 0.012 m3), as V3.0.26 carries a
    width conflict before R-T488-1: it is retired once W2 is a CONFLICT range (never named twice)."""
    b0 = T279.lines_3025()
    d = T279.doc(b0)
    for ln in d["lines"]:
        for w in ln["walls"]:
            if w["wall_id"] == "W2":
                w["conflict_increment_outside"] = 0.012 if ln["item_code"] == "ARCH.WALL_VOLUME" else 0.06
    out, *_ = T279.run(d, b0)
    return out


def test_increment_retired_into_the_range():
    b = base_with_increment()
    assert "CONFLICT_INCREMENT_OUTSIDE: W2" in next(ln for ln in b if ln["line_id"] == _pid(b, "GF"))["rfi"]["question"]
    out, ident, ch, *_ = run(b=b)
    gfp = next(ln for ln in out if ln["line_id"] == _pid(out, "GF"))
    q = gfp["rfi"]["question"]
    assert "CONFLICT_INCREMENT_OUTSIDE" not in q and "W2 CONFLICT [10.8, 10.86] m2 (X-1)" in q
    rec = gfp["calculation"]["inputs"][A.REC_KEY]
    assert [h["wall"] for h in rec["retired_increments"]] == ["W2"]
    assert not any(h.get("kind") == "CONFLICT_INCREMENT_OUTSIDE"
                   for h in gfp["calculation"]["inputs"]["blockwork_fill_v3026"]["still_held"])


def test_increment_not_the_range_refused():
    b = base_with_increment()
    d = doc(b)
    d["conflicts"][0]["range_m2"] = [10.8, 10.9]          # 0.100 named range vs the 0.060 the fill names: stale
    with pytest.raises(A.InputsError, match="increment"):
        run(d, b)


# ================================================================================================ parapet run
def _parapet_line(alt):
    from engine.source import boq_line as BL
    rec = {"upstand": {"floor_m": 0.30}, "runs": [
        {"run": "R-1", "centreline_m": [4.0, 4.0], "block_alternative_m2": [0.0, 4.0]},
        {"run": "R-2", "centreline_m": [2.5, 2.5], "block_alternative_m2": alt}],
        "bound": {"block_alternative_m2": [0.0, 4.0 + (alt or [0, 0])[1]],
                  "block_alternative_not_booked": [] if alt else ["R-2"]}}
    return BL.make_line(project_id=PID, revision_set_sha256=T279.REV, item_code="STR.CONC.PARAPET", unit="m3",
                        evidence_state="BLOCKED_RFI", element_id="ROOF#PARAPET_RC", floor="1F", formula="parapet",
                        inputs={"parapet_rc_v3023": rec}, rule_id="R", rule_version="1", documents=T279.DOCS,
                        rfi={"question": "parapet detail"}, notes="p488", item_en="Parapet", item_ar="دروة",
                        trade="CONCRETE")


def _pdoc(before, after, h=1.3):
    return {"schema": A.INPUTS_SCHEMA, "project": PID, "sources": copy.deepcopy(SRC),
            "parapets": [{"run": "R-2", "element_id": "ROOF#PARAPET_RC:R-2", "before_m2": before, "after_m2": after,
                          "centreline_m": 2.5, "height_m": h, "why": "floor outline run superseded",
                          "source_task": "T-X"}]}


def test_parapet_block_alternative_on_the_roof_run():
    # R-2 drawn straight at roof level 2.500 m, h 1.30 above the finish, upstand 0.30: [0, 2.500 x 1.00] = [0, 2.500];
    # it carried [0, 2.900] from the floor-outline arc: -0.400 m2 beside; the line's quantity / state do not move
    ln = _parapet_line([0.0, 2.9])
    ch, _log = A.changes_for(A.load_inputs(_pdoc([0.0, 2.9], [0.0, 2.5]), PID), [ln])
    a = ch[0]["after"]
    r = a["calculation"]["inputs"]["parapet_rc_v3023"]
    assert r["runs"][1]["block_alternative_m2"] == [0.0, 2.5] and r["bound"]["block_alternative_m2"] == [0.0, 6.5]
    assert a["evidence_state"] == "BLOCKED_RFI" and a["measured_net"] is None


def test_parapet_not_booked_gets_its_alternative():
    ln = _parapet_line(None)
    ch, _log = A.changes_for(A.load_inputs(_pdoc(None, [0.0, 2.5]), PID), [ln])
    r = ch[0]["after"]["calculation"]["inputs"]["parapet_rc_v3023"]
    assert r["bound"]["block_alternative_not_booked"] == [] and r["bound"]["block_alternative_m2"] == [0.0, 6.5]


def test_parapet_stale_before_refused():
    with pytest.raises(A.InputsError, match="stale"):
        A.changes_for(A.load_inputs(_pdoc([0.0, 3.0], [0.0, 2.5]), PID), [_parapet_line([0.0, 2.9])])


def test_parapet_height_not_the_run_refused():
    with pytest.raises(A.InputsError, match="centreline"):
        A.changes_for(A.load_inputs(_pdoc([0.0, 2.9], [0.0, 2.5], h=1.5), PID), [_parapet_line([0.0, 2.9])])
