"""Phase 2B-0 blind-round readiness record: the sha256 of the frozen evaluation files (scorer, dry run, protocol,
facts template), the code tree digest of the engine and tools, the environment and the test configuration.

    python3 -I research/urban_m9_p2b0/make_readiness_record.py [--write]
Without --write it prints the record; tests/m9_p2b0/test_p2b0_blind_freeze.py checks the frozen files against the
written record (a change to any of them before the round needs a new, recorded amendment)."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research/urban_m9_p2b0/BLIND_READINESS_RECORD.json"
FROZEN = ("research/urban_m9_p2a_acceptance/blind_test/blind_score.py",
          "research/urban_m9_p2a_acceptance/blind_test/dry_run.py",
          "research/urban_m9_p2a_acceptance/blind_test/BLIND_TEST_PROTOCOL.md",
          "research/urban_m9_p2b0/FACTS_TEMPLATE_HEIGHTS.json")
INFORMATIONAL = ("research/urban_m9_p2a_acceptance/blind_test/DRY_RUN_RESULT.json",)


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def code_digest():
    files = sorted(p.relative_to(ROOT).as_posix() for base in ("engine", "tools") for p in (ROOT / base).rglob("*.py")
                   if "__pycache__" not in p.parts)
    h = hashlib.sha256()
    for f in files:
        h.update(f.encode() + b"\0" + hashlib.sha256((ROOT / f).read_bytes()).digest())
    return {"files": len(files), "sha256": h.hexdigest()}


def record():
    lock = json.loads((ROOT / "research/freeze_integrity/ENVIRONMENT_LOCK.json").read_text(encoding="utf-8"))
    pk = {}
    for name in sorted(lock.get("packages") or {}):
        try:
            from importlib import metadata
            pk[name] = metadata.version(name)
        except Exception:                                   # noqa: BLE001 - recorded as absent
            pk[name] = None
    return {
        "schema": "URBAN_BLIND_READINESS_V1",
        "protocol": "URBAN_BLIND_V1 (amendment A1)",
        "base_commit": "981ef5f (Phase 2A acceptance); Phase 2B-0 is the commit that adds this record",
        "methods": {"baseline": "ARCH_TAKEOFF_V2.1 (Mode U only)", "candidate": "ARCH_TAKEOFF_V2.2 (Mode U and A)"},
        "frozen_evaluation_sha256": {p: sha(p) for p in FROZEN},
        "informational_sha256": {p: sha(p) for p in INFORMATIONAL},
        "code_tree": code_digest(),
        "environment": {"python": platform.python_version(), "implementation": platform.python_implementation(),
                        "lock_python": lock.get("python"), "packages_installed": pk,
                        "packages_locked": lock.get("packages")},
        "test_configuration": {
            "full_suite": "python3 -m pytest -p no:cacheprovider --basetemp=<tmp>/bt --junitxml=<tmp>/junit.xml",
            "targeted": "python3 -m pytest tests/m9_p2b0 tests/m9_p2a tests/zz_freeze_integrity",
            "private_real_plan": "URBAN_REAL_PLAN_DXF=<private reference plan> (real-plan tests skip without it)",
            "lock_enforcement": "URBAN_REQUIRE_LOCK_ENV=1 for the blind round",
            "run": "python3 -I tools/urban_boq_m9.py arch --drawings PLAN.dxf --out OUT --method ARCH_TAKEOFF_V2.2 "
                   "[--facts FILLED_FACTS.json]"},
    }


if __name__ == "__main__":
    r = record()
    if "--write" in sys.argv:
        OUT.write_text(json.dumps(r, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(r, indent=1, sort_keys=True))
