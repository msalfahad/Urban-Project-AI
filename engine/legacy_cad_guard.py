"""LEGACY CAD GUARD - user-facing command-line tools whose import graph reaches engine/cad_adapter.py (the legacy
LibreDWG adapter with known defects: handle-identity collision, block-lineage loss; see R8.2 / R8.3 registers) refuse
to run unless the caller opts in explicitly.

    argv = require_legacy_opt_in("tools/run_cad_pipeline.py", argv)

Opt-in: the flag --allow-legacy-cad-adapter (removed from argv before the tool parses it) or the environment variable
URBAN_ALLOW_LEGACY_CAD_ADAPTER=1. With an opt-in a warning is printed and the tool runs unchanged (historical
reproduction of earlier rounds). Without it the tool exits with status 2 and names the supported route (K1 / K2
canonical input, engine/source). Importing a tool module is never blocked - only its command-line entry point.
"""

from __future__ import annotations

import os
import sys

FLAG = "--allow-legacy-cad-adapter"
ENV = "URBAN_ALLOW_LEGACY_CAD_ADAPTER"
MESSAGE = ("{tool} runs through engine/cad_adapter.py, the legacy CAD adapter with known defects (handle-identity "
           "collision, block-lineage loss). It must not be used for a new project. Use the K1 / K2 canonical-input "
           "route (engine/source). To reproduce a historical round deliberately, pass " + FLAG + " or set " + ENV
           + "=1.")


def require_legacy_opt_in(tool, argv=None):
    """Return argv without the opt-in flag; exit (status 2) when there is no explicit opt-in. argv=None means the
    tool parses sys.argv itself: the flag is then removed from sys.argv in place and None is returned."""
    live = argv is None
    args = list(sys.argv[1:] if live else argv)
    opted = FLAG in args or os.environ.get(ENV) == "1"
    if not opted:
        sys.stderr.write("LEGACY_CAD_ADAPTER_REFUSED: " + MESSAGE.format(tool=tool) + "\n")
        raise SystemExit(2)
    args = [a for a in args if a != FLAG]
    sys.stderr.write(f"WARNING: {tool} is using the legacy CAD adapter by explicit opt-in.\n")
    if live:
        sys.argv[1:] = args
        return None
    return args
