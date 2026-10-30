"""T-279: the URBAN_V3026_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.26 (engine.source.arch_v3026), built ONLY from
the Checker-merged blockwork fill of T-333 r2 (MERGED bb54c5d6, Verifier 2026-10-29 20:54 UTC Gate A r2), each file
pinned by sha256 (an edited ledger stops the build):

  FILL_T333.csv               228 rows = 76 register-v4 walls x 3 items (MAS.BLOCK m2, ARCH.WALL_PANEL m2,
                              ARCH.WALL_VOLUME m3), one row per (candidate line, wall): status, carried figure, part
                              status, checker run, held item, drop terms, width-CONFLICT increment, openings;
  LINE_BEFORE_AFTER_T333.csv  the merged per-line figures (verified / drawing-confirmed / owner-approved / established
                              parts / drop U / drop L): declared, and reproduced wall by wall by the engine;
  OPENING_HEIGHT_BASIS_T333.csv  the height basis of every DEDUCTED opening: an ASSUMED - OWNER-APPROVED wall (or
                              established part) names the Q-55 doors its net rests on;
  CANDIDATE_V3021_MASONRY_LINES.json  the 28 masonry line ids, items, storeys and element ids the fill was bound to
                              (the ids are content-derived and unchanged through V3.0.25: re-asserted by the engine
                              against the run).

The register behind the fill is v4 (T-288 MERGED 643b310b), the wall-to-line binding T-291 (MERGED 0c6b2ba5), the
per-wall VERIFIED statuses the Checker's own T-180 re-measures (verified_by per wall), the three Checker-corrected
walls at the Checker's values (1F-W20 24.507, 1F-W22 20.401, GF-W16 15.4356 - 2.950 d HELD). Nothing is typed here:
every figure is read from the merged files.

    python3 -I research/agents_t279/t279_inputs.py            # prints the per-line parts and the declared figures
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D333 = ROOT / "research/agents_t333"
FILL = D333 / "FILL_T333.csv"
LBA = D333 / "LINE_BEFORE_AFTER_T333.csv"
OHB = D333 / "OPENING_HEIGHT_BASIS_T333.csv"
CML = D333 / "CANDIDATE_V3021_MASONRY_LINES.json"
PINS = {FILL: "3544039cbd6f6ce5bf5854679ea7c76a6c69ddad6932d24c0d5b81d4ec096512",
        LBA: "d9f5400d0c429956cb32baff1b8ecc006be06e9c2c9362080c18f93b9dafafb3",
        OHB: "31c2f7ff7cfaa20d28e6729f94346ff66277683bea5242a1387a592dced25441",
        CML: "3922e76aa0cb7e4cf50316a1eb8aa61fdf37cb7ed206cb904696969289024ad9"}
MERGE_T333 = "bb54c5d69c763084dae54d004e9228356b041983"
CHECKER_T333 = ("Verifier 2026-10-29 20:54 UTC run session_01E6cPndBbKLfGX3mWqmR2Ui: T-333 r2 Gate A PASS, MERGED "
                "bb54c5d6 (D-T333-1 closed: Q-55 door parts ASSUMED - OWNER-APPROVED); per-wall VERIFIED statuses: "
                "the Checker's T-180 re-measures named in verified_by")
EM = "ASSUMED — OWNER-APPROVED"
STATUS = {"VERIFIED": "VERIFIED", "DRAWING-CONFIRMED": "DRAWING-CONFIRMED", EM: "ASSUMED - OWNER-APPROVED",
          "HELD": "HELD", "HELD ON DROP": "HELD ON DROP", "ESTABLISHED PART + HELD": "ESTABLISHED PART + HELD"}


class PinError(ValueError):
    pass


def _pinned(p):
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != PINS[p]:
        raise PinError(f"{p.relative_to(ROOT)}: sha256 {h[:8]} is not the merged {PINS[p][:8]} (edited ledger)")
    return h


def _f(x):
    x = (x or "").strip()
    return None if x == "" else float(x)


def _st(x):
    x = (x or "").strip()
    if x == "":
        return None
    if x not in STATUS:
        raise ValueError(f"unknown status {x!r} in the merged fill")
    return STATUS[x]


def _rows(p):
    return list(csv.DictReader(p.open(encoding="utf-8", newline="")))


def owner_sources():
    """wall -> the Q-55 openings its net deducts at the fallback height (OPENING_HEIGHT_BASIS_T333)."""
    out = {}
    for r in _rows(OHB):
        if r["height_basis"] == EM:
            out.setdefault(r["host"], []).append(f"{r['opening_id']} {r['deduction_m2']}")
    return {k: "OWNER_QUESTIONS_ANSWERED Q-55 C (door height 2.20 m where no sheet prints one): " + ", ".join(v)
            for k, v in out.items()}


def build(project_id=None):
    hashes = {p.name: _pinned(p) for p in PINS}
    cml = {x["line_id"]: x for x in json.loads(CML.read_text(encoding="utf-8"))["masonry_lines"]}
    osrc = owner_sources()
    lines, order = {}, []
    for r in _rows(FILL):
        lid = r["line_id"]
        if project_id and r["project_id"] != project_id:
            raise ValueError(f"fill row for {r['project_id']!r}, the run is {project_id!r}")
        if lid not in lines:
            m = cml[lid]
            lines[lid] = {"line_id": lid, "item_code": r["item_code"], "unit": r["unit"], "floor": r["floor"],
                          "family": float(r["family"]), "element_id": m["element_id"],
                          "before": {"evidence_state": m["evidence_state"],
                                     "measured_net": None if m["measured_net"] in (None, "None") else
                                     float(m["measured_net"])},
                          "walls": []}
            order.append(lid)
        st, ps = _st(r["status"]), _st(r["part_status"])
        eff = ps if st == "ESTABLISHED PART + HELD" else st
        w = {"wall_id": r["wall_id"], "block_type": r["block_type"] if r["block_type"] not in ("", "-") else None,
             "status": st, "carried": _f(r["carried"]), "part_status": ps,
             "verified_by": r["verified_by"] or None,
             "owner_source": osrc.get(r["wall_id"]) if eff == "ASSUMED - OWNER-APPROVED" else None,
             "held_item": r["held_item"] or None, "upper_at_d0": _f(r["upper_at_d0"]),
             "drop_coefficient": _f(r["drop_coefficient"]), "conflict": r["conflict"] or None,
             "conflict_increment_outside": _f(r["conflict_increment_outside"]),
             "openings": r["opening_deductions"] or None}
        if st == "HELD ON DROP":
            w["verified_by"] = None          # a withdrawn / drop wall carries no released status
        lines[lid]["walls"].append(w)
    for r in _rows(LBA):
        if r["line_id"] not in lines:
            continue
        lines[r["line_id"]]["declared"] = {k: float(r[k] or 0) for k in (
            "verified", "drawing_confirmed", "owner_approved", "established_parts", "drop_upper_at_d0",
            "drop_coefficient")}
    pid = project_id or _rows(FILL)[0]["project_id"]
    return {"schema": "URBAN_V3026_INPUTS_V1", "project": pid, "fill_task": "T-333",
            "sources": [{"file": f"research/agents_t333/{FILL.name}", "sha256": hashes[FILL.name], "task": "T-333",
                         "merge_commit": MERGE_T333, "checker_run": CHECKER_T333}],
            "pinned": hashes, "lines": [lines[k] for k in order]}


def main():
    doc = build()
    for ln in doc["lines"]:
        print(ln["line_id"], ln["item_code"], ln["floor"], ln["family"], len(ln["walls"]), "walls",
              json.dumps(ln["declared"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
