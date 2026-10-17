"""Every hypothesis a frozen pass made becomes an inspection candidate.

    python -m tools.a18_pass_d_candidates --register <zone register>.json \
        --report <the frozen pass report>.md --out <candidates>.json

A local challenge that only revisits what a pass ADMITTED it was unsure of
cannot find what the pass was confidently wrong about. So this takes every
hypothesis in the register - every physical space, every functional zone,
every floor-finish trade zone - and makes a candidate of each, by one rule,
with no room named and none privileged.

Geometry may come from exactly three places, all of them the frozen pass's
own:

    STATED_EXTENT               the box the pass stated
    LABEL_POINT                 a fixed box centred on the label position
                                it stated, for a space it gave no extent
    UNION_OF_MEMBER_GEOMETRY    for a zone, the union of its members'
                                geometry - because a zone is what the pass
                                said it is made of

and never from a benchmark, a corrected geometry, a take-off, a known
error, or any later pass.

Confidence is read off the pass's OWN markers in its own report, so that
HIGH_CONFIDENCE -> CHALLENGED can be counted afterwards without anybody
deciding retrospectively how sure it had been.

The output is shaped so that tools.a18_local_crops can cut it unchanged:
the same padding, the same zoom, the same two framings as any other local
challenge.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from engine import export_provenance as prov

# One rule for a space the pass located but did not measure.
LABEL_HALF_PX = 400

HIGH = "HIGH_CONFIDENCE"
MEDIUM = "MEDIUM_CONFIDENCE"
LOW = "LOW_CONFIDENCE"
UNRESOLVED = "UNRESOLVED"

PHYSICAL = "PHYSICAL_SPACE"
FUNCTIONAL = "FUNCTIONAL_ZONE"
TRADE = "FLOOR_FINISH_TRADE_ZONE"

ENTRY = re.compile(r"^([a-z])\)\s", re.M)

SEEN, INFERRED, NOT_EST, NONE_STATED = (
    "SEEN", "INFERRED", "NOT_ESTABLISHED", "NONE_STATED")


def _entries(report_text) -> dict:
    """The lettered physical-space entries of section 1, as written."""
    section = report_text.split("1. PHYSICAL SPACES", 1)[-1]
    section = section.split("2. FUNCTIONAL ZONES", 1)[0]
    out, marks = {}, list(ENTRY.finditer(section))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(section)
        out[m.group(1)] = section[m.start():end].strip()
    return out


def _lines(report_text, header, nxt) -> list:
    section = report_text.split(header, 1)[-1].split(nxt, 1)[0]
    return [ln.strip() for ln in section.splitlines()
            if ln.strip().startswith(("-", "Z"))]


def marker(text) -> str:
    """The marker the pass itself wrote, or NONE_STATED."""
    up = (text or "").upper()
    if "NOT ESTABLISHED" in up:
        return NOT_EST
    if "INFERRED" in up:
        return INFERRED
    if "SEEN" in up:
        return SEEN
    return NONE_STATED


def confidence(text) -> str:
    """Map the pass's own marker into the four required labels.

    LOW_CONFIDENCE here means THE PASS STATED NO MARKER for this
    hypothesis. It does not mean the pass was unsure - deciding that
    retrospectively is exactly what this must not do - so the raw marker
    travels beside it in `pass_b_marker`.
    """
    return {NOT_EST: UNRESOLVED, INFERRED: MEDIUM, SEEN: HIGH,
            NONE_STATED: LOW}[marker(text)]


NOT_A_TOKEN = {"UNLABELLED", "UNKNOWN", ""}


def _label_token(label) -> str:
    """The pass's own English label, used to find its other assertions."""
    for part in reversed(str(label or "").split("/")):
        token = re.sub(r"[^A-Za-z. ]", "", part).strip()
        if len(token) >= 3 and token.upper() == token or len(token) >= 4:
            up = token.upper()
            return "" if up in NOT_A_TOKEN else up
    return ""


def _label_box(point) -> list:
    x, y = point
    return [x - LABEL_HALF_PX, y - LABEL_HALF_PX,
            x + LABEL_HALF_PX, y + LABEL_HALF_PX]


def _union(boxes) -> list:
    return [min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes)]


def build(register_path, report_path) -> dict:
    reg = json.loads(Path(register_path).read_text(encoding="utf-8"))
    text = Path(report_path).read_text(encoding="utf-8")
    entries = _entries(text)

    open_plan = _lines(text, "3. OPEN-PLAN RELATIONSHIPS",
                       "LEVEL CHANGES")
    geom: dict = {}
    rows = []
    for zone in reg["physical_spaces"]:
        zid = zone["zone_id"]
        letter = zid.split("-", 1)[1][0]
        source_text = entries.get(letter, "")
        if zone.get("box_as_stated"):
            box, how = list(zone["box_as_stated"]), "STATED_EXTENT"
        else:
            box, how = _label_box(zone["label_point"]), "LABEL_POINT"
        geom[zid] = box
        # A space's confidence is what the pass marked about it ANYWHERE it
        # asserted a boundary for it, not only in its catalogue entry: the
        # strongest claims in this report live in the open-plan section. The
        # lines folded in are recorded, so the derivation can be checked.
        token = _label_token(zone.get("label_as_drawn", ""))
        elsewhere = [ln for ln in open_plan
                     if token and token in ln.upper()] if token else []
        own = marker(source_text)
        spread = Counter(marker(ln) for ln in elsewhere)
        # Its own catalogue entry decides where it states a marker. Only
        # where it states none do the boundary lines decide, and then by
        # WHICH MARKER IT USED MOST - because one hedge about one feature
        # is not a verdict on the whole hypothesis, and letting it be one
        # turned every well-evidenced space with a single open question
        # into UNRESOLVED.
        if own != NONE_STATED:
            chosen = own
        elif spread:
            chosen = spread.most_common(1)[0][0]
        else:
            chosen = NONE_STATED
        rows.append({
            "candidate_id": zid,
            "hypothesis_kind": PHYSICAL,
            "source_zone_id": zid,
            "source_entry_letter": letter,
            "geometry_source": how,
            "box": box,
            "pass_b_confidence": {NOT_EST: UNRESOLVED, INFERRED: MEDIUM,
                                  SEEN: HIGH, NONE_STATED: LOW}[chosen],
            "pass_b_marker": chosen,
            "pass_b_markers_seen_in_boundary_lines": dict(spread),
            "marker_in_its_own_catalogue_entry": marker(source_text),
            "confidence_sources": {
                "catalogue_entry": f"section 1 ({letter})",
                "open_plan_lines_folded_in": len(elsewhere),
                "matched_on_label_token": token},
            "pass_b_statement": source_text,
            "pass_b_boundary_statements": elsewhere,
            "label_as_drawn": zone.get("label_as_drawn", ""),
        })

    fz_lines = _lines(text, "2. FUNCTIONAL ZONES", "3. OPEN-PLAN")
    for zone in reg["functional_zones"]:
        boxes = [geom[m] for m in zone["members"] if m in geom]
        if not boxes:
            continue
        name = zone["name"].split("(")[0].strip()
        src = next((ln for ln in fz_lines if name[:14].upper() in ln.upper()),
                   zone.get("status", ""))
        rows.append({
            "candidate_id": zone["fz_id"], "hypothesis_kind": FUNCTIONAL,
            "source_zone_id": zone["fz_id"],
            "geometry_source": "UNION_OF_MEMBER_GEOMETRY",
            "members": zone["members"], "box": _union(boxes),
            "pass_b_confidence": confidence(
                src + " " + zone.get("status", "")),
            "pass_b_marker": marker(src + " " + zone.get("status", "")),
            "pass_b_statement": src or zone.get("evidence", ""),
        })

    tz_lines = _lines(text, "4. LIKELY FLOORING TRADE ZONES", "5. KITCHENS")
    for zone in reg["floor_finish_trade_zones"]:
        boxes = [geom[m] for m in zone["members"] if m in geom]
        if not boxes:
            continue
        src = next((ln for ln in tz_lines
                    if ln.upper().startswith(("- " + zone["tz_id"] + " ",
                                              zone["tz_id"] + " "))),
                   zone.get("status", ""))
        rows.append({
            "candidate_id": zone["tz_id"], "hypothesis_kind": TRADE,
            "source_zone_id": zone["tz_id"],
            "geometry_source": "UNION_OF_MEMBER_GEOMETRY",
            "members": zone["members"], "box": _union(boxes),
            "pass_b_confidence": confidence(
                src + " " + zone.get("status", "")),
            "pass_b_marker": marker(src + " " + zone.get("status", "")),
            "pass_b_statement": src or zone.get("evidence", ""),
        })

    doc = {
        "MODEL": "EVERY_HYPOTHESIS_BECOMES_A_CANDIDATE_V1",
        "run_id": reg.get("run_id", ""),
        "derived_from": {"register": Path(register_path).name,
                         "report": Path(report_path).name,
                         "state": "FROZEN"},
        "rule": {
            "coverage": ("every physical space, functional zone and trade "
                         "zone in the frozen register becomes one candidate. "
                         "No room is named, none is privileged, none is "
                         "skipped"),
            "geometry_may_come_only_from": [
                "STATED_EXTENT", "LABEL_POINT", "UNION_OF_MEMBER_GEOMETRY"],
            "geometry_never_comes_from": [
                "benchmark geometry", "corrected geometry", "a manual "
                "take-off", "known errors", "any later pass", "the harness "
                "conversation"],
            "label_box": f"a fixed {2 * LABEL_HALF_PX}px box centred on the "
                         "stated label position, for a space the pass "
                         "located but did not measure",
            "confidence": ("read off the pass's OWN markers in its own "
                           "report: NOT ESTABLISHED -> UNRESOLVED, "
                           "INFERRED -> MEDIUM, SEEN -> HIGH, no marker -> "
                           "LOW. Never assigned retrospectively"),
            "low_confidence_means": ("the pass stated NO marker for this "
                                     "hypothesis. It does not mean the pass "
                                     "was unsure - the raw marker travels "
                                     "beside it as pass_b_marker"),
            "where_a_space_marker_is_read_from": (
                "its catalogue entry in section 1 where that states a "
                "marker. Where it states none, the open-plan lines in "
                "section 3 that name its label decide, by the marker used "
                "MOST among them - because one hedge about one feature is "
                "not a verdict on the whole hypothesis. The full "
                "distribution travels with each candidate as "
                "pass_b_markers_seen_in_boundary_lines"),
        },
        "counts": {
            "candidates": len(rows),
            "by_kind": {k: sum(1 for r in rows if r["hypothesis_kind"] == k)
                        for k in (PHYSICAL, FUNCTIONAL, TRADE)},
            "by_pass_b_confidence": {
                c: sum(1 for r in rows if r["pass_b_confidence"] == c)
                for c in (HIGH, MEDIUM, LOW, UNRESOLVED)},
            "by_geometry_source": {
                s: sum(1 for r in rows if r["geometry_source"] == s)
                for s in ("STATED_EXTENT", "LABEL_POINT",
                          "UNION_OF_MEMBER_GEOMETRY")},
        },
        "candidates": rows,
        # shaped so that tools.a18_local_crops cuts it unchanged
        "needs_local_crop": [
            {"nlc_id": r["candidate_id"],
             "requested_at": f"{r['hypothesis_kind']} hypothesis "
                             f"{r['source_zone_id']}",
             "REASON_FOR_LOCAL_CROP": (
                 f"uniform false-confidence challenge of the frozen pass's "
                 f"{r['hypothesis_kind']} hypothesis for "
                 f"{r['source_zone_id']}"),
             "coordinates_as_stated": {
                 "kind": r["geometry_source"], "box": r["box"],
                 "quoted": r["pass_b_statement"][:400]}}
            for r in rows],
    }
    doc["CANDIDATE_SET_HASH"] = prov.canonical_sha256(doc)
    return doc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--register", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    doc = build(a.register, a.report)
    Path(a.out).write_text(json.dumps(doc, indent=2, ensure_ascii=False)
                           + "\n", encoding="utf-8")
    print(json.dumps({"counts": doc["counts"],
                      "CANDIDATE_SET_HASH":
                          doc["CANDIDATE_SET_HASH"][:16]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
