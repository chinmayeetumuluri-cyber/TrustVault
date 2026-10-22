# TrustVault — short project write-up

## What I built

TrustVault is a private document-sharing application built with Django. Users upload files, organize them by category, search by document metadata, and grant named people either read or edit access. An administrator can review recent activity and verify the audit event chain.

## Permission model in my own words

Every document has one owner. The owner can view/download, edit metadata, grant or revoke access, and soft-delete that document. A named user can receive a `read` or `edit` grant. Read means view/download only; edit adds metadata changes. It does not permit deletion or sharing onward. An unassigned user is denied. Staff status alone does not let an administrator read file contents. Each request checks the current grant, so revocation affects the next request rather than waiting for a signed link to expire.

## Audit trail

The application records uploads, views, downloads, metadata changes, soft deletions, permission grants/revocations, and denied authorization attempts. Events are linked by HMAC hashes using a separately configured key. The verifier detects altered event fields or broken links while the key is safe. It is not absolute immutability: production should periodically anchor signed chain heads in a separately controlled append-only system.

## AI use

AI helped scaffold the Django application, templates, tests and documentation. The prompt log identifies specific risks requiring review: route-by-route authorization, revocation semantics, audit-chain trust assumptions, upload validation, and the difference between generated code and tested/deployed code. I must keep the prompt log accurate, run tests myself, inspect failures and replace pending commit references with real commits.

## Deliberately not built

No folder-inherited permissions, public share links, version history, malware scanning, MFA/SSO, automatic retention cleanup, or externally anchored audit checkpoints. These were excluded to prioritize a small, understandable per-document permission model. The omissions are recorded in `THREATS.md`.

## Current status

This package is a fresh implementation scaffold with source files, templates, tests and deployment documentation. It must be installed, executed, tested, reviewed and deployed before describing it as fully working. A public repository, live URL, verified test output and demo video cannot be claimed until they actually exist.
