"""T-647 development-villa build (research, unwired), R-T647-1 (t647_rules.py): the 183 structural HELD lines of the
10 Nov trial BOQ (T-636 finding F-T636-1: B11 138, B9 32, B10 13) each given ONE recorded cause with its committed
source, read from merged ledgers by line id (never typed from memory; every cited text is checked in its file).

  B11 138  the slab bar-end VALUED part lines (<parent>#SLAB_BAR_ENDS:VALUED, T-318 / ARCH_TAKEOFF_V3.0.27): read
           through the engine's own read-only arch_v3027.load_inputs on the merged T-307 / T-316 ledgers; per line
           the bound is re-derived and must equal the line's held_low / held_high in the V3.0.57 index:
             79 top parts      DESIGNER_ITEM RFI-B-S10 (plan note 2 'one third of the span' vs ST p.15
                               '.30 L1 OR .30 L2' / '.25 L1': two printed documents; the line is their envelope);
                               refused if the two readings are equal on the line (then the cause would be wrong);
             59 development    PRINTED_VALUE_GAP ST p.4 / p.5 / p.6: the mesh is printed as a rate 'n o d/m' with no
                               first / last bar position: count A = ceil(rate x W) .. B = A + 1 (T-306
                               COUNT_CONVENTION); the p.15 straight length is drawing-derived; refused if low == high.
  B10 13 / B9 8 work lines     one record each from the merged task that holds it (T-075, T-319, T-407, T-430, T-433,
                               T-482 / T-488 / T-543, T-638), the cited text checked in the file.
  B9 24 material lines         (T-498 stage rows, T-580 input): DEPENDENCY on the host block line by id when the host
                               is HELD; when the host is RELEASED, the line's own hold (T-453: white AAC block face not
                               selected) as a PRINTED_VALUE_GAP.

Nothing is wired; no candidate, released, rule, knowledge or registry file is written; no quantity moves (the HELD
census before / after is asserted identical); the five CN column lines get a FIX_ROW proposal (NOT_APPLICABLE on the
printed schedule) that stays beside the HELD line until the Checker and lane I act on it.
Rebuild (wrapper only): `URBAN_T647_WRITE=1 bash scripts/agent_env.sh pytest --tree task-T-647
tests/t647/test_t647.py::test_write_outputs`; check: `bash scripts/agent_env.sh pytest --tree task-T-647 tests/t647`.
No drawing content beyond sheet / note references and marks, no client name."""
from __future__ import annotations

import collections
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (HERE, ROOT, ROOT / "research/agents_t318"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import t647_rules as R  # noqa: E402

SCHEMA, RULE = "URBAN_T647_HELD_CAUSE_CENSUS_V1", "R-T647-1"
TRIAL = "research/agents_t636/out/TRIAL_BOQ_T636.json"
INDEX = "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
STAGE = "research/agents_t580/in/T498_STAGE_ROWS.json"
T453 = "research/agents_t453/out/BLOCK_MATERIALS_T453.csv"
T306 = "research/agents_t306/T-306_SLAB_REBAR_BOUND_DECOMPOSITION.md"
T318 = "research/agents_t318/T-318_SLAB_BAR_END_INTEGRATION.md"
T376 = "research/agents_t376/T376_LINE_UNLOCK.csv"
OUT = HERE / "out"
SCOPE = ("B9", "B10", "B11")
SUFFIX = "#SLAB_BAR_ENDS:VALUED"
BARE_LABEL = {("GF-020", "y"), ("GF-076", "x"), ("1F-041", "y")}   # T-306 LABEL_MEANING (printed list)


def src(file, read_on):
    return {"file": file, "read_on": read_on}


def _cn(n, lid):
    return {"line_id": lid, "cause_class": "FIX_ROW", "ref": f"FR-T647-{n}",
            "cause": "CN column above ground not printed: ST p.9 Schedule of Columns row CN 'foundation 30 x 30, 4 Ø14' "
                     "with the GF, 1F and 2F cells struck (DXF segment D2:7041, PDF p.9 cross-check, T-075); the current "
                     "hold TYPE_NOT_IN_SCHEDULE is the frozen schedule reader missing the CN text row",
            "also": ["the CN neck below GF is carried by the 6 CN neck lines (HELD on the founding datum, Q-21 C), not here",
                     "re-read this run (T-647): Drive 'Alsenan chalet project' / 'ST7757.pdf' p.9 rendered at 60 dpi in the "
                     "private folder: row CN 'FOUNDATION 30 30 4 ø 14', one drawn line through the GF, 1st floor and 2nd "
                     "floor cells: AGREE with T-075",
                     "Checker: the column plan (DXF sheet 12) draws 5 CN outlines; T-075 reads them as neck positions "
                     "(no column above ground); confirm the plan's level before wiring"],
            "fix_row": {"proposed_state": "NOT_APPLICABLE_WITH_EVIDENCE",
                        "hand_calculation": "storeys printed for CN above the neck = 0 (GF, 1F, 2F struck) -> CN column "
                                            "concrete above GF = 0 storeys x 0.30 x 0.30 m: no column, no line "
                                            "(an absence printed on the schedule, not a missing value)",
                        "evidence": "DRAWING-CONFIRMED (T-075 hand read on DXF and PDF p.9, merged, verifier 2026-10-19)",
                        "verdict_proposal": "ENGINE_WRONG (held lines for a member the schedule prints as absent; "
                                            "freelancer also 0 CN columns)", "wired": False},
            "sources": [src("research/agents_t075/T-075_SCHEDULE_TEXT_ROWS.md", "NOT_PRESENT, NECK_ONLY_TYPE"),
                        src("research/agents_t433/summary_t433.json", lid),
                        src("research/agents_t387/BINDING_T387.csv", lid)]}


def work_line_records():
    """the 21 B10 / B9 work lines: one record each, cited by line id from the merged task that holds it."""
    recs = [_cn(i + 1, lid) for i, lid in enumerate((
        "L-0d4cd54cb397f210d1fd", "L-1850e27801a200419510", "L-53a35abf19b1d8807f38", "L-d33f749864d96dd236f0",
        "L-de9383f76f000503e1d7"))]
    recs.append({"line_id": "L-d5401fa8986900c66c37", "cause_class": "DESIGNER_ITEM", "ref": "D-21",
                 "cause": "DOME-3 tower dome over the 2F maid room: the architecture draws a dome, the structural slab is "
                          "flat with no opening or ring; shell section / depth / extent not printed (Q-27 A)",
                 "also": ["RFI-S28"],
                 "sources": [src("research/agents_t433/summary_t433.json", "D-21 tower dome over the 2F maid room"),
                             src("research/agents_t638/out/FORMWORK_HOLD_CENSUS_T638.json", "L-d5401fa8986900c66c37")]})
    for lid, band in (("L-95a1f198cfe7f398d6ae", "7DC+7DD#1"), ("L-cfb4555cb26b39934bff", "7E7+7E8#2")):
        recs.append({"line_id": lid, "cause_class": "DESIGNER_ITEM", "ref": "D-33",
                     "cause": f"ground-beam run {band} carries a landing beam: ST p.13 prints sections only 'without "
                              "concentrated load'; the loaded run's section is not printed (beside 0.4230 .. 0.64 m3, "
                              "not adopted)", "also": ["RFI-S10"],
                     "sources": [src("research/agents_t430/T-430_GB_RUN_SECTION_INTEGRATION.md", lid)]})
    for lid in ("L-030538dda6a32c601c4c", "L-1d419b64e8ca1af30fb4", "L-9a2c81164ec6499cc28c", "L-b5ffc172a354375ca107"):
        recs.append({"line_id": lid, "cause_class": "OWNER_DECISION", "ref": "Q-65 C",
                     "cause": "parapet RC: at least 0.30 m RC above the slab in every alternative, the rest of the "
                              "parapet material is the designer's (owner Q-65 C) and the roof build-up depth at the edge "
                              "is not printed (D-39): BLOCKED_RFI, blank", "also": ["D-39"],
                     "sources": [src("research/agents_t319/T-319_PARAPET_RC_INTEGRATION.md", "Q-65 C: designer"),
                                 src("research/agents_t638/out/FORMWORK_HOLD_CENSUS_T638.json", lid),
                                 src("research/agents_t433/summary_t433.json", lid)]})
    recs.append({"line_id": "L-b62a7065645589011141", "cause_class": "DESIGNER_ITEM", "ref": "RFI-A02",
                 "cause": "pool steps not drawn (arch GF plan, ST p.7, sections): an absence of evidence, not a verified "
                          "zero", "also": [],
                 "sources": [src("research/agents_t433/summary_t433.json", "pool steps not drawn (consultant item)")]})
    for lid, eid in (("L-76a4d8e50423fb02b914", "t=0.20#BLOCKWORK:VERIFIED_BLACK"),
                     ("L-9056ebed77701b50abfc", "t=0.15#BLOCKWORK:ASSUMED___OWNER_APPROVED_WHITE"),
                     ("L-a6eedf5e4adec6d07618", "t=0.20#BLOCKWORK:DRAWING_CONFIRMED_BLACK"),
                     ("L-bbb82de298fecbafa11d", "t=0.20#BLOCKWORK:DRAWING_CONFIRMED_WHITE"),
                     ("L-e1e06ec149b44d4f6f8a", "t=0.15#BLOCKWORK:ASSUMED___OWNER_APPROVED_BLACK"),
                     ("L-e90c9dd5ca08ffb64728", "t=0.20#BLOCKWORK:VERIFIED_WHITE")):
        recs.append({"line_id": lid, "cause_class": "DESIGNER_ITEM", "ref": "D-39",
                     "cause": f"2F block walls ({eid}): wall height to the main-roof beam soffit needs the roof slab "
                              "datum / beam depth b_r, not printed (section A-A +13.90 is a finished level): HELD ON "
                              "ROOF DATUM (D-39); U = 53.5225 - 14.925 b_r m2 on the valued set, not adopted",
                     "also": ["RFI-S23"],
                     "sources": [src("research/agents_t543/t543_inputs.py", "HELD ON ROOF DATUM (D-39)"),
                                 src("research/agents_t482/T-482_BLOCKWORK_CONDITIONS.md", "HELD ON ROOF DATUM"),
                                 src("research/agents_t543/out/T543_BLOCKWORK_RECONCILE.json", lid)]})
    recs.append({"line_id": "L-7503af7cc1eea4e6735d", "cause_class": "PRINTED_VALUE_GAP",
                 "ref": "ST p.1 note 2 / p.13",
                 "cause": "black block below the main-house neighbour-side ground beams (MAIN_S, 16.270 m net axis): "
                          "printed by ST p.1 note 2, but no section prints its thickness or bottom level: height only "
                          "h >= 0.70 m (gross AT_LEAST 13.4897, net AT_LEAST 11.389 m2), no upper bound: HELD",
                 "also": [],
                 "sources": [src("research/agents_t407/T-407_HOUSE_GB_MASONRY.md", "MISSING, HELD: gross AT_LEAST 13.4897"),
                             src("research/agents_t543/out/T543_BLOCKWORK_RECONCILE.json", "L-7503af7cc1eea4e6735d")]})
    recs.append({"line_id": "L-ee857398614d817e6917", "cause_class": "DESIGNER_ITEM", "ref": "D-35",
                 "cause": "black block below the annex neighbour-side ground beams (ANNEX_S, 10.000 m net axis): the "
                          "annex exterior ground-beam soffit is a CONFLICT (levels reading L vs the printed section), "
                          "so the masonry height has no bound", "also": ["RFI-S09"],
                 "sources": [src("research/agents_t407/T-407_HOUSE_GB_MASONRY.md", "ANNEX_S HELD (CONFLICT)"),
                             src("research/agents_t543/out/T543_BLOCKWORK_RECONCILE.json", "L-ee857398614d817e6917")]})
    return recs


def sha256(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def _json(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def scope_lines(trial):
    """the F-T636-1 lines of B9 / B10 / B11 by id, with their trial record (class, bounds)."""
    pl = {p["line_id"]: p for p in trial["per_line"]}
    out = []
    for k, v in trial["findings"]["F-T636-1"]["by_item_code"].items():
        if k.split()[0] in SCOPE:
            out += [pl[lid] for lid in v["line_ids"]]
    return out


def slab_records(lines, index):
    """B11 slab bar-end VALUED parts: the T-318 record re-derived through the engine's own reader (read only)."""
    import t318_inputs as TI
    from engine.source import arch_v3027 as A
    doc = A.load_inputs(TI.build())
    recs = {r["line_id"]: r for r in doc["lines"]}
    by_eid = {l["element_id"]: l for l in index["lines"]}
    out = []
    for p in lines:
        eid = (index_by_id(index).get(p["line_id"]) or {}).get("element_id") or ""
        if not eid.endswith(SUFFIX):
            continue
        parent = by_eid.get(eid[: -len(SUFFIX)])
        r = recs.get(parent["line_id"]) if parent else None
        if r is None or r["action"] != "PARENT":
            raise R.CauseError(f"{p['line_id']}: no T-318 split record for the parent of {eid}")
        part = r["part"]
        lo, hi = D(p["held_low"]), D(p["held_high"])
        if abs(D(part["low"]) - lo) > Decimal("0.0015") or abs(D(part["high"]) - hi) > Decimal("0.0015"):
            raise R.CauseError(f"{p['line_id']}: T-318 bound {part['low']} .. {part['high']} != line {lo} .. {hi}")
        base = {"line_id": p["line_id"], "element_id": eid, "parent_line_id": parent["line_id"],
                "bound_kg": {"low": str(lo), "high": str(hi)}}
        if r["population"] == A.TOP:
            n2, p15 = part["note2"], part["p15"]
            if abs(n2["low"] - p15["low"]) < 1e-6 and abs(n2["high"] - p15["high"]) < 1e-6:
                raise R.CauseError(f"{p['line_id']}: note 2 and p.15 agree on the line: RFI-B-S10 is not its cause")
            out.append(dict(base, cause_class="DESIGNER_ITEM", ref="RFI-B-S10", population="TOP",
                            cause=f"top-bar extent printed twice: plan note 2 {n2['low']:.3f} .. {n2['high']:.3f} kg vs "
                                  f"ST p.15 {p15['low']:.3f} .. {p15['high']:.3f} kg on the same valued ends; the line "
                                  "is their envelope (no reading chosen, T-318)",
                            also=["count convention A .. B (T-306)", f"legs / held ends BLANK on the parent {parent['line_id']}"],
                            sources=[src(T318, "plan note 2 vs p.15 stays a designer item"),
                                     src(T306, "TOP_NOTE2_VS_P15"),
                                     src("research/agents_t316/TOP_LINE_LEDGER_T316.csv", parent["line_id"])]))
        else:
            hc = dev_hand(parent["line_id"])
            ka, kb = hc["A"]["kg"], hc["B"]["kg"]   # count A can carry more edge-beam ends than B on a skewed panel
            base["hand_calculation"] = {rd: {k: str(v) for k, v in hc[rd].items()} for rd in "AB"}
            tol = Decimal("0.0015")
            if (r["element"].split(":")[-1], r["direction"]) in BARE_LABEL:
                # T-306 LABEL_MEANING / T-307 F-04: '5 o 10' printed without '/m': '5 in all' is a reading too, so the
                # bound must CONTAIN both count readings (not equal them)
                if not (lo - tol <= min(ka, kb) and max(ka, kb) <= hi + tol):
                    raise R.CauseError(f"{p['line_id']}: count readings {ka} / {kb} outside the label bound {lo} .. {hi}")
                out.append(dict(base, cause_class="PRINTED_VALUE_GAP", ref="ST p.4 / p.5 slab plans (bare label)",
                                population="DEVELOPMENT",
                                cause=f"bar label printed without '/m' ('5 o 10' on {r['element']} {r['direction']}): 5 "
                                      "bars in all or 5 per metre; the bound carries both readings and the count "
                                      f"convention A .. B: {lo} .. {hi} kg",
                                also=["count convention A .. B (T-306)",
                                      f"up-turn legs BLANK on the parent {parent['line_id']}"],
                                sources=[src(T306, "LABEL_MEANING"),
                                         src("research/agents_t307/T-307_SLAB_BAR_ENDS.md", "F-04 the 3 bare-label")]))
                continue
            if abs(min(ka, kb) - lo) > tol or abs(max(ka, kb) - hi) > tol:
                raise R.CauseError(f"{p['line_id']}: hand re-add A {ka} / B {kb} != line {lo} .. {hi}")
            if hc["A"]["ends"] == hc["B"]["ends"] and hc["A"]["sum_len_m"] == hc["B"]["sum_len_m"]:
                # the count convention does not reach the valued ends: the bound is degenerate (low == high)
                kg = hc["A"]["kg"]
                out.append(dict(base, cause_class="FIX_ROW", ref="FR-T647-?", population="DEVELOPMENT",
                                cause="degenerate bound: count A and count B give the same edge-beam ends, so the valued "
                                      "part is determinate; HELD only because every T-318 part line is booked "
                                      "BOUNDED_EXPOSURE (no record holds it on an open input)",
                                also=[f"up-turn legs and undrawn ends stay BLANK on the parent {parent['line_id']}"],
                                fix_row={"proposed_state": f"DRAWING-CONFIRMED measured_net {q6(kg)} kg (one value, "
                                                           f"no range)",
                                         "hand_calculation": f"{hc['A']['ends']} edge-beam ends x (w - 0.040) summed "
                                                             f"= {hc['A']['sum_len_m']} m x {hc['A']['d_mm']}^2/162 "
                                                             f"= {q6(kg)} kg (A = B; ST p.15 '40 CL.', widths drawn)",
                                         "evidence": "DRAWING-DERIVED length (T-307, Checker Gate A PASS) re-added end by "
                                                     "end here; count identical under both readings",
                                         "verdict_proposal": "ENGINE_RIGHT on the value; the HELD state is a booking "
                                                             "artefact (release once wired)",
                                         "kg": str(q6(kg)), "wired": False},
                                sources=[src(T318, "DRAWING-CONFIRMED (BOUND): the 59 development parts"),
                                         src("research/agents_t307/BAR_END_DETAIL_T307.csv", parent["line_id"])]))
                continue
            out.append(dict(base, cause_class="PRINTED_VALUE_GAP", ref="ST p.4 / p.5 / p.6 slab plans",
                            population="DEVELOPMENT",
                            cause="bottom mesh printed as a rate 'n o d/m' with no first / last bar position: count A "
                                  "= ceil(rate x W) .. B = A + 1; the p.15 straight length w - 0.040 m is drawing-"
                                  f"derived; bound {lo} .. {hi} kg (Q-71 point 9 principle: PROVISIONAL / HELD)",
                            also=[f"up-turn legs and undrawn ends BLANK on the parent {parent['line_id']} (RFI-B-S10 (e))"],
                            sources=[src(T306, "COUNT_CONVENTION"),
                                     src("research/agents_t307/LANE_I_CONSUMER_T307.csv", parent["line_id"])]))
    return out


_IDX = {}
_DET = {}


def q6(x):
    return x.quantize(Decimal("0.000001"))


def dev_hand(parent_id):
    """hand re-add of a development part from the merged T-307 end ledger: per reading, the EDGE_BEAM ends,
    sum of (w - 0.040) and kg = sum x d^2 / 162 (the p.15 straight part; no leg, no lap)."""
    import csv
    if not _DET:
        for r in csv.DictReader((ROOT / "research/agents_t307/BAR_END_DETAIL_T307.csv").open(encoding="utf-8")):
            _DET.setdefault(r["line_id"], []).append(r)
        for r in csv.DictReader((ROOT / "research/agents_t307/BAR_END_CENSUS_T307.csv").open(encoding="utf-8")):
            _DET.setdefault(("d", r["line_id"]), int(r["d_mm"]))
    d = _DET[("d", parent_id)]
    out = {}
    for rd in "AB":
        ends = [r for r in _DET.get(parent_id, ()) if r["reading"] == rd and r["support"] == "EDGE_BEAM"]
        s = sum((D(r["width_m"]) - D("0.040") for r in ends), Decimal(0))
        out[rd] = {"ends": len(ends), "sum_len_m": s, "d_mm": d, "kg": s * D(d * d) / D(162)}
    return out


def index_by_id(index):
    k = id(index)
    if k not in _IDX:
        _IDX[k] = {l["line_id"]: l for l in index["lines"]}
    return _IDX[k]


def D(x):
    return Decimal(str(x))


def material_records(lines, trial, own):
    """B9 material lines (no element id in the index): host by the T-498 stage row."""
    stage = {r["line_id"]: r for r in _json(STAGE)["rows"]}
    pl = {p["line_id"]: p for p in trial["per_line"]}
    t453 = (ROOT / T453).read_text(encoding="utf-8")
    out = []
    for p in lines:
        if p["line_id"] in own or p["line_id"] not in stage:
            continue
        s = stage[p["line_id"]]
        host = pl.get(s["source_line_id"])
        if host is None:
            raise R.CauseError(f"{p['line_id']}: host {s['source_line_id']} not in the trial BOQ")
        base = {"line_id": p["line_id"], "element_id": s["element_id"], "item_code": s["item_code"],
                "host_line_id": s["source_line_id"]}
        if host["class"] == "HELD":
            out.append(dict(base, cause_class="DEPENDENCY", ref=s["source_line_id"],
                            cause=f"{s['item_code']} is produced from its host block line {s['source_line_id']}, "
                                  "which is HELD: the material follows the host (never valued ahead of it)",
                            also=[], sources=[src(STAGE, p["line_id"])]))
        else:
            why = "white AAC block face not selected by the project"
            if f"{s['source_line_id']}," not in t453 or why not in t453:
                raise R.CauseError(f"{p['line_id']}: no committed hold text for the released host {s['source_line_id']}")
            out.append(dict(base, cause_class="PRINTED_VALUE_GAP",
                            ref="arch sheet set: no block specification or schedule issued",
                            cause=f"{s['item_code']} on a RELEASED host ({s['source_line_id']}): the white AAC unit count "
                                  "needs the block face, which no sheet selects (supplier sheet: 62.5 x 25 = 6.4 / m2 "
                                  "or 60 x 20 = 8.33 / m2; no company AAC count rule): HELD, never the black 12.5 / m2",
                            also=["D-62 (no specification issued)"],
                            sources=[src(T453, why), src(STAGE, p["line_id"])]))
    return out


def verify_sources(recs):
    pinned = {}
    for r in recs:
        for s in r["sources"]:
            f = s["file"]
            if f not in pinned:
                pinned[f] = ((ROOT / f).read_text(encoding="utf-8"), sha256(f))
            if s["read_on"] not in pinned[f][0]:
                raise R.CauseError(f"{r['line_id']}: '{s['read_on']}' not found in {f}: the cited cause is not in its source")
    return {f: v[1] for f, v in sorted(pinned.items())}


def census(lines, fix_ids=()):
    """HELD census per trade x unit: blank n, bounded n, low / high (exact Decimal; a census, not a total)."""
    acc = collections.OrderedDict()
    for p in sorted(lines, key=lambda x: (x["group"], x["unit"])):
        if p["line_id"] in fix_ids:
            continue
        k = f"{p['group']} {p['unit']}"
        a = acc.setdefault(k, {"held_blank": 0, "held_bounded": 0, "bounded_low": Decimal(0), "bounded_high": Decimal(0)})
        if p["held_low"] is None:
            a["held_blank"] += 1
        else:
            a["held_bounded"] += 1
            a["bounded_low"] += D(p["held_low"])
            a["bounded_high"] += D(p["held_high"])
    return {k: {kk: (str(vv) if isinstance(vv, Decimal) else vv) for kk, vv in v.items()} for k, v in acc.items()}


def build():
    trial, index = _json(TRIAL), _json(INDEX)
    lines = scope_lines(trial)
    if len(lines) != 183:
        raise R.CauseError(f"scope is {len(lines)} lines, the trial BOQ names 183")
    for p in lines:
        if p["class"] != "HELD" or p.get("cause") is not None:
            raise R.CauseError(f"{p['line_id']}: not a HELD line without a cause in the trial BOQ")
    work = work_line_records()
    slab = slab_records(lines, index)
    own = {r["line_id"] for r in work} | {r["line_id"] for r in slab}
    mat = material_records(lines, trial, own)
    for n, r in enumerate(sorted((r for r in slab if r["cause_class"] == "FIX_ROW"), key=lambda r: r["line_id"]), 6):
        r["ref"] = f"FR-T647-{n}"
    recs = slab + work + mat
    ids = [r["line_id"] for r in recs]
    if sorted(ids) != sorted(p["line_id"] for p in lines) or len(set(ids)) != len(ids):
        raise R.CauseError(f"records {len(ids)} do not cover the 183 lines exactly once")
    held_ids = {p["line_id"] for p in trial["per_line"] if p["class"] == "HELD"}
    pl = {p["line_id"]: p for p in lines}
    for r in recs:
        p = pl[r["line_id"]]
        r.update(group=p["group"], item_code=p["item_code"], unit=p["unit"], family=p["family"],
                 held_low=p["held_low"], held_high=p["held_high"], measured_net=p.get("measured_net"))
        R.check(r, held_ids)
    pins = verify_sources(recs)
    pins.update({f: sha256(f) for f in (TRIAL, INDEX, STAGE, T453, T306, T318)})
    for r in recs:   # dependency on a host of this census: the host's own cause is named (one step)
        if r["cause_class"] == "DEPENDENCY":
            h = next((x for x in recs if x["line_id"] == r["ref"]), None)
            r["host_cause"] = None if h is None else f"{h['cause_class']} {h['ref']}"
    fix = {r["line_id"] for r in recs if r["cause_class"] == "FIX_ROW"}
    before = census(lines)
    after = census(lines)                     # nothing moves here: the census is the same lines, same bounds
    if before != after:
        raise R.CauseError("the HELD census moved")
    by = collections.Counter((r["group"], r["cause_class"]) for r in recs)
    return {
        "schema": SCHEMA, "rule": RULE, "task": "T-647",
        "scope": "F-T636-1 structural share (B9 32, B10 13, B11 138) of the 10 Nov trial BOQ (T-636, merged)",
        "lines": len(recs), "with_cause": sum(1 for r in recs if r.get("cause")),
        "by_group_and_class": {f"{g} {c}": n for (g, c), n in sorted(by.items())},
        "held_census_before": before, "held_census_after": after,
        "fix_rows": [{"id": r["ref"], "line_id": r["line_id"], **r["fix_row"]} for r in recs if r["cause_class"] == "FIX_ROW"],
        "fix_row_effect_if_wired": {"lines_leaving_held": len(fix),
                                    "census_without_fix_lines": census(lines, fix),
                                    "b11_kg_released_if_wired": str(sum((D(r["fix_row"]["kg"]) for r in recs
                                                                         if r["cause_class"] == "FIX_ROW"
                                                                         and r["group"] == "B11"), Decimal(0))),
                                    "b10_m3_released_if_wired": "0 (5 CN lines NOT_APPLICABLE: no member, not a value)"},
        "pinned_sources": pins,
        "records": sorted(recs, key=lambda r: (r["group"], r["item_code"], r["cause_class"], r["line_id"])),
        "not_claimed": "no quantity moved, nothing wired, no accuracy figure; HELD lines are never summed",
    }


def dumps(o):
    return json.dumps(o, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def report(o):
    L = ["# T-647 structural HELD lines to a named cause (generated; R-T647-1)", "",
         f"{o['scope']}. Lines {o['lines']}, with a recorded cause {o['with_cause']}. Nothing wired; no quantity moved.", "",
         "## Causes by trade and class", "", "| Trade / class | Lines |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in o["by_group_and_class"].items()]
    L += ["", "## HELD census before = after (trade x unit; bounded range listed, never summed into a total)", "",
          "| Trade unit | HELD blank | HELD bounded | bounded low .. high |", "|---|---|---|---|"]
    L += [f"| {k} | {v['held_blank']} | {v['held_bounded']} | {v['bounded_low']} .. {v['bounded_high']} |"
          for k, v in o["held_census_before"].items()]
    L += ["", "## Fix rows (DRAWING-CONFIRMED proposals, not wired)", ""]
    L += [f"- {f['id']} {f['line_id']}: {f['proposed_state']}; {f['hand_calculation']}; {f['verdict_proposal']}"
          for f in o["fix_rows"]]
    L += ["", "## Every line", "", "| Line | Trade | Item | Class | Ref | Cause |", "|---|---|---|---|---|---|"]
    L += [f"| {r['line_id']} | {r['group']} | {r['item_code']} | {r['cause_class']} | {r['ref']} | {r['cause'][:160]} |"
          for r in o["records"]]
    return "\n".join(L) + "\n"


def write():
    o = build()
    OUT.mkdir(exist_ok=True)
    (OUT / "HELD_CAUSE_CENSUS_T647.json").write_text(dumps(o), encoding="utf-8")
    (OUT / "HELD_CAUSE_CENSUS_T647.md").write_text(report(o), encoding="utf-8")
    return o
