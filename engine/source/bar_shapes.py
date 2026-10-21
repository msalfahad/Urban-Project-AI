"""BAR SHAPES (M2) - developed bar lengths by shape, diameter-aware bends and hooks (generic, stdlib).

Replaces any flat per-link allowance: every bend and hook is computed from the bar diameter with a NAMED code table
(engine.source.bbs_optimiser: ACI 318-19 Tables 25.3.1 / 25.3.2, recorded but not verified against a project
document -> PROVISIONAL_CODE_METHOD). A shape whose hooks the drawing does not show takes its hook kind from the
convention set, and the alternative (no hook) is always computed so the range is visible.

    straight(L)                         developed = L
    hooked(L, d, kinds)                 developed = L + sum(hook additions)            (90 / 180 standard hooks)
    closed_link(b, h, cover, d, kind)   centreline legs a = b - 2c - d, b' = h - 2c - d; four 90 deg corner bends at
                                        the code bend diameter; two closing hooks of `kind` (135_TIE default);
                                        developed = 2(a + b') - 8 r_c + 2 pi r_c + 2 x hook addition
    mass_kg(L, d)                       L x d^2 / 162 (the project unit-mass method)
"""

from __future__ import annotations

import math

from engine.source import bbs_optimiser as BO

POLICY_ID = "BAR_SHAPES_V1"
TABLES = {"ACI_318_19": BO.ACI_318_19}


def kg_per_m(d_mm):
    return d_mm * d_mm / 162.0


def mass_kg(length_m, d_mm, count=1):
    return count * length_m * kg_per_m(d_mm)


def straight(length_m):
    return {"shape": "STRAIGHT", "developed_m": length_m, "formula": "L"}


def hooked(length_m, d_mm, kinds, table="ACI_318_19"):
    adds = [BO.hook_addition(d_mm, k, TABLES[table]) for k in kinds]
    dev = length_m + sum(a["addition_m"] for a in adds)
    return {"shape": "HOOKED_" + "_".join(kinds), "developed_m": dev, "hooks": adds,
            "formula": "L + " + " + ".join(f"hook{a['kind']}({a['addition_m']:.3f})" for a in adds),
            "class": adds[0]["class"] if adds else "EXACT"}


def closed_link(b_m, h_m, cover_m, d_mm, hook_kind="135_TIE", table="ACI_318_19"):
    d = d_mm / 1000.0
    a = b_m - 2 * cover_m - d
    bb = h_m - 2 * cover_m - d
    if a <= 0 or bb <= 0:
        raise ValueError("section too small for the cover")
    tab = TABLES[table]
    D = tab["hooks"][hook_kind]["bend_d_db"](d_mm) * d          # inside bend diameter at the corners
    r_c = D / 2.0 + d / 2.0
    body = 2 * (a + bb) - 8 * r_c + 2 * math.pi * r_c
    hk = BO.hook_addition(d_mm, hook_kind, tab)
    dev = body + 2 * hk["addition_m"]
    return {"shape": "CLOSED_LINK", "developed_m": dev, "legs_m": (a, bb), "corner_radius_m": r_c,
            "hook": hk, "body_m": body,
            "formula": f"2({a:.3f}+{bb:.3f}) - 8x{r_c:.4f} + 2pi x{r_c:.4f} + 2 x {hk['addition_m']:.3f}",
            "class": hk["class"]}


def policy_record():
    return {"policy": POLICY_ID, "tables": {k: v["basis"] for k, v in TABLES.items()},
            "rule": "bends and hooks from the bar diameter and a named code table; never a flat allowance"}
