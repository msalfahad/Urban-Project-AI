"""Tests for the project-creation flow."""

import pytest

from engine.rate_library import RateLibrary, RateCategory, RateItem
from pipeline.end_to_end import TradeLine
from pipeline.create_project import (
    create_project, write_to_sandbox, render_summary,
)
from pipeline.phase0 import SandboxViolation


def _rates():
    return RateLibrary(categories=[RateCategory("c", items=[
        RateItem("خرسانه", "c", qty=380, unit="m3", unit_cost=28, total=10640),
    ])])


def _lines():
    return [TradeLine("RC concrete", "p9", 352.44, "m3", "خرسانه", "m3", priced_qty=380)]


def test_create_project_prices_and_builds_docs():
    d = create_project(
        client_name="Fatma Alsnyan", project_name="Alsenan Villa",
        trade_lines=_lines(), rates=_rates(), location="Sabah Al-Ahmad",
        schedule_quantities={"blockwork_m2": 1260.69},
    )
    assert d.total_cost == 28 * 380
    assert d.project_doc["client"] == "Fatma Alsnyan"
    assert d.project_doc["isSandbox"] is True
    assert d.programme_weeks and d.programme_weeks > 40
    assert len(d.boq_item_docs()) == 1


def test_client_name_required():
    with pytest.raises(ValueError):
        create_project(client_name="  ", project_name="X",
                       trade_lines=_lines(), rates=_rates())


def test_write_targets_sandbox_only():
    d = create_project(client_name="C", project_name="P",
                       trade_lines=_lines(), rates=_rates())
    seen = []
    ids = write_to_sandbox(d, lambda path, doc: seen.append(path) or f"id{len(seen)}")
    assert all(p.startswith("sandbox/") for p in seen)
    assert not any(p.startswith("projects/") for p in seen)
    assert ids["project_path"] == "sandbox/projects"


def test_summary_renders():
    d = create_project(client_name="C", project_name="P",
                       trade_lines=_lines(), rates=_rates())
    out = render_summary(d)
    assert "NEW PROJECT" in out and "ESTIMATED COST" in out
