# Refundly on Render — free demo

Repository: https://github.com/ahmmari691-gif/Refundly_Hackthon

Create **New → Web Service** and connect this repository.

| Setting | Value |
| --- | --- |
| Branch | main |
| Root Directory | refundly |
| Runtime | Python 3 |
| Build Command | pip install -r requirements.txt |
| Start Command | gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 60 |
| Instance Type | Free |
| Health Check Path | /health |

Environment variables:

- `PYTHON_VERSION`: `3.12.8`
- `REFUNDLY_HOSTED`: `1`
- `REFUNDLY_ADMIN_EMAIL`: your admin email (used only as a login; no email is sent)
- `REFUNDLY_ADMIN_PASSWORD`: a new unique password of at least 16 characters. Enter directly in Render, never commit it.

Render supplies `RENDER_EXTERNAL_URL`. For a custom domain, set `PUBLIC_BASE_URL` to its full HTTPS URL without a trailing slash.

After deployment, open the service URL and `/staff.html`. Sign in with the email/password above, enroll in an authenticator app, and create the manager in Team. The local computer's credentials do not work on Render.

**Free demo limitations:** SQLite is ephemeral. Accounts, 2FA enrollment, rule edits, pricing and audit records can reset after restarts/redeploys. The environment admin credentials bootstrap a fresh database. If this happens, enroll again and remove the obsolete authenticator entry. Do not use this demo for real customer operations. Render free services also spin down after inactivity, so the first request can be slow.

For persistent storage later, use a paid Render service with a disk mounted at `/var/data` and set `REFUNDLY_DB=/var/data/staff.sqlite3`. This is not enabled by this package.

The hosted entrypoint is `wsgi.py`; `python app.py` still runs the original localhost preview. Never upload `.local`, database files, `.env`, or the local staff-access file. Payments remain simulated; no Stripe or email is configured.

References: https://render.com/docs/deploy-flask and https://render.com/docs/free
