"""CANONICAL BOQ LINE (M9 S1) - one payable physical measurement per line, bilingual, traceable (generic; stdlib only).

    make_line(**fields)              -> a validated line (URBAN_CANONICAL_BOQ_LINE_V1); raises LineError on any breach
    validate(line)                   -> the line, or LineError
    totals(lines, by=("floor",))     -> {group: {unit: {"net", "lines", "bounded_low", "bounded_high"}}} - like units only
    from_route_g(item, project, ...) -> a line from a route G item (engine.source.provisional_estimate)
    adapt(vocabulary, state, **ctx)  -> (evidence_state, approval_state) for a legacy state; never raises a state
    item_name(item_code)             -> {"en", "ar"} from the item master

Two state axes, never one word for both:
    evidence   MEASURED > SOURCE_DERIVED > PROVISIONAL > BOUNDED_EXPOSURE > BLOCKED_RFI   (+ EXCLUDED_WITH_REASON,
               NOT_APPLICABLE_WITH_EVIDENCE: terminal, no quantity)
    approval   MACHINE_ONLY -> REVIEWED -> APPROVED -> RELEASED_FOR_PRICING   (+ INVALIDATED on a revision change)

Waste, procurement and a commercial basis are VIEWS that reference a line (material_result.py); they are never added
to its measured_net and never summed with it. There is no price, rate or amount field anywhere: a key that looks like
one is refused.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict

SCHEMA = "URBAN_CANONICAL_BOQ_LINE_V1"
EVIDENCE = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL", "BOUNDED_EXPOSURE", "BLOCKED_RFI", "EXCLUDED_WITH_REASON",
            "NOT_APPLICABLE_WITH_EVIDENCE")
QUANTITY_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
TERMINAL_NO_QUANTITY = ("BLOCKED_RFI", "EXCLUDED_WITH_REASON", "NOT_APPLICABLE_WITH_EVIDENCE")
RANK = {"MEASURED": 5, "SOURCE_DERIVED": 4, "PROVISIONAL": 3, "BOUNDED_EXPOSURE": 2, "BLOCKED_RFI": 1,
        "EXCLUDED_WITH_REASON": 0, "NOT_APPLICABLE_WITH_EVIDENCE": 0}
APPROVAL = ("MACHINE_ONLY", "REVIEWED", "APPROVED", "RELEASED_FOR_PRICING", "INVALIDATED")
UNITS = ("m2", "lm", "m3", "kg", "t", "pcs", "item", "m")
TRADES = ("EARTHWORKS", "CONCRETE", "REINFORCEMENT", "FORMWORK", "MASONRY", "PLASTER", "PAINT", "FLOOR_FINISH",
          "WALL_FINISH", "CEILING", "WATERPROOFING", "STAIR_FINISH", "RAILING", "MARBLE", "OPENINGS", "ALUMINIUM",
          "ROOFING", "FACADE", "EXTERNAL_WORKS", "MEP", "OTHER")
GEOMETRY_SOURCE = ("CAD_VECTOR", "PDF_VECTOR", "PDF_RASTER_CALIBRATED", "SCHEDULE_ONLY", "OWNER_FACT", "CONVENTION",
                   "SYNTHETIC_FIXTURE")
MATERIAL_STATE = ("SOURCE", "PROJECT_OWNER_FACT", "URBAN_METHOD", "BY_SPEC")
PRICE_WORDS = ("price", "rate", "amount", "cost", "kwd", "fils", "value_money")
NOT_A_PRICE = ("price_one_basis",)          # a measure-pair instruction (bill one basis), not a money field
AGENT_ROLES = ("AGENT", "MODEL", "LLM", "AI")

# item master: canonical code -> (en, ar, trade, unit); Arabic from the M9A glossary (construction vocabulary only)
ITEMS = {
    "STR.CONC.BLINDING": ("Blinding (plain concrete)", "خرسانة نظافة", "CONCRETE", "m3"),
    "STR.CONC.FOOTING": ("Footings", "قواعد", "CONCRETE", "m3"),
    "STR.CONC.NECK": ("Foundation necks", "رقاب الأعمدة", "CONCRETE", "m3"),
    "STR.CONC.STRAP": ("Strap / tie beams", "شناجات", "CONCRETE", "m3"),
    "STR.CONC.GROUND_BEAM": ("Ground beams", "ميدات", "CONCRETE", "m3"),
    "STR.CONC.GROUND_SLAB": ("Ground slab", "بلاطة أرضية", "CONCRETE", "m3"),
    "STR.CONC.COLUMN": ("Columns", "أعمدة", "CONCRETE", "m3"),
    "STR.CONC.BEAM": ("Suspended beams", "كمرات", "CONCRETE", "m3"),
    "STR.CONC.SLAB": ("Suspended slabs", "بلاطات", "CONCRETE", "m3"),
    "STR.CONC.LINTEL": ("Lintels", "عتب", "CONCRETE", "m3"),
    "STR.CONC.STAIR": ("Stair concrete", "خرسانة الدرج", "CONCRETE", "m3"),
    "STR.CONC.DOME": ("Domes and rings", "قباب", "CONCRETE", "m3"),
    "STR.CONC.POOL": ("Swimming pool concrete", "خرسانة المسبح", "CONCRETE", "m3"),
    "STR.CONC.TANK": ("Water tank concrete", "خرسانة الخزان", "CONCRETE", "m3"),
    "STR.CONC.LIFT": ("Lift pit concrete", "خرسانة حفرة المصعد", "CONCRETE", "m3"),
    "STR.CONC.BOUNDARY_WALL": ("Boundary wall concrete", "خرسانة السور", "CONCRETE", "m3"),
    "STR.CONC.PARAPET": ("RC parapets", "دروة خرسانية", "CONCRETE", "m3"),
    "STR.CONC.OTHER": ("Other reinforced concrete", "خرسانة مسلحة أخرى", "CONCRETE", "m3"),
    "STR.REBAR": ("Reinforcement", "حديد تسليح", "REINFORCEMENT", "kg"),
    "FIN.FLOOR.PORCELAIN": ("Floor porcelain", "بورسلان أرضيات", "FLOOR_FINISH", "m2"),
    "FIN.FLOOR.WET_TILE": ("Wet-room floor tile", "سيراميك أرضيات الحمامات", "FLOOR_FINISH", "m2"),
    "FIN.WALL.TILE": ("Wall porcelain / ceramic", "سيراميك جدران", "WALL_FINISH", "m2"),
    "FIN.SKIRTING": ("Skirting", "نعلة", "FLOOR_FINISH", "lm"),
    "FIN.WP.FLOOR": ("Wet-room floor waterproofing", "عازل أرضيات الحمامات", "WATERPROOFING", "m2"),
    "FIN.WP.DOORWAY": ("Doorway waterproofing continuation", "عازل عند الباب", "WATERPROOFING", "m2"),
    "FIN.WP.UPTURN": ("Waterproofing upturn 0.20 m incl. doorway", "رفعة العازل 20 سم شاملة الباب", "WATERPROOFING", "m2"),
    "FIN.CEILING": ("Ceiling area", "مساحة الأسقف", "CEILING", "m2"),
    "FIN.PLASTER": ("Internal plaster", "لياسة داخلية", "PLASTER", "m2"),
    "FIN.PAINT": ("Internal paint", "صبغ داخلي", "PAINT", "m2"),
    "FIN.MARBLE.TREAD": ("Stair tread marble", "رخام نايم", "STAIR_FINISH", "m2"),
    "FIN.MARBLE.RISER": ("Stair visible riser marble", "رخام قائم", "STAIR_FINISH", "m2"),
    "FIN.RAILING": ("Stair guardrail (sloping length)", "درابزين الدرج", "RAILING", "lm"),
    "FIN.HANDRAIL": ("Wall-mounted handrail", "مسكة الدرج", "RAILING", "lm"),
    # M9 S2 architectural route
    "ARCH.SPACE": ("Space floor area (finish to be confirmed)", "مساحة الفراغ", "FLOOR_FINISH", "m2"),
    "ARCH.EXTERIOR": ("External / roof space area", "مساحة خارجية", "EXTERNAL_WORKS", "m2"),
    "ARCH.DOOR": ("Door opening", "فتحة باب", "OPENINGS", "pcs"),
    "ARCH.WINDOW": ("Window / glazed opening", "فتحة شباك", "OPENINGS", "pcs"),
    "ARCH.PASSAGE": ("Opening without a door", "فتحة بدون باب", "OPENINGS", "pcs"),
    "FIN.STAIR.FLIGHT": ("Stair flight (sloping length)", "طول الدرج المائل", "STAIR_FINISH", "lm"),
}
# route G family (+ storey) -> item code
ROUTE_G_FAMILY = {"PLAIN_CONCRETE": "STR.CONC.BLINDING", "FOOTINGS": "STR.CONC.FOOTING", "GROUND_SLAB": "STR.CONC.GROUND_SLAB",
                  "BEAMS": "STR.CONC.BEAM", "SLABS": "STR.CONC.SLAB", "LINTELS": "STR.CONC.LINTEL",
                  "STAIRS": "STR.CONC.STAIR", "DOMES": "STR.CONC.DOME", "POOL": "STR.CONC.POOL",
                  "WATER_TANK": "STR.CONC.TANK", "LIFT": "STR.CONC.LIFT", "BOUNDARY_WALL": "STR.CONC.BOUNDARY_WALL",
                  "PARAPETS": "STR.CONC.PARAPET"}

# legacy vocabularies -> canonical (evidence, approval); a state not listed is refused, never defaulted
LEGACY = {
    "provisional_estimate": {"VERIFIED": "MEASURED", "PROVISIONAL": "PROVISIONAL", "UNRESOLVED": "BLOCKED_RFI"},
    "quantity_release": {"INDEPENDENTLY_CHECKED": "MEASURED", "SOURCE_SUPPORTED": "SOURCE_DERIVED",
                         "PROVISIONAL": "PROVISIONAL", "GEOMETRICALLY_MEASURED": "PROVISIONAL",
                         "CLASSIFIED": "BLOCKED_RFI", "DETECTED": "BLOCKED_RFI", "UNRESOLVED": "BLOCKED_RFI",
                         "ENGINEER_REVIEWED": None, "ENGINEER_APPROVED": None, "EXCLUDED": "EXCLUDED_WITH_REASON"},
    "scope_quantities": {"MEASURED": "PROVISIONAL", "BOUNDED": "BOUNDED_EXPOSURE"},
    "family_coverage": {"QUANTIFIED": "PROVISIONAL", "PARTLY_QUANTIFIED": "PROVISIONAL",
                        "BOUNDED_NOT_MEASURED": "BOUNDED_EXPOSURE", "DETECTED_NOT_QUANTIFIED": "BLOCKED_RFI",
                        "NO_EVIDENCE_FOUND": "BLOCKED_RFI", "COUNTED_IN_PARENT": "NOT_APPLICABLE_WITH_EVIDENCE"},
    "arch_quantity_truth": {"VERIFIED_COMPLETE": "MEASURED", "VERIFIED_PARTIAL_LOWER_BOUND": "BOUNDED_EXPOSURE",
                            "PROVISIONAL": "PROVISIONAL", "BLOCKED": "BLOCKED_RFI", "NOT_IN_SCOPE": "EXCLUDED_WITH_REASON"},
    "boq_canonical": {"COMPUTED_SHADOW_COMPLETE": "MEASURED", "RELEASED": "MEASURED", "AUTHORISED_SUBTOTAL": "PROVISIONAL",
                      "BLOCKED": "BLOCKED_RFI"},
    "finishes_rules": {"MEASURED": "SOURCE_DERIVED", "NOT_ESTABLISHED": "BLOCKED_RFI"},
}
# the strongest canonical state each legacy word can justify by its own definition (the "never raise" ceiling)
CEILING = {
    "provisional_estimate": {"VERIFIED": "MEASURED", "PROVISIONAL": "SOURCE_DERIVED", "UNRESOLVED": "BOUNDED_EXPOSURE"},
    "quantity_release": {"INDEPENDENTLY_CHECKED": "MEASURED", "SOURCE_SUPPORTED": "SOURCE_DERIVED", "PROVISIONAL": "PROVISIONAL",
                         "GEOMETRICALLY_MEASURED": "PROVISIONAL", "CLASSIFIED": "BLOCKED_RFI", "DETECTED": "BLOCKED_RFI",
                         "UNRESOLVED": "BOUNDED_EXPOSURE", "EXCLUDED": "EXCLUDED_WITH_REASON"},
    "scope_quantities": {"MEASURED": "PROVISIONAL", "BOUNDED": "BOUNDED_EXPOSURE"},
    "family_coverage": {"QUANTIFIED": "SOURCE_DERIVED", "PARTLY_QUANTIFIED": "PROVISIONAL",
                        "BOUNDED_NOT_MEASURED": "BOUNDED_EXPOSURE", "DETECTED_NOT_QUANTIFIED": "BLOCKED_RFI",
                        "NO_EVIDENCE_FOUND": "BLOCKED_RFI", "COUNTED_IN_PARENT": "NOT_APPLICABLE_WITH_EVIDENCE"},
    "arch_quantity_truth": {"VERIFIED_COMPLETE": "MEASURED", "VERIFIED_PARTIAL_LOWER_BOUND": "BOUNDED_EXPOSURE",
                            "PROVISIONAL": "PROVISIONAL", "BLOCKED": "BLOCKED_RFI", "NOT_IN_SCOPE": "EXCLUDED_WITH_REASON"},
    "boq_canonical": {"COMPUTED_SHADOW_COMPLETE": "MEASURED", "RELEASED": "MEASURED", "AUTHORISED_SUBTOTAL": "PROVISIONAL",
                      "BLOCKED": "BLOCKED_RFI"},
    "finishes_rules": {"MEASURED": "SOURCE_DERIVED", "NOT_ESTABLISHED": "BLOCKED_RFI"},
}
APPROVAL_FROM = {("quantity_release", "ENGINEER_REVIEWED"): "REVIEWED",
                 ("quantity_release", "ENGINEER_APPROVED"): "APPROVED"}


class LineError(ValueError):
    pass


def weaker(a, b):
    """the weaker of two evidence states (the weakest input governs)."""
    return a if RANK[a] <= RANK[b] else b


def adapt(vocabulary, state, *, has_exposure=False, support=None, decision_valid=False):
    """-> (evidence, approval). support (route G): SOURCE_COMPLETE_UNREVIEWED lets a PROVISIONAL item read SOURCE_DERIVED
    (every dimension drawn or printed). An UNRESOLVED / unquantified state with an exposure range reads BOUNDED_EXPOSURE.
    RELEASED_FOR_PRICING needs a valid engineer decision on this revision (decision_valid)."""
    table = LEGACY.get(vocabulary)
    if table is None:
        raise LineError(f"no adapter for vocabulary {vocabulary!r}")
    if state not in table:
        raise LineError(f"{vocabulary}: state {state!r} has no canonical mapping (refused, never defaulted)")
    approval = APPROVAL_FROM.get((vocabulary, state), "MACHINE_ONLY")
    ev = table[state]
    if ev is None:                                  # an approval-only state: evidence comes from the item itself
        return None, approval
    if vocabulary == "provisional_estimate" and state == "PROVISIONAL" and support == "SOURCE_COMPLETE_UNREVIEWED":
        ev = "SOURCE_DERIVED"
    if ev == "BLOCKED_RFI" and has_exposure and state in ("UNRESOLVED",):
        ev = "BOUNDED_EXPOSURE"
    if vocabulary == "boq_canonical" and state == "RELEASED":
        approval = "RELEASED_FOR_PRICING" if decision_valid else "MACHINE_ONLY"
    ceiling = CEILING[vocabulary][state]
    if RANK[ev] > RANK[ceiling]:                     # cannot happen by construction; kept as the guard the tests pin
        raise LineError(f"{vocabulary}:{state} would raise {ceiling} to {ev}")
    return ev, approval


def item_name(code):
    if code not in ITEMS:
        raise LineError(f"unknown item code {code}")
    en, ar, _t, _u = ITEMS[code]
    return {"en": en, "ar": ar}


def _no_price(obj, path="line"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            lk = str(k).lower()
            if lk not in NOT_A_PRICE and any(w == lk or lk.startswith(w + "_") or lk.endswith("_" + w)
                                             for w in PRICE_WORDS):
                raise LineError(f"{path}.{k}: price / rate / amount fields are not part of the engine output")
            _no_price(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _no_price(v, f"{path}[{i}]")


def line_id(project_id, item_code, element_id, rule_id, rule_version, unit):
    key = "|".join(str(x) for x in (project_id, item_code, element_id, rule_id, rule_version, unit))
    return "L-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]


def make_line(*, project_id, revision_set_sha256, item_code, unit, evidence_state, measured_net=None, element_id,
              floor=None, room_id=None, room_name_en=None, room_name_ar=None, physical_element=None, gross=None,
              deductions=(), additions=(), bounded_range=None, formula, inputs=None, documents=(),
              geometry_source="CAD_VECTOR", geometry_confidence="TOLERANCE_CERTIFIED", rule_id, rule_version,
              rule_set=None, rule_set_digest=None, conventions_used=(), material_state="BY_SPEC",
              approval_state="MACHINE_ONLY", review=None, rfi=None, measure_pair=None, never_additive_with=(),
              notes="", subtrade=None, item_en=None, item_ar=None, trade=None):
    if item_code in ITEMS:
        en, ar, tr, _u = ITEMS[item_code]
    else:
        en, ar, tr = item_en, item_ar, trade
    line = {"schema": SCHEMA,
            "line_id": line_id(project_id, item_code, element_id, rule_id, rule_version, unit),
            "item_code": item_code, "item_en": item_en or en, "item_ar": item_ar or ar, "trade": trade or tr,
            "subtrade": subtrade,
            "project": {"project_id": project_id, "revision_set_sha256": revision_set_sha256},
            "location": {"floor": floor, "room_id": room_id, "room_name_en": room_name_en, "room_name_ar": room_name_ar,
                         "element_id": element_id},
            "physical_element": physical_element, "unit": unit,
            "gross": gross, "deductions": list(deductions), "additions": list(additions),
            "measured_net": measured_net, "bounded_range": bounded_range,
            "calculation": {"formula": formula, "inputs": inputs or {}},
            "source": {"documents": list(documents), "geometry_source": geometry_source,
                       "geometry_confidence": geometry_confidence},
            "rule": {"rule_id": rule_id, "version": rule_version, "rule_set": rule_set, "rule_set_digest": rule_set_digest,
                     "conventions_used": list(conventions_used)},
            "material_state": material_state, "evidence_state": evidence_state, "approval_state": approval_state,
            "review": review, "rfi": rfi, "measure_pair": measure_pair,
            "never_additive_with": list(never_additive_with), "notes": notes}
    return validate(line)


def validate(line):
    req = ("line_id", "item_code", "item_en", "item_ar", "trade", "unit", "evidence_state", "approval_state", "project",
           "location", "source", "rule", "calculation")
    miss = [k for k in req if line.get(k) in (None, "")]
    if miss:
        raise LineError(f"{line.get('line_id')}: missing {miss}")
    _no_price(line)
    if line["trade"] not in TRADES:
        raise LineError(f"trade {line['trade']}")
    if line["unit"] not in UNITS:
        raise LineError(f"unit {line['unit']}")
    ev, ap = line["evidence_state"], line["approval_state"]
    if ev not in EVIDENCE:
        raise LineError(f"evidence {ev}")
    if ap not in APPROVAL:
        raise LineError(f"approval {ap}")
    if not line["calculation"].get("formula"):
        raise LineError("every line states its formula")
    if line["source"]["geometry_source"] not in GEOMETRY_SOURCE:
        raise LineError(f"geometry source {line['source']['geometry_source']}")
    if line["material_state"] not in MATERIAL_STATE:
        raise LineError(f"material state {line['material_state']}")
    net = line["measured_net"]
    if ev in QUANTITY_STATES:
        if not isinstance(net, (int, float)) or net < -1e-9:
            raise LineError(f"{line['line_id']}: a {ev} line carries a non-negative measured_net")
    elif net is not None:
        raise LineError(f"{line['line_id']}: a {ev} line carries no measured_net")
    if ev == "BOUNDED_EXPOSURE":
        br = line.get("bounded_range") or {}
        if br.get("low") is None or br.get("high") is None or br["low"] > br["high"] + 1e-9:
            raise LineError(f"{line['line_id']}: a bounded line needs low <= high")
    if ev == "BLOCKED_RFI" and not (line.get("rfi") or {}).get("question"):
        raise LineError(f"{line['line_id']}: a blocked line names the question that unlocks it")
    if ev in ("EXCLUDED_WITH_REASON", "NOT_APPLICABLE_WITH_EVIDENCE") and not line.get("notes"):
        raise LineError(f"{line['line_id']}: {ev} needs its reason")
    if ap in ("APPROVED", "RELEASED_FOR_PRICING"):
        rv = line.get("review") or {}
        if not rv.get("reviewer") or not rv.get("role") or not rv.get("decision_sha256"):
            raise LineError(f"{line['line_id']}: {ap} needs a reviewer, a role and the decision it rests on")
        if str(rv["role"]).upper() in AGENT_ROLES:
            raise LineError(f"{line['line_id']}: an agent cannot approve")
        if ev not in QUANTITY_STATES:
            raise LineError(f"{line['line_id']}: a {ev} line cannot be {ap}")
    mp = line.get("measure_pair")
    if mp is not None and mp.get("price_one_basis") is not True:
        raise LineError(f"{line['line_id']}: a measure pair always says price ONE basis")
    return line


def totals(lines, by=("floor",)):
    """like-unit sums of measured_net for quantity states, per group; bounded lines are summed as ranges apart; a line
    that names another as never-additive with it is not summed twice (the first one in the list wins)."""
    out = defaultdict(lambda: defaultdict(lambda: {"net": 0.0, "lines": 0, "bounded_low": 0.0, "bounded_high": 0.0,
                                                   "bounded_lines": 0, "blocked_lines": 0}))
    seen, skip = set(), set()
    for ln in lines:
        validate(ln)
        if ln["line_id"] in skip:
            continue
        seen.add(ln["line_id"])
        skip.update(x for x in ln["never_additive_with"] if x not in seen)
        g = tuple((ln["location"].get(k) if k in ln["location"] else ln.get(k)) for k in by)
        cell = out[g][ln["unit"]]
        ev = ln["evidence_state"]
        if ev in QUANTITY_STATES:
            cell["net"] += ln["measured_net"]
            cell["lines"] += 1
        elif ev == "BOUNDED_EXPOSURE":
            cell["bounded_low"] += ln["bounded_range"]["low"]
            cell["bounded_high"] += ln["bounded_range"]["high"]
            cell["bounded_lines"] += 1
        elif ev == "BLOCKED_RFI":
            cell["blocked_lines"] += 1
    return {g: dict(v) for g, v in out.items()}


def _route_g_code(item):
    fam, st = item["family"], item.get("storey")
    if item["trade"] == "REINFORCEMENT":
        return "STR.REBAR"
    if fam == "COLUMNS":
        return "STR.CONC.NECK" if st == "FOUNDATION" else "STR.CONC.COLUMN"
    if fam == "GROUND_BEAMS":
        return "STR.CONC.STRAP" if st == "FOUNDATION" else "STR.CONC.GROUND_BEAM"
    return ROUTE_G_FAMILY.get(fam, "STR.CONC.OTHER")


def from_route_g(item, *, project_id, revision_set_sha256, conventions_set, conventions_digest, documents=()):
    """a route G item (provisional_estimate) as a canonical line. VERIFIED -> MEASURED; PROVISIONAL -> PROVISIONAL
    (SOURCE_DERIVED when every dimension is drawn or printed); UNRESOLVED -> BOUNDED_EXPOSURE with the item's exposure,
    else BLOCKED_RFI with its blocker as the question. The numbers are the item's own; nothing is recomputed."""
    has_exp = item.get("exposure_low") is not None and item.get("exposure_high") is not None
    ev, ap = adapt("provisional_estimate", item["category"], has_exposure=has_exp, support=item.get("support"))
    code = _route_g_code(item)
    net = item["base"] if ev in QUANTITY_STATES else None
    br = None
    if ev in QUANTITY_STATES and item.get("low") is not None:
        br = {"low": item["low"], "high": item["high"], "basis": "the item's own convention range"}
    if ev == "BOUNDED_EXPOSURE":
        br = {"low": item["exposure_low"], "high": item["exposure_high"], "basis": "the item's exposure range"}
    rfi = {"question": item.get("blocker") or "unresolved", "unlocks": item["item_id"]} if ev in ("BLOCKED_RFI", "BOUNDED_EXPOSURE") else None
    sub = f"{item['family']}" + (f" / {item['dia_mm']} mm" if item.get("dia_mm") else "")
    return make_line(project_id=project_id, revision_set_sha256=revision_set_sha256, item_code=code, unit=item["unit"],
                     evidence_state=ev, approval_state=ap, measured_net=net, bounded_range=br,
                     element_id=item["item_id"], floor=item.get("storey"), physical_element=item["family"],
                     subtrade=sub, formula=item.get("formula") or ("unresolved: " + (item.get("blocker") or "")),
                     inputs={"dimensions": item.get("dimensions") or {}, "support": item.get("support"),
                             "assumptions": item.get("assumptions") or []},
                     documents=documents, geometry_source="CAD_VECTOR",
                     geometry_confidence="TOLERANCE_CERTIFIED" if ev in QUANTITY_STATES else "INFERRED_CANDIDATE",
                     rule_id=conventions_set, rule_version="conventions", rule_set=conventions_set,
                     rule_set_digest=conventions_digest, conventions_used=list(item.get("assumptions") or []),
                     material_state="SOURCE" if item["trade"] == "REINFORCEMENT" else "BY_SPEC", rfi=rfi,
                     notes=item.get("limitations") or "")


def dumps(lines):
    """byte-deterministic JSON of a list of lines."""
    return json.dumps([validate(x) for x in lines], indent=1, sort_keys=True, ensure_ascii=False) + "\n"


CSV_COLUMNS = ("line_id", "floor", "room_id", "room_name_en", "room_name_ar", "trade", "subtrade", "item_code", "item_en",
               "item_ar", "physical_element", "unit", "gross", "measured_net", "bounded_low", "bounded_high",
               "evidence_state", "approval_state", "material_state", "formula", "rule_id", "rule_version", "rfi", "notes")


def csv_rows(lines):
    for ln in lines:
        br = ln.get("bounded_range") or {}
        yield {"line_id": ln["line_id"], "floor": ln["location"].get("floor"), "room_id": ln["location"].get("room_id"),
               "room_name_en": ln["location"].get("room_name_en"), "room_name_ar": ln["location"].get("room_name_ar"),
               "trade": ln["trade"], "subtrade": ln.get("subtrade"), "item_code": ln["item_code"], "item_en": ln["item_en"],
               "item_ar": ln["item_ar"], "physical_element": ln.get("physical_element"), "unit": ln["unit"],
               "gross": ln.get("gross"), "measured_net": ln.get("measured_net"), "bounded_low": br.get("low"),
               "bounded_high": br.get("high"), "evidence_state": ln["evidence_state"],
               "approval_state": ln["approval_state"], "material_state": ln["material_state"],
               "formula": ln["calculation"]["formula"], "rule_id": ln["rule"]["rule_id"],
               "rule_version": ln["rule"]["version"], "rfi": (ln.get("rfi") or {}).get("question"), "notes": ln.get("notes")}
