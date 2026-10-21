"""A guarded Firestore writer for Phase 0 — sandbox only.

Turns on ONLY when three things are true, so a stray run can never touch
production:

1. `firebase-admin` is installed.
2. A service-account key is available (env `URBAN_FIREBASE_SA` path, or the
   standard `GOOGLE_APPLICATION_CREDENTIALS`).
3. The explicit opt-in `URBAN_ALLOW_SANDBOX_WRITE=1` is set.

Even then, the writer refuses any collection path outside the `sandbox/` tree.
"""

from __future__ import annotations

import os
from typing import Callable

SANDBOX_ROOT = "sandbox"


class SandboxWriteDisabled(RuntimeError):
    pass


def sandbox_enabled() -> bool:
    return os.environ.get("URBAN_ALLOW_SANDBOX_WRITE") == "1"


def build_sandbox_writer() -> Callable[[str, dict], str]:
    """Build a live firebase-admin writer restricted to the sandbox tree.

    Raises SandboxWriteDisabled with a clear reason if any precondition is
    missing, so the CLI can fall back to a dry run and tell the user what to set.
    """
    if not sandbox_enabled():
        raise SandboxWriteDisabled(
            "sandbox writes are off — set URBAN_ALLOW_SANDBOX_WRITE=1 to enable (test-only)."
        )

    sa_path = os.environ.get("URBAN_FIREBASE_SA") or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not sa_path or not os.path.exists(sa_path):
        raise SandboxWriteDisabled(
            "no service-account key found — set URBAN_FIREBASE_SA to the JSON key path "
            "(never commit it; it is gitignored)."
        )

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError as exc:
        raise SandboxWriteDisabled(
            "firebase-admin is not installed — run `pip install firebase-admin`."
        ) from exc

    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(sa_path))
    db = firestore.client()

    def _write(collection_path: str, document: dict) -> str:
        if not collection_path.startswith(SANDBOX_ROOT + "/") or collection_path.startswith("projects/"):
            raise SandboxWriteDisabled(f"refusing to write outside the sandbox: {collection_path!r}")
        ref = db.collection(collection_path).document()
        ref.set(document)
        return ref.id

    return _write
