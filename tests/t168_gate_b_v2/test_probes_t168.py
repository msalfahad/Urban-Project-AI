"""T-168 REGRESSION BASELINE (owner 2026-10-23 19:45 (3)): the adversarial probes 4a, 4c, 7, 8, 10 and 12b of
docs/agents/ADVERSARIAL_PROBE_2026-10-23.md (board branch), ported to pytest on a synthetic villa (SYN-GB-V2; no client
drawing, no sealed file: the "sealed" bytes below are made up here and registered in a temporary registry only).

The first commit of T-168 adds these tests as strict xfail (they fail on the merged head, where tools/v30_gate_b_v2.py
only delegates to the T-156 tool); the fix commit removes the xfail markers. Each expectation is the probe's own
"Expected" column:
  4a  beam B1 (a COUNTED V2 verdict) +1 % volume      -> flagged for review (VERIFIED_CHANGED)
  4c  blockwork W0 (COUNTED) net +4 %, non-structural -> flagged (VERIFIED_CHANGED)
  7   one line of the after side on another revision set -> refused (REVISION_MIX)
  8   verified line 2.000 -> 2.020 m3: the verdict no longer carries (STALE), the line is out of VERIFIED, and the
      change is tied to the change log: unlogged -> REVIEW_REQUIRED; logged with cause + evidence -> the row names it
  10  a line of project PY inside the PX side         -> refused (PROJECT_MIX)
  12b a renamed copy of a sealed benchmark            -> refused by its sha256 (SEALED), whatever its name
"""

from __future__ import annotations

import copy
import hashlib
import json

import pytest

from engine.source import boq_line as BL

PX, PY = "SYN-GB-V2", "SYN-OTHER"
REV_A, REV_B = "a" * 64, "b" * 64
SPEC_BEFORE = "SYN-CANDIDATE-1"
FIXED = "probe port (T-168 first commit): fails on the merged head; the fix commit removes this marker"


def G2():
    from tools import v30_gate_b_v2 as m
    return m


def line(eid, q, code="STR.CONC.FOOTING", unit="m3", project=PX, rev=REV_A):
    return BL.make_line(project_id=project, revision_set_sha256=rev, item_code=code, unit=unit, evidence_state="MEASURED",
                        measured_net=q, element_id=eid, formula="L*B*H", rule_id="R-T", rule_version="1", floor="FDN")


def sha_lines(lines):
    return hashlib.sha256(BL.dumps(lines).encode("utf-8")).hexdigest()


def verdict(lines, ids, checker_qty, vid="V2-SYN-0001", cver=SPEC_BEFORE, scope="WHOLE"):
    sel = [x for x in lines if x["line_id"] in ids]
    els = sorted(x["location"]["element_id"] for x in sel)
    return {"schema": "URBAN_CHECKER_VERDICT_V2", "verdict_id": vid, "project_id": sel[0]["project"]["project_id"],
            "revision_set_sha256": sel[0]["project"]["revision_set_sha256"], "candidate_version": cver,
            "boq_lines_sha256": sha_lines(lines), "line_ids": sorted(ids),
            "element_scope": {"ids": els, "count": len(els)}, "unit": sel[0]["unit"],
            "engine_qty": round(sum(x["measured_net"] for x in sel), 6), "checker_qty": checker_qty,
            "evidence": [{"sheet": "SYN-S1", "printed_value": "synthetic"}],
            "checker": {"run_token": "synthetic", "routine": "Checker", "verdict_commit": "abcdef12"},
            "scope": scope, "time": "2026-10-24T10:00:00Z"}


def meta(lines, spec=SPEC_BEFORE):
    return {"spec_id": spec, "boq_lines_sha256": sha_lines(lines)}


def row_of(doc, eid):
    return [r for r in doc["rows"] if r["element_id"] == eid][0]


@pytest.mark.xfail(strict=True, reason=FIXED)
def test_probe_4a_verified_beam_moves_one_percent_is_flagged():
    before = [line(f"B{i}", 2.0, code="STR.CONC.BEAM") for i in range(1, 201)]
    after = copy.deepcopy(before)
    after[0] = line("B1", 2.02, code="STR.CONC.BEAM")
    v = verdict(before, [before[0]["line_id"]], 2.0)
    doc = G2().diff(before, after, verdicts=[v], before_meta=meta(before), after_meta=meta(after, "SYN-CANDIDATE-2"),
                    require_manifests=False)
    r = row_of(doc, "B1")
    assert "VERIFIED_CHANGED" in r["flags"] and "MOVED_5PCT" not in r["flags"]
    assert r["verdict_carry"] == "STALE" and doc["summary"]["status"] == "REVIEW_REQUIRED"


@pytest.mark.xfail(strict=True, reason=FIXED)
def test_probe_4c_verified_blockwork_moves_four_percent_is_flagged():
    wl = [line(f"W{i}", 10.0, code="MAS.BLOCK", unit="m2") for i in range(200)]
    wa = copy.deepcopy(wl)
    wa[0] = line("W0", 10.4, code="MAS.BLOCK", unit="m2")
    v = verdict(wl, [wl[0]["line_id"]], 10.0)
    doc = G2().diff(wl, wa, verdicts=[v], before_meta=meta(wl), after_meta=meta(wa, "SYN-CANDIDATE-2"),
                    require_manifests=False)
    r = row_of(doc, "W0")
    assert r["flags"] == ["VERIFIED_CHANGED"]           # under 5 %, under 2 % share, not structural: only this rule
    assert doc["summary"]["per_rule"]["VERIFIED_CHANGED"]["only_this_rule"] == 1


@pytest.mark.xfail(strict=True, reason=FIXED)
def test_probe_7_after_side_mixing_two_revision_sets_is_refused():
    base = [line(f"F{i}", 1.0 + i / 10) for i in range(1, 6)]
    after = copy.deepcopy(base)
    after[0] = line("F1", 1.1, rev=REV_B)
    with pytest.raises(G2().Refused) as ex:
        G2().diff(base, after, require_manifests=False)
    assert "REVISION_MIX" in ex.value.codes


@pytest.mark.xfail(strict=True, reason=FIXED)
def test_probe_8_verified_change_is_tied_to_the_change_log(tmp_path):
    before = [line(f"F{i}", 2.0) for i in range(1, 4)]
    after = copy.deepcopy(before)
    after[0] = line("F1", 2.02)
    v = verdict(before, [before[0]["line_id"]], 2.0)
    kw = dict(verdicts=[v], before_meta=meta(before), after_meta=meta(after, "SYN-CANDIDATE-2"), require_manifests=False)
    doc = G2().diff(before, after, **kw)
    r = row_of(doc, "F1")
    assert r["verdict_carry"] == "STALE" and r["change_log"] == "MISSING"
    assert doc["summary"]["status"] == "REVIEW_REQUIRED" and doc["summary"]["verified_changed_unlogged"] == 1
    rec = {"line_id": after[0]["line_id"], "element_ids": ["F1"], "old": 2.0, "new": 2.02, "unit": "m3",
           "cause": "footing depth re-read from the schedule", "evidence": [{"sheet": "SYN-S1", "value": "H = 0.505"}],
           "checker_verdict": "NONE"}
    log = G2().changes_append(tmp_path / "CHANGES.json", rec, candidate_version="SYN-CANDIDATE-2", project_id=PX)
    doc = G2().diff(before, after, changes=log, **kw)
    r = row_of(doc, "F1")
    assert r["change_log"] == log["changes"][0]["change_id"] and r["verdict_carry"] == "STALE"   # NONE: not VERIFIED
    assert doc["summary"]["verified_changed_unlogged"] == 0


@pytest.mark.xfail(strict=True, reason=FIXED)
def test_probe_10_line_of_another_project_is_refused():
    base = [line(f"F{i}", 1.0 + i / 10) for i in range(1, 6)]
    after = base + [line("F9", 3.0, project=PY, rev=REV_B)]
    with pytest.raises(G2().Refused) as ex:
        G2().diff(base, after, require_manifests=False)
    assert "PROJECT_MIX" in ex.value.codes


@pytest.mark.xfail(strict=True, reason=FIXED)
def test_probe_12b_renamed_copy_of_a_sealed_file_is_refused_by_sha256(tmp_path):
    sealed = b'{"synthetic": "sealed benchmark stand-in, made up by the test"}\n'
    reg = {"schema": "URBAN_SEALED_REGISTRY_V1", "entries": [
        {"kind": "SEALED_FILE", "project_id": "SYN-SEALED-1", "sha256": hashlib.sha256(sealed).hexdigest(),
         "label": "synthetic sealed stand-in"}]}
    copy_path = tmp_path / "site_reference (1).json"                 # a name no name guard knows
    copy_path.write_bytes(sealed)
    with pytest.raises(G2().Refused) as ex:
        G2().guard_inputs({"after": copy_path}, registry=reg)
    assert "SEALED" in ex.value.codes
    assert json.loads(copy_path.read_text())["synthetic"]           # the guard hashed the bytes; the file is untouched
