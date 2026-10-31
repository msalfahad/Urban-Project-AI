"""T-374 STRAIGHT_BAR_SCHEDULE_V1: a bar bending schedule of shape code 00 (straight bars) only, for the bar populations
the T-371 shape census found SCHEDULABLE_NOW, bound line by line to the candidate of record (every villa; stdlib only).

A schedule row is ONE physical straight bar shape: mark, diameter d, number n, cut length, shape 00, net (installed) kg,
and the procurement view kept in separate columns (stock bars, offcuts, procurement kg). Rules (ERS s.2 - s.4,
OWNER_RULE_REBAR_2026-10-24, owner option B 2026-10-29):

  R-T374-1  shape 00 only for a population whose shape census status is SCHEDULABLE_NOW; any bent attribute (leg, hook,
            bend, crank, link, boxed, spiral) in the line's own basis refuses the row (never a bent bar shown straight).
  R-T374-2  cut length = the line's drawn straight length less the printed covers only (as the candidate measured it);
            a lap / development / starter length is never part of the cut length unless its authority is PRINTED for
            that population (T-366 matrix); otherwise the lap column carries 'HELD' by name and the bar is shown without
            it (a note-9 lap borrowed for a non-starter is refused).
  R-T374-3  net kg = n x cut length x d^2 / 162 (the candidate's own unit mass, engine/source/rebar_unit_mass
            D2_OVER_162); it must equal the candidate line kg to the candidate's storage precision, else the build stops.
  R-T374-4  procurement is a separate view: stock length S (12 m, ASSUMED - OWNER-APPROVED OD-V3-3), whole cut bars per
            stock bar, offcuts listed; no reuse of offcuts across marks is modelled (no owner rule). A bar longer than S
            needs a splice: its piece count is stated with the lap range it holds for, the cut lengths stay HELD while
            the lap is HELD.
  R-T374-5  a line that is one SEGMENT of a bar run carried through interior columns (the 'through column' ledger lines)
            is scheduled on the RUN (the physical bar), never as a separate bar; the run's net equals the sum of its
            lines.
  HELD / BLOCKED / NA lines get no schedule kg (never 0); a bounded line is scheduled only where the bound is a count
  range on one fixed straight geometry (footing Q-71 readings), otherwise it is carried by name.
  R-T374-6  (r2, Verifier 2026-10-30 21:08) a line under ANY unresolved Checker downgrade record (every
            verdicts/V3.0.x/DOWNGRADES.json, snapshot T374_BOUND_DOWNGRADES.json) is never SCHEDULED: it is booked
            HELD_DOWNGRADE (state of the record, HELD / CONFLICT) by the record id, cut length, count, procurement BLANK;
            the candidate value is carried only in the audit columns labelled with the record's basis label
            (UNSUPPORTED BASIS). The record of the latest verdict set names the line; earlier re-issues are listed.
  R-T374-6b a line NOT in a record's line list whose own content carries the record's stated basis (footing mesh,
            FOOTING_REBAR_POPULATION_V1, run = side - 2 x printed MINIMUM cover, DG-a97ec2ea66e02194) gets the same
            treatment, booked HELD_SAME_BASIS with the record id named as the basis and the extension proposed to the
            Checker (the record itself is never edited here). Every line of that record must carry the basis too, or the
            build stops (the signature is checked against the record, not assumed).

All lengths are handled in integer 0.1 mm units, so boundary cases read from decimal text are exact.

    python -I research/agents_t374/t374_straight_bbs.py --csv <out.csv> --json <out.json> [--runs <out_runs.csv>]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import re
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

POLICY = "STRAIGHT_BAR_SCHEDULE_V1"
SHAPE_00 = "00"
U = 10000                      # length units per metre (0.1 mm)
STOCK_M = Decimal("12")
STOCK_STATUS = "ASSUMED - OWNER-APPROVED (OD-V3-3; 12 m stock printed nowhere in the set, T-366)"

ROOT = Path(__file__).resolve().parents[2]
EXTRACT = ROOT / "research/agents_t297/CANDIDATE_V3016_REBAR_LINES.json"
EXTRACT_SHA = "2f28367b81fe362d98d8a97080adb62cfd9a3c0a880fc20d201735e6eba39760"
T371_BINDING = ROOT / "research/agents_t371/LINE_BINDING_T371.json"
T371_MATRIX = ROOT / "research/agents_t371/T371_MATRIX.csv"
T366_MATRIX = ROOT / "research/agents_t366/T366_MATRIX.csv"
T318_INPUTS = ROOT / "research/agents_t318/t318_inputs.py"
DOWNGRADE_SNAPSHOT = Path(__file__).resolve().parent / "T374_BOUND_DOWNGRADES.json"
BOARD_VERDICTS = ROOT.parent / "board/docs/agents/verdicts"      # the agents/control worktree beside this tree
CANDIDATE_OF_RECORD = "ARCH_TAKEOFF_V3.0.29"
FTG_MESH_BASIS_RECORD = "DG-a97ec2ea66e02194"
HELD_ROW_STATES = ("HELD_DOWNGRADE", "HELD_SAME_BASIS")
# candidate text that an owner answer has overtaken: the candidate quote is kept, the schedule appends the status (F-T374-2)
STALE_TEXT = {
    "Q-74 open": "[T-374 note F-T374-2: Q-74 is ANSWERED A (owner 2026-10-22) for the strap CONCRETE length only: "
                 "'bars, formwork and excavation derived separately'; it sets no strap bar length, so these bars stay "
                 "unscheduled on their own bar-end / section basis, not on Q-74]",
}

# T-371 population -> (bar-mark prefix, T-366 lap population id)
POPULATIONS = {
    "FTG-BOT-MESH": ("FB", "FTG-BOTTOM"),
    "COL-MAIN-BODY": ("CM", "COL-MAIN"),
    "COL-TWIST-EXTRA": ("CT", "COL-TWIST-EXTRA"),
    "CB-BOTTOM": ("CBB", "CB-BOTTOM"),
    "CB-SUPPORT-TOP": ("CBS", "CB-SUPPORT-TOP"),
    "GB-MAIN": ("GB", "GB-MAIN"),
    "SLAB-TEMP": ("ST", "SLAB-TEMPERATURE"),
}

BENT_WORDS = re.compile(r"\b(hook|hooks|hooked|leg|legs|bend|bends|bent|crank|cranked|link|links|stirrup|stirrups|"
                        r"boxed|spiral|u-bar|l-bar|up-turn|hook-down)\b", re.I)
LAP_WORDS = re.compile(r"(\blap\b|\blaps\b|LAP_|DEVELOPMENT|ANCHORAGE|BAR_ENDS|NOTE_9|note 9|note-9|STARTER)", re.I)
THROUGH = re.compile(r"^HL:GROUND_SYSTEM_STEEL:through column (\S+) \(([^)]+)\):(TOP|BOTTOM)$")
SEGMENT = re.compile(r"^HL:GROUND_SYSTEM_STEEL:GSO-(.+)-(\d+):(TOP|BOTTOM)$")


class ScheduleRefused(ValueError):
    """a row the schedule must not contain (bent shape as 00, borrowed lap, non-NOW population, bad arithmetic)."""


# ---------------------------------------------------------------- units and arithmetic

def to_u(metres) -> int:
    """metres (float / str / Decimal) -> integer 0.1 mm, exact for decimal text."""
    q = Decimal(str(metres)) * U
    if q != q.to_integral_value():
        raise ScheduleRefused(f"length {metres} m is finer than 0.1 mm")
    return int(q)


def kg_per_m(d_mm: int) -> Decimal:
    return Decimal(d_mm * d_mm) / Decimal(162)


def net_kg(n: int, length_u: int, d_mm: int) -> Decimal:
    return Decimal(n) * Decimal(length_u) / U * kg_per_m(d_mm)


def splices_needed(run_u: int, stock_u: int, lap_u: int) -> int:
    """pieces - 1 for a straight run cut from stock of stock_u with laps of lap_u (owner proposal s.2 formula)."""
    if run_u <= stock_u:
        return 0
    if lap_u >= stock_u:
        raise ScheduleRefused("lap not shorter than the stock bar")
    return -(-(run_u - stock_u) // (stock_u - lap_u))


def splice_band(run_u: int, stock_u: int) -> dict:
    """the minimum splice count of a run and the largest lap for which it holds (lap value itself HELD)."""
    if run_u <= stock_u:
        return {"splices": 0, "valid_for_lap_up_to_m": None}
    k = -(-(run_u - stock_u) // stock_u)          # lap 0
    while True:
        lap_max = Decimal((k + 1) * stock_u - run_u) / Decimal(k) / U
        if lap_max > 0:
            return {"splices": k, "valid_for_lap_up_to_m": lap_max.quantize(Decimal("0.0001"))}
        k += 1


def cut_from_stock(n: int, length_u: int, stock_u: int) -> dict:
    """whole cut bars from stock, no offcut reuse across marks: per stock bar, stock bars, offcut list."""
    if length_u <= 0 or n <= 0:
        raise ScheduleRefused("cut length and count must be positive")
    if length_u > stock_u:
        raise ScheduleRefused("bar longer than the stock length: a splice is needed (lap HELD)")
    per = stock_u // length_u
    full, rem = divmod(n, per)
    offcuts = []
    if full:
        offcuts.append((full, stock_u - per * length_u))
    if rem:
        offcuts.append((1, stock_u - rem * length_u))
    return {"bars_per_stock": per, "stock_bars": full + (1 if rem else 0),
            "offcuts": [(c, u) for c, u in offcuts if u > 0]}


def nest_ffd(pieces, stock_u: int) -> dict:
    """cutting plan for one diameter: first-fit-decreasing of every cut piece into stock bars (offcut reuse ACROSS marks;
    a procurement optimisation, not a rule). Also the lower bound ceil(sum / stock)."""
    bins = []
    for L in sorted(pieces, reverse=True):
        if L > stock_u:
            raise ScheduleRefused("piece longer than the stock bar")
        for i, free in enumerate(bins):
            if free >= L:
                bins[i] = free - L
                break
        else:
            bins.append(stock_u - L)
    total = sum(pieces)
    return {"stock_bars": len(bins), "lower_bound_bars": -(-total // stock_u) if total else 0,
            "offcut_m": fmt_m(sum(bins)), "offcuts_over_1m": sum(1 for b in bins if b >= U)}


def fmt_m(u: int) -> str:
    return format(Decimal(u) / U, "f")


def fmt_kg(x) -> str:
    return "" if x is None else format(Decimal(x).quantize(Decimal("0.000001")), "f")


# ---------------------------------------------------------------- authorities read from merged files

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def shape_status(matrix_csv=T371_MATRIX) -> dict:
    return {r["pop_id"]: r["status"] for r in csv.DictReader(open(matrix_csv, encoding="utf-8"))}


def lap_status(matrix_csv=T366_MATRIX) -> dict:
    out = {}
    for r in csv.DictReader(open(matrix_csv, encoding="utf-8")):
        out.setdefault(r["id"], {"lap_status": r["lap_status"], "splice_need": r["splice_need"],
                                 "authority": r["authority"], "sources": r["sources"]})
    return out


def lap_column(pop: str, laps: dict) -> str:
    st = laps[POPULATIONS[pop][1]]
    if st["lap_status"] == "NOT_REQUIRED":
        return "NOT_REQUIRED (T-366: bar within one stock length)"
    if st["lap_status"] == "PRINTED":
        return f"PRINTED {st['sources']} (T-366); not in the cut length"
    return f"HELD by name (T-366 {POPULATIONS[pop][1]} {st['lap_status']}; never borrowed, shown without it)"


def check_lap(pop: str, lap, laps: dict):
    """a lap may enter a cut length only with an authority T-366 lists as PRINTED for that population."""
    if lap is None:
        return
    st = laps[POPULATIONS[pop][1]]
    if st["lap_status"] != "PRINTED" or lap.get("authority") not in st["sources"].split(";"):
        raise ScheduleRefused(f"lap {lap.get('value_m')} m from {lap.get('authority')} refused for {pop}: "
                              f"T-366 {POPULATIONS[pop][1]} is {st['lap_status']}")


# ---------------------------------------------------------------- one line -> one row

def diameter(line) -> int | None:
    m = re.search(r"/\s*(\d+)\s*mm", line.get("subtrade") or "")
    d = int(m.group(1)) if m else None
    k = (line.get("inputs") or {}).get("kg_per_m")
    if d is not None and k is not None and abs(Decimal(str(k)) - kg_per_m(d)) > Decimal("0.0000005"):
        raise ScheduleRefused(f"{line['line_id']}: kg/m {k} is not d^2/162 for d = {d}")
    return d


def bent_basis(line) -> str | None:
    inp = line.get("inputs") or {}
    text = " ".join(str(v) for v in (line.get("formula"), inp.get("component"), inp.get("printed"),
                                     " ".join(inp.get("reasons") or []), line.get("element_id")) if v)
    m = BENT_WORDS.search(text)
    return m.group(0) if m else None


def schedule_line(line, pop, shapes, laps, lap=None) -> dict:
    """the schedule row of one candidate line (no bar mark yet)."""
    if shapes.get(pop) != "SCHEDULABLE_NOW":
        raise ScheduleRefused(f"{pop} is {shapes.get(pop)} in the T-371 census: no shape-00 row")
    check_lap(pop, lap, laps)
    inp = line.get("inputs") or {}
    st = line["evidence_state"]
    row = {"line_id": line["line_id"], "population": pop, "element_id": line["element_id"], "floor": line["floor"],
           "element_mark": inp.get("mark") or "", "component": inp.get("component") or "", "evidence_state": st,
           "shape_code": "", "d_mm": "", "n": "", "cut_length_m": "", "kg_per_m": "", "net_kg_low": None,
           "net_kg_high": None, "candidate_kg_low": None, "candidate_kg_high": None, "diff_kg": None,
           "lap": lap_column(pop, laps), "reason": ""}
    comp_text = " ".join(str(x) for x in (inp.get("component"), line["element_id"]) if x)
    if LAP_WORDS.search(comp_text):
        raise ScheduleRefused(f"{line['line_id']}: a lap / development / starter line is not a shape-00 body bar")
    if st == "NOT_APPLICABLE_WITH_EVIDENCE":
        row.update(row_status="NA_SUPERSEDED", reason="route G provisional line superseded by a hand ledger "
                   "(candidate NA with evidence): no bar")
        return row
    bent = bent_basis(line)
    if st == "BLOCKED_RFI":
        n, length = inp.get("count"), inp.get("length_m")
        why = "; ".join(inp.get("reasons") or []) or line.get("rfi") or line.get("formula") or ""
        if bent:
            why = f"SHAPE_NOT_00 ('{bent}' in the line's basis); " + why
        if inp.get("ledger_state") == "HELD_DEFINED" and n and length and not bent:
            d = diameter(line)
            row.update(row_status="HELD_DEFINED", reason="HELD (no schedule kg): " + why,
                       held_geometry=f"{int(n)} x {d} mm x {length} m (ledger HELD_DEFINED "
                                     f"{inp.get('held_defined_kg')} kg, not scheduled)")
        else:
            row.update(row_status="HELD", reason="HELD (no schedule kg): " + why)
        return row
    if bent:
        raise ScheduleRefused(f"{line['line_id']}: '{bent}' in the basis of a {st} line: not shape 00")
    d = diameter(line)
    if d is None:
        if st == "BOUNDED_EXPOSURE":
            br = line["bounded_range"]
            row.update(row_status="BOUNDED_NO_ROW", candidate_kg_low=Decimal(str(br["low"])),
                       candidate_kg_high=Decimal(str(br["high"])),
                       reason="BOUNDED, no bar defined (diameter / count not fixed): " + (line.get("rfi") or ""))
            return row
        raise ScheduleRefused(f"{line['line_id']}: no diameter")
    length = inp.get("length_m", inp.get("bar_length_m"))
    if st == "SOURCE_DERIVED":
        n = inp.get("count")
        if n is None or Decimal(str(n)) != Decimal(str(n)).to_integral_value():
            raise ScheduleRefused(f"{line['line_id']}: count {n} is not a whole number of bars")
        n, lu = int(Decimal(str(n))), to_u(length)
        net = net_kg(n, lu, d)
        cand = Decimal(str(line["measured_net"]))
        cause = _difference_cause(line, net, cand, n, d)
        row.update(diff_cause=cause, row_status="SCHEDULED", shape_code=SHAPE_00, d_mm=d, n=str(n), cut_length_m=fmt_m(lu),
                   kg_per_m=format(kg_per_m(d).quantize(Decimal("0.000001")), "f"), net_kg_low=net, net_kg_high=net,
                   candidate_kg_low=cand, candidate_kg_high=cand, diff_kg=net - cand, _n=(n, n), _lu=lu)
        return row
    if st == "BOUNDED_EXPOSURE":
        br = line["bounded_range"]
        cr = inp.get("count_range")
        lo_c, hi_c = Decimal(str(br["low"])), Decimal(str(br["high"]))
        if cr and length is not None:
            n_lo, n_hi, lu = int(cr[0]), int(cr[1]), to_u(length)
            lo, hi = net_kg(n_lo, lu, d), net_kg(n_hi, lu, d)
            causes = {_difference_cause(line, lo, lo_c, n_lo, d), _difference_cause(line, hi, hi_c, n_hi, d)}
            row.update(diff_cause="+".join(sorted(causes)), row_status="SCHEDULED_BOUNDED", shape_code=SHAPE_00, d_mm=d, n=f"{n_lo}..{n_hi}",
                       cut_length_m=fmt_m(lu), kg_per_m=format(kg_per_m(d).quantize(Decimal("0.000001")), "f"),
                       net_kg_low=lo, net_kg_high=hi, candidate_kg_low=lo_c, candidate_kg_high=hi_c,
                       diff_kg=(lo - lo_c) + (hi - hi_c), _n=(n_lo, n_hi), _lu=lu,
                       reason="count HELD between readings: " + (br.get("basis") or ""))
            return row
        row.update(row_status="BOUNDED_NO_ROW", candidate_kg_low=lo_c, candidate_kg_high=hi_c,
                   reason="BOUNDED on the bar geometry itself (no single cut length): " + (line.get("rfi") or ""))
        return row
    raise ScheduleRefused(f"{line['line_id']}: unknown evidence state {st}")


def _difference_cause(line, net, cand, n, d) -> str:
    """name the schedule - candidate difference of one line, or stop. The candidate stores the footing population kg
    to 6 dp and the hand ledgers (T-148 / T-149 / T-138) kg to 3 dp, computed from the UNROUNDED length while the
    ledger prints the length to 0.1 mm: the difference may be the kg rounding (half a unit of the last place) plus the
    length rounding (n x 0.05 mm x kg/m). Anything larger is not a storage effect and stops the build."""
    diff = abs(net - cand)
    pol = (line.get("inputs") or {}).get("policy") or ""
    kg_half = Decimal("0.0000005") if pol.startswith("FOOTING_REBAR_POPULATION") else Decimal("0.0005")
    if diff == 0:
        return "NONE"
    if diff <= kg_half:
        return "KG_STORAGE_ROUNDING"
    if diff <= kg_half + Decimal(n) * Decimal("0.00005") * kg_per_m(d):
        return "LENGTH_STORAGE_0.1MM+KG_ROUNDING"
    raise ScheduleRefused(f"{line['line_id']}: schedule {net} kg vs candidate {cand} kg: difference {diff} kg is not "
                          "a storage effect")


# ---------------------------------------------------------------- runs through interior columns (R-T374-5)

def find_runs(rows) -> dict:
    """band -> position -> member rows, for every band that has a 'through column' ledger line."""
    bands = set()
    for r in rows:
        m = THROUGH.match(r["element_id"])
        if m:
            bands.add(m.group(2))
    runs = defaultdict(lambda: defaultdict(list))
    for r in rows:
        m = THROUGH.match(r["element_id"])
        if m:
            runs[m.group(2)][m.group(3)].append(r)
            continue
        m = SEGMENT.match(r["element_id"])
        if m and m.group(1) in bands:
            runs[m.group(1)][m.group(3)].append(r)
    return runs


def assemble_run(band, pos, members, stock_u) -> dict:
    states = {r["row_status"] for r in members}
    if states != {"SCHEDULED"}:
        raise ScheduleRefused(f"run {band} {pos}: member states {sorted(states)}: run not schedulable whole")
    ns = {r["_n"] for r in members}
    ds = {r["d_mm"] for r in members}
    if len(ns) != 1 or len(ds) != 1:
        raise ScheduleRefused(f"run {band} {pos}: counts {ns} / diameters {ds} change along the run")
    n = next(iter(ns))[0]
    d = next(iter(ds))
    run_u = sum(r["_lu"] for r in members)
    net = sum((r["net_kg_low"] for r in members), Decimal(0))
    out = {"run_id": f"RUN-{band}-{pos}", "band": band, "position": pos, "d_mm": d, "n": n, "run_length_m": fmt_m(run_u),
           "member_lines": len(members), "net_kg": net, "_run_u": run_u}
    if run_u <= stock_u:
        c = cut_from_stock(n, run_u, stock_u)
        c = dict(c, offcuts=" + ".join(f"{k} x {fmt_m(u)} m" for k, u in c["offcuts"]))
        out.update(cut_length_m=fmt_m(run_u), splices_per_bar=0, procurement=c,
                   procurement_kg=Decimal(c["stock_bars"]) * STOCK_M * kg_per_m(d), note="one straight bar per run")
    else:
        sb = splice_band(run_u, stock_u)
        out.update(cut_length_m="HELD (splice position and lap length not printed)", splices_per_bar=sb["splices"],
                   splice_valid_for_lap_up_to_m=str(sb["valid_for_lap_up_to_m"]), procurement=None,
                   procurement_kg=None,
                   note=f"run {fmt_m(run_u)} m > stock {STOCK_M} m: {sb['splices']} splice(s) per bar for any lap up to "
                        f"{sb['valid_for_lap_up_to_m']} m; lap HELD (T-366 GB-MAIN): cut lengths and procurement HELD")
    return out


# ---------------------------------------------------------------- Checker downgrade records (R-T374-6)

def _ids(v):
    import ast
    return list(ast.literal_eval(v)) if isinstance(v, str) else list(v)


def snapshot_downgrades(verdicts_dir=BOARD_VERDICTS) -> dict:
    """read EVERY verdicts/V3.0.x/DOWNGRADES.json (board branch agents/control): per record its id, state, resolved,
    basis label, unit, the verdict sets carrying it, its line ids; plus each source file's sha256. Record ids only, no
    drawing content. A record id carried with different line ids or resolution in two sets stops the build."""
    verdicts_dir = Path(verdicts_dir)
    files = sorted(verdicts_dir.glob("V3.0.*/DOWNGRADES.json"),
                   key=lambda f: tuple(int(x) for x in f.parent.name[1:].split(".")))
    if not files:
        raise ScheduleRefused(f"no DOWNGRADES.json under {verdicts_dir}")
    recs, srcs = {}, {}
    for f in files:
        srcs[f.parent.name] = sha256(f)
        for r in json.load(open(f, encoding="utf-8"))["downgrades"]:
            k = r["downgrade_id"]
            ids = sorted(_ids(r["line_ids"]))
            cur = recs.setdefault(k, {"downgrade_id": k, "state": r["state"], "resolved": r["resolved"],
                                      "basis_label": r.get("basis_label"), "unit": r.get("unit"),
                                      "candidate_version": r.get("candidate_version"),
                                      "line_content_sha256": r.get("line_content_sha256"),
                                      "engine_qty": r.get("engine_qty"), "verdict_sets": [], "line_ids": ids})
            if cur["line_ids"] != ids or cur["resolved"] != r["resolved"] or cur["state"] != r["state"]:
                raise ScheduleRefused(f"{k}: carried with different content in {f.parent.name}")
            cur["verdict_sets"].append(f.parent.name)
    return {"schema": "T374_BOUND_DOWNGRADES_V1", "candidate_of_record": CANDIDATE_OF_RECORD,
            "source": "docs/agents/verdicts/V3.0.x/DOWNGRADES.json on branch agents/control",
            "source_sha256": srcs, "records": [recs[k] for k in sorted(recs)]}


def downgrades_by_line(snapshot) -> dict:
    """line id -> the unresolved records holding it, the one carried by the LATEST verdict set first (it names the
    line; earlier sets carrying the same line ids are its re-issues)."""
    order = lambda r: max(tuple(int(x) for x in v[1:].split(".")) for v in r["verdict_sets"])
    out = defaultdict(list)
    for r in sorted(snapshot["records"], key=order, reverse=True):
        if r["resolved"]:
            continue
        for lid in r["line_ids"]:
            out[lid].append(r)
    return dict(out)


def ftg_mesh_basis(line) -> bool:
    """R-T374-6b signature of DG-a97ec2ea66e02194's stated basis, read from the line's own content: a footing bottom
    mesh bar whose run is the side less 2 x the printed MINIMUM cover (the cover used as the bar-end position)."""
    inp = line.get("inputs") or {}
    return (inp.get("policy") == "FOOTING_REBAR_POPULATION_V1"
            and inp.get("component") in ("BOTTOM_LONG", "BOTTOM_SHORT")
            and str(inp.get("cover") or "").startswith("MINIMUM 70 mm")
            and re.search(r"side \d+ - 2 x 70 mm", line.get("formula") or "") is not None)


def apply_downgrades(row, line, by_line, basis_ids=frozenset()) -> dict:
    """R-T374-6 / -6b on one row already valued by schedule_line: a scheduled (or bounded-scheduled) row under an
    unresolved record, or carrying its basis, loses every schedule and procurement value; the candidate figure moves
    to the audit columns labelled UNSUPPORTED BASIS. Rows that are not scheduled keep their own status."""
    recs = by_line.get(line["line_id"], [])
    same = (not recs and ftg_mesh_basis(line) and FTG_MESH_BASIS_RECORD in basis_ids)
    if not recs and not same:
        return row
    if row["row_status"] not in ("SCHEDULED", "SCHEDULED_BOUNDED"):
        if recs:
            row["downgrade_id"] = recs[0]["downgrade_id"]
        return row
    inp = line.get("inputs") or {}
    printed = f"count {row['n']} x d {row['d_mm']} mm as printed; run {row['cut_length_m']} m = UNSUPPORTED BASIS"
    lo, hi = row["candidate_kg_low"], row["candidate_kg_high"]
    if recs:
        r0 = recs[0]
        rid, label = r0["downgrade_id"], r0.get("basis_label") or "UNSUPPORTED BASIS"
        status = "HELD_DOWNGRADE"
        reis = [r["downgrade_id"] for r in recs[1:]]
        why = (f"{r0['state']} by Checker downgrade {rid} (resolved false; verdict sets {', '.join(r0['verdict_sets'])}"
               + (f"; re-issue of {', '.join(reis)}" if reis else "") + f"): {label}; no cut length, no procurement")
    else:
        rid, label = FTG_MESH_BASIS_RECORD, "UNSUPPORTED BASIS"
        status = "HELD_SAME_BASIS"
        why = (f"HELD on the basis of {rid} (R-T374-6b): its own formula '{line.get('formula')}' and cover "
               f"'{inp.get('cover')}' are the record's unsupported basis (minimum cover as bar-end position, boxed-bar "
               "leg of unprinted diameter); NOT in the record's line list: extension proposed to the Checker "
               "(DGP-T374-FTGM); count also open (Q-71 readings); no cut length, no procurement")
    for k in ("shape_code", "d_mm", "n", "cut_length_m", "kg_per_m", "bar_mark", "bars_per_stock", "stock_bars",
              "offcuts", "procurement"):
        row[k] = ""
    for k in ("net_kg_low", "net_kg_high", "candidate_kg_low", "candidate_kg_high", "diff_kg", "procurement_kg_low",
              "procurement_kg_high", "offcut_kg_low", "offcut_kg_high"):
        row[k] = None
    for k in ("_n", "_lu"):
        row.pop(k, None)
    row.update(row_status=status, downgrade_id=rid, diff_cause="", held_geometry=printed, reason=why,
               audit_kg_low=lo, audit_kg_high=hi,
               audit_basis=f"{label} ({rid}): candidate upper value, audit only, never scheduled or procured")
    return row


def check_basis_signature(lines, by_line):
    """every line of the footing-mesh record must carry the basis the record states, or the 6b signature is wrong."""
    held = {lid for lid, rs in by_line.items() if any(r["downgrade_id"] == FTG_MESH_BASIS_RECORD for r in rs)}
    present = [l for l in lines if l["line_id"] in held]
    bad = [l["line_id"] for l in present if not ftg_mesh_basis(l)]
    if bad:
        raise ScheduleRefused(f"{FTG_MESH_BASIS_RECORD}: lines without the stated basis: {bad[:3]}")
    return len(present)


# ---------------------------------------------------------------- build

def load_snapshot(path=DOWNGRADE_SNAPSHOT) -> dict:
    return json.load(open(path, encoding="utf-8"))


def load_candidate(extract=EXTRACT, binding=T371_BINDING):
    if sha256(Path(extract)) != EXTRACT_SHA:
        raise ScheduleRefused("candidate extract sha256 differs from the pinned V3.0.16 extract")
    lines = json.load(open(extract, encoding="utf-8"))["lines"]
    bind = json.load(open(binding, encoding="utf-8"))
    if bind.get("extract_sha256") != EXTRACT_SHA:
        raise ScheduleRefused("T-371 binding is not on the pinned extract")
    return lines, bind["lines"]


def t318_line_ids(path=T318_INPUTS) -> set:
    """the line ids ARCH_TAKEOFF_V3.0.27 re-books (T-318: slab development + top-over-support lines), from the merged
    inputs; every other rebar line id and figure of V3.0.16 carries into V3.0.27 (T-373 reproduction)."""
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("t318_inputs", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return {x["line_id"] for x in mod.build()["lines"]}


LEDGERS = {  # policy -> (file, key columns matched to the line's inputs); every column of the row is read
    "COLUMN_STEEL_HAND_LEDGER_V1": ("research/agents_t148/T148_COLUMNS.csv", ("id", "component")),
    "BEAM_STEEL_HAND_LEDGER_V1": ("research/agents_t149/T149_BEAMS.csv", ("row_id", "component")),
    "GROUND_SYSTEM_STEEL_HAND_LEDGER_V1": ("research/agents_t138/T138_MEMBERS.csv", ("member", "component")),
}


def load_ledgers(root=ROOT) -> dict:
    return {pol: list(csv.DictReader(open(Path(root) / f, encoding="utf-8"))) for pol, (f, _) in LEDGERS.items()}


def ledger_row(line, ledgers):
    """the merged source-ledger row of a hand-ledger line (the candidate extract keeps only part of its text)."""
    inp = line.get("inputs") or {}
    pol = inp.get("policy")
    if pol not in LEDGERS or pol not in ledgers:
        return None
    key = inp.get("element")
    if pol == "BEAM_STEEL_HAND_LEDGER_V1":
        parts = line["element_id"].split(":")
        key = parts[3] if len(parts) > 4 and parts[3].startswith("R") else None
        if key is None:
            return None
    k1, k2 = LEDGERS[pol][1]
    hit = [r for r in ledgers[pol] if r[k1] == key and r[k2] == inp.get("component")]
    if len(hit) != 1:
        raise ScheduleRefused(f"{line['line_id']}: {len(hit)} source-ledger rows for {key} / {inp.get('component')}")
    return hit[0]


def shape_from_ledger(row, line, ledgers):
    """R-T374-1b: a bent attribute recorded in the source ledger row (cause / note) refuses shape 00 even when the
    candidate extract dropped that text; the line keeps its candidate kg, carried by name, never re-valued here."""
    if row["row_status"] not in ("SCHEDULED", "SCHEDULED_BOUNDED"):
        return row
    src = ledger_row(line, ledgers)
    if src is None:
        return row
    m = BENT_WORDS.search(" ".join(v or "" for v in src.values()))
    if not m:
        return row
    row.update(row_status="SHAPE_NOT_00", shape_code="", net_kg_low=None, net_kg_high=None, diff_kg=None,
               diff_cause="", reason=f"SHAPE_NOT_00: the source ledger ({LEDGERS[line['inputs']['policy']][0]}) "
                                     f"records '{m.group(0)}' for this bar: '{src.get('cause') or src.get('note')}'; "
                                     "no shape-00 row; candidate kg carried by name (a bent BBS shape needs the leg "
                                     "and bend diameter, G-T371-0)")
    for k in ("_n", "_lu"):
        row.pop(k, None)
    return row


def build(lines, pop_of, shapes, laps, rebooked_ids=frozenset(), stock_m=STOCK_M, ledgers=None, downgrades=None):
    stock_u = to_u(stock_m)
    ledgers = load_ledgers() if ledgers is None else ledgers
    by_line = downgrades_by_line(downgrades) if downgrades else {}
    basis_ids = {r["downgrade_id"] for rs in by_line.values() for r in rs}
    if FTG_MESH_BASIS_RECORD in basis_ids:
        check_basis_signature(lines, by_line)
    rows = []
    for line in sorted(lines, key=lambda x: (x["floor"], x["element_id"], x["line_id"])):
        pop = pop_of.get(line["line_id"])
        if pop not in POPULATIONS:
            continue
        if line["line_id"] in rebooked_ids:
            raise ScheduleRefused(f"{line['line_id']} is re-booked by V3.0.27 (T-318): bind the re-booked line")
        rows.append(apply_downgrades(shape_from_ledger(schedule_line(line, pop, shapes, laps), line, ledgers),
                                     line, by_line, basis_ids))
    leak = [r["line_id"] for r in rows if r["line_id"] in by_line
            and r["row_status"] in ("SCHEDULED", "SCHEDULED_BOUNDED", "RUN_PART")]
    if leak:
        raise ScheduleRefused(f"lines under an unresolved downgrade record scheduled: {leak[:3]}")
    runs = find_runs(rows)
    run_rows, in_run = [], {}
    for band in sorted(runs):
        for pos in sorted(runs[band]):
            rr = assemble_run(band, pos, runs[band][pos], stock_u)
            run_rows.append(rr)
            for r in runs[band][pos]:
                in_run[r["line_id"]] = rr["run_id"]
    # bar marks and procurement per row
    seq = defaultdict(int)
    run_mark = {}
    for r in rows:
        if r["row_status"] not in ("SCHEDULED", "SCHEDULED_BOUNDED"):
            continue
        prefix = POPULATIONS[r["population"]][0]
        rid = in_run.get(r["line_id"])
        if rid:
            if rid not in run_mark:
                seq[prefix] += 1
                run_mark[rid] = f"{prefix}{seq[prefix]:03d}"
            r["bar_mark"], r["run_id"] = run_mark[rid], rid
            r["row_status"] = "RUN_PART"
            r["procurement"] = f"on the run {rid}"
            continue
        seq[prefix] += 1
        r["bar_mark"] = f"{prefix}{seq[prefix]:03d}"
        n_lo, n_hi = r["_n"]
        if r["_lu"] > stock_u:
            sb = splice_band(r["_lu"], stock_u)
            r["procurement"] = (f"HELD: bar > stock, {sb['splices']} splice(s) for any lap up to "
                                f"{sb['valid_for_lap_up_to_m']} m; lap HELD")
            continue
        lo, hi = cut_from_stock(n_lo, r["_lu"], stock_u), cut_from_stock(n_hi, r["_lu"], stock_u)
        r["bars_per_stock"] = lo["bars_per_stock"]
        r["stock_bars"] = str(lo["stock_bars"]) if n_lo == n_hi else f"{lo['stock_bars']}..{hi['stock_bars']}"
        r["offcuts"] = " + ".join(f"{c} x {fmt_m(u)} m" for c, u in lo["offcuts"]) + (
            "" if n_lo == n_hi else " | at n high: " + " + ".join(f"{c} x {fmt_m(u)} m" for c, u in hi["offcuts"]))
        m = kg_per_m(r["d_mm"])
        r["procurement_kg_low"] = Decimal(lo["stock_bars"]) * STOCK_M * m
        r["procurement_kg_high"] = Decimal(hi["stock_bars"]) * STOCK_M * m
        r["offcut_kg_low"] = r["procurement_kg_low"] - r["net_kg_low"]
        r["offcut_kg_high"] = r["procurement_kg_high"] - r["net_kg_high"]
    for rr in run_rows:
        rr["bar_mark"] = run_mark[rr["run_id"]]
    return annotate_stale(rows), run_rows


def _count(xs):
    out = defaultdict(int)
    for x in xs:
        out[x] += 1
    return out


def summarise(rows, run_rows, stock_m=STOCK_M):
    pops = {}
    for pop in POPULATIONS:
        rs = [r for r in rows if r["population"] == pop]
        cnt = defaultdict(int)
        for r in rs:
            cnt[r["row_status"]] += 1
        sched = [r for r in rs if r["row_status"] in ("SCHEDULED", "SCHEDULED_BOUNDED", "RUN_PART")]
        exact = [r for r in sched if r["evidence_state"] == "SOURCE_DERIVED"]
        bnd = [r for r in sched if r["evidence_state"] == "BOUNDED_EXPOSURE"]
        carried = [r for r in rs if r["row_status"] == "BOUNDED_NO_ROW"]
        not00 = [r for r in rs if r["row_status"] == "SHAPE_NOT_00"]
        dg = [r for r in rs if r["row_status"] in HELD_ROW_STATES]
        s = lambda xs, k: sum((x[k] for x in xs), Decimal(0))
        pops[pop] = {
            "lines": len(rs), "row_status": dict(sorted(cnt.items())),
            "scheduled_net_kg": fmt_kg(s(exact, "net_kg_low")),
            "candidate_released_basis_kg": fmt_kg(s(exact, "candidate_kg_low")),
            "net_minus_candidate_kg": fmt_kg(s(exact, "diff_kg")),
            "difference_causes": dict(sorted(_count(r.get("diff_cause") for r in sched).items())),
            "scheduled_bounded_kg": [fmt_kg(s(bnd, "net_kg_low")), fmt_kg(s(bnd, "net_kg_high"))],
            "candidate_bounded_kg_of_scheduled": [fmt_kg(s(bnd, "candidate_kg_low")), fmt_kg(s(bnd, "candidate_kg_high"))],
            "bounded_carried_by_name_kg": [fmt_kg(s(carried, "candidate_kg_low")), fmt_kg(s(carried, "candidate_kg_high"))],
            "held_by_downgrade_audit_kg": {st: {"lines": sum(r["row_status"] == st for r in dg),
                                                "records": sorted({r["downgrade_id"] for r in dg if r["row_status"] == st}),
                                                "audit_kg": [fmt_kg(s([r for r in dg if r["row_status"] == st], "audit_kg_low")),
                                                             fmt_kg(s([r for r in dg if r["row_status"] == st], "audit_kg_high"))]}
                                           for st in HELD_ROW_STATES if any(r["row_status"] == st for r in dg)},
            "shape_not_00_carried_by_name_kg": [fmt_kg(s(not00, "candidate_kg_low")), fmt_kg(s(not00, "candidate_kg_high"))],
            "procurement_kg": [fmt_kg(sum((r.get("procurement_kg_low") or 0 for r in sched), Decimal(0))),
                               fmt_kg(sum((r.get("procurement_kg_high") or 0 for r in sched), Decimal(0)))],
            "bar_marks": len({r["bar_mark"] for r in sched}),
        }
    by_d = defaultdict(lambda: {"net_kg": Decimal(0), "procurement_kg": Decimal(0), "stock_bars": 0})
    for r in rows:
        if r["row_status"] == "SCHEDULED" and r.get("procurement_kg_low") is not None:
            b = by_d[r["d_mm"]]
            b["net_kg"] += r["net_kg_low"]
            b["procurement_kg"] += r["procurement_kg_low"]
            b["stock_bars"] += int(r["stock_bars"])
    for rr in run_rows:
        if rr["procurement_kg"] is not None:
            b = by_d[rr["d_mm"]]
            b["net_kg"] += rr["net_kg"]
            b["procurement_kg"] += rr["procurement_kg"]
            b["stock_bars"] += rr["procurement"]["stock_bars"]
    stock_u = to_u(stock_m)
    pieces = defaultdict(list)
    for r in rows:
        if r["row_status"] == "SCHEDULED" and r.get("procurement_kg_low") is not None:
            pieces[r["d_mm"]] += [r["_lu"]] * r["_n"][0]
    for rr in run_rows:
        if rr["procurement_kg"] is not None:
            pieces[rr["d_mm"]] += [rr["_run_u"]] * rr["n"]
    nested = {}
    for d, ps in sorted(pieces.items()):
        nf = nest_ffd(ps, stock_u)
        proc = Decimal(nf["stock_bars"]) * stock_m * kg_per_m(d)
        net = Decimal(sum(ps)) / U * kg_per_m(d)
        nested[str(d)] = dict(nf, pieces=len(ps), net_kg=fmt_kg(net), procurement_kg=fmt_kg(proc),
                              offcut_kg=fmt_kg(proc - net),
                              offcut_share=format((proc - net) / proc, ".4f") if proc else "")
    return {
        "policy": POLICY, "shape_code": SHAPE_00,
        "exact_rows_nested_by_diameter_ffd": nested, "stock_m": str(stock_m), "stock_status": STOCK_STATUS,
        "lines_bound": len(rows), "populations": pops,
        "runs": [{k: (fmt_kg(v) if k in ("net_kg", "procurement_kg") else v) for k, v in rr.items()
                  if not k.startswith("_")} for rr in run_rows],
        "exact_rows_procurement_by_diameter": {str(d): {"net_kg": fmt_kg(v["net_kg"]),
                                                        "procurement_kg": fmt_kg(v["procurement_kg"]),
                                                        "offcut_kg": fmt_kg(v["procurement_kg"] - v["net_kg"]),
                                                        "stock_bars": v["stock_bars"]}
                                               for d, v in sorted(by_d.items())},
    }


COLUMNS = ["line_id", "population", "floor", "element_id", "element_mark", "component", "evidence_state", "row_status",
           "bar_mark", "shape_code", "d_mm", "n", "cut_length_m", "kg_per_m", "net_kg_low", "net_kg_high",
           "candidate_kg_low", "candidate_kg_high", "diff_kg", "lap", "run_id", "bars_per_stock", "stock_bars",
           "offcuts", "procurement_kg_low", "procurement_kg_high", "offcut_kg_low", "offcut_kg_high", "procurement",
           "held_geometry", "diff_cause", "reason", "downgrade_id", "audit_kg_low", "audit_kg_high", "audit_basis"]
KG_COLS = {"net_kg_low", "net_kg_high", "candidate_kg_low", "candidate_kg_high", "diff_kg", "procurement_kg_low",
           "procurement_kg_high", "offcut_kg_low", "offcut_kg_high", "audit_kg_low", "audit_kg_high"}


def annotate_stale(rows):
    for r in rows:
        for k, note in STALE_TEXT.items():
            if k in (r.get("reason") or "") and note not in r["reason"]:
                r["reason"] = r["reason"] + " " + note
    return rows


def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (fmt_kg(r.get(k)) if k in KG_COLS else r.get(k, "")) for k in COLUMNS})


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--snapshot-from", help="verdicts dir: rewrite T374_BOUND_DOWNGRADES.json from the board first")
    a = ap.parse_args(argv)
    if a.snapshot_from:
        json.dump(snapshot_downgrades(a.snapshot_from), open(DOWNGRADE_SNAPSHOT, "w", encoding="utf-8"), indent=1)
    dg = load_snapshot()
    lines, pop_of = load_candidate()
    rows, run_rows = build(lines, pop_of, shape_status(), lap_status(), t318_line_ids(), downgrades=dg)
    summary = summarise(rows, run_rows)
    summary.update(candidate="ARCH_TAKEOFF_V3.0.27 by projection: V3.0.16 extract (sha256 " + EXTRACT_SHA[:8] +
                   ") + the T-318 re-booked line ids (none of these lines); downgrade records of every verdict set "
                   "up to " + max(dg["source_sha256"], key=lambda v: tuple(int(x) for x in v[1:].split("."))) +
                   " (" + CANDIDATE_OF_RECORD + ")", extract=str(EXTRACT.relative_to(ROOT)),
                   downgrade_snapshot={"file": DOWNGRADE_SNAPSHOT.name,
                                       "sha256": sha256(DOWNGRADE_SNAPSHOT),
                                       "unresolved_records": sum(not r["resolved"] for r in dg["records"])})
    write_csv(rows, a.csv)
    json.dump(summary, open(a.json, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps({p: (v["lines"], v["row_status"], v["scheduled_net_kg"], v["net_minus_candidate_kg"])
                      for p, v in summary["populations"].items()}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
