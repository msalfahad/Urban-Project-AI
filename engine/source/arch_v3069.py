"""ARCH_TAKEOFF_V3.0.69 (T-687, lane I, PLASTER / PAINT GATE B ROUND 1 integration package): the SAME opt-in BOQ
candidate as ARCH_TAKEOFF_V3.0 .. V3.0.68 (engine.source.arch_v30, arch_v301 .. arch_v3068), extended with THREE pieces
built from the Checker-merged plaster / paint research (T-676, T-680, T-686, T-690 R-T690-1); no line outside FIN.PLASTER
/ FIN.PAINT moves:

  FIN_RESTATE   a named HELD FIN.PLASTER / FIN.PAINT line is restated as the merged ledger states it:
                  BOUND   low .. high (both ends drawn-derived, the open datums named in the line): the stair-shaft
                          ST-01 storey bands GF / 1F / 2F (T-680 R-T680-1 / -2: W25 / W27 heads, pier returns by band),
                          the annex wet-room tile-backing render and dry-room paint on the bounded annex slab top
                          (T-686 R-T686-1), the stair-core wet rooms (T-686 R-T686-3);
                  VALUE   a bounded line that closes to one figure on an owner-approved fallback: PROVISIONAL, status
                          ASSUMED - OWNER-APPROVED with its source, the figure inside the old bound (T-676 OP-009 reveal,
                          Q-55 C door height);
                  CAUSE   a HELD blank line whose stated cause the drawing contradicts: the cause text is corrected,
                          the line stays HELD blank (T-676 A-1F-01: drawn 1.00 x 0.15 on the 1F plan; spring / rise
                          printed nowhere, D-45);
  WET_BAND      one NEW FIN.PLASTER component line per wet room, '<engine room>:plaster band above ceiling' (T-690
                R-T690-1): the wall face from the tile top H (= finished ceiling, Q-48 A) to the plaster top S (the
                structural soffit, owner 2026-11-02 / Q-72), the band no line carried; bound by id to the room's
                tile-backing FIN.PLASTER line (never added into it: a different coat by a different trade); the band
                figure is recomputed here from the merged terms (face length, H, S, roof share, beam-end deductions)
                and asserted equal to the ledger; a point band is PROVISIONAL (ASSUMED - OWNER-APPROVED H on a
                DRAWING-CONFIRMED soffit), every other band HELD BOUNDED with its datum named; where the backing line
                and the band hang on one datum, the joint room total (R-T690-1 (d)) is carried BESIDE in the band line,
                never the sum of the two separate extremes.

R-T687-1 (every villa): (a) a finish line is restated only from a Checker-merged ledger that names it by id, with the
candidate figure the ledger started from asserted equal to the line; (b) a HELD line stays HELD unless one figure is
established, and then it is PROVISIONAL with the weakest evidence status of its terms (ASSUMED - OWNER-APPROVED, the
owner source named), never VERIFIED; a value closing a bound lies inside it; (c) a corrected cause never makes a
quantity: a CAUSE restatement keeps the line blank; (d) each wall layer has its own top: tile and its backing to the
finished ceiling, plaster to the structural soffit; the band between them is its own line bound to the backing line by
id, one per room, never inside the backing line, never on a room the census did not prove in no line; (e) blank stays
blank (never 0), a bound is reported low with low and high with high; (f) only FIN.PLASTER / FIN.PAINT code totals move,
each exactly by the changes; every other line byte-identical; the V3.0.67 concrete / lintel checks and the V3.0.68
masonry check re-run on the result; (g) coat materials (Q-79 1:4 / 1:4 / spatter 1:2) are applied only on material
lines: the candidate holds no plaster material line (T-676 / T-364 MISSING), so none is opened here.
Files: V3_0_69_BOQ_LINES.json / .csv, V3_0_69_INTEGRATION_LEDGER.json / .csv, V3_0_69_DIFF.csv, V3_0_69_RUN.json.
Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3043 as A3043
from engine.source import arch_v3058 as A3058
from engine.source import arch_v3063 as A3063
from engine.source import arch_v3067 as A3067
from engine.source import arch_v3068 as A3068

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: books Checker-merged finish ledgers onto candidate lines
METHOD = "ARCH_TAKEOFF_V3.0.69"
EXTENDS = A3068.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T687_ARCH_V3_0_69"
INPUTS_SCHEMA = "URBAN_V3069_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3069_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3063.InputsError
_r = A3063._r
_fmt = A3063._fmt
line_class = A3063.line_class
RULE_ID, RULE_VERSION = "R-T687-1", "T-687"
REC_KEY = "finish_gate_b_v3069"
PLASTER, PAINT = "FIN.PLASTER", "FIN.PAINT"
CODES = (PLASTER, PAINT)
UNIT = "m2"
BOUNDED, BLANK, PROV = A3063.BOUNDED, A3063.BLANK, "PROVISIONAL"
OA = "ASSUMED - OWNER-APPROVED"
STATUSES = ("DRAWING-CONFIRMED", OA, "HELD", "UNKNOWN")      # WORKFLOW_CONTROLS s.5 (never VERIFIED here)
ACTIONS = ("BOUND", "VALUE", "CAUSE")
BAND_SUFFIX = ":plaster band above ceiling"
P_FIN, P_BAND = "FIN_RESTATE", "WET_BAND"
TOL = 1e-6
TOT_TOL = 5e-6

PIECES = {
    P_FIN: {"module": "engine/source/arch_v3069.py (named HELD FIN.PLASTER / FIN.PAINT lines restated from the "
                      "Checker-merged T-676 / T-680 / T-686 ledgers: stair-shaft storey bands, annex and stair-core "
                      "wet-room backing render, annex dry-room paint, one door reveal closed on Q-55 C, one cause "
                      "corrected; nothing else moves)",
            "policy": "FINISH_GATE_B_V1", "rule_id": "R-T676-2 / R-T680-1..2 / R-T686-1..3 (R-T687-1)",
            "owner_rules": ["Q-72 (plaster to the structural slab underside; stair shafts at full exposed height)",
                            "Q-48 A / Q-43 A (paint and tile top = finished ceiling, owner G1)",
                            "Q-55 C (door-height fallback 2.20 m where no head is printed)",
                            "Q-54 B (annex +4.30 datum held: bounds only, no point)",
                            "Q-73 (full deduction of every actual opening)",
                            "UP-QTY-STATUS-001 (held is blank or bounded, never 0)",
                            "ERS s.2-5 (drawn element first; one physical element once)"],
            "owner_manual_method": "wall face length x height (plaster to the slab underside, paint to the finished "
                                   "ceiling) - openings; the freelancer's flat 3.60 m paint height and half-deducted "
                                   "openings are not the owner rule",
            "drawing_method": "the merged ledgers: shaft faces from the T-173 model with the T-201 vector heads (W25 "
                              "+5.50 .. +7.00, W27 +9.70 .. +11.20) and the pier returns kept in their band (T-680); "
                              "annex heights from the slab top bounded 3.544 .. 4.30 (R-T678-2 + roof mark), S = s - "
                              "0.46, H = s - 1.05 (T-686); stair-core tile top 2.20 (highest head, Q-55 C) .. G1 4.35; "
                              "OP-009 2 x 0.20 x 2.20 + 0.20 x 1.00 from the own DXF read (T-676)"},
    P_BAND: {"module": "engine/source/arch_v3069.py (one FIN.PLASTER band line per wet room, ceiling -> soffit, from "
                       "the Checker-merged T-690 R-T690-1 census; bound to the room's backing line by id)",
             "policy": "FINISH_GATE_B_V1", "rule_id": "R-T690-1 (R-T687-1 (d))",
             "owner_rules": ["owner 2026-11-02 / Q-72 (plaster to the structural slab underside, above false ceilings)",
                             "Q-48 A (tile top = finished ceiling)", "Q-14 (slab 0.16 unless stated)",
                             "register ruling 2026-11-11 (the band is plaster's: plaster owns it)"],
             "owner_manual_method": "owner G1 (Q-43, plaster at the paint height) gives no band; the later owner rule "
                                    "(plaster to the slab underside) governs: band = face length x (S - H)",
             "drawing_method": "face length (T-312 / T-128 r3 / T-351) x (S - H): S = storey interval - 0.05 build-up "
                               "(T-214) - 0.16 slab (floor part), the roof part S_roof bounded by the parapet note "
                               "(b_roof < 0.30) or S >= H only on a terrace; H 3.65 GF / 3.35 1F, 2F (Q-48 A); annex "
                               "S - H = 0.59 on one datum; beam ends 0 .. 2 deducted at the low end"},
}
WAITING = dict(A3068.WAITING)
WAITING.update({
    "T687_FIN_BLANK": "FIN.PLASTER 3 lines stay HELD blank: A-GF-01 / A-1F-01 arch reveals (spring and rise printed "
                      "nowhere, D-45; information only <= 1.302 / 1.347 m2) and D-GF-15 gate reveal (width / wall, "
                      "D-53, T-313)",
    "T687_SPATTER_MATERIALS": "spatter dash (T-364) and every coat material line (cement / sand / water) are MISSING "
                              "in the candidate: Q-79 mixes wire only when those lines exist (water HELD: no ratio)",
    "T687_F_T690_1": "B27 soffit +3.60 lies 0.05 below the GF-07 pantry ceiling 3.65 (finding to the Lead; the "
                     "GF-07 band carries its B27 end deduction 0 .. 1.242 m2, the tile line is not touched)",
    "T687_F_T680_1": "W25 section A-A raster +5.6 .. +7.36 vs SW elevation vector +5.50 .. +7.00: the vector governs "
                     "(R-T686-4); residual 0.26 m2 per finish on the 1F shaft lines named (D-45 class)",
})


# ================================================================================================ inputs
def _num(x, w, lo=0.0, hi=100000.0):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or x != x or x < lo or x > hi:
        raise InputsError(f"{w}: {x!r} is not a quantity in range")
    return float(x)


def _status(s, w):
    if not isinstance(s, dict) or s.get("status") not in STATUSES or not s.get("basis"):
        raise InputsError(f"{w}: evidence status {(s or {}).get('status')!r} with its basis (WORKFLOW_CONTROLS s.5; "
                          f"never VERIFIED here)")
    if s["status"] == OA and not s.get("source"):
        raise InputsError(f"{w}: an {OA} status names its owner source")
    return dict(s)


def _restate_entry(x, srcs):
    a = x.get("action")
    w = f"{a} {x.get('line_id')}"
    if a not in ACTIONS:
        raise InputsError(f"entry action {a!r}: V3.0.69 restates to BOUND, VALUE or CAUSE only")
    A3063._need(x, ("line_id", "item_code", "expect", "basis", "source_tasks"), w)
    if x["item_code"] not in CODES:
        raise InputsError(f"{w}: {x['item_code']} is not FIN.PLASTER / FIN.PAINT")
    if any(t not in srcs for t in x["source_tasks"]):
        raise InputsError(f"{w}: no merged source named")
    ex = x["expect"]
    if ex.get("class") != "HELD":
        raise InputsError(f"{w}: only a HELD line is restated here")
    if (ex.get("low") is None) != (ex.get("high") is None):
        raise InputsError(f"{w}: expect low and high together, or neither (blank)")
    e = dict(x, status=_status(x.get("status"), w))
    af = x.get("after") or {}
    if a == "BOUND":
        lo, hi = _num(af.get("low"), w), _num(af.get("high"), w)
        if not 0 < lo < hi:
            raise InputsError(f"{w}: a bound is 0 < low < high ({lo} .. {hi}); a point is a VALUE")
        if e["status"]["status"] not in ("HELD", "UNKNOWN") or not x.get("still_open"):
            raise InputsError(f"{w}: a BOUND line is HELD and names what stays open")
    elif a == "VALUE":
        v = _num(af.get("value"), w)
        if v <= 0 or ex.get("low") is None or not (ex["low"] - TOL <= v <= ex["high"] + TOL):
            raise InputsError(f"{w}: a VALUE closes a bound from inside it (R-T687-1 (b))")
        if e["status"]["status"] != OA:
            raise InputsError(f"{w}: a value closed on a fallback is {OA}")
    else:
        if af or ex.get("low") is not None or not x.get("corrected_cause"):
            raise InputsError(f"{w}: a CAUSE restatement keeps a blank line blank and states the corrected cause")
    return e


def band_figure(b):
    """R-T690-1: the band low .. high (m2) from its merged terms. Main house: face L, H, floor soffit S_f, roof share s
    with roof soffit S_r lo .. hi (or none): L x ((1 - s)(S_f - H) + s (S_r - H)) - beam-end deduction (high end of
    the deduction at the low figure). Annex / core: L x (S - H) on one datum, the ledger's gross range and in-band
    deductions (low <= high <= gross high = L x max(S - H))."""
    L = float(b["face_length_m"])
    if b.get("S_floor_m") is not None:
        H, Sf, s = float(b["H_m"]), float(b["S_floor_m"]), float(b.get("under_roof_share") or 0)
        Sr = b.get("S_roof_m")
        if s and not Sr:
            raise InputsError(f"band {b['engine_room']}: a roof share with no roof soffit bound")
        if Sf < H:
            raise InputsError(f"band {b['engine_room']}: soffit {Sf} below the tile top {H}")
        rlo, rhi = (float(Sr[0]), float(Sr[1])) if Sr else (Sf, Sf)
        if rlo < H - TOL:
            raise InputsError(f"band {b['engine_room']}: roof soffit low {rlo} below the tile top {H}")
        d = [float(x) for x in b.get("deducted_m2") or (0, 0)]
        lo = L * ((1 - s) * (Sf - H) + s * (rlo - H)) - d[1]
        hi = L * ((1 - s) * (Sf - H) + s * (rhi - H)) - d[0]
        return _r(lo), _r(hi)
    H, S = [float(x) for x in b["H_m"]], [float(x) for x in b["S_m"]]
    g = [float(x) for x in b["gross_m2"]]
    joint = abs((S[0] - H[0]) - (S[1] - H[1])) <= TOL          # one datum: S - H fixed (annex)
    gmax = L * ((S[1] - H[1]) if joint else (S[1] - H[0]))
    if abs(g[1] - gmax) > 1e-4:
        raise InputsError(f"band {b['engine_room']}: gross high {g[1]} is not L x max(S - H) = {gmax}")
    return _r(float(b["low"])), _r(float(b["high"]))


def _band_entry(b, srcs):
    w = f"band {b.get('engine_room')}"
    A3063._need(b, ("engine_room", "room", "backing_line_id", "face_length_m", "H_m", "low", "high", "status",
                    "source_tasks", "openings_in_band"), w)
    if any(t not in srcs for t in b["source_tasks"]):
        raise InputsError(f"{w}: no merged source named")
    lo, hi = _num(b["low"], w), _num(b["high"], w)
    if not 0 < lo <= hi:
        raise InputsError(f"{w}: band 0 < low <= high ({lo} .. {hi}); blank is never 0")
    flo, fhi = band_figure(b)
    if abs(flo - lo) > 1e-4 or abs(fhi - hi) > 1e-4:
        raise InputsError(f"{w}: ledger band {lo} .. {hi} is not the recomputed {flo} .. {fhi}")
    st = _status(b["status"], w)
    if st["status"] not in (OA, "HELD") or (st["status"] == OA and lo != hi):
        raise InputsError(f"{w}: a band is {OA} only as a point (H Q-48 A on a drawn soffit), else HELD")
    if st["status"] == "HELD" and not b.get("still_open"):
        raise InputsError(f"{w}: a held band names its open datum (a datum-invariant point stays HELD with it)")
    return dict(b, low=lo, high=hi, status=st)


def load_inputs(doc, project_id=None):
    """URBAN_V3069_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "restate": [{"line_id", "item_code", "action" BOUND | VALUE | CAUSE, "expect" {"class" HELD, "low", "high"},
                  "after" {"low", "high"} | {"value"} | {}, "basis", "status" {"status", "basis", "source"},
                  "still_open", "corrected_cause" (CAUSE), "source_tasks"}],
     "bands": [{"engine_room", "room", "backing_line_id", "face_length_m", "H_m", "S_floor_m" + "S_roof_m" +
                "under_roof_share" + "deducted_m2" | "S_m" + "gross_m2", "low", "high", "status", "still_open",
                "openings_in_band", "joint_total_m2" (optional), "source_tasks"}],
     "expect_totals": {"<code>|m2": {...}} (optional, asserted on the code totals)}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = A3043._sources(doc)
    res = [_restate_entry(x, srcs) for x in doc.get("restate") or ()]
    bands = [_band_entry(b, srcs) for b in doc.get("bands") or ()]
    if not res and not bands:
        raise InputsError("no entry in the inputs")
    ids = [e["line_id"] for e in res]
    if len(set(ids)) != len(ids):
        raise InputsError("a line is named twice (one line, one restatement)")
    rooms = [b["engine_room"] for b in bands]
    if len(set(rooms)) != len(rooms):
        raise InputsError("a room has two band lines (one band per room)")
    return dict(doc, _sources=srcs, _restate=res, _bands=bands)


# ================================================================================================ lines
def _rec(srcs, **kw):
    return dict({"policy": "FINISH_GATE_B_V1", "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _state(ln):
    if ln is None:
        return None
    if ln["evidence_state"] in A3063.EXCLUDED:
        return ("NA", None)
    if ln["evidence_state"] == BOUNDED:
        b = ln["bounded_range"]
        return ("RANGE", (_r(b["low"]), _r(b["high"])))
    if ln.get("measured_net") is not None and ln["evidence_state"] != BLANK:
        return ("VALUE", _r(ln["measured_net"]))
    return ("BLANK", None)


def _assert_before(b, e):
    w = f"{e['action']} {e['line_id']}"
    if b is None:
        raise InputsError(f"{w}: not a candidate line")
    if b["item_code"] != e["item_code"] or b["unit"] != UNIT or line_class(b) != "HELD":
        raise InputsError(f"{w}: candidate line is {b['item_code']} {b['unit']} {line_class(b)}, not a HELD "
                          f"{e['item_code']} m2 line")
    s, ex = _state(b), e["expect"]
    if ex.get("low") is None:
        if s[0] != "BLANK":
            raise InputsError(f"{w}: the ledger started from a blank line, the candidate is {s}")
    elif s[0] != "RANGE" or abs(s[1][0] - ex["low"]) > TOL or abs(s[1][1] - ex["high"]) > TOL:
        raise InputsError(f"{w}: the ledger started from {ex['low']} .. {ex['high']}, the candidate is {s} "
                          f"(R-T687-1 (a))")


def _restate(b, e, srcs):
    a, af = e["action"], e.get("after") or {}
    ln = copy.deepcopy(b)
    was = {"evidence_state": b["evidence_state"], "measured_net": b.get("measured_net"),
           "bounded_range": b.get("bounded_range"), "rfi": b.get("rfi"),
           "formula": (b.get("calculation") or {}).get("formula"), "class": line_class(b)}
    st = e["status"]
    open_ = "; ".join(e.get("still_open") or ()) if isinstance(e.get("still_open"), list) else (e.get("still_open")
                                                                                                or "")
    if a == "BOUND":
        lo, hi = _r(af["low"]), _r(af["high"])
        ln["evidence_state"], ln["measured_net"], ln["gross"] = BOUNDED, None, None
        ln["bounded_range"] = {"low": lo, "high": hi, "basis": e["basis"][:200]}
        ln["rfi"] = {"question": f"open: {open_}"[:400], "blocks": [b["line_id"]]}
        head = f"HELD (BOUNDED) {_fmt(lo)} .. {_fmt(hi)} m2"
        after = {"low": lo, "high": hi}
    elif a == "VALUE":
        v = _r(af["value"])
        ln["evidence_state"], ln["measured_net"], ln["gross"], ln["bounded_range"] = PROV, v, v, None
        ln["rfi"] = None
        head = f"PROVISIONAL {_fmt(v)} m2 ({st['status']}, {st['source']})"
        after = {"value": v}
    else:
        ln["rfi"] = {"question": e["corrected_cause"][:400], "blocks": [b["line_id"]]}
        head = "HELD blank (never 0), cause corrected"
        after = {"blank": True}
    ln["calculation"] = dict(ln["calculation"], formula=(
        f"{METHOD}: {head} = {e['basis']}" + (f"; open: {open_}" if open_ and a != "VALUE" else "")
        + (f"; corrected cause: {e['corrected_cause']}" if a == "CAUSE" else ""))[:1500])
    inp = ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {})
    inp[REC_KEY] = _rec(srcs, piece=P_FIN, action=a, was=was, after=after, basis=e["basis"][:600],
                        evidence_status=st, still_open=open_[:600] or None,
                        corrected_cause=e.get("corrected_cause"), freelancer_beside=e.get("freelancer_beside"))
    A305._note(ln, f"{METHOD}: {head[:300]} (was {A302._q(A30._qty(b)) or 'blank'}); NOT RELEASED")
    return A3063._fin(ln)


def room_line(ln, engine_room, room):
    """the room's own wall-finish line: element '<engine room>:...' or the hold-ledger form 'HL:WALL_FINISH:<room with
    _>:PLASTER' (the room label the merged ledger names, e.g. GF-07 -> GF_07)."""
    eid = (ln.get("location") or {}).get("element_id") or ""
    return eid.startswith(engine_room + ":") or (bool(room) and eid == f"HL:WALL_FINISH:{room.replace('-', '_')}:PLASTER")


def _band_line(src, b, srcs):
    from engine.source import boq_line as BL
    from engine.source import arch_v3046 as A3046
    loc = src.get("location") or {}
    lo, hi = b["low"], b["high"]
    st = b["status"]
    terms = (f"face {b['face_length_m']} m x (S - H)" + (
        f", S floor {b['S_floor_m']} / roof {b.get('S_roof_m')} (share {b.get('under_roof_share')}), H {b['H_m']}, "
        f"beam ends {b.get('deducted_m2')}" if b.get("S_floor_m") is not None else
        f", S {b['S_m']} / H {b['H_m']} on one datum, gross {b['gross_m2']}"))
    joint = b.get("joint_total_m2")
    val = st["status"] == OA
    rec = _rec(srcs, piece=P_BAND, action="VALUE" if val else "BOUND", evidence_status=st,
               backing_line_id=src["line_id"], room=b["room"], engine_room=b["engine_room"], terms=terms[:600],
               openings_in_band=list(b["openings_in_band"]), joint_total_beside_m2=joint,
               still_open=b.get("still_open"))
    f = (f"{METHOD}: wet-room wall band from the tile top H (finished ceiling, Q-48 A) to the plaster top S "
         f"(structural soffit, owner 2026-11-02 / Q-72) = {terms} = {_fmt(lo)}"
         + ("" if val else f" .. {_fmt(hi)}") + " m2 (R-T690-1); beside the backing line "
         + src["line_id"] + " (never summed into it)"
         + (f"; joint room total backing + band {_fmt(joint[0])} .. {_fmt(joint[1])} m2 on one datum (R-T690-1 (d)), "
            f"beside, never the sum of the two separate extremes" if joint else ""))
    eid = f"{b['engine_room']}{BAND_SUFFIX}"
    common = dict(project_id=src["project"]["project_id"], revision_set_sha256=src["project"]["revision_set_sha256"],
                  item_code=PLASTER, unit=UNIT, element_id=eid, floor=loc.get("floor"), room_id=loc.get("room_id"),
                  room_name_en=loc.get("room_name_en"), room_name_ar=loc.get("room_name_ar"),
                  physical_element="wet-room wall plaster band between the finished ceiling and the structural soffit",
                  formula=f[:1500], inputs={REC_KEY: rec, "evidence_status": st["status"]},
                  documents=copy.deepcopy(src["source"]["documents"]),
                  geometry_source=src["source"]["geometry_source"],
                  geometry_confidence=src["source"]["geometry_confidence"], rule_id=RULE_ID, rule_version=RULE_VERSION,
                  material_state="PROJECT_OWNER_FACT")
    if val:
        ln = BL.make_line(evidence_state=PROV, measured_net=lo, gross=lo,
                          notes=f"beside {PLASTER} {src['line_id']} (never summed into it); {st['status']} "
                                f"({st.get('source')}); NOT RELEASED", **common)
    else:
        ln = BL.make_line(evidence_state=BOUNDED,
                          bounded_range={"low": lo, "high": hi, "basis": (b.get("still_open") or "")[:200]},
                          rfi={"question": f"open: {b.get('still_open')}"[:400], "blocks": [src["line_id"]]},
                          notes=f"beside {PLASTER} {src['line_id']} (never summed into it); HELD bounded; a range, "
                                f"never a picked point (a datum-invariant figure stays HELD while its datum is held); NOT RELEASED",
                          **common)
    return A3046._fin(ln)


def changes_for(doc, prev):
    """-> (changes, log): FIN_RESTATE on the named lines, then WET_BAND beside the backing lines."""
    if not doc:
        return [], {"piece": "T687", "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.69 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    eids = {(ln.get("location") or {}).get("element_id") for ln in prev}
    S = doc["_sources"]
    changes, log = [], {"piece": "T687", "state": "RUN", "by_action": {}, "bands": {"VALUE": 0, "BOUND": 0},
                        "sources": [{k: s[k] for k in ("task", "file", "sha256", "merge_commit")}
                                    for s in doc["sources"]]}
    for e in doc["_restate"]:
        b = by.get(e["line_id"])
        _assert_before(b, e)
        srcs = [S[t] for t in e["source_tasks"]]
        after = _restate(b, e, srcs)
        log["by_action"][e["action"]] = log["by_action"].get(e["action"], 0) + 1
        q = A30._qty(after)
        held = None if e["action"] == "VALUE" else [{"what": e["line_id"], "why": (after.get("rfi") or {}).get(
            "question"), "range": [q["low"], q["high"]] if q["low"] is not None else None}]
        changes.append(A305._change(P_FIN, "CHANGE", b, after, step=e["action"], evidence_status=e["status"]["status"],
                                    held=held, verification={"task": " + ".join(e["source_tasks"]),
                                                             "merge_commits": [s["merge_commit"] for s in srcs]}))
    restated = {e["line_id"]: e for e in doc["_restate"]}
    for bd in doc["_bands"]:
        src = by.get(bd["backing_line_id"])
        w = f"band {bd['engine_room']}"
        if src is None or src["item_code"] != PLASTER or src["unit"] != UNIT:
            raise InputsError(f"{w}: backing line {bd['backing_line_id']} is not a candidate FIN.PLASTER m2 line")
        if not room_line(src, bd["engine_room"], bd["room"]):
            raise InputsError(f"{w}: backing line {bd['backing_line_id']} is not this room's line")
        if f"{bd['engine_room']}{BAND_SUFFIX}" in eids:
            raise InputsError(f"{w}: the candidate already carries this band")
        if line_class(src) == "EXCLUDED":
            raise InputsError(f"{w}: an excluded backing line carries no band")
        if src["line_id"] in restated and restated[src["line_id"]]["action"] == "CAUSE":
            raise InputsError(f"{w}: a backing line with no figure")
        srcs = [S[t] for t in bd["source_tasks"]]
        ln = _band_line(src, bd, srcs)
        if ln["line_id"] in by:
            raise InputsError(f"{w}: band line id {ln['line_id']} is already a candidate line")
        act = "VALUE" if bd["status"]["status"] == OA else "BOUND"
        log["bands"][act] += 1
        changes.append(A305._change(P_BAND, "ADD", None, ln, step=act, evidence_status=bd["status"]["status"],
                                    held=None if act == "VALUE" else [{"what": "wet band", "why": bd.get("still_open"),
                                                                       "range": [bd["low"], bd["high"]]}],
                                    verification={"task": " + ".join(bd["source_tasks"]),
                                                  "merge_commits": [s["merge_commit"] for s in srcs]}))
    log["lines"] = len(changes)
    return changes, log


# ================================================================================================ checks
def expected_totals(t0, changes):
    return A3068.expected_totals(t0, changes)


def check_totals(t0, t1, changes, expect=None):
    """only FIN.PLASTER|m2 / FIN.PAINT|m2 move, each exactly by the changes (R-T687-1 (f))."""
    moved = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    bad = sorted(k for k in moved if k not in (f"{c}|{UNIT}" for c in CODES))
    if bad:
        raise ValueError(f"{METHOD}: totals moved outside FIN.PLASTER / FIN.PAINT: {bad}")
    want = expected_totals(t0, changes)
    out = {}
    for k in moved:
        z, a = want.get(k), t1.get(k)
        if z is None or a is None:
            raise ValueError(f"{METHOD}: {k} moved with no change on it")
        if a["lines"] != z["lines"] or a["bounded_lines"] != z["bounded_lines"] or \
                a["blocked_lines"] != z["blocked_lines"] or \
                any(abs(a[f] - z[f]) > TOT_TOL for f in ("released", "held_low", "held_high")):
            raise ValueError(f"{METHOD}: {k} totals {a} are not the changes' {z}")
        if expect and k in expect:
            for f, v in expect[k].items():
                if abs(a[f] - v) > TOT_TOL:
                    raise ValueError(f"{METHOD}: {k} {f} {a[f]} is not the inputs' {v}")
        out[k] = {"base": t0.get(k), "v3_0_69": a, "view": A3058.total_view(a)}
    return out


def check_finishes(lines, before=None):
    """on finished lines: every V3.0.69 record is in the state its action names; a band line binds a FIN.PLASTER
    line of the same room, one band per room; no line VERIFIED; with `before`: a restated line was HELD. -> summary"""
    by = {ln["line_id"]: ln for ln in lines}
    out = {a: 0 for a in ACTIONS}
    out.update(band_value=0, band_bound=0)
    rooms = set()
    old = {x["line_id"]: x for x in before} if before is not None else None
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        eid = (ln.get("location") or {}).get("element_id") or ""
        if not rec:
            if eid.endswith(BAND_SUFFIX):
                raise ValueError(f"{METHOD}: {ln['line_id']} a band line with no V3.0.69 record")
            continue
        s = _state(ln)
        if (rec.get("evidence_status") or {}).get("status") == "VERIFIED" or ln["item_code"] not in CODES:
            raise ValueError(f"{METHOD}: {ln['line_id']} a V3.0.69 line is a FIN code and never VERIFIED")
        if rec["piece"] == P_FIN:
            a = rec["action"]
            ok = rec["was"]["class"] == "HELD" and (
                (a == "BOUND" and s[0] == "RANGE" and 0 < s[1][0] < s[1][1] and bool((ln.get("rfi") or {}).get(
                    "question"))) or
                (a == "VALUE" and s[0] == "VALUE" and ln["evidence_state"] == PROV and s[1] > 0) or
                (a == "CAUSE" and s[0] == "BLANK" and bool((ln.get("rfi") or {}).get("question"))))
            if old is not None:
                ok = ok and ln["line_id"] in old and line_class(old[ln["line_id"]]) == "HELD"
            if not ok:
                raise ValueError(f"{METHOD}: {ln['line_id']} a {a} line is not in its state")
            out[a] += 1
        elif rec["piece"] == P_BAND:
            src = by.get(rec["backing_line_id"])
            if src is None or src["item_code"] != PLASTER or not room_line(src, rec["engine_room"], rec["room"]):
                raise ValueError(f"{METHOD}: {ln['line_id']} binds no backing line of its room")
            if rec["engine_room"] in rooms or not eid.endswith(BAND_SUFFIX) or ln["item_code"] != PLASTER:
                raise ValueError(f"{METHOD}: {ln['line_id']} a second band for {rec['engine_room']} or a bad id")
            rooms.add(rec["engine_room"])
            if s[0] == "VALUE" and ln["evidence_state"] == PROV and rec["evidence_status"]["status"] == OA:
                out["band_value"] += 1
            elif s[0] == "RANGE" and 0 < s[1][0] <= s[1][1] and rec["evidence_status"]["status"] == "HELD" and \
                    bool((ln.get("rfi") or {}).get("question")):
                out["band_bound"] += 1
            else:
                raise ValueError(f"{METHOD}: {ln['line_id']} a band line is not in its state")
        else:
            raise ValueError(f"{METHOD}: {ln['line_id']} unknown piece {rec['piece']}")
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.69 lines, identity). Changed lines replace their candidate line in place, added band lines follow the
    base; every other candidate line byte-identical (asserted); the V3.0.67 concrete / lintel checks and the V3.0.68
    masonry check re-run (nothing of theirs may move)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out, repl, add = list(prev), set(), []
    for c in changes:
        a = c["after"]
        if a["item_code"] not in CODES or a["unit"] != UNIT:
            raise ValueError(f"{METHOD}: {a['item_code']} is not a code this version may touch")
        if c["action"] == "CHANGE":
            i = sid.get(a["line_id"])
            if i is None or a["line_id"] in repl:
                raise ValueError(f"{METHOD}: a changed line is not a candidate line or changes twice")
            out[i] = a
            repl.add(a["line_id"])
        elif c["action"] == "ADD":
            if c["piece"] != P_BAND or a["line_id"] in sid:
                raise ValueError(f"{METHOD}: only band lines are added, never over a candidate id")
            add.append(a)
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = out + add
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    outside = [ln for ln in prev if ln["line_id"] not in repl]
    bad = [a["line_id"] for a in outside if A30.line_sha(a) != A30.line_sha(out[sid[a["line_id"]]])]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} candidate line(s) differ outside the named changes")
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines")
    ident = {"base_lines": len(prev), "v3_0_69_lines": len(out), "v3_0_69_rows": len(changes), "replaced": len(repl),
             "added": len(add), "concrete_v3_0_67": A3067.check_concrete(out, prev),
             "lintels_v3_0_67": A3067.check_lintels(out), "masonry_v3_0_68": A3068.check_masonry(out),
             "finishes": check_finishes(out, prev),
             "outside_rows": len(outside), "outside_rows_identical_to_base": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        a = c["after"]
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(a)]) if A30._key(a) in rel else dict(A30._qty(None), state="NOT_IN_RELEASED")
        rec = a["calculation"]["inputs"][REC_KEY]
        loc = a.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c.get("step"), "change": c["action"],
                     "line_id": a["line_id"], "item_code": a["item_code"], "floor": loc.get("floor"),
                     "element_id": loc.get("element_id"), "unit": a["unit"],
                     "before_released_v2_9": b29, "before_base": A30._qty(c.get("before")),
                     "after_v3_0_69": A30._qty(a), "class": [None if c.get("before") is None else
                                                            line_class(c["before"]), line_class(a)],
                     "evidence_status": c.get("evidence_status"), "still_held": c.get("held"),
                     "record": {k: v for k, v in rec.items() if k not in ("ledger_sha256", "was")},
                     "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "element_id", "unit", "v2_9",
              "base", "v3_0_69", "class", "evidence_status", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_69")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_69": q(r.get("after_v3_0_69")), "class": " -> ".join(str(x) for x in r["class"]),
                       "evidence_status": r["evidence_status"],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    return [dict({k: v for k, v in d.items() if k != "v3_0_58"}, v3_0_69=d["v3_0_58"])
            for d in A3058.diff_rows(prev, new, released_lines)]


def write(out, prev, changes, log, released_lines=None, for_lead=(), expect_totals=None):
    """the V3_0_69_* files beside the base candidate's files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    new, ident = integrate(prev, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(prev, new, released_lines)
    named = {c["after"]["line_id"] for c in changes}
    stray = [d["line_id"] for d in diff if d["vs_base"] != "SAME" and d["line_id"] not in named]
    if stray:
        raise ValueError(f"{METHOD}: {len(stray)} line(s) changed outside the named changes")
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_base", {}).setdefault(d["vs_base"], 0)
        dsum["vs_base"][d["vs_base"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    moved = check_totals(A304.code_totals(prev), A304.code_totals(new), changes, expect_totals)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "summary": log, "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_69_BOQ_LINES.json": BL.dumps(new),
             "V3_0_69_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_69_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_69_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_69_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_69_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "codes": list(CODES), "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "CODES", "load_inputs",
           "changes_for", "band_figure", "expected_totals", "check_totals", "check_finishes", "integrate",
           "ledger_rows", "diff_rows", "write", "InputsError", "line_class"]
