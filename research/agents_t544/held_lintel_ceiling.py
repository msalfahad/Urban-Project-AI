"""R-T544-1 1.0.0 (T-544, lane S, non-candidate): the face a HELD lintel (existence not established: the opening head is a
designer item) can take out of its host masonry, bounded from above by the MEASURED masonry beside both jambs (every
villa). Research rule BESIDE R-T498-2 1.0.0 (research/agents_t537/r_t498_2.py, imported read-only, never edited).

PHYSICAL ELEMENT. Over an opening whose head height is not established (no printed sill / height: designer D-45 on the
development villa) it is not known whether masonry is built above the opening, so whether a lintel exists. IF one
exists it is one RC piece cast to length over the clear opening and resting on the masonry beside each jamb; it cannot
run past the first column face, the next opening or the end of the masonry on its own wall line (R-T516-1 / R-T527-1
stopper order). Its face in the host wall is therefore in {0} U [D x L_min, D x L_ceil] and the material base needs
only the two ends of the hull: 0 .. D x L_ceil.

RULE R-T544-1 (scope: any HELD lintel face on any host masonry line; provenance R-T516-1 masonry beside a jamb,
R-T527-1 V3 drawn ends, R-T498-2 (1)-(3) and (6), F-T537-1 a min-bearing length is no maximum, F-T537-2 ceiling
rounding direction; no new factor, no new rate):
  (1) END CEILING. Each end's ceiling c is the measured a (jamb -> first COLUMN / OPENING / END_OF_MASONRY, full wall
      thickness, LINTEL_BEARING_V3) ROUNDED UP to the mm (an upper bound rounds up; F-T537-2). An end that stopped at
      the search limit is re-searched along the same line to L_MAX (20 m); still no stopper -> no ceiling. A
      printed-minimum bearing figure (0.40 m detail, 0.15 m precast) is never a ceiling: refused.
  (2) LINTEL CEILING. L_ceil = w_gap + c_START + c_END rounded UP to the mm, w_gap the DRAWN clear gap (the jamb the a's
      are measured from), never the rounded schedule width. Any end without a ceiling -> the face is OPEN above.
  (3) HELD FACE. face = [0, D x L_ceil] (0: the lintel may not exist; never D x (w + 0.80), which is a LOWER bound of a
      built lintel). B != host thickness -> OPEN (R-T498-2 (6), partial depth).
  (4) SHARED PIER. Two lintels whose facing ends stop at each other (one pier, OPENING stopper both ways) on the SAME
      host are ONE joint record: lo = sum of the member lows, hi = max(D) x (outer c + w_gap + pier + w_gap + outer c),
      the pier counted once (both members cannot each take the whole pier); on two hosts -> both OPEN (R-T498-2 (6)).
      The joint span is cross-checked against the face-to-face distance of the outer stoppers when both are columns.
  (5) The records enter R-T498-2 material_base unchanged ((2) low end takes every high end; any open face -> HELD).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t537"))
import r_t498_2 as R  # noqa: E402  (read only)

RULE_ID = "R-T544-1"
RULE_VERSION = "1.0.0"
STOPPERS_WITH_CEILING = ("COLUMN", "OPENING", "END_OF_MASONRY")
MIN_BEARING_FIGURES = (0.40, 0.15)            # printed detail minimum / owner precast minimum: never a ceiling


class RuleError(R.RuleError):
    pass


def ceil_mm(x):
    """round UP to the mm (an upper bound); a value already on the mm (within 1e-7 m) stays."""
    v = float(x) * 1000.0
    return math.ceil(v - 1e-4) / 1000.0


def end_ceiling(oid, end):
    """end: {"side", "a_m" (6 dp measured reach), "stopper", "basis": "MEASURED" | "MIN_BEARING"} -> ceiling m or None."""
    side = end.get("side")
    if side not in ("START", "END"):
        raise RuleError(f"{oid}: end side {side!r}")
    if end.get("basis") != "MEASURED":
        raise RuleError(f"{oid} {side}: basis {end.get('basis')!r}: only a MEASURED reach is a ceiling (a printed "
                        f"minimum bearing bounds from below)")
    st = end.get("stopper")
    if st == "SEARCH_LIMIT":
        return None
    if st not in STOPPERS_WITH_CEILING:
        raise RuleError(f"{oid} {side}: stopper {st!r} has no ceiling rule")
    return ceil_mm(R._m(end.get("a_m"), f"{oid} {side} a", R.L_MAX))


def held_face(oid, section_B_D_m, w_gap_m, ends, host_t_m):
    """one HELD lintel -> an R-T498-2 face record (face_m2 [0, hi] or [0, None] OPEN) with its ceilings."""
    B, D = (R._m(x, f"{oid} section", R.D_MAX) for x in section_B_D_m)
    w = R._m(w_gap_m, f"{oid} w_gap", R.L_MAX)
    if len(ends) != 2 or {e.get("side") for e in ends} != {"START", "END"}:
        raise RuleError(f"{oid}: needs one START and one END")
    cs = {e["side"]: end_ceiling(oid, e) for e in ends}
    rec = {"opening_id": oid, "legacy": False, "ceilings_m": cs, "w_gap_m": w, "D_m": D, "rule": RULE_ID}
    if abs(B - float(host_t_m)) > 1e-6:
        return dict(rec, face_m2=[0.0, None], open=True, L_ceil_m=None,
                    why=f"lintel width {B} != host thickness {host_t_m}: partial depth, OPEN (R-T498-2 (6))")
    if None in cs.values():
        return dict(rec, face_m2=[0.0, None], open=True, L_ceil_m=None,
                    why="an end without a measured stopper: upper length unknown, OPEN (never a min-bearing figure)")
    L = ceil_mm(w + cs["START"] + cs["END"])
    return dict(rec, face_m2=[0.0, R._r(D * L)], open=False, L_ceil_m=L,
                why=f"HELD (existence not established): face 0 .. D {D} x L_ceil {L} (w_gap {w} + ceilings "
                    f"{cs['START']} + {cs['END']}, measured, rounded up)")


def joint_face(members, hosts_of):
    """two lintels sharing one pier -> one joint record on their single host, else both OPEN.

    members: [first, second] in band order; each {"opening_id", "D_m", "w_gap_m", "face_lo_m2", "outer": end dict
    (the end away from the pier)}; plus "pier_m" (measured, both facing ends stop at each other) on the first."""
    a, b = members
    ha, hb = hosts_of.get(a["opening_id"]), hosts_of.get(b["opening_id"])
    jid = f"{a['opening_id']}+{b['opening_id']}"
    if ha is None or ha != hb:
        return {m["opening_id"]: {"opening_id": m["opening_id"], "face_m2": [0.0, None], "open": True,
                                  "legacy": False, "why": "shared pier split over two hosts: designer item (R-T498-2 (6))"}
                for m in members}
    D = max(R._m(m["D_m"], f"{m['opening_id']} D", R.D_MAX) for m in members)
    pier = ceil_mm(R._m(a["pier_m"], f"{jid} pier", R.L_MAX))
    co = [end_ceiling(m["opening_id"], m["outer"]) for m in members]
    lo = R._r(sum(R._m(m["face_lo_m2"], f"{m['opening_id']} face lo", R.L_MAX * R.D_MAX) for m in members))
    rec = {"opening_id": jid, "legacy": False, "members": [a["opening_id"], b["opening_id"]], "pier_m": pier,
           "outer_ceilings_m": co, "D_m": D, "rule": RULE_ID}
    if None in co:
        return {jid: dict(rec, face_m2=[lo, None], open=True, L_ceil_m=None,
                          why="an outer end without a measured stopper: OPEN")}
    L = ceil_mm(co[0] + R._m(a["w_gap_m"], "w", R.L_MAX) + pier + R._m(b["w_gap_m"], "w", R.L_MAX) + co[1])
    if D * L < lo - 1e-9:
        raise RuleError(f"{jid}: joint ceiling below the member lows (inverted)")
    return {jid: dict(rec, face_m2=[lo, R._r(D * L)], open=False, L_ceil_m=L,
                      why=f"one pier {pier} m shared on one host: joint span {L} m (pier counted once), "
                          f"face [{lo}, {R._r(D * L)}]")}
