"""M1 POST-FREEZE: the frozen planning estimate against the external estimates, family by family (after bc28327).

    python3 -I research/alsenan_m1_usable_boq/post_freeze/post_freeze_comparison.py

Read only after the M1 freeze verified, and never fed back: M1's manifest is verified before and after, and every M1
output is byte-identical afterwards. The external estimates are reference positions, not truth:
    freelancer QS, christiannp-autocad, U-C4N, old Urban V3b   research/alsenan_multi_engine_comparison (S3.1 tables)
    R9.1 item reconciliation                                   research/R9_1_CHRIS_POST_FREEZE/15_*
No external figure is written out (several are benchmark-firewall figures). Each comparison gives the external
estimate's POSITION against M1's planning range (BELOW / INSIDE / ABOVE), its difference as a whole percentage of
M1's base (none for the totals, whose scopes differ), and one discrepancy CLASS:
    AGREES_WITHIN_M1_RANGE   (same components; inside the range)
    SCOPE  MEASUREMENT_CONVENTION  MISSING_COMPONENT  GEOMETRY_EXTRACTION_ERROR  UNSUPPORTED_ASSUMPTION
    DOUBLE_COUNTING  UNRESOLVED
with the side it applies to (M1 or the external estimate) and the reason.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
ROOT = PKG.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import delta_release as DR             # noqa: E402

BOQ = PKG / "boq"
MANIFEST = PKG / "06_M1_FREEZE_MANIFEST.json"
ME = ROOT / "research" / "alsenan_multi_engine_comparison"
R91 = ROOT / "research" / "R9_1_CHRIS_POST_FREEZE" / "15_QUANTITY_RECONCILIATION_UPDATED.csv"
S9 = ROOT / "research" / "alsenan_structural_s9"
ENGINES = (("FREELANCER_QS", "freelancer QS"), ("CHRISTIANNP", "christiannp-autocad"), ("UC4N", "U-C4N"),
           ("URBAN", "old Urban V3b"))
CLASSES = ("AGREES_WITHIN_M1_RANGE", "SCOPE", "MEASUREMENT_CONVENTION", "MISSING_COMPONENT",
           "GEOMETRY_EXTRACTION_ERROR", "UNSUPPORTED_ASSUMPTION", "DOUBLE_COUNTING", "UNRESOLVED")
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")
BENCH = ("44.19", "352.436075", "77.6305", "75.09", "39.7515", "65.965875", "59.8174", "21.8328", "12.348",
         "337.812", "333.173", "22.619", "22.916")

# (group, M1 families, M1 storeys or None, external rows (category, subcategory prefix or None), same components?)
GROUPS = [
    ("FOOTINGS", {"FOOTINGS"}, None, [("FOUNDATIONS", None)], True),
    ("GROUND_BEAMS_AND_STRAPS", {"GROUND_BEAMS"}, None, [("STRAP_BEAMS", None), ("GROUND_BEAMS", None)], True),
    ("GROUND_SLAB", {"GROUND_SLAB"}, None, [("GROUND_SLAB", None)], True),
    ("GROUND_ZONE (allocation-free)", {"GROUND_BEAMS", "GROUND_SLAB"}, None,
     [("STRAP_BEAMS", None), ("GROUND_BEAMS", None), ("GROUND_SLAB", None)], True),
    ("FOUNDATION_NECKS", {"COLUMNS"}, {"FOUNDATION"}, [("COLUMNS_NECKS", "FOUNDATION")], True),
    ("COLUMNS_GF", {"COLUMNS"}, {"GF"}, [("COLUMNS_NECKS", "GF")], True),
    ("COLUMNS_1F", {"COLUMNS"}, {"1F"}, [("COLUMNS_NECKS", "1F")], True),
    ("COLUMNS_2F", {"COLUMNS"}, {"2F"}, [("COLUMNS_NECKS", "2F")], True),
    ("FRAME_GF (allocation-free)", {"COLUMNS", "BEAMS", "SLABS", "CANTILEVER_PORTIONS"}, {"GF"},
     [("FRAME_NORMALISED", "GF")], True),
    ("FRAME_1F (allocation-free)", {"COLUMNS", "BEAMS", "SLABS", "CANTILEVER_PORTIONS"}, {"1F"},
     [("FRAME_NORMALISED", "1F")], True),
    ("FRAME_2F (allocation-free)", {"COLUMNS", "BEAMS", "SLABS", "CANTILEVER_PORTIONS", "WATER_TANK_ROOF"}, {"2F"},
     [("FRAME_NORMALISED", "2F")], True),
    ("FRAME_ALL_FLOORS (allocation-free)", {"COLUMNS", "BEAMS", "SLABS", "CANTILEVER_PORTIONS", "WATER_TANK_ROOF"},
     {"GF", "1F", "2F", "ALL"}, [("FRAME_NORMALISED", None)], True),
    ("BEAMS_ALL_FLOORS", {"BEAMS"}, None, [("BEAMS", "all floors")], True),
    ("SLABS_ALL_FLOORS", {"SLABS", "CANTILEVER_PORTIONS"}, None, [("SLABS", "all floors")], True),
    ("STAIRS", {"STAIRS"}, None, [("STAIRS", None)], True),
    ("DOMES", {"DOMES"}, None, [("DOME", None)], False),
    ("POOL", {"POOL"}, None, [("POOL", None)], False),
    ("LIFT_AND_STRUCTURAL_WALLS", {"LIFT"}, None, [("SPECIAL_RC", "structural")], False),
    ("BOUNDARY_WALL", {"BOUNDARY_WALL"}, None, [("SPECIAL_RC", "boundary")], True),
    ("TOTAL_RC (scopes differ: position only)", None, None, [("TOTAL_CONCRETE", None)], False),
]

# why an external estimate sits outside M1's range (or why a numeric match is not an agreement), per group.
# (class, side, reason); a dict keyed by engine overrides the default.
REASONS = {
    "FOOTINGS": {"default": ("MEASUREMENT_CONVENTION", "both", "the footing / strap / ground-beam overlap prism and "
                             "the F / F10 tag reading; M1's range already holds both tags"),
                 "URBAN": ("MISSING_COMPONENT", "external", "V3b blocked the F / F10 conflict footing")},
    "GROUND_BEAMS_AND_STRAPS": {
        "FREELANCER_QS": ("UNSUPPORTED_ASSUMPTION", "external", "30 x 60 applied to every run, a perimeter beam "
                          "included; the printed p.13 classes and the exterior 'FOLLOW ARCH.' depth are not used"),
        "CHRISTIANNP": ("DOUBLE_COUNTING", "external", "straps measured into the footings (the footing already owns "
                        "that prism); ground beams otherwise close to M1's base"),
        "UC4N": ("DOUBLE_COUNTING", "external", "straps measured into the footings, as christiannp"),
        "URBAN": ("MISSING_COMPONENT", "external", "V3b blocked the exterior ground beams (depth 'FOLLOW ARCH.')")},
    "GROUND_SLAB": {
        "default": ("MISSING_COMPONENT", "M1", "M1 carries S9's 21 slab-on-grade faces (~168 m2); R9.1's best "
                    "route finds every cell between the ground beams (~217 m2) and the external estimates take a "
                    "gross plate (~295 - 320 m2). Part is a real M1 gap (cells S9 never quantified), part a gross "
                    "vs net convention"),
        "URBAN": ("MISSING_COMPONENT", "external", "V3b kept only the two labelled zones")},
    "GROUND_ZONE (allocation-free)": {
        "default": ("MISSING_COMPONENT", "M1", "dominated by the ground-slab extent (see GROUND_SLAB); the ground "
                    "beams themselves are close once straps are measured clear"),
        "URBAN": ("MISSING_COMPONENT", "external", "V3b blocked the exterior ground beams and most slab cells")},
    "FOUNDATION_NECKS": ("UNSUPPORTED_ASSUMPTION", "both", "neck height: M1 uses +1.00 top, the printed 1.50 m "
                         "minimum founding depth and each footing's depth (about 2 m of neck); the external estimates "
                         "assume 1.5 m or an undeclared height. The founding level is not printed (RFI-A03)"),
    "COLUMNS_GF": {
        "default": ("MEASUREMENT_CONVENTION", "both", "height basis: clear height below the beams (external) vs the "
                    "printed floor-to-floor (M1 / S9 point), and storey allocation"),
        "CHRISTIANNP": ("GEOMETRY_EXTRACTION_ERROR", "external", "R9.1 records donor false positives among the GF "
                        "columns, on top of the height basis"),
        "UC4N": ("GEOMETRY_EXTRACTION_ERROR", "external", "same population as christiannp (R9.1 donor false "
                 "positives)"), "URBAN": ("MISSING_COMPONENT", "external", "V3b was a lower bound here (blocked occurrences)")},
    "COLUMNS_1F": {"default": ("MEASUREMENT_CONVENTION", "both", "height basis (clear height below beams vs "
                                "floor-to-floor)"), "URBAN": ("MISSING_COMPONENT", "external", "V3b was a lower bound here (blocked occurrences)")},
    "COLUMNS_2F": {"default": ("MEASUREMENT_CONVENTION", "both", "height basis (clear height below beams vs "
                                "floor-to-floor)"), "URBAN": ("MISSING_COMPONENT", "external", "V3b was a lower bound here (blocked occurrences)")},
    "FRAME_GF (allocation-free)": {
        "default": ("UNRESOLVED", "both", "allocation-free, so the beam / slab convention is not the cause; needs an "
                    "object crosswalk"),
        "CHRISTIANNP": ("UNSUPPORTED_ASSUMPTION", "external", "R9.1: christiannp's slab volume over its own net area "
                        "implies 0.20 m on GF against the printed 0.16 m"),
        "URBAN": ("MISSING_COMPONENT", "external", "V3b's columns and beams were partial (lower bound)")},
    "FRAME_1F (allocation-free)": {"default": ("UNRESOLVED", "both", "allocation-free; needs an object crosswalk "
                                               "(1F beams and slab extents)"),
                                   "URBAN": ("MISSING_COMPONENT", "external", "V3b's columns and beams were partial "
                                             "(lower bound)")},
    "FRAME_2F (allocation-free)": ("UNRESOLVED", "both", "allocation-free (the roof-tank slab included); the 2F roof / "
                                   "stair-roof storey allocation may still differ between estimates"),
    "FRAME_ALL_FLOORS (allocation-free)": {
        "default": ("UNRESOLVED", "both", "allocation-free across floors; see the floor rows"),
        "CHRISTIANNP": ("UNSUPPORTED_ASSUMPTION", "external", "implied GF slab thickness above the printed one "
                        "(R9.1)"),
        "URBAN": ("MISSING_COMPONENT", "external", "V3b's columns and beams were partial (lower bound)")},
    "BEAMS_ALL_FLOORS": {
        "default": ("MEASUREMENT_CONVENTION", "both", "downstand below the slab (external / V3b) vs M1 reading A (the "
                    "slab strip inside H); only the frame rows are comparable"),
        "FREELANCER_QS": ("MEASUREMENT_CONVENTION", "both", "gross depth; numerically inside M1's A - B range")},
    "SLABS_ALL_FLOORS": ("MEASUREMENT_CONVENTION", "both", "slab full depth over the beams (external / V3b) vs M1 "
                         "slab panels that stop at the beam faces; only the frame rows are comparable"),
    "STAIRS": {
        "FREELANCER_QS": ("UNSUPPORTED_ASSUMPTION", "external", "a 0.28 m slab-equivalent over the stair plan"),
        "default": ("UNRESOLVED", "external", "basis undeclared (waist, landings, steps on grade)")},
    "DOMES": ("SCOPE", "both", "different components: the freelancer counts 3 drums (1.0 x 22.6 x 0.1); M1 counts the "
              "shell and the ring beams (the drum is UNRESOLVED in M1). A numeric match is not an agreement"),
    "POOL": ("SCOPE", "external", "the freelancer adds pump-room walls and floor and a larger base"),
    "LIFT_AND_STRUCTURAL_WALLS": ("SCOPE", "both", "different components: the freelancer's 20 cm lift shaft walls vs "
                                  "M1's pit walls (M1 has the shaft walls UNRESOLVED)"),
    "BOUNDARY_WALL": ("UNRESOLVED", "M1", "M1 has no length for the boundary wall on the structural set; the "
                      "freelancer assumes 42 m of 30 x 60 (UNSUPPORTED_ASSUMPTION until the architectural set shows "
                      "it)"),
    "TOTAL_RC (scopes differ: position only)": ("SCOPE", "both", "totals combine different scopes and conventions; "
                                                "shown as a position only, never compared as a percentage"),
}
STEEL_MAP = {"BEAMS": {"BEAMS", "LINTELS"}, "FOUNDATIONS_RELATED": {"FOOTINGS"},
             "GROUND_BEAMS_AND_GROUND_SLAB": {"GROUND_BEAMS", "GROUND_SLAB"}, "SLABS": {"SLABS", "WATER_TANK_ROOF"},
             "STAIRS_AND_DOME": {"STAIRS", "DOMES"}, "SWIMMING_POOL": {"POOL"}, "WALLS_AND_COLUMNS": {"COLUMNS"}}
STEEL_REASON = {
    "BEAMS": ("MISSING_COMPONENT", "M1", "beam bars of the unmeasurable and conflict spans, side bars and residue "
              "spans have no bar model; laps / wastage conventions also differ"),
    "FOUNDATIONS_RELATED": ("MISSING_COMPONENT", "M1", "footing bar groups M1 holds UNRESOLVED (F / F10, boxed and "
                            "extra bars) and column starters filed elsewhere"),
    "GROUND_BEAMS_AND_GROUND_SLAB": ("MISSING_COMPONENT", "M1", "ground-beam spans M1 carries as provisional concrete "
                                     "have no bar model (see PF-M1-03); the freelancer also applies its own sections"),
    "SLABS": ("MEASUREMENT_CONVENTION", "both", "slab mesh / top bars: lap and wastage allowances and the slab extent"),
    "STAIRS_AND_DOME": ("MISSING_COMPONENT", "M1", "stair bars are UNRESOLVED in M1 (typical detail only)"),
    "SWIMMING_POOL": ("MISSING_COMPONENT", "M1", "pool bars are UNRESOLVED in M1 (depths 'AS PER ARCH')"),
    "WALLS_AND_COLUMNS": ("MEASUREMENT_CONVENTION", "both", "column ties / laps / starters: M1 uses S3.1's model; "
                          "the freelancer's wall population and allowances differ"),
}


class ComparisonError(RuntimeError):
    pass


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _csv(rows):
    keys = list(rows[0].keys()) if rows else []
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=keys, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if v is None else v) for k, v in r.items()})
    return buf.getvalue()


def _m1_range(floor, fams, storeys, trade="CONCRETE"):
    lo = b = hi = 0.0
    n = 0
    for r in floor:
        if r["trade"] != trade or (fams is not None and r["family"] not in fams):
            continue
        if fams is None and r["family"] == "PLAIN_CONCRETE":
            continue
        if storeys and r["storey"] not in storeys:
            continue
        lo += float(r["PLANNING_LOW"])
        b += float(r["PLANNING_BASE"])
        hi += float(r["PLANNING_HIGH"])
        n += int(r["N_VERIFIED"]) + int(r["N_PROVISIONAL"])
    return (lo, b, hi) if n else (None, None, None)


def _position(x, lo, hi, tol=1e-6):
    if x is None:
        return "NO_EXTERNAL_VALUE"
    if lo is None:
        return "NO_M1_VALUE"
    return "BELOW" if x < lo - tol else "ABOVE" if x > hi + tol else "INSIDE"


def _reason(group, eng):
    r = REASONS[group]
    if isinstance(r, dict):
        r = r.get(eng) or r.get("default")
    return r


def concrete():
    me = json.loads((ME / "MULTI_ENGINE_CONCRETE_COMPARISON.json").read_text(encoding="utf-8"))["rows"]
    floor = _rows(BOQ / "FLOOR_SUMMARY.csv")
    out = []
    for group, fams, storeys, ext, same in GROUPS:
        lo, b, hi = _m1_range(floor, fams, storeys)
        sel = [r for r in me if any(r["category"] == c and (s is None or r["subcategory"].startswith(s))
                                    for c, s in ext)]
        if not sel:
            raise ComparisonError(f"{group}: no external row")
        for eng, label in ENGINES:
            vals = [r.get(eng) for r in sel]
            x = None if any(v is None for v in vals) else sum(vals)
            pos = _position(x, lo, hi)
            if pos == "INSIDE" and same:
                cls, side, why = "AGREES_WITHIN_M1_RANGE", "", "same components; inside M1's planning range"
            elif pos in ("NO_EXTERNAL_VALUE",):
                cls, side, why = "UNRESOLVED", "external", "no value for this group"
            elif pos == "NO_M1_VALUE":
                cls, side, why = _reason(group, eng)
            else:
                cls, side, why = _reason(group, eng)
                if pos == "INSIDE":
                    why = "numerically inside M1's range, but " + why
            total = group.startswith("TOTAL")
            out.append({"GROUP": group, "M1_FAMILIES": "+".join(sorted(fams)) if fams else "ALL RC",
                        "M1_STOREYS": "+".join(sorted(storeys)) if storeys else "ALL",
                        "EXTERNAL_ROWS": "+".join(f"{c}{'/' + s if s else ''}" for c, s in ext), "ENGINE": label,
                        "M1_PLANNING_LOW_M3": None if lo is None else round(lo, 3),
                        "M1_PLANNING_BASE_M3": None if b is None else round(b, 3),
                        "M1_PLANNING_HIGH_M3": None if hi is None else round(hi, 3),
                        "EXTERNAL_POSITION": pos,
                        "DIFF_PCT_OF_M1_BASE": (None if total or x is None or not b else
                                                int(round(100 * (x - b) / b))),
                        "CLASS": cls, "APPLIES_TO": side, "REASON": why})
    return out


def reinforcement():
    d = json.loads((ME / "MULTI_ENGINE_REBAR_COMPARISON.json").read_text(encoding="utf-8"))
    fam = _rows(BOQ / "FAMILY_SUMMARY.csv")
    out = []
    for r in d["rows"]:
        fams = STEEL_MAP[r["category"]]
        lo = sum(float(x["PLANNING_LOW"]) for x in fam if x["trade"] == "REINFORCEMENT" and x["family"] in fams)
        b = sum(float(x["PLANNING_BASE"]) for x in fam if x["trade"] == "REINFORCEMENT" and x["family"] in fams)
        hi = sum(float(x["PLANNING_HIGH"]) for x in fam if x["trade"] == "REINFORCEMENT" and x["family"] in fams)
        n_un = sum(int(x["N_UNRESOLVED"]) for x in fam if x["trade"] == "REINFORCEMENT" and x["family"] in fams)
        x = r["freelancer_steel_t"] * 1000
        pos = _position(x, lo, hi)
        cls, side, why = (("AGREES_WITHIN_M1_RANGE", "", "inside M1's range") if pos == "INSIDE" else
                          STEEL_REASON[r["category"]])
        out.append({"GROUP": r["category"], "M1_FAMILIES": "+".join(sorted(fams)), "ENGINE": "freelancer QS",
                    "M1_PLANNING_LOW_KG": round(lo, 1), "M1_PLANNING_BASE_KG": round(b, 1),
                    "M1_PLANNING_HIGH_KG": round(hi, 1), "M1_UNRESOLVED_BAR_ITEMS": n_un, "EXTERNAL_POSITION": pos,
                    "DIFF_PCT_OF_M1_BASE": int(round(100 * (x - b) / b)) if b else None, "CLASS": cls,
                    "APPLIES_TO": side, "REASON": why})
    tot = [x for x in fam if x["trade"] == "REINFORCEMENT"]
    lo, b, hi = (sum(float(x[k]) for x in tot) for k in ("PLANNING_LOW", "PLANNING_BASE", "PLANNING_HIGH"))
    for o in d["oracle_net_rebar"]:
        out.append({"GROUP": "TOTAL_NET_REBAR (position only)", "M1_FAMILIES": "ALL",
                    "ENGINE": {"UC4N": "U-C4N", "CHRISTIANNP": "christiannp-autocad"}.get(o["oracle"], o["oracle"]),
                    "M1_PLANNING_LOW_KG": round(lo, 1), "M1_PLANNING_BASE_KG": round(b, 1),
                    "M1_PLANNING_HIGH_KG": round(hi, 1),
                    "M1_UNRESOLVED_BAR_ITEMS": sum(int(x["N_UNRESOLVED"]) for x in tot),
                    "EXTERNAL_POSITION": _position(o["net_rebar_t"] * 1000, lo, hi), "DIFF_PCT_OF_M1_BASE": None,
                    "CLASS": "UNRESOLVED", "APPLIES_TO": "both",
                    "REASON": f"the oracle declares its own net rebar {o['state'].lower().replace('_', ' ')}; M1 has "
                              "unresolved bar items too, so neither total is complete"})
    return out


R91_MAP = {   # R9.1 item -> (M1 quantity, how)
    "Ground-beam concrete": ("GB", "M1 GROUND_BEAMS planning (includes straps)"),
    "Strap beams concrete": (None, "M1 straps are inside GROUND_BEAMS (not split)"),
    "Ground slab concrete": ("GS", "M1 GROUND_SLAB planning"),
    "Footings concrete (matched occurrences)": ("FOOT", "M1 FOOTINGS planning"),
    "Columns FOUNDATION": ("C_FOUNDATION", "M1 COLUMNS FOUNDATION (necks)"),
    "Columns GF": ("C_GF", "M1 COLUMNS GF"), "Columns 1F": ("C_1F", "M1 COLUMNS 1F"),
    "Columns 2F": ("C_2F", "M1 COLUMNS 2F"), "Beams concrete": ("BEAMS", "M1 BEAMS planning (reading A base)"),
    "Suspended slabs concrete": ("SLABS", "M1 SLABS + cantilever portions"),
}


def r91():
    floor = _rows(BOQ / "FLOOR_SUMMARY.csv")
    q = {"GB": _m1_range(floor, {"GROUND_BEAMS"}, None), "GS": _m1_range(floor, {"GROUND_SLAB"}, None),
         "FOOT": _m1_range(floor, {"FOOTINGS"}, None), "BEAMS": _m1_range(floor, {"BEAMS"}, None),
         "SLABS": _m1_range(floor, {"SLABS", "CANTILEVER_PORTIONS"}, None)}
    for s in ("FOUNDATION", "GF", "1F", "2F"):
        q[f"C_{s}"] = _m1_range(floor, {"COLUMNS"}, {s})
    out = []

    def num(v):
        m = re.match(r"^\s*([0-9.]+)\s*$", v or "")
        return float(m.group(1)) if m else None
    for r in _rows(R91):
        if r["ITEM"] not in R91_MAP:
            continue
        key, how = R91_MAP[r["ITEM"]]
        lo, b, hi = q[key] if key else (None, None, None)
        row = {"R9_1_ITEM": r["ITEM"], "M1_QUANTITY": how, "M1_PLANNING_LOW_M3": None if lo is None else round(lo, 3),
               "M1_PLANNING_BASE_M3": None if b is None else round(b, 3),
               "M1_PLANNING_HIGH_M3": None if hi is None else round(hi, 3)}
        for col, label in (("URBAN_BEST", "R9.1 Urban best"), ("CHRIS_FROZEN", "christiannp frozen"),
                           ("UC4N", "U-C4N"), ("FREELANCER_QS_REFERENCE", "freelancer QS")):
            row[f"{label} POSITION"] = _position(num(r[col]), lo, hi) if key else "NOT_SPLIT_IN_M1"
        row["R9_1_ROOT_CAUSE"] = r["ROOT_CAUSE_CLASS"]
        out.append(row)
    return out


def missing_steel_candidates():
    """Concrete components M1 carries (PROVISIONAL / UNRESOLVED) with no bar row of any lane in S9 03, matched by
    component id or by beam-line prefix. Candidates for a missing-reinforcement exception, to verify."""
    bars = {b["COMPONENT_ID"] for b in _rows(S9 / "03_REINFORCEMENT_BOQ_RECONCILIATION.csv")}
    pref = {re.split(r"[#:]", b)[0] for b in bars}
    out = defaultdict(lambda: {"n": 0, "m3_base": 0.0})
    for cat in ("PROVISIONAL", "UNRESOLVED"):
        for r in _rows(BOQ / f"{cat}_REGISTER.csv"):
            if r["TRADE"] != "CONCRETE" or r["FAMILY"] not in ("BEAMS", "GROUND_BEAMS", "LIFT"):
                continue
            cid = r["COMPONENT_ID"]
            if cid in bars or re.split(r"[#:]", cid)[0] in pref or cid.startswith("BEAM-CORNER"):
                continue
            k = (r["FAMILY"], cat)
            out[k]["n"] += 1
            out[k]["m3_base"] += float(r["BASE"] or 0)
    return [{"FAMILY": f, "M1_CATEGORY": c, "CONCRETE_COMPONENTS_WITHOUT_ANY_BAR_ROW": v["n"],
             "THEIR_PROVISIONAL_M3_BASE": round(v["m3_base"], 3)} for (f, c), v in sorted(out.items())]


def findings(conc, steel, cand):
    gs = [r for r in conc if r["GROUP"] == "GROUND_SLAB" and r["ENGINE"] != "old Urban V3b"]
    tot = [r for r in conc if r["GROUP"].startswith("TOTAL")]
    n_un = sum(r["CONCRETE_COMPONENTS_WITHOUT_ANY_BAR_ROW"] for r in cand)
    agree = sum(1 for r in conc if r["CLASS"] == "AGREES_WITHIN_M1_RANGE")
    return [
        {"FINDING_ID": "PF-M1-01", "TOPIC": "totals",
         "FINDING": "Every external RC total sits " + "/".join(sorted({r["EXTERNAL_POSITION"] for r in tot if
                                                                       r["ENGINE"] != "old Urban V3b"})) +
                    " M1's planning range; old V3b sits " + next(r["EXTERNAL_POSITION"] for r in tot if
                                                                  r["ENGINE"] == "old Urban V3b") +
                    ". The totals combine different scopes, so this is not an accuracy figure.",
         "ACTION": "none (not a benchmark)"},
        {"FINDING_ID": "PF-M1-02", "TOPIC": "ground slab",
         "FINDING": "All three external estimates sit " + "/".join(sorted({r['EXTERNAL_POSITION'] for r in gs})) +
                    " M1's ground slab. M1 carries S9's 21 faces; R9.1's best route finds more cells between the "
                    "ground beams. This is the largest real M1 gap the comparison exposes.",
         "ACTION": "M1.1: add the R9.1 cells as PROVISIONAL faces (printed T = 10 cm) after review; do not tune to "
                   "the external areas"},
        {"FINDING_ID": "PF-M1-03", "TOPIC": "missing reinforcement items",
         "FINDING": f"{n_un} beam / ground-beam / lift concrete components that M1 carries have no bar row of any "
                    "lane in S9 03 (matched by id or beam-line prefix). M1's 33 unresolved reinforcement items "
                    "therefore understate what has no bar model.",
         "ACTION": "M1.1: one UNRESOLVED reinforcement item per such component, so the exception report is complete"},
        {"FINDING_ID": "PF-M1-04", "TOPIC": "necks",
         "FINDING": "M1's neck volumes are above every external estimate: M1 derives about 2 m of neck from the "
                    "printed 1.50 m minimum founding depth and +1.00 top; the others assume 1.5 m or do not say.",
         "ACTION": "keep the printed-rule base; RFI-A03 (founding level) decides"},
        {"FINDING_ID": "PF-M1-05", "TOPIC": "ground beams and straps",
         "FINDING": "christiannp and U-C4N measure straps into the footings (a double count against the footing); "
                    "the freelancer applies 30 x 60 everywhere. M1's ground beams sit near the oracles once straps "
                    "are measured clear.",
         "ACTION": "none to M1; RFI-A05 / exterior depth still open"},
        {"FINDING_ID": "PF-M1-06", "TOPIC": "steel",
         "FINDING": "The freelancer is above M1 in most steel groups. Where M1 has a bar model the difference is "
                    "laps / wastage and section assumptions; elsewhere it is M1's unresolved bars (no bar model, no "
                    "ratio used).",
         "ACTION": "M1 keeps unresolved bars out of the total; a ratio is never used to fill them"},
        {"FINDING_ID": "PF-M1-07", "TOPIC": "agreement count",
         "FINDING": f"{agree} of {len(conc)} engine-group comparisons agree within M1's range on the same "
                    "components. DOMES and the lift walls match numerically but count different components.",
         "ACTION": "none"},
    ]


def run():
    DR.verify_frozen(MANIFEST, ROOT)
    before = json.loads(MANIFEST.read_text(encoding="utf-8"))["outputs"]
    conc, steel, items, cand = concrete(), reinforcement(), r91(), missing_steel_candidates()
    for r in conc + steel:
        if r["CLASS"] not in CLASSES:
            raise ComparisonError(f"class {r['CLASS']}")
    fnd = findings(conc, steel, cand)
    summary = {"round": "M1 post-freeze", "freeze_commit": "bc28327", "external_figures_written": False,
               "m1_outputs_unchanged": True, "concrete_comparisons": len(conc),
               "concrete_by_class": {c: sum(1 for r in conc if r["CLASS"] == c) for c in CLASSES},
               "steel_comparisons": len(steel),
               "steel_by_class": {c: sum(1 for r in steel if r["CLASS"] == c) for c in CLASSES},
               "missing_reinforcement_candidates": sum(r["CONCRETE_COMPONENTS_WITHOUT_ANY_BAR_ROW"] for r in cand),
               "sources": ["research/alsenan_multi_engine_comparison/MULTI_ENGINE_CONCRETE_COMPARISON.json",
                           "research/alsenan_multi_engine_comparison/MULTI_ENGINE_REBAR_COMPARISON.json",
                           "research/R9_1_CHRIS_POST_FREEZE/15_QUANTITY_RECONCILIATION_UPDATED.csv",
                           "research/alsenan_structural_s9/03_REINFORCEMENT_BOQ_RECONCILIATION.csv"],
               "rule": "no external estimate is used to tune M1; positions and classes only"}
    out = {"01_CONCRETE_RECONCILIATION.csv": _csv(conc), "02_REINFORCEMENT_RECONCILIATION.csv": _csv(steel),
           "03_R9_1_ITEM_POSITIONS.csv": _csv(items), "04_MISSING_REINFORCEMENT_CANDIDATES.csv": _csv(cand),
           "05_POST_FREEZE_FINDINGS.csv": _csv(fnd),
           "06_POST_FREEZE_SUMMARY.json": json.dumps(summary, indent=1, sort_keys=True) + "\n"}
    out["00_POST_FREEZE_README.md"] = readme(summary, fnd)
    for k, v in out.items():
        if HYGIENE.search(v) or [x for x in BENCH if x in v]:
            raise ComparisonError(f"hygiene / benchmark figure in {k}")
        (HERE / k).write_text(v, encoding="utf-8")
    DR.verify_frozen(MANIFEST, ROOT)
    if json.loads(MANIFEST.read_text(encoding="utf-8"))["outputs"] != before:
        raise ComparisonError("M1 outputs changed")
    return summary


def readme(s, fnd):
    L = ["# M1 post-freeze: the planning estimate against the external estimates", "",
         "Written after the M1 freeze (`bc28327`). M1 is verified before and after, and nothing here feeds back.",
         "",
         "- **No external figure is written.** Several are benchmark-firewall figures. Each comparison gives the "
         "external estimate's position against M1's planning range, the difference as a whole percentage of M1's "
         "base (except for totals, whose scopes differ), and one discrepancy class with the side it applies to.",
         "- **No external estimate is a measured truth.** No accuracy figure is claimed.", "",
         "| Class | Concrete comparisons | Steel comparisons |", "|---|---:|---:|"]
    for c in CLASSES:
        L.append(f"| {c} | {s['concrete_by_class'][c]} | {s['steel_by_class'][c]} |")
    L += ["", "## Findings", "", "| ID | Topic | Finding | Action |", "|---|---|---|---|"]
    for f in fnd:
        L.append(f"| {f['FINDING_ID']} | {f['TOPIC']} | {f['FINDING']} | {f['ACTION']} |")
    L += ["", "Files: `01_CONCRETE_RECONCILIATION.csv` (family groups, four engines), `02_REINFORCEMENT_"
              "RECONCILIATION.csv`, `03_R9_1_ITEM_POSITIONS.csv`, `04_MISSING_REINFORCEMENT_CANDIDATES.csv`, "
              "`06_POST_FREEZE_SUMMARY.json`.", ""]
    return "\n".join(L)


if __name__ == "__main__":
    print(json.dumps(run(), indent=1))
