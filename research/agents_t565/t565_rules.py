"""T-565 B1 EARTHWORKS RECONCILIATION rules (EARTHWORKS_RECONCILE_V1; R-T565-1 .. 4; every villa; research, unwired).

Physical elements (ERS s.2.1):
  excavation  in-situ soil removed from the existing ground (NGL / EG) to the formation over the zone plan  [IN_SITU m3]
  backfill    finished compacted soil returned to EG = excavation - every buried solid below EG, once      [COMPACTED m3]
  displacement the buried solids below EG themselves (footing, neck, beam, blinding, underlay, pool shell) [SOLID m3]
  disposal    in-situ soil leaving the site; needs the compacted / in-situ dry-density ratio k            [IN_SITU m3]
  compaction  layers (count) and formation footprints (m2)                                                  [COUNT / AREA]
  soil treatment (anti-termite) sprayed area                                                                [AREA m2]

R-T565-1  A benchmark component with NO ROW is NO_ROW: never 0, never subtracted, never a percentage. The comparison of
          a component with NO_ROW on either side is NOT_COMPARABLE; a scope verdict is recorded separately, from the
          drawing evidence for the element's existence.
R-T565-2  Quantities are added or compared only within ONE basis (IN_SITU / COMPACTED / LOOSE / SOLID / AREA / COUNT):
          a bulked (LOOSE) m3 against an in-place m3 is refused, as is compacted against in-situ, unless the sourced
          factor that converts them is given (none is: owner 2026-11-02 18:00, R-T347-5).
R-T565-3  Valued, held-range and held-blank parts of a family total are kept apart; a held part is never 0 and never
          enters the valued sum; a component table must re-add exactly (6 dp) to each total in each basis.
R-T565-4  Each buried element's volume is owned ONCE across the excavation zones, by element id: its shares over the
          zones re-add exactly to its own concrete / blinding / underlay line; a share named twice, a share in two
          zones for the same plan, or an element of a valued zone with no share is refused (never silently dropped).
          A zone's backfill deducts each element id at most once.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

BASES = {"IN_SITU": "m3", "COMPACTED": "m3", "LOOSE": "m3", "SOLID": "m3", "AREA": "m2", "COUNT": "nr"}
STATES = ("VALUED", "HELD_RANGE", "HELD_BLANK", "NO_ROW", "NOT_IN_SCOPE")
Q6 = Decimal("0.000001")


def d6(x) -> Decimal:
    if x is None:
        raise ValueError("missing value: a held or absent quantity is never 0")
    if isinstance(x, float):
        x = repr(x)
    return Decimal(str(x)).quantize(Q6, rounding=ROUND_HALF_UP)


def _basis(basis: str, unit: str | None = None) -> str:
    if basis not in BASES:
        raise ValueError(f"unknown basis {basis!r}")
    if unit is not None and unit != BASES[basis]:
        raise ValueError(f"unit {unit!r} does not belong to basis {basis} ({BASES[basis]})")
    return basis


# ------------------------------------------------------------------------------------------------------ quantities
def valued(v, basis: str, unit: str | None = None) -> dict:
    v = d6(v)
    if v < 0:
        raise ValueError("negative quantity")
    return {"state": "VALUED", "basis": _basis(basis, unit), "value": v}


def held_range(lo, hi, basis: str, unit: str | None = None, reason: str = "") -> dict:
    lo, hi = d6(lo), d6(hi)
    if lo < 0 or hi < lo:
        raise ValueError(f"bad held range {lo} .. {hi}")
    return {"state": "HELD_RANGE", "basis": _basis(basis, unit), "low": lo, "high": hi, "reason": reason}


def held_blank(basis: str, reason: str) -> dict:
    if not reason:
        raise ValueError("a held-blank quantity names what holds it")
    return {"state": "HELD_BLANK", "basis": _basis(basis), "reason": reason}


def no_row(basis: str, evidence: str) -> dict:
    if not evidence:
        raise ValueError("NO_ROW needs the search evidence (files / rows read)")
    return {"state": "NO_ROW", "basis": _basis(basis), "evidence": evidence}


def not_in_scope(basis: str, evidence: str) -> dict:
    if not evidence:
        raise ValueError("NOT_IN_SCOPE needs the drawing / specification search evidence")
    return {"state": "NOT_IN_SCOPE", "basis": _basis(basis), "evidence": evidence}


def total(parts: list[dict]) -> dict:
    """R-T565-2 / -3: one basis; valued / held-range / held-blank kept apart. NO_ROW or NOT_IN_SCOPE is not a
    quantity and cannot be summed (it is reported as a state of the whole component instead)."""
    if not parts:
        raise ValueError("empty sum")
    bases = {p["basis"] for p in parts}
    if len(bases) != 1:
        raise ValueError(f"mixed bases refused in one sum: {sorted(bases)} (e.g. bulked vs in-place m3)")
    out = {"basis": bases.pop(), "valued": Decimal(0), "held_low": Decimal(0), "held_high": Decimal(0),
           "held_blank": 0, "n": len(parts)}
    for p in parts:
        s = p["state"]
        if s == "VALUED":
            out["valued"] += p["value"]
        elif s == "HELD_RANGE":
            out["held_low"] += p["low"]
            out["held_high"] += p["high"]
        elif s == "HELD_BLANK":
            out["held_blank"] += 1
        else:
            raise ValueError(f"{s} is not a quantity and is never summed (never 0)")
    # a part that no line carries is absent, never 0 (F-C-T510-3 / T-512: an all-blank code printed as 0.0)
    if not any(p["state"] == "VALUED" for p in parts):
        out["valued"] = None
    if not any(p["state"] == "HELD_RANGE" for p in parts):
        out["held_low"] = out["held_high"] = None
    return out


def compare(engine: dict, his: dict) -> dict:
    """R-T565-1 / -2: engine vs benchmark for one component. Returns the difference (engine - his) only when both are
    quantities of the same basis; NO_ROW on either side -> NOT_COMPARABLE with no number and no percentage."""
    if engine["basis"] != his["basis"]:
        raise ValueError(f"basis mismatch refused: engine {engine['basis']} vs his {his['basis']}")
    if his["state"] in ("NO_ROW", "NOT_IN_SCOPE") or engine["state"] in ("NO_ROW", "NOT_IN_SCOPE"):
        both_absent = his["state"] in ("NO_ROW", "NOT_IN_SCOPE") and engine["state"] in ("NO_ROW", "NOT_IN_SCOPE")
        return {"class": "AGREE_ABSENT" if both_absent else "NOT_COMPARABLE", "difference": None, "pct": None}
    if engine["state"] == "VALUED" and his["state"] == "VALUED":
        diff = engine["value"] - his["value"]
        pct = None if his["value"] == 0 else d6(diff / his["value"] * 100)
        return {"class": "COMPARED", "difference": diff, "pct": pct}
    return {"class": "HELD", "difference": None, "pct": None}


def table_closes(rows: list[dict], key: str, expected) -> Decimal:
    """R-T565-3: the component rows' `key` re-add exactly (6 dp) to the stated total."""
    s = sum((d6(r[key]) for r in rows), Decimal(0))
    if s != d6(expected):
        raise AssertionError(f"component table does not close on {key}: {s} != {d6(expected)}")
    return s


# ------------------------------------------------------------------------------------------------ ownership (R-4)
def ownership(elements: dict[str, Decimal], shares: list[tuple[str, str, Decimal]]) -> dict:
    """elements: element id -> its own line volume (SOLID m3). shares: (element id, zone, m3). Each (element, zone)
    once; each element's shares re-add exactly to its line; every element owned; unknown element refused.
    Returns zone -> owned m3 and element -> {zone: m3}."""
    seen, per_el, per_zone = set(), {}, {}
    for el, zone, v in shares:
        if el not in elements:
            raise ValueError(f"share for an element with no line: {el}")
        if (el, zone) in seen:
            raise ValueError(f"buried volume deducted twice: {el} in {zone}")
        seen.add((el, zone))
        v = d6(v)
        if v < 0:
            raise ValueError(f"negative share {el} {zone}")
        per_el.setdefault(el, {})[zone] = v
        per_zone[zone] = per_zone.get(zone, Decimal(0)) + v
    missing = sorted(set(elements) - set(per_el))
    if missing:
        raise ValueError(f"buried element owned by no zone (never silently dropped): {missing}")
    for el, z in per_el.items():
        s = sum(z.values(), Decimal(0))
        if s != d6(elements[el]):
            raise ValueError(f"{el}: shares {s} != line {d6(elements[el])} (owned more or less than once)")
    return {"per_zone": per_zone, "per_element": per_el}


def backfill(excavation_in_situ, displacement: list[tuple[str, Decimal]]) -> Decimal:
    """Neat backfill of one zone (COMPACTED m3, geometric) = excavation - each buried element id once."""
    ids = [e for e, _ in displacement]
    dup = sorted({e for e in ids if ids.count(e) > 1})
    if dup:
        raise ValueError(f"buried volume deducted twice: {dup}")
    b = d6(excavation_in_situ) - sum((d6(v) for _, v in displacement), Decimal(0))
    if b < 0:
        raise ValueError("displacement exceeds the excavation: zone plan or depth wrong")
    return b


def disposal_in_situ(excavation_in_situ, backfill_compacted, k=None, k_source: str | None = None):
    """In-situ m3 leaving the site when all fill is taken from the excavation: E - B x k, k = compacted dry density /
    in-situ dry density (measured or specified). No sourced k -> HELD (None): never E - B (that mixes bases)."""
    if k is None or not k_source:
        return None
    return d6(excavation_in_situ) - d6(backfill_compacted) * d6(k)


def layers(zone_depth_m, lift_m) -> int:
    """Number of finished compacted lifts over a backfill depth (ceil); lift from an answered or provisional rule."""
    zd, lf = d6(zone_depth_m), d6(lift_m)
    if lf <= 0 or zd < 0:
        raise ValueError("bad depth / lift")
    n = int(zd / lf)
    return n + (1 if n * lf < zd else 0)


# ------------------------------------------------------------------------------------------- hand villa (fixture)
def pad_villa(L, B, H, blinding_t, ngl_above_base, neck_b=None, neck_d=None, working_space=None):
    """One pad L x B x H on a blinding of the pad plan x t; NGL `ngl_above_base` above the pad base; neck b x d from
    the pad top to NGL. No working space unless a drawing / approved method prints one (then a plan offset)."""
    L, B, H, t, h = (d6(x) for x in (L, B, H, blinding_t, ngl_above_base))
    if max(L, B, H, t, h) > 50:
        raise ValueError("dimension above 50 m: millimetres passed as metres?")
    ws = d6(working_space) if working_space is not None else Decimal(0)
    plan = (L + 2 * ws) * (B + 2 * ws)
    depth = h + t
    exc = d6(plan * depth)
    pad = d6(L * B * H)
    blind = d6(L * B * t)
    disp = [("PAD", pad), ("BLINDING", blind)]
    if neck_b is not None:
        nh = h - H
        if nh < 0:
            raise ValueError("pad top above NGL")
        disp.append(("NECK", d6(d6(neck_b) * d6(neck_d) * nh)))
    bf = backfill(exc, disp)
    return {"excavation_in_situ": exc, "displacement_solid": sum((v for _, v in disp), Decimal(0)),
            "backfill_compacted": bf, "parts": dict(disp), "depth": depth, "plan": plan}
