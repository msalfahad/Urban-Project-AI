"""T-378 STAIR_NOTE9_ROLE_BINDING_V1 (research code, stdlib; read-only on every candidate and ledger).

Question (F-T373-2): 22 candidate STR.REBAR stair lines book a DEVELOPMENT length '2 x 40 d .. 2 x 70 d per bar' whose
cited basis is ST p.8 note 9. Note 9 names STARTER bars only (Arabic 'اشاير': 'tie / development length of the
starter bars not less than 70 x dia in tension zones, 40 x dia in compression zones', zone not printed; T-366). A stair
CAN have starters, so before any arithmetic each line's bar is given its physical role and each booked end is read on
the drawing:

  STARTER       the end is drawn as a SEPARATE bar left out of the supporting beam / slab / G.B into the flight and
                tied (overlapped) with the flight bar: inside note 9's scope -> the line's bound is KEPT (still a range,
                never released: the tension / compression zone is not printed).
  NOT_STARTER   the end is the line's OWN bar: it continues / anchors into the support as one drawn shape, ends inside
                the same element, or runs on into another flight; no starter and no tie is drawn -> note 9 is no
                authority (R-T373-1) -> HELD by name, BLANK, never 0.
  UNKNOWN       the end's support or shape is not printed and a starter is one of the alternatives; the missing print
                must be named -> HELD by name, BLANK.

A line's figure covers every end it books ('2 x' = two ends). The line keeps note 9's bound only when EVERY booked end
is a STARTER; one NOT_STARTER end and the line is NOT_STARTER; otherwise UNKNOWN. A line is never split here (that would
be a new figure; a downgrade-only record only moves a whole line to HELD, owner 2026-10-24 23:57).

Rule R-T378-1 (every villa; provenance T-373 F-T373-2, T-378): before note 9 (or any starter-bar note) values a stair
bar's end, the bar's role and the end's drawn shape are recorded with the sheet / detail / label; only a drawn separate
starter tied with the flight bar is inside the note's scope; the flight's own anchorage, a bar ending inside its own
element and a flight-to-flight continuation are not.

    python3 -I research/agents_t378/t378_stair_note9.py \
        --csv research/agents_t378/T378_STAIR_ROLE_LEDGER.csv --json research/agents_t378/T378_SUMMARY.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "STAIR_NOTE9_ROLE_BINDING_V1"
NOTE9 = re.compile(r"note\s*9", re.I)
ENDS_IN_BASIS = re.compile(r"(\d+)\s*x\s*40\s*d\s*\.\.\s*(?:count B x )?(\d+)\s*x\s*70\s*d")

_spec = importlib.util.spec_from_file_location("t373_lap_binding", ROOT / "research/agents_t373/t373_lap_binding.py")
T373 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T373)

# T-373 record (MERGED db5a8dff) on V3_0_27_BOQ_LINES.json f7972540: the candidate's bounded STR.REBAR after its record
T373_AFTER = (Decimal("11276.569488"), Decimal("14287.667938"))
RELEASED_STR_REBAR = Decimal("10250.167987")

DRAWN_AS = {
    "SEPARATE_STARTER_TIED": "STARTER",          # a separate bar out of the support, overlapped with the flight bar
    "OWN_BAR_INTO_SUPPORT": "NOT_STARTER",       # the line's own bar continues / anchors into the support (one shape)
    "OWN_BAR_INSIDE_ELEMENT": "NOT_STARTER",     # the end stays inside the same element (step-bar leg, flight side)
    "FLIGHT_TO_FLIGHT": "NOT_STARTER",           # runs on into the next flight of the same stair (continuous or lap)
    "NOT_PRINTED": "UNKNOWN",                    # support / shape not printed; a starter is one alternative
}
ROLES = {"FLIGHT_MAIN", "FLIGHT_DISTRIBUTION", "STEP_BAR", "LANDING_BOTTOM", "LANDING_TOP", "FLIGHT_TOP_AT_SUPPORT",
         "STARTER_INTO_FLIGHT"}


class RoleError(ValueError):
    """A refusal: the input cannot be classified without inventing something."""


def classify_end(end):
    if not end.get("ref"):
        raise RoleError(f"end {end.get('end')} without a sheet / detail / label reference")
    drawn = end.get("drawn_as")
    if drawn not in DRAWN_AS:
        raise RoleError(f"unknown drawn shape {drawn!r}")
    cls = DRAWN_AS[drawn]
    if cls == "UNKNOWN" and not end.get("missing"):
        raise RoleError(f"end {end.get('end')} UNKNOWN without the missing print named")
    return cls


def ends_booked(basis):
    m = ENDS_IN_BASIS.search(basis or "")
    if not m or m.group(1) != m.group(2):
        raise RoleError(f"cannot read the number of ends from the basis {basis!r}")
    return int(m.group(1))


def classify_line(line, role):
    """line: candidate line (slim); role: {'role', 'ends': [...]}. Returns (line_class, proposed, reason, end_classes)."""
    if line.get("unit") != "kg":
        raise RoleError(f"{line['line_id']} in {line.get('unit')}: the binding reads kg only (t only at export)")
    if line.get("evidence_state") == "RELEASED" or line.get("measured_net") is not None:
        raise RoleError(f"{line['line_id']} is valued as released: a note 9 length is never released (zone not printed)")
    basis = (line.get("bounded_range") or {}).get("basis", "")
    if not NOTE9.search(basis):
        raise RoleError(f"{line['line_id']}: basis does not rest on note 9; outside this binding")
    if not role or role.get("role") not in ROLES:
        raise RoleError(f"{line['line_id']}: the bar's physical role must be defined before any classification")
    ends = role.get("ends") or []
    n = ends_booked(basis)
    if len(ends) != n:
        raise RoleError(f"{line['line_id']}: the figure books {n} ends, {len(ends)} read on the drawing")
    classes = [classify_end(e) for e in ends]
    if all(c == "STARTER" for c in classes):
        return "STARTER", "KEEP_RANGE", "every booked end is a drawn starter tied with the flight bar: inside note 9", classes
    if "NOT_STARTER" in classes:
        why = "; ".join(f"{e['end']}: {e['drawn_as']}" for e, c in zip(ends, classes) if c == "NOT_STARTER")
        return "NOT_STARTER", "HELD", f"note 9 names starter bars only; {why}: no printed authority, HELD by name, BLANK", classes
    why = "; ".join(f"{e['end']}: {e['missing']}" for e, c in zip(ends, classes) if c == "UNKNOWN")
    return "UNKNOWN", "HELD", f"not printed: {why}: HELD by name, BLANK", classes


def value_after(proposed, low, high):
    """KEEP_RANGE keeps the bound (never released); HELD is BLANK (None), never 0."""
    if proposed == "KEEP_RANGE":
        return low, high
    if proposed == "HELD":
        return None, None
    raise RoleError(f"unknown proposal {proposed}")


def check_record(rows):
    """Refuses a HELD row written as 0 (or any figure), a KEEP row that changed its figure, a line bound twice."""
    seen = set()
    for r in rows:
        if r["line_id"] in seen:
            raise RoleError(f"line bound twice: {r['line_id']}")
        seen.add(r["line_id"])
        if r["proposed"] == "HELD" and (r["kg_low_after"] is not None or r["kg_high_after"] is not None):
            raise RoleError(f"{r['line_id']}: HELD must be BLANK, never 0 or a figure")
        if r["proposed"] == "KEEP_RANGE" and (r["kg_low_after"], r["kg_high_after"]) != (r["kg_low_now"], r["kg_high_now"]):
            raise RoleError(f"{r['line_id']}: a kept bound cannot change")
    return True


def landing_lap_authority(cited):
    """A lap on a landing / flight bar valued from a printed note: delegated to R-T373-1 (the note must name the
    group). p.15 NOTE 1 names slab TEMPERATURE bars only, note 9 STARTER bars only."""
    return T373.lap_authority("STAIR_LANDING", cited)


# ---------------------------------------------------------------- Alsenan binding
def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_listed(t373_csv):
    rows = [r for r in csv.DictReader(open(t373_csv, encoding="utf-8")) if r["proposed"] == "LISTED_ONLY"]
    if not rows:
        raise RoleError("no LISTED_ONLY rows in the T-373 binding")
    return rows


def bind(listed, extract_lines, roles):
    """listed: T-373 LISTED_ONLY rows (V3.0.27 f7972540 figures); extract_lines: the V3.0.16 extract (formula / basis /
    inputs; same line ids); roles: {(element, component): role}."""
    by_id = {l["line_id"]: l for l in extract_lines}
    out = []
    for r in listed:
        l = by_id.get(r["line_id"])
        if l is None:
            raise RoleError(f"{r['line_id']} not in the extract")
        low_now, high_now = Decimal(r["kg_low_now"]), Decimal(r["kg_high_now"])
        br = l["bounded_range"]
        if (Decimal(str(br["low"])), Decimal(str(br["high"]))) != (low_now, high_now):
            raise RoleError(f"{r['line_id']}: V3.0.16 extract figure differs from the V3.0.27 binding: stale input")
        key = (l["inputs"]["element"], l["inputs"]["component"])
        role = roles.get(f"{key[0]}|{key[1]}")
        cls, proposed, reason, end_classes = classify_line(l, role)
        lo_a, hi_a = value_after(proposed, low_now, high_now)
        out.append({
            "line_id": l["line_id"], "element_id": l["element_id"], "floor": l["floor"], "subtrade": l["subtrade"],
            "stair_element": key[0], "component": key[1], "printed": l["inputs"]["printed"], "role": role["role"],
            "role_text": role["role_text"],
            "ends": " || ".join(f"{e['end']} [{e['support']}] {e['drawn_as']} -> {c} ({e['ref']})"
                                + (f" MISSING: {e['missing']}" if e.get("missing") else "")
                                for e, c in zip(role["ends"], end_classes)),
            "authority_cited": "P8-NOTE9", "basis_now": br["basis"], "line_class": cls, "proposed": proposed,
            "reason": reason, "state_now": l["evidence_state"], "kg_low_now": low_now, "kg_high_now": high_now,
            "kg_low_after": lo_a, "kg_high_after": hi_a, "end_classes": end_classes,
        })
    unused = set(roles) - {f"{l['stair_element']}|{l['component']}" for l in out}
    if unused:
        raise RoleError(f"role records bound to no line: {sorted(unused)}")
    check_record(out)
    return out


def summarise(rows):
    held = [r for r in rows if r["proposed"] == "HELD"]
    kept = [r for r in rows if r["proposed"] == "KEEP_RANGE"]
    s = lambda rs, k: sum((r[k] for r in rs), Decimal(0))
    ends = {}
    for r in rows:
        for c in r["end_classes"]:
            ends[c] = ends.get(c, 0) + 1
    by_class = {}
    for r in rows:
        by_class[r["line_class"]] = by_class.get(r["line_class"], 0) + 1
    by_stair = {}
    for r in rows:
        b = by_stair.setdefault(r["floor"], [0, Decimal(0), Decimal(0)])
        b[0] += 1; b[1] += r["kg_low_now"]; b[2] += r["kg_high_now"]
    held_lo, held_hi = s(held, "kg_low_now"), s(held, "kg_high_now")
    return {
        "lines": len(rows), "line_class": by_class, "end_class": ends,
        "valued_now_kg": [str(s(rows, "kg_low_now")), str(s(rows, "kg_high_now"))],
        "downgrade_set": {"lines": len(held), "kg_now": [str(held_lo), str(held_hi)], "kg_after": "BLANK",
                          "line_ids": sorted(r["line_id"] for r in held)},
        "kept_bound": {"lines": len(kept), "kg": [str(s(kept, "kg_low_now")), str(s(kept, "kg_high_now"))]},
        "by_floor": {k: {"lines": v[0], "kg_now": [str(v[1]), str(v[2])]} for k, v in sorted(by_stair.items())},
        "str_rebar_bounded_after_t373": [str(T373_AFTER[0]), str(T373_AFTER[1])],
        "str_rebar_bounded_after_t378": [str(T373_AFTER[0] - held_lo), str(T373_AFTER[1] - held_hi)],
        "str_rebar_released": str(RELEASED_STR_REBAR) + " (unchanged)",
    }


COLS = ["line_id", "element_id", "floor", "subtrade", "stair_element", "component", "printed", "role", "role_text",
        "ends", "authority_cited", "basis_now", "line_class", "proposed", "reason", "state_now", "kg_low_now",
        "kg_high_now", "kg_low_after", "kg_high_after"]


def _f(x):
    return "BLANK" if x is None else format(x, "f")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--t373", default=str(ROOT / "research/agents_t373/T373_LAP_BINDING.csv"))
    ap.add_argument("--extract", default=str(ROOT / "research/agents_t297/CANDIDATE_V3016_REBAR_LINES.json"))
    ap.add_argument("--roles", default=str(ROOT / "research/agents_t378/ALSENAN_STAIR_ROLE_INPUT.json"))
    ap.add_argument("--csv")
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    roles = json.load(open(a.roles, encoding="utf-8"))
    rows = bind(load_listed(a.t373), json.load(open(a.extract, encoding="utf-8"))["lines"], roles["roles"])
    summ = {"schema": SCHEMA, "candidate": "V3_0_27_BOQ_LINES.json f7972540 (figures via the T-373 binding)",
            "inputs_sha256": {"t373_csv": _sha(a.t373)[:16], "extract": _sha(a.extract)[:16], "roles": _sha(a.roles)[:16]},
            **summarise(rows)}
    if a.csv:
        with open(a.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore", lineterminator="\n")
            w.writeheader()
            for r in sorted(rows, key=lambda r: (-r["kg_high_now"], r["line_id"])):
                w.writerow({k: (_f(r[k]) if k.startswith("kg_") else r[k]) for k in COLS})
    if a.json:
        Path(a.json).write_text(json.dumps(summ, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if not a.csv and not a.json:
        print(json.dumps(summ, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
