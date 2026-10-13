"""M9 S6 Phase 1 - what must not change. ARCH_TAKEOFF_V1 measures the synthetic villa exactly as the HEAD before S6
Phase 1 did (tests/m9_s6/data/V1_SYNTHETIC_VILLA_SNAPSHOT.json, written from 6b7a2e4 by
research/urban_m9_s6/phase1/v1_snapshot.py); V1 never runs the admission unless asked; --strict-admission adds only
DRAWING_DISCOVERY.json to V1's own files; ARCH_TAKEOFF_V2 keeps every V1 line unchanged. Route G is untouched: with
--structural, V1 warns about the default conventions and keeps them, V2 requires them explicitly."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ezdxf = pytest.importorskip("ezdxf")

from tools import urban_boq_m9 as M9                   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SNAP = Path(__file__).resolve().parent / "data" / "V1_SYNTHETIC_VILLA_SNAPSHOT.json"
V1, V2 = "ARCH_TAKEOFF_V1", "ARCH_TAKEOFF_V2"


def _snapshot_fn():
    spec = importlib.util.spec_from_file_location("s6_v1_snapshot", ROOT / "research" / "urban_m9_s6" / "phase1" /
                                                  "v1_snapshot.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.snapshot


def test_v1_measures_the_villa_exactly_as_before_s6(build):
    room, arch, _ = M9.arch_compute(str(build("base")), method=V1)
    want = json.loads(SNAP.read_text(encoding="utf-8"))
    got = json.loads(json.dumps(_snapshot_fn()(room, arch)))
    for k in ("lines", "unresolved", "rooms", "openings", "regions", "floor_categories"):
        assert got[k] == want[k], k


def test_v2_keeps_every_v1_line_unchanged(build):
    p = str(build("base"))
    r1, a1, _ = M9.arch_compute(p, method=V1)
    r2, a2, _ = M9.arch_compute(p, method=V2)
    by2 = {ln["line_id"]: ln for ln in r2["lines"]}
    for ln in r1["lines"]:
        assert json.dumps(by2.get(ln["line_id"]), sort_keys=True) == json.dumps(ln, sort_keys=True), ln["line_id"]
    snap = _snapshot_fn()
    s1, s2 = snap(r1, a1), snap(r2, a2)
    for k in ("rooms", "openings", "regions", "floor_categories"):
        assert s1[k] == s2[k], k


def test_v1_never_runs_the_admission(build, monkeypatch):
    from tools import arch_discovery as AD

    def boom(*a, **k):
        raise AssertionError("the admission ran on ARCH_TAKEOFF_V1")
    monkeypatch.setattr(AD, "admit_intake", boom)
    monkeypatch.setattr(AD, "shapes", boom)
    room, arch, _ = M9.arch_compute(str(build("base")), method=V1)
    assert room["lines"] and "discovery" not in arch and arch["run"]["policy"] == M9.ARCH_POLICY_ID


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_v1_strict_adds_only_the_discovery_report(build, cli, tmp_path):
    p = build("base")
    a, b = tmp_path / "a", tmp_path / "b"
    assert cli("--drawings", p, "--out", a, "--method", V1)[0] == 0
    assert cli("--drawings", p, "--out", b, "--method", V1, "--strict-admission")[0] == 0
    fa = {x.name for x in a.iterdir() if x.is_file()}
    fb = {x.name for x in b.iterdir() if x.is_file()}
    assert fb - fa == {"DRAWING_DISCOVERY.json"} and fa <= fb
    for n in sorted(fa):
        assert _sha(a / n) == _sha(b / n), n


def test_structural_conventions_v1_warns_v2_requires(build, cli, tmp_path, monkeypatch, h):
    from tools import urban_boq_m2 as M2

    class Stop(Exception):
        pass

    def stop(*a, **k):
        raise Stop
    monkeypatch.setattr(M2, "compute", stop)
    p = build("base")
    with pytest.raises(Stop):                     # V1 reaches route G with its defaults, after a visible warning
        cli("--drawings", p, "--out", tmp_path / "v1", "--method", V1, "--structural", p)
    out = tmp_path / "v2"
    rc, _, err = cli("--drawings", p, "--out", out, "--method", V2, "--structural", p)
    assert rc == 2 and "WARNING: --structural without --conventions" in err
    codes = {f["code"] for f in h.read(out, "ADMISSION_BLOCKED.json")["stopping_findings"]}
    assert codes == {"STRUCTURAL_CONVENTIONS_REQUIRED", "PLAN_AND_STRUCTURAL_ARE_ONE_FILE"}


def test_the_v1_warning_is_printed(build, cli, tmp_path, monkeypatch, capsys):
    from tools import urban_boq_m2 as M2

    def stop(*a, **k):
        raise KeyboardInterrupt
    monkeypatch.setattr(M2, "compute", stop)
    p = build("base")
    with pytest.raises(KeyboardInterrupt):
        M9.main(["arch", "--drawings", str(p), "--out", str(tmp_path / "o"), "--method", V1, "--structural", str(p)])
    assert "route G runs with its default convention set" in capsys.readouterr().err
