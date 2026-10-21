"""Phase A2 generic ENTITY_ROLE_INFERENCE on a synthetic two-room plan whose layers have meaningless names: walls,
door, window, columns, overhead, furniture, annotation, stairs, plot boundary and sheet frame must be told apart by
evidence only, false positives must be refused, claims must stay source-scoped, and the frozen topology must certify
the rooms only through the claims and the inferred doors (no layer map, no names)."""

from __future__ import annotations

import math
import random

import pytest

from engine.source import canonical_input as CI, entity_role_inference as ERI, geometry_role as GR
from engine.source import role_authority as RA, room_topology as RT, text_role as TX, topology_closures as TC

REV = CI.SourceRevision("SYN_A2", CI.EXACT_SOURCE, "b" * 64, None, "TEST")
LT = {"CONT": [], "DASHED": [12.0, -6.0], "AXIS": [30.0, -6.0, 6.0, -6.0]}
LAYER_LT = {"7": "CONT", "Q": "CONT", "8": "DASHED", "6": "AXIS"}
_h = [1000]


def _key():
    _h[0] += 1
    return str(_h[0])


def seg(x1, y1, x2, y2, layer, path=(), etype="LINE", name=None):
    h = _key()
    steps = tuple(CI.LineageStep(p, "B" + p, name or "BLK" + p) for p in path)
    return CI.CanonicalPart(CI.SourceIdentity(REV.revision_id, h, tuple(path), "SEGMENT", 0), "SEGMENT",
                            (float(x1), float(y1), float(x2), float(y2)), layer, CI.VISIBLE, steps, "T:" + h, etype)


def arc(cx, cy, r, a0, a1, layer, path=(), name=None):
    h = _key()
    steps = tuple(CI.LineageStep(p, "B" + p, name or "BLK" + p) for p in path)
    return CI.CanonicalPart(CI.SourceIdentity(REV.revision_id, h, tuple(path), "ARC", 0), "ARC",
                            (float(cx), float(cy), float(r), a0, a1), layer, CI.VISIBLE, steps, "T:" + h, "ARC")


def circle(cx, cy, r, layer, path=()):
    h = _key()
    steps = tuple(CI.LineageStep(p, "B" + p, "BLK" + p) for p in path)
    return CI.CanonicalPart(CI.SourceIdentity(REV.revision_id, h, tuple(path), "CIRCLE", 0), "CIRCLE",
                            (float(cx), float(cy), float(r)), layer, CI.VISIBLE, steps, "T:" + h, "CIRCLE")


def text(v, x, y, path=(), layer="0"):
    h = _key()
    steps = tuple(CI.LineageStep(p, "B" + p, "TAG") for p in path)
    return CI.PlacedText(CI.SourceIdentity(REV.revision_id, h, tuple(path), "TEXT", 0), v, float(x), float(y), 200.0,
                         layer, CI.VISIBLE, steps, "TEXT")


def poly(pts, layer, closed=True, etype="LWPOLYLINE", path=()):
    n = len(pts)
    return [seg(*pts[i], *pts[(i + 1) % n], layer, path=path, etype=etype) for i in range(n if closed else n - 1)]


def plan(wall="7", window="Q", door_layer="D9", with_door=True, rename=None):
    """Two 4.8 x 4.6 m rooms, 200 mm double-line walls, a 900 mm door in the partition, a 1500 mm window in the
    bottom wall, two columns, overhead lines, a furniture symbol, a north-arrow callout, a stair, a service line
    crossing a wall, a floor drain, a plot boundary and a sheet frame. mm units."""
    L = (lambda n: rename.get(n, n)) if rename else (lambda n: n)
    w = L(wall)
    P = []
    # outer faces (bottom face broken by the window gap 2000..3500)
    P += [seg(0, 0, 2000, 0, w), seg(3500, 0, 10000, 0, w), seg(10000, 0, 10000, 5000, w),
          seg(10000, 5000, 0, 5000, w), seg(0, 5000, 0, 0, w)]
    # inner faces
    P += [seg(200, 200, 2000, 200, w), seg(3500, 200, 5000, 200, w), seg(5200, 200, 9800, 200, w),
          seg(9800, 200, 9800, 4800, w), seg(9800, 4800, 5200, 4800, w), seg(5000, 4800, 200, 4800, w),
          seg(200, 4800, 200, 200, w)]
    # window jambs + partition with a door gap 1000..1900 and its jambs
    P += [seg(2000, 0, 2000, 200, w), seg(3500, 0, 3500, 200, w),
          seg(5000, 200, 5000, 1000, w), seg(5000, 1900, 5000, 4800, w),
          seg(5200, 200, 5200, 1000, w), seg(5200, 1900, 5200, 4800, w),
          seg(5000, 1000, 5200, 1000, w), seg(5000, 1900, 5200, 1900, w)]
    # window in the gap: two glazing lines 100 mm apart (they look like a thin wall pair) spanning jamb to jamb
    P += [seg(2000, 50, 3500, 50, L(window)), seg(2000, 150, 3500, 150, L(window))]
    # door symbol occurrence: swing r 900 hinged on the jamb corner, open leaf along +x
    if with_door:
        P += [arc(5200, 1000, 900, 0.0, math.pi / 2, L(door_layer), path=("D1",), name="X1"),
              seg(5200, 1000, 6100, 1000, L(door_layer), path=("D1",), name="X1")]
    # columns: two filled 300 x 300 outlines against the inner face
    P += poly([(200, 2200), (500, 2200), (500, 2500), (200, 2500)], L("C"))
    P += poly([(9500, 2200), (9800, 2200), (9800, 2500), (9500, 2500)], L("C"))
    # overhead (dashed) beam lines inside the rooms
    P += [seg(1000, 3000, 4000, 3000, L("8")), seg(6000, 1500, 9000, 1500, L("8"))]
    # furniture symbol occurrence (no text): a round table
    P += [circle(2500, 2500, 400, L("9"), path=("F1",))] + poly([(2000, 2000), (3000, 2000), (3000, 3000),
                                                                (2000, 3000)], L("9"), path=("F1",))
    # north-arrow callout occurrence (lines + text), outside the building
    P += [seg(11500, 7000, 11500, 7600, L("5"), path=("N1",)), seg(11400, 7400, 11500, 7600, L("5"), path=("N1",))]
    # stair: 6 treads, going 300, width 1200, inside room 2
    P += [seg(6000, 2500 + 300 * i, 7200, 2500 + 300 * i, L("5")) for i in range(6)]
    # a service line crossing the bottom wall (both faces) and an isolated floor drain
    P += [seg(7000, -600, 7000, 600, L("5"))]
    P += [circle(8500, 4000, 150, L("5"))]
    # plot boundary on four sides, and a sheet frame enclosing everything
    P += poly([(-1500, -1500), (11500, -1500), (11500, 6500), (-1500, 6500)], L("5"))
    P += poly([(-3000, -3000), (13000, -3000), (13000, 8500), (-3000, 8500)], w)
    T = [text("BEDROOM", 2600, 3800, path=("T1",)), text("KITCHEN", 7600, 1200, path=("T2",)),
         text("N", 11500, 7700, path=("N1",))]
    fills = [(L("C"), (200, 2200, 500, 2500)), (L("C"), (9500, 2200, 9800, 2500))]
    inp = CI.CanonicalMeasurementInput(REV, "R1", "MF:R1", 1.0, "UNIT", tuple(P), tuple(T), (), {}, {})
    lay_lt = {L(k): v for k, v in LAYER_LT.items()}
    return inp, fills, lay_lt


def run(**kw):
    inp, fills, lay_lt = plan(**kw)
    return inp, ERI.infer(inp, linetypes=LT, layer_linetype=lay_lt, fills=fills)


def roles_by_layer(inp, r):
    out = {}
    for p in inp.parts:
        out.setdefault(CI.effective_layer(p)[0], set()).add(r["part_roles"].get(p.identity.key))
    return out


# ------------------------------------------------------------------ linetype from the definition, not the name
def test_linetype_class_reads_the_pattern():
    assert ERI.linetype_class([]) == ERI.CONTINUOUS
    assert ERI.linetype_class([12.0, -6.0]) == ERI.UNIFORM_DASH
    assert ERI.linetype_class([30.0, -6.0, 6.0, -6.0]) == ERI.DASH_DOT
    assert ERI.linetype_class([0.0, -3.0, 12.0, -3.0]) == ERI.DASH_DOT
    assert ERI.linetype_class(None) == ERI.LT_UNKNOWN


# ------------------------------------------------------------------ positive roles from evidence
def test_numeric_wall_layer_accepted_from_pairs_joins_and_door_hinges():
    inp, r = run()
    d = r["decisions"]["7"]
    assert d["state"] == "ACCEPTED" and d["role"] == ERI.WALL_FACE
    assert {"GEOMETRY_PAIRS", "GEOMETRY_JOINS", "CONTEXT_DOOR_HINGES"} <= set(d["channels"])
    assert r["observations"]["7"]["pair_offset_median_mm"] == 200.0


def test_layer_names_carry_no_authority():
    """Renaming every layer (to names the lexicon would read as WINDOW / WALL / DOOR) changes no decision."""
    _, a = run()
    _, b = run(rename={"7": "WINDOW", "Q": "WALL", "D9": "FURN", "C": "TEXT", "8": "GLASS", "9": "COLUMN", "5": "DOOR"})
    m = {"7": "WINDOW", "Q": "WALL", "D9": "FURN", "C": "TEXT", "8": "GLASS", "9": "COLUMN", "5": "DOOR"}
    for lay, d in a["decisions"].items():
        assert b["decisions"][m.get(lay, lay)]["state"] == d["state"]
        assert b["decisions"][m.get(lay, lay)].get("role") == d.get("role")
    assert sorted(a["part_roles"].values()) == sorted(b["part_roles"].values())


def test_door_motif_found_without_door_layer_or_block_name():
    _, r = run()
    assert list(r["inferred_doors"]) == ["ID1"]
    sig = r["inferred_doors"]["ID1"]
    assert abs(sig["radius"] - 900) < 1e-9 and sig["inferred"] == ERI.POLICY_ID


def test_window_lines_paired_like_a_thin_wall_are_glazing_not_wall():
    _, r = run()
    assert r["glazing_share"]["Q"] >= 0.5
    assert r["decisions"]["Q"]["state"] == "PART_LEVEL"
    assert len(r["glazing"]["parts"]) == 2 and r["glazing"]["windows"][0]["width_mm"] == 1500.0


def test_columns_from_filled_rectangles():
    _, r = run()
    assert r["decisions"]["C"]["role"] == ERI.COLUMN and len(r["columns"]["C"]) == 2


# ------------------------------------------------------------------ negative roles
def test_sheet_frame_rejected_and_never_wall_evidence():
    inp, r = run()
    fk = set(r["frames"]["frames"][0]["parts"])
    assert len(fk) == 4 and all(r["part_roles"][k] == ERI.SHEET_FRAME for k in fk)


def test_plot_boundary_rejected():
    inp, r = run()
    pk = set(r["plot_boundary"]["parts"])
    assert len(pk) == 4 and r["plot_boundary"]["sides"] == ["E", "N", "S", "W"]
    assert all(r["part_roles"][k] == ERI.PLOT_BOUNDARY for k in pk)


def test_overhead_and_axis_from_linetype_pattern():
    _, r = run()
    assert r["decisions"]["8"]["role"] == ERI.OVERHEAD


def test_furniture_and_annotation_occurrences():
    _, r = run()
    assert r["occurrences"]["IF1"]["role"] == ERI.SYMBOL
    assert r["occurrences"]["IN1"]["role"] == ERI.ANNOTATION


def test_treads_wall_crossing_line_and_isolated_drain():
    inp, r = run()
    runs = r["treads"]["runs"]
    assert len(runs) == 1 and runs[0]["tread_lines"] == 6 and runs[0]["going_mm"] == 300.0
    by = {p.identity.key: p for p in inp.parts}
    cross = [k for k, v in r["residual"]["parts"].items() if v == ERI.ANNOTATION]
    drain = [k for k, v in r["residual"]["parts"].items() if v == ERI.SYMBOL]
    assert len(cross) == 1 and by[cross[0]].geometry[0] == 7000.0
    assert len(drain) == 1 and by[drain[0]].kind == "CIRCLE"


# ------------------------------------------------------------------ false positives refused
def test_single_line_layer_is_not_a_wall():
    inp, r = run(wall="7")
    # the mixed layer "5" (treads, plot, service line) never becomes a wall
    assert r["decisions"].get("5", {}).get("role") != ERI.WALL_FACE


def test_door_false_positives_rejected():
    inp, fills, lay = plan(with_door=False)
    extra = [arc(5200, 1000, 900, 0.0, math.pi / 2, "D9", path=("D2",)),                  # swing, no leaf
             arc(7500, 3000, 900, 0.0, math.pi / 2, "D9", path=("D3",)),                  # floating, not on a wall
             seg(7500, 3000, 8400, 3000, "D9", path=("D3",)),
             arc(5200, 1000, 3000, 0.0, math.pi / 2, "D9", path=("D4",)),                 # 3 m radius: not a door
             seg(5200, 1000, 8200, 1000, "D9", path=("D4",))]
    inp = CI.CanonicalMeasurementInput(REV, "R1", "MF:R1", 1.0, "UNIT", inp.parts + tuple(extra), inp.texts, (), {}, {})
    r = ERI.infer(inp, linetypes=LT, layer_linetype=lay, fills=fills)
    assert r["inferred_doors"] == {}
    why = sorted(x["why"] for x in r["doors"]["rejected"])
    assert why == ["HINGE_NOT_ANCHORED_ON_A_WALL_FACE_CANDIDATE", "NO_LEAF_FROM_HINGE"]


# ------------------------------------------------------------------ claims: scope, state, authority
def test_claims_are_policy_accepted_scoped_and_explicit():
    inp, r = run()
    assert r["claims"]
    for c in r["claims"]:
        assert c.review_state == RA.POLICY_ACCEPTED and c.authority == RA.INFERENCE_AUTHORITY
        assert c.scope == "R1" and c.part_keys and c.evidence
        assert RA.claim_applies(c, inp.revision, "R1")[0]
        assert not RA.claim_applies(c, inp.revision, "R2")[0]
        other = CI.SourceRevision("OTHER", CI.EXACT_SOURCE, "c" * 64, None, "TEST")
        assert not RA.claim_applies(c, other, "R1")[0]


def test_policy_accepted_needs_the_inference_authority_and_evidence():
    base = dict(claim_id="X", source_revision_id=REV.revision_id, source_anchor_sha256=REV.anchor_sha256,
                layer="7", layer_basis="EFFECTIVE", role=GR.TOPOLOGY_BOUNDARY)
    ok = RA.SourceLayerRoleClaim(evidence=("e",), authority=RA.INFERENCE_AUTHORITY, review_state=RA.POLICY_ACCEPTED, **base)
    assert RA.claim_applies(ok, REV)[0]
    for bad in (RA.SourceLayerRoleClaim(evidence=("e",), authority="SOMEONE", review_state=RA.POLICY_ACCEPTED, **base),
                RA.SourceLayerRoleClaim(evidence=(), authority=RA.INFERENCE_AUTHORITY,
                                        review_state=RA.POLICY_ACCEPTED, **base),
                RA.SourceLayerRoleClaim(evidence=("e",), authority=RA.INFERENCE_AUTHORITY,
                                        review_state=RA.SOURCE_EVIDENCE_CANDIDATE, **base)):
        assert not RA.claim_applies(bad, REV)[0]


def test_text_roles_ignore_inference_part_claims():
    inp, r = run()
    tr = TX.classify(inp, claims=r["claims"])
    labels = [t for t in inp.texts if t.value in ("BEDROOM", "KITCHEN")]
    assert all(tr[t.identity.key].role == TX.ROOM_LABEL_ESTABLISHED for t in labels)


def test_corroboration_adds_a_channel_never_a_candidate():
    inp, fills, lay = plan()
    r = ERI.infer(inp, linetypes=LT, layer_linetype=lay, fills=fills,
                  corroboration={"7": {ERI.WALL_FACE: ["R0"]}, "9": {ERI.WALL_FACE: ["R0"]}})
    assert r["decisions"]["7"]["channels"]["CONTEXT_SAME_SOURCE"] == 1
    assert r["decisions"]["9"]["state"] != "ACCEPTED"           # no wall candidate there: nothing to corroborate
    co = ERI.corroboration_from({"A": r, "B": r})
    assert co["A"]["7"][ERI.WALL_FACE] == ["B"]


def test_inference_is_deterministic_and_order_free():
    inp, fills, lay = plan()
    a = ERI.infer(inp, linetypes=LT, layer_linetype=lay, fills=fills)
    parts = list(inp.parts)
    random.Random(7).shuffle(parts)
    inp2 = CI.CanonicalMeasurementInput(REV, "R1", "MF:R1", 1.0, "UNIT", tuple(parts), inp.texts, (), {}, {})
    b = ERI.infer(inp2, linetypes=LT, layer_linetype=lay, fills=fills)
    assert [ERI.claim_record(c) for c in a["claims"]] == [ERI.claim_record(c) for c in b["claims"]]
    assert a["part_roles"] == b["part_roles"]


# ------------------------------------------------------------------ through the frozen topology
def _topo(inp, r, doors=True):
    return RT.run(inp, frame_insert=None, expected_revision_id=REV.revision_id, selected_region_id="R1",
                  unrealised=[], closure_policy=TC.POLICY_ID, claims=r["claims"],
                  inferred_doors=r["inferred_doors"] if doors else None)


def _labelled(res):
    return [s for s in res["sites"] if s["labels"]]


def test_rooms_certify_only_through_claims_and_inferred_doors():
    inp, r = run()
    res = _topo(inp, r)
    lab = _labelled(res)
    assert len(lab) == 2 and all(s["status"] == "CERTIFIED" for s in lab), [(s["issues"], s["area_m2"]) for s in lab]
    assert res["roles"]["inferred_doors"] == {"ID1": "ADMITTED"}
    assert {v["state"] for v in res["openings"].values()} == {"CLOSED"}
    # without the inferred door the partition opening stays open: the two labels share one site
    res2 = _topo(inp, r, doors=False)
    assert any(len(s["labels"]) == 2 for s in res2["sites"]) or not all(s["status"] == "CERTIFIED"
                                                                       for s in _labelled(res2))
    # without any claim nothing is admitted: no labelled site certifies
    res3 = RT.run(inp, frame_insert=None, expected_revision_id=REV.revision_id, selected_region_id="R1",
                  unrealised=[], closure_policy=TC.POLICY_ID)
    assert not any(s["status"] == "CERTIFIED" and s["labels"] for s in (res3.get("sites") or []))


def test_default_path_unchanged_without_inferred_doors():
    """inferred_doors=None leaves the door set exactly what geometry_role found (the Qortuba path)."""
    inp, r = run()
    items, probes, labels, adm, closures, status, dp = RT.topology_inputs(inp, frame_insert=None, eps_n=0.01,
                                                                          eps_r=1.0, claims=r["claims"])
    assert "inferred_doors" not in adm and adm["doors"] == GR.admit(inp, frame_insert=None, eps=0.01)["doors"]


def test_policy_record_is_digested_and_names_no_project():
    rec = ERI.policy_record()
    assert len(rec["digest"]) == 64
    blob = repr(rec).upper()
    for word in ("P7757", "ALSENAN", "QORTUBA", "ST7757"):
        assert word not in blob
