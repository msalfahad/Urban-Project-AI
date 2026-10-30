"""T-362 (research, unwired): the masonry-accessory parts T-355 left open, every villa.

Builds on research/agents_t355/t355_masonry_accessories.py (imported, never edited): the same physical elements
(bed-joint MESH STRIP m.l at every third course, SHARMAT pcs per third course at each wall-to-column junction), the
same per-level geometry (R-T355-1 .. 7). This module adds four rules.

PHYSICAL ELEMENT (ERS s.2.1): a thin-bed AAC ("white") block wall is laid in an adhesive bed of a few millimetres,
not in a 10 mm cement-sand joint (owner 2026-10-29: the provisional 10 mm applies to mortared blocks, NOT to AAC
thin-bed). Its course module is therefore the BLOCK HEIGHT plus a thin adhesive bed; the block height is a product
property of the supplier family actually laid.

RULES (every villa; provenance in T-362_WHITE_COURSES_LINTEL_BEARINGS.md)
- R-T362-1 THIN-BED COURSE: module = supplier block height + adhesive bed. The block height comes only from a NAMED
  supplier family (source required; no default height); the adhesive bed is a band, never a mortar joint: a bed
  above 5 mm on a thin-bed course is refused. When the project's family is not established by a drawing, a
  specification or an owner answer, every candidate family is computed side by side, none is chosen, and the wall's
  quantity stays HELD (CONDITIONAL on the family) - the families are never added, averaged or picked by size.
- R-T362-2 LEVEL BAND: a level counts for a family only as far as it is the same over the bed band (adhesive
  bed_lo .. bed_hi per joint, first-course levelling bed first_lo .. first_hi above the structural floor): per level
  the certain net = the smallest net over the band corners, the rest of the band is HELD (cause LEVEL_BAND); a level
  that exists at one corner only is HELD whole. Ties per junction: certain = the smallest count, the band HELD.
- R-T362-3 LINTEL BEARING PER END: at a level the lintel occupies, each end's concrete in the wall's own run is
  min(printed minimum, masonry between the jamb and the next column, opening or run end): in every reading of the
  drawing the lintel fills at least that, so it is CUT, not held. It needs both jamb stations tied to the run's
  pieces; an opening without stations keeps T-355's hold (printed minimum x 2, capped to the block). A bearing
  longer than the printed minimum is not drawn: the strip is measured at the minimum, the length the lintel
  concrete line books (S8.6 PROJECT_BASIS_QTO: min(0.40, masonry beyond the jamb)), so the two trades partition the
  run (no gap, no double count). A bearing that runs past the run end into a crossing wall is named, not cut there.
  New rule; R-T355-2's bearing clause (bearing HELD) stays in T-355's committed outputs.
- R-T362-4 ONE JUNCTION ONE OWNER: a physical junction (column piece key with run and station, face) belongs to one
  wall; the same junction under two wall ids is refused.

Units: metres (units="mm" converts on entry, as in T-355).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t355"))
import t355_masonry_accessories as X  # noqa: E402

TOL = 1e-6
SCHEMA = "T362_MASONRY_WHITE_V1"
MAX_THIN_BED = 0.005


class WhiteError(X.AccessoryError):
    pass


@dataclass(frozen=True)
class Family:
    name: str
    block_h: float
    source: str


@dataclass(frozen=True)
class Band:
    bed_lo: float          # adhesive bed per joint, low end
    bed_hi: float          # adhesive bed per joint, high end
    first_lo: float        # first-course levelling bed under course 1, low end
    first_hi: float        # first-course levelling bed, high end
    source: str


def family(name, block_h, source, units="m"):
    h = X._m(block_h, units)
    if not source:
        raise WhiteError(f"family {name}: a block height needs its supplier source (no default AAC height)")
    if not (0.05 <= h <= 0.40):
        raise WhiteError(f"family {name}: block height {h} m outside 0.05 .. 0.40 m (units?)")
    return Family(name, h, source)


def band(bed_lo, bed_hi, first_lo, first_hi, source, units="m"):
    lo, hi, f0, f = X._m(bed_lo, units), X._m(bed_hi, units), X._m(first_lo, units), X._m(first_hi, units)
    if not source:
        raise WhiteError("an adhesive band needs its source")
    if not (0 < lo <= hi):
        raise WhiteError(f"adhesive bed band {lo} .. {hi}")
    if hi > MAX_THIN_BED + TOL:
        raise WhiteError(f"adhesive bed {hi} m on a thin-bed AAC course refused: a mortar joint is not a thin bed "
                         "(owner 2026-10-29: the 10 mm joint is for mortared blocks only)")
    if not (lo - TOL <= f0 <= f <= 0.05):
        raise WhiteError(f"first-course bed band {f0} .. {f} m (units?)")
    return Band(lo, hi, f0, f, source)


def corners(fam: Family, b: Band):
    """the band corners as (tag, course spec, uniform datum shift): LOW = thinnest adhesive and first bed, HIGH =
    thickest. T-355's course n sits on one joint, so a first bed f is that joint plus a datum shift f - joint."""
    lo = X.course_spec(fam.block_h, b.bed_lo, f"{fam.source}; adhesive {b.source}", "CONDITIONAL")
    hi = X.course_spec(fam.block_h, b.bed_hi, f"{fam.source}; adhesive {b.source}", "CONDITIONAL")
    return [("LOW", lo, round(b.first_lo - b.bed_lo, 6)), ("HIGH", hi, round(b.first_hi - b.bed_hi, 6))]


def shift_panel(p: X.Panel, d: float, course):
    """raise the course datum by d == lower every height measured from the structural floor by d."""
    if d <= TOL:
        return replace(p, course=course)
    pcs = tuple(x if x.kind != "BLOCK" or x.top is None else replace(x, top=round(x.top - d, 6)) for x in p.pieces)
    ops = tuple(replace(o, bottom=None if o.bottom is None else max(0.0, round(o.bottom - d, 6)),
                        top=None if o.top is None else round(o.top - d, 6)) for o in p.openings)
    return replace(p, pieces=pcs, openings=ops, course=course)


def end_bearing(printed_min, masonry_left, masonry_right):
    """R-T362-3: the lintel's concrete in the wall's own run at one opening = per end min(printed minimum, masonry
    between the jamb and the next column / opening / run end). Unknown masonry on an end -> None (held)."""
    if printed_min is None or printed_min <= 0:
        raise WhiteError("no printed minimum bearing: the bearing stays HELD")
    if masonry_left is None or masonry_right is None:
        return None
    if masonry_left < -TOL or masonry_right < -TOL:
        raise WhiteError(f"negative masonry beside a jamb ({masonry_left}, {masonry_right}): station outside the run")
    return round(min(printed_min, max(0.0, masonry_left)) + min(printed_min, max(0.0, masonry_right)), 6)


def with_stations(panel: X.Panel, stations: dict):
    """openings whose two jamb stations are tied to the run: the bearing pair becomes the per-end figure (stored as
    half the pair in T-355's symmetric field); the others keep the printed minimum and stay HELD."""
    ops, tied = [], set()
    for o in panel.openings:
        st = stations.get(o.oid)
        if st is not None and o.bearing is not None:
            pair = end_bearing(o.bearing, *st)
            if pair is not None:
                ops.append(replace(o, bearing=pair / 2.0))
                tied.add(o.oid)
                continue
        ops.append(o)
    return replace(panel, openings=tuple(ops)), tied


def bearing_cut(recs, tied=None):
    """R-T362-3 on T-355 level records: the LINTEL_BEARING hold of an opening whose jambs are tied to the run is
    concrete (cut, not held); tied=None treats every opening as tied (synthetic fixtures with per-end bearings)."""
    out = []
    for r in recs:
        r = dict(r)
        go = [(w.split(":")[0], L) for c, L, w in r["held"] if c == "LINTEL_BEARING"
              and (tied is None or w.split(":")[0] in tied)]
        moved = sum(L for _, L in go)
        r["bearing_ops"] = go
        if moved > TOL:
            ids = {o for o, _ in go}
            r["cut_lintel_m"] = round(r["cut_lintel_m"] + moved, 6)
            r["held_m"] = round(r["held_m"] - moved, 6)
            r["held"] = [h for h in r["held"] if not (h[0] == "LINTEL_BEARING" and h[2].split(":")[0] in ids)]
        r["bearing_cut_m"] = round(moved, 6)
        out.append(r)
    return out


def white_levels(panel: X.Panel, fam: Family, b: Band, tied=None):
    """R-T362-1 / 2 / 3: per level of one wall under one family: certain net, band-held, other holds."""
    runs, dd = {}, {}
    state = None
    for tag, spec, d in corners(fam, b):
        recs, st = X.mesh_levels(shift_panel(panel, d, spec))
        runs[tag] = {r["k"]: r for r in bearing_cut(recs, tied)}
        dd[tag] = d
        state = st if state is None or st.startswith("HELD") else state
    if state and state.startswith("HELD"):
        return [], state
    ks = sorted(set(runs["LOW"]) | set(runs["HIGH"]))
    out = []
    for k in ks:
        a, c = runs["LOW"].get(k), runs["HIGH"].get(k)
        zlo = round(a["level_m"] + dd["LOW"], 6) if a else None
        zhi = round(c["level_m"] + dd["HIGH"], 6) if c else None
        base = a or c
        if a is None or c is None:
            out.append({**base, "family": fam.name, "level_lo_m": zlo, "level_hi_m": zhi, "level_m": zlo or zhi,
                        "net_m": 0.0, "certain_net_m": 0.0, "band_held_m": round(base["net_m"], 6),
                        "band": "LEVEL EXISTS AT ONE BAND CORNER ONLY"})
            continue
        lo_net = min(a["net_m"], c["net_m"])
        hi_net = max(a["net_m"], c["net_m"])
        rr = dict(a)
        rr.update(family=fam.name, level_lo_m=zlo, level_hi_m=zhi, level_m=zlo, certain_net_m=round(lo_net, 6),
                  band_held_m=round(hi_net - lo_net, 6), net_m=round(lo_net, 6),
                  held_m=round(max(a["held_m"], c["held_m"]), 6),
                  band="STABLE" if hi_net - lo_net <= TOL else "NET DIFFERS OVER THE BAND")
        out.append(rr)
    return out, "MEASURED" if out else "NO LEVEL (wall lower than three courses)"


def white_ties(panel: X.Panel, fam: Family, b: Band):
    per = {}
    for tag, spec, d in corners(fam, b):
        for t in X.ties(shift_panel(panel, d, spec)):
            per.setdefault((t["column_at"], t["face"]), {})[tag] = t
    out = []
    for key, v in per.items():
        a, c = v["LOW"], v["HIGH"]
        r = dict(a)
        if a["state"] != "MEASURED" or c["state"] != "MEASURED":
            r.update(state="HELD", ties=None, band_held=None, held=a["held"] or c["held"])
        else:
            lo, hi = min(a["ties"], c["ties"]), max(a["ties"], c["ties"])
            r.update(ties=lo, band_held=hi - lo, family=fam.name)
        out.append(r)
    return out


def check_one_owner(tie_records):
    """R-T362-4: one physical junction, one wall."""
    seen = {}
    for t in tie_records:
        k = (t["column_at"], t["face"])
        if k in seen and seen[k] != t["wall_id"]:
            raise WhiteError(f"junction {k} counted from two walls ({seen[k]}, {t['wall_id']})")
        seen[k] = t["wall_id"]
    return len(seen)


def no_family_sum(results: dict):
    """families are alternatives: a combined figure is refused."""
    if len(results) > 1 and "ALL" in results:
        raise WhiteError("families added into one figure refused (alternatives, none chosen)")
    return results
