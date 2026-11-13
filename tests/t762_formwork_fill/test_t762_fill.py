"""T-762 formwork fill: synthetic villa (not Alsenan). Normal: face values carried once per line. Adverse: a host with a
measured line and a held line must not get the whole host ratio twice (the MAIN_FILL double count); an OQ-10 earth-cast
twin is never summed with its formed reading; a figure above the engine's CAP is pulled inside it; nothing stays blank."""
import importlib.util
import json
import pathlib

HERE = pathlib.Path(__file__).resolve()
SPEC = importlib.util.spec_from_file_location("fill_t762", HERE.parents[2] / "research/agents_t762/fill_t762.py")
F = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(F)

B1, B2, G1 = "L-" + "b1" * 10, "L-" + "b2" * 10, "L-" + "c1" * 10


def _line(lid, code, eid, cls, net=None, lo=None, hi=None, unit="m2"):
    return {"line_id": lid, "item_code": code, "element_id": eid, "class": cls, "measured_net": net,
            "held_low": lo, "held_high": hi, "unit": unit, "binding": None, "unbound_records": []}


def _face(fid, status, m2=None, lo=None, hi=None, alt="", method="G", kind="SIDE", item="x"):
    return {"face_id": fid, "status": status, "m2": m2, "lo": lo, "hi": hi, "held_from": None, "alternative": alt,
            "method": method, "face_kind": kind, "item": item, "basis_note": ""}


def _build(tmp):
    lines = [
        _line(B1, "STR.CONC.BEAM", "SYN:BEAM:1", "RELEASED", 1.0, unit="m3"),
        _line(B2, "STR.CONC.BEAM", "SYN:BEAM:2", "RELEASED", 2.0, unit="m3"),
        _line(G1, "STR.CONC.GROUND_BEAM", "SYN:GB:1", "RELEASED", 1.0, unit="m3"),
        _line("L-f01", "STR.FORMWORK", f"FW:{B1}:FACES:CALCULATED:-:G", "RELEASED", 8.0),   # complete host: 8 m2/m3
        _line("L-f02", "STR.FORMWORK", f"FW:{B2}:FACES:CALCULATED:-:G", "RELEASED", 10.0),
        _line("L-f03", "STR.FORMWORK", f"FW:{B2}:FACES:HELD:-:G", "HELD"),                     # one unvalued face
        _line("L-f04", "STR.FORMWORK", f"FW:{G1}:OQ10:E=G", "HELD"),
        _line("L-f05", "STR.FORMWORK", f"FW:{G1}:FACES:HELD:OQ10_EARTH_CAST:E=G", "HELD"),
        _line("L-f06", "STR.FORMWORK", f"FW:{G1}:FACES:HELD:OQ10_FORMED:E=G", "HELD"),
        _line("L-f07", "STR.FORMWORK", "FW:FACE:SYN-UNTIED-1", "HELD"),
    ]
    # a third complete beam host so the beam ratio has >= 2 complete hosts: B1 (8/1) + B3 (12/1) -> 10 m2/m3
    B3 = "L-" + "b3" * 10
    lines += [_line(B3, "STR.CONC.BEAM", "SYN:BEAM:3", "RELEASED", 1.0, unit="m3"),
              _line("L-f08", "STR.FORMWORK", f"FW:{B3}:FACES:CALCULATED:-:G", "RELEASED", 12.0)]
    ledger = {"lines": [
        {"line_id": B2, "faces": [_face("S-1", "CALCULATED", 10.0), _face("S-2", "HELD")]},
        {"line_id": G1, "faces": [_face("S-3", "ALTERNATIVE", 3.0, alt="OQ10_FORMED", method="E=G"),
                                  _face("S-4", "ALTERNATIVE", 0.0, alt="OQ10_EARTH_CAST", method="E=G"),
                                  _face("S-5", "HELD", lo=1.0, hi=2.0, alt="OQ10_FORMED", method="E=G"),
                                  _face("S-6", "HELD", alt="OQ10_EARTH_CAST", method="E=G")]}],
        "no_line": [{"face_id": "SYN-UNTIED-1", "status": "HELD", "m2": None, "lo": 4.0, "hi": 6.0, "held_from": None,
                     "element": "PARAPET", "item": "synthetic parapet face"}]}
    t761 = {"rows": []}
    mf = {"rows": [{"set": "FORMWORK_RATIO", "line_id": "L-f03", "after": {"class": "RELEASED", "net": 20.0}}]}
    t729 = {"entries": [{"line_id": "L-f07", "action": "CAP", "cap": "4.4", "rule": "SYN"}]}
    paths = {}
    for k, v in (("idx", {"candidate_version": "SYN", "lines": lines}), ("led", ledger), ("t761", t761), ("mf", mf),
                 ("t729", t729)):
        paths[k] = tmp / f"{k}.json"; paths[k].write_text(json.dumps(v))
    return paths


def test_normal_and_adverse(tmp_path):
    p = _build(tmp_path)
    out = F.main(str(p["idx"]), str(p["led"]), str(p["t761"]), str(p["mf"]), str(tmp_path / "out"), str(p["t729"]))
    rows = {r["line_id"]: r for r in out["rows"]}
    assert out["summary"]["still_blank"] == 0 and set(rows) == {"L-f03", "L-f04", "L-f05", "L-f06", "L-f07"}
    # ratio from complete hosts B1 + B3 only: 20 m2 / 2 m3 = 10 (B2 has a held line, so it is not complete)
    assert abs(out["ratios_m2_per_m3"]["STR.CONC.BEAM"]["ratio"] - 10.0) < 1e-9
    # adverse 1: B2 total = 2 m3 x 10 = 20; 10 already measured -> the held face takes the residual 10, not 20
    assert abs(rows["L-f03"]["after"]["net"] - 10.0) < 1e-9 and rows["L-f03"]["supersedes_main_fill"] == 20.0
    # adverse 2: OQ-10 formed reading once (3.0); the earth-cast twin carries 0, never added
    assert rows["L-f04"]["after"]["net"] == 3.0 and rows["L-f04"]["label"] == "DEFAULT"
    assert rows["L-f05"]["after"]["net"] == 0.0 and rows["L-f05"]["method"] == "OQ10_EARTH_CAST_NOT_ADOPTED"
    # normal: held formed face by its range midpoint
    assert abs(rows["L-f06"]["after"]["net"] - 1.5) < 1e-9 and rows["L-f06"]["label"] == "ESTIMATE"
    # adverse 3: untied face midpoint 5.0 exceeds the engine CAP 4.4 -> pulled to the midpoint of 0..cap
    assert abs(rows["L-f07"]["after"]["net"] - 2.2) < 1e-9 and "T729_BOUND" in rows["L-f07"]["method"]
    assert all(r["label"] in ("MEASURED", "DRAWING-READ", "DEFAULT", "ESTIMATE", "SAFETY") and r["basis"] for r in rows.values())
