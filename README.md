# TrustVault — Secure document sharing with an audit trail

TrustVault is a Django application prototype for private document sharing. Its key rule is **default deny**: the server checks the current user's document-level permission on every document detail, download, edit, delete and permission-management request.

## Features

- Django authentication; administrator (`is_staff`), document owner and viewer roles.
- Per-document `read` and `edit` grants to named users; owners can update or revoke grants.
- Private file storage outside static/public media roots. Downloads stream through an authorization-checked POST endpoint; raw file URLs are not shown.
- Search/filter by title/filename/description, owner, category and upload date.
- Upload extension, size and basic file-signature checks for PDF, PNG, JPG, TXT and CSV.
- Audit records for upload, view, download, edit, soft delete, permission grant/revoke, and denied authorization attempts.
- HMAC-linked audit chain and a staff-only verification page.
- Security tests for cross-user access, guessed UUIDs, permission revocation, read-vs-edit separation, uploads and audit records.
- Responsive server-rendered UI; no public self-registration.

## Stack

Python 3.11+, Django 5.2, SQLite for local development, PostgreSQL recommended for deployment, Gunicorn and WhiteNoise.

## Local setup

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

python -m pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py check
python manage.py test
```

The application reads environment variables directly; Django does not automatically load `.env`. Set them in your terminal or your hosting provider. For a quick local run, the default development key is present, but do not use it for a public deployment.

### Create a local admin account

```bash
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Sign in at `/accounts/login/`.

### Create disposable demo accounts and seed data

```bash
python manage.py seed_demo --password "Replace-This-Strong-Demo-Pass"
```

This creates `admin_demo`, `owner_demo`, `viewer_demo`, and `outsider_demo`. The shared password is the one supplied to the command. The sample document is owned by `owner_demo`; `viewer_demo` has read-only access; `outsider_demo` has no access.

**Never deploy these demo accounts or shared password unchanged.** Create unique credentials for a public demo, and remove the seeding command/accounts after evaluation if they are not needed.

## Configuration

Copy `.env.example` and set the variables in your shell/host:

- `DJANGO_SECRET_KEY`: long, random, private secret.
- `DJANGO_DEBUG=False` in production.
- `DJANGO_ALLOWED_HOSTS`: comma-separated hostnames, no wildcard.
- `DATABASE_URL`: PostgreSQL URL in production; omit for local SQLite.
- `AUDIT_HMAC_KEY`: separate, long random key. Keep it outside the database and source repository.
- `PRIVATE_MEDIA_ROOT`: optional path for private uploaded files, preferably a persistent private volume.
- `MAX_UPLOAD_MB`: intended upload limit; the current form validation uses a 10 MB application limit.
- `SECURE_SSL_REDIRECT=True` when HTTPS is correctly configured at the host.

Generate secrets with Python, for example `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

## Production/deployment checklist

1. Use PostgreSQL and a persistent **private** file volume or a private object-storage bucket. Never configure `/private_uploads` as a public static/media directory.
2. Set every secret through host environment variables. Never commit `.env`.
3. Set `DJANGO_DEBUG=False`, exact `DJANGO_ALLOWED_HOSTS`, `SECURE_SSL_REDIRECT=True` where appropriate, and enforce HTTPS.
4. Configure backups for the database and private file storage; test restoring both.
5. Run `python manage.py migrate`, `python manage.py check --deploy`, and `python manage.py test`.
6. Create fresh accounts with unique passwords; only the intended admin should have staff/superuser rights.
7. Export audit chain heads to independently controlled, append-only storage on a schedule. A database-local chain alone cannot defeat an attacker who controls both database and audit key.
8. Verify revocation against the deployed system. There are no long-lived signed download URLs in this implementation; every download request checks the current database grant.
9. Confirm the host does not serve uploaded files directly. Only the authenticated download view may return file bytes.

### Generic Render-style deployment

- Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
- Start command: `gunicorn trustvault.wsgi:application`
- Add a managed PostgreSQL `DATABASE_URL` and all required environment variables.
- Mount a persistent disk and set `PRIVATE_MEDIA_ROOT` to its mount path. Ensure it is not publicly served.
- Run `python manage.py createsuperuser` once via the host shell, then create demo users with separate credentials.
- Confirm health, HTTPS, file persistence, and security tests before sharing the live URL.

The deployment provider's filesystem, shell, environment and database behavior may differ; follow its current dashboard instructions and verify the resulting deployment. A live URL is not created by this repository alone.

## Role model

| Role | Read/download | Edit metadata | Grant/revoke | Delete | Audit activity |
|---|---|---|---|---|---|
| Administrator (`is_staff`) | Only if separately granted/owner | Only if separately granted/owner | Owner rule applies; staff does not automatically grant access | Staff can delete through owner/admin delete rule | Yes |
| Owner | Yes, for owned active documents | Yes | Yes, for owned documents | Soft delete | No global audit page unless staff |
| Viewer with `read` grant | Yes, while grant exists | No | No | No | No |
| User with `edit` grant | Yes, while grant exists | Yes | No | No | No |
| Unassigned user | No | No | No | No | No |

Superuser/staff status is deliberately **not** a blanket document-read bypass. A grant is checked from the database for every request.

## API / route documentation

See [`API.md`](API.md) for endpoints, HTTP methods and authorization behavior.

## Security and limitations

- See [`THREATS.md`](THREATS.md) for threat analysis, mitigations and accepted risks.
- See [`PROMPTS.md`](PROMPTS.md) for AI-use records. Continue it during actual work; do not invent commit hashes or claim unrun tests passed.
- See [`WRITEUP.md`](WRITEUP.md) for the design summary and known gaps.
- This is a hiring-challenge starter implementation, not a third-party security certification. Run the test suite and review code before public deployment.

## Demo video outline

A five-minute demo outline is in [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md). Record your own screen and narration after deploying the verified version.
