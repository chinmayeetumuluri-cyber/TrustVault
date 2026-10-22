# Five-minute TrustVault demo script

Record this after deploying and verifying the current code. Use a demo environment with fictional data only.

**0:00–0:30 — Intro**
- State the problem: document access must be per-person and auditable.
- Show the TrustVault dashboard and explain the default-deny permission model.

**0:30–1:15 — Upload and organize**
- Sign in as `owner_demo`.
- Upload a harmless sample PDF or text file.
- Show category, metadata, hash and search/filter behavior.

**1:15–2:00 — Grant access**
- As owner, grant `viewer_demo` read access.
- Sign in as viewer and open/download the document.
- Explain that the server checks the database grant on each request.

**2:00–2:45 — Attack and revoke**
- Sign in as `outsider_demo` and attempt the same document URL and download POST; show the denial.
- As owner, revoke viewer access.
- Sign in as viewer and repeat the request; it should now be denied.
- Use actual observed behavior only; do not edit or stage a simulated result.

**2:45–3:45 — Audit evidence**
- Sign in as admin and open Audit activity.
- Show allowed and denied events, actor, timestamp and target.
- Run audit verification and explain both what it detects and its limits.

**3:45–4:30 — Automated tests**
- Show the actual output of `python manage.py test`.
- Point to the tests for guessed IDs, cross-user access, revocation and read/edit separation.

**4:30–5:00 — Trade-offs**
- Explain the private file storage, no public download URL, and why revocation blocks subsequent requests.
- Name accepted risks honestly: external audit anchoring, malware scanning, concurrency and production operational hardening.
