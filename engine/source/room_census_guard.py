"""ROOM CENSUS GUARD (T-099): every face of a plan is reported once - no room silently drops out of the census.

Two ways a real room is lost today, before any quantity is taken (arch_rooms.spaces, frozen, is not changed):
  (1) arch_rooms MIN_SPACE_M2 = 1.0: a face under 1.0 m2 is a SLIVER and no space at all, so a LABELLED small W.C.,
      shower or duct vanishes; a labelled face thinner than THIN_LIMIT_M (DOORWAY / WALL) vanishes the same way. The
      V2.8 lost-label finding (arch_v28.lost_labels) does not see them: the label IS inside a face, a sliver.
  (2) a face with no room label is typed by fixture evidence the owner has since narrowed (Q-13 B), or not at all
      (UNLABELLED: no wet and no dry scope, and nothing says the room is waiting for a decision).

This method piece reads the faces arch_rooms.spaces returned (after its own evidence pass) and gives each face exactly
ONE census record. It is NOT wired into a released method: no face, room or quantity is changed, nothing is released
here (a later ARCH_TAKEOFF version does that).

    census(faces, ents=None, roles=None, unit_m=None, frame=None, sanitary_of=None, space_kind_of=None)
        -> {"policy", "frame", "records": [one per face], "summary"}

    faces       S["faces"] of arch_rooms.spaces (any method version): face_id, class, codes, area_m2, polygon (drawing
                units), hole_polygons, label_source, symbols_inside, ...
    ents        the same plan's entities (texts, inserts, segments, arcs, circles): the labels and the fixture
                evidence inside each face are read from them (wet_room_evidence.plan_evidence). None = only the face's
                own codes are known: a non-space face with codes is still HELD (its label words not shown), an
                unlabelled room is HELD (evidence not read), never typed
    roles       layer -> arch_plan role of that plan (the fixture reader needs OTHER vs WALL)
    unit_m      metres per drawing unit (needed with ents)
    sanitary_of optional {face_id: [sanitary-drawing items]} (wet_room_evidence.classify: Q-13 B second drawing)
    space_kind_of optional {face_id: STAIR | SHAFT | VOID}: what the run found from geometry (stacked shafts); a face
                with stair flights or a void symbol inside is read from its own symbols_inside

Records (status / reason):
    LABELLED                         a ROOM / MIXED / MERGED face the engine typed from a label TEXT: passed through
                                     unchanged (area, codes, class copied; the guard measures nothing)
    HELD SUB_THRESHOLD_LABELLED      a non-space face (SLIVER, or a thin DOORWAY / WALL face) under the space threshold
                                     holding a room label: its label words, code, wet / dry kind of the label, m2 and
                                     the faces it touches are kept for review; nothing is released. A face under about
                                     0.81 m2 is always thin for the room builder (2A/P of a square is half its side),
                                     so a labelled 0.80 m2 W.C. arrives as a WALL / DOORWAY face, not a SLIVER
    HELD THIN_FACE_LABELLED          a thin face of at least the threshold (a long narrow duct) holding a room label
    HELD UNDECODED_TEXT_INSIDE       a non-space face holding a text in a font the reader could not map (an SHX Arabic
                                     label arrives as mojibake): a label may be there - review. Spaces carry the ids of
                                     such texts in undecoded_texts; the summary lists those in no face at all
    HELD SUB_THRESHOLD_FIXTURE       an unlabelled non-space face under the threshold holding a toilet, shower, bath,
                                     basin or drain (a WC compartment drawn under 1 m2 is a room, not a sliver)
    HELD UNLABELLED_ROOM             a space with no room label whose type the evidence does not establish
                                     (wet_room_evidence reason NO_LABEL_NO_EVIDENCE / WET_DRY_NOT_ESTABLISHED, or the
                                     evidence was not read): wet / dry review, no wet and no dry quantity
    TYPED_BY_EVIDENCE                a space the room builder left without a label word, typed by wet_room_evidence:
                                     reason LABEL_WET / LABEL_DRY when a label it reads (ROOM_VOCAB_V2, hand-wash
                                     words) is inside, else the evidence the owner accepts: a toilet /
                                     shower / bath block, WC linework on a sanitary layer or with a drain mark, a
                                     sanitary-drawing toilet (Q-13 B, UP-WET-002), a basin-only hand-wash space
                                     (Q-06 a), or a room-tag block (the room's name drawn as a block)
    NO_ROOM_FINISH                   a space with no label that its own symbols (stair flights, void symbol) or the run
                                     (stacked shaft) type as stair, shaft or void: no wet / dry room finish
    SLIVER / THIN_FACE               a face under the threshold / a thin face with no room label and no sanitary
                                     evidence: not a space (unchanged)

Every record carries area_m2 (the face's measured area; never 0 for a held space, never dropped), engine_class /
engine_codes / engine_label_source (what arch_rooms said) and differs_from_engine when the census reading types the
face differently (e.g. Q-13 B holds a face V2.7 typed BATHROOM from loose WC lines on a furniture layer).

Rules: UP-QTY-STATUS-001 (every labelled space reported once: released, held or excluded; never 0), UP-WET-001,
UP-WET-002, owner Q-06 (a), Q-13 (B). Project-agnostic: no layer, room or project name of any villa in code; m and mm,
rotated and mirrored plans read alike (areas come from the faces, positions only from point-in-polygon tests).
"""

from __future__ import annotations

from engine.source import arch_rooms as AR
from engine.source import room_vocab as RV
from engine.source import wet_room_evidence as WRE

POLICY = "ROOM_CENSUS_GUARD_V1"
RULES = ("UP-QTY-STATUS-001", "UP-WET-001", "UP-WET-002", "Q-06", "Q-13")
THRESHOLD_M2 = AR.MIN_SPACE_M2                      # read from the frozen room builder, never restated
LABEL_STATUSES = ("TYPED", "HELD_COMPOUND")         # room_vocab.classify statuses that make a text a room label
ENGINE_SPACE = ("ROOM", "MIXED", "MERGED", "UNLABELLED")
THIN = ("DOORWAY", "WALL")
SANITARY_SIGNS = set(WRE.TOILET_KINDS) | {WRE.BASIN} | set(WRE.DRAIN_KINDS)
# label sources of the room builder that come from the drawing's room words: the label text itself, or the words of the
# labelled zone a word-less part of a drawn-line zone partition belongs to (arch_rooms._apply_zones)
LABEL_SOURCES = ("TEXT", None, "ZONE_GROUP", "ZONE_SHARED")
UNDECODED = "SHX_UNMAPPED"                          # drawing_model text encoding of an unmapped SHX font
NEIGHBOUR_TOL_M = 0.001                             # two faces share boundary (coincidence, not a drafting gap)
HELD, LABELLED, TYPED, NO_FINISH, SLIVER, THIN_FACE = ("HELD", "LABELLED", "TYPED_BY_EVIDENCE", "NO_ROOM_FINISH",
                                                       "SLIVER", "THIN_FACE")
STATUSES = (LABELLED, HELD, TYPED, NO_FINISH, SLIVER, THIN_FACE)


# ------------------------------------------------------------------------------------------------ helpers
def _ring(poly):
    pts = [(float(p[0]), float(p[1])) for p in (poly or ())]
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    return pts


def _inside_face(x, y, f):
    ring = _ring(f.get("polygon"))
    return len(ring) >= 3 and WRE._pip(x, y, ring) and \
        not any(WRE._pip(x, y, _ring(h)) for h in f.get("hole_polygons") or () if len(_ring(h)) >= 3)


def label_of(text):
    """one text -> {"text", "code", "kind", "wet", "status", "basis"} when it is a room label (ROOM_VOCAB_V2 TYPED or
    HELD_COMPOUND, or a hand-wash word, owner Q-06), else None."""
    lab = WRE._label_of_text(text or "")
    if lab["status"] == "TYPED":
        return lab
    c = RV.classify(text or "")
    if c["status"] in LABEL_STATUSES:
        return {"text": text, "code": c["code"], "kind": c["kind"], "wet": c["wet"], "status": c["status"],
                "basis": c["basis"]}
    return None


def _labels_in(f, texts):
    out = []
    for t in texts:
        if t.get("x") is None or t.get("y") is None or not _inside_face(t["x"], t["y"], f):
            continue
        lab = label_of(t.get("value") if t.get("value") is not None else t.get("text"))
        if lab:
            out.append(dict(lab, text_id=t.get("id")))
    return out


def _undecoded_in(f, texts):
    """texts inside the face whose font the reader could not map (an SHX Arabic label reads as mojibake): a label may
    be there but cannot be read - a review note, never a room type."""
    return [t.get("id") for t in texts if t.get("encoding") == UNDECODED and _inside_face(t["x"], t["y"], f)]


def _wet_dry_of_labels(labels):
    kinds = {x["kind"] for x in labels if x.get("kind")}
    wet = {bool(x["wet"]) for x in labels if x.get("wet") is not None}
    if not labels:
        return None
    if any(x["status"] != "TYPED" for x in labels):
        return "REVIEW"                                  # a held compound names no room type
    if kinds and kinds <= set(WRE.NO_FINISH_KINDS):
        return "NONE"
    return "WET" if wet == {True} else "DRY" if wet == {False} else "REVIEW"


def _neighbours(f, faces, unit_m):
    """ids of the other faces sharing boundary with f (shapely distance <= NEIGHBOUR_TOL_M): where a stray label's
    room may be. Diagnostic only."""
    try:
        from shapely.geometry import Polygon
    except ImportError:                                  # pragma: no cover - shapely is pinned in requirements.txt
        return None
    tol = NEIGHBOUR_TOL_M / unit_m if unit_m else 0.0
    ring = _ring(f.get("polygon"))
    if len(ring) < 3:
        return []
    p = Polygon(ring).buffer(0)
    out = []
    for g in faces:
        if g is f or len(_ring(g.get("polygon"))) < 3:
            continue
        q = Polygon(_ring(g["polygon"])).buffer(0)
        if p.distance(q) <= tol:
            out.append({"face_id": g["face_id"], "class": g["class"], "codes": list(g.get("codes") or ()),
                        "area_m2": g.get("area_m2")})
    return sorted(out, key=lambda x: str(x["face_id"]))


def _geom_kind(f, space_kind_of):
    if space_kind_of and f["face_id"] in space_kind_of:
        return space_kind_of[f["face_id"]]
    sym = f.get("symbols_inside") or {}
    if sym.get("stair_flights"):
        return AR.STAIR
    if sym.get("void_symbols"):
        return AR.VOID
    return None


# ------------------------------------------------------------------------------------------------ census
def _base(f, frame):
    return {"face_id": f["face_id"], "frame": frame, "engine_class": f["class"],
            "engine_codes": list(f.get("codes") or ()), "engine_label_source": f.get("label_source"),
            "area_m2": f.get("area_m2")}


def census(faces, ents=None, roles=None, unit_m=None, frame=None, sanitary_of=None, space_kind_of=None):
    if ents is not None and (roles is None or not unit_m):
        raise ValueError("ents needs the plan's layer roles and unit_m (the fixture reader measures in metres)")
    texts = [t for t in (ents or {}).get("texts") or () if t.get("x") is not None and t.get("y") is not None]
    unplaced = [t.get("id") for t in (ents or {}).get("texts") or () if t.get("x") is None or t.get("y") is None]
    if ents is not None:
        ents = dict(ents, texts=texts)                  # a text with no insertion point is in no face (room_label_guard
                                                        # holds such a label: ROOM_LABEL_NO_POSITION)
    records = []
    for f in faces:
        rec = _base(f, frame)
        cls = f["class"]
        engine_text = cls in ("ROOM", "MIXED", "MERGED") and f.get("label_source") in LABEL_SOURCES and \
            f.get("codes")
        if engine_text:
            rec.update(status=LABELLED, reason=None, wet_dry=None, rules=["UP-QTY-STATUS-001"],
                       basis="labelled room of the room builder (" + str(f.get("label_source") or "TEXT") +
                             "): passed through unchanged")
            records.append(rec)
            continue
        if ents is not None:
            labels = _labels_in(f, texts)
        else:                                            # only the room builder's own reading of the face's words
            from engine.source import knowledge as K
            labels = [{"text": f"[{c}]", "code": c, "kind": AR.LEX[c][2], "wet": c in K.wet_codes(), "status": "TYPED",
                       "basis": "room builder codes (no texts given)"} for c in f.get("codes") or () if c in AR.LEX]
        rec["labels"] = [{k: x[k] for k in ("text", "code", "kind", "status")} for x in labels]
        undec = _undecoded_in(f, texts) if ents is not None else []
        if undec:
            rec["undecoded_texts"] = undec
        if cls not in ENGINE_SPACE:                      # SLIVER, DOORWAY, WALL: not a space for the room builder
            # under the threshold by AREA (a face under about 0.81 m2 is always thin for the room builder: 2A/P of a
            # square is half its side, so a labelled 0.80 m2 W.C. is a WALL / DOORWAY face, not a SLIVER)
            small = (f.get("area_m2") or 0.0) < THRESHOLD_M2
            if labels:
                rec.update(status=HELD, reason="SUB_THRESHOLD_LABELLED" if small else "THIN_FACE_LABELLED",
                           wet_dry=_wet_dry_of_labels(labels), rules=["UP-QTY-STATUS-001"],
                           basis=("a face of {:.4f} m2, under the {:.2f} m2 space threshold," if small else
                                  "a thin face of {:.4f} m2 (doorway / wall piece for the room builder)")
                           .format(f.get("area_m2") or 0.0, THRESHOLD_M2) + " holding the room label(s) " +
                           ", ".join(repr(x["text"]) for x in labels) + ": the labelled space is not measured - "
                           "review the plan (nothing released)")
                if unit_m:
                    rec["neighbours"] = _neighbours(f, faces, unit_m)
                records.append(rec)
                continue
            signs = []
            if small and ents is not None:
                ev = WRE.plan_evidence(_ring(f["polygon"]), ents, roles, unit_m,
                                       [_ring(h) for h in f.get("hole_polygons") or ()])
                signs = sorted({x["kind"] for x in ev["fixtures"] if x["kind"] in SANITARY_SIGNS} |
                               {d["kind"] for d in ev["drains"]} |
                               ({"WC_LINEWORK"} if ev["wc_linework"] else set()))
            if undec and not signs:
                rec.update(status=HELD, reason="UNDECODED_TEXT_INSIDE", wet_dry="REVIEW", rules=["UP-QTY-STATUS-001"],
                           basis="a {} face of {:.4f} m2 holding {} text(s) in a font the reader could not map: a room "
                                 "label may be there - review (nothing released)".format(
                                     "sub-threshold" if small else "thin", f.get("area_m2") or 0.0, len(undec)))
                if unit_m:
                    rec["neighbours"] = _neighbours(f, faces, unit_m)
            elif signs:
                rec.update(status=HELD, reason="SUB_THRESHOLD_FIXTURE", wet_dry="REVIEW",
                           rules=["UP-QTY-STATUS-001", "UP-WET-002"], evidence=signs,
                           basis="an unlabelled face of {:.4f} m2, under the {:.2f} m2 space threshold, holding "
                                 "sanitary evidence ({}): a small room, not a sliver - review (nothing released)"
                           .format(f.get("area_m2") or 0.0, THRESHOLD_M2, ", ".join(signs)))
                if unit_m:
                    rec["neighbours"] = _neighbours(f, faces, unit_m)
            else:
                rec.update(status=SLIVER if cls == "SLIVER" else THIN_FACE, reason=None, wet_dry=None, rules=[],
                           basis="no room label and no sanitary evidence inside: not a space (unchanged)")
            records.append(rec)
            continue
        # a space without a label text: UNLABELLED, or typed by the room builder from blocks / fixtures / geometry
        if labels and all(x["status"] != "TYPED" for x in labels):
            # only held compounds (a phrase naming no room type): the label decides and it decides nothing (Q-13 B)
            rec.update(status=HELD, reason="UNLABELLED_ROOM", wet_dry="REVIEW", rules=["UP-QTY-STATUS-001", "Q-13"],
                       basis="the label(s) " + ", ".join(repr(x["text"]) for x in labels) + " name no room type "
                             "(held compound, ROOM_VOCAB_V2) - review (nothing released)")
            records.append(rec)
            continue
        gk = _geom_kind(f, space_kind_of)
        if gk is None and f.get("codes") and f.get("label_source") not in ("BLOCK_NAME", "FIXTURES",
                                                                            "FIXTURE_LAYER") and \
                not str(f.get("label_source") or "").startswith(("FIXTURES+", "SCENARIO:")) and \
                all(AR.LEX[c][2] in WRE.NO_FINISH_KINDS for c in f["codes"]):
            gk = AR.LEX[f["codes"][0]][2]                # typed from geometry by the run (a stacked shaft footprint)
        if ents is None:
            if gk in WRE.NO_FINISH_KINDS:
                rec.update(status=NO_FINISH, reason=None, wet_dry="NONE", rules=["UP-WET-001"],
                           basis=f"no label; typed {gk} from its own geometry: no wet / dry room finish")
            else:
                rec.update(status=HELD, reason="UNLABELLED_ROOM", wet_dry="REVIEW", rules=["UP-QTY-STATUS-001"],
                           basis="no room label; the plan's entities were not given, so no evidence was read - "
                                 "wet / dry review (never a dry default)")
            records.append(rec)
            continue
        ev = WRE.plan_evidence(_ring(f["polygon"]), ents, roles, unit_m,
                               [_ring(h) for h in f.get("hole_polygons") or ()])
        san = (sanitary_of or {}).get(f["face_id"]) if sanitary_of is not None else None
        c = WRE.classify(ev, san, space_kind=gk)
        rec["evidence"] = {"label_source": ev["labels"]["source"],
                           "fixtures": sorted(x["kind"] for x in ev["fixtures"]),
                           "drains": sorted(d["kind"] for d in ev["drains"]),
                           "wc_linework": [{"layers": w["layers"], "on_sanitary_layer": w["on_sanitary_layer"]}
                                           for w in ev["wc_linework"]],
                           "sanitary_layer_segments": ev["sanitary_layer_segments"],
                           "sanitary_drawing": c["evidence"]["sanitary_drawing"]}
        rec["wet_room_evidence"] = {"class": c["class"], "reason": c["reason"]}
        rec["coordination_checks"] = c["coordination_checks"]
        if c["class"] == WRE.NONE:
            rec.update(status=NO_FINISH, reason=None, wet_dry="NONE", rules=c["rules"], basis=c["basis"])
        elif c["class"] in (WRE.WET, WRE.DRY):
            rec.update(status=TYPED, reason=c["reason"], wet_dry=c["class"], rules=c["rules"], basis=c["basis"],
                       typed_codes=list(ev["labels"]["codes"]) or None)
        else:
            rec.update(status=HELD, reason="UNLABELLED_ROOM", wet_dry="REVIEW", rules=c["rules"],
                       basis=c["basis"] + " - wet / dry review (nothing released)", evidence_reason=c["reason"])
        records.append(rec)
    for rec in records:
        rec["differs_from_engine"] = _differs(rec)
    outside = [t.get("id") for t in texts if t.get("encoding") == UNDECODED and
               not any(_inside_face(t["x"], t["y"], f) for f in faces)]
    return {"policy": POLICY, "frame": frame, "threshold_m2": THRESHOLD_M2, "records": records,
            "summary": dict(summary(records, len(faces)), texts_without_position=unplaced,
                            undecoded_texts_in_no_face=outside)}


def _differs(rec):
    """does the census type the face differently from the room builder? (engine typed a space the census holds, or the
    engine dropped a face the census holds / types)"""
    eng_space = rec["engine_class"] in ("ROOM", "MIXED", "MERGED")
    if rec["status"] == LABELLED:
        return False
    if rec["status"] == HELD:
        return eng_space or rec["engine_class"] not in ENGINE_SPACE
    if rec["status"] == TYPED:
        return not eng_space
    if rec["status"] == NO_FINISH:
        return False
    return False


def summary(records, n_faces=None):
    by = {}
    for r in records:
        k = r["status"] + (":" + r["reason"] if r["status"] == HELD and r.get("reason") else "")
        b = by.setdefault(k, {"faces": 0, "m2": 0.0})
        b["faces"] += 1
        b["m2"] = round(b["m2"] + (r.get("area_m2") or 0.0), 6)
    held_zero = [r["face_id"] for r in records if r["status"] == HELD and not (r.get("area_m2") or 0) > 0]
    out = {"faces": len(records), "by_status": dict(sorted(by.items())),
           "held": sum(1 for r in records if r["status"] == HELD),
           "differs_from_engine": sum(1 for r in records if r["differs_from_engine"]),
           "held_without_area": held_zero}
    if n_faces is not None:
        out["every_face_once"] = n_faces == len(records) and len({id(r) for r in records}) == len(records)
    return out


def policy_record():
    return {"policy": POLICY, "rules": list(RULES), "threshold_m2": THRESHOLD_M2, "statuses": list(STATUSES),
            "held_reasons": ["SUB_THRESHOLD_LABELLED", "THIN_FACE_LABELLED", "UNDECODED_TEXT_INSIDE",
                             "SUB_THRESHOLD_FIXTURE", "UNLABELLED_ROOM"],
            "never": ["a face dropped from the census", "a held space shown as 0 m2", "a dry default for an unlabelled "
                      "room", "a room typed wet from loose WC lines off a sanitary layer with no drain mark (Q-13 B)",
                      "a change to a face, room or released quantity"]}
