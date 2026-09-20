"""Storey / copy-family register (PA06 WS5).

A storey is supported by repeated plan copies (translation families with
an optional 90-degree rotation), level marks and level text inside the
view, floor labels, sheet roles and owner input.  Names are never
inferred from coordinate order alone: without a deterministic name the
storey is FLOOR_01, FLOOR_02 ... in level order when levels exist, else in
copy order with STOREY_RELATION_STATUS = ORDER_NOT_ESTABLISHED.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from engine.ingest import ids
from engine.ingest.views import _long_segments, COPY_MATCH_MIN

LEVEL_RE = re.compile(r"^(?:%%p|±|\+|-)\s*(\d{1,2})[.,](\d{2})\s*$")
FLOOR_WORDS = (("GROUND", "GROUND_FLOOR"), ("FIRST", "FIRST_FLOOR"), ("SECOND", "SECOND_FLOOR"), ("ROOF", "ROOF"), ("BASEMENT", "BASEMENT"), ("MEZZ", "MEZZANINE"),
               ("الارضي", "GROUND_FLOOR"), ("الأرضي", "GROUND_FLOOR"), ("الاول", "FIRST_FLOOR"), ("الأول", "FIRST_FLOOR"), ("السطح", "ROOF"))


def _rotate(pts, k):
    out = []
    for x, y in pts:
        for _ in range(k):
            x, y = -y, x
        out.append((x, y))
    return out


def _vote(sa, sb, bucket=100.0):
    by = {}
    for l, ang, p1, p2 in sb:
        by.setdefault((l, ang), []).extend([p1, p2])
    votes, exact = Counter(), {}
    for l, ang, p1, p2 in sa:
        for (x, y) in (p1, p2):
            for (bx, by_) in by.get((l, ang), []):
                key = (round((bx - x) / bucket), round((by_ - y) / bucket))
                votes[key] += 1; exact.setdefault(key, []).append((bx - x, by_ - y))
    if not votes:
        return None
    key, n = votes.most_common(1)[0]
    dxs = sorted(d[0] for d in exact[key]); dys = sorted(d[1] for d in exact[key])
    return n, dxs[len(dxs) // 2], dys[len(dys) // 2]


def copy_families(views, min_matches=COPY_MATCH_MIN):
    """Pairwise transforms between views (translation, optionally after a k x 90 degree rotation of the second view)."""
    sigs = {v["VIEW_ID"]: _long_segments(v["PRIMITIVES"], None) for v in views}
    links = []
    for i, a in enumerate(views):
        for b in views[i + 1:]:
            sa, sb = sigs[a["VIEW_ID"]], sigs[b["VIEW_ID"]]
            base_need = max(10, min(min_matches, int(0.4 * min(2 * len(sa), 2 * len(sb)))))     # small drawings: 40 % of the shorter endpoint list
            if 2 * len(sa) < base_need or 2 * len(sb) < base_need:
                continue
            best = None
            for k in range(4):
                sbk = [(l, (ang + 90 * k) % 180, _rotate([p1], k)[0], _rotate([p2], k)[0]) for l, ang, p1, p2 in sb]
                vote = _vote(sa, sbk)
                need = base_need if k == 0 else 2 * base_need       # a rotated match must be twice as strong as a translation to count
                if vote and vote[0] >= need and (best is None or vote[0] > best[0][0]):
                    best = (vote, k)
            if best:
                (n, dx, dy), k = best
                links.append({"FROM_VIEW": a["VIEW_ID"], "TO_VIEW": b["VIEW_ID"], "ROTATION_DEG": 90 * k, "DX_MM": round(dx, 2), "DY_MM": round(dy, 2), "MATCHES": n, "STATUS": "SOURCE_ESTABLISHED"})
    # connected components = families
    parent = {v["VIEW_ID"]: v["VIEW_ID"] for v in views}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for l in links:
        parent[find(l["FROM_VIEW"])] = find(l["TO_VIEW"])
    fams = {}
    for v in views:
        fams.setdefault(find(v["VIEW_ID"]), []).append(v["VIEW_ID"])
    families = []
    for root, members in fams.items():
        if len(members) < 2:
            continue
        families.append({"FAMILY_ID": ids.make_id("VIEW", "FAMILY", ",".join(sorted(members)), tol=1.0).replace("VW-", "CF-"), "MEMBERS": sorted(members),
                         "LINKS": [l for l in links if l["FROM_VIEW"] in members], "STATUS": "SOURCE_ESTABLISHED"})
    return families, links


def _levels_in(view):
    vals = []
    for t in view.get("TEXTS", []):
        m = LEVEL_RE.match(t.value.strip().replace(" ", ""))
        if m:
            sign = -1 if t.value.strip().startswith("-") else 1
            vals.append(sign * (int(m.group(1)) + int(m.group(2)) / 100))
    return sorted(set(vals))


def _floor_words(view):
    hits = []
    for t in view.get("TEXTS", []):
        up = t.value.upper()
        for w, name in FLOOR_WORDS:
            if w in up:
                hits.append(name)
    return Counter(hits)


def storey_register(views, families, sheet_roles_by_view=None, owner_storeys=None):
    """STOREY_REGISTER rows for plan-like views."""
    sheet_roles_by_view = sheet_roles_by_view or {}
    owner_storeys = owner_storeys or {}
    plan_views = [v for v in views if v.get("ROLE", {}).get("FINAL_ROLE") in ("FLOOR_PLAN", "ROOF_PLAN") or v["VIEW_ID"] in owner_storeys]
    fam_of = {m: f["FAMILY_ID"] for f in families for m in f["MEMBERS"]}
    rows = []
    for v in plan_views:
        levels = _levels_in(v)
        words = _floor_words(v)
        ref = min(levels) if levels else None       # the lowest level mark inside a plan is normally its finished floor level
        name, name_src, name_status = None, None, "NOT_ESTABLISHED"
        if v["VIEW_ID"] in owner_storeys:
            name, name_src, name_status = owner_storeys[v["VIEW_ID"]], "OWNER_PROJECT_INPUT", "OWNER_ESTABLISHED"
        elif words:
            name, name_src, name_status = words.most_common(1)[0][0], "FLOOR_LABEL_TEXT", "SOURCE_ESTABLISHED"
        elif sheet_roles_by_view.get(v["VIEW_ID"], {}).get("STOREY"):
            name, name_src, name_status = sheet_roles_by_view[v["VIEW_ID"]]["STOREY"], "SHEET_INDEX_CONFIG", "CONFIG_DECLARED"
        rows.append({"PLAN_COPY_ID": v["VIEW_ID"], "FAMILY_ID": fam_of.get(v["VIEW_ID"]), "VIEW_ROLE": v.get("ROLE", {}).get("FINAL_ROLE"), "LEVEL_MARKS_IN_VIEW": levels,
                     "REFERENCE_LEVEL": ref, "LEVEL_SOURCE": "LEVEL_TEXT_IN_VIEW" if levels else None, "STOREY_NAME": name, "NAME_SOURCE": name_src, "NAME_STATUS": name_status,
                     "COPY_TRANSFORM": None})
    # order: by reference level where every member has one; else copy order with the relation NOT_ESTABLISHED
    by_family = {}
    for r in rows:
        by_family.setdefault(r["FAMILY_ID"], []).append(r)
    for fid, members in by_family.items():
        if fid and all(m["REFERENCE_LEVEL"] is not None for m in members) and len({m["REFERENCE_LEVEL"] for m in members}) == len(members):
            members.sort(key=lambda m: m["REFERENCE_LEVEL"]); rel = "ORDERED_BY_LEVEL_TEXT"
        else:
            members.sort(key=lambda m: m["PLAN_COPY_ID"]); rel = "ORDER_NOT_ESTABLISHED"
        for i, m in enumerate(members, 1):
            m["STOREY_ID"] = ids.make_id("VIEW", "STOREY", fid or m["PLAN_COPY_ID"], i if rel == "ORDERED_BY_LEVEL_TEXT" else m["PLAN_COPY_ID"], tol=1.0).replace("VW-", "SY-")
            m["GENERIC_NAME"] = f"FLOOR_{i:02d}" if rel == "ORDERED_BY_LEVEL_TEXT" else "FLOOR_UNORDERED"
            m["STOREY_RELATION_STATUS"] = rel
            m["CONFIDENCE_STATUS"] = "SOURCE_ESTABLISHED" if rel == "ORDERED_BY_LEVEL_TEXT" and m["NAME_STATUS"] != "NOT_ESTABLISHED" else ("PROVISIONAL" if rel == "ORDERED_BY_LEVEL_TEXT" else "NOT_ESTABLISHED")
    for f in families:
        for l in f["LINKS"]:
            for r in rows:
                if r["PLAN_COPY_ID"] == l["TO_VIEW"]:
                    r["COPY_TRANSFORM"] = {"FROM": l["FROM_VIEW"], "DX_MM": l["DX_MM"], "DY_MM": l["DY_MM"], "ROTATION_DEG": l["ROTATION_DEG"], "MATCHES": l["MATCHES"]}
    return rows
