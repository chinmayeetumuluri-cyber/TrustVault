# AI use log — TrustVault

This file is intentionally a working log. Keep it updated during implementation and commit it with the code changes. Do not backdate entries or invent commit hashes. Replace `PENDING` with actual commit links after committing the related fix.

## Reused context / instructions

- Core requirement: server-side default-deny authorization for every document route; UI visibility is not security.
- Re-check permissions at download time; revocation must affect subsequent requests.
- Keep audit events for both allowed and denied actions; document the limits of a database-local hash chain.
- Prefer the smallest understandable implementation over broad features that cannot be tested.
- Never claim tests passed unless they were actually run.

## 2026-10-21 — Entry 1: Initial architecture and clean rebuild

- **Prompt / request:** “Build TrustVault from scratch from the full challenge requirements. The old project has errors; do not rely on it.”
- **Produced:** Django project layout, document/category/grant/audit models, route map, initial permission helpers and responsive templates.
- **What was wrong / needed review:** Generated code is not verified merely because it looks complete. File storage defaults needed explicit review because private documents must not be exposed through a public media route. Role semantics and all route checks needed direct tests.
- **What I did instead:** Added a dedicated private filesystem storage class, authorization helper functions, and tests that call document endpoints directly. Still requires running the suite in an installed environment and reviewing each route.
- **Fix commit:** PENDING — create a commit after local verification and replace this line with its actual GitHub commit URL.

## 2026-10-21 — Entry 2: Authorization and revocation review

- **Prompt / request:** “Ensure a user cannot read, download, edit or delete another user's document by changing the URL, and access revocation must work immediately.”
- **Produced:** `can_read`, `can_edit`, owner checks on grant/delete routes, protected detail/download/edit/delete views, and cross-user regression tests.
- **What was wrong / needed review:** UUIDs are not authorization. A detail-page-only check would leave download or edit routes exposed; a signed or cached download URL would weaken immediate revocation. Admin status can also accidentally become a blanket read bypass.
- **What I did instead:** Put checks in each view and made each download POST re-query the grant. Added tests for guessed UUIDs, read-vs-edit separation, revocation, and administrator non-bypass. Run tests and add any missing route cases before submission.
- **Fix commit:** PENDING — replace with the actual commit URL after committing the authorization and tests.

## 2026-10-21 — Entry 3: Audit integrity review

- **Prompt / request:** “Create an audit trail for uploads, downloads, changes, deletions, permission changes and denied access attempts, and explain how it can be trusted.”
- **Produced:** `AuditEvent` records with HMAC-linked event hashes, a staff-only audit view, and a chain-verification endpoint.
- **What was wrong / needed review:** A plain hash chain is not immutable, and a database administrator may delete the tail or rewrite the chain if they also control the signing key. Concurrent writes may race. Calling this “tamper-proof” would be inaccurate.
- **What I did instead:** Describe it as tamper-evident, keep the HMAC key in environment configuration, add a verifier, and document external append-only checkpointing and concurrency serialization as production hardening gaps.
- **Fix commit:** PENDING — replace with the actual commit URL after committing audit logic/tests/docs.

## 2026-10-21 — Entry 4: Upload validation review

- **Prompt / request:** “Validate uploaded file type and size rather than trusting the browser's filename.”
- **Produced:** An allowlist for PDF, PNG, JPG, TXT and CSV, a 10 MB limit, and basic file signature checks.
- **What was wrong / needed review:** Extension and a short signature check are not malware scanning and do not make arbitrary file formats safe. Text files can contain active content if later rendered unsafely, and request bodies may be parsed before form-level size validation.
- **What I did instead:** Limit supported types, never render uploaded file contents inline, store files privately, use Django's escaped templates, and document the need for reverse-proxy limits and malware scanning in production.
- **Fix commit:** PENDING — replace with the actual commit URL after committing upload validation and tests.

## 2026-10-21 — Entry 5: Submission and threat coverage review

- **Prompt / request:** “Prepare API documentation, threats, setup/deployment instructions, seed data and a demo plan for the hiring challenge.”
- **Produced:** `README.md`, `API.md`, `THREATS.md`, `WRITEUP.md`, `DEMO_SCRIPT.md` and a demo seeding command.
- **What was wrong / needed review:** Documentation can overstate security or imply a live deployment and tests exist before they do. Seed credentials must not be silently reused on a public deployment, and a generated project is not the same as a verified submission.
- **What I did instead:** Marked deployment/test verification as required, made the seed password an explicit command argument, documented accepted risks, and left commit links pending rather than inventing them.
- **Fix commit:** PENDING — replace with the actual commit URL after reviewing and committing these docs.

## Ongoing entries

Append a new dated entry whenever AI contributes to a material change. State the specific issue you caught, how you verified the fix, and the real commit URL. Before submission, replace every `PENDING` line with a real commit link or explain honestly why no commit exists. Do not claim a test passed until you ran it.
