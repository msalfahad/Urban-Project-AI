"""T-034: ARCH_TAKEOFF_V2.10 = ARCH_TAKEOFF_V2.9 + the room names typed with ROOM_VOCAB_V2 (T-022,
engine.source.room_vocab) on the released architectural route (tools/urban_boq_m9.py).

Synthetic villa (tools/arch_synth, not a client drawing), its ground-floor rooms relabelled by hand:
  BEDROOM face 6.40..9.20 x 4.40..9.20 m with a 0.40 x 0.40 column inside -> 'حمام سباحة' (swimming pool):
      2.80 x 4.80 - 0.40 x 0.40 = 13.44 - 0.16 = 13.28 m2, POOL, an exterior space: no wet-room scope
  BATH face 9.40..12.20 x 0.20..2.60 m -> 'حمام ماستر' (master bathroom): 2.80 x 2.40 = 6.72 m2, BATHROOM, wet
  KITCHEN face 9.40..12.20 x 2.80..9.20 m -> 'غسيل سيارات' (car wash): 2.80 x 6.40 = 17.92 m2, names no room:
      held as an unlabelled space (with its question), never typed, its area kept (never 0)
Hand truth from the meaning of each label (UP-WET-001 wet codes) and the drawn coordinates, not from engine output.
V2.9 on the same drawing keeps its as-found reading (pool BATHROOM wet, master bath MASTER_BEDROOM dry, car wash
LAUNDRY wet): the method it is is unchanged. Variants: mirrored, a quarter turn, drawing units metres."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

from tools import arch_synth as AS
from tools import urban_boq_m9 as M9

ROOT = Path(__file__).resolve().parents[2]
A = 1e-6
WORDS = {"BEDROOM": "حمام سباحة", "BATH": "حمام ماستر", "KITCHEN": "غسيل سيارات"}
POOL_M2 = 2.80 * 4.80 - 0.40 * 0.40                     # 13.28
MBATH_M2 = 2.80 * 2.40                                  # 6.72
WASH_M2 = 2.80 * 6.40                                   # 17.92
WET_ITEMS = ("FIN.FLOOR.WET_TILE", "FIN.WALL.TILE", "FIN.WP.FLOOR")
# GF hand truth per method: area -> (codes, class, wet scope lines expected)
V210_GF = {round(POOL_M2, 6): (["POOL"], "ROOM", False), round(MBATH_M2, 6): (["BATHROOM"], "ROOM", True),
           round(WASH_M2, 6): ([], "UNLABELLED", False)}
V29_GF = {round(POOL_M2, 6): (["BATHROOM"], "ROOM", True), round(MBATH_M2, 6): (["MASTER_BEDROOM"], "ROOM", False),
          round(WASH_M2, 6): (["LAUNDRY"], "ROOM", True)}


def _to_metres(src, dst):
    """the same drawing in metres ($INSUNITS 6): every model-space entity scaled by 0.001 about the origin."""
    import ezdxf
    from ezdxf.math import Matrix44
    doc = ezdxf.readfile(str(src))
    doc.header["$INSUNITS"] = 6
    m = Matrix44.scale(0.001, 0.001, 0.001)
    for e in doc.modelspace():
        e.transform(m)
    doc.saveas(str(dst))
    return dst


def _villa(path, *, words=WORDS, mirror=False, quarter_turns=0, metres=False):
    mm = path.with_suffix(".mm.dxf") if metres else path
    with mock.patch.dict(AS.GF_WORDS, words):
        AS.villa(mm, mirror=mirror, quarter_turns=quarter_turns)
    return _to_metres(mm, path) if metres else path


def _run(dxf, method):
    try:
        room, arch = M9.arch_compute(str(dxf), method=method)[:2]
    except M9.CompletenessFailed as ex:                        # never expected here; inspected all the same
        room, arch = ex.room_boq, ex.arch
    return room, arch


def _gf(room, arch):
    """GF rooms of the three relabelled faces by area -> (codes, class, has wet-scope lines, room record)."""
    out = {}
    for r in arch["rooms"]:
        a = round(r["area_m2"], 6)
        if r["floor"] == "GF" and a in V210_GF:
            assert a not in out, a
            items = {ln["item_code"] for ln in room["lines"] if ln["location"].get("room_id") == r["room_id"]}
            out[a] = (r["codes"], r["class"], bool(items & set(WET_ITEMS)), r)
    return out


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("t034")


def test_hand_truth():
    assert POOL_M2 == pytest.approx(13.28, abs=1e-9) and MBATH_M2 == pytest.approx(6.72, abs=1e-9)
    assert WASH_M2 == pytest.approx(17.92, abs=1e-9)
    i = M9.ARCH_METHODS.index(M9.V210)
    assert M9.ARCH_METHODS[i - 1] == M9.V29                       # every earlier method still listed, in order
    assert M9.ARCH_METHODS[i + 1:] == (M9.V211, M9.V212)          # T-079 / T-096: the only later methods, in order


@pytest.mark.parametrize("mirror,quarter_turns,metres", [(False, 0, False), (True, 0, False), (False, 1, False),
                                                         (True, 3, True), (False, 0, True)])
def test_v2_10_types_pool_master_bath_and_holds_car_wash(work, mirror, quarter_turns, metres):
    dxf = _villa(work / f"v_{int(mirror)}_{quarter_turns}_{int(metres)}.dxf", mirror=mirror,
                 quarter_turns=quarter_turns, metres=metres)
    room, arch = _run(dxf, M9.V210)
    gf = _gf(room, arch)
    assert set(gf) == set(V210_GF)                                  # no room lost, areas to the hand value
    for a, (codes, cls, wet) in V210_GF.items():
        assert gf[a][:3] == (codes, cls, wet), (a, gf[a][:3])
    wash = gf[round(WASH_M2, 6)][3]
    assert "UNLABELLED_SPACE" in wash["issue"]                     # held with its question, not a dry default
    wash_lines = [ln for ln in room["lines"] if ln["location"].get("room_id") == wash["room_id"]
                  and ln["item_code"] == "ARCH.SPACE"]
    assert len(wash_lines) == 1 and wash_lines[0]["measured_net"] == pytest.approx(WASH_M2, abs=A)   # never 0
    assert wash_lines[0]["evidence_state"] != "SOURCE_DERIVED"
    assert arch["run"]["method"] == M9.V210 and arch["run"]["policy"] == M9.ARCH_POLICY_ID_V210
    assert arch["run"]["v2_10"]["room_vocabulary"] == "ROOM_VOCAB_V2"
    assert arch["run"]["v2_10"]["knowledge"] == M9.V29_KNOWLEDGE


def test_v2_9_on_the_same_drawing_keeps_its_reading(work):
    room, arch = _run(_villa(work / "v29.dxf"), M9.V29)
    gf = _gf(room, arch)
    assert {a: v[:3] for a, v in gf.items()} == V29_GF
    assert arch["run"]["policy"] == M9.ARCH_POLICY_ID_V29 and "v2_10" not in arch["run"]


def _sig(room, arch):
    lines = sorted(json.dumps({k: ln.get(k) for k in ("item_code", "location", "measured_net", "evidence_state",
                                                      "unit", "bounded_range")}, sort_keys=True, ensure_ascii=False,
                              default=str) for ln in room["lines"])
    rooms = sorted((r["room_id"], tuple(r["codes"]), r["class"], round(r["area_m2"], 9)) for r in arch["rooms"])
    return lines, rooms


def test_v2_10_equals_v2_9_where_no_compound_label_is_drawn(work):
    """the stock villa (LIVING, غرفة نوم, BATH, KITCHEN, MASTER BEDROOM, STAIR, LOBBY): no compound phrase, so every
    line and room of V2.10 is the V2.9 one; only the run record says which method ran."""
    dxf = work / "stock.dxf"
    AS.villa(dxf)
    a, b = _run(dxf, M9.V29), _run(dxf, M9.V210)
    assert _sig(*a) == _sig(*b)
    assert a[1]["run"]["method"] == M9.V29 and b[1]["run"]["method"] == M9.V210


def test_cli_accepts_v2_10_and_writes_its_manifest(work):
    dxf = _villa(work / "cli.dxf")
    out = work / "cli_out"
    r = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "urban_boq_m9.py"), "arch", "--drawings", str(dxf),
                        "--out", str(out), "--method", M9.V210], capture_output=True, text=True, cwd=str(work))
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]
    found = sorted(out.rglob(M9.V24_MANIFEST))
    assert len(found) == 1, found
    man = json.loads(found[0].read_text(encoding="utf-8"))
    assert man["method"] == M9.V210 and man["policy"] == "URBAN_OUTPUT_MANIFEST_V2_10"
