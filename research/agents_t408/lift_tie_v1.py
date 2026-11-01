"""LIFT_TIE_BIND_V1 (T-408, research, unwired, stdlib only): the lift TIE BEAM required by a note on storey height, the
ring beams on the shaft band and the slab over the shaft (top of shaft), each bound to ONE candidate line or named
MISSING; the pit-wall line checked for every fact its height depends on. Any villa; the development villa is one input
(t408_alsenan.py). Builds on LIFT_STRUCTURE_V1 (T-401 MERGED 23f948bb): its ring_geometry() is reused unchanged.

Physical element (ERS s.2.1). A lift tie beam is a reinforced-concrete beam between the lift columns at a printed height
in every storey whose F.F.L. -> F.F.L. height exceeds a printed limit (development set: ST p.8 note 19, 3.00 m when the
storey exceeds 4.30 m). It braces the columns and carries the shaft wall above it. Its geometries are separate (ERS s.3):
  concrete  clear runs between the faces of THAT storey's lift columns x b x d (the columns own the joints, T-394 ruling);
  formwork  two side faces (shaft face, outer face) per run x d, and the soffit per run x b (top face cast against nothing:
            no form; ends against the columns: no form);
  rebar     only from a bar detail of this member; none printed -> HELD, never a rate;
  masonry   the shaft wall of that storey loses run x d of block face where the tie beam passes.

Rules (R-T408-1 .. 6, proposed, every villa; provenance T-408 on the development set; adopting them is a new rule
version):
  R-T408-1  the tie-beam length is measured on the column outlines of the storey that carries it (not the pit ring
            plan); an outline missing at that storey leaves the length HELD (COLUMN_OUTLINE_MISSING).
  R-T408-2  the length is the clear runs between column faces; a length through the columns (centre line or gross ring
            perimeter) is refused (TIE_THROUGH_COLUMNS); a tie line equal to a column line is refused
            (TIE_IN_COLUMN_LINE).
  R-T408-3  the section comes only from a print of THIS member (its own section, schedule row or note); a section of
            another beam (neighbour mark, ring beam, ground beam), a default or the freelancer is refused
            (SECTION_BORROWED); none printed -> concrete, formwork and masonry displacement HELD (None, never 0) with
            the length beside.
  R-T408-4  the tie beam and the floor ring beam above share one plan band: they are separate members only while the
            tie top (level + d) stays below the ring-beam soffit; a clash is refused (TIE_IN_RING_BEAM); an unprinted
            slab level or section leaves the check OPEN by name (never assumed clear).
  R-T408-5  a column-section alternative (D-63 type CONFLICT) changes the tie length only by what it moves along the
            ring or into the shaft; growth across the ring outwards leaves the runs unchanged; growth into the drawn
            shaft clear is refused (SHAFT_CLEAR_REDUCED).
  R-T408-6  a candidate line keeps its binding only when its id, item code, state and value match the verified binding
            (version to version); a changed value, state or code is a FINDING, never re-bound silently
            (BINDING_DRIFT); a held line names every fact its value depends on (ERS lesson 2026-10-31, T-401).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agents_t401"))
import lift_structure_v1 as L1  # noqa: E402

METHOD_ID = "LIFT_TIE_BIND_V1"
Refused = L1.Refused
DC, HELD, MISSING, LISTED, OPEN = "DRAWING-CONFIRMED", "HELD", "MISSING", "LISTED", "OPEN"
OWN_PRINT = "PRINTED_FOR_THIS_MEMBER"
TOL = L1.TOL
_r = L1._r


def storey_runs(ring_outer, shaft, columns, unit):
    """R-T408-1 / -5: clear runs (m) between the faces of the storey's own column outlines on the ring band."""
    s = L1.scale(unit)
    if not columns:
        raise Refused("COLUMN_OUTLINE_MISSING", "no column outline at this storey")
    outer, inner = L1.rect(ring_outer, s), L1.rect(shaft, s)
    cols = []
    for c in columns:
        if c is None:
            raise Refused("COLUMN_OUTLINE_MISSING", "an outline is missing at this storey")
        r = L1.rect(c, s)
        if L1.iarea(r, inner) > TOL:
            raise Refused("SHAFT_CLEAR_REDUCED", repr(c))
        cols.append(r)
    g = L1.ring_geometry(outer, inner, cols)
    return {"runs_m": {k: _r(v) for k, v in g["runs_m"].items()}, "run_total_m": _r(g["run_total_m"]),
            "band_m": {k: _r(v) for k, v in g["thickness_m"].items()}}


def _section(sec):
    """R-T408-3: a section is used only when printed for this member."""
    if sec is None:
        return None
    if sec.get("source") != OWN_PRINT:
        raise Refused("SECTION_BORROWED", repr(sec.get("source")))
    if not sec.get("ref"):
        raise Refused("SECTION_BORROWED", "no sheet reference")
    b, d = float(sec["b"]), float(sec["d"])
    if b <= 0 or d <= 0:
        raise Refused("SECTION_NOT_POSITIVE", repr((b, d)))
    return b, d


def clash_check(tie_level_m, d, ring_beam_top_m, ring_beam_depth_m):
    """R-T408-4: returns ('CLEAR', gap) / ('OPEN', missing facts); refuses a clash."""
    missing = []
    if d is None:
        missing.append("tie-beam section (b x d)")
    if ring_beam_top_m is None:
        missing.append("structural top level of the floor slab / ring beam above")
    if ring_beam_depth_m is None:
        missing.append("ring-beam depth")
    if missing:
        return OPEN, missing
    soffit = ring_beam_top_m - ring_beam_depth_m
    gap = soffit - (tie_level_m + d)
    if gap < -TOL:
        raise Refused("TIE_IN_RING_BEAM", f"tie top {tie_level_m + d:.3f} above ring soffit {soffit:.3f}")
    return "CLEAR", _r(gap)


def tie_beam(storey, tie_rule, geometry, section=None, line_id=None, column_line_ids=(), claimed_length_m=None,
             ring_above=None):
    """One storey's tie beam and its dependent items. storey {name, ffl, next_ffl}; tie_rule {limit, level, ref};
    geometry = storey_runs(...); section {b, d, source, ref} or None; ring_above {top, depth} (m, None if unprinted)."""
    hgt = storey["next_ffl"] - storey["ffl"]
    if not tie_rule or hgt <= tie_rule["limit"] + TOL:
        return {"storey": storey["name"], "required": False, "storey_height_m": _r(hgt), "components": []}
    if line_id is not None and line_id in set(column_line_ids):
        raise Refused("TIE_IN_COLUMN_LINE", line_id)
    L = geometry["run_total_m"]
    if claimed_length_m is not None and abs(claimed_length_m - L) > 1e-4:
        raise Refused("TIE_THROUGH_COLUMNS" if claimed_length_m > L else "TIE_LENGTH_SHORT",
                      f"claimed {claimed_length_m:.3f} vs clear runs {L:.3f}")
    bd = _section(section)
    level = storey["ffl"] + tie_rule["level"]
    ra = ring_above or {}
    state, info = clash_check(level, bd[1] if bd else None, ra.get("top"), ra.get("depth"))
    name = storey["name"]
    note = f"length {L:.3f} m DRAWING-CONFIRMED ({tie_rule.get('ref', 'note')}; storey {hgt:.2f} > {tie_rule['limit']:.2f})"
    comps = []

    def add(cid, comp, owner, unit, value_if_known, held_fact):
        if bd is None:
            st, val, miss = (HELD if line_id else MISSING), None, [held_fact]
        elif line_id:
            st, val, miss = DC, value_if_known(*bd), []
        else:
            st, val, miss = MISSING, None, [f"no candidate line (value {value_if_known(*bd):.6f} {unit} ready)"]
        comps.append({"id": cid, "component": comp, "owner_trade": owner, "unit": unit, "value": _r(val),
                      "status": st, "missing": miss, "length_m": L, "note": note})

    sec_fact = "tie-beam section (b x d), printed nowhere"
    add(f"TIE_BEAM:{name}", f"lift tie beam concrete at +{tie_rule['level']:.2f} ({name})", "STRUCTURE", "m3",
        lambda b, d: L * b * d, sec_fact)
    add(f"TIE_BEAM:{name}:FORM_SIDES", "tie-beam side forms (shaft face + outer face)", "FORMWORK", "m2",
        lambda b, d: 2 * L * d, sec_fact)
    add(f"TIE_BEAM:{name}:FORM_SOFFIT", "tie-beam soffit form", "FORMWORK", "m2", lambda b, d: L * b, sec_fact)
    add(f"TIE_BEAM:{name}:BLOCK_DISPLACED", "shaft block face displaced by the tie beam", "BLOCKWORK", "m2",
        lambda b, d: L * d, sec_fact)
    comps.append({"id": f"TIE_BEAM:{name}:REBAR", "component": "tie-beam bars", "owner_trade": "STRUCTURE",
                  "unit": "kg", "value": None, "status": HELD if line_id else MISSING,
                  "missing": ["bar detail of the tie beam (no schedule row, no section)"], "length_m": L,
                  "note": "never a kg/m3 rate"})
    for c in comps:
        if c["status"] in (HELD, MISSING) and c["value"] is not None:
            raise Refused("HELD_WITH_VALUE", c["id"])
    return {"storey": name, "required": True, "storey_height_m": _r(hgt), "tie_level_m": _r(level),
            "clash": {"state": state, "detail": info}, "components": comps}


def bind_check(expected, lines_by_id):
    """R-T408-6: expected [{component, line_id, item_code, state, value}] vs candidate lines {id: line}."""
    rows = []
    for e in expected:
        ln = lines_by_id.get(e["line_id"])
        if ln is None:
            rows.append({**e, "result": "LINE_GONE"})
            continue
        drift = []
        if ln.get("item_code") != e["item_code"]:
            drift.append("item_code")
        if ln.get("state") != e["state"]:
            drift.append("state")
        v, w = ln.get("value"), e.get("value")
        if (v is None) != (w is None) or (v is not None and abs(float(v) - float(w)) > 1e-6):
            drift.append("value")
        rows.append({**e, "line_value": v, "line_state": ln.get("state"),
                     "result": "BOUND" if not drift else "BINDING_DRIFT:" + "/".join(drift)})
    return rows


def held_facts_check(line_text, facts):
    """R-T408-6 (second half): which of the named facts a held line's text does not name."""
    t = (line_text or "").lower()
    return [f for f, keys in facts.items() if not any(k.lower() in t for k in keys)]


def displacement_pairs(tie_comps, block_line_state):
    """The masonry deduction is carried once: on the block line when the tie is valued, else both HELD together."""
    blk = next((c for c in tie_comps if c["id"].endswith(":BLOCK_DISPLACED")), None)
    if blk is None:
        return None
    if blk["value"] is None and block_line_state not in ("HELD", "BLOCKED_RFI", "PROVISIONAL_HELD"):
        return {"result": "OPEN", "why": "block line valued while its tie-beam deduction is HELD: named, not netted"}
    return {"result": "PAIRED", "why": "tie and its block displacement held / valued together"}
