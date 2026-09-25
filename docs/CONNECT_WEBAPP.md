# Linking the AI system to Urban Projects Manager

Both run on the same Firebase project (`urbanprojectsmanager`), so linking is a
matter of giving the AI system a **service-account key** to authenticate with —
then it can read the web app's data and write to it.

## Access status (honest)

| | Access |
|--|--------|
| The app's **source code** (models, rules, functions) | ✅ full read (repo cloned) |
| The app's **live data** (projects, BOQs, pricing in Firestore) | ❌ none until the key below is provided |

The key can only be generated from **your** Firebase account — that login is
yours, so this one step needs you. Everything else is built and waiting.

## The key — 5 steps (about 2 minutes)

1. Open **console.firebase.google.com** and sign in.
2. Select the project **urbanprojectsmanager**.
3. Click the **gear icon** (top-left, next to "Project Overview") → **Project settings**.
4. Open the **Service accounts** tab → click **Generate new private key** → confirm **Generate key**.
   - A file downloads, named like `urbanprojectsmanager-firebase-adminsdk-xxxxx.json`.
5. **Give it to this session** — either:
   - **upload the JSON file here** in the chat (it stays in this private, temporary
     workspace and is gitignored — never committed), or
   - add it as an environment secret and tell me the path.

Then tell me it's in, and I run:

```bash
URBAN_FIREBASE_SA=/path/to/key.json python3 -m tools.connect_firestore
```

which does three things and prints the result:
1. **Connects** to `urbanprojectsmanager`.
2. **Reads** — lists a few real projects (proves the AI can see the web app).
3. **Sandbox write** — writes and immediately deletes a throwaway test doc under
   `sandbox/` (proves it can write, without touching any real project).

## This key is a password — handle it that way

An Admin SDK key has broad access to the project. So:

- ❌ never paste its **contents** into chat (upload the file instead).
- ❌ it is never committed — `.gitignore` already blocks `*-service-account.json`,
  `serviceAccountKey.json`, and `*-adminsdk-*.json`.
- ✅ it lives only in this temporary workspace; when the session ends it's gone.

**Optional, more locked-down:** if you'd rather not hand over a full Admin key, you
can instead create a narrower service account in the Google Cloud console with
only the **Cloud Datastore User** role (Firestore read/write, nothing else). Tell
me and I'll give you those clicks. The standard Firebase key above is fine for a
first link.

## What happens after the link works

- I can read the **Alsenan Chalet** project's real pricing/units directly (no more
  PDF export needed) to keep the Rate Library in step.
- The **project-creation flow** can write an approved BOQ into a **test project**
  in the app (still sandbox-guarded — no production project is touched without
  your say-so).
- The **orchestrator** can be wired to real Firestore triggers so the agents loop
  automatically.
