"""T-503 (lane S, non-candidate): the B1-04 DISPOSAL balance (DISPOSAL_BALANCE_V1) on the earthworks lines of the
candidate of record ARCH_TAKEOFF_V3.0.48 (lines sha 33a81c53, T-350 r4 MERGED 5de697ff), development villa.

Inputs, each pinned by sha256 (an edited file stops the run); every figure and status is READ, none typed:
  research/agents_t350r4/summary_t350r4.json      the 7 earthworks lines V3.0.48 changed or added (ids, states,
                                                  quantities, evidence status, held items)
  research/agents_t485/out/LINE_INDEX_V3_0_46.json the ids of the 20 earthworks lines (the 13 V3.0.48 left HELD BLANK
                                                  keep their V3.0.43 ids; the 2 added are in the summary)

Typed here: the role of each line (excavation in situ / compacted fill) and the one exclusion below.
EXCLUSION (board T-503 row): the external ground-beam TRENCH line L-438a4abd3adc0475d0bd is HELD-DEFECTIVE in
V3.0.48 (Checker F-C-T350R4-1: its bound 1.203269 .. 1.432834 counts 0.134 m3 inside F10F and ground over the pits'
beyond-plot strip); T-497 restates it. Until T-497 merges, the term is HELD PENDING T-497 (its bound is never used).
Geotechnical evidence: none for this villa (no soil report among the project files) -> suitable share 0 .. 1.
Densities: none measured, none specified as a placement target -> HELD. Contract measurement basis: none -> in situ.

    python3 -I research/agents_t503/t503_alsenan.py          # writes summary_t503.json beside this file
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import disposal_balance_v1 as B  # noqa: E402

S48 = ROOT / "research/agents_t350r4/summary_t350r4.json"
IDX = ROOT / "research/agents_t485/out/LINE_INDEX_V3_0_46.json"
PINS = {S48: "69a6756c25bda5a26ff5eb2e62f38465b0d2f762b98e98829eb2af44c6fcb2ab",
        IDX: "d9e0a7e46b2e17a1cef78d8630cf2b1f6c2aa8bbe5dbe0f29037e6f1e54f2dd0"}
CANDIDATE_SHA = "33a81c5387dc5c306086867da32415892e164a60a6a42893dc040e2d64f963ce"
TRENCH_PENDING = "L-438a4abd3adc0475d0bd"
DISPOSAL_LINE = "L-78d7c8a989ab34527a1c"
ROLE = {"STR.EARTH.EXCAVATION": B.EXC, "STR.EARTH.BACKFILL": B.FILL}


def _load(p):
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != PINS[p]:
        raise SystemExit(f"{p.name}: sha256 differs from the merged file (edited input)")
    return json.loads(b)


def terms():
    s48, idx = _load(S48), _load(IDX)
    if s48["candidate_sha256"] != CANDIDATE_SHA or s48["method"] != "ARCH_TAKEOFF_V3.0.48":
        raise SystemExit("summary is not the candidate of record V3.0.48")
    lines = {l["line_id"]: l for l in idx["lines"] if l["element_id"].startswith("EW-T350:")}
    changed = {r["line_id"]: r for r in s48["rows"]}
    for lid, r in changed.items():
        lines.setdefault(lid, {"line_id": lid, "item_code": r["item_code"], "element_id": r["element_id"]})
    if len(lines) != s48["earthworks"]["lines"]:
        raise SystemExit(f"{len(lines)} earthworks lines, the candidate has {s48['earthworks']['lines']}")
    out, disposal = [], None
    for lid in sorted(lines, key=lambda x: lines[x]["element_id"]):
        l = lines[lid]
        if l["item_code"] == "STR.EARTH.DISPOSAL":
            disposal = l
            continue
        zone = l["element_id"].split(":", 2)[2]
        r = changed.get(lid)
        if lid == TRENCH_PENDING:
            out.append(B.term(lid, ROLE[l["item_code"]], status=B.HELD, zone=zone,
                              held_parts=["HELD PENDING T-497: the V3.0.48 bound is HELD-DEFECTIVE (F-C-T350R4-1), "
                                          "never used"]))
            continue
        if r is None or r["after"]["state"] == "BLOCKED_RFI":
            out.append(B.term(lid, ROLE[l["item_code"]], status=B.HELD, zone=zone,
                              held_parts=(r or {}).get("still_held", [])))
            continue
        a = r["after"]
        lo, hi = (a["value"], a["value"]) if a["value"] is not None else (a["low"], a["high"])
        out.append(B.term(lid, ROLE[l["item_code"]], lo, hi, status=r["evidence_status"], zone=zone,
                          held_parts=r["still_held"]))
    if disposal is None or disposal["line_id"] != DISPOSAL_LINE:
        raise SystemExit("the B1-04 disposal line is not the V3.0.43 one")
    return out


def run():
    T = terms()
    res = B.balance(T, rho_insitu=B.density(None, B.HELD, kind="INSITU"),
                    rho_target=B.density(None, B.HELD, kind="PLACEMENT_TARGET"),
                    suit=B.suitability(), rho_loose_import=None, bulk=B.bulking(), contract_basis=None)
    res["disposal_line"] = DISPOSAL_LINE
    res["candidate"] = {"method": "ARCH_TAKEOFF_V3.0.48", "lines_sha256": CANDIDATE_SHA}
    res["terms"] = [{k: t[k] for k in ("line_id", "role", "zone", "low", "high", "status")} for t in T]
    return res


def main(write=True):
    res = run()
    if write:
        (HERE / "summary_t503.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return res


if __name__ == "__main__":
    r = main()
    print("E", r["excavation"]["low"], "..", r["excavation"]["high"], "open", r["excavation"]["held_lines"])
    print("D", r["fill_demand"]["low"], "..", r["fill_demand"]["high"], "open", r["fill_demand"]["held_lines"])
    for k in ("disposal_insitu_m3", "import_compacted_m3"):
        print(k, "low:", B.describe_end(r[k]["low"]), "| high:", B.describe_end(r[k]["high"]))
    print("state", r["state"], "payable", r["payable"])
