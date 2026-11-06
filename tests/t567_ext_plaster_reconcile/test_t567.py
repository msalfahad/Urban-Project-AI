"""T-567: external plaster / facade finish vs the freelancer by elevation and face class (research/agents_t567).
Synthetic box villa "B567" (not the training villa), hand calculations; adverse cases; then the development-villa pins
(repository inputs only: T-337 / T-348 / T-346 / T-324 merged ledgers, the parsed freelancer cells, the line index)."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from fractions import Fraction as F
from itertools import permutations
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t567"))
import t567_rules as R  # noqa: E402

# ---- villa "B567" (hand): a closed box 10.00 x 8.00 m outside, walls +0.00 -> roof +3.50, parapet 1.00 above the
# roof, wall / parapet thickness 0.20, one window 1.50 x 1.20 on the NE face.
#   walls: perimeter 2 x (10 + 8) = 36.00 m x 3.50 = 126.00 m2 gross; less the window 1.80 = 124.20 m2 net (Q-73 full)
#   parapet outer face: 36.00 x 1.00 = 36.00 m2
#   parapet inner face: on the INNER run 36.00 - 8 x 0.20 = 34.40 m x 1.00 = 34.40 m2 (not 36.00: a closed ring)
#   parapet top: centre-line run 36.00 - 4 x 0.20 = 35.20 m x 0.20 = 7.04 m2
#   our gross 126.00 + 36.00 + 34.40 + 7.04 = 203.44 m2; net 203.44 - 1.80 = 201.64 m2
# The brief's '126.00 - 1.80 + parapet 36.00 x 2' (= 196.20) takes the inner face on the outer run (+1.60) and has
# no top (-7.04): 124.20 + 36.00 + 34.40 + 7.04 = 201.64 is the physically built figure.
# His statement (a typical one-plane practice): 4 elevation rows from +0.00 to the parapet top +4.50:
#   SE 10 x 4.5 = 45.00, NE 8 x 4.5 = 36.00, NW 45.00, SW 36.00 (= 162.00) + one parapet row "both faces"
#   36.00 x 1.00 x 2 = 72.00 -> gross 234.00; openings at half 0.90 -> net 233.10.
# Bridge his gross - ours = 234.00 - 203.44 = +30.56 = outer parapet face counted again in his parapet row +36.00
#   + inner face at the outer run +1.60 - tops in no row of his -7.04; net: 233.10 - 201.64 = +31.46
#   = 30.56 - 0.90 (his half) + 1.80 (our full hole).
BOX = dict(length="10.00", width="8.00", height="3.50", parapet_h="1.00", t="0.20", windows=[("1.50", "1.20")])


def his_rows(book, names=("SE", "NE", "NW", "SW"), lengths=("10", "8", "10", "8")):
    rows = []
    for e, L in zip(names, lengths):
        rows.append(R.HisRow(f"wall-{e}", e, F(L) * F("4.5"),
                             [R.Portion(f"BOX/{e}/STOREY", F(1)), R.Portion(f"BOX/{e}/PARAPET", F(1))]))
    rows.append(R.HisRow("parapet", "ROOF", F("72.00"),
                         [R.Portion(f"BOX/{e}/PARAPET-INNER+TOP", F(1)) for e in names],
                         terms=[R.term("inner face taken on the outer run (8 x 0.20 x 1.00)", "ENGINE_RIGHT", "1.60",
                                       source="hand"),
                                R.term("parapet tops: in no row of his", "ENGINE_RIGHT", "-7.04", source="hand")],
                         his_only=[R.term("outer parapet face counted again ('both faces' on top of a plane to the "
                                          "parapet top)", "ENGINE_RIGHT", "36.00", source="hand")]))
    return rows


def test_box_faces_by_hand():
    b, holes = R.box_faces(**BOX)
    f = b.faces
    walls = sum(x.lo for x in f.values() if x.face_class == "STOREY")
    outer = sum(x.lo for x in f.values() if x.face_class == "PARAPET_OUTER")
    it = sum(x.lo for x in f.values() if x.face_class == "PARAPET_INNER_TOP")
    assert (walls, holes, walls - holes, outer, it) == (F("126.00"), F("1.80"), F("124.20"), F("36.00"),
                                                        F("34.40") + F("7.04"))
    assert R.parapet_inner_face("36.00", "0.20", "1.00") == F("34.40")


def test_box_bridge_exact_by_hand():
    b, holes = R.box_faces(**BOX)
    res = R.bridge(b, his_rows(b), F("234.00"), F("0.90"), (holes, holes))
    for pas in ("lo", "hi"):
        p = res["passes"][pas]
        assert p["our_gross"] == F("203.44") and p["gross_diff"] == F("30.56") and p["residual"] == 0
        assert p["our_net"] == F("201.64") and p["his_net"] == F("233.10") and p["net_diff"] == F("31.46")
        assert p["ours_only"] == []
        # elevation matrix: each elevation's faces land in its own group; ROOF holds the inner + top
        assert p["matrix"][("SE", "SE")] == F("45.00") and p["matrix"][("NE", "NE")] == F("36.00")
        assert p["matrix"][("ROOF (parapet inner + top)", "ROOF")] == F("41.44")


@pytest.mark.parametrize("names", list(permutations(("SE", "NE", "NW", "SW")))[:6])
def test_mirror_and_rotation_do_not_move_the_totals(names):
    b, holes = R.box_faces(**BOX, elev_names=names)
    res = R.bridge(b, his_rows(b, names), F("234.00"), F("0.90"), (holes, holes))
    assert res["passes"]["lo"]["gross_diff"] == F("30.56")


def test_millimetre_input_gives_the_same_faces():
    b1, h1 = R.box_faces(**BOX)
    b2, h2 = R.box_faces(length="10000", width="8000", height="3500", parapet_h="1000", t="200",
                         windows=[("1500", "1200")], unit="mm")
    assert h1 == h2 and {k: v.lo for k, v in b1.faces.items()} == {k: v.lo for k, v in b2.faces.items()}


def test_partly_visible_plinth_and_datum_terms_close():
    # one face 10 m, drawn +0.15 -> +4.50 (plinth 0.15 -> 1.00 kept as its own class); his plane +1.00 -> +4.50
    b = R.Book()
    b.add(R.face("X/SE/plinth", "SE", "PLINTH", F("10") * F("0.85")))
    b.add(R.face("X/SE/storey", "SE", "STOREY", F("10") * F("3.50")))
    row = R.HisRow("1", "SE", F("35.00"), [R.Portion("X/SE/plinth", F(1)), R.Portion("X/SE/storey", F(1))],
                   terms=[R.term("plinth below his +1.00 plane (Q-07 B)", "RULE_DIFFERENCE", "-8.50", source="hand")])
    assert R.bridge(b, [row], F("35.00"), F(0), (F(0), F(0)))["passes"]["lo"]["residual"] == 0


# ---- adverse
def test_face_on_two_elevations_refused():
    b = R.Book()
    b.add(R.face("GF/C-1/storey", "NE", "STOREY", "10.0"))
    with pytest.raises(R.RuleError, match="two elevations"):
        b.add(R.face("GF/C-1/storey", "NW", "STOREY", "10.0"))
    with pytest.raises(R.RuleError, match="booked twice"):
        b.add(R.face("GF/C-1/storey", "NE", "STOREY", "10.0"))


def test_face_matched_by_two_rows_beyond_its_whole_refused():
    b, holes = R.box_faces(**BOX)
    rows = his_rows(b)
    rows.append(R.HisRow("again", "NW", F("35.00"), [R.Portion("BOX/SE/STOREY", F(1))]))
    with pytest.raises(R.RuleError, match="more than its whole"):
        R.bridge(b, rows, F("269.00"), F("0.90"), (holes, holes))


def test_cladding_inside_render_refused():
    b, _ = R.box_faces(**BOX)
    with pytest.raises(R.RuleError, match="cladding m2 inside render"):
        b.check_cladding({"BOX/SE/STOREY": "4.00"})
    b.check_cladding({})                                   # no cladding: passes
    clad = R.face("BOX/SE/STONE", "SE", "CLADDING", "4.00")
    b.add(clad)
    assert "BOX/SE/STONE" not in b.render()                # a cladding face is never in the render total


def test_inner_face_on_the_outer_run_refused():
    with pytest.raises(R.RuleError, match="inner run"):
        R.parapet_inner_face("36.00", "0.20", "1.00", run_basis="OUTER")


def test_held_and_unknown_rules():
    with pytest.raises(R.RuleError, match="hidden 0"):
        R.face("k", "NE", "SLAB_EDGE", "0", "0", status="HELD")
    with pytest.raises(R.RuleError, match="one value"):
        R.face("k", "NE", "STOREY", "1", "2", status="DRAWING-CONFIRMED")
    with pytest.raises(R.RuleError, match="UNKNOWN carries no number"):
        R.face("k", "NE", "STOREY", "1", status="UNKNOWN")
    with pytest.raises(R.RuleError, match="blank face must be HELD"):
        R.face("k", "NE", "STOREY", None, None)
    blank = R.face("k", "NE", "SLAB_EDGE", None, None, status="HELD", length="4.10")   # depth not printed
    b = R.Book()
    b.add(blank)
    res = R.bridge(b, [], F(0), F(0), (F(0), F(0)))
    assert res["blank_faces"] == ["k"] and res["passes"]["lo"]["our_gross"] == 0   # counted by name, never as 0 m2
    with pytest.raises(R.RuleError, match="blank HELD face cannot be matched"):
        R.bridge(b, [R.HisRow("1", "NE", F("5"), [R.Portion("k", F(1))])], F("5"), F(0), (F(0), F(0)))


def test_units_floats_sources_tolerance_refused():
    with pytest.raises(R.RuleError, match="m.l item"):
        R.face("arris", "NE", "STOREY", "12.0", unit="m.l")
    with pytest.raises(R.RuleError, match="floats"):
        R.d(1.5)
    with pytest.raises(R.RuleError, match="names its source"):
        R.term("x", "ENGINE_RIGHT", "1")
    with pytest.raises(R.RuleError, match="cause"):
        R.term("x", "LOOKS_CLOSE", "1", source="s")
    b, holes = R.box_faces(**BOX)
    with pytest.raises(R.RuleError, match="exact"):
        R.bridge(b, his_rows(b), F("234.00"), F("0.90"), (holes, holes), tolerance=F("0.01"))


def test_bridge_that_does_not_close_refused():
    b, holes = R.box_faces(**BOX)
    rows = his_rows(b)
    rows[-1].terms = rows[-1].terms[:1]                    # drop the tops term: his row no longer closes
    with pytest.raises(R.RuleError, match="!= his"):
        R.bridge(b, rows, F("234.00"), F("0.90"), (holes, holes))
    rows = his_rows(b)
    with pytest.raises(R.RuleError, match="add up to his gross"):
        R.bridge(b, rows, F("230.00"), F("0.90"), (holes, holes))


def test_remeasure_keeps_elevation_and_class():
    b = R.Book()
    b.add(R.face("1F/NW-2/PARAPET/parapet", "NW", "PARAPET_OUTER", "4.223108", "4.585300", status="HELD"))
    b.replace("1F/NW-2/PARAPET/parapet", R.face("1F/NW-2/PARAPET/parapet", "NW", "PARAPET_OUTER", "3.977236"))
    with pytest.raises(R.RuleError, match="keeps the face's elevation"):
        b.replace("1F/NW-2/PARAPET/parapet", R.face("1F/NW-2/PARAPET/parapet", "SW", "PARAPET_OUTER", "3.9"))
    with pytest.raises(R.RuleError, match="physical reason"):
        b.remove("1F/NW-2/PARAPET/parapet", "")


# ---- development villa (repository inputs)
OUT = ROOT / "research/agents_t567/out"


def _j():
    return json.loads((OUT / "T567_EXT_RECONCILE.json").read_text(encoding="utf-8"))


def test_alsenan_check_mode():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t567/t567_alsenan.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "CHECK OK" in r.stdout, r.stdout + r.stderr


def test_alsenan_his_statement_and_bridge_pins():
    d = _j()
    assert d["his"] == {"gross_J93": "1502.8400000", "groups": {
        "SW": "275.1600000", "SE": "191.5425000", "NE": "258.0000000", "NW": "389.9375000", "ROOF": "185.7040000",
        "PARAPETS": "44.3800000", "BOUNDARY": "107.2400000", "DRIP": "50.8760000"}, "openings_J97": "65.7450000",
        "deduction_half": "32.8725000", "net_invoice_r25": "1469.9675000"}
    lo, hi = d["passes"]["lo"], d["passes"]["hi"]
    assert (lo["our_gross"], hi["our_gross"]) == ("1166.4517846", "1185.4079770")
    assert lo["residual"] == hi["residual"] == "0.0000000"
    assert (lo["gross_diff"], hi["gross_diff"]) == ("336.3882154", "317.4320230")
    assert d["net_bound"]["our_net_lo"] == "1035.1779836" and d["net_bound"]["our_net_hi"] == "1087.6191760"
    assert d["like_for_like_gross"]["his_comparable_net"] == "1082.0240000"
    for p in (lo, hi):
        for g, v in p["his_by_group"].items():   # each of his groups closes on his own subtotal
            assert F(v["drawn_matched"]) + F(v["terms"]) + F(v["his_only"]) == F(v["his"]), g
        assert sum(F(x) for x in p["our_by_elevation"].values()) == F(p["our_gross"])
        assert sum(F(x) for x in p["by_cause"].values()) == F(p["gross_diff"])


def test_alsenan_candidate_lines_held_never_zero():
    d = _j()
    assert all(v["quantity"] is None and v["class"] == "HELD" for v in d["candidate_lines"].values())
    assert d["candidate_families"]["FIN.EXT.FINISH"] == {"lines": 3, "valued": 0, "blank": 3, "valued_m2": "0.0000000"}
    assert d["candidate_families"]["EXT.FENCE.PLASTER"]["valued"] == 0


def test_alsenan_faces_once_each_on_one_elevation_and_t348_applied():
    import csv
    rows = list(csv.DictReader((OUT / "FACES_T567.csv").open(encoding="utf-8")))
    keys = [r["key"] for r in rows]
    assert len(keys) == len(set(keys)) == 109 - 2 + 11 + 2      # T-337 109; T-348 r2 removes 2, adds 11; T-567 adds the SW pier returns (2)
    assert {r["elevation"] for r in rows} <= {"SW", "SE", "NE", "NW", "PASSAGE"}
    by = {r["key"]: r for r in rows}
    assert by["1F/NW-2/PARAPET/parapet"]["lo"] == "3.9772360" and by["1F/NW-2/PARAPET/parapet"]["status"] == \
        "DRAWING-CONFIRMED"
    assert "1F/NW-1/SLAB_EDGE_BELOW/slab_edge" not in by and "1F/NW-3/SLAB_EDGE_BELOW/slab_edge" not in by
    assert by["1F/NW-2/SCREEN-INTRADOS/reveal"]["class"] == "REVEAL"          # own family, not in the totals
    d = _j()
    assert set(d["own_family_faces_not_in_totals"]) == {"1F/NW-2/SCREEN-INTRADOS/reveal",
                                                        "1F/NW-2/RECESS-SOFFIT/soffit"}
    assert len(d["blank_faces_by_name"]) == 6                 # slab edges, depth not printed: blank, never 0


def test_alsenan_sw_pier_returns_r_t567_6():
    import csv
    by = {r["key"]: r for r in csv.DictReader((OUT / "FACES_T567.csv").open(encoding="utf-8"))}
    # pier outline 0.305222 + 0.157080 + 0.600000 + 0.479442 on a 1.005222 m span: returns 0.536522 m
    assert by["1F/NW-5/SW-PIER-RETURNS/storey"]["lo"] == "2.2533924"            # x 4.20 (+5.50 -> +9.70)
    assert (by["1F/NW-5/SW-PIER-RETURNS/parapet"]["lo"], by["1F/NW-5/SW-PIER-RETURNS/parapet"]["hi"]) == \
        ("0.0536522", "0.6974786")                                                  # x 0.10 .. 1.30, HELD


# ---- R-T567-6 on villa B567: a pier 0.60 wide projecting 0.30 with two square returns, on a key measured on its
# projection, storey 3.50 m: returns 2 x 0.30 = 0.60 m x 3.50 = 2.10 m2; a jamb return is a reveal, not render.
def test_projecting_pier_returns_by_hand():
    seg = [("0.30", "0", "face"), ("0.60", "0.60", "face"), ("0.30", "0", "face")]
    fx, jx = R.projecting_returns(seg, "0.60")
    assert (fx, jx) == (F("0.60"), 0)
    assert R.returns_face("P/SE/PIER/storey", "SE", fx, "3.50").lo == F("2.10")
    fx, jx = R.projecting_returns([("0.157080", "0.100000", "jamb"), ("0.50", "0.50", "face")], "0.60")
    assert fx == 0 and jx == F("0.057080")


def test_projecting_returns_adverse():
    with pytest.raises(R.RuleError, match="not closed on the key"):
        R.projecting_returns([("0.30", "0", "face"), ("0.60", "0.60", "face")], "0.70")
    with pytest.raises(R.RuleError, match="never shorter"):
        R.projecting_returns([("0.50", "0.60", "face")], "0.60")
    with pytest.raises(R.RuleError, match="double-counts the fronts"):
        R.returns_face("P/SE/PIER/storey", "SE", "1.20", "3.50", developed_in_full=True)


def test_alsenan_no_client_text_in_outputs():
    for p in OUT.iterdir():
        t = p.read_text(encoding="utf-8")
        assert not re.search("[؀-ۿ]", t), p.name     # no workbook (Arabic) text copied
