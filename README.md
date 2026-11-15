<p align="center">
  <img src="refundly/static/assets/refundly-logo.jpg" alt="Refundly logo" width="230">
</p>

<h1 align="center">Refundly</h1>
<p align="center"><strong>Your deposit. Your next move.</strong><br>Understand rental deductions, explore your state's rules, and put your dispute in writing.</p>
<p align="center">
  <a href="https://refundly-sxo7.onrender.com">Live demo</a> ·
  <a href="https://refundly-sxo7.onrender.com/review?example=1">Try an example</a> ·
  <a href="#staff-access--account-setup">Staff access</a>
</p>

## What is Refundly?

Moving out should not mean giving up on your security deposit. Refundly helps US renters understand withheld amounts and prepare a clear, evidence-based response to their landlord.

The demo covers **California, New York, Texas, Florida, and Illinois**. Renters can use it without creating an account.

> **Legal information, not legal advice.** Refundly is not a law firm. Assessments are preliminary, and neither the service nor a generated letter guarantees a deposit refund or court award. State exceptions, local rules, and the facts of each tenancy matter.

## How it works

1. **Describe your rental.** Select the state and enter your deposit, dates, and amount already returned.
2. **Review each deduction.** Add the charge, amount, condition, age, and available evidence.
3. **Understand what to question.** See a preliminary classification and explanation for each line, plus relevant procedural requirements.
4. **Explore possible compensation.** A separate panel shows conditional statutory calculations or guidance. This does **not** increase the amount to review at the top or get added automatically to the demand letter.
5. **Prepare your letter.** Review and edit a draft, then download it as PDF or TXT. Follow-up documents and a calendar reminder help plan the next step.

## Features

- Responsive English-language homepage and renter workspace.
- No renter registration; temporary drafts stay in the browser tab and can be cleared.
- Rule-based deduction analysis, with explanations rather than unexplained AI scores.
- State-law library with official links, source-check dates, limitations, and Refundly record history.
- Separate conditional-compensation panel, including assumptions and court-dependent conditions.
- Editable demand and follow-up letters with PDF/TXT export.
- Simulated checkout, with a default demo price of **$19**.
- Manager and administrator workspaces with synthetic support and payment records.

**Demo boundaries:** no real charges, Stripe integration, email delivery, saved renter cases, or AI API connection. No API key is needed to run this version. Demo staff metrics and payment records are illustrative, not real customer activity.

## Law sources and accuracy

The version-controlled baseline is [`law_catalog.json`](refundly/law_catalog.json). The library distinguishes official statutory checks, official guidance, and incomplete checks; these are editorial source checks, **not attorney certification**.

New York, Texas, and Florida entries were compared with official statutory text. California uses official DRE guidance where direct statutory access was unavailable. Illinois remains marked as a partial check requiring a full-text recheck. The UI displays the applicable source-check dates and limitations.

A deduction being flagged for review does not establish unlawful withholding or bad faith. Compensation calculations illustrate conditional scenarios; the court determines entitlement and any award. The app does not automatically monitor future legal changes.

## Run locally

Use Python **3.12** to match the deployed demo.

```bash
git clone https://github.com/ahmmari691-gif/Refundly_Hackthon.git
cd Refundly_Hackthon/refundly
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 app.py
```

On Windows, activate the environment with `.venv\Scripts\activate` and use `python` if `python3` is unavailable.

Open **http://127.0.0.1:8000**. Press `Ctrl+C` to stop. For another port, run `python3 app.py --port 8001`.

## Technology and structure

Python handles the rules and document generation. The hosted app uses Flask and Gunicorn; the interface uses HTML, CSS, and JavaScript. ReportLab creates PDFs, and SQLite stores staff accounts and workspace data.

```text
Refundly_Hackthon/
├── README.md                 # Project overview
├── render.yaml               # Render service configuration
└── refundly/
    ├── app.py                # Local server, analysis, and letter generation
    ├── wsgi.py               # Flask entry point for hosting
    ├── staff.py              # Staff authentication and workspace API
    ├── law_catalog.json      # State-law baseline and provenance
    ├── requirements.txt
    ├── static/               # Homepage, renter UI, staff UI, and assets
    └── test_*.py             # Automated checks
```

## Tests

From the `refundly` directory:

```bash
python3 -m unittest discover -v
```

Checks cover calculation and input validation, staff permissions, authentication, rule publication, and other demo behavior. Staff tests use temporary databases.

## Hosting on Render

The repository includes a Render configuration. The deployed service uses:

| Setting | Value |
| --- | --- |
| Root directory | `refundly` |
| Build command | `pip install -r requirements.txt` |
| Start command | `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 60` |
| Health check | `/health` |
| Python | `3.12.8` |

Set the hosted administrator variables described below before the first launch. Use the WSGI entry point for hosting; `app.py` is the local development server.

**Storage:** the free demo uses an ephemeral SQLite database. Staff accounts, admin edits, and history can reset when that filesystem is replaced. The committed law baseline survives redeployment. Persistent staff data requires persistent storage or a database service.

## Staff access & account setup

### Explore without an account

Open [Staff sign-in](https://refundly-sxo7.onrender.com/staff) and select **Demo admin** or **Demo manager** below the first-sign-in hint.

These are browser-only demonstrations with synthetic data. They do not grant real administrator access. Changes are temporary, and creating a staff member in this mode does **not** create a real login.

### Local administrator and manager accounts

On the first local run with an empty staff database, the app generates accounts for:

- `admin@refundly.demo`
- `manager@refundly.demo`

Each receives a unique random password. Find the credentials in **`refundly/.local/staff-access.txt`** (or `.local/staff-access.txt` when already inside `refundly`). The file is generated locally; it is not supplied in the repository.

1. Open `http://127.0.0.1:8000/staff`.
2. Enter the generated email and password. Leave **Authenticator code** blank on first sign-in.
3. Add the displayed setup key to a time-based authenticator app.
4. Enter its current six-digit code to finish enrollment.
5. Use your password and a fresh authenticator code for later sign-ins.

### Create the first hosted administrator

In the Render service's environment settings, configure:

| Variable | Purpose |
| --- | --- |
| `REFUNDLY_HOSTED` | Set to `1` for hosted mode |
| `REFUNDLY_ADMIN_EMAIL` | Your administrator email |
| `REFUNDLY_ADMIN_PASSWORD` | A unique password of at least **16 characters** |

The app creates this administrator **only when the staff database contains no users**. Updating these variables does not reset an existing account's password. Hosted mode does not seed the local demo administrator and manager accounts.

After deployment, open `/staff` and complete the same authenticator enrollment described above. Do not put real passwords or authenticator keys in this README, source files, or commits.

### Add another administrator or manager

1. Sign in to a **real administrator account**, not Demo admin.
2. Open **Team & access**.
3. Enter the staff member's name and email, and select **admin** or **manager**.
4. Create the account and share the generated password privately. **No email is sent automatically.**
5. The new staff member signs in at `/staff` and enrolls an authenticator.

Managers work with the synthetic support queue, quality review, and response templates. Administrators additionally manage state rules, demo pricing and payments, staff access, website settings, and audit records. Administrators can change roles, disable access, and end staff sessions.

There is no self-service staff registration or password-recovery flow in this demo. Keep `.local/`, database files, generated passwords, and authenticator secrets out of GitHub and shared archives.

---

**Refundly — a clearer starting point for your next move.**

---



**Sources**
1. California Courts. (n.d.). Security deposits. California Courts Self-Help Guide. https://selfhelp.courts.ca.gov/guide-security-deposits-california⁠

2. Texas State Law Library. (n.d.). Security deposits. https://guides.sll.texas.gov/landlord-tenant-law/security-deposits⁠

3. U.S. Bureau of Labor Statistics. (2026). Employment status of the civilian noninstitutional population by age, sex, and race, 2025 annual averages. https://www.bls.gov/cps/cpsaat03.htm⁠

4. U.S. Census Bureau. (2024). American Community Survey: Tenure (Table B25003). https://data.census.gov/table/ACSDT1Y2024.B25003⁠

5. U.S. Census Bureau. (2024). American Community Survey: Tenure by units in structure (Table B25032). https://data.census.gov/table/ACSDT1Y2024.B25032⁠

6. U.S. Census Bureau. (2025). American Community Survey: Tenure (Table B25003). https://data.census.gov/table/ACSDT1Y2025.B25003⁠

7. Zillow. (2024). Consumer Housing Trends Report 2024. Zillow Research. https://www.zillow.com/research/⁠

8. Zillow. (2026). Consumer Housing Trends Report 2026. Zillow Research. https://www.zillow.com/research/⁠
