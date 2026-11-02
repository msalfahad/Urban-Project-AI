"""T-446 on the development villa: the ceiling and skirting completeness join (T-435, R-T435-1) re-run on the candidate
of record ARCH_TAKEOFF_V3.0.39 (json 8d1bbe5d, T-429 Gate B), with R-T446-1 (join_rerun_v1.py): the floored elements
valued outside B3-01 (lift thresholds B6-07, doorway marble thresholds, held opening strips), the stair-room floor
parts keyed as parts (not merged into their face), the host-face double-ownership check, the stair-room part skirting
from the merged T-441 face table, and the delta against the merged T-435 table (V3.0.37). Research only; nothing is
wired, no candidate or released quantity changes.

    python3 -I research/agents_t446/t446_alsenan.py <dir holding V3_0_39_BOQ_LINES.json> --write   # own run, writes
    python3 -I research/agents_t446/t446_alsenan.py --check                                       # committed closes

V3_0_39_BOQ_LINES.json is reproduced on the Drive copies (Drive "Alsenan chalet project": P7757_DXF_COMPRESSED.zip ->
P7757.dxf sha256 ab54dd55, "ST7757 dxf.dxf" sha256 9f9d1179, decoded into .work/private only) by
research/agents_t167/v304_run.py then research/agents_t429/v3039_run.py. Only line ids, item codes, face ids, states
and quantities are read and committed; no room name, coordinate or drawing content.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
T435 = HERE.parent / "agents_t435"
T441 = HERE.parent / "agents_t441"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(T435))
import ceiling_skirting_join_v1 as J  # noqa: E402
import join_rerun_v1 as R  # noqa: E402
import t435_alsenan as A  # noqa: E402

CANDIDATE = "ARCH_TAKEOFF_V3.0.39"
CANDIDATE_JSON_SHA256_8 = "8d1bbe5d"   # T-429 Gate B pin (board T-446 row)
T435_TABLE_SHA256 = "f9d5087c887aa477f205ca4195886f5a5faa0d6f195ac2bc036e90529709e53e"   # merged c7f85e7a
T441_FACES_SHA256_8 = None   # filled from the file at run time and recorded in the summary
TABLE = HERE / "JOIN_T446.csv"
DELTA = HERE / "DELTA_T446.csv"
SUMMARY = HERE / "summary.json"

# stair-room floor parts that T-421 put on their face's room id: keyed as parts (face~part), as T-418 / T-441 measure
PARTS = {"GF-R31F8AE": ("GF-ST-HALL", "GF-ST-LOBBY030", "GF-ST-CN"), "2F-R4D1B62": ("2F-ST-LOBBY",)}
# the T-435 table's face rows that these parts replace (T-435 carried them as EXTRA on the face id)
RENAMED = {"GF-R31F8AE": ["GF-R31F8AE~GF-ST-HALL", "GF-R31F8AE~GF-ST-LOBBY030", "GF-R31F8AE~GF-ST-CN"],
           "2F-R4D1B62": ["2F-R4D1B62~2F-ST-LOBBY"]}

# floor parts that integration rows add and are still not in V3.0.39 (cross-referenced only)
EXTRA = [e for e in A.EXTRA if e["space_id"] == "GF-RFD4E1D"]
EXTRA[0] = dict(EXTRA[0], source="T-431 QUEUED (T-427 MERGED 65ce8f6d: GF dining floor 4.885 + 0.760 = 5.645); "
                "not in V3.0.39")

# spaces whose layer question cannot be asked yet: (space prefix, layer or None for both) -> cause
UNKNOWN_FLOOR = "UNKNOWN_FLOOR_NOT_ESTABLISHED"
UNKNOWN_HEAD = "UNKNOWN_HEAD_NOT_ESTABLISHED"


def flatten(raw):
    lines = A.flatten(raw)
    for ln in lines:
        parts = PARTS.get(ln["room_id"] or "")
        if parts and J.family_of(ln["item_code"], ln["trade"]) in ("FLOOR", "BED"):
            p = ln["element_id"].split(":")[1] if ":" in ln["element_id"] else ""
            if p not in parts:
                raise SystemExit(f"floor line {ln['line_id']} on {ln['room_id']} names no known part: {ln['element_id']}")
            ln["room_id"] = f"{ln['room_id']}~{p}"
    return lines


def _raw_by_id(raw):
    return {ln["line_id"]: ln for ln in raw}


def faces_t441():
    data = (T441 / "FACES_T441.csv").read_bytes()
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    per = {}
    for r in rows:
        per.setdefault(r["part"], []).append(r)
    out = {p: R.part_skirting(st) for p, st in per.items()}
    return out, hashlib.sha256(data).hexdigest()[:8]


def element_reasons(lines, raw, elements):
    """reasons for the floored elements outside B3-01, each from the line's own calculation inputs / formula"""
    rawid = _raw_by_id(raw)
    rs, unknown = [], {}
    host_ceiling = {"GF-RC99C2A": "L-eb3be58f", "1F-R78C367": "L-43bf1f86", "2F-R4D1B62": "L-dd6930fd"}
    for e in elements:
        sid, ln = e["space_id"], rawid[e["line_id"]]
        calc = ln.get("calculation") or {}
        inp = calc.get("inputs") or {}
        formula = str(calc.get("formula") or "")
        el = (ln.get("location") or {}).get("element_id") or ""
        if e["kind"] == "LIFT_THRESHOLD":
            host = e["host_face"]
            rs += [
                {"space_id": sid, "layer": J.CEILING, "code": "CEILING_ON_HOST_FACE", "line_id": host_ceiling[host],
                 "evidence": f"B6-07 lies on the landing floor in front of the lift door (certain floor part 0.300 m2, "
                 f"T-421 s.2) inside face {host}, whose ceiling line is the face plan area (one surface)"},
                {"space_id": sid, "layer": J.CEILING, "code": "OPENING_SOFFIT_IN_WALL",
                 "evidence": "the position-dependent 0 .. 0.200 m2 in the shaft wall band is under the lift door head "
                 "(register LIFT LANDING THRESHOLD)"},
                {"space_id": sid, "layer": J.SKIRTING, "code": "DOORWAY_STRIP",
                 "evidence": "spans the clear width between the drawn jambs (jambs = B6-06 surround); front edge open "
                 "to the landing floor; no wall face (UP-SKIRT-001 'not across door openings')"},
            ]
            continue
        kind = inp.get("opening_kind") or ""
        kinds = inp.get("opening_kinds") or []
        door = (kind == "DOOR" or kinds == ["DOOR"] or "-THRESHOLD-D-" in el or "THRESHOLD-D-" in el
                or "doorway" in (ln.get("item_en") or "").lower())
        exterior_door = "one side exterior" in str(inp) or "stair room / +9.70 roof" in str(inp)
        if "gate:" in formula:
            unknown[(sid, J.CEILING)] = (UNKNOWN_HEAD, "gate: clear width and host wall not established "
                                         "(T-325 UNRESOLVED; T-326 holds its jambs and head)")
            unknown[(sid, J.SKIRTING)] = (UNKNOWN_HEAD, "as the ceiling: host wall not established")
            continue
        if door or exterior_door:
            ev = (f"floored element in a door opening ({kind or kinds or 'door id ' + el}): the head is the opening "
                  f"soffit / lintel (UP-CEIL-001 'actual eligible surfaces'); the frame closes the strip ends "
                  f"(UP-SKIRT-001 'not across door openings')")
            rs += [{"space_id": sid, "layer": J.CEILING, "code": "OPENING_SOFFIT_IN_WALL", "evidence": ev},
                   {"space_id": sid, "layer": J.SKIRTING, "code": "DOORWAY_STRIP", "evidence": ev}]
            continue
        if kinds == ["PASSAGE"]:
            rs.append({"space_id": sid, "layer": J.CEILING, "code": "OPENING_SOFFIT_IN_WALL",
                       "evidence": "doorless passage strip in the wall thickness: its head is the opening soffit"})
            e["wall_face_lm"] = round(2 * float(inp["wall_t_m"]), 4)
            e["wall_face_status"] = ("HELD: the two jamb returns 2 x wall thickness (URBAN-SKIRTING-OPENING-METHOD "
                                     "doorless jambs, PROVISIONAL); no skirting line names them"
                                     + ("; T-441 / T-447 hold the OP-020 reveal 0.400 lm" if "OP-020" in kinds or
                                        "OP-020" in str(inp.get("opening_ids")) else ""))
            continue
        if inp.get("floor_status") == "NOT_ESTABLISHED":
            for layer in J.LAYERS:
                unknown[(sid, layer)] = (UNKNOWN_FLOOR, "unattributed strip: whether a floor exists is not "
                                         "established (floor_status NOT_ESTABLISHED, BLOCKED_RFI)")
    return rs, unknown


def stair_part_reasons(t441):
    rs = []
    for part, ceil, ceil_ev in (
        ("GF-R31F8AE~GF-ST-HALL", "L-2175a965", "the GF stair room's ceiling parent (BLOCKED_RFI), whose held list "
         "names the top and the flight undersides; the piece over the +1.00 hall is not split out"),
        ("GF-R31F8AE~GF-ST-CN", "L-2175a965", "as the hall; the strip's position (lobby side or under the winders) "
         "is unread (T-418), so the parent holds it"),
        ("2F-R4D1B62~2F-ST-LOBBY", "L-dd6930fd", "the 2F stair room's ceiling parent (BLOCKED_RFI; decor part "
         "L-10e79bd4 5.6258 m2 beside; the lobby's position in the decor part is not shown by the line)"),
    ):
        rs.append({"space_id": part, "layer": J.CEILING, "code": "CEILING_ON_HOST_FACE", "line_id": ceil,
                   "evidence": ceil_ev})
    rs.append({"space_id": "GF-R31F8AE~GF-ST-LOBBY030", "layer": J.CEILING, "code": "UNDER_FLIGHT_SOFFIT",
               "line_id": "L-1fcec332", "evidence": "the +0.30 back-door lobby lies under the +3.50 half landing "
               "(T-418 / T-421 s.1): its ceiling is the landing underside, the ST-01 soffit line (flight / landing "
               "undersides, BLOCKED_RFI); L-2175a965 itself says 'stair soffit pieces are the stair soffit lines'"})
    for part, sk, fpart in (("GF-R31F8AE~GF-ST-HALL", "L-47fa825d", "GF-ST-HALL"),
                            ("GF-R31F8AE~GF-ST-LOBBY030", "L-47fa825d", "GF-ST-LOBBY030"),
                            ("GF-R31F8AE~GF-ST-CN", "L-47fa825d", None),
                            ("2F-R4D1B62~2F-ST-LOBBY", "L-b8d4a7f0", "2F-ST-LOBBY")):
        m = t441.get(fpart) if fpart else None
        ev = (f"the part's wall faces are inside the stair room's skirting parent {sk} (BLOCKED_RFI); T-441 MERGED "
              f"ece154fe measures them: " + (f"{m['drawn_lm']:.3f} lm DRAWING-CONFIRMED, HELD stretches "
                                              f"{m['held_lm']}" if m else "no face read (strip unread, T-418)")
              + "; lane I splits the parent (T-443)")
        rs.append({"space_id": part, "layer": J.SKIRTING, "code": "SKIRTING_ON_HOST_FACE", "line_id": sk,
                   "evidence": ev})
    return rs


def pantry_reasons():
    # T-439 MERGED 2f63773e: the two pantry strips' base is the full-height wet wall tile L-f5c5a1a9 (no skirting);
    # their ceiling line is a lane I proposal (1.700 m2), so the ceiling stays SILENT in the candidate
    ev = "T-439 MERGED 2f63773e: wet pantry walls tiled to the floor (Q-37 A / Q-48 A); no skirting line"
    return [{"space_id": s, "layer": J.SKIRTING, "code": "WET_WALL_TILE_TO_FLOOR", "line_id": "L-f5c5a1a9",
             "evidence": ev} for s in ("GF-SITE-0a31aaa10796d33a", "GF-OP-003-NO-OPENING")]


def build(raw):
    lines = flatten(raw)
    base = J.census(lines, EXTRA)
    elements = R.element_spaces(lines, set(base))
    t441, faces_sha = faces_t441()
    el_rs, unknown = element_reasons(lines, raw, elements)
    spaces = J.census(lines, EXTRA + elements)
    # T-435's doorway-strip reasons apply to its own B3-01 strip spaces only; elements get theirs from their lines
    reasons = A.reasons_for(lines, base) + stair_part_reasons(t441) + pantry_reasons() + el_rs
    reasons = [A._full_id(r, lines) for r in reasons]
    rows = J.join(spaces, lines, reasons)
    rows = R.apply_host_rule(rows, reasons)
    for r in rows:
        if r["status"] == J.OWNED and r["states"] and all(s.startswith("NOT_APPLICABLE") for s in r["states"]):
            r["status"] = "OWNED_NOT_APPLICABLE"
        elif r["status"] in (J.OWNED, J.PARTIAL) and r["line_qty"] is None:
            r["status"] = "OWNED_HELD"
        u = unknown.get((r["space_id"], r["layer"]))
        if u and r["status"] == J.SILENT:
            r["status"], r["unknown_cause"] = u
            r.pop("omission", None)
        elif u:
            raise SystemExit(f"{r['space_id']} {r['layer']}: unknown cause on a row that is {r['status']}")
        r["class"] = next((e["kind"] for e in elements if e["space_id"] == r["space_id"]), "B3-01")
    total = R.census_total({k: v for k, v in spaces.items() if v.floor_lines}, lines)
    return lines, spaces, rows, total, t441, faces_sha


def table(rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["space_id", "class", "floor", "kind", "floor_m2", "layer", "status", "line_ids", "line_states",
                "line_qty", "line_bound", "shortfall_m2", "reasons", "refused", "omission_unit", "omission_value",
                "omission_status", "unknown_cause"])
    for r in rows:
        om = r.get("omission") or {}
        w.writerow([r["space_id"], r["class"], r["floor"], r["kind"],
                    "" if r["floor_m2"] is None else f"{r['floor_m2']:.4f}", r["layer"], r["status"],
                    " ".join(x[:10] for x in r["line_ids"]), " ".join(r["states"]),
                    "" if r["line_qty"] is None else f"{r['line_qty']:.4f}",
                    "" if not r["line_bound"] else f"{r['line_bound'][0]:.4f}..{r['line_bound'][1]:.4f}",
                    f"{r['shortfall_m2']:.4f}" if "shortfall_m2" in r else "", " ".join(r["reasons"]),
                    " ".join(r["refused"]), om.get("unit", ""),
                    "" if om.get("value") is None else f"{om['value']:.4f}", om.get("status", ""),
                    r.get("unknown_cause", "")])
    return buf.getvalue()


def t435_rows():
    data = (T435 / "JOIN_T435.csv").read_bytes()
    assert hashlib.sha256(data).hexdigest() == T435_TABLE_SHA256, "merged T-435 table changed"
    rows = []
    for r in csv.DictReader(io.StringIO(data.decode("utf-8"))):
        rows.append({"space_id": r["space_id"], "layer": r["layer"], "status": r["status"],
                     "line_ids": r["line_ids"].split(), "reasons": r["reasons"].split(),
                     "floor_m2": float(r["floor_m2"]) if r["floor_m2"] else None,
                     "omission": {"value": float(r["omission_value"]) if r["omission_value"] else None}})
    return rows


def delta_table(d):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["space_id", "layer", "change", "from_or_into", "before_status", "before_lines", "before_reasons",
                "after_status", "after_lines", "after_reasons"])
    for c in d["changes"]:
        b, a = c["before"] or {}, c["after"] or {}
        fm = c.get("floor_m2")
        w.writerow([c["space_id"], c["layer"], c["change"], c.get("from") or " ".join(c.get("into") or [])
                    or ("" if not fm else f"floor m2 {fm[0]} -> {fm[1]}"),
                    b.get("status", ""), " ".join(b.get("lines", [])), " ".join(b.get("reasons", [])),
                    a.get("status", ""), " ".join(x[:10] for x in a.get("lines", [])), " ".join(a.get("reasons", []))])
    return buf.getvalue()


def summarise(rows, d, total, t441, faces_sha, sha):
    st = {}
    for r in rows:
        st.setdefault(r["layer"], {}).setdefault(r["status"], 0)
        st[r["layer"]][r["status"]] += 1
    sil = [r for r in rows if r["status"] == J.SILENT]
    return {
        "task": "T-446", "rule": R.RULE, "candidate": CANDIDATE, "candidate_json_sha256_8": sha[:8],
        "baseline": "T-435 JOIN_T435.csv on ARCH_TAKEOFF_V3.0.37 (733f2efb), table sha " + T435_TABLE_SHA256[:8],
        "t441_faces_sha256_8": faces_sha, "t441_part_skirting": t441,
        "spaces": len({r["space_id"] for r in rows}),
        "spaces_by_class": {c: len({r["space_id"] for r in rows if r["class"] == c})
                            for c in sorted({r["class"] for r in rows})},
        "status_counts": st, "census_total": total,
        "silent_omissions": [{"space_id": r["space_id"], "layer": r["layer"], "floor_m2": r["floor_m2"],
                              "omission": r["omission"], "source": r["source"]} for r in sil],
        "unknown": [{"space_id": r["space_id"], "layer": r["layer"], "status": r["status"],
                     "cause": r["unknown_cause"]} for r in rows if "unknown_cause" in r],
        "double_owned": [r["space_id"] + "/" + r["layer"] for r in rows if r["status"] == J.DOUBLE],
        "overlap_line_ids": J.overlap(rows),
        "delta_counts": {k: sum(1 for c in d["changes"] if c["change"] == k)
                         for k in ("NEW", "GONE", "SPLIT", "SPLIT_FROM", "OWNER_CHANGED",
                                                                "FLOOR_M2_CHANGED")},
        "silent_before": d["silent_before"], "silent_after": d["silent_after"],
        "table_sha256": hashlib.sha256(table(rows).encode()).hexdigest(),
        "delta_sha256": hashlib.sha256(delta_table(d).encode()).hexdigest(),
    }


def main(argv):
    if argv and argv[0] == "--check":
        s = json.loads(SUMMARY.read_text(encoding="utf-8"))
        assert hashlib.sha256(TABLE.read_bytes()).hexdigest() == s["table_sha256"], "table does not reproduce"
        assert hashlib.sha256(DELTA.read_bytes()).hexdigest() == s["delta_sha256"], "delta does not reproduce"
        assert s["candidate_json_sha256_8"] == CANDIDATE_JSON_SHA256_8
        print("committed tables close:", s["table_sha256"][:8], s["delta_sha256"][:8])
        return 0
    data = (Path(argv[0]) / "V3_0_39_BOQ_LINES.json").read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if sha[:8] != CANDIDATE_JSON_SHA256_8:
        raise SystemExit(f"candidate json {sha[:8]} is not the pinned {CANDIDATE_JSON_SHA256_8}")
    raw = json.loads(data)
    raw = raw["lines"] if isinstance(raw, dict) else raw
    lines, spaces, rows, total, t441, faces_sha = build(raw)
    d = R.delta(t435_rows(), rows, RENAMED)
    s = summarise(rows, d, total, t441, faces_sha, sha)
    print(table(rows))
    print(delta_table(d))
    print(json.dumps(s, indent=1, ensure_ascii=True))
    if "--write" in argv:
        TABLE.write_text(table(rows), encoding="utf-8")
        DELTA.write_text(delta_table(d), encoding="utf-8")
        SUMMARY.write_text(json.dumps(s, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
