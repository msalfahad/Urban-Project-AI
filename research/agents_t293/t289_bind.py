"""T-293 binding: formwork member key -> candidate concrete line id(s), from merged registers and the candidate's own
element ids only (named t289_bind because it reuses the T-289 column frame binding).

  GB:<run>               T-242 run -> engine band(s) (T-289 BAND_PAIRING, MERGED 455c93c4, + the three oblique bands of
                         OBLIQUE_BAND_PAIRING_T293) -> the STR.CONC.GROUND_BEAM line whose element id is that band
  COLUMN:<COL-xx-nn>     formwork column id = T-248 owner_t119_id -> T-248 member -> its engine column id moved by the
                         one modal frame translation (T-289 column_offset) -> the STR.CONC.COLUMN line (<= 2 mm, one)
  FOOTING_LINE:<line id> a footing line chosen by mark (type rows) or by handle (CANDIDATE footing_handles) upstream
  STRAP:SBn              the HL:STRAP_CONCRETE:SBn:CONCRETE line (axis length, Q-74)
  BOUNDARY_FDN_M1        the STR.CONC.BOUNDARY_WALL foundation strip line
  POOL:WALLS / POOL:BASE the HL:POOL_CONCRETE:POOL-1:WALLS / :BASE lines
A line in state NOT_APPLICABLE_WITH_EVIDENCE carries no concrete (superseded or undrawn) and owns no face.
"""

from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t289"))
import t289_alsenan as A289  # noqa: E402

NOT_OWNER = ("NOT_APPLICABLE_WITH_EVIDENCE",)
FIXED = {
    "STRAP:SB1": ("STR.CONC.STRAP", r"^HL:STRAP_CONCRETE:SB1:CONCRETE$"),
    "STRAP:SB2": ("STR.CONC.STRAP", r"^HL:STRAP_CONCRETE:SB2:CONCRETE$"),
    "STRAP:SB3": ("STR.CONC.STRAP", r"^HL:STRAP_CONCRETE:SB3:CONCRETE$"),
    "BOUNDARY_FDN_M1": ("STR.CONC.BOUNDARY_WALL", r":BOUNDARY_WALL:FOUNDATION:"),
    "POOL:WALLS": ("STR.CONC.POOL", r"^HL:POOL_CONCRETE:POOL-1:WALLS$"),
    "POOL:BASE": ("STR.CONC.POOL", r"^HL:POOL_CONCRETE:POOL-1:BASE$"),
}
PLANTED = {   # T-220 MERGED 579e613d, T-220_PLANTED_COLUMNS.md rows 18 - 20: record id <- FFRS / SFRS member <- T-119 id
    "COLUMN:COL-1F-57": ("FFRS:66A", "HL:PLANTED_COLUMN:PC-1F-A:CONCRETE"),
    "COLUMN:COL-1F-58": ("FFRS:69D", "HL:PLANTED_COLUMN:PC-1F-B:CONCRETE"),
    "COLUMN:COL-2F-59": ("SFRS:778", "HL:PLANTED_COLUMN:PC-2F:CONCRETE"),
}
NO_LINE = {
    "LIFT": "no candidate concrete line for the lift-pit walls (height 'AS ARCH.'; no merged pit-wall concrete ledger)",
    "BOUNDARY_PADS": "no candidate concrete line for the boundary-wall pads (count not printed, T-065 C3)",
}


def _band(eid):
    m = re.search(r":GROUND_BEAMS:GROUND:(BAND[0-9.]+)$", eid or "")
    return m.group(1) if m else None


def run_bands(pairing, oblique):
    inv = collections.defaultdict(list)
    for b, v in pairing["bands"].items():
        for h in v["runs"]:
            inv[h["run"]].append(b)
    for b, v in oblique.get("bands", {}).items():
        inv[v["run"]].append(b)
    return inv


def footing_marks(lines):
    """mark -> footing line ids (P-C:FTG:SHn:<mark>@x,y:...); the 1B1B outline line (tags F + F10) under 'F10'"""
    out = collections.defaultdict(list)
    for l in lines:
        if l["item_code"] != "STR.CONC.FOOTING":
            continue
        m = re.match(r"^P-C:FTG:SH\d+:(\w+)@", l["element_id"] or "")
        if m:
            out[m.group(1)].append(l["line_id"])
        elif "outline 1B1B" in (l.get("notes") or "") and "F10" in (l.get("notes") or ""):
            out["F10"].append(l["line_id"])
    return {k: sorted(v) for k, v in out.items()}


def bind_all(cand, t248_rows, pairing, oblique, members_used=()):
    lines = [l for l in cand["lines"] if l["evidence_state"] not in NOT_OWNER]
    out, why = {}, {}
    by_band = collections.defaultdict(list)
    for l in lines:
        if l["item_code"] == "STR.CONC.GROUND_BEAM" and _band(l["element_id"]):
            by_band[_band(l["element_id"])].append(l["line_id"])
    for run, bands in run_bands(pairing, oblique).items():
        ids = sorted({i for b in bands for i in by_band.get(b, [])})
        out["GB:" + run] = ids
        if not ids:
            why["GB:" + run] = f"bands {bands} hold no STR.CONC.GROUND_BEAM line"
    members = {r["member"]: r for r in t248_rows}
    cols = [l for l in lines if l["item_code"] == "STR.CONC.COLUMN"]
    off = A289.column_offset([{"element_id": l["element_id"]} for l in cols], members)
    by_member = collections.defaultdict(list)
    for l in cols:
        m = A289.bind_column(l["element_id"], members, off)
        if m is not None:
            by_member[m["member"]].append(l["line_id"])
    for r in t248_rows:
        if r["owner_t119_id"]:
            k = "COLUMN:" + r["owner_t119_id"]
            out[k] = sorted(by_member.get(r["member"], []))
            if not out[k]:
                why[k] = f"T-248 member {r['member']} ({r['kind']}) binds to no candidate STR.CONC.COLUMN line"
    for k, (member, eid) in PLANTED.items():
        if members.get(member, {}).get("owner_t119_id") != k.split(":", 1)[1]:
            raise ValueError(f"T-248 member {member} is not {k}")
        out[k] = sorted(l["line_id"] for l in lines if l["element_id"] == eid)
        why.pop(k, None) if out[k] else why.__setitem__(k, f"no candidate line {eid}")
    for k, (code, pat) in FIXED.items():
        out[k] = sorted(l["line_id"] for l in lines if l["item_code"] == code and re.search(pat, l["element_id"] or ""))
        if not out[k]:
            why[k] = f"no {code} line with an element id matching {pat!r}"
    for l in lines:
        if l["item_code"] == "STR.CONC.FOOTING":
            out["FOOTING_LINE:" + l["line_id"]] = [l["line_id"]]
    for k, v in NO_LINE.items():
        out[k], why[k] = [], v
    for m in members_used:
        if m.startswith("BOUNDARY_GB:"):
            out[m] = []
            why[m] = ("no candidate concrete line for the boundary ground beam 20 x 40 at N.G. (T-253 MERGED "
                      "c2d5b3cd, DRAWING-CONFIRMED); the only boundary line is the foundation strip M1")
    out["_column_offset"] = off
    out["_reason"] = why
    return out
