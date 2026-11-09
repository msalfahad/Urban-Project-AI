"""T-631 WIRING MANIFEST V16 + OVERLAY DRY RUN (R-T631-1; lane I, non-candidate, research only).

V16 carries the fix rows the Checker MERGED after V15 (T-629, cut 2026-11-08T11:14Z) into the overlay:
  - T-624 (MERGED 1e38add2, Verifier 11:58Z): FR-T624-1 GF B26 @ C25 drawn wedge +0.005245 m3, FR-T624-2 1F B19 @ C15
    drawn wedge +0.001064 m3 (own package: no earlier package writes either line), FR-T624-3 GF CB8 col-2 end gap
    +0.003405 m3 on L-7c1a1da8 (chained INSIDE the T-610 crossing-zone package, which already writes the line), and
    FR-T624-4: item (c) closes the F-T619-1 range: the B27 tip 0.001524 m2 lies inside the B27 rectangle and is billed
    once (Checker AGREE, companion 0): the V14 companion HELD 0 .. 0.001295 m3 leaves as EXCLUDED (chained in the same
    T-610 package that added it), never RELEASED 0. B10 66.392081 .. 66.393376 -> 66.401795 m3 (a point).
  - T-622 (MERGED 31fe39db, Verifier 10:00Z): FR-T622-2 GF-14 wash lobby wall tile 26.6544 -> 26.567691 m2 (open side
    on threshold 2DB 1.255652, face chain 8.243203 x 3.65 - 2 doors 0.80 x 2.20); worker DRAWING-CONFIRMED (the Checker
    did not re-measure GF-14): carried DRAWING-CONFIRMED, never VERIFIED.
  - T-625 (MERGED 47824e04, Verifier 12:59Z): FR-T625-1 row 0 round-stair footprint 6.124412 -> 6.137684 m2 (arc band
    4.044824 + run 2.09286; Checker own re-measure, ENGINE_WRONG chord flattening): the GF porcelain line
    L-7625f35c deducts the footprint, so it moves -0.013272 m2. Its two UNRESOLVED ranges enter as ranges, never points
    (R-T619-1 (c)): FR-T625-2 strings 0 .. 0.393843 m2 (0.05 bands beside the tread edges: stair structure / cladding
    or floor; if stair, out of the GF porcelain): the line at its low end (-0.393843) + companion HELD 0 .. 0.393843;
    FR-T625-3 1F slab-edge margin 0 .. 0.376 m2 beyond the void lines B74 / B75 (finish if the void-edge detail puts
    it there): the 1F porcelain line L-b06400d4 is already its low end; companion HELD 0 .. 0.376.
Merged with 0 rows, listed: T-626, T-629 (V15 itself), T-630, T-632. Not merged at claim, refused by name: T-627
(READY), T-628 (TODO). Nothing is wired; no candidate, released (V2.9 + route G), rule, knowledge or registry file is
written; no drawing is read: every figure comes from a committed, Checker-merged output, sha256-pinned and named.

R-T631-1 (every villa on the engine's line-index scheme):
  (a) MERGED ONLY (R-T629-1 (a)): a fix row enters only from a task MERGED with a Checker verdict; merged tasks whose
      rows move no line are listed with 0 rows; a task not merged is refused by name.
  (b) ONE WRITER PER LINE (R1): a fix row on a line an earlier package writes chains inside that package, its before
      being that package's after; otherwise it opens its own package.
  (c) A RANGE CLOSED BY A MERGED RE-MEASURE LEAVES AS EXCLUDED, NEVER AS RELEASED 0: the companion of a range whose
      source re-measure shows the attributed piece billed once by the owning line (companion 0 in the verdict) is set
      EXCLUDED in the package that added it, with the verdict named; the owning line's low end stands.
  (d) A FOOTPRINT DEDUCTION MOVES ITS HOST FLOOR LINE BY THE NEGATIVE OF THE FOOTPRINT CHANGE, and only the line the
      source names (T-625 'effect if adopted' L-7625f35c); the bed / mortar lines that follow the floor area are listed
      as downstream impacts for Gate B, never moved without their own verdict.
  (e) A RANGE IS NEVER A POINT (R-T619-1 (c)): a range enters as the line at its low end and a companion HELD 0 ..
      width; a range on a line that is already its low end adds the companion only, with a ruling naming the source.
  (f) A WORKER-ONLY FIGURE THE CHECKER DID NOT NAME AS A FIX ROW (T-625 curtail 0.157787, RS-A arrival band 0.0575)
      is listed with its figure, never wired, never 0.
  (g) Every line V16 does not write is identical to the V15 overlay; totals move only on the keys V16 writes.
Rebuild: pytest-driven writer (tests/t631_manifest_v16, URBAN_T631_WRITE=1); `--check` compares.
"""

from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
T629_DIR = ROOT / "research/agents_t629"
if str(T629_DIR) not in sys.path:
    sys.path.insert(0, str(T629_DIR))

import manifest_v15 as M15                                            # noqa: E402  (R-T629-1, read only)

M14, M9, OV = M15.M14, M15.M9, M15.OV
D, S = M15.D, M15.S

SCHEMA = "URBAN_T631_WIRING_MANIFEST_V16"
RULE = "R-T631-1"
OUT_JSON = HERE / "out/WIRING_MANIFEST_V16.json"
IN = {
    "T624": ROOT / "research/agents_t624/out/T624_BEAM_END_OPEN_ITEMS.json",
    "T622": ROOT / "research/agents_t622/out/WALL_TILE_REMEASURE_T622.json",
    "T625": ROOT / "research/agents_t625/out/T625_EVIDENCE.json",
    "T632": ROOT / "research/agents_t632/out/T632_UPSTAND_CENSUS.json",
    "V15": T629_DIR / "out/WIRING_MANIFEST_V15.json",
    "V15_CODE": T629_DIR / "manifest_v15.py",
}
PINS = {
    "T624": "17c00e0f7b855f52a78d4b7adbee4cce9a6880be55d7cf63fb539fb98ec2bdbb",
    "T622": "9750dad42874b7214cca2476f859911f26243a1b6442241ecd68dbdb58b151f3",
    "T625": "c23dfaf7688a9a244df73b26f408b75fdfd80cf363620f755d2381ed249f13ef",
    "T632": "57bcb9c0219c3cfd01cd03da69ec1cb6ffc705d5ad1beee9c6c94200769ba184",
    "V15": "05c92b00a35263c45de8e482122013a20617ba5ad9a7b4b4e16eb8057a4b9e27",
    "V15_CODE": "0bed02658cae851174245d6368c1f33e318a617d2bc5d3a794522a7970ad0a60",
}

# R-T631-1 (a): board MERGED verdicts at claim (2026-11-08T15:00Z; Verifier text abridged, full text on BOARD.md)
MERGED = {
    "T-622": {"merge": "31fe39db",
              "verdict": "BOARD T-622 VERIFIER 2026-11-08T10:00Z: GF-14 (+0.086709 ENGINE_WRONG stays worker "
                         "DRAWING-CONFIRMED) not re-measured; 39 other rows DRAWING-CONFIRMED; line stays PARTIALLY "
                         "VERIFIED"},
    "T-624": {"merge": "1e38add2",
              "verdict": "BOARD T-624 VERIFIER 2026-11-08T11:58Z: (c) B27 rect rebuilt 3.271257 x 0.9 = 2.944132 m2, tip "
                         "in it 0.001524 m2: billed once, companion 0, V14 closes to 66.392081 AGREE; (d) CB8 gap 0.004540 "
                         "m2 x 0.75 = 0.003405 AGREE; (b) B19 @ C15 wedge 0.001418 x 0.75 = 0.001064 AGREE; B26 @ C25 own "
                         "0.006189 x 0.85 = 0.005261 vs 0.005245 (-0.000016 m3, immaterial, named); B10 66.401795 "
                         "ENGINE_RIGHT on own calc for the three omissions; FR-T624-1..3 for the next manifest"},
    "T-625": {"merge": "47824e04",
              "verdict": "BOARD T-625 VERIFIER 2026-11-08T12:59Z: ROW 0 own 6.137684 m2 AGREE (sector 4.044824 + run "
                         "2.092860); engine 6.124412 is 0.013272 short = ENGINE_WRONG (chord flattening); row 0 VERIFIED; "
                         "NOT re-measured: curtail 0.157787, strings 0 .. 0.393843 (UNRESOLVED), slab margin 0 .. 0.376; "
                         "fix row for manifest V16 (T-631)"},
    "T-626": {"merge": "74e52c34",
              "verdict": "BOARD T-626 VERIFIER 2026-11-08T13:59Z: pantry / +9.70 domes / dome 1300 rows VERIFIED "
                         "components; classes stand; +4.30 annex TOLERANCE 0.001332 accepted; no line moved"},
    "T-629": {"merge": "b0eb7f60", "verdict": "BOARD T-629 VERIFIER 2026-11-08T12:58Z: V15 GATE A PASS (the base)"},
    "T-630": {"merge": "d9714012", "verdict": "BOARD T-630 VERIFIER 2026-11-08T13:58Z: end-to-end dry run; no line moved"},
    "T-632": {"merge": "e90e0f4d",
              "verdict": "BOARD T-632 VERIFIER 2026-11-08T13:57Z: B20 upstand 0.20 x 0.20 x 3.000 = 0.120 m3 = engine "
                         "ENGINE_RIGHT; F-C-P02-12 withdrawn; hatches 390 / 391 HELD length only"},
}
NO_ROW = {
    "T-626": "wet-room / roof membrane rows to evidence: every class stands (RULE_DIFFERENCE pantry, ENGINE_RIGHT domes, "
             "TOLERANCE +4.30 0.001332 accepted, residual 0.521668 UNRESOLVED on his lump row): no line moves",
    "T-629": "manifest V15: the base of V16 (rebuilt and compared, not restated)",
    "T-630": "end-to-end BOQ dry run on V15: reads lines, moves none",
    "T-632": "B20 upstand ENGINE_RIGHT (0.120 m3 = engine); hatches 390 / 391 HELD length only (no volume, thickness "
             "unprinted): no fix row",
}
NOT_MERGED = {"T-627": "READY at claim (B12 opening rows), not merged", "T-628": "TODO at claim (footing / lift-wall)"}

BEAM = ("STR.CONC.BEAM", "m3")
TILE = ("FIN.WALL.TILE", "m2")
PORC = ("FIN.FLOOR.PORCELAIN", "m2")
P_OVER = M14.P_OVER
P_WEDGE = "BEAM_END_WEDGES (T-624 FR-T624-1 / FR-T624-2)"
P_GF14 = "WALL_TILE_GF14 (T-622 FR-T622-2)"
P_STAIR = "ROUND_STAIR_FOOTPRINT (T-625 FR-T625-1 / -2 / -3)"
COMPANION = "NEW:STR.CONC.BEAM:HL:BEAM_LEDGER:GF:BM-GF-048#BAND0048.1#FR-T610-1:RANGE"
B27_LINE = "L-3dddf99008ab922da814"
GF14_LINE = "L-fa408571a8adcfaf1a1f"
GF_PORC = "L-7625f35c503d9f8e6196"                     # FIN.FLOOR.PORCELAIN GF-RC99C2A:floor (T-625 effect line)
F1_PORC = "L-b06400d46d252f242018"                     # FIN.FLOOR.PORCELAIN 1F-R78C367:floor (1F living, 33.411036)
GF14_H, GF14_DOORS = Decimal("3.65"), (("D-GF-11", "0.8", "2.20"), ("D-GF-12", "0.8", "2.20"))
B10_V15, B10_V16 = Decimal("66.392081"), Decimal("66.401795")
WRITES = {"STR.CONC.BEAM|m3", "FIN.WALL.TILE|m2", "FIN.FLOOR.PORCELAIN|m2"}


class ManifestError(Exception):
    pass


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def pins():
    for k, pin in PINS.items():
        if sha256(IN[k]) != pin:
            raise ManifestError(f"PIN: {IN[k].name} sha256 {sha256(IN[k])[:8]} is not the pinned {pin[:8]}")


def require_merged(task, merged=None):
    m = MERGED if merged is None else merged
    if task not in m or not m[task].get("merge") or not m[task].get("verdict"):
        raise ManifestError(f"{task} is not MERGED with a Checker verdict: its rows cannot enter a manifest")
    return m[task]


def no_row_sources(merged=None, no_row=None, not_merged=None):
    m = MERGED if merged is None else merged
    out = {t: {"merge": require_merged(t, m)["merge"], "rows": 0, "why": why}
           for t, why in (NO_ROW if no_row is None else no_row).items()}
    refused = {}
    for t, why in (NOT_MERGED if not_merged is None else not_merged).items():
        if t in m:
            raise ManifestError(f"{t} is listed as not merged but carries a merge: build its rows")
        refused[t] = {"refusal": f"{t} is not MERGED with a Checker verdict", "state": why}
    return out, refused


def _line(idx, lid, code_unit, cls="RELEASED"):
    line = idx.get(lid)
    if line is None:
        raise ManifestError(f"{lid}: not in the index")
    if (line["item_code"], line.get("unit")) != code_unit:
        raise ManifestError(f"{lid}: {line['item_code']} {line.get('unit')} is not a {code_unit[0]} {code_unit[1]} line")
    if cls and line["class"] != cls:
        raise ManifestError(f"{lid}: {line['class']}, expected {cls}")
    return line


def writer_of(order, lid):
    """R-T631-1 (b): the package that already writes the line, or None."""
    names = sorted({n for n, ops in order for op in ops if op["line_id"] == lid})
    if len(names) > 1:
        raise ManifestError(f"{lid}: written by {names} (R1 already broken upstream)")
    return names[0] if names else None


def _set(pkg, fid, lid, before, after_v, evidence, verdict, beside, note=None):
    if after_v <= 0:
        raise ManifestError(f"{lid}: {before['measured_net']} -> {S(after_v)} leaves nothing (HELD is never 0)")
    return M9.row(pkg, fid, "SET", lid, before, M9.released(float(after_v)), evidence, verdict, beside=beside,
                  note=note)


# ---- T-624: beam end wedges, CB8 gap, F-T619-1 closure ---------------------------------------------------------

def t624_rows(t624, idx, order, merged=None, source="T-624"):
    """FR-T624-1 / -2 (own package), FR-T624-3 and FR-T624-4 (chained in the T-610 package that writes the lines)."""
    src = require_merged(source, merged)
    fr = {r["id"]: r for r in t624["fix_rows"]}
    if sorted(fr) != ["FR-T624-1", "FR-T624-2", "FR-T624-3"]:
        raise ManifestError(f"T-624 fix rows {sorted(fr)} are not FR-T624-1 .. -3")
    pairs = {(p["line_id"], p["column"]): p for p in t624["b_pairs"]}
    wedge, chained, rulings, tot = [], [], [], Decimal(0)
    for fid in ("FR-T624-1", "FR-T624-2"):
        f = fr[fid]
        col = f["at"].split(" ")[0]
        p = pairs.get((f["line_id"], col))
        if p is None or p["verdict"] != "ENGINE_WRONG_OMISSION" or p["wedge_class"] != "DRAWN_WEDGE":
            raise ManifestError(f"{fid}: no ENGINE_WRONG_OMISSION drawn wedge at {col} on {f['line_id']}")
        if D(str(p["wedge_billed_by_any_line_m2"])) != 0 or D(str(p["wedge_in_any_t229_region_m2"])) != 0:
            raise ManifestError(f"{fid}: the wedge is billed elsewhere: an add would double count")
        ch = D(str(f["change_m3"]))
        if ch != D(str(p["omission_m3"])) or abs(D(str(p["wedge_m2"])) * D(str(p["depth_m"])) - ch) > D("0.0000005"):
            raise ManifestError(f"{fid}: {S(ch)} m3 is not wedge {p['wedge_m2']} x depth {p['depth_m']}")
        if writer_of(order, f["line_id"]):
            raise ManifestError(f"{fid}: {f['line_id']} is written by {writer_of(order, f['line_id'])}: chain it there")
        line = _line(idx, f["line_id"], BEAM)
        before = OV.state(line)
        wedge.append(_set(P_WEDGE, fid, f["line_id"], before, D(str(before["measured_net"])) + ch, "PARTIALLY VERIFIED",
                          src["verdict"],
                          beside={"mark": f["mark"], "storey": f["storey"], "column": f["at"], "cause": f["cause"],
                                  "wedge_m2": S(D(str(p["wedge_m2"]))), "depth_m": S(D(str(p["depth_m"]))),
                                  "change_m3": S(ch), "wedge_sides_on": p["wedge_sides_on"],
                                  "who_is_right": "ENGINE_WRONG OMISSION (Checker AGREE"
                                                  + (", own 0.005261 vs 0.005245: -0.000016 m3 immaterial, named)"
                                                     if fid == "FR-T624-1" else ")"),
                                  "rule": "R-T624-1 / UP-CONC-JOINT-001 1.0.0 (face to face on drawn members)",
                                  "component_evidence": "VERIFIED piece; the line as a whole stays PARTIALLY VERIFIED"},
                          note="R-T631-1 (b): no earlier package writes the line"))
        tot += ch
        rulings.append({"layer": OV.layer(BEAM[0]), "host_re": "^" + OV.host(line["element_id"]).replace(".", r"\.")
                        + "$", "sources": ["CANDIDATE", P_WEDGE],
                        "ruling": f"{fid} adds the drawn wedge at {f['at']} to {f['line_id']}: billed by no line and in no "
                                  "T-229 region (T-624 b_pairs: wedge_billed_by_any_line 0, in_any_t229_region 0): the "
                                  "other run(s) of the ledger beam do not hold it",
                        "fix_row": fid})
    # FR-T624-3: CB8 west end gap (supersedes FR-T614-H1, listed unwired in V14)
    f, h = fr["FR-T624-3"], t624["d_H1"]
    if h["line_id"] != f["line_id"] or h["verdict"] != "ENGINE_WRONG_OMISSION" or h["held_row"] != "FR-T614-H1" \
            or D(str(h["billed_by_any_line_m2"])) != 0 or D(str(h["m3"])) != D(str(f["change_m3"])):
        raise ManifestError("FR-T624-3: the d_H1 record is not the unbilled CB8 end gap of the fix row")
    pkg = writer_of(order, f["line_id"])
    if pkg != P_OVER:
        raise ManifestError(f"FR-T624-3: {f['line_id']} writer {pkg} is not the T-610 package")
    st = OV.state(idx[f["line_id"]])
    ch3 = D(str(f["change_m3"]))
    chained.append(_set(P_OVER, "FR-T624-3", f["line_id"], st, D(str(st["measured_net"])) + ch3, "PARTIALLY VERIFIED",
                        src["verdict"],
                        beside={"mark": f["mark"], "storey": f["storey"], "at": f["at"], "cause": f["cause"],
                                "gap_m": S(D(str(h["end_gap_m"]))), "piece_m2": S(D(str(h["region_m2"]))),
                                "depth_m": S(D(str(h["depth_m"]))), "change_m3": S(ch3),
                                "supersedes": "FR-T614-H1 HELD 0 .. 0.003405 m3 (V14 held_not_wired) by name",
                                "who_is_right": "ENGINE_WRONG OMISSION (Checker AGREE 0.004540 x 0.75)",
                                "chained_after": "FR-T610-2 on the same line"},
                        note="R-T631-1 (b): chained inside the T-610 package"))
    tot += ch3
    # FR-T624-4: item (c) closes the F-T619-1 range
    c = t624["c_B27_tip"]
    if c["state"] != "BILLED_ONCE_BY_OWNER" or c["verdict"] != "ENGINE_RIGHT" or D(str(c["companion_m3"])) != 0 \
            or c["B27_line_id"] != B27_LINE or D(str(c["tip_in_B27_rectangle_m2"])) != D(str(c["tip_m2"])):
        raise ManifestError("FR-T624-4: T-624 (c) does not close the tip as billed once by B27")
    if writer_of(order, COMPANION) != P_OVER:
        raise ManifestError(f"FR-T624-4: {COMPANION} is not the T-610 package's companion")
    cst = OV.state(idx[COMPANION])
    if cst["class"] != "HELD" or D(str(cst["held_low"])) != 0 or D(str(cst["held_high"])) != D("0.001295"):
        raise ManifestError(f"FR-T624-4: companion {cst} is not HELD 0 .. 0.001295 (stale)")
    chained.append(M9.row(P_OVER, "FR-T624-4", "SET", COMPANION, cst, M9.excluded(), "VERIFIED", src["verdict"],
                          beside={"closes": "F-T619-1 (V14 range 66.392081 .. 66.393376)",
                                  "tip_m2": S(D(str(c["tip_m2"]))), "in_B27_rect_m2": S(D(str(c["tip_in_B27_rectangle_m2"]))),
                                  "B27_rect_m2": S(D(str(c["B27_rectangle_m2"]))),
                                  "rule": "R-T631-1 (c): a range closed by a merged re-measure leaves as EXCLUDED, never "
                                          "RELEASED 0; B27 low end 4.206189 stands"},
                          note="chained in the package that added the companion"))
    return wedge, chained, rulings, tot


# ---- T-622: GF-14 wall tile ---------------------------------------------------------------------------------------

def gf14_row(t622, idx, order, merged=None, source="T-622"):
    src = require_merged(source, merged)
    room = next((r for r in t622["rooms"] if r["room"] == "GF-14"), None)
    if room is None or room["line_id"] != GF14_LINE:
        raise ManifestError("GF-14: no T-622 room record on the GF-14 line")
    if writer_of(order, GF14_LINE):
        raise ManifestError(f"GF-14: written by {writer_of(order, GF14_LINE)}: chain it there (R1)")
    line = _line(idx, GF14_LINE, TILE)
    if D(str(line["measured_net"])) != D(room["line"]):
        raise ManifestError(f"GF-14: line {line['measured_net']} is not the source's engine {room['line']} (stale)")
    if [(o["id"], o["w"], o["head"]) for o in room["openings"]] != [(a, b, c) for a, b, c in GF14_DOORS] \
            or D(room["H"]) != GF14_H:
        raise ManifestError("GF-14: openings / height are not the two 0.80 x 2.20 doors at 3.65")
    face = D(room["face_lm"])
    ded = sum((D(w) * D(h) for _, w, h in GF14_DOORS), Decimal(0))
    hand = face * GF14_H - ded
    if abs(hand - D(room["own_net"])) > D("0.0000005") or D(room["line"]) - D(room["own_net"]) != D(room["line_minus_own"]):
        raise ManifestError(f"GF-14: hand {S(hand)} is not the source's own {room['own_net']}")
    own = D(room["own_net"])
    return M9.row(P_GF14, "FR-T622-2", "SET", GF14_LINE, OV.state(line), M9.released(float(own)), "DRAWING-CONFIRMED",
                  src["verdict"],
                  beside={"chain": room["chain"], "open_side": room["open"], "face_lm": room["face_lm"],
                          "height_m": room["H"], "doors": [f"{a} {b} x {c}" for a, b, c in GF14_DOORS],
                          "hand": f"{room['face_lm']} x {S(GF14_H)} - {S(ded)} = {S(hand)} -> {S(own)} (6 dp)",
                          "change_m2": S(own - D(room["line"])),
                          "who_is_right": "ENGINE_WRONG (per-face 4 dp rounding + open side on threshold 2DB): worker "
                                          "DRAWING-CONFIRMED, the Checker did not re-measure GF-14",
                          "rule": "owner 2026-11-02 wet-area walls, Q-48 A tile top, Q-55 C door head, Q-73"},
                  note="carried DRAWING-CONFIRMED; the Checker re-adds it at Gate B")


# ---- T-625: round-stair footprint and its ranges ------------------------------------------------------------------

def t625_rows(t625, idx, order, merged=None, source="T-625"):
    src = require_merged(source, merged)
    r0 = t625["row0"]
    own, eng = D(r0["own"]), D(r0["engine_split_reproduced"]["engine_F1_F2"][0]) + \
        D(r0["engine_split_reproduced"]["engine_F1_F2"][1])
    parts = D(r0["F1"]) + D(r0["F2"])
    if own != parts or D(r0["difference"]) != own - Decimal("6.124412"):
        raise ManifestError(f"T-625 row 0: own {S(own)} is not F1 + F2 {S(parts)} or the stated difference")
    if "L-7625f35c" not in r0["effect_if_adopted"]:
        raise ManifestError("T-625 row 0: the effect line is not the GF porcelain line")
    cp = r0["class_proposal"]
    if not cp["strings"].startswith("UNRESOLVED 0 .. 0.393843"):
        raise ManifestError("T-625 strings range is not UNRESOLVED 0 .. 0.393843")
    strings = sum((D(v["area"]) for k, v in r0["parts"].items() if "string band" in k), Decimal(0))
    if strings != Decimal("0.393843"):
        raise ManifestError(f"T-625 string bands re-add to {S(strings)}, not 0.393843")
    sm = t625["first_floor_readings"]["slab_edge_margin"]
    if not sm["class_proposal"].startswith("UNRESOLVED 0 .. 0.376") or D(sm["bound_m2"]) != Decimal("0.376"):
        raise ManifestError("T-625 slab-edge margin is not UNRESOLVED 0 .. 0.376")
    margin_hand = (D(sm["north_len"]) + D(sm["east_len_to_band_top"])) * D(sm["north_offset"])
    if margin_hand > D(sm["bound_m2"]):
        raise ManifestError(f"T-625 margin {S(margin_hand)} exceeds its bound")
    for lid in (GF_PORC, F1_PORC):
        if writer_of(order, lid):
            raise ManifestError(f"{lid}: written by {writer_of(order, lid)}: chain it there (R1)")
    gf = _line(idx, GF_PORC, PORC)
    f1 = _line(idx, F1_PORC, PORC)
    b0 = OV.state(gf)
    d1 = own - Decimal("6.124412")
    v1 = D(str(b0["measured_net"])) - d1
    rows = [_set(P_STAIR, "FR-T625-1", GF_PORC, b0, v1, "VERIFIED", src["verdict"],
                 beside={"row": "T-621 row 0 round-stair footprint (deducted from the GF porcelain, UP-CER-001)",
                         "footprint_before_m2": "6.124412", "footprint_after_m2": S(own),
                         "parts": {"F1 arc band (239 / 23D / 256)": r0["F1"], "F2 run (22E / A7 / 13C less 2FD2)": r0["F2"]},
                         "change_m2": S(-d1), "cause": r0["cause"],
                         "who_is_right": "ENGINE_WRONG 0.013272 m2 (chord flattening), Checker own re-measure AGREE",
                         "rule": "R-T631-1 (d): the host floor moves by minus the footprint change"})]
    b1 = M9.released(float(v1))
    lo = v1 - strings
    elem = gf["element_id"] + "#FR-T625-2:RANGE"
    rows.append(_set(P_STAIR, "FR-T625-2", GF_PORC, b1, lo, "HELD", src["verdict"],
                     beside={"range_m2": f"{S(lo)} .. {S(v1)} (line at the low end; companion HELD 0 .. {S(strings)}; "
                                         "R-T619-1 (c))",
                             "what": "0.05 string bands beside the tread edges (inner curve 0.092854 + inner run "
                                     "0.092454 + outer curve 0.208535): stair structure / cladding (then out of the "
                                     "porcelain) or floor; ST-02 structure undrawn (Q-50 / T-269 designer item)",
                             "class": "UNRESOLVED (no owner question: ERS 2.7 not met, designer item)"},
                     note="R-T631-1 (e): range, never a point"))
    rows.append(M9.row(P_STAIR, "FR-T625-2", "ADD", f"NEW:{PORC[0]}:{elem}", None, M9.held(0.0, float(strings)), "HELD",
                       src["verdict"], code=PORC[0], unit=PORC[1], elem=elem,
                       beside={"range_of": GF_PORC, "low_m2": S(lo), "high_m2": S(v1),
                               "rule": "R-T619-1 (c): a range is never a point"},
                       note="companion of the ranged SET; HELD 0 .. width"))
    elem3 = f1["element_id"] + "#FR-T625-3:RANGE"
    rows.append(M9.row(P_STAIR, "FR-T625-3", "ADD", f"NEW:{PORC[0]}:{elem3}", None,
                       M9.held(0.0, float(D(sm["bound_m2"]))), "HELD", src["verdict"], code=PORC[0], unit=PORC[1],
                       elem=elem3,
                       beside={"range_of": F1_PORC, "low_m2": S(D(str(f1["measured_net"]))),
                               "high_m2": S(D(str(f1["measured_net"])) + D(sm["bound_m2"])),
                               "what": "1F slab edge 0.05 beyond the void lines B74 / B75 (ST 2D2 / 2CF): finish only if "
                                       "a void-edge / balustrade detail puts it there",
                               "rule": "R-T631-1 (e): the line is already its low end; the companion carries the width"},
                       note="companion only; the 1F porcelain line stays"))
    ruling = {"layer": OV.layer(PORC[0]), "host_re": "^" + OV.host(f1["element_id"]).replace(".", r"\.") + "$",
              "sources": ["CANDIDATE", P_STAIR],
              "ruling": "FR-T625-3 adds the HELD companion 0 .. 0.376 m2 of the 1F living porcelain (slab-edge margin, "
                        "T-625 UNRESOLVED): a range width beside its own line, never a second floor",
              "fix_row": "FR-T625-3"}
    listed = {"curtail_0.157787_m2": "worker ENGINE_WRONG proposal (first-step curtail, arc 258), Checker did not "
                                     "re-measure: listed, not wired (R-T631-1 (f)); marble trade check named",
              "rs_a_arrival_band_0.0575_m2": "worker ENGINE_WRONG proposal (1F arrival nosing band D24 / D22), not "
                                             "named a fix row: listed, not wired"}
    return rows, [ruling], {"own": S(own), "engine": S(eng), "gf_after_low": S(lo), "gf_after_high": S(v1),
                            "strings": S(strings), "margin_bound": sm["bound_m2"]}, listed


# ---- overlay ------------------------------------------------------------------------------------------------------

def v15_state():
    """the T-629 build up to its overlay (read only), so V16 steps from the exact V15 state."""
    M15.pins()
    t615, walls = M15._json(M15.IN["T615"]), M15._csv(M15.IN["T615_WALLS"])
    t617, t556, t622 = M15._json(M15.IN["T617"]), M15._json(M15.IN["T556"]), M15._json(M15.IN["T622"])
    v4 = M15._json(M15.IN["V4"])
    idx, order14, rul14, after14, rep14, t584 = M15.v14_state()
    written14 = {op["line_id"] for _, ops in order14 for op in ops}
    after498 = M15._state_after(idx, order14, M15.P498)
    blk, _, _ = M15.block015_rows(t615, walls, v4, after498)
    band, _ = M15.band_rows(t617, t556, dict(order14)[M15.P563])
    pantry = M15.pantry_row(t622, after14, taken=written14)
    order15 = M15.chain_into(M15.chain_into(order14, M15.P498, blk), M15.P563, band) + [(M15.P_PANTRY, [pantry])]
    rul15 = list(rul14) + M15.RULINGS_V15
    after15, rep15 = OV.apply(idx, order15, rul15)
    return idx, order15, rul15, after15, rep15, t584


def build():
    pins()
    t624, t622, t625, t632 = _json(IN["T624"]), _json(IN["T622"]), _json(IN["T625"]), _json(IN["T632"])
    v15j = _json(IN["V15"])
    idx, order15, rul15, after15, rep15, t584 = v15_state()
    if len(after15) != v15j["overlay"]["lines"]["after_v15"]:
        raise ManifestError("V15 state rebuild differs from the committed V15 line count")
    last = {}
    for r in v15j["rows"]:                       # a chained line is checked on its last step
        if r["kind"] in ("ADD", "SET"):
            last[r["line_id"]] = r
    for r in last.values():
        if not OV.same_state(OV.state(after15[r["line_id"]]), r["after"]):
            raise ManifestError(f"{r['line_id']}: V15 rebuild differs from the committed V15 row")
    t15 = OV.totals(after15)
    if t15["STR.CONC.BEAM|m3"]["released"] != S(B10_V15):
        raise ManifestError(f"B10 V15 {t15['STR.CONC.BEAM|m3']['released']} is not {S(B10_V15)}")
    sources, refused = no_row_sources()
    wedge, chained, rul_w, beam_add = t624_rows(t624, after15, order15)
    gf14 = gf14_row(t622, after15, order15)
    stair, rul_s, stair_out, stair_listed = t625_rows(t625, after15, order15)
    rows16 = wedge + chained + [gf14] + stair
    M9.validate_rows(rows16)
    order16 = M15.chain_into(order15, P_OVER, chained) + [(P_WEDGE, wedge), (P_GF14, [gf14]), (P_STAIR, stair)]
    rul16 = list(rul15) + rul_w + rul_s
    after16, rep = OV.apply(idx, order16, rul16)
    v16_lines = {r["line_id"] for r in rows16}
    others = sorted(k for k in set(after15) | set(after16) if k not in v16_lines and after15.get(k) != after16.get(k))
    if others:
        raise ManifestError(f"lines V16 does not write changed: {others[:5]}")
    t16 = OV.totals(after16)
    dt = OV.diff_totals(t15, t16)
    if set(dt) != WRITES:
        raise ManifestError(f"totals moved on {sorted(dt)}, V16 writes {sorted(WRITES)}")
    if any(c["status"] == "UNEXPLAINED" for c in rep["conflicts"]):
        raise ManifestError(f"unexplained conflicts: {[c for c in rep['conflicts'] if c['status'] == 'UNEXPLAINED']}")
    flagged = [r for r in rep["rows"] if r["status"] != "APPLIED"]
    v16_ops = {r["op_id"] for r in rows16}
    if any(r["op_id"] in v16_ops for r in flagged):
        raise ManifestError(f"a V16 row is not APPLIED: {[r for r in flagged if r['op_id'] in v16_ops]}")
    if len(flagged) != len([r for r in rep15["rows"] if r["status"] != "APPLIED"]):
        raise ManifestError("the flagged rows of V15 changed")
    # hand acceptance per family
    b15, b16 = t15["STR.CONC.BEAM|m3"], t16["STR.CONC.BEAM|m3"]
    if D(b16["released"]) != B10_V16 or D(b16["released"]) - D(b15["released"]) != beam_add \
            or D(b15["held_high"]) - D(b16["held_high"]) != Decimal("0.001295") or b16["held_low"] != b15["held_low"] \
            or b16["held_n"] != b15["held_n"] - 1 or b16["excluded_n"] != b15["excluded_n"] + 1:
        raise ManifestError(f"B10 {b15} -> {b16} is not +{S(beam_add)} released and the companion out")
    w15, w16 = t15["FIN.WALL.TILE|m2"], t16["FIN.WALL.TILE|m2"]
    dgf14 = D(gf14["beside"]["change_m2"])
    if D(w16["released"]) - D(w15["released"]) != dgf14:
        raise ManifestError(f"FIN.WALL.TILE moved {S(D(w16['released']) - D(w15['released']))}, GF-14 says {S(dgf14)}")
    p15, p16 = t15["FIN.FLOOR.PORCELAIN|m2"], t16["FIN.FLOOR.PORCELAIN|m2"]
    dp = D(p16["released"]) - D(p15["released"])
    if dp != Decimal("-0.013272") - Decimal("0.393843") or D(p16["held_high"]) - D(p15["held_high"]) != \
            Decimal("0.393843") + Decimal("0.376") or p16["held_n"] != p15["held_n"] + 2:
        raise ManifestError(f"FIN.FLOOR.PORCELAIN {p15} -> {p16} is not the T-625 rows")
    # downstream: lines on the same floor hosts that follow the area (listed for Gate B, not moved)
    hosts = {OV.host(after15[GF_PORC]["element_id"]), OV.host(after15[F1_PORC]["element_id"])}
    downstream = sorted(({"line": k, "item": l["item_code"], "unit": l.get("unit"), "element": l["element_id"],
                          "state": OV.state(l)} for k, l in after16.items()
                         if k not in v16_lines and k != F1_PORC and l["class"] != "EXCLUDED"
                         and l["item_code"].startswith("FIN.FLOOR")
                         and any(l["element_id"].startswith(h.split(":")[0] + ":floor") for h in hosts)),
                        key=lambda x: x["line"])
    hosts14 = {OV.host(after15[GF14_LINE]["element_id"])}
    downstream += sorted(({"line": k, "item": l["item_code"], "unit": l.get("unit"), "element": l["element_id"],
                           "state": OV.state(l)} for k, l in after16.items()
                          if k != GF14_LINE and l["class"] != "EXCLUDED" and OV.host(l["element_id"]) in hosts14),
                         key=lambda x: x["line"])
    status = {}
    for r in rep["rows"]:
        status.setdefault(r["package"], {}).setdefault(r["status"], 0)
        status[r["package"]][r["status"]] += 1
    M11 = M15.M11
    t412 = M11.load_t412()
    nrows, _ = M11.nosing_ledger(t412, M11._json(M11.IN["T598"]))
    cen = M9.census_on(after16, M11.census_edges(t412, nrows), t584, {M9.E1_LINE: ("ST-03", "E1")})
    if cen["doubles"] or cen["orphans"]:
        raise ManifestError("stair census doubles / orphans after V16")
    table = []
    for r in rows16:
        b, a = r.get("before"), r.get("after")
        table.append({"row": r["row"], "package": r["package"], "kind": r["kind"], "line_id": r["line_id"],
                      "item": r.get("item_code") or after15[r["line_id"]]["item_code"],
                      "before": None if b is None else {k: b[k] for k in OV.QFIELDS},
                      "after": None if a is None else {k: a[k] for k in OV.QFIELDS},
                      "evidence": r["evidence"]["status"], "verdict": r["evidence"]["verdict_line"][:40]})
    beam_hand = " + ".join(S(D(r["beside"]["change_m3"])) for r in wedge + chained if "change_m3" in r["beside"])
    return {
        "schema": SCHEMA, "rule": RULE, "task": "T-631", "candidate": M9.T580.CANDIDATE,
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in IN.values()},
        "sources_merged": {k: v["merge"] for k, v in MERGED.items()},
        "sources_no_row": sources, "sources_refused": refused,
        "supersedes": {
            "V14 held_not_wired FR-T614-H1 (CB8 col 2 west, HELD 0 .. 0.003405 m3)": "FR-T624-3 (measured 0.003405)",
            "V14 F-T619-1 / FR-T610-1 companion HELD 0 .. 0.001295 m3": "FR-T624-4 EXCLUDED (range closed, billed once)",
            "V15 held_not_wired 'T-622 GF-14'": "FR-T622-2 (wired DRAWING-CONFIRMED on the Lead's T-631 row)"},
        "held_not_wired": {"T-625": stair_listed,
                           "T-632": "hatches 390 (3.100 m x 0.200) / 391 (1.782 m x 0.200) HELD length only; strip "
                                    "2 x 0.865 m2 HELD (thickness unprinted): no owning line, Lead slab-edge fix row"},
        "line_table": table,
        "rows": [dict(r) for r in rows16],
        "beam_b10": {"STR.CONC.BEAM|m3": {"v15": b15, "v16": b16},
                     "hand": f"{S(B10_V15)} + {beam_hand} = {b16['released']} (a point: companion 0 .. 0.001295 "
                             "EXCLUDED by FR-T624-4); pre-existing HELD unchanged",
                     "vs_freelancer": "his 66.093875: +0.307920 m3 (+0.466 %), ENGINE_RIGHT on the Checker's own calc "
                                      "for the three omissions (T-624)"},
        "wall_tile": {"FIN.WALL.TILE|m2": {"v15": w15, "v16": w16}, "hand": gf14["beside"]["hand"],
                      "line": GF14_LINE, "change_m2": gf14["beside"]["change_m2"]},
        "floor_porcelain": {"FIN.FLOOR.PORCELAIN|m2": {"v15": p15, "v16": p16}, "t625": stair_out,
                            "hand": f"GF {S(D(str(after15[GF_PORC]['measured_net'])))} - 0.013272 (row 0) = "
                                    f"{stair_out['gf_after_high']}; strings low end - {stair_out['strings']} = "
                                    f"{stair_out['gf_after_low']} + HELD 0 .. {stair_out['strings']}; 1F "
                                    f"{S(D(str(after15[F1_PORC]['measured_net'])))} + HELD 0 .. 0.376"},
        "downstream_not_moved": downstream,
        "overlay": {
            "lines": {"base": len(idx), "after_v15": len(after15), "after_v16": len(after16)},
            "order": [{"package": n, "ops": len(o), "status": status.get(n, {})} for n, o in order16],
            "flagged_rows": flagged,
            "stale": sum(r["status"] == "STALE" for r in rep["rows"]),
            "two_package_lines": 0,                     # OV.apply raises R1 otherwise
            "unexplained_conflicts": sum(c["status"] == "UNEXPLAINED" for c in rep["conflicts"]),
            "conflicts": [c for c in rep["conflicts"] if any(l in v16_lines for l in c["lines"])],
            "rulings_v16": rul_w + rul_s,
            "other_lines_changed_vs_v15_overlay": others,
            "v16_vs_v15_totals": dt,
        },
        "stair_edge_census_after_v16": {"edges": cen["edges"], "doubles": len(cen["doubles"]),
                                        "orphans": len(cen["orphans"])},
        "findings": {
            "F-T631-1": "the floor bed lines on the GF / 1F porcelain hosts follow the floor area by rule; V16 moves "
                        "the porcelain only (verdict-named): the bed lines listed under downstream_not_moved need the "
                        "same delta at Gate B or their own verdict",
            "F-T631-2": "the T-625 curtail 0.157787 m2 and the RS-A arrival band 0.0575 m2 are worker proposals the "
                        "Checker did not re-measure: they need a Checker verdict before any manifest carries them",
        },
        "candidate_files_touched": 0, "released_quantities_changed": 0,
    }


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, default=str) + "\n"


def write_outputs():
    b = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(dumps(b), encoding="utf-8")
    return b


def main(argv):
    text = dumps(build())
    if "--check" in argv:
        ok = OUT_JSON.exists() and OUT_JSON.read_text(encoding="utf-8") == text
        print("T-631 manifest V16: committed output", "is the rebuild" if ok else "DIFFERS from the rebuild")
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
