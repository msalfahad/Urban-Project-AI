"""R-T498-2 1.0.0 (T-537, lane I, non-candidate): blockwork material base of a host wall whose lintel faces are BOUNDED
or RANGED (every villa). A new rule version BESIDE R-T498-1 1.0.0 (engine/source/arch_v3059.py on the T-498 stage,
never edited): R-T498-1 knows a lintel face of ONE value (deducted, the lintel line valued) and a HELD face 0 .. max
(the lintel line blank); after the lintel wiring (T-516 R-T516-1, T-519 R-T519-1, T-524 R-T524-1) a REQUIRED lintel is
cast to a length that is only known as an interval, so its face in the host wall is an interval too. Gap RG-1 /
F-T530-2 (T-530 WIRING MANIFEST, merged f05abdd6).

PHYSICAL ELEMENT. The block face that remains in a host wall after the RC lintel band over each opening is taken out
of it, and the glue (white AAC) or the laying mortar and units (black block) on that face. The MAS.BLOCK contract area
(drawn pieces x clear height - openings) never moves: only the MATERIAL base loses the lintel face (R-T453-5, owner
Q-73, register 'RC LINTEL over an opening vs the host masonry wall'). Installed (theoretical) quantities only; waste /
breakage stay HELD (no sourced value; owner: waste separate); procurement rounding belongs to the purchasing group.

RULE R-T498-2 (scope: every host masonry line of any villa whose material base loses one or more lintel faces;
provenance: R-T453-5 face = D x L, R-T516-1 L in [w + 2 x printed minimum bearing, w + a_s + a_e], R-T524-1 deficit-end
length, R-T523-1 one ceiling per purchasing group, UP-QTY-STATUS-001, owner 2026-11-02 AAC glue / black block rules;
no new factor, no new rate):
  (1) FACE. Each lintel face in the host is D x [L_lo, L_hi] in m2, D the lintel depth and [L_lo, L_hi] the built
      length interval of ITS OWN lintel line (VALUED: L_lo = L_hi; BOUNDED_MIN_BEARING: T-516 lengths; HELD_BY_NAME with
      a bound: T-524 lengths; a lone held face with no length: R-T498-1 0 .. face_max, kept ONLY where that maximum
      is a proven ceiling). L_hi unknown -> the face is OPEN above. A held face whose 'maximum' is D x (w + 2 x the
      printed minimum bearing) (the T-453 length) is OPEN: R-T516-1 proved that length is the LOWER bound of a built
      lintel, so it bounds nothing from above (finding F-T537-1).
  (2) BASE. material base = [net - sum(face_hi) - sum(legacy held max), net - sum(face_lo)]: the LOW end of the
      material takes the HIGH end of every face (the longest lintel) and the HIGH end takes the LOW end of every face;
      no midpoint, never the larger or the smaller alone. lo == hi on every face -> one value (EXACT).
  (3) OPEN. Any open face -> the material line is HELD blank by name, never 0; its known UPPER end (net - sum face_lo)
      x rate is shown BESIDE as AT_MOST, never as the quantity.
  (4) MATERIALS. Every material of the host is the base interval x its owner rate (12.5 / m2 black 40 x 20; mortar
      joint m3 / m2; glue 3.5 / 4.5 kg / m2): a ranged base gives a ranged line (BOUNDED_EXPOSURE) with both ends.
  (5) PURCHASE. A ranged key enters its purchasing group with both ends; R-T523-1 sums the ends ONCE per group and
      takes the ceiling of EACH end: to-buy [ceil(sum lo / pack), ceil(sum hi / pack)]. When both ceilings are equal
      the to-buy is DETERMINATE (every value in the range needs that number of packs); otherwise it stays a range by
      name: the ceiling of the high end is never booked as 'the' quantity. A group with a HELD member or a HELD loss
      stays HELD with AT_LEAST (R-T523-1 unchanged).
  (6) REFUSED. An inverted interval (L_lo > L_hi), a negative or millimetre length / depth, faces whose high ends exceed
      the host net, a lintel whose width B differs from the host thickness (partial-depth lintel: the remaining block
      skin is not measured -> that face OPEN, HELD), a two-lintel PAIR whose members sit on two hosts (split = designer
      item -> both hosts' faces OPEN), the same lintel named on two hosts, a pre-rounded bag figure.

Nothing here imports the candidate or changes a frozen file; no drawing, client name or coordinate is in this folder.
"""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path

RULE_ID = "R-T498-2"
RULE_VERSION = "1.0.0"
EXTENDS = "R-T498-1 1.0.0 (case (1) only; R-T498-1 is not edited)"
ROOT = Path(__file__).resolve().parents[2]
TOL = 1e-9
FACE_TOL = 0.0005                     # m2: candidate lines print 4 decimals
D_MAX, L_MAX = 2.0, 20.0              # m: a depth / length above these is millimetres or a unit error
# the basis of a HELD face's maximum: UPPER_PROVEN = D x a measured ceiling length (piers / stoppers measured);
# MIN_BEARING_LENGTH = D x (w + 2 x printed minimum bearing), the T-453 length, a LOWER bound of a built lintel (T-516)
FACE_MAX_BASES = ("UPPER_PROVEN", "MIN_BEARING_LENGTH")


class RuleError(ValueError):
    pass


def _r(x, n=6):
    return None if x is None else round(float(x) + 0.0, n)


def _m(x, where, hi):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0:
        raise RuleError(f"{where}: {x!r} is not a non-negative number in metres")
    if x > hi:
        raise RuleError(f"{where}: {x} m is above {hi} m (millimetres or a unit error: refused)")
    return float(x)


# ------------------------------------------------------------------------------------------------ (1) face
def lintel_face(lz, host_t_m):
    """one lintel -> {"opening_id", "face_m2": [lo, hi or None], "open": bool, "why"}.

    lz: {"opening_id", "state" in VALUED | BOUNDED_MIN_BEARING | HELD_BY_NAME | HELD_FACE,
         "section_B_D_m": [B, D], "length_m": [lo, hi or None]   (VALUED / BOUNDED / HELD_BY_NAME with a bound)
         "face_max_m2": x or None                                 (HELD_FACE: R-T498-1 legacy, 0 .. max)}"""
    oid = lz.get("opening_id")
    if not oid:
        raise RuleError("a lintel face without an opening id")
    st = lz.get("state")
    if st == "HELD_FACE":
        fm, basis = lz.get("face_max_m2"), lz.get("face_max_basis")
        if basis not in FACE_MAX_BASES:
            raise RuleError(f"{oid}: a HELD face states the basis of its maximum ({', '.join(FACE_MAX_BASES)})")
        if fm is None:
            return {"opening_id": oid, "face_m2": [0.0, None], "open": True, "legacy": True,
                    "why": "HELD lintel face with no bound (R-T498-1): open above"}
        fm = _r(_m(fm, f"{oid} face_max", L_MAX * D_MAX))
        if basis == "MIN_BEARING_LENGTH":
            return {"opening_id": oid, "face_m2": [0.0, None], "open": True, "legacy": True, "min_bearing_face_m2": fm,
                    "why": f"HELD lintel face whose 'maximum' {fm} m2 is D x (w + 2 x printed minimum bearing): R-T516-1 "
                           f"shows that length is the LOWER bound of a built lintel, so it is no maximum; if the lintel "
                           f"exists its face lies in [{fm}, D x (w + a_s + a_e)], piers not measured: open above"}
        return {"opening_id": oid, "face_m2": [0.0, fm], "open": False, "legacy": True,
                "why": "HELD lintel face 0 .. a proven maximum (R-T498-1 case kept)"}
    if st not in ("VALUED", "BOUNDED_MIN_BEARING", "HELD_BY_NAME"):
        raise RuleError(f"{oid}: lintel state {st!r} has no face rule")
    sec = lz.get("section_B_D_m")
    if not (isinstance(sec, (list, tuple)) and len(sec) == 2):
        raise RuleError(f"{oid}: section_B_D_m is [B, D] in metres")
    B, D = _m(sec[0], f"{oid} B", D_MAX), _m(sec[1], f"{oid} D", D_MAX)
    ln = lz.get("length_m")
    if not (isinstance(ln, (list, tuple)) and len(ln) == 2) or ln[0] is None:
        raise RuleError(f"{oid}: length_m is [L_lo, L_hi or None]; a {st} lintel without a lower length is HELD_FACE")
    lo = _m(ln[0], f"{oid} L_lo", L_MAX)
    hi = None if ln[1] is None else _m(ln[1], f"{oid} L_hi", L_MAX)
    if hi is not None and lo > hi + TOL:
        raise RuleError(f"{oid}: inverted length interval [{lo}, {hi}] (refused)")
    if st == "VALUED" and (hi is None or abs(hi - lo) > TOL):
        raise RuleError(f"{oid}: a VALUED lintel has one length")
    if abs(B - float(host_t_m)) > 1e-6:
        return {"opening_id": oid, "face_m2": [0.0, None], "open": True, "legacy": False,
                "why": f"lintel width {B} m differs from the host thickness {host_t_m} m (partial-depth lintel: the "
                       f"block skin beside it is not measured): face OPEN, the material HELD"}
    if hi is None:
        return {"opening_id": oid, "face_m2": [_r(D * lo), None], "open": True, "legacy": False,
                "why": "upper length not measured (no pier ceiling): face open above, the material HELD, never 0"}
    return {"opening_id": oid, "face_m2": [_r(D * lo), _r(D * hi)], "open": False, "legacy": False,
            "why": f"D {D} x L [{lo}, {hi}] of the lintel line ({st})"}


def pair_faces(pair, hosts_of):
    """a two-lintel pair (T-524: over one pier, split = designer) on its host(s): carried ONCE on a host that holds
    both members, else every member's face is OPEN. pair: {"pair": [a, b], "D_m", "length_m": [lo, hi]}."""
    a, b = pair["pair"]
    ha, hb = hosts_of.get(a), hosts_of.get(b)
    if ha is not None and ha == hb:
        D = _m(pair["D_m"], f"pair {a}+{b} D", D_MAX)
        lo, hi = (_m(x, f"pair {a}+{b} L", L_MAX) for x in pair["length_m"])
        if lo > hi + TOL:
            raise RuleError(f"pair {a}+{b}: inverted length interval")
        return {ha: [{"opening_id": f"{a}+{b}", "face_m2": [_r(D * lo), _r(D * hi)], "open": False, "legacy": False,
                      "why": "pair bound carried once on its single host"}]}
    out = {}
    for x, h in ((a, ha), (b, hb)):
        if h is not None:
            out.setdefault(h, []).append({"opening_id": x, "face_m2": [0.0, None], "open": True, "legacy": False,
                                          "why": "pair split over two hosts: the per-lintel split is a designer item"})
    return out


# ------------------------------------------------------------------------------------------------ (2)-(3) base
def material_base(net_m2, faces):
    """contract net + faces -> {"state": EXACT | RANGE | HELD, "base_m2": [lo, hi] (lo None when HELD), ...}."""
    net = _m(net_m2, "host net", 1e5)
    ids = [f["opening_id"] for f in faces]
    if len(set(ids)) != len(ids):
        raise RuleError("a lintel face is named twice on one host")
    s_lo = sum(f["face_m2"][0] for f in faces)
    if s_lo > net + FACE_TOL:
        raise RuleError(f"lintel faces (low ends {_r(s_lo)} m2) exceed the host net {net} m2")
    hi_base = max(net - s_lo, 0.0)
    if any(f["open"] for f in faces):
        return {"state": "HELD", "base_m2": [None, _r(hi_base)], "contract_net_m2": net,
                "face_sum_m2": [_r(s_lo), None], "faces": faces,
                "why": "an open lintel face: the material is HELD blank by name, its upper end beside (AT_MOST)"}
    rng_hi = sum(f["face_m2"][1] for f in faces if not f["legacy"])
    leg_hi = sum(f["face_m2"][1] for f in faces if f["legacy"])
    if net - rng_hi < -FACE_TOL:
        raise RuleError(f"lintel faces (high ends {_r(rng_hi)} m2) exceed the host net {net} m2")
    lo_base = max(net - rng_hi - leg_hi, 0.0)     # the legacy 0 .. max part is clipped at 0 as R-T498-1 did
    state = "EXACT" if abs(hi_base - lo_base) <= TOL else "RANGE"
    return {"state": state, "base_m2": [_r(lo_base), _r(hi_base)], "contract_net_m2": net,
            "face_sum_m2": [_r(s_lo), _r(rng_hi + leg_hi)], "faces": faces,
            "why": "material base = [net - sum face_hi, net - sum face_lo] (R-T498-2 (2))"}


# ------------------------------------------------------------------------------------------------ (4) materials
def material_line(base, rate, unit, *, n=6):
    """base interval x owner rate -> a valued, ranged or HELD-blank material figure (never 0 for HELD)."""
    k = _m(rate, "rate", 1e3)
    lo, hi = base["base_m2"]
    if base["state"] == "HELD":
        return {"state": "HELD", "value": None, "range": None, "unit": unit,
                "at_most_beside": _r(hi * k, n), "why": base["why"]}
    if base["state"] == "EXACT":
        return {"state": "VALUED", "value": _r(hi * k, n), "range": None, "unit": unit}
    return {"state": "BOUNDED_EXPOSURE", "value": None, "range": [_r(lo * k, n), _r(hi * k, n)], "unit": unit}


def joint_m3_per_m2(t, unit_m, module_m):
    """the R-T498-1 joint volume per m2 of wall face (T-367 geometry), restated for the fixture."""
    return t * (1.0 - (unit_m[0] * unit_m[1]) / (module_m[0] * module_m[1]))


# ------------------------------------------------------------------------------------------------ (5) purchase
def _t523():
    p = ROOT / "research" / "agents_t523" / "t523_binding_map_v2.py"
    spec = importlib.util.spec_from_file_location("t523_binding_map_v2_for_t537", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def group_to_buy(group, lines, pack, *, loss_state="HELD"):
    """material lines (kg / pcs) of one purchasing group -> R-T523-1 record (the merged function, not a copy) plus the
    R-T498-2 (5) reading: DETERMINATE when both ceilings agree, RANGE otherwise; HELD while a member / loss is HELD."""
    m523 = _t523()
    mem = []
    for i, ln in enumerate(lines):
        if ln.get("rounded"):
            raise RuleError(f"{group}: member {i} arrives already rounded (round once per purchasing group)")
        if ln["state"] == "HELD":
            mem.append(m523.member(f"m{i}", installed=None))
        elif ln["state"] == "VALUED":
            mem.append(m523.member(f"m{i}", installed=(ln["value"], ln["value"]), loss_state=loss_state))
        else:
            mem.append(m523.member(f"m{i}", installed=tuple(ln["range"]), loss_state=loss_state))
    g = m523.group_purchase(group, mem, pack)
    tb = g.get("to_buy") or g.get("to_buy_at_least")
    if g["status"] == "COMPUTED":
        g["reading"] = "DETERMINATE" if tb[0] == tb[1] else "RANGE (by name; the high ceiling is not 'the' figure)"
    else:
        g["reading"] = "HELD (AT_LEAST known part; a member or the loss is HELD)"
    g["rule"] = f"{RULE_ID} (5) on R-T523-1"
    return g
