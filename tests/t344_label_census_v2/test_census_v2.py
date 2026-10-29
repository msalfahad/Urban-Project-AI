"""T-344: label census V2 (tools/label_census_v2.py) on a hand-made villa that is not Alsenan.

Hand villa (millimetres). GF plan region 0..20000 x 0..15000; 1F region 0..20000 x 20000..35000.
  rooms  R-BATH 3000 x 2500 (BATHROOM, face F-BATH, ledger LINE); R-LAUN 3000 x 2500 east of it (LAUNDRY, F-LAUN, LINE)
  labels T1 'BATHROOM' in R-BATH                         -> MEASURED (V1 and V2)
         T2 Arabic 'car wash' in R-LAUN                  -> V1 LAUNDRY (MEASURED); V2: a compound naming no room: HELD
         T3 Arabic 'swimming pool' in the court, no room -> V1 BATHROOM by its first word; V2 POOL; bound PARTIAL
         T4 'SWIMMING POOL' beside it (bilingual pair)  -> DUPLICATE_OF T3
         T5 'COURT', T6 'COURT' (one court, two labels)  -> MISSING with its scope; T6 DUPLICATE_OF T5
         T7 'MAID' in no room and with no ledger row     -> stays SILENT_OMISSION (genuinely unbound)
         T8 'VOID' on 1F, no room                        -> NOT_APPLICABLE with evidence
Hand quantities (the ledger's research figures; the census only checks them, never measures):
  pool water 4.00 x 2.00, depth 1.20, walls 0.20, base 0.25:
    walls  centreline 2 x (4.20 + 2.20) = 12.80 m x 0.20 x 1.40 = 3.584 m3  (line L-PW, bound by its source POOL-A)
    base   4.40 x 2.40 x 0.25 = 2.640 m3                                     (line L-PB)
    membrane MISSING  floor 8.00 + walls 2 x (4.00 + 2.00) x 1.20 = 14.40  -> 22.40 m2
  court 10.00 x 6.00 = 60.00 - pool outer 4.40 x 2.40 = 10.56 -> paving MISSING 49.44 m2
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import label_census as V1                          # noqa: E402
from tools import label_census_v2 as C                        # noqa: E402

POOL_AR = "حمام سباحة"
CARWASH_AR = "غسيل سيارات"
REG = [{"region_id": "S1:GF", "floor": "GF", "box": [0, 0, 20000, 15000]},
       {"region_id": "S1:1F", "floor": "1F", "box": [0, 20000, 20000, 35000]}]

WALLS = 2 * (4.20 + 2.20) * 0.20 * 1.40
BASE = 4.40 * 2.40 * 0.25
MEMBRANE = 4.0 * 2.0 + 2 * (4.0 + 2.0) * 1.20
PAVING = 10.0 * 6.0 - 4.40 * 2.40


def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def villa(scale=1.0, mirror=False):
    def p(x, y):
        return ((20000 - x) if mirror else x) * scale, y * scale

    def poly(pts):
        return [p(x, y) for x, y in pts]

    texts = [("T1", "BATHROOM", 1500, 1250), ("T2", CARWASH_AR, 4500, 1250), ("T3", POOL_AR, 12000, 8000),
             ("T4", "SWIMMING POOL", 12500, 8400), ("T5", "COURT", 9000, 12000), ("T6", "COURT", 16000, 12000),
             ("T7", "MAID", 18000, 2000), ("T8", "VOID", 10000, 28000)]
    texts = [{"id": i, "value": v, "encoding": "UNICODE", "x": p(x, y)[0], "y": p(x, y)[1]} for i, v, x, y in texts]
    regs = []
    for r in REG:
        (a, b), (c, d) = p(r["box"][0], r["box"][1]), p(r["box"][2], r["box"][3])
        regs.append(dict(r, box=[min(a, c), min(b, d), max(a, c), max(b, d)]))
    rooms = [{"room_id": "R-BATH", "face_id": "F-BATH", "floor": "GF", "codes": ["BATHROOM"],
              "polygon": poly(_rect(0, 0, 3000, 2500)), "area_m2": 7.5},
             {"room_id": "R-LAUN", "face_id": "F-LAUN", "floor": "GF", "codes": ["LAUNDRY"],
              "polygon": poly(_rect(3000, 0, 6000, 2500)), "area_m2": 7.5}]
    cov = [{"floor": "GF", "physical_regions": {"faces": [{"face_id": "F-BATH", "state": "LINE", "category": "ROOM_FLOOR"},
                                                          {"face_id": "F-LAUN", "state": "LINE", "category": "ROOM_FLOOR"}]}}]
    return texts, regs, rooms, cov


def ledger():
    rows = {
        "T3": {"text_id": "T3", "floor": "GF", "code": "POOL", "face_id": "X-POOL", "binding": "PARTIAL",
               "duplicate_of": None, "lines": ["L-PB", "L-PW"]},
        "T4": {"text_id": "T4", "floor": "GF", "code": "POOL", "face_id": "X-POOL", "binding": "DUPLICATE_OF",
               "duplicate_of": "T3", "lines": ["L-PB", "L-PW"]},
        "T5": {"text_id": "T5", "floor": "GF", "code": "GARDEN", "face_id": "X-COURT", "binding": "MISSING",
               "duplicate_of": None, "lines": []},
        "T6": {"text_id": "T6", "floor": "GF", "code": "GARDEN", "face_id": "X-COURT", "binding": "DUPLICATE_OF",
               "duplicate_of": "T5", "lines": []},
        "T8": {"text_id": "T8", "floor": "1F", "code": "VOID", "face_id": "X-VOID", "binding": "NOT_APPLICABLE",
               "duplicate_of": None, "lines": []},
    }
    scopes = {
        "X-POOL": [{"scope": "pool shell", "status": "BOUND", "lines": ["L-PW", "L-PB"], "refused": []},
                   {"scope": "pool membrane", "status": "MISSING", "lines": [], "refused": [],
                    "quantity": round(MEMBRANE, 6), "bound": None, "unit": "m2"},
                   {"scope": "wet-room tile / WP", "status": "NOT_APPLICABLE", "lines": [], "refused": [],
                    "evidence": "the label reads 'swimming pool' and lies in the pool face: no bathroom is drawn"}],
        "X-COURT": [{"scope": "court paving", "status": "MISSING", "lines": [], "refused": [],
                     "quantity": round(PAVING, 6), "unit": "m2"}],
        "X-VOID": [{"scope": "floor of the opening", "status": "NOT_APPLICABLE", "lines": [], "refused": [],
                    "evidence": "slab opening open to below"}],
    }
    return {"rows": rows, "scopes": scopes}


def lines():
    return {"L-PW": {"line_id": "L-PW", "item_code": "STR.CONC.POOL", "quantity": round(WALLS, 6),
                     "source": ["POOL-A"], "cites": []},
            "L-PB": {"line_id": "L-PB", "item_code": "STR.CONC.POOL", "quantity": round(BASE, 6),
                     "source": ["POOL-A"], "cites": []},
            "L-OTHER": {"line_id": "L-OTHER", "item_code": "FIN.FLOOR.PORCELAIN", "quantity": 7.5,
                        "source": [], "cites": ["T3"]}}


def run(scale=1.0, mirror=False, led=None, ln=None):
    t, r, rm, cv = villa(scale, mirror)
    return C.census_v2(t, r, rm, cv, (), ledger() if led is None else led, lines() if ln is None else ln)


def st(out):
    return {r["text_id"]: (r["status"], r["binding"], r["duplicate_of"]) for r in out["labels"]}


EXPECT = {"T1": ("MEASURED", None, None), "T2": ("HELD", None, None), "T3": ("ACCOUNTED_BY_BINDING", "PARTIAL", None),
          "T4": ("ACCOUNTED_BY_BINDING", "PARTIAL", "T3"), "T5": ("ACCOUNTED_BY_BINDING", "MISSING", None),
          "T6": ("ACCOUNTED_BY_BINDING", "MISSING", "T5"), "T7": ("SILENT_OMISSION", None, None),
          "T8": ("ACCOUNTED_BY_BINDING", "NOT_APPLICABLE", None)}


def test_hand_quantities():
    assert WALLS == pytest.approx(3.584) and BASE == pytest.approx(2.64)
    assert MEMBRANE == pytest.approx(22.40) and PAVING == pytest.approx(49.44)


def test_normal_case():
    out = run()
    assert st(out) == EXPECT
    s = out["summary"]
    assert s["policy"] == "URBAN_LABEL_CENSUS_V2" and s["vocabulary"] == "ROOM_VOCAB_V2"
    assert s["by_status"] == {"MEASURED": 1, "HELD": 1, "UNSUPPORTED": 0, "ACCOUNTED_BY_BINDING": 5,
                              "SILENT_OMISSION": 1}
    assert s["by_binding"] == {"BOUND": 0, "PARTIAL": 1, "MISSING": 1, "NOT_APPLICABLE": 1}
    assert s["duplicates_counted_once"] == 2
    assert s["silent_by_cause"] == {"NO_ROOM": 1}                     # T7: the genuinely unbound label
    by = {r["text_id"]: r for r in out["labels"]}
    assert by["T3"]["code"] == "POOL" and by["T3"]["v1_code"] == "BATHROOM" and by["T3"]["retype"].startswith("RETYPED")
    assert by["T3"]["lines"] == ["L-PB", "L-PW"]
    assert by["T2"]["cause"] == "VOCAB_V2_HELD_COMPOUND" and by["T2"]["census_v1_status"] == "MEASURED"
    assert s["open_scopes"] == {"T3": ["pool membrane: 22.4 m2"], "T5": ["court paving: 49.44 m2"]}


@pytest.mark.parametrize("scale,mirror", [(0.001, False), (1.0, True), (0.001, True)])
def test_mirror_and_metres_read_alike(scale, mirror):
    assert st(run(scale, mirror)) == EXPECT


def test_v1_tool_unchanged_and_inputs_not_mutated():
    t, r, rm, cv = villa()
    before = copy.deepcopy((t, r, rm, cv))
    v1 = V1.census(t, r, rm, cv)
    C.census_v2(t, r, rm, cv, (), ledger(), lines())
    assert (t, r, rm, cv) == before
    assert V1.census(t, r, rm, cv) == v1                               # V1 output identical before / after
    s1 = {x["text_id"]: (x["code"], x["status"]) for x in v1["labels"]}
    assert s1["T3"] == ("BATHROOM", "SILENT_OMISSION") and s1["T2"] == ("LAUNDRY", "MEASURED")
    assert v1["summary"]["policy"] == "URBAN_LABEL_CENSUS_V1" and v1["summary"]["by_status"]["SILENT_OMISSION"] == 6


def test_without_ledger_every_unbound_label_stays_silent():
    t, r, rm, cv = villa()
    out = C.census_v2(t, r, rm, cv)
    assert out["summary"]["by_status"]["SILENT_OMISSION"] == 6 and out["summary"]["binding_rule"] is None


# ---- adverse --------------------------------------------------------------------------------------------------
def _refusal(out, tid):
    r = {x["text_id"]: x for x in out["labels"]}[tid]
    assert r["status"] == "SILENT_OMISSION", r
    return r["binding_refused"]


def test_adverse_bathroom_word_inside_a_pool_compound_is_not_bound_as_a_bathroom():
    # read with V1 (first word): the pool label is a BATHROOM; the POOL row of the ledger must be refused, and the
    # duplicate that leans on it too (never wet-room scope from a bare word the compound contradicts)
    led = ledger()
    b, _, _, why = C.check_row("T3", "GF", "BATHROOM", led, lines())
    assert b is None and why.startswith("REFUSED_CODE")
    led["rows"]["T3"]["code"] = "BATHROOM"                             # a ledger that took the bare word
    out = run(led=led)
    assert _refusal(out, "T3").startswith("REFUSED_CODE")
    assert _refusal(out, "T4") == "REFUSED_DUPLICATE_OTHER_CODE BATHROOM vs POOL"
    led = ledger()                                                     # the first label refused by its census floor
    led["rows"]["T3"]["floor"] = "1F"                                  # refuses its duplicate too (counted once)
    out = run(led=led)
    assert _refusal(out, "T3").startswith("REFUSED_FLOOR")
    assert _refusal(out, "T4").startswith("REFUSED_DUPLICATE_TARGET_REFUSED T3: REFUSED_FLOOR")


def test_adverse_binding_by_name_only_is_refused():
    led = ledger()
    led["rows"]["T3"]["lines"] = ["L-OTHER", "L-PB", "L-PW"]          # a line no BOUND scope carries
    assert _refusal(run(led=led), "T3").startswith("REFUSED_NAME_ONLY L-OTHER")
    led = ledger()                                                     # a scope line known only by citing the label
    led["scopes"]["X-POOL"][0]["lines"] = ["L-OTHER", "L-PB", "L-PW"]
    led["rows"]["T3"]["lines"] = ["L-OTHER", "L-PB", "L-PW"]
    assert _refusal(run(led=led), "T3").startswith("REFUSED_NAME_ONLY L-OTHER (its own inputs")


def test_adverse_binding_to_a_non_existent_line_is_refused():
    led = ledger()
    led["scopes"]["X-POOL"][0]["lines"] = ["L-GHOST", "L-PB"]
    led["rows"]["T3"]["lines"] = ["L-GHOST", "L-PB"]
    assert _refusal(run(led=led), "T3") == "REFUSED_UNKNOWN_LINE L-GHOST"
    t, r, rm, cv = villa()                                             # no candidate at all: bound lines unchecked
    out = C.census_v2(t, r, rm, cv, (), ledger(), None)
    assert _refusal(out, "T3").startswith("REFUSED_NO_CANDIDATE")
    assert {x["text_id"]: x["status"] for x in out["labels"]}["T5"] == "ACCOUNTED_BY_BINDING"   # no line needed


def test_adverse_missing_scope_carried_as_zero_or_a_zero_line_is_refused():
    led = ledger()
    led["scopes"]["X-COURT"][0]["quantity"] = 0.0
    assert _refusal(run(led=led), "T5").startswith("REFUSED_MISSING_AS_ZERO")
    assert _refusal(run(led=led), "T6").startswith("REFUSED_DUPLICATE_TARGET_REFUSED")
    led = ledger()
    led["scopes"]["X-COURT"][0]["quantity"] = None
    assert _refusal(run(led=led), "T5").startswith("REFUSED_MISSING_UNQUANTIFIED")
    ln = lines()
    ln["L-PW"]["quantity"] = 0
    assert _refusal(run(ln=ln), "T3") == "REFUSED_ZERO_LINE L-PW"


def test_adverse_not_applicable_without_evidence_and_inconsistent_binding():
    led = ledger()
    led["scopes"]["X-VOID"][0]["evidence"] = None
    assert _refusal(run(led=led), "T8").startswith("REFUSED_NOT_APPLICABLE_WITHOUT_EVIDENCE")
    led = ledger()
    led["rows"]["T3"]["binding"] = "BOUND"                             # the membrane is MISSING: the row overstates
    assert _refusal(run(led=led), "T3") == "REFUSED_BINDING_INCONSISTENT row BOUND vs scopes PARTIAL"


def test_adverse_duplicate_of_another_face_or_wrong_floor_is_refused():
    led = ledger()
    led["rows"]["T6"]["duplicate_of"] = "T3"
    assert _refusal(run(led=led), "T6").startswith("REFUSED_DUPLICATE_OTHER_FACE")
    led = ledger()
    led["rows"]["T8"]["floor"] = "GF"
    assert _refusal(run(led=led), "T8").startswith("REFUSED_FLOOR")
    led = ledger()
    led["rows"]["T5"]["binding"] = "MISSING_NO_FACE"
    assert _refusal(run(led=led), "T5") == "REFUSED_NO_FACE"


def test_ledger_csv_round_trip(tmp_path):
    led = ledger()
    import csv
    rp, sp = tmp_path / "rows.csv", tmp_path / "scopes.csv"
    with open(rp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, ["text_id", "floor", "code", "face_id", "binding", "duplicate_of", "lines"])
        w.writeheader()
        for r in led["rows"].values():
            w.writerow({**r, "duplicate_of": r["duplicate_of"] or "", "lines": json.dumps(r["lines"])})
    with open(sp, "w", newline="", encoding="utf-8") as fh:
        cols = ["face_id", "scope", "status", "lines", "refused", "quantity", "bound", "unit", "evidence_status",
                "evidence"]
        w = csv.DictWriter(fh, cols)
        w.writeheader()
        for f, ss in led["scopes"].items():
            for s in ss:
                w.writerow({"face_id": f, "scope": s["scope"], "status": s["status"], "lines": json.dumps(s["lines"]),
                            "refused": json.dumps(s["refused"]), "quantity": s.get("quantity") or "",
                            "bound": json.dumps(s["bound"]) if s.get("bound") else "", "unit": s.get("unit") or "",
                            "evidence_status": "", "evidence": s.get("evidence") or ""})
    assert st(run(led=C.load_ledger(rp, sp))) == EXPECT


def test_dxf_run_types_the_pool_compound(tmp_path):
    """one architectural run on a drawn plan: the compound pool label outside every room is typed POOL by V2 (V1:
    BATHROOM) and bound by the ledger; a COURT label with no ledger row stays SILENT_OMISSION."""
    import ezdxf
    from tools import urban_boq_m9 as M
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    for n in ("A-WALL", "A-TEXT", "A-FRAME"):
        doc.layers.add(n)
    msp = doc.modelspace()
    msp.add_lwpolyline(_rect(-8000, -9000, 14000, 12000), close=True, dxfattribs={"layer": "A-FRAME"})
    msp.add_text("GROUND FLOOR PLAN", dxfattribs={"layer": "A-TEXT", "height": 500}).set_placement((-6000, -8000))
    for x0, y0, x1, y1 in ((0, 0, 4400, 0), (4400, 0, 4400, 3400), (4400, 3400, 0, 3400), (0, 3400, 0, 0),
                           (200, 200, 4200, 200), (4200, 200, 4200, 3200), (4200, 3200, 200, 3200),
                           (200, 3200, 200, 200)):
        msp.add_line((x0, y0), (x1, y1), dxfattribs={"layer": "A-WALL"})
    for txt, xy in (("KITCHEN", (2200, 1700)), (POOL_AR, (8000, 1700)), ("COURT", (8000, 6000))):
        msp.add_text(txt, dxfattribs={"layer": "A-TEXT", "height": 150}).set_placement(xy)
    path = tmp_path / "villa.dxf"
    doc.saveas(str(path))
    boq, arch, intake = M.arch_compute(str(path), method="ARCH_TAKEOFF_V2.9", layer_roles={"A-WALL": "WALL"})
    v1 = V1.census_of_run((boq, arch, intake))
    pool_tid = [r["text_id"] for r in v1["labels"] if r["text"] == POOL_AR][0]
    led = {"rows": {pool_tid: dict(ledger()["rows"]["T3"], text_id=pool_tid, floor=[r for r in v1["labels"]
                                                                                    if r["text_id"] == pool_tid][0]["floor"])},
           "scopes": ledger()["scopes"]}
    out = C.census_v2(intake.get("texts") or (), arch.get("regions") or (), arch.get("rooms") or (),
                      arch.get("coverage") or (), boq.get("unresolved") or (), led, lines())
    by = {r["text"]: r for r in out["labels"]}
    assert {r["text"]: r["code"] for r in v1["labels"]}[POOL_AR] == "BATHROOM"
    assert by[POOL_AR]["code"] == "POOL" and by[POOL_AR]["status"] == "ACCOUNTED_BY_BINDING"
    assert by[POOL_AR]["binding"] == "PARTIAL"
    assert by["COURT"]["status"] == "SILENT_OMISSION" and by["COURT"]["binding_refused"] == "NO_BINDING_ROW"
    assert by["KITCHEN"]["status"] == {r["text"]: r["status"] for r in v1["labels"]}["KITCHEN"]
    assert len(out["labels"]) == len(v1["labels"])                    # no label dropped by the vocabulary change
