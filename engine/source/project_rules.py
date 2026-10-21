"""PROJECT RULES (M9 Phase 2B-2, ARCH_TAKEOFF_V2.4 only) - Level A Urban master standards (the knowledge registry
1.1.0) and Level B project-specific rules (input URBAN_PROJECT_RULES_V1), the scoped resolver every V2.4 quantity
reads its rule values from, and the Project Engineering Rules Sheet generated before the BOQ calculation
(UP-RULES-001).

    load(doc)                          -> the validated project rules (ProjectRulesError on a malformed rule)
    bind(doc, rooms=, openings=, walls=) -> {project rule id: binding} for point-scoped rules (ROOM / OPENING / WALL)
    Resolver(doc, bindings).get(rule_id, parameter, target)
                                       -> {"value", "state", "urban_value", "project_rule_ids", "source", "overridden",
                                           "conflict", ...}: the most specific matching project rule, else the Urban
                                           standard (OWNER_STANDARD_ASSUMED), CONFLICT_REVIEW when rules of the same
                                           rank disagree (value None: the affected quantity is unresolved)
    rules_sheet(doc, bindings=, project_id=, drawing=, facts=, decisions=, resolver=)
                                       -> the sheet: 15 sections, one row per rule (Urban standard, project evidence,
                                          applied rule, source, status, impact), rules_sha256 / sheet_sha256
    invalidation(old_sheet, new_sheet) -> FIRST_RUN / UNCHANGED / RULES_CHANGED with the changed rows and the trades
                                          and items they affect

Target of a resolution: {"floor", "room_id", "codes", "door_category", "opening_id", "wall_id"} (any subset).
Scopes: PROJECT < LOCATION_TYPE = DOOR_CATEGORY < FLOOR < ROOM < WALL < OPENING; a "types" / "categories" filter on a
FLOOR or ROOM scope adds half a rank. Nothing here measures; nothing changes a drawn dimension. Project-agnostic;
stdlib only."""

from __future__ import annotations

import copy
import hashlib
import json
import math
from collections import defaultdict

from engine.source import knowledge as K

SCHEMA = "URBAN_PROJECT_RULES_V1"
SHEET_SCHEMA = "URBAN_PROJECT_RULES_SHEET_V1"
POLICY_ID = "PROJECT_RULES_V1"
STATES = ("DRAWING_CONFIRMED", "PROJECT_SPECIFIED", "OWNER_STANDARD_ASSUMED", "OWNER_PROJECT_APPROVED",
          "CONFLICT_REVIEW", "ENGINE_LIMITATION", "MISSING_DOCUMENT")
SOURCE_STATE = {"DRAWING": "DRAWING_CONFIRMED", "SCHEDULE": "PROJECT_SPECIFIED", "DETAIL": "PROJECT_SPECIFIED",
                "SPECIFICATION": "PROJECT_SPECIFIED", "OWNER_PROJECT_APPROVAL": "OWNER_PROJECT_APPROVED"}
RANK = {"PROJECT": 0.0, "LOCATION_TYPE": 1.0, "DOOR_CATEGORY": 1.0, "FLOOR": 2.0, "ROOM": 3.0, "WALL": 4.0,
        "OPENING": 5.0}
POINT_SCOPES = ("ROOM", "WALL", "OPENING")
SECTIONS = ("01_PROJECT_IDENTIFICATION", "02_ARCHITECTURAL_RULES", "03_DOOR_STANDARDS", "04_WINDOWS",
            "05_FLOOR_FINISHES", "06_WALL_FINISHES", "07_SKIRTING", "08_WATERPROOFING", "09_CEILINGS", "10_STAIRS",
            "11_STRUCTURAL_MEASUREMENT", "12_OPENINGS_AND_DEDUCTIONS", "13_EXTERNAL_WORKS",
            "14_UNRESOLVED_CONFLICTS", "15_OWNER_APPROVED_PROJECT_EXCEPTIONS")
ROW_FIELDS = ("row_id", "section", "rule", "rule_id", "urban_standard", "drawing_specification", "applied_rule",
              "source", "status", "impact", "scope", "notes")
WET_GROUP, EXT_GROUP = "WET_AREA", "EXTERIOR"
EXTERIOR_CODES = ("BALCONY", "ROOF")
DOORWAY_DETAILS = ("UPTURN_ACROSS_THRESHOLD", "CONTINUATION_TERMINATED", "JAMB_RETURNS")
WALL_STRUCTURES = ("STRUCTURAL", "NON_STRUCTURAL")
DOOR_CATEGORIES = ("INTERNAL_PVC", "BATHROOM_PVC", "EXTERNAL_ALUMINIUM", "MAIN_ENTRANCE")
ENGINE_PIER_M = 0.10                     # UP-DOOR-FEAS-001: ENGINE_REVIEW_THRESHOLD, not an owner standard
OPENING_REACH_M = 0.6
WALL_REACH_M = 0.05

WP_SCOPES = ("PROJECT", "LOCATION_TYPE", "FLOOR", "ROOM")
DOOR_SCOPES = ("PROJECT", "DOOR_CATEGORY", "FLOOR", "OPENING")
WP_ITEMS = ("FIN.WP.FLOOR", "FIN.WP.DOORWAY", "FIN.WP.WALL_UPTURN", "FIN.WP.DOORWAY_TRANSITION", "FIN.WP.TERMINATION",
            "FIN.WP.PENETRATION", "FIN.WP (material)", "FIN.WP (procurement)")
DOOR_ITEMS = ("DOOR.INTERNAL.PVC", "DOOR.EXTERNAL.ALUMINIUM", "DOOR.MAIN_ENTRANCE", "DOOR feasibility",
              "FIN.PLASTER (door jambs)")


class ProjectRulesError(ValueError):
    pass


def _f(lo, hi):
    def check(v):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not lo <= v <= hi:
            raise ProjectRulesError(f"a number in [{lo}, {hi}] (got {v!r})")
        return float(v)
    return check


def _enum(values):
    def check(v):
        if v not in values:
            raise ProjectRulesError(f"one of {values} (got {v!r})")
        return v
    return check


def _treatment(v):
    """{"kind": "PATCH", "size_m": [a, b]} (membrane area each) | {"kind": "PROPRIETARY", "name": ...} (pcs)."""
    if not isinstance(v, dict) or v.get("kind") not in ("PATCH", "PROPRIETARY"):
        raise ProjectRulesError(f"a treatment {{kind: PATCH | PROPRIETARY, ...}} (got {v!r})")
    if v["kind"] == "PATCH":
        s = v.get("size_m")
        if not (isinstance(s, (list, tuple)) and len(s) == 2):
            raise ProjectRulesError("a PATCH treatment needs size_m [a, b]")
        [_f(0.01, 3.0)(x) for x in s]
    return dict(v)


def _system(v):
    if not isinstance(v, dict) or not v.get("system_id"):
        raise ProjectRulesError(f"a membrane system {{system_id, name, ...}} (got {v!r})")
    return dict(v)


def _lg(rule_id):
    return K.rule(rule_id)["logic"]


def _door_urban(t):
    cat = (t or {}).get("door_category")
    row = (_lg("UP-DOOR-OPEN-002")["table"] or {}).get(cat)
    return row["required_nominal_door_m"] if row else None


def _height_urban(t):
    return _lg("UP-DOOR-HGT-001")["owner_reference_height_m"].get((t or {}).get("door_category"))


# (rule_id, parameter) -> spec: check, allowed scopes, sheet section, label, urban standard (target -> value or None)
#                               and its state when no project rule applies, impact (trades, items)
PARAMETERS = {
    ("UP-WP-001", "roll_width_m"): dict(check=_f(0.3, 5.0), scopes=WP_SCOPES, section="08_WATERPROOFING",
                                        label="membrane roll width", urban=lambda t: _lg("UP-WP-001")["roll_width_m"],
                                        trades=("WATERPROOFING",), items=("FIN.WP (material)", "FIN.WP (procurement)")),
    ("UP-WP-001", "roll_length_m"): dict(check=_f(1.0, 100.0), scopes=WP_SCOPES, section="08_WATERPROOFING",
                                         label="membrane roll length",
                                         urban=lambda t: _lg("UP-WP-001")["roll_length_m"], trades=("WATERPROOFING",),
                                         items=("FIN.WP (material)", "FIN.WP (procurement)")),
    ("UP-WP-002", "lap_m"): dict(check=_f(0.02, 0.5), scopes=WP_SCOPES, section="08_WATERPROOFING",
                                 label="membrane overlap at strip joints", urban=lambda t: _lg("UP-WP-002")["lap_m"],
                                 trades=("WATERPROOFING",), items=("FIN.WP (material)", "FIN.WP (procurement)")),
    ("UP-WP-003", "upturn_h_m"): dict(check=_f(0.05, 1.5), scopes=WP_SCOPES, section="08_WATERPROOFING",
                                      label="waterproofing upturn height",
                                      urban=lambda t: _lg("UP-WP-003")["upturn_h_m"], trades=("WATERPROOFING",),
                                      items=("FIN.WP.WALL_UPTURN", "FIN.WP.DOORWAY_TRANSITION", "FIN.WP (material)",
                                             "FIN.WP (procurement)")),
    ("UP-WP-DOOR-001", "doorway_detail"): dict(check=_enum(DOORWAY_DETAILS), scopes=WP_SCOPES,
                                               section="08_WATERPROOFING", label="doorway waterproofing detail",
                                               urban=None, missing="the project waterproofing detail at doorways",
                                               trades=("WATERPROOFING",),
                                               items=("FIN.WP.DOORWAY_TRANSITION", "FIN.WP (material)",
                                                      "FIN.WP (procurement)")),
    ("UP-WP-003", "termination_detail"): dict(check=_enum(("TERMINATION_BAR", "TURN_DOWN", "WATER_STOP")),
                                              scopes=WP_SCOPES, section="08_WATERPROOFING",
                                              label="edge termination detail", urban=None,
                                              missing="the termination detail at open edges / dry openings",
                                              trades=("WATERPROOFING",), items=("FIN.WP.TERMINATION",)),
    ("UP-WP-004", "penetration_treatment"): dict(check=_treatment, scopes=WP_SCOPES, section="08_WATERPROOFING",
                                                 label="penetration / drain treatment", urban=None,
                                                 missing="the penetration / collar detail of the membrane system",
                                                 trades=("WATERPROOFING",),
                                                 items=("FIN.WP.PENETRATION", "FIN.WP (material)")),
    ("UP-WP-004", "corner_treatment"): dict(check=_treatment, scopes=WP_SCOPES, section="08_WATERPROOFING",
                                            label="corner / junction treatment (membrane patches)", urban=None,
                                            missing="the corner treatment of the membrane system",
                                            trades=("WATERPROOFING",), items=("FIN.WP (material)",)),
    ("UP-WP-MAT-001", "system"): dict(check=_system, scopes=WP_SCOPES, section="08_WATERPROOFING",
                                      label="membrane system (procurement group)", urban=None,
                                      missing="the membrane system of the location (specification / data sheet)",
                                      trades=("WATERPROOFING",), items=("FIN.WP (procurement)",)),
    ("UP-WP-LAY-001", "min_reusable_m"): dict(check=_f(0.05, 5.0), scopes=WP_SCOPES, section="08_WATERPROOFING",
                                              label="minimum reusable offcut", urban=lambda t: None,
                                              urban_note="no narrow offcut is retained (UP-WP-LAY-001)",
                                              trades=("WATERPROOFING",), items=("FIN.WP (procurement)",)),
    ("UP-DOOR-OPEN-002", "required_nominal_door_m"): dict(check=_f(0.5, 3.0), scopes=DOOR_SCOPES,
                                                          section="03_DOOR_STANDARDS",
                                                          label="required nominal door width", urban=_door_urban,
                                                          trades=("OPENINGS",), items=DOOR_ITEMS),
    ("UP-DOOR-OPEN-002", "allowance_m"): dict(check=_f(0.0, 0.5), scopes=DOOR_SCOPES, section="03_DOOR_STANDARDS",
                                              label="architectural opening allowance",
                                              urban=lambda t: _lg("UP-DOOR-OPEN-002")["allowance_m"],
                                              trades=("OPENINGS",), items=DOOR_ITEMS),
    ("UP-DOOR-HGT-001", "door_height_m"): dict(check=_f(1.8, 4.5), scopes=DOOR_SCOPES, section="03_DOOR_STANDARDS",
                                               label="door height", urban=_height_urban,
                                               trades=("OPENINGS", "PLASTER"), items=DOOR_ITEMS),
    ("UP-DOOR-FEAS-001", "min_pier_m"): dict(check=_f(0.0, 1.0), scopes=DOOR_SCOPES, section="03_DOOR_STANDARDS",
                                             label="minimum wall pier left beside an enlarged opening",
                                             urban=lambda t: ENGINE_PIER_M, urban_state="ENGINE_LIMITATION",
                                             urban_note="ENGINE_REVIEW_THRESHOLD 0.10 m (not an owner standard)",
                                             trades=("OPENINGS", "MASONRY"), items=("DOOR feasibility",)),
    ("UP-DOOR-FEAS-001", "wall_structure"): dict(check=_enum(WALL_STRUCTURES), scopes=("PROJECT", "FLOOR", "WALL"),
                                                 section="11_STRUCTURAL_MEASUREMENT",
                                                 label="structural status of a host wall", urban=None,
                                                 missing="the structural drawings (load-bearing walls)",
                                                 trades=("OPENINGS", "MASONRY", "CONCRETE"),
                                                 items=("DOOR feasibility",)),
}


def location_types(codes):
    """the location types a room's codes put it in: the codes themselves, WET_AREA (UP-WET-001), EXTERIOR."""
    c = [str(x) for x in codes or ()]
    out = set(c)
    if set(c) & set(K.wet_codes()):
        out.add(WET_GROUP)
    if set(c) & set(EXTERIOR_CODES):
        out.add(EXT_GROUP)
    return out


def _canon(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha(x):
    return hashlib.sha256(_canon(x).encode("utf-8")).hexdigest()


def load(doc):
    """validate a URBAN_PROJECT_RULES_V1 document. A rule naming a parameter the engine does not know is kept (listed
    as ENGINE_LIMITATION on the sheet, never applied); a malformed rule is refused."""
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        raise ProjectRulesError(f"project rules: schema must be {SCHEMA}")
    out = copy.deepcopy(doc)
    seen = set()
    for r in out.get("rules") or ():
        rid = r.get("id")
        if not rid or rid in seen:
            raise ProjectRulesError(f"project rule id missing or repeated: {rid!r}")
        seen.add(rid)
        src = r.get("source") or {}
        if src.get("kind") not in SOURCE_STATE or not src.get("ref"):
            raise ProjectRulesError(f"{rid}: source {{kind: {'|'.join(SOURCE_STATE)}, ref}} is required")
        sc = r.get("scope") or {}
        if sc.get("kind") not in RANK:
            raise ProjectRulesError(f"{rid}: scope kind {sc.get('kind')!r} not one of {tuple(RANK)}")
        if sc["kind"] in ("FLOOR",) + POINT_SCOPES and not sc.get("floor"):
            raise ProjectRulesError(f"{rid}: a {sc['kind']} scope names its floor")
        if sc["kind"] in POINT_SCOPES and sc.get("point_m") is None and not (sc["kind"] == "OPENING" and
                                                                             sc.get("opening_id")):
            raise ProjectRulesError(f"{rid}: a {sc['kind']} scope names a point_m (or an opening_id)")
        if sc["kind"] == "LOCATION_TYPE" and not sc.get("types"):
            raise ProjectRulesError(f"{rid}: a LOCATION_TYPE scope lists its types")
        if sc["kind"] == "DOOR_CATEGORY" and not set(sc.get("categories") or ()) <= set(DOOR_CATEGORIES):
            raise ProjectRulesError(f"{rid}: door categories must be among {DOOR_CATEGORIES}")
        spec = PARAMETERS.get((r.get("rule_id"), r.get("parameter")))
        if spec is None:
            r["_supported"] = False
            continue
        if sc["kind"] not in spec["scopes"]:
            raise ProjectRulesError(f"{rid}: {r['rule_id']} {r['parameter']} takes the scopes {spec['scopes']}")
        try:
            r["value"] = spec["check"](r.get("value"))
        except ProjectRulesError as ex:
            raise ProjectRulesError(f"{rid}: {r['rule_id']} {r['parameter']} must be {ex}") from None
        r["_supported"] = True
    return out


def _inside(p, poly):
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def _dist_seg(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.dist(p, (a[0] + t * dx, a[1] + t * dy))


def bind(doc, *, rooms=(), openings=(), walls=()):
    """point-scoped rules -> the element they name. rooms: [{room_id, floor, polygon_m, hole_polygons_m?}];
    openings: [{floor, opening_id, centre_m}]; walls: [{floor, wall_id, centreline_m [a, b], t_m}]. An unbound rule
    is reported (PROJECT_RULE_UNBOUND) and never applied."""
    out = {}
    for r in doc.get("rules") or ():
        sc = r["scope"]
        k = sc["kind"]
        if k not in POINT_SCOPES:
            out[r["id"]] = {"kind": k, "state": "NOT_POINT_SCOPED"}
            continue
        fl, p = sc["floor"], tuple(sc["point_m"]) if sc.get("point_m") is not None else None
        hit = None
        if k == "ROOM":
            hits = [x["room_id"] for x in rooms if x.get("floor") == fl and _inside(p, x["polygon_m"]) and not
                    any(_inside(p, h) for h in x.get("hole_polygons_m") or ())]
            hit = hits[0] if len(hits) == 1 else None
            out[r["id"]] = {"kind": k, "state": "BOUND" if hit else "UNBOUND", "room_id": hit,
                            "candidates": len(hits)}
        elif k == "OPENING":
            if sc.get("opening_id"):
                hits = [o for o in openings if o.get("floor") == fl and o.get("opening_id") == sc["opening_id"]]
            else:
                hits = sorted((o for o in openings if o.get("floor") == fl and o.get("centre_m") is not None and
                               math.dist(p, o["centre_m"]) <= OPENING_REACH_M),
                              key=lambda o: (math.dist(p, o["centre_m"]), o["opening_id"]))
            hit = hits[0]["opening_id"] if hits else None
            out[r["id"]] = {"kind": k, "state": "BOUND" if hit else "UNBOUND", "opening_id": hit}
        else:
            hits = sorted((w for w in walls if w.get("floor") == fl and
                           _dist_seg(p, *w["centreline_m"]) <= w["t_m"] / 2.0 + WALL_REACH_M),
                          key=lambda w: (_dist_seg(p, *w["centreline_m"]), w["wall_id"]))
            hit = hits[0]["wall_id"] if hits else None
            out[r["id"]] = {"kind": k, "state": "BOUND" if hit else "UNBOUND", "wall_id": hit}
    return out


def _matches(r, b, t):
    sc = r["scope"]
    k = sc["kind"]
    types = set(sc.get("types") or ())
    if types and not types & location_types(t.get("codes")):
        return False
    if k == "PROJECT":
        return True
    if k == "LOCATION_TYPE":
        return bool(types)
    if k == "DOOR_CATEGORY":
        return t.get("door_category") in (sc.get("categories") or ())
    if k == "FLOOR":
        return t.get("floor") == sc["floor"] and (not sc.get("categories") or
                                                  t.get("door_category") in sc["categories"])
    if (b or {}).get("state") != "BOUND":
        return False
    if k == "ROOM":
        return t.get("room_id") == b["room_id"]
    if k == "OPENING":
        return t.get("floor") == sc["floor"] and t.get("opening_id") == b["opening_id"]
    return t.get("wall_id") == b["wall_id"]


def _rank(r):
    sc = r["scope"]
    return RANK[sc["kind"]] + (0.5 if sc["kind"] in ("FLOOR", "ROOM") and (sc.get("types") or sc.get("categories"))
                               else 0.0)


def _src(r):
    return f"{r['source']['kind']}: {r['source']['ref']}"


class Resolver:
    """the applied value of one (rule, parameter) for one element; every resolution is recorded (`log`)."""

    def __init__(self, doc=None, *, bindings=None):
        self.doc = doc or {"schema": SCHEMA, "rules": []}
        self.bindings = bindings or {}
        self.log = {}

    def get(self, rule_id, parameter, target):
        spec = PARAMETERS[(rule_id, parameter)]
        t = target or {}
        urban = spec["urban"](t) if spec.get("urban") else None
        cands = [r for r in self.doc.get("rules") or () if r.get("_supported") and r["rule_id"] == rule_id and
                 r["parameter"] == parameter and _matches(r, self.bindings.get(r["id"]), t)]
        out = {"rule_id": rule_id, "parameter": parameter, "urban_value": urban,
               "urban_source": f"registry {rule_id} ({K.rule_set()})", "project_rule_ids": [], "overridden": [],
               "conflict": [], "source": None}
        if not cands:
            if spec.get("urban") is None:
                out.update(value=None, state="MISSING_DOCUMENT", note=f"no project rule gives {spec['missing']}")
            else:
                out.update(value=urban, state=spec.get("urban_state", "OWNER_STANDARD_ASSUMED") if urban is not None
                           or spec.get("urban_note") else "MISSING_DOCUMENT", source=out["urban_source"],
                           note=spec.get("urban_note"))
        else:
            top = max(_rank(r) for r in cands)
            best = sorted((r for r in cands if _rank(r) == top), key=lambda r: r["id"])
            vals = {_canon(r["value"]) for r in best}
            out["overridden"] = sorted(r["id"] for r in cands if _rank(r) < top)
            if len(vals) > 1:
                out.update(value=None, state="CONFLICT_REVIEW",
                           conflict=[{"id": r["id"], "value": r["value"], "source": _src(r)} for r in best],
                           note="PROJECT_RULE_CONFLICT (UP-RULES-001): " + " / ".join(
                               f"{r['id']} {r['value']}" for r in best) + " disagree for this element")
            else:
                states = {SOURCE_STATE[r["source"]["kind"]] for r in best}
                st = "OWNER_PROJECT_APPROVED" if "OWNER_PROJECT_APPROVED" in states else \
                    "PROJECT_SPECIFIED" if "PROJECT_SPECIFIED" in states else "DRAWING_CONFIRMED"
                out.update(value=copy.deepcopy(best[0]["value"]), state=st, project_rule_ids=[r["id"] for r in best],
                           source="; ".join(_src(r) for r in best))
        key = (rule_id, parameter, out["state"], _canon(out["value"]), tuple(out["project_rule_ids"]))
        self.log[key] = self.log.get(key, 0) + 1
        return out

    def usage(self):
        return [{"rule_id": k[0], "parameter": k[1], "state": k[2], "value": json.loads(k[3]),
                 "project_rule_ids": list(k[4]), "elements": n} for k, n in sorted(self.log.items())]


# ------------------------------------------------------------------------------------------------ the rules sheet
def _row(row_id, section, rule, rule_id, *, urban=None, urban_source=None, project=(), applied=None, source=None,
         status, trades=(), items=(), scope="PROJECT", notes="", **extra):
    if status not in STATES:
        raise ProjectRulesError(f"row {row_id}: status {status}")
    return dict({"row_id": row_id, "section": section, "rule": rule, "rule_id": rule_id,
                 "urban_standard": {"value": urban, "source": urban_source},
                 "drawing_specification": list(project), "applied_rule": {"value": applied},
                 "source": source, "status": status, "impact": {"trades": list(trades), "items": list(items)},
                 "scope": scope, "notes": notes}, **extra)


def _scope_text(sc):
    k = sc["kind"]
    bits = [k]
    for key in ("floor", "types", "categories", "point_m", "opening_id"):
        if sc.get(key):
            bits.append(f"{key}={sc[key]}")
    return " ".join(str(b) for b in bits)


def _fact_state(authority):
    a = str(authority or "").upper()
    return "DRAWING_CONFIRMED" if a.startswith("SOURCE") else "PROJECT_SPECIFIED" if a else "MISSING_DOCUMENT"


def _standard_rows(doc, res):
    rows = []
    for (rule_id, parameter), spec in PARAMETERS.items():
        project = [{"id": r["id"], "value": r["value"], "scope": _scope_text(r["scope"]), "source": _src(r)}
                   for r in doc.get("rules") or () if r.get("_supported") and r["rule_id"] == rule_id and
                   r["parameter"] == parameter]
        targets = ([{"door_category": c} for c in ("INTERNAL_PVC", "BATHROOM_PVC", "EXTERNAL_ALUMINIUM",
                                                   "MAIN_ENTRANCE")]
                   if parameter in ("required_nominal_door_m", "door_height_m") else
                   [{"codes": ["BATHROOM"]}, {"codes": ["BALCONY"]}] if rule_id.startswith("UP-WP") else [{}])
        for t in targets:
            label = spec["label"] + (f" - {t['door_category']}" if t.get("door_category") else
                                     " - wet areas" if t.get("codes") == ["BATHROOM"] else
                                     " - exterior (balcony / roof)" if t.get("codes") == ["BALCONY"] else "")
            if parameter == "required_nominal_door_m" and t.get("door_category") == "MAIN_ENTRANCE":
                rows.append(_row(f"S-{rule_id}-{parameter}-MAIN_ENTRANCE", spec["section"], label, "UP-DOOR-CLS-004",
                                 urban="as drawn", urban_source="registry UP-DOOR-CLS-004", applied="as drawn",
                                 source="the drawing (actual project dimensions)", status="DRAWING_CONFIRMED",
                                 trades=spec["trades"], items=spec["items"],
                                 notes="no ordinary opening standard is applied to the main entrance"))
                continue
            proj = Resolver(doc, bindings={r["id"]: {"state": "NOT_POINT_SCOPED"} for r in doc.get("rules") or ()})
            g = proj.get(rule_id, parameter, t)
            rows.append(_row(f"S-{rule_id}-{parameter}" + (f"-{t['door_category']}" if t.get("door_category") else
                                                          "-WET" if t.get("codes") == ["BATHROOM"] else
                                                          "-EXT" if t.get("codes") == ["BALCONY"] else ""),
                             spec["section"], label, rule_id, urban=g["urban_value"], urban_source=g["urban_source"],
                             project=project,
                             applied=g["value"], source=g["source"], status=g["state"], trades=spec["trades"],
                             items=spec["items"], scope="PROJECT (project-wide default; scoped rules below)",
                             notes=g.get("note") or ""))
    return rows


def _project_rule_rows(doc, bindings):
    rows = []
    rivals = defaultdict(list)                                  # a rule in a section-14 conflict is never "applied"
    for c in _conflict_rows(doc):
        a, b = (p_["id"] for p_ in c["drawing_specification"])
        rivals[a].append(b)
        rivals[b].append(a)
    for r in doc.get("rules") or ():
        spec = PARAMETERS.get((r.get("rule_id"), r.get("parameter")))
        b = bindings.get(r["id"]) or {}
        notes = []
        if spec is None:
            rows.append(_row(f"P-{r['id']}", "14_UNRESOLVED_CONFLICTS", f"{r.get('rule_id')} {r.get('parameter')}",
                             r.get("rule_id"), project=[{"id": r["id"], "value": r.get("value"),
                                                         "scope": _scope_text(r["scope"]), "source": _src(r)}],
                             applied=None, source=_src(r), status="ENGINE_LIMITATION", scope=_scope_text(r["scope"]),
                             notes="PROJECT_RULE_NOT_SUPPORTED: the engine has no parameter "
                                   f"{r.get('parameter')!r} for {r.get('rule_id')}; listed, never applied",
                             project_rule_id=r["id"]))
            continue
        t = {"door_category": (r["scope"].get("categories") or [None])[0],
             "codes": list(r["scope"].get("types") or [])}
        urban = spec["urban"](t) if spec.get("urban") else None
        status = SOURCE_STATE[r["source"]["kind"]]
        if b.get("state") == "UNBOUND":
            status = "CONFLICT_REVIEW"
            notes.append(f"PROJECT_RULE_UNBOUND (UP-RULES-001): {r['id']} names a point on {r['scope']['floor']} that "
                         "lies in no element of its kind; not applied")
        if rivals.get(r["id"]):
            status = "CONFLICT_REVIEW"
            notes.append(f"PROJECT_RULE_CONFLICT (UP-RULES-001): {r['id']} disagrees with "
                         f"{', '.join(sorted(rivals[r['id']]))} in the same scope; not applied (section 14)")
        rows.append(_row(f"P-{r['id']}", "15_OWNER_APPROVED_PROJECT_EXCEPTIONS"
                         if r["source"]["kind"] == "OWNER_PROJECT_APPROVAL" else spec["section"],
                         spec["label"], r["rule_id"], urban=urban,
                         urban_source=f"registry {r['rule_id']} ({K.rule_set()})",
                         project=[{"id": r["id"], "value": r["value"], "scope": _scope_text(r["scope"]),
                                   "source": _src(r)}],
                         applied=r["value"] if status != "CONFLICT_REVIEW" else None, source=_src(r), status=status,
                         trades=spec["trades"], items=spec["items"], scope=_scope_text(r["scope"]),
                         notes="; ".join(notes), project_rule_id=r["id"], binding=b))
    return rows


def _conflict_rows(doc):
    """pairs of project rules of the same rank that could meet one element with different values (a point-scoped
    pair is checked at resolution): listed in section 14."""
    rows = []
    rules = [r for r in doc.get("rules") or () if r.get("_supported") and r["scope"]["kind"] not in POINT_SCOPES]
    for i, a in enumerate(rules):
        for b in rules[i + 1:]:
            if (a["rule_id"], a["parameter"]) != (b["rule_id"], b["parameter"]) or _rank(a) != _rank(b):
                continue
            if _canon(a["value"]) == _canon(b["value"]):
                continue
            sa, sb = a["scope"], b["scope"]
            overlap = sa["kind"] == "PROJECT" or (
                sa.get("floor") == sb.get("floor") if sa["kind"] == "FLOOR" else
                bool(set(sa.get("types") or ()) & set(sb.get("types") or ())) if sa["kind"] == "LOCATION_TYPE" else
                bool(set(sa.get("categories") or ()) & set(sb.get("categories") or ())))
            if overlap:
                spec = PARAMETERS[(a["rule_id"], a["parameter"])]
                rows.append(_row(f"C-{a['id']}-{b['id']}", "14_UNRESOLVED_CONFLICTS", spec["label"], a["rule_id"],
                                 urban=spec["urban"]({}) if spec.get("urban") else None,
                                 project=[{"id": r["id"], "value": r["value"], "scope": _scope_text(r["scope"]),
                                           "source": _src(r)} for r in (a, b)],
                                 applied=None, source=f"{_src(a)} | {_src(b)}", status="CONFLICT_REVIEW",
                                 trades=spec["trades"], items=spec["items"], scope=_scope_text(sa),
                                 notes=f"PROJECT_RULE_CONFLICT (UP-RULES-001): {a['id']} and {b['id']} disagree; both "
                                       "kept, the affected quantities unresolved"))
    return rows


def _fixed_rows(doc, facts, decisions):
    f = facts or {}
    oh = f.get("opening_heights") or {}
    rows = []
    add = rows.append
    reg = {r["rule_id"]: r for r in K.registry()["rules"]}

    def std(rid, sec, rule, *, trades=(), items=(), notes="", status="OWNER_STANDARD_ASSUMED", applied=None):
        r = reg.get(rid)
        add(_row(f"F-{rid}", sec, rule, rid, urban=applied or (r or {}).get("title"),
                 urban_source=f"registry {rid} ({K.rule_set()})" if r else rid, applied=applied or "the Urban rule",
                 source=f"registry {rid}" if r else rid, status=status, trades=trades, items=items, notes=notes))
    # 02 architectural
    std("UP-KB-PREC-001", "02_ARCHITECTURAL_RULES", "source authority hierarchy; as drawn kept apart from required",
        trades=("ALL",))
    std("UP-RULES-001", "02_ARCHITECTURAL_RULES", "Level A Urban standards / Level B project rules", trades=("ALL",))
    dec = (decisions or {}).get("decisions") or []
    add(_row("F-UP-SPACE-002", "02_ARCHITECTURAL_RULES" if not dec else "15_OWNER_APPROVED_PROJECT_EXCEPTIONS",
             "project space decisions (interior / exterior status)", "UP-SPACE-002",
             urban="interior / exterior status from enclosure and connectivity (UP-SPACE-001)",
             urban_source="registry UP-SPACE-001", applied=f"{len(dec)} project decision(s)" if dec else "none given",
             source="URBAN_PROJECT_DECISIONS_V1" if dec else None,
             status="OWNER_PROJECT_APPROVED" if dec else "OWNER_STANDARD_ASSUMED", trades=("OPENINGS",),
             items=("DOOR classes",)))
    # 03 doors (fixed)
    std("UP-DOOR-CLS-005", "03_DOOR_STANDARDS", "elevator entrances excluded (elevator quotation schedule)",
        trades=("OPENINGS",))
    std("UP-DOOR-FEAS-001", "03_DOOR_STANDARDS", "door feasibility (5 classes, never a structural approval)",
        trades=("OPENINGS", "MASONRY"))
    # 04 windows
    add(_row("F-WINDOW-WIDTH", "04_WINDOWS", "window widths", None, urban="as drawn", applied="the CAD band opening",
             source="the drawing", status="DRAWING_CONFIRMED", trades=("ALUMINIUM",), items=("ARCH.WINDOW",)))
    w = oh.get("WINDOW")
    add(_row("F-WINDOW-HEIGHT", "04_WINDOWS", "window heights and sills", None, urban=None,
             applied=w.get("value_m") if w else None, source=(w or {}).get("authority"),
             status=_fact_state((w or {}).get("authority")), trades=("ALUMINIUM", "PLASTER", "PAINT", "WALL_FINISH"),
             items=("ARCH.WINDOW", "FIN.PLASTER", "FIN.PAINT", "FIN.WALL.TILE"),
             notes="" if w else "the window schedule / elevations"))
    add(_row("F-WINDOW-SCHEDULE", "04_WINDOWS", "window schedule", None, urban=None, applied=None, source=None,
             status="MISSING_DOCUMENT", trades=("ALUMINIUM",), items=("ARCH.WINDOW",),
             notes="no window schedule is read (types, sill / floor-level glazing)"))
    std("UP-REF-REVEAL-001", "04_WINDOWS", "reveal finishes (plaster default)", status="ENGINE_LIMITATION",
        trades=("PLASTER",), notes="an owner method kept for reference; no emitter in the architectural route")
    # 05 floor finishes
    std("UP-WET-001", "05_FLOOR_FINISHES", "owner wet areas and their finish scope", trades=("FLOOR_FINISH",
                                                                                            "WATERPROOFING"))
    std("UP-THR-001", "05_FLOOR_FINISHES", "marble thresholds at wet doorways, porcelain elsewhere",
        trades=("MARBLE", "FLOOR_FINISH"), items=("FIN.MARBLE.THRESHOLD",))
    fin = f.get("finishes") or {}
    add(_row("F-FLOOR-TILE-SIZES", "05_FLOOR_FINISHES", "selected floor tile sizes", "UP-CER-010", urban=None,
             applied=fin or None, source="facts finishes" if fin else None,
             status="PROJECT_SPECIFIED" if fin else "MISSING_DOCUMENT", trades=("FLOOR_FINISH",),
             items=("FIN.FLOOR (material)",), notes="" if fin else "the project finish specification"))
    std("UP-REF-CABINET-001", "05_FLOOR_FINISHES", "floor finish continues under cabinetry", status="ENGINE_LIMITATION",
        trades=("FLOOR_FINISH",), notes="an owner method kept for reference")
    # 06 wall finishes
    std("UP-FIN-WALL-001", "06_WALL_FINISHES", "full-height wall porcelain in wet areas", trades=("WALL_FINISH",),
        items=("FIN.WALL.TILE",))
    std("UP-FIN-PAINT-001", "06_WALL_FINISHES", "no paint over full-height porcelain", trades=("PAINT",))
    std("UP-FIN-PLASTER-001", "06_WALL_FINISHES", "door jamb and head plaster (by door category height)",
        trades=("PLASTER",), items=("FIN.PLASTER (door jambs)",))
    wh = f.get("wall_heights") or {}
    add(_row("F-WALL-HEIGHTS", "06_WALL_FINISHES", "wall finish heights", None, urban=None,
             applied={fl: {tr: v.get("value_m") for tr, v in t.items()} for fl, t in wh.items()} or None,
             source="facts wall_heights" if wh else None,
             status=(sorted({_fact_state(v.get("authority")) for t in wh.values() for v in t.values()}) or
                     ["MISSING_DOCUMENT"])[0], trades=("PLASTER", "PAINT", "WALL_FINISH"),
             items=("FIN.PLASTER", "FIN.PAINT", "FIN.WALL.TILE"), notes="" if wh else "sections / finish schedule"))
    # 07 skirting
    std("UP-SKIRT-001", "07_SKIRTING", "skirting on eligible dry-room wall boundaries", trades=("FLOOR_FINISH",),
        items=("FIN.SKIRTING",))
    # 08 waterproofing (fixed)
    for rid, txt in (("UP-WP-MAT-001", "net / installed / procurement kept apart; systems never combined"),
                     ("UP-WP-LAY-001", "deterministic layout and cutting plan"),
                     ("UP-WP-DOOR-001", "doorway transitions modelled on their own")):
        std(rid, "08_WATERPROOFING", txt, trades=("WATERPROOFING",), items=WP_ITEMS)
    # 09 ceilings
    std("UP-CEIL-001", "09_CEILINGS", "ceilings: actual eligible surfaces only", trades=("CEILING",),
        items=("FIN.CEILING",))
    add(_row("F-CEILING-TYPES", "09_CEILINGS", "ceiling types, bulkheads, coves", None, urban=None, applied=None,
             source=None, status="MISSING_DOCUMENT", trades=("CEILING",), items=("FIN.CEILING",),
             notes="the reflected ceiling plan"))
    # 10 stairs
    st = f.get("stairs") or {}
    add(_row("F-STAIR-GEOMETRY", "10_STAIRS", "stair rise / riser count", "UP-STAIR-002", urban=None,
             applied={fl: (v.get("riser_m") or {}).get("value_m") for fl, v in st.items()} or None,
             source="facts stairs" if st else None,
             status=(sorted({_fact_state((v.get("riser_m") or {}).get("authority")) for v in st.values()}) or
                     ["MISSING_DOCUMENT"])[0], trades=("STAIR_FINISH",), items=("FIN.MARBLE.RISER",),
             notes="" if st else "stair sections"))
    add(_row("F-STAIR-HALL", "10_STAIRS", "stair-hall wall finishes", None, urban=None, applied=None, source=None,
             status="MISSING_DOCUMENT", trades=("PLASTER", "PAINT"),
             notes="no owner policy: owner question OQ-03 (dry-room treatment proposed)"))
    # 11 structural
    add(_row("F-COLUMNS", "11_STRUCTURAL_MEASUREMENT", "columns", None, urban=None, applied="as drawn on the plan",
             source="the drawing (column layer)", status="DRAWING_CONFIRMED", trades=("CONCRETE",),
             items=("DOOR feasibility",)))
    add(_row("F-STRUCTURAL-DRAWINGS", "11_STRUCTURAL_MEASUREMENT", "structural drawings", None, urban=None,
             applied=None, source=None, status="ENGINE_LIMITATION", trades=("CONCRETE", "MASONRY"),
             notes="the architectural route does not read the structural drawings: load-bearing walls, beams and "
                   "lintels are not verified (route G measures the structure separately)"))
    # 12 openings and deductions
    d = oh.get("DOOR")
    add(_row("F-DOOR-HEIGHTS-DEDUCTIONS", "12_OPENINGS_AND_DEDUCTIONS", "door heights in wall-finish deductions",
             "UP-CER-009", urban="owner reference heights are not used for confirmed deductions",
             applied=d.get("value_m") if d else None, source=(d or {}).get("authority"),
             status=_fact_state((d or {}).get("authority")), trades=("PLASTER", "PAINT", "WALL_FINISH"),
             notes="" if d else "the door schedule (heights); the deduction stays a range"))
    add(_row("F-WINDOW-POSITION", "12_OPENINGS_AND_DEDUCTIONS", "window sill / head position in deductions",
             "UP-CER-009", urban=None, applied="full height inside the finish height", source=None,
             status="ENGINE_LIMITATION", trades=("PLASTER", "PAINT", "WALL_FINISH"),
             notes="WINDOW_POSITION_ASSUMED: sill / head levels are not in a plan"))
    std("UP-DOOR-DEP-001", "12_OPENINGS_AND_DEDUCTIONS", "an enlarged opening changes other trades (review)",
        trades=("OPENINGS", "MASONRY", "PLASTER", "PAINT"))
    # 13 external works
    std("UP-WP-ROOF-001", "13_EXTERNAL_WORKS", "roofs and balconies waterproofed", trades=("WATERPROOFING",),
        items=WP_ITEMS)
    add(_row("F-EXTERIOR-SCOPE", "13_EXTERNAL_WORKS", "exterior finish scope (interlock, external tiles)", None,
             urban=None, applied=None, source=None, status="MISSING_DOCUMENT", trades=("EXTERNAL_WORKS",),
             items=("ARCH.EXTERIOR",), notes="no owner policy: owner question OQ-04"))
    # 14 registry conflicts still open
    for c in K.registry()["conflicts"]:
        if c["state"] in ("OPEN", "CONFLICTED"):
            add(_row(f"F-{c['id']}", "14_UNRESOLVED_CONFLICTS", " vs ".join(c["between"]), c["id"], urban=None,
                     applied=c["resolution"], source=f"registry conflict {c['id']}", status="CONFLICT_REVIEW",
                     notes=c["resolution"]))
    return rows


def rules_sheet(doc=None, *, bindings=None, project_id, drawing, facts=None, decisions=None, resolver=None):
    """the Project Engineering Rules Sheet. The rule rows (and rules_sha256) depend only on the inputs - the registry,
    the project rules, the facts, the decisions - so the sheet exists before any quantity; `usage` (how often each
    resolution was applied) is evidence added after the run and is not hashed."""
    doc = doc or {"schema": SCHEMA, "rules": []}
    bindings = bindings or {}
    rows = _fixed_rows(doc, facts, decisions) + _standard_rows(doc, None) + _project_rule_rows(doc, bindings) + \
        _conflict_rows(doc)
    rows.insert(0, _row("F-PROJECT", "01_PROJECT_IDENTIFICATION", "project and drawing", None, urban=None,
                        applied={"project_id": project_id, "drawing": drawing.get("file"),
                                 "drawing_sha256": drawing.get("sha256"), "revision": doc.get("drawing_revision")},
                        source="the drawing file (sha256)", status="DRAWING_CONFIRMED", trades=("ALL",)))
    rows.insert(1, _row("F-REVISION", "01_PROJECT_IDENTIFICATION", "drawing revision", None, urban=None,
                        applied=doc.get("drawing_revision"), source="project rules" if doc.get("drawing_revision")
                        else None, status="PROJECT_SPECIFIED" if doc.get("drawing_revision") else "MISSING_DOCUMENT",
                        trades=("ALL",), notes="" if doc.get("drawing_revision") else "the drawing revision is not "
                                                                                      "stated"))
    rows.insert(2, _row("F-PROJECT-RULES", "01_PROJECT_IDENTIFICATION", "project rules input", "UP-RULES-001",
                        urban="the Urban standards (Level A)", applied=f"{len(doc.get('rules') or ())} project rule(s)",
                        source=SCHEMA if doc.get("rules") else None,
                        status="PROJECT_SPECIFIED" if doc.get("rules") else "OWNER_STANDARD_ASSUMED", trades=("ALL",),
                        notes="" if doc.get("rules") else "no project rules: every rule is the Urban standard"))
    ids = [r["row_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ProjectRulesError("duplicate rules-sheet row id")
    order = {s: i for i, s in enumerate(SECTIONS)}
    rows.sort(key=lambda r: (order[r["section"]], r["row_id"]))
    reg = {"rule_set": K.rule_set(), "digest": K.digest()}
    rules_part = {"registry": reg, "rows": [{k: v for k, v in r.items() if k not in ("binding",)} for r in rows
                                            if r["section"] != "01_PROJECT_IDENTIFICATION"],
                  "project_rules": [{k: v for k, v in r.items() if not k.startswith("_")}
                                    for r in doc.get("rules") or ()],
                  "bindings": {k: v for k, v in sorted(bindings.items())}}
    rules_sha = sha(rules_part)
    sheet = {"schema": SHEET_SCHEMA, "policy": POLICY_ID, "rule": "UP-RULES-001", "registry": reg,
             "project": {"project_id": project_id, "drawing": drawing, "revision": doc.get("drawing_revision"),
                         "rules_input": {"schema": doc.get("schema"), "rules": len(doc.get("rules") or ()),
                                         "sha256": sha([{k: v for k, v in r.items() if not k.startswith("_")}
                                                        for r in doc.get("rules") or ()])}},
             "states": list(STATES),
             "sections": [{"id": s, "rows": sum(1 for r in rows if r["section"] == s)} for s in SECTIONS],
             "rows": rows, "status_counts": {s: sum(1 for r in rows if r["status"] == s) for s in STATES},
             "rules_sha256": rules_sha}
    sheet["sheet_sha256"] = sha({"rules_sha256": rules_sha, "project": sheet["project"]})
    if resolver is not None:
        sheet["usage"] = resolver.usage()
    return sheet


def invalidation(old, new):
    """what a new rules sheet changes against the one the earlier outputs were computed with."""
    if old is None:
        return {"state": "FIRST_RUN", "changed": [], "affected_trades": [], "affected_items": []}
    if old.get("rules_sha256") == new["rules_sha256"]:
        return {"state": "UNCHANGED", "previous_rules_sha256": old.get("rules_sha256"), "changed": [],
                "affected_trades": [], "affected_items": []}
    o = {r["row_id"]: r for r in old.get("rows") or ()}
    n = {r["row_id"]: r for r in new["rows"]}
    changed = []
    for rid in sorted(set(o) | set(n)):
        a, b = o.get(rid), n.get(rid)
        if a is not None and b is not None and _canon((a["applied_rule"], a["status"], a["drawing_specification"])) \
                == _canon((b["applied_rule"], b["status"], b["drawing_specification"])):
            continue
        r = b or a
        changed.append({"row_id": rid, "rule_id": r.get("rule_id"), "project_rule_id": r.get("project_rule_id"),
                        "before": None if a is None else {"applied": a["applied_rule"]["value"], "status": a["status"]},
                        "after": None if b is None else {"applied": b["applied_rule"]["value"], "status": b["status"]},
                        "trades": r["impact"]["trades"], "items": r["impact"]["items"]})
    return {"state": "RULES_CHANGED", "previous_rules_sha256": old.get("rules_sha256"), "changed": changed,
            "affected_trades": sorted({t for c in changed for t in c["trades"]}),
            "affected_items": sorted({i for c in changed for i in c["items"]}),
            "action": "every quantity was recomputed from the drawing with the new sheet; the outputs of the earlier "
                      "sheet were moved aside (SUPERSEDED_<n>), never reused"}


CSV_COLUMNS = ("row_id", "section", "rule", "rule_id", "urban_standard", "drawing_specification", "applied_rule",
               "source", "status", "impact", "scope", "notes")


def csv_rows(sheet):
    out = []
    for r in sheet["rows"]:
        out.append({"row_id": r["row_id"], "section": r["section"], "rule": r["rule"], "rule_id": r["rule_id"],
                    "urban_standard": _canon(r["urban_standard"]["value"]),
                    "drawing_specification": "; ".join(f"{p['id']}={_canon(p['value'])} ({p['scope']}; {p['source']})"
                                                       for p in r["drawing_specification"]),
                    "applied_rule": _canon(r["applied_rule"]["value"]), "source": r["source"], "status": r["status"],
                    "impact": " / ".join(r["impact"]["trades"]) + (" : " + ", ".join(r["impact"]["items"])
                                                                    if r["impact"]["items"] else ""),
                    "scope": r["scope"], "notes": r["notes"]})
    return out


def policy_record():
    return {"policy": POLICY_ID, "rule": "UP-RULES-001", "schema": SCHEMA, "sheet_schema": SHEET_SCHEMA,
            "states": list(STATES), "scopes": dict(RANK), "sections": list(SECTIONS),
            "parameters": [f"{a} {b}" for a, b in PARAMETERS], "engine_pier_m": ENGINE_PIER_M}
