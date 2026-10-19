"""LABEL CENSUS (T-004a): every room label of a plan drawing against what the architectural route made of it.

Read-only diagnostic (UP-QTY-STATUS-001: every labelled space is reported once). Nothing is measured here and no
engine output is changed; the census only looks up each label in the route's own outputs:

    census(texts, regions, rooms, coverage, unresolved=(), word=None) -> {"labels": [...], "unread": [...], "summary"}

    texts       the architectural texts of the drawing (tools/arch_intake.read_arch: id, value, encoding, x, y)
    regions     the plan regions of the run (region_id, floor, box in drawing units)
    rooms       the run's rooms (room_id, face_id, floor, codes, polygon / hole_polygons in drawing units)
    coverage    the run's ARCH_COMPLETENESS_V1 records (physical_regions.faces: face_id, state, category)
    unresolved  the run's unresolved / RFI records (a label whose text id is named there is HELD, not silent)
    word        the room vocabulary the run used (None: arch_rooms.room_word, the vocabulary of ARCH_TAKEOFF_V2.9)

A text is a room label when the vocabulary gives it a room code. Each label inside a plan region gets one status:

    MEASURED         inside a room whose face the coverage ledger accounts as LINE (a measured BOQ line)
    HELD             inside a room whose face is RFI, or its text id is named in an unresolved record
    UNSUPPORTED      inside a room whose face the ledger EXCLUDES (shaft, wall mass, ...), category kept
    (a face with several ledger entries: a VOID label reads the face's VOID part; any other label the strongest
    entry, LINE before RFI before EXCLUDED)
    SILENT_OMISSION  none of the above: inside no room of its floor (cause NO_ROOM), inside a room whose codes do not
                     carry the label's code (CODE_NOT_ON_ROOM), or inside a room with no coverage record
                     (NO_COVERAGE_RECORD). Missing never becomes measured or zero.

Texts the reader could not decode (encoding SHX_UNMAPPED) inside a plan region are counted as UNREAD_SHX, never
guessed (a later decoder reads them). Texts outside every plan region (elevations, title blocks) are out of scope.
General: no layer, room or project name is coded here; the drawing units are the run's own (polygons and text
points are compared in the same units, so mm and m drawings read alike).

CLI (prints the summary and writes the full census as JSON):
    python3 -I tools/label_census.py DRAWING.dxf --out census.json [--method ARCH_TAKEOFF_V2.9]
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

POLICY = "URBAN_LABEL_CENSUS_V1"
RULE = "UP-QTY-STATUS-001"
STATUSES = ("MEASURED", "HELD", "UNSUPPORTED", "SILENT_OMISSION")
STATE_STATUS = {"LINE": "MEASURED", "RFI": "HELD", "EXCLUDED": "UNSUPPORTED"}
UNREAD = ("SHX_UNMAPPED",)


def _inside(x, y, poly):
    """even-odd point in polygon (vertices in any order or orientation: rotated and mirrored plans read alike)."""
    ins = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i][:2], poly[(i + 1) % n][:2]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            ins = not ins
    return ins


def _in_box(t, b):
    return b[0] <= t["x"] <= b[2] and b[1] <= t["y"] <= b[3]


def _region_of(t, regions):
    for r in regions:
        if r.get("box") and _in_box(t, r["box"]):
            return r
    return None


def _room_of(t, rooms):
    """-> the rooms whose polygon holds the text point and none of whose holes does."""
    return [r for r in rooms if r.get("polygon") and _inside(t["x"], t["y"], r["polygon"]) and
            not any(_inside(t["x"], t["y"], h) for h in (r.get("hole_polygons") or ()))]


def _face_states(coverage):
    """face_id -> every (state, category) the coverage ledger gives the face (one face can hold a measured floor, an
    excluded void and a stair seen from below)."""
    out = {}
    for c in coverage or ():
        for f in ((c.get("physical_regions") or {}).get("faces") or ()):
            out.setdefault(f["face_id"], []).append((f.get("state"), f.get("category")))
    return out


def _pick(entries, code):
    """the ledger entry a label reads: a VOID label the face's excluded VOID part; any other label the strongest
    accounting of its face (a measured line, else an RFI, else an exclusion)."""
    if code == "VOID":
        for e in entries:
            if e[1] == "VOID":
                return e
    for want in ("LINE", "RFI", "EXCLUDED"):
        for e in entries:
            if e[0] == want:
                return e
    return entries[0]


def _named_ids(unresolved):
    """every token of the unresolved / RFI records that could be a text id (a held label must be named there, never
    inferred): split on every character that is not a letter, digit, '_' or '-'."""
    import re
    return set(re.split(r"[^0-9A-Za-z_\-]+", json.dumps(list(unresolved or ()), default=str)))


def census(texts, regions, rooms, coverage, unresolved=(), word=None):
    if word is None:
        from engine.source import arch_rooms as AR
        word = AR.room_word
    states = _face_states(coverage)
    named = _named_ids(unresolved)
    labels, unread = [], []
    for t in texts or ():
        reg = _region_of(t, regions or ())
        if reg is None:
            continue
        if t.get("encoding") in UNREAD:
            unread.append({"text_id": t["id"], "region_id": reg["region_id"], "floor": reg.get("floor"),
                           "status": "UNREAD_SHX", "font": t.get("font")})
            continue
        code, _ = word(t.get("value") or "")
        if not code:
            continue
        rec = {"text_id": t["id"], "text": t.get("value"), "code": code, "region_id": reg["region_id"],
               "floor": reg.get("floor"), "room_id": None, "face_id": None, "status": None, "cause": None}
        held_by_name = str(t["id"]) in named
        own = [r for r in (rooms or ()) if r.get("floor") in (None, reg.get("floor"))]
        hits = _room_of(t, own)
        if not hits:
            rec["status"], rec["cause"] = ("HELD", "NAMED_IN_UNRESOLVED") if held_by_name else \
                ("SILENT_OMISSION", "NO_ROOM")
            labels.append(rec)
            continue
        room = min(hits, key=lambda r: abs(r.get("area_m2") or 0.0))     # nested: the innermost room
        rec.update(room_id=room.get("room_id"), face_id=room.get("face_id"))
        st = states.get(room.get("face_id"))
        if code not in (room.get("codes") or ()) and code not in (room.get("codes_with_void") or ()):
            rec["status"], rec["cause"] = ("HELD", "NAMED_IN_UNRESOLVED") if held_by_name else \
                ("SILENT_OMISSION", "CODE_NOT_ON_ROOM")
        elif st is None:
            rec["status"], rec["cause"] = ("HELD", "NAMED_IN_UNRESOLVED") if held_by_name else \
                ("SILENT_OMISSION", "NO_COVERAGE_RECORD")
        else:
            st = _pick(st, code)
            rec["status"] = STATE_STATUS.get(st[0], "SILENT_OMISSION")
            rec["cause"] = f"LEDGER_{st[0]}" + (f":{st[1]}" if st[1] else "")
        labels.append(rec)
    by_floor = {}
    for rec in labels:
        by_floor.setdefault(rec["floor"], Counter())[rec["status"]] += 1
    for u in unread:
        by_floor.setdefault(u["floor"], Counter())["UNREAD_SHX"] += 1
    summary = {"policy": POLICY, "rule": RULE, "labels": len(labels),
               "by_status": {s: sum(1 for r in labels if r["status"] == s) for s in STATUSES},
               "unread_shx": len(unread),
               "silent_by_cause": dict(Counter(r["cause"] for r in labels if r["status"] == "SILENT_OMISSION")),
               "by_floor": {str(k): dict(v) for k, v in sorted(by_floor.items(), key=lambda kv: str(kv[0]))}}
    return {"labels": labels, "unread": unread, "summary": summary}


def census_of_run(result):
    """census of one arch_compute result (the (boq, arch, intake) tuple of tools/urban_boq_m9.arch_compute)."""
    boq, arch, intake = result
    return census(intake.get("texts") or (), arch.get("regions") or (), arch.get("rooms") or (),
                  arch.get("coverage") or (), boq.get("unresolved") or ())


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("drawing")
    ap.add_argument("--out", required=True)
    ap.add_argument("--method", default="ARCH_TAKEOFF_V2.9")
    a = ap.parse_args(argv)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools import urban_boq_m9 as M
    out = census_of_run(M.arch_compute(a.drawing, method=a.method))
    out["summary"]["method"] = a.method
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps(out["summary"], ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
