"""T-404 FENCE_FINISH_V1: finishes of a plot boundary fence, face by face (research rules, stdlib only).

Not wired into any method. Every villa; provenance T-404 (built on merged T-396 BOUNDARY_FENCE_V1 runs / heights,
T-361 gates, T-263 buried coating, T-305 / T-337 house facade ledger; owner Q-63 C, Q-65 C, OWNER_NOTES_SIGMA item 3;
method rules URBAN-FINISH-QUANTITY-INDEPENDENT-OF-MATERIAL@v1 and URBAN-FINISH-EXTRAS-SEPARATE-ITEMS@v1; ERS s.2 / s.3).

Physical element: a boundary fence wall has, per run, an OUTSIDE face (street / neighbour / sea), a PLOT face, free
stop-ends (a jamb end at a gate where the fence stops), and a TOP; finish layers (plaster, Sigma / paint, a coping, a
coating below N.G.) are bound to those faces. Kept apart:

  * the PHYSICAL FACE above N.G. (length x printed wall height, gates deducted by id): geometry, DRAWING-CONFIRMED when
    its inputs are;
  * the FINISHABLE (exposed) part of a face, from the finished ground of THAT side to the top: a printed finished level
    gives it, an unprinted ground keeps it HELD within bounds;
  * each finish LAYER on a face: exists as a quantity only by a printed note / detail of the fence or an owner rule
    that names site walls; otherwise HELD with AT_MOST = the face, never 0, never the house facade finish by default.

Rules (R-T404-n, proposed; a rule change is a new version, never an edit in place):
  R-T404-1  face census: each run gives an OUTSIDE face and a PLOT face (own keys, each counted once), its free stop-ends
            and its top. At an external corner the outside faces of both runs run to the corner point (outside length =
            the outer band line); the plot faces stop at the internal corner (plot length = outside length - t per
            corner). One length x 2 for 'both sides' is refused: the two faces differ by t per corner.
  R-T404-2  gates by id: face gross = face length including the gate x height; each gate is deducted at full height
            from both faces when no wall is drawn over it; a gate wider than its face is refused. A stop-end face
            (t x height) is added only where the fence itself ends at the jamb; a jamb formed by another element's
            wall (the house) belongs to that element's face ledger.
  R-T404-3  heights: the physical face height is the printed wall height above N.G. (R-T396-2). The finishable height of
            a side runs from that side's finished ground: a PRINTED finished level drawn against the fence gives the
            lower bound top - level; where it is not shown along the whole run, the finishable area is HELD between
            that bound and the physical face; an unprinted outside ground gives AT_MOST = the physical face only.
  R-T404-4  profile: a top profile drawn but not dimensioned (a dip, a rounded end) keeps the face net HELD at most the
            rectangle, and the top's developed length HELD at least its plan length; the plan length is never the value.
  R-T404-5  layer authority: plaster, Sigma / paint, coping, coating below N.G. on a site wall are quantities only by a
            printed note / detail of the fence or an owner rule that names site walls; the house facade method (exterior
            plaster + Sigma, OWNER_NOTES_SIGMA) is not carried to the fence by default; an element drawn on no sheet (a
            coping) is NOT_DRAWN, named, with no quantity; a held layer is never 0.
  R-T404-6  freelancer rows are mapped to faces by length before any comparison, and the difference is closed in m2 to
            named causes (height, length, extra rows, scope) with the residual stated.
"""

from __future__ import annotations

DC = "DRAWING-CONFIRMED"
HELD = "HELD"
NOT_DRAWN = "NOT_DRAWN"
SIDES = ("OUTSIDE", "PLOT")
LAYERS = ("PLASTER", "SIGMA_PAINT")


class FinishError(ValueError):
    pass


def _num(x, what, zero_ok=False):
    if x is None:
        raise FinishError(f"{what}: missing (a missing value is HELD, never 0)")
    if not isinstance(x, (int, float)) or isinstance(x, bool):
        raise FinishError(f"{what}: not a number")
    if x < 0 or (x == 0 and not zero_ok):
        raise FinishError(f"{what}: {x} not positive")
    return float(x)


def _m(x, what, unit="m", zero_ok=False):
    if unit != "m":
        raise FinishError(f"{what}: unit {unit!r} (convert to m once, at the source)")
    v = _num(x, what, zero_ok)
    if v > 200:
        raise FinishError(f"{what}: {v} m is not a plot dimension (mm passed as m?)")
    return v


def face_lengths(outer_m, t_m, corners, unit="m"):
    """R-T404-1: (outside, plot) lengths of one run whose OUTER band line is outer_m with `corners` external corners
    at its ends (0, 1 or 2) that this run's outer line runs to."""
    o = _m(outer_m, "outer length", unit)
    t = _m(t_m, "thickness", unit)
    if t > 1.0:
        raise FinishError(f"thickness {t} m: not a fence wall")
    if corners not in (0, 1, 2):
        raise FinishError("corners: 0, 1 or 2")
    plot = o - corners * t
    if plot <= 0:
        raise FinishError("plot face length not positive")
    return round(o, 6), round(plot, 6)


def physical_face(run, side, length_m, height, gates=(), profile="NONE", unit="m"):
    """R-T404-1 / -2 / -4: one face. height = {'value', 'status'} from R-T396-2; gates = [(id, width_m)];
    profile 'NONE' or 'UNDIMENSIONED'."""
    if side not in SIDES:
        raise FinishError(f"side {side!r}")
    L = _m(length_m, f"{run} {side} length", unit)
    key = f"{run}/{side}"
    if height is None or height.get("value") is None or height.get("status") != DC:
        cand = None if not height or height.get("value") is None else round(L * height["value"], 6)
        return {"key": key, "run": run, "side": side, "length_m": L, "height_m": None if not height else height.get("value"),
                "gross_m2": None, "deductions": [], "net_m2": None, "at_most_m2": None,
                "comparison_only_m2": cand, "status": HELD, "held": ["face height not printed / element HELD"]}
    h = _m(height["value"], "height", unit)
    gross = L * h
    deds = []
    seen = set()
    for gid, w in gates:
        if not gid or gid in seen:
            raise FinishError(f"gate id {gid!r} missing or repeated on {key}")
        seen.add(gid)
        w = _m(w, f"gate {gid}", unit)
        deds.append((gid, round(w * h, 6)))
    if sum(w for _, w in gates) >= L:
        raise FinishError(f"{key}: gates fill or exceed the face (a gate is inside its run)")
    net = gross - sum(d for _, d in deds)
    if profile == "UNDIMENSIONED":
        return {"key": key, "run": run, "side": side, "length_m": L, "height_m": h, "gross_m2": round(gross, 6),
                "deductions": deds, "net_m2": None, "at_most_m2": round(net, 6), "comparison_only_m2": None,
                "status": HELD, "held": ["top profile drawn, not dimensioned (R-T404-4)"]}
    if profile != "NONE":
        raise FinishError(f"profile {profile!r}")
    return {"key": key, "run": run, "side": side, "length_m": L, "height_m": h, "gross_m2": round(gross, 6),
            "deductions": deds, "net_m2": round(net, 6), "at_most_m2": None, "comparison_only_m2": None,
            "status": DC, "held": []}


def stop_end(run, jamb_id, t_m, height, own_end=True, profile="NONE", unit="m"):
    """R-T404-2: the end face of the fence at a gate jamb (t x h); refused where the jamb is another element's wall."""
    if not own_end:
        raise FinishError(f"{run} {jamb_id}: the jamb is another element's wall (its face ledger owns it)")
    t = _m(t_m, "thickness", unit)
    h = _m(height["value"], "height", unit)
    m2 = round(t * h, 6)
    key = f"{run}/END-{jamb_id}"
    if profile == "UNDIMENSIONED" or height.get("status") != DC:
        return {"key": key, "m2": None, "at_most_m2": m2, "status": HELD,
                "held": ["end top drawn lower / rounded, not dimensioned (R-T404-4)"]}
    return {"key": key, "m2": m2, "at_most_m2": None, "status": DC, "held": []}


def top(run, plan_len_m, t_m, profile="NONE", unit="m"):
    """R-T404-4: the wall top: m.l and m2. A shaped top is HELD with AT_LEAST the plan values."""
    L = _m(plan_len_m, "top plan length", unit)
    t = _m(t_m, "thickness", unit)
    if profile == "UNDIMENSIONED":
        return {"key": f"{run}/TOP", "ml": None, "m2": None, "at_least_ml": round(L, 6),
                "at_least_m2": round(L * t, 6), "status": HELD,
                "held": ["top profile drawn, not dimensioned: developed length > plan length"]}
    if profile != "NONE":
        raise FinishError(f"profile {profile!r}")
    return {"key": f"{run}/TOP", "ml": round(L, 6), "m2": round(L * t, 6), "at_least_ml": None, "at_least_m2": None,
            "status": DC, "held": []}


def finishable(face, top_above_ng_m, ground_level_m=None, along_whole_run=False):
    """R-T404-3: the exposed part of a physical face. ground_level_m = a PRINTED finished level of this side above N.G.
    (None = not printed). Returns value (only when the level is shown along the whole run and the face is DC) or a
    HELD range [lo, hi]."""
    hi = face["net_m2"] if face["net_m2"] is not None else face["at_most_m2"]
    if hi is None:
        return {"key": face["key"], "m2": None, "lo_m2": None, "hi_m2": None, "status": HELD,
                "basis": "face HELD"}
    top_h = _m(top_above_ng_m, "top above N.G.")
    if ground_level_m is None:
        return {"key": face["key"], "m2": None, "lo_m2": None, "hi_m2": hi, "status": HELD,
                "basis": "finished ground of this side not printed: at most the physical face"}
    g = _num(ground_level_m, "finished level", zero_ok=True)
    if g >= top_h:
        raise FinishError("finished level above the wall top")
    exposed_h = top_h - g
    deduct = sum(d for _, d in face["deductions"]) / top_h * exposed_h if face["deductions"] else 0.0
    lo = face["length_m"] * exposed_h - deduct
    if face["status"] == DC and along_whole_run:
        return {"key": face["key"], "m2": round(lo, 6), "lo_m2": None, "hi_m2": None, "status": DC,
                "basis": f"printed level +{g:.2f} along the run"}
    if face["status"] != DC:
        return {"key": face["key"], "m2": None, "lo_m2": None, "hi_m2": hi, "status": HELD,
                "basis": f"printed level +{g:.2f}; face profile HELD: at most the physical face"}
    return {"key": face["key"], "m2": None, "lo_m2": round(lo, 6), "hi_m2": round(hi, 6), "status": HELD,
            "basis": f"printed level +{g:.2f} drawn at the run ends only"}


def layer(face_key, layer_name, geometry_m2, authority=None, house_method=False):
    """R-T404-5: a finish layer on a site-wall face. authority = a printed note / detail of the fence or an owner rule
    naming site walls; house_method=True (the house facade finish carried over) is refused."""
    if house_method:
        raise FinishError(f"{face_key} {layer_name}: the house facade finish is not carried to the fence by default")
    if authority:
        if geometry_m2 is None:
            return {"key": face_key, "layer": layer_name, "m2": None, "at_most_m2": None, "status": HELD,
                    "authority": authority, "held": ["geometry HELD"]}
        return {"key": face_key, "layer": layer_name, "m2": geometry_m2, "at_most_m2": None, "status": DC,
                "authority": authority, "held": []}
    return {"key": face_key, "layer": layer_name, "m2": None, "at_most_m2": geometry_m2, "status": HELD,
            "authority": None, "held": ["no printed note / detail and no owner rule names this layer on a site wall"]}


def no_shared_faces(fence_keys, house_keys):
    """acceptance (c): a fence face key is never a house facade key."""
    shared = sorted(set(fence_keys) & set(house_keys))
    if shared:
        raise FinishError(f"faces in both ledgers: {shared}")
    return 0


def once(faces):
    """R-T404-1: each face key once."""
    seen = set()
    for f in faces:
        if f["key"] in seen:
            raise FinishError(f"{f['key']}: counted twice")
        seen.add(f["key"])
    return len(seen)


def totals(items, value="m2"):
    """each status separately; a HELD item adds its name and its bound, never a number to the DC total."""
    out = {"dc": 0.0, "held": [], "held_at_most": 0.0, "held_at_most_complete": True}
    for it in items:
        if it["status"] == DC:
            out["dc"] += it[value] if value in it else it["net_m2"]
        else:
            out["held"].append(it["key"])
            b = it.get("at_most_m2") if value == "m2" else None
            if b is None:
                b = it.get("hi_m2")
            if b is None:
                out["held_at_most_complete"] = False
            else:
                out["held_at_most"] += b
    out["dc"] = round(out["dc"], 6)
    out["held_at_most"] = round(out["held_at_most"], 6)
    return out


def reconcile(his_rows, own_unmatched, own_h):
    """R-T404-6: his rows [(id, n, len, h, own_len or None)] mapped to our faces of height own_h; own_unmatched =
    [(key, m2)] our faces in the compared scope that no row of his carries. Causes in m2; residual stated.
    own_len None = a row of his with no counterpart in our census (its whole m2 is a cause)."""
    for rid, n, L, h, own_len in his_rows:
        _num(n, f"{rid} count")
        _num(L, f"{rid} length")
        _num(h, f"{rid} height")
    his_total = round(sum(n * L * h for _, n, L, h, _ in his_rows), 6)
    own_total = round(sum(n * ol * own_h for _, n, _, _, ol in his_rows if ol is not None)
                      + sum(m for _, m in own_unmatched), 6)
    causes = [(k, "our face, no row of his", round(-m, 6)) for k, m in own_unmatched]
    for rid, n, L, h, own_len in his_rows:
        if own_len is None:
            causes.append((rid, "his row, no counterpart in the face census", round(n * L * h, 6)))
            continue
        causes.append((rid, f"height {h} vs {own_h}", round(n * L * (h - own_h), 6)))
        if abs(L - own_len) > 1e-9:
            causes.append((rid, f"length {L} vs {own_len}", round(n * (L - own_len) * own_h, 6)))
    explained = round(sum(c for _, _, c in causes), 6)
    return {"his_m2": his_total, "own_m2": own_total, "diff_m2": round(his_total - own_total, 6),
            "causes": causes, "residual_m2": round(his_total - own_total - explained, 6) + 0.0}
