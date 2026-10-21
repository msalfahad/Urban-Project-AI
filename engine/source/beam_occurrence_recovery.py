"""BEAM_OCCURRENCE_RECOVERY (generic): every beam tag and every structural face band gets a terminal record.

Routes (independent):
    TAG route         a tag bound to an adjacent band whose width matches its scheduled breadth
    FACE route        a paired-face band with no tag -> candidate occurrence (width from the band, depth candidate
                      from scheduled types of that width; several candidates -> scenario)
    CONTINUITY route  an untagged band collinear with and touching a tagged band of the same width -> inherits the
                      type (PROVISIONAL)
    SCHEDULE          definitions only - never an occurrence

Outcomes per object:
    BOUND                 tag + band agree                    -> VERIFIED volume (length x B x (D - t))
    TYPE_CONFLICT         two tags of different types on one band -> SOURCE_CONFLICT, both scenarios kept
    TAG_WITHOUT_BAND      tag with no band: UNQUANTIFIED unless a same-type length is supplied (CANDIDATE, low 0 -
                          it may repeat a measured beam)
    BAND_WITHOUT_TAG      FACE / CONTINUITY candidate          -> PROVISIONAL / CANDIDATE
A band is quantified once, whatever the number of routes that see it. Stdlib only.
"""

from __future__ import annotations

from collections import defaultdict

from engine.source import population_conservation as PC
from engine.source import quantity_scenarios as QS


class BeamRecoveryError(ValueError):
    pass


def _vol(L, B, D, t):
    return L * B * max(D - t, 0.0)


def recover(tags, bands, schedule, *, slab_t_m, tag_band=None, continuity=None, same_type_length=None):
    """tags: [{tag_id, type}]; bands: [{band_id, length_m, width_m, handles}]; schedule: {type: {B_m, D_m}};
    tag_band: {tag_id: band_id} (adjacency already established by geometry); continuity: {band_id: tagged band_id};
    same_type_length: {type: median length m} for tags without a band."""
    tag_band = tag_band or {}
    continuity = continuity or {}
    same_type_length = same_type_length or {}
    band_by_id = {b["band_id"]: b for b in bands}
    if len(band_by_id) != len(bands):
        raise BeamRecoveryError("a band is listed twice")
    tags_on = defaultdict(list)
    for t in tags:
        b = tag_band.get(t["tag_id"])
        if b is not None:
            if b not in band_by_id:
                raise BeamRecoveryError(f"tag {t['tag_id']} bound to unknown band {b}")
            tags_on[b].append(t)
    out, parts, occs = [], [], []

    def emit(oid, kind, state, part, qty, known, why, unresolved=()):
        occ = {"occurrence_id": oid, "source_handles": known.get("handles", []), "position": known.get("position"),
               "count": 1, "known_geometry": known, "candidate_definitions": known.get("candidates", [])}
        occs.append({"occurrence_id": oid})
        parts.append(part)
        out.append({"occurrence_id": oid, "outcome": kind, "part": part,
                    "terminal": PC.terminal(occ, state, quantity=qty, unresolved=unresolved, why=why)})

    for b in bands:
        bid, L, W = b["band_id"], b["length_m"], b["width_m"]
        known = {"length_m": L, "width_m": W, "handles": b.get("handles", [])}
        on = tags_on.get(bid, [])
        types = sorted({t["type"] for t in on})
        if len(types) == 1 and types[0] in schedule:
            d = schedule[types[0]]
            v = _vol(L, d["B_m"], d["D_m"], slab_t_m)
            emit(bid, "BOUND", "MEASURED_COMPLETE", QS.part(bid, "VERIFIED", v, origin="SOURCE_FACT"), v,
                 dict(known, type=types[0]), "tag + band + schedule")
        elif len(types) > 1:
            vs = [_vol(L, schedule[t]["B_m"], schedule[t]["D_m"], slab_t_m) for t in types if t in schedule]
            best = max(vs)
            emit(bid, "TYPE_CONFLICT", "CANDIDATE_QUANTIFIED",
                 QS.part(bid, "SOURCE_CONFLICT", best, min(vs), max(vs), origin="SOURCE_FACT",
                         why=f"tags {types} on one band"), best, dict(known, candidates=types),
                 "two schedule types on one band", ("TYPE",))
        else:
            src = continuity.get(bid)
            inherit = [t["type"] for t in tags_on.get(src, [])] if src else []
            if inherit and inherit[0] in schedule:
                d = schedule[inherit[0]]
                v = _vol(L, d["B_m"], d["D_m"], slab_t_m)
                emit(bid, "BAND_WITHOUT_TAG", "CANDIDATE_QUANTIFIED",
                     QS.part(bid, "PROVISIONAL", v, 0.0, v, origin="DERIVED", why=f"continuity with {src}"), v,
                     dict(known, candidates=[inherit[0]]), "continuity route", ("TYPE",))
            else:
                cand = sorted(t for t, d in schedule.items() if abs(d["B_m"] - W) < 1e-6)
                if cand:
                    vs = [_vol(L, W, schedule[t]["D_m"], slab_t_m) for t in cand]
                    best = sorted(vs)[len(vs) // 2]
                    emit(bid, "BAND_WITHOUT_TAG", "CANDIDATE_QUANTIFIED",
                         QS.part(bid, "CANDIDATE", best, 0.0, max(vs), origin="CANDIDATE",
                                 why=f"untagged band; types of width {W}: {cand}"), best,
                         dict(known, candidates=cand), "face route", ("TYPE",))
                else:
                    emit(bid, "BAND_WITHOUT_TAG", "UNQUANTIFIED", QS.part(bid, "UNQUANTIFIED", why="no type of this width"),
                         None, known, "face route, no scheduled type of this width", ("TYPE", "DEPTH"))
    for t in tags:
        if t["tag_id"] in tag_band:
            continue
        oid = f"TAG:{t['tag_id']}"
        Lm = same_type_length.get(t["type"])
        d = schedule.get(t["type"])
        if Lm and d:
            v = _vol(Lm, d["B_m"], d["D_m"], slab_t_m)
            emit(oid, "TAG_WITHOUT_BAND", "CANDIDATE_QUANTIFIED",
                 QS.part(oid, "CANDIDATE", v, 0.0, v, origin="CANDIDATE",
                         why="same-type median length; may repeat a measured beam"), v,
                 {"type": t["type"], "handles": t.get("handles", [])}, "tag without band", ("GEOMETRY",))
        else:
            emit(oid, "TAG_WITHOUT_BAND", "UNQUANTIFIED", QS.part(oid, "UNQUANTIFIED", why="tag without band"), None,
                 {"type": t["type"], "handles": t.get("handles", [t["tag_id"]])}, "tag without band", ("GEOMETRY",))
    cons = PC.require_conserved(occs, [o["terminal"] for o in out])
    return {"objects": out, "volume": QS.combine(parts, unit="m3"), "conservation": cons}
