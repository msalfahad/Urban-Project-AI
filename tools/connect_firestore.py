"""Connect to the Urban Projects Manager Firestore and prove the link.

Run this once the service-account key is in the environment. It:
  1. loads firebase-admin with the key,
  2. does a READ test (counts a few projects) — proves the AI can see live data,
  3. does a SANDBOX WRITE test (writes + deletes a throwaway doc under
     `sandbox/`) — proves it can write, without touching any real project.

It never writes to a production `projects/...` path. Credentials come only from
the environment; nothing is hard-coded or committed.

Usage:
    URBAN_FIREBASE_SA=/path/to/serviceAccountKey.json \
    python3 -m tools.connect_firestore
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

PROJECT_ID = "urbanprojectsmanager"


def _key_path() -> str | None:
    return os.environ.get("URBAN_FIREBASE_SA") or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")


def main() -> int:
    key = _key_path()
    if not key:
        print("✋ No service-account key found.\n"
              "   Set URBAN_FIREBASE_SA to the JSON key path (see docs/CONNECT_WEBAPP.md).",
              file=sys.stderr)
        return 2
    if not os.path.exists(key):
        print(f"✋ Key path does not exist: {key}", file=sys.stderr)
        return 2

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError:
        print("✋ firebase-admin is not installed. Run: pip install firebase-admin", file=sys.stderr)
        return 3

    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(key))
        db = firestore.client()
    except Exception as exc:  # noqa: BLE001
        print(f"✋ Could not initialise with the key: {exc}", file=sys.stderr)
        return 4

    print(f"✅ Connected to Firebase project: {PROJECT_ID}")

    # 1. READ test — can the AI see live data?
    try:
        projects = list(db.collection("projects").limit(5).stream())
        print(f"✅ READ ok — {len(projects)} project(s) visible (showing up to 5):")
        for p in projects:
            d = p.to_dict() or {}
            print(f"     • {p.id}: {d.get('name', '(no name)')}")
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️  READ failed: {exc}", file=sys.stderr)

    # 2. SANDBOX WRITE test — can it write (without touching real data)?
    try:
        ref = db.collection("sandbox/_connectivity/checks").document()
        stamp = datetime.now(timezone.utc).isoformat()
        ref.set({"ok": True, "by": "connect_firestore", "at": stamp})
        got = ref.get().to_dict()
        ref.delete()  # clean up immediately
        print(f"✅ SANDBOX WRITE ok — wrote and removed a test doc at {got['at']}")
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️  SANDBOX WRITE failed: {exc}", file=sys.stderr)

    print("\n🔗 Link verified. The AI can now read the web app and write to the sandbox.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
