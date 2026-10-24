"""T-251 (gate 0): the trade completeness CHECK must not look, to the family-master guard, like a module that measures a
NOT_IMPLEMENTED family.

Root cause: tests/t130_family_master treats any quoted item-code literal in engine/source (outside the item master and
the census map) as 'a module writes this code'. trade_completeness_v1.line_trade compared the line's code with the
literal of the wall-mounted handrail (family B7-10, NOT_IMPLEMENTED), so the guard read the check as a measuring
module. Fix: the railing codes come from the item master (boq_line.ITEMS, trade RAILING) at import time. The guard is
unchanged; these tests pin (1) the classifier is behaviour-identical to the T-236 one over every item code x every trade,
(2) the module carries no literal of a NOT_IMPLEMENTED family in any family-master version, (3) the same scan still
catches a module that does write one (adverse).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from engine.source import boq_line as BL
from engine.source import trade_completeness_v1 as TC

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "engine/source/trade_completeness_v1.py"
MASTERS = [p for p in sorted((ROOT / "rules/coverage").glob("BOQ_FAMILY_MASTER_*.json"))
           if p.name != "BOQ_FAMILY_MASTER_1.0.0.json"]      # 1.0.0 lists no item codes per family (from 1.1.0 on)
CODE = re.compile(r"\"((?:STR|FIN|ARCH|MAS|DOOR)\.[A-Z0-9_.]*[A-Z0-9_])\"")     # the t130 scan, copied (read-only there)

# the T-236 classifier for the railing branch, kept here (tests are outside the guard's scan) as the reference
T236_RAILING = ("FIN.RAILING", "FIN.HANDRAIL")


def _t236_line_trade(line):
    code = line.get("item_code") or ""
    if code.startswith("STR.CONC."):
        fam = code[len("STR.CONC."):]
        return f"CONCRETE.{fam}" if fam in TC.CONCRETE_FAMILIES else "CONCRETE.OTHER"
    if code.startswith("STR.REBAR"):
        return "REBAR"
    if code in ("MAS.BLOCK", "ARCH.WALL_RUN") or line.get("trade") == "MASONRY":
        return TC._thickness(line) or "MASONRY.UNSTATED"
    if code in ("ARCH.DOOR",) or code.startswith("DOOR."):
        return "DOORS"
    if code == "ARCH.WINDOW":
        return "WINDOWS"
    if code.startswith("FIN.MARBLE.TREAD") or code.startswith("FIN.MARBLE.RISER") or \
            code.startswith("FIN.MARBLE.LANDING") or code.startswith("FIN.STAIR."):
        return "STAIRS"
    if code in T236_RAILING:
        return "RAILINGS"
    if code.startswith("FIN.WP."):
        return "WATERPROOFING"
    tr = line.get("trade")
    return TC.TRADE_MAP.get(tr, f"OTHER:{tr}")


def _not_implemented_codes():
    out = {}
    for p in MASTERS:
        for f in json.loads(p.read_text(encoding="utf-8"))["families"]:
            if f["capability"] == "NOT_IMPLEMENTED":
                for c in f["item_codes"]:
                    out.setdefault(c, (p.name, f["code"]))
    return out


def test_railing_codes_come_from_the_item_master():
    assert TC.RAILING_CODES == frozenset(T236_RAILING)
    assert TC.RAILING_CODES == frozenset(c for c, r in BL.ITEMS.items() if r[2] == "RAILING")
    assert all(BL.ITEMS[c][3] == "lm" for c in TC.RAILING_CODES)


@pytest.mark.parametrize("trade", list(BL.TRADES) + [None, "UNLISTED"])
def test_classifier_identical_to_t236_for_every_item_code_and_trade(trade):
    codes = sorted(BL.ITEMS) + ["", "FIN.HANDRAILX", "FIN.RAIL", "STR.CONC.FOOTING", "STR.CONC.NEW", "DOOR.X"]
    for code in codes:
        for extra in ({}, {"subtrade": "150"}, {"physical_element": "walls t=0.20"}):
            ln = dict({"item_code": code, "trade": trade}, **extra)
            assert TC.line_trade(ln) == _t236_line_trade(ln), (code, trade, extra)


def test_normal_handrail_and_guardrail_lines_are_railings_whatever_their_trade():
    for code in sorted(TC.RAILING_CODES):
        assert TC.line_trade({"item_code": code, "trade": "RAILING"}) == "RAILINGS"
        assert TC.line_trade({"item_code": code, "trade": "MARBLE"}) == "RAILINGS"   # the code decides, not the trade


def test_adverse_near_codes_are_not_railings():
    assert TC.line_trade({"item_code": "FIN.HANDRAILX", "trade": "MARBLE"}) == "OTHER:MARBLE"
    assert TC.line_trade({"item_code": "FIN.RAIL", "trade": None}) == "OTHER:None"
    assert TC.line_trade({"item_code": "FIN.UNKNOWN", "trade": "RAILING"}) == "RAILINGS"   # the trade map, as T-236


def test_check_module_writes_no_not_implemented_code_in_any_master_version():
    assert MASTERS, "no family master found"
    bad = _not_implemented_codes()
    hits = [(c, bad[c]) for c in CODE.findall(MODULE.read_text(encoding="utf-8")) if c in bad]
    assert hits == []


def test_adverse_the_same_scan_catches_a_measuring_module_writing_the_code():
    bad = _not_implemented_codes()
    assert "FIN.HANDRAIL" in bad                               # still NOT_IMPLEMENTED: the case the fix is about
    measuring = 'def emit(lines):\n    lines.append({"item_code": "FIN.HANDRAIL", "unit": "lm", "qty": 3.2})\n'
    assert [c for c in CODE.findall(measuring) if c in bad] == ["FIN.HANDRAIL"]
    t236_literal = '    if code in ("FIN.RAILING", "FIN.HANDRAIL"):\n'          # the T-236 line itself
    assert "FIN.HANDRAIL" in CODE.findall(t236_literal)
