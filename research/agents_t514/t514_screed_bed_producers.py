"""T-514: cement / sand PRODUCERS for the screed, threshold / lift marble and outdoor bed host lines (research,
UNWIRED: read by no released method and no candidate V3.0.x; no candidate or released quantity changes).

PHYSICAL ELEMENT FIRST (ERS s.2.1). For every host line the T-511 census left NO_PRODUCER (8 screeds, 14 marble door
thresholds, 3 lift thresholds, 3 lift surrounds, 4 outdoor floors) this table states the layer actually built and its
printed thickness, then decides ONE of: PRODUCED (an owner record whose scope names that physical element gives the
mix and its per-m3 figures), HELD with every missing input named (never 0, never a default), or NOT_APPLICABLE with
evidence. Kept apart: physical layer, installed (theoretical) material, waste, procurement.

Rules (project-independent; R-T514-1 .. 6):
  R-T514-1 LAYER BEFORE ARITHMETIC. A host is computed only when its layer kind is a SITE-MIXED cement : sand layer
           (LAYER_KINDS[kind]['site_mixed'] True). A printed 'screed' with no product / mix stated is
           SCREED_PRODUCT_NOT_STATED (site-mixed cement : sand, a ready-mixed / pre-bagged screed and a lightweight
           falls fill carry different keys: the owner's Q-41 words keep 'screed' apart from 'cement'); a stone
           cladding's fixing and a paver sand bed are not cement : sand beds until a record says so.
  R-T514-2 MIX ONLY FROM A RECORD WHOSE SCOPE NAMES THE ELEMENT. A mix comes from a record in MIX_RECORDS (owner
           decision, company rule built from one, or a printed project note) whose `scope` contains the host's layer
           kind; a caller-supplied ratio with no record (UNSOURCED_MIX) or a record used outside its scope
           (OUT_OF_SCOPE) is refused. The status label is the record's (ASSUMED - OWNER-APPROVED for an owner
           record; DRAWING-CONFIRMED for a printed note); never VERIFIED.
  R-T514-3 ONE CONVERSION PER RATIO (F-T511-4). Bags / sand per m3 of a ratio come from ONE figure per project: an
           owner per-m3 figure for that ratio governs (1:4: Q-45 B practice figure 8.0 bags + 1.1 m3, re-given by
           the owner for Q-78 A and recorded in UPC-TILE-BED-001); the Q-53 C derivation (dry factor 1.33, 1,440
           kg/m3) is the owner's figure ONLY for 1:3 (UP-STAIR-017, his answer to that question) and a method for a
           ratio he gave no figure for. A second figure for the same ratio fails (CONVERSION_CONFLICT): the T-489
           V2 1:4 conversion 7.6608 / 1.064 is BESIDE and may not price a 1:4 layer while the owner's 8.0 / 1.1
           stands (existing versions untouched; this is a rule note of this research record).
  R-T514-4 REPRODUCE BEFORE DERIVING. A screed m3 must equal its m2 partner x the printed thickness (or its merged
           source record when it has no partner) within 1e-6; a bed m3 is area x the record's band (low = thin,
           high = thick; no mid value). Thickness in m / cm / mm is normalised; any other unit fails.
  R-T514-5 ONE PRODUCER PER PHYSICAL KEY. The new rows join the T-511 census (R-T511-2): a second producer on a key
           already produced fails (TWO_PRODUCERS); every host keeps exactly one state.
  R-T514-6 HELD BY NAME, NEVER 0. A HELD host names each missing input (LAYER_TYPE, THICKNESS, MIX, AREA, FINISH);
           a sensitivity figure is BESIDE, labelled NOT A QUANTITY, and enters no subtotal; subtotals follow
           R-T499-1 (a group with a HELD member is HELD, its known part AT_LEAST).

Inputs (sha256-pinned, never edited): the T-511 census module and output (its own 11 pinned inputs, candidate
ARCH_TAKEOFF_V3.0.57 25a8b406), the T-507 line index of V3.0.57 (cross-check of every host line read), the company
rulebook 1.0.0 (UPC-TILE-BED-001), URBAN_RULES_1.8.0 (UP-STAIR-017) and arch_v3058.py (V3.0.58 moves only FIN.WP.ROOF /
FIN.WP.ROOF_UPTURN lines, NOT_A_KEY codes, so every host line of V3.0.58 is the V3.0.57 line).

    python3 -I research/agents_t514/t514_screed_bed_producers.py [OUT_DIR]   # SCREED_BED_PRODUCERS_T514.json / .csv
    python3 -I research/agents_t514/t514_screed_bed_producers.py --check     # exit 1 on any failure
"""

from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import io
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from engine.source import finish_materials_table as V1  # noqa: E402

SCHEMA = "URBAN_T514_SCREED_BED_PRODUCERS_V1"
TABLE = "T-514"
GUARD_CLASS = "UNWIRED_PRODUCER"
CANDIDATE = "ARCH_TAKEOFF_V3.0.58"
CANDIDATE_LINES_SHA8 = "c9570e6c"   # V3_0_58_BOQ_LINES.json (T-507 run note); = V3.0.57 25a8b406 + 5 NOT_A_KEY lines

T511_PY = ROOT / "research/agents_t511/t511_cement_sand_census.py"
T511_OUT = ROOT / "research/agents_t511/out/CEMENT_SAND_CENSUS_T511.json"
INDEX57 = ROOT / "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
RULEBOOK = ROOT / "rules/rulebook/URBAN_COMPANY_RULEBOOK_1.0.0.json"
RULES18 = ROOT / "rules/owner_decisions/URBAN_RULES_1.8.0.json"
V3058 = ROOT / "engine/source/arch_v3058.py"
PINS = {T511_OUT: "a2716399281fbf9dde2e5e762b57562dabe8edccb53af9781da82bc58678aea5",
        INDEX57: "fed5141ea31bfdd9c5f3d89c7fb1fa01365ddbf07b797002780a22016a7f5738",
        RULEBOOK: "4e9c57cef33d32ede26bea4eaf3823e2dc3880d56708dd18ec5df3760b84c055",
        RULES18: "0e4cc090f99bdbfddcc3e1130a3ca90efb4fee19de8bba6116ecf47b83900bac",
        V3058: "b9292a7e40b41cc8bf52953e9c8b75436aad27e66b325ba79b36e66b64be1b94"}
TOL = 1e-6


class ProducerError(ValueError):
    pass


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _load(p, pins=True):
    if pins and _sha(p) != PINS[p]:
        raise ProducerError(f"PIN: {Path(p).name} sha256 {_sha(p)[:8]} is not the pinned {PINS[p][:8]}")
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def t511():
    spec = importlib.util.spec_from_file_location("t511_cement_sand_census", T511_PY)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------- R-T514-1: layer kinds -------------------------
LAYER_KINDS = {
    "FLOOR_TILE_BED": {"site_mixed": True, "trade": "OUTDOOR_BED", "layer": "FLOOR_TILE_BED"},
    "STAIR_MARBLE_BED": {"site_mixed": True, "trade": "STONE_BED", "layer": "STAIR_BED_1:3"},
    "BLOCK_LAYING_MORTAR": {"site_mixed": True, "trade": "MASONRY_LAYING", "layer": "MASONRY_LAYING"},
    "SITE_MIXED_SCREED": {"site_mixed": True, "trade": "SCREED", "layer": "SCREED"},
    "SCREED_PRODUCT_NOT_STATED": {"site_mixed": None, "trade": "SCREED", "layer": "SCREED",
                                  "missing": "LAYER_TYPE: printed 'screed' only: site-mixed cement : sand, "
                                             "ready-mixed / pre-bagged screed or other product not stated"},
    "ROOF_FALLS_SCREED": {"site_mixed": None, "trade": "SCREED", "layer": "SCREED",
                          "missing": "LAYER_TYPE: roof falls layer (cement : sand screed or lightweight fill) not "
                                     "stated"},
    "THRESHOLD_STONE_BED": {"site_mixed": True, "trade": "STONE_BED", "layer": "STONE_BED"},
    "STONE_CLADDING_FIXING": {"site_mixed": None, "trade": "STONE_BED", "layer": "STONE_BED",
                              "missing": "LAYER_TYPE: wall-face marble fixing (adhesive, mortar dabs or mechanical) "
                                         "not printed; not a floor bed"},
    "PAVER_SAND_BED": {"site_mixed": False, "trade": "OUTDOOR_BED", "layer": "OUTDOOR_BED",
                       "missing": "LAYER_TYPE: interlock on a sand bed (no cement); bed thickness / sand per m2 in "
                                  "no owner record (T-495 DECLARED_OUT)"},
    "OUTDOOR_FINISH_NOT_DECIDED": {"site_mixed": None, "trade": "OUTDOOR_BED", "layer": "OUTDOOR_BED",
                                   "missing": "FINISH: floor finish not decided by the owner (T-495 options beside)"},
}


# ---------------------------------------------------------------- R-T514-2 / 3: mix records ----------------------
def _find(o, rid):
    hit = []

    def walk(x):
        if isinstance(x, dict):
            if x.get("rule_id") == rid:
                hit.append(x)
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(o)
    if len(hit) != 1:
        raise ProducerError(f"STALE_INPUT: {rid} found {len(hit)} times")
    return hit[0]


def mix_records(pins=True):
    """The owner mix records, READ from their files (not retyped), each with its scope of physical layer kinds."""
    tb = _find(_load(RULEBOOK, pins), "UPC-TILE-BED-001")
    st = _find(_load(RULES18, pins), "UP-STAIR-017")
    p = tb["params"]
    if tb["status"] != "OWNER_CONFIRMED" or p["mix_cement_sand"]["value"] != "1:4":
        raise ProducerError("STALE_INPUT: UPC-TILE-BED-001 is not an OWNER_CONFIRMED 1:4 record")
    per14 = V1.OWNER_VALUES["per_m3_of_mortar"]["1:4"]
    if (abs(per14["cement_bags_50kg"] - p["cement_bags_per_m3"]["value"]) > TOL
            or abs(per14["sand_m3_loose"] - p["loose_sand_m3_per_m3"]["value"]) > TOL
            or list(V1.OWNER_VALUES["bed_m"]["DRY_FLOOR"]) != list(p["thickness_m_regular_floor"]["value"])
            or list(V1.OWNER_VALUES["bed_m"]["WET_FLOOR"]) != list(p["thickness_m_wet_floor"]["value"])):
        raise ProducerError("STALE_INPUT: UPC-TILE-BED-001 and the V1 record of Q-45 disagree")
    if st["status"] != "OWNER_APPROVED" or st["params"]["mix_cement_sand"] != "1:3":
        raise ProducerError("STALE_INPUT: UP-STAIR-017 is not an OWNER_APPROVED 1:3 record")
    return {
        "UPC-TILE-BED-001": {
            "label": "ASSUMED - OWNER-APPROVED", "source": tb["source"], "scope": ("FLOOR_TILE_BED",),
            "ratio": "1:4", "bags_per_m3": p["cement_bags_per_m3"]["value"],
            "sand_m3_per_m3": p["loose_sand_m3_per_m3"]["value"],
            "band_m": {"REGULAR": tuple(p["thickness_m_regular_floor"]["value"]),
                       "WET": tuple(p["thickness_m_wet_floor"]["value"])},
            "waste": V1.OWNER_VALUES["mortar_waste"],
            "waste_source": "Q-45 B 5 % on mortar (PROVISIONAL, V1 record), its own field"},
        "UP-STAIR-017": {
            "label": "ASSUMED - OWNER-APPROVED", "source": st["approval"]["source"], "scope": ("STAIR_MARBLE_BED",),
            "ratio": "1:3", "bags_per_m3": st["params"]["theoretical_cement_bags_per_m3"],
            "sand_m3_per_m3": st["params"]["theoretical_sand_m3_per_m3"], "band_m": None, "waste": None,
            "waste_source": "UP-STAIR-017: never a waste allowance without a named source"},
        "Q-78-A": {
            "label": "ASSUMED - OWNER-APPROVED", "source": "Q-78 A (owner 2026-11-02): 1:4 priced with the Q-45 figures",
            "scope": ("BLOCK_LAYING_MORTAR",), "ratio": "1:4", "bags_per_m3": per14["cement_bags_50kg"],
            "sand_m3_per_m3": per14["sand_m3_loose"], "band_m": None, "waste": None, "waste_source": None},
    }


def conversions(records, extra=()):
    """R-T514-3: one (bags, sand) figure per ratio over every record + any extra (ratio, bags, sand, source) a caller
    brings (e.g. a derived conversion). Returns ({ratio: (bags, sand, [sources])}, fails)."""
    conv, fails = {}, []
    items = [(r["ratio"], r["bags_per_m3"], r["sand_m3_per_m3"], rid) for rid, r in sorted(records.items())]
    items += list(extra)
    for ratio, b, s, src in items:
        if ratio not in conv:
            conv[ratio] = (b, s, [src])
            continue
        b0, s0, srcs = conv[ratio]
        if abs(b - b0) > TOL or abs(s - s0) > TOL:
            fails.append({"kind": "CONVERSION_CONFLICT", "where": ratio,
                          "why": f"{src} {b} bags / {s} m3 vs {'+'.join(srcs)} {b0} / {s0} per m3"})
        else:
            srcs.append(src)
    return conv, fails


def thickness_m(t):
    """R-T514-4: a printed thickness in m / cm / mm -> m; None stays None; any other unit fails."""
    if t is None:
        return None
    f = {"m": 1.0, "cm": 0.01, "mm": 0.001}.get(t.get("unit"))
    if f is None or t.get("value") is None:
        raise ProducerError(f"UNIT: thickness {t!r} has no m / cm / mm value")
    return t["value"] * f


def resolve(line, decl, records, partner=None, mix=None):
    """R-T514-1 / 2 / 4 / 6 on one host line. mix: optional {'record': id} (or {'ratio': ...} = refused).
    Returns (state, rows, missing, record_id). rows are T-511 prow-shaped dicts (built by the caller's prow)."""
    kind = decl["kind"]
    lk = LAYER_KINDS.get(kind)
    if lk is None:
        raise ProducerError(f"UNCLASSIFIED_LAYER: {kind}")
    missing = []
    if lk["site_mixed"] is not True:
        missing.append(lk["missing"])
    rec_id = None
    if mix is not None:
        rec_id = mix.get("record")
        if rec_id is None or rec_id not in records:
            raise ProducerError(f"UNSOURCED_MIX: {line['line_id']} mix {mix!r} names no record in MIX_RECORDS")
        if kind not in records[rec_id]["scope"]:
            raise ProducerError(f"OUT_OF_SCOPE: {rec_id} covers {records[rec_id]['scope']}, not {kind}")
    else:
        cands = [rid for rid, r in sorted(records.items()) if kind in r["scope"]]
        rec_id = cands[0] if len(cands) == 1 else None
        if len(cands) > 1:
            raise ProducerError(f"TWO_RECORDS: {kind} in the scope of {cands}")
    if rec_id is None and lk["site_mixed"] is not False:
        missing.append("MIX: no owner record or printed note gives the mix of this layer "
                       "(drawings: none printed; owner records Q-45 B / UPC-TILE-BED-001 floor-tile beds, Q-53 C / "
                       "UP-STAIR-017 stair marble beds, Q-78 A block laying: none names it)")
    t = thickness_m(decl.get("thickness"))
    rec = records.get(rec_id) if rec_id else None
    band = None
    if t is not None:
        band = (t, t)
    elif rec is not None and rec.get("band_m"):
        band = rec["band_m"].get(decl.get("floor_class"))
        if band is None:
            missing.append(f"THICKNESS: floor class {decl.get('floor_class')!r} not in {rec_id}")
    else:
        missing.append("THICKNESS: not printed and in no owner record")
    # area / volume
    net = line["measured_net"] if line["class"] == "RELEASED" else None
    m3 = None
    if net is None:
        missing.append(f"AREA: candidate line {line['class']}")
    elif line["unit"] == "m3":
        m3 = (net, net)
        if t is not None and partner is not None:
            if partner["class"] != "RELEASED" or partner["measured_net"] is None:
                missing.append("AREA: m2 partner not released")
                m3 = None
            elif abs(partner["measured_net"] * t - net) > TOL:
                raise ProducerError(f"REPRODUCE: {line['line_id']} m3 {net} != partner {partner['measured_net']} "
                                    f"m2 x {t} m")
        elif decl.get("record_m3") is not None and abs(decl["record_m3"]["value"] - net) > TOL:
            raise ProducerError(f"REPRODUCE: {line['line_id']} m3 {net} != source record {decl['record_m3']}")
    elif line["unit"] == "m2":
        m3 = None if band is None else (net * band[0], net * band[1])
    else:
        missing.append(f"UNIT: host unit {line['unit']}")
    if missing or rec is None or m3 is None:
        return "HELD", m3, sorted(set(missing)) or ["MIX"], rec_id
    return "PRODUCED", m3, [], rec_id


def producer_rows(M, line, m3, rec, rec_id, trade, layer):
    """Installed / waste / procurement rows on one PRODUCED host (T-511 prow shape; one key per stage)."""
    read = {"class": line["class"], "net": line["measured_net"]}
    rows = []
    for mat, per in ((M.CEMENT, rec["bags_per_m3"]), (M.SAND, rec["sand_m3_per_m3"])):
        lo, hi = m3[0] * per, m3[1] * per
        why = f"{rec_id} {rec['ratio']} ({rec['label']})"
        rows.append(M.prow(TABLE, M.PRODUCER, line["line_id"], line["line_id"], layer, mat, M.INSTALLED, lo, hi,
                           read=read, reason=why, trade=trade))
        if rec["waste"] is None:
            rows.append(M.prow(TABLE, M.PRODUCER, line["line_id"], line["line_id"], layer, mat, M.WASTE, None, None,
                               read=read, reason=rec["waste_source"], trade=trade))
            rows.append(M.prow(TABLE, M.PRODUCER, line["line_id"], line["line_id"], layer, mat, M.PROCUREMENT, None,
                               None, read=read, reason="waste HELD: procurement HELD", trade=trade))
        else:
            w = rec["waste"]
            rows.append(M.prow(TABLE, M.PRODUCER, line["line_id"], line["line_id"], layer, mat, M.WASTE, lo * w,
                               hi * w, read=read, reason=rec["waste_source"], trade=trade))
            rows.append(M.prow(TABLE, M.PRODUCER, line["line_id"], line["line_id"], layer, mat, M.PROCUREMENT,
                               lo * (1 + w), hi * (1 + w), read=read, reason="installed + waste", trade=trade))
    return rows


def sensitivity(line, decl, conv):
    """BESIDE, NOT A QUANTITY (R-T514-6): what the HELD layer would take at each owner ratio the project already
    uses, over the printed thickness or, with none printed, the owner's regular-floor band. Never summed."""
    net = line["measured_net"] if line["class"] == "RELEASED" else None
    if net is None:
        return None
    t = thickness_m(decl.get("thickness"))
    if line["unit"] == "m3":
        m3 = (net, net)
        basis = "released m3"
    elif line["unit"] == "m2":
        band = (t, t) if t is not None else tuple(V1.OWNER_VALUES["bed_m"]["DRY_FLOOR"])
        m3 = (net * band[0], net * band[1])
        basis = f"area x {band[0]} .. {band[1]} m"
    else:
        return None
    out = {"line_id": line["line_id"], "basis": basis, "m3": [_r(m3[0]), _r(m3[1])],
           "label": "NOT A QUANTITY: sensitivity at the ratios the project already uses; enters no subtotal"}
    for ratio in sorted(conv):
        b, s, _ = conv[ratio]
        out[ratio] = {"cement_bags": [_r(m3[0] * b), _r(m3[1] * b)], "sand_m3": [_r(m3[0] * s), _r(m3[1] * s)]}
    return out


# ---------------------------------------------------------------- build --------------------------------------------
def build(pins=True, declarations=None, mixes=None):
    import t514_inputs as INP
    M = t511()
    if pins:
        _load(T511_OUT, pins)
    decls = INP.DECLARATIONS if declarations is None else declarations
    mixes = mixes or {}
    records = mix_records(pins)
    conv, fails = conversions(records)
    lines, ident = M.candidate(pins)
    by_id = {ln["line_id"]: ln for ln in lines}
    # cross-check: every host read here is byte-equal (by value) to the T-507 V3.0.57 index line
    # (F-T514-1) the T-511 chain applies T-310 ADD rows from their 4-decimal display column; the line index carries
    # the candidate figure. A difference below 5e-5 in the net only is a DISPLAY_ROUNDING finding and the index
    # line governs; any other difference fails.
    i57 = {x["line_id"]: x for x in _load(INDEX57, pins)["lines"]}
    findings = []
    for lid in decls:
        a, b = by_id.get(lid), i57.get(lid)
        if a is None or b is None:
            fails.append({"kind": "STALE_CANDIDATE", "where": lid, "why": "host missing from the T-511 chain or the "
                                                                         "T-507 V3.0.57 index"})
            continue
        if M._key(a) == M._key(b):
            continue
        ka, kb = M._key(a), M._key(b)
        if (ka[:2] + ka[3:] == kb[:2] + kb[3:] and ka[2] is not None and kb[2] is not None
                and abs(ka[2] - kb[2]) < 5e-5):
            findings.append({"id": "F-T514-1", "line_id": lid, "t511_chain_net": ka[2], "index_net": kb[2],
                             "why": "DISPLAY_ROUNDING: T-511 chain read the T-310 row display value; the candidate "
                                    "line index governs"})
            for i, ln in enumerate(lines):
                if ln["line_id"] == lid:
                    lines[i] = dict(ln, measured_net=kb[2])
            by_id[lid] = next(ln for ln in lines if ln["line_id"] == lid)
        else:
            fails.append({"kind": "STALE_CANDIDATE", "where": lid, "why": "host differs between T-511 chain and the "
                                                                         "T-507 V3.0.57 index"})
    src = Path(V3058).read_text(encoding="utf-8") if pins else ""
    if pins and ("nothing outside FIN.WP.ROOF / FIN.WP.ROOF_UPTURN moves" not in src):
        fails.append({"kind": "STALE_CANDIDATE", "where": "V3.0.58", "why": "arch_v3058 no longer states its scope"})
    # T-511 producers and states, unchanged except the hosts this table resolves
    m_rows, m_states = M.masonry_rows(lines, pins)
    p_rows, p_states = M.plaster_rows(lines, pins)
    b_rows, b_states, _missing = M.bed_rows(lines, pins)
    o_rows, o_states, _beside = M.other_hosts(lines, pins)
    s_rows, s_states = M.stair_bed_rows(lines, pins)
    states = {}
    for st in (m_states, p_states, b_states, o_states, s_states):
        states.update(st)
    before = copy.deepcopy(states)
    new_rows, table, beside = [], [], []
    for lid, decl in sorted(decls.items()):
        ln = by_id.get(lid)
        if ln is None:
            fails.append({"kind": "STALE_CANDIDATE", "where": lid, "why": "declared host not on the candidate"})
            continue
        kind, trade, _w = M.CODE_TABLE.get(ln["item_code"], ("?", None, None))
        if kind != "HOST":
            fails.append({"kind": "KEY_ON_NON_HOST", "where": lid, "why": f"{ln['item_code']} is {kind}"})
            continue
        partner = by_id.get(decl.get("partner")) if decl.get("partner") else None
        try:
            state, m3, missing, rec_id = resolve(ln, decl, records, partner, mixes.get(lid))
        except ProducerError as e:
            fails.append({"kind": str(e).split(":")[0], "where": lid, "why": str(e)})
            continue
        lk = LAYER_KINDS[decl["kind"]]
        row = {"line_id": lid, "item_code": ln["item_code"], "element": decl.get("element"), "class": ln["class"],
               "net": ln["measured_net"], "unit": ln["unit"], "layer_kind": decl["kind"],
               "thickness_m": thickness_m(decl.get("thickness")),
               "thickness_source": (decl.get("thickness") or {}).get("source"), "finish": decl.get("finish"),
               "state": state, "record": rec_id, "missing": missing,
               "m3": None if m3 is None else [_r(m3[0]), _r(m3[1])], "t511_state": list(before.get(lid, ()))}
        if state == "PRODUCED":
            rec = records[rec_id]
            rows = producer_rows(M, ln, m3, rec, rec_id, trade, lk["layer"])
            new_rows += rows
            states.pop(lid, None)
            row["label"] = rec["label"]
            row["cement_bags"] = [_r(m3[0] * rec["bags_per_m3"]), _r(m3[1] * rec["bags_per_m3"])]
            row["sand_m3"] = [_r(m3[0] * rec["sand_m3_per_m3"]), _r(m3[1] * rec["sand_m3_per_m3"])]
        else:
            states[lid] = ("HELD", trade, "HELD (T-514): " + "; ".join(missing))
            row["label"] = "HELD"
            s = sensitivity(ln, decl, conv) if lk["site_mixed"] is not False else None
            if s:
                beside.append(s)
        table.append(row)
    # lm partners / m2 screed partners keep their T-511 NOT_APPLICABLE state (unchanged)
    rows = m_rows + p_rows + b_rows + o_rows + s_rows + new_rows
    c = M.census(lines, rows, states)
    fails += c["fails"]
    tally = {}
    for (lid, mat), st in c["states"].items():
        if mat == M.CEMENT:
            tally[st] = tally.get(st, 0) + 1
    old = _load(T511_OUT, pins) if pins else None
    hosts = {}
    for row in table:
        hosts.setdefault(row["layer_kind"], {}).setdefault(row["state"], 0)
        hosts[row["layer_kind"]][row["state"]] += 1
    return {
        "schema": SCHEMA, "table": TABLE, "guard_class": GUARD_CLASS, "candidate": CANDIDATE,
        "candidate_lines_sha8": CANDIDATE_LINES_SHA8, "census_base": M.CANDIDATE, "census_base_sha8": M.CANDIDATE_SHA8,
        "identity": {"t511": ident, "v3058": "V3.0.57 + 5 FIN.WP.ROOF / FIN.WP.ROOF_UPTURN lines (NOT_A_KEY, "
                                             "arch_v3058 R-T507-1 (e)); every host line identical"},
        "input_sha256": {Path(p).relative_to(ROOT).as_posix(): h for p, h in PINS.items()},
        "rules": ["R-T514-%d" % i for i in range(1, 7)],
        "mix_records": {k: {kk: (list(vv) if isinstance(vv, tuple) else vv) for kk, vv in v.items()}
                        for k, v in sorted(records.items())},
        "conversions": {k: {"bags_per_m3": v[0], "sand_m3_per_m3": v[1], "sources": v[2]}
                        for k, v in sorted(conv.items())},
        "conversion_beside": {"ratio": "1:4", "bags_per_m3": 7.6608, "sand_m3_per_m3": 1.064,
                              "source": "T-489 PLASTER_MATERIALS_TABLE_V2 (Q-53 C method applied to 1:4)",
                              "state": "BESIDE: refused as a second 1:4 figure while the owner's 8.0 / 1.1 stands "
                                       "(R-T514-3); difference -4.24 % cement, -3.27 % sand"},
        "hosts": table, "hosts_by_kind": {k: dict(sorted(v.items())) for k, v in sorted(hosts.items())},
        "host_states_cement": dict(sorted(tally.items())),
        "t511_host_states_cement": old["host_states_cement"] if old else None,
        "missing_hosts": INP.MISSING_HOSTS, "beside": beside, "findings": findings,
        "screed_released_m3": _r(sum(r["net"] for r in table if r["layer_kind"] == "SCREED_PRODUCT_NOT_STATED"
                                     and r["class"] == "RELEASED")),
        "subtotals": c["subtotals"], "t511_project": (old or {}).get("subtotals", {}).get("PROJECT"),
        "keys_with_two_producers": sum(1 for f in fails if f["kind"] == "TWO_PRODUCERS"),
        "rows": sorted(new_rows, key=lambda r: (r["line_id"], r["material"], r["stage"])),
        "fails": fails, "released_quantities_changed": 0,
    }


CSV_COLS = ("line_id", "item_code", "layer_kind", "class", "net", "unit", "thickness_m", "state", "record", "label",
            "m3", "cement_bags", "sand_m3", "missing")


def write(m, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "SCREED_BED_PRODUCERS_T514.json").write_text(
        json.dumps(m, indent=1, sort_keys=True, ensure_ascii=False, default=list) + "\n", encoding="utf-8")
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CSV_COLS)
    for r in m["hosts"]:
        w.writerow(["" if r.get(k) is None else (" .. ".join(map(str, r[k])) if isinstance(r.get(k), list)
                                                 else r.get(k)) for k in CSV_COLS])
    (out_dir / "SCREED_BED_PRODUCERS_T514.csv").write_text(buf.getvalue(), encoding="utf-8")


def main(argv):
    m = build()
    if argv and argv[0] == "--check":
        for f in m["fails"]:
            print("FAIL", f["kind"], f["where"], f["why"])
        print(f"fails {len(m['fails'])}; hosts {len(m['hosts'])}; states {m['host_states_cement']}")
        return 1 if m["fails"] else 0
    write(m, Path(argv[0]) if argv else HERE / "out")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
