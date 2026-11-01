"""JOIN_RERUN_V1 (T-446, rule R-T446-1, any villa): the CEILING_SKIRTING_JOIN_V1 census (T-435, R-T435-1) re-run on
a new candidate, with three additions. Research module, unwired, stdlib only; no layer name, room id or dimension of any
villa is in this file. The T-435 module is imported, never edited.

R-T446-1 (provenance T-446; adds to R-T435-1, changes none of it):
  1. FLOORED ELEMENTS OUTSIDE B3-01. A walked floor surface valued (or held) in another family is a floored element too:
     a lift landing threshold (B6-07), a doorway marble threshold, a held opening threshold strip. Each is a census space
     of its own (key '<face>~<element>' when its face is a floored space or carries a ceiling / skirting line, so a
     host's m2 never changes and a host's line is never inherited silently), with
     its m2 or HELD (None, never 0). Lines in state NOT_APPLICABLE* are not spaces (they are owned elsewhere).
  2. HOST-FACE DOUBLE OWNERSHIP. A space whose layer is given to its host face (CEILING_ON_HOST_FACE /
     SKIRTING_ON_HOST_FACE) AND that also has a line of that layer keyed on itself is DOUBLE_OWNED (the host line's plan
     area / boundary already covers it; never summed).
  3. PART SKIRTING FROM A FACE TABLE. A floor part's drawn wall-face length is the sum of its WALL / COLUMN stretches;
     a stretch along a flight (OPEN, STAIR_SIDE: the stair skirting B7-07 / B7-08) or an opening never carries part
     skirting, and a held stretch stays HELD (never 0, never added).
  4. DELTA. Two join tables are compared per (space, layer): NEW, GONE, SPLIT / SPLIT_FROM (a face carried as parts),
     OWNER_CHANGED (status, owning line set or reasons), FLOOR_M2_CHANGED (same owner, floored m2 moved), SAME;
     plus the SILENT count and m2 / lm before and after.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agents_t435"))
import ceiling_skirting_join_v1 as J  # noqa: E402

METHOD = "JOIN_RERUN_V1"
RULE = "R-T446-1"

# item codes (prefix) of floored elements valued outside FIN.FLOOR.* (B3-01), with their element class
ELEMENT_CODES = {
    "FIN.MARBLE.LIFT_THRESHOLD": "LIFT_THRESHOLD",   # B6-07 (UP-ELEV-005)
    "FIN.MARBLE.THRESHOLD": "DOOR_THRESHOLD",        # marble in a doorway strip (wet / dry change)
    "ARCH.THRESHOLD": "THRESHOLD_STRIP",             # opening strip, finish to be confirmed
}
HOST_REASONS = ("CEILING_ON_HOST_FACE", "SKIRTING_ON_HOST_FACE")
FACE_KINDS = ("WALL", "COLUMN")
NO_PART_SKIRTING = ("OPEN", "STAIR_SIDE", "DOOR", "PASSAGE", "LIFT_OPENING")
HELD_KINDS = ("GUARD_HELD", "HELD", "UNKNOWN")


def element_class(item_code: str) -> str | None:
    c = (item_code or "").upper()
    for k, v in ELEMENT_CODES.items():
        if c == k or c.startswith(k + "."):
            return v
    return None


def element_spaces(lines: list[dict], floored: set[str], key_of=None) -> list[dict]:
    """census spaces for floored elements valued outside B3-01 (rule 1), as J.census extra_spaces"""
    key_of = key_of or (lambda ln: ln.get("room_id"))
    out: dict[str, dict] = {}
    layer_faces = {key_of(ln) for ln in lines if J.family_of(ln.get("item_code"), ln.get("trade")) in J.LAYERS}
    for ln in lines:
        cls = element_class(ln.get("item_code"))
        if cls is None or ln.get("unit") != "m2" or J.is_not_applicable(ln):
            continue
        face = key_of(ln) or ""
        el = ln.get("element_id") or ln.get("line_id")
        # keyed on its own face only when that face is no floored space and carries no ceiling / skirting line;
        # otherwise '<face>~<element>', so a host's m2 never changes and a host's line is never inherited silently
        sid = face if (face and face not in floored and face not in layer_faces) else f"{face}~{el}"
        if sid in out or sid in floored:
            raise ValueError(f"floored element {sid} twice: one m2 one line")
        q, bound = J.quantity(ln)
        out[sid] = {"space_id": sid, "floor": ln.get("floor", ""), "m2": q, "kind": cls,
                    "source": f"{cls} line {ln.get('line_id')} ({ln.get('evidence_state')})",
                    "host_face": face or None, "line_id": ln.get("line_id"),
                    "bound": bound}
    return list(out.values())


def apply_host_rule(rows: list[dict], reasons: list[dict]) -> list[dict]:
    """rule 2: an own line of the layer + a host-face reason for that layer -> DOUBLE_OWNED"""
    host = {(r["space_id"], r["layer"]) for r in reasons if r["code"] in HOST_REASONS}
    for r in rows:
        if r["line_ids"] and (r["space_id"], r["layer"]) in host and r["status"] != J.DOUBLE:
            r["status"] = J.DOUBLE
            r.pop("shortfall_m2", None)
    return rows


def part_skirting(stretches: list[dict]) -> dict:
    """rule 3: a floor part's drawn skirting lm from its face stretches (kind, length_m, skirting_lm)"""
    conf, held = 0.0, []
    for s in stretches:
        k = s["kind"]
        sk = s.get("skirting_lm")
        if k in NO_PART_SKIRTING:
            if sk not in (None, "") and abs(float(sk)) > 1e-9:
                raise ValueError(f"stretch {s.get('side')} {k} carries part skirting {sk}: a flight side or an "
                                 f"opening is never a part's skirting face")
            continue
        if k in HELD_KINDS:
            held.append(float(s["length_m"]))
            continue
        if k not in FACE_KINDS:
            raise ValueError(f"unknown stretch kind {k}")
        if sk in (None, ""):
            raise ValueError(f"face stretch {s.get('side')} without a skirting figure")
        conf += float(sk)
    return {"drawn_lm": round(conf, 4), "held_lm": [round(h, 4) for h in held],
            "status": "DRAWING-CONFIRMED" if not held else "DRAWING-CONFIRMED + HELD stretches"}


def key(r: dict) -> tuple[str, str]:
    return (r["space_id"], r["layer"])


def delta(before: list[dict], after: list[dict], renamed: dict[str, list[str]] | None = None) -> dict:
    """rule 4: per (space, layer) NEW / GONE / OWNER_CHANGED / SAME; `renamed` maps an old space id to the ids that
    replace it (a face split into parts), so a split is OWNER_CHANGED (SPLIT), not GONE + NEW"""
    renamed = renamed or {}
    b = {key(r): r for r in before}
    a = {key(r): r for r in after}
    split_into = {n: o for o, ns in renamed.items() for n in ns}
    out = []
    for k in sorted(set(a) | set(b)):
        ra, rb = a.get(k), b.get(k)
        if rb is None and ra is not None and split_into.get(k[0]) is not None:
            rb2 = b.get((split_into[k[0]], k[1]))
            out.append({"space_id": k[0], "layer": k[1], "change": "SPLIT_FROM", "from": split_into[k[0]],
                        "before": _sig(rb2), "after": _sig(ra)})
        elif rb is None:
            out.append({"space_id": k[0], "layer": k[1], "change": "NEW", "before": None, "after": _sig(ra)})
        elif ra is None:
            ch = "SPLIT" if k[0] in renamed else "GONE"
            out.append({"space_id": k[0], "layer": k[1], "change": ch, "before": _sig(rb), "after": None,
                        "into": renamed.get(k[0])})
        elif _sig(ra) != _sig(rb):
            out.append({"space_id": k[0], "layer": k[1], "change": "OWNER_CHANGED", "before": _sig(rb),
                        "after": _sig(ra)})
        elif _m2(ra) != _m2(rb):
            out.append({"space_id": k[0], "layer": k[1], "change": "FLOOR_M2_CHANGED", "before": _sig(rb),
                        "after": _sig(ra), "floor_m2": (_m2(rb), _m2(ra))})
    return {"changes": out, "silent_before": _silent(before), "silent_after": _silent(after)}


def _sig(r):
    if r is None:
        return None
    # line ids compared on their first 10 characters (the committed join tables carry 'L-' + 8 hex)
    return {"status": r["status"], "lines": sorted(x[:10] for x in (r.get("line_ids") or [])),
            "reasons": sorted(r.get("reasons") or [])}


def _m2(r):
    return None if r.get("floor_m2") is None else round(r["floor_m2"], 4)


def _silent(rows):
    sil = [r for r in rows if r["status"] == J.SILENT]
    c = [r for r in sil if r["layer"] == J.CEILING]
    s = [r for r in sil if r["layer"] == J.SKIRTING]
    return {"ceiling_spaces": len(c), "ceiling_m2": round(sum(r["floor_m2"] or 0 for r in c), 4),
            "ceiling_m2_held_spaces": sum(1 for r in c if r["floor_m2"] is None),
            "skirting_spaces": len(s),
            "skirting_lm_measured": round(sum((r.get("omission") or {}).get("value") or 0 for r in s), 4),
            "skirting_lm_unknown_spaces": sum(1 for r in s if (r.get("omission") or {}).get("value") is None)}


def census_total(spaces: dict, lines: list[dict], key_of=None) -> dict:
    """the census re-adds to the candidate: sum of the B3-01 spaces' m2 == sum of the candidate's floored FIN.FLOOR m2
    lines (not NOT_APPLICABLE, not bed); held lines counted separately, never 0"""
    cand, cand_held = 0.0, 0
    for ln in lines:
        if J.family_of(ln.get("item_code"), ln.get("trade")) != "FLOOR" or ln.get("unit") != "m2":
            continue
        if J.is_not_applicable(ln):
            continue
        q, _ = J.quantity(ln)
        if q is None:
            cand_held += 1
        else:
            cand += q
    # the census space m2 is None when any part is held: re-add from the lines kept on each space
    ids = {ln.get("line_id"): ln for ln in lines}
    cen, cen_held = 0.0, 0
    for sp in spaces.values():
        for lid in sp.floor_lines:
            q, _ = J.quantity(ids[lid])
            if q is None:
                cen_held += 1
            else:
                cen += q
    return {"candidate_m2": round(cand, 6), "candidate_held_lines": cand_held, "census_m2": round(cen, 6),
            "census_held_lines": cen_held, "residual_m2": round(cand - cen, 6)}
