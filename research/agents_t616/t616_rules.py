"""R-T616-1 OPENING-LIST LINTEL RESIDUAL BY OPENING (every villa; research rule, unwired; T-616).

Physical element: one lintel over each masonry opening whose head lies below the structural member above it, resting
on built masonry at both ends (owner lintel rule 2026-11-02: stock 1.20 / 1.50 / 2.50 / 3.00 / 4.00 m, 0.15 m bearing
each side, the shortest piece that fits, > 4.00 m FLAGGED). A count difference between two opening lists is closed
opening by opening, never by matching a total.

(1) PHYSICAL REQUIREMENT per opening (`requirement`), from the opening's own drawn evidence, in this order:
    host RC / glazing line                    -> NOT_APPLICABLE (no precast lintel in a concrete wall or a glazing line;
                                                 a record that still counts one is REFUSED)
    host unknown                              -> UNRESOLVED 0 .. 1
    curved on plan                            -> a straight stock piece is admissible only if its chord over the opening
                                                 plus both bearings stays inside the wall band (sagitta at the outer face
                                                 <= wall t - piece width); otherwise NO_STRAIGHT_PIECE (the head support
                                                 is a design item, HELD by name, never a stock piece, never 0)
    a structural member over the full width   -> UNRESOLVED 0 .. 1 (head at the soffit: none; head below it: one)
      and the head not printed
    door frame + a clear-height margin record -> REQUIRED 1 when (lowest soffit - door head - lintel depth - floor
                                                 build-up) >= 0, UNRESOLVED when short
    masonry both jambs + a bounded head       -> REQUIRED 1 (a door frame / leaf, an arch block or header lines
      (door frame, arch, header lines)           drawn: the opening does not reach the soffit, so masonry is carried)
    otherwise                                 -> UNRESOLVED 0 .. 1
(2) RESIDUAL BY OPENING (`close_residual`): the two lists are put in the same groups (storey x wall section the other
    list uses; an engine opening is in exactly one storey and one group: a second storey or group is REFUSED). Pairing
    order: (a) identity keys (census), (b) same width within the group, (c) nearest width within the group. Every
    admissible pairing is enumerated (equal widths and equal distances branch); the ours-only COUNT must be the same in
    all of them (else refused); the ids are reported as FIRM (ours-only in every pairing) and POSSIBLE (in some), never
    as a chosen identity. Group nr = ours-only - theirs-only - their pieces on our no-lintel openings; the groups must
    sum EXACTLY to the table difference (asserted) and a non-zero group with no named opening is REFUSED (closure by
    total alone).
(3) VERDICT: per group the ENGINE_RIGHT nr is a bound [min, max] over the admissible sets of the ours-only openings
    whose lintel is REQUIRED; the rest is UNRESOLVED (each 0 .. 1, named). An ours-only opening that takes no lintel on
    our side is refused (it cannot be in our count). Their piece on an opening that is NOT_APPLICABLE / NO_STRAIGHT_PIECE
    on our side is ENGINE_RIGHT -1 for the precast count. AT_MOST layer (our list = every masonry opening that may carry
    one): an ours-only unit is ENGINE_RIGHT on that basis when every candidate is a DRAWN opening in a masonry wall
    (both faces read); the ESTABLISHED layer is the REQUIRED bound above.
(4) An opening absent from a DEDUCTION list is not proof the other side omitted the opening: his wall runs may stop at
    its jambs (no gross, so no deduction, and no masonry above the head either). The implied lintel count from a
    deduction list is a floor of his opening list, labelled 'implied'.
Lengths are float metres from the drawing records; counts are whole pieces (nr).
"""
from __future__ import annotations

import math
from collections import Counter, OrderedDict
from itertools import combinations, product

RULE_ID = "R-T616-1"
STOCK = (1.20, 1.50, 2.50, 3.00, 4.00)
OWNER_BEARING = 0.15
WIDTH_TOL = 0.005
REQUIRED, NOT_APPLICABLE, NO_STRAIGHT_PIECE, UNRESOLVED = ("REQUIRED", "NOT_APPLICABLE", "NO_STRAIGHT_PIECE",
                                                           "UNRESOLVED")
HOSTS = ("MASONRY", "RC", "GLAZING", "UNKNOWN")
HEADS = ("DOOR_FRAME", "ARCH_DRAWN", "HEADER_LINES", "NONE")
BEAMS = ("NONE", "FULL_WIDTH", "UNKNOWN")
ENGINE_RIGHT = "ENGINE_RIGHT"


class ResidualError(ValueError):
    pass


def _pos(x, what, hi=12.0):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x:
        raise ResidualError(f"{what}: {x!r} is not a number")
    if x <= 0:
        raise ResidualError(f"{what}: {x!r} is not positive (held is never 0)")
    if x > hi:
        raise ResidualError(f"{what}: {x} m is above {hi} m (mm / cm refused)")
    return float(x)


def stock_piece(width_m, bearing_m=OWNER_BEARING):
    """owner rule: shortest stock >= w + 2 b; None = FLAGGED (> 4.00 m)."""
    need = _pos(width_m, "opening width") + 2 * bearing_m
    for L in STOCK:
        if L + 1e-9 >= need:
            return L
    return None


def sagitta(r_out_m, arc_m, bearing_m=OWNER_BEARING):
    """the outer-face sagitta of the straight chord over an opening of outer arc length arc_m plus both bearings."""
    r = _pos(r_out_m, "outer radius", hi=1000.0)
    a = _pos(arc_m, "opening arc") + 2 * bearing_m
    theta = a / r
    if theta >= math.pi:
        return float("inf")
    return r * (1.0 - math.cos(theta / 2.0))


def requirement(op):
    """op: {'id', 'host' (HOSTS), 'head' (HEADS), 'beam_over' (BEAMS), optional 'curved': {'r_out_m', 'arc_m',
    'wall_t_m', 'piece_w_m'}, optional 'claimed_count'} -> {'decision', 'lo', 'hi', 'why'}."""
    oid = op.get("id")
    host, head, beam = op.get("host"), op.get("head"), op.get("beam_over")
    for v, allowed, what in ((host, HOSTS, "host"), (head, HEADS, "head"), (beam, BEAMS, "beam_over")):
        if v not in allowed:
            raise ResidualError(f"{oid}: {what} {v!r} unknown (one of {allowed})")
    claimed = op.get("claimed_count")
    if host in ("RC", "GLAZING"):
        if claimed:
            raise ResidualError(f"{oid}: a precast lintel counted in a {host} host is refused (no masonry to carry)")
        return {"decision": NOT_APPLICABLE, "lo": 0, "hi": 0, "why": f"host {host}: no precast lintel"}
    cv = op.get("curved")
    if cv:
        for k in ("r_out_m", "arc_m", "wall_t_m", "piece_w_m"):
            if cv.get(k) is None:
                return {"decision": UNRESOLVED, "lo": 0, "hi": 1, "why": f"curved on plan: {k} not established"}
        s = sagitta(cv["r_out_m"], cv["arc_m"])
        room = _pos(cv["wall_t_m"], "wall t", 1.0) - _pos(cv["piece_w_m"], "piece width", 1.0)
        if s > room + 1e-9:
            if claimed:
                raise ResidualError(f"{oid}: a straight stock lintel in a curved wall refused (sagitta {s:.3f} m > "
                                    f"{room:.3f} m of the band)")
            return {"decision": NO_STRAIGHT_PIECE, "lo": 0, "hi": 0, "sagitta_m": round(s, 4),
                    "why": f"curved on plan: chord sagitta {s:.3f} m > band room {room:.3f} m; head support is a design "
                           f"item (HELD by name), never a stock piece"}
    if host == "UNKNOWN":
        return {"decision": UNRESOLVED, "lo": 0, "hi": 1, "why": "host material not established"}
    cm = op.get("clear_margin_m")
    if head == "DOOR_FRAME" and cm is not None:
        if not isinstance(cm, (int, float)) or isinstance(cm, bool):
            raise ResidualError(f"{oid}: clear margin {cm!r} is not a number")
        if cm >= 0:
            return {"decision": REQUIRED, "lo": 1, "hi": 1,
                    "why": f"door head below the lowest soffit with {cm:.2f} m to spare after the lintel depth"}
        return {"decision": UNRESOLVED, "lo": 0, "hi": 1, "why": f"door head clearance short by {-cm:.2f} m"}
    if beam == "FULL_WIDTH" and head != "DOOR_FRAME":
        return {"decision": UNRESOLVED, "lo": 0, "hi": 1,
                "why": "a structural member over the full width, head not printed: at its soffit 0, below it 1"}
    if beam == "FULL_WIDTH":
        return {"decision": UNRESOLVED, "lo": 0, "hi": 1,
                "why": "door head under a full-width member: masonry between head and soffit not established"}
    if head in ("DOOR_FRAME", "ARCH_DRAWN", "HEADER_LINES") and beam == "NONE":
        return {"decision": REQUIRED, "lo": 1, "hi": 1, "why": f"masonry host, bounded head ({head}), no member over it"}
    return {"decision": UNRESOLVED, "lo": 0, "hi": 1, "why": f"head {head} / member over it {beam}: not established"}


# ------------------------------------------------------------------------------------------------ residual
MAX_BRANCHES = 20000


def _check_ours(ours):
    seen = {}
    for o in ours:
        oid = o.get("id")
        if not oid:
            raise ResidualError("an opening without an id")
        key = (o.get("storey"), o.get("group"))
        if oid in seen:
            if seen[oid] != key:
                raise ResidualError(f"{oid}: counted in two storeys / groups {seen[oid]} and {key} (refused)")
            raise ResidualError(f"{oid}: listed twice")
        seen[oid] = key
        if o.get("counts") not in (0, 1):
            raise ResidualError(f"{oid}: counts must be 1 (in our lintel list) or 0 (opening carried, no lintel)")
        if o["counts"] == 1:
            _pos(o.get("width_m"), f"{oid} width")


def _group_sets(name, ours_c, their_w):
    """all admissible ours-only sets of one group under steps (b) same width, (c) nearest width (ties branch)."""
    by_w = OrderedDict()
    for o in ours_c:
        by_w.setdefault(round(o["width_m"], 3), []).append(o["id"])
    tw = Counter(round(w, 3) for w in their_w)
    fixed_choices = []          # per width class: the ways to choose which ids stay unpaired after step (b)
    rest_t = []
    for w in sorted(set(by_w) | set(tw)):
        ids, n = by_w.get(w, []), tw.get(w, 0)
        m = min(n, len(ids))
        rest_t += [w] * (n - m)
        fixed_choices.append([tuple(c) for c in combinations(ids, len(ids) - m)])
    width = {o["id"]: round(o["width_m"], 3) for o in ours_c}
    out, n_br = set(), 0
    for combo in product(*fixed_choices):
        pool = [i for part in combo for i in part]
        branches = [(tuple(pool), 0)]
        for wt in sorted(rest_t):
            nxt = []
            for left, th_only in branches:
                if not left:
                    nxt.append((left, th_only + 1))
                    continue
                d = {i: abs(width[i] - wt) for i in left}
                dmin = min(d.values())
                for i in left:
                    if d[i] - dmin <= WIDTH_TOL:
                        nxt.append((tuple(x for x in left if x != i), th_only))
            branches = nxt
            n_br += len(branches)
            if n_br > MAX_BRANCHES:
                raise ResidualError(f"{name}: more than {MAX_BRANCHES} pairing branches (split the group)")
        for left, th_only in branches:
            out.add((frozenset(left), th_only))
    return out


def close_residual(ours, theirs, keys=None):
    """ours: [{'id', 'storey', 'group', 'width_m', 'counts' (1 in our lintel list / 0 carried without one)}];
    theirs: [{'group', 'widths': [...]}] (each width one deducted opening = one implied lintel);
    keys: {our id: (group, their width)} identity evidence (census keys), used first.
    -> per group the admissible ours-only sets, the firm / possible ids, and the nr closure (asserted)."""
    _check_ours(ours)
    keys = dict(keys or {})
    groups = OrderedDict()
    for o in ours:
        groups.setdefault(o["group"], {"ours": [], "theirs": None})["ours"].append(o)
    for g in theirs:
        G = groups.setdefault(g["group"], {"ours": [], "theirs": None})
        if G["theirs"] is not None:
            raise ResidualError(f"their group {g['group']} given twice")
        G["theirs"] = [_pos(w, f"their {g['group']} width") for w in g["widths"]]
    res, total = [], 0
    for name, G in groups.items():
        left_t = list(G["theirs"] or [])
        keyed, no_lintel_paired = [], []
        rest = []
        for o in G["ours"]:
            k = keys.get(o["id"])
            if not k:
                rest.append(o)
                continue
            if k[0] != name:
                raise ResidualError(f"{o['id']}: key group {k[0]} is not its group {name}")
            hit = next((i for i, w in enumerate(left_t) if abs(w - k[1]) <= WIDTH_TOL), None)
            if hit is None:
                raise ResidualError(f"{o['id']}: keyed to their {k[1]} m in {name}, which is not in their list")
            w = left_t.pop(hit)
            keyed.append({"ours": o["id"], "theirs_w": w})
            if o["counts"] == 0:
                no_lintel_paired.append({"ours": o["id"], "theirs_w": w})
        ours_c = [o for o in rest if o["counts"] == 1]
        unpaired_zero = [o["id"] for o in rest if o["counts"] == 0]
        sets = _group_sets(name, ours_c, left_t)
        ks = {len(s) for s, _ in sets}
        ts = {t for _, t in sets}
        if len(ks) != 1 or len(ts) != 1:
            raise ResidualError(f"{name}: the ours-only count is not unique across pairings ({ks}, {ts})")
        k, t_only = ks.pop(), ts.pop()
        all_sets = [s for s, _ in sets]
        firm = sorted(frozenset.intersection(*all_sets)) if all_sets else []
        poss = sorted(frozenset.union(*all_sets) - set(firm)) if all_sets else []
        nr = k - t_only - len(no_lintel_paired)
        total += nr
        res.append({"group": name, "ours_counted": len(ours_c) + sum(1 for x in keyed if x["ours"] not in
                    {z["ours"] for z in no_lintel_paired}), "theirs_n": len(G["theirs"] or []), "keyed": keyed,
                    "ours_only_k": k, "ours_only_firm": firm, "ours_only_possible": poss,
                    "admissible_sets": sorted(sorted(s) for s in all_sets), "theirs_only": t_only,
                    "paired_no_lintel_ours": no_lintel_paired, "carried_no_lintel_unpaired": unpaired_zero,
                    "nr": nr})
    ours_nr = sum(o["counts"] for o in ours)
    theirs_nr = sum(len(g["widths"]) for g in theirs)
    diff = ours_nr - theirs_nr
    if total != diff:
        raise ResidualError(f"groups close to {total} nr, the table difference is {diff} nr: not closed")
    for g in res:
        if g["nr"] and not (g["ours_only_firm"] or g["ours_only_possible"] or g["paired_no_lintel_ours"]
                            or g["theirs_only"]):
            raise ResidualError(f"{g['group']}: {g['nr']} nr with no named opening (closure by total refused)")
    return {"rule": RULE_ID, "groups": res, "ours_nr": ours_nr, "theirs_nr": theirs_nr, "difference_nr": diff,
            "closure_nr": total}


def verdicts(closed, req, drawn=None):
    """R-T616-1 (3): per group, ENGINE_RIGHT nr as a bound over the admissible sets (an ours-only opening whose lintel
    is REQUIRED), the rest UNRESOLVED (0 .. 1 each, named); a theirs piece on an opening that takes none on our side
    (NOT_APPLICABLE / NO_STRAIGHT_PIECE) is ENGINE_RIGHT -1; their unmatched units UNRESOLVED."""
    rows = []
    for g in closed["groups"]:
        er = []
        for s in g["admissible_sets"]:
            ds = [req[i]["decision"] for i in s]
            bad = [i for i in s if req[i]["decision"] not in (REQUIRED, UNRESOLVED)]
            if bad:
                raise ResidualError(f"{g['group']}: ours-only opening(s) {bad} take no lintel on our side")
            er.append(sum(1 for d in ds if d == REQUIRED))
        lo, hi = (min(er), max(er)) if er else (0, 0)
        cand = set(g["ours_only_firm"]) | set(g["ours_only_possible"])
        if drawn is None:
            at_most = None
        else:
            missing = sorted(cand - set(drawn))
            at_most = ENGINE_RIGHT if not missing else {"UNRESOLVED": missing}
        neg = []
        for p in g["paired_no_lintel_ours"]:
            d = req[p["ours"]]["decision"]
            neg.append({"ours": p["ours"], "verdict": ENGINE_RIGHT if d in (NOT_APPLICABLE, NO_STRAIGHT_PIECE)
                        else UNRESOLVED, "decision": d})
        rows.append({"group": g["group"], "ours_only_k": g["ours_only_k"], "at_most_verdict": at_most,
                     "engine_right_nr": [lo, hi],
                     "unresolved_nr": [g["ours_only_k"] - hi, g["ours_only_k"] - lo],
                     "their_piece_on_no_lintel": neg, "theirs_only_unresolved": g["theirs_only"]})
    return rows
