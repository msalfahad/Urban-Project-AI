"""T-527 DXF re-run (development villa): rebuilds the merged MASONRY_CENTRELINE_V2 capture (research/agents_t125) from the
private architectural DXF and re-runs every lintel end under LINTEL_BEARING_V3, then asserts the committed numbers-only
evidence (research/agents_t527/out/JAMB_EVIDENCE_V3_T527.csv) equals the fresh run byte for byte.

Private inputs live OUTSIDE every worktree (<checkout>/.work/private, git-excluded): P7757/P7757.dxf decoded from Drive
'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip. The scratch capture and the fresh CSV are written only into
<checkout>/.work/private/t527/. Skipped (by name) when the private drawing is absent, so a clean checkout stays green.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t527"))

PRIVATE = ROOT.parent / "private"
DXF = PRIVATE / "P7757" / "P7757.dxf"
SCRATCH = PRIVATE / "t527"
DXF_SHA8 = "ab54dd55"

pytestmark = pytest.mark.skipif(not DXF.is_file(), reason="private drawing P7757.dxf absent (Drive-only input)")


@pytest.fixture(scope="module")
def scratch():
    assert hashlib.sha256(DXF.read_bytes()).hexdigest()[:8] == DXF_SHA8
    SCRATCH.mkdir(parents=True, exist_ok=True)
    pkl, js = SCRATCH / "t125_inputs.pkl", SCRATCH / "t125_v2.json"
    if not pkl.is_file():
        sys.path.insert(0, str(ROOT / "research" / "agents_t125"))
        import alsenan_v2_dump
        alsenan_v2_dump.main([str(DXF), "--out", str(pkl)])
    if not js.is_file():
        sys.path.insert(0, str(ROOT / "research" / "agents_t125"))
        import alsenan_v2_run
        alsenan_v2_run.main([str(pkl), "--out", str(js)])
    return SCRATCH


def test_fresh_run_equals_committed_evidence(scratch):
    import t527_extract as X
    fresh = scratch / "JAMB_EVIDENCE_V3_T527.csv"
    X.main(str(scratch), out=fresh, probe=scratch / "probe_t527.json")
    committed = ROOT / "research" / "agents_t527" / "out" / "JAMB_EVIDENCE_V3_T527.csv"
    assert committed.is_file(), "commit the fresh run: " + str(fresh)
    assert fresh.read_bytes() == committed.read_bytes()
    bays = ROOT / "research" / "agents_t527" / "out" / X.BAYS_NAME
    assert (scratch / X.BAYS_NAME).read_bytes() == bays.read_bytes()
