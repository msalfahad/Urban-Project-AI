"""T-518 MATERIALS WASTE / PROCUREMENT FACTOR PROVENANCE census (lane I, non-candidate, research only).

PHYSICAL ELEMENT. The procurement quantity of a material = the installed (theoretical) quantity + named losses
(cutting, breakage, mixing, spillage), each its own account, + pack rounding once per purchasing group. The installed
quantity never contains a loss; a loss factor enters procurement only with a source.

ENGINEERING QUESTION. For each merged material producer and key: which factor is applied, at which stage (installed /
waste / procurement / purchase rounding), and what is its source (answered owner decision, owner rule file, reference
book, or none)?

What this module does (read only on every producer; it changes no producer, candidate line or rule file):
  1. enumerate every producer key (table x layer / material x stage) from the merged producers' own outputs;
  2. bind each key to one FACTOR record (value, stage, source, status) -> unread keys must be 0;
  3. re-derive the factor arithmetic from the producers' rows (waste = installed x w, procurement = installed + waste,
     installed = area x band x per-m3, i.e. no waste inside installed) and the engine V1..V5 lineage;
  4. check pack rounding happens once per purchasing group.

Rules (every villa):
  R-T518-1 FACTOR PLACEMENT. A loss factor is applied inside a procurement figure only when its status is
           OWNER_CONFIRMED or ASSUMED - OWNER-APPROVED with a named source; otherwise it is shown BESIDE (its own
           figure) and the procurement for that part is HELD (AT_LEAST the sourced part), never folded, never 0.
           The installed quantity never carries a factor.
  R-T518-2 ROUND ONCE. Whole packs are taken once per product at its purchasing group from the fractional sum; a
           sub-group whole-pack figure is a comparison only and is never summed into a purchase.
  R-T518-3 SCOPE OF A FACTOR. An owner factor applies only within the scope of the decision that gave it (the Q-45 B
           5 % mortar waste: the Q-45 cement-sand tile / stone beds); it is never borrowed by another material
           (black-block mortar, plaster coats, screeds) whose own rule says 'sourced value only'.

Owner provenance read for the factors (OWNER_QUESTIONS_ANSWERED.md and the rulebook, read in full for these records):
  Q-45 answer B (2026-10-19 21:40): practice values incl. 'waste 5 %' on mortar accepted, PROVISIONAL.
  Owner correction 2026-10-20 12:15 (OWNER_DIRECTIVE_2026-10-20.md, withdrawal note; OWNER_SESSION_CHANGES): the audit
     line X3 'waste 5 % not owner-approved' is WITHDRAWN; 'Q-45 values incl. waste 5 %' keep their applicability.
  Q-53 C / UP-STAIR-017 (2026-10-20): 1:3 stair bed, theoretical 9.576 bags + 0.9975 m3 / m3, PRELIMINARY PURCHASING
     10 bags + 1.00 m3 / m3 (a separate layer); 'no waste without a named source or owner-approved allowance'.
  Rulebook 1.0.0 (owner 2026-11-02): UPC-ADHESIVE-001 / UPC-AAC-GLUE-001 / UPC-BLACK-BLOCK-001 waste null ('sourced
     value only', 'never a hardcoded 5 %'), CEIL_PER_PRODUCT_PER_PURCHASING_GROUP; UPC-BLACK-MORTAR-001 not_given
     'mortar waste (sourced value only)'; UPC-TILE-BED-001 silent on waste; UPC-CEMENT-LAYERS-METHOD-001 values null.
  UP-CER-010 (owner 2026-10-12): tile cutting waste from the room layout, never a flat %.
  T-455 board row (Lead transcription of the owner directive 2026-11-02 B3): one spare box per tile type.

Stdlib only. Run: python3 -I research/agents_t518/t518_factor_census.py [--write]
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

SCHEMA = "URBAN_T518_FACTOR_CENSUS_V1"
OUT = os.path.join(ROOT, "research", "agents_t518", "out")

# ------------------------------------------------------------------ statuses ----------------------------------------
OWNER_CONFIRMED = "OWNER CONFIRMED"
OWNER_APPROVED = "ASSUMED - OWNER-APPROVED"
PROVISIONAL = "PROVISIONAL"
NO_SOURCE = "NO SOURCE"
NO_FACTOR = "NO FACTOR"            # the producer applies no loss factor at all (nothing to source)
SOURCED = (OWNER_CONFIRMED, OWNER_APPROVED)

# placement of a factor
SEPARATE = "SEPARATE WASTE FIELD -> PROCUREMENT"
INSIDE_INSTALLED = "INSIDE INSTALLED (DEFECT)"
HELD_ACCOUNT = "WASTE HELD, PROCUREMENT HELD"
PURCHASING_RATE = "PURCHASING-ALLOWANCE RATE (separate layer)"
LAYOUT = "LAYOUT (cutting plan), no %"
NONE = "NONE"

# ------------------------------------------------------------------ R-T518-1 / R-T518-2 (generic) -------------------


class CensusError(ValueError):
    pass


def factor(value, source=None, status=NO_SOURCE, name="waste"):
    """One loss factor. A value with a SOURCED status needs a source; a fraction above 0.5 is a unit error."""
    if value is not None:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0 or value > 0.5:
            raise CensusError(f"{name}: {value!r} is not a fraction in [0, 0.5] (a percent passed as a fraction?)")
    if status in SOURCED and not source:
        raise CensusError(f"{name}: status {status} without a named source")
    return {"name": name, "value": value, "source": source, "status": status}


def place(installed_low, installed_high, factors):
    """R-T518-1 for one key. installed may be None (HELD). Returns installed (never touched), each factor's own
    account (inside or BESIDE) and the procurement: a figure only when every factor is sourced and has a value; else
    HELD with AT_LEAST = installed + the sourced parts. Never folds a factor into installed, never returns 0 for HELD."""
    rec = {"installed": None if installed_low is None else [installed_low, installed_high],
           "accounts": [], "procurement": None, "procurement_status": "HELD", "at_least": None, "beside": []}
    if installed_low is None or installed_high is None:
        rec["reason"] = "installed HELD: procurement HELD"
        return rec
    lo, hi, complete = installed_low, installed_high, True
    for f in factors:
        if f["value"] is None:
            complete = False
            rec["accounts"].append({"name": f["name"], "value": None, "status": f["status"], "place": HELD_ACCOUNT,
                                    "why": "no value: this part of the procurement HELD"})
        elif f["status"] in SOURCED:
            a = {"name": f["name"], "low": installed_low * f["value"], "high": installed_high * f["value"],
                 "status": f["status"], "source": f["source"], "place": SEPARATE}
            rec["accounts"].append(a)
            lo, hi = lo + a["low"], hi + a["high"]
        else:
            complete = False
            rec["beside"].append({"name": f["name"], "low": installed_low * f["value"],
                                  "high": installed_high * f["value"], "status": f["status"], "source": f["source"],
                                  "why": "factor without an owner source: BESIDE, never inside the procurement"})
    if complete:
        rec.update(procurement=[lo, hi], procurement_status="COMPUTED")
    else:
        rec.update(at_least=[lo, hi], reason="a factor is unsourced or has no value: procurement HELD (AT_LEAST)")
    return rec


def purchase(parts, pack, group):
    """R-T518-2: one purchasing group, one product. parts = [(id, fractional qty or None)]. A pre-rounded part
    (flagged by the caller as ('id', qty, 'ROUNDED')) is refused: rounding happens here, once."""
    known, held = 0.0, []
    for p in parts:
        if len(p) > 2 and p[2] == "ROUNDED":
            raise CensusError(f"{group}: part {p[0]} arrives already rounded (round once per purchasing group)")
        if p[1] is None:
            held.append(p[0])
        else:
            known += p[1]
    if held:
        return {"group": group, "status": "HELD", "packs": None, "at_least_known": round(known, 6) if parts and
                len(held) < len(parts) else None, "held": held}
    return {"group": group, "status": "COMPUTED", "packs": int(math.ceil(round(known / pack, 9) - 1e-9)),
            "fractional": round(known / pack, 6), "held": []}


# ------------------------------------------------------------------ the factor register (Alsenan producers) ---------
# Each record: the factor a producer applies to its keys, where, and its source. 'code' is the producer line that
# applies it (read on this commit). 'match' selects the census keys it governs: (table, layer-or-material prefix).
Q45 = ("Q-45 answer B (owner 2026-10-19 21:40: practice values accepted incl. waste 5 % on mortar, PROVISIONAL rate); "
       "owner correction 2026-10-20 12:15 (OWNER_DIRECTIVE_2026-10-20.md withdrawal note: X3 'waste 5 % not owner-"
       "approved' WITHDRAWN, Q-45 values incl. waste 5 % keep their applicability)")

FACTORS = [
    {"id": "FX-01", "table": "T-500", "match": [("T-500", "TILE_BED")], "keys": "TILE_BED cement / sand",
     "factor": "mortar waste", "value": 0.05, "stage": SEPARATE, "source": Q45, "status": OWNER_APPROVED,
     "code": "research/agents_t500/t500_tile_bed_mortar.py:193-200 (waste_* fields, procurement = installed x (1+w))",
     "rounding": "whole cement bags per item code (DRY, WET) AND per T-500 project: sub-groups (see F-T518-3)",
     "verdict": "OK: sourced, separate field; scope = Q-45 floor / bartash beds"},
    {"id": "FX-02", "table": "T-514", "match": [("T-514", "FLOOR_TILE_BED")], "keys": "FLOOR_TILE_BED cement / sand",
     "factor": "mortar waste", "value": 0.05, "stage": SEPARATE, "source": Q45, "status": OWNER_APPROVED,
     "code": "research/agents_t514/t514_screed_bed_producers.py:177-178, 297-301",
     "rounding": "none at row level (T-511 project subtotal)",
     "verdict": "OK: sourced (the producer's label 'PROVISIONAL, V1 record' undersells it: owner-approved, provisional "
                "rate); scope: an outdoor porcelain floor bed is a Q-45 'floor' bed"},
    {"id": "FX-03", "table": "T-514", "match": [("T-514", "THRESHOLD"), ("T-514", "SCREED"), ("T-514", "STONE")],
     "keys": "threshold stone bed / screeds (no merged row: HELD before any material)", "factor": "mortar waste",
     "value": None, "stage": HELD_ACCOUNT, "source": None, "status": NO_SOURCE,
     "code": "research/agents_t514/t514_screed_bed_producers.py:182-187, 291-295",
     "rounding": "-", "verdict": "OK: HELD, never 0 (Q-45 scope does not cover screeds: Q-41 thickness HELD)"},
    {"id": "FX-04", "table": "STAIR_BED_V1", "match": [("STAIR_BED_V1", "STAIR_BED")],
     "keys": "STAIR_BED_1:3 cement / sand", "factor": "purchasing allowance (cement 10 / 9.576 = x1.044277; sand "
     "1.00 / 0.9975 = x1.002506)", "value": None, "stage": PURCHASING_RATE,
     "source": "Q-53 C / UP-STAIR-017@1.0.0 purchasing_allowance (owner 2026-10-20 12:02)", "status": OWNER_APPROVED,
     "code": "research/agents_t511/t511_cement_sand_census.py:585-594 (PROCUREMENT = m3 x 10 / 1.00; WASTE HELD)",
     "rounding": "T-511 subtotals", "verdict": "PURCHASING RATE sourced; WASTE HELD while the Q-45 B 5 % (owner-"
     "approved on Q-45 mortar, which named the marble stair bed) is applied to the same bed by FINISH V1: two "
     "producers disagree (F-T518-2)"},
    {"id": "FX-05", "table": "T-453", "match": [("T-453", "MASONRY_LAYING")],
     "keys": "black-block mortar m3, cement, sand; AAC glue kg / bags", "factor": "mortar / glue waste",
     "value": None, "stage": HELD_ACCOUNT,
     "source": "UPC-BLACK-MORTAR-001 not_given 'mortar waste (sourced value only)'; UPC-AAC-GLUE-001 waste null",
     "status": NO_SOURCE, "code": "research/agents_t453/t453_material_ledger.py:267-272, 359-364",
     "rounding": "AAC glue: ceil once per PROJECT group (HELD: 11 held lines, known 229.5755 kg)",
     "verdict": "OK: HELD; the Q-45 5 % is NOT borrowed (R-T518-3)"},
    {"id": "FX-06", "table": "T-453", "match": [("T-453", "MASONRY_UNITS")], "keys": "black / AAC block units",
     "factor": "breakage / cutting", "value": None, "stage": HELD_ACCOUNT,
     "source": "UPC-BLACK-BLOCK-001 waste null ('never a hardcoded 5 %'); Q-75 'track waste separately'",
     "status": NO_SOURCE, "code": "research/agents_t453/t453_material_ledger.py:334-342",
     "rounding": "procurement count HELD (theoretical not rounded)", "verdict": "OK: HELD, never 0"},
    {"id": "FX-07", "table": "T-453", "match": [("T-453", "LINTEL_RC")], "keys": "lintel concrete m3 (no candidate line)",
     "factor": "none", "value": None, "stage": NONE, "source": None, "status": NO_FACTOR,
     "code": "research/agents_t453/t453_material_ledger.py (lintels)", "rounding": "-",
     "verdict": "OK: no factor applied"},
    {"id": "FX-08", "table": "T-454 / T-489", "match": [("T-454", ""), ("T-489", "")],
     "keys": "bond coat / levelling render / wall plaster mortar, cement, sand", "factor": "mortar waste",
     "value": None, "stage": HELD_ACCOUNT,
     "source": "UPC-CEMENT-LAYERS-METHOD-001 values null; no owner record", "status": NO_SOURCE,
     "code": "research/agents_t511/t511_cement_sand_census.py:479-481 (WASTE / PROCUREMENT HELD)", "rounding": "-",
     "verdict": "OK: HELD (Q-45 'wall mortar 2 cm' is the superseded wet-wall bed, not plaster: R-T518-3)"},
    {"id": "FX-09", "table": "T-455 / V4 / V5", "match": [("T-455", "TILE_ADHESIVE"), ("T-495", "TILE_ADHESIVE")],
     "keys": "tile adhesive bags", "factor": "adhesive waste", "value": None, "stage": HELD_ACCOUNT,
     "source": "UPC-ADHESIVE-001 waste null; purchase 'waste NOT APPLIED'", "status": NO_SOURCE,
     "code": "engine/source/finish_materials_table_v4.py:222-245 (ceil per group), :235", "rounding":
     "ceil once per adhesive product at the PROJECT group (HELD group: no bags to buy; V5 AT_LEAST)",
     "verdict": "OK"},
    {"id": "FX-10", "table": "T-455 / V4 / V5", "match": [("T-455", "TILE_UNITS")], "keys": "tiles, boxes",
     "factor": "cutting waste from layout + 1 spare box per tile product", "value": None, "stage": LAYOUT,
     "source": "UP-CER-010@1.0.0 (owner 2026-10-12); spare: owner directive 2026-11-02 B3 as transcribed on the "
     "T-455 board row (not in the answered register)", "status": OWNER_APPROVED,
     "code": "engine/source/finish_materials_table_v4.py:81, 262-272", "rounding":
     "ceil(project tiles / pieces per box) per tile product, once; per-room sum beside only",
     "verdict": "OK (boxes HELD: no pieces per box sourced)"},
    {"id": "FX-11", "table": "FINISH_MATERIALS_TABLE_V1 (V2..V5 inherit)",
     "match": [("FINISH_MATERIALS_TABLE_V1", "TILE_BED")], "keys": "V1 mortar_m3 / cement / sand per finish row",
     "factor": "mortar waste", "value": 0.05, "stage": INSIDE_INSTALLED, "source": Q45, "status": OWNER_APPROVED,
     "code": "engine/source/finish_materials_table.py:67, 213-215 (mortar_m3 = area x bed x 1.05; cement / sand from "
             "it); finish_materials_table_v2.py:47-49 re-exports; v3 V2.row for every kind but WET_WALL; v4:198, v5",
     "rounding": "V1 project ceil of the summed bags", "verdict": "DEFECT D-T518-1: sourced value, wrong place (no "
     "waste field; mortar_m3 carries it). T-511 reads it correctly as a PROCUREMENT reader; unwired, no candidate "
     "quantity affected"},
    {"id": "FX-12", "table": "T-495 (bound by T-496)", "match": [("T-495", "OUTDOOR_BED"), ("T-495", "TILE_BED_MORTAR")],
     "keys": "outdoor bed option mortar m3 / cement / sand", "factor": "mortar waste", "value": 0.05,
     "stage": INSIDE_INSTALLED, "source": Q45, "status": OWNER_APPROVED,
     "code": "research/agents_t495/t495_finish_held_ledger.py:166-167 (V1 materials, '+5 % waste: a BOUND'); "
             "research/agents_t496/t496_binding_map.py:297-300 binds bed_mortar_m3 at stage INSTALLED",
     "rounding": "-", "verdict": "DEFECT D-T518-2 (T-496 stage label): T-511 classes the same figures PROCUREMENT "
     "(correct); both HELD, never summed"},
    {"id": "FX-13", "table": "T-505", "match": [("T-505", "")], "keys": "disposal / import loss terms",
     "factor": "loss_reuse, loss_import", "value": None, "stage": HELD_ACCOUNT,
     "source": "owner 2026-11-02 18:00 (3): losses separate accounts; values need a source", "status": NO_SOURCE,
     "code": "research/agents_t505/disposal_balance_v2.py:58-68", "rounding": "-", "verdict": "OK: HELD, never 0"},
]


def factor_for(table, layer):
    """the factor record governing one census key, or None (an unread key)."""
    hits = [f for f in FACTORS for (t, p) in f["match"] if t == table and (layer or "").startswith(p)]
    return hits[0] if hits else None


# ------------------------------------------------------------------ census of the producer keys ---------------------
INPUTS = {
    "T-511": "research/agents_t511/out/CEMENT_SAND_CENSUS_T511.json",
    "T-514": "research/agents_t514/out/SCREED_BED_PRODUCERS_T514.json",
    "T-496": "research/agents_t496/out/BINDING_MAP_T496.json",
    "T-500": "research/agents_t500/out/TILE_BED_MORTAR_T500.json",
    "T-455": "research/agents_t455/out/TILE_PURCHASE_T455.json",
    "T-453": "research/agents_t453/out/MATERIAL_LEDGER_T453.json",
    "T-505": "research/agents_t505/summary_t505.json",
}


def _load(name):
    p = os.path.join(ROOT, INPUTS[name])
    with open(p, "rb") as fh:
        raw = fh.read()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def _stage_of_t500(field):
    if field.startswith("waste_"):
        return "WASTE"
    if field.startswith("procurement_"):
        return "PROCUREMENT"
    return "INSTALLED"


def census_keys(data):
    """every producer key: (table, layer-or-material, material-or-kind, stage) -> count of rows behind it."""
    keys = {}

    def add(k):
        keys[k] = keys.get(k, 0) + 1
    for src in ("T-511", "T-514"):
        for r in data[src]["rows"]:
            add((r["table"], r["layer"], r["material"], r["stage"]))
    for b in data["T-496"]["bindings"]:
        add((b["table"], b["material"], b["kind"], b["stage"]))
    for r in data["T-500"]["rows"]:
        for fld in r:
            if fld.endswith(("_low", "_high")) and any(x in fld for x in ("cement", "sand", "installed_m3")):
                mat = "CEMENT_50KG" if "cement" in fld else ("SAND_LOOSE" if "sand" in fld else "MORTAR_M3")
                add(("T-500", "TILE_BED", mat, _stage_of_t500(fld)))
    pur = data["T-455"]["purchase"]
    for g in pur["adhesive"]:
        add(("T-455", "TILE_ADHESIVE", "bags_20kg", "PURCHASE"))
    add(("T-455", "TILE_UNITS", "boxes", "PURCHASE"))
    for g in data["T-453"]["glue_groups"]:
        if g != "known_part_by_label" and g != "note":
            add(("T-453", "MASONRY_LAYING", "glue_bags_25kg", "PURCHASE"))
    add(("T-453", "MASONRY_LAYING", "mortar_m3", "PROCUREMENT"))
    add(("T-453", "MASONRY_UNITS", "units_nr", "PROCUREMENT"))
    for t in ("loss_reuse", "loss_import"):
        add(("T-505", "LOSS", t, "LOSS"))
    return keys


# ------------------------------------------------------------------ re-derivations ----------------------------------
def _rel(a, b, tol=2e-6):
    return a is not None and b is not None and abs(a - b) <= tol * max(1.0, abs(b))


def check_t500(d):
    """installed = area x band x per (no waste inside); waste = installed x w; procurement = installed + waste."""
    fails, n = [], 0
    ov = d["owner_values"]
    w = ov["waste"]
    for r in d["rows"]:
        if r["status"] != "BOUND":
            continue
        per = ov[r["kind"]]
        for end, i in (("low", 0), ("high", 1)):
            n += 1
            m3 = r[f"installed_m3_{end}"]          # the producer rounds m3 to 6 dp before the per-m3 figures
            if abs(m3 - r["area_m2"] * per["band_m"][i]) > 1e-6:
                fails.append(f"{r['id']} installed_m3_{end}: {m3} != area x band {r['area_m2'] * per['band_m'][i]}")
            for mat, k in (("cement_bags", "cement_bags_per_m3"), ("sand_m3", "sand_m3_per_m3")):
                n += 3
                inst, wst, pro = r[f"{mat}_{end}"], r[f"waste_{mat}_{end}"], r[f"procurement_{mat}_{end}"]
                if not _rel(inst, m3 * per[k]):
                    fails.append(f"{r['id']} {mat}_{end}: installed {inst} != m3 x per {m3 * per[k]}")
                if not _rel(wst, inst * w):
                    fails.append(f"{r['id']} {mat}_{end}: waste {wst} != installed x {w}")
                if not _rel(pro, inst + wst):
                    fails.append(f"{r['id']} {mat}_{end}: procurement {pro} != installed + waste")
    return n, fails


def check_t514(d):
    fails, n = [], 0
    rows = {}
    for r in d["rows"]:
        rows.setdefault((r["line_id"], r["material"]), {})[r["stage"]] = r
    for (lid, mat), st in rows.items():
        inst, wst, pro = st.get("INSTALLED"), st.get("WASTE"), st.get("PROCUREMENT")
        if not (inst and wst and pro) or inst["low"] is None:
            continue
        a = inst["read"]["net"]
        per = 8.0 if mat == "CEMENT_50KG" else 1.1
        for end, band in (("low", 0.03), ("high", 0.04)):
            n += 3
            if not _rel(inst[end], a * band * per):
                fails.append(f"T-514 {lid} {mat} {end}: installed {inst[end]} != {a} x {band} x {per}")
            if not _rel(wst[end], inst[end] * 0.05):
                fails.append(f"T-514 {lid} {mat} {end}: waste != installed x 0.05")
            if not _rel(pro[end], inst[end] + wst[end]):
                fails.append(f"T-514 {lid} {mat} {end}: procurement != installed + waste")
    return n, fails


def check_stair_allowance(t511):
    """FX-04: STAIR_BED_V1 procurement / installed = UP-STAIR-017 purchasing / theoretical per m3, per line and material."""
    ratio = {"CEMENT_50KG": 10.0 / 9.576, "SAND_LOOSE": 1.0 / 0.9975}
    by, fails, n = {}, [], 0
    for r in t511["rows"]:
        if r["table"] == "STAIR_BED_V1" and r["status"] == "COMPUTED":
            by.setdefault((r["line_id"], r["material"]), {})[r["stage"]] = r
    for (lid, mat), st in by.items():
        for end in ("low", "high"):
            n += 1
            if not _rel(st["PROCUREMENT"][end], st["INSTALLED"][end] * ratio[mat]):
                fails.append(f"STAIR_BED_V1 {lid} {mat} {end}: procurement / installed != {ratio[mat]:.6f}")
    return n, fails


def check_finish_lineage(area=10.0):
    """D-T518-1: the engine V1..V5 dry-floor mortar carries the 5 % (installed figure x 1.05). Returns the evidence."""
    from engine.source import finish_materials_table as V1
    from engine.source import finish_materials_table_v2 as V2
    from engine.source import finish_materials_table_v5 as V5
    lo, hi = V1.OWNER_VALUES["bed_m"][V1.DRY_FLOOR]
    w = V1.OWNER_VALUES["mortar_waste"]
    v1 = V1.materials(V1.DRY_FLOOR, V1.PORCELAIN_CERAMIC, area)
    v5 = V5.table([{"id": "fx", "floor": "F", "kind": V1.DRY_FLOOR, "area_m2": area}])["rows"][0]
    out = {"area_m2": area, "physical_m3": [area * lo, area * hi], "waste_fraction": w,
           "v1_mortar_m3": [v1["mortar_m3_low"], v1["mortar_m3_high"]],
           "v5_mortar_m3": [v5["mortar_m3_low"], v5["mortar_m3_high"]],
           "v2_materials_is_v1": V2.materials is V1.materials,
           "v1_has_waste_field": any(k.startswith("waste") for k in v1)}
    out["folded"] = (_rel(v1["mortar_m3_low"], area * lo * (1 + w)) and _rel(v5["mortar_m3_high"], area * hi * (1 + w))
                     and not out["v1_has_waste_field"])
    return out


def check_t495_binding(t496):
    """D-T518-2: T-496 binds the T-495 bed mortar (V1, waste folded) at stage INSTALLED; the installed share /1.05."""
    rows = []
    for b in t496["bindings"]:
        if b["table"] == "T-495" and b["material"] == "TILE_BED_MORTAR" and b["bound"]:
            area = b["read"]["held_read"][0]
            ok = _rel(b["bound"][0], area * 0.03 * 1.05) and _rel(b["bound"][1], b["read"]["held_read"][1] * 0.04 * 1.05)
            rows.append({"row": b["row"], "stage": b["stage"], "bound_m3": b["bound"], "folded_5pct": ok,
                         "installed_m3": [round(b["bound"][0] / 1.05, 6), round(b["bound"][1] / 1.05, 6)],
                         "overstatement_m3": [round(b["bound"][0] - b["bound"][0] / 1.05, 6),
                                              round(b["bound"][1] - b["bound"][1] / 1.05, 6)]})
    return rows


def rounding_scopes(t500, t511):
    """F-T518-3: whole cement bags printed per T-500 item code and per T-511 trade; only the all-trade cement group is
    the purchasing group. Summing sub-group whole bags overstates by the extra ceilings."""
    sub = {k: v for k, v in t500["subtotals"].items() if k != "PROJECT"}
    proj = t500["subtotals"]["PROJECT"]
    out = {}
    for end in ("low", "high"):
        out[end] = {"sum_of_item_code_ceils": sum(v[f"cement_bags_to_buy_{end}"] for v in sub.values()),
                    "t500_project_ceil": proj[f"cement_bags_to_buy_{end}"],
                    "fractional": proj[f"procurement_cement_bags_{end}"]["value"]
                    if isinstance(proj[f"procurement_cement_bags_{end}"], dict) else proj[f"procurement_cement_bags_{end}"]}
        out[end]["excess_if_summed"] = out[end]["sum_of_item_code_ceils"] - out[end]["t500_project_ceil"]
    t511_scopes = sorted({sc for sc, v in t511["subtotals"].items()
                          for st in v.values() for e in st.values() if "whole_bags_low" in e})
    out["t511_whole_bag_scopes_now"] = t511_scopes
    out["t511_project_cement_status"] = t511["subtotals"]["PROJECT"]["PROCUREMENT"]["CEMENT_50KG"]["status"]
    return out


def stair_scope(t511, w=0.05):
    """F-T518-2: the Q-45 B 5 % on the stair bed, as the figure BESIDE (not applied)."""
    s = {}
    for r in t511["rows"]:
        if r["table"] == "STAIR_BED_V1" and r["stage"] == "INSTALLED" and r["status"] == "COMPUTED":
            s.setdefault(r["material"], [0.0, 0])
            s[r["material"]][0] += r["low"]
            s[r["material"]][1] += 1
    return {m: {"installed": round(v[0], 6), "lines": v[1], "q45_waste_beside": round(v[0] * w, 6)}
            for m, v in s.items()}


# ------------------------------------------------------------------ build -------------------------------------------
def build():
    data, sha = {}, {}
    for k in INPUTS:
        data[k], sha[INPUTS[k]] = _load(k)
    keys = census_keys(data)
    rows, unread = [], []
    for (table, layer, mat, stage), cnt in sorted(keys.items()):
        f = factor_for(table, layer)
        if f is None:
            unread.append([table, layer, mat, stage])
            continue
        rows.append({"table": table, "layer": layer, "material": mat, "stage": stage, "rows_behind": cnt,
                     "factor_id": f["id"], "factor": f["factor"], "value": f["value"], "placement": f["stage"],
                     "source": f["source"], "status": f["status"]})
    n500, f500 = check_t500(data["T-500"])
    n514, f514 = check_t514(data["T-514"])
    nst, fst = check_stair_allowance(data["T-511"])
    lineage = check_finish_lineage()
    t495 = check_t495_binding(data["T-496"])
    inside = [f["id"] for f in FACTORS if f["stage"] == INSIDE_INSTALLED]
    no_src_applied = [f["id"] for f in FACTORS if f["status"] in (NO_SOURCE, PROVISIONAL) and f["value"] is not None]
    out = {
        "schema": SCHEMA, "input_sha256": sha,
        "census": {"keys": len(keys), "rows_behind": sum(keys.values()), "read": len(rows), "unread": len(unread),
                   "unread_keys": unread, "factor_records": len(FACTORS),
                   "producers": sorted({r["table"] for r in rows})},
        "factors": FACTORS, "keys": rows,
        "checks": {"t500_arithmetic": {"checked": n500, "fails": f500},
                   "t514_arithmetic": {"checked": n514, "fails": f514},
                   "stair_purchasing_allowance": {"checked": nst, "fails": fst},
                   "finish_v1_v5_lineage": lineage, "t495_binding": t495,
                   "rounding_scopes": rounding_scopes(data["T-500"], data["T-511"]),
                   "stair_bed_q45_scope": stair_scope(data["T-511"])},
        "findings": {
            "factors_inside_installed": inside,
            "unsourced_factor_applied": no_src_applied,
            "D-T518-1": "FINISH_MATERIALS_TABLE V1 (engine/source/finish_materials_table.py:213-215) folds the Q-45 B "
                        "5 % into mortar_m3 / cement / sand with no waste field; V2 (:49 materials = V1.materials), "
                        "V3 (every kind but WET_WALL via V2.row), V4 (:198) and V5 inherit it. Fix: a new version with "
                        "installed / waste / procurement fields (T-500 shape); V1..V5 untouched.",
            "D-T518-2": "T-496 binds the T-495 outdoor bed option mortar (V1, 5 % folded) at stage INSTALLED "
                        "(t496_binding_map.py:297-300); T-511 classes the same figures PROCUREMENT. HELD, never summed.",
            "F-T518-1": "F-C-T514-1 resolved: the 5 % on the Q-45 tile beds is ASSUMED - OWNER-APPROVED (Q-45 B + owner "
                        "correction 2026-10-20 12:15), not unsourced; T-500 / T-514 apply it in a separate field.",
            "F-T518-2": "Stair 1:3 bed: FINISH V1 applies the Q-45 B 5 % (Q-45 named the marble stair bed); STAIR_BED_V1 "
                        "(Q-53 C / UP-STAIR-017) holds waste and uses the purchasing allowance. Two producers, two "
                        "readings of one owner factor: waste stays HELD with the 5 % BESIDE until the Lead / Checker rule "
                        "which governs (no stacking of 5 % on the purchasing allowance).",
            "F-T518-3": "Cement whole bags are printed at sub-group scopes (T-500 per item code and per table; T-511 per "
                        "trade); the purchasing group of 50 kg cement is the villa (all trades). A sum of sub-group "
                        "ceilings is never a purchase (R-T518-2)."},
        "rules": ["R-T518-1@1.0.0 factor placement: sourced -> separate account in procurement; unsourced -> BESIDE, "
                  "procurement HELD (AT_LEAST); installed never carries a factor",
                  "R-T518-2@1.0.0 round once per product at its purchasing group",
                  "R-T518-3@1.0.0 an owner factor applies only within the scope of its decision"],
        "released_quantities_changed": 0,
    }
    return out


def _csv(out):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    cols = ("table", "layer", "material", "stage", "rows_behind", "factor_id", "factor", "value", "placement",
            "status", "source")
    w.writerow(cols)
    for r in out["keys"]:
        w.writerow([r[c] for c in cols])
    return buf.getvalue()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    out = build()
    c = out["census"]
    print(f"keys {c['keys']} (rows behind {c['rows_behind']}), read {c['read']}, unread {c['unread']}; "
          f"factors {c['factor_records']}; inside installed {out['findings']['factors_inside_installed']}; "
          f"unsourced applied {out['findings']['unsourced_factor_applied']}; "
          f"T-500 checks {out['checks']['t500_arithmetic']['checked']} fails {len(out['checks']['t500_arithmetic']['fails'])}; "
          f"T-514 checks {out['checks']['t514_arithmetic']['checked']} fails {len(out['checks']['t514_arithmetic']['fails'])}")
    if "--write" in argv:
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, "FACTOR_CENSUS_T518.json"), "w") as fh:
            json.dump(out, fh, indent=1, sort_keys=True)
            fh.write("\n")
        with open(os.path.join(OUT, "FACTOR_CENSUS_T518.csv"), "w") as fh:
            fh.write(_csv(out))
    return out


if __name__ == "__main__":
    main()
