"""B1-04 disposal as one figure from the B1 lines of an index (T-796, rule R-T796-2; every villa).

Physical element: excavated soil (in situ m3) that is not placed back on the plot. The drawing note "fill from
excavation material" makes BOTH fills come from the spoil: Z1 = trench / pit backfill back to existing ground, Z2 =
placed fill from existing ground up to the slab underside. Balance (in situ, k = in-situ m3 per compacted m3):

    disposal = max(0, E - k (Z1 + Z2))          import (compacted) = max(0, (Z1 + Z2) - E / k)

k is not sourced on this villa (T-505: MPW s.02220 / 02223 give no factor), so the figure is carried at k = 1 and
labelled ESTIMATE; k_break = E / (Z1 + Z2) is reported beside it (the factor at which the surplus becomes an import).
If the drawings say Z2 is imported (not from excavation), disposal = E - k Z1 and Z2 is an import line.
"""
from __future__ import annotations

Z2_TOKEN = ":Z2"


def split_b1(lines):
    """Sum RELEASED excavation and backfill (Z1 vs Z2) of an index; HELD lines are returned, never summed as 0."""
    E = Z1 = Z2 = 0.0
    held = []
    for l in lines:
        c = l["item_code"]
        if c not in ("STR.EARTH.EXCAVATION", "STR.EARTH.BACKFILL"):
            continue
        if l["class"] == "EXCLUDED":
            continue
        if l["class"] != "RELEASED" or l.get("measured_net") is None:
            held.append(l["line_id"]); continue
        v = float(l["measured_net"])
        if c == "STR.EARTH.EXCAVATION":
            E += v
        elif str(l.get("element_id", "")).endswith(Z2_TOKEN):
            Z2 += v
        else:
            Z1 += v
    return E, Z1, Z2, held


def balance(E, Z1, Z2, k=1.0, z2_from_excavation=True):
    if k is None or k <= 0:
        raise ValueError("k must be a positive factor (in-situ m3 per compacted m3)")
    reused = (Z1 + Z2) if z2_from_excavation else Z1
    disposal = max(0.0, E - k * reused)
    imp = max(0.0, reused - E / k) + (0.0 if z2_from_excavation else Z2)
    k_break = E / reused if reused else None
    return dict(disposal_in_situ=disposal, import_compacted=imp, k_break=k_break,
                label="ESTIMATE" if k == 1.0 else "DEFAULT")
