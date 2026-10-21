"""T-035: the Alsenan project facts file is valid and holds only sourced heights (UP-HGT-001)."""
import json
from pathlib import Path

from engine.source import arch_measure as AM

FACTS = Path(__file__).parent / "facts" / "ALSENAN_ARCH_FACTS_V1.json"


def _facts():
    return json.loads(FACTS.read_text(encoding="utf-8"))


def test_facts_file_validates():
    f = _facts()
    assert f["schema"] == AM.FACTS_SCHEMA
    assert AM.validate_facts(f) is f


def test_every_height_is_a_printed_source_value():
    f = _facts()
    vals = [v for trades in f.get("wall_heights", {}).values() for v in trades.values()]
    vals += [v for comps in f.get("height_components", {}).values() for v in comps.values()]
    for v in vals:
        assert isinstance(v["value_m"], (int, float)) and v["value_m"] > 0
        # a printed drawing value or a stated owner project fact (WALL_HEIGHT_AUTHORITY_POLICY_V1 ranks 1-4); never a
        # typical value or the freelancer's
        assert v["authority"].upper().startswith(("SOURCE", "OWNER_PROJECT_FACT")), v


def test_every_floor_without_a_height_lists_what_is_missing():
    f = _facts()
    missing = f["not_printed"]["missing"]
    for floor in ("GF", "1F", "2F"):
        for trade in ("PLASTER", "PAINT"):
            have = (f.get("wall_heights", {}).get(floor) or {}).get(trade)
            assert have or missing[floor][trade], (floor, trade)
