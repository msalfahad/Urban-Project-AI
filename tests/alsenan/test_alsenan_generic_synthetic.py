"""Phase A generic engines on synthetic known answers: benchmark firewall, CAD text codes, schedule-table reader,
structural QTO (rectangles, tag association, size check, concrete rows, rebar fail-closed), level-mark unit evidence
through the frozen frame rule, and the exporter's banner / scoped-additive parameters."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from engine import boq_rc1_xlsx as BX
from engine.source import benchmark_firewall as FW, cad_text as CT, frame as FR, level_marks as LM
from engine.source import schedule_table as ST, structural_qto as SQ

RULES = (FW.Rule("data/inputs/*", FW.SOURCE), FW.Rule("tests/*/registers/*", FW.HISTORICAL_PROJECT_RESULT),
         FW.Rule("*benchmark*", FW.BENCHMARK_GOLD), FW.Rule("*.xlsx", FW.MANUAL_BOQ), FW.Rule("*.py", FW.CODE))


# ------------------------------------------------------------------ firewall
def test_firewall_classifies_by_path_first_rule_wins(tmp_path):
    assert FW.classify("tests/r1/registers/x.json", RULES)[0] == FW.HISTORICAL_PROJECT_RESULT
    assert FW.classify("data/inputs/abc.dxf", RULES)[0] == FW.SOURCE
    assert FW.classify("docs/benchmark_seal.md", RULES)[0] == FW.BENCHMARK_GOLD
    assert FW.classify("notes.txt", RULES)[0] == FW.UNCLASSIFIED
    # a relative path is resolved against the given root, not the working directory
    assert FW.classify("data/inputs/abc.dxf", RULES, root=tmp_path)[0] == FW.SOURCE
    c = FW.census(["data/inputs/a.dxf", "tests/q/registers/r.json", "x/benchmark.json"], RULES, root=tmp_path)
    assert c["by_class"] == {"BENCHMARK_GOLD": 1, "HISTORICAL_PROJECT_RESULT": 1, "SOURCE": 1}
    assert len(c["denied_present"]) == 2


def test_firewall_audit_records_every_open_and_fails_on_a_denied_file(tmp_path):
    ok, bad = tmp_path / "data" / "inputs" / "a.dxf", tmp_path / "tests" / "q" / "registers" / "gold.json"
    for p in (ok, bad):
        p.parent.mkdir(parents=True)
        p.write_text("x")
    with FW.OpenAudit() as a:
        ok.read_text()
    assert str(ok) in a.opened
    assert FW.verdict(a.opened, RULES, root=tmp_path)["state"] == FW.PASS
    with FW.OpenAudit() as b:
        ok.read_text()
        bad.read_text()
    v = FW.verdict(b.opened, RULES, root=tmp_path)
    assert v["state"] == FW.FAIL and v["violations"][0]["class"] == FW.HISTORICAL_PROJECT_RESULT
    with FW.OpenAudit() as c:
        pass
    assert c.opened == ()                        # an inactive recorder records nothing


def test_firewall_module_verdict():
    assert FW.module_verdict(["engine.source.frame", "lab_old_project"], ["*old_project*"])["state"] == FW.FAIL
    assert FW.module_verdict(["engine.source.frame"], ["*old_project*"])["state"] == FW.PASS


# ------------------------------------------------------------------ CAD text
def test_cad_text_control_codes():
    assert CT.plain("8%%C12") == ("8Ø12", ("%%c",))
    assert CT.plain("%%p0.00")[0] == "±0.00"
    assert CT.plain("%%USECTION A-A")[0] == "SECTION A-A"
    assert CT.plain("100%%%")[0] == "100%"
    assert CT.plain(None) == (None, ())


def test_legacy_codepage_flag_is_conservative():
    assert CT.legacy_codepage_suspect("Hg]v,M")
    assert CT.legacy_codepage_suspect("äö")
    assert not CT.legacy_codepage_suspect("MASTER BED ROOM")
    assert not CT.legacy_codepage_suspect("5.50")


# ------------------------------------------------------------------ schedule table
def grid(xs, ys, skip_h=()):
    """Full grid; skip_h = [(y, x0, x1)] horizontal pieces left out (merged cells)."""
    H, V = [], []
    for y in ys:
        cuts = sorted(s for s in skip_h if s[0] == y)
        a = xs[0]
        for _, x0, x1 in cuts:
            if x0 > a:
                H.append((y, a, x0, f"h{y}:{a}"))
            a = x1
        if a < xs[-1]:
            H.append((y, a, xs[-1], f"h{y}:{a}"))
    for x in xs:
        V.append((x, ys[-1], ys[0], f"v{x}"))
    return H, V


def test_schedule_reads_cells_by_drawn_column_not_tag():
    xs, ys = [0, 10, 20, 30], [30, 20, 10, 0]
    H, V = grid(xs, ys)
    items = [ST.Item("t1", "TYPE", 2, 25), ST.Item("t2", "L", 12, 25), ST.Item("t3", "W", 22, 25),
             ST.Item("a1", "F1", 2, 15, "ATTRIB", "TY", "I1"), ST.Item("a2", "90", 12, 15, "ATTRIB", "W", "I1"),
             ST.Item("a3", "80", 22, 15, "ATTRIB", "H", "I1"),
             ST.Item("a4", "F2", 2, 5, "ATTRIB", "TY", "I2"), ST.Item("a5", "190", 12, 5, "ATTRIB", "W", "I2"),
             ST.Item("a6", "170", 22, 5, "ATTRIB", "H", "I2")]
    t = ST.read(items, H, V, eps=0.1)
    assert t["state"] == ST.COMPLETE and len(t["bands"]) == 3
    leaves = ST.header_paths(t, [0])
    rec = ST.record(t, 1, leaves)
    by = {r["path"][-1]: r for r in rec}
    assert by["L"]["values"] == ["90"] and by["L"]["tags"] == ["W"]          # tag 'W' drawn under 'L'
    assert by["W"]["values"] == ["80"]


def test_schedule_merged_cell_spans_two_sub_rows():
    xs, ys = [0, 10, 20], [30, 20, 10, 0]
    H, V = grid(xs, ys, skip_h=[(10, 0, 10)])     # the type column has no line between the two sub-rows
    items = [ST.Item("h1", "TYPE", 2, 25), ST.Item("h2", "BARS", 12, 25), ST.Item("k", "F8", 2, 10.5 - 6),
             ST.Item("b1", "6/m TOP", 12, 15), ST.Item("b2", "9/m BOT", 12, 5)]
    t = ST.read(items, H, V, eps=0.1)
    assert t["bands"][2]["cells"][0]["continues_above"] is True
    leaves = ST.header_paths(t, [0])
    r1, r2 = ST.record(t, 1, leaves), ST.record(t, 2, leaves)
    assert r1[0]["values"] == r2[0]["values"] == ["F8"] and r1[0]["merged_bands"] == 2
    assert r1[1]["values"] == ["6/m TOP"] and r2[1]["values"] == ["9/m BOT"]


def test_schedule_reports_unplaced_values_never_drops_them():
    xs, ys = [0, 10, 20], [20, 10, 0]
    H, V = grid(xs, ys)
    t = ST.read([ST.Item("on", "X", 10, 15), ST.Item("out", "Y", 50, 5), ST.Item("in", "Z", 5, 5)], H, V, eps=0.1)
    assert t["state"] == ST.ITEMS_UNPLACED
    assert {u["key"]: u["why"] for u in t["unplaced"]} == {"on": ST.ON_GRID_LINE, "out": ST.OUTSIDE_TABLE}
    assert ST.read([ST.Item("a", "v", 1, 1)], [], [], eps=0.1)["state"] == ST.NO_GRID


# ------------------------------------------------------------------ structural QTO
def rect(key, x0, y0, x1, y1, split=False):
    segs = [(f"{key}b", x0, y0, x1, y0), (f"{key}r", x1, y0, x1, y1), (f"{key}t", x1, y1, x0, y1),
            (f"{key}l", x0, y1, x0, y0)]
    if split:                                     # one edge drawn in two collinear pieces
        segs[0] = (f"{key}b1", x0, y0, (x0 + x1) / 2, y0)
        segs.append((f"{key}b2", (x0 + x1) / 2, y0, x1, y0))
    return segs


def test_rectangles_with_split_edges_and_nesting():
    segs = rect("A", 0, 0, 1600, 1400, split=True) + rect("B", 3000, 0, 3900, 800) + rect("C", 3100, 100, 3400, 400)
    r = SQ.rectangles(segs, eps=1.0)
    assert sorted((round(x["width"]), round(x["height"])) for x in r) == [(300, 300), (900, 800), (1600, 1400)]


def test_rectangles_never_close_an_open_shape():
    segs = rect("A", 0, 0, 1000, 1000)[:3]
    assert SQ.rectangles(segs, eps=1.0) == []
    rotated = [("r1", 0, 0, 700, 700), ("r2", 700, 700, 0, 1400), ("r3", 0, 1400, -700, 700), ("r4", -700, 700, 0, 0)]
    assert SQ.rectangles(rotated, eps=1.0) == []           # inclined: reported elsewhere, never forced


def test_association_smallest_rectangle_orphans_and_double_tags():
    r = SQ.rectangles(rect("A", 0, 0, 2000, 2000) + rect("B", 500, 500, 900, 900) + rect("C", 5000, 0, 6000, 1000),
                      eps=1.0)
    a = SQ.associate(r, [{"key": "t1", "value": "F2", "x": 700, "y": 700}, {"key": "t2", "value": "F3", "x": 100, "y": 100},
                         {"key": "t3", "value": "F4", "x": 9000, "y": 0},
                         {"key": "t4", "value": "F5", "x": 5100, "y": 100}, {"key": "t5", "value": "F6", "x": 5200, "y": 200}])
    small = next(x for x in a["rectangles"] if x["width"] == 400)
    assert [t["value"] for t in small["tags"]] == ["F2"]
    assert [o["value"] for o in a["orphans"]] == ["F4"]
    assert any(i["why"] == SQ.MULTIPLE_TAGS for i in a["issues"])


def test_size_check_both_orientations_and_mismatch():
    r = SQ.rectangles(rect("A", 0, 0, 1400, 1600), eps=1.0)[0]
    assert SQ.size_check(r, 1600, 1400, 1.0, tol_mm=1.0)["state"] == SQ.SIZE_CONFIRMED
    assert SQ.size_check(r, 1700, 1400, 1.0, tol_mm=1.0)["state"] == SQ.SIZE_MISMATCH
    assert SQ.size_check(r, 16000, 14000, 10.0, tol_mm=1.0)["state"] == SQ.SIZE_CONFIRMED


def test_concrete_row_complete_and_blocked():
    d = {"L": {"m": 1.6, "source": "SCHED"}, "W": {"m": 1.4, "source": "SCHED"}, "H": {"m": 0.3, "source": "SCHED"}}
    ok = SQ.concrete_row(item="S", element_class="FOOTING", floor="F", element_id="F3@1", count=2, dims=d,
                         formula="2 x L x W x H", sources=["k"])
    assert ok["status"] == SQ.COMPLETE and ok["qty"] == pytest.approx(1.344)
    bad = SQ.concrete_row(item="S", element_class="COLUMN", floor="GF", element_id="C1", count=4,
                          dims=dict(d, H={"m": None, "source": None}), formula="", sources=[])
    assert bad["status"] == SQ.BLOCKED and bad["qty"] is None and "DIMENSION_NOT_ESTABLISHED:H" in bad["blockers"]
    none = SQ.concrete_row(item="S", element_class="X", floor="F", element_id="x", count=None, dims=d, formula="",
                           sources=[])
    assert none["qty"] is None and "COUNT_NOT_ESTABLISHED" in none["blockers"]


def test_rebar_fails_closed_and_refuses_a_ratio():
    assert SQ.rebar_gate({"bar_diameter_mm": "12", "count_or_spacing": "8"})["state"] == SQ.PARTIAL
    assert SQ.rebar_gate({})["state"] == SQ.BLOCKED
    full = {f: "x" for f in SQ.REBAR_FIELDS}
    assert SQ.rebar_gate(full)["state"] == SQ.COMPLETE
    with pytest.raises(ValueError):
        SQ.rebar_gate({"kg_per_m3": 100})


# ------------------------------------------------------------------ level marks -> frame
def marks(vals_y, layer="L", h=200.0):
    return [{"key": f"k{i}", "text": t, "y": y, "layer": layer, "height": h} for i, (t, y) in enumerate(vals_y)]


def test_level_parse_is_strict():
    assert [LM.parse_level(x) for x in ("+1.00", "%%p0.00", "-0.50", "5.50", "3700", "1:100", "A5")] == \
        [1.0, 0.0, -0.5, 5.5, None, None, None]


def test_level_marks_agree_and_the_frame_rule_decides():
    e = LM.view_evidence(marks([("+1.00", 1000.0), ("+5.50", 5500.0), ("+0.15", 150.0)]), view_id="V", source_sha256="a" * 64)
    assert e["state"] == "AGREE" and len(e["evidence"]) == 1 and e["evidence"][0].derived_value == pytest.approx(1.0)
    decl, _ = FR.declaration_evidence(4, "MODEL_SPACE", "a" * 64, parser="TEST")
    a = FR.assess(FR.NATIVE_UNIT, list(decl) + e["evidence"], "a" * 64, scope="MODEL_SPACE")
    assert a.status == FR.PROVISIONAL and a.value == pytest.approx(1.0)       # one class: never VERIFIED alone


def test_level_marks_disagreeing_pairs_conflict_never_average():
    e = LM.view_evidence(marks([("+1.00", 1000.0), ("+5.50", 5500.0), ("+0.15", 100.0)]), view_id="V",
                         source_sha256="b" * 64)
    assert e["state"] == "PAIRS_DISAGREE" and len(e["evidence"]) >= 2
    a = FR.assess(FR.NATIVE_UNIT, e["evidence"], "b" * 64, scope="MODEL_SPACE")
    assert a.status == FR.CONFLICT


def test_level_marks_inverted_give_no_evidence():
    e = LM.view_evidence(marks([("+1.00", 1000.0), ("+0.15", 1500.0)]), view_id="V", source_sha256="d" * 64)
    assert e["state"] == "INVERTED_OR_FLAT_MARKS" and e["evidence"] == []


def test_level_marks_mixed_families_and_single_value():
    assert LM.view_evidence(marks([("+1.00", 0.0)]) + marks([("+2.00", 1000.0)], h=300.0), view_id="V",
                            source_sha256="c" * 64)["state"] == "MIXED_ANNOTATION_FAMILIES"
    assert LM.view_evidence(marks([("+1.00", 0.0), ("+1.00", 0.0)]), view_id="V",
                            source_sha256="c" * 64)["state"] == "FEWER_THAN_TWO_VALUES"


# ------------------------------------------------------------------ exporter parameters
def model(**extra):
    m = {"S": {"role": "ADDITIVE_SUMMARY", "header": ["A", "Q"], "rows": [["X", 1.5]], "qty_cols": [1], "status_col": None}}
    m.update(extra)
    return m


def test_exporter_banner_and_scoped_additive_summaries(tmp_path):
    two = model(T={"role": "ADDITIVE_SUMMARY", "header": ["A"], "rows": [["Y"]], "status_col": None})
    with pytest.raises(ValueError):
        BX.write(two, tmp_path / "a.xlsx", created=__import__("datetime").datetime(2026, 1, 1))
    two["S"]["scope"], two["T"]["scope"] = "ONE", "TWO"
    w = BX.write(two, tmp_path / "b.xlsx", created=__import__("datetime").datetime(2026, 1, 1), banner="MY BANNER",
                 summary_name="S")
    got = BX.read(tmp_path / "b.xlsx")
    assert got["S"][0][0] == "MY BANNER" and "SCOPE: ONE" in got["S"][1][0]
    v = BX.validate(tmp_path / "b.xlsx", two, summary_sheet="S", canonical_ids=["X"], banner="MY BANNER", summary_name="S")
    assert v["state"] == "PASS"
    two["T"]["scope"] = "ONE"
    with pytest.raises(ValueError):
        BX.write(two, tmp_path / "c.xlsx", created=__import__("datetime").datetime(2026, 1, 1))


def test_exporter_defaults_unchanged():
    m = {"S": {"role": "BREAKDOWN", "header": [], "rows": []}}
    assert BX.role_text(m["S"]) == BX.ROLE_TEXT["BREAKDOWN"]
    assert "QORTUBA" in BX.BANNER                      # the default banner still reproduces the RC1 workbook
