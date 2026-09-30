"""Urban source engine — read the source correctly, before anything interprets it.

R8.1 scope: neutral source observations, the K1 canonical CAD geometry
kernel, source findings and the two digests. Nothing here identifies a wall
or a room, applies a trade rule, assigns a material, infers a unit or
publishes a quantity.

DEPENDENCY RULE (enforced by tests/r8_0/test_r8_0_import_boundaries.py):
engine.source is UPSTREAM. It imports only the standard library and other
engine.source modules (the source dependency register also allows ezdxf,
shapely and numpy; R8.1 deliberately uses none of them, see
cad/kernel_ocs.py). It never imports engine.qs_core, engine.ingest,
research, tests, MCP servers, donor engines or live-AutoCAD COM.
"""
