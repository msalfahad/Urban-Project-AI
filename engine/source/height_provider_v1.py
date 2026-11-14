"""HEIGHT PROVIDER V1 (T-793; owner ACCURACY_PLAN_2026-11-14 change A): the first consumer of PROJECT_INPUTS_V1.

One object per villa that the plaster / paint / ceiling / wet-room wall-tile height families call instead of the
R-T763-1 constants (SLAB 0.16, H 4.34 / 4.04 / 3.84 annex, ceiling drop 0.90, wet ceiling 2.70, tile top 3.00). Every
height is read from the villa's inputs sheet through project_inputs_v1 (one formula each, its components and their
sources, a BOQ label DRAWING-READ / DEFAULT). Nothing here is a constant of any project.

Refusals (never 0, never a default invented here):
  * a storey that is not on the sheet, or a required storey value missing / HELD  -> MissingInputError (refused);
  * a storey height outside STOREY_RANGE_M (a sheet typed in mm or cm, or a typing slip) -> InputsError (refused);
  * a SLOPED storey, or an optional value (ceiling drop, wet ceiling, tile top) HELD   -> result state HELD, and the
    float accessor `value()` raises HeldHeightError: the caller keeps its line HELD.

Wet-room split (R-T763-1 r2): render behind the tiles = tile top; band above it = H - tile top; render + band = H. A
tile top above H is capped at H (the wall ends at the slab soffit) and flagged TILE_TOP_ABOVE_H, band 0 measured.

Project-agnostic; stdlib + project_inputs_v1 only. Reads no candidate and changes no BOQ line (nothing is wired into
arch_v30xx or the hub by T-793).
"""

from __future__ import annotations

from engine.source import project_inputs_v1 as P

SCHEMA = "HEIGHT_PROVIDER_V1"
FAMILIES = ("storey", "plaster", "ceiling", "paint", "wall_tile", "wet_render", "wet_band", "blockwork")
# plausibility band for one storey (FFL to next FFL) in metres: outside it the sheet is refused as a unit / typing error
STOREY_RANGE_M = (2.0, 12.0)
EPS = 1e-9

MissingInputError = P.MissingInputError
InputsError = P.InputsError


class HeldHeightError(ValueError):
    """The height is HELD (sloped storey / optional input HELD): the caller keeps its line HELD, never 0."""


class HeightProvider:
    """Heights of one villa, read from its PROJECT_INPUTS_V1 sheet (dict, JSON text or path)."""

    def __init__(self, sheet):
        self.sheet = P.load(sheet)
        self.project_id = self.sheet["project_id"]
        lo, hi = STOREY_RANGE_M
        for st in self.sheet["storeys"]:
            if "SLOPED" in st["flags"]:
                continue
            h = st["next_ffl"]["value"] - st["ffl"]["value"]
            if not (lo - EPS <= h <= hi + EPS):
                raise InputsError(f"{st['id']}: storey height {h:g} m outside {lo:g} .. {hi:g} m "
                                  "(sheet in mm / cm or a typing slip?): refused, never rescaled")

    # ------------------------------------------------------------------------------------------- results
    def storeys(self) -> list:
        return [st["id"] for st in self.sheet["storeys"]]

    def storey(self, sid: str) -> dict:
        return P.storey_height(self.sheet, sid)

    def plaster(self, sid: str) -> dict:
        return P.plaster_height(self.sheet, sid)

    def ceiling(self, sid: str, wet: bool = False) -> dict:
        return P.ceiling_height(self.sheet, sid, wet=wet)

    def paint(self, sid: str, wet: bool = False) -> dict:
        return P.paint_height(self.sheet, sid, wet=wet)

    def blockwork(self, sid: str, **kw) -> dict:
        return P.blockwork_height(self.sheet, sid, **kw)

    def wall_tile(self, sid: str) -> dict:
        """Wet-room wall-tile top from F.F.L. (owner 2026-11-13: 3.00 on the training villa), capped at H."""
        st = P.storey(self.sheet, sid)
        ph = self.plaster(sid)
        if ph["state"] == P.HELD:
            return P._held(st, "wall tile height", ph["why"])
        tile = st["wet_tile_height"]
        if tile["value"] is None:
            return P._held(st, "wall tile height", "wet_tile_height HELD")
        comps = ph["components"] + [P._comp("wet_tile_height", tile)]
        if tile["value"] > ph["value_m"] + EPS:
            r = P._result(ph["value_m"], "min(wet_tile_height, H) = H", comps, st)
            r["flags"].append("TILE_TOP_ABOVE_H")
            return r
        return P._result(tile["value"], "wet_tile_height (<= H)", comps, st)

    def wet_render(self, sid: str) -> dict:
        """Height of the render behind the wet-room tiles = the tile top (R-T763-1 r2)."""
        r = dict(self.wall_tile(sid))
        if r["state"] == "DERIVED":
            r["formula"] = "render = " + r["formula"]
        return r

    def wet_band(self, sid: str) -> dict:
        """Height of the band above the tile top = H - tile top (all above the wet ceiling, unpainted)."""
        st = P.storey(self.sheet, sid)
        t = self.wall_tile(sid)
        if t["state"] == P.HELD:
            return P._held(st, "wet band height", t["why"])
        ph = self.plaster(sid)
        v = max(0.0, ph["value_m"] - t["value_m"])
        r = P._result(v, "H - min(wet_tile_height, H)", t["components"], st)
        r["flags"] = list(t["flags"])
        if v <= EPS:
            r["note"] = "0 here is a measured result (tiles reach the slab soffit), not a missing value"
        return r

    def get(self, family: str, sid: str, wet: bool = False) -> dict:
        if family not in FAMILIES:
            raise InputsError(f"unknown height family {family!r}; one of {FAMILIES}")
        if family in ("ceiling", "paint"):
            return getattr(self, family)(sid, wet=wet)
        if wet:
            raise InputsError(f"{family}: no wet / dry variant")
        return getattr(self, family)(sid)

    def value(self, family: str, sid: str, wet: bool = False) -> float:
        """The height in metres as a float; raises HeldHeightError when HELD (never returns 0 for missing)."""
        r = self.get(family, sid, wet=wet)
        if r["state"] != "DERIVED" or r["value_m"] is None:
            raise HeldHeightError(f"{family} {sid}{' wet' if wet else ''}: HELD ({r.get('why', '')})")
        return r["value_m"]

    def table(self) -> dict:
        """{storey: {family: metres or None (HELD)}} for a reviewer / the workbook inputs sheet."""
        out = {}
        for sid in self.storeys():
            row = {}
            for fam in FAMILIES:
                for wet in ((False, True) if fam in ("ceiling", "paint") else (False,)):
                    key = fam + ("_wet" if wet else ("_dry" if fam in ("ceiling", "paint") else ""))
                    row[key] = self.get(fam, sid, wet=wet)["value_m"]
            out[sid] = row
        return out
