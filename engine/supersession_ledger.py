"""REVISION / SUPERSESSION LEDGER (§23): a previous statement that turned
out wrong is marked, never overwritten. Forward-only."""

from __future__ import annotations

import hashlib
import json

MARKS = ("WITHDRAWN", "SUPERSEDED", "CORRECTED_BY_OWNER_EVIDENCE", "APPARATUS_DEFECT",
         "SUPERSEDED_IN_PART")


def entry(*, ledger_id, previous_statement, previous_artifact, mark, replaced_by,
          evidence, frozen_artifact_unchanged=True, date=None) -> dict:
    if mark not in MARKS:
        raise ValueError(f"unknown mark {mark}")
    e = {"LEDGER_ID": ledger_id, "PREVIOUS_STATEMENT": previous_statement,
         "PREVIOUS_ARTIFACT": previous_artifact, "MARK": mark,
         "REPLACED_BY": replaced_by, "EVIDENCE": evidence,
         "FROZEN_ARTIFACT_UNCHANGED": frozen_artifact_unchanged, "DATE": date,
         "FORWARD_ONLY": True}
    e["ENTRY_SHA256"] = hashlib.sha256(json.dumps(e, sort_keys=True).encode()).hexdigest()[:16]
    return e


def assert_frozen_unchanged(freeze_record: dict, current_sha_by_artifact: dict) -> dict:
    """Every artifact hashed in an earlier freeze must still hash the same."""
    changed = {a: (h, current_sha_by_artifact.get(a))
               for a, h in freeze_record.get("ARTIFACT_SHA256", {}).items()
               if h is not None and current_sha_by_artifact.get(a) not in (None, h)}
    return {"OK": not changed, "CHANGED": changed}
