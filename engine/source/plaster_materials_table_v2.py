"""PLASTER MATERIALS TABLE V2 (task T-489, from Q-79 withdrawn by the Lead 2026-11-03 12:18; opt-in, UNWIRED_PRODUCER:
read by no released method and by no candidate V3.0.x; no released or candidate quantity changes; V1 is untouched).

What V2 adds to V1 (PLASTER_MATERIALS_TABLE_V1, T-454): the MIX stage of each coat, kept apart from the area and the
thickness stage that V1 already gives (V1 rows are the input, never recomputed here):

    coat mortar m3 (V1: area x thickness; a MINIMUM thickness gives an AT_LEAST bound, a missing one HELD)
      x per-m3 figures of the coat's cement : sand ratio 1:n by VOLUME, converted by a named derivation convention:
            dry volume      = dry_factor (dry loose materials per 1 m3 of wet placed mortar)
            cement m3       = dry_factor / (1 + n)           cement kg = cement m3 x cement_kg_m3
            cement bags     = cement kg / bag_kg              sand m3   = dry_factor x n / (1 + n)
      -> cement bags, sand m3 per coat (water HELD: no sourced water figure).

Sources (search order of the rule hierarchy, MISSION 'Rule hierarchy' and 'Cement-based materials'; ERS s.2):
    ratio       (1) project drawings / specification: none printed (T-080, T-329, T-335, T-454).
                (2) owner project decision: none (Q-79 withdrawn, not answered).
                (3) company rulebook: UPC-CEMENT-LAYERS-METHOD-001 null for every layer.
                (4) documented engineering references (T-489 search, research/agents_t489/T-489_PLASTER_MIX.md):
                    Kuwait General Specification for Buildings and Engineering Works 1990, chapter 09200 'plastering
                    works' (the governing reference): NOT READABLE - the Drive file is 11.8 MB, over the connector's
                    10 MB download limit, and its text index stops at 97,008 characters (chapter 02230); KSE 'Bayt
                    Al-Omr' 2023: thicknesses only; every other reference on Drive under the limit prints no plaster
                    mix. So every ratio is HELD with the missing source named (MIX_REFERENCE), never 0.
    conversion  owner derivation convention Q-53 C (owner 2026-10-20 12:02): dry factor 1.33, cement 1,440 kg/m3,
                50 kg bag. It is a CONVERSION method (how a ratio becomes bags), owner-approved, 'not universal
                constants'; its 1:3 RATIO belongs to the stair bed and is never borrowed for a wall coat (nor Q-78's
                1:4 block mortar): a mix whose source cites Q-53 or Q-78 is refused for these coats.

A project passes its ratio per layer with `mix` = {layer: {"sand_parts": n, "source": "...", "level": 1 | 2 | 3 | 4}}
(cement is 1 part by volume). Level 1 PROJECT DOCUMENT, 2 OWNER PROJECT DECISION, 3 OWNER CONFIRMED COMPANY RULE,
4 ENGINEERING ESTIMATE. An entry with no source, a level outside 1-4, or a source citing Q-53 / Q-78 is refused.

Statuses (F-C-T454-1): 'ESTIMATED-NET' is a provenance label, not a WORKFLOW_CONTROLS s.5 status. Each figure carries
`s5_status` from S5_MAP, the weakest of its inputs (area, thickness, ratio, conversion): a level-4 ENGINEERING ESTIMATE
or an AT_LEAST bound maps to s.5 HELD (s.4: with no approved fallback and no drawing evidence the quantity is HELD;
the estimate is shown beside, labelled, never released, never VERIFIED); an owner level 2 / 3 input maps to
ASSUMED - OWNER-APPROVED; a level 1 input on a PROVISIONAL / VERIFIED area to DRAWING-CONFIRMED. VERIFIED is never set
here (only the Checker verifies). Sensitivity 1:3 / 1:4 / 1:5 is shown on every coat that has mortar m3 (or a bound):
NOT A QUANTITY. Project-agnostic: no project, room name or count. Function names avoid the B4-05 / B9-04 family
name terms (T-130 guard).
"""

from __future__ import annotations

import copy
import math

from engine.source import plaster_materials_table_v1 as V1

METHOD_ID = "PLASTER_MATERIALS_TABLE_V2"
DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"
SUPERSEDES = None             # V1 stays the table of the area / thickness stage; V2 reads V1 rows and adds the mix stage
RULES = V1.RULES + ("Q-53 C (owner 2026-10-20 12:02): ratio -> bags conversion convention, used as a CONVERSION only",
                    "MISSION 'Rule hierarchy' levels 1-4; WORKFLOW_CONTROLS s.4 / s.5 statuses (F-C-T454-1)")

HELD, AT_LEAST, OK = V1.HELD, V1.AT_LEAST, V1.OK
S5_VERIFIED, S5_DRAWING, S5_OWNER, S5_HELD, S5_UNKNOWN = (
    "VERIFIED", "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD", "UNKNOWN")
LEVEL_LABEL = {1: "PROJECT DOCUMENT", 2: "OWNER PROJECT DECISION", 3: "OWNER CONFIRMED COMPANY RULE",
               4: "ENGINEERING ESTIMATE"}
# provenance label (V1 area / thickness labels and V2 ratio levels) -> WORKFLOW_CONTROLS s.5 evidence status
S5_MAP = {V1.VNET: S5_DRAWING, V1.PNET: S5_DRAWING, V1.ENET: S5_HELD, HELD: S5_HELD,
          "PROJECT DOCUMENT": S5_DRAWING, "OWNER PROJECT DECISION": S5_OWNER,
          "OWNER CONFIRMED COMPANY RULE": S5_OWNER, "ENGINEERING ESTIMATE": S5_HELD}
_RANK = {S5_DRAWING: 0, S5_OWNER: 1, S5_UNKNOWN: 2, S5_HELD: 3}
SENSITIVITY_SAND_PARTS = (3, 4, 5)
BORROW_REFUSED = ("Q-53", "Q-78")

CONVERSION = {"dry_factor": 1.33, "cement_kg_m3": 1440.0, "bag_kg": 50.0, "level": 3,
              "source": "owner Q-53 C (2026-10-20 12:02, OWNER_QUESTIONS_ANSWERED.md): per 1.00 m3 finished mortar, "
                        "dry factor 1.33, cement 1440 kg/m3, 50 kg bag; 'not universal constants'; conversion only, "
                        "never the stair-bed 1:3 ratio"}

_KGS = ("Kuwait General Specification for Buildings and Engineering Works 1990 (Drive: Engineering Sources / 01 Kuwait "
        "References), chapter 09200 'plastering works'")
MIX_SEARCH = (
    ("project drawings / specification", "no plaster, render or spatter mix printed (T-080, T-329, T-335, T-454)"),
    ("owner project decision", "none (Q-79 withdrawn 2026-11-03 12:18, not answered)"),
    ("company rulebook 1.0.0", "UPC-CEMENT-LAYERS-METHOD-001 leaves every layer's mix null"),
    (_KGS, "NOT READABLE: file 11,809,903 bytes, over the Drive connector's 10 MB download limit (download refused "
           "2026-11-03); the text index (read_file_content / search snippet) stops at 97,008 characters, chapter "
           "02230; the table of contents lists 09200 'أعمال المساح' but its text is past the cut"),
    ("KSE 'Bayt Al-Omr' 2023 (Drive: 01 Kuwait References)", "items 57 / 60 / 62 / 75: thicknesses only, no mix"),
    ("Qatar Construction Specifications QCS 2014 (Drive: 04 Regional Codes)", "NOT READABLE: 86.9 MB, over the limit"),
    ("Saudi Building Code 2018 general (Drive: 04 Regional Codes)", "NOT READABLE: 11.3 MB, over the limit"),
    ("Al-Jund 'Finishes' (Drive: 02 Construction Books)", "NOT READABLE: 79.9 MB, over the limit (no text layer, T-454)"),
    ("other Drive reference files under the limit", "Drive full-text search for plaster / render / spatter terms "
                                                   "returns none of them with a plaster mix"),
)
MIX_REFERENCE = {ly: {"sand_parts": None, "level": None, "source": None,
                      "missing": "no readable source prints this coat's cement : sand ratio; governing reference "
                                 "not readable: " + _KGS + " (over the 10 MB connector limit)"}
                 for ly in ("BOND_COAT", "WALL_PLASTER", "LEVELLING_RENDER")}


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def _pos(v, what):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v) or v <= 0:
        raise ValueError(f"{what} must be a finite number > 0, got {v!r}")
    return float(v)


def conversion_checked(conv):
    out = {k: _pos(conv.get(k), k) for k in ("dry_factor", "cement_kg_m3", "bag_kg")}
    if not str(conv.get("source") or "").strip():
        raise ValueError("a conversion convention with no source is never applied")
    if not 1.0 <= out["dry_factor"] <= 2.0:
        raise ValueError(f"dry_factor {out['dry_factor']} outside 1.0 .. 2.0 (a percentage or a typo)")
    lvl = conv.get("level")
    if lvl not in LEVEL_LABEL:
        raise ValueError(f"conversion level must be one of {sorted(LEVEL_LABEL)}, got {lvl!r}")
    return dict(out, source=conv["source"], level=lvl)


def per_m3(sand_parts, conv=CONVERSION):
    """1 : n by volume -> per 1 m3 of wet placed coat: dry m3, cement m3 / kg / bags, sand m3 (no waste, no water)."""
    n = _pos(sand_parts, "sand parts")
    c = conversion_checked(conv)
    cem_m3 = c["dry_factor"] / (1.0 + n)
    kg = cem_m3 * c["cement_kg_m3"]
    return {"ratio": f"1:{n:g}", "dry_m3": _r(c["dry_factor"]), "cement_m3": _r(cem_m3, 9), "cement_kg": _r(kg, 6),
            "cement_bags": _r(kg / c["bag_kg"], 9), "sand_m3": _r(c["dry_factor"] * n / (1.0 + n), 9)}


def mix_checked(layer, m):
    if m is None:
        return None
    src = str(m.get("source") or "").strip()
    if not src:
        raise ValueError(f"{layer}: a mix with no source is never applied")
    if any(b in src for b in BORROW_REFUSED):
        raise ValueError(f"{layer}: a mix sourced from {BORROW_REFUSED} is a borrowed ratio (stair bed / block "
                         f"mortar), never a wall coat's")
    if m.get("level") not in LEVEL_LABEL:
        raise ValueError(f"{layer}: mix level must be one of {sorted(LEVEL_LABEL)}, got {m.get('level')!r}")
    return {"sand_parts": _pos(m.get("sand_parts"), f"{layer} sand parts"), "source": src, "level": m["level"],
            "label": LEVEL_LABEL[m["level"]]}


def weakest(*labels):
    st = [S5_MAP.get(x, S5_UNKNOWN) for x in labels]
    return max(st, key=lambda s: _RANK[s])


def _coat(x, mix, conv):
    """one V1 layer record -> the same record + its mix stage."""
    out = copy.deepcopy(x)
    base, bound = x.get("mortar_m3"), False
    if base is None and x.get("mortar_m3_at_least") is not None:
        base, bound = x["mortar_m3_at_least"], True
    out["sensitivity_not_a_quantity"] = None if base is None else {
        f"1:{n}": {"cement_bags": _r(base * per_m3(n, conv)["cement_bags"]), "sand_m3": _r(base * per_m3(n, conv)
                                                                                          ["sand_m3"])}
        for n in SENSITIVITY_SAND_PARTS}
    out["sensitivity_basis"] = None if base is None else (
        ("AT_LEAST mortar bound " if bound else "mortar ") + f"{base} m3 x Q-53 C conversion: NOT A QUANTITY")
    ref = MIX_REFERENCE.get(x["layer"], {})
    out.update(water=HELD, conversion_source=conv["source"])
    if x.get("class_held") or (x.get("status") == HELD and x.get("mortar_m3_at_least") is None):
        why = x.get("reason") or "V1 layer HELD"
        return dict(out, mix=None, mix_source=None, mix_label=None, cement_bags=None, sand_m3=None,
                    cement_bags_at_least=None, sand_m3_at_least=None, materials_status=HELD, s5_status=S5_HELD,
                    materials_reason=f"V1 layer HELD ({why}); and mix: " + (
                        "given" if mix else ref.get("missing", "no source")))
    if mix is None:
        return dict(out, mix=None, mix_source=None, mix_label=None, cement_bags=None, sand_m3=None,
                    cement_bags_at_least=None, sand_m3_at_least=None, materials_status=HELD, s5_status=S5_HELD,
                    materials_reason="NEEDS_MIX: " + ref.get("missing", "no source"))
    f = per_m3(mix["sand_parts"], conv)
    bags, sand = _r(base * f["cement_bags"]), _r(base * f["sand_m3"])
    conv_label = LEVEL_LABEL[conv["level"]]
    thick_label = V1.ENET if x.get("label") == V1.ENET else x.get("area_label")
    s5 = weakest(x.get("area_label"), thick_label, mix["label"], conv_label, *([HELD] if bound else []))
    rec = dict(out, mix=f, mix_source=mix["source"], mix_label=mix["label"], s5_status=s5)
    if bound:
        return dict(rec, cement_bags=None, sand_m3=None, cement_bags_at_least=bags, sand_m3_at_least=sand,
                    materials_status=AT_LEAST,
                    materials_reason="thickness is a printed minimum: cement / sand are bounds beside a HELD figure")
    return dict(rec, cement_bags=bags, sand_m3=sand, cement_bags_at_least=None, sand_m3_at_least=None,
                materials_status=OK, materials_reason=f"mortar {base} m3 x {f['ratio']} ({mix['label']})")


def apply(v1_table, mix=None, conversion=CONVERSION):
    """V1 table -> V2 table: each V1 row's layers with their mix stage, and sums per layer (a HELD value is listed,
    never added as 0; a total exists only when every row of the layer has one)."""
    conv = conversion_checked(conversion)
    mixes = {ly: mix_checked(ly, m) for ly, m in (mix or {}).items()}
    unknown = sorted(set(mixes) - set(MIX_REFERENCE))
    if unknown:
        raise ValueError(f"mix for unknown layers {unknown}")
    rows = []
    for r in v1_table["rows"]:
        nr = {k: copy.deepcopy(v) for k, v in r.items() if k != "layers"}
        nr["layers"] = [_coat(x, mixes.get(x["layer"]), conv) for x in r["layers"]]
        rows.append(nr)
    return {"method": METHOD_ID, "reads": v1_table.get("method"), "rules": list(RULES), "conversion": conv,
            "mix_given": copy.deepcopy(mixes), "mix_reference": copy.deepcopy(MIX_REFERENCE),
            "mix_search": [list(s) for s in MIX_SEARCH], "rows": rows, "sums": _sums(rows)}


def _sums(rows):
    out = {}
    for ly in ("BOND_COAT", "WALL_PLASTER", "LEVELLING_RENDER"):
        recs = [(r["id"], x) for r in rows for x in r["layers"] if x["layer"] == ly]
        if not recs:
            continue

        def tot(key):
            v = [x.get(key) for _, x in recs]
            return None if any(a is None for a in v) else _r(sum(v))

        sens = {}
        for n in SENSITIVITY_SAND_PARTS:
            k = f"1:{n}"
            have = [x["sensitivity_not_a_quantity"][k] for _, x in recs if x.get("sensitivity_not_a_quantity")]
            sens[k] = {"cement_bags": _r(sum(h["cement_bags"] for h in have)) if have else None,
                       "sand_m3": _r(sum(h["sand_m3"] for h in have)) if have else None, "rows": len(have)}
        st = [x["s5_status"] for _, x in recs]
        out[ly] = {"rows": len(recs), "cement_bags": tot("cement_bags"), "sand_m3": tot("sand_m3"),
                   "cement_not_in_sum": [i for i, x in recs if x.get("cement_bags") is None],
                   "s5_status": max(st, key=lambda s: _RANK[s]),
                   "sensitivity_not_a_quantity": sens}
    return out


def table(elements, project=None, reference=V1.REFERENCE, mix=None, conversion=CONVERSION):
    """elements (V1 form) -> V1 area / thickness stage -> V2 mix stage."""
    return apply(V1.table(elements, project=project, reference=reference), mix=mix, conversion=conversion)
