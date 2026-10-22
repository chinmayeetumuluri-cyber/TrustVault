# Threat model — TrustVault

## Security objective

A document's bytes and metadata are reachable only by its owner or a user with a current document-level grant. Revocation must affect the next request. Audit evidence should reveal unauthorized attempts and ordinary database tampering.

## Permission model and trust boundaries

- Default deny. The document UUID is an identifier, not a capability.
- Owner can read, download, edit metadata, grant/revoke, and soft-delete their own document.
- A `read` grant allows read/download only. An `edit` grant allows read/download and metadata edits.
- Staff can inspect audit activity and may perform administrative deletion/grant operations, but staff/superuser status alone does not grant document read/download.
- Uploaded bytes live under `PRIVATE_MEDIA_ROOT`, separate from static files; the app streams them only after checking current access.
- Revocation deletes the grant row. There are no expiring or permanent share URLs, so the next request consults the database.
- The application server and configured audit key are trusted. A host/database administrator is not fully constrained by this prototype.

## Threats, mitigations, and tests

| Threat | Mitigation | Test / residual risk |
|---|---|---|
| Insecure direct object reference (guess/change UUID) | UUID IDs plus authorization on every detail/download/edit/delete/grant route; UUID is not treated as secret | `test_ungranted_user_cannot_view_detail`, `test_ungranted_user_cannot_download_even_with_guessed_uuid`, edit/delete tests |
| Hidden buttons treated as access control | Views enforce permissions independently of templates | Direct HTTP tests call endpoints without using UI |
| User with read grant edits metadata | `can_edit` requires owner or `edit` grant | `test_read_grant_does_not_allow_edit` |
| User with edit grant deletes or shares onward | Delete/grant management require owner or staff | `test_edit_grant_allows_edit_but_not_delete` |
| Revoked grant still works | Permission queried on each request; no long-lived signed URLs | `test_grant_read_then_revoke_blocks_next_download` |
| Unauthorized user downloads file via public media path | Custom private storage, no `MEDIA_URL` route; download view is the only app route returning file bytes | Verify deployment web server/object storage does not expose private root |
| Upload executable disguised as PDF | Extension allowlist, size limit and basic magic/signature checks for PDF/PNG/JPEG; null-byte check for text | Upload tests reject unsupported extension and invalid PDF signature. This is not full malware scanning or comprehensive parser validation |
| Oversized upload / resource exhaustion | 10 MB application limit; configure reverse-proxy request limits too | The app-level form check occurs after request parsing; host-level limits are still needed |
| CSRF on grant/revoke/delete/upload | Django CSRF middleware, forms include CSRF token, state changes use POST | Add explicit CSRF regression tests before production |
| Cross-site content sniffing / framing | `nosniff`, `X-Frame-Options: DENY`, private no-store on download | Validate headers on deployed HTTPS endpoint |
| Audit event modified in database | HMAC over canonical event fields and previous-event hash; staff verification detects changed fields/order when key remains secret | `test_audit_chain_links_events`; add tests that mutate event fields and verify failure |
| Audit rows deleted or entire chain rewritten | Chain link + external key makes casual edits detectable | **Accepted limitation:** database-only chain cannot prove deletion of the tail; privileged attacker with DB and key can forge a new chain. Export signed chain heads to separately controlled append-only storage |
| Audit event contains private content | Events store identifiers, usernames, action and metadata, not document bytes | Avoid logging document contents, credentials or sensitive request bodies |
| Admin account compromise | Admin activity is role-gated; admin status doesn't bypass read checks | Strong unique passwords, MFA/SSO and least privilege are deployment work |
| Session theft | HttpOnly/SameSite cookies, secure cookies in production, HTTPS expected | Session expiry, MFA and device/session revocation need further hardening |
| User enumeration through login | Generic login error; no public registration | Rate limiting and monitoring are not implemented |
| Race between revoke and in-flight download | Access checked at request start; no long-lived URL | **Accepted limitation:** a download already authorized and streaming may finish after revocation. Revocation blocks subsequent requests; cannot claw back bytes already delivered |
| File changed on disk after upload | SHA-256 recorded at upload and shown in metadata | Current download does not re-hash bytes. Add integrity verification on read or immutable/object-lock storage |
| Audit chain concurrency | Sequential chain uses latest event hash | **Known limitation:** concurrent writes can race without a database-wide serialization strategy. Use a transactional sequence/lock for production and test concurrency |
| Soft-deleted document's file remains on disk | Deleted rows are excluded from access; audit event retained | **Known limitation:** physical file cleanup/retention workflow is not implemented; backups may retain bytes |
| Stored XSS via document title/filename | Django template autoescaping; filename sanitized to basename | Keep autoescaping enabled; do not mark user content safe |
| SQL injection through search filters | Django ORM parameterization | Avoid raw SQL without parameters |
| Insecure deployment defaults | production check warns on default key, shared audit key and wildcard hosts | Must set secrets, DEBUG=False, exact hosts, HTTPS, PostgreSQL and private persistent storage before live use |

## What the tests prove

The test suite exercises authorization through direct requests rather than only checking whether links are hidden. The test suite should be run with `python manage.py test` after each security-sensitive change. A meaningful regression test must fail if its corresponding authorization check is removed.

## Accepted risks / not implemented

1. No malware scanning, antivirus quarantine, or deep file parser validation.
2. No MFA, enterprise SSO, rate limiting, password-reset email flow, or account lifecycle automation.
3. No external append-only audit sink; current HMAC chain assumes the key remains separate from the database.
4. No complete concurrent audit-chain serialization guarantee.
5. No cryptographic revalidation of file contents at every download.
6. No automatic physical deletion/retention cleanup for soft-deleted files.
7. No signed, externally anchored audit checkpoints.
8. No groups, folder inheritance, public/external sharing links, version history, or recovery UI.
9. No in-flight download cancellation when a grant is revoked; only subsequent requests are blocked.
10. Local filesystem storage is suitable for local evaluation, not horizontally scaled production without a private shared/object storage design.

## Before publishing a live URL

Use separate secrets, production settings, PostgreSQL, private persistent storage, HTTPS, unique demo credentials, database/file backups, external audit checkpoints, host-level upload limits, and a final authorization attack pass. Never upload real confidential documents to the demo.
