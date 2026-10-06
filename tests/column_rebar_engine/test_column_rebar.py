"""Generic column-rebar engine: hand-derived known answers + mutation tests (synthetic project, no real drawing).

Every expected number below is worked out by hand in the comment next to it - never by calling a production function.
Unit mass is written out as pi/4 x d^2 x 7850 kg/m3.
"""

from __future__ import annotations

import copy
import math
import re
from pathlib import Path

import pytest

from engine.source import column_rebar as CR
from engine.source import engineering_flags as EF
from engine.source import project_claims as PC

ROOT = Path(__file__).resolve().parents[2]
M8 = math.pi / 4 * 0.008 ** 2 * 7850      # 0.39478 kg/m
M16 = math.pi / 4 * 0.016 ** 2 * 7850     # 1.57834 kg/m
CTX = {"project_id": "SYN-1", "drawing_revision": "R1"}
GAP_FLAG = "gapflagkey000001"
RATE_FLAG = "rateflagkey00001"


def bands():
    # synthetic bands with a deliberate gap at L = 800 (two open limits), detail drawn with 4 / 6 bars per long face
    return [
        {"band_id": "BAND_1", "lo_mm": None, "lo_incl": False, "hi_mm": 500, "hi_incl": True, "topology": CR.ONE_LINK},
        {"band_id": "BAND_2", "lo_mm": 500, "lo_incl": False, "hi_mm": 800, "hi_incl": False,
         "topology": CR.TWO_OVERLAPPING_LINKS, "drawn_bars_per_face": 4,
         "links": [{"bar_range": [0, 2]}, {"bar_range": [1, 3]}]},
        {"band_id": "BAND_3", "lo_mm": 800, "lo_incl": False, "hi_mm": 1200, "hi_incl": False,
         "topology": CR.MULTI_LINK_SET, "drawn_bars_per_face": 6,
         "links": [{"bar_range": [0, 4]}, {"bar_range": [1, 5]}, {"bar_range": [2, 3]}]},
    ]


def claims():
    return [
        PC.make_claim(project_id="SYN-1", claim_id="CL-RATE", kind=PC.ADJUDICATION, fact="TIE_RATE_SEMANTICS",
                      value=CR.SETS_PER_M, source_person="reviewer", date="2026-01-01", drawing_revision="R1",
                      flag_keys=[RATE_FLAG]),
        PC.make_claim(project_id="SYN-1", claim_id="CL-GAP", kind=PC.ADJUDICATION, fact="TIE_TOPOLOGY_BAND",
                      value={"long_side_mm": 800, "band_id": "BAND_3"}, source_person="reviewer", date="2026-01-01",
                      drawing_revision="R1", flag_keys=[GAP_FLAG]),
    ]


def project(**over):
    P = {"context": dict(CTX), "steel_density_kg_m3": 7850,
         "tie_rule": {"rule_id": "TIES-1", "dia_mm": 8, "rate_per_m": 6, "per_metre_semantics": CR.UNRESOLVED,
                      "zones": [{"zone_id": "Z", "rate_per_m": 6, "length_mm": None}]},
         "topology_bands": bands(), "bar_arrangement": {"method": "CORNERS_PLUS_LONG_FACES"},
         "cover": {"rule_id": "COV-1", "cover_mm": 25, "source_ref": "note"},
         "lap_rule": {"rule_id": "LAP-1", "state": "UNRESOLVED", "current_D": 40, "alternatives_D": [70]},
         "anchorage_rule": {"rule_id": "LAP-1", "state": "UNRESOLVED", "current_D": 40, "alternatives_D": [70]},
         "starter_rule": {"rule_id": "ST-1", "state": "CANDIDATE", "foot_mm": 300, "projection_D": 40,
                          "bottom_cover_mm": 70},
         "hook_method": {"method_id": "HOOK-135", "extension_d": 6, "min_extension_mm": 75, "hooks_per_link": 2},
         "claims": claims()}
    P.update(over)
    return P


def seg(sid, B, D, n, *, chain="CH1", idx=1, storey_mm=3000, depth=None, above=None, below=None, flags=(),
        ctype="K1", cands=None):
    return {"segment_id": sid, "occurrence_id": sid, "chain_id": chain, "floor": f"L{idx}", "storey_index": idx,
            "resolved_type": ctype,
            "candidates": cands or [{"type": ctype, "definition": {"B_mm": B, "D_mm": D,
                                                                    "bars": {"count": n, "dia_mm": 16}}}],
            "interval": {"length_mm": storey_mm, "state": CR.ESTABLISHED, "basis": "printed"},
            "clear_zone": {"framing_depth_mm": depth, "state": CR.ESTABLISHED if depth is not None else CR.BLOCKED},
            "above": above or {"exists": False}, "below": below or {"kind": "COLUMN"},
            "flag_keys": list(flags) + [RATE_FLAG]}


def run(segs, P=None, flags=()):
    return CR.evaluate(segs, P or project(), flags)


def parts(res, sid):
    return {p["part_id"].split("|", 1)[1]: p for p in res["parts"] if p["segment_id"] == sid}


# ================================================================================================ known answers
def ka_20x50(res):
    """20x50, 4 bars, one link, storey 3000, clear zone 3000 - 500 = 2500.
    across = 200 - 50 - 8 = 142 ; along = 500 - 50 - 8 = 442 ; path = 2 x (142 + 442) = 1168
    levels = ceil(6 x 2.5) = 15 ; links = 15 ; tie core kg = 15 x 1.168 x M8
    main core = 4 x 3.0 m ; anchorage at top (stops) = 4 x 40 x 16 = 640 mm each."""
    p = parts(res, "A")
    assert p["MAIN_CORE"]["count"] == 4 and p["MAIN_CORE"]["length_per_piece_mm"] == 3000
    assert abs(p["MAIN_CORE"]["kg"] - 4 * 3.0 * M16) < 1e-9
    assert abs(p["TIE_PERIMETER"]["length_per_piece_mm"] - 1168) < 1e-9 and p["TIE_PERIMETER"]["count"] == 15
    assert abs(p["TIE_PERIMETER"]["kg"] - 15 * 1.168 * M8) < 1e-9
    assert "TIE_INTERNAL" not in p
    assert p["HOOK_1"]["count"] == 15 and p["HOOK_1"]["length_per_piece_mm"] == 75     # max(6 x 8, 75)
    assert p["ANCHORAGE_TOP"]["length_per_piece_mm"] == 640


def ka_25x60(res):
    """25x60, 8 bars (4 per long face), two overlapping links on bars 0-2 and 1-3, clear zone 3000 - 400 = 2600.
    bar line: x0 = 25 + 8 + 8 = 41, x1 = 600 - 41 = 559, spacing = 518 / 3 = 172.667
    each link: along = 2 x 172.667 + 16 + 8 = 369.333 ; across = 250 - 58 = 192 ; path = 2 x 561.333 = 1122.667
    perimeter = 2 x (192 + 542) = 1468 ; excess = 2 x 1122.667 - 1468 = 777.333
    levels = ceil(6 x 2.6) = ceil(15.6) = 16 ; links placed = 32 (tie sets per metre)."""
    p = parts(res, "B")
    ev = res["segments"][1]["evals"]["K1"]["ties"][CR.CLEAR_ZONE]
    assert ev["links_per_level"] == 2
    paths = [x["core_path_mm"] for x in ev["links"]]
    assert all(abs(x - (2 * (192 + 2 * 518 / 3 + 24))) < 1e-9 for x in paths) and len(paths) == 2
    assert [x["bar_range_per_long_face"] for x in ev["links"]] == [[0, 2], [1, 3]]
    assert abs(p["TIE_PERIMETER"]["length_per_piece_mm"] - 1468) < 1e-9 and p["TIE_PERIMETER"]["count"] == 16
    assert abs(p["TIE_INTERNAL"]["length_per_piece_mm"] - (2 * 1122.6666666666667 - 1468)) < 1e-6
    assert p["HOOK_1"]["count"] == 32 and p["HOOK_2"]["count"] == 32


def ka_30x80(res):
    """30x80, 12 bars (6 per face), L = 800 on the gap - three links only through the claim.
    x0 = 41, x1 = 759, spacing = 718 / 5 = 143.6 ; across = 300 - 58 = 242
    LINK-1 bars 0-4: along = 4 x 143.6 + 24 = 598.4 -> path 1680.8 ; LINK-2 bars 1-5: same 1680.8
    LINK-3 bars 2-3: along = 143.6 + 24 = 167.6 -> path 819.2 ; perimeter 2 x (242 + 742) = 1968
    zone 3000 - 600 = 2400 -> levels ceil(14.4) = 15 ; links = 45 (18 links per metre at 3 links per level)."""
    ev = res["segments"][2]["evals"]["K1"]["ties"][CR.CLEAR_ZONE]
    assert ev["band"]["state"] == CR.RESOLVED_BY_CLAIM and ev["band"]["claim_id"] == "CL-GAP"
    got = [round(x["core_path_mm"], 6) for x in ev["links"]]
    assert got == [1680.8, 1680.8, 819.2]
    assert [x["link_id"] for x in ev["links"]] == ["LINK-1", "LINK-2", "LINK-3"]
    assert abs(ev["perimeter_mm"] - 1968) < 1e-9
    assert ev["by_method"][CR.RATE_COUNT] == {"levels": 15, "links": 45}
    assert ev["by_method"][CR.SPACING_WITH_ENDS] == {"levels": 16, "links": 48}


def ka_25x100(res):
    """25x100, 12 bars, three links. x1 = 1000 - 41 = 959 ; spacing = 918 / 5 = 183.6 ; across 192
    LINK-1: along 4 x 183.6 + 24 = 758.4 -> 1900.8 ; LINK-3: along 183.6 + 24 = 207.6 -> 799.2 ; perimeter 2268
    zone 3000 (no framing depth -> clear zone not established -> full storey shown, ties BLOCKED)."""
    ev = res["segments"][3]["evals"]["K1"]["ties"][CR.FULL_ZONE]
    assert [round(x["core_path_mm"], 6) for x in ev["links"]] == [1900.8, 1900.8, 799.2]
    assert abs(ev["perimeter_mm"] - 2268) < 1e-9
    assert ev["by_method"][CR.RATE_COUNT]["levels"] == 18                 # ceil(6 x 3.0)
    p = parts(res, "D")
    assert p["TIE_PERIMETER"]["release_state"] == CR.BLOCKED            # clear zone unknown -> not a lower bound


def fixture():
    return [seg("A", 200, 500, 4, chain="CA", depth=500),
            seg("B", 250, 600, 8, chain="CB", depth=400),
            seg("C", 300, 800, 12, chain="CC", depth=600, flags=[GAP_FLAG]),
            seg("D", 250, 1000, 12, chain="CD", depth=None)]


@pytest.fixture
def res():
    return run(fixture())


def test_known_answers(res):
    ka_20x50(res)
    ka_25x60(res)
    ka_30x80(res)
    ka_25x100(res)


def test_rate_levels_exact_and_both_methods():
    lv = CR.tie_levels(4500, [{"zone_id": "Z", "rate_per_m": 6, "length_mm": None}])
    assert lv[CR.RATE_COUNT] == 27 and lv[CR.SPACING_WITH_ENDS] == 28 and lv["difference"] == 1   # 6 x 4.5 = 27
    assert lv["zones"][0]["equivalent_spacing_mm"] == 1000 / 6
    # two zones: 500 at 10/m (5 levels) + remainder 2500 at 6/m (15 levels)
    lv = CR.tie_levels(3000, [{"zone_id": "E", "rate_per_m": 10, "length_mm": 500},
                              {"zone_id": "M", "rate_per_m": 6, "length_mm": None}])
    assert lv[CR.RATE_COUNT] == 20 and lv[CR.SPACING_WITH_ENDS] == 21


def test_mass_conservation(res):
    mc = CR.mass_conservation(res, lambda s: s["floor"])
    assert all(mc["checks"].values()), mc["checks"]
    a = sum(p["kg"] for p in res["parts"] if p["segment_id"] == "A")
    assert abs(mc["segments"]["A"]["total"] - a) < 1e-9


def test_releases(res):
    p = parts(res, "A")
    assert p["MAIN_CORE"]["release_state"] == CR.VERIFIED
    assert p["TIE_PERIMETER"]["release_state"] == CR.LOWER_BOUND          # zone method open -> never verified
    assert p["HOOK_1"]["release_state"] == CR.PROVISIONAL
    assert p["ANCHORAGE_TOP"]["release_state"] == CR.PROVISIONAL         # lap rule unresolved
    assert parts(res, "B")["TIE_INTERNAL"]["release_state"] == CR.PROVISIONAL
    assert res["segments"][0]["occurrence_state"] == "REBAR_LOWER_BOUND"


def test_type_conflict_shared_part_is_lower_bound_differing_part_follows_corroboration():
    c1 = {"type": "K2", "definition": {"B_mm": 250, "D_mm": 500, "bars": {"count": 8, "dia_mm": 16}}}
    c2 = {"type": "K3", "definition": {"B_mm": 200, "D_mm": 500, "bars": {"count": 8, "dia_mm": 16}}}
    s = seg("X", 0, 0, 0, depth=500, ctype="K2", cands=[c1, c2])
    s["conflict_flag_keys"] = ["conf"]
    r = run([s])
    p = parts(r, "X")
    assert p["MAIN_CORE"]["release_state"] == CR.LOWER_BOUND and p["MAIN_CORE"]["conflict_shared"]
    assert p["TIE_PERIMETER"]["release_state"] == CR.BLOCKED            # sections differ, nothing corroborated
    c2["corroborated"] = True
    p = parts(run([s]), "X")
    assert p["TIE_PERIMETER"]["release_state"] == CR.LOWER_BOUND        # provisional value (K3) under the zone LB
    assert p["TIE_PERIMETER"]["candidate_type"] == "K3"


def test_lap_starter_and_planted():
    lower = seg("L", 250, 500, 8, chain="CL", idx=0, depth=400,
                above={"exists": True, "bars": {"count": 6, "dia_mm": 16}},
                below={"kind": "FOOTING", "footing": {"depth_mm": 600, "ref": "FT"}})
    upper = seg("U", 200, 500, 6, chain="CL", idx=1, depth=400)
    planted = seg("P", 200, 500, 4, chain="CP", depth=400, below={"kind": "PLANTED_SUPPORT"})
    r = run([lower, upper, planted])
    p = parts(r, "L")
    assert p["LAP_TOP"]["count"] == 6 and p["LAP_TOP"]["length_per_piece_mm"] == 640          # 40 x 16
    assert p["ANCHORAGE_TOP_STOPPED"]["count"] == 2                                           # 8 - 6 bars stop
    assert p["STARTER"]["length_per_piece_mm"] == (600 - 70) + 300 + 640                      # 1470
    assert p["STARTER"]["release_state"] == CR.PROVISIONAL
    assert "ANCHORAGE_BASE" in parts(r, "P")
    assert r["input_problems"] == []


def test_firewall_engine_holds_no_project_data():
    src = (ROOT / "engine" / "source" / "column_rebar.py").read_text(encoding="utf-8")
    names = re.compile(r"alsenan|st7757|p7757|qortuba|rashed|44\.19|6Ø8|6%%c8|\b4\.5\b|\b450\b|\b800\b", re.I)
    marks = re.compile(r"\b(?:C|F|SB|CB|GB|B|CN)\d{1,2}\b|\bX\d{2}-Y\d{2}\b")
    assert not names.findall(src) + marks.findall(src)
    for lit in ("25", "70", "40", "6"):            # cover, soil cover, lap factor, rate: inputs, never literals
        assert not re.search(rf"(?<![\w.]){lit}(?![\w.])", src), lit


# ================================================================================================ mutations
def test_mut_one_link_where_two_required(monkeypatch):
    orig = CR.map_link_ranges
    monkeypatch.setattr(CR, "map_link_ranges", lambda b, k: (orig(b, k)[0][:1], orig(b, k)[1]))
    with pytest.raises(AssertionError):
        ka_25x60(run(fixture()))


def test_mut_two_links_where_three_required(monkeypatch):
    orig = CR.map_link_ranges
    monkeypatch.setattr(CR, "map_link_ranges", lambda b, k: (orig(b, k)[0][:2], orig(b, k)[1]))
    with pytest.raises(AssertionError):
        ka_30x80(run(fixture()))


def test_mut_rate_read_as_single_pieces():
    P = project(claims=[c for c in claims() if c["claim_id"] != "CL-RATE"] + [
        PC.make_claim(project_id="SYN-1", claim_id="CL-PIECES", kind=PC.ADJUDICATION, fact="TIE_RATE_SEMANTICS",
                      value=CR.LINKS_PER_M, source_person="x", date="2026-01-01", drawing_revision="R1",
                      flag_keys=[RATE_FLAG])])
    with pytest.raises(AssertionError):
        ka_30x80(run(fixture(), P))


def test_mut_column_omitted_on_upper_floor():
    lower = seg("L", 250, 500, 8, chain="CL", idx=0, above={"exists": True, "bars": {"count": 6, "dia_mm": 16}})
    upper = seg("U", 200, 500, 6, chain="CL", idx=1)
    assert CR.evaluate([lower, upper], project())["input_problems"] == []
    probs = CR.evaluate([lower], project(), expected_occurrences=["L", "U"])["input_problems"]
    assert any("missing occurrence U" in x for x in probs) and any("continues above" in x for x in probs)


def test_mut_column_wrongly_continued_upward():
    top = seg("T", 200, 500, 6, chain="CT", idx=2, above={"exists": True, "bars": {"count": 6, "dia_mm": 16}})
    assert CR.evaluate([top], project())["input_problems"]


def test_mut_wrong_schedule_row(monkeypatch):
    defs = [{"column_type": "K1", "storey_band": "LOW", "bars": 8}, {"column_type": "K1", "storey_band": "UP",
                                                                      "bars": 6}]
    band_of = {"L0": "LOW", "L1": "UP"}

    def check():
        assert CR.schedule_row(defs, "K1", "L1", band_of)[0]["bars"] == 6
        assert CR.schedule_row(defs, "K1", "L9", band_of) == (None, "NO_ROW")      # never borrowed
    check()
    orig = CR.schedule_row
    monkeypatch.setattr(CR, "schedule_row", lambda d, t, s, b: orig(d, t, "L0", b))
    with pytest.raises((AssertionError, TypeError)):
        check()


def test_mut_main_bars_truncated_at_soffit(monkeypatch):
    def cut(seg_, cand, P):
        s2 = copy.deepcopy(seg_)
        s2["interval"]["length_mm"] -= s2["clear_zone"]["framing_depth_mm"] or 0
        return orig(s2, cand, P)
    orig = CR._main_parts
    monkeypatch.setattr(CR, "_main_parts", cut)
    with pytest.raises(AssertionError):
        ka_20x50(run(fixture()))


def test_mut_ties_verified_despite_open_zone(monkeypatch):
    orig = CR._tie_parts

    def bad(*a, **k):
        out = orig(*a, **k)
        for p in out:
            p["basis_state"] = CR.VERIFIED
        return out
    monkeypatch.setattr(CR, "_tie_parts", bad)
    with pytest.raises(AssertionError):
        test_releases(run(fixture()))


def test_mut_hook_hidden_in_verified_core(monkeypatch):
    orig = CR.link_geometry

    def bad(*a, **k):
        links, per = orig(*a, **k)
        return links, per + 150          # two 75 mm hooks folded into the core path
    monkeypatch.setattr(CR, "link_geometry", bad)
    with pytest.raises(AssertionError):
        ka_20x50(run(fixture()))


def test_mut_duplicate_storey_segment():
    s = fixture()
    probs = CR.evaluate(s + [copy.deepcopy(s[0])], project())["input_problems"]
    assert any("duplicate segment A" in x for x in probs)
    r = CR.evaluate(s + [copy.deepcopy(s[0])], project())
    assert not CR.mass_conservation(r, lambda x: x["floor"])["checks"]["no_duplicate_part"]


def test_mut_claim_leaks_into_another_project():
    P = project(context={"project_id": "SYN-2", "drawing_revision": "R1"})
    r = run(fixture(), P)
    ev = r["segments"][2]["evals"]["K1"]["ties"][CR.CLEAR_ZONE]
    assert ev["band"]["state"] == CR.RULE_GAP and set(ev["band"]["candidates"]) == {"BAND_2", "BAND_3"}
    with pytest.raises(AssertionError):
        ka_30x80(r)
    new, _, q = CR.method_flags(r, P)
    assert any(f["context"]["s3_kind"] == "TIE_TOPOLOGY_RULE_GAP" and f["issue_type"] == "RULE_GAP" for f in new)
    # same project, other revision -> refused too; same project, other L -> refused
    assert run(fixture(), project(context={"project_id": "SYN-1", "drawing_revision": "R2"}))["segments"][2][
        "evals"]["K1"]["ties"][CR.CLEAR_ZONE]["band"]["state"] == CR.RULE_GAP
    assert CR.select_band(800, bands(), context=CTX, claims=claims(), flag_keys=[GAP_FLAG])["state"] == \
        CR.RESOLVED_BY_CLAIM
    assert CR.select_band(800, bands(), context=CTX, claims=claims(), flag_keys=["other"])["state"] == CR.RULE_GAP


def test_method_flags_supersede_unquantified_blocked_flag(res):
    old = EF.make_flag(project_id="SYN-1", drawing_revision="R1", detector="d", discipline="STRUCTURAL",
                       trade="REINFORCEMENT", element_type="COLUMN", element_id="z", issue_type="ENGINEERING_METHOD_REQUIRED",
                       issue_summary="zone", element_ids=["A", "B"], affected_facts=["transverse_zone"],
                       release_effect=EF.BLOCKED)
    new, sup, q = CR.method_flags(res, project(), [old])
    kinds = {f["context"]["s3_kind"] for f in new}
    assert {"TIE_ZONE_METHOD_REQUIRED", "END_LEVEL_COUNT_METHOD_REQUIRED", "HOOK_METHOD_REQUIRED",
            "LAP_METHOD_REQUIRED"} <= kinds
    assert sup and sup[0]["status"] == EF.SUPERSEDED and len(sup[0]["history"]) == 2
    z = q["TIE_ZONE_METHOD_REQUIRED"]
    assert z["alternative_kg"] > z["current_kg"] and z["segments_clear_zone_not_established"] == ["D"]
