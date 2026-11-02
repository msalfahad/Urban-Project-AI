"""T-458 (owner directive 2026-11-02 C3): the wet-room upturn is 0.20 m with NO door deduction (UP-WP-002 2.0.0,
owner Q-03 / Q-35 C); the legacy 0.15 m / door-deduction sites are superseded and unreachable from the candidate.

Hand-calculated fixture (not the training villa): a 3.00 x 2.00 m bathroom, one 0.80 m door in a 0.20 m wall.
  floor face 3.00 x 2.00 = 6.000 m2; boundary incl. the door crossing 2 x (3.00 + 2.00) = 10.000 m;
  whole upturn 10.000 x 0.20 = 2.000 m2 (NOT (10.000 - 0.80) x 0.15 = 1.380 m2, the legacy V1 answer), split
  (UP-WP-002 2.0.0 reported_separately) into the run beside the doorway (10.000 - 0.80) x 0.20 = 1.840 m2 and the
  doorway segment 0.80 x 0.20 = 0.160 m2; doorway floor piece 0.80 x 0.20 (wall depth) = 0.160 m2, part of the floor.
  UP-WP-003 1.1.0 by the doorway detail:
    SEPARATE_RETURN        floor 6.000 + 0.160 = 6.160; upturn 1.840 + 0.160 = 2.000; total 8.160 m2
    COVERAGE_INSIDE_PIECE  floor 6.160; upturn 1.840 (segment NOT_BILLED, inside the piece); total 8.000 m2
                           (r1 billed 8.160: +0.160 m2 double count, Verifier 2026-11-02T04:57Z)
    not established        floor 6.160; upturn 1.840 MEASURED + segment HELD (0.160 if billed); never 0, never both
  Adverse wall depth 0.25 m, coverage inside the piece: piece 0.80 x 0.25 = 0.200 m2 billed once, segment not billed.
"""

from __future__ import annotations

import ast
import math
import re
from pathlib import Path

import pytest

from engine.source import rule_store as RS
from engine.source import waterproofing_policy_v2 as WP2

ROOT = Path(__file__).resolve().parents[2]
LEGACY = {"engine.source.waterproofing_policy", "engine.source.room_slice", "engine.finishes_rules",
          "engine.source.arch_quantity_truth"}


def _perimeter(poly):
    return sum(math.dist(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def _door(detail, wall_t=0.20, oid="D1", width=0.80):
    return {"id": oid, "width_m": width, "wall_t_m": wall_t, "doorway_detail": detail}


def _comp(r, item, comp):
    return [i for i in r["items"] if i["item"] == item and i["component"] == comp]


def test_normal_room_with_a_door_separate_return():
    r = WP2.wet(floor_m2=6.0, boundary_lm=10.0, doors=[_door(WP2.SEPARATE_RETURN)], room="B1")
    run = _comp(r, "FIN.WP.UPTURN", "BOUNDARY_RUN_EXCL_DOORWAYS")[0]
    seg = _comp(r, "FIN.WP.UPTURN", "DOORWAY_SEGMENT")[0]
    piece = _comp(r, "FIN.WP.FLOOR", "DOORWAY_PIECE")[0]
    assert run["upturn_m"] == pytest.approx(0.20) and run["door_crossings_deducted"] is False
    assert run["m2"] == pytest.approx(1.840)
    assert seg["state"] == "MEASURED" and seg["m2"] == pytest.approx(0.160)
    assert piece["state"] == "MEASURED" and piece["m2"] == pytest.approx(0.160) and piece["part_of_floor_area"]
    assert r["totals"]["FIN.WP.UPTURN"]["measured_m2"] == pytest.approx(2.000)    # whole boundary x 0.20
    assert r["totals"]["FIN.WP.FLOOR"]["measured_m2"] == pytest.approx(6.160)     # face + doorway piece
    assert r["state"] == "MEASURED" and r["held_items"] == []


def test_adverse_coverage_inside_the_piece_is_billed_once():
    """UP-WP-003 1.1.0: the doorway piece and the doorway segment cover the same doorway -> only one is billed."""
    r = WP2.wet(floor_m2=6.0, boundary_lm=10.0, doors=[_door(WP2.COVERAGE_INSIDE_PIECE)], room="B1")
    seg = _comp(r, "FIN.WP.UPTURN", "DOORWAY_SEGMENT")[0]
    assert seg["state"] == "NOT_BILLED" and seg["m2"] is None and seg["physical_m2"] == pytest.approx(0.160)
    assert seg["covered_by"] == "D1:DOORWAY_PIECE"
    assert r["totals"]["FIN.WP.UPTURN"]["measured_m2"] == pytest.approx(1.840)
    assert r["totals"]["FIN.WP.FLOOR"]["measured_m2"] == pytest.approx(6.160)
    billed = sum(t["measured_m2"] for t in r["totals"].values())
    assert billed == pytest.approx(8.000)                    # r1 billed 8.160 (the 0.160 m2 doorway twice)
    assert r["state"] == "MEASURED"
    # deeper wall: the piece (0.80 x 0.25 = 0.200) contains the segment (0.160) and is the one billed
    deep = WP2.wet(floor_m2=6.0, boundary_lm=10.0, doors=[_door(WP2.COVERAGE_INSIDE_PIECE, wall_t=0.25)], room="B2")
    assert _comp(deep, "FIN.WP.FLOOR", "DOORWAY_PIECE")[0]["m2"] == pytest.approx(0.200)
    assert sum(t["measured_m2"] for t in deep["totals"].values()) == pytest.approx(6.0 + 0.200 + 1.840)


def test_adverse_doorway_detail_not_established_is_held_never_zero_never_both():
    for det in (None, "SOMETHING_ELSE"):
        r = WP2.wet(floor_m2=6.0, boundary_lm=10.0, doors=[_door(det)], room="B1")
        seg = _comp(r, "FIN.WP.UPTURN", "DOORWAY_SEGMENT")[0]
        assert seg["state"] == "HELD" and seg["m2"] is None
        assert seg["reason"].startswith("DOORWAY_CONTINUATION_NOT_ESTABLISHED")
        assert seg["if_billed_m2"] == pytest.approx(0.160)
        assert r["totals"]["FIN.WP.UPTURN"] == {"measured_m2": pytest.approx(1.840), "held_rows": 1,
                                                "not_billed_rows": 0}
        assert _comp(r, "FIN.WP.FLOOR", "DOORWAY_PIECE")[0]["m2"] == pytest.approx(0.160)   # floor area either way
        assert r["state"] == "HELD" and r["held_items"] == ["FIN.WP.UPTURN:DOORWAY_SEGMENT:D1"]


def test_adverse_legacy_door_deduction_and_015_not_reproduced():
    one = WP2.wet(floor_m2=6.0, boundary_lm=10.0, doors=[_door(WP2.SEPARATE_RETURN)], room="a")
    two = WP2.wet(floor_m2=6.0, boundary_lm=10.0, doors=[_door(WP2.SEPARATE_RETURN),
                                                         _door(WP2.SEPARATE_RETURN, oid="D2", width=0.90)], room="b")
    u1, u2 = (x["totals"]["FIN.WP.UPTURN"]["measured_m2"] for x in (one, two))
    assert u1 == u2 == pytest.approx(2.000)              # doors never reduce the upturn
    assert u1 != pytest.approx((10.0 - 0.80) * 0.15)     # the legacy V1 answer 1.380
    assert _comp(two, "FIN.WP.UPTURN", "BOUNDARY_RUN_EXCL_DOORWAYS")[0]["m2"] == pytest.approx((10.0 - 1.70) * 0.20)
    assert len(_comp(two, "FIN.WP.UPTURN", "DOORWAY_SEGMENT")) == 2
    assert len(_comp(two, "FIN.WP.FLOOR", "DOORWAY_PIECE")) == 2
    with pytest.raises(ValueError):                      # door widths longer than the boundary: bad input, refused
        WP2.wet(floor_m2=1.0, boundary_lm=0.5, doors=[_door(WP2.SEPARATE_RETURN)], room="c")


def test_units_mirror_rotation():
    mm = [(0, 0), (3000, 0), (3000, 2000), (0, 2000)]
    u = 0.001                                            # metres per drawing unit
    m = [(x * u, y * u) for x, y in mm]
    mirrored = [(-x, y) for x, y in m]
    c, s = math.cos(0.7), math.sin(0.7)
    rotated = [(x * c - y * s, x * s + y * c) for x, y in m]
    vals = {round(WP2.wet(floor_m2=6.0, boundary_lm=_perimeter(p), doors=[_door(WP2.COVERAGE_INSIDE_PIECE)],
                          room="r")["totals"]["FIN.WP.UPTURN"]["measured_m2"], 9) for p in (m, mirrored, rotated)}
    assert vals == {1.84}
    # a caller that forgets the unit gets 2000 m2, never silently 2 m2: the input is metres by contract
    assert WP2.wet(floor_m2=6.0, boundary_lm=_perimeter(mm), room="r")["totals"]["FIN.WP.UPTURN"]["measured_m2"] == \
        pytest.approx(2000.0)


def test_missing_inputs_are_held_never_zero():
    r = WP2.wet(floor_m2=None, boundary_lm=None, doors=[_door(None, wall_t=None)], room="x")
    for item, comp in (("FIN.WP.FLOOR", "ROOM_FACE"), ("FIN.WP.UPTURN", "BOUNDARY_RUN_EXCL_DOORWAYS"),
                       ("FIN.WP.FLOOR", "DOORWAY_PIECE"), ("FIN.WP.UPTURN", "DOORWAY_SEGMENT")):
        it = _comp(r, item, comp)[0]
        assert it["state"] == "HELD" and it["m2"] is None
    assert r["state"] == "HELD" and all(t["measured_m2"] == 0.0 and t["held_rows"] for t in r["totals"].values())
    # an unknown door width: the run cannot be split off -> HELD with the whole-boundary figure kept for the record
    partial = WP2.wet(floor_m2=6.0, boundary_lm=10.0, doors=[_door(WP2.SEPARATE_RETURN, width=None)], room="y")
    run = _comp(partial, "FIN.WP.UPTURN", "BOUNDARY_RUN_EXCL_DOORWAYS")[0]
    assert run["state"] == "HELD" and run["whole_boundary_m2"] == pytest.approx(2.000)
    assert sorted(partial["held_items"]) == ["FIN.WP.FLOOR:DOORWAY_PIECE:D1",
                                             "FIN.WP.UPTURN:BOUNDARY_RUN_EXCL_DOORWAYS",
                                             "FIN.WP.UPTURN:DOORWAY_SEGMENT:D1"]
    # unknown wall depth with the coverage inside the piece: the piece is HELD and the segment stays NOT_BILLED
    deep = WP2.wet(floor_m2=6.0, boundary_lm=10.0, doors=[_door(WP2.COVERAGE_INSIDE_PIECE, wall_t=None)], room="z")
    assert _comp(deep, "FIN.WP.FLOOR", "DOORWAY_PIECE")[0]["state"] == "HELD"
    assert _comp(deep, "FIN.WP.UPTURN", "DOORWAY_SEGMENT")[0]["state"] == "NOT_BILLED"
    assert WP2.procurement(None, system="X", lap_factor=1.1)["procurement_m2"] is None


def test_rule_store_supersession():
    assert RS.rule("UP-WP-002", RS.LATEST_APPROVED)["value"] == pytest.approx(0.20)
    assert RS.rule("UP-WP-002", "1.4.0")["value"] == pytest.approx(0.15)     # the superseded base record, history


def test_policy_id_distinct_and_clash_recorded():
    ids = {}
    for p in sorted((ROOT / "engine").rglob("*.py")):
        for m in re.finditer(r'^POLICY_ID\s*=\s*"([^"]+)"', p.read_text(encoding="utf-8"), re.M):
            ids.setdefault(m.group(1), []).append(p.relative_to(ROOT).as_posix())
    assert ids[WP2.POLICY_ID] == ["engine/source/waterproofing_policy_v2.py"]
    # the V1 clash (opposite doorway rules) is exactly the recorded pair; a third claimant fails here
    assert sorted(ids["WATERPROOFING_POLICY_V1"]) == ["engine/source/waterproofing.py",
                                                      "engine/source/waterproofing_policy.py"]
    clash = [s for s in WP2.SUPERSEDED if s["id_clash_with"]]
    assert [s["id_clash_with"] for s in clash] == ["engine/source/waterproofing.py"]


def _closure(start):
    seen, todo = set(), [start]
    while todo:
        mod = todo.pop()
        if mod in seen:
            continue
        rel = mod.replace(".", "/")
        path = next((q for q in (ROOT / f"{rel}.py", ROOT / rel / "__init__.py") if q.exists()), None)
        if path is None:
            continue
        seen.add(mod)
        pkg = mod if path.name == "__init__.py" else mod.rsplit(".", 1)[0]
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                todo += [a.name for a in node.names if a.name.startswith("engine")]
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:
                    parts = pkg.split(".")
                    parts = parts[:len(parts) - node.level + 1]
                    base = ".".join(parts + ([node.module] if node.module else []))
                if base.startswith("engine"):
                    todo.append(base)
                    todo += [f"{base}.{a.name}" for a in node.names]
    return seen


def test_candidate_closure_never_imports_a_legacy_upturn_module():
    """adverse guard: the candidate ARCH_TAKEOFF_V3.0.40 module (every import, also inside functions) must not reach a
    module that still applies 0.15 m or the upturn door deduction."""
    for start in ("engine.source.arch_v3040", "engine.source.arch_v3041"):
        c = _closure(start)
        assert start in c and len(c) > 20
        assert not (c & LEGACY), sorted(c & LEGACY)
        # F-C-T458-1: urban_methods (wet_upturn_m 0.15 in a ROOF method) IS reached; recorded as reached-but-unread
        assert "engine.source.urban_methods" in c
    um = [s for s in WP2.SUPERSEDED if s["site"].startswith("engine/source/urban_methods.py")]
    assert len(um) == 1 and um[0]["reached_by_candidate"] is True and um[0]["read"] is False


def test_no_engine_or_tools_code_reads_wet_upturn_m():
    """F-C-T458-1: the 0.15 m in urban_methods is stated but never read: the key appears only where it is defined, the
    roof method is never resolved, and the only resolve() caller asks another rule."""
    key, defs, reads = "wet_upturn_m", [], []
    for base in ("engine", "tools"):
        for p in sorted((ROOT / base).rglob("*.py")):
            rel = p.relative_to(ROOT).as_posix()
            if rel == "engine/source/waterproofing_policy_v2.py":
                continue
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if key in line:
                    (defs if re.search(r'"wet_upturn_m":\s*0\.15', line) else reads).append(f"{rel}:{n}")
                if re.search(r'resolve\(\s*["\']URBAN-ROOF-WATERPROOF-UPTURN', line):
                    reads.append(f"{rel}:{n} resolves the roof method")
    assert defs == ["engine/source/urban_methods.py:43"] and reads == [], (defs, reads)
    callers = []
    for base in ("engine", "tools"):
        for p in sorted((ROOT / base).rglob("*.py")):
            txt = p.read_text(encoding="utf-8")
            callers += [f"{p.relative_to(ROOT).as_posix()}:{m.group(0)}"
                        for m in re.finditer(r"\bUM[13]?\.resolve\([^)]*\)", txt)]
    assert callers == ["engine/source/footing_rebar_population_v1.py:UM3.resolve(RULE_ID, project_rule_override)"]
