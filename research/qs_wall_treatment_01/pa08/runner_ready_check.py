"""PA08 runner-ready check: a DRY RUN of the whole validation harness on a synthetic villa.

This is NOT independent validation (the villa is written by the engine's author) and the result is marked so.  It
proves only that every step executes end to end: acceptance refuses the synthetic source as validation, the truth
pack validates and seals, the blind subprocess runs the generic pipeline with the file-access audit, the output is
frozen before the truth is opened, the comparison classifies every fact, gate v4 evaluates, and a deliberate leak
(a forbidden path in the run's sources) is caught as VALIDATION_INVALID.
"""

from __future__ import annotations

import json
import math
import os
import shutil
from pathlib import Path

from research.qs_wall_treatment_01.pa08 import blind_run as BR, compare as CMP, config as C8, gate_v4 as G4, source_acceptance as SA, truth_pack as TP

T = 200.0     # wall thickness of the synthetic villa (mm)


def _wall(a, b, t=T, layer="W"):
    L = math.hypot(b[0] - a[0], b[1] - a[1]); ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L; nx, ny = -uy, ux
    return [{"kind": "SEGMENT", "layer": layer, "x1": a[0] + nx * t / 2, "y1": a[1] + ny * t / 2, "x2": b[0] + nx * t / 2, "y2": b[1] + ny * t / 2},
            {"kind": "SEGMENT", "layer": layer, "x1": a[0] - nx * t / 2, "y1": a[1] - ny * t / 2, "x2": b[0] - nx * t / 2, "y2": b[1] - ny * t / 2}]


def _seg(a, b, layer="W"):
    return {"kind": "SEGMENT", "layer": layer, "x1": a[0], "y1": a[1], "x2": b[0], "y2": b[1]}


def _door(axis_pt_a, axis_pt_b, t=T, leaf=True):
    """Jambs across the wall at both ends of the gap plus a quarter-circle leaf swing from the second jamb."""
    (xa, ya), (xb, yb) = axis_pt_a, axis_pt_b
    if abs(ya - yb) < 1e-9:      # wall along x
        out = [_seg((xa, ya - t / 2), (xa, ya + t / 2)), _seg((xb, yb - t / 2), (xb, yb + t / 2))]
        if leaf:
            out.append({"kind": "ARC", "layer": "D", "cx": xb, "cy": yb + t / 2, "r": abs(xb - xa), "a0": math.pi / 2, "a1": math.pi})
    else:                       # wall along y
        out = [_seg((xa - t / 2, ya), (xa + t / 2, ya)), _seg((xb - t / 2, yb), (xb + t / 2, yb))]
        if leaf:
            out.append({"kind": "ARC", "layer": "D", "cx": xa + t / 2, "cy": ya, "r": abs(yb - ya), "a0": 0.0, "a1": math.pi / 2})
    return out


def synthetic_villa(path):
    """Six-case villa: LIVING (V1), KITCHEN with a door (V2), an L-shaped STUDY (V3), a DINING room with a curved wall (V4),
    an open passage STUDY-DINING (V5), a column protruding into the KITCHEN at its east wall (V6).  Axis coordinates in mm."""
    P = []
    # ground ring and the shared walls (axis lines)
    # walls are drawn the CAD way: the faces stop at every door / passage gap (the jambs close the gap ends)
    for a, b in (((0, 0), (12000, 0)), ((0, 0), (0, 8000)), ((0, 8000), (4000, 8000)), ((4000, 8000), (4000, 6500)), ((4000, 6500), (6000, 6500)),
                 ((0, 4000), (2000, 4000)), ((2900, 4000), (8000, 4000)), ((8900, 4000), (12000, 4000)),
                 ((6000, 0), (6000, 1500)), ((6000, 2400), (6000, 4600)), ((6000, 6300), (6000, 8000)), ((12000, 0), (12000, 5000)), ((6000, 8000), (9000, 8000))):
        P += _wall(a, b)
    # curved wall of the DINING room: centre (9000, 5000), axis radius 3000, from (12000, 5000) to (9000, 8000)
    P += [{"kind": "ARC", "layer": "W", "cx": 9000.0, "cy": 5000.0, "r": 3000.0 - T / 2, "a0": 0.0, "a1": math.pi / 2}, {"kind": "ARC", "layer": "W", "cx": 9000.0, "cy": 5000.0, "r": 3000.0 + T / 2, "a0": 0.0, "a1": math.pi / 2}]
    # doors: LIVING-KITCHEN in the x=6000 wall (y 1500..2400), LIVING-STUDY in the y=4000 wall (x 2000..2900), KITCHEN-DINING in the y=4000 wall (x 8000..8900)
    P += _door((6000, 1500), (6000, 2400)) + _door((2000, 4000), (2900, 4000)) + _door((8000, 4000), (8900, 4000))
    # open passage STUDY-DINING in the x=6000 wall: jambs at y=4600 and y=6300 (1700 wide), no leaf
    P += _door((6000, 4600), (6000, 6300), leaf=False)
    # column 400 x 400 protruding into the KITCHEN from the east wall inner face (x = 11900): crossed rectangle
    P += [_seg((11500, 1800), (11900, 1800)), _seg((11500, 2200), (11900, 2200)), _seg((11500, 1800), (11500, 2200)), _seg((11500, 1800), (11900, 2200), "C"), _seg((11500, 2200), (11900, 1800), "C")]
    # hatch strokes on the south wall (material evidence), a dimension, small furniture entities for view clustering
    P += [_seg((1000 + i * 60, -40), (1040 + i * 60, 40)) for i in range(20)]
    P += [_seg((0, -600), (12000, -600), "DIM")]
    P += [{"kind": "CIRCLE", "layer": "F", "cx": 2000 + i * 150, "cy": 3000, "r": 20} for i in range(40)]
    # drawing frame so no wall is the outermost line of the view
    for a, b in (((-3000, -3000), (16000, -3000)), ((16000, -3000), (16000, 11000)), ((16000, 11000), (-3000, 11000)), ((-3000, 11000), (-3000, -3000))):
        P.append(_seg(a, b, "FRAME"))
    doc = {"insunits": 4, "dimlfac": 1.0, "linetypes": {"W": "CONTINUOUS", "D": "CONTINUOUS", "DIM": "CONTINUOUS", "F": "CONTINUOUS", "C": "CONTINUOUS", "FRAME": "CONTINUOUS"}, "primitives": P,
           "texts": [{"value": "LIVING", "x": 3000, "y": 2000}, {"value": "KITCHEN", "x": 9000, "y": 2000}, {"value": "STUDY", "x": 2000, "y": 6000}, {"value": "DINING", "x": 8000, "y": 5500}, {"value": "%%p0.00", "x": 500, "y": 3500}],
           "dimensions": [{"x1": 0, "y1": -600, "x2": 12000, "y2": -600, "display": 12000}]}
    Path(path).write_text(json.dumps(doc), "utf-8")
    return Path(path)


def synthetic_truth_pack():
    """Hand-coded from the synthetic villa's construction (the way a verifier reads the original sheet): axis basis, never from the engine."""
    def w(sid, a, b, t=T):
        return {"SEGMENT_ID": sid, "A_MM": list(a), "B_MM": list(b), "THICKNESS_MM": t, "ROLE": "WALL", "MATERIAL_PRESENT": True, "DEVELOPED_LENGTH_MM": math.hypot(b[0] - a[0], b[1] - a[1])}
    def op(oid, host, a, b, role):
        return {"OPENING_ID": oid, "HOST_SEGMENT_ID": host, "A_MM": list(a), "B_MM": list(b), "WIDTH_MM": math.hypot(b[0] - a[0], b[1] - a[1]), "ROLE": role}
    common = {"SOURCE_SHEET": "SYNTHETIC_VILLA / MODEL", "VERIFIER": "dry run author (NOT independent)", "VERIFIED_ON": "synthetic", "MEASUREMENT_BASIS": "AXIS", "CURVED_SEGMENTS": [], "OPEN_EDGES": [], "COLUMNS": []}
    cases = [
        dict(common, CASE_ID="V1", CASE_KIND="V1", SOURCE_LOCATOR={"BBOX_MM": [-300, -300, 6300, 4300]},
             WALL_SEGMENTS=[w("V1-S", (0, 0), (12000, 0)), w("V1-W", (0, 0), (0, 8000))], OPENINGS=[], PHYSICAL_SPACE_RELATION={"SPACE_COUNT": 1, "RELATIONS": []}, MANUALLY_VERIFIED_DIMENSIONS={"CLEAR_X_MM": 5800, "CLEAR_Y_MM": 3800}),
        dict(common, CASE_ID="V2", CASE_KIND="V2", SOURCE_LOCATOR={"BBOX_MM": [5700, -300, 12300, 4300]},
             WALL_SEGMENTS=[w("V2-E", (12000, 0), (12000, 5000)), w("V2-M", (6000, 0), (6000, 8000))], OPENINGS=[op("V2-D1", "V2-M", (6000, 1500), (6000, 2400), "DOOR")],
             PHYSICAL_SPACE_RELATION={"SPACE_COUNT": 1, "RELATIONS": [["KITCHEN", "LIVING", "DOOR"]]}, MANUALLY_VERIFIED_DIMENSIONS={"CLEAR_X_MM": 5800, "CLEAR_Y_MM": 3800}),
        dict(common, CASE_ID="V3", CASE_KIND="V3", SOURCE_LOCATOR={"BBOX_MM": [-300, 3700, 6300, 8300]},
             WALL_SEGMENTS=[w("V3-N", (0, 8000), (4000, 8000)), w("V3-NOTCH-V", (4000, 8000), (4000, 6500)), w("V3-NOTCH-H", (4000, 6500), (6000, 6500)), w("V3-S", (0, 4000), (12000, 4000))],
             OPENINGS=[op("V3-D1", "V3-S", (2000, 4000), (2900, 4000), "DOOR")], PHYSICAL_SPACE_RELATION={"SPACE_COUNT": 1, "RELATIONS": [["STUDY", "LIVING", "DOOR"]]},
             MANUALLY_VERIFIED_DIMENSIONS={"CLEAR_X_MM": 5800, "CLEAR_Y_MM": 3800, "NOTCH_MM": [1800, 1400]}),
        dict(common, CASE_ID="V4", CASE_KIND="V4", SOURCE_LOCATOR={"BBOX_MM": [5700, 3700, 12300, 8300]},
             WALL_SEGMENTS=[w("V4-N", (6000, 8000), (9000, 8000))],
             CURVED_SEGMENTS=[{"SEGMENT_ID": "V4-ARC", "CENTRE_MM": [9000, 5000], "RADIUS_AXIS_MM": 3000, "START_ANGLE_RAD": 0.0, "END_ANGLE_RAD": math.pi / 2, "THICKNESS_MM": T, "ROLE": "WALL", "MATERIAL_PRESENT": True,
                              "DEVELOPED_LENGTH_MM": 3000 * math.pi / 2}],
             OPENINGS=[op("V4-D1", "V3-S", (8000, 4000), (8900, 4000), "DOOR")], PHYSICAL_SPACE_RELATION={"SPACE_COUNT": 1, "RELATIONS": [["DINING", "KITCHEN", "DOOR"]]},
             MANUALLY_VERIFIED_DIMENSIONS={"ARC_RADIUS_AXIS_MM": 3000, "ARC_SWEEP_DEG": 90}),
        dict(common, CASE_ID="V5", CASE_KIND="V5", SOURCE_LOCATOR={"BBOX_MM": [3700, 4300, 8300, 6700]},
             WALL_SEGMENTS=[], OPENINGS=[op("V5-P1", "V2-M", (6000, 4600), (6000, 6300), "OPEN_PASSAGE")], OPEN_EDGES=[{"EDGE_ID": "V5-E1", "A_MM": [6000, 4600], "B_MM": [6000, 6300], "ROLE": "OPEN_PASSAGE"}],
             PHYSICAL_SPACE_RELATION={"SPACE_COUNT": 2, "RELATIONS": [["STUDY", "DINING", "OPEN"]]}, MANUALLY_VERIFIED_DIMENSIONS={"PASSAGE_WIDTH_MM": 1700}),
        dict(common, CASE_ID="V6", CASE_KIND="V6", SOURCE_LOCATOR={"BBOX_MM": [11000, 1300, 12300, 2700]},
             WALL_SEGMENTS=[], OPENINGS=[], COLUMNS=[{"COLUMN_ID": "V6-C1", "CENTRE_MM": [11700, 2000], "SIDES_MM": [400, 400], "EXPOSED_FACES": ["W", "N", "S"], "EMBEDDED_FACES": ["E"]}],
             PHYSICAL_SPACE_RELATION={"SPACE_COUNT": None, "RELATIONS": [], "NOTE": "locator smaller than the room: count not compared"}, MANUALLY_VERIFIED_DIMENSIONS={"COLUMN_MM": [400, 400]}),
    ]
    return {"ARTIFACT": "TRUTH_PACK", "PROJECT_ALIAS": "SYNTHETIC_DRY_RUN", "INDEPENDENT": False, "BUILT_BEFORE_PRODUCTION_RUN": True, "SOURCE_OF_TRUTH": "original source drawings only",
            "NOTE": "synthetic villa written by the engine's author: exercises the harness only, never counts as validation", "CASES": cases}


def run(out_dir=None):
    out = Path(out_dir or C8.OUT8) / "dry_run"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    villa = synthetic_villa(out / "SYNTHETIC_VILLA.json")
    steps = []
    # 1 acceptance: a synthetic primitive JSON is refused as validation (and there is no PDF)
    acc = SA.accept("SYNTHETIC_DRY_RUN", [str(villa)], {str(villa): "ARCHITECTURAL"})
    (out / "PA08_SOURCE_ACCEPTANCE.json").write_text(json.dumps(acc, indent=1), "utf-8")
    steps.append({"STEP": "SOURCE_ACCEPTANCE", "OK": acc["INDEPENDENT_VALIDATION_STATUS"] == "REJECTED_SYNTHETIC_DRY_RUN_ONLY", "STATUS": acc["INDEPENDENT_VALIDATION_STATUS"], "EXPOSURE": acc["HAS_THIS_PROJECT_BEEN_USED_TO_DEVELOP_THE_ENGINE"]})
    # 1b acceptance must refuse the development project by hash and alias
    dev = [p for p in C8.DEVELOPMENT_PROJECTS["P7757"]["PATHS"] if Path(p).exists()]
    acc_dev = SA.accept("CANDIDATE_X", dev[:1]) if dev else None
    steps.append({"STEP": "ACCEPTANCE_REFUSES_DEVELOPMENT_PROJECT", "OK": (acc_dev or {}).get("INDEPENDENT_VALIDATION_STATUS") == "REJECTED_NOT_INDEPENDENT" if dev else None,
                  "EXPOSURE": (acc_dev or {}).get("KNOWN_PRIOR_EXPOSURE"), "NOTE": None if dev else "development files absent from this checkout"})
    # 2-3 truth pack: validate, seal (into the dry-run sealed dir)
    pack = synthetic_truth_pack()
    v = TP.validate(pack)
    pack_path = out / "TRUTH_PACK_SYNTHETIC.json"; pack_path.write_text(json.dumps(pack, indent=1), "utf-8")
    sealed = out / "sealed"; sealed.mkdir()
    shutil.copyfile(pack_path, sealed / "TRUTH_PACK.json")
    seal = {"ARTIFACT": "PA08_TRUTH_SEAL", "PACK": str(sealed / "TRUTH_PACK.json"), "SHA256": BR._sha(sealed / "TRUTH_PACK.json"), "CASES": v["CASES"], "KINDS": v["KINDS"], "SEALED_BEFORE_BLIND_RUN": True, "DRY_RUN": True}
    (out / "PA08_TRUTH_SEAL.json").write_text(json.dumps(seal, indent=1), "utf-8")
    bad = dict(pack); bad["CASES"] = [dict(pack["CASES"][0], EXPECTED_PLASTER_AREA_M2=12.0)] + pack["CASES"][1:]
    steps.append({"STEP": "TRUTH_PACK_VALIDATE_AND_SEAL", "OK": v["VALID"] and not TP.validate(bad)["VALID"], "ERRORS": v["ERRORS"], "FORBIDDEN_KEY_REFUSED": not TP.validate(bad)["VALID"], "SHA256": seal["SHA256"]})
    # 4 blind run: the view id is learned from a first in-process run so the owner storey name can be declared (an owner input, not a truth)
    from engine.ingest import pipeline7 as P7
    from tests.test_pa06_pipeline import REG
    registry = dict(REG, _REGISTRY_ID="PA08_DRY_RUN_TEST_REGISTRY", DOOR_HEIGHT={"VALUE": 2.2, "SOURCE_TYPE": "OWNER_PROJECT_INPUT"}, DOOR_REVEAL_DEPTH={"VALUE": 0.15, "SOURCE_TYPE": "OWNER_PROJECT_INPUT"})
    cfg0 = BR.config_for(acc, registry, trades=("NORMAL_INTERNAL_PLASTER",), dry_run=True)
    pre = P7.run(cfg0)
    storeys = {vid: "GROUND_FLOOR" for vid in pre.storey_of_view}
    cfg = BR.config_for(acc, registry, trades=("NORMAL_INTERNAL_PLASTER",), dry_run=True, owner_storey_names=storeys)
    blind_dir = out / "blind"
    blind = BR.launch(cfg, [str(villa)], out_dir=blind_dir)
    (out / "PA08_BLIND_RESULT.json").write_text(json.dumps(blind, indent=1), "utf-8")
    steps.append({"STEP": "BLIND_RUN", "OK": blind["STATUS"] == "COMPLETED" and not blind["VIOLATIONS"], "STATUS": blind["STATUS"], "FILES_OPENED": blind["FILES_OPENED"], "STDERR_TAIL": blind["STDERR_TAIL"][-400:] if blind["STATUS"] != "COMPLETED" else None})
    # 4b deliberate leak: the sealed truth pack listed as a source -> VALIDATION_INVALID
    leak_cfg = dict(cfg, SOURCES=cfg["SOURCES"] + [{"PATH": str(sealed / "TRUTH_PACK.json"), "KIND": "PRIMITIVE_JSON", "FAMILY": "ARCHITECTURAL"}])
    leak = BR.launch(leak_cfg, [str(villa)], out_dir=out / "blind_leak_test")
    steps.append({"STEP": "LEAK_IS_CAUGHT", "OK": leak["STATUS"] == "VALIDATION_INVALID" and bool(leak["VIOLATIONS"]), "STATUS": leak["STATUS"], "VIOLATIONS": leak["VIOLATIONS"]})
    # 5-6 freeze then compare
    result = gate = None
    if blind["STATUS"] == "COMPLETED":
        freeze = blind["FREEZE"]
        truth = json.loads((sealed / "TRUTH_PACK.json").read_text("utf-8"))
        assert BR._sha(sealed / "TRUTH_PACK.json") == seal["SHA256"]
        result = CMP.compare(blind_dir, truth, freeze)
        result["STATUS"] = "DRY_RUN_EXECUTED_NOT_VALIDATION"
        (out / "PA08_INDEPENDENT_VALIDATION_RESULT_DRY_RUN.json").write_text(json.dumps(result, indent=1), "utf-8")
        steps.append({"STEP": "COMPARE", "OK": True, "CLASS_COUNTS": result["CLASS_COUNTS"], "METRICS": result["METRICS"], "CRITICAL_MISMATCHES": result["CRITICAL_MISMATCHES"]})
        regs = {n: json.loads((blind_dir / f"{n}.json").read_text("utf-8")) for n in ("PA07_QUANTITY_SAFETY_REGISTER", "PA07_PHYSICAL_SPACE_REGISTER", "PA06_SOURCE_UNIT_REGISTER") if (blind_dir / f"{n}.json").exists()}
        gate = G4.evaluate(review=None, validation=result, acceptance=acc, blind=blind, truth_seal=seal, leakage=None, blind_registers=regs, dry_run=True)
        (out / "PA08_PROJECT_3_GATE_V4_DRY_RUN.json").write_text(json.dumps(gate, indent=1), "utf-8")
        steps.append({"STEP": "GATE_V4", "OK": gate["READINESS"] == "NOT_READY", "READINESS": gate["READINESS"], "COUNTS": gate["COUNTS"]})
    rec = {"ARTIFACT": "PA08_RUNNER_READY_CHECK", "STATUS": "DRY_RUN_ON_SYNTHETIC_VILLA", "INDEPENDENT_VALIDATION": "NOT_EXECUTED (no independent source)", "COUNTS_AS_VALIDATION": False,
           "RUNNER_READY": all(s["OK"] for s in steps if s["OK"] is not None), "STEPS": steps, "OUTPUT_DIR": str(out),
           "WHAT_A_REAL_RUN_NEEDS": ["an ACCEPTED source package (pa08.source_acceptance)", "a hand-built truth pack sealed before the run", "python -m research.qs_wall_treatment_01.pa08.run ..."]}
    (Path(out_dir or C8.OUT8) / "PA08_RUNNER_READY_CHECK.json").write_text(json.dumps(rec, indent=1), "utf-8")
    return rec


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("RUNNER_READY", "STATUS")}, indent=1))
    for s in r["STEPS"]:
        print(s["STEP"], s["OK"], {k: v for k, v in s.items() if k not in ("STEP", "OK", "FILES_OPENED")})
