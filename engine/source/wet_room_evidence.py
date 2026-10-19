"""WET ROOM EVIDENCE V1 (T-010) - is a space wet, dry or held? The architectural room label first, the sanitary
drawing second, loose linework last; never a guess. Method piece, NOT wired into any ARCH_TAKEOFF method:
arch_rooms.py, arch_v27.py, space_model.py, owner_finish_scope.py and every frozen builder are unchanged.

    label_reading(texts, tags)                  -> what the architectural labels inside the space say
    plan_evidence(polygon, ents, roles, unit_m) -> labels, room-tag blocks, fixture blocks, water-closet linework (and
                                                   its layer), sanitary-layer linework, drain / soil-pipe marks inside
                                                   one space of an architectural plan
    classify(plan_ev, sanitary=None)            -> {"class": WET | DRY | HELD | NONE, "reason", "basis", "rules",
                                                    "flags", "coordination_checks", "evidence"}
    wet_scope_quantities(polygon_m, ...)        -> floor, wall porcelain and membrane m2 of a WET space (UP-WET-001),
                                                   every item HELD with its reason when an input is not established
    assess(...)                                 -> classify + quantities in one record

Owner rules applied (no other source):
- Q-13 = B (owner, 2026-10-19), with the architectural room label as PRIMARY evidence: the architectural plan says
  what a room is, the sanitary drawing where fixtures, drains and showers are. A toilet-like object in a room labelled
  as a dry room does not make it wet. Loose lines count as a toilet only on a plumbing / sanitary layer or with a drain
  or soil-pipe mark. No label and ambiguous sanitary evidence: HELD (WET_DRY_NOT_ESTABLISHED), no wet and no dry
  quantity. A real toilet need not show a drain in the same CAD view. Uncertain fixture recognition never creates
  ceramic, waterproofing or plumbing quantities. A labelled wet room missing a fixture or drain in one drawing gets a
  COORDINATION_CHECK and keeps its class.
- Q-06 = (a) (owner, 2026-10-18): a basin-only hand-wash space (a basin, no WC, shower or bath) is WET with the wet
  scope (porcelain floor, full-height wall porcelain, waterproofing, marble threshold). It supersedes, for such a
  space, the 'basin alone -> REVIEW' reading of UP-WET-002 1.3.0 (registry 1.5.0 / 1.6.0, unchanged here).
- UP-WET-001 (wet codes and their scope), UP-WET-002 (fixture vocabulary, the 1.3.0 WC linework profile, used only as
  a CANDIDATE detector), UP-WP-001 / UP-WP-002 / UP-WP-003 (membrane floor, 0.20 m upturn, doorway continuation),
  UP-FIN-WALL-001 (full-height wall porcelain = the clear height), UP-CER-009 (wall run x height - openings),
  UP-QTY-STATUS-001 (every item reported: measured or held, never 0).

Project-agnostic: no layer, room or project name of any villa in code. Stdlib only (plus the engine modules it
reads)."""

from __future__ import annotations

import math
import re

from engine.source import arch_plan as AP
from engine.source import arch_rooms as AR
from engine.source import arch_v27 as V27
from engine.source import drawing_model as DM
from engine.source import room_vocab as RV
from engine.source import waterproofing_system as WS

METHOD_ID = "WET_ROOM_EVIDENCE_V1"
WET, DRY, HELD, NONE = "WET", "DRY", "HELD", "NONE"
MEASURED = "MEASURED"
HAND_WASH = "HAND_WASH"                      # a space named for its hand-wash basin(s) (owner Q-06: wet)
NO_FINISH_KINDS = (AR.STAIR, AR.SHAFT, AR.VOID, AR.EXTERIOR)

# hand-wash space words (the space named after its basin): Arabic 'مغسلة / مغاسل' (wash basin / basins), English
# 'hand wash', 'wash basin', 'wash area'. Read AFTER the compound table of ROOM_VOCAB_V2, so 'مغسلة سيارات' (car wash)
# stays a held compound and never a hand-wash space. Owner Q-06 (a) gives such a space the wet scope.
HAND_WASH_WORDS = (r"(^|\s)(ال)?مغسل[ةه]($|\s)", r"(^|\s)(ال)?مغاسل($|\s)", r"HAND\s*WASH", r"WASH\s*BASIN",
                   r"WASH\s*AREA", r"(^|[^A-Z])WASH($|[^A-Z])")

# sanitary evidence kinds (plan blocks, sanitary-drawing items)
WC, BASIN, SHOWER, BATH, URINAL = "WC", "BASIN", "SHOWER", "BATH", "URINAL"
FLOOR_DRAIN, SOIL_PIPE, KITCHEN_SINK, WASHING_MACHINE = "FLOOR_DRAIN", "SOIL_PIPE", "KITCHEN_SINK", "WASHING_MACHINE"
SANITARY_KINDS = (WC, BASIN, SHOWER, BATH, URINAL, FLOOR_DRAIN, SOIL_PIPE, KITCHEN_SINK, WASHING_MACHINE)
TOILET_KINDS = (WC, SHOWER, BATH, URINAL)            # a fixture that alone makes a space a bathroom
DRAIN_KINDS = (FLOOR_DRAIN, SOIL_PIPE)               # a drain / soil-pipe mark (Q-13 B corroboration)


def _norm(t):
    return DM.normalize(t or "").upper()


def hand_wash_word(text):
    """-> the matched hand-wash word or None (only when ROOM_VOCAB_V2 finds no compound and no room word)."""
    u = _norm(text)
    if not u or len(u) > RV.MAX_LABEL_CHARS:
        return None
    for p in HAND_WASH_WORDS:
        m = re.search(p, u)
        if m:
            return m.group(0).strip()
    return None


def _label_of_text(text):
    """one label text -> {"text", "code", "kind", "wet", "status", "basis"} (ROOM_VOCAB_V2, then hand-wash words)."""
    c = RV.classify(text)
    if c["status"] == "TYPED":
        return {"text": text, "code": c["code"], "kind": c["kind"], "wet": c["wet"], "status": "TYPED",
                "basis": c["basis"]}
    if c["status"] == "NO_ROOM_WORD":
        w = hand_wash_word(text)
        if w:
            return {"text": text, "code": HAND_WASH, "kind": AR.WET, "wet": True, "status": "TYPED",
                    "basis": f"hand-wash word '{w}' (owner Q-06: a hand-wash space is wet)"}
    return {"text": text, "code": None, "kind": None, "wet": None, "status": c["status"], "basis": c["basis"]}


def label_reading(texts=(), tags=()):
    """the architectural labels of one space: texts first (each typed by ROOM_VOCAB_V2, then the hand-wash words);
    room-tag block names only when no text types the space. -> {"source": TEXT | BLOCK_TAG | None, "codes",
    "labels", "untyped"}."""
    labels = [_label_of_text(t) for t in texts if (t or "").strip()]
    typed = [x for x in labels if x["status"] == "TYPED"]
    if typed:
        return {"source": "TEXT", "codes": sorted({x["code"] for x in typed}), "labels": typed,
                "untyped": [x for x in labels if x["status"] != "TYPED"]}
    tag_codes = sorted({c for c in (AR.tag_of(b) for b in tags) if c})
    if tag_codes:
        from engine.source import knowledge as K
        return {"source": "BLOCK_TAG", "codes": tag_codes,
                "labels": [{"text": b, "code": AR.tag_of(b), "kind": AR.LEX[AR.tag_of(b)][2],
                            "wet": AR.tag_of(b) in K.wet_codes(), "status": "TYPED", "basis": "room-tag block name"}
                           for b in tags if AR.tag_of(b)],
                "untyped": labels}
    return {"source": None, "codes": [], "labels": [], "untyped": labels}


# ------------------------------------------------------------------------------------------------ plan evidence
def _pip(x, y, poly):
    ins = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            ins = not ins
    return ins


def _fixture_kind(name):
    """a block name -> a sanitary kind (arch_rooms.FIXTURES vocabulary, refined: bath tub / shower / urinal) or the
    drain kind of waterproofing_system.PEN_PATTERNS, or None."""
    cls, _code = AR.fixture_of(name)
    u = _norm(name)
    if cls == "WC":
        return URINAL if re.search(r"URINAL", u) else WC
    if cls == "SHOWER":
        return BATH if re.search(r"BATH\s*TUB|(^|[^A-Z])TUB($|[^A-Z])|JACUZZI", u) else SHOWER
    if cls == "BASIN":
        return BASIN
    if cls == "KITCHEN_APPLIANCE":
        return KITCHEN_SINK if re.search(r"SINK", u) else "KITCHEN_APPLIANCE"
    if cls == "WASHING_MACHINE":
        return WASHING_MACHINE
    if cls == "IRONING_BOARD":
        return "IRONING_BOARD"
    return _drain_kind(name)


def _drain_kind(text):
    for kind, pat in WS.PEN_PATTERNS:
        if kind == "FLOOR_DRAIN" and pat.search(text or ""):
            return FLOOR_DRAIN
        if kind == "PIPE_PENETRATION" and re.search(r"(?i)((^|[^A-Z])S\.?V\.?P($|[^A-Z])|SOIL\s*(STACK|PIPE))",
                                                    text or ""):
            return SOIL_PIPE
    return None


def _sanitary_layer(layer):
    u = _norm(layer)
    return any(re.search(p, u) for p, c in AR.FIXTURE_LAYERS if c == "BATHROOM")


def plan_evidence(polygon, ents, roles, unit_m, holes=()):
    """the evidence one architectural-plan space holds. polygon / holes in drawing units; ents the architectural
    route's entities (segments, arcs, circles, inserts with optional box, texts); roles maps a layer to its arch_plan
    role (WALL, COLUMN, WINDOW, DOOR, OTHER). Nothing is typed here."""
    def inside(x, y):
        return _pip(x, y, polygon) and not any(_pip(x, y, h) for h in holes)
    xs, ys = [p[0] for p in polygon], [p[1] for p in polygon]
    pad = 0.05 / unit_m
    box = (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)

    def in_box(p):
        return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]
    texts = [t for t in ents.get("texts") or () if inside(t["x"], t["y"])]
    fixtures, tags, drains = [], [], []
    for i in ents.get("inserts") or ():
        b = i.get("box")
        x, y = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) if b else (i["x"], i["y"])
        if not inside(x, y):
            continue
        k = _fixture_kind(i["name"])
        if k in DRAIN_KINDS:
            drains.append({"kind": k, "source": "BLOCK", "name": i["name"], "id": i["id"]})
        elif k:
            fixtures.append({"kind": k, "block": i["name"], "layer": i.get("layer"), "id": i["id"]})
        elif AR.tag_of(i["name"]):
            tags.append(i["name"])
    for t in texts:
        k = _drain_kind(t.get("value"))
        if k and len(_norm(t.get("value"))) <= 12:            # a drain mark, not a sentence that mentions a drain
            drains.append({"kind": k, "source": "TEXT", "name": t.get("value"), "id": t.get("id")})
    fx_h = {V27._decimal_handle(x["id"]) for x in fixtures} - {None}
    fx_ids = {x["id"] for x in fixtures}

    def own(e):                                            # a fixture block's own linework is the fixture
        path = e.get("path") or ()
        return bool(set(path) & fx_ids) or any(V27._decimal_handle(p) in fx_h for p in path)
    loose_s = [s for s in ents.get("segments") or () if roles.get(s["layer"], AP.OTHER) == AP.OTHER and not own(s)
               and in_box(s["a"]) and in_box(s["b"])]
    loose_a = [a for a in ents.get("arcs") or () if roles.get(a["layer"], AP.OTHER) == AP.OTHER and not own(a)
               and in_box(a["c"])]
    loose_c = [c for c in ents.get("circles") or () if roles.get(c["layer"], AP.OTHER) == AP.OTHER and not own(c)
               and in_box(c["c"])]
    wall_segs = [s for s in ents.get("segments") or () if roles.get(s["layer"]) == AP.WALL]
    acc, rej = V27.wc_shapes_v271(loose_s, loose_a, loose_c, unit_m, wall_segs)
    layer_of = {e["id"]: e["layer"] for e in loose_s + loose_a + loose_c}
    wc_lines = []
    for w in acc:
        if not inside(*w["centre"]):
            continue
        lays = sorted({layer_of.get(i) for i in list(w["bowl_ids"]) + list(w["cistern_ids"]) if layer_of.get(i)})
        wc_lines.append({"bowl_m": w["bowl_m"], "cistern_m": w["cistern_m"], "bowl_shape": w["bowl_shape"],
                         "layers": lays, "on_sanitary_layer": bool(lays) and all(_sanitary_layer(x) for x in lays)})
    rejected = [{"bowl_m": w["bowl_m"], "reason": w["reason"]} for w in rej if inside(*w["centre"])]
    san = [s for s in loose_s if _sanitary_layer(s["layer"]) and
           inside((s["a"][0] + s["b"][0]) / 2, (s["a"][1] + s["b"][1]) / 2)]
    return {"labels": label_reading([t.get("value") for t in texts], tags),
            "fixtures": fixtures, "drains": drains, "wc_linework": wc_lines, "wc_rejected": rejected,
            "sanitary_layer_segments": len(san),
            "sanitary_layers": sorted({s["layer"] for s in san})}


# ------------------------------------------------------------------------------------------------ classification
def _sanitary(sanitary):
    """sanitary-drawing items of the space: None = the sanitary drawing was not read for it."""
    if sanitary is None:
        return None
    out = []
    for x in sanitary:
        k = x["kind"] if isinstance(x, dict) else x
        if k not in SANITARY_KINDS:
            raise ValueError(f"unknown sanitary kind {k!r} (one of {', '.join(SANITARY_KINDS)})")
        out.append(dict(x) if isinstance(x, dict) else {"kind": k})
    return out


def classify(plan_ev, sanitary=None, *, space_kind=None):
    """WET / DRY / HELD / NONE for one space (see the module text for the owner rules). plan_ev: plan_evidence(...)
    or a dict of the same shape; sanitary: the sanitary drawing's items inside the space ([{"kind", "ref"}]), [] when
    the sheet was read and shows nothing there, None when no sanitary drawing was read. space_kind: what the room
    builder found from geometry alone (STAIR from tread flights, SHAFT from a stacked footprint, VOID from a void
    symbol); it decides only for a space with no label (NONE: no room finish)."""
    from engine.source import knowledge as K
    san = _sanitary(sanitary)
    lab = plan_ev.get("labels") or {"codes": [], "source": None}
    codes = list(lab.get("codes") or ())
    fx = plan_ev.get("fixtures") or []
    fx_k = {x["kind"] for x in fx}
    stray = []
    if HAND_WASH in codes and len(codes) > 1 and BASIN not in fx_k and \
            BASIN not in {x["kind"] for x in _sanitary(sanitary) or ()}:
        # a hand-wash word names the basin it stands by: in a space that another room word types and that holds no
        # basin in either drawing, the word is a neighbour's label drawn across the wall line
        codes = [c for c in codes if c != HAND_WASH]
        stray.append("COORDINATION_CHECK: a hand-wash word lies inside this space, which another room word types "
                     "and which holds no basin in either drawing - read as a neighbouring space's label (Q-13: "
                     "the room's own label decides)")
    drains = [d["kind"] for d in plan_ev.get("drains") or ()]
    wcl = plan_ev.get("wc_linework") or []
    san_lines = plan_ev.get("sanitary_layer_segments", 0) >= AR.FIXTURE_LAYER_MIN_SEGMENTS
    san_k = {x["kind"] for x in san or ()}
    # what each drawing shows (a basin's own linework is never a second fixture: plan_evidence excludes it)
    plan_toilet = bool(fx_k & set(TOILET_KINDS)) or san_lines or any(w["on_sanitary_layer"] for w in wcl)
    plan_wc_loose = [w for w in wcl if not w["on_sanitary_layer"]]
    plan_drain = bool(set(drains) & set(DRAIN_KINDS))
    san_drain = bool(san_k & set(DRAIN_KINDS))
    plan_any = plan_toilet or bool(fx_k & {BASIN}) or plan_drain or bool(plan_wc_loose)
    san_any = bool(san_k & set(TOILET_KINDS + (BASIN,) + DRAIN_KINDS))
    ev = {"labels": lab, "plan_fixtures": sorted(fx_k), "plan_drains": sorted(set(drains)),
          "wc_linework": wcl, "wc_rejected": plan_ev.get("wc_rejected") or [],
          "sanitary_layer_segments": plan_ev.get("sanitary_layer_segments", 0),
          "sanitary_drawing": None if san is None else sorted(san_k)}
    rec = {"method": METHOD_ID, "evidence": ev, "flags": [], "coordination_checks": stray}

    def out(cls, reason, basis, rules):
        return dict(rec, **{"class": cls, "reason": reason, "basis": basis, "rules": rules})

    # 1. the architectural label decides what the room is (Q-13 B: primary evidence)
    if codes:
        kinds = {AR.WET if c == HAND_WASH else AR.LEX[c][2] for c in codes}
        wet_c = [c for c in codes if c == HAND_WASH or c in K.wet_codes()]
        if kinds <= set(NO_FINISH_KINDS):
            return out(NONE, "NO_ROOM_FINISH", "labelled " + "+".join(codes) + ": stair, shaft, void or exterior "
                       "space - no wet / dry room finish (UP-WET-001)", ["UP-WET-001"])
        if wet_c and len(wet_c) != len(codes):
            return out(HELD, "WET_ZONE_EXTENT_NOT_DRAWN", "labels of a wet function (" + "+".join(wet_c) + ") and a "
                       "dry one (" + "+".join(c for c in codes if c not in wet_c) + ") in one space: the wet zone is "
                       "not bounded by a drawn line or wall (UP-WET-001)", ["UP-WET-001", "UP-QTY-STATUS-001"])
        if wet_c:
            for c in wet_c:
                if c in K.confirm_codes():
                    rec["flags"].append(f"WET_SCOPE_PROJECT_CONFIRMATION: {c} is a wet area where the project "
                                        "scope establishes it (UP-WET-001)")
            if "BATHROOM" in wet_c or HAND_WASH in wet_c:
                need = "a WC, shower, bath, basin or drain" if "BATHROOM" in wet_c else "a basin"
                plan_has = plan_any if "BATHROOM" in wet_c else BASIN in fx_k
                san_has = san_any if "BATHROOM" in wet_c else BASIN in san_k
                if not plan_has and san is None:
                    rec["coordination_checks"].append(
                        f"COORDINATION_CHECK: labelled {'+'.join(wet_c)} but the plan shows no {need} inside and "
                        "no sanitary drawing was read for it (Q-13: the class is kept)")
                elif not plan_has and not san_has:
                    rec["coordination_checks"].append(
                        f"COORDINATION_CHECK: labelled {'+'.join(wet_c)} but neither the plan nor the sanitary "
                        f"drawing shows {need} inside (Q-13: the class is kept, never deleted)")
                elif san is not None and not san_has:
                    rec["coordination_checks"].append(
                        f"COORDINATION_CHECK: labelled {'+'.join(wet_c)}; the sanitary drawing shows no {need} "
                        "inside (Q-13: the class is kept)")
            return out(WET, "LABEL_WET", "architectural label " + "+".join(codes) + " (" + str(lab.get("source")) +
                       ") - owner wet area" + (" (Q-06: hand-wash space)" if HAND_WASH in codes else ""),
                       ["Q-13", "UP-WET-001"] + (["Q-06"] if HAND_WASH in codes else []))
        # a dry label: a toilet-like object does not make it wet (Q-13); a real sanitary item is a coordination check
        seen = sorted((fx_k & set(TOILET_KINDS + (BASIN,))) | ({"WC_LINEWORK"} if wcl else set()) |
                      ({"SANITARY_LAYER_LINEWORK"} if san_lines else set()) | set(drains) |
                      {f"SANITARY_DRAWING_{k}" for k in san_k & set(TOILET_KINDS + (BASIN,) + DRAIN_KINDS)})
        if seen:
            rec["coordination_checks"].append(
                f"COORDINATION_CHECK: labelled {'+'.join(codes)} (dry) but sanitary evidence is drawn inside (" +
                ", ".join(seen) + "): the label decides (Q-13); an en-suite without its partition or a fixture "
                "outside its room - review, no wet quantity")
        return out(DRY, "LABEL_DRY", "architectural label " + "+".join(codes) + " (" + str(lab.get("source")) + ")",
                   ["Q-13", "UP-WET-001"])
    if space_kind in NO_FINISH_KINDS:
        return out(NONE, "NO_ROOM_FINISH", f"no label; the room builder types it {space_kind} from geometry - no "
                   "wet / dry room finish (UP-WET-001)", ["UP-WET-001"])
    # 2. no label: the fixtures decide, and only when they are certain
    toilet_src = []
    if fx_k & set(TOILET_KINDS):
        toilet_src.append("PLAN_FIXTURE_BLOCK(" + ",".join(sorted(fx_k & set(TOILET_KINDS))) + ")")
    if san_lines:
        toilet_src.append("PLAN_SANITARY_LAYER_LINEWORK")
    if any(w["on_sanitary_layer"] for w in wcl):
        toilet_src.append("PLAN_WC_LINEWORK_ON_SANITARY_LAYER")
    if plan_wc_loose and (plan_drain or san_drain):
        toilet_src.append("PLAN_WC_LINEWORK_WITH_DRAIN_MARK")
    if san_k & set(TOILET_KINDS):
        toilet_src.append("SANITARY_DRAWING(" + ",".join(sorted(san_k & set(TOILET_KINDS))) + ")")
    other_wet = (fx_k | san_k) & {"KITCHEN_APPLIANCE", KITCHEN_SINK, WASHING_MACHINE, "IRONING_BOARD"}
    basin = BASIN in fx_k or BASIN in san_k
    if (toilet_src or basin) and other_wet:
        return out(HELD, "WET_DRY_NOT_ESTABLISHED", "no label; sanitary fixtures together with " +
                   ", ".join(sorted(other_wet)) + ": which wet room this is (bathroom, kitchen, laundry) is not "
                   "established", ["Q-13", "UP-QTY-STATUS-001"])
    if toilet_src:
        return out(WET, "FIXTURES_TOILET", "no label; " + " + ".join(toilet_src) + " (Q-13 B)",
                   ["Q-13", "UP-WET-002", "UP-WET-001"])
    if basin:
        src = [s for s, b in (("plan basin block", BASIN in fx_k), ("sanitary-drawing basin", BASIN in san_k)) if b]
        return out(WET, "BASIN_ONLY_HAND_WASH", "no label; " + " and ".join(src) + ", no WC, shower or bath: a "
                   "basin-only hand-wash space is wet (owner Q-06 a)", ["Q-06", "UP-WET-001"])
    if plan_wc_loose:
        return out(HELD, "WET_DRY_NOT_ESTABLISHED", "no label; a water-closet shape drawn as loose lines on " +
                   ", ".join(sorted({l for w in plan_wc_loose for l in w["layers"]})) + " (not a plumbing / "
                   "sanitary layer) with no drain or soil-pipe mark: a WC and a chair at a wall look alike (L-P8-01) "
                   "- no wet and no dry quantity (Q-13 B)", ["Q-13", "UP-WET-002", "UP-QTY-STATUS-001"])
    if plan_drain or san_drain or other_wet:
        return out(HELD, "WET_DRY_NOT_ESTABLISHED", "no label; only " + ", ".join(sorted(set(drains) | (san_k & set(
                   DRAIN_KINDS)) | other_wet)) + ": a drain or an appliance alone does not say which room this is",
                   ["Q-13", "UP-QTY-STATUS-001"])
    return out(HELD, "NO_LABEL_NO_EVIDENCE", "no room label and no sanitary evidence: the space's type is not "
               "established (never a dry default)", ["UP-QTY-STATUS-001"])


# ------------------------------------------------------------------------------------------------ quantities
def _area(p):
    return abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))) / 2


def _perim(p):
    return sum(math.dist(p[i], p[(i + 1) % len(p)]) for i in range(len(p)))


def _held(item, why, rule, **kw):
    return dict({"item": item, "state": HELD, "m2": None, "reason": why, "rule": rule}, **kw)


def wet_scope_quantities(polygon_m, holes_m=(), *, doors=(), windows=(), passages=(), clear_height=None,
                         zone_line_lm=0.0):
    """the owner wet scope of one WET space (UP-WET-001), in metres. doors: [{"id", "width_m", "wall_t_m",
    "height_m"}] (a value None when not established); windows: [{"id", "width_m", "height_m"}]; passages: [{"id",
    "width_m"}]; clear_height: {"value_m", "source"} or None (UP-FIN-WALL-001: full height = the clear height);
    zone_line_lm: boundary drawn as a zone line (no wall: no wall finish along it). Formulas are those of the
    ARCH_TAKEOFF line items (arch_measure): FIN.FLOOR.WET_TILE and FIN.WP.FLOOR = the floor face (UP-WP-001);
    FIN.WP.UPTURN = the one-sided boundary incl. doorways x the UP-WP-002 upturn, no door deduction; FIN.WP.DOORWAY =
    door width x wall thickness (UP-WP-003); FIN.WALL.TILE = wall run x full height - openings (UP-CER-009). An input
    that is not established makes its item HELD (never 0)."""
    from engine.source import rule_store as RS
    up = RS.rule("UP-WP-002", RS.LATEST_APPROVED)["value"]
    floor = _area(polygon_m) - sum(_area(h) for h in holes_m)
    per = _perim(polygon_m) + sum(_perim(h) for h in holes_m)
    items = [{"item": "FIN.FLOOR.WET_TILE", "state": MEASURED, "m2": round(floor, 6), "rule": "UP-WET-001",
              "formula": "floor face (outer ring - holes)"},
             {"item": "FIN.WP.FLOOR", "state": MEASURED, "m2": round(floor, 6), "rule": "UP-WP-001",
              "formula": "floor face"},
             {"item": "FIN.WP.UPTURN", "state": MEASURED, "m2": round(per * up, 6), "rule": "UP-WP-002",
              "formula": f"one-sided boundary incl. doorways {per:.3f} m x {up:g} m (no door deduction)",
              "perimeter_lm": round(per, 6), "upturn_m": up}]
    for d in doors:
        if d.get("width_m") is None or d.get("wall_t_m") is None:
            items.append(_held("FIN.WP.DOORWAY", "DOORWAY_DEPTH_OR_WIDTH_NOT_ESTABLISHED", "UP-WP-003",
                               opening=d.get("id")))
        else:
            items.append({"item": "FIN.WP.DOORWAY", "state": MEASURED, "m2": round(d["width_m"] * d["wall_t_m"], 6),
                          "rule": "UP-WP-003", "formula": "door width x wall thickness", "opening": d.get("id")})
    run = per - (zone_line_lm or 0.0)
    if not clear_height or clear_height.get("value_m") is None:
        items.append(_held("FIN.WALL.TILE", "WALL_FINISH_HEIGHT_NOT_ESTABLISHED (UP-CER-009): full height "
                           "(UP-FIN-WALL-001) is the clear height, which is not established for this space",
                           "UP-FIN-WALL-001", wall_run_lm=round(run, 6)))
    else:
        H = clear_height["value_m"]
        ded, missing = [], []
        for o, kd in [(d, "door") for d in doors] + [(w, "window") for w in windows]:
            if o.get("height_m") is None or o.get("width_m") is None:
                missing.append(f"{kd} {o.get('id')}")
            else:
                ded.append({"what": f"{kd} {o.get('id')}", "m2": round(o["width_m"] * min(o["height_m"], H), 6)})
        for p in passages:
            if p.get("width_m") is None:
                missing.append(f"passage {p.get('id')}")
            else:
                ded.append({"what": f"passage {p.get('id')}", "m2": round(p["width_m"] * H, 6)})
        gross = run * H
        if missing:
            items.append(_held("FIN.WALL.TILE", "OPENING_SIZE_NOT_ESTABLISHED: " + ", ".join(missing), "UP-CER-009",
                               gross_m2=round(gross, 6), deductions=ded, height_m=H,
                               height_source=clear_height.get("source")))
        else:
            items.append({"item": "FIN.WALL.TILE", "state": MEASURED,
                          "m2": round(gross - sum(x["m2"] for x in ded), 6), "rule": "UP-FIN-WALL-001",
                          "formula": f"wall run {run:.3f} m x full height {H:g} m - openings", "gross_m2": round(gross, 6),
                          "deductions": ded, "height_m": H, "height_source": clear_height.get("source")})
    wp = [x for x in items if x["item"].startswith("FIN.WP.")]
    membrane = {"item": "FIN.WP (floor + upturn + doorways)", "rule": "UP-WP-001/002/003"}
    if all(x["state"] == MEASURED for x in wp):
        membrane.update(state=MEASURED, m2=round(sum(x["m2"] for x in wp), 6))
    else:
        membrane.update(state=HELD, m2=None, reason="a doorway piece is held")
    return {"items": items, "membrane": membrane, "floor_m2": round(floor, 6), "perimeter_lm": round(per, 6)}


def assess(plan_ev, sanitary=None, *, polygon_m=None, holes_m=(), space_kind=None, **qty):
    """classify one space and, when it is WET and its outline is given, its wet-scope quantities; a HELD space
    carries no quantity (Q-13: uncertain recognition never creates ceramic or waterproofing)."""
    rec = classify(plan_ev, sanitary, space_kind=space_kind)
    if rec["class"] == WET and polygon_m:
        rec["quantities"] = wet_scope_quantities(polygon_m, holes_m, **qty)
    else:
        rec["quantities"] = None
    return rec


def policy_record():
    return {"id": METHOD_ID, "wired": False,
            "rules": ["Q-13 (B, label primary)", "Q-06 (a)", "UP-WET-001", "UP-WET-002 1.3.0 (WC profile as a "
                      "candidate only)", "UP-WP-001", "UP-WP-002", "UP-WP-003", "UP-FIN-WALL-001", "UP-CER-009",
                      "UP-QTY-STATUS-001"],
            "order": ["architectural label (ROOM_VOCAB_V2, then hand-wash words; room-tag block names when no text "
                      "types the space)", "plan fixture blocks / sanitary-layer linework / WC linework on a sanitary "
                      "layer / WC linework with a drain mark", "sanitary drawing items", "basin only -> hand-wash "
                      "(wet)", "anything else -> HELD"],
            "hand_wash_words": list(HAND_WASH_WORDS)}
