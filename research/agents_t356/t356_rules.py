"""T-356 rules: the held range of a buried-concrete line from its open readings (pure, stdlib only; every villa).

R-T356-1  A line whose quantity rests on an OPEN question (a designer item: D-15, Q-28, D-34, ...) carries the range of
          EVERY admissible reading, never one of them as its value; its contractual state is HELD (value blank).
R-T356-2  Strap blinding where no section prints a blinding under the strap: the reading 'none' is admissible, so the
          low end is 0 (a bound, never a value). The high end is the strap's OWN strip (strap plan grown by the printed
          projection on its two sides, between the faces of the footings it joins, inside the plot): merging into
          the footing layer can only lower it. A plan overlap with a member at another level (a ground beam 0.28 m+
          above the strap, T-230) is NEVER deducted: two layers at different levels share no volume.
R-T356-3  A band whose section is open between printed sections and whose crossings with footings may or may not
          share elevation: range = [min section x free length, max section x drawn length]. A length the band's own
          drawing does not give (a side missing, a paired-face run) is a wrong basis, never a reading, even when the
          figure falls inside the range.
R-T356-4  A drawn intersection of the band with another printed solid (a pad cast with it, a column through it) is
          owned once; while the owner or the count is unprinted the band line's low end is NOT ESTABLISHED by that
          split (the physical total does not move).
R-T356-5  Length-class sections (p.13 'more than 5 m', 'less than 5 m', 'less than 2.5 m'): every title whose
          literal condition holds on any admissible length basis is a reading; the range spans their depths; a
          length on a class boundary that no title covers literally (exactly 5.00 m) keeps both neighbours. Picking
          the 'most specific' title is a precedence the drawing does not print (D-34): a designer item.
R-T356-6  Verdict of a line against its ledger range: LINE_RIGHT (line range = ledger range), CORRECT_RANGE (line
          shows a single reading or a range that excludes an admissible reading), LEDGER_RIGHT is the same as
          CORRECT_RANGE when the ledger already carries the full range. A figure is never chosen because it is larger,
          more conservative or closer to the freelancer.
"""

TOL = 1e-6
MAX_M = 1000.0      # a villa member longer than 1 km is a unit error (mm passed for m)


class Refused(ValueError):
    """An input that would hide an open reading, double count a volume or write a held quantity as a number."""


def _num(x, what):
    if x is None or isinstance(x, bool) or not isinstance(x, (int, float)):
        raise Refused(f"{what}: a number is required, got {x!r}")
    if x < 0:
        raise Refused(f"{what}: negative {x}")
    return float(x)


def _len(x, what):
    v = _num(x, what)
    if v > MAX_M:
        raise Refused(f"{what}: {v} m is not a villa length (mm passed for m?)")
    return v


def strap_blinding_range(own_strip_m2, thickness_m, blinding_printed_under_straps, gb_plan_overlap_m2=0.0,
                         gb_vertical_gap_m=None, merged_strip_m2=None):
    """R-T356-2. Returns {'low', 'high', 'merged', 'status'} in m3."""
    a = _num(own_strip_m2, "own strip")
    t = _num(thickness_m, "blinding thickness")
    if gb_plan_overlap_m2:
        if gb_vertical_gap_m is None or gb_vertical_gap_m > 0:
            raise Refused("a ground beam above the strap shares no blinding volume with it: no plan deduction")
    if merged_strip_m2 is not None and _num(merged_strip_m2, "merged strip") > a + TOL:
        raise Refused("the merged strip cannot exceed the own strip")
    if blinding_printed_under_straps:
        return {"low": (merged_strip_m2 if merged_strip_m2 is not None else a) * t, "high": a * t,
                "merged": None if merged_strip_m2 is None else merged_strip_m2 * t, "status": "PRINTED_LEVEL_OPEN"}
    return {"low": 0.0, "high": a * t, "merged": None if merged_strip_m2 is None else merged_strip_m2 * t,
            "status": "HELD"}


def band_range(drawn_length_m, crossing_length_m, width_m, depths_m):
    """R-T356-3: section readings x length readings (free .. drawn)."""
    L = _len(drawn_length_m, "drawn length")
    c = _len(crossing_length_m, "crossing length")
    b = _num(width_m, "width")
    if c > L + TOL:
        raise Refused("crossing length exceeds the drawn band")
    ds = sorted({_num(d, "depth") for d in depths_m})
    if not ds:
        raise Refused("no printed section")
    return {"low": (L - c) * b * ds[0], "high": L * b * ds[-1], "readings": len(ds) * 2}


def band_line_low(band_low_m3, split_per_item_m3, split_count):
    """R-T356-4: an unprinted count of shared solids leaves the line's low end not established (None)."""
    lo = _num(band_low_m3, "band low")
    s = _num(split_per_item_m3, "split volume")
    if split_count is None:
        return None
    n = split_count
    if isinstance(n, bool) or not isinstance(n, int) or n < 0:
        raise Refused("split count must be a non-negative integer")
    return lo - s * n


def class_titles(length_bases_m, titles):
    """R-T356-5. titles: [(name, op, limit_m, depth_m)], op in {'<', '>'}. Returns the readings that hold literally
    on any basis; a basis exactly on a limit no title covers keeps the neighbouring titles of that limit."""
    if not titles:
        raise Refused("no printed title")
    hold = set()
    for L in length_bases_m:
        L = _len(L, "length basis")
        hit = [t for t in titles if (L < t[2] if t[1] == "<" else L > t[2])]
        if not hit:
            hit = [t for t in titles if abs(t[2] - L) <= TOL]
            if not hit:
                raise Refused(f"length {L} m is covered by no printed title")
        hold.update(hit)
    return sorted(hold, key=lambda t: t[3])


def depth_range(net_plan_m2, readings):
    a = _num(net_plan_m2, "net plan")
    ds = [r[3] for r in readings]
    return {"low": a * min(ds), "high": a * max(ds), "single": len(set(ds)) == 1}


def verdict(line_low, line_high, ledger_low, ledger_high, tol=5e-4):
    """R-T356-6: compare a candidate line with the ledger range (m3)."""
    if ledger_low is None or ledger_high is None:
        raise Refused("ledger range must carry both ends (use NOT_ESTABLISHED separately)")
    if line_low is None or line_high is None:
        return "CORRECT_RANGE"
    same = abs(line_low - ledger_low) <= tol and abs(line_high - ledger_high) <= tol
    if same:
        return "LINE_RIGHT"
    return "CORRECT_RANGE"


def fill_value(status, value):
    """A FILL / ledger cell: HELD and NOT_ESTABLISHED are blank, never 0 (lesson T-332)."""
    if status in ("HELD", "NOT_ESTABLISHED", "SPLIT_UNRESOLVED"):
        if value not in (None, ""):
            raise Refused(f"{status} carries a value {value!r}")
        return ""
    if value is None:
        raise Refused(f"{status} without a value")
    return f"{float(value):.6f}"
