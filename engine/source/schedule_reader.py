"""SCHEDULE READER (M2) - structural schedules from attribute rows or text tables, without a project profile (generic).

Two source forms, one output:

ATTRIBUTE ROWS   a schedule drawn as block inserts, one insert per row, each value an ATTRIB (common in Kuwait CAD
                 offices). Rows are grouped by their attribute TAG SET. In a group:
                   mark field   the tag whose values look like plan marks (F3, C1, B12, CB4, SB2) in most rows - found
                                by CONTENT, not by the tag's spelling;
                   dimensions   tags whose stem is a size word (W / WIDTH / B / BR, H / HT / L / LENGTH, D / DEPTH /
                                DEPHT / DP / T / THK, Arabic equivalents);
                   bars         stem pairs COUNT + DIAMETER (X-B / X-D, X.R / X.D, X-N / X-DIA), read by
                                schedule_grammar (6 + 16 -> 6Ø16; 10 + 14/m -> 10Ø14/m);
                   storeys      a tag prefix before '.' names a storey band (FOU. / GR. / 1ST. / 2ND. / ROOF.).
TEXT TABLES      schedule texts in rows and columns (a CAD table drawn with lines, or a PDF table): a header row
                 holding a mark word and at least one size word fixes the columns; rows below align by y; every value
                 is assigned to the header column whose x-span holds it.

Units are inferred per family from plausibility (a beam width 20 is cm, 200 mm, 0.2 m) and RECORDED as an inference;
a family whose values fit no unit cleanly is a WARNING. Duplicate marks with different values are a CONFLICT kept
with every candidate (no row is chosen). Nothing here creates a member: the plan decides occurrence.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict

from engine.source import drawing_model as DM
from engine.source import schedule_grammar as SG

POLICY_ID = "SCHEDULE_READER_V1"
SIZE_WORDS = {
    "W": ("W", "WIDTH", "B", "BR", "BREADTH", "عرض", "العرض"),
    "H": ("H", "HT", "HEIGHT", "L", "LENGTH", "LEN", "طول", "الطول", "ارتفاع"),
    "D": ("D", "DEPTH", "DEPHT", "DP", "T", "THK", "THICK", "THICKNESS", "عمق", "سمك", "السمك"),
}
MARK_WORDS = ("TYPE", "MARK", "NAME", "REF", "TAG", "NO", "ID", "النوع", "الرمز", "رقم")
COUNT_SUFFIX = ("B", "R", "N", "NO", "NUM", "CNT")
DIA_SUFFIX = ("D", "DIA", "Ø")
STOREY_PREFIX = {"FOU": "FOUNDATION", "FDN": "FOUNDATION", "FND": "FOUNDATION", "GR": "GF", "GF": "GF", "G": "GF",
                 "1ST": "1F", "1F": "1F", "FF": "1F", "2ND": "2F", "2F": "2F", "SF": "2F", "3RD": "3F", "3F": "3F",
                 "ROOF": "ROOF", "TOP": "ROOF", "R": "ROOF"}
UNITS_M = {"mm": 0.001, "cm": 0.01, "m": 1.0}
PLAUSIBLE_M = {   # (field) -> range in metres per family
    "FOOTING": {"W": (0.4, 12.0), "H": (0.4, 12.0), "D": (0.2, 2.0)},
    "COLUMN": {"W": (0.15, 2.0), "H": (0.15, 2.0)},
    "BEAM": {"W": (0.1, 1.5), "H": (0.15, 2.0)},
    "CONTINUOUS_BEAM": {"W": (0.1, 1.5), "H": (0.15, 2.0)},
    "STRAP_BEAM": {"W": (0.15, 2.0), "H": (0.2, 2.0)},
    "GROUND_BEAM": {"W": (0.15, 1.5), "H": (0.2, 2.0)},
    "LINTEL": {"W": (0.1, 0.6), "H": (0.1, 1.0)},
}


class ScheduleError(ValueError):
    pass


def _num(v):
    t = DM.normalize(v).replace(",", ".")
    m = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*", t)
    return float(m.group(1)) if m else None


def _split_tag(tag):
    """'FOU.W' -> ('FOU', 'W'); 'SH-T-B' -> ('', 'SH-T-B'); 'BOT1-D' -> ('', 'BOT1-D')."""
    t = DM.normalize(tag).upper()
    if "." in t:
        a, b = t.split(".", 1)
        if a in STOREY_PREFIX:
            return a, b
    return "", t


def _size_role(stem):
    s = stem.upper().strip()
    for role, words in SIZE_WORDS.items():
        if s in (w.upper() for w in words):
            return role
    return None


def _bar_pairs(stems):
    """stems -> [(bar_stem, count_stem, dia_stem)] for stem pairs X-B/X-D, X-R/X-D, XB/XD."""
    out = []
    st = set(stems)
    for s in sorted(st):
        for cs in COUNT_SUFFIX:
            for sep in ("-", "_", "."):
                if s.endswith(sep + cs):
                    base = s[: -len(sep + cs)]
                    for ds in DIA_SUFFIX:
                        d = base + sep + ds
                        if d in st:
                            out.append((base, s, d))
    # storey-group bars: 'R' (count) with 'D' (dia) inside one prefix group
    if "R" in st and "D" in st:
        out.append(("MAIN", "R", "D"))
    # an orphan count stem (X-B with no X-D) beside a lone 'D' next to a size 'H': the D is that bar's diameter
    used = {c for _, c, _ in out}
    orphans = [s for s in sorted(st) if s not in used and any(s.endswith(sep + cs) for sep in ("-", "_")
                                                              for cs in COUNT_SUFFIX)]
    if len(orphans) == 1 and "D" in st and "H" in st and ("R" not in st):
        base = orphans[0].rsplit("-", 1)[0].rsplit("_", 1)[0]
        out.append((base, orphans[0], "D"))
    return out


def mark_field(rows, tags):
    best, score = None, 0.0
    for t in tags:
        vals = [r.get(t, "") for r in rows]
        fams = [DM.mark_family(v)[0] for v in vals if v]
        s = sum(1 for f in fams if f) / max(len(rows), 1)
        if s > score or (s == score and best is not None and _split_tag(t)[1] in MARK_WORDS):
            best, score = t, s
    return (best, score) if score >= 0.6 else (None, score)


def infer_unit(family, values):
    """values: {role: [numbers]} -> (unit, share, per-unit shares)."""
    rng = PLAUSIBLE_M.get(family) or PLAUSIBLE_M["BEAM"]
    shares = {}
    for u, f in UNITS_M.items():
        n = ok = 0
        for role, vs in values.items():
            if role not in rng:
                continue
            lo, hi = rng[role]
            for v in vs:
                n += 1
                ok += lo <= v * f <= hi
        shares[u] = ok / n if n else 0.0
    best = max(shares, key=lambda u: (shares[u], u == "cm"))
    return best, shares[best], shares


def from_attribute_rows(attributes, inserts=None, sheet_of=None):
    """attributes: [{owner, tag, value, x, y}] -> {families: {...}, rows: [...], conflicts, warnings}."""
    by_owner = defaultdict(dict)
    pos = {}
    for a in attributes:
        by_owner[a["owner"]][a["tag"]] = a["value"]
        pos.setdefault(a["owner"], (a["x"], a["y"]))
    groups = defaultdict(list)
    for owner, vals in by_owner.items():
        groups[tuple(sorted(vals))].append((owner, vals))
    rows, warnings, fam_vals = [], [], defaultdict(lambda: defaultdict(list))
    for tags, members in sorted(groups.items(), key=lambda kv: kv[0]):
        if len(members) < 1 or len(tags) < 3:
            continue
        recs = [v for _, v in members]
        mf, share = mark_field(recs, tags)
        if mf is None:
            continue
        stems = defaultdict(set)
        for t in tags:
            p, s = _split_tag(t)
            stems[p].add(s)
        for owner, vals in sorted(members, key=lambda m: str(m[0])):
            mark_raw = vals.get(mf, "")
            for mark in [m for m in re.split(r"[/,]", DM.normalize(mark_raw)) if m.strip()]:
                fam, mk = DM.mark_family(mark)
                if fam is None:
                    continue
                row = {"mark": mk, "family": fam, "source": f"INSERT {owner}", "mark_tag": mf,
                       "position": pos.get(owner), "sheet": sheet_of(*pos[owner]) if sheet_of and owner in pos else None,
                       "tag_set": list(tags), "by_storey": {}, "raw": dict(vals)}
                for prefix, ss in stems.items():
                    rec = {"dims_raw": {}, "bars": []}
                    for s in ss:
                        role = _size_role(s)
                        tag = f"{prefix}.{s}" if prefix else s
                        if role and tag != mf:
                            v = _num(vals.get(tag, ""))
                            if v is not None:
                                rec["dims_raw"].setdefault(role, v)
                    pairs = _bar_pairs(ss)
                    if any(ds == "D" for _, _, ds in pairs):
                        rec["dims_raw"].pop("D", None)          # 'D' read as a bar diameter, never also a depth
                    for base, cs, ds in pairs:
                        ct = f"{prefix}.{cs}" if prefix else cs
                        dt = f"{prefix}.{ds}" if prefix else ds
                        c, d = vals.get(ct, ""), vals.get(dt, "")
                        if not (c or d):
                            continue
                        b = SG.bar_from_cells(c, d)
                        b["role"] = base
                        rec["bars"].append(b)
                    if prefix:
                        if rec["dims_raw"] or rec["bars"]:
                            row["by_storey"][STOREY_PREFIX.get(prefix, prefix)] = rec
                    else:
                        row["dims_raw"], row["bars"] = rec["dims_raw"], rec["bars"]
                for role, v in row.get("dims_raw", {}).items():
                    fam_vals[fam][role].append(v)
                for st in row["by_storey"].values():
                    for role, v in st["dims_raw"].items():
                        fam_vals[fam][role].append(v)
                rows.append(row)
    return _finish(rows, fam_vals, warnings, "ATTRIBUTE_ROWS")


def from_text_table(texts, *, row_tol, col_pad):
    """texts: [{value, x, y}] of one schedule region -> the same row records (header words fix the columns)."""
    T = [dict(t, norm=DM.normalize(t["value"])) for t in texts if DM.normalize(t["value"])]
    lines = defaultdict(list)
    for t in sorted(T, key=lambda t: (-t["y"], t["x"])):
        key = next((k for k in lines if abs(k - t["y"]) <= row_tol), t["y"])
        lines[key].append(t)
    ordered = sorted(lines.items(), key=lambda kv: -kv[0])
    header, cols = None, None
    for y, ts in ordered:
        roles = {}
        for t in ts:
            u = t["norm"].upper()
            if u in (w.upper() for w in MARK_WORDS) or any(w in u for w in ("TYPE", "MARK")):
                roles[t["x"]] = "MARK"
            else:
                r = _size_role(re.sub(r"\(.*?\)", "", u).strip())
                if r:
                    roles[t["x"]] = r
                elif re.search(r"BOT|BOTTOM|سفلي", u):
                    roles[t["x"]] = "BAR_BOTTOM"
                elif re.search(r"TOP|علوي", u):
                    roles[t["x"]] = "BAR_TOP"
                elif re.search(r"STIR|LINK|TIE|كانات", u):
                    roles[t["x"]] = "BAR_LINKS"
        if "MARK" in roles.values() and len(roles) >= 2:
            header, cols = y, sorted(roles.items())
            break
    if header is None:
        return {"families": {}, "rows": [], "conflicts": [], "warnings": ["no header row with a mark word"],
                "form": "TEXT_TABLE"}
    xs = [x for x, _ in cols]
    edges = [(-1e18 if i == 0 else (xs[i - 1] + xs[i]) / 2.0, 1e18 if i == len(xs) - 1 else (xs[i] + xs[i + 1]) / 2.0)
             for i in range(len(xs))]
    rows, fam_vals = [], defaultdict(lambda: defaultdict(list))
    for y, ts in ordered:
        if y >= header - row_tol:
            continue
        cell = defaultdict(list)
        for t in ts:
            for (x, role), (lo, hi) in zip(cols, edges):
                if lo - col_pad <= t["x"] < hi + col_pad:
                    cell[role].append(t["norm"])
                    break
        if "MARK" not in cell:
            continue
        for mark in re.split(r"[/,]", " ".join(cell["MARK"])):
            fam, mk = DM.mark_family(mark.strip())
            if fam is None:
                continue
            row = {"mark": mk, "family": fam, "source": f"TEXT_TABLE y={y:.1f}", "mark_tag": "MARK",
                   "by_storey": {}, "dims_raw": {}, "bars": [], "raw": {k: " ".join(v) for k, v in cell.items()}}
            for role in ("W", "H", "D"):
                if role in cell:
                    v = _num(cell[role][0])
                    if v is None:
                        m = re.match(r"^\s*([0-9.]+)\s*[xX×*]\s*([0-9.]+)\s*$", cell[role][0])
                        if m and role == "W":
                            row["dims_raw"]["W"], row["dims_raw"]["H"] = float(m.group(1)), float(m.group(2))
                            continue
                    if v is not None:
                        row["dims_raw"][role] = v
            for role in ("BAR_BOTTOM", "BAR_TOP", "BAR_LINKS"):
                for raw in cell.get(role, []):
                    b = SG.parse_bar(raw)
                    b["role"] = role[4:]
                    row["bars"].append(b)
            for role, v in row["dims_raw"].items():
                fam_vals[fam][role].append(v)
            rows.append(row)
    return _finish(rows, fam_vals, [], "TEXT_TABLE")


def _finish(rows, fam_vals, warnings, form):
    for fam in ("BEAM", "CONTINUOUS_BEAM", "GROUND_BEAM", "STRAP_BEAM", "LINTEL"):
        if fam in fam_vals and "H" not in fam_vals[fam] and "D" in fam_vals[fam]:
            fam_vals[fam]["H"] = fam_vals[fam].pop("D")
    fams = {}
    for fam, vals in fam_vals.items():
        unit, share, shares = infer_unit(fam, vals)
        fams[fam] = {"unit": unit, "unit_m": UNITS_M[unit], "plausible_share": round(share, 3), "shares": shares,
                     "n_rows": sum(1 for r in rows if r["family"] == fam),
                     "unit_basis": "INFERRED_FROM_PLAUSIBLE_MEMBER_SIZES"}
        if share < 0.8:
            warnings.append(f"{fam}: no unit fits the schedule values cleanly (best {unit}, {share:.0%})")
    depth_families = ("BEAM", "CONTINUOUS_BEAM", "GROUND_BEAM", "STRAP_BEAM", "LINTEL")
    for r in rows:
        if r["family"] in depth_families and "H" not in r.get("dims_raw", {}) and "D" in r.get("dims_raw", {}):
            r["dims_raw"]["H"] = r["dims_raw"].pop("D")            # a beam's DEPTH is its section depth H
            r["depth_tag"] = "D"
        u = fams.get(r["family"], {}).get("unit_m")
        r["dims_m"] = {k: v * u for k, v in r.get("dims_raw", {}).items()} if u else {}
        for st in r["by_storey"].values():
            st["dims_m"] = {k: v * u for k, v in st["dims_raw"].items()} if u else {}
    conflicts = []
    by = defaultdict(list)
    for r in rows:
        by[(r["family"], r["mark"])].append(r)
    for (fam, mk), rs in sorted(by.items()):
        sig = {repr((sorted(r.get("dims_raw", {}).items()), sorted((s, sorted(v["dims_raw"].items()))
                                                                       for s, v in r["by_storey"].items())))
               for r in rs}
        if len(sig) > 1:
            conflicts.append({"family": fam, "mark": mk, "kind": "SOURCE_CONFLICT_DUPLICATE_MARK",
                              "candidates": [{"source": r["source"], "dims_raw": r.get("dims_raw"),
                                              "by_storey": {k: v["dims_raw"] for k, v in r["by_storey"].items()}}
                                             for r in rs]})
    return {"policy": POLICY_ID, "form": form, "families": fams, "rows": rows, "conflicts": conflicts,
            "warnings": warnings}


def library(sched):
    """{(family, mark): row or None-if-conflicting} with conflicts excluded (never a silent choice)."""
    bad = {(c["family"], c["mark"]) for c in sched["conflicts"]}
    lib = {}
    for r in sched["rows"]:
        k = (r["family"], r["mark"])
        if k in bad:
            lib[k] = None
        else:
            lib.setdefault(k, r)
    return lib


def policy_record():
    return {"policy": POLICY_ID, "forms": ["ATTRIBUTE_ROWS", "TEXT_TABLE"],
            "rule": "the mark field is found by content; units are inferred and recorded; duplicate marks with "
                    "different values are kept as a conflict"}
