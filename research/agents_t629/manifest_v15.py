"""T-629 WIRING MANIFEST V15 + OVERLAY DRY RUN (R-T629-1; lane I, non-candidate, research only).

V15 carries the fix rows the Checker MERGED after V14 (T-619) into the Gate B diff targets that own the lines:
  - T-615 (Q-80 A, UPC-BLACK-BLOCK-001 1.1.0): the 12 staged 0.15 m black material lines of the T-498 package (6 hosts x
    units + panel mortar) leave HELD blank (R-T533-1, V4 block_module) and take the restated quantities; the perimeter
    joint mortar of the same 6 hosts enters as its own key (the T-498 step 6 pattern); all ASSUMED — OWNER-APPROVED.
    Chained INSIDE the T-498 package (the lines are T-498 stage lines: one Gate B unit per line, R1).
  - T-617 FR-T617-1 (Q-72): on the T-563 plaster lines of GF-08 / 1F-13 / 2F-01 the lift landing door deduction is
    capped at 1.00 x (face height - (D - t)); the HELD low end rises by the band 0.59 / 0.59 / 0.24 m2, the high stays.
    Chained INSIDE the T-563 package (the lines are T-563 lines).
  - T-622: the GF-07 pantry wall tile line 32.3422 -> 32.375 m2 (Checker own re-measure, ENGINE_WRONG -0.0328 m2;
    the Checker named it the fix row). Its own package (no earlier package writes the line).
Merged with 0 rows, listed: T-618 (FR-T618-1 statement restate; FR-T618-2 porch skirting held, no owning line),
T-620, T-621, T-623. Not merged at claim, refused by name: T-624, T-628. Nothing is wired; no candidate, released
(V2.9 + route G), rule, knowledge or registry file is written; no drawing is read: every figure comes from a committed,
Checker-merged output, each sha256-pinned and named.

R-T629-1 (every villa on the engine's line-index scheme):
  (a) MERGED ONLY (R-T619-1 (a) code): a fix row enters only from a task MERGED with a Checker verdict; merged tasks
      whose rows move no line are listed with 0 rows; a task not merged is refused by name.
  (b) A FIX ROW ON A LINE THAT A PENDING GATE B PACKAGE WRITES CHAINS INSIDE THAT PACKAGE: its before is the package's
      own after on that line (never the candidate's); a second package writing the line stays refused (R1). The
      appended steps carry the source task, rule and verdict, and the package keeps its name.
  (c) AN OWNER ANSWER RELEASES A HELD-BY-NAME MATERIAL LINE ONLY ON ITS RECORD: a staged line HELD by R-T533-1 takes
      a value only when (1) the answering rule version is cited (UPC-BLACK-BLOCK-001 1.1.0, Q-80 A), (2) its quantity
      re-derives from the rule exactly (units = base x 1 / (0.40 x 0.20); panel = base x 0.15 x (1 - 0.39 x 0.19 x
      12.5)) within the source's print precision, (3) the walls of each host re-add to the host's contract line, and
      (4) the line was HELD blank before. Walls the source keeps HELD on their own cause (GF-W22 D-27, 2F-W08 D-39)
      never enter; their hosts' material lines stay HELD blank. Evidence is ASSUMED — OWNER-APPROVED (WORKFLOW_CONTROLS
      s.5), never VERIFIED.
  (d) A RANGE IS NEVER A POINT (R-T619-1 (c)): a range lo .. hi enters as the line at lo and a companion HELD line
      0 .. (hi - lo); a range whose high leaves named pieces HELD (dome-opening pieces, T-520) has an OPEN companion
      (0 .. open), never the stated high as a cap.
  (e) A HELD BOUND MOVES ONLY BY ITS NAMED CAUSE: FR-T617-1 raises the HELD low end by exactly the band w x (D - t) of
      each named landing door, only where the source's deduction high is w x face height (the full face) and the band
      is below it; the high and the class stay; the material binding reads on those lines are listed as re-read.
  (f) NO OWNING LINE, NO WIRE (R-T619-1 (g)): ties / bed-joint strip (no candidate code, families B9-06 / B9-07
      proposed), the porch skirting (scope for the Lead) and a worker-only figure the Checker did not name as a fix row
      are listed with their figures, never placed on a guessed line, never 0; strip figures on walls whose area stays
      HELD (F-C-T615-1) carry the parent's HELD cause.
  (g) Every line V15 does not write is identical to the V14 overlay; totals move only on the keys V15 writes.
Rebuild: `python3 -I research/agents_t629/manifest_v15.py` (`--check`).
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
T619_DIR = ROOT / "research/agents_t619"
if str(T619_DIR) not in sys.path:
    sys.path.insert(0, str(T619_DIR))

import manifest_v14 as M14                                            # noqa: E402  (R-T619-1, read only)

M13, M11, M9, OV = M14.M13, M14.M11, M14.M9, M14.OV
D, S = M14.D, M14.S

SCHEMA = "URBAN_T629_WIRING_MANIFEST_V15"
RULE = "R-T629-1"
OUT_JSON = HERE / "out/WIRING_MANIFEST_V15.json"
IN = {
    "T615": ROOT / "research/agents_t615/out/SUMMARY_T615.json",
    "T615_WALLS": ROOT / "research/agents_t615/out/WALLS_015_T615.csv",
    "T615_ACC": ROOT / "research/agents_t615/out/ACCESSORIES_015_T615.csv",
    "T617": ROOT / "research/agents_t617/out/T617_HEAD_BOUNDS.json",
    "T556": ROOT / "research/agents_t556/out/T556_PLASTER_HEIGHT.json",
    "T618": ROOT / "research/agents_t618/out/T618_RESIDUALS.json",
    "T622": ROOT / "research/agents_t622/out/WALL_TILE_REMEASURE_T622.json",
    "V4": ROOT / "research/agents_t549/WIRING_MANIFEST_V4.json",
    "V6": ROOT / "research/agents_t558/WIRING_MANIFEST_V6.json",
    "V14": T619_DIR / "out/WIRING_MANIFEST_V14.json",
    "V14_CODE": T619_DIR / "manifest_v14.py",
}
PINS = {
    "T615": "6192fe79c09f9a203f8702387c7ad0ec3651fd86d56ac85f4b9014b6f783c8dc",
    "T615_WALLS": "4811f105711ad7112cef72c4de7bf186b8122b123fbea58170b1ec2b382e12e0",
    "T615_ACC": "87a1d4884cf70e028e46180914df61e23f939cb6f694ab936d7f4814fae79a2d",
    "T617": "883043d7ae606f37384d9071804f1aa0ac8a331fa854adde53ccc39646caaf3d",
    "T556": "8169a1953c386ccab7bbd9283404c100dc9d8105e6c10b7244593c9af442cd84",
    "T618": "3ca6790cf6378e2221d57fabbb7b775566fd27a0fea80b0b18190dcc8a0ef49f",
    "T622": "9750dad42874b7214cca2476f859911f26243a1b6442241ecd68dbdb58b151f3",
    "V4": "b0a8c6736122522e44690f9b49d2781eb1508cf8be3514f472cc169d5e5fc387",
    "V6": "b44b919e4ef749e7d283da6d080e1a806f590a9eba9ef474eeb833c23c78cfe9",
    "V14": "a8409ce1286fef3cf39a7129d7d97839e5ae73b911bfaf0ac3b3d84e2834c959",
    "V14_CODE": "4b31afc68bd31ef64deece60604b2af0ee90e65d2a45de250b5efcf1ca81a901",
}

# R-T629-1 (a): board MERGED verdicts at claim (2026-11-08T11:01Z; Verifier text abridged, full text on BOARD.md)
MERGED = {
    "T-615": {"merge": "b8265219",
              "verdict": "BOARD T-615 VERIFIER 2026-11-08T08:21Z: GATE A PASS; rulebook 1.1.0 UPC-BLACK-BLOCK-001 "
                         "confirmed_modules_m 0.15 = 0.40 x 0.20 (Q-80 A verbatim); own checks: 1 / (0.40 x 0.20) = "
                         "12.5 / m2; 15 wall bases 175.871 (low 175.531) -> units 2,198.3875 (low 2,194.1375) AGREE; "
                         "panel 0.0110625 m3 / m2 -> 1.945573 (low 1.941812) AGREE; cement x 8, sand x 1.1 AGREE; ties "
                         "AGREE; drawing search: no 15 cm face printed. Statuses ASSUMED - OWNER-APPROVED; waste / "
                         "procurement HELD; F-C-T615-1: GF-W22 / 2F-W08 strip carries the parent's HELD cause"},
    "T-617": {"merge": "44ee93d5",
              "verdict": "BOARD T-617 VERIFIER 2026-11-08T04:58Z: soffits GF 3.70 / 1F 3.40 / 2F 3.75 (own DXF read, "
                         "B14 / B7 20 x 75, B2 20 x 40); FR-T617-1 band 1.00 x (D - 0.16) = 0.59 / 0.59 / 0.24 m2 AGREE "
                         "(for the plaster wiring T-558); head DRAWING-BOUNDED above, low end HELD"},
    "T-618": {"merge": "85a473ce",
              "verdict": "BOARD T-618 VERIFIER 2026-11-08T06:02Z: 0 ENGINE_WRONG; FR-T618-1 (statement restatement, "
                         "lane I) and FR-T618-2 (porch scope, Lead) accepted; E1 +1.00 porch walled 3.50 lm AGREE "
                         "(own read), ENGINE_OMISSION CANDIDATE, scope HELD (never 0)"},
    "T-620": {"merge": "91b73cd8",
              "verdict": "BOARD T-620 VERIFIER 2026-11-08T09:59Z: statement V11 + scorecard V11; no quantity moved"},
    "T-621": {"merge": "T-621 engine merge (Verifier 2026-11-08T08:01Z)",
              "verdict": "BOARD T-621 VERIFIER 2026-11-08T08:01Z: B3 floor tile rows to evidence; no class or "
                         "quantity moved"},
    "T-622": {"merge": "31fe39db",
              "verdict": "BOARD T-622 VERIFIER 2026-11-08T10:00Z: own re-measure GF-07 pantry faces 10.500 m x 3.65 = "
                         "38.325 - W09 2.25 - W10 1.50 - door 2.20 = 32.375 m2 AGREE worker; engine line 32.3422 (walk "
                         "face 10.491) 0.0328 m2 short: ENGINE_WRONG confirmed -> fix row for an integration package; "
                         "GF-14 +0.086709 ENGINE_WRONG stays worker DRAWING-CONFIRMED (not re-measured)"},
    "T-623": {"merge": "T-623 engine merge (Verifier 2026-11-08T09:59Z)",
              "verdict": "BOARD T-623 VERIFIER 2026-11-08T09:59Z: B10 unknown rows to evidence; F-T623-1 split "
                         "correction for the statement; no candidate quantity moved"},
}
NO_ROW = {
    "T-618": "FR-T618-1 restates two statement residuals as ranges (stair skirting (-inf, 0.710951], rails (-inf, "
             "0.226]): statement only (folded in V11, T-620); FR-T618-2 porch skirting: no owning line (listed held)",
    "T-620": "reconciled statement V11 + scorecard V11: reads lines, moves none",
    "T-621": "B3 floor tile rows to evidence: no class or quantity moved",
    "T-623": "B10 beam / column rows to evidence; F-T623-1 is a split correction inside the statement, no line moves",
}
NOT_MERGED = {"T-624": "TODO at claim (beam-end open items)", "T-628": "TODO at claim (footing / lift-wall rows)"}

EVID_ASSUMED = "ASSUMED — OWNER-APPROVED"
EVIDENCE = tuple(M9.EVIDENCE) + (EVID_ASSUMED,)
RULE_BLOCK = "UPC-BLACK-BLOCK-001 1.1.0 (rulebook 1.1.0; Q-80 A owner 2026-11-07)"
MODULE = (Decimal("0.40"), Decimal("0.20"))                  # installed 40 x 20 (Q-80 A)
FACE = (Decimal("0.39"), Decimal("0.19"))                    # face 39 x 19 + 10 mm joint (owner 2026-10-29)
THICK = Decimal("0.15")
UNITS_PER_M2 = 1 / (MODULE[0] * MODULE[1])                   # 12.5
PANEL_M3_PER_M2 = THICK * (1 - FACE[0] * FACE[1] * UNITS_PER_M2)   # 0.0110625
CEMENT_BAGS_PER_M3, SAND_M3_PER_M3 = Decimal("8"), Decimal("1.1")   # UPC-BLACK-MORTAR-001 (T-615 basis)
EXCLUDED_WALLS = {"GF-W22": "D-27 area conflict on its parent (T-488), own HELD",
                  "2F-W08": "D-39 2F storey (T-488), own HELD"}
UNITS, MORTAR = ("MAS.UNITS.BLACK", "pcs"), ("MAS.MORTAR.BLACK", "m3")
P498, P563 = "T-498", "T-563"
P_PANTRY = "WALL_TILE_PANTRY (T-622 FR-T622-1)"
PANTRY_LINE = "L-f5c5a1a9c9ee2b644cb5"                       # FIN.WALL.TILE GF-RC06FED#WALL_TILE:GF-07
PANTRY_ROW = 46                                              # T-622 row 'GF-07 open pantry'
PANTRY_PARTS = [("west face 4.450 + column 2FAE return 0.050", "4.500"), ("north face", "3.000"),
                ("south face", "3.000")]
PANTRY_H = "3.65"
PANTRY_DEDUCT = [("W09 1.50 x 1.50", "2.25"), ("W10 1.00 x 1.50", "1.50"), ("door 1.00 x 2.20", "2.20")]
LANDING_W = Decimal("1.00")                                  # landing door width (T-608 / T-617)
WRITES = {"MAS.UNITS.BLACK|pcs", "MAS.MORTAR.BLACK|m3", "FIN.PLASTER|m2", "FIN.WALL.TILE|m2"}
RULINGS_V15 = [
    {"layer": "MAS.MORTAR", "host_re": r"^(GF|1F)-WALLS:walls t=0\.15$", "sources": ["T-498", "T-498:perimeter"],
     "ruling": "B9-04 perimeter joint mortar of the 0.15 m black walls is its own producer key beside the panel "
               "bed-joint mortar, never inside it (R-T520-1; the T-498 step 6 / 0.20 m ruling, extended by T-615)",
     "fix_row": "T-498 + V15 FR-T615-3 (perimeter, 0.15 m hosts) carries both lines apart"},
]


class ManifestError(Exception):
    pass


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pins():
    for k, pin in PINS.items():
        if sha256(IN[k]) != pin:
            raise ManifestError(f"PIN: {IN[k].name} sha256 {sha256(IN[k])[:8]} is not the pinned {pin[:8]}")


def q6(x):
    return Decimal(x).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def require_merged(task, merged=None):
    try:
        return M14.require_merged(task, MERGED if merged is None else merged)
    except M14.ManifestError as e:
        raise ManifestError(str(e)) from None


def no_row_sources(merged=None, no_row=None, not_merged=None):
    try:
        return M14.no_row_sources(MERGED if merged is None else merged, NO_ROW if no_row is None else no_row,
                                  NOT_MERGED if not_merged is None else not_merged)
    except M14.ManifestError as e:
        raise ManifestError(str(e)) from None


def row(pkg, fix_row, kind, line_id, before, after, evidence, verdict, source=None, **kw):
    """M9.row with the WORKFLOW_CONTROLS s.5 status ASSUMED — OWNER-APPROVED allowed; source = the overlay origin."""
    if evidence not in EVIDENCE:
        raise ManifestError(f"{line_id}: evidence status {evidence!r} is not a WORKFLOW_CONTROLS s.5 status")
    try:
        r = M9.row(pkg, fix_row, kind, line_id, before, after,
                   "HELD" if evidence == EVID_ASSUMED else evidence, verdict, **kw)
    except M9.ManifestError as e:
        raise ManifestError(str(e)) from None
    r["evidence"]["status"] = evidence
    if source:
        r["source"] = source
    return r


# ---- R-T629-1 (c)/(d): T-615 0.15 m black-block material lines -------------------------------------------------

def walls_by_host(walls, v4):
    """the T-615 wall rows grouped on the V4 block_module hosts; every host / wall pairing must agree."""
    hosts = {h["host_line"]: h for h in v4["block_module"]["host_lines"]}
    out = {}
    for w in walls:
        if w["wall_id"] in EXCLUDED_WALLS:
            raise ManifestError(f"{w['wall_id']}: kept HELD by its own cause ({EXCLUDED_WALLS[w['wall_id']]}): "
                                "it never enters (R-T629-1 (c))")
        if w["line_id"] not in hosts:
            raise ManifestError(f"{w['wall_id']}: host {w['line_id']} is not a V4 block_module host line")
        out.setdefault(w["line_id"], []).append(w)
    for lid, h in hosts.items():
        got = sorted(w["wall_id"] for w in out.get(lid, []))
        if got != sorted(h["walls"]):
            raise ManifestError(f"{lid}: T-615 walls {got} are not the V4 host walls {sorted(h['walls'])}")
    return out, hosts


def wall_quantities(w):
    """R-T629-1 (c)(2): re-derive from the rule; the source's printed figures must agree to their print precision."""
    mb, mbl = D(w["material_base_m2"]), D(w["material_base_low_m2"])
    if mbl > mb or mbl <= 0:
        raise ManifestError(f"{w['wall_id']}: low base {S(mbl)} is not within 0 .. {S(mb)}")
    q = {"units": mb * UNITS_PER_M2, "units_low": mbl * UNITS_PER_M2,
         "panel": mb * PANEL_M3_PER_M2, "panel_low": mbl * PANEL_M3_PER_M2,
         "per_lo": D(w["perimeter_low_m3"]), "per_fig": D(w["perimeter_figure_m3"]),
         "per_hi": D(w["perimeter_high_m3"])}
    for k, src, tol in (("units", "units_nr", "0.00005"), ("units_low", "units_nr_low", "0.00005"),
                        ("panel", "panel_mortar_m3", "0.0000005"), ("panel_low", "panel_mortar_m3_low", "0.0000005")):
        if abs(q[k] - D(w[src])) > D(tol):
            raise ManifestError(f"{w['wall_id']}: {src} {w[src]} does not re-derive from the rule ({S(q[k])})")
    if not (q["per_lo"] <= q["per_fig"] <= q["per_hi"]):
        raise ManifestError(f"{w['wall_id']}: perimeter {S(q['per_lo'])} / {S(q['per_fig'])} / {S(q['per_hi'])} "
                            "is not low <= figure <= high")
    q["held_pieces"] = w.get("perimeter_held_pieces") or ""
    return q


def _staged(idx, host_elem, code_unit):
    hits = [k for k, l in idx.items() if (l["item_code"], l.get("unit")) == code_unit
            and l["element_id"] == "MATERIAL:" + host_elem and l["class"] != "EXCLUDED"]
    if len(hits) != 1:
        raise ManifestError(f"{code_unit[0]} on MATERIAL:{host_elem}: {len(hits)} live lines, expected one staged")
    return hits[0]


def _ranged(pkg, fix, lid, before, lo, hi, elem, code_unit, verdict, beside, open_high=False, source=None):
    """R-T629-1 (d): line at lo (+ companion HELD 0 .. hi - lo, or 0 .. open when named pieces stay HELD)."""
    if lo <= 0:
        raise ManifestError(f"{lid}: a restated quantity {S(lo)} must be positive (HELD is never 0)")
    if hi < lo:
        raise ManifestError(f"{lid}: range {S(lo)} .. {S(hi)} is reversed")
    rows = []
    b = dict(beside)
    if hi > lo or open_high:
        b["range"] = f"{S(lo)} .. {S(hi)}" + (" + named pieces HELD (open)" if open_high else "") + \
                     " (line at the low end; companion HELD; R-T629-1 (d))"
    if before is None:
        rows.append(row(pkg, fix, "ADD", lid, None, M9.released(float(lo)), EVID_ASSUMED, verdict, source=source,
                        code=code_unit[0], unit=code_unit[1], elem=elem, beside=b))
    else:
        rows.append(row(pkg, fix, "SET", lid, before, M9.released(float(lo)), EVID_ASSUMED, verdict, source=source,
                        beside=b))
    if hi > lo or open_high:
        celem = elem + f"#{fix}:RANGE"
        rows.append(row(pkg, fix, "ADD", f"NEW:{code_unit[0]}:{celem}", None,
                        M9.held(0.0, None if open_high else float(hi - lo)), EVID_ASSUMED, verdict, source=source,
                        code=code_unit[0], unit=code_unit[1], elem=celem,
                        beside={"range_of": lid, "low": S(lo), "high_stated": S(hi), "open": open_high,
                                "rule": "R-T629-1 (d): a range is never a point"}))
    return rows


def block015_rows(t615, walls, v4, idx, merged=None, source="T-615"):
    """FR-T615-1 / -2 / -3 (+ -4 beside): chained steps for the T-498 package on the 6 V4 hosts."""
    src = require_merged(source, merged)
    if not t615["rule"].startswith("UPC-BLACK-BLOCK-001 1.1.0"):
        raise ManifestError(f"T-615 rule {t615['rule']!r} is not UPC-BLACK-BLOCK-001 1.1.0 (R-T629-1 (c)(1))")
    mod = t615["module_015"]
    if [D(str(x)) for x in mod["installed_m"]] != list(MODULE) or D(str(mod["units_per_m2"])) != UNITS_PER_M2:
        raise ManifestError(f"T-615 module {mod['installed_m']} / {mod['units_per_m2']} is not 40 x 20 / 12.5")
    if sorted(t615["excluded"]) != sorted(EXCLUDED_WALLS):
        raise ManifestError(f"T-615 excluded walls {sorted(t615['excluded'])} are not {sorted(EXCLUDED_WALLS)}")
    groups, hosts = walls_by_host(walls, v4)
    rows, per_host = [], []
    tot = {k: Decimal(0) for k in ("units", "units_low", "panel", "panel_low", "per_lo", "per_fig", "per_hi")}
    for hid in sorted(groups):
        host = idx.get(hid)
        h = hosts[hid]
        if host is None or host["item_code"] != "MAS.BLOCK" or host["element_id"] != h["element_id"] \
                or "t=0.15" not in host["element_id"] or not host["element_id"].endswith("_BLACK"):
            raise ManifestError(f"{hid}: not the 0.15 m black MAS.BLOCK host {h['element_id']}")
        if host["class"] != "RELEASED" or D(host["measured_net"]) != D(str(h["contract_m2"])):
            raise ManifestError(f"{hid}: host {host['class']} {host['measured_net']} is not the V4 contract "
                                f"{h['contract_m2']}")
        ws = groups[hid]
        contract = sum((D(w["contract_m2"]) for w in ws), Decimal(0))
        if abs(contract - D(host["measured_net"])) > D("0.00005"):
            raise ManifestError(f"{hid}: walls re-add to {S(contract)} m2, host line {host['measured_net']} "
                                "(R-T629-1 (c)(3))")
        qs = [wall_quantities(w) for w in ws]
        a = {k: sum((q[k] for q in qs), Decimal(0)) for k in tot}
        for k in tot:
            tot[k] += a[k]
        held_pieces = "; ".join(f"{w['wall_id']}: {q['held_pieces']}" for w, q in zip(ws, qs) if q["held_pieces"])
        statuses = sorted({w["area_status"] for w in ws})
        common = {"host": hid, "walls": sorted(w["wall_id"] for w in ws), "area_status": statuses,
                  "rule": RULE_BLOCK, "was": "HELD blank by name (R-T533-1, V4 block_module)",
                  "why_assumed": "owner company rule (Q-80 A), not printed: weakest of the area statuses and the "
                                 "module status"}
        u_lid, m_lid = _staged(idx, h["element_id"], UNITS), _staged(idx, h["element_id"], MORTAR)
        for lid in (u_lid, m_lid):
            st = OV.state(idx[lid])
            if st["class"] != "HELD" or st["held_low"] is not None or st["held_high"] is not None:
                raise ManifestError(f"{lid}: {st} is not HELD blank: stale or already restated (R-T629-1 (c)(4))")
        u_lo, u_hi = q6(a["units_low"]), q6(a["units"])
        p_lo, p_hi = q6(a["panel_low"]), q6(a["panel"])
        rows += _ranged(P498, "FR-T615-1", u_lid, OV.state(idx[u_lid]), u_lo, u_hi, idx[u_lid]["element_id"], UNITS,
                        src["verdict"], dict(common, item="units, theoretical (procurement HELD: waste not sourced)",
                                             derivation=f"{S(sum((D(w['material_base_m2']) for w in ws), Decimal(0)))}"
                                                        f" m2 x {S(UNITS_PER_M2)} / m2"), source="T-498")
        rows += _ranged(P498, "FR-T615-2", m_lid, OV.state(idx[m_lid]), p_lo, p_hi, idx[m_lid]["element_id"],
                        MORTAR, src["verdict"],
                        dict(common, item="panel bed / head joint mortar",
                             derivation=f"base x {S(PANEL_M3_PER_M2)} m3 / m2 (0.15 x (1 - 0.39 x 0.19 x 12.5))",
                             cement_bags_50kg=f"{S(q6(p_lo * CEMENT_BAGS_PER_M3))} .. {S(q6(p_hi * CEMENT_BAGS_PER_M3))}",
                             sand_m3_loose=f"{S(q6(p_lo * SAND_M3_PER_M3))} .. {S(q6(p_hi * SAND_M3_PER_M3))}"),
                        source="T-498")
        pl, pf, ph = a["per_lo"], a["per_fig"], a["per_hi"]
        rows += _ranged(P498, "FR-T615-3", f"NEW:MAS.MORTAR.BLACK:PERIMETER:{hid}", None, pl, ph, h["element_id"],
                        MORTAR, src["verdict"],
                        dict(common, item="perimeter joint mortar (own key beside the panel)", figure_m3=S(pf),
                             held_pieces=held_pieces or None,
                             cement_bags_50kg=f"{S(q6(pl * CEMENT_BAGS_PER_M3))} .. {S(q6(ph * CEMENT_BAGS_PER_M3))}",
                             sand_m3_loose=f"{S(q6(pl * SAND_M3_PER_M3))} .. {S(q6(ph * SAND_M3_PER_M3))}",
                             rule_perimeter="R-T520-1 on the register module"),
                        open_high=bool(held_pieces), source="T-498:perimeter")
        per_host.append({"host": hid, "element": h["element_id"], "walls": sorted(w["wall_id"] for w in ws),
                         "contract_m2": S(contract), "units": [S(u_lo), S(u_hi)], "panel_m3": [S(p_lo), S(p_hi)],
                         "perimeter_m3": [S(pl), S(pf), S(ph)], "perimeter_open": bool(held_pieces),
                         "lines": {"units": u_lid, "panel": m_lid}})
    # R-T629-1 (c): totals re-add to the source's summary (its 4 / 6 dp prints)
    chk = [("units_low", t615["units_nr"]["low"], "0.0001"), ("units", t615["units_nr"]["theoretical"], "0.0001"),
           ("panel_low", t615["panel_mortar_m3"]["low"], "0.000001"),
           ("panel", t615["panel_mortar_m3"]["material_base"], "0.000001"),
           ("per_lo", t615["perimeter_mortar_m3"]["low"], "0.000001"),
           ("per_fig", t615["perimeter_mortar_m3"]["figure"], "0.000001"),
           ("per_hi", t615["perimeter_mortar_m3"]["high"], "0.000001")]
    for k, stated, tol in chk:
        if abs(tot[k] - D(str(stated))) > D(tol):
            raise ManifestError(f"T-615 {k}: hosts re-add to {S(tot[k])}, the source states {stated}")
    return rows, per_host, tot


def held_hosts_untouched(idx_after, v4, written):
    """the material lines of hosts the source keeps HELD (no '#..._BLACK' host of V4) stay HELD blank, unwritten."""
    v4_elems = {"MATERIAL:" + h["element_id"] for h in v4["block_module"]["host_lines"]}
    out = []
    for k, l in sorted(idx_after.items()):
        if (l["item_code"], l.get("unit")) in (UNITS, MORTAR) and "t=0.15" in l["element_id"] \
                and l["element_id"] not in v4_elems and not k.startswith("NEW:"):
            if k in written or l["class"] != "HELD" or l["held_low"] is not None or l["held_high"] is not None:
                raise ManifestError(f"{k}: a 0.15 m material line outside the 6 hosts moved")
            out.append({"line": k, "item": l["item_code"], "element": l["element_id"], "state": "HELD blank"})
    return out


def accessories_listed(t615, acc):
    """R-T629-1 (f): ties / strip have no candidate code: listed with figures; F-C-T615-1 parents' causes kept."""
    ties = [a for a in acc if a["item"] == "MAS.TIE.SHARMAT"]
    strip = [a for a in acc if a["item"] == "MAS.MESH.BED_JOINT"]
    nt = sum(int(a["now"]) for a in ties)
    sl = sum((D(a["now"]) for a in strip), Decimal(0))
    ts, ss = t615["ties_pcs"], t615["bed_joint_strip_ml"]
    if nt != ts["end_restated"] + ts["interior_restated"] or \
            ts["ledger_measured_before"] + nt != ts["ledger_measured_after"]:
        raise ManifestError(f"ties: rows {nt} do not re-add to {ts}")
    if sl != D(str(ss["restated"])) or D(str(ss["ledger_measured_before"])) + sl != D(str(ss["ledger_measured_after"])):
        raise ManifestError(f"strip: rows {S(sl)} do not re-add to {ss}")
    conditional = []
    for a in strip:
        if a["wall_id"] in EXCLUDED_WALLS:
            conditional.append({"wall": a["wall_id"], "strip_ml": a["now"],
                                "parent_held": EXCLUDED_WALLS[a["wall_id"]],
                                "reads": "conditional on the parent's HELD area (F-C-T615-1), never an unconditional "
                                         "point"})
    for a in ties:
        if a["wall_id"] in EXCLUDED_WALLS:
            conditional.append({"wall": a["wall_id"], "ties_pcs": a["now"],
                                "parent_held": EXCLUDED_WALLS[a["wall_id"]],
                                "reads": "count by course 6 .. 6 on 3.75 .. 3.85 m (T-615), the wall area stays HELD"})
    return {"MAS.TIE.SHARMAT|pcs": {"restated": nt, "ledger": f"{ts['ledger_measured_before']} -> "
                                                              f"{ts['ledger_measured_after']} measured",
                                    "still_held_junctions": ts["still_held_junctions"]},
            "MAS.MESH.BED_JOINT|m.l": {"restated": S(sl), "walls": len(strip),
                                       "ledger": f"{ss['ledger_measured_before']} -> {ss['ledger_measured_after']}"},
            "conditional_on_parent_held": conditional,
            "wired": "NO: no candidate line carries MAS.TIE.SHARMAT / MAS.MESH.BED_JOINT (families B9-06 / B9-07 "
                     "proposed, no registry row); listed for the T-498 materials package, never 0",
            "cement_sand": "beside the mortar lines (UPC-BLACK-MORTAR-001 x 8 bags / x 1.1 m3 per m3): purchasing "
                           "group keys, not candidate lines (V3 'sand is a material-group key'); waste HELD"}


# ---- R-T629-1 (b)/(e): FR-T617-1 on the T-563 plaster lines ------------------------------------------------------

def band_rows(t617, t556, t563_ops, merged=None, source="T-617"):
    src = require_merged(source, merged)
    ops = {op["line_id"]: op for op in t563_ops if op["kind"] == "SET"}
    t556r = {r["line_id"]: r for r in t556["rows"]}
    rows, out = [], []
    for r in t617["rows"]:
        q = r["q72_plaster_for_T558"]
        plaster = [l["line_id"] for l in r["candidate_faces"]["lines"] if l["item_code"] == "FIN.PLASTER"]
        if len(plaster) != 1:
            raise ManifestError(f"{r['opening']}: no single plaster line")
        lid = plaster[0]
        op = ops.get(lid)
        if op is None:
            raise ManifestError(f"{lid}: no T-563 SET on the line: FR-T617-1 has no package to chain in")
        door = r["opening"].split("(")[1].rstrip(")")
        n = t556r[lid]["new"]
        od = [o for o in n["openings"] if o["id"] == door]
        if len(od) != 1:
            raise ManifestError(f"{lid}: T-556 deducts {door} {len(od)} times")
        face_h = D(q["face_h_m"])
        band = D(q["always_plastered_above_head_m2"])
        if band != LANDING_W * D(q["check_D_minus_t"]):
            raise ManifestError(f"{lid}: band {S(band)} is not w x (D - t) = {S(LANDING_W)} x {q['check_D_minus_t']}")
        if D(od[0]["lo"]) != 0 or D(od[0]["hi"]) != LANDING_W * face_h:
            raise ManifestError(f"{lid}: T-556 deducts {door} {od[0]['lo']} .. {od[0]['hi']}, not 0 .. w x "
                                f"{S(face_h)}: the band does not apply (R-T629-1 (e))")
        if not (0 < band < LANDING_W * face_h) or D(q["deduction_cap_m2"]) != LANDING_W * face_h - band:
            raise ManifestError(f"{lid}: cap {q['deduction_cap_m2']} is not w x face - band")
        a = op["after"]
        if D(a["held_low"]) != D(n["net_lo"]) or D(a["held_high"]) != D(n["net_hi"]) or a["class"] != "HELD":
            raise ManifestError(f"{lid}: the T-563 after {a} is not the T-556 frame {n['net_lo']} .. {n['net_hi']}")
        lo, hi = D(a["held_low"]) + band, D(a["held_high"])
        if lo > hi:
            raise ManifestError(f"{lid}: the low end {S(lo)} would pass the high {S(hi)}")
        rows.append(row(P563, "FR-T617-1", "SET", lid, dict(a), M9.held(float(lo), float(hi)), "HELD", src["verdict"],
                        source=P563,
                        beside={"room": op.get("note"), "door": door, "storey": r["storey"],
                                "member": f"{r['member_over_door']['mark']} D {r['member_over_door']['depth_m']}",
                                "band_m2": S(band), "deduction_before": f"0 .. {od[0]['hi']}",
                                "deduction_after": f"0 .. {q['deduction_cap_m2']}",
                                "low": f"{a['held_low']} + {S(band)} = {S(lo)}", "high": "unchanged",
                                "rule": "Q-72 (plaster to the slab underside) + R-T617-1; R-T629-1 (e)",
                                "chained_after": op["op_id"]},
                        note="R-T629-1 (b): chained inside the T-563 package"))
        out.append({"line": lid, "room": op.get("note"), "door": door, "band_m2": S(band),
                    "before": [S(D(a["held_low"])), S(hi)], "after": [S(lo), S(hi)]})
    return rows, out


def binding_reads(v6, band):
    """R-T629-1 (e): the V6 material binding reads on the moved plaster lines (re-read at Gate B, named)."""
    moved = {b["line"]: b for b in band}
    out = []
    for b in v6["bindings"]["rows"]:
        if b["line_id"] in moved:
            ex = b["expected_after"]["held_read"]
            out.append({"key": b["key"], "expected_after_v6": ex, "reads_after_v15": moved[b["line_id"]]["after"]})
    return out


# ---- T-622: pantry wall tile --------------------------------------------------------------------------------------

def pantry_row(t622, idx, merged=None, source="T-622", taken=()):
    src = require_merged(source, merged)
    if PANTRY_LINE in taken:
        raise ManifestError(f"{PANTRY_LINE}: written by another package: chain it there (R1)")
    line = idx.get(PANTRY_LINE)
    if line is None or (line["item_code"], line.get("unit")) != ("FIN.WALL.TILE", "m2") \
            or not line["element_id"].endswith("WALL_TILE:GF-07") or line["class"] != "RELEASED":
        raise ManifestError(f"{PANTRY_LINE}: not the released GF-07 wall tile line")
    r = next(x for x in t622["rows"] if x["row"] == PANTRY_ROW)
    engine, own = -D(r["stated"]), -D(r["own"])
    if D(line["measured_net"]) != engine:
        raise ManifestError(f"{PANTRY_LINE}: line {line['measured_net']} is not the source's engine {S(engine)} "
                            "(stale or already corrected)")
    faces = sum((D(v) for _, v in PANTRY_PARTS), Decimal(0))
    hand = faces * D(PANTRY_H) - sum((D(v) for _, v in PANTRY_DEDUCT), Decimal(0))
    if hand != own:
        raise ManifestError(f"pantry: Checker parts give {S(hand)}, the source's own figure is {S(own)}")
    return row(P_PANTRY, "FR-T622-1", "SET", PANTRY_LINE, OV.state(line), M9.released(float(own)), "VERIFIED",
               src["verdict"],
               beside={"faces_m": [{"what": n, "m": v} for n, v in PANTRY_PARTS], "faces_total_m": S(faces),
                       "height_m": PANTRY_H, "deductions_m2": [{"what": n, "m2": v} for n, v in PANTRY_DEDUCT],
                       "hand": f"{S(faces)} x {PANTRY_H} - {S(sum((D(v) for _, v in PANTRY_DEDUCT), Decimal(0)))} = "
                               f"{S(hand)}",
                       "change_m2": S(own - engine), "who_is_right": "ENGINE_WRONG (walk face 10.491 vs drawn 10.500)",
                       "rule": "Q-37 A pantry wet + UP-PANTRY-003 host walls full height; open edge tiles nothing "
                               "(UP-PANTRY-002)"},
               note="room line re-measured by the Checker; the B4 family stays PARTIALLY VERIFIED")


# ---- overlay ------------------------------------------------------------------------------------------------------

def v14_state():
    """the T-619 build up to its overlay (read only), so V15 steps from the exact V14 state."""
    M14.pins()
    t608, t610, t614 = M14._json(M14.IN["T608"]), M14._json(M14.IN["T610"]), M14._json(M14.IN["T614"])
    idx, order13, rul, after13, rep13, t584 = M14.v13_state()
    lift = M14.lift_rows(t608, after13)
    over, _ = M14.overlap_rows(t610, t614, after13)
    end, _ = M14.end_rows(t614, after13, taken={r["line_id"] for r in over})
    lint = M14.lintel_rows(after13)
    order14 = order13 + [(M14.P_LIFT, lift), (M14.P_OVER, over), (M14.P_END, end), (M14.P_LINT, lint)]
    rul14 = list(rul) + M14.end_rulings(t614, after13, end)
    after14, rep14 = OV.apply(idx, order14, rul14)
    return idx, order14, rul14, after14, rep14, t584


def chain_into(order, pkg, rows):
    """R-T629-1 (b): append rows to the named package (kept in place in the order); refused when it is absent."""
    if not rows:
        return order
    names = [n for n, _ in order]
    if pkg not in names:
        raise ManifestError(f"{pkg}: no such package in the order: a chained step needs its owning package")
    out = []
    for n, ops in order:
        out.append((n, list(ops) + [dict(r, package=n) for r in rows] if n == pkg else ops))
    return out


def _state_after(idx, order, upto):
    names = [n for n, _ in order]
    return OV.apply(idx, order[:names.index(upto) + 1], [])[0] if upto in names else None


def build():
    pins()
    t615, walls, acc = _json(IN["T615"]), _csv(IN["T615_WALLS"]), _csv(IN["T615_ACC"])
    t617, t556, t618, t622 = _json(IN["T617"]), _json(IN["T556"]), _json(IN["T618"]), _json(IN["T622"])
    v4, v6, v14j = _json(IN["V4"]), _json(IN["V6"]), _json(IN["V14"])
    idx, order14, rul14, after14, rep14, t584 = v14_state()
    if len(after14) != v14j["overlay"]["lines"]["after_v14"]:
        raise ManifestError("V14 state rebuild differs from the committed V14 line count")
    last = {}
    for r in v14j["rows"]:                       # a chained line (B27) is checked on its last step
        if r["kind"] in ("ADD", "SET"):
            last[r["line_id"]] = r
    for r in last.values():
        if not OV.same_state(OV.state(after14[r["line_id"]]), r["after"]):
            raise ManifestError(f"{r['line_id']}: V14 rebuild differs from the committed V14 row")
    t14 = OV.totals(after14)
    written14 = {op["line_id"] for _, ops in order14 for op in ops}
    sources, refused = no_row_sources()
    # T-615 steps read the T-498 package's own after (the stage lines)
    after498 = _state_after(idx, order14, P498)
    blk, per_host, blk_tot = block015_rows(t615, walls, v4, after498)
    t563_ops = dict(order14)[P563]
    band, band_out = band_rows(t617, t556, t563_ops)
    pantry = pantry_row(t622, after14, taken=written14)
    rows15 = blk + band + [pantry]
    M9.validate_rows(rows15)
    order15 = chain_into(chain_into(order14, P498, blk), P563, band) + [(P_PANTRY, [pantry])]
    rul15 = list(rul14) + RULINGS_V15
    after15, rep = OV.apply(idx, order15, rul15)
    v15_lines = {r["line_id"] for r in rows15}
    others = sorted(k for k in set(after14) | set(after15) if k not in v15_lines and after14.get(k) != after15.get(k))
    if others:
        raise ManifestError(f"lines V15 does not write changed: {others[:5]}")
    t15 = OV.totals(after15)
    dt = OV.diff_totals(t14, t15)
    if set(dt) != WRITES:
        raise ManifestError(f"totals moved on {sorted(dt)}, V15 writes {sorted(WRITES)}")
    if any(c["status"] == "UNEXPLAINED" for c in rep["conflicts"]):
        raise ManifestError(f"unexplained conflicts: {[c for c in rep['conflicts'] if c['status'] == 'UNEXPLAINED']}")
    flagged = [r for r in rep["rows"] if r["status"] != "APPLIED"]
    v15_ops = {r["op_id"] for r in rows15}
    if any(r["op_id"] in v15_ops for r in flagged):
        raise ManifestError(f"a V15 row is not APPLIED: {[r for r in flagged if r['op_id'] in v15_ops]}")
    if len(flagged) != len([r for r in rep14["rows"] if r["status"] != "APPLIED"]):
        raise ManifestError("the flagged rows of V14 changed")
    untouched = held_hosts_untouched(after15, v4, v15_lines)
    # hand acceptance per family
    u14, u15 = t14["MAS.UNITS.BLACK|pcs"], t15["MAS.UNITS.BLACK|pcs"]
    m14, m15 = t14["MAS.MORTAR.BLACK|m3"], t15["MAS.MORTAR.BLACK|m3"]
    du = D(u15["released"]) - D(u14["released"])
    dm = D(m15["released"]) - D(m14["released"])
    u_lo = sum((D(h["units"][0]) for h in per_host), Decimal(0))
    u_hi = sum((D(h["units"][1]) for h in per_host), Decimal(0))
    p_lo = sum((D(h["panel_m3"][0]) for h in per_host), Decimal(0))
    p_hi = sum((D(h["panel_m3"][1]) for h in per_host), Decimal(0))
    pe_lo = sum((D(h["perimeter_m3"][0]) for h in per_host), Decimal(0))
    pe_hi = sum((D(h["perimeter_m3"][2]) for h in per_host), Decimal(0))
    if du != u_lo or dm != p_lo + pe_lo:
        raise ManifestError(f"released moved units {S(du)} / mortar {S(dm)}; rows say {S(u_lo)} / {S(p_lo + pe_lo)}")
    pl14, pl15 = t14["FIN.PLASTER|m2"], t15["FIN.PLASTER|m2"]
    band_sum = sum((D(b["band_m2"]) for b in band_out), Decimal(0))
    if D(pl15["held_low"]) - D(pl14["held_low"]) != band_sum or pl15["held_high"] != pl14["held_high"] \
            or pl15["released"] != pl14["released"] or pl15["held_n"] != pl14["held_n"]:
        raise ManifestError("FIN.PLASTER moved by more than the FR-T617-1 band on the held low end")
    wt14, wt15 = t14["FIN.WALL.TILE|m2"], t15["FIN.WALL.TILE|m2"]
    dpan = D(wt15["released"]) - D(wt14["released"])
    if dpan != D(pantry["beside"]["change_m2"]):
        raise ManifestError(f"FIN.WALL.TILE moved {S(dpan)}, the pantry row says {pantry['beside']['change_m2']}")
    status = {}
    for r in rep["rows"]:
        status.setdefault(r["package"], {}).setdefault(r["status"], 0)
        status[r["package"]][r["status"]] += 1
    t412 = M11.load_t412()
    nrows, _ = M11.nosing_ledger(t412, M11._json(M11.IN["T598"]))
    cen = M9.census_on(after15, M11.census_edges(t412, nrows), t584, {M9.E1_LINE: ("ST-03", "E1")})
    if cen["doubles"] or cen["orphans"]:
        raise ManifestError("stair census doubles / orphans after V15")
    table = []
    for r in rows15:
        b, a = r.get("before"), r.get("after")
        table.append({"row": r["row"], "package": r["package"], "kind": r["kind"], "line_id": r["line_id"],
                      "item": r.get("item_code") or after14.get(r["line_id"], after498.get(r["line_id"], {})).get(
                          "item_code"),
                      "before": None if b is None else {k: b[k] for k in OV.QFIELDS},
                      "after": None if a is None else {k: a[k] for k in OV.QFIELDS},
                      "evidence": r["evidence"]["status"]})
    p_open = sum(1 for h in per_host if h["perimeter_open"])
    return {
        "schema": SCHEMA, "rule": RULE, "task": "T-629", "candidate": M9.T580.CANDIDATE,
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in IN.values()},
        "sources_merged": {k: v["merge"] for k, v in MERGED.items()},
        "sources_no_row": sources, "sources_refused": refused,
        "supersedes": {
            "V4 block_module stage_material_lines (R-T533-1: the 12 staged lines on the 6 hosts stay HELD blank)":
                "superseded on those 12 lines by T-615 (Q-80 A, UPC-BLACK-BLOCK-001 1.1.0); the 0.15 m material lines "
                "of the hosts outside V4 (GF-W22 D-27 parent, 2F-W08 D-39, unclassed 0.15) stay HELD blank",
            "V14 sources_no_row T-617 ('FR-T617-1: no manifest line')":
                "superseded: on the T-563 plaster basis (Q-72, to the slab soffit) the band narrows the HELD low end; "
                "0.000 m2 holds only on the candidate's G1 faces (paint, and plaster before T-563)"},
        "held_not_wired": {
            "accessories_T615": accessories_listed(t615, acc),
            "FR-T618-2": {"what": "E1 +1.00 porch landing skirting, walled faces N 1.40 + E 0.90 + 0.80 + S 0.26 + "
                                  "0.14 = 3.50 lm (Checker own read)",
                          "state": "ENGINE_OMISSION CANDIDATE; scope (porch / outdoor skirting) HELD for the Lead; "
                                   "no owning line or item code ruled: not wired, never 0",
                          "source": t618["fix_rows"][1][:60]},
            "T-622 GF-14": {"what": "GF-14 wash lobby wall tile line +0.086709 m2 high (per-face rounding)",
                            "state": "worker DRAWING-CONFIRMED, not re-measured by the Checker and not named as a fix "
                                     "row: listed, not wired"},
        },
        "line_table": table,
        "rows": [dict(r) for r in rows15],
        "block_015": {
            "hosts": per_host,
            "units_pcs": {"v14": u14, "v15": u15,
                          "hand": f"{u14['released']} + {S(u_lo)} (6 hosts, low) = {u15['released']}; companion HELD "
                                  f"0 .. {S(u_hi - u_lo)} (1F-W13 D-1F-09 face 0 .. 0.34 m2 x 12.5)",
                          "range_after": f"{u15['released']} .. {S(D(u15['released']) + u_hi - u_lo)}"},
            "mortar_m3": {"v14": m14, "v15": m15,
                          "hand": f"{m14['released']} + panel {S(p_lo)} + perimeter {S(pe_lo)} = {m15['released']}; "
                                  f"companions panel 0 .. {S(p_hi - p_lo)}, perimeter bounded 0 .. {S(pe_hi - pe_lo)} "
                                  f"with {p_open} host(s) open (dome-opening pieces HELD by name, T-520)"},
            "summary_reread": {k: S(v) for k, v in blk_tot.items()},
            "held_hosts_untouched": untouched,
            "freelancer": "blockwork in m2 only (T-176): units / mortar UNRESOLVED (no comparison possible)",
        },
        "plaster_band": {"rows": band_out, "FIN.PLASTER|m2": {"v14": pl14, "v15": pl15},
                         "hand": " + ".join(b["band_m2"] for b in band_out) + f" = {S(band_sum)} m2 on the HELD low "
                                 "end; high, class and released unchanged",
                         "binding_reads_to_reread": binding_reads(v6, band_out)},
        "pantry": {"FIN.WALL.TILE|m2": {"v14": wt14, "v15": wt15}, "line": PANTRY_LINE,
                   "hand": pantry["beside"]["hand"], "change_m2": pantry["beside"]["change_m2"]},
        "overlay": {
            "lines": {"base": len(idx), "after_v14": len(after14), "after_v15": len(after15)},
            "order": [{"package": n, "ops": len(o), "status": status.get(n, {})} for n, o in order15],
            "flagged_rows": flagged,
            "stale": sum(r["status"] == "STALE" for r in rep["rows"]),
            "two_package_lines": 0,                     # OV.apply raises R1 otherwise
            "unexplained_conflicts": sum(c["status"] == "UNEXPLAINED" for c in rep["conflicts"]),
            "conflicts": [c for c in rep["conflicts"] if any(l in v15_lines for l in c["lines"])],
            "rulings_v15": RULINGS_V15,
            "other_lines_changed_vs_v14_overlay": others,
            "v15_vs_v14_totals": dt,
        },
        "stair_edge_census_after_v15": {"edges": cen["edges"], "doubles": len(cen["doubles"]),
                                        "orphans": len(cen["orphans"])},
        "findings": {
            "F-T629-1": "the T-563 Gate B package carries FR-T617-1 as chained steps on GF-08 / 1F-13 / 2F-01; its "
                        "V6 binding reads (T-454 bond coat etc.) on those lines must re-read the new low end at Gate B",
            "F-T629-2": "the T-498 Gate B package now releases the 0.15 m black units / mortar on the 6 hosts as "
                        "ASSUMED — OWNER-APPROVED; T-580 block_module_check (stage rows HELD) still holds for the "
                        "stage extract itself, the V15 steps chain after it",
        },
        "candidate_files_touched": 0, "released_quantities_changed": 0,
    }


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, default=str) + "\n"


def main(argv):
    text = dumps(build())
    if "--check" in argv:
        ok = OUT_JSON.exists() and OUT_JSON.read_text(encoding="utf-8") == text
        print("T-629 manifest V15: committed output", "is the rebuild" if ok else "DIFFERS from the rebuild")
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
