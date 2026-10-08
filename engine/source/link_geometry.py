"""LINK GEOMETRY - stirrup / link topology and envelope lower bounds for accurate beam reinforcement (generic).

Stdlib only. Pure functions; no project values. Every length is an ENVELOPE LOWER BOUND under stated premises:

  core_path_mm(b, h, cover, d)
      closed rectangular link, measured on the bar centreline with the corners taken sharp:
          2 (b - 2c - d) + 2 (h - 2c - d)
      Cover is taken to the link's outer face. If the project cover is measured to the main bars instead, the link
      only grows, so the value stays a lower bound under either reference face. Hooks, hook extensions and bend
      allowances are NOT included; they are separate blocked facets. Corner rounding shortens the loop by
      (8 - 2 pi) R per link (R = centreline bend radius), which the drawn closing hooks more than add back. That is a
      stated premise of the lower bound, not a code value.

  end_leg_mm(h, cover, d_link, d_top, d_bottom)
      a top bar turned down at an end support whose foot reaches the bottom-bar level:
          (h - c - d_link - d_top / 2) - (c + d_link + d_bottom / 2)
      the centre-to-centre drop between the two bar layers. Bend radius and any extension below the bottom bar are
      excluded.

  count_lower_bound(rate_per_m, run_m)  = ceil(rate x run); no +1 end bar
  topology_from_closed_links(n)         = {"links": n, "legs": 2 n}; one closed rectangular link has two vertical legs
  invariant(interpretations, keys)      = the shared value of `keys` when every surviving interpretation agrees, else None
"""

from __future__ import annotations

import math

SINGLE_CLOSED_LINK = "SINGLE_CLOSED_LINK_2_LEG"
STR2 = "STR2_OUTER_PLUS_ONE_INNER_4_LEG"
STR3 = "STR3_OUTER_PLUS_TWO_INNER_6_LEG"
TOPOLOGIES = {SINGLE_CLOSED_LINK: 1, STR2: 2, STR3: 3}

CORE_PATH_PREMISES = (
    "closed rectangular link on the bar centreline, corners sharp",
    "cover taken to the link outer face (a main-bar cover reference only enlarges the link)",
    "hooks, hook extensions and bend allowances excluded (separate blocked facets)",
    "corner rounding (8 - 2 pi) R per link is offset by the drawn closing hooks",
)


class LinkGeometryError(ValueError):
    pass


def _positive(**kw):
    for k, v in kw.items():
        if v is None or v <= 0:
            raise LinkGeometryError(f"{k} must be a positive number, got {v!r}")


def topology_from_closed_links(n_links):
    if n_links not in (1, 2, 3):
        raise LinkGeometryError(f"unsupported link set: {n_links} closed links")
    name = {1: SINGLE_CLOSED_LINK, 2: STR2, 3: STR3}[n_links]
    return {"topology": name, "links": n_links, "legs": 2 * n_links}


def core_path_mm(b_mm, h_mm, cover_mm, d_mm):
    """Lower-bound centreline core path of the outer closed link of a b x h section."""
    _positive(b_mm=b_mm, h_mm=h_mm, cover_mm=cover_mm, d_mm=d_mm)
    w = b_mm - 2 * cover_mm - d_mm
    t = h_mm - 2 * cover_mm - d_mm
    if w <= 0 or t <= 0:
        raise LinkGeometryError("section too small for the cover and link diameter")
    return 2.0 * w + 2.0 * t


def end_leg_mm(h_mm, cover_mm, d_link_mm, d_top_mm, d_bottom_mm):
    """Lower-bound vertical leg of a top bar turned down to the bottom-bar level (centre to centre)."""
    _positive(h_mm=h_mm, cover_mm=cover_mm, d_link_mm=d_link_mm, d_top_mm=d_top_mm, d_bottom_mm=d_bottom_mm)
    top = h_mm - cover_mm - d_link_mm - d_top_mm / 2.0
    bottom = cover_mm + d_link_mm + d_bottom_mm / 2.0
    if top <= bottom:
        raise LinkGeometryError("section too shallow for the bar layers")
    return top - bottom


def count_lower_bound(rate_per_m, run_m):
    """ceil(rate x run) with a small tolerance against binary noise; no +1 end bar."""
    _positive(rate_per_m=rate_per_m, run_m=run_m)
    return int(math.ceil(rate_per_m * run_m - 1e-9))


def invariant(interpretations, keys):
    """The common value of `keys` across all interpretations (dicts), or None if any differ or none survive."""
    if not interpretations:
        return None
    first = tuple(interpretations[0].get(k) for k in keys)
    if any(v is None for v in first):
        return None
    for it in interpretations[1:]:
        if tuple(it.get(k) for k in keys) != first:
            return None
    return dict(zip(keys, first))
