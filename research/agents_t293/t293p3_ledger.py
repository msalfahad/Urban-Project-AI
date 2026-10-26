"""T-293 part 3: the stair, dome and water-tank formwork rows of formwork r4 tied, piece by piece, to the
ARCH_TAKEOFF_V3.0.18 candidate concrete lines (stair lines split by T-266).

    python3 -I research/agents_t293/t293p3_ledger.py            # build + assert, print the summary
    python3 -I research/agents_t293/t293p3_ledger.py --write    # also write the committed outputs in this folder

Inputs (all in the repository; no drawing content): the part-1 source records of formwork r4 (t293_alsenan.faces_r4 on
FORMWORK_LINES_R4.csv, T-264 MERGED 90203feb, + the two T-290 delta rows); the stair soffit ledger LEDGER_T281.csv
(T-281 MERGED 789ebbb4: drawn soffit planes per flight / landing, methods O and D); the stair / dome closure ledger
LEDGER_T258.csv (T-258 r2 MERGED b1b72a50); the T-266 component-closure inputs (t266_inputs.build(), T-266 MERGED
ceeb5135 = V3.0.18); the candidate concrete lines CANDIDATE_V3016_CONCRETE_LINES.json (stair / dome / ring lines are
byte-identical in V3.0.17: none is in the T-254 per-line table); part 2's slab-level pieces
FORMWORK_FACE_TO_LINE_T293_P2.csv (where a stair row's piece is already booked on a beam line).

Scope (Lead 2026-10-26 00:15): every r4 row of element STAIR, DOME and TANK, the two T-290 delta rows, the winder slab
row R4-316 and the dome-opening band row R4-313 that part 2 left NAMED for part 3. Nothing is wired, no candidate or
released line changes, no formwork quantity is rewritten (r4 stays as merged; a corrected formwork revision is a new
file, carried by T-199).

Rules added here (research scope, any villa; provenance T-293 part 3 on T-264 r4 / T-281 / T-258 r2 / T-266 / T-290):

R-FW-P3-1  a formed face is tied to the candidate line that carries the concrete of the PIECE it bounds: after a
           component split (R-COMPONENT-CLOSURE-1) the part line; a piece still held inside the parent -> the parent; a
           HOLD line -> that line. When no quantity of the candidate carries the piece's concrete (held remainder, HOLD
           line, BLOCKED line), the face is HELD with it: blank, its value kept (held_from), never shown as measured. A
           face supplied as measured on such a piece is refused.
R-FW-P3-2  a stair soffit form is the drawn soffit plane (T-281 method O, true area = plan x sec). Where a formwork
           row was derived from a volume / thickness, its excess over the drawn soffit is split to its physical cause:
           inside a beam band or a column outline -> NO_FACE_INSIDE_MEMBER (no surface exists there); under another
           member's footprint that member's rows already hold -> DUPLICATE_IN_SOURCE (one face once, D-T163-3); a
           reading the concrete ledger retired -> RETIRED_IN_SOURCE; an unmarked drawn line -> HELD on an UNKNOWN
           member; a column exposure in CONFLICT -> HELD on the piece. Pieces close on the row; the print rounding of
           the row (<= 0.0005 m2) is its own named piece.
R-FW-P3-3  method D (drawing-derived physical planes, T-281) is carried beside each tied soffit piece as an
           alternative, never summed with method O and never chosen by size.
R-FW-P3-4  one member, one formed-face view: an r4 row that describes a member already tied under another element
           (the TANK row = beam B15 BM-2F-007, tied in part 2) is a DUPLICATE_VIEW, never a second face; its open
           designer item (D-44) is reported against that member's faces.
R-FW-P3-5  a drawn element with no candidate line (the dome drums, Lead 14:15 / T-266 s.4 (2)) stays
           NO_CANDIDATE_LINE, HELD, its row kept: no face invented, no value, never 0.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RES = ROOT / "research"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(RES / "agents_t266"))
import face_line_ledger as F  # noqa: E402
import t293_alsenan as P1  # noqa: E402  (part 1 source records, merged 294da634)

TOL = F.TOL
CALC, HELD, NA = "CALCULATED", "HELD", "NOT_APPLICABLE"
NO_FACE = "NO_FACE_INSIDE_MEMBER"
DUP = "DUPLICATE_IN_SOURCE"
RETIRED = "RETIRED_IN_SOURCE"
ROUND = "PRINT_ROUNDING"
DUPVIEW = "DUPLICATE_VIEW"
POINTER = "POINTER_ROW"
NOT_MEASURED = ("BLOCKED_RFI", "BOUNDED_EXPOSURE", "NOT_APPLICABLE_WITH_EVIDENCE")
CAND_FILE = HERE / "CANDIDATE_V3016_CONCRETE_LINES.json"
P2_FILE = HERE / "FORMWORK_FACE_TO_LINE_T293_P2.csv"
T266 = "T-266 MERGED ceeb5135 (Checker Gate B 22:49) = ARCH_TAKEOFF_V3.0.18"
SCOPE = {"STAIR", "DOME", "TANK"}
PART2_NAMED = ("R4-313", "R4-316")          # part 2 left these two slab-level rows NAMED for part 3
# the three V3.0.18 part lines, as T-266's handoff prints them; recomputed here from the merged inputs (asserted)
T266_PART_IDS = {"L-7863355dfcb68a681d2d": "L-e37d81a8be8e0aa0010c", "L-b6b0354b7842f0ed6e41": "L-056402f98a6dbbcde0a0",
                 "L-821032bc04a0b0d02133": "L-85f64587588af8537b4b"}


class Refused(F.Refused):
    pass


# ================================================================================================ generic (any villa)

def split_row(row: dict, pieces: list) -> list:
    """R-FW-P3-2: one source row -> its pieces. pieces: dicts with 'id', 'member', 'm2', 'kind' (None = a face to tie,
    else one of NO_FACE / DUP / RETIRED / 'HELD'), 'note'. The print rounding is added as its own piece; any other
    residual, a negative piece or a piece without member is refused."""
    if row.get("m2") is None:
        raise Refused(f"{row['face_id']}: a row without a quantity is not split (tie it whole)")
    out, s = [], 0.0
    for p in pieces:
        if not p.get("member"):
            raise Refused(f"{row['face_id']}.{p.get('id')}: piece without a member")
        if p["m2"] is None or p["m2"] < 0:
            raise Refused(f"{row['face_id']}.{p['id']}: piece quantity {p['m2']!r} (a piece is a positive area)")
        s += p["m2"]
        q = dict(row, face_id=f"{row['face_id']}.{p['id']}", split_of=row["face_id"], members=[p["member"]],
                 m2=round(p["m2"], 6), lo=None, hi=None, basis_note=p.get("note", ""), piece_kind=p.get("kind"))
        if p.get("alt_D") is not None:
            q["alt_D_m2"] = round(p["alt_D"], 6)
        if p.get("kind") == "HELD":
            q["hold_piece"] = p.get("note", "")         # held after the tie (its source status stays the row's)
        out.append(q)
    res = round(row["m2"] - s, 6)
    if abs(res) > TOL:
        raise Refused(f"{row['face_id']}: pieces {s:.6f} do not close on the row {row['m2']} (residual {res})")
    if res != 0.0:
        out.append(dict(row, face_id=f"{row['face_id']}.ROUNDING", split_of=row["face_id"],
                        members=[row["members"][0]], m2=res, lo=None, hi=None, piece_kind=ROUND,
                        basis_note=f"the row prints {row['m2']} m2 (3 dp of a 4-dp volume / thickness): residual {res}"))
    return out


def named_kinds(pieces: list) -> dict:
    """face id -> (tie kind, reason) for the pieces that are not faces to tie"""
    why = {NO_FACE: "inside another member's outline: no surface exists there (R-FW-P3-2)",
           DUP: "under another member whose own rows already hold this face (one face once, D-T163-3)",
           RETIRED: "a reading the concrete ledger retired: not a physical face (R-FW-P3-2)",
           ROUND: "print rounding of the source row (<= 0.0005 m2), named so the row closes exactly"}
    return {p["face_id"]: (p["piece_kind"], why[p["piece_kind"]] + (": " + p["basis_note"] if p.get("basis_note") and
                                                                     p["piece_kind"] != ROUND else ""))
            for p in pieces if p.get("piece_kind") in why}


def hold_pieces(rows: list) -> list:
    """R-FW-P3-2: a piece split off as HELD (column exposure in CONFLICT, unknown member) is blank, its value kept"""
    for r in rows:
        if r.get("hold_piece") is not None and r.get("m2") is not None:
            r["held_from"], r["m2"], r["status"] = r["m2"], None, HELD
            r["held_reason"] = r.pop("hold_piece")
    return rows


def hold_on_unbooked_pieces(rows: list, held_members: set) -> list:
    """R-FW-P3-1: a TIED face whose piece's concrete no candidate quantity carries becomes HELD (blank, value kept)"""
    for r in rows:
        if r["tie"] == F.TIED and r["members"][0] in held_members and r["status"] == CALC:
            r["status_before_piece_hold"] = r["status"]
            r["held_from"], r["m2"], r["status"] = r["m2"], None, HELD
            r["held_reason"] = "R-FW-P3-1: the concrete of this piece is carried by no candidate quantity " \
                               "(held remainder / HOLD line); the face is held with it, its value kept"
    return rows


def refuse_measured_on_held(rows: list, held_members: set) -> None:
    for r in rows:
        if r["tie"] == F.TIED and r["members"][0] in held_members and r.get("m2") is not None:
            raise Refused(f"{r['face_id']}: a measured face ({r['m2']} m2) on the held piece {r['members'][0]} "
                          f"(R-FW-P3-1: held with its piece, blank)")


VIEW_PAIRS = (frozenset({"TANK", "BEAM"}), frozenset({"STAIR", "BEAM"}), frozenset({"DOME", "BEAM"}))


def check_one_view(rows: list, pairs=VIEW_PAIRS) -> None:
    """R-FW-P3-4 / R-FW-LINE-1: no member carries faces from two element views that describe the same faces (a tank
    wall that is a beam, a stair piece that is a beam band, a dome ring that is a beam) as quantities"""
    seen = collections.defaultdict(set)
    for r in rows:
        if r["tie"] == F.TIED and (r.get("m2") is not None or r.get("held_from") is not None):
            seen[r["members"][0]].add(r.get("element"))
    two = {m: v for m, v in seen.items() if any(p <= v for p in pairs)}
    if two:
        raise Refused(f"members booked under two element views: {two}")


# ================================================================================================ Alsenan inputs

def _f(v):
    return None if v in (None, "") else float(v)


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rd(rel):
    return list(csv.DictReader((ROOT / rel).open(encoding="utf-8")))


def candidate():
    return json.loads(CAND_FILE.read_text(encoding="utf-8"))


def t281():
    return {r["id"]: r for r in rd("research/agents_t281/LEDGER_T281.csv")}


def p2_rows():
    return list(csv.DictReader(P2_FILE.open(encoding="utf-8")))


def v3018_lines(cand):
    """the V3.0.18 stair / dome / ring lines: the V3.0.16 lines (byte-identical in V3.0.17) + the T-266 records
    (SPLIT -> parent blank + part line, REBASE, HOLD), part line ids recomputed by the engine's own id function"""
    import t266_inputs as L18
    from engine.source import arch_v3018 as A, boq_line as BL
    v17 = {}
    for ln in (RES / "agents_t254/T-254_BASIS_CORRECTION.md").read_text(encoding="utf-8").splitlines():
        if ln.startswith("| L-"):
            v17[ln.strip("|").split("|")[0].strip()] = 1
    by = {x["line_id"]: dict(x) for x in cand["lines"]}
    keep = {lid: x for lid, x in by.items() if x["item_code"] in ("STR.CONC.STAIR", "STR.CONC.DOME")
            or x["element_id"].startswith("HL:DOME_RING:")}
    bad = sorted(set(keep) & set(v17))
    if bad:
        raise Refused(f"stair / dome lines changed by V3.0.17 (T-254): {bad}")
    pid = cand["project"]["project_id"]
    parts, held_pieces, piece_line = {}, {}, {}
    for r in L18.build()["records"]:
        if r["kind"] not in ("SPLIT", "REBASE", "HOLD"):
            continue
        b = keep.get(r["line_id"])
        if b is None or b["element_id"] != r["element_id"]:
            raise Refused(f"T-266 record {r['line_id']}: not a stair / dome line of the candidate")
        if r["kind"] == "SPLIT":
            b.update(evidence_state="BLOCKED_RFI", measured_net=None, bounded_low=None, bounded_high=None,
                     v3018="SPLIT_PARENT (held remainder)")
            for p in r["parts"]:
                eid = A.part_element_id(r["element_id"], p["part"])
                lid = BL.line_id(pid, b["item_code"], eid, A.RULE_ID, A.RULE_VERSION, b["unit"])
                if T266_PART_IDS[r["line_id"]] != lid:
                    raise Refused(f"part line of {r['line_id']}: recomputed {lid} != T-266 {T266_PART_IDS[r['line_id']]}")
                parts[lid] = {"line_id": lid, "item_code": b["item_code"], "floor": b["floor"], "element_id": eid,
                              "unit": b["unit"], "evidence_state": A.STATE_OF[p["status"]],
                              "measured_net": p["value"], "evidence_status": p["status"],
                              "v3018": f"SPLIT_PART of {r['line_id']}"}
                for x in p["pieces"]:
                    piece_line[x["id"]] = lid
            for h in r["still_held"]:
                piece_line[h["piece"]] = r["line_id"]
                held_pieces[h["piece"]] = h["item"]
        elif r["kind"] == "REBASE":
            b.update(evidence_state=A.STATE_OF[r["status"]], measured_net=r["value"], bounded_low=None,
                     bounded_high=None, v3018=f"REBASE {r['status']}")
        else:
            b.update(evidence_state="BLOCKED_RFI", measured_net=None, bounded_low=None, bounded_high=None,
                     v3018="HOLD")
            held_pieces["ST03-E1-STEPS"] = r["held_item"] + " (steps 0.355017 DC named in the held line, not booked)"
            held_pieces["ST03-E1-WAIST"] = r["held_item"]
            piece_line["ST03-E1-STEPS"] = piece_line["ST03-E1-WAIST"] = r["line_id"]
    keep.update(parts)
    return keep, piece_line, held_pieces


# stair pieces of the r4 rows (r4 item prefix -> T-258 piece id)
STAIR_PIECE = {"MS1-L ": "ST01-MS1-L", "MS1-T ": "ST01-MS1-T", "MS1-LD ": "ST01-MS1-LD", "MS1-U ": "ST01-MS1-U",
               "MS2-L ": "ST01-MS2-L", "MS2-TR ": "ST01-MS2-TR", "MS2-LD ": "ST01-MS2-LD", "MS2-U ": "ST01-MS2-U",
               "E1 ": None, "D1 riser": "ST01b-D1-STEPS", "D1 waist": "ST01b-D1-WAIST", "RS-C ": "ST02-RS-C",
               "RS-S ": "ST02-RS-S", "RS-LD ": "ST02-RS-LD", "RS-A ": "ST02-RS-A"}
# V3.0.16 lines of the pieces T-266 did not split (one piece per line)
LINE_OF_PIECE = {"ST01-MS2-L": "L-67e4b0485135f84acc46", "ST01-MS2-U": "L-bb0e57b1948175a3d5b8",
                 "ST01-MS2-LD": "L-2416e65f053a14199cfc", "ST01-MS2-TR": "L-659243ed9fc2831c3ae8",
                 "SHELL:DOME-A": "L-8ea34765d16b54898140", "SHELL:DOME-B": "L-fffa895ed96b9d6a682c",
                 "SHELL:DOME-3": "L-d5401fa8986900c66c37",
                 # T-193 / T-160: DOME-A = DOME-1 west = DOME-1F-W ring (B4 in-bay 1.5105 x 0.50 = 0.7552);
                 # DOME-B = DOME-2 east = DOME-1F-E ring (BLOCKED, 0.8997 candidate never released)
                 "RING:DOME-A": "L-48b7d139bff681199543", "RING:DOME-B": "L-ab37afa17f2ac5b0efd1"}
HELD_LINE_PIECES = {"ST01-MS2-TR": "C-ST-3: junction of the two plates 0.168 apart not drawn (line BLOCKED_RFI)",
                    "SHELL:DOME-3": "G3-a / D-21: tower dome shell not detailed (line BLOCKED_RFI, DG-5)"}
# beam bands the waist volumes run into (T-258 r2 'source' text: drawn lines, not a convention)
IN_BEAM = {"ST01-MS1-U": (0.20, "B20 band P-C:BEAMS:GF:BAND0043.2 (L-d06033aa8d5f29aef490): last riser line 0.20 inside "
                                "the band 458 / 2C6 (ST p.4; T-258 r2 ST01-MS1-U)"),
           "ST01-MS2-U": (0.20, "B23 band P-C:BEAMS:1F:BAND0031.2 (L-5ca0573b64ee1cb22e0e): last line 0.20 inside "
                                "5E4 / 5E1 (ST p.5; T-258 r2 ST01-MS2-U)"),
           "ST01-MS2-L": (0.150, "B20 band (stair-side face 2C6 on p.4): first riser line 0.150 inside the band "
                                 "(ST p.5; T-281 ST01-MS2-L)")}
LANE = 1.20                                  # structural lanes of ST-01 / ST-02 (T-258 r2, R-STAIR-LANE-1)


def _sec(t, pid):
    r = t[pid]
    return float(r["true_O"]) / float(r["plan_O"])


def stair_pieces(rec, piece, t, p2):
    """the Alsenan pieces of one CALCULATED soffit / riser row (R-FW-P3-2); None = tie the row whole"""
    it = rec["item"]
    m = f"PIECE:{piece}"
    if "riser forms" in it:
        if piece == "ST02-RS-A":
            r = 4.50 / 28                        # Q-50 A cond (T-258 r2)
            return [dict(id="LANE", member=m, m2=5 * LANE * r, note="5 x 1.200 (structural lane, T-258 r2) x 4.50 / 28"),
                    dict(id="ARCH_WIDTH", member=m, m2=5 * (1.25 - LANE) * r, kind=RETIRED,
                         note="5 x 0.05 x 4.50 / 28: the architectural 1.25 width T-258 r2 replaced by the lane 1.200 "
                              "(T-290 s.5 (2))")]
        return None
    if piece in ("ST01-MS1-LD",):
        return None
    if piece == "ST01-MS2-LD":
        w, e = float(t["ST01-MS2-LD-W"]["true_O"]), float(t["ST01-MS2-LD-E"]["true_O"])
        return [dict(id="W", member=m, m2=w, alt_D=float(t["ST01-MS2-LD-W"]["true_D"]),
                     note="T-281 ST01-MS2-LD-W plate 1.150 x 1.300 (method O; D 1.0849: the MS2-L head kink 0.4101 plan "
                          "runs sloped under its edge)"),
                dict(id="E", member=m, m2=e, alt_D=float(t["ST01-MS2-LD-E"]["true_D"]),
                     note="T-281 ST01-MS2-LD-E plate 1.200 x 1.200"),
                dict(id="RETIRED_0480", member=m, m2=rec["m2"] - w - e, kind=RETIRED,
                     note="the 0.480 / 0.16 reading T-258 s.3 retired as a double count: 1.30 x 0.05, the MS2-L last "
                          "going (T-290 s.5 (1))")]
    if "waist soffit" in it:
        s = _sec(t, piece)
        kink = t.get(f"{piece}/head kink")
        alt = float(t[piece]["true_D"]) + (float(kink["true_D"]) if kink else 0.0)
        out = [dict(id="SOFFIT", member=m, m2=float(t[piece]["true_O"]), alt_D=alt,
                    note=f"T-281 {piece} drawn soffit, method O: plan {t[piece]['plan_O']} x sec {s:.6f}"
                         + (f"; method D {t[piece]['true_D']} + head kink {kink['true_D']} (the sloped soffit runs on "
                            f"{kink['plan_D']} m2 plan under the next plate's edge, which method O books flat with that "
                            f"plate{'; here the plate is the 1F arrival slab C-T1, a slab panel of part 2' if piece == 'ST02-RS-A' else ''})"
                            if kink else ""))]
        if piece in IN_BEAM:
            d, why = IN_BEAM[piece]
            out.append(dict(id="IN_BEAM", member=m, m2=d * LANE * s, kind=NO_FACE,
                            note=f"{d:.3f} x {LANE:.3f} x sec {s:.6f}: waist volume inside the {why}"))
        sub = {"ST01-MS2-L": [("ST01-MS2-L/column 691 exposure", "COL691", "HELD")],
               "ST02-RS-S": [("ST02-RS-S/B3 'With Stair' band underside", "B3", DUP),
                             ("ST02-RS-S/CA member underside", "CA", DUP),
                             ("ST02-RS-S/column 380 exposure", "COL380", "HELD"),
                             ("ST02-RS-S/hidden pair 535 / 536", "HIDDEN_535_536", "UNKNOWN")],
               "ST02-RS-A": [("ST02-RS-A/hidden pair 2CC / 2CD", "HIDDEN_2CC_2CD", "UNKNOWN")]}.get(piece, [])
        for tid, pid, kind in sub:
            a = float(t[tid]["plan_O"]) * s
            if kind == DUP:
                note = DUP_NOTE[pid] % (t[tid]["plan_O"], s)
                out.append(dict(id=pid, member=m, m2=a, kind=DUP, note=note))
            elif kind == "HELD":
                out.append(dict(id=pid, member=m, m2=a, kind="HELD",
                                note=f"T-281 {tid} {t[tid]['plan_O']} plan x sec: column projects 0.050 into the lane "
                                     f"(T-248 D-16 CONFLICT): column face or stair soffit not settled"))
            else:
                out.append(dict(id=pid, member=f"UNKNOWN:{pid}", m2=a, kind="HELD",
                                note=f"T-281 {tid} {t[tid]['plan_O']} plan x sec: unmarked layer-5 pair along the lane "
                                     f"(F-T281-03, C-ST-3 designer row): what it is, is not drawn"))
        if piece == "ST02-RS-A":
            out.append(dict(id="ARCH_WIDTH", member=m, m2=(1.25 - LANE) * 1.20 * s, kind=RETIRED,
                            note="0.05 x 1.200 run x sec: the architectural 1.25 width T-258 r2 replaced by the lane"))
        return out
    if "landing soffit" in it and piece == "ST02-RS-LD":
        g = {k: float(t[f"ST02-RS-LD{k}"]["plan_O"]) for k in ("", "/column 374", "/B3 'With Stair' band underside",
                                                               "/hidden pair 2CC / 2CD", "/hidden pair 535 / 536")}
        gross = sum(g.values())
        return [dict(id="SOFFIT", member=m, m2=g[""], alt_D=float(t["ST02-RS-LD"]["true_D"]),
                     note="T-281 ST02-RS-LD plate (method O; D 0.674803: the RS-S head kink runs sloped under its edge)"),
                dict(id="COL374", member=m, m2=g["/column 374"], kind=NO_FACE,
                     note="column 374 0.550 x 0.050 inside the plate outline (T-258 / Checker 13:10)"),
                dict(id="B3", member=m, m2=g["/B3 'With Stair' band underside"], kind=DUP,
                     note=DUP_NOTE["B3_LD"] % g["/B3 'With Stair' band underside"]),
                dict(id="HIDDEN_2CC_2CD", member="UNKNOWN:HIDDEN_2CC_2CD", m2=g["/hidden pair 2CC / 2CD"], kind="HELD",
                     note="T-281 unmarked pair 2CC / 2CD under the plate (F-T281-03)"),
                dict(id="HIDDEN_535_536", member="UNKNOWN:HIDDEN_535_536", m2=g["/hidden pair 535 / 536"], kind="HELD",
                     note="T-281 unmarked pair 535 / 536 under the plate (F-T281-03)"),
                dict(id="PRE_R2", member=m, m2=rec["m2"] - gross, kind=RETIRED,
                     note=f"the pre-r2 0.2256 m3 reading (T-290 s.5 (2)); the drawn plate gross is {gross:.6f} "
                          f"(1.150 x 1.200)")]
    return None


DUP_NOTE = {
    "B3": "T-281 %s plan x sec %.6f: the RS-S lane over the 'B3 (With Stair)' band T-139 GF-159, whose underside part 2 "
          "holds on BM-GF-057 (R4-258.GF-159, HELD 1.375625 m2, Q-61 C)",
    "CA": "T-281 %s plan x sec %.6f: the CA member 54E (T-139 GF-143 / 144 / 158) whose underside part 2 books on "
          "BM-GF-039 / BM-GF-057 (R4-254 GF-144 0.1725 + GF-158 0.1425 CALCULATED, R4-258 GF-143 0.03 HELD)",
    "B3_LD": "%.6f m2 of the plate over the 'B3 (With Stair)' band GF-159 (part 2 R4-258.GF-159 on BM-GF-057)"}


def check_dup_booked(p2):
    """the DUPLICATE_IN_SOURCE pieces are really booked in part 2 (T-139 faces, plan m2)"""
    m = {}
    for r in p2:
        if r.get("walk_face") in ("GF-159", "GF-143", "GF-144", "GF-158") and "SOFFIT" in r["face_id"]:
            m[r["walk_face"]] = (_f(r["m2"]) if r["m2"] else _f(r["held_from"]) or _f(r["hi"]), r["line_id"], r["tie"])
    want = {"GF-159": 1.375625, "GF-143": 0.03, "GF-144": 0.1725, "GF-158": 0.1425}
    for k, v in want.items():
        if k not in m or abs(m[k][0] - v) > 1e-6 or m[k][2] != F.TIED:
            raise Refused(f"part 2 does not book {k} {v} on a beam line: {m.get(k)}")
    return m


def sources():
    """the part-1 source records of every row in scope (identical records, so the three parts union exactly)"""
    src, faces, named = P1.faces_r4(P1.r4_rows(), P1.boundary_runs())
    keep = [s for s in src if s["element"] in SCOPE or s["face_id"].startswith("T290-")
            or s["face_id"] in PART2_NAMED]
    if len(keep) != 46:
        raise Refused(f"part 3 scope: {len(keep)} source rows, expected 46 (23 STAIR + 18 DOME + 1 TANK + 2 T-290 + 2)")
    return keep


def classify(src, t, p2, piece_line, held_pieces=()):
    faces, named = [], {}
    for rec in src:
        rec = dict(rec)
        it, el, fid = rec["item"], rec["element"], rec["face_id"]
        if rec["status"] == "S1_NOT_RELEASED":
            faces.append(rec)
            named[fid] = (F.SCENARIO, "client-request scenario S1: never a candidate face (ScenarioLeak guard)")
            continue
        if fid.startswith("T290-"):
            faces.append(rec)
            named[fid] = (POINTER, "the T-290 delta is booked as the RETIRED piece of its r4 row (R4-326.RETIRED_0480 "
                                   "/ R4-337.ARCH_WIDTH); this row is its record, never a second correction")
            continue
        if fid == "R4-313":
            faces.append(rec)
            named[fid] = (POINTER, "dome-opening slab-thickness band: r4 OWNED_BY_OTHER_LINE, booked inside the ring "
                                   "rows R4-345 / R4-352 ('inner face = the dome-opening face over the ring depth')")
            continue
        if fid == "R4-316":
            rec["members"] = ["PIECE:ST01-MS1-T-SLAB"]
            rec["basis_note"] = "slab under the MS1-T winders = T-258 piece ST01-MS1-T-SLAB (turn slab 0.2304 .. 0.2496 " \
                                "m3 / 0.16), held in the ST-01 GF parent (C-ST-3 / G2-a)"
            faces.append(rec)
            continue
        if el == "TANK":
            faces.append(rec)
            named[fid] = (DUPVIEW, "the r4 'water-tank walls (B15 20 x 120)' are beam B15 = BM-2F-007 (T-149 R125, "
                                   "0.20 x 1.20 x 2.70; candidate P-C:BEAMS:2F:BAND0006.2 L-713bc64aaa210610e7fe), whose "
                                   "faces part 2 ties (R4-298 .. R4-312); D-44 (up- or downstand) is carried against "
                                   "those faces (F-T293-P3-03); the rest of the tank is not drawn (D-44 / D-52)")
            continue
        if el == "DOME":
            d = next(k for k in ("DOME-TOWER", "DOME-A", "DOME-B") if it.startswith(k))
            dd = "DOME-3" if d == "DOME-TOWER" else d
            if "drum" in it:
                rec["members"] = [f"DRUM:{dd}"]
            elif d == "DOME-TOWER" or "shell" in it:
                rec["members"] = [f"SHELL:{dd}"]
            else:
                rec["members"] = [f"RING:{dd}"]
            faces.append(rec)
            continue
        # STAIR
        if it.startswith("flight and landing side faces"):
            faces.append(rec)
            named[fid] = (F.NAMED, "aggregate over every stair (stringer profiles at the walls and the well), no value: "
                                   "HELD; whether the flights are cast against the walls is not printed")
            continue
        pre = next(k for k in STAIR_PIECE if it.startswith(k))
        piece = STAIR_PIECE[pre] or ("ST03-E1-STEPS" if "riser" in it else "ST03-E1-WAIST")
        rec["members"] = [f"PIECE:{piece}"]
        if piece == "ST03-E1-WAIST":
            rec["basis_note"] = "Checker 2026-10-25 11:05 (T-266 s.4 (3)): concrete waist HELD (G2-w), soffit form " \
                                "NOT_APPLICABLE (section B-B draws the waist on fill); no CONFLICT remains"
        if rec["status"] == CALC and piece not in held_pieces:
            P = stair_pieces(rec, piece, t, p2)
            if P:
                ps = split_row(rec, P)
                faces.extend(ps)
                named.update(named_kinds(ps))
                continue
        faces.append(rec)
    return faces, named


def binding(lines, piece_line):
    b = {"_reason": {}}
    for p, lid in piece_line.items():
        b[f"PIECE:{p}"] = [lid]
    for k, lid in LINE_OF_PIECE.items():
        b[k if ":" in k else f"PIECE:{k}"] = [lid]
    for d in ("DOME-A", "DOME-B"):
        b[f"DRUM:{d}"] = []
        b["_reason"][f"DRUM:{d}"] = "drum: drawn (section B-B 1.30 m), material / thickness not printed (G3-b); the " \
                                    "candidate has no line (Lead 14:15 named omission, T-266 s.4 (2)): no face, no value"
    for u in ("HIDDEN_535_536", "HIDDEN_2CC_2CD"):
        b[f"UNKNOWN:{u}"] = []
        b["_reason"][f"UNKNOWN:{u}"] = "unmarked layer-5 pair (F-T281-03): the member is not identified, no line"
    for m, ids in b.items():
        if m != "_reason":
            for lid in ids:
                if lid not in lines:
                    raise Refused(f"{m}: line {lid} not in the V3.0.18 stair / dome set")
    return b


def build():
    cand = candidate()
    lines, piece_line, held_pieces = v3018_lines(cand)
    t, p2 = t281(), p2_rows()
    check_dup_booked(p2)
    src = sources()
    faces, named = classify(src, t, p2, piece_line, held_pieces)
    b = binding(lines, piece_line)
    out = F.tie(faces, b, lines, named, source=src)
    held = {f"PIECE:{p}" for p in held_pieces} | {f"PIECE:{p}" if ":" not in p else p for p in HELD_LINE_PIECES}
    held |= {m for m, ids in b.items() if m != "_reason" and ids and lines[ids[0]]["evidence_state"] in NOT_MEASURED}
    hold_pieces(out["rows"])
    hold_on_unbooked_pieces(out["rows"], held)
    refuse_measured_on_held(out["rows"], held)
    check_one_view(out["rows"] + [dict(r, members=[r["members"]], m2=_f(r["m2"]), held_from=_f(r["held_from"]))
                                  for r in p2])
    for r in out["rows"]:
        lid = r.get("line_id")
        if lid:
            r["line_v3018"] = lines[lid].get("v3018", "byte-identical to V3.0.16 / V3.0.17")
            r["line_state"] = lines[lid]["evidence_state"]
            if r["status"] == HELD and r.get("held_from") is None and r.get("lo") is None and r.get("m2") is None:
                r.setdefault("held_reason", "HELD in formwork r4 (no value)")
        if r.get("piece_kind") == "HELD" and r["tie"] == F.TIED:
            r["tie_reason"] = "piece HELD on the line: " + r.get("held_reason", "")
    return cand, lines, src, out, held


# ================================================================================================ outputs

KEYS = ["face_id", "revision", "element", "floor", "item", "face_kind", "method", "m2", "lo", "hi", "status",
        "status_in", "members", "tie", "line_id", "line_item_code", "line_element_id", "line_state", "line_v3018",
        "tie_reason", "held_from", "held_reason", "alt_D_m2", "piece_kind", "split_of", "basis_note"]


def reconciliation(out):
    """per r4 row with pieces: printed, tied (O), alternative D, and every other kind -> the cause of each m2"""
    rows = collections.defaultdict(list)
    for r in out["rows"]:
        rows[r.get("split_of") or r["face_id"]].append(r)
    rep = []
    for fid, rs in sorted(rows.items()):
        if len(rs) < 2:
            continue
        k = collections.defaultdict(float)
        for r in rs:
            v = r["m2"] if r["m2"] is not None else (r.get("held_from") or 0.0)
            kind = r["tie"] if r["tie"] != F.TIED else ("TIED_HELD" if r["status"] == HELD else "TIED")
            k[kind] += v
        alt = sum(r.get("alt_D_m2") or 0.0 for r in rs if r["tie"] == F.TIED and r.get("alt_D_m2") is not None)
        src_m2 = sum(v for v in k.values())
        rep.append({"row": fid, "item": rs[0]["item"], "r4_m2": round(src_m2, 6),
                    "by_kind": {a: round(v, 6) for a, v in sorted(k.items())},
                    "tied_alt_D_m2": round(alt, 6) if alt else None,
                    "line_id": next((r["line_id"] for r in rs if r.get("line_id")), None)})
    return rep


def write(outdir=HERE):
    cand, lines, src, out, held = build()
    with (outdir / "FORMWORK_FACE_TO_LINE_T293_P3.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=KEYS, extrasaction="ignore")
        w.writeheader()
        for r in out["rows"]:
            x = dict(r)
            x["members"] = ";".join(r["members"])
            for k in ("m2", "lo", "hi", "held_from", "alt_D_m2"):
                if isinstance(x.get(k), float):
                    x[k] = "%.6f" % x[k]
            w.writerow(x)
    cons = F.consumer(out["rows"], lines, "ARCH_TAKEOFF_V3.0.18 (stair lines split by T-266; dome / ring lines "
                      "byte-identical to V3.0.16)", cand["project"])
    cons["part"] = "3 (stairs, domes, water tank); union with parts 1 and 2: the part-1 NAMED rows R4-317 .. R4-360, " \
                   "T290-MS2-LD / T290-RS-A and the part-2 NAMED rows R4-313 / R4-316 are replaced by the rows here"
    for ln in cons["lines"]:
        alts = [f.get("alt_D_m2") for f in ln["faces"]]
        ln["v3018"] = lines[ln["concrete_line_id"]].get("v3018", "byte-identical to V3.0.16 / V3.0.17")
        ln["alternative_D_soffit_m2"] = round(sum(a for a in alts if a), 6) if any(alts) else None
    for ln in cons["lines"]:
        for f in ln["faces"]:
            src_alt = next((r.get("alt_D_m2") for r in out["rows"] if r["face_id"] == f["face_id"]), None)
            if src_alt is not None:
                f["alt_D_m2"] = src_alt
    (outdir / "T199_FORMWORK_BY_LINE_T293_P3.json").write_text(json.dumps(cons, indent=1, sort_keys=True) + "\n",
                                                               encoding="utf-8")
    vl = {"schema": "T293_P3_V3018_STAIR_DOME_LINES_V1", "derived": f"{T266}: V3.0.16 lines + T-266 records "
          "(t266_inputs.build), part ids by engine.source.boq_line.line_id", "project": cand["project"],
          "lines": [lines[k] for k in sorted(lines)]}
    (outdir / "CANDIDATE_V3018_STAIR_DOME_LINES_T293P3.json").write_text(json.dumps(vl, indent=1, sort_keys=True)
                                                                          + "\n", encoding="utf-8")
    s = summary(cand, lines, src, out, held)
    (outdir / "summary_t293_p3.json").write_text(json.dumps(s, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return s


def summary(cand, lines, src, out, held):
    rows = out["rows"]
    tied = collections.defaultdict(lambda: collections.defaultdict(float))
    for r in rows:
        if r["tie"] == F.TIED:
            v = r["m2"] if r["m2"] is not None else 0.0
            tied[r["line_id"]][r["status"]] += v
    live = sorted(l for l, x in lines.items() if x["evidence_state"] != "NOT_APPLICABLE_WITH_EVIDENCE")
    return {"schema": "T293_P3_SUMMARY_V1", "source_rows": len(src), "pieces": len(rows),
            "by_tie": dict(sorted(collections.Counter(r["tie"] for r in rows).items())),
            "closure": out["closure"],
            "tied_m2_by_line_status": {k: {s: round(v, 6) for s, v in d.items()} for k, d in sorted(tied.items())},
            "live_lines_without_faces": sorted(set(live) - set(tied)),
            "held_pieces": sorted(held),
            "reconciliation": reconciliation(out),
            "inputs_sha256": {p: _sha(ROOT / p)[:8] for p in (
                "research/agents_t264/FORMWORK_LINES_R4.csv", "research/agents_t281/LEDGER_T281.csv",
                "research/agents_t258/LEDGER_T258.csv", "research/agents_t293/CANDIDATE_V3016_CONCRETE_LINES.json",
                "research/agents_t293/FORMWORK_FACE_TO_LINE_T293_P2.csv", "research/agents_t266/t266_inputs.py")}}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.write:
        s = write()
    else:
        cand, lines, src, out, held = build()
        s = summary(cand, lines, src, out, held)
    print(json.dumps({k: s[k] for k in ("source_rows", "pieces", "by_tie")}, indent=1))
    for r in s["reconciliation"]:
        print(r["row"], r["r4_m2"], r["by_kind"], r["tied_alt_D_m2"])


if __name__ == "__main__":
    main()
