"""T-435 on the development villa: the ceiling and skirting completeness join for every floored space of the candidate of
record ARCH_TAKEOFF_V3.0.37 (+ the floor parts the READY / QUEUED integration rows add: T-421 stair-room floors from
T-418, T-431 GF dining piece from T-427). Research only; nothing is wired, no candidate or released quantity changes.

    python3 -I research/agents_t435/t435_alsenan.py <dir holding V3_0_37_BOQ_LINES.json> --write   # own run, writes
    python3 -I research/agents_t435/t435_alsenan.py --check                                       # committed closes

The V3_0_37_BOQ_LINES.json is reproduced on the Drive copies (Drive "Alsenan chalet project": P7757_DXF_COMPRESSED.zip
-> P7757.dxf sha256 ab54dd55, "ST7757 dxf.dxf" sha256 9f9d1179, decoded into .work/private only) by
research/agents_t167/v304_run.py then research/agents_t420/v3037_run.py. Only line ids, item codes, face ids, states and
quantities are read and committed; no room name, coordinate or drawing content.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ceiling_skirting_join_v1 as J  # noqa: E402

CANDIDATE = "ARCH_TAKEOFF_V3.0.37"
CANDIDATE_JSON_SHA256_8 = "733f2efb"  # T-420 merged pin (board T-421 row: 'bind to V3.0.37 json 733f2efb')
TABLE = HERE / "JOIN_T435.csv"
SUMMARY = HERE / "summary.json"

# sub-face floor lines (element ids start 'HL:'): the face they lie in, from the merged ledgers that made them
HOSTS = {
    "HL:FLOOR_SCOPE:UNDER_STAIR:GF:GF-RC99C2A-UNDER-STAIR": ("GF-RC99C2A~UNDER-STAIR", "GF-RC99C2A"),   # T-414 / T-427
    "HL:FLOOR_SCOPE:WET:GF:GF-PANTRY-RC99C2A-PART": ("GF-RC99C2A~PANTRY", "GF-RC99C2A"),                # Q-37 A, T-286
    "HL:FLOOR_SCOPE:WET:GF:GF-PANTRY-RC06FED": ("GF-RC06FED", "GF-RC06FED"),     # the pantry face's own floor (Q-37 A)
    "HL:FLOOR_SCOPE:WET:GF:SITE-0a31aaa10796d33a": ("GF-SITE-0a31aaa10796d33a", None),   # pantry strip (T-427 1.100)
    "HL:FLOOR_SCOPE:TO_WET:GF:GF-OP-003-NO-OPENING": ("GF-OP-003-NO-OPENING", None),     # pantry opening strip 0.600
}

# floor parts that integration rows add (not yet in V3.0.37); their figures are the Checker-merged ledgers'
EXTRA = [
    {"space_id": "GF-R31F8AE", "floor": "GF", "m2": 4.805 + 1.3225, "kind": "DRY",
     "source": "T-421 READY 62daaaa6 (T-418 MERGED 361f6e47: GF stair hall +1.00 4.8050 + back lobby +0.30 1.3225)"},
    {"space_id": "2F-R4D1B62", "floor": "2F", "m2": 2.500, "kind": "DRY",
     "source": "T-421 READY 62daaaa6 (T-418 MERGED 361f6e47: 2F stair lobby 2.5000, porcelain Q-70 A)"},
    {"space_id": "GF-RFD4E1D", "floor": "GF", "m2": 5.645, "kind": "DRY",
     "source": "T-431 QUEUED (T-427 MERGED 65ce8f6d: GF dining floor along the south facade 4.885 + 0.760 = 5.645)",
     "wall_face_lm": 3.90, "wall_face_status": "DRAWING-CONFIRMED (T-427 Checker: wall 2.70 + column 2FCF faces 1.20; "
     "T-431 plans it on L-71e2e002)"},
]

# reasons with evidence; a reason that cites a line is checked against V3.0.37 (missing / wrong family -> REFUSED)
DOOR_STRIP_EVIDENCE = ("candidate element ':doorway strip' (floor in the wall thickness under a door: the head is the "
                       "opening soffit / lintel, UP-CEIL-001 'actual eligible surfaces'; UP-SKIRT-001 'not across door "
                       "openings')")


def reasons_for(lines, spaces):
    rs = []
    for sid in spaces:
        if "-STRIP-" in sid:
            rs.append({"space_id": sid, "layer": J.CEILING, "code": "OPENING_SOFFIT_IN_WALL",
                       "evidence": DOOR_STRIP_EVIDENCE})
            rs.append({"space_id": sid, "layer": J.SKIRTING, "code": "DOORWAY_STRIP", "evidence": DOOR_STRIP_EVIDENCE})
    rs += [
        {"space_id": "GF-RC99C2A~UNDER-STAIR", "layer": J.CEILING, "code": "UNDER_FLIGHT_SOFFIT",
         "line_id": "L-c77e3887", "evidence": "floor under the GF round stair inside the open room (T-414 / T-427 "
         "'under-stair 2.07'); above it is the flight's underside, the ST-02 soffit line (BLOCKED_RFI, RFI-S27)"},
        {"space_id": "GF-RC99C2A~UNDER-STAIR", "layer": J.SKIRTING, "code": "SKIRTING_ON_HOST_FACE",
         "line_id": "L-71e2e002", "evidence": "the part lies inside face GF-RC99C2A; the face's skirting runs on the "
         "face boundary (UP-SKIRT-001)"},
        {"space_id": "GF-RC99C2A~PANTRY", "layer": J.CEILING, "code": "CEILING_ON_HOST_FACE", "line_id": "L-eb3be58f",
         "evidence": "the pantry part (Q-37 A) lies inside face GF-RC99C2A, whose ceiling line is the face plan area "
         "110.922696 less what is not decor (T-284 / T-335 fill), with classes DRY + WET"},
        {"space_id": "GF-RC99C2A~PANTRY", "layer": J.SKIRTING, "code": "SKIRTING_ON_HOST_FACE", "line_id": "L-71e2e002",
         "evidence": "inside face GF-RC99C2A (its boundary skirting); whether the wet pantry walls take skirting or "
         "tile is NOT settled here (cross-check, s.5)"},
    ]
    return [_full_id(r, lines) for r in rs]


def _full_id(r, lines):
    if "line_id" in r:
        m = [ln["line_id"] for ln in lines if ln["line_id"].startswith(r["line_id"])]
        r = dict(r, line_id=m[0] if len(m) == 1 else r["line_id"])
    return r


def flatten(raw):
    out = []
    for ln in raw:
        loc = ln.get("location") or {}
        b = ln.get("bounded_range")
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "trade": ln.get("trade"),
                    "unit": ln.get("unit"), "floor": loc.get("floor", ""), "room_id": loc.get("room_id"),
                    "element_id": loc.get("element_id", ""), "evidence_state": ln.get("evidence_state"),
                    "measured_net": ln.get("measured_net"),
                    "bounded_range": (b.get("low"), b.get("high")) if isinstance(b, dict) else b})
    for ln in out:
        if ln["room_id"] is None:
            hit = [k for k in HOSTS if ln["element_id"] == k or ln["element_id"].startswith(k + ":")]
            if len(hit) == 1:
                ln["room_id"] = HOSTS[hit[0]][0]
    return out


def build(lines):
    # a skirting / ceiling line in state NOT_APPLICABLE* is an explicit 'no item here, with evidence' row of its own
    # family: it OWNS the layer for the join (not an omission), and carries no quantity
    spaces = J.census(lines, EXTRA)
    rows = J.join(spaces, lines, reasons_for(lines, spaces))
    for r in rows:
        if r["status"] == J.OWNED and r["states"] and all(s.startswith("NOT_APPLICABLE") for s in r["states"]):
            r["status"] = "OWNED_NOT_APPLICABLE"
        elif r["status"] in (J.OWNED, J.PARTIAL) and r["line_qty"] is None:
            r["status"] = "OWNED_HELD"
    # reverse join: ceiling / skirting lines on a face with no floor-finish line (informational)
    floored = set(spaces)
    reverse = sorted({(ln["room_id"], ln["item_code"], ln["line_id"], ln["measured_net"]) for ln in lines
                      if J.family_of(ln["item_code"], ln["trade"]) in (J.CEILING, J.SKIRTING)
                      and ln["room_id"] not in floored}, key=lambda t: (str(t[0]), t[2]))
    return spaces, rows, reverse


def table(rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["space_id", "floor", "kind", "floor_m2", "source", "layer", "status", "line_ids", "line_states",
                "line_qty", "line_bound", "shortfall_m2", "reasons", "refused", "omission_unit", "omission_value",
                "omission_status"])
    for r in rows:
        om = r.get("omission") or {}
        w.writerow([r["space_id"], r["floor"], r["kind"], "" if r["floor_m2"] is None else f"{r['floor_m2']:.4f}",
                    r["source"], r["layer"], r["status"], " ".join(x[:10] for x in r["line_ids"]),
                    " ".join(r["states"]), "" if r["line_qty"] is None else f"{r['line_qty']:.4f}",
                    "" if not r["line_bound"] else f"{r['line_bound'][0]:.4f}..{r['line_bound'][1]:.4f}",
                    f"{r['shortfall_m2']:.4f}" if "shortfall_m2" in r else "", " ".join(r["reasons"]),
                    " ".join(r["refused"]), om.get("unit", ""),
                    "" if om.get("value") is None else f"{om['value']:.4f}", om.get("status", "")])
    return buf.getvalue()


def summarise(rows, reverse, sha):
    st = {}
    for r in rows:
        st.setdefault(r["layer"], {}).setdefault(r["status"], 0)
        st[r["layer"]][r["status"]] += 1
    sil = [r for r in rows if r["status"] == J.SILENT]
    part = [r for r in rows if r["status"] == J.PARTIAL]
    return {
        "task": "T-435", "candidate": CANDIDATE, "candidate_json_sha256_8": sha[:8], "spaces": len({r["space_id"] for r in rows}),
        "status_counts": st,
        "silent_omissions": [{"space_id": r["space_id"], "layer": r["layer"], "floor_m2": r["floor_m2"],
                              "omission": r["omission"], "source": r["source"]} for r in sil],
        "ceiling_silent_m2": round(sum(r["floor_m2"] or 0 for r in sil if r["layer"] == J.CEILING), 4),
        "skirting_silent_spaces": sum(1 for r in sil if r["layer"] == J.SKIRTING),
        "ceiling_partial": [{"space_id": r["space_id"], "floor_m2": r["floor_m2"], "ceiling_m2": r["line_qty"],
                             "shortfall_m2": r["shortfall_m2"]} for r in part],
        "double_owned": [r["space_id"] + "/" + r["layer"] for r in rows if r["status"] == J.DOUBLE],
        "overlap_line_ids": J.overlap(rows),
        "reverse_no_floor_line": [{"room_id": a, "item_code": b, "line_id": c[:10], "qty": d} for a, b, c, d in reverse],
        "table_sha256": hashlib.sha256(table(rows).encode()).hexdigest(),
    }


def main(argv):
    if argv and argv[0] == "--check":
        s = json.loads(SUMMARY.read_text(encoding="utf-8"))
        assert hashlib.sha256(TABLE.read_bytes()).hexdigest() == s["table_sha256"], "table does not reproduce"
        assert s["candidate_json_sha256_8"] == CANDIDATE_JSON_SHA256_8
        print("committed table closes:", s["table_sha256"][:8])
        return 0
    src = Path(argv[0]) / "V3_0_37_BOQ_LINES.json"
    data = src.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if sha[:8] != CANDIDATE_JSON_SHA256_8:
        raise SystemExit(f"candidate json {sha[:8]} is not the pinned {CANDIDATE_JSON_SHA256_8}")
    raw = json.loads(data)
    raw = raw["lines"] if isinstance(raw, dict) else raw
    lines = flatten(raw)
    spaces, rows, reverse = build(lines)
    s = summarise(rows, reverse, sha)
    print(table(rows))
    print(json.dumps({k: v for k, v in s.items() if k != "reverse_no_floor_line"}, indent=1, ensure_ascii=True))
    print("reverse:", s["reverse_no_floor_line"])
    if "--write" in argv:
        TABLE.write_text(table(rows), encoding="utf-8")
        SUMMARY.write_text(json.dumps(s, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
