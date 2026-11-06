"""T-544 DXF re-run: the 8 ends (and the extended search) re-measured from the private architectural DXF equal the
committed numbers-only evidence byte for byte. Private inputs OUTSIDE every worktree (<checkout>/.work/private,
git-excluded): P7757/P7757.dxf from Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip; scratch in
<checkout>/.work/private/t544. Skipped by name when the drawing is absent."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t544"))
PRIVATE = ROOT.parent / "private"
DXF = PRIVATE / "P7757" / "P7757.dxf"
SCRATCH = PRIVATE / "t544"

pytestmark = pytest.mark.skipif(not DXF.is_file(), reason="private drawing P7757.dxf absent (Drive-only input)")


def test_fresh_run_equals_committed_evidence():
    assert hashlib.sha256(DXF.read_bytes()).hexdigest()[:8] == "ab54dd55"
    SCRATCH.mkdir(parents=True, exist_ok=True)
    pkl, js = SCRATCH / "t125_inputs.pkl", SCRATCH / "t125_v2.json"
    sys.path.insert(0, str(ROOT / "research" / "agents_t125"))
    if not pkl.is_file():
        import alsenan_v2_dump
        alsenan_v2_dump.main([str(DXF), "--out", str(pkl)])
    if not js.is_file():
        import alsenan_v2_run
        alsenan_v2_run.main([str(pkl), "--out", str(js)])
    import t544_extract as X
    fresh = SCRATCH / "fresh" / "JAMB_EVIDENCE_T544.csv"
    fresh.parent.mkdir(exist_ok=True)
    X.main(str(SCRATCH), out=fresh)
    out = ROOT / "research" / "agents_t544" / "out"
    assert fresh.read_bytes() == (out / "JAMB_EVIDENCE_T544.csv").read_bytes()
    assert (fresh.parent / X.EXT_NAME).read_bytes() == (out / X.EXT_NAME).read_bytes()
    assert (fresh.parent / X.P2_NAME).read_bytes() == (out / X.P2_NAME).read_bytes()
