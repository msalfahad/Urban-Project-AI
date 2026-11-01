"""T-400: the URBAN_V3035_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.35 (engine.source.arch_v3035), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build). Every figure is READ from those files; the
only typed text is the line binding (engine ids, checked against the candidate by the module: a stale binding stops),
the element ids of the new lines and the named causes:

  research/agents_t396/LEDGER_T396.csv     T-396 (MERGED e129577d, Verifier 2026-10-31T14:05Z Gate A PASS, own re-measure
      north 31.370 + street 5.600 m x 2.65 printed = 97.9705 m2 AGREE): run length, height, plane, block held terms;
  research/agents_t403/summary_t403.json   T-403 (MERGED a72a7282, Verifier 2026-10-31T17:58Z Gate A PASS, own
      re-measure upper G.B 3.5256 m3, masonry AT_LEAST 17.628 m2 AGREE): upper G.B gross, lower band split, pads,
      masonry below N.G.;
  research/agents_t404/FACES_T404.csv / ITEMS_T404.csv  T-404 (MERGED 698282e4, Verifier 2026-10-31T17:58Z Gate A
      PASS, own re-measure faces 83.1305 + 82.0705 m2 DC, layers HELD AGREE): faces per side, top, stop-end, coping,
      the facade-shared check;
  research/agents_t361/GATES_T361.csv      T-361 (MERGED e8d0bb06, Verifier 2026-10-30 15:37 UTC Gate A PASS): G-01
      opening 2.50 leaf HELD, G-02 = D-GF-15 counted once.

    python3 -I research/agents_t400/t400_inputs.py [project_id]      # prints the lines, restates and bindings
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

L396 = ROOT / "research/agents_t396/LEDGER_T396.csv"
X396 = ROOT / "research/agents_t396/CROSS_TRADE_T396.csv"
S403 = ROOT / "research/agents_t403/summary_t403.json"
F404 = ROOT / "research/agents_t404/FACES_T404.csv"
I404 = ROOT / "research/agents_t404/ITEMS_T404.csv"
G361 = ROOT / "research/agents_t361/GATES_T361.csv"
PINS = {L396: "c240852b69b4a74bad7203c0cbdc101866c8be8ba06f5a09c470d97e1d9af903",
        X396: "55f45dc44d5df87826d52167dc765a76a40ac8979af281c7172e64dd20785070",
        S403: "6e77a25705c2a2b89a6bebdd73d3990fb076f865ddd13028f9770863db656f2d",
        F404: "d90c95947f44639c37f12bf6d226fffa93ca679350204eae13ead69c9729586f",
        I404: "ba281937d2d719ab36f740c413a8eb18da66dade75c5c5c21edb0c8604695487",
        G361: "e9554a2e4fc18c8f67a4868e92880f5ba7e1948731d7beee36f34ba888303d29"}


def _rel(p):
    return str(p.relative_to(ROOT))


SOURCES = {
    "T-396": {"task": "T-396", "file": f"{_rel(L396)}; {_rel(X396)}", "sha256": f"{PINS[L396]}; {PINS[X396]}",
              "merge_commit": "e129577dc0ae9f43198ae271ba2da1ddc139716f",
              "checker_run": "Verifier 2026-10-31T14:05Z session_01E6cPnaMLNPxb5oviV8rveH (Gate A PASS; own re-measure "
                             "north 31.370 m, street 5.600 m, section '265' printed, plane 97.9705 m2 AGREE; 0 overlap "
                             "with facade / blockwork)"},
    "T-403": {"task": "T-403", "file": _rel(S403), "sha256": PINS[S403],
              "merge_commit": "a72a7282b96b6a5173e6160982b19fe7d49aba3a",
              "checker_run": "Verifier 2026-10-31T17:58Z (Gate A PASS; own re-measure upper G.B 0.20 x 0.40 x 44.07 = "
                             "3.5256 m3, lower band fence 44.07 / pool 3.50 / house 44.37 m, masonry AT_LEAST 17.628 m2 "
                             "AGREE)"},
    "T-404": {"task": "T-404", "file": f"{_rel(F404)}; {_rel(I404)}", "sha256": f"{PINS[F404]}; {PINS[I404]}",
              "merge_commit": "698282e49657dacc14a62f9181efe3ca4bcd21af",
              "checker_run": "Verifier 2026-10-31T17:58Z (Gate A PASS; own re-measure north 15.000 + 16.370 = 31.370, "
                             "plot 30.970, street 8.300, gate 2.500; p.12 no finish / coping / note: faces 83.1305 + "
                             "82.0705 m2 DC, layers HELD AGREE)"},
    "T-361": {"task": "T-361", "file": _rel(G361), "sha256": PINS[G361],
              "merge_commit": "e8d0bb063cba3bd50e1f5d400ce5a8bb151b45be",
              "checker_run": "Verifier 2026-10-30 15:37 UTC session_01E6cPndXCmif3NKt2V7FBr7 (Gate A PASS; G-02 = "
                             "D-GF-15 counted once, G-01 leaf HELD)"},
}

# the line binding (engine ids; the module checks each against the candidate: a stale binding stops)
UPPER_GB_LINE = "L-fb7a6431fede62e93fd5"
LOWER_BAND_LINE = "L-6290a9f3d93f38cd46d6"

RUN_IDS = {"F-NORTH (upper neighbour)": "F-NORTH", "F-STREET": "F-STREET", "F-SEA (Q-63 C element)": "F-SEA",
           "F-LOWER passage closure": "F-LOWER"}
HELD_RUN = {"F-SEA": "sea-side element HELD by the owner (Q-63 C: material, height, structure, gate); the 2.65 is "
                     "drawn, not printed",
            "F-LOWER": "passage closure: no top printed (partly under the GF roof +5.50; T-361 E-02 stop-end HELD)"}
LAYER_HOLD = ("no finish printed on p.12 (no render line, coping or note) and OWNER_NOTES_SIGMA item 3 unanswered; "
              "the house system is never carried by default (R-T404-5)")


def _read(p):
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != PINS[p]:
        raise SystemExit(f"{_rel(p)}: sha256 differs from the merged file (edited after the merge?)")
    return b.decode("utf-8")


def _csv(p):
    return list(csv.DictReader(io.StringIO(_read(p))))


def _f(x):
    return None if x in (None, "") else float(x)


def _line(action, code, eid, phys, cause, tasks, run=None, side=None, terms=None, value=None, held=None, beside=None,
          status=None, never_with=()):
    r = {"action": action, "item_code": code, "element_id": eid, "physical_element": phys, "run": run, "side": side,
         "cause": cause, "source_tasks": list(tasks), "never_with": list(never_with),
         "evidence_status": status or ("DRAWING-CONFIRMED" if action == "FENCE_VALUE" else "HELD")}
    if action == "FENCE_VALUE":
        r.update(terms=terms, value=value)
    else:
        r.update(held_reason=held, beside=beside)
    return r


def build(project_id=None):
    from engine.source import arch_v3035 as A
    led = _csv(L396)
    faces = _csv(F404)
    items = {r["item"]: r for r in _csv(I404)}
    s403 = json.loads(_read(S403))
    gates = {r["id"]: r for r in _csv(G361)}
    rows = []
    plane_total = 0.0
    for r in led:
        run = RUN_IDS[r["run"]]
        L, H = _f(r["solid_m"]), _f(r["height_m"])
        if r["plane_status"] == "DRAWING-CONFIRMED":
            v = _f(r["plane_m2"])
            plane_total += v
            rows.append(_line("FENCE_VALUE", A.WALL, f"FENCE:{run}:WALL_PLANE", "boundary fence wall plane above N.G.",
                              f"run {r['run_m']} m - gates {r['gates_m']} - corner owned elsewhere "
                              f"{r['corner_owned_elsewhere_m']} = solid {r['solid_m']} m; height {r['height_m']} m "
                              f"{r['height_basis']} (p.12 '265')", ["T-396"], run=run,
                              terms={"length_m": L, "height_m": H}, value=v))
            rows.append(_line("FENCE_HELD", A.BLOCK, f"FENCE:{run}:BLOCK_NET", "boundary fence blockwork net",
                              "plane less the boundary columns and the lower band if not block", ["T-396"], run=run,
                              held="block net not established: " + "; ".join(json.loads(r["block_held_terms"])),
                              beside={"kind": "AT_MOST", "value": _f(r["block_at_most_m2"]), "unit": "m2"},
                              never_with=[f"FENCE:{run}:WALL_PLANE"]))
        else:
            cmp_ = _f(r["plane_comparison_only_m2"])
            rows.append(_line("FENCE_HELD", A.WALL, f"FENCE:{run}:WALL_PLANE", "boundary fence wall plane above N.G.",
                              f"solid {r['solid_m']} m; height {r['height_basis']}", ["T-396"], run=run,
                              held=HELD_RUN[run], beside=({"kind": "COMPARISON_ONLY", "value": cmp_, "unit": "m2"}
                                                          if cmp_ else None)))
            rows.append(_line("FENCE_HELD", A.BLOCK, f"FENCE:{run}:BLOCK_NET", "boundary fence blockwork net",
                              "the run's plane is HELD", ["T-396"], run=run,
                              held=f"plane HELD ({HELD_RUN[run]}); block net with it"))
    rows.append(_line("FENCE_HELD", A.BLOCK_COUNT, "FENCE:ALL:BLOCKS", "boundary fence blocks (type and count)",
                      "Q-65 C fence material HELD (provisional alternatives comparison only)", ["T-396"],
                      held="block type HELD (Q-65 C): count by specification of the block, never an assumed size"))
    tot = s403["takeoff"]["totals"]
    band = s403["fence_band"]
    rows.append(_line("FENCE_HELD", A.BELOW_NG, "FENCE:BAND:MASONRY_BELOW_NG",
                      "boundary wall masonry below N.G. between the two ground beams",
                      f"band {band['axis_m']} m x h; h = formation - blinding 0.10 - lower G.B (0.40 | 0.60) - upper "
                      f"G.B 0.40 >= 0.40 m (ST p.9 note 1 excavation >= 1.50 m)", ["T-403"],
                      held="formation printed only as a minimum ('AS PER EXCAVATION DEPTH BELOW N.G.', ST p.14 A-A; "
                           "p.9 n.1): the height has no upper bound; net less the boundary columns (count M4); black "
                           "block on the neighbour runs (ST p.1 n.2), street / sea type HELD (Q-65 C)",
                      beside={"kind": "AT_LEAST", "value": tot["MASONRY_plane_at_least_m2"], "unit": "m2"}))
    pad = s403["takeoff"]["runs"][0]["PADS_m3"]
    rows.append(_line("FENCE_HELD", A.PAD, "FENCE:BAND:PADS", "boundary wall pad footings 1.30 x 0.80 x 0.30",
                      "ST p.14 A-A pad '(130x80x30)' beside each boundary column", ["T-403"],
                      held=f"pad count not printed ('SEE ARCH PLAN', none drawn: M4); per pad {pad['unit_gross']} m3 "
                           f"gross, of which {pad['unit_beam_share']} m3 is the lower beam's share (owner of the share "
                           f"open); blinding under the pads with the count",
                      beside={"kind": "PER_UNIT", "value": pad["unit_gross"], "unit": "m3 per pad"},
                      status="HELD"))
    faces_total = 0.0
    for f in faces:
        run, side = f["run"], f["side"]
        eid = f"FENCE:{run}:FACE:{side}"
        L, H = _f(f["length_m"]), _f(f["height_m"])
        if f["face_status"] == "DRAWING-CONFIRMED":
            v = _f(f["net_m2"])
            faces_total += v
            rows.append(_line("FENCE_VALUE", A.FACE, eid, f"boundary fence physical face, {side.lower()} side",
                              f"{side.lower()} face {f['length_m']} m (R-T404-1 corner convention) x {f['height_m']} m "
                              f"printed; of which lower 0.50 band {f['of_which_lower_050_band_m2']} m2", ["T-404"],
                              run=run, side=side, terms={"length_m": L, "height_m": H}, value=v))
        else:
            am, cmp_ = _f(f["at_most_m2"]), _f(f["comparison_only_m2"])
            rows.append(_line("FENCE_HELD", A.FACE, eid, f"boundary fence physical face, {side.lower()} side",
                              f"{side.lower()} face {f['length_m']} m; gate deduction {f['deductions'] or 'none'}",
                              ["T-404"], run=run, side=side, held=f["face_held"],
                              beside=({"kind": "AT_MOST", "value": am, "unit": "m2"} if am else
                                      {"kind": "COMPARISON_ONLY", "value": cmp_, "unit": "m2"} if cmp_ else None)))
        for code, st, amk, what in ((A.PLASTER, "plaster_status", "plaster_at_most_m2", "plaster / render"),
                                    (A.PAINT, "sigma_paint_status", "sigma_paint_at_most_m2", "paint / Sigma")):
            am = _f(f[amk])
            rows.append(_line("FENCE_HELD", code, f"{eid}:{code.rsplit('.', 1)[1]}",
                              f"boundary fence {what} layer, {side.lower()} side", f"layer on face {eid}", ["T-404"],
                              run=run, side=side,
                              held=(LAYER_HOLD if f["face_status"] == "DRAWING-CONFIRMED" or am else
                                    f"face HELD ({f['face_held']}); layer with it"),
                              beside=({"kind": "AT_MOST", "value": am, "unit": "m2"} if am else None),
                              never_with=[eid]))
    top_n = items["F-NORTH/TOP wall top (m.l / m2)"]
    rows.append(_line("FENCE_VALUE", A.TOP, "FENCE:F-NORTH:TOP", "boundary fence wall top 0.20 wide",
                      f"p.12 section: plain 0.20 top, no coping drawn ({top_n['value2']} m2 at 0.20); finish layer "
                      f"HELD with the faces", ["T-404"], run="F-NORTH", terms={"length_m": _f(top_n["value"])},
                      value=_f(top_n["value"])))
    top_s = items["F-STREET/TOP wall top (m.l / m2)"]
    rows.append(_line("FENCE_HELD", A.TOP, "FENCE:F-STREET:TOP", "boundary fence wall top 0.20 wide",
                      "street top follows the undimensioned dip and rounded end", ["T-404"], run="F-STREET",
                      held="street top profile drawn, not dimensioned (p.12 elevation: dip with X railing, rounded "
                           "end; R-T404-4)",
                      beside={"kind": "AT_LEAST", "value": _f(top_s["at_least"]), "unit": "m"}))
    end = items["F-STREET/END-G-01 stop-end face at the gate jamb"]
    rows.append(_line("FENCE_HELD", A.FACE, "FENCE:F-STREET:FACE:END-G-01", "boundary fence stop-end face at the "
                      "G-01 jamb", "t 0.20 x 2.65 = 0.53 at most", ["T-404", "T-361"], run="F-STREET", side="END",
                      held="end top drawn rounded and lower (p.12 elevation), undimensioned",
                      beside={"kind": "AT_MOST", "value": _f(end["at_most"]), "unit": "m2"}))
    g1 = gates["G-01"]
    rows.append(_line("FENCE_HELD", A.GATE, "FENCE:G-01:LEAF", "street gate G-01 leaf (opening in the street fence)",
                      f"opening {g1['opening_width_m']} m DRAWING-CONFIRMED (HIDDEN gap = p.12 '250'); not in the "
                      f"opening census", ["T-361"], run="F-STREET",
                      held=f"no leaf drawn: {g1['held_text']}",
                      beside={"kind": "OPENING_WIDTH", "value": _f(g1["opening_width_m"]), "unit": "m"}))
    g2 = gates["G-02"]
    rows.append(_line("FENCE_HELD", A.GATE, "FENCE:G-02:LEAF", "sea-side gate G-02 (= opening D-GF-15, counted once)",
                      f"{g2['gates_pcs']} gate, {g2['leaves_pcs']} leaf, {g2['opening_width_m']} m jamb to jamb "
                      f"DRAWING-CONFIRMED (D120 block; elevations draw leaf {g2['leaf_size_m']} m, not printed); in no "
                      f"door count line of the opening census ({g2['census'][:120]})", ["T-361"], run="F-SEA",
                      held=f"Q-63 C sea-side element: {g2['held_text']}",
                      beside={"kind": "OPENING_WIDTH", "value": _f(g2["opening_width_m"]), "unit": "m"}))
    ub = s403["takeoff"]["totals"]["UPPER_GB_at_most_m3"]
    restates = [{"action": "HELD_BOUND", "line_id": UPPER_GB_LINE,
                 "expect": {"item_code": "STR.CONC.GROUND_BEAM", "evidence_state": "BLOCKED_RFI",
                            "measured_net": None},
                 "gross_terms": {"length_m": band["upper_gb_len_by_area_m"], "width_m": 0.20, "depth_m": 0.40},
                 "low": 0.0, "high": ub,
                 "cause": "upper boundary G.B 20 x 40 (ST p.14 plan + A-A, top at N.G.) on the 44.07 m band: gross "
                          "DRAWING-CONFIRMED; each boundary column takes its joint 0.20 x 0.30 x 0.40 = 0.024 m3 "
                          "(T-394), count not printed (M4): net HELD, never one end",
                 "source_tasks": ["T-403"]}]
    sp = s403["lower_band_split_L6290a9f3"]["by_class"]
    bindings = [{"action": "BIND", "line_id": LOWER_BAND_LINE,
                 "expect": dict(LOWER_BAND_EXPECT),
                 "what": "lower boundary band (whole 91.94 m): the fence share is inside this one line",
                 "share": {k: [v["solid_low_m3"], v["solid_high_m3"]] for k, v in sorted(sp.items())},
                 "cause": "one physical band, one line; the line carries the Checker line-content downgrade of the "
                          "T-356 band (verdicts/V3.0.29/DOWNGRADES.json): its split by owner class needs the "
                          "downgrade re-issued on the split lines (Checker), never a second fence line",
                 "evidence_status": "HELD", "source_tasks": ["T-403"]}]
    bindings += EXTRA_BINDINGS
    x = items["faces shared with the house facade ledger"]
    records = [{"item": "FENCE:ALL:COPING", "status": "NOT_DRAWN", "unit": "lm",
                "cause": items["coping on the fence top"]["evidence"], "source_tasks": ["T-404"]},
               {"item": "FENCE:G-01:FAR_JAMB", "status": "OTHER_OWNER", "unit": "m2",
                "cause": items["G-01 far jamb (house wall)"]["evidence"], "source_tasks": ["T-404"]},
               {"item": "FENCE:BAND:GB_COATING_BELOW_NG", "status": "OTHER_OWNER", "unit": "m2",
                "cause": items["coating below N.G.: boundary G.B faces"]["evidence"], "source_tasks": ["T-404"]},
               {"item": "FENCE:BAND:MASONRY_COATING_BELOW_NG", "status": "NOT_DRAWN", "unit": "m2",
                "cause": items["coating below N.G.: boundary masonry faces (44.07 m band, both faces)"]["evidence"],
                "source_tasks": ["T-404"]}]
    return {"schema": A.INPUTS_SCHEMA, "project_id": project_id, "sources": [SOURCES[t] for t in sorted(SOURCES)],
            "lines": rows, "restates": restates, "bindings": bindings, "records": records,
            "checks": {"plane_total_m2": round(plane_total, 6), "faces_dc_total_m2": round(faces_total, 6),
                       "facade_shared_m2": _f(x["value"]),
                       "gate_ids": {"G-01": "FENCE_GATE_LINE", "G-02": "FENCE_GATE_LINE"},
                       "gate_alias": {"G-02": "D-GF-15"}}}


LOWER_BAND_EXPECT = {"item_code": "STR.CONC.BOUNDARY_WALL", "evidence_state": "SOURCE_DERIVED", "measured_net": 7.2204,
                     "element_id": "P-C:SCOPE:BOUNDARY_WALL:FOUNDATION:CC-9fd936ab60:BEAM"}
EXTRA_BINDINGS = [
    {"action": "BIND", "line_id": "L-78babf2c6da600cb800e",
     "expect": {"item_code": "MET.RAILING.GUARD", "evidence_state": "BLOCKED_RFI", "measured_net": None,
                "element_id": "RAIL:RL-10"},
     "what": "street fence dip X railing RL-10 (the profile cut of F-STREET): its own held railing line, never block",
     "cause": "T-396 CROSS_TRADE: the X railing fills the street dip, carried by the railing line (V3.0.30 HELD)",
     "evidence_status": "HELD", "source_tasks": ["T-396"]},
    {"action": "BIND", "line_id": "L-56acf34557c315f65bb1",
     "expect": {"item_code": "ARCH.THRESHOLD", "evidence_state": "BLOCKED_RFI", "measured_net": None,
                "element_id": "GF-THRESHOLD-D-GF-15:threshold strip:HELD"},
     "what": "the threshold strip of D-GF-15 = G-02: its own held strip line (V3.0.29), not a gate count",
     "cause": "T-361: G-02 = D-GF-15, the same element; the strip is a floor item of the doorway, the leaf is the gate",
     "evidence_status": "HELD", "source_tasks": ["T-361"]},
]

if __name__ == "__main__":
    d = build(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps({k: d[k] for k in ("restates", "bindings", "records", "checks")}, indent=1, ensure_ascii=False))
    for r in d["lines"]:
        print(r["action"], r["item_code"], r["element_id"], r.get("value"), (r.get("beside") or {}).get("value"))
