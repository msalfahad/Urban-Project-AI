"""M2 generic components on their own: schedule reader (attribute rows, drawn text tables), bar notation, bar shapes,
CAD heal, title classification and normalisation. Truth is stated by hand or comes from the synthetic generator's
own independent formulas (tools/synthetic_villa: aci_hook_add, link_len), never from the engine under test."""

from __future__ import annotations

import math

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine.source import bar_shapes as BS                  # noqa: E402
from engine.source import cad_heal as CH                    # noqa: E402
from engine.source import drawing_model as DM              # noqa: E402
from engine.source import schedule_grammar as SG            # noqa: E402
from engine.source import schedule_reader as SR             # noqa: E402
from tools import synthetic_villa as SV                     # noqa: E402
from tools import urban_intake as UI                        # noqa: E402


# ------------------------------------------------------------------ schedule reader
@pytest.mark.parametrize("seed", [1, 2])                       # both tag sets: FO-TY / W / H / DEPHT and MARK / WIDTH ...
def test_attribute_rows_match_the_design(tmp_path, seed):
    dxf = SV.generate(tmp_path, seed)
    D = SV.design(seed)
    truth = SV.schedule_rows(D)
    S = SR.from_attribute_rows(UI.read(dxf)["attributes"])
    got = {(r["family"], r["mark"]): r for r in S["rows"]}
    for f in truth["FOOTING"]:
        r = got[("FOOTING", f["mark"])]
        dims = sorted(r["dims_m"][k] for k in ("W", "H"))
        assert dims == pytest.approx(sorted((f["L"], f["W"])), abs=1e-9)
        assert r["dims_m"]["D"] == pytest.approx(f["D"], abs=1e-9)
    for b in truth["BEAM"]:
        r = got[(DM.mark_family(b["mark"])[0], b["mark"])]
        assert r["dims_m"]["W"] == pytest.approx(b["B"], abs=1e-9)
        assert r["dims_m"]["H"] == pytest.approx(b["H"], abs=1e-9)          # beam DEPTH read as section depth H
    assert not S["conflicts"]


def test_text_table_reader():
    rows = [("TYPE", "WIDTH", "DEPTH", "BOTTOM", "TOP"),
            ("B1", "20", "60", "3Ø16", "2Ø12"),
            ("B2", "25", "70", "4Ø16", "2Ø14"),
            ("B3/B4", "20", "50", "3Ø14", "2Ø12")]
    texts = [{"value": v, "x": 100.0 * c, "y": 1000.0 - 50.0 * r} for r, row in enumerate(rows)
             for c, v in enumerate(row)]
    S = SR.from_text_table(texts, row_tol=10, col_pad=5)
    got = {r["mark"]: r for r in S["rows"]}
    assert set(got) == {"B1", "B2", "B3", "B4"}                     # a combined B3/B4 row is two rows
    assert got["B2"]["dims_m"]["W"] == pytest.approx(0.25) and got["B2"]["dims_m"]["H"] == pytest.approx(0.70)
    assert S["families"]["BEAM"]["unit"] == "cm"
    bot = [b for b in got["B1"]["bars"] if b["role"] == "BOTTOM"][0]
    assert (bot["count"], bot["dia_mm"]) == (3, 16)


def test_duplicate_mark_with_different_sizes_is_a_conflict_not_a_choice():
    rows = [("TYPE", "WIDTH", "DEPTH"), ("B1", "20", "60"), ("B1", "20", "70")]
    texts = [{"value": v, "x": 100.0 * c, "y": 1000.0 - 50.0 * r} for r, row in enumerate(rows)
             for c, v in enumerate(row)]
    S = SR.from_text_table(texts, row_tol=10, col_pad=5)
    assert S["conflicts"] and SR.library(S)[("BEAM", "B1")] is None


@pytest.mark.parametrize("raw,count,dia,grammar", [
    ("3%%c16", 3, 16, "COUNT_DIA"), ("Ø12/20cm", None, 12, "DIA_AT_SPACING"), ("5Ø8/m", 5, 8, "COUNT_DIA_PER_M"),
    ("2Ø14/Top", 2, 14, "COUNT_DIA_POSITION"), ("4 Ø 12 / 15 cm", 4, 12, "COUNT_DIA_AT_SPACING"),
])
def test_bar_notation(raw, count, dia, grammar):
    b = SG.parse_bar(raw)
    assert (b["grammar"], b["count"], b["dia_mm"]) == (grammar, count, dia)


def test_unreadable_bar_is_blocked_not_guessed():
    b = SG.parse_bar("see detail 7")
    assert b["grammar"] == "UNPARSED" and b["count"] is None and b["interpretation_state"] == "BLOCKED_INTERPRETATION"


# ------------------------------------------------------------------ bar shapes
@pytest.mark.parametrize("b,h,c,d", [(0.2, 0.5, 0.025, 8), (0.3, 0.7, 0.025, 10), (0.25, 0.6, 0.04, 12),
                                     (0.4, 0.9, 0.05, 20)])
def test_closed_link_matches_an_independent_derivation(b, h, c, d):
    # the engine rounds each hook addition to 1 micrometre (bbs_optimiser.hook_addition): two hooks -> <= 2e-6 m
    assert BS.closed_link(b, h, c, d)["developed_m"] == pytest.approx(SV.link_len(b, h, c, d), abs=2e-6)


@pytest.mark.parametrize("d", [8, 12, 16, 20, 25, 32])
def test_hook_additions_depend_on_the_diameter(d):
    for kind in ("90", "135_TIE"):
        got = BS.hooked(1.0, d, [kind])["developed_m"] - 1.0
        assert got == pytest.approx(SV.aci_hook_add(d, kind), abs=1e-6)


def test_mass_is_d_squared_over_162():
    assert BS.mass_kg(12.0, 16) == pytest.approx(12.0 * 256 / 162)


# ------------------------------------------------------------------ CAD heal
def _s(i, a, b, layer="E"):
    return {"id": i, "layer": layer, "a": a, "b": b}


def test_merge_collinear_duplicates_and_pieces_but_not_across_a_column():
    segs = [_s("1", (0, 0), (1000, 0)), _s("2", (1000, 0), (2000, 0)), _s("3", (0, 0), (2000, 0)),
            _s("4", (2300, 0), (4000, 0)), _s("5", (0, 200), (4000, 200)), _s("6", (0, 0), (0, 100), "OTHER")]
    out, log = CH.merge_collinear(segs, {"E"}, gap=3.0, off_tol=0.5)
    on = sorted((round(s["a"][0]), round(s["b"][0]), round(s["a"][1])) for s in out if s["layer"] == "E")
    assert on == [(0, 2000, 0), (0, 4000, 200), (2300, 4000, 0)]          # 300 mm gap (a column) never closes
    assert sum(h["pieces"] for h in log) == 3 and any(s["id"] == "6" for s in out)


def test_extend_dangling_end_within_snap_and_report_the_wide_one():
    col = [((1000, -300), (1000, 300))]                                    # a column face at x = 1000
    segs = [_s("a", (0, 100), (998.5, 100)),                              # 1.5 mm short: drafting noise
            _s("b", (0, -100), (985.0, -100)),                            # 15 mm short: wide, reported
            _s("c", (0, 0), (960.0, 0))]                                  # 40 mm short: never closed
    out, log = CH.extend_dangling(segs, {"E"}, col, snap=5.0, eps=0.5, wide_snap=20.0)
    by = {s["id"]: s for s in out}
    assert by["a"]["b"][0] == pytest.approx(1000.0) and by["b"]["b"][0] == pytest.approx(1000.0)
    assert by["c"]["b"][0] == pytest.approx(960.0)
    codes = {h["id"]: h["code"] for h in log}
    assert codes == {"a": "HEAL_EXTEND", "b": "HEAL_EXTEND_WIDE"}


# ------------------------------------------------------------------ titles and normalisation
@pytest.mark.parametrize("lang", ["EN", "AR"])
def test_titles_classify_in_both_languages(lang):
    want = {"FOUNDATION": ("FOUNDATION_PLAN", None), "GF": ("SLAB_PLAN", "GF"), "1F": ("SLAB_PLAN", "1F"),
            "SCHED": ("SCHEDULE", None)}
    for k, (role, storey) in want.items():
        r, s, ev = DM.classify_title([SV.TITLES[lang][k]])
        assert r == role and (storey is None or s == storey), (lang, k, r, s)


def test_normalize_diameter_code_and_arabic_digits():
    assert DM.normalize("3%%c16") == "3Ø16"
    assert DM.normalize("٣١") == "31"
