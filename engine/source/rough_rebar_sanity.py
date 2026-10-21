"""ROUGH_REBAR_SUMMARY - the Urban estimating / sanity product (generic).

    ROUGH_REBAR_KG = STRUCTURAL_CONCRETE_M3 x CATEGORY_RATIO_KG_M3          (per configured category)

A completely separate product from ACCURATE_BOQ_REBAR (engine/source/accurate_boq_rebar.py). Its only input is the
final concrete register; it never receives, reads, completes or changes an accurate reinforcement quantity, never
sets a release status, never feeds procurement and is never a fallback when a BBS cannot be calculated. The two
products meet only in the report layer (engine/source/rebar_sanity_variance.py, engine/source/rebar_boq_sections.py).

Rules
  * every concrete occurrence is classified into ONE structural element class, mapped explicitly to ONE rough
    category; an occurrence entered twice is an error;
  * an element class without an unambiguous mapping (RAFT, PILE_CAP, RETAINING_WALL, WATER_TANK, LIFT_*, PARAPET_*,
    LINTEL, SPECIAL_RC_ELEMENT, ...) or a category without a ratio is ROUGH_RATIO_NOT_CONFIGURED - no guess;
  * concrete is carried by release state; the RELEASED basis (verified + lower bound) and the MODELLED basis
    (+ provisional) are reported separately; BLOCKED concrete never enters a rough figure;
  * the ratios are a PROFILE (URBAN_OWNER_ESTIMATING_RULE, SANITY_CHECK_ONLY) supplied as data - none is written here.
Stdlib only.
"""

from __future__ import annotations

from collections import defaultdict

PRODUCT = "ROUGH_REBAR_SUMMARY"
POLICY_ID = "ROUGH_REBAR_SUMMARY_V2"
TITLE_EN = "ROUGH REBAR SUMMARY"
TITLE_AR = "تقدير تقريبي للحديد حسب حجم الخرسانة"
AUTHORITY = "URBAN_OWNER_ESTIMATING_RULE"
USE = "SANITY_CHECK_ONLY"
MANDATORY_NOTE = ("ROUGH REBAR SUMMARY is an estimating and sanity-check tool only. It is not a reinforcement takeoff "
                  "and must not replace the ACCURATE BOQ REBAR / BBS quantity.")
NOT_CONFIGURED = "ROUGH_RATIO_NOT_CONFIGURED"
CONCRETE_STATES = ("VERIFIED", "LOWER_BOUND", "PROVISIONAL", "BLOCKED")
RELEASED_STATES = ("VERIFIED", "LOWER_BOUND")
MODELLED_STATES = ("VERIFIED", "LOWER_BOUND", "PROVISIONAL")
ROUGH_CATEGORIES = ("FOUNDATIONS_RELATED", "GROUND_BEAMS_AND_GROUND_SLAB", "WALLS_AND_COLUMNS", "BEAMS", "SLABS",
                    "STAIRS_AND_DOME", "SWIMMING_POOL")

# structural usage groups (element classes)
ELEMENT_CLASSES = (
    "FOUNDATION_PAD", "COMBINED_FOOTING", "STRIP_FOOTING", "RAFT", "PILE_CAP", "FOUNDATION_NECK",
    "FOUNDATION_STRAP_BEAM",
    "GROUND_BEAM", "GROUND_SLAB", "BOUNDARY_GROUND_BEAM",
    "COLUMN", "STRUCTURAL_WALL", "RETAINING_WALL",
    "BEAM", "CONTINUOUS_BEAM", "RING_BEAM", "LINTEL", "BEAM_COLUMN_JOINT",
    "SOLID_SLAB", "FLAT_SLAB", "RIBBED_SLAB",
    "STAIR", "DOME",
    "POOL_BASE", "POOL_WALL", "POOL_BEAM",
    "PARAPET_RC", "PARAPET_STIFFENER_COLUMN", "PARAPET_TOP_RING_BEAM",
    "LIFT_PIT", "LIFT_WALL", "LIFT_TIE_BEAM",
    "WATER_TANK", "SPECIAL_RC_ELEMENT",
    "PLAIN_CONCRETE",          # blinding / lean concrete: never reinforced, never in a rough category
)

# explicit default mapping element class -> rough category; a profile may replace it. Classes absent here are
# deliberately NOT_CONFIGURED until an owner rule maps them; PLAIN_CONCRETE is excluded by design.
DEFAULT_MAPPING = {
    "FOUNDATION_PAD": "FOUNDATIONS_RELATED", "COMBINED_FOOTING": "FOUNDATIONS_RELATED",
    "STRIP_FOOTING": "FOUNDATIONS_RELATED", "FOUNDATION_NECK": "FOUNDATIONS_RELATED",
    "FOUNDATION_STRAP_BEAM": "FOUNDATIONS_RELATED",
    "GROUND_BEAM": "GROUND_BEAMS_AND_GROUND_SLAB", "GROUND_SLAB": "GROUND_BEAMS_AND_GROUND_SLAB",
    "BOUNDARY_GROUND_BEAM": "GROUND_BEAMS_AND_GROUND_SLAB",
    "COLUMN": "WALLS_AND_COLUMNS", "STRUCTURAL_WALL": "WALLS_AND_COLUMNS",
    "BEAM_COLUMN_JOINT": "WALLS_AND_COLUMNS",      # column bars and ties run through the joint
    "BEAM": "BEAMS", "CONTINUOUS_BEAM": "BEAMS", "RING_BEAM": "BEAMS",
    "SOLID_SLAB": "SLABS", "FLAT_SLAB": "SLABS", "RIBBED_SLAB": "SLABS",
    "STAIR": "STAIRS_AND_DOME", "DOME": "STAIRS_AND_DOME",
    "POOL_BASE": "SWIMMING_POOL", "POOL_WALL": "SWIMMING_POOL", "POOL_BEAM": "SWIMMING_POOL",
}
EXCLUDED_CLASSES = ("PLAIN_CONCRETE",)
REQUIRES_EXPLICIT_RULE = ("RAFT", "PILE_CAP", "RETAINING_WALL", "WATER_TANK", "LIFT_PIT", "LIFT_WALL",
                          "LIFT_TIE_BEAM", "PARAPET_RC", "PARAPET_STIFFENER_COLUMN", "PARAPET_TOP_RING_BEAM",
                          "LINTEL", "SPECIAL_RC_ELEMENT")

# keyword classifier (used only when the occurrence carries no explicit element_class); order matters
_KEYWORDS = (
    ("PLAIN_CONCRETE", ("BLINDING", "PLAIN CONCRETE", "LEAN CONCRETE")),
    ("FOUNDATION_STRAP_BEAM", ("STRAP",)), ("FOUNDATION_NECK", ("NECK", "PEDESTAL")),
    ("COMBINED_FOOTING", ("COMBINED FOOTING",)), ("STRIP_FOOTING", ("STRIP FOOTING",)), ("RAFT", ("RAFT",)),
    ("PILE_CAP", ("PILE CAP",)), ("FOUNDATION_PAD", ("ISOLATED FOOTING", "FOOTING", "PAD")),
    ("BOUNDARY_GROUND_BEAM", ("BOUNDARY WALL BEAM", "BOUNDARY GROUND BEAM")),
    ("GROUND_BEAM", ("GROUND BEAM",)), ("GROUND_SLAB", ("GROUND SLAB", "SLAB ON GRADE")),
    ("POOL_BASE", ("POOL BASE",)), ("POOL_WALL", ("POOL WALL", "SWIMMING POOL")),
    ("LIFT_PIT", ("LIFT PIT",)), ("LIFT_TIE_BEAM", ("LIFT TIE",)), ("LIFT_WALL", ("LIFT WALL", "LIFT SHAFT")),
    ("WATER_TANK", ("WATER TANK", "TANK")), ("RETAINING_WALL", ("RETAINING",)),
    ("PARAPET_STIFFENER_COLUMN", ("PARAPET STIFFENER", "PARAPET COLUMN")),
    ("PARAPET_TOP_RING_BEAM", ("PARAPET RING", "PARAPET TOP")), ("PARAPET_RC", ("PARAPET",)),
    ("DOME", ("DOME",)), ("STAIR", ("STAIR",)), ("LINTEL", ("LINTEL",)), ("RING_BEAM", ("RING BEAM",)),
    ("BEAM_COLUMN_JOINT", ("JOINT",)), ("CONTINUOUS_BEAM", ("CONTINUOUS BEAM",)), ("BEAM", ("BEAM", "DOWNSTAND")),
    ("STRUCTURAL_WALL", ("STRUCTURAL WALL", "SHEAR WALL", "RC WALL")), ("COLUMN", ("COLUMN",)),
    ("RIBBED_SLAB", ("RIBBED", "HORDI")), ("FLAT_SLAB", ("FLAT SLAB",)), ("SOLID_SLAB", ("SLAB",)),
)
# an occurrence is concrete only: any reinforcement-looking field is refused (the rough engine never sees steel)
_STEEL_FIELDS = ("kg", "steel", "rebar", "bar", "bbs", "tonnage")


class RoughRebarError(ValueError):
    pass


def classify(occ):
    """Element class of one concrete occurrence: its explicit `element_class` if given (validated), else the keyword
    classifier over `description`. Returns (class, basis); (None, 'UNCLASSIFIED') when nothing matches."""
    ec = occ.get("element_class")
    if ec:
        if ec not in ELEMENT_CLASSES:
            raise RoughRebarError(f"unknown element class {ec}")
        return ec, "EXPLICIT"
    text = " ".join(str(occ.get(k) or "") for k in ("description", "family", "kind")).upper()
    for cls, words in _KEYWORDS:
        if any(w in text for w in words):
            return cls, "KEYWORD"
    return None, "UNCLASSIFIED"


def validate_profile(profile):
    """A rough profile: {profile_id, authority: URBAN_OWNER_ESTIMATING_RULE, use: SANITY_CHECK_ONLY,
    ratios_kg_per_m3: {category: int}, mapping (optional)}. Ratios are positive integers; a mapping may only use
    known element classes and configured rough categories."""
    if profile.get("authority") != AUTHORITY or profile.get("use") != USE:
        raise RoughRebarError(f"rough profile must be {AUTHORITY} / {USE}")
    for cat, v in (profile.get("ratios_kg_per_m3") or {}).items():
        if not isinstance(v, int) or isinstance(v, bool) or v <= 0:
            raise RoughRebarError(f"ratio for {cat} must be a positive integer kg/m3")
    for ec, cat in (profile.get("mapping_overrides") or {}).items():
        if ec not in ELEMENT_CLASSES or ec in EXCLUDED_CLASSES:
            raise RoughRebarError(f"mapping override for unknown / excluded element class {ec}")
        if cat not in ROUGH_CATEGORIES:
            raise RoughRebarError(f"mapping override {ec} -> {cat}: not a rough category")
    mapping = effective_mapping(profile)
    for ec, cat in mapping.items():
        if ec not in ELEMENT_CLASSES:
            raise RoughRebarError(f"mapping uses unknown element class {ec}")
        if ec in EXCLUDED_CLASSES:
            raise RoughRebarError(f"{ec} cannot be mapped to a rough category")
        if not isinstance(cat, str) or not cat:
            raise RoughRebarError(f"{ec}: mapping must name one rough category")
    return profile


def effective_mapping(profile):
    """The profile's own `mapping` (full replacement) or DEFAULT_MAPPING, then its `mapping_overrides` on top. An
    override belongs to that profile only (e.g. a profile calibrated with necks counted with columns maps
    FOUNDATION_NECK to WALLS_AND_COLUMNS; another profile may not)."""
    m = dict(profile.get("mapping") or DEFAULT_MAPPING)
    m.update(profile.get("mapping_overrides") or {})
    return m


def ratio_for(category, profile):
    r = (profile.get("ratios_kg_per_m3") or {}).get(category)
    return (r, "CONFIGURED") if r else (None, NOT_CONFIGURED)


def category_of(element_class, profile=None):
    """The rough category of an element class, or None (NOT_CONFIGURED / excluded)."""
    mapping = effective_mapping(profile or {})
    return None if element_class in EXCLUDED_CLASSES else mapping.get(element_class)


def rough_summary(occurrences, profile):
    """occurrences: [{occurrence_id, element_class? | description, concrete_m3, concrete_state}] from the concrete
    register. Returns the ROUGH_REBAR_SUMMARY {categories, not_configured, excluded, note}."""
    validate_profile(profile)
    mapping = effective_mapping(profile)
    seen = set()
    cats = defaultdict(lambda: {s: 0.0 for s in CONCRETE_STATES} | {"occurrences": [], "classes": set()})
    not_configured, excluded = [], []
    for o in occurrences:
        oid = o["occurrence_id"]
        steel = [k for k in o if any(w in k.lower() for w in _STEEL_FIELDS)]
        if steel:
            raise RoughRebarError(f"{oid}: concrete occurrences only - reinforcement fields {steel} are refused")
        if oid in seen:
            raise RoughRebarError(f"occurrence {oid} entered twice (double counting)")
        seen.add(oid)
        ec, basis = classify(o)
        st = o.get("concrete_state")
        if st not in CONCRETE_STATES:
            raise RoughRebarError(f"{oid}: concrete_state must be one of {CONCRETE_STATES}")
        if ec in EXCLUDED_CLASSES:
            excluded.append({"occurrence_id": oid, "element_class": ec, "why": "plain concrete is not reinforced"})
            continue
        cat = mapping.get(ec) if ec else None
        if cat is None:
            not_configured.append({"occurrence_id": oid, "element_class": ec, "classifier_basis": basis,
                                   "state": NOT_CONFIGURED, "concrete_m3": o.get("concrete_m3"),
                                   "concrete_state": st,
                                   "why": "needs an explicit owner rule" if ec in REQUIRES_EXPLICIT_RULE
                                   else "no unambiguous rough category"})
            continue
        if o.get("concrete_m3") is not None:
            cats[cat][st] += o["concrete_m3"]
        cats[cat]["occurrences"].append(oid)
        cats[cat]["classes"].add(ec)
    out = {}
    for cat, c in sorted(cats.items()):
        r, rs = ratio_for(cat, profile)
        rel = sum(c[s] for s in RELEASED_STATES)
        mod = sum(c[s] for s in MODELLED_STATES)
        out[cat] = {"category": cat, "ratio_kg_per_m3": r, "ratio_state": rs,
                    "verified_concrete_m3": c["VERIFIED"], "lower_bound_concrete_m3": c["LOWER_BOUND"],
                    "provisional_concrete_m3": c["PROVISIONAL"], "blocked_concrete_m3": c["BLOCKED"],
                    "released_concrete_m3": rel, "modelled_concrete_m3": mod,
                    "rough_kg_released_basis": None if r is None else rel * r,
                    "rough_kg_modelled_basis": None if r is None else mod * r,
                    "occurrences": len(c["occurrences"]), "element_classes": sorted(c["classes"]), "use": USE}
    return {"product": PRODUCT, "policy_id": POLICY_ID, "profile_id": profile.get("profile_id"),
            "authority": AUTHORITY, "use": USE, "categories": out, "not_configured": not_configured,
            "excluded": excluded, "note": MANDATORY_NOTE}


def schema():
    return {"schema": "ROUGH_REBAR_SUMMARY_SCHEMA", "product": PRODUCT, "policy_id": POLICY_ID,
            "authority": AUTHORITY, "use": USE, "element_classes": list(ELEMENT_CLASSES),
            "default_mapping": DEFAULT_MAPPING, "excluded_classes": list(EXCLUDED_CLASSES),
            "requires_explicit_rule": list(REQUIRES_EXPLICIT_RULE), "concrete_states": list(CONCRETE_STATES),
            "note": MANDATORY_NOTE,
            "rules": ["rough = concrete x category ratio; estimating / sanity only",
                      "input is the concrete register only; no reinforcement quantity enters",
                      "one occurrence -> one element class -> one category; never two",
                      "unmapped class / unconfigured ratio -> ROUGH_RATIO_NOT_CONFIGURED (no guess)",
                      "released basis (verified + lower bound) and modelled basis (+ provisional) kept apart",
                      "blocked concrete never enters a rough figure",
                      "never modifies, completes or releases ACCURATE_BOQ_REBAR; never feeds procurement"]}
