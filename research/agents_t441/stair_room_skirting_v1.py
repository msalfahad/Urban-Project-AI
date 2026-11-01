"""STAIR_ROOM_SKIRTING_V1 (T-441, research; any villa): the floor-level wall-face length of each FLOOR part of a stair
room (R-T418-1 parts), measured side by side, so a skirting line that is BLOCKED for the whole stair room can carry a
drawn length for the floored parts beside its blocked parent. Stdlib only; nothing here is wired into a method.

Rules (R-T441-1 .. 4, proposed, research):
  R-T441-1  A floor part's boundary is cut into SIDES; each side is cut into STRETCHES that cover it exactly once
            (no gap, no overlap). A stretch is one of:
              WALL / COLUMN      vertical finished face at the part's floor level (skirted, UP-SKIRT-001)
              DOOR               door opening, deducted by its opening id, no jamb skirting (frame covers the jamb)
              PASSAGE            doorless opening, deducted by id; its two jamb returns are listed separately
              LIFT_OPENING       lift landing opening, deducted by id; its jambs belong to the lift surround (B6-06) and
                                 its 0.200 band to the threshold (B6-07): never skirting (register LIFT LANDING THRESHOLD)
              OPEN               no face: the part continues into another floor part, a flight or a void
              STAIR_SIDE         a wall face beside the part that the merged stair side table (T-410) already owns
                                 from its drawn station: listed, not counted here (R-T441-2)
              GUARD_HELD         a solid stair band / guard face whose wall-or-guard role is not established: HELD
              HELD / UNKNOWN     a face whose existence or extent is not established: HELD, blank, never 0
  R-T441-2  One physical base, one owner: a WALL / COLUMN stretch may not share wall line, plan interval and level with
            a stair side stretch of the merged side table (T-410): where the flight's stretch starts (its drawn station)
            the floor part's face stops.
  R-T441-3  Deductions are by opening id, with the drawn gap as width; an opening without an id is refused.
  R-T441-4  Lengths in metres (a stretch over 50 m is refused as a unit slip); every HELD / UNKNOWN / GUARD_HELD figure
            stays None in the confirmed total and carries its cause and, where drawn, its candidate length.
"""
from __future__ import annotations

METHOD = "STAIR_ROOM_SKIRTING_V1"
RULES = ("R-T441-1", "R-T441-2", "R-T441-3", "R-T441-4")
TOL = 1e-6
MAX_M = 50.0

FACE = ("WALL", "COLUMN")
OPENINGS = ("DOOR", "PASSAGE", "LIFT_OPENING")
HELD_KINDS = ("GUARD_HELD", "HELD", "UNKNOWN")
KINDS = FACE + OPENINGS + ("OPEN", "STAIR_SIDE") + HELD_KINDS

DRAWING_CONFIRMED = "DRAWING-CONFIRMED"
HELD = "HELD"
PROVISIONAL = "PROVISIONAL"


class Refused(ValueError):
    pass


def _r(x):
    return round(x + 0.0, 6)


def check_side(side):
    """a side's stretches cover [0, length] once, in order; refuse gaps, overlaps, unknown kinds, unit slips."""
    L = side["length"]
    if not (0 < L <= MAX_M):
        raise Refused(f"side {side['id']}: length {L} m outside (0, {MAX_M}] (unit slip?)")
    pos = 0.0
    for st in side["stretches"]:
        k = st["kind"]
        if k not in KINDS:
            raise Refused(f"side {side['id']}: unknown stretch kind {k}")
        a, b = st["s0"], st["s1"]
        if b - a <= TOL:
            raise Refused(f"side {side['id']}: empty or reversed stretch {a}..{b}")
        if abs(a - pos) > TOL:
            raise Refused(f"side {side['id']}: {'gap' if a > pos else 'overlap'} at s {pos:.3f} .. {a:.3f}")
        if k in OPENINGS and not st.get("opening_id"):
            raise Refused(f"side {side['id']}: {k} at s {a:.3f} deducted without an opening id (R-T441-3)")
        if k in FACE and not st.get("handles"):
            raise Refused(f"side {side['id']}: {k} face at s {a:.3f} without a drawn handle")
        if k in HELD_KINDS and not st.get("cause"):
            raise Refused(f"side {side['id']}: {k} at s {a:.3f} without a cause (R-T441-4)")
        if k in HELD_KINDS and st.get("lm") == 0:
            raise Refused(f"side {side['id']}: {k} carried as 0 (held is blank, never 0)")
        pos = b
    if abs(pos - L) > TOL:
        raise Refused(f"side {side['id']}: stretches end at {pos:.3f}, side is {L:.3f} (short cover)")


def check_jambs(space):
    """jamb returns: a PASSAGE may carry jambs (separate, not in the confirmed net); a LIFT_OPENING never does."""
    kinds = {st["opening_id"]: st["kind"] for sd in space["sides"] for st in sd["stretches"] if st["kind"] in OPENINGS}
    for j in space.get("jambs", []):
        k = kinds.get(j["opening_id"])
        if k is None:
            raise Refused(f"jamb {j['id']}: opening {j['opening_id']} is not deducted on this part")
        if k == "LIFT_OPENING":
            raise Refused(f"jamb {j['id']}: lift-opening jamb given skirting (owner B6-06 surround)")
        if k == "DOOR":
            raise Refused(f"jamb {j['id']}: door jamb given skirting (UP-SKIRT-001: not across / into door openings)")
        if not (0 < j["depth"] <= 1.0):
            raise Refused(f"jamb {j['id']}: depth {j['depth']} m outside (0, 1] (unit slip?)")


def overlaps(space, flight_stretches):
    """R-T441-2: WALL / COLUMN stretches of this part that share wall line, plan interval and level with a merged
    stair side stretch. Each side and each flight stretch names its wall line ('line') and its plan interval in the
    same along-line coordinate ('t0'..'t1'); a flight stretch carries its level range (lo, hi)."""
    out = []
    for sd in space["sides"]:
        for st in sd["stretches"]:
            if st["kind"] not in FACE:
                continue
            t0 = sd["t0"] + sd["dir"] * st["s0"]
            t1 = sd["t0"] + sd["dir"] * st["s1"]
            lo_t, hi_t = min(t0, t1), max(t0, t1)
            for f in flight_stretches:
                if f["line"] != sd["line"]:
                    continue
                if not (f["lo"] - TOL <= space["level"] <= f["hi"] + TOL):
                    continue
                ov = min(hi_t, f["t1"]) - max(lo_t, f["t0"])
                if ov > TOL:
                    out.append({"side": sd["id"], "s0": st["s0"], "flight": f["id"], "overlap_m": _r(ov)})
    return out


def measure(space, flight_stretches=()):
    """face table and totals of one floor part. Refuses a part whose faces overlap a flight stretch (R-T441-2)."""
    for sd in space["sides"]:
        check_side(sd)
    check_jambs(space)
    ov = overlaps(space, flight_stretches)
    if ov:
        raise Refused(f"part {space['id']}: wall face shared with a stair side stretch {ov} (R-T441-2)")
    rows, gross, ded, held = [], 0.0, [], []
    for sd in space["sides"]:
        for st in sd["stretches"]:
            L = _r(st["s1"] - st["s0"])
            k = st["kind"]
            row = {"part": space["id"], "side": sd["id"], "s0": _r(st["s0"]), "s1": _r(st["s1"]), "kind": k,
                   "length_m": L, "handles": st.get("handles", ""), "opening_id": st.get("opening_id", ""),
                   "note": st.get("note", "")}
            if k in FACE:
                gross += L
                row["skirting_lm"], row["status"] = L, DRAWING_CONFIRMED
            elif k in OPENINGS:
                ded.append({"opening_id": st["opening_id"], "kind": k, "width_m": L})
                row["skirting_lm"], row["status"] = 0.0, "DEDUCTED"
            elif k == "OPEN":
                row["skirting_lm"], row["status"] = 0.0, "NO FACE"
            elif k == "STAIR_SIDE":
                if not st.get("flight"):
                    raise Refused(f"side {sd['id']}: STAIR_SIDE at s {st['s0']:.3f} without the owning stair stretch")
                row["skirting_lm"], row["status"] = 0.0, "OWNED BY STAIR SIDE " + st["flight"]
            else:
                held.append({"side": sd["id"], "kind": k, "candidate_lm": st.get("candidate_lm", L),
                             "candidate_high_lm": st.get("candidate_high_lm"), "cause": st["cause"]})
                row["skirting_lm"], row["status"] = None, HELD
            row["cause"] = st.get("cause", "")
            rows.append(row)
    boundary = sum(sd["length"] for sd in space["sides"])
    face_side = sum(r["length_m"] for r in rows if r["kind"] in FACE + OPENINGS)
    jambs = [{"id": j["id"], "opening_id": j["opening_id"], "depth_m": _r(j["depth"]), "status": j.get("status", HELD),
              "cause": j.get("cause", "")} for j in space.get("jambs", [])]
    return {"part": space["id"], "room": space["room"], "level": space["level"], "rows": rows,
            "boundary_m": _r(boundary),
            "gross_face_side_m": _r(face_side),           # faces + openings: the drawn wall line beside the part
            "deductions": ded, "deducted_m": _r(sum(d["width_m"] for d in ded)),
            "net_confirmed_lm": _r(gross),               # WALL + COLUMN only; never includes a held stretch
            "held": held, "held_count": len(held),
            "jambs": jambs, "jambs_lm": _r(sum(j["depth_m"] for j in jambs)),
            "status": DRAWING_CONFIRMED if not held else "DRAWING-CONFIRMED part + HELD remainder"}


def lift_band_check(space, band):
    """the lift threshold band (front edge on the wall line, two side edges = the jambs) lies outside the floor part
    and owns no skirting: refuse a part that lists any band edge as a WALL / COLUMN stretch."""
    edges = set(band["edge_handles"])
    for sd in space["sides"]:
        for st in sd["stretches"]:
            if st["kind"] in FACE and edges & set(st.get("handles", "").split()):
                raise Refused(f"part {space['id']}: lift threshold band edge {sorted(edges & set(st['handles'].split()))} "
                              "counted as wall face (register LIFT LANDING THRESHOLD: B6-06 / B6-07)")
    return True
