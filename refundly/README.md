# Refundly — local demo with staff workspaces

English-language renter tool, public landing page, demonstration checkout, PDF export, and role-based staff workspace. Python 3.9+ with ReportLab. No Stripe, email, or AI API keys required.

## Run
```sh
cd refundly
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 app.py
```
Open http://127.0.0.1:8000. Staff: http://127.0.0.1:8000/staff.html. Stop with Ctrl+C. Change the port with `--port 8001`.

The active working copy for this chat is `/Users/masha/Documents/Codex/2026-11-14/x20/outputs/depositback`; that directory name is retained for compatibility. On this computer it is running with the bundled Python runtime, which already includes ReportLab.

## First staff sign-in
On the first run, unique random passwords are generated for `admin@refundly.demo` and `manager@refundly.demo`. Find them in `.local/staff-access.txt`, which is not web-served or included in source archives. On first sign-in, enter email/password and leave the code blank. Add the displayed setup key to an authenticator app, then submit the current 6-digit code. All later sign-ins require a fresh code. New accounts created by an admin also require enrollment.

Passwords use salted PBKDF2-HMAC-SHA256 (600,000 iterations); the SQLite database stores session token hashes. Sessions use HttpOnly/SameSite cookies, expire after 8 hours, and are revoked when access or roles change. State-changing staff API requests require same-origin JSON and a session CSRF token. TOTP rejects reused codes, and repeated failed sign-ins are throttled.

This runs only on loopback HTTP. It is a local development demonstration, not production-ready authentication infrastructure: TOTP seeds are locally stored with filesystem access protection, not encrypted using a production key service; cookies must be Secure over HTTPS in a deployed service. No public deployment was performed. Do not deploy the standard-library server or share the `.local` directory.

Implementation references: [Python password hashing](https://docs.python.org/3/library/hashlib.html#hashlib.pbkdf2_hmac), [TOTP RFC 6238](https://www.rfc-editor.org/rfc/rfc6238).

## Renter workflow — no account
- Homepage, existing visual direction, example case, FAQ, terms/privacy.
- Five-state rental form with native and field-level validation.
- Add, remove, duplicate deductions; live totals and unexplained withholding.
- Temporary draft in the browser tab's session storage, with explicit clear action. No renter case, email, payment, or document is persisted server-side.
- Preliminary rule-based assessments, conditional remedies, official sources.
- Simulated checkout at the configured price (default $19), decline/retry flow. No real card form, charge, or order. The frontend gate is a demo interaction, not a payment entitlement system.
- Editable demand/follow-up letter. Download TXT or directly generated PDF. PDF evidence/sending guide, print option, calendar reminder.
- PDFs are generated in memory and returned directly. Font requests go to Google Fonts; user-entered content is not included.

## Manager workspace
Synthetic, explicitly labelled requests only. Search by masked email/case/payment/subject; status/state/assignee filters. Status and ownership changes, replies, private notes, published response templates, escalation to admin, quality review, and full demo refunds. Refund reasons/comments are mandatory; managers cannot issue partial or repeat refunds. No reply or notification is actually emailed.

## Admin workspace
Includes manager tools plus state-rule drafts, publication, history and restoration; price and checkout toggle; synthetic payment listing/CSV and partial demo refunds bounded by the paid amount; staff creation, roles, disabling and session revocation; append-only audit log; homepage hero copy, staff announcement and maintenance mode; publishing proposed support-response templates.

Published rule changes affect anonymous review calculations and explanations. Classification code does not treat fixed asset lifetimes as law. Historical effective-date rules and local ordinances require legal review.

## Boundaries and remaining specification items
This build covers the requested local demo foundation, not every production module in the supplied specification. Not implemented: live Stripe/Apple Pay/Google Pay, email, real renter case storage or magic-link login (excluded by request), My Case/My Data, uploads/retention/deletion workflows, real customer support intake, visitor/conversion analytics, promo codes, bulk queue actions, full date/type/sort filtering, AI instructions and state-specific letter-template version editor, separate itemization/return deadline schema, small-claims limit administration, rule test sandbox, scheduled legal-review reminders, editable FAQ/disclaimer UI, password recovery, deployment hardening, and a formal complete accessibility audit. These are not silently represented as working features.

The staff metrics and payment records are synthetic fixture data, not business revenue or actual customer outcomes. Support response templates are distinct from the deterministic legal-letter generator.

## Tests
```sh
python3 -m unittest discover -v
```
24 tests cover legal examples and validation, role denial, CSRF/origin checks, TOTP reference vector and replay prevention, session revocation, refund boundaries, draft/publish/restore behavior, and audit immutability. Staff tests use isolated temporary databases. Source JavaScript syntax and the browser's administrator sign-in and renter checkout/PDF download flow were checked.

## Backup and data
`Refundly-before-roles.zip` is the unchanged pre-workspace code backup. Current source packages intentionally exclude `.local`, caches, local passwords, test credentials, and virtual environments. Starting a clean archive generates its own local staff database and passwords.

Rules sources reviewed November 14, 2026: links in `app.py` and UI; California court guidance at https://selfhelp.courts.ca.gov/guide-security-deposits-california was accessible, direct statute access returned 403. Texas context: https://guides.sll.texas.gov/landlord-tenant-law/security-deposit-refunds . Rules remain preliminary and require legal review before any production use.

Artwork details are in `ARTWORK.md`. The supplied Refundly logo is used unchanged, framed with CSS.

## State-law provenance
`law_catalog.json` is the version-controlled baseline, checked 2026-11-14.
NY, TX and FL summaries were compared with official statutory text. CA was
checked against official DRE guidance because the statute endpoint was blocked.
IL remains explicitly partial: official indexed excerpts confirmed deadlines,
but the full text and remedy still need rechecking. These are editorial checks,
not attorney certification, and do not cover all local rules or case law.

The public State law library shows the source actually checked, sections, date,
limitations and published/archived record history. Drafts and staff identities
are private. Admins must supply a change summary, source-check method and date;
only approved state-source HTTPS hosts are accepted. Publication preserves the
previous version; restoration creates a new record. Legacy system entries are
migrated without overwriting administrator edits or inventing prior checks.

On free Render, SQLite staff edits/history are ephemeral. The committed baseline
survives redeployment; later admin changes require exporting history JSON and
committing a reviewed baseline, or moving SQLite to persistent storage. No
scheduled legal monitoring or automatic verification is claimed.
