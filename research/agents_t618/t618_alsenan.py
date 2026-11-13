"""T-618 builder (research, unwired): the five small finishes residuals of the reconciled statement, each to a physical
or arithmetic cause from the drawings, or UNRESOLVED with what evidence would close it (R-T618-1, t618_rules.py).

    python3 -I research/agents_t618/t618_alsenan.py            (write out/T618_RESIDUALS.json)
    python3 -I research/agents_t618/t618_alsenan.py --check    (rebuild, byte-identical)

Inputs (pinned by hash): T618_DRAWN.json (own DXF read, lengths only), the merged T-574 / T-578 / T-602 / T-606 outputs
and his raw rows (numbers only, sheets keyed by a hash of the title; no workbook text). Sign: his - ours throughout
(the statement's sign). Nothing is released; no candidate line, rule / knowledge version or registry file changes.
"""
from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t618_rules as R  # noqa: E402

D = R.D
OUTJ = HERE / "out" / "T618_RESIDUALS.json"
DRAWN = "research/agents_t618/T618_DRAWN.json"
RAW = "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json"
T574 = "research/agents_t574/out/T574_SKIRTING_RECONCILE.json"
T578 = "research/agents_t578/out/T578_RAIL_NOSING_RECONCILE.json"
T602 = "research/agents_t602/out/T602_DOOR_STEPS.json"
T606 = "research/agents_t606/out/T606_OUTLINE_CAUSES.json"
PINS = {DRAWN: None, RAW: "752c9f4e0c4546d0", T574: None, T578: None, T602: None, T606: None}
PIN_FILE = HERE / "PINS.json"
SHEETS = {"ebc195c023cb": "CER", "3a9d8cc3e07d": "MRB"}
STATEMENT = {"1F curved": D("0.73933"), "2F corridor": D("0.70"),   # rooms printed ours - his (T-574): -0.73933 / -0.70
             "door steps": D("0.40"), "rails": D("0.226"),
             "stair skirting": D("0.710951")}
SEA_GATE = "D-GF-15"
STREET_GATE = ("G-01", D("2.5"))          # boundary gap: no door block; its gap is its only drawn width (T-602)
ROOM_ROWS = {"1F curved": (22, "1F curved east bed room + lobby", "1F-CUR.ours"),
             "2F corridor": (29, "2F corridor = lobby + arrival", "2F-CORR.ours")}
STAIRS = {"ST-03 entrance (E1)": ("MRB", 16, 17, 18, 19, "ST-03:E1-LD"),
          "ST-01 main": ("MRB", 23, 24, 25, 26, None),
          "ST-02 round (inner)": ("MRB", 30, 31, 32, 33, "ST-02:RS-LD")}


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def pins():
    want = json.loads(PIN_FILE.read_text())
    bad = {p: _sha(p) for p in PINS if want.get(p) != _sha(p)}
    if bad:
        raise R.RuleError(f"inputs changed since T-618 pinned them: {bad}")
    return {p: want[p] for p in sorted(PINS)}


def _j(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def his_cells():
    cells = {}
    for x in _j(RAW)["rows"]:
        if x["file"] != "FIN":
            continue
        key = SHEETS.get(hashlib.sha256(x["sheet"].encode()).hexdigest()[:12])
        if key:
            for c, v in x["cells"].items():
                if isinstance(v.get("v"), (int, float)):
                    cells[f"{key}.{c}"] = D(repr(round(v["v"], 6)) if isinstance(v["v"], float) else v["v"])
    return cells


def s6(x):
    return None if x is None else str(D(x).quantize(Decimal("0.000001")))


def rng(lo, hi):
    return [s6(lo), s6(hi)]


# ---- rows 1 and 2: room outlines ---------------------------------------------------------------------------------------
def room_row(name, cells, drawn, t606):
    r, label, oid = ROOM_ROWS[name]
    his_p, his_a = cells[f"CER.C{r}"], cells[f"CER.D{r}"]
    room = next(x for x in t606["rooms"] if x["room"] == label)
    ours_p, ours_a = (D(v) for v in room["readings"]["ours"])
    dP, dA = his_p - ours_p, his_a - ours_a
    if dP != STATEMENT[name]:
        raise R.RuleError(f"{name}: his - ours {dP} is not the statement's {STATEMENT[name]}")
    off = drawn["offset"][oid]
    if off["orthogonal"] and D(str(off["k"])) != 4:
        raise R.RuleError(f"{name}: an orthogonal outline must have k = 4, read {off['k']}")
    ot = R.offset_test(ours_p, dP, dA, D(str(off["k"])))
    nr = R.notch_reading(dP, dA)
    tests = [{"reading": "uniform face offset (centreline / plaster face / outer face), any t", "status": ot["status"],
              "evidence": {k: s6(v) if isinstance(v, Decimal) else v for k, v in ot.items() if k != "status"}
              | {"k": str(off["k"]), "arcs": off["arcs"]}}]
    if nr is not None:
        w, d = nr["width"], nr["depth"]
        fits = w <= max(D(str(off["cell_x_m"])), D(str(off["cell_y_m"])))
        hits = [h for h, _, L in off["cell_lines"] if abs(D(str(L)) - w) <= D("0.01") or abs(D(str(L)) - d)
                <= D("0.01")]
        tests.append({"reading": f"one rectangular {nr['kind'].lower()} walked round (dP = 2 d, dA = {nr['sign']} w d)",
                      "status": "NOT_DRAWN" if not hits else "CANDIDATE",
                      "evidence": {"depth": s6(d), "width": s6(w), "fits_cell": fits, "cell_lines_of_that_size": hits,
                                   "cell_lines_read": len(off["cell_lines"])}})
    prior = {"1F curved": "T-606: 4 bases x reveals, none (P, A); T-612: arc read as its chord, refuted by sign",
             "2F corridor": "T-606: maid + roof reveals 0.70 (A 7.705, on his rounding boundary) and lift + roof "
                            "reveals 0.70 (A 7.725): perimeter-only, refused; east-flight foot 13.50 / 7.72: neither"}[name]
    return {"row": name, "unit": "lm", "his": [str(his_p), str(his_a)], "ours": [str(ours_p), str(ours_a)],
            "dP": s6(dP), "dA": s6(dA), "readings_tested": tests, "prior_readings": prior,
            "verdict": R.check_verdict("UNRESOLVED"),
            "cause": "no drawn reading reproduces his row; every uniform offset is refuted "
                     + ("by sign" if ot["status"] == "REFUTED" and "why" in ot else "by the pair (dP, dA)")
                     + ", and the one-notch / one-pocket shape that would fit has no drawn edge in the cell",
            "closes_it": "his room sides (a dimensioned sketch or per-side figures of his row); without them no "
                         "drawing read can attribute it (ERS s.3: a bigger search only finds figure coincidences)"}


# ---- row 3: door steps --------------------------------------------------------------------------------------------------
def door_row(drawn, t602):
    his = [D(x["lm"]) for x in t602["his"]["rows"]]
    rec = t602["reconciliation"]
    ours = {x["opening"]: D(x["lm"]) for x in rec["ours_steps"]}
    if sum(his) - sum(ours.values()) != STATEMENT["door steps"]:
        raise R.RuleError("door steps: his - ours is not the statement's 0.40")
    blocks = {k: D(str(v["leaf_block_width"])) for k, v in drawn["door_blocks"].items()}
    if set(blocks) | {STREET_GATE[0]} != set(ours):
        raise R.RuleError(f"door blocks {sorted(blocks)} + street gate do not cover the census {sorted(ours)}")
    elev = D(str(drawn["elevation"]["D-GF-15 elevation panel"]["length"]))
    readings = {
        "wall gap (ours, T-592 / UP-THR-001)": dict(ours),
        "door-leaf block width": {**blocks, STREET_GATE[0]: STREET_GATE[1]},
        "door-leaf block width, sea gate as drawn on the elevation (27FA)": {**blocks, SEA_GATE: elev,
                                                                             STREET_GATE[0]: STREET_GATE[1]},
    }
    tests = []
    for name, pcs in readings.items():
        st = R.reading_test(his, list(pcs.values()))
        tests.append({"reading": name, "pieces": {k: str(v) for k, v in sorted(pcs.items())},
                      "sum": str(sum(pcs.values())), "status": st})
    cand = [t for t in tests if t["status"] == "CANDIDATE"]
    if len(cand) != 1:
        raise R.RuleError(f"door steps: expected exactly one candidate reading, got {len(cand)}")
    c = readings[cand[0]["reading"]]
    parts = {k: s6(c[k] - ours[k]) for k in sorted(ours) if c[k] != ours[k]}
    ms = R.multiset_compare(his, list(ours.values()))
    return {"row": "door steps", "unit": "lm", "his_pieces": [str(x) for x in his], "his": str(sum(his)),
            "ours": str(sum(ours.values())), "residual": s6(sum(his) - sum(ours.values())),
            "multiset_vs_ours": {k: [str(x) for x in v] if isinstance(v, list) else v for k, v in ms.items()},
            "readings_tested": tests, "candidate_parts": parts,
            "verdict": R.check_verdict("UNRESOLVED"),
            "candidate_cause": "RULE_DIFFERENCE (proposal): one uniform reading reproduces all six of his pieces: the "
                               "door-leaf block width at every house door (D-GF-09 block 1.000 drawn over its 0.900 "
                               "wall gap: +0.10) and the sea gate at its elevation panel 1.30 against the 1.000 plan "
                               "gap (+0.30); ours pays the wall gap (T-592, UP-THR-001), which is the stone's "
                               "physical length; the street gate 2.50 agrees",
            "why_not_established": "his rows carry no opening id (R-T602-1 (d)); a multiset equality is a CANDIDATE, "
                                   "never an assignment",
            "closes_it": "an opening id on his six rows, or the owner confirming which length a door step is paid on "
                         "(the wall gap is already the T-592 basis)"}


# ---- row 4: rails -------------------------------------------------------------------------------------------------------
def rail_row(t578):
    rl = t578["rails_lm"]
    his = D(rl["his"]["value"])
    runs = {r["run"]: r for r in rl["runs"]}
    valued = D(runs["RAIL:RL-05"]["value"]) + D(runs["RAIL:RL-06"]["value"])
    if his - valued != STATEMENT["rails"] or D(rl["like_for_like_hypothesis_A"]["his_minus_ours"]) != STATEMENT["rails"]:
        raise R.RuleError("rails: hypothesis A residual is not the statement's 0.226")
    in_scope = {k: v for k, v in runs.items() if v["status"] == "HELD" and "ST-02" in (v.get("why") or "")}
    if sorted(in_scope) != ["RAIL:RL-09"]:
        raise R.RuleError(f"rails: ST-02 HELD runs inside hypothesis A are {sorted(in_scope)}, expected RL-09")
    held = [(D(v["bound"][0]), None if v["bound"][1] is None else D(v["bound"][1])) for v in in_scope.values()]
    lo, hi = R.range_residual(his, valued, held)
    refused = True
    try:
        R.refuse_point_residual(STATEMENT["rails"], lo, hi)
        refused = False
    except R.RuleError:
        pass
    return {"row": "rails", "unit": "lm", "his": str(his), "hypothesis": "A (his = ST-02 system + D-23, T-393 / T-578)",
            "valued_in_scope": {"RAIL:RL-05": runs["RAIL:RL-05"]["value"], "RAIL:RL-06": runs["RAIL:RL-06"]["value"]},
            "held_in_scope": {k: v["bound"] for k, v in in_scope.items()}, "range_his_minus_ours": rng(lo, hi),
            "point_0.226_refused_as_quantity": refused, "verdict": R.check_verdict("UNRESOLVED"),
            "cause": "ARITHMETIC: hypothesis A's own scope holds RL-09, the RS-C outer band of the same round stair, "
                     "HELD 0 .. unbounded (guard or string not established, band ends differ between the plans); the "
                     "0.226 is the upper end of the range his - ours, not a residual quantity (R-T618-1 (a))",
            "closes_it": "RL-09's role (designer RFI, T-398 / RFI-S27) and a breakdown of his typed 18.95 (none exists: "
                         "F-T578-1); until both, hypothesis A itself stays a hypothesis"}


# ---- row 5: stair skirting ----------------------------------------------------------------------------------------------
def stair_row(cells, drawn, t574):
    groups = {g["id"]: g for g in t574["stairs"]["groups"]}
    out, ranges, point = [], [], D(0)
    for st, (sh, r_steps, r_land, r_lm, r_nr, lid) in STAIRS.items():
        g = groups[st]
        his, ours = D(g["his"]), D(g["ours"])
        if cells[f"{sh}.C{r_lm}"] != his:
            raise R.RuleError(f"{st}: his lm row differs from T-574")
        held = [(D(c["bound"][0]), None if c["bound"][1] is None else D(c["bound"][1])) for c in g["causes"]
                if c["verdict"] == "HELD"]
        lo, hi = R.range_residual(his, ours, held)
        point += his - ours - sum((h[0] for h in held), D(0))
        ranges.append((lo, hi))
        steps, pieces = cells[f"{sh}.B{r_steps}"], cells[f"{sh}.B{r_nr}"]
        land_m2 = cells[f"{sh}.D{r_land}"]
        e = {"stair": st, "his_lm": str(his), "ours_valued_level": str(ours),
             "held_bounds": [rng(a, b) for a, b in held], "range_his_minus_ours": rng(lo, hi),
             "point_from_lower_bounds": s6(his - ours - sum((h[0] for h in held), D(0))),
             "notation": {"his_steps": str(steps), "his_per_step_pieces": str(pieces),
                          "per_step_row_is_flight_side": R.per_step_row_is_flight(pieces, steps),
                          "his_landing_m2": str(land_m2)}}
        if lid:
            L = drawn["landings"][lid]
            walled, opn = R.landing_bound(L["sides"])
            area = D(str(L["x_m"])) * D(str(L["y_m"]))
            e["drawn_landing"] = {"x": str(L["x_m"]), "y": str(L["y_m"]), "area": s6(area),
                                  "walled_by_side": {k: str(v["walled"]) for k, v in sorted(L["sides"].items())},
                                  "walled_total": s6(walled), "open_total": s6(opn),
                                  "his_landing_area_reproduced": R.within(area, land_m2)}
            e["level_only"] = {"his_minus_ours": s6(his - ours),
                               "his_above_walled_bound": s6(R.excess_on_open_faces(his, walled))}
        out.append(e)
    lo, hi = R.add_ranges(ranges)
    if point != STATEMENT["stair skirting"] or hi != STATEMENT["stair skirting"]:
        raise R.RuleError(f"stair skirting: lower-bound point {point} / upper end {hi} is not the statement's 0.710951")
    refused = True
    try:
        R.refuse_point_residual(STATEMENT["stair skirting"], lo, hi)
        refused = False
    except R.RuleError:
        pass
    e1 = next(x for x in out if x["stair"].startswith("ST-03"))
    rs = next(x for x in out if x["stair"].startswith("ST-02"))
    if D(rs["drawn_landing"]["walled_total"]) != D(rs["ours_valued_level"]):
        raise R.RuleError("ST-02: our RS-LD level skirting is not the drawn walled length")
    return {"row": "stair skirting", "unit": "lm", "his": "29.87", "per_stair": out,
            "range_his_minus_ours": rng(lo, hi), "point_0.710951_refused_as_quantity": refused,
            "net_of": {x["stair"]: x["point_from_lower_bounds"] for x in out},
            "verdict": R.check_verdict("UNRESOLVED"),
            "cause": "ARITHMETIC + NOTATION: the 0.710951 is the upper end of a range (ORR-007: the flight form range is "
                     "never summed as a point) and a net of three stairs (+2.899456 E1, -0.038505 ST-01, -2.150 ST-02); "
                     "his lm row sits beside a per-step piece row whose count equals his step count on all three "
                     "stairs, so his flights are the pieces (nr) and his lm row is level skirting: subtracting our "
                     "flight bound from it is a cross-element comparison",
            "findings": {
                "ST-02": f"drawn corner landing {rs['drawn_landing']['x']} x {rs['drawn_landing']['y']} has ONE walled "
                         f"side (S 1.20 + column face 0.05 = {rs['drawn_landing']['walled_total']} = our RS-LD "
                         f"{rs['ours_valued_level']}: ENGINE_RIGHT as drawn); his 2.40 lies "
                         f"{rs['level_only']['his_above_walled_bound']} above the walled bound, on risers / the open "
                         f"edge (no wall base): ENGINE_RIGHT on that excess IF his row is landing skirting (CANDIDATE: "
                         f"his landing 1.44 m2 is not the drawn {rs['drawn_landing']['area']})",
                "ST-03 E1": f"the +1.00 porch landing {e1['drawn_landing']['x']} x {e1['drawn_landing']['y']} has "
                            f"{e1['drawn_landing']['walled_total']} lm of walled faces (N 1.40, E 1.70 net of the main "
                            f"door, S 0.40 net of the pantry door) and NO candidate skirting line: ENGINE_OMISSION "
                            f"CANDIDATE, scope HELD (exterior porch base not printed; same question as his yard row); "
                            f"his 4.37 is {e1['level_only']['his_above_walled_bound']} above it and his landing 5.1 m2 "
                            f"is not the drawn {e1['drawn_landing']['area']}: no reading established",
                "ST-01": "his 23.10 unsplit; below our valued + smallest flight form by 0.038505 (0.17 %); no landing "
                         "read this run (main stair: 4 flights, 2 winder turns HELD)"},
            "closes_it": "the flight form (ORR-007 / S-9 winders) closes the ranges; his per-stair breakdown would "
                         "settle the level / flight split; the owner's porch-skirting scope settles E1 (3.50 lm)"}


def build():
    p = pins()
    cells, drawn = his_cells(), _j(DRAWN)
    rows = [room_row("1F curved", cells, drawn, _j(T606)), room_row("2F corridor", cells, drawn, _j(T606)),
            door_row(drawn, _j(T602)), rail_row(_j(T578)), stair_row(cells, drawn, _j(T574))]
    return {"schema": "T618_RESIDUALS_V1", "rule": R.RULE_ID, "sign": "his - ours", "pins": p,
            "released": "nothing (research; no candidate line, rule / knowledge version or registry file changed)",
            "statement_rows": {k: str(v) for k, v in STATEMENT.items()}, "rows": rows,
            "engine_wrong": [], "fix_rows": [
                "FR-T618-1 (lane I, statement V-next, no quantity): restate 'stair skirting UNRESOLVED 0.710951' as the "
                "range (-inf, 0.710951] by stair, and 'rails UNRESOLVED 0.226' as (-inf, 0.226] under hypothesis A "
                "with RL-09 named; a HELD range's lower bound is never subtracted into a point residual",
                "FR-T618-2 (Lead, scope): E1 +1.00 porch landing skirting 3.50 lm walled faces, no candidate line: "
                "ENGINE_OMISSION candidate, HELD on the porch / outdoor skirting scope (never 0)"]}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--pin" in argv:
        PIN_FILE.write_text(json.dumps({p: _sha(p) for p in sorted(PINS)}, indent=1) + "\n")
        print("pinned")
        return 0
    txt = json.dumps(build(), indent=1, ensure_ascii=False) + "\n"
    if "--check" in argv:
        same = OUTJ.exists() and OUTJ.read_text(encoding="utf-8") == txt
        print("T618 check:", "byte-identical" if same else "DIFFERS")
        return 0 if same else 1
    OUTJ.parent.mkdir(exist_ok=True)
    OUTJ.write_text(txt, encoding="utf-8")
    print("written", OUTJ.relative_to(ROOT))
    return 0


# T-653: this builder's functions run in the same local 40-digit context as its rules (before T-653 they ran
# at 40 only because importing the rules changed the process-global context).
R.in_prec40(globals())


if __name__ == "__main__":
    raise SystemExit(main())
