# TrustVault route/API documentation

TrustVault currently uses Django server-rendered HTML routes rather than a separate JSON REST API. State-changing requests require authentication, POST, and Django CSRF protection.

| Route | Method | Who may call it | Behavior |
|---|---|---|---|
| `/accounts/login/` | GET/POST | Anyone | Django session login |
| `/accounts/logout/` | POST | Authenticated user | Logout; CSRF protected |
| `/` | GET | Authenticated user | Lists only owned or explicitly granted active documents; supports query filters |
| `/documents/upload/` | GET/POST | Authenticated user | Uploads a validated file; authenticated user becomes owner |
| `/documents/<uuid>/` | GET | Owner or user with current grant | Document details; unauthorized existing document returns 403 and is audited |
| `/documents/<uuid>/download/` | POST | Owner or user with current grant | Re-checks access on every request, audits, then streams file bytes |
| `/documents/<uuid>/edit/` | GET/POST | Owner or user with `edit` grant | Changes title, description, category |
| `/documents/<uuid>/delete/` | POST | Owner or superuser | Soft-deletes from active access and records event |
| `/documents/<uuid>/grants/` | POST | Owner or superuser for that document | Creates/updates a named user's `read` or `edit` grant |
| `/documents/<uuid>/grants/<user_id>/revoke/` | POST | Owner or superuser for that document | Deletes the current grant; subsequent requests are denied |
| `/admin/activity/` | GET | Authenticated staff | Shows recent audit events |
| `/admin/activity/verify/` | GET | Authenticated staff | Verifies the HMAC chain |
| `/admin/` | GET/POST | Django admin staff/superuser as configured | Model administration; audit events are read-only through admin |

## Authorization details

- All document routes resolve the UUID and then call a server-side permission helper or owner check. Hiding UI controls is not considered authorization.
- An administrator does not automatically gain read/download permission; the admin must also own or be granted the document. Staff can inspect audit records.
- A `read` grant cannot edit, delete, or manage grants.
- An `edit` grant permits metadata editing and download, but not deletion or grant management.
- Upload validation is enforced by a Django form. Direct-to-storage public links are not generated.
- Downloads require POST, session authentication, CSRF and a current permission check.
- Login redirects anonymous users to the login page.
- Unknown document UUIDs return 404. Unauthorized requests for known documents return 403 and create an audit event.

## Error behavior

- `302`: unauthenticated request redirected to login.
- `403`: known document but insufficient permission.
- `404`: document missing, soft-deleted, or file missing.
- Form errors: rendered with validation feedback; no document is created on invalid upload.

These routes are not a versioned public API. If a JSON API is added later, it must reuse the same authorization functions and tests rather than implementing separate weaker checks.
