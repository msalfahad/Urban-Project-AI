"""COLUMN_END_CENSUS_V3 (R-T532-1, research rule, every villa): the masonry / column junction census read directly on
the piece kinds a run-piece ledger carries (T-274 BEAM / FACE / NONE / COLUMN / ST_COLUMN), not only on BLOCK / COLUMN.

Physical element (ERS s.2.1): the vertical block-to-concrete joint where a masonry panel meets the face of an RC column,
inside a run (the run crosses the column) or at a run end (the run stops on the column face, R-T526-1).

What a T-274 piece IS (the question of F-C-T526-1). T-274 cuts each census run (the plan centreline of a masonry wall,
MASONRY_CENTRELINE_V2) at every column outline, beam band and structural face, and names each plan stretch by what its
MID-POINT lies in (research/agents_t274/t274_geom.py, the `key = {...}` branch):
  COLUMN     inside an architectural column outline: the stretch is concrete in plan, no masonry stands there.
  ST_COLUMN  inside a structural-sheet column outline over a drawn face (no architectural column): concrete in plan.
  BEAM       inside a route G beam band drawn ABOVE the wall: the stretch is MASONRY in plan whose head meets the beam
             soffit (height = storey - beam depth, build_t274.exact_pieces; T-317 run_pieces maps it to BLOCK under
             BEAM). A beam band is a member over the wall, not a course in it: it is neither a masonry band nor a
             lintel course (lintels are measured over openings by T-453 / T-516, never as a T-274 run piece).
  FACE       inside a structural slab-plan face (SLAB, DOME_OPENING+RING, STAIR, BEAM, BEAM_OR_COLUMN): MASONRY in plan;
             its head is the slab soffit when the face is a slab with a printed thickness, HELD otherwise. A
             BEAM_OR_COLUMN face is masonry in plan only because neither drawing has a column outline over it
             (t274_geom.py tests the structural column outlines first and names ST_COLUMN when one contains it).
  NONE       inside nothing drawn above: MASONRY in plan with its head HELD (build_t274 / T-317: no printed soffit).
Any other kind (a ledger of another villa or a later version) is UNKNOWN: every boundary it takes part in is HELD by
name, never silently skipped and never counted.

Census V3 for one run: (a) an INTERIOR junction at every boundary between two consecutive pieces of roles MASONRY and
CONCRETE (any masonry kind against COLUMN / ST_COLUMN), class '<kind>-<kind>', e.g. BEAM-COLUMN; MASONRY-MASONRY (a
change of head only) and CONCRETE-CONCRETE are no junction; a boundary touching an UNKNOWN piece is HELD; (b) an END
junction at each run end that COLUMN_END_CENSUS_V2 classifies COLUMN / COLUMN_WITHIN_JOINT (the classifier is reused
unchanged) when the end piece is MASONRY; an UNKNOWN end piece there is HELD; a CONCRETE end piece with a column beyond
it is a drawing contradiction and raises (V2 behaviour); GAP_HELD / PARTIAL_COLUMN ends stay HELD by name.
V2 (research/agents_t526/end_census_v2.py) is not edited: it remains the rule for BLOCK / COLUMN piece lists.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agents_t526"))
import end_census_v2 as V2  # noqa: E402

EndCensusError = V2.EndCensusError
classify_end = V2.classify_end
EndResult = V2.EndResult

MASONRY, CONCRETE, UNKNOWN = "MASONRY", "CONCRETE", "UNKNOWN"

# kind -> (role in plan, head of the masonry stretch, source of the mapping)
KIND_MAP = {
    "BLOCK": (MASONRY, "as the ledger states", "end_census_v2 / T-317 / T-355 piece kind (merged)"),
    "COLUMN": (CONCRETE, "-", "t274_geom.py: mid-point inside an architectural column outline (acols)"),
    "ST_COLUMN": (CONCRETE, "-", "t274_geom.py: mid-point inside a structural column outline (stcols), via ST_COLUMN"),
    "BEAM": (MASONRY, "beam soffit (storey - printed depth), HELD when the depth is not printed",
             "t274_geom.py: mid-point inside a route G beam band; build_t274.exact_pieces h = basis - depth; "
             "t317_alsenan.run_pieces -> BLOCK under BEAM"),
    "FACE": (MASONRY, "slab soffit when face_cls SLAB with a printed t, else HELD",
             "t274_geom.py: mid-point inside a structural slab-plan face, no band, no column outline; "
             "build_t274.exact_pieces; t317_alsenan.run_pieces -> BLOCK under SLAB / HELD"),
    "NONE": (MASONRY, "HELD (nothing with a printed soffit is drawn over it)",
             "t274_geom.py: mid-point inside no outline, band or face; build_t274 HELD height; "
             "t317_alsenan.run_pieces -> BLOCK, top None"),
}


def role(kind):
    """(role, head, source) of one piece kind; an unmapped kind is UNKNOWN (HELD), never guessed."""
    if not isinstance(kind, str) or not kind:
        raise EndCensusError("a piece without a kind cannot be placed in the census")
    return KIND_MAP.get(kind, (UNKNOWN, "-", f"kind {kind!r} has no mapping: HELD by name"))


def end_junctions_v3(run_id, kinds, end_results, lengths=None):
    """V3 junction list for one run whose pieces carry `kinds` in run order (end 0 first)."""
    if not kinds:
        raise EndCensusError(f"{run_id}: a run with no pieces")
    if len(end_results) != 2:
        raise EndCensusError(f"{run_id}: two end results are required (end 0, end 1)")
    roles = [role(k)[0] for k in kinds]
    out = []
    for i in range(len(kinds) - 1):
        a, b = roles[i], roles[i + 1]
        cls = f"{kinds[i]}-{kinds[i + 1]}"
        at = f"piece {i}/{i + 1}"
        if UNKNOWN in (a, b):
            out.append({"run": run_id, "at": at, "source": "V3_INTERIOR", "state": "HELD", "class": cls,
                        "held": f"piece kind {kinds[i] if a == UNKNOWN else kinds[i + 1]!r} not mapped: "
                                "masonry / concrete not established"})
        elif {a, b} == {MASONRY, CONCRETE}:
            col = i + 1 if b == CONCRETE else i
            out.append({"run": run_id, "at": at, "source": "V3_INTERIOR", "state": "LISTED", "class": cls,
                        "column_piece": col, "face": "column_start" if col == i + 1 else "column_end"})
    for end, r in enumerate(end_results):
        idx = 0 if end == 0 else len(kinds) - 1
        inner, rl = kinds[idx], roles[idx]
        if r.cls in ("COLUMN", "COLUMN_WITHIN_JOINT"):
            if rl == CONCRETE:
                raise EndCensusError(f"{run_id} end {end}: a column beyond the end but the end piece is {inner}")
            if rl == UNKNOWN:
                out.append({"run": run_id, "at": f"end {end}", "source": "V3_END", "state": "HELD",
                            "class": f"{inner}-END_COLUMN", "gap_m": r.gap_m,
                            "held": f"end piece kind {inner!r} not mapped: masonry / concrete not established"})
                continue
            out.append({"run": run_id, "at": f"end {end}", "source": "V3_END", "state": "LISTED",
                        "class": f"{inner}-END_COLUMN", "gap_m": r.gap_m})
        elif r.cls in ("GAP_HELD", "PARTIAL_COLUMN"):
            if not r.held:
                raise EndCensusError("a held end needs its reason")
            out.append({"run": run_id, "at": f"end {end}", "source": "V3_END", "state": "HELD",
                        "class": f"{inner}-{r.cls}", "held": r.held})
        elif r.cls == "COLUMN_PIECE_IN_RUN":
            if rl != CONCRETE:
                raise EndCensusError(f"{run_id} end {end}: COLUMN_PIECE_IN_RUN but the end piece is {inner}")
        elif r.cls != "NO_COLUMN":
            raise EndCensusError(f"{run_id} end {end}: end class {r.cls!r} unknown")
    return out


def v2_on_kinds(run_id, kinds, end_results):
    """what V2 does on the same piece list: its result, or the exception text (for the before / after record)."""
    try:
        return V2.end_junctions(run_id, list(kinds), end_results), ""
    except EndCensusError as e:
        return None, str(e)
