"""T-608 R-T608-1 lift landing door scope by trade: a non-Alsenan fixture (one lift landing door, one passage, one door;
plain and mirrored), the rule's adverse cases, and the Alsenan rebuild (byte-identical, no private input)."""
from __future__ import annotations

import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t608"
sys.path.insert(0, str(HERE))
import t608_rules as R  # noqa: E402

D = Decimal


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ fixture villa (not Alsenan)
# lift landing door 1.10 wide in a 0.25 shaft-front wall, face height 3.00; passage 1.20; door 0.90
LIFT = {"evidence": ["PANEL_LINES", "SHAFT_CROSS"], "width_m": "1.10", "height_m": None, "wall_h_m": "3.00",
        "lift_package_note": False, "head_established": False, "lintel_if_built_m3": "0.095"}
PASSAGE = {"evidence": [], "width_m": "1.20"}
DOOR = {"evidence": ["DOOR_LEAF"], "width_m": "0.90"}


def test_kind_from_drawn_evidence_never_the_label():
    assert R.kind_of(LIFT["evidence"]) == "LIFT_LANDING_DOOR"
    assert R.kind_of(PASSAGE["evidence"]) == "PASSAGE"
    assert R.kind_of(DOOR["evidence"]) == "DOOR"
    assert R.kind_of(["PANEL_LINES"]) == "FRAMED"           # frame drawn, no shaft symbol: not promoted to lift
    with pytest.raises(R.ScopeError):
        R.kind_of(["LABEL_PASSAGE"])


def test_rule_applies_only_to_lift_doors():
    for op in (PASSAGE, DOOR, dict(LIFT, evidence=["PANEL_LINES"])):
        with pytest.raises(R.ScopeError):
            R.expected(op, "SKIRTING")


def test_normal_expected_per_family():
    e = {f: R.expected(LIFT, f) for f in R.FAMILIES}
    assert e["OPENING_COUNT"]["status"] == "EXCLUDED"
    assert e["DOOR_SUPPLY"]["status"] == "HELD" and e["DOOR_SUPPLY"]["bound"] == ["1", "1"]
    assert e["DOOR_SUPPLY"]["value"] is None
    assert e["SKIRTING"]["value"] == "1.10"
    assert e["BLOCKWORK"]["status"] == "HELD" and e["BLOCKWORK"]["bound"] == ["0", "3.3000"]
    assert e["WALL_FACES"]["bound"] == ["0", "3.3000"] and e["WALL_FACES"]["value"] is None
    assert e["LINTEL"]["status"] == "HELD" and e["LINTEL"]["bound"] == ["0", "0.095"]
    assert e["THRESHOLD"]["owner_trade"].startswith("B6-07")
    assert e["SURROUND"]["owner_trade"].startswith("B6-06")
    assert e["WET_TRADES"]["status"] == "NOT_APPLICABLE"


def test_printed_height_and_printed_note_settle_their_families():
    op = dict(LIFT, height_m="2.10", lift_package_note=True, head_established=True)
    assert R.expected(op, "BLOCKWORK")["value"] == "2.3100"
    assert R.expected(op, "WALL_FACES")["status"] == "DEDUCT"
    s = R.expected(op, "DOOR_SUPPLY")
    assert s["status"] == "DRAWING-CONFIRMED" and s["owner_trade"].startswith("LIFT PACKAGE")
    assert R.expected(op, "LINTEL")["value"] == "0.095"


def _line(**k):
    base = {"line_id": "L-x", "item_code": None, "takes": True, "class": "RELEASED", "value": None,
            "kind_label": None, "height_used_m": None, "jamb_lm": None}
    base.update(k)
    return base


def test_audit_fix_rows_and_omission():
    assert R.audit(LIFT, "OPENING_COUNT", _line(item_code="ARCH.PASSAGE", kind_label="PASSAGE"))[0] == "FIX_ROW"
    assert R.audit(LIFT, "OPENING_COUNT", _line(item_code="ARCH.PASSAGE", **{"class": "EXCLUDED"}))[0] == "CORRECT"
    assert R.audit(LIFT, "DOOR_SUPPLY", _line(takes=False, **{"class": "NONE"}))[0] == "OMISSION"
    assert R.audit(LIFT, "SKIRTING", _line(item_code="FIN.SKIRTING", jamb_lm="0"))[0] == "CORRECT"
    assert R.audit(LIFT, "BLOCKWORK", _line(item_code="MAS.BLOCK", **{"class": "HELD"}))[0] == "CORRECT"
    assert R.audit(LIFT, "SURROUND", _line(item_code="FIN.PLASTER"))[0] == "FIX_ROW"
    assert R.audit(LIFT, "THRESHOLD", _line(item_code="ARCH.THRESHOLD"))[0] == "FIX_ROW"
    assert R.audit(LIFT, "LINTEL", _line(item_code="STR.CONC.LINTEL"))[0] == "FIX_ROW"
    pcs, names = R.tally([("a", "FIX_ROW", "x", "-1"), ("b", "CORRECT", None, None), ("c", "OMISSION", "y", None)])
    assert pcs == D("-1") and names == ["a", "c"]


@pytest.mark.parametrize("family,line", [
    ("SKIRTING", _line(item_code="FIN.SKIRTING", jamb_lm="0.50")),                         # skirted as doorless
    ("DOOR_SUPPLY", _line(item_code="DOOR.LIFT", **{"class": "EXCLUDED"})),               # out of scope, no note
    ("DOOR_SUPPLY", _line(item_code="DOOR.INTERNAL.PVC")),                                # priced as a PVC door
    ("BLOCKWORK", _line(item_code="MAS.BLOCK", height_used_m="2.20", **{"class": "HELD"})),  # Q-55 fallback borrowed
    ("WALL_FACES", _line(item_code="FIN.PLASTER", height_used_m="2.4", **{"class": "HELD"})),  # freelancer 2.40
    ("WALL_FACES", _line(item_code="FIN.PAINT")),                                         # released on unprinted h
    ("BLOCKWORK", _line(item_code="MAS.BLOCK", value="12.5", **{"class": "HELD"})),       # HELD carrying a value
])
def test_adverse_treatments_refused(family, line):
    with pytest.raises(R.ScopeError):
        R.audit(LIFT, family, line)


def test_adverse_inputs_refused():
    with pytest.raises(R.ScopeError):
        R.expected(dict(LIFT, width_m=None), "BLOCKWORK")
    with pytest.raises(R.ScopeError):
        R.expected(dict(LIFT, height_m="3.20"), "BLOCKWORK")                 # above the 3.00 face
    with pytest.raises(R.ScopeError):
        R.expected(LIFT, "CEILING")
    assert R.expected(dict(LIFT, wall_h_m=None), "WALL_FACES")["bound"] is None   # no bound, still HELD, never 0
    assert R.audit(dict(LIFT, lift_package_note=True), "DOOR_SUPPLY",
                   _line(item_code="DOOR.LIFT", **{"class": "EXCLUDED"}))[0] == "CORRECT"
    with pytest.raises(R.ScopeError):
        R.tally([("a", "MAYBE", None, None)])


# ------------------------------------------------------------------ drawn fixture through the extractor
def _dxf(path, mirror=False):
    import ezdxf

    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    s = -1.0 if mirror else 1.0
    lo, hi = 0.0, 250.0 * s                      # wall faces (0.25 m wall); shaft beyond the 'hi' face
    # lift gap x 3000 .. 4100 (1.10), passage 6000 .. 7200, door 9000 .. 9900
    for a, b in ((0, 3000), (4100, 6000), (7200, 9000), (9900, 12000)):
        msp.add_line((a, lo), (b, lo), dxfattribs={"layer": "1"})
        msp.add_line((a, hi), (b, hi), dxfattribs={"layer": "1"})
    for off in (0.0, 60.0, 120.0, 250.0):
        y = hi - off * s
        msp.add_line((3000, y), (4100, y), dxfattribs={"layer": "5"})
    msp.add_line((2900, hi + 100 * s), (4200, hi + 1800 * s), dxfattribs={"layer": "5"})     # shaft cross
    msp.add_line((9000, lo), (9000, lo - 900 * s), dxfattribs={"layer": "5"})              # door leaf (not a diagonal)
    doc.saveas(path)
    return doc


def _census(doc):
    hs = {}
    for e in doc.modelspace().query("LINE"):
        hs[(e.dxf.layer, round(e.dxf.start.x), round(e.dxf.start.y), round(e.dxf.end.x))] = e.dxf.handle
    faces = [h for (ly, x0, y0, x1), h in hs.items() if ly == "1" and (x1 == 3000 or x0 == 4100)]
    panels = [h for (ly, x0, y0, x1), h in hs.items() if ly == "5" and x0 == 3000 and x1 == 4100]
    return {"storeys": {"XF": {"gaps": [
        {"band_angle_deg": 0.0, "evidence": ["PANEL_LINES"], "ids": {"panel_lines": panels},
         "jamb_face_handles": faces},
        {"band_angle_deg": 0.0, "evidence": [], "ids": {}, "jamb_face_handles": []}]}}}


@pytest.mark.parametrize("mirror", [False, True])
def test_extractor_reads_the_fixture_lift_gap(tmp_path, mirror):
    pytest.importorskip("ezdxf")
    ex = _load("t608_extract")
    p = tmp_path / "fx.dxf"
    doc = _dxf(str(p), mirror)
    data = ex.read(str(p), census=_census(doc))
    g = data["lift_gaps"]["XF"]
    assert g["width_m"] == 1.1 and g["wall_t_m"] == 0.25
    assert [x["offset_from_shaft_face_mm"] for x in g["panel_lines"]] == [0.0, 60.0, 120.0, 250.0]
    assert all(x["covers_gap"] for x in g["panel_lines"])
    assert R.kind_of(g["evidence"]) == "LIFT_LANDING_DOOR"
    assert list(data["lift_gaps"]) == ["XF"]                    # the passage gap (no panels) is not read as a lift
    assert data["text_census"]["P7757.dxf"]["hits"]["lift_words"] == []


def test_keyed_arabic_is_decoded_before_matching():
    ex = _load("t608_extract")
    assert ex.decode_keyed("lwu]") == "مصعد"            # 'lift' typed on the Latin key positions
    assert ex.decode_keyed("lwu}}]") == "مصعد"          # drawing braces inside the word are dropped
    assert ex.PATTERNS["lift_words"].search(ex.decode_keyed("rhu]m lwu]"))


def test_extractor_without_shaft_symbol_stays_framed(tmp_path):
    pytest.importorskip("ezdxf")
    ex = _load("t608_extract")
    p = tmp_path / "fx.dxf"
    doc = _dxf(str(p))
    for e in list(doc.modelspace().query("LINE")):
        if e.dxf.layer == "5" and abs(e.dxf.end.y - e.dxf.start.y) > 1000 and abs(e.dxf.end.x - e.dxf.start.x) > 1:
            doc.modelspace().delete_entity(e)
    doc.saveas(str(p))
    g = ex.read(str(p), census=_census(doc))["lift_gaps"]["XF"]
    assert g["shaft_side"] is False and R.kind_of(g["evidence"]) == "FRAMED"


# ------------------------------------------------------------------ Alsenan rebuild (committed inputs only)
def test_alsenan_rebuild_byte_identical():
    b = _load("t608_alsenan")
    data = b.build()
    j = json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    assert j == b.JSON_OUT.read_text(encoding="utf-8")
    assert b.md(data) == b.MD_OUT.read_text(encoding="utf-8")


def test_alsenan_unreviewed_text_hit_stops_the_build(monkeypatch):
    b = _load("t608_alsenan")
    real = b._json

    def fake(rel):
        d = real(rel)
        if rel == b.IN["DRAWN"]:
            d = json.loads(json.dumps(d))
            d["text_census"]["P7757.dxf"]["hits"]["supply_or_schedule"].append("FFFF")
        return d

    monkeypatch.setattr(b, "_json", fake)
    with pytest.raises(SystemExit):
        b.build()


def test_alsenan_result_contract():
    data = json.loads((HERE / "out" / "T608_SCOPE_TABLE.json").read_text(encoding="utf-8"))
    s = data["summary"]
    assert s["released_quantities_changed"] == 0 and s["candidate_files_touched"] == 0
    assert sorted(s["task_non_correct"]) == ["1F DOOR_SUPPLY", "1F OPENING_COUNT", "GF DOOR_SUPPLY", "GF OPENING_COUNT"]
    fr1 = next(f for f in data["fix_rows"] if f["id"] == "FR-T608-1")
    assert fr1["family_total"] == {"unit": "pcs", "before": "9", "after": "6", "delta": "-3"}
    for r in data["rows"]:
        for ln in r["lines"]:
            if ln["class"] == "HELD":
                assert ln["measured_net"] is None                   # HELD never carries a value
        if r["family"] == "SKIRTING":
            assert r["verdict"] == "CORRECT"
    faces = {r["storey"]: r for r in data["rows"] if r["family"] == "WALL_FACES"}
    assert faces["1F"]["sole_blocker"] and faces["2F"]["sole_blocker"] and not faces["GF"]["sole_blocker"]
