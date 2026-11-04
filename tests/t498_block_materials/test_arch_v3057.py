"""T-498 ARCH_TAKEOFF_V3.0.57 on a synthetic villa-K498 candidate (hand fixture, not the development villa): blockwork
material lines beside the MAS.BLOCK lines; every base line byte-identical; adverse inputs refused.

Villa K498 by hand (company rulebook: black 12.5 / m2 for the 40 x 20 module, 0.20 m only; glue 3.5 / 4.5 kg/m2;
mortar 1:4 = 8 bags + 1.1 m3 sand per m3; joint 0.39 x 0.19 unit in a 0.40 x 0.20 module -> 0.07375 t m3/m2):
  A  GF black 0.20 VERIFIED, net 20.000 m2, REQUIRED RC lintel D-A (w 1.00, L 1.80, D 0.20): face 0.360 m2
       base 19.640 m2 -> 245.500 pcs; mortar 19.64 x 0.01475 = 0.289690 m3 -> 2.31752 bags, 0.318659 m3 sand beside
  B  1F white 0.15 DRAWING-CONFIRMED, net 10.000 m2, HELD lintel D-B face 0 .. 0.320 m2
       base range 9.680 .. 10.000 m2 -> glue 33.880 .. 35.000 kg (BOUNDED); white units HELD
  C  1F black 0.15 OWNER-APPROVED, net 8.000 m2: units HELD (module not stated), mortar HELD,
       beside 8 x 0.0110625 = 0.0885 m3
  D  GF white 0.20 VERIFIED, net 5.000 m2 -> glue 22.500 kg; white units HELD
  E  2F parent t=0.20 BLOCKED (colour not split) -> 4 blank material lines by name, never 0
  -> 12 lines added; totals move only in the four material codes; every base line byte-identical."""
import copy

import pytest

from engine.source import arch_v304 as A304
from engine.source import arch_v3057 as M
from engine.source import boq_line as BL

PID, REV = "villa-k498", "0" * 64
E_A = "GF-WALLS:walls t=0.20#BLOCKWORK:VERIFIED_BLACK"
E_B = "1F-WALLS:walls t=0.15#BLOCKWORK:DRAWING_CONFIRMED_WHITE"
E_C = "1F-WALLS:walls t=0.15#BLOCKWORK:ASSUMED___OWNER_APPROVED_BLACK"
E_D = "GF-WALLS:walls t=0.20#BLOCKWORK:VERIFIED_WHITE"
E_E = "2F-WALLS:walls t=0.20"


def mk(eid, code, unit, state, net=None, floor="GF", inputs=None):
    return BL.make_line(inputs=inputs, project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                        measured_net=net, gross=net, element_id=eid, floor=floor, formula="synthetic", rule_id="R-X",
                        rule_version="1", item_en=code, item_ar=code, trade=None if code in BL.ITEMS else "MASONRY",
                        rfi={"question": "roof datum not printed"} if state == "BLOCKED_RFI" else None)


def lid(eid, code="MAS.BLOCK", unit="m2"):
    return BL.line_id(PID, code, eid, "R-X", "1", unit)


def candidate():
    return [mk(E_A, "MAS.BLOCK", "m2", "MEASURED", 20.0),
            mk(E_B, "MAS.BLOCK", "m2", "SOURCE_DERIVED", 10.0, floor="1F"),
            mk(E_C, "MAS.BLOCK", "m2", "PROVISIONAL", 8.0, floor="1F"),
            mk(E_D, "MAS.BLOCK", "m2", "MEASURED", 5.0),
            mk(E_E, "MAS.BLOCK", "m2", "BLOCKED_RFI", floor="2F"),
            mk("LINTEL:D-A", "STR.CONC.LINTEL", "m3", "PROVISIONAL", 0.072, inputs={"lintel_v3053": {
                "opening_id": "D-A", "decision": "REQUIRED", "width_m": 1.0, "bearing_m": 0.40, "section_m": [0.20, 0.20],
                "length_m": 1.80, "pieces": 1, "formwork_m2_beside": 0.92, "host_face_m2": 0.36,
                "host_line": lid(E_A)}}),
            mk("LINTEL:D-B", "STR.CONC.LINTEL", "m3", "BLOCKED_RFI", floor="1F", inputs={"lintel_v3053": {
                "opening_id": "D-B", "decision": "HELD", "why": "head not printed", "host_line": lid(E_B)}}),
            mk("GF-R1:skirting", "FIN.SKIRTING", "lm", "MEASURED", 9.0)]


SRC = [{"task": "T-K", "file": "ledger.py", "sha256": "k" * 64, "merge_commit": "abcdef12", "checker_run": "run k"}]
JOINT = {"module_m": [0.40, 0.20], "unit_m": [0.39, 0.19], "joint_mm": 10, "status": "OWNER-PROVISIONAL",
         "source": "villa K498 joint"}
EXPECT = {lid(E_A): {M.U_BLACK: 245.5, M.MORTAR: 0.28969},
          lid(E_B): {M.GLUE: [33.88, 35.0], M.U_WHITE: "HELD"},
          lid(E_C): {M.U_BLACK: "HELD", M.MORTAR: "HELD"},
          lid(E_D): {M.GLUE: 22.5, M.U_WHITE: "HELD"}}


def doc(**over):
    d = {"schema": M.INPUTS_SCHEMA, "project": PID, "sources": SRC, "joint": copy.deepcopy(JOINT),
         "faces": {lid(E_A): {"required": [{"opening_id": "D-A", "face_m2": 0.36}], "held": []},
                   lid(E_B): {"required": [], "held": [{"opening_id": "D-B", "face_max_m2": 0.32, "why": "head"}]}},
         "expect": copy.deepcopy(EXPECT)}
    d.update(over)
    return d


def run(d=None, prev=None):
    prev = candidate() if prev is None else prev
    ch, log = M.changes_for(M.load_inputs(d or doc(), PID), prev)
    new, ident = M.integrate(prev, ch)
    return prev, ch, log, new, ident


def by(ch):
    return {(c["after"]["calculation"]["inputs"][M.REC_KEY]["source_line_id"], c["after"]["item_code"]): c["after"]
            for c in ch}


def test_normal_hand_figures():
    prev, ch, log, new, ident = run()
    b = by(ch)
    assert len(ch) == 12 and ident["added"] == 12 and ident["replaced"] == 0
    a = b[(lid(E_A), M.U_BLACK)]
    assert a["evidence_state"] == "MEASURED" and a["measured_net"] == pytest.approx(245.5) and a["unit"] == "pcs"
    m = b[(lid(E_A), M.MORTAR)]
    assert m["evidence_state"] == "PROVISIONAL" and m["measured_net"] == pytest.approx(0.28969)
    bm = m["calculation"]["inputs"][M.REC_KEY]["beside_materials"]
    assert bm["cement_bags_50kg"] == pytest.approx(2.31752) and bm["sand_m3_loose"] == pytest.approx(0.318659)
    lint = m["calculation"]["inputs"][M.REC_KEY]["base"]["lintels"]
    assert lint[0]["lintel_line_id"] == lid("LINTEL:D-A", "STR.CONC.LINTEL", "m3") and lint[0]["kind"] == "REQUIRED"
    g = b[(lid(E_B), M.GLUE)]
    assert g["evidence_state"] == "BOUNDED_EXPOSURE" and g["measured_net"] is None
    assert (g["bounded_range"]["low"], g["bounded_range"]["high"]) == pytest.approx((33.88, 35.0))
    assert b[(lid(E_D), M.GLUE)]["measured_net"] == pytest.approx(22.5)
    c = b[(lid(E_C), M.MORTAR)]
    assert c["evidence_state"] == "BLOCKED_RFI" and c["measured_net"] is None
    assert c["calculation"]["inputs"][M.REC_KEY]["figure_beside"]["mortar_m3"] == pytest.approx(0.0885)
    held = [b[(lid(E_E), k)] for k in M.CODES]
    assert all(x["evidence_state"] == "BLOCKED_RFI" and x["measured_net"] is None for x in held)
    assert all(b[k]["evidence_state"] == "BLOCKED_RFI" for k in b if k[1] == M.U_WHITE)


def test_base_lines_byte_identical_and_totals_only_material_codes():
    prev, ch, log, new, ident = run()
    assert [BL.dumps([x]) for x in new[:len(prev)]] == [BL.dumps([x]) for x in prev]
    moved = M.check_totals(A304.code_totals(prev), A304.code_totals(new))
    assert moved and all(k.split("|")[0] in M.CODES for k in moved)
    assert ident["materials"]["material_lines"] == 12 and ident["materials"]["producers"] == 12


def test_mirror_order_does_not_change_lines():
    """the same lines in reverse order give the same material lines (no order dependence)."""
    _, ch1, *_ = run()
    _, ch2, *_ = run(prev=list(reversed(candidate())))
    assert sorted(BL.dumps([c["after"]]) for c in ch1) == sorted(BL.dumps([c["after"]]) for c in ch2)


def test_adverse_unbounded_held_face_holds_material():
    d = doc()
    d["faces"][lid(E_B)]["held"][0]["face_max_m2"] = None
    d["expect"][lid(E_B)][M.GLUE] = "HELD"
    _, ch, *_ = run(d)
    g = by(ch)[(lid(E_B), M.GLUE)]
    assert g["evidence_state"] == "BLOCKED_RFI" and g["measured_net"] is None and not g.get("bounded_range")


@pytest.mark.parametrize("mutate,msg", [
    (lambda d: d["faces"][lid(E_A)]["required"][0].update(face_m2=360.0), "millimetres"),
    (lambda d: d.update(rates={"black": 12.5}), "typed rate"),
    (lambda d: d["faces"].update({lid(E_E): {"required": [{"opening_id": "D-X", "face_m2": 0.3}]}}), "HELD line"),
    (lambda d: d["faces"][lid(E_A)]["required"].append({"opening_id": "D-B", "face_m2": 0.3}), "two lines"),
    (lambda d: d["faces"][lid(E_A)]["required"].__setitem__(0, {"opening_id": "D-A", "face_m2": 25.0}), "millimetres"),
    (lambda d: d["expect"][lid(E_A)].update({M.U_BLACK: 250.0}), "expected"),
    (lambda d: d.update(sources=[]), "no source"),
])
def test_adverse_inputs_refused(mutate, msg):
    d = doc()
    mutate(d)
    with pytest.raises(M.InputsError, match=msg):
        run(d)


def test_adverse_face_larger_than_line_refused():
    d = doc()
    d["faces"][lid(E_D)] = {"required": [{"opening_id": "D-A2", "face_m2": 6.0}], "held": []}
    prev = candidate() + [mk("LINTEL:D-A2", "STR.CONC.LINTEL", "m3", "PROVISIONAL", 0.5)]  # never integrated
    with pytest.raises(M.InputsError, match="exceed the line net"):
        run(d, prev)


def test_adverse_required_face_on_blank_lintel_refused():
    d = doc()
    d["faces"][lid(E_A)]["required"][0]["opening_id"] = "D-B"
    d["faces"][lid(E_B)]["held"] = []
    with pytest.raises(M.InputsError, match="no valued"):
        run(d)


def test_adverse_second_producer_refused():
    prev = candidate() + [mk("MATERIAL:x", M.U_BLACK, "pcs", "MEASURED", 10.0)]
    with pytest.raises(M.InputsError, match="one producer"):
        run(prev=prev)


def test_adverse_missing_net_never_zero():
    """a released masonry line with no colour key cannot produce materials (refused), a held one is blank by name."""
    prev = candidate()
    prev[0] = mk("GF-WALLS:walls t=0.20", "MAS.BLOCK", "m2", "MEASURED", 20.0)
    d = doc(faces={}, expect={})
    with pytest.raises(M.InputsError, match="no block type"):
        run(d, prev)


def test_joint_geometry():
    assert M.joint_m3_per_m2(JOINT, 0.20) == pytest.approx(0.01475)
    assert M.joint_m3_per_m2(JOINT, 0.15) == pytest.approx(0.0110625)
