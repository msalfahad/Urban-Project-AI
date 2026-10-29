"""T-344 Alsenan (development villa): census V2 with the merged T-342 binding, offline from committed files.

research/agents_t344/CENSUS_V2_ALSENAN.json is the tool's own run on Drive 'Alsenan chalet project' /
P7757_DXF_COMPRESSED.zip (P7757.dxf sha256 ab54dd55..), label texts omitted. rebind() on the committed V1 census of
T-342 (research/agents_t342/CENSUS_T342.json) must give the same statuses label by label, and the V1 census itself
stays as T-342 committed it (41 / 28 / 1 / 1 / 11 silent)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import label_census_v2 as C                        # noqa: E402

T342 = ROOT / "research" / "agents_t342"
LIVE = json.loads((ROOT / "research" / "agents_t344" / "CENSUS_V2_ALSENAN.json").read_text(encoding="utf-8"))


def _rebind():
    cen = json.loads((T342 / "CENSUS_T342.json").read_text(encoding="utf-8"))
    led = C.load_ledger(T342 / "LABEL_BINDING_T342.csv", T342 / "SCOPES_T342.csv")
    return cen, C.rebind(cen, led, C.load_lines(T342 / "CANDIDATE_V3022_T342.json"))


def test_live_run_counts():
    s = LIVE["summary"]
    assert s["labels"] == 41 and s["unread_shx"] == 47
    assert s["by_status"] == {"MEASURED": 28, "HELD": 1, "UNSUPPORTED": 1, "ACCOUNTED_BY_BINDING": 11,
                              "SILENT_OMISSION": 0}
    assert s["by_binding"] == {"BOUND": 3, "PARTIAL": 1, "MISSING": 1, "NOT_APPLICABLE": 1}
    assert s["duplicates_counted_once"] == 5 and s["retyped"] == ["AT19"] and s["binding_refused"] == {}
    assert LIVE["v1_census_equals_t342_committed"] is True


def test_v1_census_unchanged():
    cen, _ = _rebind()
    s = cen["summary"]
    assert (s["policy"], s["labels"], s["by_status"]) == \
        ("URBAN_LABEL_CENSUS_V1", 41, {"MEASURED": 28, "HELD": 1, "UNSUPPORTED": 1, "SILENT_OMISSION": 11})


def test_rebind_equals_the_live_run_label_by_label():
    _, out = _rebind()
    k = ("text_id", "code", "v1_code", "status", "binding", "duplicate_of", "lines")
    assert [{x: r.get(x) for x in k} for r in out["labels"]] == [{x: r.get(x) for x in k} for r in LIVE["labels"]]
    assert out["summary"]["by_status"] == LIVE["summary"]["by_status"]


def test_at19_is_the_pool_and_the_court_scopes_are_named():
    by = {r["text_id"]: r for r in LIVE["labels"]}
    assert by["AT19"]["code"] == "POOL" and by["AT19"]["v1_code"] == "BATHROOM" and by["AT19"]["binding"] == "PARTIAL"
    assert by["AT20"]["duplicate_of"] == "AT19" and by["AT385"]["duplicate_of"] == "AT379"
    assert by["AT225"]["binding"] == "NOT_APPLICABLE"
    court = {s["scope"]: s["quantity"] for s in by["AT21"]["open_scopes"]}
    assert round(sum(court.values()), 4) == round(119.5416 + 10.679 + 3.3594 + 1.96 + 5.1794 + 21.0142 + 7.1094, 4)
    fin = [s for s in by["AT19"]["open_scopes"] if s["quantity"] is None]
    assert len(fin) == 1 and fin[0]["bound"][0] > 21                  # held blank with its drawn bound, never 0


def test_adverse_v1_vocabulary_cannot_bind_the_pool_label():
    cen, _ = _rebind()
    led = C.load_ledger(T342 / "LABEL_BINDING_T342.csv", T342 / "SCOPES_T342.csv")
    ln = C.load_lines(T342 / "CANDIDATE_V3022_T342.json")
    at19 = [r for r in cen["labels"] if r["text_id"] == "AT19"][0]
    b, _, _, why = C.check_row("AT19", at19["floor"], at19["code"], led, ln)       # V1 code BATHROOM
    assert b is None and why.startswith("REFUSED_CODE ledger POOL vs census BATHROOM")
